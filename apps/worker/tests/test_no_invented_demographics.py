"""
D-136 — the report does not invent demographics, and cannot start to.

`_build_neighborhood_context` and `_build_area_analysis_context` read
`sitex_data["neighborhood"]` and `sitex_data["area_analysis"]`. Neither key
is written by either producer of that blob (D-135), so their defaults were
not defaults — they were the only path:

    "female_ratio": neighborhood.get("female_ratio", "51.5"),
    "male_ratio":   neighborhood.get("male_ratio",   "48.5"),
    "avg_beds":     neighborhood.get("avg_beds",     "3"),
    "area_min_radius": area.get("area_min_radius", "0.1 mi"),

Forty-one fields of made-up figures, assembled on every render.

NO REPORT EVER PRINTED ONE. That is why D-136 was filed FRAGILE rather than
WRONG, and saying so precisely is the D-113 discipline — an unreachable
state is not a live defect. Both contexts are deleted now, so the gate is
not "this is not rendered" but "this does not exist".

WHY A TEST FOR CODE THAT IS GONE
--------------------------------
Because the defect was never the rendering, it was the SHAPE: a plausible
key in the context dict with a plausible number behind it. The next person
adding a "Neighborhood" page to a theme does not look for a producer; they
look for a context key, find one, and ship `51.5% female / 48.5% male` for
a census tract nobody looked at. Deleting the builders removes today's
instance. This stops the shape coming back under any name.
"""
import ast
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import THEME_TEMPLATES, PropertyReportBuilder  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

BUILDER = ROOT / "src/worker/property_builder.py"
TEMPLATES = ROOT / "src/worker/templates/property"
THEMES = sorted(THEME_TEMPLATES)

#: The figures themselves. Written down rather than read from the code, which
#: is the point — a test that read them from the module under test would
#: pass the moment somebody changed `51.5` to `52.0`.
INVENTED = ("51.5", "48.5", "0.1 mi", "0.5 mi", "1.2 mi")


def render_context(theme="teal"):
    """The dict `render_html` hands the template, captured at the handover.

    `render_html` builds it inline and returns a string, so there is nothing
    to import and nothing exposed. Intercepting the template's `render` is
    the only way to see what the templates are actually offered — and what
    they are OFFERED is the subject here, not what they print.
    """
    import jinja2
    captured = {}
    original = jinja2.Template.render

    def spy(self, *a, **kw):
        captured.update(kw or (a[0] if a and isinstance(a[0], dict) else {}))
        return original(self, *a, **kw)

    jinja2.Template.render = spy
    try:
        PropertyReportBuilder(dict(report_data(theme))).render_html()
    finally:
        jinja2.Template.render = original
    assert captured, "nothing captured — the builder no longer renders a Template"
    return captured


@pytest.mark.parametrize("theme", THEMES)
def test_the_context_has_no_neighborhood_and_no_area_analysis(theme):
    """Asserted on the CONTEXT, which is where the trap was.

    Not on the render: both were already absent from every render when they
    were at their most dangerous, sitting in the dict under a plausible name
    waiting for a page to be written against them. A render test was green
    for the entire life of the defect.
    """
    ctx = render_context(theme)
    for key in ("neighborhood", "area_analysis"):
        assert key not in ctx, (
            f"{theme}: `{key}` is back in the render context. Nothing renders "
            f"it today, which is exactly the state D-136 was filed in."
        )


def test_the_builder_does_not_assemble_them():
    """Structural, by parsing, because the context is built inside a 200-line
    method and the dict literal is not importable."""
    tree = ast.parse(BUILDER.read_text(encoding="utf-8"))
    funcs = {n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    gone = {"_build_neighborhood_context", "_build_area_analysis_context"}
    assert not (funcs & gone), (
        f"{sorted(funcs & gone)} is back. Both read a `sitex_data` key no "
        f"producer writes and filled the gap with invented figures (D-136). "
        f"If there is a real source now, the fields come from it and the "
        f"defaults go — a default IS the invention."
    )


def test_no_invented_figure_is_a_default_anywhere_in_the_builder():
    """The shape, not the two function names.

    Renaming the builders would satisfy the test above. These are the actual
    numbers, and they have no business being a fallback for anything.
    """
    src = BUILDER.read_text(encoding="utf-8")
    # Comments are the record of what was removed and say the numbers out
    # loud. Stripped before matching — a grep that finds its own postmortem
    # is the trap this project has now hit nine times.
    code = "\n".join(
        line.split("#", 1)[0] if not line.lstrip().startswith("#") else ""
        for line in src.split("\n")
    )
    hits = [v for v in INVENTED if f'"{v}"' in code or f"'{v}'" in code]
    assert not hits, (
        f"{hits} appear as literals in the builder. These are D-136's invented "
        f"demographics — a ratio and three radii that no data source supplies."
    )


@pytest.mark.parametrize("theme", THEMES)
def test_no_template_reads_a_demographic_context(theme):
    """The other end. The builders are gone; a template referencing them
    would now render empty rather than fabricated — which is better and
    still not something to ship."""
    src = (TEMPLATES / THEME_TEMPLATES[theme]).read_text(encoding="utf-8")
    hits = re.findall(r"\b(?:neighborhood|area_analysis)\.\w+", src)
    assert not hits, (
        f"{theme} reads {sorted(set(hits))}. Nothing produces these (D-135, "
        f"D-136); the page would print blanks, and the fix somebody reaches "
        f"for is a default, which is how this started."
    )
