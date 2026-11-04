"""D-352, D-342 — no lead is saved without consent, and a lead keeps the words it agreed to.

The property report page (`/p/{code}`) had an optional consent box: the form
did not check it, `POST /v1/leads/capture` defaulted `consent_given` to false,
and the lead was stored and handed to the agent either way. The Home Value
Page required the box in the browser but its endpoint accepted a request
without it. Neither stored the sentence beside the box (`leads.consent_text`,
migration 0063).

Red on main: a capture with `consent_given: false` returns 200 and writes a
row; `consent_text` is neither accepted nor stored.
"""
import os
import uuid

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")

P_WORDING = "I consent to being contacted about this property and related services."
CMA_WORDING = "I agree to receive my report and to be contacted by Dana Ortiz about my property."


@pytest.fixture
def agent():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the consent tests")
    tag = uuid.uuid4().hex[:8]
    account, user, report = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    code, agent_code = f"c{tag}"[:8], f"a{tag}"[:8]
    with psycopg.connect(DB_URL) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'Consent Test', %s, 'REGULAR', 'free')", (account, f"consent-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name, agent_code) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz', %s)",
                     (user, account, f"agent-{tag}@example.com", agent_code))
        conn.execute(
            "INSERT INTO property_reports (id, account_id, user_id, report_type, theme, property_address, "
            "property_city, property_state, property_zip, status, short_code, is_active) "
            "VALUES (%s, %s, %s, 'seller', 2, '1358 5th Street', 'La Verne', 'CA', '91750', "
            "'complete', %s, TRUE)", (report, account, user, code))
    yield {"account": account, "report": report, "code": code, "agent_code": agent_code}
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM leads WHERE account_id = %s", (account,))
        conn.execute("DELETE FROM lead_rate_limits WHERE property_report_id = %s", (report,))
        conn.execute("DELETE FROM consumer_reports WHERE agent_id = %s", (user,))
        conn.execute("DELETE FROM property_reports WHERE id = %s", (report,))
        conn.execute("DELETE FROM users WHERE id = %s", (user,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (account,))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    # A real address: the Home Value Page rate-limits on `inet`, and the default
    # TestClient host ("testclient") is not one.
    return TestClient(app, raise_server_exceptions=False, client=("198.51.100.7", 50000))


def _leads(account):
    with psycopg.connect(DB_URL) as conn:
        return conn.execute("SELECT consent_given, consent_text, source FROM leads "
                            "WHERE account_id = %s", (account,)).fetchall()


def _capture(client, code, **extra):
    body = {"short_code": code, "name": "Walkthrough Homeowner",
            "email": f"h{uuid.uuid4().hex[:6]}@example.com", "source": "qr_scan", **extra}
    return client.post("/v1/leads/capture", json=body)


def test_the_property_page_refuses_a_lead_without_consent(client, agent):
    r = _capture(client, agent["code"], consent_given=False, consent_text=P_WORDING)
    assert r.status_code == 422, r.text
    assert "Consent" in r.json()["detail"]
    assert _leads(agent["account"]) == [], "a lead was saved without consent"


def test_the_property_page_stores_the_wording_agreed_to(client, agent):
    r = _capture(client, agent["code"], consent_given=True, consent_text=P_WORDING)
    assert r.status_code == 200, r.text
    assert _leads(agent["account"]) == [(True, P_WORDING, "qr_scan")]


def _cma(client, agent_code, monkeypatch, **extra):
    import celery
    monkeypatch.setattr(celery.current_app, "send_task", lambda *a, **k: None)
    body = {"phone": "6265550199", "delivery_method": "sms", "property_apn": "8381-021-001",
            "property_fips": "06037", "property_address": "1358 5th Street",
            "property_city": "La Verne", "property_state": "CA", "property_zip": "91750", **extra}
    return client.post(f"/v1/cma/{agent_code}/request", json=body)


def test_the_home_value_page_refuses_a_request_without_consent(client, agent, monkeypatch):
    r = _cma(client, agent["agent_code"], monkeypatch, consent_given=False)
    assert r.status_code == 422, r.text
    assert _leads(agent["account"]) == []


def test_the_home_value_page_stores_the_wording_agreed_to(client, agent, monkeypatch):
    r = _cma(client, agent["agent_code"], monkeypatch, consent_given=True, consent_text=CMA_WORDING)
    assert r.status_code == 200, r.text
    assert _leads(agent["account"]) == [(True, CMA_WORDING, "cma_page")]
