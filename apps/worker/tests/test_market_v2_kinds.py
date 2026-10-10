"""The kinds wired onto Design's `_v2` page — `closed`, `new_listings`,
`price_bands`.

Design's market package is adopted one kind at a time, as the property surface
was. `market_builder.V2_KINDS` is the seam: a kind not in it renders exactly as
it does today. `closed` was first because it is the table kind WITH
continuation pages, so it exercises `header.start_at = 1`,
`footer.start_at = 1` and the row capacity together — the architectural risks,
which if wrong invalidate the other seven kinds.

It was NOT first for contrast. All six `market__*` baseline rows were badge
selectors on `new_listings` and `price_bands`, so wiring `closed` closed zero
of them by construction — established before building it, by the heuristic
D-171 and D-177 produced: ask where a token paints before estimating what it
closes. The prediction held exactly at every step: 0 for `closed`, 3 for
`new_listings`, 3 for `price_bands`, and the market surface is now at zero
baselined failures.

WHAT THIS FILE COVERS: the band values and the per-kind body values, which are
Python. The `price_bands` BODY — the band rows, the bar scale and the
no-count-is-not-zero distinction — lives in `test_band_chart.py`, which was
repointed from the old chart rather than deleted.

Renamed twice: from `test_market_v2_closed.py` when the second kind landed, and
from `test_market_v2_table_kinds.py` when `price_bands` landed and the seam
stopped being all table kinds. Both for the same reason — a file named after
one instance of a seam describes that instance, which is §0.6's rule about
selectors applied to a filename. The name is now the seam itself, so it should
not need renaming again.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "scripts"))

from measure_market_pagination import report_data  # noqa: E402
from worker.market_builder import (  # noqa: E402
    ALL_REPORT_TYPES, V2_DASH, V2_GRID, V2_KINDS, V2_LABEL_LADDER,
    V2_NEW_WITHIN_DAYS, V2_NO_DATA, MarketReportBuilder,
    _ratio_as_percent, _v2_beds_baths, _v2_card_specs, _v2_label_size,
)


def a_kind_outside_the_seam() -> str:
    """A report type that has NOT moved to the `_v2` page, derived.

    THREE TESTS IN THIS FILE NAMED `inventory` FOR THIS, and `inventory` moved
    into the seam on 2026-10-08 — so each of them silently stopped being a
    control and started being a second assertion about a `_v2` kind. One of the
    three even carried the comment "`inventory`, not `closed`: closed renders
    the `_v2` page now", which is the same substitution one kind earlier.

    **A positive control drawn from the set being migrated is consumed by the
    migration.** So it is derived from the remainder and the remainder is
    asserted non-empty: when the last kind moves, these tests say their control
    is gone rather than quietly passing for the wrong reason.
    """
    outside = sorted(set(ALL_REPORT_TYPES) - V2_KINDS)
    assert outside, (
        "every report type is now in V2_KINDS, so there is no kind left to act "
        "as the control for these tests. They are no longer proving what they "
        "say — replace the control with a synthetic report type, or retire the "
        "tests with the seam."
    )
    return outside[0]
from worker.template_filters import format_currency_short  # noqa: E402


def builder(report_type="closed", n=20, **over):
    data = report_data(report_type, n)
    data["ai_insights"] = None          # Design: no narrative on table kinds
    data.update(over)
    return MarketReportBuilder(data)


# ─────────────────────────────────────────────────────────────────────────────
# The seam
# ─────────────────────────────────────────────────────────────────────────────

def test_every_kind_in_the_seam_has_its_band_values():
    """A kind in `V2_KINDS` must have a band spec, or the band renders empty.

    The property surface's `V2_THEMES` had the same contract. Adding a kind
    here without its per-kind band values is the mistake this guards, and
    `_v2_band` raises rather than returning a shell.

    THE SET IS PINNED, not derived, and that is the point: adding a kind to the
    seam should fail a test until someone writes the kind's band values and
    updates this line. It was named `..._holds_one_kind` when there was one,
    which was a name that went stale the moment the second landed.
    """
    assert V2_KINDS == frozenset({"closed", "new_listings", "price_bands",
                                  "inventory", "new_listings_gallery",
                                  "open_houses", "featured_listings"}), (
        f"V2_KINDS is {set(V2_KINDS)}. Every kind in it needs its own band "
        f"values from Design's per-kind table — big number, label, pill, three "
        f"stats — and `_v2_band` raises NotImplementedError without them."
    )
    for kind in V2_KINDS:
        band = builder(kind)._v2_band()
        assert band["big"] is not None, f"{kind} has no big number"
        assert len(band["cells"]) == 3, f"{kind} has {len(band['cells'])} stats"
        # `label` is NOT asserted truthy: on `price_bands` Design's headline
        # rule deliberately returns no label when the data cannot support the
        # claim, and the plain title goes in `big` instead. Requiring a label
        # here would have forced the claim to be made.
        assert "label" in band


def test_a_kind_without_a_band_spec_raises_rather_than_rendering_empty():
    """A kind outside the seam stands in for one added to it without values.

    The control is DERIVED, not named — see `a_kind_outside_the_seam`.
    """
    kind = a_kind_outside_the_seam()
    b = builder(kind)
    b.report_type = kind
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
    # not asserting that the generator is simply unreachable. DERIVED — this
    # line said `inventory` until `inventory` joined the seam.
    other = builder(a_kind_outside_the_seam())
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


# ─────────────────────────────────────────────────────────────────────────────
# `price_bands` — the third kind, and NOT a table.
#
# Design's bands kind renders seven fixed band rows and no listings table, so
# it is the first kind to exercise the page's body dispatch. It is also the
# kind that closed the last three market baseline rows.
# ─────────────────────────────────────────────────────────────────────────────

def bands(rows):
    """A `price_bands` builder with the band rows given."""
    b = builder("price_bands", n=20)
    b.report_data["price_bands"] = rows
    return b


def band_row(count, dom, label=None, median=1_000_000, ppsf=500):
    return {"label": label or f"band-{dom}", "count": count,
            "median_price": median, "avg_dom": dom, "avg_ppsf": ppsf}


def test_price_bands_renders_bands_and_no_table():
    """The body dispatch, asserted both ways.

    A kind that rendered both bodies would paginate as neither, and a kind
    that rendered the wrong one would still look like a report.
    """
    b = builder("price_bands", n=20)
    html = b.render_html()
    assert 'class="brow"' in html, "the bands body did not render"
    assert 'class="trow"' not in html, "a table rendered on the bands kind"
    table = builder("closed", n=5).render_html()
    assert 'class="brow"' not in table, "the bands body rendered on a table kind"


@pytest.mark.parametrize("report_type", sorted(V2_KINDS))
def test_the_v2_page_ships_no_html_comment(report_type):
    """JINJA DOES NOT TREAT `<!-- -->` AS A COMMENT, and the page found out.

    A note added beside the label guard was written as an HTML comment and
    quoted the expression it was about. Jinja substituted it, so the rendered
    page carried the literal `None` **inside a comment** — invisible to the
    gate that reads the page for a bare `None`, and visible to anyone reading
    the template source as evidence the guard did not work.

    Two separate reasons to have none of them here. The first is that: a
    template comment must be `{#  #}`, which never renders, rather than one
    that renders and then hides what it rendered. The second is plainer — an
    HTML comment ships to the client, and this document is sent to PDFShift
    and then to an agent's customer.
    """
    html = builder(report_type, n=12).render_html()
    assert "<!--" not in html, (
        f"{report_type}'s page ships an HTML comment. In a Jinja template a "
        f"`<!-- -->` comment is rendered, not skipped, so any expression inside "
        f"it is substituted and then hidden from every gate that reads the "
        f"page. Use `{{#  #}}`."
    )
    for leftover in ("{{", "{%"):
        assert leftover not in html, (
            f"{report_type}'s page contains an unrendered {leftover!r}"
        )


def test_a_refused_headline_renders_no_label_and_not_the_word_none():
    """`autoescape=False` prints `None` where a template prints a missing value.

    `_v2_fastest_headline` returns `label=None` whenever it refuses, which is
    most of the time by design — and the template's label span was
    unconditional, so the band read

        {Area} · Price Bands
        None

    at 22px, under the plain title. Caught by
    `tests/test_market_templates.py::test_no_undefined_values[price_bands]`,
    which is the only gate on this surface that reads the rendered page for a
    bare `None`, and which only began covering this kind when it joined the
    seam — the third kind's move to find untested behaviour.

    The 50px label box stays; only the span is conditional, so the band's
    height does not move between a kind that has a label and one that does not.
    """
    html = bands([band_row(4, 8), band_row(4, 40)]).render_html()
    assert "· Price Bands" in html, "the plain title did not render"
    assert ">None<" not in html and "None</span>" not in html
    assert 'class="band-label"' not in html, (
        "the label span rendered for a headline that refused to make a claim"
    )
    assert 'class="band-label-box"' in html, (
        "the fixed 50px box went with the span, so the band is now a "
        "different height on this kind"
    )
    # And the other way: when the claim IS made, the label is there.
    claimed = bands([band_row(12, 8), band_row(12, 40)]).render_html()
    assert 'class="band-label"' in claimed
    assert "is moving fastest" in claimed


def test_the_big_number_is_designs_size_per_kind():
    """88px default, 64px for bands — a price range does not fit at 88."""
    assert builder("closed")._v2_band()["big_px"] == 88
    assert builder("new_listings")._v2_band()["big_px"] == 88
    assert builder("price_bands")._v2_band()["big_px"] == 64


# ── Design's headline rule, which mostly refuses ─────────────────────────────

def test_the_fastest_headline_needs_ten_listings():
    """Design: the claim only when the band has >=10 listings."""
    nine = bands([band_row(9, 8), band_row(12, 30), band_row(12, 40)])._v2_band()
    assert nine["label"] is None
    assert nine["big"].endswith("· Price Bands"), nine["big"]
    ten = bands([band_row(10, 8), band_row(12, 30), band_row(12, 40)])._v2_band()
    assert ten["label"] == "is moving fastest"


def test_the_fastest_headline_needs_three_days_ahead_of_the_area():
    """And >=3 days faster than the area average, not than the slowest band."""
    close = bands([band_row(12, 20), band_row(12, 21), band_row(12, 22)])._v2_band()
    assert close["label"] is None, close
    clear = bands([band_row(12, 8), band_row(12, 22), band_row(12, 40)])._v2_band()
    assert clear["label"] == "is moving fastest"
    assert clear["pill_sub"] == "15 days faster than the area"


def test_a_single_band_cannot_be_faster_than_itself():
    """The degenerate case: with one band the area average IS that band, so it
    is 0 days ahead and the claim must be refused. A rule comparing a value to
    an average it dominates is the shape worth checking at n=1."""
    one = bands([band_row(12, 10)])._v2_band()
    assert one["label"] is None, one


def test_bands_with_no_speed_refuse_the_headline_entirely():
    """`avg_dom` is None for a band with no sales — and for EVERY band on the
    preview path, because it is computed from `closed_history`, which only
    production supplies (D-173's family). So the plain title is what the
    branding preview shows, and that is correct rather than broken."""
    none = bands([band_row(12, None), band_row(12, None)])._v2_band()
    assert none["label"] is None
    assert none["pill"] is None


# ── The rows ─────────────────────────────────────────────────────────────────

def test_the_bar_is_a_share_of_the_largest_band_not_of_the_total():
    """A share of the total makes every bar short once there are several
    bands, and Design's row is a comparison rather than a composition."""
    rows = bands([band_row(10, 10), band_row(5, 20), band_row(1, 30)]
                 )._v2_bands_body()["rows"]
    assert [r["bar_pct"] for r in rows] == [100, 50, 10]


def test_the_fastest_and_slowest_tags_land_on_one_band_each():
    rows = bands([band_row(12, 8), band_row(12, 22), band_row(12, 40)]
                 )._v2_bands_body()["rows"]
    assert [r["tag"] for r in rows] == ["Fastest", None, "Slowest"]
    assert [r["is_fastest"] for r in rows] == [True, False, False]
    assert [r["is_slowest"] for r in rows] == [False, False, True]


def test_one_band_carries_no_tag_because_there_is_nothing_to_compare_it_to():
    """A COMPARATIVE TAG NEEDS TWO THINGS TO COMPARE.

    `hottest_and_slowest` returns the single band for both, so a literal read
    would tag it "Fastest Slowest". This test's first version fixed half of
    that — it asserted "Fastest" and not also "Slowest" — and shipped the
    other half: a lone band labelled the fastest of one.

    Found by `test_band_chart.py`, repointed from the chart this page replaced,
    which rendered the row and read the tag off the page. The headline already
    refuses here for the same arithmetic (a band is 0 days ahead of an average
    that is itself); the body's tag now refuses too, and both refusals are the
    same sentence: there is nothing to be faster than.
    """
    rows = bands([band_row(12, 10)])._v2_bands_body()["rows"]
    assert rows[0]["is_fastest"] is False
    assert rows[0]["is_slowest"] is False
    assert rows[0]["tag"] is None


def test_two_ranked_bands_are_enough_for_a_tag():
    """The boundary above, from the other side — a refusal that never lifts is
    indistinguishable from a feature that does not work (§0.6)."""
    rows = bands([band_row(12, 8), band_row(12, 40)])._v2_bands_body()["rows"]
    assert [r["tag"] for r in rows] == ["Fastest", "Slowest"]


def test_an_uncounted_band_does_not_count_towards_the_two():
    """`rankable` requires a known count AND a known speed.

    A band with `avg_dom` and no `count` key is not in the ranking — the same
    distinction `_v2_known_count` draws for the bar — so it cannot be the
    second band that licenses a tag on the first.
    """
    rows = bands([band_row(12, 8),
                  {"label": "$2M+", "avg_dom": 40}])._v2_bands_body()["rows"]
    assert [r["tag"] for r in rows] == [None, None]
    assert rows[1]["count"] == V2_DASH


def test_a_band_with_no_sales_is_kept_and_carries_no_tag():
    """`build_bands` keeps empty bands deliberately — "nothing above $1.6M" is
    a fact about the market. An empty band has no speed, so no tag."""
    rows = bands([band_row(12, 8), band_row(0, None, label="$2M+")]
                 )._v2_bands_body()["rows"]
    assert len(rows) == 2
    empty = rows[1]
    assert empty["count"] == "0" and empty["bar_pct"] == 0
    assert empty["tag"] is None and empty["days"] == V2_DASH


def test_the_slow_tag_is_designs_measured_hex():
    """`#B42318`, which Design measured at 5.9:1. The fastest tag is derived
    (`accent_ink`); only this one is a literal, because "slow" is not a brand
    colour on any brand."""
    body = bands([band_row(12, 8), band_row(12, 40)])._v2_bands_body()
    assert body["slow_tag"] == "#B42318"
    html = builder("price_bands", n=20).render_html()
    assert "#B42318" in html


# ─────────────────────────────────────────────────────────────────────────────
# `inventory` — the fourth kind, and the one whose payoff is zero of both.
#
# Five pages before and after, and the contrast baseline was already empty, so
# nothing here is measured as a saving. What it is, is `closed`'s twin with one
# column changed and one pill that makes a CLAIM — "seller's market" — which is
# the first time Design's package asks this surface to interpret rather than
# report. That claim is what these cover.
# ─────────────────────────────────────────────────────────────────────────────

def inv(n=20, **over):
    return builder("inventory", n=n, **over)


def test_inventory_renders_the_table_and_designs_columns():
    b = inv()
    html = b.render_html()
    assert 'class="trow thead"' in html and 'class="brow' not in html
    cols = b._v2_table()["columns"]
    assert cols["price"] == "List price", cols
    assert cols["fifth"] == "Status", cols


def test_the_count_line_says_homes_for_sale_and_not_sales():
    """`noun` per kind. "212 sales" on an inventory report is a number that is
    right about something else — the hardest kind of wrong to see."""
    table = inv()._v2_table()
    assert table["noun"] == "homes for sale"
    assert table["noun_one"] == "home for sale"
    assert "sale" in table["noun"] and "sold" not in table["noun"]


@pytest.mark.parametrize("dom,want_fifth,want_emphasis", [
    (0, "New", True),            # listed today — the boundary that matters most
    (1, "New", True),
    (7, "New", True),            # INCLUSIVE: Design says `<= 7`
    (8, V2_DASH, False),         # one day past
    (90, V2_DASH, False),
    (None, V2_DASH, False),      # absent is not fresh
    (True, V2_DASH, False),      # a bool is not a day count
    ("3", V2_DASH, False),       # nor is a string
])
def test_the_status_column_is_new_within_a_week_inclusive(dom, want_fifth,
                                                          want_emphasis):
    """Design: "`New` in `accent_ink` 600 when DOM <= 7, else `—` 400".

    Seven is inclusive and the test says so at the boundary, because `< 7` and
    `<= 7` differ on one day in seven and neither reads wrong in a diff.
    """
    rows = inv(n=1, listings=[{
        "street_address": "1 A St", "city": "Irvine", "list_price": 900000,
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800,
        "status": "Active", "days_on_market": dom,
    }])._v2_table()["rows"]
    assert rows[0]["fifth"] == want_fifth
    assert rows[0]["emphasis"] is want_emphasis


def test_inventory_shows_the_list_price_and_never_a_sale_price():
    """A home for sale has not sold. `closed`'s `close if close else lst` would
    be the right value by accident on a feed that leaks a close price."""
    rows = inv(n=1, listings=[{
        "street_address": "1 A St", "city": "Irvine",
        "list_price": 900000, "close_price": 1_400_000,
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800,
        "status": "Active", "days_on_market": 3,
    }])._v2_table()["rows"]
    assert rows[0]["price"] == format_currency_short(900000, upper=True)
    assert "1.4M" not in rows[0]["price"]


def test_a_kind_with_columns_but_no_fifth_column_rule_raises():
    """The `else` that used to be `closed`'s ratio.

    An unwired kind given table columns would have rendered a page of dashes
    under its own header — finished-looking and silent. It raises now.
    """
    b = inv()
    b.report_type = "market_snapshot"
    import worker.market_builder as mb
    original = mb.V2_TABLE_COLUMNS
    mb.V2_TABLE_COLUMNS = {**original, "market_snapshot": original["closed"]}
    try:
        with pytest.raises(NotImplementedError):
            b._v2_table()
    finally:
        mb.V2_TABLE_COLUMNS = original


def test_the_band_counts_homes_for_sale_not_listings_in_a_window():
    band = inv()._v2_band()
    assert "homes for sale in" in band["label"]
    assert [c["label"] for c in band["cells"]] == [
        "Median list", "New this week", "Avg. days listed"]


@pytest.mark.parametrize("moi,want_pill,want_label", [
    (1.9, "1.9 months", "seller's market"),
    (3.9, "3.9 months", "seller's market"),   # just inside
    # "4.0 months", NOT "4 months". `compute.moi.describe` formats `f"{moi}
    # months"` and does not strip a trailing zero. `property_builder.py:2683`
    # DOES (`f"{moi:.1f}".rstrip("0").rstrip(".")`), so the two surfaces print
    # a whole number differently — noted on D-182 rather than changed here,
    # because `describe` is shared and its output is pinned by other tests.
    (4.0, "4.0 months", "balanced market"),   # THE BOUNDARY: 4 is balanced
    (6.0, "6.0 months", "balanced market"),   # inclusive at the top
    (6.1, "6.1 months", "buyer's market"),
    (0, "0 months", "seller's market"),       # NOTHING FOR SALE — see below
])
def test_the_pill_classifies_the_market_at_the_shared_thresholds(
        moi, want_pill, want_label):
    """Design: "1.9 months" / "of inventory · seller's market".

    THE THRESHOLDS ARE `compute.moi`'s, not this page's. They were
    reimplemented six times at two different values before this (D-182), and a
    seventh copy on a new page is how that reaches a fourth surface.

    MOI of exactly 0 is a real answer and the most seller-favourable market
    there can be — nothing is for sale. A truthiness test would drop it into
    the unknown branch, giving the OPPOSITE of the right answer.
    """
    pill, sub = inv(metrics={"months_of_inventory": moi})._v2_inventory_pill()
    assert pill == want_pill
    assert sub == f"of inventory · {want_label}"


@pytest.mark.parametrize("moi", [None, "1.9", True])
def test_no_estimate_means_no_pill_rather_than_a_dash(moi):
    """`months_of_supply` returns `None` whenever MOI cannot honestly be
    estimated (D-056 removed the 0.0 and 99.9 sentinels). The pill is a claim
    about the market; "— months of inventory · " is a claim with the evidence
    taken out of the middle of it, so the whole pill is dropped."""
    metrics = {} if moi is None else {"months_of_inventory": moi}
    b = inv(metrics=metrics)
    assert b._v2_inventory_pill() == (None, None)
    html = b.render_html()
    assert "of inventory" not in html
    # The ELEMENT, not the class name — `.band-pill`'s rule is in the <style>
    # block on every render of this page whether or not a pill is drawn.
    assert '<span class="band-pill">' not in html


def test_new_this_week_counts_seven_days_and_not_the_lookback_window():
    """`new_listings_count` is a DIFFERENT QUANTITY — that report's own
    lookback, 30 days by default and settable per schedule. Design's cell says
    "New this week"."""
    listings = [{
        "street_address": f"{i} A St", "city": "Irvine", "list_price": 900000,
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800, "status": "Active",
        "days_on_market": d,
    } for i, d in enumerate([0, 3, 7, 8, 20, 29, 40])]
    b = inv(listings=listings, metrics={"new_listings_count": 6})
    assert b._v2_new_this_week() == "3", (
        "three listings are within seven days; a 30-day figure would say six"
    )


def test_no_day_counts_at_all_is_absent_rather_than_zero():
    """"No listing reports a DOM" and "no listing is new" are different facts
    and only the second is a claim about the market (D-137)."""
    listings = [{
        "street_address": "1 A St", "city": "Irvine", "list_price": 900000,
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800, "status": "Active",
        "days_on_market": None,
    }]
    assert inv(listings=listings)._v2_new_this_week() == V2_NO_DATA


def test_the_recorded_new_window_is_designs():
    assert V2_NEW_WITHIN_DAYS == 7


def test_inventory_draws_no_trend_and_the_pace_series_has_no_report_type():
    """What Design's page costs: the sales-pace chart has nowhere to go.

    Asserted on BOTH sides — the page does not draw it, and the map that
    decides what `tasks.py` pays to fetch no longer claims it does. Leaving the
    second would buy a year of closings for a chart that cannot render, which
    is D-113's defect inverted.
    """
    html = inv().render_html()
    assert "trend-chart" not in html
    assert "Homes sold per month" not in html
    assert "inventory" not in MarketReportBuilder.TREND_SERIES, (
        "`inventory` is back in TREND_SERIES, so `tasks.py` will fetch twelve "
        "months of closings for a page with no chart slot."
    )


# ─────────────────────────────────────────────────────────────────────────────
# The three gallery kinds — two cards, three grids, and the measurement that
# said Design's own page-1 grids do not fit under Design's own band.
# ─────────────────────────────────────────────────────────────────────────────

def gal(kind, n=12, **over):
    return builder(kind, n=n, **over)


@pytest.mark.parametrize("kind", sorted(V2_GRID))
def test_a_gallery_kind_renders_a_grid_and_no_table(kind):
    html = gal(kind).render_html()
    assert 'class="grid"' in html
    assert 'class="trow' not in html and 'class="brow' not in html
    cols = V2_GRID[kind]["cols"]
    assert f"repeat({cols}, minmax(0, 1fr))" in html, (
        f"{kind} did not render Design's {cols}-column grid"
    )


def test_only_featured_gets_its_own_card():
    """Design: "same card as listings" for the gallery kinds, and a bigger one
    for featured. Four cards on a page can afford the size; nine cannot."""
    assert gal("featured_listings")._v2_gallery()["card"] == "featured"
    for kind in ("new_listings_gallery", "open_houses"):
        assert gal(kind)._v2_gallery()["card"] == "listing"
    featured = gal("featured_listings").render_html()
    assert "gcard featured" in featured
    assert "gcard featured" not in gal("open_houses").render_html()


@pytest.mark.parametrize("item,want", [
    ({"beds": 3, "baths": 2, "sqft": 1480}, "3 bd / 2 ba / 1,480 sq ft"),
    # ZERO BEDROOMS IS A STUDIO, not "0 bd" and not missing. The legacy card
    # said Studio and the gate on it exists because `or` eats the 0.
    ({"beds": 0, "baths": 1, "sqft": 600}, "Studio / 1 ba / 600 sq ft"),
    ({"beds": 2, "baths": 1.5, "sqft": 900}, "2 bd / 1.5 ba / 900 sq ft"),
    # Absent parts are DROPPED, not rendered as None or 0.
    ({"beds": 3, "sqft": 1200}, "3 bd / 1,200 sq ft"),
    ({"beds": None, "baths": None, "sqft": None}, ""),
    ({"beds": True, "baths": 2, "sqft": 900}, "2 ba / 900 sq ft"),
])
def test_the_card_specs_drop_what_is_absent_and_name_a_studio(item, want):
    assert _v2_card_specs(item) == want


def test_the_meta_line_does_not_lead_with_a_separator():
    """`{hood} · {specs}` joined from the parts that exist. A dot-joined
    template renders `· 3 bd / 2 ba` when the hood is missing."""
    rows = gal("open_houses", n=1, listings=[{
        "street_address": "1 A St", "list_price": 900000,
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800, "status": "Active",
    }])._v2_gallery()["rows"]
    assert not rows[0]["meta"].startswith("\u00b7")
    assert rows[0]["meta"] == "3 bd / 2 ba / 1,800 sq ft"


def test_the_open_house_pill_names_the_days_actually_present():
    """NOT the literal "Sat & Sun". Design's example reads that way because
    their sample week has both; a feed with one Sunday slot would promise
    Saturday viewings that do not exist."""
    def pill(dates):
        return gal("open_houses", n=len(dates), listings=[{
            "street_address": f"{i} A St", "city": "Irvine",
            "list_price": 900000, "bedrooms": 3, "bathrooms": 2, "sqft": 1800,
            "status": "Active", "next_open_house": d,
        } for i, d in enumerate(dates)])._v2_band()["pill_sub"]

    assert pill(["2026-10-10", "2026-10-11"]) == "Sat & Sun \u00b7 Irvine"
    assert pill(["2026-10-11"]) == "Sun \u00b7 Irvine"
    assert pill(["2026-10-11", "2026-10-11"]) == "Sun \u00b7 Irvine"
    # No parseable date at all: the city alone, never an invented day.
    assert pill(["Sat 1-4pm"]) == "Irvine"


def test_an_unparseable_open_house_still_reaches_its_card():
    """The split: the band only claims what it could read, the card shows what
    the feed said. Feeds send "Sat 1-4pm" in this field as well as ISO dates."""
    b = gal("open_houses", n=1, listings=[{
        "street_address": "1 A St", "city": "Irvine", "list_price": 900000,
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800, "status": "Active",
        "next_open_house": "Sat 1-4pm",
    }])
    first, last, _ = b._v2_open_house_span()
    assert (first, last) == (None, None), "the band claimed a span it could not read"
    assert "Sat 1-4pm" in b.render_html(), "the card dropped what the feed said"
    band = b._v2_band()
    assert band["cells"][0]["value"] == V2_NO_DATA
    assert band["cells"][1]["value"] == V2_NO_DATA


def test_the_open_house_span_does_not_trust_an_upstream_sort():
    """`build_open_houses_result` sorts ascending; a body that relies on that
    breaks when someone adds a filter."""
    dates = ["2026-10-12", "2026-10-10", "2026-10-11"]
    b = gal("open_houses", n=3, listings=[{
        "street_address": f"{i} A St", "city": "Irvine", "list_price": 900000,
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800, "status": "Active",
        "next_open_house": d,
    } for i, d in enumerate(dates)])
    first, last, _ = b._v2_open_house_span()
    assert first == "Sat 10 Oct" and last == "Mon 12 Oct", (first, last)


def test_featured_averages_are_absent_rather_than_zero():
    """"No listing reports a sq ft" is not "the average is zero" (D-137)."""
    b = gal("featured_listings", n=1, listings=[{
        "street_address": "1 A St", "city": "Irvine", "list_price": 900000,
        "bedrooms": 3, "bathrooms": 2, "status": "Active",
    }])
    assert b._v2_average("sqft") is None
    cells = {c["label"]: c["value"] for c in b._v2_band()["cells"]}
    assert cells["Avg. sq ft"] == V2_DASH
    assert cells["Avg. price"] != V2_DASH


def test_the_band_count_agrees_with_the_cards_below_it():
    """A band saying "9 homes to see" over six cards is worse than either
    number alone. The count is the capped listing count, not the feed's."""
    b = gal("open_houses", n=40)
    band = b._v2_band()
    gallery = b._v2_gallery()
    assert band["big"] == _v2_count_of(len(gallery["rows"]))


def _v2_count_of(n):
    return f"{n:,}"


def test_the_missing_photo_tile_is_designs_and_carries_no_stock_house():
    """Design: tint tile, neighbourhood 22px/600 in primary bottom-left,
    "Photos coming soon" 9.5px mono uppercase. No broken-image icon, no stock
    house — a photo of a house that is not the house is the one thing here
    that would be a lie."""
    html = gal("open_houses", n=3).render_html()
    assert "Photos coming soon" in html
    assert "gphoto empty" in html
    assert "\U0001F3E0" not in html, "the legacy broken-image house emoji is back"
    # The price plate stays on the tile, per Design.
    import re
    tile = re.search(r'<div class="gphoto empty">(.*?)</div>\s*<div class="ginfo"',
                     html, re.S)
    assert tile and "gplate" in tile.group(1)


def test_the_price_plate_is_a_solid_plate_and_never_text_on_photography():
    """Design's rule, and the only one readable over an unknown image."""
    html = gal("open_houses", n=3).render_html()
    import re
    rule = re.search(r"\.gplate \{([^}]*)\}", html, re.S).group(1)
    assert "background: #ffffff" in rule, rule
    assert "#14161A" in rule, rule
