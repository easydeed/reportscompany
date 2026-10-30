"""D-134 and D-169: two lines of property-report copy Jerry decided on 2026-10-30.

D-134. The range on the "What the comparable sales support" page had no
method beside it. It now says how it was made: "Range of the comparable sales
shown." — true as written, because low and high are the lowest and highest
closed sale among the comparables, and every comparable is listed in the report.

D-169. The agent's job title shows under their name, if they entered one. It
used to be computed, defaulted to "Real Estate Agent", and printed nowhere.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import PropertyReportBuilder  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = ("harbor", "linen", "atlas")
METHOD = "Range of the comparable sales shown."


def _render(theme, **agent):
    d = report_data(theme)
    d["agent"] = {**(d.get("agent") or {}), **agent}
    return PropertyReportBuilder(d).render_html()


def _body(html):
    return html.split("</style>", 1)[1]


def _text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


@pytest.mark.parametrize("theme", THEMES)
def test_the_range_says_how_it_was_made(theme):
    text = _text(_body(_render(theme)))
    assert METHOD in text
    # beside the figure: after the range headline, before the band
    assert text.index("median") < text.index(METHOD) < text.index("This is what recent sales")


def test_the_method_is_true_of_the_range_it_sits_beside():
    """Low and high are the cheapest and dearest closed comparable, and every
    comparable is in the report, so "of the comparable sales shown" holds."""
    d = report_data("harbor")
    b = PropertyReportBuilder(d)
    comps = d["comparables"]
    closed = sorted(float(c.get("sale_price") or c.get("price")) for c in comps
                    if str(c.get("status") or "").lower() in ("closed", "sold"))
    assert closed, "the fixture has no closed comparables to range over"
    assert b._v2_closed_prices(comps) == closed
    html = b.render_html()
    for c in comps:
        assert (c.get("street_address") or c.get("address")).split(",")[0] in html, (
            "a comparable feeding the range is not shown in the report")


@pytest.mark.parametrize("theme", THEMES)
def test_an_entered_title_shows_under_the_agents_name(theme):
    body = _body(_render(theme, title="Broker Associate"))
    name = body.index('class="agentpanel-name"')
    title = body.index('<span class="agentpanel-title">Broker Associate</span>')
    meta = body.index('class="agentpanel-meta"')
    assert name < title < meta


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("title", [None, "", "   "])
def test_no_title_entered_means_no_line_and_no_default(theme, title):
    body = _body(_render(theme, title=title))
    assert "agentpanel-title" not in body
    assert "Real Estate Agent" not in _text(body)


def test_the_builder_invents_no_title():
    b = PropertyReportBuilder.__new__(PropertyReportBuilder)
    b.report_data = {"agent": {"title": None}, "branding": {}}
    assert b._build_agent_context()["title"] == ""
