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
    assert PAGE_1_CAPACITY["closed"]["no_narrative"] == 15
    assert PAGE_1_CAPACITY["closed"]["with_narrative"] == 11
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
