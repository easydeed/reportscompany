#!/usr/bin/env python3
"""
Regenerate apps/worker/tests/golden/color_roles.json.

`compute_color_roles` feeds every property PDF and every market PDF. This file
locks what each of the five property themes and the six picker presets actually
render — **and the contrast each role achieves**, which is the part D-099 was
about: the old helpers claimed AA in their docstrings, enforced 3.0 in their
code, and nothing wrote the achieved number down anywhere.

Running this is how you change those values deliberately. The diff is the review.
"""
import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))

from worker.property_builder import compute_color_roles  # noqa: E402
from worker.themes import contrast  # noqa: E402

WHITE = "#ffffff"

#: The five property themes, each with the dark surface its own templates use
#: (`PropertyReportBuilder._THEME_DARK_BG`) and the brand colour it defaults to.
PROPERTY_THEMES = (
    ("teal", "#34D1C3", "#18235c"),
    ("modern", "#FF6B5B", "#1A1F36"),
    ("classic", "#1B365D", "#1B365D"),
    ("bold", "#0F1629", "#15216E"),
    ("elegant", "#1A1A1A", "#1a1a1a"),
)

#: The six the master plan measured, against the default dark.
PICKER_THEMES = (
    ("demo_title", "#DC2626", "#18235c"),
    ("luxury_estates", "#0D9488", "#18235c"),
    ("coastal", "#0E7490", "#18235c"),
    ("amber", "#F59E0B", "#18235c"),
    ("lime", "#84CC16", "#18235c"),
    ("violet", "#7C3AED", "#18235c"),
)

HEADER = [
    "GOLDEN FILE — compute_color_roles for every theme, with the contrast each role ACHIEVES.",
    "Regenerate with: python3 scripts/regen_color_roles_golden.py",
    "",
    "The ratios are the point. Before D-099 the helpers targeted 3.0 while their",
    "docstrings cited WCAG AA 4.5, and theme_color_on_dark cleared 4.5 on no theme",
    "at all. Writing the achieved number down is what makes that visible.",
    "",
    "on_light is measured against white; on_dark against the theme's own dark",
    "surface; text against the brand colour it sits on. All three must be >= 4.5.",
]


def entry(brand, dark):
    r = compute_color_roles(brand, dark)
    return collections.OrderedDict([
        ("brand", brand.lower()),
        ("dark_surface", dark.lower()),
        ("theme_color", r["theme_color"]),
        ("theme_color_light", r["theme_color_light"]),
        ("theme_color_dark", r["theme_color_dark"]),
        ("theme_color_on_light", r["theme_color_on_light"]),
        ("theme_color_on_dark", r["theme_color_on_dark"]),
        ("theme_color_text", r["theme_color_text"]),
        ("achieved", collections.OrderedDict([
            ("on_light_vs_white", round(contrast(r["theme_color_on_light"], WHITE), 2)),
            ("on_dark_vs_surface", round(contrast(r["theme_color_on_dark"], dark), 2)),
            ("text_vs_brand", round(contrast(r["theme_color_text"], brand), 2)),
            ("raw_brand_vs_white", round(contrast(brand, WHITE), 2)),
        ])),
    ])


def build():
    return collections.OrderedDict([
        ("_comment", HEADER),
        ("property_themes", collections.OrderedDict(
            (n, entry(b, d)) for n, b, d in PROPERTY_THEMES)),
        ("picker_themes", collections.OrderedDict(
            (n, entry(b, d)) for n, b, d in PICKER_THEMES)),
    ])


def main() -> int:
    path = REPO / "apps/worker/tests/golden/color_roles.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), indent=2) + "\n")
    print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
