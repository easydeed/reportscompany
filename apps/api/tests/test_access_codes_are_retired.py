"""Access codes are retired: no property page can be locked (D-359).

An agent could set an access code on a property page. The public page then
showed "Access Code Required" with no field to enter it, and the lead route
refused every lead that did not carry the code, which no form ever sent. So a
code silently turned the lead page off for everyone, the agent included.

Decided 2026-11-05: remove the setting rather than build code entry. A code
already stored is left in the database and ignored.

Red on main: the page with a stored code reports `requires_access_code: true`,
its leads get 403, and the settings API accepts a new code.
"""
import os
import uuid
from pathlib import Path

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")

REPO = Path(__file__).resolve().parents[3]
PASSWORD = "AccessCodeRetired123!"
STORED = "4821"
WORDING = "I consent to being contacted about this property and related services."


@pytest.fixture
def page():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the access-code test")
    tag = uuid.uuid4().hex[:7]
    acc, report = str(uuid.uuid4()), str(uuid.uuid4())
    email, code = f"retired-{tag}@example.com", f"k{tag}"
    with psycopg.connect(DB_URL) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active) "
                     "VALUES (%s, 'Access Code Test', %s, 'REGULAR', 'free', 'active', true)", (acc, f"code-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active, "
                     "first_name, last_name) VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', true, true, "
                     "'Dana', 'Ortiz')", (acc, acc, email, PASSWORD))
        conn.execute("INSERT INTO account_users (account_id, user_id, role, created_at) "
                     "VALUES (%s, %s, 'OWNER', now())", (acc, acc))
        conn.execute("INSERT INTO property_reports (id, account_id, user_id, report_type, theme, property_address, "
                     "property_city, property_state, property_zip, status, short_code, is_active, access_code) "
                     "VALUES (%s, %s, %s, 'seller', 2, '1 A St', 'La Verne', 'CA', '91750', 'complete', %s, true, %s)",
                     (report, acc, acc, code, STORED))
    yield {"account": acc, "report": report, "code": code, "email": email}
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM leads WHERE account_id = %s", (acc,))
        conn.execute("DELETE FROM lead_rate_limits WHERE property_report_id = %s", (report,))
        conn.execute("DELETE FROM property_reports WHERE id = %s", (report,))
        conn.execute("DELETE FROM account_users WHERE account_id = %s", (acc,))
        conn.execute("DELETE FROM users WHERE id = %s", (acc,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    # The lead route records the client IP in an inet column; TestClient's
    # default host ("testclient") is not one.
    return TestClient(app, raise_server_exceptions=False, client=("198.51.100.9", 50000))


def _stored_code(report):
    with psycopg.connect(DB_URL) as conn:
        return conn.execute("SELECT access_code FROM property_reports WHERE id = %s", (report,)).fetchone()[0]


def _leads(account):
    with psycopg.connect(DB_URL) as conn:
        return conn.execute("SELECT count(*) FROM leads WHERE account_id = %s", (account,)).fetchone()[0]


def _capture(client, code, **extra):
    body = {"short_code": code, "name": "Walkthrough Homeowner", "email": f"h{uuid.uuid4().hex[:6]}@example.com",
            "consent_given": True, "consent_text": WORDING, "source": "qr_scan", **extra}
    return client.post("/v1/leads/capture", json=body)


def _auth(client, email):
    r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_a_page_with_a_stored_code_is_not_locked(client, page):
    r = client.get(f"/v1/property/public/{page['code']}")
    assert r.status_code == 200, r.text
    assert r.json()["requires_access_code"] is False


def test_its_lead_form_takes_a_lead_with_no_code(client, page):
    r = _capture(client, page["code"])
    assert r.status_code == 200, r.text
    assert _leads(page["account"]) == 1


def test_a_wrong_code_is_ignored_too(client, page):
    r = _capture(client, page["code"], access_code="not-the-code")
    assert r.status_code == 200, r.text
    assert _leads(page["account"]) == 1


def test_the_settings_api_refuses_a_new_code_and_leaves_the_stored_one(client, page):
    auth = _auth(client, page["email"])
    r = client.patch(f"/v1/property/reports/{page['report']}/settings", headers=auth,
                     json={"access_code": "9999"})
    assert r.status_code == 422, r.text
    assert "no longer supported" in r.json()["detail"]
    assert _stored_code(page["report"]) == STORED


def test_other_settings_still_save_and_leave_the_stored_code(client, page):
    auth = _auth(client, page["email"])
    r = client.patch(f"/v1/property/reports/{page['report']}/settings", headers=auth,
                     json={"max_leads": 25})
    assert r.status_code == 200, r.text
    assert r.json()["max_leads"] == 25
    assert _stored_code(page["report"]) == STORED, "stored codes are left as they are"


def test_the_settings_page_offers_no_access_code():
    src = (REPO / "apps/web/app/app/property/[id]/settings/page.tsx").read_text(encoding="utf-8")
    assert "Access Code" not in src, "the settings page still shows an access-code field"
    assert "access_code:" not in src.split("body: JSON.stringify(", 1)[1].split(")", 1)[0], \
        "the settings page still sends an access code"
