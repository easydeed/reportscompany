"""Every theme renders the six pages, in order, and numbers them itself.

WHAT THIS REPLACED. `test_contents_matches_the_document.py` (D-121) checked
that the nine-page architecture's contents page agreed with the document:
each row pointed at the page it named, the footers counted sheets, a dropped
page renumbered the rest. When harbor and linen moved onto Design's six-page
architecture there was no contents page left anywhere, so that file's subject
was gone. Its point was never the contents page; it was "the document the
reader holds is the document we meant to render". This is that, for six pages.

THE CLAIMS, PER THEME
  1. With market data, the sheets are exactly `V2_PAGE_ORDER`, in that order.
  2. Without it, `market_trends` is the only page that goes, and the order of
     the rest is unchanged.
  3. Whatever the caller selects — nothing, the wizard's six, the retired
     nine-page list, only the required pages, or a list in the wrong order —
     the sheets are in document order and always include `REQUIRED_PAGES`.
     The retired list is how an old saved report re-renders; it lost its
     notes page before `normalize_page_set` (that was live: every atlas report
     from the wizard was five pages with no agent panel).
  4. Every sheet carries "Page n of N", n runs 1..N with no gap or repeat, and
     N is the number of sheets — D-121's property, which is what a reader
     uses to tell whether a page is missing.

The expected pages are the builder's own constants, not a list written here:
a hand-copied list would agree with the builder by construction (§0.6). What
is asserted is the RELATION between what was asked for and what rendered.

`scripts/regressions/six_page_set.json` breaks each claim and each goes red.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import THEME_TEMPLATES, PropertyReportBuilder  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)
ORDER = list(PropertyReportBuilder.V2_PAGE_ORDER)
REQUIRED = PropertyReportBuilder.REQUIRED_PAGES
SHEET = re.compile(r'<section class="sheet sheet-(\w+)"')
FOOT = re.compile(r"Page (\d+) of (\d+)")

#: The list the wizard sent before this batch, verbatim, and the one saved on
#: every property report created before it.
RETIRED_NINE = ["cover", "overview", "contents", "aerial", "property",
                "analysis", "market_trends", "comparables", "range"]


def _render(theme, *, market=True, selected=None):
    data = report_data(theme)
    data["selected_pages"] = selected
    if market:
        from worker.compute.market_trends import SAMPLE_MARKET_TRENDS
        data["market_trends_data"] = {**SAMPLE_MARKET_TRENDS, "city": "La Verne"}
    return PropertyReportBuilder(data).render_html()


def _sheets(html):
    return SHEET.findall(html)


@pytest.fixture(scope="module")
def full():
    return {t: _render(t) for t in THEMES}


def test_the_six_pages_are_the_ones_design_specified():
    """The constant itself, once, so a change to it is a visible decision."""
    assert ORDER == ["cover", "property", "comparables", "range", "market_trends", "notes"]
    assert REQUIRED == {"cover", "property", "comparables", "notes"}


@pytest.mark.parametrize("theme", THEMES)
def test_renders_exactly_six_in_order(theme, full):
    assert _sheets(full[theme]) == ORDER, f"{theme}: {_sheets(full[theme])}"


@pytest.mark.parametrize("theme", THEMES)
def test_without_market_data_only_market_trends_goes(theme):
    assert _sheets(_render(theme, market=False)) == [p for p in ORDER if p != "market_trends"]


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("selected", [
    None,
    ORDER,
    RETIRED_NINE,
    ["property", "comparables"],
    list(reversed(ORDER)),
], ids=["nothing", "wizard-six", "retired-nine", "required-only", "reversed"])
def test_any_selection_renders_in_document_order_with_the_required_pages(theme, selected):
    sheets = _sheets(_render(theme, selected=selected))
    assert sheets == [p for p in ORDER if p in sheets], f"{theme}: out of order {sheets}"
    assert REQUIRED <= set(sheets), f"{theme}: missing {sorted(REQUIRED - set(sheets))}"
    asked = {PropertyReportBuilder.LEGACY_PAGES.get(p, p) for p in (selected or ORDER)}
    for optional in set(ORDER) - REQUIRED:
        assert (optional in sheets) == (optional in asked), (
            f"{theme}: {optional} {'rendered without being asked for' if optional in sheets else 'was asked for and did not render'}")


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("market", [True, False], ids=["six", "five"])
def test_every_sheet_numbers_itself_out_of_the_total_rendered(theme, market):
    html = _render(theme, market=market)
    sheets, feet = _sheets(html), FOOT.findall(html)
    assert len(feet) == len(sheets), f"{theme}: {len(sheets)} sheets, {len(feet)} footers"
    assert [int(n) for n, _ in feet] == list(range(1, len(sheets) + 1)), feet
    assert {int(t) for _, t in feet} == {len(sheets)}, (
        f"{theme}: footers claim {sorted({int(t) for _, t in feet})}, "
        f"{len(sheets)} rendered (D-121)")


@pytest.mark.parametrize("theme", THEMES)
def test_a_market_page_without_a_monthly_series_prints_no_python_none(theme):
    """`monthly_median` is None when its computation raises, and the chart
    axis printed `None` three times over an empty plot."""
    from worker.compute.market_trends import SAMPLE_MARKET_TRENDS
    data = report_data(theme)
    data["market_trends_data"] = {**SAMPLE_MARKET_TRENDS, "monthly_median": None}
    html = PropertyReportBuilder(data).render_html()
    assert "sheet-market_trends" in html
    assert ">None<" not in html, f"{theme} prints a Python None"
    assert "Not enough recorded sales to chart" in html
