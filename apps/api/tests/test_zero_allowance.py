"""A zero manual allowance refuses new manual work (LR-015, D-375).

Real routes on the migrated database, signed in through /v1/auth/login; only
the report queues, the SiteX lookup and the QR upload are replaced.

On main the resolver kept an override of 0 ("freeze account"), but the gate
measured usage against `max(limit, 1)`: a frozen account was admitted at usage
0 and again at usage 1 (1/1 is inside the 10% grace band). The legacy
evaluator went further and called 0 "Unlimited plan - no restrictions".

What is held here:
- limit 0 refuses at usage 0 and usage 1, for market and property reports,
  through the per-product override and the legacy single override; a refusal
  writes no row, queues nothing and never calls SiteX;
- positive limits, the existing 10% grace, the default, the unlimited sentinel
  and overrides above the plan are unchanged; every seeded plan still admits;
- schedules are a separate capacity: a zero manual allowance does not stop
  creating a schedule (the send side is held in the worker's
  test_durable_schedule_dispatch.py).
"""
import os
import uuid

import pytest

DB = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg")
pytestmark = pytest.mark.skipif(not DB or "fake" in (DB or ""), reason="Set DATABASE_URL to run this test")
PASSWORD = "ZeroAllowance123!"

MARKET = {"report_type": "market_snapshot", "zips": ["91750"], "lookback_days": 30}
PROPERTY = {"report_type": "seller", "property_address": "1 A St", "property_city": "La Verne",
            "property_state": "CA", "property_zip": "91750"}
SCHEDULE = {
    "name": "LR-015 weekly", "report_type": "market_snapshot", "zip_codes": ["91750"],
    "lookback_days": 30, "cadence": "weekly", "weekly_dow": 1, "send_hour": 9, "send_minute": 0,
    "timezone": "America/Los_Angeles", "recipients": ["client@example.com"],
    "include_attachment": True, "active": True,
}
OVERRIDES = ("market_reports_limit_override", "property_reports_limit_override",
             "schedules_limit_override", "monthly_report_limit_override")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def account(client):
    """A fresh verified account; returns (id, auth headers)."""
    made = []

    def make(plan="free", market_used=0, property_used=0, **overrides):
        assert set(overrides) <= set(OVERRIDES), overrides
        aid = str(uuid.uuid4())
        email = f"lr015-{aid[:8]}@example.com"
        cols = ", ".join(overrides)
        with psycopg.connect(DB, autocommit=True) as conn:
            conn.execute(
                "INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active"
                + (", " + cols if cols else "") + ") VALUES (%s, 'LR-015', %s, 'REGULAR', %s, 'active', true"
                + ", %s" * len(overrides) + ")",
                (aid, f"lr015-{aid[:8]}", plan, *overrides.values()))
            conn.execute("INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active) "
                         "VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', true, true)",
                         (aid, aid, email, PASSWORD))
            conn.execute("INSERT INTO account_users (account_id, user_id, role) VALUES (%s, %s, 'OWNER')", (aid, aid))
            for _ in range(market_used):
                conn.execute("INSERT INTO report_generations (account_id, user_id, report_type, status, generated_at) "
                             "VALUES (%s, %s, 'market_snapshot', 'completed', now())", (aid, aid))
            for n in range(property_used):
                conn.execute("INSERT INTO property_reports (account_id, user_id, report_type, theme, property_address, "
                             "property_city, property_state, property_zip, status, short_code, is_active) "
                             "VALUES (%s, %s, 'seller', 2, '1 A St', 'La Verne', 'CA', '91750', 'complete', %s, true)",
                             (aid, aid, f"z{aid[:6]}{n}"))
        made.append(aid)
        r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return aid, {"Authorization": f"Bearer {r.json()['access_token']}"}
    yield make
    with psycopg.connect(DB, autocommit=True) as conn:
        for aid in made:
            for table in ("request_idempotency", "report_generations", "property_reports", "schedules",
                          "account_users", "users"):
                conn.execute(f"DELETE FROM {table} WHERE account_id = %s", (aid,))
            conn.execute("DELETE FROM accounts WHERE id = %s", (aid,))


@pytest.fixture(autouse=True)
def seams(monkeypatch):
    """Record what would have left the building: queued jobs and SiteX calls."""
    from api import worker_client
    from api.routes import property as property_route
    out = {"market": [], "property": [], "sitex": []}
    monkeypatch.setattr(worker_client, "enqueue_generate_report", lambda rid, *a, **k: out["market"].append(rid))
    monkeypatch.setattr(property_route, "enqueue_property_report", lambda rid, *a, **k: out["property"].append(rid))

    async def lookup(address, csz, *a, **k):
        out["sitex"].append(address)
        return None

    async def qr(url, *a, **k):
        return "https://example.invalid/qr.png"
    monkeypatch.setattr(property_route, "lookup_property", lookup)
    monkeypatch.setattr(property_route, "generate_qr_code", qr)
    return out


def _count(table, aid):
    with psycopg.connect(DB) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE account_id = %s", (aid,)).fetchone()[0]


def _market(client, auth):
    return client.post("/v1/reports", json=MARKET, headers=auth)


def _property(client, auth):
    return client.post("/v1/property/reports", json=PROPERTY, headers=auth)


def _refused(r, error, used, limit):
    assert r.status_code == 429, (r.status_code, r.text)
    detail = r.json()["detail"]
    assert detail["error"] == error and detail["used"] == used and detail["limit"] == limit, detail


# ── zero is a freeze ────────────────────────────────────────────────────────

@pytest.mark.parametrize("used", [0, 1])
def test_a_zero_market_allowance_refuses_and_creates_nothing(client, account, seams, used):
    aid, auth = account(market_used=used, market_reports_limit_override=0)
    _refused(_market(client, auth), "market_report_limit_reached", used, 0)
    assert _count("report_generations", aid) == used, "a refused report was written (counted)"
    assert seams["market"] == [], "a refused report was queued (it would have been sent)"


@pytest.mark.parametrize("used", [0, 1])
def test_the_legacy_single_override_of_zero_freezes_market_reports_too(client, account, seams, used):
    aid, auth = account(market_used=used, monthly_report_limit_override=0)
    _refused(_market(client, auth), "market_report_limit_reached", used, 0)
    assert _count("report_generations", aid) == used and seams["market"] == []


@pytest.mark.parametrize("used", [0, 1])
def test_a_zero_property_allowance_refuses_before_sitex(client, account, seams, used):
    aid, auth = account(plan="pro", property_used=used, property_reports_limit_override=0)
    _refused(_property(client, auth), "property_report_limit_reached", used, 0)
    assert _count("property_reports", aid) == used, "a refused property report was written"
    assert seams["property"] == [] and seams["sitex"] == [], "a refused property report spent a lookup or a job"


def test_retrying_a_refusal_stays_refused(client, account, seams):
    aid, auth = account(market_reports_limit_override=0)
    for _ in range(3):
        _refused(_market(client, auth), "market_report_limit_reached", 0, 0)
    assert _count("report_generations", aid) == 0 and seams["market"] == []


# ── everything that is not zero is unchanged ───────────────────────────────

@pytest.mark.parametrize("plan", ["free", "trial", "solo", "starter", "pro", "team", "affiliate", "sponsored_free"])
def test_every_seeded_plan_still_admits_a_first_report(client, account, seams, plan):
    aid, auth = account(plan=plan)
    r = _market(client, auth)
    assert r.status_code == 202, (plan, r.text)
    assert _count("report_generations", aid) == 1 and len(seams["market"]) == 1


@pytest.mark.parametrize("used,admitted", [(0, True), (2, True), (3, True), (4, False)])
def test_the_default_plan_keeps_its_ten_percent_grace(client, account, seams, used, admitted):
    """free = 3: grace_ceiling(3) = 4, so usage 3 is still admitted and 4 is not."""
    aid, auth = account(plan="free", market_used=used)
    r = _market(client, auth)
    if admitted:
        assert r.status_code == 202, r.text
    else:
        _refused(r, "market_report_limit_reached", used, 3)
    assert _count("report_generations", aid) == used + admitted


@pytest.mark.parametrize("used,admitted", [(0, True), (1, True), (2, False)])
def test_an_override_of_one_is_not_zero(client, account, seams, used, admitted):
    """The existing grace: a limit of 1 admits usage 0 and 1 (1/1 < 1.1). Only 0 is a freeze."""
    aid, auth = account(market_used=used, market_reports_limit_override=1)
    r = _market(client, auth)
    assert (r.status_code == 202) is admitted, (used, r.status_code, r.text)


def test_an_override_above_the_plan_is_honoured(client, account, seams):
    aid, auth = account(plan="free", market_used=4, market_reports_limit_override=10)
    assert _market(client, auth).status_code == 202


def test_the_unlimited_sentinel_is_still_unlimited(client, account, seams):
    aid, auth = account(plan="pro", market_used=40)
    assert _market(client, auth).status_code == 202


def test_per_product_overrides_are_independent(client, account, seams):
    """Market frozen, property open: each product reads its own allowance."""
    aid, auth = account(plan="pro", market_reports_limit_override=0, property_reports_limit_override=5)
    _refused(_market(client, auth), "market_report_limit_reached", 0, 0)
    r = _property(client, auth)
    assert r.status_code in (200, 201), r.text
    assert _count("property_reports", aid) == 1 and len(seams["property"]) == 1 and seams["sitex"] == ["1 A St"]


def test_a_zero_manual_allowance_does_not_stop_a_schedule(client, account, seams):
    """November 9: schedules use schedule capacity, never the manual allowance."""
    aid, auth = account(plan="solo", market_reports_limit_override=0, monthly_report_limit_override=0)
    r = client.post("/v1/schedules", json=SCHEDULE, headers=auth)
    assert r.status_code == 201, r.text
    assert _count("schedules", aid) == 1


def test_the_usage_endpoint_reports_a_freeze_as_exceeded(client, account):
    aid, auth = account(market_reports_limit_override=0)
    r = client.get("/v1/account/plan-usage", headers=auth)
    assert r.status_code == 200, r.text
    market = r.json()["limits"]["market_reports"]
    assert market == {"used": 0, "limit": 0, "status": "exceeded", "can_proceed": False}, market
