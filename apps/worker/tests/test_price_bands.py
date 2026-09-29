"""Price bands that mean the same thing two weeks running (D-111).

The defect was not that the bands were ugly. It was that a report titled
"Price Bands" showed roughly 50/25/25 **by construction** — its boundaries
were quartiles of the current result set — so the counts could not move and
the labels moved constantly. The part carrying information was constant and
the part that is constant in reality was what changed on the page.

These assert the property that replaces it: **in an unchanging market the
boundaries hold still and the counts vary**. That is one statement and it is
the whole fix; everything else here guards a way of satisfying it dishonestly.
"""
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/worker/src"))

from worker.compute.price_bands import (  # noqa: E402
    LADDER,
    MAX_BANDS,
    MIN_HISTORY_FOR_EXTENT,
    band_edges,
    build_bands,
    choose_step,
    extent_from_history,
    format_price,
    hottest_and_slowest,
)
from worker.market_builder import HISTORY_REPORT_TYPES, TREND_REPORT_TYPES  # noqa: E402
from worker.report_builders import build_result_json  # noqa: E402


def market(n, low, high, skew=1.6, seed=None):
    rng = random.Random(seed)
    return [round(low + (high - low) * (rng.random() ** skew), -3) for _ in range(n)]


def listings(prices, **extra):
    return [{"list_price": p, "status": "Active", **extra} for p in prices]


def history(prices):
    return [{"close_price": p} for p in prices]


# ── the property the whole change exists for ────────────────────────────────

@pytest.mark.parametrize("label,n,low,high", [
    ("irvine-like", 60, 600_000, 2_400_000),
    ("smaller", 25, 350_000, 900_000),
    ("thin", 10, 400_000, 1_200_000),
])
def test_the_boundaries_hold_still_while_the_counts_move(label, n, low, high):
    """
    Draw independent weekly samples from ONE unchanging market and ask what
    each run would render. Quartiles gave 33 / 219 / 363 distinct first-band
    labels across these three markets; this asks for one edge set and for
    counts that actually differ.
    """
    rng = random.Random(20260929)
    pool = market(4000, low, high, seed=1)
    edge_sets, count_vectors = set(), set()
    for _ in range(120):
        week = listings(rng.sample(pool, n))
        past = history(rng.sample(pool, min(n * 52, len(pool))))
        built = build_bands(week, past)
        edge_sets.add(tuple(b["low"] for b in built["bands"]))
        count_vectors.add(tuple(b["count"] for b in built["bands"]))

    assert len(edge_sets) == 1, (
        f"{label}: the boundaries moved {len(edge_sets)} ways in an unchanging "
        f"market — that is the defect this replaced"
    )
    assert len(count_vectors) > 60, (
        f"{label}: only {len(count_vectors)} distinct count vectors in 120 "
        f"runs. If the counts cannot move, the boundaries are absorbing the "
        f"variation again and the report carries no information."
    )


def test_a_market_that_really_moves_gets_new_bands():
    """
    THE GUARD ON THE PROPERTY ABOVE. "Always return the same six bands"
    satisfies the stability half perfectly and is useless. Boundaries must
    follow a market that genuinely shifts a step.
    """
    cheap = build_bands(listings(market(40, 200_000, 500_000, seed=2)),
                        history(market(600, 200_000, 500_000, seed=3)))
    dear = build_bands(listings(market(40, 1_500_000, 6_000_000, seed=4)),
                       history(market(600, 1_500_000, 6_000_000, seed=5)))
    assert cheap["step"] != dear["step"], "the same step for both markets"
    assert [b["low"] for b in cheap["bands"]] != [b["low"] for b in dear["bands"]]


# ── the boundaries are round, and there are not too many ────────────────────

def test_every_boundary_is_a_multiple_of_a_ladder_step():
    built = build_bands(listings(market(40, 600_000, 2_400_000, seed=6)),
                        history(market(600, 600_000, 2_400_000, seed=7)))
    assert built["step"] in LADDER
    for band in built["bands"]:
        assert band["low"] % built["step"] == 0, f"{band['low']} is not round"


@pytest.mark.parametrize("low,high", [
    (200_000, 400_000), (350_000, 900_000), (600_000, 2_400_000),
    (1_000_000, 12_000_000), (50_000, 90_000_000),
])
def test_no_market_produces_more_bands_than_the_row_holds(low, high):
    """
    The cards are a flex row that holds six. Past that a label has under
    30px of content width and the en-dash wraps onto a line of its own — see
    MAX_BANDS for the three attempts it took to establish that, the last of
    which was rendering it and looking.
    """
    step, edges = band_edges(low, high)
    assert 1 <= len(edges) <= MAX_BANDS, f"{len(edges)} bands for {low}–{high}"
    assert step in LADDER


def test_the_top_band_is_open_ended_and_catches_the_dearest_listing():
    prices = [620_000, 900_000, 1_400_000, 3_900_000]
    built = build_bands(listings(prices), history(market(600, 600_000, 1_500_000, seed=8)))
    assert built["bands"][-1]["high"] is None, "the top band must be open-ended"
    assert sum(b["count"] for b in built["bands"]) == len(prices), (
        "a listing fell outside every band"
    )


# ── empty bands, which were unreachable before this ─────────────────────────

def test_an_empty_band_is_kept_and_counted_as_zero():
    """
    The old code dropped empty bands (`if band_listings:`), which is why the
    chart's "none" row and the cards' zero rendering have never been reached.
    With fixed boundaries an empty band is routine, and it is information:
    "nothing above $1.6M" is a fact about the market. A band that vanishes
    makes the row lie about its own shape.
    """
    prices = [620_000, 640_000, 660_000, 3_800_000]
    built = build_bands(listings(prices), history(market(600, 600_000, 4_000_000, seed=9)))
    empties = [b for b in built["bands"] if b["count"] == 0]
    assert empties, "no empty band in a market with a gap this wide"
    assert all(b["count"] is not None for b in built["bands"])


def test_the_empty_band_reaches_the_rendered_chart():
    """
    The path, not just the data. `band_distribution_chart` draws "none" for a
    zero band — added when it was unreachable, and this is the first test that
    renders one.
    """
    from worker.market_builder import MarketReportBuilder
    prices = [620_000, 640_000, 660_000, 3_800_000]
    result = build_result_json(
        "price_bands",
        listings(prices, days_on_market=12, price_per_sqft=500,
                 city="Irvine", street_address="1 A St"),
        {"city": "Irvine", "lookback_days": 30,
         "closed_history": history(market(600, 600_000, 4_000_000, seed=10))},
    )
    assert any(b["count"] == 0 for b in result["price_bands"])
    html = MarketReportBuilder({**result, "report_type": "price_bands",
                                "branding": {}}).render_html()
    assert ">none<" in html.replace(" ", "").replace("\n", "") or "none" in html, (
        "the empty band rendered nothing at all"
    )


# ── the extent, and what happens without one ────────────────────────────────

def test_too_little_history_falls_back_and_says_so_on_the_page():
    """
    A market with under twelve months of closings has no extent to anchor to.
    Falling back to this period's results is right; doing it silently is not,
    because bands that may move look identical to bands that will not.
    """
    assert extent_from_history(history(market(MIN_HISTORY_FOR_EXTENT - 1, 6e5, 9e5, seed=11))) is None
    built = build_bands(listings([700_000, 800_000]), history([900_000]))
    assert built["extent_source"] == "results"
    assert built["note"] and "may shift" in built["note"]

    plenty = build_bands(listings([700_000, 800_000]),
                         history(market(200, 600_000, 1_200_000, seed=12)))
    assert plenty["extent_source"] == "history"
    assert plenty["note"] is None


def test_the_caveat_reaches_the_chart_caption():
    from worker.market_builder import MarketReportBuilder
    rows = listings([700_000, 800_000, 1_100_000], days_on_market=9,
                    price_per_sqft=500, city="Irvine", street_address="1 A St")
    thin = build_result_json("price_bands", rows,
                             {"city": "Irvine", "lookback_days": 30,
                              "closed_history": history([900_000])})
    note = MarketReportBuilder({**thin, "report_type": "price_bands",
                                "branding": {}})._band_chart_note()
    assert "may shift between reports" in note


def test_a_listing_outside_the_years_range_still_lands_in_a_band():
    """The history sets the extent; this period must still fit inside it."""
    built = build_bands(listings([250_000, 9_000_000]),
                        history(market(300, 600_000, 1_200_000, seed=13)))
    assert sum(b["count"] for b in built["bands"]) == 2


# ── the ranking sentinel (D-108's family, in a third costume) ───────────────

def test_a_same_day_band_can_be_the_hottest():
    """
    The old ranking was
        min(bands, key=lambda b: b["avg_dom"] if b["avg_dom"] > 0 else 999)
    so a band whose sales all went under contract the day they listed scored
    999 and could never win. Zero-is-falsy in a ranking, wearing a sentinel
    rather than a filter, which is why D-108's sweep did not catch it.
    """
    bands = [
        {"label": "fast", "count": 4, "avg_dom": 0.0},
        {"label": "mid", "count": 4, "avg_dom": 20.0},
        {"label": "slow", "count": 4, "avg_dom": 60.0},
    ]
    hottest, slowest = hottest_and_slowest(bands)
    assert hottest["label"] == "fast"
    assert slowest["label"] == "slow"


def test_an_empty_band_is_not_the_hottest_just_because_it_has_no_sales():
    bands = [
        {"label": "empty", "count": 0, "avg_dom": None},
        {"label": "real", "count": 4, "avg_dom": 18.0},
    ]
    hottest, slowest = hottest_and_slowest(bands)
    assert hottest["label"] == "real" and slowest["label"] == "real"


def test_no_band_with_sales_means_no_ranking_rather_than_a_wrong_one():
    hottest, slowest = hottest_and_slowest([{"label": "e", "count": 0, "avg_dom": None}])
    assert hottest["avg_dom"] is None and hottest["label"] == "—"


# ── who pays for the fetch ──────────────────────────────────────────────────

def test_price_bands_is_in_the_history_set_but_not_the_trend_set():
    """
    It needs the same twelve months for a different reason — to size
    boundaries, not to draw a line. Folding it into TREND_REPORT_TYPES would
    make it fetch a trend it never draws.
    """
    assert "price_bands" in HISTORY_REPORT_TYPES
    assert "price_bands" not in TREND_REPORT_TYPES
    assert TREND_REPORT_TYPES < HISTORY_REPORT_TYPES


# ── labels ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("value,expected", [
    (250_000, "$250K"), (750_000, "$750K"), (900_000, "$900K"),
    (1_000_000, "$1M"), (1_500_000, "$1.5M"), (2_000_000, "$2M"),
    # THE ONE THAT MATTERS. $250K is one of the commonest steps on the
    # ladder, so $1.25M is a boundary the product routinely draws — and one
    # decimal place rendered it "$1.2M", stating a boundary the band does not
    # have. A reader putting a $1,240,000 listing into "$1.2M – $1.5M" would
    # be putting it in the wrong band. Found by this test, not by reading.
    (1_250_000, "$1.25M"), (1_750_000, "$1.75M"),
])
def test_a_label_states_the_boundary_the_band_actually_has(value, expected):
    assert format_price(value) == expected


def test_every_boundary_the_ladder_can_draw_round_trips_through_its_label():
    """
    The property behind the case above: no step on the ladder, at any
    multiple in a plausible price range, may render a label that names a
    different number.
    """
    import re
    for step in LADDER:
        for k in range(1, 40):
            value = step * k
            if value > 40_000_000:
                break
            label = format_price(value)
            digits = float(re.sub(r"[^0-9.]", "", label))
            scale = 1_000_000 if label.endswith("M") else 1_000
            assert digits * scale == value, (
                f"{value:,} renders as {label}, which names {digits * scale:,.0f}"
            )
