#!/usr/bin/env python3
"""
Regenerate apps/worker/tests/golden/themes.json.

The golden file is not documentation of what `derive_theme()` does — it is a
lock on what every affiliate on each of the six live themes sees. Running this
is how you CHANGE that, deliberately, and the resulting diff is the review. If
you find yourself running it to make a failing test pass, the failing test was
the point.
"""
import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))

from worker.themes import DARK_SURFACE, WHITE, contrast, derive_theme  # noqa: E402

#: The six themes whose primaries the master plan measured (§02, "Contrast of
#: the current build, measured"). Names are the plan's, lowercased.
THEMES = (
    ("demo_title", "#DC2626"),
    ("luxury_estates", "#0D9488"),
    ("coastal", "#0E7490"),
    ("amber", "#F59E0B"),
    ("lime", "#84CC16"),
    ("violet", "#7C3AED"),
)

HEADER = [
    "GOLDEN FILE — the five derived tokens for the six themes that exist today.",
    "Regenerate with: python3 scripts/regen_theme_golden.py",
    "A diff here means derive_theme() changed what every affiliate on that theme sees.",
    "That is allowed, but never incidentally: the diff is the review.",
    "contrast_primary_on_white is the measurement that motivated Workstream A.",
    "luxury_estates ships 3.74:1 today; primary_ink is what replaces it.",
    "contrast_on_dark_vs_surface is measured against themes.DARK_SURFACE (#0f172a),",
    "the ONE fixed dark neutral decided 2026-09-23 — and against nothing else.",
    "Six of the eight dark surfaces the templates paint today are lighter than it;",
    "see the note on DARK_SURFACE for the measured shortfall on each.",
]


def build():
    themes = collections.OrderedDict()
    for name, hexv in THEMES:
        t = derive_theme(hexv)
        themes[name] = collections.OrderedDict(
            [("input", hexv)]
            + [(k, t[k]) for k in ("primary", "primary_dark", "primary_ink",
                                   "on_primary", "tint", "primary_on_dark")]
            + [
                ("contrast_primary_on_white", round(contrast(t["primary"], WHITE), 2)),
                ("contrast_ink_on_white", round(contrast(t["primary_ink"], WHITE), 2)),
                ("contrast_on_primary", round(contrast(t["on_primary"], t["primary"]), 2)),
                ("contrast_on_dark_vs_surface",
                 round(contrast(t["primary_on_dark"], DARK_SURFACE), 2)),
            ]
        )
    return collections.OrderedDict([("_comment", HEADER), ("themes", themes)])


def main() -> int:
    path = REPO / "apps/worker/tests/golden/themes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), indent=2) + "\n")
    print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
