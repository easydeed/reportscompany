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


def test_the_eight_kind_page_cost_recomputes():
    """Every row, against the cap, the pin and Design's own spec."""
    sys.path.insert(0, str(REPO / "apps/worker/src"))
    from worker.market_builder import PDF_CONFIG  # noqa: E402

    doc = _doc_table_rows()
    assert len(doc) == 8, f"§2a has {len(doc)} parseable kinds, expected 8: {sorted(doc)}"

    wrong = []
    for report_type, (cap, n, ours, theirs) in sorted(doc.items()):
        real_cap = PDF_CONFIG[report_type]["cap"]
        want_n = min(120, real_cap)
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
    assert not wrong, "§2a disagrees with the recomputation:\n  " + "\n  ".join(wrong)


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


def test_the_gallery_question_states_the_asymmetry_correctly():
    """§6's two readings, recomputed.

    The question to Design is only worth asking if the arithmetic behind it is
    right: one reading of the spec changes nothing and the other adds six pages
    to one kind and five to the other. Both numbers come from the same
    measurement as everything else, so both are checked.
    """
    import math
    body = text()
    cases = {
        "new_listings_gallery": (120, 14, 20),
        "open_houses": (100, 12, 17),
    }
    for kind, (n, want_9, want_6) in cases.items():
        page_1 = PAGE_1_CAPACITY[kind]["no_narrative"]
        at_9 = math.ceil((n - page_1) / 9) + 1
        at_6 = math.ceil((n - page_1) / 6) + 1
        assert (at_9, at_6) == (want_9, want_6), (
            f"{kind} at N={n}: a 3x3 continuation gives {at_9} pages and a 3x2 "
            f"gives {at_6}; §6 says {want_9} and {want_6}."
        )
        assert OURS_CONTINUATION[kind] == 9, (
            f"{kind}'s continuation is now "
            f"{OURS_CONTINUATION[kind]}, not 9 — §6's 'unchanged from "
            f"ours' reading no longer holds."
        )
    assert "**20 pages**, from 14" in body
    assert "**17 pages**, from 12" in body
    assert "is a gallery continuation page a 3×3 of the same card" in body, (
        "§6 no longer asks the question. The arithmetic is the argument for "
        "asking it, not a substitute for the ask."
    )
