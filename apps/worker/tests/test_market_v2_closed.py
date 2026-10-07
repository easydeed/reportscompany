"""The `closed` kind on Design's `_v2` page — the builder half.

Design's market package is adopted one kind at a time, as the property surface
was. `market_builder.V2_KINDS` is the seam: a kind not in it renders exactly as
it does today. `closed` is first because it is the table kind WITH continuation
pages, so it exercises `header.start_at = 1`, `footer.start_at = 1` and the row
capacity together — the architectural risks, which if wrong invalidate the other
seven kinds.

It is NOT first for contrast. All six `market__*` baseline rows are badge
selectors on `new_listings` and `price_bands`, so wiring `closed` closes zero of
them by construction — established before building it, by the heuristic D-171
and D-177 produced: ask where a token paints before estimating what it closes.

WHAT THIS FILE COVERS: the band values and the table rows, which are Python.
The page template is separate and so is its test.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "scripts"))

from measure_market_pagination import report_data  # noqa: E402
from worker.market_builder import (  # noqa: E402
    V2_DASH, V2_KINDS, V2_LABEL_LADDER, V2_NO_DATA, MarketReportBuilder,
    _ratio_as_percent, _v2_beds_baths, _v2_label_size,
)
from worker.template_filters import format_currency_short  # noqa: E402


def builder(report_type="closed", n=20, **over):
    data = report_data(report_type, n)
    data["ai_insights"] = None          # Design: no narrative on table kinds
    data.update(over)
    return MarketReportBuilder(data)


# ─────────────────────────────────────────────────────────────────────────────
# The seam
# ─────────────────────────────────────────────────────────────────────────────

def test_the_seam_holds_one_kind():
    """A kind in `V2_KINDS` must have a band spec, or the band renders empty.

    The property surface's `V2_THEMES` had the same contract. Adding a kind
    here without its per-kind band values is the mistake this guards, and
    `_v2_band` raises rather than returning a shell.
    """
    assert V2_KINDS == frozenset({"closed"}), (
        f"V2_KINDS is {set(V2_KINDS)}. Every kind in it needs its own band "
        f"values from Design's per-kind table — big number, label, pill, three "
        f"stats — and `_v2_band` raises NotImplementedError without them."
    )
    for kind in V2_KINDS:
        band = builder(kind)._v2_band()
        assert band["big"] is not None and band["label"]
        assert len(band["cells"]) == 3


def test_a_kind_without_a_band_spec_raises_rather_than_rendering_empty():
    b = builder("inventory")
    b.report_type = "inventory"
    with pytest.raises(NotImplementedError):
        b._v2_band()


# ─────────────────────────────────────────────────────────────────────────────
# D-178 — one scale, normalised once
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,want", [
    (0.982, 98.2),      # the fixture's scale
    (98.2, 98.2),       # production's scale (compute/extract.py:79)
    (1.0, 100.0),       # 100% as a fraction
    (100, 100.0),       # 100% as a percent
    (0, None),          # not a sale at asking
    (None, None),
    (True, None),       # a bool is not a ratio
    ("98.2", None),     # nor is a string
])
def test_the_ratio_is_normalised_to_percent(raw, want):
    """The same key arrives on two scales and the templates used to guess.

    `macros.jinja2` carried `ratio * 100 if ratio < 2 else ratio` at TWO sites.
    One copy now, in Python, with a test — which is the whole of D-178.
    """
    assert _ratio_as_percent(raw) == want


def test_the_band_pill_reads_as_a_percentage():
    pill = builder()._v2_band()["pill"]
    assert pill and pill.endswith("% of asking"), pill
    value = float(pill.split("%")[0])
    assert 50 <= value <= 150, (
        f"the pill reads {pill!r}. A fraction rendered as a percent gives "
        f"'1.0% of asking', which is what D-178 was."
    )


def test_a_missing_ratio_drops_the_pill_rather_than_printing_zero():
    b = builder()
    b.report_data["metrics"] = dict(b.report_data["metrics"])
    b.report_data["metrics"].pop("list_to_sale_ratio", None)
    assert b._v2_band()["pill"] is None


# ─────────────────────────────────────────────────────────────────────────────
# The over-asking count, and the vs-list colour rule
# ─────────────────────────────────────────────────────────────────────────────

def test_over_asking_counts_only_sales_that_cleared_asking():
    b = builder(n=5)
    for item in b.report_data["listings"][:3]:
        item["close_price"] = item["list_price"] * 1.05
    assert b._v2_band()["cells"][2]["value"] == "3"


def test_a_listing_with_no_list_price_is_not_counted_as_over_asking():
    """Absent is not a default (D-137). `close > None` would raise; `close > 0`
    would count every sale as over asking, which is the quiet version."""
    b = builder(n=4)
    for item in b.report_data["listings"]:
        item["list_price"] = None
    assert b._v2_band()["cells"][2]["value"] == V2_NO_DATA


def test_a_non_numeric_list_price_does_not_crash_the_count():
    """What the `isinstance` guard actually protects, found by the harness.

    A mutation that removed the guard did NOT fail this file — `if not lst:
    continue` catches a None, so the type check looked redundant. It is not:
    a STRING list price (`"500000"`, which a feed can yield) is truthy, reaches
    `close > lst`, and raises TypeError. The guard is the only thing between a
    typed feed value and a 500 on the render path.

    So the mutation was badly constructed AND the case was untested. Both were
    invisible until the harness reported `DID NOT FIRE`.
    """
    b = builder(n=3)
    for item in b.report_data["listings"]:
        item["list_price"] = "500000"
    assert b._v2_band()["cells"][2]["value"] == V2_NO_DATA


def test_the_vs_list_rule_fires_above_asking_and_not_at_it():
    """Design: ">100% in `accent_ink` 600, else `#5E636B` 400".

    At exactly 100% a sale did not clear asking, so the emphasis is wrong
    there — and `>=` is the easiest way to get this wrong.
    """
    b = builder(n=3)
    listings = b.report_data["listings"]
    listings[0]["close_price"] = listings[0]["list_price"]          # exactly
    listings[1]["close_price"] = listings[1]["list_price"] * 1.01   # over
    listings[2]["close_price"] = listings[2]["list_price"] * 0.99   # under
    flags = [row["vs_over"] for row in b._v2_table()["rows"]]
    assert flags == [False, True, False], flags


# ─────────────────────────────────────────────────────────────────────────────
# Formatting — Design's casing, without a second formatter
# ─────────────────────────────────────────────────────────────────────────────

def test_designs_casing_does_not_change_every_other_surface():
    """`upper` is a flag, not a fork. The lowercase `k` ships everywhere else."""
    assert format_currency_short(470000) == "$470k"
    assert format_currency_short(470000, upper=True) == "$470K"
    assert format_currency_short(1200000) == format_currency_short(
        1200000, upper=True) == "$1.2M"


@pytest.mark.parametrize("item,want", [
    ({"beds": 3, "baths": 2}, "3/2"),
    ({"beds": 3, "baths": 1.5}, "3/1.5"),
    ({"beds": 0, "baths": 1}, "0/1"),        # a studio is not missing data
    ({"beds": 3, "baths": None}, f"3/{V2_DASH}"),
    ({"beds": None, "baths": None}, V2_DASH),
])
def test_beds_baths_distinguishes_zero_from_absent(item, want):
    """D-108 and D-168 both shipped as `or` chains over these two fields."""
    assert _v2_beds_baths(item) == want


def test_the_label_ladder_is_designs_and_steps_down():
    """A fixed 50px box, so the type steps rather than the band growing."""
    sizes = [_v2_label_size("x" * n) for n in (10, 26, 27, 34, 35, 44, 45)]
    assert sizes == [22, 22, 18, 18, 15, 15, 13], sizes
    assert V2_LABEL_LADDER == ((26, 22), (34, 18), (44, 15))


# ─────────────────────────────────────────────────────────────────────────────
# The table, against the pinned capacity
# ─────────────────────────────────────────────────────────────────────────────

def test_the_table_reports_what_it_shows_and_what_exists():
    """"Showing 13 of N" is a claim about two numbers, and both are read from
    `_build_listings_context` rather than recomputed — `closed`'s cap is 200,
    so a 20-listing fixture shows all of them and the line must say 20 of 20
    rather than 13 of anything."""
    table = builder(n=20)._v2_table()
    assert table["showing"] == 20
    assert table["total"] == 20
    assert len(table["rows"]) == 20


def test_every_row_has_every_column_design_specifies():
    columns = {"address", "hood", "beds_baths", "sqft", "price", "vs_list",
               "vs_over", "days"}
    rows = builder(n=5)._v2_table()["rows"]
    assert rows
    for row in rows:
        assert set(row) == columns, sorted(set(row) ^ columns)
