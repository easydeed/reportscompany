"""D-350, D-351 — the /r page shows what the PDF shows, and no estimate.

`GET /v1/r/{id}/data` returned `value_estimate` — the home's square footage
times the comps' AVERAGE price per square foot, ±8%, with a "most likely"
price in the middle — and the viewer led with it. The PDF of the same report
prints the range of the comparable sales and no point estimate; the owner
decided against an estimate outside the range panel (2026-11-04). The market
tab said "Homes Sold (6 mo)" over "within 2 miles … in the last 12 months"
while the PDF said 0.6 mi and 6 months, and showed an average $/sqft where the
PDF shows a median.

Red on main: the response has `value_estimate` with a `mid`, no `comps_range`,
and the market stats carry no window or radius.
"""
import json
import os
import re
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest

DB_URL = os.getenv("DATABASE_URL")
psycopg = pytest.importorskip("psycopg", reason="psycopg is required for integration tests")

VIEWER = (Path(__file__).resolve().parents[3]
          / "apps/web/components/mobile-report/MobileReportViewer.tsx")


def _ago(days):
    return (date.today() - timedelta(days=days)).isoformat()


#: Four closed sales and one active listing. Closed prices 470,000 / 590,000 /
#: 631,500 / 635,000, so the range is 470,000–635,000 and the upper median is
#: 631,500. The active listing at 900,000 must not reach the range.
COMPS = [
    {"address": "1845 Walnut St", "price": 470000, "close_price": 470000, "sqft": 770,
     "status": "Closed", "close_date": _ago(70), "distance_miles": 0.24, "days_on_market": 12},
    {"address": "1848 1st St", "price": 590000, "close_price": 590000, "sqft": 698,
     "status": "Closed", "close_date": _ago(100), "distance_miles": 0.3, "days_on_market": 20},
    {"address": "1889 Bonita Ave", "price": 631500, "close_price": 631500, "sqft": 940,
     "status": "Closed", "close_date": _ago(40), "distance_miles": 0.58, "days_on_market": 8},
    {"address": "1507 2nd St", "price": 635000, "close_price": 635000, "sqft": 912,
     "status": "Closed", "close_date": _ago(150), "distance_miles": 0.54, "days_on_market": 30},
    {"address": "9 Asking Way", "price": 900000, "sqft": 1000,
     "status": "Active", "distance_miles": 1.9},
]


@pytest.fixture
def report():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run the consumer report test")
    tag = uuid.uuid4().hex[:8]
    account, agent, rid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    with psycopg.connect(DB_URL) as conn:
        conn.execute(
            "INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
            "VALUES (%s, 'Range Test', %s, 'REGULAR', 'free')", (account, f"range-{tag}"))
        conn.execute(
            "INSERT INTO users (id, account_id, email, first_name, last_name) "
            "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (agent, account, f"agent-{tag}@example.com"))
        conn.execute(
            "INSERT INTO consumer_reports (id, agent_id, agent_code, property_address, "
            "property_city, property_state, property_zip, property_data, comparables, "
            "value_estimate, market_stats, status) VALUES (%s, %s, 'T1', '1358 5th Street', "
            "'La Verne', 'CA', '91750', %s, %s, %s, %s, 'ready')",
            (rid, agent,
             json.dumps({"address": "1358 5th Street", "city": "La Verne", "state": "CA",
                         "zip": "91750", "sqft": 786}),
             json.dumps(COMPS),
             # What the worker stored before this change: an estimate.
             json.dumps({"low": 509799, "mid": 554130, "high": 598460, "confidence": "medium"}),
             json.dumps({"median_price": 631500, "avg_price_per_sqft": 705,
                         "total_sold_last_6mo": 5})))
    yield rid
    with psycopg.connect(DB_URL) as conn:
        conn.execute("DELETE FROM report_analytics WHERE report_id = %s", (rid,))
        conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
        conn.execute("DELETE FROM users WHERE id = %s", (agent,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (account,))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def test_the_page_gets_the_comps_range_and_no_estimate(client, report):
    r = client.get(f"/v1/r/{report}/data")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "value_estimate" not in body
    assert "554130" not in r.text and "509799" not in r.text, "the stored estimate leaked through"
    assert body["comps_range"] == {"low": 470000, "high": 635000, "count": 4,
                                   "method": "Range of the comparable sales shown."}


def test_the_market_tab_says_what_the_pdf_says(client, report):
    stats = client.get(f"/v1/r/{report}/data").json()["market_stats"]
    assert stats["median_price"] == 631500           # upper median of closed sales
    assert stats["median_price_per_sqft"] == 696      # 635000 / 912, the PDF's median row
    assert stats["homes_sold"] == 4                   # closed only; the listing is not a sale
    assert stats["window_months"] == 6                # oldest close 150 days ago
    assert stats["radius_miles"] == 0.6               # farthest closed sale, 0.58 mi
    assert "avg_price_per_sqft" not in stats and "total_sold_last_6mo" not in stats


def test_the_viewer_prints_no_estimate_and_no_fixed_window():
    src = VIEWER.read_text(encoding="utf-8")
    assert "value_estimate" not in src
    assert "Most likely" not in src and "confidence" not in src
    assert "Estimated Value" not in src
    assert not re.search(r"2 miles|12 months|6 mo\)", src), "the viewer states a window or radius of its own"
    assert "report.comps_range.method" in src
