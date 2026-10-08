"""The table kinds on Design's `_v2` page — `closed` and `new_listings`.

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

WHAT THIS FILE COVERS: the band values and the table rows for both wired
kinds, which are Python. Renamed from `test_market_v2_closed.py` when the
second kind landed — a file named after one instance of a seam describes that
instance, which is §0.6's rule about selectors applied to a filename.
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
    assert V2_KINDS == frozenset({"closed", "new_listings"}), (
        f"V2_KINDS is {set(V2_KINDS)}. Every kind in it needs its own band "
        f"values from Design's per-kind table — big number, label, pill, three "
        f"stats — and `_v2_band` raises NotImplementedError without them."
    )
    for kind in V2_KINDS:
        band = builder(kind)._v2_band()
        assert band["big"] is not None and band["label"]
        assert len(band["cells"]) == 3


def test_a_kind_without_a_band_spec_raises_rather_than_rendering_empty():
    # `inventory` is `closed`'s twin and is NOT in V2_KINDS, so it stands in
    # for "a kind someone added to the seam without its band values".
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
    flags = [row["emphasis"] for row in b._v2_table()["rows"]]
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
    # `fifth` and `emphasis`, not `vs_list`/`vs_over`: the fifth column means
    # "vs. list" on `closed` and "Listed" on `new_listings`, so the row carries
    # one shape and the page reads one shape whichever kind rendered.
    columns = {"address", "hood", "beds_baths", "sqft", "price", "fifth",
               "emphasis", "days"}
    rows = builder(n=5)._v2_table()["rows"]
    assert rows
    for row in rows:
        assert set(row) == columns, sorted(set(row) ^ columns)


def test_a_v2_render_does_not_pay_for_a_narrative_it_discards(monkeypatch):
    """What the `V2_KINDS` narrative suppression actually buys.

    Not determinism — the `_v2` page has no narrative block, so prose could not
    move the pagination even if it were generated. A mutation removing the
    suppression came back `DID NOT FIRE`, which is how that claim got checked
    and corrected.

    What it buys is not paying for it: an OpenAI round trip per render whose
    output the template discards. So the assertion is about the CALL, which is
    the thing that changes.
    """
    import worker.market_builder as mb

    calls = []
    monkeypatch.setattr(
        mb, "generate_market_pdf_narrative",
        lambda *a, **k: calls.append(a) or "some generated prose")

    b = builder()
    b.report_data["ai_insights"] = ""      # nothing pre-supplied
    html = b.render_html()
    assert calls == [], (
        f"a v2 render called the narrative generator {len(calls)} time(s). "
        f"The page discards the result, so this is a paid-for round trip with "
        f"no output."
    )
    assert "some generated prose" not in html

    # The control: a kind that has NOT moved still generates one, so this is
    # not asserting that the generator is simply unreachable.
    other = builder("inventory")
    other.report_data["ai_insights"] = ""
    other.render_html()
    assert calls, (
        "a non-v2 kind did not call the narrative generator either, so the "
        "assertion above proves nothing about the seam."
    )


# ─────────────────────────────────────────────────────────────────────────────
# `new_listings` — the second kind, and the one that saves eleven pages.
#
# Added because the regression harness reported three mutations as DID NOT
# FIRE: the kind was wired and nothing tested what makes it different from
# `closed`. The seam's whole purpose is that the two kinds differ, so the
# differences are what needs covering.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("days,want", [
    (0, "Today"),        # THE INTERESTING VALUE — a listing that went live
                         # today reports 0, and `or` reads that as missing
    (1, "1 d ago"),
    (14, "14 d ago"),
    (None, V2_DASH),
    (True, V2_DASH),     # a bool is not a day count
    ("3", V2_DASH),
])
def test_listed_renders_today_at_zero_days(days, want):
    from worker.market_builder import _v2_listed_label
    assert _v2_listed_label(days) == want


def test_new_listings_shows_the_list_price_not_a_sale_price():
    """A new listing has no sale price, so reading `close or list` would be
    right by accident. Given a close price it must still show the list one."""
    b = builder("new_listings", n=3)
    for item in b.report_data["listings"]:
        item["list_price"] = 500_000
        item["close_price"] = 925_000      # must be ignored on this kind
    prices = {row["price"] for row in b._v2_table()["rows"]}
    assert prices == {"$500K"}, prices


def test_the_fifth_column_and_the_noun_are_per_kind():
    """One row shape, two meanings — and the count line's word matters.

    "20 sales" on a new-listings report is the number right and the word
    wrong, which nothing but a reader would catch.
    """
    closed = builder("closed", n=4)._v2_table()
    new = builder("new_listings", n=4)._v2_table()
    assert closed["columns"]["price"] == "Sold for"
    assert closed["columns"]["fifth"] == "vs. list"
    assert closed["noun"] == "sales" and closed["noun_one"] == "sale"
    assert new["columns"]["price"] == "List price"
    assert new["columns"]["fifth"] == "Listed"
    assert new["noun"] == "new listings" and new["noun_one"] == "new listing"
    assert closed["noun"] != new["noun"], (
        "both kinds share a count-line noun, so one of them is wrong"
    )


def test_new_listings_emphasises_a_listing_posted_today():
    """The same accent rule, a different fact: `closed` accents over asking,
    `new_listings` accents listed-today. One rule in the page, two facts."""
    b = builder("new_listings", n=3)
    days = [0, 5, 12]
    for item, d in zip(b.report_data["listings"], days):
        item["days_on_market"] = d
    rows = b._v2_table()["rows"]
    assert [r["emphasis"] for r in rows] == [True, False, False]
    assert [r["fifth"] for r in rows] == ["Today", "5 d ago", "12 d ago"]


def test_the_new_listings_band_carries_designs_three_stats():
    """Median list · Under $1M · Of inventory, and a price-range pill."""
    band = builder("new_listings", n=20)._v2_band()
    assert [c["label"] for c in band["cells"]] == [
        "Median list", "Under $1M", "Of inventory"]
    assert band["label"].startswith("new listings in ")
    assert band["pill_sub"] == "this week"
    assert band["pill"] and " – " in band["pill"], band["pill"]


def test_the_price_range_comes_from_the_listings_not_from_a_metric():
    """No metric reports a range, and inventing one from a median would be a
    number with no source."""
    b = builder("new_listings", n=3)
    for item, p in zip(b.report_data["listings"], (400_000, 1_250_000, 800_000)):
        item["list_price"] = p
    assert b._v2_band()["pill"] == "$400K – $1.2M"


def test_share_of_inventory_is_absent_rather_than_zero_without_an_active_count():
    """D-137: "0% of inventory" is a claim; a market with no recorded active
    count has no share to state."""
    b = builder("new_listings", n=4)
    b.report_data["counts"] = dict(b.report_data["counts"] or {})
    b.report_data["counts"]["Active"] = 0
    assert b._v2_band()["cells"][2]["value"] == V2_NO_DATA


def test_under_a_million_counts_rather_than_shares():
    b = builder("new_listings", n=4)
    for item, p in zip(b.report_data["listings"],
                       (400_000, 999_999, 1_000_000, 2_000_000)):
        item["list_price"] = p
    assert b._v2_band()["cells"][1]["value"] == "2"
