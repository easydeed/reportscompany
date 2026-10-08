"""The capacity comparison we send Design, against the pin it quotes.

`docs/MARKET_CAPACITY_VS_DESIGN_2026-10-07.md` tells Design their row counts are
less dense than ours and costs one extra page on a 118-row `closed` report. It
is a document that leaves the building, and the figures in it came out of a
browser measurement that CI cannot run.

So the half that can be checked without Chromium is checked: the document must
agree with `PAGE_1_CAPACITY`, which is the pinned result of that measurement and
is itself gated by `test_narrative_box.py`. The stale figures this corrects —
"13 rows on page 1 and 25 on page 2" — sat in a docstring for exactly as long as
nothing read them.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs/MARKET_CAPACITY_VS_DESIGN_2026-10-07.md"
sys.path.insert(0, str(REPO / "apps/worker/tests"))

from test_narrative_box import PAGE_1_CAPACITY  # noqa: E402

#: What Design's package specifies, from the market README's continuation-pages
#: section. Their numbers, not ours to derive — the point is the comparison.
DESIGN_SPEC = {"closed_page_1": 13, "closed_continuation": 26}


def text():
    return DOC.read_text(encoding="utf-8")


def doc_capacity():
    """§5's ```capacity block, parsed.

    NOT `str(rows) in text`. The first version of this gate did that and
    passed on a capacity of 17 because the document contains "D-173" — a
    two-digit number matching inside a defect id. Substring-is-not-a-construct,
    in the gate written to stop a document going stale, which is the third time
    in this session that pattern has been the bug.
    """
    body = text()
    start = body.index("```capacity") + len("```capacity")
    block = body[start:body.index("```", start)]
    out = {}
    for line in block.strip().splitlines():
        key, _, value = line.partition("=")
        report_type, _, state = key.strip().partition(".")
        out.setdefault(report_type, {})[state] = int(value.strip())
    return out


def test_the_document_quotes_the_pinned_capacity():
    """§5, parsed, against the pin — both directions."""
    doc, pin = doc_capacity(), PAGE_1_CAPACITY
    assert doc == pin, (
        f"§5 and PAGE_1_CAPACITY disagree.\n  document: {doc}\n  pin:      "
        f"{pin}\n\nRe-run `measure_market_pagination.py --emit-capacity` and "
        f"update §5. A document sent to Design must not quote a capacity the "
        f"build no longer has — that is the thing we have asked them three "
        f"times not to do."
    )


def test_the_comparison_is_against_the_no_narrative_column():
    """The claim rests on reading their 13 against our 15, not our 11.

    Design removes the narrative from the table kinds, so their page 1 is one
    state. Comparing against the figure production renders today would be
    comparing two different documents, which is the error this whole exchange
    has been about.
    """
    body = text()
    # `closed` moved to the `_v2` page on 2026-10-07 and now reads 17 in BOTH
    # states, because the narrative is suppressed for `V2_KINDS`. The identity
    # is the assertion worth making: page-1 capacity is a number rather than a
    # property of prose length, which is the determinism Design's design buys
    # and the thing the old 15/11 split could not give.
    assert (PAGE_1_CAPACITY["closed"]["no_narrative"]
            == PAGE_1_CAPACITY["closed"]["with_narrative"] == 17), (
        f"`closed` reads {PAGE_1_CAPACITY['closed']}. Two different numbers "
        f"mean the narrative is reaching the `_v2` page again, which makes "
        f"page-1 capacity depend on prose length."
    )
    # `inventory` has NOT moved, and still shows the swing the move removes.
    assert PAGE_1_CAPACITY["inventory"]["no_narrative"] == 15
    assert PAGE_1_CAPACITY["inventory"]["with_narrative"] == 11
    assert "the middle column" in body, (
        "the document no longer says which column the comparison is against. "
        "Their 13 is a no-narrative figure; ours is 15 without and 11 with."
    )


def test_the_page_cost_arithmetic_holds():
    """One extra page on N=118, from Design's own formula.

    Recomputed rather than trusted, because it is the only number in the
    document that is arithmetic on top of a measurement and so the only one
    that can be wrong while every input is right.
    """
    import math
    n = 118
    theirs = math.ceil((n - DESIGN_SPEC["closed_page_1"])
                       / DESIGN_SPEC["closed_continuation"]) + 1
    ours_p1 = PAGE_1_CAPACITY["closed"]["no_narrative"]
    ours = math.ceil((n - ours_p1) / 29) + 1
    assert (theirs, ours) == (6, 5), (
        f"the page cost is now theirs={theirs}, ours={ours}; the document says "
        f"6 and 5. Either a capacity moved or Design's spec changed."
    )
    assert "| Design's spec (13 + 26/page) | **6** |" in text()
    assert "| ours, no narrative (15 + 29/page) | **5** |" in text()


def test_the_stale_docstring_is_not_back():
    """The figures this corrects, by value."""
    script = (REPO / "scripts/measure_market_pagination.py").read_text(
        encoding="utf-8")
    assert "13 rows on page 1 and 25 on page 2" not in script
    assert "11 then 29" in script, (
        "the script's docstring no longer records the measurement that "
        "replaced the stale one. A corrected number with no date and no "
        "method is the next stale number."
    )


# ─────────────────────────────────────────────────────────────────────────────
# §2a — the eight-kind page cost.
#
# Gated because §0.6's new rule applies to it: a document's data is for the
# gate. The markdown table IS a structured region, so it is parsed by its pipes
# rather than scanned for numbers — the row is the claim, not the sentence.
# ─────────────────────────────────────────────────────────────────────────────

#: Continuation capacity per kind, from the same measurement run as
#: PAGE_1_CAPACITY. Not in that dict because it pins page 1 only.
OURS_CONTINUATION = {
    "closed": 29, "inventory": 29, "new_listings": 8, "price_bands": 6,
    "market_snapshot": 6, "new_listings_gallery": 9, "featured_listings": 9,
    "open_houses": 9,
}

#: Design's per-kind row counts. `None` continuation means their package states
#: the page-1 grid and NOT what a continuation page carries — which is a real
#: gap in the spec and is why those rows carry no delta.
DESIGN_ROWS = {
    "closed": (13, 26), "inventory": (13, 26), "new_listings": (13, 26),
    "new_listings_gallery": (6, None), "featured_listings": (4, None),
    "open_houses": (9, None), "market_snapshot": (0, None),
    "price_bands": (0, None),
}


def _pages(page_1, continuation, n):
    if n <= page_1:
        return 1
    if not continuation:
        return None
    import math
    return math.ceil((n - page_1) / continuation) + 1


def _doc_table_rows():
    """§2a's rows, by their pipes: `{type: (cap, n, ours, theirs_or_None)}`."""
    rows = {}
    for line in text().splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        name = cells[0].strip("`")
        if name not in DESIGN_ROWS:
            continue
        theirs = cells[4].strip("* ")
        rows[name] = (
            int(cells[1]), int(cells[2]), int(cells[3].strip("* ")),
            int(theirs) if theirs.isdigit() else None,
        )
    return rows


def _forecast_inputs():
    """§2a's ```forecast block — the capacities the forecast was taken with."""
    body = text()
    start = body.index("```forecast") + len("```forecast")
    block = body[start:body.index("```", start)]
    out = {}
    for line in block.strip().splitlines():
        key, _, value = line.partition("=")
        kind, _, field = key.strip().partition(".")
        out.setdefault(kind, {})[field] = int(value.strip())
    return out


def test_the_eight_kind_page_cost_recomputes():
    """§2a's arithmetic, against ITS OWN RECORDED INPUTS — not the live pin.

    This checked `ours` against `PAGE_1_CAPACITY` and broke the moment a kind
    was built, because the pin moved and the forecast did not. That is the
    right behaviour for a current document and the wrong behaviour for a
    recorded one: **a forecast validated against live inputs cannot stay
    valid, and editing it to match destroys the only thing it was for.**

    So §2a now records the capacities it was taken with, and this checks the
    arithmetic is internally consistent. §7 holds the built figures and
    `test_the_built_figures_match_the_live_pin` checks those against the pin.
    """
    sys.path.insert(0, str(REPO / "apps/worker/src"))
    from worker.market_builder import PDF_CONFIG  # noqa: E402

    doc = _doc_table_rows()
    assert len(doc) == 8, f"§2a has {len(doc)} parseable kinds, expected 8: {sorted(doc)}"
    inputs = _forecast_inputs()
    assert inputs, "§2a records no forecast inputs, so its arithmetic cannot be checked"

    wrong = []
    for report_type, (cap, n, ours, theirs) in sorted(doc.items()):
        real_cap = PDF_CONFIG[report_type]["cap"]
        want_n = min(120, real_cap)
        if report_type in inputs:
            want_ours = _pages(inputs[report_type]["page_1"],
                               inputs[report_type]["continuation"], want_n)
        else:
            # Kinds the forecast did not restate took the pin at the time, and
            # none of them has been built, so the pin is still their input.
            want_ours = _pages(PAGE_1_CAPACITY[report_type]["no_narrative"],
                               OURS_CONTINUATION[report_type], want_n)
        t_p1, t_cont = DESIGN_ROWS[report_type]
        want_theirs = _pages(t_p1, t_cont, want_n) if t_cont else None
        if (cap, n, ours, theirs) != (real_cap, want_n, want_ours, want_theirs):
            wrong.append(
                f"{report_type}: document says cap={cap} N={n} ours={ours} "
                f"theirs={theirs}; recomputed cap={real_cap} N={want_n} "
                f"ours={want_ours} theirs={want_theirs}"
            )
    assert not wrong, "§2a disagrees with its own inputs:\n  " + "\n  ".join(wrong)


def test_the_built_figures_match_the_live_pin():
    """§7, which IS current, against the pin — the other half of the split.

    The wired kinds must read the same number in every narrative state, which
    is the determinism Design's design buys, and §7's table must say what the
    pin says.
    """
    sys.path.insert(0, str(REPO / "apps/worker/src"))
    from worker.market_builder import V2_KINDS  # noqa: E402
    import math

    body = text()
    for kind in sorted(V2_KINDS):
        states = set(PAGE_1_CAPACITY[kind].values())
        assert len(states) == 1, (
            f"{kind} is wired to the `_v2` page and reads {PAGE_1_CAPACITY[kind]}. "
            f"Two numbers mean page-1 capacity depends on prose length again."
        )
        page_1 = PAGE_1_CAPACITY[kind]["no_narrative"]
        built = math.ceil((120 - page_1) / 26) + 1
        assert f"| `{kind}` |" in body, f"§7 does not list {kind}"
        assert f"| **{built}** |" in body, (
            f"{kind} builds to {built} pages at {page_1} + 26/page; §7 says "
            f"something else."
        )
    assert "**Eleven pages saved across two kinds**" in body


def test_the_net_saving_is_what_the_document_claims():
    """The headline the decision rests on: eight pages saved, not one lost.

    `closed` alone says +1. All three stated kinds say −8, because
    `new_listings` moves off the analytics layout. A document that quotes only
    the first would be true and misleading, which is the thing §0.6's
    enumerate-the-parts rule is about.
    """
    doc = _doc_table_rows()
    stated = [(o, t) for _, _, o, t in doc.values() if t is not None]
    assert len(stated) == 3, f"{len(stated)} kinds carry a delta, expected 3"
    ours, theirs = sum(o for o, _ in stated), sum(t for _, t in stated)
    assert (ours, theirs) == (26, 18), (
        f"the stated kinds now total ours={ours} theirs={theirs}; the document "
        f"says 26 and 18, a saving of 8."
    )
    body = text()
    assert "| **the three stated kinds** | | | **26** | **18** | **−8** |" in body
    assert "**eight pages saved**" in body, (
        "the document no longer states the net. The per-kind rows are true "
        "individually and the sum is the finding."
    )


# ─────────────────────────────────────────────────────────────────────────────
# The measured answer — `docs/GALLERY_CONTINUATION_MEASURED_2026-10-07.md`.
#
# This replaced an ask. Jerry, 2026-10-07: measure it rather than spend a
# fourth round asking Design for a number we can take ourselves. The document
# is kept gated for the same reason the ask was: it is the record the gallery
# page counts rest on, and §0.6 says its data is for the gate.
# ─────────────────────────────────────────────────────────────────────────────

MEASURED = REPO / "docs/GALLERY_CONTINUATION_MEASURED_2026-10-07.md"

#: The geometry the answer rests on, from
#: `scripts/measure_gallery_continuation_fit.py`. Pinned rather than re-derived
#: because re-deriving needs a browser and CI has none — the same contract as
#: `PAGE_1_CAPACITY`.
CARD_PX, ROW_GAP_PX, BODY_PX = 258, 8, 9.67 * 96


def test_the_gallery_arithmetic_holds():
    """Three rows fit and four do not, recomputed from the pinned geometry.

    The claim is not "9 per page" — it is that 9 is a consequence of a 258px
    card in a 928px body. If the card changes, this says so before the page
    counts quietly move.
    """
    three = 3 * CARD_PX + 2 * ROW_GAP_PX
    four = 4 * CARD_PX + 3 * ROW_GAP_PX
    assert three <= BODY_PX < four, (
        f"three rows are {three}px and four are {four}px against a "
        f"{BODY_PX:.0f}px body — the three-rows-fit conclusion no longer holds."
    )
    headroom = BODY_PX - three
    body = MEASURED.read_text(encoding="utf-8")
    assert f"| **{headroom:.0f}** — 0.53 of a card |" in body, (
        f"headroom is {headroom:.0f}px ({headroom / CARD_PX:.2f} of a card); "
        f"the document states something else."
    )
    assert f"{four:,} — **128px over**" in body or f"{four:,} — 128px over" in body


def test_the_measurement_states_why_a_headless_render_is_faithful():
    """The photo's fixed height is the whole reason, and it is checkable.

    Remote photos do not load in this container. The measurement is only
    trustworthy because `.listing-photo` reserves 180px in CSS regardless — so
    if that rule changes to an intrinsic height, this conclusion is void and
    the document would be asserting something it can no longer support.
    """
    css = (REPO / "apps/worker/src/worker/templates/market/_base/base.jinja2"
           ).read_text(encoding="utf-8")
    # LINE-ANCHORED, and the first version was not. `"height: 180px;" in css`
    # matches inside `min-height: 180px;`, so changing the declaration to a
    # MINIMUM — which makes the box content-driven and voids this whole
    # measurement — left the gate green. The regression harness caught it;
    # a hand-run would have reported a pass. Substring-is-not-a-construct,
    # instance fifteen, in the gate guarding a measurement.
    declared = any(line.strip() == "height: 180px;"
                   for line in css.splitlines())
    assert declared, (
        "`.listing-photo` no longer carries a fixed 180px height. The gallery "
        "measurement was taken without photos and is only faithful because "
        "that space is reserved in CSS. Re-measure with images before "
        "trusting the page counts."
    )
    body = MEASURED.read_text(encoding="utf-8")
    assert "height: 180px" in body
    assert "invariant to content" in body or "does not depend on content" in body


def test_the_capacity_document_reports_the_answer_not_the_question():
    """§6 was an ask; it is now a finding. A stale question is worse than none."""
    body = text()
    assert "Gallery continuation: measured, and it is three rows" in body
    assert "One question back" not in body, (
        "§6 still asks the gallery question, which has been measured and "
        "answered. Leaving the ask in would send Design a question we have "
        "already settled."
    )
