"""Sponsored pilot gate (November 12): no Stripe checkout for sponsored agents.

A sponsored agent pays nothing, and checkout can still create a second
subscription or a second Stripe customer (LR-011; LR-012 to LR-014 open). Until
those land, POST /v1/billing/checkout refuses a sponsored account before any
Stripe call, and GET /v1/account/plan-usage says so, so the app offers no
Upgrade. Real routes on the migrated database; Stripe is a recorder.

On main a sponsored agent reached `stripe.Customer.create` and
`stripe.checkout.Session.create` (billing.py: "Sponsored agents ... CAN
self-upgrade").
"""
import os
import uuid
from types import SimpleNamespace

import pytest

DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")
PASSWORD = "SponsoredGate123!"


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def account(client):
    made = []

    def make(account_type="REGULAR", sponsored=False, plan="free"):
        aid = str(uuid.uuid4())
        email = f"spg-{aid[:8]}@example.com"
        with psycopg.connect(DB, autocommit=True) as conn:
            sponsor = None
            if sponsored:
                sponsor = str(uuid.uuid4())
                conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active) "
                             "VALUES (%s, 'Sponsor Co', %s, 'INDUSTRY_AFFILIATE', 'affiliate', 'active', true)",
                             (sponsor, f"spg-s-{sponsor[:8]}"))
                made.append(sponsor)
            conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active, "
                         "sponsor_account_id) VALUES (%s, 'Agent', %s, %s, %s, 'active', true, %s)",
                         (aid, f"spg-{aid[:8]}", account_type, plan, sponsor))
            conn.execute("INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active) "
                         "VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', true, true)",
                         (aid, aid, email, PASSWORD))
            conn.execute("INSERT INTO account_users (account_id, user_id, role) VALUES (%s, %s, 'OWNER')", (aid, aid))
        made.insert(0, aid)
        r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return aid, {"Authorization": f"Bearer {r.json()['access_token']}"}
    yield make
    with psycopg.connect(DB, autocommit=True) as conn:
        for aid in made:
            conn.execute("DELETE FROM account_users WHERE account_id = %s", (aid,))
            conn.execute("DELETE FROM users WHERE account_id = %s", (aid,))
            conn.execute("UPDATE accounts SET sponsor_account_id = NULL WHERE id = %s", (aid,))
        for aid in made:
            conn.execute("DELETE FROM accounts WHERE id = %s", (aid,))


@pytest.fixture
def stripe(monkeypatch):
    """Configured Stripe whose every call is recorded instead of sent."""
    from api.routes import billing
    calls = []

    class StripeError(Exception):
        pass

    fake = SimpleNamespace(
        error=SimpleNamespace(StripeError=StripeError),
        Customer=SimpleNamespace(create=lambda **kw: calls.append(("Customer.create", kw)) or SimpleNamespace(id="cus_test")),
        checkout=SimpleNamespace(Session=SimpleNamespace(
            create=lambda **kw: calls.append(("Session.create", kw)) or SimpleNamespace(url="https://checkout.test/s"))),
    )
    monkeypatch.setattr(billing, "stripe", fake)
    monkeypatch.setattr(billing, "validate_stripe_config", lambda: (True, []))
    monkeypatch.setattr(billing, "get_plan_by_slug",
                        lambda cur, slug: {"plan_slug": slug, "plan_name": "Growth", "stripe_price_id": "price_test"})
    return calls


def _customer_id(aid):
    with psycopg.connect(DB) as conn:
        return conn.execute("SELECT stripe_customer_id FROM accounts WHERE id = %s", (aid,)).fetchone()[0]


def test_a_sponsored_agent_is_refused_before_any_stripe_call(client, account, stripe):
    aid, auth = account(sponsored=True, plan="sponsored_free")
    r = client.post("/v1/billing/checkout", json={"plan_slug": "starter"}, headers=auth)
    assert r.status_code == 403, r.text
    assert r.json()["detail"] == {"error": "sponsored_checkout_paused",
                                  "message": "Upgrades aren't available on sponsored accounts right now."}
    assert stripe == [], "a sponsored account reached Stripe"
    assert _customer_id(aid) is None, "a Stripe customer was recorded for a refused checkout"


def test_retrying_stays_refused(client, account, stripe):
    aid, auth = account(sponsored=True, plan="sponsored_free")
    for _ in range(3):
        assert client.post("/v1/billing/checkout", json={"plan_slug": "pro"}, headers=auth).status_code == 403
    assert stripe == []


def test_an_unsponsored_agent_still_reaches_checkout(client, account, stripe):
    aid, auth = account()
    r = client.post("/v1/billing/checkout", json={"plan_slug": "starter"}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json() == {"url": "https://checkout.test/s"}
    assert [name for name, _ in stripe] == ["Customer.create", "Session.create"]


def test_a_company_account_keeps_its_own_refusal(client, account, stripe):
    aid, auth = account(account_type="TITLE_COMPANY", plan="team")
    r = client.post("/v1/billing/checkout", json={"plan_slug": "starter"}, headers=auth)
    assert r.status_code == 400 and r.json()["detail"]["error"] == "invalid_account_type", r.text
    assert stripe == []


@pytest.mark.parametrize("kind,expected", [
    ({"sponsored": True, "plan": "sponsored_free"}, False),
    ({}, True),
    ({"account_type": "INDUSTRY_AFFILIATE", "plan": "affiliate"}, False),
])
def test_plan_usage_reports_the_same_rule(client, account, kind, expected):
    aid, auth = account(**kind)
    r = client.get("/v1/account/plan-usage", headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["account"]["checkout_available"] is expected


@pytest.mark.parametrize("account_type,sponsor,flag,expected", [
    ("REGULAR", None, False, True),
    ("REGULAR", "s", False, False),
    ("REGULAR", "s", True, True),          # lifting the gate is one constant
    ("TITLE_COMPANY", None, True, False),
    ("INDUSTRY_AFFILIATE", None, True, False),
])
def test_the_rule(monkeypatch, account_type, sponsor, flag, expected):
    from api.config import billing as config
    monkeypatch.setattr(config, "SPONSORED_SELF_CHECKOUT", flag)
    assert config.checkout_available(account_type, sponsor) is expected
