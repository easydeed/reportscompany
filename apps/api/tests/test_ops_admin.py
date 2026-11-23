"""LR-027 slice 4: the admin ops routes (design #317 rev 3, sections 5 and 7).

Real PostgreSQL, real login, a disposable Redis database for the test request.
"""
import os
import uuid

import psycopg
import pytest

DB_URL = os.getenv("DATABASE_URL")
PASSWORD = "ops-admin-test-pass-1"
pytestmark = pytest.mark.skipif(not DB_URL, reason="DATABASE_URL (a disposable local database) is needed")


def _user(cur, email, *, platform_admin):
    uid = str(uuid.uuid4())
    cur.execute("""INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active, created_at, updated_at)
                   VALUES (%s, 'Ops Test', %s, 'REGULAR', 'free', 'active', true, now(), now())""",
                (uid, f"ops-test-{uid[:8]}"))
    cur.execute("""INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active,
                                      is_platform_admin, first_name, created_at, updated_at)
                   VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', true, true, %s, 'Ops', now(), now())""",
                (uid, uid, email, PASSWORD, platform_admin))
    cur.execute("INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s, %s, 'OWNER', now())",
                (uid, uid))
    return uid


@pytest.fixture
def people():
    suffix = uuid.uuid4().hex[:8]
    emails = {"admin": f"ops-admin-{suffix}@example.com", "agent": f"ops-agent-{suffix}@example.com"}
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        ids = {"admin": _user(cur, emails["admin"], platform_admin=True),
               "agent": _user(cur, emails["agent"], platform_admin=False)}
        cur.execute("DELETE FROM ops_alerts")
        conn.commit()
    yield emails, ids
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM ops_alerts")
        for uid in ids.values():
            cur.execute("DELETE FROM account_users WHERE user_id = %s", (uid,))
            cur.execute("DELETE FROM users WHERE id = %s", (uid,))
            cur.execute("DELETE FROM accounts WHERE id = %s", (uid,))
        conn.commit()


@pytest.fixture
def r(monkeypatch):
    redis = pytest.importorskip("redis")
    url = os.getenv("TEST_REDIS_URL")
    if not url:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is not set")
        pytest.skip("Set TEST_REDIS_URL to a disposable Redis database")
    conn = redis.from_url(url, decode_responses=True)
    from api.routes import ops_admin
    conn.delete(ops_admin.TEST_ALERT_KEY)
    monkeypatch.setattr(ops_admin, "_redis", lambda: conn)
    yield conn
    conn.delete(ops_admin.TEST_ALERT_KEY)


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


def auth(client, email):
    resp = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_only_platform_admins_reach_the_ops_routes(client, people, r):
    emails, _ = people
    agent = auth(client, emails["agent"])
    assert client.post("/v1/admin/ops/test-alert", headers=agent).status_code == 403
    assert client.get("/v1/admin/ops/alerts", headers=agent).status_code == 403
    assert client.post("/v1/admin/ops/notifications/1/resolution", headers=agent,
                       json={"resolution": "received", "evidence": "x" * 5}).status_code == 403
    assert client.post("/v1/admin/ops/test-alert").status_code == 401
    assert r.get("ops:test_alert:requested") is None                     # nothing was requested


def test_a_test_alert_is_one_pending_request_for_the_monitor(client, people, r):
    emails, _ = people
    admin = auth(client, emails["admin"])
    first = client.post("/v1/admin/ops/test-alert", headers=admin)
    assert first.status_code == 202
    assert r.get("ops:test_alert:requested") == first.json()["request_id"]
    assert 0 < r.ttl("ops:test_alert:requested") <= 3600
    again = client.post("/v1/admin/ops/test-alert", headers=admin)
    assert again.status_code == 409                                       # one at a time
    assert r.get("ops:test_alert:requested") == first.json()["request_id"]


def seed(states):
    """One incident with one notification row per (state, resolution)."""
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO ops_alerts (key) VALUES ('schedule_overdue') RETURNING id")
        alert = cur.fetchone()[0]
        made = []
        for i, state in enumerate(states):
            cur.execute("""INSERT INTO ops_alert_notifications (alert_id, event, channel, state, attempts)
                           VALUES (%s, %s, 'email', %s, 1) RETURNING id""", (alert, f"renotify:{i}", state))
            made.append(cur.fetchone()[0])
        conn.commit()
    return made


def test_the_alert_list_shows_open_incidents_and_what_needs_reconciliation(client, people, r):
    emails, _ = people
    admin = auth(client, emails["admin"])
    unknown, accepted, not_sent = seed(["unknown", "accepted", "not_sent"])
    body = client.get("/v1/admin/ops/alerts", headers=admin).json()
    assert [a["key"] for a in body["open_alerts"]] == ["schedule_overdue"]
    assert [n["id"] for n in body["needs_reconciliation"]] == [unknown]
    assert {n["id"] for n in body["recent"]} == {unknown, accepted, not_sent}
    assert "@" not in str(body)                                           # no destinations exist to leak


def test_an_operator_records_receipt_once_with_evidence(client, people, r):
    emails, ids = people
    admin = auth(client, emails["admin"])
    unknown, accepted, not_sent = seed(["unknown", "accepted", "not_sent"])
    url = "/v1/admin/ops/notifications/{}/resolution"
    assert client.post(url.format(unknown), headers=admin,
                       json={"resolution": "received", "evidence": "  "}).status_code == 422
    ok = client.post(url.format(unknown), headers=admin,
                     json={"resolution": "not_received", "evidence": "Not in inbox or spam at 14:05"})
    assert ok.status_code == 200 and ok.json()["resolution"] == "not_received"
    again = client.post(url.format(unknown), headers=admin, json={"resolution": "received", "evidence": "later"})
    assert again.status_code == 409                                        # first resolution wins
    assert client.post(url.format(accepted), headers=admin,
                       json={"resolution": "received", "evidence": "Seen on phone, SID SM-1"}).status_code == 200
    refused = client.post(url.format(not_sent), headers=admin, json={"resolution": "received", "evidence": "n/a"})
    assert refused.status_code == 409 and "not_sent" in refused.json()["detail"]
    assert client.post(url.format(999999999), headers=admin,
                       json={"resolution": "received", "evidence": "n/a"}).status_code == 404
    with psycopg.connect(DB_URL) as conn:
        row = conn.execute("SELECT resolution, resolution_evidence FROM ops_alert_notifications WHERE id = %s",
                           (unknown,)).fetchone()
    assert row[0] == "not_received" and row[1].startswith("Not in inbox or spam at 14:05")
    assert f"user:{ids['admin']}" in row[1]
    body = client.get("/v1/admin/ops/alerts", headers=admin).json()
    assert body["needs_reconciliation"] == []
