"""The §7.3 trend chart: the series, and the marks it turns into.

The assertions that matter here are about HONESTY rather than appearance. A
median chart can be wrong in ways that look perfectly fine: a month with no
sales plotted at zero draws a crash; a month with one sale plotted as a median
draws a market; a series bucketed from a truncated fetch draws whichever
thousand rows the API happened to return first. Each of those renders a clean
line.
"""

import re
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.compute.monthly_trend import (  # noqa: E402
    MIN_CLOSED_FOR_MEDIAN,
    count_series,
    median_series,
)
from worker.market_builder import MarketReportBuilder  # noqa: E402
from worker.themes import derive_theme  # noqa: E402

TODAY = date(2026, 9, 24)


def closings(month, year=2026, n=8, price=900000):
    return [{"close_date": f"{year}-{month:02d}-15", "close_price": price + i * 1000}
            for i in range(n)]


def full_year(n=8):
    rows = []
    for k in range(12):
        y, mo = TODAY.year, TODAY.month - k
        while mo <= 0:
            y, mo = y - 1, mo + 12
        rows += closings(mo, y, n=n, price=845000 + (11 - k) * 7000)
    return rows


# ── the series ───────────────────────────────────────────────────────────────

def test_a_month_with_no_sales_is_a_gap_and_not_a_zero():
    rows = [r for r in full_year() if "-07-" not in r["close_date"]]
    series = median_series(rows, today=TODAY)
    july = [p for p in series if p["label"] == "Jul"][0]
    assert july["value"] is None, "no sales must be None"
    assert july["value"] != 0, "a zero here would draw a crash that did not happen"
    assert july["n"] == 0


#: The recorded minimum, written down rather than read from the module under
#: test. The first version of the tests below sized their fixtures as
#: `MIN_CLOSED_FOR_MEDIAN - 1` and `MIN_CLOSED_FOR_MEDIAN`, so lowering the
#: threshold to 1 moved the fixtures with it and the suite stayed green — the
#: regression was applied deliberately and MISSED. That is §0.6's "a test that
#: reads its expected value from the thing under test cannot fail", found for
#: the second time in one session, which is the argument for the rule.
RECORDED_MINIMUM = 3


def test_the_recorded_minimum_matches_the_module():
    assert MIN_CLOSED_FOR_MEDIAN == RECORDED_MINIMUM, (
        "the minimum sample for a monthly median changed. It is a judgement "
        "about when a median stops meaning anything, shared with "
        "compute.moi.MIN_CLOSED_FOR_MOI — record the new value here and say why."
    )


def test_a_month_below_the_minimum_sample_is_a_gap():
    rows = [r for r in full_year() if "-05-" not in r["close_date"]]
    rows += closings(5, n=RECORDED_MINIMUM - 1)
    series = median_series(rows, today=TODAY)
    may = [p for p in series if p["label"] == "May"][0]
    assert may["n"] == RECORDED_MINIMUM - 1
    assert may["value"] is None, (
        f"a median over {RECORDED_MINIMUM - 1} sales is those sales' prices, not a market's"
    )


def test_a_month_exactly_at_the_minimum_is_drawn():
    """The boundary from the inside — an off-by-one here silently empties the
    chart in thin markets, which is where a trend is most wanted."""
    rows = [r for r in full_year() if "-05-" not in r["close_date"]]
    rows += closings(5, n=RECORDED_MINIMUM)
    series = median_series(rows, today=TODAY)
    may = [p for p in series if p["label"] == "May"][0]
    assert may["value"] is not None


def test_a_truncated_fetch_is_refused_rather_than_drawn():
    assert median_series(full_year(), today=TODAY, truncated=True) is None


def test_one_drawable_month_is_not_a_trend():
    assert median_series(closings(9), today=TODAY) is None


def test_the_window_ends_on_this_month_and_is_twelve_long():
    series = median_series(full_year(), today=TODAY)
    assert len(series) == 12
    assert series[-1]["label"] == "Sep" and series[-1]["year"] == 2026
    assert series[0]["label"] == "Oct" and series[0]["year"] == 2025


def test_unreadable_dates_and_missing_prices_are_skipped_not_guessed():
    rows = full_year() + [
        {"close_date": "not-a-date", "close_price": 1},
        {"close_date": None, "close_price": 1},
        {"close_date": "2026-09-01", "close_price": None},
    ]
    series = median_series(rows, today=TODAY)
    assert series is not None
    assert all(p["value"] is None or p["value"] > 1000 for p in series)


# ── the marks ────────────────────────────────────────────────────────────────

def report(report_type="market_snapshot", history=None, primary="#1B365D"):
    data = {
        "report_type": report_type, "city": "Irvine", "lookback_days": 30,
        "listings": [], "metrics": {}, "counts": {},
        "branding": {"agent_name": "A", "primary_color": primary},
        "ai_insights": "Balanced.",
    }
    if history is not None:
        data["closed_history"] = history
    return MarketReportBuilder(data).render_html()


def svg_of(html):
    match = re.search(r'<div class="trend-chart[^"]*">(.*?)</div>', html, re.S)
    return match.group(1) if match else None


def test_no_history_renders_no_chart():
    assert svg_of(report()) is None


def test_a_report_type_without_a_trend_renders_no_chart():
    assert svg_of(report("closed", full_year())) is None


def test_the_line_breaks_across_a_gap_instead_of_spanning_it():
    rows = [r for r in full_year() if "-07-" not in r["close_date"]]
    svg = svg_of(report(history=rows))
    assert svg
    path = re.search(r'<path d="([^"]+)"', svg).group(1)
    assert path.count("M") == 2, (
        f"a gap must start a new subpath, not connect across the missing month: {path}"
    )


def test_an_unbroken_series_is_one_subpath():
    """Positive control for the assertion above — it must be able to read 1."""
    path = re.search(r'<path d="([^"]+)"', svg_of(report(history=full_year()))).group(1)
    assert path.count("M") == 1


def test_only_the_endpoint_and_the_extreme_are_labelled():
    """Never a number on every point. With a rising series the extreme IS the
    endpoint, so exactly one value label and one marker."""
    svg = svg_of(report(history=full_year()))
    assert svg.count("<circle") == 1
    labels = re.findall(r'font-weight="600"[^>]*>([^<]+)<', svg)
    assert len(labels) == 1, f"expected one value label, got {labels}"


def test_a_mid_series_peak_is_labelled_as_well_as_the_endpoint():
    rows = []
    for k in range(12):
        y, mo = TODAY.year, TODAY.month - k
        while mo <= 0:
            y, mo = y - 1, mo + 12
        peak = 400000 if k == 6 else 0
        rows += closings(mo, y, price=800000 + peak)
    svg = svg_of(report(history=rows))
    assert svg.count("<circle") == 2
    assert len(re.findall(r'font-weight="600"[^>]*>([^<]+)<', svg)) == 2


def test_the_mark_wears_primary_ink_and_never_the_raw_brand_colour():
    """§7.3, and it is a contrast rule rather than a style one: primary_ink is
    the only brand value themes.py guarantees at 4.5:1 on white."""
    primary = "#1B365D"
    ink = derive_theme(primary)["primary_ink"]
    svg = svg_of(report(history=full_year(), primary=primary))
    stroke = re.search(r'<path d="[^"]+" fill="none" stroke="([^"]+)"', svg).group(1)
    assert stroke.lower() == ink.lower()


def test_axis_and_value_text_do_not_wear_the_series_colour():
    """Text wears text tokens. A brand hue light enough to be a cheerful line is
    illegible as 9px type."""
    primary = "#0D9488"
    ink = derive_theme(primary)["primary_ink"].lower()
    svg = svg_of(report(history=full_year(), primary=primary))
    for fill in re.findall(r'<text[^>]*fill="([^"]+)"', svg):
        assert fill.lower() not in (ink, primary.lower()), fill


def test_the_gridlines_are_solid():
    """Dashing reads as 'projection' or 'threshold' when it is just a grid."""
    svg = svg_of(report(history=full_year()))
    assert "stroke-dasharray" not in svg


def test_the_note_states_the_sample_the_medians_came_from():
    html = report(history=full_year(n=8))
    assert "96 sales" in html
    assert f"fewer than {MIN_CLOSED_FOR_MEDIAN} closings" in html


def test_the_chart_carries_no_script_and_no_external_reference():
    """PDFShift renders this; anything it would have to fetch is a failure mode."""
    svg = svg_of(report(history=full_year()))
    assert "<script" not in svg
    assert "http://" not in svg and "https://" not in svg


# ── the count series, and why it is not a months-of-supply trend ─────────────

def test_a_month_with_no_closings_is_a_real_zero_in_the_count_series():
    """The opposite of the median series, deliberately.

    "No homes sold in July" is a fact about July. "The median of no sales" is
    not a quantity. Same rows, same bucketing, different treatment of empty —
    and getting it backwards either draws a crash that did not happen or hides
    a month that genuinely had none.
    """
    rows = [r for r in full_year() if "-07-" not in r["close_date"]]
    series = count_series(rows, today=TODAY)
    july = [p for p in series if p["label"] == "Jul"][0]
    assert july["value"] == 0
    assert july["value"] is not None


def test_the_count_series_ignores_the_median_minimum_sample():
    """A count of two is exactly two. The minimum exists because a median over
    two sales is noise, which does not apply to counting them."""
    rows = [r for r in full_year() if "-05-" not in r["close_date"]]
    rows += closings(5, n=2)
    series = count_series(rows, today=TODAY)
    may = [p for p in series if p["label"] == "May"][0]
    assert may["value"] == 2


def test_the_count_series_needs_no_prices():
    """It buckets on close_date alone, so rows with a missing price still count
    — a sale without a recorded price is still a sale."""
    rows = [{"close_date": r["close_date"], "close_price": None} for r in full_year()]
    series = count_series(rows, today=TODAY)
    assert sum(p["value"] for p in series) == len(rows)
    assert median_series(rows, today=TODAY) is None, "no prices, so no medians"


def test_an_empty_window_draws_nothing():
    assert count_series([], today=TODAY) is None


def test_a_truncated_fetch_is_refused_for_counts_too():
    assert count_series(full_year(), today=TODAY, truncated=True) is None


def test_the_inventory_report_gets_the_pace_series_and_market_snapshot_the_median():
    inv = report("inventory", full_year())
    assert svg_of(inv) is not None, "the inventory report should carry a trend"
    assert "Homes sold per month" in inv
    assert "Median closed price by month" in report("market_snapshot", full_year())


def test_the_pace_note_says_it_is_not_months_of_supply():
    """§7.3 asked for an MOI trend and this is not one. The note has to say so,
    because a pace line on an inventory report is exactly what a reader would
    otherwise take for supply."""
    html = report("inventory", full_year())
    assert "past inventory levels are not recoverable" in html


def test_no_report_type_outside_the_map_draws_a_trend():
    for report_type in ("closed", "price_bands", "new_listings",
                        "new_listings_gallery", "featured_listings", "open_houses"):
        assert svg_of(report(report_type, full_year())) is None, report_type


def test_a_zero_month_is_plotted_rather_than_skipped():
    """`selectattr('value')` in the macro would have dropped a real zero as a
    gap. The line must pass through it — a month at zero is the most important
    point on a pace chart."""
    rows = [r for r in full_year() if "-07-" not in r["close_date"]]
    svg = svg_of(report("inventory", rows))
    path = re.search(r'<path d="([^"]+)"', svg).group(1)
    assert path.count("M") == 1, f"the pace line broke at a zero month: {path}"




def _axis_ticks(svg):
    """The three y-axis tick labels, top to bottom."""
    return re.findall(r'text-anchor="end"[^>]*>([^<]+)</text>', svg)


def test_the_count_axis_is_anchored_at_zero():
    """Seven sales against thirteen on a baseline of five reads as a collapse.

    For a count of homes sold, zero is both meaningful and reachable, so the
    axis must start there and let the swing be its true size — the axis should
    not do the exaggerating.
    """
    ticks = _axis_ticks(svg_of(report("inventory", full_year())))
    assert ticks[-1] == "0", f"count axis floor is {ticks[-1]!r}, expected 0"


def test_the_price_axis_is_not_anchored_at_zero():
    """The other half of the same decision, and the reason it is per-series.

    A median price is never near zero; anchoring it there flattens every real
    movement into a straight line. Without this assertion, "anchor at zero"
    could be applied to both and the price chart would silently stop saying
    anything.
    """
    ticks = _axis_ticks(svg_of(report("market_snapshot", full_year())))
    assert ticks[-1] not in ("0", "$0"), (
        f"the median price axis is anchored at {ticks[-1]!r}, which flattens it"
    )
