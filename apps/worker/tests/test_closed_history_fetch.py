"""The twelve-month history fetch: that it happens, and what it refuses.

D-113. `MarketReportBuilder._build_monthly_trend` read `closed_history` and
nothing wrote it, so §7.3's chart never rendered. The contract gate
(`test_render_context_contract.py`) now catches that class structurally; these
assert the specifics of the fetch itself — which report types pay for it, what
the query asks the vendor, and that a truncated year is refused rather than
drawn.

WHY THESE DO NOT JUST CHECK `closed_history` IS NON-EMPTY. The defect was a
producer that did not exist, and a test that runs the producer proves only
that the producer runs. What matters is the contract between the two halves:
the fetch is bought for exactly the report types that draw a chart, and the
truncation flag the fetch sets is the one the series refuses on.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/worker/src"))

from worker.compute.monthly_trend import count_series, median_series  # noqa: E402
from worker.market_builder import (  # noqa: E402
    TREND_REPORT_TYPES,
    ALL_REPORT_TYPES,
    MarketReportBuilder,
)
from worker.query_builders import TREND_HISTORY_DAYS, build_closed_history  # noqa: E402


# ── who pays for it ─────────────────────────────────────────────────────────

def test_the_fetch_list_is_derived_from_the_draw_list():
    """
    The caller decides whether to buy the data; the builder decides whether to
    draw it. Two literals fail quietly in both directions — a fetch nobody
    uses, or a chart whose data was never bought. The first draft of
    `TREND_REPORT_TYPES` was a second literal, which is why this exists.
    """
    assert TREND_REPORT_TYPES == frozenset(MarketReportBuilder.TREND_SERIES)


def test_only_the_trend_reports_pay_for_a_second_query():
    """A second vendor request on the reports that cannot use the answer.

    WAS 2, IS 1, AND THE GATE IS WHAT NOTICED. `inventory` drew the sales-pace
    series and was therefore in `TREND_SERIES`, which `TREND_REPORT_TYPES` is
    derived from and `tasks.py` reads to decide whether to buy twelve months of
    closings. Design's `_v2` page for `inventory` has no chart slot, so from
    2026-10-08 the chart cannot render — and leaving the type in the map would
    have paid for a year of rows nothing could use.

    That is D-113's defect inverted: D-113 was a chart whose data was never
    bought, this would have been data no chart could spend. The comment on
    `TREND_REPORT_TYPES` names both directions, and this is the second one
    arriving.

    So the number went DOWN because a report stopped needing the fetch, which
    is the one way it can move that is good news. The instruction below still
    stands for the other direction.
    """
    assert TREND_REPORT_TYPES < set(ALL_REPORT_TYPES)
    assert len(TREND_REPORT_TYPES) == 1, (
        "if a report type gained a trend, this number moves with it — but "
        "check the fetch is wanted before updating it. If it went DOWN, a kind "
        "stopped drawing a chart: make sure it stopped paying for the data too, "
        "which is the whole reason this set is derived from `TREND_SERIES`."
    )
    assert TREND_REPORT_TYPES == frozenset({"market_snapshot"}), (
        f"the trend reports are now {set(TREND_REPORT_TYPES)}. `inventory` "
        f"left on 2026-10-08 with its chart; `market_snapshot` is the last "
        f"kind drawing one and the last kind unwired."
    )


# ── what the query asks for ─────────────────────────────────────────────────

def test_the_history_query_filters_on_close_date_not_list_date():
    """
    `minclosedate`, NOT `mindate`. The series buckets by `close_date`, so the
    filter has to be the one the feed applies to that field — and `mindate`
    was measured doing nothing at all, silently (D-074/D-075).
    """
    q = build_closed_history({"city": "Irvine"})
    assert "minclosedate" in q
    assert "mindate" not in q, "mindate does not filter; D-075 measured it"
    assert q["status"] == "Closed"


def test_the_history_window_is_the_window_the_chart_draws():
    q = build_closed_history({"city": "Irvine"})
    asked = date.fromisoformat(q["minclosedate"])
    expected = date.today() - timedelta(days=TREND_HISTORY_DAYS)
    assert abs((asked - expected).days) <= 1, (
        f"the query asks for {(date.today() - asked).days} days; the chart "
        f"draws twelve months"
    )
    assert TREND_HISTORY_DAYS == 365


def test_the_history_query_carries_no_report_filters():
    """
    The trend is the MARKET's twelve months. A chart captioned "median sale
    price" that silently showed only 3-bed homes under $1.5M is a different
    statistic wearing the same label.
    """
    q = build_closed_history({
        "city": "Irvine",
        "filters": {"beds_min": 3, "price_max": 1_500_000, "type": "RES"},
    })
    for leaked in ("minbeds", "maxprice", "minprice", "type", "subtype"):
        assert leaked not in q, f"{leaked} leaked into the history query"


# ── what it refuses ─────────────────────────────────────────────────────────

def _year_of_closings(per_month=8):
    rows, today = [], date.today()
    for k in range(12):
        year, month = today.year, today.month - k
        while month <= 0:
            year, month = year - 1, month + 12
        for i in range(per_month):
            rows.append({"close_date": f"{year}-{month:02d}-15",
                         "close_price": 800000 + k * 5000 + i * 1000})
    return rows


@pytest.mark.parametrize("series", [median_series, count_series])
def test_a_truncated_year_is_refused_rather_than_drawn(series):
    """
    THE FLAG THE FETCH SETS IS THE FLAG THE SERIES REFUSES ON.

    A fetch that hit its ceiling returns a floor, and a median over an
    order-dependent subset of one is a wrong number that looks right (D-078).
    Both halves exist; this asserts they are the same contract, because the
    fetch setting a flag nothing reads is the shape of D-113 itself.
    """
    history = _year_of_closings()
    assert series(history, truncated=False) is not None
    assert series(history, truncated=True) is None, (
        "a truncated year was drawn instead of refused"
    )


def test_a_truncated_history_produces_no_chart_end_to_end():
    """The refusal reaching the render, not just the compute function."""
    data = {
        "report_type": "market_snapshot", "city": "Irvine", "lookback_days": 30,
        "listings": [], "metrics": {}, "counts": {}, "branding": {},
        "closed_history": _year_of_closings(),
        "closed_history_truncated": True,
    }
    series, note, fmt = MarketReportBuilder(data)._build_monthly_trend()
    assert series is None, "a truncated year reached the chart"

    data["closed_history_truncated"] = False
    series, note, fmt = MarketReportBuilder(data)._build_monthly_trend()
    assert series is not None, "a complete year produced no chart"


def test_an_absent_history_is_a_report_without_a_chart_not_a_failure():
    """
    The degradation that shipped for three weeks is still the right behaviour
    when the fetch genuinely fails — it just must not be the normal case.
    """
    data = {
        "report_type": "market_snapshot", "city": "Irvine", "lookback_days": 30,
        "listings": [], "metrics": {}, "counts": {}, "branding": {},
        "closed_history": [], "closed_history_truncated": False,
    }
    assert MarketReportBuilder(data)._build_monthly_trend() == (None, None, None)
    assert MarketReportBuilder(data).render_html()          # renders anyway


# ── what an ignored cutoff would actually cost ──────────────────────────────

def _spanning(years, start_year, per_month=5):
    rows = []
    for year in range(start_year, start_year + years):
        for month in range(1, 13):
            for i in range(per_month):
                rows.append({"close_date": f"{year}-{month:02d}-15",
                             "close_price": 900000 + i * 1000})
    return rows


@pytest.mark.parametrize("series", [median_series, count_series])
def test_a_longer_span_than_asked_for_draws_the_same_twelve_months(series):
    """
    THE CLAIM THIS REPLACES WAS WRONG, WHICH IS WHY IT IS A TEST NOW.

    PR #105 said that if `minclosedate` were ignored "the chart draws from an
    unfiltered year and nothing would notice", and that travelled into the
    probe's comments and a message to the vendor trip before anyone checked
    it. It is false: both series iterate `_window(today, 12)` and LOOK UP each
    month, so rows outside the last twelve calendar months land in buckets
    nobody reads.

    The consequence matters — it is why the client-side re-filter `moi.py`
    uses is not worth copying here. `moi` COUNTS rows to derive a rate, so one
    extra row is one extra sale; the trend LOOKS UP months, so an extra row is
    never read.
    """
    today = date(2026, 9, 29)
    five_years = _spanning(5, 2022)
    one_year = [r for r in five_years
                if "2025-10-01" <= r["close_date"] <= "2026-09-30"]
    # The guard on the fixture, not on the code: most of the wide set has to
    # fall OUTSIDE the drawn window, or the test proves nothing. (The first
    # version asserted `len(five) > len(one) * 4` and failed on its own
    # arithmetic — the slice ran to the end of 2026, fifteen months, not
    # twelve.)
    outside = [r for r in five_years if r not in one_year]
    assert len(outside) > len(one_year) * 3, (
        f"only {len(outside)} of {len(five_years)} rows are outside the "
        f"window; the fixture is not testing a wider span"
    )

    wide = series(five_years, today=today)
    narrow = series(one_year, today=today)
    assert wide == narrow, "a wider span changed the series"
    assert len(wide) == 12
    assert (wide[0]["label"], wide[0]["year"]) == ("Oct", 2025)
    assert (wide[-1]["label"], wide[-1]["year"]) == ("Sep", 2026)


def test_the_real_exposure_is_the_row_cap_and_it_fails_safe():
    """
    An ignored cutoff makes the fetch ask for the whole closed history, which
    hits the row cap in a busy market and sets the truncation flag — and the
    series refuses. "No chart on the biggest markets", not "a wrong chart".

    Filtering client-side could not help: truncation happens at fetch time,
    and filtering the rows that came back does not restore the ones that
    did not.
    """
    today = date(2026, 9, 29)
    history = _spanning(5, 2022)
    assert median_series(history, today=today, truncated=True) is None
    assert count_series(history, today=today, truncated=True) is None
