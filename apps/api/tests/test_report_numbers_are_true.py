"""D-106 and D-168 on the API side (pre-pilot, Jerry 2026-11-09).

D-106  The comps route and the SimplyRETS normaliser read `bathsFull` alone, so
       2 full baths and a powder room read "2". Convention: halves count 0.5.
D-168  The comps route wrote 0 for a missing bedroom/bath/living-area count, and
       `/r` filled every missing comp number with 0, so the homeowner saw
       "0 Beds" for a comp whose record has no bedroom count.

Red on main: every test below fails there.
"""
import json
import os
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest

from test_comp_close_window import _call, mock_auth, _no_database  # noqa: F401

REPO = Path(__file__).resolve().parents[3]


def _ago(days):
    return (date.today() - timedelta(days=days)).isoformat()


def _row(mls_id, prop):
    return {"mlsId": mls_id, "mls": {"status": "Closed"}, "listPrice": 700000,
            "sales": {"closeDate": _ago(20), "closePrice": 690000},
            "address": {"full": f"{mls_id} Comp St"}, "geo": {"lat": 34.1008, "lng": -117.7678},
            "property": dict(type="RES", **prop)}


# ── the comps the agent picks from ──────────────────────────────────────────

def test_the_comps_route_counts_half_baths_and_invents_no_zeros(mock_auth):
    _, body = _call("Closed", [
        _row("FULL", {"bedrooms": 3, "bathsFull": 2, "bathsHalf": 1, "area": 1500}),
        _row("BARE", {}),
    ])
    by = {c["mls_id"]: c for c in body["comparables"]}
    assert by["FULL"]["bathrooms"] == 2.5
    assert (by["BARE"]["bedrooms"], by["BARE"]["bathrooms"], by["BARE"]["sqft"]) == (None, None, None)


def test_the_simplyrets_normaliser_counts_half_baths():
    from api.services.simplyrets import baths_total, normalize_listing
    assert normalize_listing(_row("N", {"bathsFull": 1, "bathsHalf": 1}))["bathrooms"] == 1.5
    assert baths_total({}) is None


# ── what the homeowner sees on /r ───────────────────────────────────────────

STORED = [
    # written after the fix: missing counts are absent
    {"address": "1 Missing St", "status": "Closed", "close_price": 610000, "price": 610000,
     "close_date": _ago(30)},
    # written before the fix: missing counts were stored as 0
    {"address": "2 Zeroed St", "status": "Closed", "close_price": 640000, "price": 640000,
     "bedrooms": 0, "bathrooms": 0, "sqft": 0, "distance_miles": 0, "close_date": _ago(40)},
    # a complete record keeps every value
    {"address": "3 Whole St", "status": "Closed", "close_price": 655000, "price": 655000,
     "bedrooms": 3, "bathrooms": 2.5, "sqft": 1500, "distance_miles": 0.4, "days_on_market": 0,
     "close_date": _ago(50)},
]


def test_r_prints_no_zero_for_a_missing_count():
    psycopg = pytest.importorskip("psycopg")
    db = os.getenv("DATABASE_URL")
    if not db:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL")
    from fastapi.testclient import TestClient
    from api.main import app
    tag = uuid.uuid4().hex[:8]
    acc, agent, rid = (str(uuid.uuid4()) for _ in range(3))
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'D-168', %s, 'REGULAR', 'free')", (acc, f"d168-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (agent, acc, f"d168-{tag}@example.com"))
        conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, "
                     "property_address, property_city, property_state, property_zip, "
                     "property_data, comparables, status) VALUES (%s, %s, 'D18', '6265550123', "
                     "'1358 5th Street', 'La Verne', 'CA', '91750', %s, %s, 'sent')",
                     (rid, agent, json.dumps({"sqft": 786}), json.dumps(STORED)))
    try:
        r = TestClient(app, raise_server_exceptions=False).get(f"/v1/r/{rid}/data")
        assert r.status_code == 200, r.text
        by = {c["address"]: c for c in r.json()["comparables"]}
        for address in ("1 Missing St", "2 Zeroed St"):
            c = by[address]
            assert (c["bedrooms"], c["bathrooms"], c["sqft"], c["distance_miles"]) == (None, None, None, None), (
                f"{address} shows {c}")
        whole = by["3 Whole St"]
        assert (whole["bedrooms"], whole["bathrooms"], whole["sqft"]) == (3, 2.5, 1500)
        assert whole["distance_miles"] == 0.4
    finally:
        with psycopg.connect(db, autocommit=True) as conn:
            conn.execute("DELETE FROM report_analytics WHERE report_id = %s", (rid,))
            conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
            conn.execute("DELETE FROM users WHERE id = %s", (agent,))
            conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


def test_the_viewer_prints_a_dash_where_the_api_sends_none():
    src = (REPO / "apps/web/components/mobile-report/MobileReportViewer.tsx").read_text()
    assert "{comp.bedrooms}</p>" not in src and "{comp.bathrooms}</p>" not in src
    assert "{comp.sqft.toLocaleString()}</p>" not in src
    assert "comp.bedrooms ?? '—'" in src and "comp.bathrooms ?? '—'" in src


def test_the_wizard_stores_no_zero_for_missing_days_on_market():
    src = (REPO / "apps/web/components/property-wizard/property-wizard.tsx").read_text()
    assert "dom: c.dom ?? c.days_on_market ?? null," in src
    assert "c.dom || c.days_on_market || 0" not in src
