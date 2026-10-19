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


def test_the_hue_tally_is_the_one_the_relay_quotes(src, doc):
    derived = {}
    for hue in HUE.findall(src):
        derived[hue] = derived.get(hue, 0) + 1
    stated = {
        m.group(1): int(m.group(2))
        for m in re.finditer(r"`((?:indigo|violet)-\d+)` ×(\d+)", doc)
    }
    assert stated, "the relay no longer quotes a hue tally at all"
    assert derived == stated, (
        f"the relay states {stated}; MobileReportViewer.tsx has {derived}"
    )
    assert sum(derived.values()) == 14, (
        f"the relay's question is about fourteen hard-coded sites; there are "
        f"now {sum(derived.values())}"
    )


def test_the_file_is_still_half_brand_driven(src, doc):
    lines = [i for i, l in enumerate(src.splitlines(), 1) if BRAND.search(l)]
    assert len(lines) == 5, (
        f"the relay says five lines read the agent's brand; now {len(lines)}: "
        f"{lines}. If the file became fully brand-driven the question is moot; "
        f"if it became fully hard-coded it is sharper. Either way, re-read it."
    )
    assert "**Five lines take the agent's brand**" in doc


def test_the_collision_the_relay_names_is_still_there(src):
    """Three `text-violet-200` labels sitting on a surface whose colour comes
    from `primary_color`. This is the one claim in the relay that does not need
    a render, so it is the one worth pinning."""
    lines = src.splitlines()
    gradient = next(
        i for i, l in enumerate(lines)
        if "linear-gradient" in l and BRAND.search(l)
    )
    after_hero = next(
        i for i, l in enumerate(lines)
        if i > gradient and "{/* Address Card */}" in l
    )
    violet = [i for i, l in enumerate(lines) if "text-violet-200" in l]
    assert violet and all(gradient < i < after_hero for i in violet), (
        f"the three violet labels are no longer inside the brand-gradient hero "
        f"(gradient at line {gradient + 1}, hero ends by line {after_hero + 1}, "
        f"labels at {[i + 1 for i in violet]}). The relay's one render-free "
        f"claim no longer holds as written."
    )
    assert len(violet) == 3


def test_the_relay_still_says_it_changed_nothing(doc):
    """If someone restyles the viewer, this document stops being an open
    question and becomes a record of a decision Design did not make."""
    assert "Nothing in this file is changed." in doc
