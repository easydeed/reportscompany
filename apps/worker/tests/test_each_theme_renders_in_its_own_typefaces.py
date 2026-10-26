"""Each theme's typefaces reach the CSS the browser reads, as valid CSS.

THE DEFECT. The themes differ ONLY in typography (Design's README: "display/
body typeface, weight, tracking, case and corner radius"). Each entry file sets
`t_display` and `t_body` as font stacks with quoted family names, and the
shared page interpolates them into custom properties. The builder renders with
autoescape on, so the quotes came out as `&#39;`:

    --display: &#39;Barlow Condensed&#39;, &#39;Arial Narrow&#39;, sans-serif;

which is not valid CSS. The declaration was dropped and atlas — the default
theme — rendered in the browser's default serif from 2026-10-06, when it moved
onto the shared page, until a render was looked at on 2026-10-26. Nothing
failed: every gate read text, numbers, colours and pages, and a page in Times
has all of those.

THE CLAIMS, PER THEME
  1. The rendered `--display` and `--body-face` are exactly the entry file's
     `t_display` and `t_body`, character for character.
  2. No HTML entity appears anywhere inside a `<style>` block. An entity in CSS
     is always an escaping accident; there is no CSS construct that needs one.

`scripts/regressions/six_page_set.json` removes the `| safe` and this goes red.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import TEMPLATES_DIR, THEME_TEMPLATES, PropertyReportBuilder  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)
ENTITY = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")


def _entry_value(theme, name):
    src = (TEMPLATES_DIR / THEME_TEMPLATES[theme]).read_text(encoding="utf-8")
    m = re.search(r"\{%\s*set\s+" + name + r'\s*=\s*"([^"]*)"\s*%\}', src)
    assert m, f"{theme}: {name} is not set in {THEME_TEMPLATES[theme]}"
    return m.group(1)


@pytest.fixture(scope="module")
def styles():
    out = {}
    for theme in THEMES:
        html = PropertyReportBuilder(report_data(theme)).render_html()
        out[theme] = "".join(re.findall(r"<style>(.*?)</style>", html, re.S))
    return out


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("prop,var", [("--display", "t_display"), ("--body-face", "t_body")])
def test_each_theme_renders_in_its_own_typefaces(theme, prop, var, styles):
    m = re.search(re.escape(prop) + r":\s*([^;]*);", styles[theme])
    assert m, f"{theme}: no {prop} declaration in the rendered CSS"
    assert m.group(1).strip() == _entry_value(theme, var), (
        f"{theme}: {prop} rendered as {m.group(1)!r}, the entry file sets "
        f"{_entry_value(theme, var)!r}")


@pytest.mark.parametrize("theme", THEMES)
def test_no_html_entity_inside_a_style_block(theme, styles):
    found = sorted(set(ENTITY.findall(styles[theme])))
    assert not found, f"{theme}: HTML entities in CSS {found} — an autoescape accident"


@pytest.mark.parametrize("theme", THEMES)
def test_figures_are_lining_on_every_theme(theme, styles):
    """Cormorant's default figures are old-style: linen's cover read
    "2 · I · 786 · 1949". The body sets lining figures and everything
    inherits them."""
    # A rule whose selector is exactly `body` — not the `html, body` reset.
    bodies = re.findall(r"(?m)^\s*body\s*\{([^}]*)\}", styles[theme])
    assert any(re.search(r"font-variant-numeric:\s*lining-nums", b) for b in bodies), (
        f"{theme}: the body does not set lining figures")
