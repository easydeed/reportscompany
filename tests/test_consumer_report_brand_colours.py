"""The consumer report's own colours follow the agent's brand, or they do not.

`/r/[id]` is the public home-value report an agent sends a lead. Its hero panel
is painted with `branding.primary_color`, and three labels inside it are
hard-coded `text-violet-200` — a hue chosen against the FALLBACK gradient, so
it is correct for exactly one agent: the one who set no brand.

Gated rather than fixed because the fix is three deletions in a file nothing in
this container can render (D-193), and the surface is the first thing a lead
sees. The marker is strict, so the day the classes go the build says so and
D-199 can be closed.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
VIEWER = REPO / "apps/web/components/mobile-report/MobileReportViewer.tsx"

_D199_GATED = pytest.mark.xfail(
    strict=True,
    reason="D-199: three labels inside the brand-coloured hero are hard-coded "
           "text-violet-200, so every agent who has set a brand gets #DDD6FE "
           "on a surface of their own colour. Not fixed here: three deletions "
           "in a file this container cannot render.",
)

BRAND = re.compile(r"branding\?\.(?:primary|accent)_color")


def _hero_span(lines):
    """The brand-gradient panel: from the gradient to the next sibling card."""
    start = next(i for i, l in enumerate(lines)
                 if "linear-gradient" in l and BRAND.search(l))
    end = next(i for i, l in enumerate(lines)
               if i > start and "{/* Address Card */}" in l)
    return start, end


def test_the_hero_panel_is_still_painted_with_the_agents_brand():
    """The guard on the test below. If the hero stopped reading
    `primary_color`, a green run there would mean nothing was checked."""
    lines = VIEWER.read_text(encoding="utf-8").splitlines()
    start, end = _hero_span(lines)
    assert end > start + 3, "the hero panel is no longer where this test looks"
    assert "text-white" in lines[start], (
        "the hero container no longer sets text-white, which is what the "
        "three hard-coded labels are overriding"
    )


@_D199_GATED
def test_no_text_inside_the_brand_hero_hard_codes_a_hue():
    lines = VIEWER.read_text(encoding="utf-8").splitlines()
    start, end = _hero_span(lines)
    offenders = [
        (i + 1, l.strip()[:70])
        for i, l in enumerate(lines)
        if start < i < end and re.search(r"text-(?:violet|indigo|purple)-\d+", l)
    ]
    assert offenders == [], (
        f"hard-coded text hues inside a panel whose background is the agent's "
        f"brand: {offenders}"
    )
