"""D-077, D-078, D-110, D-164: what the market reports say is what is true.

D-077 (Jerry, 2026-10-30). The inventory report's "Active" count was the
listings table's population (listed inside the lookback window) while months
of supply divided EVERY home for sale by the sales rate. Both figures now count
every home for sale; the table keeps its window and says so.

D-078. A truncated fetch and too few sales both gave months of supply None,
and the words published for both were "Not enough recent sales to estimate" —
the opposite situation, for a busy market.

D-110 (Jerry, 2026-10-30). A report that matched nothing is not sent. The
agent is told instead.

D-164. The market path read, defaulted, logged and passed a theme id that
`MarketReportBuilder` never reads.
"""
import ast
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker import tasks  # noqa: E402
from worker.compute.moi import describe  # noqa: E402
from worker.market_builder import MarketReportBuilder  # noqa: E402
from worker.report_builders import build_inventory_result, build_result_json  # noqa: E402

NOW = datetime.now()


def listing(status="Active", days_listed=5, city="Anytown", price=500_000, closed_days=None):
    row = {"status": status, "city": city, "street_address": "1 Elm St", "list_price": price,
           "bedrooms": 3, "bathrooms": 2, "sqft": 1500, "days_on_market": days_listed,
           "list_date": NOW - timedelta(days=days_listed), "property_type": "Residential"}
    if closed_days is not None:
        row.update(close_price=price, close_date=NOW - timedelta(days=closed_days),
                   close_to_list_ratio=100.0)
    return row


def market(new=3, older=5, closed=10, active_total=None, **ctx):
    rows = ([listing(days_listed=5) for _ in range(new)]
            + [listing(days_listed=200) for _ in range(older)]
            + [listing("Closed", 30, closed_days=20) for _ in range(closed)])
    context = {"city": "Anytown", "lookback_days": 30, "active_total": active_total}
    context.update(ctx)
    return build_inventory_result(rows, context)


# ── D-077 ────────────────────────────────────────────────────────────────────

def test_the_active_count_is_every_home_for_sale_like_the_supply_numerator():
    result = market(new=3, older=5, active_total=212)
    assert result["counts"]["Active"] == 212 == result["metrics"]["total_active"]
    assert result["metrics"]["listed_in_window"] == 3


def test_without_a_feed_count_both_fall_back_to_the_same_rows():
    result = market(new=3, older=5)
    assert result["counts"]["Active"] == result["metrics"]["total_active"] == 8


def test_the_page_says_the_table_is_the_ones_listed_in_the_window():
    data = dict(market(new=3, older=5, active_total=212), report_type="inventory",
                closed_history=[], branding={})
    b = MarketReportBuilder(data)
    html = b.render_html()
    assert "212" in html
    assert b._v2_table()["noun"] == "listed in the last 30 days"
    assert "3 listed in the last 30 days" in " ".join(html.split())


# ── D-078 ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("flag", ["active_was_truncated", "closed_was_truncated"])
def test_a_truncated_fetch_is_too_many_to_count_not_too_few_sales(flag):
    shown = market(closed=40, **{flag: True})["metrics"]["months_of_inventory_display"]
    assert shown["current"] is None
    assert shown["formatted_current"] == "Too many listings to count exactly"
    assert "Not enough" not in shown["formatted_current"]


def test_too_few_sales_still_says_so():
    shown = market(closed=2)["metrics"]["months_of_inventory_display"]
    assert shown["formatted_current"] == "Not enough recent sales to estimate"
    assert describe(None)["reason"] == "not_enough_sales"


# ── D-110 ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("report_type", [
    "market_snapshot", "new_listings", "inventory", "closed", "price_bands",
    "open_houses", "new_listings_gallery", "featured_listings"])
def test_every_report_says_how_many_listings_it_matched(report_type):
    ctx = {"city": "Anytown", "lookback_days": 30, "filters": {}}
    assert build_result_json(report_type, [], ctx)["matched"] == 0
    elsewhere = [listing(city="Othertown") for _ in range(4)]
    assert build_result_json(report_type, elsewhere, ctx)["matched"] == 0
    assert build_result_json(report_type, [listing() for _ in range(4)], ctx)["matched"] == 4


def test_only_a_stamped_zero_counts_as_matching_nothing():
    assert tasks._matched_nothing({"matched": 0})
    assert not tasks._matched_nothing({"matched": 3})
    assert not tasks._matched_nothing({})  # cached before the stamp existed
    assert not tasks._matched_nothing(None)


def test_a_report_that_matched_nothing_is_not_sent(monkeypatch):
    held = []

    def no_send(**kw):
        raise AssertionError("a report that matched nothing was sent to its recipients")

    monkeypatch.setattr(tasks, "send_schedule_email", no_send)
    monkeypatch.setattr(tasks, "_hold_empty_report", lambda *a: held.append(a))
    status, _ = tasks._send_and_log_report_email(
        None, None, "acct", "run-1", ["buyer@example.test"], "inventory", "Anytown",
        None, 30, {"matched": 0}, "https://x.test/r.pdf", schedule_id="sched-1")
    assert status == tasks.NOT_SENT_MATCHED_NOTHING
    assert held == [("acct", "run-1", "sched-1", ["buyer@example.test"], "inventory", "Anytown")]


class FakeCursor:
    def __init__(self, already_told=False):
        self.already_told = already_told
        self.inserts = []
        self._last = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self._last = s
        if s.startswith("INSERT INTO email_log"):
            self.inserts.append((s, params))

    def fetchone(self):
        s = self._last or ""
        if "FROM email_log" in s:
            return (1,) if self.already_told else None
        if "FROM schedules" in s:
            return ("Weekly Anytown inventory",)
        if "au.role = 'OWNER'" in s:
            return ("agent@example.test",)
        return None


class FakeConn:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self):
        return self.cur


class Resp:
    status_code = 200
    text = "ok"


def _hold(monkeypatch, cur):
    sent = []
    monkeypatch.setattr(tasks, "_open_log_connection", lambda: FakeConn(cur))
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setattr(tasks.httpx, "post", lambda url, **kw: sent.append(kw["json"]) or Resp())
    tasks._hold_empty_report("acct", "run-1", "sched-1", ["buyer@example.test"], "inventory", "Anytown")
    return sent


def test_the_agent_is_told_and_the_recipients_are_not(monkeypatch):
    cur = FakeCursor()
    sent = _hold(monkeypatch, cur)
    assert len(sent) == 1 and sent[0]["to"] == ["agent@example.test"]
    assert sent[0]["subject"] == "Your Weekly Anytown inventory matched no listings"
    assert "Anytown" in sent[0]["html"] and "wasn" in sent[0]["html"]
    held, notice = cur.inserts
    assert "'suppressed'" in held[0] and held[1][3] == ["buyer@example.test"]
    assert notice[1][3] == ["agent@example.test"] and notice[1][4].startswith("[matched nothing]")
    assert notice[1][6] == "sent"


def test_a_redelivered_run_does_not_tell_the_agent_twice(monkeypatch):
    cur = FakeCursor(already_told=True)
    assert _hold(monkeypatch, cur) == [] and cur.inserts == []


def test_the_notice_says_nothing_went_out_and_the_schedule_is_still_on():
    subject, html, _ = tasks._empty_notice(
        report_name="Weekly Anytown", area="Anytown", scheduled=True, url="https://x.test/app/schedules")
    text = " ".join(html.split())
    assert "returned no listings" in text and "wasn&rsquo;t sent to your recipients" in text
    assert "still on" in text
    _, adhoc, _ = tasks._empty_notice(report_name="Inventory report", area="Anytown",
                                      scheduled=False, url="https://x.test/app/reports")
    assert "still on" not in adhoc


def test_a_scheduled_run_that_matched_nothing_is_recorded_as_skipped_empty():
    src = Path(tasks.__file__).read_text()
    assert "if status_code == NOT_SENT_MATCHED_NOTHING:\n" in src
    assert "run_status = 'skipped_empty'" in src


# ── D-164 ────────────────────────────────────────────────────────────────────

def _generate_report_source():
    src = Path(tasks.__file__).read_text()
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "generate_report")
    return ast.get_source_segment(src, fn)


def test_the_market_path_reads_and_passes_no_theme():
    body = _generate_report_source()
    assert "SELECT theme_id" not in body, "the market path still reads a theme nothing uses"
    assert 'builder_data["theme_id"]' not in body, "the builder is still handed a theme it ignores"
    assert "accent=" in body, "the log line no longer names the colour that is actually chosen"
