"""The figures in the trend-chart relay, recomputed.

WHY THIS IS GATED
-----------------
`docs/TREND_CHART_FOR_DESIGN_2026-10-14.md` asks Design one question and the
whole question rests on arithmetic: that a 179.5px chart costs five rows, that
five rows costs one page on each of three kinds, and that the band would have to
lose 117px for it to cost none. **A relay that quotes a page count the build no
longer has is the thing we have asked Design three times not to do** — so the
page counts come from the live pin and the live continuation figure, not from
numbers typed into the document.

The browser-measured geometry cannot be recomputed here (CI has no browser,
which is why `measure_gallery_continuation_fit.py` is a script rather than a
test), so those values are pinned and asserted to still be what the document
states. Same split, and the same reasoning, as
`test_gallery_grid_relay_is_current.py`.
"""
import math
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs/TREND_CHART_FOR_DESIGN_2026-10-14.md"
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "apps/worker/tests"))

from test_narrative_box import PAGE_1_CAPACITY  # noqa: E402

sys.path.insert(0, str(REPO / "tests"))
from test_market_capacity_doc_is_current import V2_BUILT_PAGES, V2_CONTINUATION  # noqa: E402

#: Browser-measured, Chromium headless at 816x1056. Body/band/room are the
#: same values `test_gallery_grid_relay_is_current.py` pins, from the same
#: render; the chart height and the row pitch are from the chart scoping on
#: 2026-10-12.
MEASURED = {
    "body_px": 928.3,
    "band_px": 265.4,
    "room_on_page_1_px": 662.9,
    "row_pitch_px": 34.7,
    "thead_px": 22,
    "showing_px": 23,
    "chart_px": 179.5,
}

#: The kinds the relay asks about: Design's `_v2` table body, where a page-1
#: chart displaces rows. DERIVED from the pin rather than listed, so a kind
#: whose body changes drops out of the question instead of being asserted
#: about silently — §0.6's rule about a remainder written by hand.
TABLE_KINDS = sorted(k for k, n in V2_CONTINUATION.items() if n == 26)

LISTINGS = 120  # what the surface is sized for, and what V2_BUILT_PAGES used


def rows_on_page_1(chart: bool) -> int:
    room = (MEASURED["room_on_page_1_px"] - MEASURED["thead_px"]
            - MEASURED["showing_px"] - (MEASURED["chart_px"] if chart else 0))
    return int(room // MEASURED["row_pitch_px"])


def pages(page_1_rows: int, per_page: int) -> int:
    if LISTINGS <= page_1_rows:
        return 1
    return 1 + math.ceil((LISTINGS - page_1_rows) / per_page)


@pytest.fixture(scope="module")
def body():
    return DOC.read_text(encoding="utf-8")


def test_the_relay_asks_about_the_table_kinds_the_pin_still_has():
    assert TABLE_KINDS == ["closed", "inventory", "new_listings"], (
        f"the table kinds are now {TABLE_KINDS}. The relay's §3 names three "
        f"and sums them; a fourth (or a third that left) changes the ask."
    )


def test_the_room_the_band_leaves_is_the_documents_arithmetic(body):
    left = MEASURED["body_px"] - MEASURED["band_px"]
    assert abs(left - MEASURED["room_on_page_1_px"]) < 0.05, left
    for value in MEASURED.values():
        assert str(value) in body, (
            f"the document no longer quotes the measured {value}. If the "
            f"geometry was re-measured, update MEASURED here too."
        )


def test_page_1_capacity_recomputes_to_the_pin_without_a_chart():
    """17, and it must equal what the build actually pins.

    This is the half that makes the with-chart number trustworthy: the same
    arithmetic, with the chart term removed, has to land on the figure the
    render produced.
    """
    computed = rows_on_page_1(chart=False)
    for kind in TABLE_KINDS:
        assert PAGE_1_CAPACITY[kind]["no_narrative"] == computed, (
            f"{kind} pins {PAGE_1_CAPACITY[kind]['no_narrative']} rows on page 1 "
            f"and the relay's arithmetic gives {computed}. One of them is "
            f"wrong, and the document is quoting the arithmetic."
        )
    assert computed == 17


def test_the_chart_costs_five_rows_and_the_document_says_so(body):
    without, with_chart = rows_on_page_1(False), rows_on_page_1(True)
    assert (without, with_chart) == (17, 12), (without, with_chart)
    assert without - with_chart == 5
    assert "costs five rows on page 1" in body


@pytest.mark.parametrize("kind", TABLE_KINDS)
def test_the_page_counts_recompute_from_the_live_pin(kind, body):
    now = pages(PAGE_1_CAPACITY[kind]["no_narrative"], V2_CONTINUATION[kind])
    assert now == V2_BUILT_PAGES[kind], (
        f"{kind}: the relay's formula gives {now} pages for the CURRENT page "
        f"and the build measured {V2_BUILT_PAGES[kind]}. Fix the formula "
        f"before quoting the with-chart number it produces."
    )
    with_chart = pages(rows_on_page_1(True), V2_CONTINUATION[kind])
    assert (now, with_chart) == (5, 6), (now, with_chart)


def test_the_totals_in_the_document_are_the_sums(body):
    now = sum(pages(PAGE_1_CAPACITY[k]["no_narrative"], V2_CONTINUATION[k])
              for k in TABLE_KINDS)
    with_chart = sum(pages(rows_on_page_1(True), V2_CONTINUATION[k])
                     for k in TABLE_KINDS)
    assert (now, with_chart) == (15, 18), (now, with_chart)
    assert f"**{now}**" in body and f"**{with_chart}**" in body
    assert f"{with_chart} pages against {now}" in body


def test_the_band_height_that_would_make_the_chart_free_is_the_one_quoted(body):
    """The finding, and the reason the ask is about the band.

    Solved rather than quoted: the largest band for which a page-1 chart still
    leaves enough rows to keep each table kind at five pages.
    """
    per_page = 26
    need = next(r for r in range(1, 40) if pages(r, per_page) == 5)
    free_band = (MEASURED["body_px"] - MEASURED["thead_px"]
                 - MEASURED["showing_px"] - MEASURED["chart_px"]
                 - need * MEASURED["row_pitch_px"])
    assert need == 16, need
    assert abs(free_band - 148.6) < 0.1, free_band
    drop = MEASURED["band_px"] - free_band
    assert abs(drop - 116.8) < 0.1, drop
    assert "148.6px" in body
    assert "117px" in body, (
        f"the document should state the {drop:.1f}px the band would have to "
        f"lose, rounded"
    )


def test_the_relay_makes_no_proposal_and_names_the_free_option(body):
    """Form, not content — the two things that made the earlier asks work.

    Design answered the gallery ask because it asked one question and proposed
    nothing. A relay that arrives with a redesign gets a defence instead of an
    answer.
    """
    assert "Nothing here asks you to change the page" in body
    assert "It is not a request" in body or "That is not a request" in body
    assert "`market_snapshot` has no listings table" in body


def test_the_relay_states_which_charts_already_render(body):
    """§7.3 specifies two families, and one of them is NOT at issue.

    The first version of this ask would have asked about both, which invites
    Design to re-open a chart they already solved with their bands body.
    """
    assert "band distribution" in body and "No question here." in body
    assert re.search(r"median trend\*{0,2}\s*\|\s*renders on `market_snapshot`", body), (
        "the relay must say the median trend already renders, and on which "
        "kind — otherwise the ask reads as a request for a chart that exists"
    )
