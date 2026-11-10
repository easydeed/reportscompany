"""Three ways a sent report printed a wrong number (pre-pilot, Jerry 2026-11-09).

D-188  The market running head, on every page, printed `sum(counts)` beside the
       report title: a closed report with 50 active, 20 pending and 40 closed
       said "110 Closed Sales" above a band that says 40.
D-168  The property report's comp record turned a missing value into 0: a comp
       with no days on market "sold the day it listed", no distance meant "at
       your address", no bedroom count meant a studio.
D-106  Bathrooms were read from a key the feed does not send (market reports
       had no bath count at all) or from `bathsFull` alone (2 full baths and a
       powder room read "2"). Jerry's convention: halves count 0.5, so 2.5.

Red on main: every test below fails there.
"""
import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "scripts"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")

from measure_market_pagination import report_data  # noqa: E402
from worker.market_builder import ALL_REPORT_TYPES, MarketReportBuilder  # noqa: E402


# ── D-188: the running head says what the page says ─────────────────────────

def _market(kind, counts=None):
    data = report_data(kind, 20)
    data["ai_insights"] = None
    if counts is not None:
        data["counts"] = counts
    return MarketReportBuilder(data)


def _running_head(builder):
    m = re.search(r'class="rh-meta">([^<]*)<', builder.render_page_header_html())
    return m.group(1).strip() if m else None


def test_a_closed_report_heads_its_pages_with_its_own_count():
    b = _market("closed", {"Active": 50, "Pending": 20, "Closed": 40})
    assert b._v2_band()["big"] == 40
    assert _running_head(b) == "40 homes sold", _running_head(b)


def test_inventory_counts_homes_for_sale_not_every_status():
    b = _market("inventory", {"Active": 10, "Pending": 0, "Closed": 10})
    assert _running_head(b) == "10 homes for sale", _running_head(b)


@pytest.mark.parametrize("kind", ALL_REPORT_TYPES)
def test_every_kind_s_running_head_is_its_own_headline_count(kind):
    b = _market(kind, {"Active": 67, "Pending": 12, "Closed": 38})
    count, noun = b._v2_headline_count()
    assert count is not None and noun, f"{kind} has no headline count"
    assert _running_head(b) == f"{count} {noun}"
    assert count != 67 + 12 + 38, f"{kind}'s running head is still the sum of every status"
    band = b._v2_band()
    shown = {str(band["big"])} | {str(c["value"]) for c in band["cells"]}
    assert str(count) in shown or f"{count:,}" in shown, (
        f"{kind}: the running head says {count} {noun}, which the page-1 band does not show")


# ── D-168: a missing comp value stays missing ───────────────────────────────

def _property(comps):
    from worker.property_builder import PropertyReportBuilder
    return PropertyReportBuilder({
        "property_address": "1358 5th Street", "property_city": "La Verne",
        "property_state": "CA", "property_zip": "91750",
        "sitex_data": {"sqft": 786, "bedrooms": 2}, "comparables": comps,
    })


SPARSE = {"address": "9 Sparse St", "status": "Closed", "close_price": 640000,
          "price": 640000, "sqft": 1000, "close_date": "2026-09-01"}


def test_a_comp_with_no_values_has_none_of_them_not_zeros():
    (c,) = _property([dict(SPARSE)])._build_comparables_context()
    for key in ("days_on_market", "distance_miles", "bedrooms", "bathrooms",
                "year_built", "lot_size"):
        assert c[key] is None, f"a missing {key} became {c[key]!r}"


def test_a_recorded_zero_is_still_zero():
    """0 days on market is real: it listed and sold the same day."""
    (c,) = _property([dict(SPARSE, days_on_market=0)])._build_comparables_context()
    assert c["days_on_market"] == 0


def test_the_comp_card_prints_no_zero_for_a_missing_count():
    from worker.property_builder import PropertyReportBuilder
    b = _property([dict(SPARSE)])
    ctx = {"property": b._build_property_context(), "agent": b._build_agent_context(),
           "stats": b._build_stats_context(), "comparables": b._build_comparables_context(),
           "audience": "agent", "prepared_for": ""}
    b._build_v2_context(ctx, list(PropertyReportBuilder.V2_PAGE_ORDER))
    (c,) = ctx["comparables"]
    assert "0 bd" not in c["v2_specs"] and "0 ba" not in c["v2_specs"], c["v2_specs"]
    assert c["v2_dist"] != "0.0 mi"


def test_average_days_on_market_skips_comps_with_none():
    comps = [dict(SPARSE, address="A", days_on_market=10),
             dict(SPARSE, address="B", days_on_market=20),
             dict(SPARSE, address="C")]
    assert _property(comps)._build_stats_context()["avg_days_on_market"] == 15


# ── D-106: bathrooms, full + half/2 ─────────────────────────────────────────

@pytest.mark.parametrize("prop,want", [
    ({"bathsFull": 2, "bathsHalf": 1}, 2.5),
    ({"bathsFull": 2, "bathsHalf": 2}, 3.0),
    ({"bathsFull": 3}, 3.0),
    ({"bathsHalf": 1}, 0.5),
    ({}, None),
    (None, None),
])
def test_baths_follow_jerrys_convention(prop, want):
    from worker.compute.extract import baths_total
    assert baths_total(prop) == want


def test_market_listings_carry_a_bath_count():
    """The extractor read `property.bathrooms`, which the feed never sends."""
    from worker.compute.extract import PropertyDataExtractor
    raw = [{"mlsId": 1, "listPrice": 900000, "listDate": "2026-10-01T00:00:00Z",
            "mls": {"status": "Active", "daysOnMarket": 5},
            "address": {"full": "1 A St", "city": "Irvine", "postalCode": "92618"},
            "property": {"bedrooms": 3, "bathsFull": 2, "bathsHalf": 1, "area": 1500,
                         "type": "RES", "subType": "SingleFamilyResidence"}}]
    (row,) = PropertyDataExtractor(raw).run()
    assert row["bathrooms"] == 2.5


def test_the_cma_stores_both_bath_counts_and_no_invented_zeros(monkeypatch):
    """The real consumer task, MLS feed faked: what it stores for each comp."""
    import json
    import uuid
    psycopg = pytest.importorskip("psycopg")
    db = os.getenv("DATABASE_URL")
    if not db or "fake" in db:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL")
    from worker import tasks
    from worker.vendors import simplyrets
    from worker.sms import send as sms_send

    def row(mls_id, prop):
        return {"mlsId": mls_id, "listPrice": 700000, "mls": {"status": "Closed"},
                "sales": {"closePrice": 690000, "closeDate": "2026-09-01"},
                "address": {"full": f"{mls_id} Comp St"}, "geo": {"lat": 34.1, "lng": -117.7},
                "property": dict(type="RES", **prop)}
    feed = [row("FULL", {"bedrooms": 3, "bathsFull": 2, "bathsHalf": 1, "area": 1500}),
            row("BARE", {}), row("X3", {"bedrooms": 2, "bathsFull": 1, "area": 900})]
    monkeypatch.setattr(tasks, "DATABASE_URL", db)
    monkeypatch.setattr(simplyrets, "fetch_properties", lambda *a, **k: list(feed))
    monkeypatch.setattr(tasks, "render_pdf", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no PDF")))
    monkeypatch.setattr(sms_send, "get_twilio_client", lambda: None)
    tag = uuid.uuid4().hex[:8]
    acc, user, rid = (str(uuid.uuid4()) for _ in range(3))
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'D-106', %s, 'REGULAR', 'free')", (acc, f"d106-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Zoe', 'Noelle')", (user, acc, f"d106-{tag}@example.com"))
        conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, "
                     "consent_given, property_address, property_city, property_state, property_zip, "
                     "property_data, status, delivery_method) VALUES (%s, %s, 'D16', '6265550123', "
                     "TRUE, '1358 5th Street', 'La Verne', 'CA', '91750', %s, 'pending', 'sms')",
                     (rid, user, json.dumps({"latitude": 34.1, "longitude": -117.7})))
    try:
        tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
        with psycopg.connect(db) as conn:
            (comps,) = conn.execute("SELECT comparables FROM consumer_reports WHERE id = %s",
                                    (rid,)).fetchone()
        by = {c["mls_id"]: c for c in comps}
        assert by["FULL"]["bathrooms"] == 2.5, by["FULL"]
        assert by["X3"]["bathrooms"] == 1.0
        assert (by["BARE"]["bedrooms"], by["BARE"]["bathrooms"], by["BARE"]["sqft"]) == (None, None, None), (
            f"missing counts were stored as {by['BARE']}")
    finally:
        with psycopg.connect(db, autocommit=True) as conn:
            conn.execute("DELETE FROM sms_logs WHERE consumer_report_id = %s", (rid,))
            conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
            conn.execute("DELETE FROM users WHERE id = %s", (user,))
            conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))
