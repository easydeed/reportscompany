"""Page-1 capacity per market kind, and — until 2026-10-28 — the narrative box.

WHAT REMAINS IS `PAGE_1_CAPACITY`. The narrative box half of this file went
with the legacy page (see the note above the capacity tests); the history
below is kept because the capacities were first measured against it.

The narrative's copy budget and the box it has to fit were one decision (§7.2).

`ai_market_narrative.NARRATIVE_MAX_CHARS` and the `height` on
`.ai-narrative-text` in templates/market are two halves of the same number. The
budget exists because the box does not clip; the box is safe because the budget
holds. Split across a Python module and a CSS rule, they can drift apart
silently and the first sign would be a pushed-down table in a customer's PDF.

Most of this is browser-free and runs in CI. The one assertion that genuinely
needs a paginator — that a budget-length narrative renders inside four lines —
cannot, so it is `scripts/measure_market_pagination.py`'s territory and the
numbers it produced are recorded here as the pinned capacities below.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


#: Page-1 listing capacity, per report type and per deterministic state.
#:
#: EMITTED, NOT TYPED. `python3 scripts/measure_market_pagination.py
#: --emit-capacity` prints this dict; re-pinning is a paste. These numbers have
#: been re-derived three times — after §7.2's narrative cap, after §7.1's
#: masthead move, after D-102's masthead bound — and the derivation was right
#: every time. Reading them off a terminal and retyping them was the weak step,
#: which is how the defect board's own summary header went stale. The
#: regeneration stays deliberate and its diff is what a reviewer reads; the same
#: contract as golden/themes.json.
#:
#: The states are deterministic, not variable. `no_narrative` differs because a
#: report with no narrative renders no box. `with_trend` exists only for the two
#: types that carry a monthly series, and on market_snapshot it is 0 by DESIGN:
#: page 1 holds the twelve-month price trend and the listings begin on page 2
#: (Jerry, 2026-09-28 — D-102). Both remain two-page reports with all nine
#: listings; the choice was what page 1 leads with.
#:
#: THE `with_trend` ROWS WERE NOT EVIDENCE UNTIL 2026-09-29 (D-113). Nothing
#: wrote `closed_history` on the production path, so no report had ever entered
#: that state: the numbers were measured from a fixture the measuring script
#: supplied to itself, describing a layout the product could not produce, and
#: D-102's decision was taken on them. Re-measured after the fetch landed —
#: **identical**, which is the good outcome and does not retroactively make the
#: earlier run evidence. It was a correct prediction, confirmed late.
#:
#: THE BAND-BEARING ROWS MOVED, 2026-09-29 (D-111), AND FOR THE SAME REASON
#: ONE LEVEL DOWN. `price_bands` 4/3 -> 2/1 and `new_listings` 4/3 -> 3/2.
#: Not because the layout changed but because the MEASUREMENT was taken
#: against a two-band fixture the script supplied to itself, while production
#: now emits six to eight. The old numbers described a card row the product
#: does not render. The fixture builds its bands with the real `build_bands`
#: now, so the next re-pin measures what ships.
#:
#: AND AGAIN when MAX_BANDS came down from 8 to 6 after the eight-band render
#: was looked at: `price_bands` 2/1 -> 3/2, `new_listings` unchanged at 3/2.
#: A shorter card row gives a listing back. Third re-pin in one day, each one
#: from a real change to what the page renders — which is the pin working.
#:
#: `price_bands` at `with_narrative: 2` is DECIDED, not open (Jerry,
#: 2026-09-29): it is a distribution report, the cards and the chart ARE the
#: content, and the listings are supporting detail. Unlike market_snapshot
#: (D-102) nothing is competing for that space, so there is no trade to make.
#:
#: Within a state the number does not move with content: the narrative box is
#: fixed (§7.2) and the masthead's title and subtitle are bounded (D-102), so
#: these are properties of the layout rather than of a fixture.
PAGE_1_CAPACITY = {
    "new_listings_gallery": {"no_narrative": 6, "with_narrative": 6},
    # 6 -> 2, AND IT IS DESIGN'S CARD, NOT A REGRESSION IN OURS. Their
    # featured card is 326.8px against the shared gallery card's 238.3 —
    # 18px price plate, 15px address, and a 2-column grid whose photo is
    # 260px tall because the column is 349px wide. Two fit under the band
    # where six did. See §8 of the capacity document: this is the one kind
    # the market adoption COSTS pages on.
    "featured_listings": {"no_narrative": 2, "with_narrative": 2},
    "open_houses": {"no_narrative": 6, "with_narrative": 6},
    # 0 / 0, ONE STATE, since D-255. Design's snapshot body carries no
    # listings — inventory, price tiers, the median line, property types —
    # so nothing paginates, as for `price_bands`. It was 3 / 3 / 0 on the
    # legacy page, where `with_trend` (D-102) gave page 1 to the chart and
    # sent the nine listings to page 2. Measured by
    # `scripts/measure_market_pagination.py`: 1 page, [0].
    "market_snapshot": {"no_narrative": 0, "with_narrative": 0},
    # 17 IN BOTH STATES since `closed` moved to Design's `_v2` page, and that
    # identity is the point: the narrative is suppressed for `V2_KINDS`, so
    # page-1 capacity is one number rather than a property of prose length.
    # It was 15 / 11 — a four-row swing — on the old page.
    "closed": {"no_narrative": 17, "with_narrative": 17},
    # 17/17, ONE STATE — and the third number is gone, not just equalised.
    # `with_trend: 5` recorded the inventory page's capacity when it carried
    # the sales-pace chart; Design's `_v2` page has no chart slot, so the
    # pace series has no report type at all (see `TREND_SERIES`). A
    # `with_trend` key here would be a capacity for a state the kind can no
    # longer be in.
    "inventory": {"no_narrative": 17, "with_narrative": 17},
    # ZERO, AND IT IS NOT A REGRESSION. `price_bands` moved to Design's `_v2`
    # page, which renders seven fixed band rows and NO LISTINGS TABLE — so the
    # number of listings that fit on page 1 is zero because none are rendered,
    # not because none fit. The kind went from 2 pages to 1.
    #
    # A capacity of 0 reading as a failure is the risk here, which is why the
    # measurement script prints "n/a (no listings table)" for it rather than a
    # bare 0.
    "price_bands": {"no_narrative": 0, "with_narrative": 0},
    # 17 in both states since `new_listings` moved to the `_v2` page, from
    # 3 / 2 on the analytics layout. The biggest single change on this surface:
    # 16 pages to 5 for 120 listings.
    "new_listings": {"no_narrative": 17, "with_narrative": 17},
}


# THE NARRATIVE BOX'S FOUR GATES WERE HERE: the box was a fixed four lines,
# `NARRATIVE_MAX_CHARS` fit it and filled 90% of it, and the prompt asked for
# the 2-3 sentences it was measured against. `.ai-narrative-text` lived in the
# legacy `base.jinja2`, deleted on 2026-10-28 once every kind was on Design's
# page — which renders no narrative — so the box has no stylesheet and the
# budget no page. The PDF stopped generating the prose in the same change.


@pytest.mark.parametrize("report_type", sorted(PAGE_1_CAPACITY))
def test_every_report_type_has_a_recorded_page_1_capacity(report_type):
    """Pinned, the same way continuation pages are — these are the numbers
    §7.2's targets have to be written against, and they only mean anything
    while the narrative box and the masthead stay bounded."""
    entry = PAGE_1_CAPACITY[report_type]
    assert entry["with_narrative"] >= 0
    assert entry["no_narrative"] >= entry["with_narrative"], (
        f"{report_type}: a report WITHOUT a narrative cannot hold fewer "
        f"listings on page 1 than one with"
    )
    if "with_trend" in entry:
        assert entry["with_trend"] <= entry["with_narrative"], (
            f"{report_type}: adding a chart to page 1 cannot make room for MORE "
            f"listings on it"
        )


def test_the_recorded_capacities_cover_every_report_type():
    from worker.market_builder import ALL_REPORT_TYPES
    assert set(PAGE_1_CAPACITY) == set(ALL_REPORT_TYPES)
