"""The counts in the report-viewer relay, recomputed.

WHY THIS IS GATED
-----------------
`docs/REPORT_VIEWER_TINTS_FOR_DESIGN_2026-10-19.md` asks Design one question —
whether "no tinted surfaces" reaches inside the report — and the question only
makes sense while the file it describes still looks like that. A relay quoting
a hue tally the source no longer has is the thing we have asked Design three
times not to do, so the tally is recomputed here rather than trusted.

Same split, and the same reasoning, as `test_trend_chart_relay_is_current.py`
and `test_gallery_grid_relay_is_current.py`: what can be derived is derived,
and what cannot be (a rendered screenshot of the teal-brand collision — this
container has no `node_modules`) is stated in the document as not done.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
VIEWER = REPO / "apps/web/components/mobile-report/MobileReportViewer.tsx"
DOC = REPO / "docs/REPORT_VIEWER_TINTS_FOR_DESIGN_2026-10-19.md"

HUE = re.compile(r"\b(?:indigo|violet)-(?:\d+)\b")
BRAND = re.compile(r"branding\?\.(?:primary|accent)_color")


@pytest.fixture(scope="module")
def src():
    return VIEWER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def doc():
    return DOC.read_text(encoding="utf-8")


def test_the_surface_the_relay_asks_about_is_still_the_one_mounted_at_r_id():
    page = (REPO / "apps/web/app/r/[id]/page.tsx").read_text(encoding="utf-8")
    assert "mobile-report/MobileReportViewer" in page, (
        "/r/[id] no longer mounts MobileReportViewer, so the relay is asking "
        "about a file that is not the live consumer report"
    )


def test_no_indigo_or_violet_class_remains(src, doc):
    """Closed 2026-11-05 by Design's round 2. Fourteen hard-coded hue sites when
    the relay was written, five after the first handoff, none since."""
    derived = {}
    for hue in HUE.findall(src):
        derived[hue] = derived.get(hue, 0) + 1
    assert derived == {}, (
        f"the relay is closed on zero; MobileReportViewer.tsx has {derived}. "
        f"A hue class on the report needs a ruling from Design, not a quiet return"
    )
    assert "**No indigo or violet class remains**" in doc


def test_no_line_reads_the_brand_directly(src, doc):
    """Every brand colour on /r comes from `theme_tokens`, the PDF's derived inks.
    Five direct reads when the relay was written, one after the first handoff."""
    lines = [i for i, l in enumerate(src.splitlines(), 1) if BRAND.search(l)]
    assert lines == [], (
        f"MobileReportViewer.tsx reads `branding?.primary/accent_color` directly at {lines}; "
        f"read the tokens instead"
    )
    assert "**no line takes the agent's\n> brand directly**" in doc or \
        "**no line takes the agent's brand directly**" in doc


def test_the_collision_the_relay_named_is_gone(src):
    """Three `text-violet-200` labels on a surface coloured from `primary_color`:
    the relay's one render-free claim. It no longer holds, and must not return."""
    assert "text-violet-200" not in src
    assert not any("linear-gradient" in l and BRAND.search(l) for l in src.splitlines())


def test_the_relay_still_says_it_changed_nothing(doc):
    """If someone restyles the viewer, this document stops being an open
    question and becomes a record of a decision Design did not make."""
    assert "Nothing in this file is changed." in doc
