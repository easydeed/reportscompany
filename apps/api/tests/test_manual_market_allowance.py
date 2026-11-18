"""Manual admissions at the last positive-grace slot, on migrated PostgreSQL."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import pytest

from test_idempotent_create import (
    DB, REPORT, SCHEDULE, _count, _key, _keyed, account, client, psycopg, queue,
)

pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="requires migrated DATABASE_URL")


@pytest.fixture
def last_slot(account, monkeypatch):
    from api.routes import reports

    notices = []
    monkeypatch.setattr(reports, "_check_and_notify_limit", lambda *args: notices.append(args))
    aid, auth = account()
    with psycopg.connect(DB) as conn:
        conn.execute("UPDATE accounts SET market_reports_limit_override = 1 WHERE id = %s", (aid,))
        conn.execute("""INSERT INTO report_generations (account_id, report_type, status)
                        VALUES (%s, 'market_snapshot', 'completed')""", (aid,))
    return aid, auth, notices


def assert_exhausted(response):
    assert response.status_code == 429, response.text
    detail = response.json()["detail"]
    assert (detail["error"], detail["used"], detail["limit"]) == ("market_report_limit_reached", 2, 1)


def test_distinct_keys_compete_for_one_slot(client, last_slot, queue, monkeypatch):
    from api.services import idempotency

    aid, auth, notices = last_slot
    winner, contender = _key(), _key()
    inserted = Queue()
    release = threading.Event()
    record = idempotency.record

    def hold_before_commit(cur, account_id, claim, report_id):
        record(cur, account_id, claim, report_id)
        if claim.key == winner:
            inserted.put(cur.connection.info.backend_pid)
            assert release.wait(30), "test did not release the first transaction"

    monkeypatch.setattr(idempotency, "record", hold_before_commit)
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(DB, autocommit=True) as observer:
        first = pool.submit(_keyed, client, auth, "reports", REPORT, winner)
        try:
            first_pid = inserted.get(timeout=20)
            second = pool.submit(_keyed, client, auth, "reports", REPORT, contender)
            # Wait for actual contention, or for an unserialized request to finish.
            blocked = False
            deadline = time.monotonic() + 15
            while not second.done() and time.monotonic() < deadline:
                blocked = observer.execute("""
                    SELECT EXISTS (SELECT 1 FROM pg_stat_activity
                                   WHERE datname = current_database() AND %s = ANY(pg_blocking_pids(pid)))
                """, (first_pid,)).fetchone()[0]
                if blocked:
                    break
                time.sleep(0.02)
        finally:
            release.set()
        accepted = first.result(timeout=20)
        assert accepted.status_code == 202, accepted.text
        assert_exhausted(second.result(timeout=20))
        assert blocked, "second admission never waited for the first transaction"

    rid = accepted.json()["report_id"]
    replay = _keyed(client, auth, "reports", REPORT, winner)
    assert replay.status_code == 202 and replay.headers["Idempotent-Replayed"] == "true"
    assert replay.json() == {"report_id": rid, "status": "pending"}
    assert _count("report_generations", aid) == 2 and _count("request_idempotency", aid) == 1
    assert queue == [rid] and len(notices) == 1


def test_each_status_counts_once_and_failure_releases_the_slot(client, last_slot, queue):
    aid, auth, _ = last_slot
    accepted = client.post("/v1/reports", headers=auth, json=REPORT)
    assert accepted.status_code == 202, accepted.text
    rid = accepted.json()["report_id"]
    retry_key = _key()
    with psycopg.connect(DB, autocommit=True) as conn:
        for status, displayed in (("pending", 1), ("processing", 2)):
            conn.execute("UPDATE report_generations SET status = %s WHERE id = %s", (status, rid))
            assert_exhausted(_keyed(client, auth, "reports", REPORT, retry_key))
            usage = client.get("/v1/account/plan-usage", headers=auth).json()["usage"]
            assert usage["market_reports_used"] == displayed
        conn.execute("UPDATE report_generations SET status = 'failed' WHERE id = %s", (rid,))
        replacement = _keyed(client, auth, "reports", REPORT, retry_key)
        assert replacement.status_code == 202, replacement.text
        replacement_id = replacement.json()["report_id"]
        conn.execute("UPDATE report_generations SET status = 'completed' WHERE id = %s", (replacement_id,))
    assert_exhausted(client.post("/v1/reports", headers=auth, json=REPORT))
    assert queue == [rid, replacement_id]
    assert _count("request_idempotency", aid) == 1


def test_enqueue_failure_frees_capacity_without_a_usage_notice(client, last_slot, monkeypatch, queue):
    from api import worker_client

    _, auth, notices = last_slot
    failed_key = _key()

    def fail_enqueue(*args):
        raise ConnectionError("synthetic queue failure")

    with monkeypatch.context() as failed_queue:
        failed_queue.setattr(worker_client, "enqueue_generate_report", fail_enqueue)
        attempt = _keyed(client, auth, "reports", REPORT, failed_key)
    replay = _keyed(client, auth, "reports", REPORT, failed_key)
    assert replay.json() == {"report_id": attempt.json()["report_id"], "status": "failed"}
    assert not notices
    replacement = client.post("/v1/reports", headers=auth, json=REPORT)
    assert replacement.status_code == 202, replacement.text
    assert queue == [replacement.json()["report_id"]] and len(notices) == 1


def test_only_this_months_billable_manual_generations_reserve(client, last_slot, queue):
    aid, auth, _ = last_slot
    schedule = client.post("/v1/schedules", headers=auth, json=SCHEDULE)
    assert schedule.status_code == 201, schedule.text
    sid = schedule.json()["id"]
    with psycopg.connect(DB) as conn:
        conn.execute("""
            INSERT INTO report_generations (account_id, report_type, status, billable)
            SELECT %s, 'market_snapshot', status, FALSE FROM unnest(ARRAY['pending','processing','completed']) status
        """, (aid,))
        conn.execute("""INSERT INTO report_generations (account_id, report_type, status, generated_at)
                        VALUES (%s, 'market_snapshot', 'completed', date_trunc('month', now()) - interval '1 day')""",
                     (aid,))
        legacy = conn.execute("""INSERT INTO report_generations (account_id, report_type, status)
                                 VALUES (%s, 'market_snapshot', 'processing') RETURNING id""", (aid,)).fetchone()[0]
        conn.execute("INSERT INTO schedule_runs (schedule_id, report_run_id) VALUES (%s, %s)", (sid, legacy))
        # The ticker also stores the schedule ID on the generation itself. It
        # survives deletion of a schedule and its cascading schedule_runs.
        conn.execute("""INSERT INTO report_generations (account_id, report_type, status, input_params)
                        VALUES (%s, 'market_snapshot', 'completed', jsonb_build_object('schedule_id', %s::text))""",
                     (aid, sid))
    accepted = client.post("/v1/reports", headers=auth, json=REPORT)
    assert accepted.status_code == 202, accepted.text
    assert_exhausted(client.post("/v1/reports", headers=auth, json=REPORT))
    assert queue == [accepted.json()["report_id"]]
    # Exhausting manual capacity still allows an active schedule.
    another = client.post("/v1/schedules", headers=auth, json={**SCHEDULE, "name": "Second weekly"})
    assert another.status_code == 201 and another.json()["active"], another.text
