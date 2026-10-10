"""The figures in the Design relay, recomputed.

WHY THIS IS GATED
-----------------
`docs/GALLERY_GRID_FOR_DESIGN_2026-10-10.md` asks Design two questions and each
one rests on an arithmetic claim: that five pixels on `featured_listings` is
worth a page, and that eighty on `open_houses` is worth none. **A relay that
quotes a page count the build no longer has is the thing we have asked them
three times not to do** — it was the whole subject of the 2026-10-06 exchange,
and sending one would cost the standing to ask.

So the page counts are recomputed from the live caps and the live pin, and the
pixel measurements are held against the values the browser produced. The
measured geometry cannot be recomputed here (it needs a browser, and CI has
none — the same reason `measure_gallery_continuation_fit.py` is a script), so
those are pinned and asserted to still be the numbers the document states.
"""
import math
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs/GALLERY_GRID_FOR_DESIGN_2026-10-10.md"
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "apps/worker/tests"))

from test_narrative_box import PAGE_1_CAPACITY  # noqa: E402
from worker.market_builder import PDF_CONFIG, V2_GRID  # noqa: E402

#: Measured by `scripts/measure_gallery_continuation_fit.py` on 2026-10-10,
#: Chromium headless, 816x1056 viewport.
MEASURED = {
    "body_px": 928.3,
    "band_px": 265.4,
    "room_on_page_1_px": 662.9,
    "shared_card_px": 238.3,
    "featured_card_px": 326.8,
    "row_gap_px": 14,
    "continuation_headroom_px": 185.3,
}

#: Cards per continuation page, from the measured fit: three rows of the shared
#: card at 3 columns, two rows of the featured card at 2.
CONTINUATION_CARDS = {
    "new_listings_gallery": 9,
    "open_houses": 9,
    "featured_listings": 4,
}


@pytest.fixture(scope="module")
def body():
    return DOC.read_text(encoding="utf-8")


def test_every_measured_figure_is_still_the_one_quoted(body):
    """A pinned measurement, asserted against the document that relays it."""
    for name, value in MEASURED.items():
        shown = f"{value:,}" if isinstance(value, int) else f"{value}"
        assert shown in body, (
            f"the document no longer quotes the measured {name} of {shown}. "
            f"If the geometry was re-measured, update MEASURED here too — a "
            f"relay that quotes a figure the build no longer has is the thing "
            f"we have asked Design three times not to do."
        )


def test_the_band_leaves_what_the_document_says_it_leaves(body):
    """The one sum the document does itself."""
    left = MEASURED["body_px"] - MEASURED["band_px"]
    assert abs(left - MEASURED["room_on_page_1_px"]) < 0.05, left


@pytest.mark.parametrize("kind", sorted(V2_GRID))
def test_the_page_counts_recompute_from_the_live_caps(kind, body):
    """`1 + ceil((cap - page_1) / continuation)`, from the live config.

    NOT from numbers typed into the document. The caps are `PDF_CONFIG`'s and
    the page-1 figures are the measured pin, so a cap change or a re-pin makes
    this fail rather than letting the relay go stale.
    """
    cap = PDF_CONFIG[kind]["cap"]
    page_1 = PAGE_1_CAPACITY[kind]["no_narrative"]
    per_page = CONTINUATION_CARDS[kind]
    ours = 1 if cap <= page_1 else 1 + math.ceil((cap - page_1) / per_page)

    stated_rows = V2_GRID[kind]["rows_page_1"] * V2_GRID[kind]["cols"]
    theirs = (math.ceil(cap / per_page) if stated_rows >= per_page
              else 1 + math.ceil((cap - stated_rows) / per_page))

    # THE PAGE-COUNT ASSERTION APPLIES TO THE TWO KINDS THE RELAY ASKS ABOUT.
    # `new_listings_gallery`'s grid fits, so the document makes no page claim
    # about it and there is nothing to hold against the recomputation. The
    # first version asserted the count for all three and failed on the one
    # with no question — the same scope mistake as D-185, in the gate written
    # to record D-185.
    if kind == "open_houses":
        assert (ours, theirs) == (12, 12), (
            f"open_houses is {ours} pages ours and {theirs} theirs. The "
            f"document's second question rests on them being EQUAL — that the "
            f"80px shortfall costs nothing. If they have diverged, the ask "
            f"changes from a density question to a cost."
        )
        assert "worth nothing" in body
    elif kind == "featured_listings":
        assert (ours, theirs) == (4, 3), (
            f"featured_listings is {ours} pages ours and {theirs} theirs. The "
            f"document's first question rests on the gap being exactly one "
            f"page."
        )
        assert "worth a page" in body
        assert f"=  {ours} pages" in body or f"= {ours} pages" in body, (
            f"{kind}: the document does not state {ours} pages"
        )
    else:
        assert ours == 23, (
            f"{kind} is {ours} pages at cap {cap}. The relay deliberately "
            f"makes no claim about this kind because its stated grid fits — "
            f"if that changed, it needs a question of its own."
        )


def test_the_relay_states_which_shortfall_is_free(body):
    """The inversion is the finding: the bigger miss is the cheaper one.

    Ranking the two asks by how many pixels they miss by would have put the
    effort on `open_houses`, which costs nothing.
    """
    assert "eighty pixels, worth nothing" in body
    assert "five pixels, worth a page" in body


def test_the_relay_does_not_claim_the_continuation_fit_regressed(body):
    """#156 measured 138px of continuation headroom on the legacy page and the
    `_v2` page measures 185.3 — it went UP by 47.3.

    Asserted because the band is page-1-only ("Continuation pages carry the
    running head and the table — there is no separate brand strip"), so it
    cannot cost the continuation page, and a relay saying otherwise would be
    telling Design their card got worse when it got better.
    """
    assert MEASURED["continuation_headroom_px"] > 138.0
    assert "185.3px spare" in body
    assert "three rows of the shared card fit" in body
