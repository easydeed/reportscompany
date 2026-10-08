"""What the market-report builder actually renders, derived by watching it.

WHY THIS MODULE EXISTS, AND WHY IT DOES NOT READ THE BUILDERS.

Workstream C ended with a declarative map of which blocks each email report
type renders. It was written first by reading the eight builder functions, by
the author of the refactor that had just moved every block, and seven of the
eight entries were wrong. Rewritten from a trace of the render, all eight were
right. That is now a standing rule (execution plan §0.6, *a description of what
code does is a hypothesis*), and Workstream D inherits it: the PDF equivalent
of that map is written here from an instrument, never from the source.

The instrument is `jinja2.runtime.Macro.__call__`. Every layout in
`templates/market/_base/macros.jinja2` is a Jinja macro, so wrapping that one
method records the exact sequence of macros a render invoked — without adding a
marker to the production HTML, and without any test-only branch in the builder.
"""

import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from jinja2.runtime import Macro

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.market_builder import (  # noqa: E402
    ALL_REPORT_TYPES,
    LAYOUT_MAP,
    V2_KINDS,
    PDF_CONFIG,
    MarketReportBuilder,
)

STREETS = ["Main St", "Oak Ave", "Elm Dr", "Birch Ln", "Cedar Ct", "Maple Way",
           "Pine Rd", "Walnut Blvd", "Juniper Pl", "Sycamore Ter"]


def listings(n):
    return [
        {
            "street_address": f"{100 + i * 7} {STREETS[i % len(STREETS)]}",
            "city": "Irvine",
            "list_price": 650000 + (i * 13500) % 900000,
            "close_price": 640000 + (i * 12900) % 880000,
            "bedrooms": 2 + (i % 4),
            "bathrooms": 1.5 + (i % 3),
            "sqft": 1200 + (i * 37) % 2400,
            "status": ["Active", "Pending", "Closed"][i % 3],
            "days_on_market": 3 + (i * 5) % 90,
            "photo_url": None,
            "next_open_house": "Sat 1-4pm" if i % 3 == 0 else None,
        }
        for i in range(n)
    ]


def report_data(report_type, n=40):
    return {
        "report_type": report_type,
        "city": "Irvine",
        "lookback_days": 30,
        "filters_label": "2+ beds, SFR, under $1.5M",
        "listings": listings(n),
        "metrics": {
            "median_list_price": 922500, "median_close_price": 907500,
            "avg_dom": 12, "months_of_inventory": 2.1, "price_per_sqft": 520,
            "list_to_sale_ratio": 0.982, "new_listings_count": 42,
        },
        "counts": {"Active": 67, "Pending": 12, "Closed": 38},
        "total_listings": n,
        "branding": {
            "agent_name": "Jennifer Martinez",
            "agent_title": "Luxury Home Specialist",
            "primary_color": "#1B365D",
            "accent_color": None,
        },
        "ai_insights": "The Irvine market showed balanced activity this period.",
        "price_bands": [
            {"label": "$600-800K", "count": 18, "pct": 22},
            {"label": "$800K-1M", "count": 31, "pct": 38},
        ],
    }


@contextmanager
def recording_macros():
    """Record every Jinja macro invoked inside the block, in call order."""
    seen = []
    original = Macro.__call__

    def wrapper(self, *args, **kwargs):
        seen.append(self.name)
        return original(self, *args, **kwargs)

    Macro.__call__ = wrapper
    try:
        yield seen
    finally:
        Macro.__call__ = original


def macros_for(report_type, n=40):
    with recording_macros() as seen:
        MarketReportBuilder(report_data(report_type, n)).render_html()
    return seen


#: The layout macro each report type actually runs, recorded from a render on
#: 2026-09-24 — not read off LAYOUT_MAP, which is the thing being checked.
LAYOUT_MACRO = {
    "new_listings_gallery": "gallery_layout",
    "featured_listings": "gallery_layout",
    "open_houses": "gallery_layout",
    "market_snapshot": "market_narrative_layout",
    "closed": "closed_inventory_layout",
    "inventory": "closed_inventory_layout",
    "price_bands": "pricebands_layout",
    "new_listings": "analytics_layout",
}


def test_every_report_type_is_covered_by_the_recorded_map():
    assert set(LAYOUT_MACRO) == set(ALL_REPORT_TYPES)


@pytest.mark.parametrize("report_type", sorted(set(ALL_REPORT_TYPES) - V2_KINDS))
def test_the_layout_map_matches_the_macro_that_runs(report_type):
    """LAYOUT_MAP[t] + '_layout' must be the macro the render actually calls.

    base.jinja2 dispatches on `layout`, so a LAYOUT_MAP edit that does not
    match a branch there falls through to the `{% else %}` and renders the
    gallery — silently, and with output that still looks like a report.

    EXCLUDES `V2_KINDS`, which render Design's `_v2` page and call no layout
    macro at all. Excluded by SUBTRACTING the seam rather than by listing the
    kinds that remain: a hand-written remainder is a second copy of
    `V2_KINDS`, and it would go stale the moment a second kind moves — which
    is the next thing to happen. `test_a_v2_kind_calls_no_layout_macro` below
    covers them positively, because a kind dropping out of this test's
    parameters and being asserted nowhere is how coverage disappears quietly.
    """
    called = macros_for(report_type)
    layout_macros = [m for m in called if m.endswith("_layout")]
    assert layout_macros == [LAYOUT_MACRO[report_type]], (
        f"{report_type}: recorded map says {LAYOUT_MACRO[report_type]}, "
        f"render called {layout_macros}"
    )
    assert f"{LAYOUT_MAP[report_type]}_layout" == LAYOUT_MACRO[report_type], (
        f"{report_type}: LAYOUT_MAP says {LAYOUT_MAP[report_type]!r}, which is "
        f"not the layout that rendered"
    )


#: The `_v2` body each kind renders, recorded from a render on 2026-10-08.
#:
#: Design's page is a shared band over ONE per-kind body, and the template
#: dispatches on which body context the builder filled. Pinned here per kind
#: for the same reason `LAYOUT_MACRO` is: the first version of the test below
#: asserted `class="trow thead"` for every kind in the seam, which was true
#: while the seam held only table kinds and became wrong the moment
#: `price_bands` — whose body is bands, not a table — joined it. A marker that
#: fits only the kinds already wired asserts "the seam is taken" and means
#: "the seam is taken by a table kind".
V2_BODY_MARKER = {
    "closed": 'class="trow thead"',
    "new_listings": 'class="trow thead"',
    "inventory": 'class="trow thead"',
    "price_bands": 'class="brow bhead"',
}


@pytest.mark.parametrize("report_type", sorted(V2_KINDS))
def test_a_v2_kind_calls_no_layout_macro_and_renders_the_v2_page(report_type):
    """The other half of the seam, asserted rather than implied.

    A kind in `V2_KINDS` leaves the macro dispatch entirely. Three ways that
    can go wrong silently: it renders the old page anyway (the seam not taken),
    it renders the new page AND a macro (both, which would paginate as
    neither), or it renders the band over the WRONG body — a bands kind showing
    a listings table, which is a plausible-looking report of the wrong thing.
    All three are caught: the macro list must be empty, the kind's own body
    marker must be present, and every OTHER kind's marker must be absent.
    """
    assert report_type in V2_BODY_MARKER, (
        f"{report_type} joined V2_KINDS with no recorded body marker. Record "
        f"which body it renders here; otherwise this test can only check that "
        f"it rendered something."
    )
    data = report_data(report_type)
    data["ai_insights"] = None
    builder = MarketReportBuilder(data)
    with recording_macros() as seen:
        html = builder.render_html()
    layout_macros = [m for m in seen if m.endswith("_layout")]
    assert layout_macros == [], (
        f"{report_type} is in V2_KINDS and still called {layout_macros}. The "
        f"seam is not taken, or it is taken twice."
    )
    assert 'class="band"' in html, (
        f"{report_type} called no layout macro and did not render the `_v2` "
        f"page either — so it rendered neither document."
    )
    mine = V2_BODY_MARKER[report_type]
    assert mine in html, (
        f"{report_type} rendered the `_v2` band with no {mine!r} body"
    )
    for other in set(V2_BODY_MARKER.values()) - {mine}:
        assert other not in html, (
            f"{report_type} rendered {other!r} as well as its own {mine!r} — "
            f"two bodies under one band"
        )


#: Layout macros no report type reaches any more, because every kind that used
#: them moved to Design's `_v2` page.
#:
#: WHY THIS IS WRITTEN DOWN RATHER THAN CLEANED UP. `derive_template_
#: reachability.py` works at FILE level, and `market/_base/macros.jinja2` stays
#: live as long as any one macro in it is reached — so a layout going dead inside a
#: live file is invisible to it, and two of them already had. `analytics_layout`
#: went dead when `new_listings` moved on 2026-10-08 and nothing recorded it;
#: `pricebands_layout` went dead the same day. Deleting them is a separate
#: decision (they are the rollback path for the seam, and `base.jinja2`'s
#: dispatch still names them), but accumulating them unnoticed is how a
#: template file comes to be two thirds dead without anyone having decided it —
#: which is exactly what `property/_base/base.jinja2`'s 5,570 dead lines are.
UNREACHABLE_LAYOUT_MACROS = ["analytics_layout", "closed_inventory_layout",
                             "pricebands_layout"]


def test_the_layouts_no_report_type_reaches_are_recorded():
    """Dead layouts are named, so going dead is a decision and not a drift.

    Derived from the recorded map rather than from the source: a macro is
    unreachable when every kind whose layout it is has moved into `V2_KINDS`.
    """
    reached = {m for t, m in LAYOUT_MACRO.items() if t not in V2_KINDS}
    unreachable = sorted(set(LAYOUT_MACRO.values()) - reached)
    assert unreachable == UNREACHABLE_LAYOUT_MACROS, (
        f"the set of unreachable layout macros changed to {unreachable}. If a "
        f"kind just moved to the `_v2` page, record its layout here and say in "
        f"the commit whether the macro is being kept as the rollback path or "
        f"removed. If one came back, say why."
    )


#: `price_bands[:4]` — D-107's construct — and where it still is.
#:
#: D-107 removed the four-of-six band slice from `pricebands_layout` and left an
#: identical one in `analytics_layout`, which nobody noticed for ten days because
#: the entry named one macro and the fix edited that macro. `grep -n
#: "price_bands\[:4\]"` finds both on one line and was not run.
#:
#: Pinned rather than deleted. The surviving copy is dead three times over —
#: `build_new_listings_result` emits no `price_bands` key, `analytics_layout`
#: never served the `price_bands` kind, and no kind reaches `analytics_layout`
#: at all since 2026-10-08 — so editing it would be a diff that looks like a fix
#: and changes no rendered page. What this holds is the RECORD: if the count
#: moves, either someone removed the dead slice (fine, say so here) or a second
#: one appeared (not fine).
BAND_SLICE_SITES = {"analytics_layout": 1, "pricebands_layout": 0}


def test_the_four_of_six_band_slice_is_only_where_it_is_recorded():
    """D-107's construct, counted per macro rather than per file.

    A grep of the whole file would say "one `[:4]` remains" and not say which
    macro, which is the information that mattered: one copy was reachable and
    one was not, and the entry was about the reachable one.
    """
    import re
    source = (Path(__file__).resolve().parents[1]
              / "src/worker/templates/market/_base/macros.jinja2"
              ).read_text(encoding="utf-8")
    # Split on macro boundaries so a slice is attributed to the macro it is in.
    starts = [(m.start(), m.group(1))
              for m in re.finditer(r"\{%\s*macro\s+(\w+)", source)]
    found = {name: 0 for name in BAND_SLICE_SITES}
    for i, (pos, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(source)
        if name in found:
            found[name] = source[pos:end].count("price_bands[:4]")
    assert found == BAND_SLICE_SITES, (
        f"D-107's `price_bands[:4]` is now {found}, recorded as "
        f"{BAND_SLICE_SITES}. A market with six bands renders four cards and "
        f"says nothing about the other two. If the dead copy in "
        f"`analytics_layout` was removed, record that here; if a new one "
        f"appeared, it is D-107 coming back."
    )
    whole = source.count("price_bands[:4]")
    assert whole == sum(BAND_SLICE_SITES.values()), (
        f"{whole} occurrences of `price_bands[:4]` in the file but "
        f"{sum(BAND_SLICE_SITES.values())} inside the macros this test knows "
        f"about — one is somewhere this test does not look."
    )


def test_the_dispatch_fallback_is_reachable_only_by_an_unknown_layout():
    """Positive control: prove the assertion above can fail.

    A checker whose normal output is 'match' is indistinguishable from one that
    has stopped matching anything (§0.6, *a detector's silence*). Point a known
    report type at a layout base.jinja2 has no branch for and the fallback
    gallery must run instead.
    """
    # DERIVED, NOT NAMED. This line said `closed`, then `inventory`, and each
    # became wrong when that kind joined the seam — a kind in `V2_KINDS` never
    # reaches base.jinja2's dispatch, so it cannot exercise the fallback this
    # control exists to prove is reachable. A positive control drawn from the
    # set being migrated is consumed by the migration, so the remainder is
    # computed and asserted non-empty.
    outside = sorted(set(ALL_REPORT_TYPES) - V2_KINDS)
    assert outside, (
        "every report type is in V2_KINDS, so no kind can reach base.jinja2's "
        "dispatch and this control cannot be run at all. The fallback is now "
        "unreachable from production — retire it with the old layouts, or say "
        "here why it stays."
    )
    data = report_data(outside[0])
    builder = MarketReportBuilder(data)
    builder.layout = "no_such_layout"
    with recording_macros() as seen:
        builder.render_html()
    layout_macros = [m for m in seen if m.endswith("_layout")]
    assert layout_macros == ["gallery_layout"], layout_macros


#: How many listings each report type puts in the PDF, recorded from a render.
#:
#: These are written down rather than read from PDF_CONFIG on purpose. The first
#: version of the test below took its expectation from `PDF_CONFIG[t]["cap"]`
#: and sized its input at `cap + 25`, so changing a cap changed the expectation
#: and the input together and the assertion held either way — a test that could
#: not fail. Changing "closed" from 200 to 150 was applied deliberately and the
#: suite stayed green, which is how it was found. Pinned values make a cap
#: change a decision someone has to write down twice.
RENDERED_LISTING_CAP = {
    "market_snapshot": 9,
    "price_bands": 8,
    "featured_listings": 12,
    "closed": 200,
    "inventory": 200,
    "new_listings": 200,
    "new_listings_gallery": 200,
    "open_houses": 100,
}


#: Kinds whose rendered listing count is deliberately NOT their cap, and what
#: it is instead.
#:
#: `price_bands` moved to Design's `_v2` page on 2026-10-08, and that page's
#: body for this kind is the band table — five columns of price-band
#: aggregates, no listings at all. So `PDF_CONFIG["price_bands"]["cap"] = 8`
#: now governs nothing that renders.
#:
#: THE CAP IS LEFT AT 8 AND NOT REMOVED. `cap` is read by `_build_listings_
#: context`, which still runs for this kind and still feeds `total_count`, and
#: the entry is also where `pages` and the header/footer offsets live. Deleting
#: the number because one of its consumers went quiet is the change that breaks
#: the other four. What is recorded here is that it is inert for rendering —
#: so if someone gives `price_bands` a listings table, 8 rows appear, and this
#: gate fires asking whether 8 was ever a decision for that body.
RENDERED_DESPITE_CAP = {
    "price_bands": 0,
}


@pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
def test_the_cap_is_what_limits_the_listings_that_render(report_type):
    """The pinned cap must match PDF_CONFIG *and* the rows that actually render.

    For a kind in `RENDERED_DESPITE_CAP` the second half is pinned separately,
    asserted rather than skipped: a kind that renders zero listings when the
    config says eight is a fact worth holding still, and skipping it would let
    a page silently start or stop rendering listings with nothing to say so.
    """
    cap = RENDERED_LISTING_CAP[report_type]
    assert PDF_CONFIG[report_type]["cap"] == cap, (
        f"{report_type}: PDF_CONFIG says {PDF_CONFIG[report_type]['cap']}, "
        f"this suite has {cap} recorded. If the change is intended, record it "
        f"here too and say why in the commit."
    )
    n = cap + 25
    html = MarketReportBuilder(report_data(report_type, n)).render_html()
    rendered = sum(
        1 for i in range(n)
        if f"{100 + i * 7} {STREETS[i % len(STREETS)]}" in html
    )
    expected = RENDERED_DESPITE_CAP.get(report_type, cap)
    if expected != cap:
        assert rendered == expected, (
            f"{report_type}: this suite records that the cap ({cap}) governs "
            f"nothing on this page and {expected} listings render, but "
            f"{rendered} of {n} did. Either the body changed or the cap "
            f"started governing again; both are decisions to write down."
        )
        return
    assert rendered == cap, (
        f"{report_type}: cap is {cap} but {rendered} of {n} listings rendered"
    )


def test_the_more_listings_callout_cannot_emit_anything_today():
    """Every PDF_CONFIG entry has more_template=None, so the callout is inert.

    Deliberately so — the "+ N more, contact me for the complete list" copy was
    removed because agents had no way to produce that list. The macro and the
    builder branch that feeds it both survive, and the call still happens on
    every render, so this records that the path is currently unreachable. If
    someone restores a more_template, this test fails and says to check the
    copy is honest before it ships again.
    """
    assert all(c["more_template"] is None for c in PDF_CONFIG.values())
    for report_type in ALL_REPORT_TYPES:
        html = MarketReportBuilder(report_data(report_type)).render_html()
        if report_type in V2_KINDS:
            # Design's page has no such callout and calls no macros, so the
            # "the call still happens on every render" half does not apply.
            # The OUTPUT half still does, and matters more: a `_v2` page that
            # started emitting the copy would be the same dishonest callout on
            # a new document.
            assert 'class="more-listings-note' not in html, report_type
            continue
        called = macros_for(report_type)
        assert "more_listings_callout" in called, report_type
        # The bare class name also appears in a `.more-listings-note
        # { break-inside: avoid }` rule in the stylesheet, which is itself
        # unreachable today. Match the attribute so this asserts about MARKUP
        # and not about CSS — the first version of it matched the rule and
        # failed, which is the same false positive as grepping for a string
        # that occurs in an unrelated place.
        assert 'class="more-listings-note' not in html, report_type
