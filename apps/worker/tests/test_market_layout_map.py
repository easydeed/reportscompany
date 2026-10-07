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


@pytest.mark.parametrize("report_type", sorted(V2_KINDS))
def test_a_v2_kind_calls_no_layout_macro_and_renders_the_v2_page(report_type):
    """The other half of the seam, asserted rather than implied.

    A kind in `V2_KINDS` leaves the macro dispatch entirely. Two ways that can
    go wrong silently: it renders the old page anyway (the seam not taken), or
    it renders the new page AND a macro (both, which would paginate as
    neither). Both are caught by requiring the macro list to be empty and the
    page's own marker to be present.
    """
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
    assert 'class="band"' in html and 'class="trow thead"' in html, (
        f"{report_type} called no layout macro and did not render the `_v2` "
        f"page either — so it rendered neither document."
    )


def test_the_dispatch_fallback_is_reachable_only_by_an_unknown_layout():
    """Positive control: prove the assertion above can fail.

    A checker whose normal output is 'match' is indistinguishable from one that
    has stopped matching anything (§0.6, *a detector's silence*). Point a known
    report type at a layout base.jinja2 has no branch for and the fallback
    gallery must run instead.
    """
    # `inventory`, not `closed`: closed renders the `_v2` page now and
    # never reaches base.jinja2's dispatch, so it cannot exercise the
    # fallback this control exists to prove is reachable.
    data = report_data("inventory")
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


@pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
def test_the_cap_is_what_limits_the_listings_that_render(report_type):
    """The pinned cap must match PDF_CONFIG *and* the rows that actually render."""
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
