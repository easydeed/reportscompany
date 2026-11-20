"""D-399: the platform-admin account switch controls access and scheduled work."""
import json
import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from api.auth import hash_password
from test_durable_schedule_dispatch import R1, R2, _q, db, sendgrid, world  # noqa: F401


@pytest.fixture
def people(world, monkeypatch):
    from api import db as api_db
    from api.main import app
    from api.middleware.authn import RateLimitMiddleware
    from worker.email import send

    # Each TestClient lifespan closes its pool at shutdown.
    monkeypatch.setattr(api_db, "_pool", None)
    monkeypatch.setattr(RateLimitMiddleware, "_redis", lambda self, op, *args, default=None: default)
    # Exercise recipient resolution, suppression, send claims and HTTP delivery
    # with a deterministic body. Template rendering has its own suite.
    monkeypatch.setattr(send, "schedule_email_html", lambda **kw: f"<a href='{kw['unsubscribe_url']}'>Unsubscribe</a>")
    target = world.account
    sponsor = str(uuid.uuid4())
    password = "OnlyForThisFixture123!"
    hashed = hash_password(password)
    admin_email = f"{sponsor}@example.com"
    _q(world.db, "INSERT INTO accounts (id, name, slug, account_type) "
                 "VALUES (%s, 'Test sponsor', %s, 'INDUSTRY_AFFILIATE')", sponsor, sponsor)
    _q(world.db, "INSERT INTO users (account_id, email, password_hash, is_platform_admin) "
                 "VALUES (%s, %s, %s, TRUE)", sponsor, admin_email, hashed)
    _q(world.db, "UPDATE accounts SET sponsor_account_id = %s WHERE id = %s", sponsor, world.account)
    email = _q(world.db, "UPDATE users SET password_hash = %s WHERE id = %s RETURNING email",
               hashed, world.user)[0][0]
    disabled = f"disabled-{sponsor}@example.com"
    _q(world.db, "INSERT INTO users (account_id, email, password_hash, is_active, created_at) "
                 "VALUES (%s, %s, %s, FALSE, now() - interval '1 year')", world.account, disabled, hashed)
    with TestClient(app, base_url="https://testserver") as client:
        def login(address):
            return client.post("/v1/auth/login", json={"email": address, "password": password})

        admin = login(admin_email)
        assert admin.status_code == 200, admin.text
        admin_headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}

        def activate(active):
            result = client.patch(f"/v1/admin/accounts/{target}", params={"is_active": active},
                                  headers=admin_headers)
            assert result.status_code == 200, result.text
            assert result.json()["is_active"] is active

        yield client, login, activate, sponsor, email, disabled
    _q(world.db, "DELETE FROM accounts WHERE id IN (%s,%s)", target, sponsor)


def test_login_session_and_keys_follow_account_state(world, people):
    client, login, activate, sponsor, email, disabled = people
    session = login(email)
    assert session.status_code == 200
    headers = {"Authorization": f"Bearer {session.json()['access_token']}"}
    key = client.post("/v1/api-keys", headers=headers, json={"name": "fixture"}).json()["api_key"]
    key_headers = {"Authorization": f"Bearer {key}"}
    revoked = client.post("/v1/api-keys", headers=headers, json={"name": "revoked"}).json()
    assert client.delete(f"/v1/api-keys/{revoked['id']}", headers=headers).status_code == 204
    assert client.get("/v1/api-keys", headers=key_headers).status_code == 200
    activate(False)
    assert login(email).status_code == 401
    assert client.get("/v1/me").status_code == 401  # existing browser cookie
    assert client.get("/v1/me", headers=headers).status_code == 401
    assert client.get("/v1/api-keys", headers=key_headers).status_code == 401

    # A real secondary membership remains usable while the primary is suspended.
    _q(world.db, "INSERT INTO account_users (account_id, user_id, role) VALUES (%s,%s,'MEMBER')",
       sponsor, world.user)
    assert login(email).status_code == 200
    context = client.get("/v1/me").json()
    assert (context["account_id"], context["user_id"]) == (sponsor, world.user)
    assert client.get("/v1/api-keys", headers=key_headers).status_code == 401
    activate(True)
    assert client.get("/v1/me", headers=headers).json()["account_id"] == world.account
    assert client.get("/v1/api-keys", headers=key_headers).status_code == 200
    assert client.get("/v1/api-keys", headers={"Authorization": f"Bearer {revoked['api_key']}"}).status_code == 401
    assert login(disabled).status_code == 401


def test_suspended_schedule_skips_handoff_then_resumes(world, people, sendgrid):
    _, _, activate, _, _, _ = people
    pending = world.tick()
    assert world.publishes(pending) == 1
    activate(False)
    assert world.deliver(pending)["reason"] == "cancelled"
    _q(world.db, "UPDATE schedules SET next_run_at = now() WHERE id = %s", world.schedule)
    world.tick()
    assert world.published == [pending]
    assert sendgrid.posts == []
    assert _q(world.db, "SELECT status, error FROM email_log WHERE schedule_id = %s AND report_id IS NULL",
              world.schedule) == [("suppressed", world.sr.MSG_DEACTIVATED)]
    assert _q(world.db, "SELECT active, next_run_at > now() FROM schedules WHERE id = %s",
              world.schedule) == [(True, True)]

    activate(True)
    _q(world.db, "UPDATE schedules SET next_run_at = now() WHERE id = %s", world.schedule)
    resumed = world.tick()
    assert resumed != pending
    world.deliver(resumed)
    assert sorted(sendgrid.posts) == [R1, R2]


def test_sponsored_recipient_uses_active_account_and_person(world, people, sendgrid, monkeypatch):
    _, _, activate, sponsor, email, _ = people

    typed = json.dumps({"type": "sponsored_agent", "id": world.account})
    group = _q(world.db, "INSERT INTO contact_groups (account_id, name) VALUES (%s,'Agents') RETURNING id",
               sponsor)[0][0]
    _q(world.db, "INSERT INTO contact_group_members (account_id, group_id, member_type, member_id) "
                 "VALUES (%s,%s,'sponsored_agent',%s)", sponsor, group, world.account)
    grouped = json.dumps({"type": "group", "id": str(group)})
    with psycopg.connect(world.db, autocommit=True) as conn, conn.cursor() as cur:
        resolve = world.tasks.resolve_recipients_to_emails
        assert set(resolve(cur, sponsor, [typed, R1])) == {email, R1}
        assert resolve(cur, sponsor, [grouped]) == [email]
        activate(False)
        assert resolve(cur, sponsor, [typed, grouped, R1]) == [R1]

    # A different, active account sends to its stored group plus one manual recipient.
    _q(world.db, "UPDATE users SET email_verified = TRUE WHERE account_id = %s", sponsor)
    _q(world.db, "UPDATE schedules SET account_id = %s, recipients = %s WHERE id = %s",
       sponsor, [grouped, R1], world.schedule)
    monkeypatch.setattr(world, "account", sponsor)
    world.deliver(world.tick())
    assert sendgrid.posts == [R1]
    activate(True)
    _q(world.db, "UPDATE schedules SET next_run_at = now() WHERE id = %s", world.schedule)
    world.deliver(world.tick())
    assert sorted(sendgrid.posts) == sorted([R1, R1, email])


def test_legacy_scheduled_message_rechecks_suspension(world, people, sendgrid):
    _, _, activate, _, _, _ = people
    run_id = world.tick()
    _q(world.db, "UPDATE schedule_runs SET recovery_tracked = FALSE WHERE report_run_id = %s", run_id)
    activate(False)
    assert world.deliver(run_id)["reason"] == "cancelled"
    assert world.run(run_id)["error"] == world.sr.MSG_DEACTIVATED
    assert sendgrid.posts == []
