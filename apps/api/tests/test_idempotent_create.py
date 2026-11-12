"""A retried create returns what the first one made (LR-024, D-382/D-330).

Real routes on the migrated database, signed in through /v1/auth/login; only
the report queue is replaced. Design rev 3 (Codex design PASS): keyed creates
use POST /v1/idempotent/{reports,schedules}; the old routes take no key.

On main a create whose answer was lost and was sent again made a second
report (a second usage count, a second email to each recipient) or a second
schedule that sends on every run.
"""
import json
import os
import threading
import uuid

import pytest

DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")
PASSWORD = "IdempotentCreate123!"

REPORT = {"report_type": "market_snapshot", "zips": ["91750", "91711"], "lookback_days": 30}
SCHEDULE = {
    "name": "LR-024 weekly", "report_type": "market_snapshot", "zip_codes": ["91750"],
    "lookback_days": 30, "cadence": "weekly", "weekly_dow": 1, "send_hour": 9, "send_minute": 0,
    "timezone": "America/Los_Angeles", "recipients": ["client@example.com"],
    "include_attachment": True, "active": True,
}


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def account(client):
    """A fresh verified account on a plan with room; returns (id, auth headers)."""
    made = []

    def make(verified=True, plan="pro"):
        aid = str(uuid.uuid4())
        email = f"lr024-{aid[:8]}@example.com"
        with psycopg.connect(DB, autocommit=True) as conn:
            conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active) "
                         "VALUES (%s, 'LR-024', %s, 'REGULAR', %s, 'active', true)", (aid, f"lr024-{aid[:8]}", plan))
            conn.execute("INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active) "
                         "VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', %s, true)",
                         (aid, aid, email, PASSWORD, verified))
            conn.execute("INSERT INTO account_users (account_id, user_id, role) VALUES (%s, %s, 'OWNER')", (aid, aid))
        made.append(aid)
        r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return aid, {"Authorization": f"Bearer {r.json()['access_token']}"}
    yield make
    with psycopg.connect(DB, autocommit=True) as conn:
        for aid in made:
            for table in ("request_idempotency", "report_generations", "schedules", "account_users", "users"):
                conn.execute(f"DELETE FROM {table} WHERE account_id = %s", (aid,))
            conn.execute("DELETE FROM accounts WHERE id = %s", (aid,))


@pytest.fixture(autouse=True)
def queue(monkeypatch):
    from api import worker_client
    queued = []
    monkeypatch.setattr(worker_client, "enqueue_generate_report", lambda rid, *a, **k: queued.append(rid))
    return queued


def _count(table, aid):
    with psycopg.connect(DB) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE account_id = %s", (aid,)).fetchone()[0]


def _keyed(client, headers, what, body, key, raw=None):
    h = {**headers, "Idempotency-Key": key}
    if raw is not None:
        return client.post(f"/v1/idempotent/{what}", content=raw, headers={**h, "Content-Type": "application/json"})
    return client.post(f"/v1/idempotent/{what}", json=body, headers=h)


def _key():
    return f"k-{uuid.uuid4().hex}"


# ── a retry replays ─────────────────────────────────────────────────────────

def test_a_retried_report_is_the_same_report_counted_and_queued_once(client, account, queue):
    aid, auth = account()
    key = _key()
    first = _keyed(client, auth, "reports", REPORT, key)
    again = _keyed(client, auth, "reports", REPORT, key)
    assert first.status_code == 202 and again.status_code == 202
    assert again.json()["report_id"] == first.json()["report_id"]
    assert again.headers.get("Idempotent-Replayed") == "true" and "Idempotent-Replayed" not in first.headers
    assert _count("report_generations", aid) == 1, "the retry made a second report (a second usage count)"
    assert queue == [first.json()["report_id"]], "the retry queued the report again (a second email)"


def test_a_retried_schedule_is_the_same_schedule(client, account):
    aid, auth = account()
    key = _key()
    first = _keyed(client, auth, "schedules", SCHEDULE, key)
    again = _keyed(client, auth, "schedules", SCHEDULE, key)
    assert first.status_code == 201 and again.status_code == 201
    assert again.json()["id"] == first.json()["id"] and again.headers.get("Idempotent-Replayed") == "true"
    assert _count("schedules", aid) == 1


def test_four_concurrent_requests_with_one_key_create_one(client, account, monkeypatch, queue):
    from api.services import idempotency
    aid, auth = account()
    key = _key()
    real = idempotency.lookup
    together = threading.Barrier(4, timeout=3)

    def all_at_once(*a, **k):
        try:
            together.wait()
        except threading.BrokenBarrierError:
            pass
        return real(*a, **k)
    monkeypatch.setattr(idempotency, "lookup", all_at_once)
    out = []
    threads = [threading.Thread(target=lambda: out.append(_keyed(client, auth, "reports", REPORT, key))) for _ in range(4)]
    [t.start() for t in threads]
    [t.join(60) for t in threads]
    assert sorted(r.status_code for r in out) == [202] * 4, [r.text for r in out]
    assert len({r.json()["report_id"] for r in out}) == 1
    assert _count("report_generations", aid) == 1 and len(queue) == 1


# ── what a key will not do ──────────────────────────────────────────────────

def test_the_same_key_with_a_different_request_is_refused_and_creates_nothing(client, account):
    aid, auth = account()
    key = _key()
    _keyed(client, auth, "reports", REPORT, key)
    other = _keyed(client, auth, "reports", {**REPORT, "lookback_days": 90}, key)
    assert other.status_code == 409 and other.json()["detail"]["error"] == "idempotency_key_reused"
    assert _count("report_generations", aid) == 1


@pytest.mark.parametrize("age, outcome", [
    ("6 days 23 hours", "replay"),
    ("7 days 1 second", "expired"),
    ("30 days", "expired"),
])
def test_the_replay_window_is_seven_days_and_an_old_key_is_never_new(client, account, age, outcome):
    aid, auth = account()
    key = _key()
    first = _keyed(client, auth, "reports", REPORT, key)
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute(f"UPDATE request_idempotency SET created_at = NOW() - interval '{age}' WHERE account_id = %s", (aid,))
    again = _keyed(client, auth, "reports", REPORT, key)
    if outcome == "replay":
        assert again.status_code == 202 and again.json()["report_id"] == first.json()["report_id"]
    else:
        assert again.status_code == 410 and again.json()["detail"]["error"] == "idempotency_key_expired"
    assert _count("report_generations", aid) == 1
    assert _count("request_idempotency", aid) == 1, "the old key was dropped or replaced"


def test_a_deleted_schedule_is_gone_and_never_recreated(client, account):
    aid, auth = account()
    key = _key()
    sid = _keyed(client, auth, "schedules", SCHEDULE, key).json()["id"]
    assert client.delete(f"/v1/schedules/{sid}", headers=auth).status_code in (200, 204)
    again = _keyed(client, auth, "schedules", SCHEDULE, key)
    assert again.status_code == 410
    assert again.json()["detail"] == {**again.json()["detail"], "error": "idempotent_resource_gone", "resource_id": sid}
    assert _count("schedules", aid) == 0 and _count("request_idempotency", aid) == 1


def test_an_edited_schedule_replays_as_it_is_now(client, account):
    aid, auth = account()
    key = _key()
    sid = _keyed(client, auth, "schedules", SCHEDULE, key).json()["id"]
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("UPDATE schedules SET name = 'Renamed since' WHERE id = %s", (sid,))
    assert _keyed(client, auth, "schedules", SCHEDULE, key).json()["name"] == "Renamed since"


# ── scope ───────────────────────────────────────────────────────────────────

def test_a_key_belongs_to_its_account(client, account):
    a, auth_a = account()
    b, auth_b = account()
    key = _key()
    ra = _keyed(client, auth_a, "reports", REPORT, key).json()["report_id"]
    rb = _keyed(client, auth_b, "reports", REPORT, key)
    assert rb.status_code == 202 and rb.json()["report_id"] != ra, "account B was handed account A's report"
    assert "Idempotent-Replayed" not in rb.headers
    assert _count("report_generations", a) == 1 and _count("report_generations", b) == 1


def test_a_key_belongs_to_its_endpoint(client, account):
    aid, auth = account()
    key = _key()
    assert _keyed(client, auth, "reports", REPORT, key).status_code == 202
    s = _keyed(client, auth, "schedules", SCHEDULE, key)
    assert s.status_code == 201 and "Idempotent-Replayed" not in s.headers
    assert _count("request_idempotency", aid) == 2


# ── the fingerprint ─────────────────────────────────────────────────────────

def test_the_fingerprint_is_the_validated_request(client, account):
    aid, auth = account()
    key = _key()
    first = _keyed(client, auth, "reports", REPORT, key).json()["report_id"]
    reordered = json.dumps({"lookback_days": 30, "zips": ["91750", "91711"], "report_type": "market_snapshot"})
    assert _keyed(client, auth, "reports", None, key, raw=reordered).json()["report_id"] == first, "key order"
    omitted_default = {k: v for k, v in REPORT.items() if k != "lookback_days"}
    assert _keyed(client, auth, "reports", omitted_default, key).json()["report_id"] == first, "omitted default"
    explicit_null = {**REPORT, "city": None, "filters": None}
    assert _keyed(client, auth, "reports", explicit_null, key).json()["report_id"] == first, "explicit null"
    swapped = {**REPORT, "zips": ["91711", "91750"]}
    assert _keyed(client, auth, "reports", swapped, key).status_code == 409, "array order is part of the request"
    # Top-level field order is fixed by the model; a nested object keeps the
    # client's key order, so the canonical form must sort it.
    key2 = _key()
    nested = _keyed(client, auth, "reports", {**REPORT, "filters": {"minprice": 1, "maxprice": 2}}, key2).json()["report_id"]
    again = _keyed(client, auth, "reports", {**REPORT, "filters": {"maxprice": 2, "minprice": 1}}, key2)
    assert again.status_code == 202 and again.json()["report_id"] == nested, "nested key order"
    assert _count("report_generations", aid) == 2


def _schedule_id(r):
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.mark.parametrize("form", ["null", "empty", "only_nulls"])
def test_schedule_filters_absent_null_and_empty_are_one_request(client, account, form):
    """Codex code review: all of these store `{}` (schedules.py), so they are
    the same request and must hash alike; a real filter is a different one."""
    aid, auth = account()
    key = _key()
    first = _schedule_id(_keyed(client, auth, "schedules", SCHEDULE, key))  # filters omitted
    variant = {"null": None, "empty": {}, "only_nulls": {"minbeds": None, "price_strategy": None}}[form]
    again = _keyed(client, auth, "schedules", {**SCHEDULE, "filters": variant}, key)
    assert again.headers.get("Idempotent-Replayed") == "true", again.text
    assert _schedule_id(again) == first
    real_filter = _keyed(client, auth, "schedules", {**SCHEDULE, "filters": {"minbeds": 2}}, key)
    assert real_filter.status_code == 409, "a real filter is a different request"
    assert _count("schedules", aid) == 1 and _count("request_idempotency", aid) == 1


def test_schedule_filter_key_order_and_values(client, account):
    aid, auth = account()
    key = _key()
    first = _schedule_id(_keyed(client, auth, "schedules", {**SCHEDULE, "filters": {"minprice": 1, "maxprice": 2}}, key))
    same = _keyed(client, auth, "schedules", {**SCHEDULE, "filters": {"maxprice": 2, "minprice": 1, "subtype": None}}, key)
    assert _schedule_id(same) == first
    assert _keyed(client, auth, "schedules", {**SCHEDULE, "filters": {"minprice": 1, "maxprice": 3}}, key).status_code == 409
    assert _count("schedules", aid) == 1


@pytest.mark.parametrize("field", ["filters", "additional_params"])
def test_report_null_and_empty_object_are_one_request(client, account, field):
    """reports.py stores `payload.<field> or {}`: null, omitted and {} are one request."""
    aid, auth = account()
    key = _key()
    first = _keyed(client, auth, "reports", REPORT, key).json()["report_id"]
    for variant in (None, {}):
        again = _keyed(client, auth, "reports", {**REPORT, field: variant}, key)
        assert again.headers.get("Idempotent-Replayed") == "true", (variant, again.text)
        assert again.json()["report_id"] == first
    assert _keyed(client, auth, "reports", {**REPORT, field: {"x": 1}}, key).status_code == 409
    assert _count("report_generations", aid) == 1


# ── nothing half-done ───────────────────────────────────────────────────────

@pytest.mark.parametrize("what, table", [("reports", "report_generations"), ("schedules", "schedules")])
def test_a_failure_after_the_key_is_written_leaves_neither_key_nor_resource(client, account, monkeypatch, what, table):
    from api.services import idempotency
    aid, auth = account()
    real = idempotency.record

    def then_fail(*a, **k):
        real(*a, **k)
        raise RuntimeError("the transaction fails after the key insert")
    monkeypatch.setattr(idempotency, "record", then_fail)
    r = _keyed(client, auth, what, REPORT if what == "reports" else SCHEDULE, _key())
    assert r.status_code == 500
    assert _count(table, aid) == 0 and _count("request_idempotency", aid) == 0


def test_a_refused_request_stores_no_key_and_its_retry_runs_fresh(client, account):
    aid, auth = account(verified=False)
    key = _key()
    refused = _keyed(client, auth, "reports", {**REPORT, "send_email": True, "recipients": ["c@example.com"]}, key)
    assert refused.status_code == 403 and _count("request_idempotency", aid) == 0
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("UPDATE users SET email_verified = true WHERE account_id = %s", (aid,))
    again = _keyed(client, auth, "reports", {**REPORT, "send_email": True, "recipients": ["c@example.com"]}, key)
    assert again.status_code == 202 and "Idempotent-Replayed" not in again.headers
    assert _count("report_generations", aid) == 1


# ── the routes ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("what", ["reports", "schedules"])
def test_the_keyed_route_requires_a_well_formed_key(client, account, what):
    _, auth = account()
    body = REPORT if what == "reports" else SCHEDULE
    missing = client.post(f"/v1/idempotent/{what}", json=body, headers=auth)
    assert missing.status_code == 422 and missing.json()["detail"]["error"] == "idempotency_key_required"
    bad = _keyed(client, auth, what, body, "short")
    assert bad.status_code == 422 and bad.json()["detail"]["error"] == "invalid_idempotency_key"


def test_a_replay_still_needs_a_signed_in_account(client, account):
    _, auth = account()
    key = _key()
    _keyed(client, auth, "reports", REPORT, key)
    anonymous = client.post("/v1/idempotent/reports", json=REPORT, headers={"Idempotency-Key": key})
    assert anonymous.status_code == 401


def test_the_old_routes_ignore_a_key_and_store_nothing(client, account):
    """Unchanged for every other caller: the key means something only on the keyed routes."""
    aid, auth = account()
    key = _key()
    h = {**auth, "Idempotency-Key": key}
    assert client.post("/v1/reports", json=REPORT, headers=h).status_code == 202
    assert client.post("/v1/reports", json=REPORT, headers=h).status_code == 202
    assert _count("report_generations", aid) == 2 and _count("request_idempotency", aid) == 0
