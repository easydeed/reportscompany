"""An asking price is not a sale (LR-018 / D-377), on the worker side.

The CMA comp builder in `process_consumer_report` wrote `closePrice or
listPrice` as the price and a missing MLS status as "Closed", so a closed
listing with no recorded close price reached the homeowner's range, median and
$/sqft at what the seller ASKED. The PDF builder read prices the same way
(`price` first, `list_price` as a fallback), including for the cover overview's
prompt.

Two layers:
- the real task, with only the MLS feed, the PDF renderer and Twilio faked:
  what it STORES for the report;
- the real builder over stored comps of both shapes (the worker/API shape with
  `close_price`, and the wizard shape with only `sale_price`): what the PDF
  PRINTS, including for a report stored before this change.

Red on main: the $950,000 asking price is stored as a comp's price, sits at the
top of the stored range and the market median, and tops the PDF's range.
"""
import os
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")


def _ago(days):
    return (date.today() - timedelta(days=days)).isoformat()


def _row(mls_id, *, status="Closed", list_price=None, close_price=None, sqft=1000):
    row = {"mlsId": mls_id, "property": {"type": "RES", "area": sqft, "bedrooms": 3},
           "address": {"full": f"{mls_id} Comp St"}, "geo": {"lat": 34.1008, "lng": -117.7678},
           "sales": {"closeDate": _ago(30)}}
    if status is not None:
        row["mls"] = {"status": status}
    if list_price is not None:
        row["listPrice"] = list_price
    if close_price is not None:
        row["sales"]["closePrice"] = close_price
    return row


RECORDED = [_row(f"S{i}", list_price=p + 10000, close_price=p)
            for i, p in enumerate((610000, 640000, 655000))]
ASKING_ONLY = _row("ASK", list_price=950000)
NO_STATUS_NO_SALE = _row("UNK", status=None, list_price=880000)


# ── the rule itself ───────────────────────────────────────────────────────────

def test_the_rule_never_prices_a_sale_at_its_asking_price():
    from worker.tasks import _comp_sale_fields, _is_usable_comp
    assert _comp_sale_fields(ASKING_ONLY) == {
        "status": "Closed", "price": None, "close_price": None, "list_price": 950000}
    assert not _is_usable_comp(ASKING_ONLY)
    assert _comp_sale_fields(RECORDED[0])["price"] == 610000
    assert _is_usable_comp(RECORDED[0])


def test_a_missing_status_is_closed_only_with_a_recorded_price():
    from worker.tasks import _comp_sale_fields, _is_usable_comp
    sold = _row("SNS", status=None, close_price=625000, list_price=640000)
    assert _comp_sale_fields(sold)["status"] == "Closed" and _is_usable_comp(sold)
    # The CMA search asks for closed sales only: with no price, still not a comp.
    assert not _is_usable_comp(NO_STATUS_NO_SALE)


# ── the real task: what is stored ─────────────────────────────────────────────

@pytest.fixture
def stored_cma(monkeypatch):
    """Run the real consumer task against the migrated DB with a fake MLS feed."""
    if not DB_URL or "fake" in DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL")
    from worker import tasks
    from worker.vendors import simplyrets
    from worker.sms import send as sms_send
    monkeypatch.setattr(tasks, "DATABASE_URL", DB_URL)
    feed = RECORDED + [ASKING_ONLY, NO_STATUS_NO_SALE]
    monkeypatch.setattr(simplyrets, "fetch_properties", lambda *a, **k: list(feed))
    monkeypatch.setattr(tasks, "render_pdf", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no PDF here")))

    class Twilio:
        def __init__(self):
            self.messages = self

        def create(self, **k):
            class M:
                sid, status = "SM" + "0" * 32, "queued"
            return M()
    monkeypatch.setattr(sms_send, "get_twilio_client", lambda: Twilio())
    monkeypatch.setattr(sms_send, "TWILIO_PHONE_NUMBER", "+15555550000")

    tag = uuid.uuid4().hex[:8]
    acc, user, rid = (str(uuid.uuid4()) for _ in range(3))
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug, sms_credits) "
                     "VALUES (%s, 'LR-018', %s, 'REGULAR', 'free', 5)", (acc, f"lr018w-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Zoe', 'Noelle')", (user, acc, f"lr018w-{tag}@example.com"))
        conn.execute(
            "INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, consent_given, "
            "property_address, property_city, property_state, property_zip, property_data, status, "
            "delivery_method) VALUES (%s, %s, 'L18', '6265550123', TRUE, '1358 5th Street', 'La Verne', "
            "'CA', '91750', %s, 'pending', 'sms')",
            (rid, user, '{"bedrooms": 3, "sqft": 1000, "latitude": 34.1008, "longitude": -117.7678}'))
    tasks.process_consumer_report.apply(args=[rid]).get(propagate=False)
    with psycopg.connect(DB_URL) as conn:
        row = conn.execute("SELECT comparables, value_estimate, market_stats FROM consumer_reports "
                           "WHERE id = %s", (rid,)).fetchone()
    yield row
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("DELETE FROM sms_logs WHERE consumer_report_id = %s", (rid,))
        conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
        conn.execute("DELETE FROM users WHERE id = %s", (user,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


def test_the_cma_stores_no_asking_price_as_a_sale(stored_cma):
    comparables, value_estimate, market_stats = stored_cma
    ids = {c["mls_id"] for c in comparables}
    assert ids == {"S0", "S1", "S2"}, f"stored comps: {sorted(ids)}"
    assert all(c["price"] == c["close_price"] for c in comparables)
    assert value_estimate == {"low": 610000, "high": 655000, "count": 3}, value_estimate
    assert market_stats["median_price"] == 640000, market_stats
    assert market_stats["total_sold_last_6mo"] == 3


# ── the PDF: what is printed, including for a report stored before ───────────

def _v2(comparables):
    from worker.property_builder import PropertyReportBuilder
    builder = PropertyReportBuilder({
        "property_address": "1358 5th Street", "property_city": "La Verne",
        "property_state": "CA", "property_zip": "91750",
        "sitex_data": {"sqft": 786, "bedrooms": 2}, "comparables": comparables,
    })
    ctx = {
        "property": builder._build_property_context(),
        "agent": builder._build_agent_context(),
        "stats": builder._build_stats_context(),
        "comparables": builder._build_comparables_context(),
        "audience": "agent", "prepared_for": "",
    }
    return builder, ctx


#: Worker/API shape, as a consumer report stored it BEFORE this change.
STORED_CONSUMER = [
    {"status": "Closed", "price": 950000, "list_price": 950000, "close_price": None,
     "sqft": 1000, "close_date": _ago(20), "address": "ASK Comp St"},
] + [
    {"status": "Closed", "price": p, "list_price": p + 10000, "close_price": p,
     "sqft": 1000, "close_date": _ago(30), "address": f"S{i} Comp St"}
    for i, p in enumerate((610000, 640000, 655000))
]


def test_a_stored_consumer_report_re_renders_without_the_asking_price():
    builder, ctx = _v2(STORED_CONSUMER)
    shown = {c["address"] for c in ctx["comparables"]}
    assert "ASK Comp St" not in shown, "the PDF lists an asking price as a comparable sale"
    assert builder._v2_closed_prices(ctx["comparables"]) == [610000, 640000, 655000]
    stats = ctx["stats"]
    assert stats["price_high"] == 655000, (
        f"the cover overview's prompt would say the range tops out at {stats['price_high']}")


def test_an_agent_report_keeps_its_recorded_sales():
    """Wizard shape: only `sale_price` survives, and it is used."""
    wizard = [{"status": "Closed", "sale_price": p, "list_price": p + 10000,
               "sqft": 1000, "sold_date": _ago(30), "address": f"W{i} St"}
              for i, p in enumerate((600000, 620000))]
    builder, ctx = _v2(wizard)
    assert builder._v2_closed_prices(ctx["comparables"]) == [600000, 620000]


def test_an_active_comp_still_shows_its_list_price():
    builder, ctx = _v2([{"status": "Active", "price": 899000, "list_price": 899000,
                         "sqft": 1000, "list_date": _ago(5), "address": "A1 St"}])
    assert [c["sale_price"] for c in ctx["comparables"]] == [899000]
    assert builder._v2_closed_prices(ctx["comparables"]) == []


# ── Codex review of #277: the comps page and every statistic describe the same homes ──

def test_every_pdf_statistic_is_computed_from_the_comps_it_shows():
    agree = [
        {"status": "Closed", "close_price": 610000, "price": 610000, "list_price": 620000,
         "sqft": 1000, "close_date": _ago(40), "distance_miles": 0.4, "days_on_market": 10,
         "address": "A1 St"},
        {"status": "Closed", "close_price": 640000, "price": 640000, "list_price": 650000,
         "sqft": 1000, "close_date": _ago(60), "distance_miles": 0.5, "days_on_market": 20,
         "address": "A2 St"},
        {"status": "Closed", "close_price": None, "price": 950000, "list_price": 950000,
         "sqft": 1000, "close_date": _ago(2400), "distance_miles": 40.0, "days_on_market": 500,
         "address": "Far Asking St"},
    ]
    builder, ctx = _v2(agree)
    shown = [c["address"] for c in ctx["comparables"]]
    assert shown == ["A1 St", "A2 St"] or sorted(shown) == ["A1 St", "A2 St"], shown
    stats = ctx["stats"]
    assert stats["total_comps"] == 2, stats
    assert stats["max_distance"] == 0.5, f"an excluded comp set the radius: {stats['max_distance']}"
    assert stats["avg_days_on_market"] == 15, f"an excluded comp set days on market: {stats}"
    window = builder._window_months(builder.report_data["comparables"])
    assert window == 6, f"an excluded comp set the window: {window} months"
    assert agree[2]["address"] == "Far Asking St", "the caller's comps were modified"
    assert len(agree) == 3
