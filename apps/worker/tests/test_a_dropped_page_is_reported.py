"""
D-142 — a page that failed to load and a page that was never asked for.

`render_html` builds `market_trends` from a live SimplyRETS fetch and
`overview` from an OpenAI call. When either returns nothing it removes the
page and logs at `info`. The document then renders one page shorter with
nothing in it saying so, and **a report missing its market-trends page
because SimplyRETS was down is byte-for-byte the same document as one whose
page set never included it.**

Three readers, none served: the recipient saw a shorter document with no
explanation, the agent saw nothing at all, and we had one `info` line per
render in a log nobody reads per-report.

WHAT THIS GATES, AND WHAT IT DELIBERATELY DOES NOT
---------------------------------------------------
Whether the DOCUMENT says a page is missing, and whether the report row
carries a `pages_dropped` column, are product and schema decisions — Jerry's
and Claude Design's. They are open.

What needed no decision is that the fact be *computable in aggregate*.
"Market trends failed on 40% of consumer reports last week" is the number
the entry says nobody can currently produce, and it needs exactly two
things: the difference computed, and said at a level somebody greps.

So: `pages_dropped` on the builder and in the context (where a theme and a
task can both reach it the day either is decided), and one WARNING per
affected render. **Nothing is logged when nothing was dropped**, so the
line's presence is the signal rather than its contents.

THE DIRECTION THAT MATTERS IS THE QUIET ONE
-------------------------------------------
A test that only checks "a dropped page is reported" passes against code
that reports every render as a drop. Both directions are asserted: a render
that drops nothing must say nothing, or the aggregate it exists to produce
is 100% on every surface and means nothing.
"""
import logging
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import THEME_TEMPLATES, PropertyReportBuilder  # noqa: E402
from worker.theme_registry import DEFAULT_THEME_NAME  # noqa: E402
from _template_chain import SELF_CONTAINED_THEMES  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)

#: The two pages that can vanish, and what each one needs to exist.
#: `market_trends` needs a live SimplyRETS fetch; `overview` needs an OpenAI
#: key. Neither is available in a test, which is precisely why both drop.
DROPPABLE = ("market_trends", "overview")


def render(theme=DEFAULT_THEME_NAME, pages=None):
    # The default theme by NAME, not a literal. This said "teal" until
    # 2026-10-06; `resolve()` returns the default for a retired name, so
    # every test in this file had been measuring bold while saying teal.
    data = dict(report_data(theme))
    if pages is not None:
        data["selected_pages"] = list(pages)
    builder = PropertyReportBuilder(data)
    builder.render_html()
    return builder


def test_a_page_that_could_not_be_built_is_named():
    """Both droppable pages requested, neither service reachable."""
    builder = render(pages=["cover", "property", "market_trends", "overview", "range"])
    assert set(builder.pages_dropped) == set(DROPPABLE), (
        f"asked for {DROPPABLE} with no SimplyRETS and no OpenAI key; "
        f"dropped {builder.pages_dropped}"
    )


def test_a_render_that_drops_nothing_says_nothing(caplog):
    """THE QUIET DIRECTION.

    If every render logs a drop, the aggregate this exists to produce reads
    100% on every surface and is worth nothing. The default page set contains
    neither droppable page, so this render has nothing to report.
    """
    with caplog.at_level(logging.WARNING, logger="worker.property_builder"):
        builder = render(pages=["cover", "property", "analysis", "comparables", "range"])
    assert builder.pages_dropped == []
    assert not [r for r in caplog.records if "pages_dropped" in r.getMessage()], (
        "a render that dropped nothing logged a drop"
    )


def test_the_drop_is_logged_at_warning_and_names_the_pages(caplog):
    """`info` was the old level and half of why nobody read it. A page the
    customer asked for and did not get is not routine."""
    with caplog.at_level(logging.INFO, logger="worker.property_builder"):
        render(pages=["cover", "property", "market_trends", "range"])
    hits = [r for r in caplog.records if "pages_dropped" in r.getMessage()]
    assert len(hits) == 1, f"expected one line, got {len(hits)}"
    assert hits[0].levelno == logging.WARNING, (
        f"logged at {hits[0].levelname}; a missing page is not info"
    )
    assert "market_trends" in hits[0].getMessage(), (
        "the line does not name the page, so the aggregate cannot be taken "
        "per page — which is the question that gets asked"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_the_context_carries_it_so_a_theme_can_render_it(theme):
    """Whether a theme SHOULD is Claude Design's call. That it can is ours.

    Asserted per theme because the context is built once and handed to five
    templates, and a key that reaches four of them is the defect family this
    report has produced five times.
    """
    import jinja2
    captured = {}
    original = jinja2.Template.render

    def spy(self, *a, **kw):
        captured.update(kw or (a[0] if a and isinstance(a[0], dict) else {}))
        return original(self, *a, **kw)

    jinja2.Template.render = spy
    try:
        data = dict(report_data(theme))
        data["selected_pages"] = ["cover", "property", "market_trends", "range"]
        PropertyReportBuilder(data).render_html()
    finally:
        jinja2.Template.render = original
    assert captured.get("pages_dropped") == ["market_trends"], (
        f"{theme}: the context says pages_dropped={captured.get('pages_dropped')!r}"
    )


def test_pages_dropped_is_a_list_before_any_render():
    """A caller reading it should not have to know whether a render has
    happened, and `None` is the shape that makes them find out the hard way."""
    assert PropertyReportBuilder({}).pages_dropped == []


def test_an_added_page_is_not_reported_as_a_drop():
    """`comparables_all` is ADDED to the page set, not dropped from it
    (D-159). A difference taken the wrong way round would report every
    multi-comp report as having lost a page."""
    # A SELF-CONTAINED THEME, because the added page this asserts on is the
    # comparables continuation — and the shared architecture has none: page 4
    # lists every comp, so there is nothing to continue. Using the default
    # theme here asked bold for a page Design removed.
    data = dict(report_data(SELF_CONTAINED_THEMES[0]))
    data["comparables"] = [
        {**data["comparables"][0], "address": f"{i} Added Way",
         "sale_price": 500_000 + i * 1000} for i in range(8)
    ]
    builder = PropertyReportBuilder(data)
    html = builder.render_html()
    assert "comparables-all" in html, "the fixture did not trigger the added page"
    assert builder.pages_dropped == [], (
        f"an added page was counted as dropped: {builder.pages_dropped}"
    )
