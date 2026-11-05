"""The consumer report's range panel carries no hard-coded hue (D-199, fixed).

`/r/[id]` is the public home-value report an agent sends a lead. Its hero was a
gradient painted from `branding.primary_color` → `accent_color`, with three
labels hard-coded `text-violet-200`: a hue chosen against the fallback gradient,
so right for exactly one agent, the one who set no brand.

Design's round 2 (R9, 2026-11-05) replaced it with the PDF's range panel on the
fixed dark neutral `#0f172a`, its heading in `primary_on_dark`, which is derived
against that surface. These hold the fix: the panel is on the fixed neutral,
reads no raw brand colour, and no text in it names a Tailwind hue. They were a
strict xfail until the fix landed.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VIEWER = REPO / "apps/web/components/mobile-report/MobileReportViewer.tsx"

BRAND = re.compile(r"branding\?\.(?:primary|accent)_color")
HUE = re.compile(r"text-(?:violet|indigo|purple)-\d+")


def _panel_span(lines):
    """The range panel: from its comment to the address card that follows it."""
    start = next(i for i, l in enumerate(lines) if "{/* Range panel" in l)
    end = next(i for i, l in enumerate(lines) if i > start and "{/* Address card" in l)
    return start, end


def test_the_range_panel_is_on_the_fixed_neutral_not_the_brand():
    """The guard on the test below: if the panel moved, a green run there would
    mean nothing was checked."""
    lines = VIEWER.read_text(encoding="utf-8").splitlines()
    start, end = _panel_span(lines)
    panel = lines[start:end]
    assert len(panel) > 5, "the range panel is no longer where this test looks"
    assert any("background: '#0f172a'" in l for l in panel), (
        "the range panel is no longer on the fixed dark neutral its derived "
        "heading ink (`primary_on_dark`) is computed against")
    assert not any(BRAND.search(l) or "linear-gradient" in l for l in panel), (
        "the range panel paints from the raw brand again")


def test_no_text_inside_the_range_panel_hard_codes_a_hue():
    lines = VIEWER.read_text(encoding="utf-8").splitlines()
    start, end = _panel_span(lines)
    offenders = [(i + 1, l.strip()[:70]) for i, l in enumerate(lines)
                 if start < i < end and HUE.search(l)]
    assert offenders == [], f"hard-coded text hues inside the range panel: {offenders}"
