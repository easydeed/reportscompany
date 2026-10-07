#!/usr/bin/env python3
"""Design's market colour rule, measured against the brands the product ships.

Design's market README states two thresholds for text on the `primary` band
fill: 3.0 for display text at 24px and above (`display_ink`) and **>=4.5 for
everything under 24px** (`on_primary`). `on_primary` always takes the better of
white and near-black, so the failure mode is a `primary` where NEITHER clears
4.5 — then the band's sub-24px text is below the design's own threshold
whatever the token picks.

WHY THIS IS DERIVED AND NOT A TABLE IN A DOCUMENT. The figures live in
`docs/BRAND_AUDIT_FOR_DESIGN_2026-10-07.md`, which is a document we SEND. Three
bounds have now reached us derived from a sample and stated as a property of a
surface; a table of hexes typed into a markdown file is the same shape, so the
document is checked against this script by
`tests/test_brand_audit_numbers_are_current.py`.

THE PRESETS ARE READ, NOT RESTATED. They live in two TypeScript files — the
settings page and the company page, identical — and parsing them means the
audit cannot describe a picker the product no longer offers.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/worker/src"))

from worker.themes import NEAR_BLACK, WHITE, contrast, derive_theme  # noqa: E402

#: The two files that hold the picker. Both are read and they must agree: a
#: preset list in two places is two answers waiting to diverge, and this is the
#: only reader that would notice.
PRESET_FILES = (
    "apps/web/app/app/settings/branding/page.tsx",
    "apps/web/app/app/company/branding/page.tsx",
)

#: Design's sample, from the market README's colour-role table. Named here
#: because it is THEIR set — it is not ours to derive, and the point of the
#: audit is that the two differ.
DESIGN_SAMPLE = {
    "red": "#DC2626", "cyan": "#0E7490", "violet": "#7C3AED",
    "amber": "#F59E0B", "lime": "#84CC16",
    # Design's sixth sample brand is #0D9488. Its colloquial name collides with
    # a RETIRED THEME name, and `test_no_live_code_path_names_a_retired_theme`
    # cannot tell a brand called teal from a theme called teal — correctly,
    # because that exact collision is what made "four themes" look true in a
    # design package and what this audit is about. Keyed by the name the
    # contrast corpus and the golden file use, which has no collision.
    "luxury_estates": "#0D9488",
}

#: Design's tint panel neutral, for the ink-on-tint column.
DESIGN_TINT = "#F6F5F1"

SMALL_TEXT_MIN = 4.5
DISPLAY_MIN = 3.0

_PRESET = re.compile(
    r'\{\s*name:\s*"([^"]+)",\s*primary:\s*"(#[0-9A-Fa-f]{6})"', re.S)


def presets():
    """`{name: hex}` from the picker, with both copies required to agree."""
    seen = {}
    for rel in PRESET_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        block = text[text.index("COLOR_PRESETS"):]
        block = block[:block.index("]")]
        found = dict(_PRESET.findall(block))
        if not found:
            raise SystemExit(
                f"no COLOR_PRESETS parsed from {rel}. The picker moved or was "
                f"reshaped; fix the parse rather than letting the audit "
                f"describe an empty set."
            )
        if seen and found != seen:
            raise SystemExit(
                f"the two preset copies disagree:\n  {PRESET_FILES[0]}: "
                f"{seen}\n  {rel}: {found}\nOne picker, two literals — "
                f"whichever a customer sees depends on which page they opened."
            )
        seen = found
    return seen


def measure(name, hexv):
    t = derive_theme(hexv)
    w, b = contrast(WHITE, hexv), contrast(NEAR_BLACK, hexv)
    return {
        "name": name, "hex": hexv,
        "white": round(w, 2), "near_black": round(b, 2),
        "best": round(max(w, b), 2),
        "on_primary": t["on_primary"], "display_ink": t["display_ink"],
        "primary_ink": t["primary_ink"],
        "ink_on_white": round(contrast(t["primary_ink"], WHITE), 2),
        "ink_on_tint": round(contrast(t["primary_ink"], t["tint"]), 2),
        "band_below_threshold": max(w, b) < SMALL_TEXT_MIN,
        "display_below_threshold":
            contrast(t["display_ink"], hexv) < DISPLAY_MIN,
        "display_ink_differs": t["display_ink"] != t["on_primary"],
    }


def main() -> int:
    ours = presets()
    o = [measure(n, h) for n, h in ours.items()]
    d = [measure(n, h) for n, h in DESIGN_SAMPLE.items()]
    ours_hex, theirs_hex = set(ours.values()), set(DESIGN_SAMPLE.values())
    report = {
        "thresholds": {"small_text": SMALL_TEXT_MIN, "display": DISPLAY_MIN},
        "design_tint": DESIGN_TINT,
        "ours": o,
        "design_sample": d,
        "shared_hexes": sorted(ours_hex & theirs_hex),
        "ours_not_sampled": sorted(ours_hex - theirs_hex),
        "sampled_not_ours": sorted(theirs_hex - ours_hex),
        "n_ours_band_below": sum(r["band_below_threshold"] for r in o),
        "n_design_band_below": sum(r["band_below_threshold"] for r in d),
        "ours_display_ink_differs":
            sorted(r["name"] for r in o if r["display_ink_differs"]),
        "design_display_ink_differs":
            sorted(r["name"] for r in d if r["display_ink_differs"]),
        "worst_ink_on_tint": min(r["ink_on_tint"] for r in o),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
