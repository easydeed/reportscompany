"""
The handover documents state numbers. These are those numbers, re-derived.

WHY THIS EXISTS
---------------
`docs/CLAUDE_DESIGN_HANDOVER.md` and `docs/JERRY_PROPERTY_FIELDS_DECISION.md`
are read by people outside this repository who cannot check them. Both were
written by re-running the measurements rather than quoting earlier write-ups
— and doing that found two numbers in `DEFECT_LIST.md` that were wrong:
the contrast role table said "132 of 215" where it is **146 of 213**, and
the unmeasurable-element sweep was stated as three elements where it is
**one**, in six documents.

A number in a handover goes stale the first time somebody fixes something,
and the reader will never know. So the claims that can be checked cheaply
are checked here, and the expensive one — the full ten-document contrast
measurement — names the command instead.

WHAT IS AND IS NOT ASSERTED
---------------------------
Asserted: the field list, its size, and the live/dead template split. Each
is derived from the code the documents describe, so a change to the code
fails this before it reaches a reader.

Not asserted: the 213/51/2 contrast figures. They need two renders and a
browser, and `test_pdf_contrast.py` already ratchets the underlying
baseline — a second slow copy of that would be a second answer waiting to
be believed. The handover names the command; this test names the gate.
"""
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import THEME_TEMPLATES  # noqa: E402

HANDOVER = REPO / "docs/CLAUDE_DESIGN_HANDOVER.md"
JERRY = REPO / "docs/JERRY_PROPERTY_FIELDS_DECISION.md"
CONTRACT = ROOT / "tests/test_render_context_contract.py"
TEMPLATES = ROOT / "src/worker/templates/property"

#: Settled elsewhere and deliberately not part of Jerry's decision.
SETTLED = {"mailing_address", "estimated_value"}


def orphans() -> set[str]:
    """The sitex_data orphan set, read from the gate that asserts it.

    Read rather than restated: the gate fails when the set changes in either
    direction, so this is the one place the list is true.
    """
    src = CONTRACT.read_text(encoding="utf-8")
    start = src.index('"property_builder reads sitex_data"')
    block = src[start:src.index("mobile_reports reads property_data", start)]
    body = block[block.index("{", block.index("lambda")):]
    return set(re.findall(r'"([a-z_]+)"', body[:body.index("},")]))


def test_the_orphan_count_in_both_documents_matches_the_gate():
    live = orphans()
    assert len(live) == 19, f"the gate now has {len(live)} orphans: {sorted(live)}"
    assert SETTLED <= live
    for doc, n in ((HANDOVER, 19), (JERRY, 17)):
        text = doc.read_text(encoding="utf-8")
        assert str(n) in text, f"{doc.name} no longer states {n}"


def test_every_field_jerry_is_asked_about_is_still_an_orphan():
    """And every orphan is in front of him.

    Both directions: a field quietly sourced leaves a question that no longer
    needs asking, and a field that becomes an orphan after this was written
    is one he was never shown.
    """
    live = orphans() - SETTLED
    text = JERRY.read_text(encoding="utf-8")
    named = {f for f in live if f"`{f}`" in text}
    assert named == live, (
        f"not in the document: {sorted(live - named)}; "
        f"in the document and no longer an orphan: "
        f"{sorted(f for f in SETTLED if f'`{f}`' in text) }"
    )


def test_both_template_trees_are_the_size_the_handover_says():
    """7,715 dead across seven files, 5,767 live across five.

    THE FIRST VERSION OF THIS NUMBER WAS 15,628, FROM A `wc -l` WHOSE GLOB
    LISTED ONE FILE TWICE. It went into two defect entries, a pull request
    and the handover before anything recomputed it — §0.6's first rule, that
    a number in a tool's output is a property of the tool until you check.
    So it is computed here, from the files, and the document has to agree.

    If somebody deletes the dead tree — which is the right outcome — this
    fails, and the handover's section 0 goes with it. That is the point.
    """
    live_paths = {TEMPLATES / v for v in THEME_TEMPLATES.values()}
    dead = sorted(p for p in TEMPLATES.rglob("*.jinja2") if p not in live_paths)
    text = HANDOVER.read_text(encoding="utf-8")

    def total(paths):
        return sum(len(p.read_text(encoding="utf-8").splitlines()) for p in paths)

    assert len(dead) == 7, f"{len(dead)} dead templates now: {[p.name for p in dead]}"
    for label, n in (("dead", total(dead)), ("live", total(sorted(live_paths)))):
        assert f"{n:,}" in text, (
            f"the {label} tree is {n:,} lines; the handover states something else"
        )


@pytest.mark.parametrize("name", sorted(THEME_TEMPLATES.values()))
def test_the_handover_names_the_five_files_to_open(name):
    text = HANDOVER.read_text(encoding="utf-8")
    assert name.split("/")[-1] in text, (
        f"{name} is a live template and the handover does not name it, so a "
        f"designer has no way to tell it from the dead copy beside it"
    )


def test_the_handover_names_the_six_colours_and_their_kinds():
    """The six are the deliverable. Their KIND is what makes the list
    actionable — a literal is a swatch change, a brand default is a rule, a
    derived colour is our code."""
    text = HANDOVER.read_text(encoding="utf-8").lower()
    for colour in ("#94a3b8", "#d69649", "#4a90a4", "#c55145", "#ff6b5b", "#34d1c3"):
        assert colour in text, f"{colour} is one of the six and is not named"
    for kind in ("literal", "brand default", "derived"):
        assert kind in text, f"the handover does not distinguish {kind!r}"
