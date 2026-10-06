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
from _template_chain import chain  # noqa: E402

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
    """5,570 dead across five files, 2,284 live across four.

    THE FIRST VERSION OF THIS NUMBER WAS 15,628, FROM A `wc -l` WHOSE GLOB
    LISTED ONE FILE TWICE. It went into two defect entries, a pull request
    and the handover before anything recomputed it — §0.6's first rule, that
    a number in a tool's output is a property of the tool until you check.
    So it is computed here, from the files, and the document has to agree.

    If somebody deletes the dead tree — which is the right outcome — this
    fails, and the handover's section 0 goes with it. That is the point.
    """
    # THE CHAIN, so the shared architecture counts as live. Reading only the
    # entry files put `_v2/report.jinja2` — the file that renders bold's six
    # pages — in the DEAD column, beside D-131's tree, which is the one
    # distinction this test exists to keep straight.
    live_paths = {p for t in THEME_TEMPLATES for p in chain(t)}
    dead = sorted(p for p in TEMPLATES.rglob("*.jinja2") if p not in live_paths)
    text = HANDOVER.read_text(encoding="utf-8")

    def total(paths):
        return sum(len(p.read_text(encoding="utf-8").splitlines()) for p in paths)

    # One dead file per theme plus the two in `property/_base/`. Derived, so the next
    # cut moves it: the literal 7 here went stale on the theme cut and the
    # failure read as "the dead tree changed" when it was "a theme left".
    # One dead twin per theme plus the two in `property/_base/`. A theme moving to the
    # shared architecture does not change this: its `<theme>.jinja2` twin
    # stays dead and its entry file stays live.
    expected_dead = len(THEME_TEMPLATES) + 2
    assert len(dead) == expected_dead, (
        f"{len(dead)} dead templates, expected {expected_dead} "
        f"({len(THEME_TEMPLATES)} themes + _base/base + _base/_macros): "
        f"{[p.name for p in dead]}"
    )
    for label, n in (("dead", total(dead)), ("live", total(sorted(live_paths)))):
        assert f"{n:,}" in text, (
            f"the {label} tree is {n:,} lines; the handover states something else"
        )


@pytest.mark.parametrize("name", sorted(THEME_TEMPLATES.values()))
def test_the_handover_names_every_live_file_to_open(name):
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


# ── the correction documents' contrast claims ──────────────────────────────

CORRECTIONS = REPO / "docs/design-corrections"


def _ratio(fg: str, bg: str) -> float:
    def lum(h):
        h = h.lstrip("#")
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    a, b = sorted((lum(fg), lum(bg)), reverse=True)
    return round((a + 0.05) / (b + 0.05), 2)


#: (foreground, background, what the shared document states).
#: The whole point of that document is that a contrast figure stated as an
#: adjective was wrong by 1.2 in both of Design's READMEs. Stating ours as
#: numbers and not computing them would be the same mistake with better
#: manners.
STATED = [
    ("#8a8e95", "#ffffff", 3.29),
    ("#5e636b", "#ffffff", 6.05),
    ("#b9bbc1", "#ffffff", 1.92),
    ("#dc2626", "#fee2e2", 3.95),
    ("#d97706", "#fef3c7", 2.86),
    ("#059669", "#d1fae5", 3.32),
    ("#16a34a", "#e7f6ed", 2.95),
    ("#ca8a04", "#faf3e5", 2.66),
    ("#dc2626", "#fbe9e9", 4.12),
]


@pytest.mark.parametrize("fg,bg,stated", STATED)
def test_every_ratio_in_the_corrections_is_the_ratio(fg, bg, stated):
    actual = _ratio(fg, bg)
    assert abs(actual - stated) < 0.015, (
        f"the corrections say {fg} on {bg} is {stated}; it is {actual}"
    )
    text = (CORRECTIONS / "00-SHARED.md").read_text(encoding="utf-8")
    assert f"{stated}" in text, f"{fg} on {bg} = {stated} is not stated in 00-SHARED.md"


#: The semantic inks the shared document offers as a floor. Each must be the
#: FIRST value clearing 4.5 that the stated derivation produces — a number
#: that merely passes would hide a derivation that stopped working.
SEMANTIC_INKS = [("#12873d", 4.61), ("#9e6c03", 4.57),
                 ("#b26205", 4.52), ("#05875f", 4.53)]


@pytest.mark.parametrize("ink,stated", SEMANTIC_INKS)
def test_the_semantic_inks_clear_the_threshold(ink, stated):
    actual = _ratio(ink, "#ffffff")
    assert actual >= 4.5, f"{ink} is offered as a semantic ink and measures {actual}"
    assert abs(actual - stated) < 0.015, f"{ink} is {actual}, stated as {stated}"
    assert ink in (CORRECTIONS / "00-SHARED.md").read_text(encoding="utf-8")


def test_the_corrections_name_the_live_templates_and_not_only_the_dead_ones():
    """A correction document whose whole subject is "you read the wrong files"
    has to name the right ones."""
    text = (CORRECTIONS / "00-SHARED.md").read_text(encoding="utf-8")
    for live in ("market/market.jinja2", "<theme>_report.jinja2"):
        assert live in text, f"{live} is not named as a live template"
    # `property/_base/`, QUALIFIED. `00-SHARED.md` already says it per
    # surface — its table lists `market/_base/` in the LIVE column — and this
    # assertion is what keeps that true, because `"_base/" in text` would also
    # be satisfied by a rewrite that called the market base dead.
    for dead in ("trendy-*.html", "property/_base/"):
        assert dead in text, f"{dead} is not named as a dead one"
