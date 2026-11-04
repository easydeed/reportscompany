"""The digital report's per-theme faces are the PDF's (Design's handoff, 2026-11-04).

`/p/{code}` (`app/p/[code]/page.tsx`) and `/r/{id}` (`MobileReportViewer.tsx`)
each carry a `THEME_FACES` table — display face, body face, weight, tracking,
case and corner per theme — copied from the PDF entry files
(`templates/property/<theme>/<theme>_report.jinja2`). A copy drifts; this reads
both sides and compares, theme by theme from the registry, so it names none.
"""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/api/src"))
from api.theme_registry import THEME_NUMBER_MAP  # noqa: E402

PAGES = ["apps/web/app/p/[code]/page.tsx", "apps/web/components/mobile-report/MobileReportViewer.tsx"]
THEMES = sorted(THEME_NUMBER_MAP.values())


def _pdf(theme):
    src = (REPO / f"apps/worker/src/worker/templates/property/{theme}/{theme}_report.jinja2").read_text()
    def get(name):
        m = re.search(r"\{%\s*set t_" + name + r"\s*=\s*(['\"])(.*?)\1\s*%\}|\{%\s*set t_" + name + r"\s*=\s*(\d+)\s*%\}", src)
        assert m, (theme, name)
        return m.group(2) if m.group(2) is not None else m.group(3)
    return {k: get(k) for k in ("display", "body", "display_weight", "display_tracking", "display_case", "radius")}


def _norm_stack(stack):
    return [f.strip().strip("'\"") for f in stack.split(",")]


def _page(path, theme):
    src = (REPO / path).read_text()
    loaders = {var: fam.replace("_", " ") for var, fam in
               re.findall(r"const (\w+) = (\w+)\(\{ subsets", src)}
    m = re.search(theme + r": \{ display: `\$\{(\w+)\.style\.fontFamily\}, ([^`]*)`, body: `\$\{(\w+)\.style\.fontFamily\}, ([^`]*)`, "
                  r"weight: (\d+), tracking: ['\"]([^'\"]*)['\"], kase: ['\"]([^'\"]*)['\"], radius: ['\"]([^'\"]*)['\"] \}", src)
    assert m, f"{path}: no THEME_FACES entry for {theme}"
    dvar, dfall, bvar, bfall, weight, tracking, kase, radius = m.groups()
    return {"display": [loaders[dvar]] + _norm_stack(dfall), "body": [loaders[bvar]] + _norm_stack(bfall),
            "weight": weight, "tracking": tracking, "case": kase, "radius": radius}


@pytest.mark.parametrize("path", PAGES)
@pytest.mark.parametrize("theme", THEMES)
def test_the_page_wears_the_pdfs_faces(path, theme):
    pdf, page = _pdf(theme), _page(path, theme)
    assert page["display"] == _norm_stack(pdf["display"]), "display face"
    assert page["body"] == _norm_stack(pdf["body"]), "body face"
    assert page["weight"] == pdf["display_weight"]
    assert page["tracking"] == pdf["display_tracking"]
    assert page["case"] == pdf["display_case"]
    assert page["radius"].removesuffix("px") == pdf["radius"].removesuffix("px"), "corner"


@pytest.mark.parametrize("path", PAGES)
def test_every_live_theme_has_faces_and_no_retired_one_does(path):
    src = (REPO / path).read_text()
    table = re.search(r"const THEME_FACES: Record<string, ThemeFaces> = \{(.*?)\n\};", src, re.S).group(1)
    keys = set(re.findall(r"^\s*(\w+): \{", table, re.M))
    assert keys == set(THEMES)
