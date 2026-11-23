"""LR-027 slice 2: the observe-only monitor's signals, incidents and runner.

Signal tests run inside ONE transaction with session_replication_role =
replica: the tables a signal reads are emptied, exact rows are seeded (foreign
keys are not checked, NOT NULL and CHECK constraints are), the signal is read,
and everything rolls back. Real PostgreSQL, the migrated schema, no mocks of SQL.
"""
import json
import logging
import os
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")

from worker import ops_monitor, ops_signals  # noqa: E402
from worker.ops_signals import Reading  # noqa: E402

TABLES = ("schedules", "schedule_runs", "report_generations", "email_log",
          "consumer_reports", "webhook_deliveries", "ops_alert_members", "ops_alerts")


def u():
    return str(uuid.uuid4())


@pytest.fixture
def cur():
    conn = psycopg.connect(DB)
    try:
        c = conn.cursor()
        c.execute("SET LOCAL session_replication_role = replica")
        for t in TABLES:
            c.execute(f"DELETE FROM {t}")
        yield c
    finally:
        conn.rollback()
        conn.close()


def ids(reading):
    return set(reading.identities)


# ── schedule-level signals ───────────────────────────────────────────────────

def schedule(cur, *, active=True, next_run="now() - interval '16 minutes'", created="now() - interval '1 day'"):
    sid = u()
    cur.execute(f"""INSERT INTO schedules (id, account_id, name, report_type, cadence, recipients, active,
                    next_run_at, created_at) VALUES (%s, %s, 'x', 'market_snapshot', 'weekly', '{{}}', %s,
                    {next_run}, {created})""", (sid, u(), active))
    return f"schedule:{sid}"


def test_an_overdue_active_schedule_is_reported_and_nothing_else(cur):
    overdue = schedule(cur)
    never_computed = schedule(cur, next_run="NULL", created="now() - interval '20 minutes'")
    schedule(cur, next_run="now() - interval '14 minutes'")               # within the 15-minute margin
    schedule(cur, active=False)                                           # the inactive 43 stay out
    assert ids(ops_signals.schedule_overdue(cur)) == {overdue, never_computed}


def test_a_blocked_schedule_is_one_member_however_often_it_was_skipped(cur):
    sid = u()
    for age in ("1 hour", "2 hours"):
        cur.execute(f"""INSERT INTO email_log (account_id, schedule_id, status, created_at)
                        VALUES (%s, %s, 'blocked_unverified', now() - interval '{age}')""", (u(), sid))
    cur.execute("""INSERT INTO email_log (account_id, schedule_id, status, created_at)
                   VALUES (%s, %s, 'blocked_unverified', now() - interval '25 hours')""", (u(), u()))
    reading = ops_signals.schedule_blocked(cur)
    assert ids(reading) == {f"schedule:{sid}"} and reading.count == 1


def run(cur, *, status="queued", tracked=True, attempts=1, age="10 minutes", outcomes=None):
    rid = u()
    cur.execute(f"""INSERT INTO schedule_runs (schedule_id, report_run_id, status, recovery_tracked,
                    dispatch_attempts, created_at, send_outcomes)
                    VALUES (%s, %s, %s, %s, %s, now() - interval '{age}', %s::jsonb)""",
                (u(), rid, status, tracked, attempts, json.dumps(outcomes or [])))
    return rid


def test_dispatch_stranded_is_tracked_open_runs_past_the_attempts_or_horizon(cur):
    exhausted = run(cur, attempts=6)
    old = run(cur, status="processing", age="7 hours")
    run(cur, attempts=5)
    run(cur, tracked=False, attempts=9)
    run(cur, status="completed", attempts=9)
    assert ids(ops_signals.dispatch_stranded(cur)) == {f"run:{exhausted}", f"run:{old}"}


# ── email outcomes ───────────────────────────────────────────────────────────

def email(cur, *, status="failed", code=None, error=None, provider="sendgrid", schedule_id=None,
          report_id=None, resolution=None, age="5 minutes", to=None):
    eid = u()
    cur.execute(f"""INSERT INTO email_log (id, account_id, provider, status, response_code, error, schedule_id,
                    report_id, resolution, created_at, to_emails, subject)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now() - interval '{age}', %s, 'subject')""",
                (eid, u(), provider, status, code, error, schedule_id, report_id, resolution, to))
    return eid


def test_one_held_scheduled_attempt_is_one_member_across_both_tables(cur):
    rid = run(cur, status="needs_review")
    email(cur, status="needs_review", schedule_id=u(), report_id=rid)
    loose = email(cur, status="needs_review")
    email(cur, status="needs_review", resolution="sent")                 # an operator decided
    reading = ops_signals.send_needs_review(cur)
    assert ids(reading) == {f"run:{rid}", f"email:{loose}"} and reading.count == 2


def test_refusals_count_only_what_sendgrid_refused(cur):
    refused = []
    for _ in range(8):                                    # tracked: code NULL, truth in send_outcomes
        rid = run(cur, status="failed", outcomes=[{"email": "e", "outcome": "rejected", "status_code": 403}])
        email(cur, schedule_id=u(), report_id=rid)
        refused.append(f"run:{rid}")
    refused.append(f"email:{email(cur, code=403, error='forbidden')}")       # legacy, real 4xx
    refused.append(f"email:{email(cur, code=429, error='too many')}")
    email(cur, code=400, error="No recipients")                              # synthesized: never sent
    email(cur, code=400, error="No PDF URL")
    email(cur, code=500, error="Request error: boom")                        # ambiguous: neither
    email(cur, code=504, error="Timeout: read")
    email(cur, provider="resend", code=422)                                  # not SendGrid
    email(cur, code=403, age="2 hours")                                      # outside the hour
    reading = ops_signals.provider_refusals(cur)
    assert reading.tripped and ids(reading) == set(refused)
    assert reading.value == {"refused": 10, "deliveries": 14}


def test_nine_refusals_do_not_trip_and_neither_does_a_small_share(cur):
    for _ in range(9):
        email(cur, code=403)
    assert not ops_signals.provider_refusals(cur).tripped
    email(cur, code=403)
    for _ in range(91):                                   # 10 of 101 is under 10%
        email(cur, status="sent", code=202)
    assert not ops_signals.provider_refusals(cur).tripped


def test_sends_that_never_reached_sendgrid_are_their_own_signal(cur):
    a = email(cur, code=400, error="No recipients")
    b = email(cur, code=500, error="SENDGRID_API_KEY not configured")
    c = run(cur, status="failed", outcomes=[{"email": "e", "outcome": "not_sent", "status_code": None}])
    reading = ops_signals.send_not_attempted(cur)
    assert reading.tripped and ids(reading) == {f"email:{a}", f"email:{b}", f"run:{c}"}
    assert not ops_signals.provider_refusals(cur).tripped


# ── reports, consumers, webhooks ─────────────────────────────────────────────

def report(cur, status, minutes):
    rid = u()
    cur.execute(f"""INSERT INTO report_generations (id, account_id, report_type, status, generated_at)
                    VALUES (%s, %s, 'market_snapshot', %s, LOCALTIMESTAMP - interval '{minutes} minutes')""",
                (rid, u(), status))
    return f"report:{rid}"


def test_a_report_still_processing_45_minutes_after_creation_is_stuck(cur):
    stuck = report(cur, "processing", 46)
    report(cur, "processing", 44)
    report(cur, "completed", 90)
    assert ids(ops_signals.report_stuck(cur)) == {stuck}


@pytest.mark.parametrize("failed, ok, tripped", [(5, 15, True), (5, 25, False), (4, 0, False)])
def test_report_failures_need_five_and_a_fifth(cur, failed, ok, tripped):
    for _ in range(failed):
        report(cur, "failed", 10)
    for _ in range(ok):
        report(cur, "completed", 10)
    report(cur, "failed", 90)                             # outside the hour
    reading = ops_signals.report_failures(cur)
    assert reading.tripped is tripped and reading.value == {"failed": failed, "total": failed + ok}


def consumer(cur, created="1 hour", **cols):
    cid = u()
    names = ", ".join(cols)
    values = ", ".join(cols.values())
    cur.execute(f"""INSERT INTO consumer_reports (id, agent_id, agent_code, property_address, created_at
                    {', ' + names if cols else ''})
                    VALUES (%s, %s, 'code', '1 Secret St', now() - interval '{created}'
                    {', ' + values if cols else ''})""", (cid, u()))
    return f"consumer:{cid}"


def test_consumer_deliveries_that_did_not_complete(cur):
    stuck = consumer(cur, delivery_claimed_at="now() - interval '16 minutes'")
    agent = consumer(cur, agent_notify_status="'failed'", updated_at="now() - interval '20 minutes'")
    consumer(cur, agent_notify_status="'failed'")                     # just refused: its retry is due
    pdf = consumer(cur, pdf_status="'generating'", pdf_claimed_at="now() - interval '16 minutes'")
    consumer(cur, delivery_claimed_at="now() - interval '16 minutes'", consumer_email_sent_at="now()")
    consumer(cur, delivery_claimed_at="now() - interval '5 minutes'")
    consumer(cur, created="8 days", agent_notify_status="'failed'")
    assert ids(ops_signals.consumer_delivery_stuck(cur)) == {stuck, agent, pdf}


def test_a_customer_webhook_failing_three_times_an_hour(cur):
    hook, quiet = u(), u()
    for status, err in ((500, None), (None, "timeout"), (404, None)):
        cur.execute("""INSERT INTO webhook_deliveries (account_id, webhook_id, event, payload, response_status,
                       error, created_at) VALUES (%s, %s, 'report.completed', '{}', %s, %s, LOCALTIMESTAMP)""",
                    (u(), hook, status, err))
    for status in (500, 200, 200):
        cur.execute("""INSERT INTO webhook_deliveries (account_id, webhook_id, event, payload, response_status,
                       created_at) VALUES (%s, %s, 'report.completed', '{}', %s, LOCALTIMESTAMP)""",
                    (u(), quiet, status))
    assert ids(ops_signals.report_webhook_failures(cur)) == {f"webhook:{hook}"}


# ── incidents and membership ─────────────────────────────────────────────────

def test_an_incident_announces_each_member_once_and_resolves(cur, caplog):
    caplog.set_level(logging.WARNING, logger=ops_monitor.logger.name)
    a, b = "run:" + u(), "run:" + u()
    assert ops_monitor.record(cur, "k", Reading(True, [a], 1, {"count": 1})) == "open"
    assert ops_monitor.record(cur, "k", Reading(True, [a], 1, {"count": 1})) is None
    assert ops_monitor.record(cur, "k", Reading(True, [a, b], 2, {"count": 2})) == "new_members"
    assert caplog.messages[-1].count("new=1") == 1 and b in caplog.messages[-1]
    assert ops_monitor.record(cur, "k", Reading(True, [b], 1, {})) is None      # a left
    assert ops_monitor.record(cur, "k", Reading(True, [a, b], 2, {})) is None   # a returned: not new
    cur.execute("SELECT count(*) FROM ops_alert_members m JOIN ops_alerts o ON o.id = m.alert_id WHERE o.key = 'k'")
    assert cur.fetchone()[0] == 2
    assert ops_monitor.record(cur, "k", Reading(False)) == "resolved"
    assert ops_monitor.record(cur, "k", Reading(False)) is None
    assert ops_monitor.record(cur, "k", Reading(True, [a], 1, {})) == "open"
    assert "flap=true" in caplog.messages[-1]                                  # re-tripped within 30 min


def test_beyond_the_stored_bound_only_growth_is_announced(cur):
    stored = [f"run:{i}" for i in range(ops_signals.MEMBER_LIMIT)]
    assert ops_monitor.record(cur, "big", Reading(True, stored, 6000, {})) == "open"
    for _ in range(3):
        assert ops_monitor.record(cur, "big", Reading(True, stored, 6000, {})) is None
    assert ops_monitor.record(cur, "big", Reading(True, stored, 5990, {})) is None
    assert ops_monitor.record(cur, "big", Reading(True, stored, 6001, {})) == "grew"
    cur.execute("SELECT members_truncated, member_count, notified_count FROM ops_alerts WHERE key='big'")
    assert cur.fetchone() == (True, 6001, 6001)


def test_logs_carry_identities_and_counts_never_contact_details(cur, caplog):
    caplog.set_level(logging.WARNING, logger=ops_monitor.logger.name)
    for _ in range(3):
        email(cur, code=400, error="No recipients", to=["homeowner.secret@example.com", "+15555550123"])
    consumer(cur, agent_notify_status="'failed'")
    for sig in ops_signals.SIGNALS:
        ops_monitor.record(cur, sig.key, sig.read(cur))
    text = caplog.text
    assert "OPS_ALERT mode=observe" in text
    for secret in ("homeowner.secret", "@example.com", "5555550123", "Secret St", "subject"):
        assert secret not in text, secret


# ── heartbeats ───────────────────────────────────────────────────────────────

@pytest.fixture
def r():
    """An explicitly disposable Redis (TEST_REDIS_URL, set by CI). Cleanup
    deletes only the keys these tests own, never the database (Codex #322)."""
    redis = pytest.importorskip("redis")
    from worker import ops_heartbeat as hb
    url = os.getenv("TEST_REDIS_URL")
    if not url:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is not set")
        pytest.skip("Set TEST_REDIS_URL to a disposable Redis database")
    conn = redis.from_url(url, decode_responses=True)
    try:
        conn.ping()
    except redis.exceptions.ConnectionError:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is unreachable")
        pytest.skip("TEST_REDIS_URL is unreachable")
    owned = (hb.TICKER_KEY, hb.WORKER_KEY, hb.CELERY_QUEUE, ops_monitor.LEASE_KEY)
    conn.delete(*owned)
    yield conn
    conn.delete(*owned)


def test_heartbeat_signals_tell_a_dead_worker_from_a_backlog(r):
    from worker import ops_heartbeat as hb
    now = int(r.time()[0])
    r.set(hb.TICKER_KEY, now)
    r.set(hb.WORKER_KEY, now - 600)
    readings = ops_monitor.heartbeat_readings(r)
    assert not readings["ticker_stale"].tripped
    assert readings["worker_stale"].tripped and not readings["worker_backlog"].tripped
    r.rpush(hb.CELERY_QUEUE, "x")
    readings = ops_monitor.heartbeat_readings(r)
    assert readings["worker_backlog"].tripped and not readings["worker_stale"].tripped
    r.delete(hb.TICKER_KEY)
    assert ops_monitor.heartbeat_readings(r)["ticker_stale"].tripped


# ── the runner ───────────────────────────────────────────────────────────────

@pytest.fixture
def committed_keys(monkeypatch):
    # The runner also reads the real heartbeats; keep those incidents out of a
    # committed test run.
    monkeypatch.setattr(ops_monitor, "heartbeat_readings", lambda _client: {})
    made = []
    yield made
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("DELETE FROM ops_alerts WHERE key = ANY(%s)", (made,))


def test_one_failing_signal_never_stops_the_others(monkeypatch, committed_keys, r):
    good, bad = f"t-good-{u()}", f"t-bad-{u()}"
    committed_keys += [good, bad]

    def boom(_cur):
        raise RuntimeError("signal broke")

    monkeypatch.setattr(ops_signals, "SIGNALS", [
        ops_signals.Signal(bad, True, "x", boom),
        ops_signals.Signal(good, True, "x", lambda _cur: Reading(True, ["run:" + u()], 1, {})),
    ])
    results = ops_monitor.run_once(DB, r)
    assert results[bad] == "error" and results[good] == "open"


def test_the_budget_defers_what_is_left(monkeypatch, committed_keys, r):
    keys = [f"t-budget-{u()}" for _ in range(3)]
    committed_keys += keys
    monkeypatch.setattr(ops_signals, "SIGNALS",
                        [ops_signals.Signal(k, True, "x", lambda _cur: Reading(False)) for k in keys])
    ticks = iter([0, 0, 91, 92, 93, 94, 95, 96, 97, 98])
    results = ops_monitor.run_once(DB, r, clock=lambda: next(ticks))
    assert results[keys[0]] is None and results[keys[1]] == "deferred" and results[keys[2]] == "deferred"


def test_without_the_0069_tables_the_monitor_does_nothing(caplog):
    scratch = os.getenv("TEST_DATABASE_URL")
    if not scratch:
        pytest.skip("TEST_DATABASE_URL (an empty scratch database) is needed")
    caplog.set_level(logging.WARNING, logger=ops_monitor.logger.name)
    assert ops_monitor.run_once(scratch, None) == {}
    assert "migration 0069" in caplog.text


def test_an_unreachable_database_is_logged_not_raised(caplog):
    caplog.set_level(logging.WARNING, logger=ops_monitor.logger.name)
    assert ops_monitor.run_once("postgresql://postgres@127.0.0.1:1/x", None) == {}
    assert "database unreachable" in caplog.text


def test_one_run_per_window_across_tickers_and_never_overlapping(monkeypatch, r):
    started, release = [], threading.Event()

    def fake_run(db_url, client):
        started.append(db_url)
        release.wait(5)

    monkeypatch.setattr(ops_monitor, "run_once", fake_run)
    clock = [1000.0]
    a = ops_monitor.MonitorRunner("db-a", clock=lambda: clock[0])
    b = ops_monitor.MonitorRunner("db-b", clock=lambda: clock[0])
    assert a.maybe_start(r) is True
    for _ in range(100):
        if started:
            break
        time.sleep(0.01)
    assert b.maybe_start(r) is True
    b.thread.join(2)
    assert started == ["db-a"]                            # lease held: b's window did not run
    clock[0] += 400
    r.delete(ops_monitor.LEASE_KEY)
    assert a.maybe_start(r) is False                      # previous run still alive
    release.set()
    a.thread.join(5)
    assert a.maybe_start(r) is True
    a.thread.join(5)
    assert started == ["db-a", "db-a"]
    assert 0 < r.ttl(ops_monitor.LEASE_KEY) <= ops_monitor.LEASE_S


def test_a_redis_outage_never_reaches_the_ticker_loop(monkeypatch):
    redis = pytest.importorskip("redis")
    ran = []
    monkeypatch.setattr(ops_monitor, "run_once", lambda *a: ran.append(1))
    down = redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=0.2, socket_timeout=0.2)
    runner = ops_monitor.MonitorRunner("db")
    runner.maybe_start(down)                              # never raises
    runner.thread.join(2)
    assert ran == []                                      # no lease, no run


def test_the_ticker_starts_the_monitor_after_each_tick():
    import ast
    tree = ast.parse((ROOT / "src/worker/schedules_tick.py").read_text())
    loop = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "run_forever")
    calls = [ast.unparse(n.func) for n in ast.walk(loop) if isinstance(n, ast.Call)]
    assert "tick_once" in calls and "monitor.maybe_start" in calls


def test_the_monitor_module_never_calls_a_provider_itself(monkeypatch):
    """All delivery lives in ops_notify, behind OPS_ALERTS_ENABLED (slice 3)."""
    monkeypatch.delenv("OPS_ALERTS_ENABLED", raising=False)
    assert ops_monitor.enabled_mode() == "observe"
    code = ast_code(ROOT / "src/worker/ops_monitor.py")
    for sender in ("sendgrid", "twilio", "send_sms", "send_email", "ops_alert_notifications", "send_task"):
        assert sender not in code, sender


def ast_code(path):
    """The module's code with docstrings removed, lower-cased."""
    import ast
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            body[0] = ast.Pass()
    return ast.unparse(tree).lower()


# ── The monitor must never hold up the ticker either (Codex #322 principle) ──

@pytest.fixture
def silent_redis_client():
    import socket
    redis = pytest.importorskip("redis")
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(16)
    held = []

    def accept():
        while True:
            try:
                held.append(server.accept()[0])
            except OSError:
                return

    threading.Thread(target=accept, daemon=True).start()
    yield redis.from_url(f"redis://127.0.0.1:{server.getsockname()[1]}/0",
                         socket_connect_timeout=1, socket_timeout=1)
    server.close()
    for conn in held:
        conn.close()


def test_a_redis_that_never_answers_never_holds_up_a_tick(silent_redis_client):
    import time as clock
    clock_now = [0.0]
    runner = ops_monitor.MonitorRunner("db", clock=lambda: clock_now[0])
    started = clock.monotonic()
    for _ in range(5):
        runner.maybe_start(silent_redis_client)
        clock_now[0] += 400                     # a new window every tick
    assert clock.monotonic() - started < 0.5, "the lease call ran on the ticker's thread"


# ── Codex #323: the states the WRITERS leave, driven through the real writers ──

def consumer_row(cur, *, status="processing", sent=False, agent_id=None, updated="now()"):
    rid, gen = u(), u()
    cur.execute(f"""INSERT INTO consumer_reports (id, agent_id, agent_code, property_address, status,
                    generation_id, consumer_email_sent_at, created_at, updated_at)
                    VALUES (%s, %s, 'code', '1 Secret St', %s, %s, {'now()' if sent else 'NULL'},
                    now() - interval '1 hour', {updated})""", (rid, agent_id or u(), status, gen))
    return rid, gen


def stuck(cur):
    return ids(ops_signals.consumer_delivery_stuck(cur))


def test_a_provider_refused_consumer_delivery_is_reported(cur):
    from worker import consumer_delivery as cd
    rid, gen = consumer_row(cur)
    attempt, _key = cd.claim_email(cur.connection, rid, gen, account_id=u(),
                                   to_email="homeowner@example.com", subject="Your report")
    assert stuck(cur) == set()                                        # claimed just now: in flight
    assert cd.release_refused(cur.connection, rid, attempt, channel="email",
                              text="Resend refused the message (422)", response_code=422)
    cur.execute("SELECT status, delivery_claimed_at FROM consumer_reports WHERE id = %s", (rid,))
    assert cur.fetchone() == ("failed", None)                         # the claim is cleared
    assert stuck(cur) == {f"consumer:{rid}"}


def test_an_active_retry_is_not_reported_until_it_stops(cur):
    from worker import consumer_delivery as cd
    from worker.tasks import consumer_failure_text
    rid, gen = consumer_row(cur)
    attempt, _ = cd.claim_email(cur.connection, rid, gen, account_id=u(), to_email="h@example.com", subject="s")
    cd.release_refused(cur.connection, rid, attempt, channel="email", text="Resend 429", response_code=429)
    retrying = consumer_failure_text("Resend 429 (attempt 1 of 4; retrying)")    # the task's own note
    cur.execute("UPDATE consumer_reports SET error_message = %s, updated_at = now() WHERE id = %s", (retrying, rid))
    assert stuck(cur) == set()                                        # a retry is due within minutes
    cur.execute("UPDATE consumer_reports SET updated_at = now() - interval '20 minutes' WHERE id = %s", (rid,))
    assert stuck(cur) == {f"consumer:{rid}"}                          # the retry never came
    gave_up = consumer_failure_text("Resend 429 (gave up after 4 attempts)")
    cur.execute("UPDATE consumer_reports SET error_message = %s, updated_at = now() WHERE id = %s", (gave_up, rid))
    assert stuck(cur) == {f"consumer:{rid}"}                          # exhausted: terminal at once


def test_a_held_or_never_generated_consumer_report_is_reported(cur):
    held, _ = consumer_row(cur, status="needs_review")
    generating, _ = consumer_row(cur, status="processing", updated="now() - interval '50 minutes'")
    consumer_row(cur, status="processing")                            # generating normally
    consumer_row(cur, status="failed", sent=True)                     # delivered: never reported
    assert stuck(cur) == {f"consumer:{held}", f"consumer:{generating}"}


def agent_ready(cur):
    agent = u()
    cur.execute("INSERT INTO users (id, account_id, email, phone) VALUES (%s, %s, %s, '+15555550100')",
                (agent, u(), f"agent-{agent[:8]}@example.com"))
    rid, _ = consumer_row(cur, status="sent", sent=True, agent_id=agent)
    return rid


def test_an_abandoned_agent_claim_is_reported_and_a_sent_one_is_not(cur):
    from worker import consumer_delivery as cd
    rid = agent_ready(cur)
    claimed = cd.claim_agent_notification(cur.connection, rid, from_phone="+15555550199",
                                          build_body=lambda row: "New lead")
    assert claimed is not None
    attempt = claimed[0]
    assert stuck(cur) == set()                                        # inside the claim window
    cur.execute("UPDATE consumer_reports SET agent_notify_claimed_at = now() - interval '20 minutes' WHERE id = %s",
                (rid,))
    assert stuck(cur) == {f"consumer:{rid}"}                          # the worker died after the claim
    cur.execute("UPDATE consumer_reports SET agent_notify_claimed_at = NULL WHERE id = %s", (rid,))
    assert stuck(cur) == {f"consumer:{rid}"}                          # the undated case
    assert cd.record_agent_sent(cur.connection, rid, attempt, sid="SM-test")
    assert stuck(cur) == set()                                        # the agent was notified


def test_an_agent_refusal_counts_only_after_its_retries(cur):
    from worker import consumer_delivery as cd
    rid = agent_ready(cur)
    attempt = cd.claim_agent_notification(cur.connection, rid, from_phone="+15555550199",
                                          build_body=lambda row: "New lead")[0]
    assert cd.release_agent_refused(cur.connection, rid, attempt, text="Twilio 429")
    cur.execute("SELECT agent_notify_claimed_at FROM consumer_reports WHERE id = %s", (rid,))
    assert cur.fetchone() == (None,)                                  # the refusal cleared the claim
    assert stuck(cur) == set()                                        # a retry re-claims within minutes
    # The table's trigger stamps updated_at on every write (it is off in this
    # replica-role transaction, so the test stamps it as the trigger would).
    cur.execute("UPDATE consumer_reports SET updated_at = now() - interval '20 minutes' WHERE id = %s", (rid,))
    assert stuck(cur) == {f"consumer:{rid}"}                          # no retry came


def homeowner_delivered(cur, *, phone="+15555550100"):
    """A lead whose homeowner email the REAL writers recorded as sent."""
    from worker import consumer_delivery as cd
    agent = u()
    cur.execute("INSERT INTO users (id, account_id, email, phone) VALUES (%s, %s, %s, %s)",
                (agent, u(), f"agent-{agent[:8]}@example.com", phone))
    rid, gen = consumer_row(cur, status="processing", agent_id=agent)
    attempt, _key = cd.claim_email(cur.connection, rid, gen, account_id=u(),
                                   to_email="homeowner@example.com", subject="Your report")
    assert cd.record_email_sent(cur.connection, rid, attempt, account_id=u(),
                                response_code=200, provider_message_id="msg-test")
    cur.execute("SELECT status, agent_notify_status FROM consumer_reports WHERE id = %s", (rid,))
    assert cur.fetchone() == ("sent", None)                           # stopped BEFORE the agent claim
    return rid


def delivered_ago(cur, rid, interval):
    cur.execute("UPDATE consumer_reports SET consumer_email_sent_at = now() - %s::interval WHERE id = %s",
                (interval, rid))


def test_an_agent_text_that_never_started_is_reported(cur):
    """Codex re-review of #323: the run died between the homeowner's `sent`
    write and claim_agent_notification, so no agent claim, SID or time exists."""
    from worker import consumer_delivery as cd
    rid = homeowner_delivered(cur)
    assert stuck(cur) == set()                                        # fresh: _notify_agent runs inline
    delivered_ago(cur, rid, "20 minutes")
    assert stuck(cur) == {f"consumer:{rid}"}                          # overdue and never claimed
    claimed = cd.claim_agent_notification(cur.connection, rid, from_phone="+15555550199",
                                          build_body=lambda row: "New lead")
    assert claimed is not None                                        # the writer agrees it is recoverable
    assert cd.record_agent_sent(cur.connection, rid, claimed[0], sid="SM-test")
    assert stuck(cur) == set()                                        # already-sent evidence


def test_an_unstarted_agent_text_is_not_reported_when_it_is_not_owed(cur):
    from worker import consumer_delivery as cd
    no_phone = homeowner_delivered(cur, phone="  ")                   # no usable phone
    delivered_ago(cur, no_phone, "20 minutes")
    blank = homeowner_delivered(cur, phone=None)
    delivered_ago(cur, blank, "20 minutes")
    assert stuck(cur) == set()
    skipped = homeowner_delivered(cur)                                # the writer's intentional skip
    delivered_ago(cur, skipped, "20 minutes")
    cur.execute("UPDATE consumer_reports SET agent_notify_status = 'skipped' WHERE id = %s", (skipped,))
    sent = homeowner_delivered(cur)                                   # sent evidence, status untouched
    delivered_ago(cur, sent, "20 minutes")
    cur.execute("UPDATE consumer_reports SET agent_sms_sent_at = now() WHERE id = %s", (sent,))
    sid_only = homeowner_delivered(cur)
    delivered_ago(cur, sid_only, "20 minutes")
    cur.execute("UPDATE consumer_reports SET agent_sms_sid = 'SM-x' WHERE id = %s", (sid_only,))
    assert stuck(cur) == set()
    assert cd.claim_agent_notification(cur.connection, no_phone, from_phone="+15555550199",
                                       build_body=lambda row: "x") is None


def test_past_the_recovery_window_it_stays_reported_and_is_never_re_texted(cur):
    """The 24-hour automatic-recovery boundary is the writer's. The alert keeps
    the row in front of a person; it does not make it eligible again."""
    from worker import consumer_delivery as cd
    rid = homeowner_delivered(cur)
    delivered_ago(cur, rid, f"{cd.AGENT_RECOVERY_HOURS + 1} hours")
    assert stuck(cur) == {f"consumer:{rid}"}
    assert cd.agent_stage(cur, rid)[2] is False                       # not eligible
    assert cd.claim_agent_notification(cur.connection, rid, from_phone="+15555550199",
                                       build_body=lambda row: "x") is None


@pytest.fixture
def committed_runs():
    made = []
    yield made
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("DELETE FROM schedule_runs WHERE report_run_id = ANY(%s::uuid[])", (made,))


def tracked_run(made):
    run, token = u(), u()
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("SET session_replication_role = replica")
        conn.execute("""INSERT INTO schedule_runs (schedule_id, report_run_id, status, recovery_tracked,
                        owner_token, created_at) VALUES (%s, %s, 'processing', TRUE, %s, now())""",
                     (u(), run, token))
    made.append(run)
    return run, token


def test_tracked_pre_claim_refusals_reach_send_not_attempted(committed_runs):
    from worker import scheduled_runs, tasks
    refused = []
    for _ in range(3):
        run, token = tracked_run(committed_runs)
        result = tasks._send_tracked(None, u(), run, u(), [], "subject", {}, "Account", None, "REGULAR",
                                     tasks.TrackedSend(run, token))
        assert result.status == scheduled_runs.FAILED and result.error.startswith("failed_email: nothing sent")
        assert scheduled_runs.finish(DB, run, token, result.status, result.error)
        refused.append(f"run:{run}")
    suppressed, token = tracked_run(committed_runs)                   # all_suppressed: completed
    scheduled_runs.finish(DB, suppressed, token, scheduled_runs.COMPLETED,
                          "every recipient has unsubscribed; nothing sent")
    cancelled, token = tracked_run(committed_runs)
    scheduled_runs.finish(DB, cancelled, token, "cancelled", "schedule deleted")
    with psycopg.connect(DB) as conn:
        reading = ops_signals.send_not_attempted(conn.cursor())
    assert reading.tripped and set(refused) <= ids(reading)
    assert f"run:{suppressed}" not in ids(reading) and f"run:{cancelled}" not in ids(reading)
