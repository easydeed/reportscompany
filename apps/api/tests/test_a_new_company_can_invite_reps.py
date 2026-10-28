"""
A title company with no branding set up can invite reps and save its brand.

THE DEFECT. Every company starts with no `affiliate_branding` row: the row is
created by its first branding save. `copy_branding_to_child`, which every rep
invite calls, fell back to an INSERT omitting `brand_display_name` — NOT NULL,
no default — and its `except` retried another INSERT omitting it, inside the
transaction the first failure had already aborted. So every rep invite from a
company that had not saved its branding first was a 500. Pacific Coast Title
was unaffected only because it had a row; the next company would have hit it
on day one.

The company's own first save had the same hole: an upsert that inserts the
body's `brand_display_name`, which the branding form may leave empty.

THE CLAIMS, for a company with no branding row:
  1. Inviting a rep succeeds, and the rep's branding row carries the
     company's name.
  2. Saving branding without a display name succeeds, names the brand after
     the company, and cascades to the rep.

`scripts/regressions/new_company_branding.json` puts each hole back; each goes red.
"""
import os
import uuid

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")
pytestmark = pytest.mark.skipif(not DB_URL, reason="Set DATABASE_URL to run this test")

PASSWORD = "NewCompany123!"


@pytest.fixture
def company():
    tag = uuid.uuid4().hex[:8]
    cid = str(uuid.uuid4())
    email = f"newco-{tag}@test-tenant.example.com"
    with psycopg.connect(DB_URL) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'Day One Title', %s, 'TITLE_COMPANY', 'affiliate')", (cid, f"day-one-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active) "
                     "VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', true, true)",
                     (cid, cid, email, PASSWORD))
        conn.execute("INSERT INTO account_users (account_id, user_id, role) VALUES (%s, %s, 'OWNER')", (cid, cid))
        assert conn.execute("SELECT 1 FROM affiliate_branding WHERE account_id = %s", (cid,)).fetchone() is None
    yield {"id": cid, "email": email, "tag": tag}
    with psycopg.connect(DB_URL) as conn:
        ids = [r[0] for r in conn.execute(
            "SELECT id FROM accounts WHERE id = %s OR parent_account_id = %s", (cid, cid)).fetchall()]
        conn.execute("DELETE FROM signup_tokens WHERE account_id = ANY(%s)", (ids,))
        conn.execute("DELETE FROM email_log WHERE account_id = ANY(%s)", (ids,))
        conn.execute("UPDATE accounts SET parent_account_id = NULL WHERE id = ANY(%s)", (ids,))
        conn.execute("DELETE FROM accounts WHERE id = ANY(%s)", (ids,))


@pytest.fixture
def client(monkeypatch):
    import api.routes.company as company_routes
    monkeypatch.setattr(company_routes, "send_role_invite_email", lambda *a, **k: None)
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def _auth(client, email):
    r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _invite(client, company, auth):
    return client.post("/v1/company/invite-rep", headers=auth, json={
        "name": "Day One Rep", "email": f"newco-rep-{company['tag']}@test-tenant.example.com",
        "first_name": "Dee", "last_name": "One"})


def test_a_company_with_no_branding_can_invite_a_rep(client, company):
    r = _invite(client, company, _auth(client, company["email"]))
    assert r.status_code == 200, r.text
    with psycopg.connect(DB_URL) as conn:
        row = conn.execute("SELECT brand_display_name, branding_override FROM affiliate_branding "
                           "WHERE account_id = %s", (r.json()["rep_account_id"],)).fetchone()
    assert row == ("Day One Title", False), row


def test_a_company_with_no_branding_can_save_it_without_a_display_name(client, company):
    auth = _auth(client, company["email"])
    rep = _invite(client, company, auth).json()["rep_account_id"]
    r = client.patch("/v1/company/branding", headers=auth, json={"primary_color": "#0E7490"})
    assert r.status_code == 200, r.text
    with psycopg.connect(DB_URL) as conn:
        own = conn.execute("SELECT brand_display_name, primary_color FROM affiliate_branding "
                           "WHERE account_id = %s", (company["id"],)).fetchone()
        reps = conn.execute("SELECT brand_display_name, primary_color FROM affiliate_branding "
                            "WHERE account_id = %s", (rep,)).fetchone()
    assert own == ("Day One Title", "#0E7490"), own
    assert reps == ("Day One Title", "#0E7490"), "the save did not cascade to the rep"
