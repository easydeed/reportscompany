"""An asking price is not a sale (LR-018 / D-377), on the API side.

Every comp builder had two fallbacks that together turned a listing into a
sale: the price was `closePrice or listPrice`, and a missing MLS status was
written as "Closed". A closed listing with no recorded close price therefore
entered the range, the median and $/sqft at what the seller ASKED, and an "All"
search could label an active listing a sale.

These run the real `/v1/property/comparables` route (the agent path, vendor
call replaced) and the real `/r` summary over stored consumer rows (the
homeowner path, which re-reads history with no migration).

Red on main: the $950,000 asking price is returned as a comparable sale and
sits at the top of the /r range, median and $/sqft.
"""
from datetime import date, timedelta

import pytest

# The endpoint harness: the real route, the vendor replaced, no database.
from test_comp_close_window import _call, mock_auth, _no_database  # noqa: F401


def _ago(days):
    return (date.today() - timedelta(days=days)).isoformat()


def _row(mls_id, *, status="Closed", list_price=None, close_price=None, days=20, sqft=1000):
    row = {
        "mlsId": mls_id,
        "property": {"type": "RES", "area": sqft},
        "address": {"full": f"{mls_id} Comp St"},
        "geo": {"lat": 34.1008, "lng": -117.7678},
    }
    if status is not None:
        row["mls"] = {"status": status}
    if list_price is not None:
        row["listPrice"] = list_price
    if close_price is not None or status == "Closed":
        row["sales"] = {"closeDate": _ago(days)}
        if close_price is not None:
            row["sales"]["closePrice"] = close_price
    return row


RECORDED = [_row(f"S{i}", list_price=p + 10000, close_price=p)
            for i, p in enumerate((610000, 640000, 655000, 670000, 700000))]
ASKING_ONLY = _row("ASK", list_price=950000)          # closed, no close price


# ── the agent path: what the comps endpoint returns ────────────────────────

def test_a_closed_listing_with_no_sale_price_is_not_returned_as_a_sale(mock_auth):
    _, body = _call("Closed", RECORDED + [ASKING_ONLY])
    ids = {c["mls_id"] for c in body["comparables"]}
    assert "ASK" not in ids, "a $950,000 asking price was returned as a comparable sale"
    assert all(c["price"] == c["close_price"] for c in body["comparables"]), body["comparables"]


def test_a_level_short_of_real_sales_widens_instead_of_padding(mock_auth):
    """The filter runs before the ladder counts, so an asking-price row cannot
    hold a level open."""
    def feed(params):
        # The strict level has two real sales and three asking prices; later
        # levels find five real sales.
        if params.get("minarea"):
            return RECORDED[:2] + [_row(f"A{i}", list_price=900000 + i) for i in range(3)]
        return RECORDED
    sent, body = _call("Closed", feed)
    assert len(sent) > 1, "the ladder stopped at a level padded with asking prices"
    assert {c["mls_id"] for c in body["comparables"]} == {f"S{i}" for i in range(5)}


def test_a_missing_status_is_never_assumed_closed(mock_auth):
    """An All search: no status and no sale is unknown, not a sale."""
    unknown = _row("UNK", status=None, list_price=880000)
    sold_no_status = _row("SNS", status=None, close_price=625000, list_price=640000)
    active = _row("ACT", status="Active", list_price=899000)
    _, body = _call("All", [unknown, sold_no_status, active])
    by_id = {c["mls_id"]: c for c in body["comparables"]}
    assert "UNK" not in by_id, f"a listing with no status came back as {by_id.get('UNK')}"
    assert by_id["SNS"]["status"] == "Closed" and by_id["SNS"]["price"] == 625000, (
        "a recorded close price is evidence of a sale; that one may be called Closed")
    assert by_id["ACT"]["status"] == "Active" and by_id["ACT"]["price"] == 899000


def test_an_active_search_still_prices_by_the_list_price(mock_auth):
    _, body = _call("Active", [_row("ACT", status="Active", list_price=899000),
                               _row("NOS", status=None, list_price=799000)])
    by_id = {c["mls_id"]: c for c in body["comparables"]}
    assert by_id["ACT"]["price"] == 899000
    # The vendor filtered on Active, so a row without a status is Active.
    assert by_id["NOS"]["status"] == "Active" and by_id["NOS"]["price"] == 799000


def test_the_simplyrets_normaliser_follows_the_same_rule():
    from api.services.simplyrets import normalize_listing
    out = normalize_listing(ASKING_ONLY)
    assert out["close_price"] is None and out["price"] == 0, out
    assert normalize_listing(_row("UNK", status=None, list_price=880000))["status"] == ""


def test_the_schema_normaliser_never_reads_a_raw_row_s_list_price_as_its_sale():
    from api.schemas.property import normalize_comparable
    assert normalize_comparable(ASKING_ONLY)["sale_price"] in (0, 0.0, None)
    assert normalize_comparable(RECORDED[0])["sale_price"] == 610000


# ── the homeowner path: stored rows, re-read by /r ─────────────────────────

#: What the worker stored before this change for a closed comp with no close
#: price: `price` fell back to the list price, `close_price` stayed None.
STORED_HISTORY = [
    {"status": "Closed", "price": 950000, "list_price": 950000, "close_price": None,
     "sqft": 1000, "close_date": _ago(20), "distance_miles": 0.3},
] + [
    {"status": "Closed", "price": p, "list_price": p + 10000, "close_price": p,
     "sqft": 1000, "close_date": _ago(30), "distance_miles": 0.4}
    for p in (610000, 640000, 655000)
]


def test_r_re_reads_a_stored_asking_price_without_it():
    from api.services.comp_summary import summarize
    s = summarize(STORED_HISTORY)
    assert s["range"]["high"] == 655000, f"the asking price is in the range: {s['range']}"
    assert s["range"]["count"] == 3
    assert s["median_price"] == 640000
    assert s["median_price_per_sqft"] == 640
    assert s["homes_sold"] == 3


def test_the_r_page_does_not_show_a_stored_asking_price_as_sold():
    """A stored report from before this change, through the real /r handler."""
    import json
    import os
    import uuid
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
                     "VALUES (%s, 'LR-018', %s, 'REGULAR', 'free')", (acc, f"lr018r-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (agent, acc, f"lr018r-{tag}@example.com"))
        conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, "
                     "property_address, property_city, property_state, property_zip, "
                     "property_data, comparables, status) VALUES (%s, %s, 'L18', '6265550123', "
                     "'1358 5th Street', 'La Verne', 'CA', '91750', %s, %s, 'sent')",
                     (rid, agent, json.dumps({"sqft": 786}), json.dumps(STORED_HISTORY)))
    try:
        r = TestClient(app, raise_server_exceptions=False).get(f"/v1/r/{rid}/data")
        assert r.status_code == 200, r.text
        body = r.json()
        sold = [c["sold_price"] for c in body["comparables"]]
        assert 950000 not in sold, f"the page lists an asking price as a sale: {sold}"
        assert sorted(sold) == [610000, 640000, 655000]
        assert body["comps_range"]["high"] == 655000
        assert body["market_stats"]["median_price"] == 640000
    finally:
        with psycopg.connect(db, autocommit=True) as conn:
            conn.execute("DELETE FROM report_analytics WHERE report_id = %s", (rid,))
            conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
            conn.execute("DELETE FROM users WHERE id = %s", (agent,))
            conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))
