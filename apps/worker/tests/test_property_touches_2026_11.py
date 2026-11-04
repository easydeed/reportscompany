"""Design's property-report touches T1–T9 (handoff 2026-11-03), held in place.

Applied edit by edit from `docs/design-claude/updatedReports/design_handoff_property_touchups/
touches.json`, after its `--check` passed against main. T8b (the empty-chart
copy) was held back: it prints "in  to chart" and "over the  of closed sales"
when the city or the window is empty. Its style half, T8a, is applied.

Rendered checks where the behaviour is in the markup; CSS checks where it is
only in the stylesheet, which the before/after renders measured (no page
grew, nothing clipped, caption under its marker on every brand).
"""
import os
import re
import sys
from pathlib import Path

import pytest
from jinja2 import Environment

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import PropertyReportBuilder  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = ("harbor", "linen", "atlas")
TEMPLATE = (Path(__file__).resolve().parents[1]
            / "src/worker/templates/property/_v2/report.jinja2").read_text(encoding="utf-8")


def _render(theme="harbor", **extra):
    d = report_data(theme)
    d.update(extra)
    return PropertyReportBuilder(d).render_html()


def _body(html):
    return html.split("</style>", 1)[1]


# T3 ─ one name for the document
@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("audience,kind", [(None, "Seller's report"), ("consumer", "Home value report")])
def test_the_running_head_names_the_document_as_the_masthead_does(theme, audience, kind):
    extra = {"audience": audience} if audience else {}
    body = _body(_render(theme, **extra))
    heads = re.findall(r'<span class="runhead-address">([^<]*)</span>', body)
    assert heads, "no running head rendered"
    for head in heads:
        assert head.replace("&#39;", "'").startswith(f"{kind} · "), head
    assert "Property report ·" not in body


# T6 ─ a missing-photo tile says how far away the sale is
def test_a_missing_photo_tile_leads_with_the_distance():
    body = _body(_render())
    names = re.findall(r'<span class="comp-nophoto-name">([^<]*)</span>', body)
    assert names and all(n.endswith(" mi") for n in names), names
    assert "From your home · no photo on file" in body


def test_a_tile_with_no_distance_falls_back_to_the_city():
    d = report_data("harbor")
    d["comparables"] = [dict(c, distance=None, distance_miles=None) for c in d["comparables"]]
    body = _body(PropertyReportBuilder(d).render_html())
    names = re.findall(r'<span class="comp-nophoto-name">([^<]*)</span>', body)
    assert names and all(n == "La Verne" for n in names), names
    assert "From your home" not in body


# T7 ─ the caption sits under the marker it describes
def _caption_block():
    start = TEMPLATE.index('{% if doc.subject_x is not none %}\n        <div class="band-you">')
    end = TEMPLATE.index("{% endif %}\n", TEMPLATE.index("</div>", start)) + len("{% endif %}\n")
    return TEMPLATE[start:end]


@pytest.mark.parametrize("x,expect", [
    (12.5, 'style="left:12.5%"'),
    (50.0, 'style="left:50.0%;transform:translateX(-50%)"'),
    (88.0, 'style="right:12.0%"'),
])
def test_the_caption_is_anchored_where_the_marker_is(x, expect):
    html = Environment(autoescape=True).from_string(_caption_block()).render(
        doc={"subject_x": x, "last_sale_label": "$369,000 in 2015"})
    assert expect in html, html


def test_the_axis_row_no_longer_carries_the_caption():
    body = _body(_render())
    axis = re.search(r'<div class="band-axis" style="margin-top:6px">(.*?)</div>', body, re.S).group(1)
    assert "your home" not in axis
    marker = re.search(r'class="band-marker" style="left:([\d.]+)%"', body).group(1)
    assert f'class="band-you-text" style="left:{marker}%"' in body


# T9 ─ tap-to-call and tap-to-write
@pytest.mark.parametrize("theme", THEMES)
def test_the_agents_phone_and_email_are_links(theme):
    body = _body(_render(theme))
    assert '<a class="agentpanel-phone" href="tel:2135550100">(213) 555-0100</a>' in body
    assert '<a class="agentpanel-email" href="mailto:zoe@example.com">zoe@example.com</a>' in body
    pages = body.count('class="pagefoot"')
    assert pages and body.count('<a href="tel:2135550100">(213) 555-0100</a>') == pages


def test_links_look_like_the_text_they_replaced():
    assert "a { color: inherit; text-decoration: none; }" in TEMPLATE


# T1, T2, T4, T5, T8a ─ stylesheet-only touches
@pytest.mark.parametrize("touch,needle", [
    ("T1 name balances", ".cover-for-name { font-family: var(--display); font-weight: var(--display-weight); font-size: 20px; line-height: 1.15; letter-spacing: var(--display-tracking); text-wrap: balance; }"),
    ("T2 in-short ends on an ellipsis", "-webkit-line-clamp: 5; overflow: hidden; }"),
    ("T4 not-on-record is a caption", ".notonrecord { display: flex; flex-direction: column;"),
    ("T5 four comps go 2 x 2", ".comp-grid:has(.comp:nth-child(4):last-child) { grid-template-columns: repeat(2, minmax(0, 1fr)); }"),
    ("T5 one to three comps sit in one row", ".comp-grid:has(.comp:first-child:last-child) { grid-template-rows: none; align-content: start; }"),
    ("T8a empty chart fills its area", ".chart-empty { margin: 0 0 24px; flex: 1;"),
])
def test_the_stylesheet_carries_the_touch(touch, needle):
    assert needle in TEMPLATE, touch


def test_t8b_copy_was_held_back():
    """The empty-chart sentence stays the one that reads whole with no city
    and no window. Design's T8b interpolates both without a guard."""
    assert "Not enough recorded sales to chart a monthly median for this area." in TEMPLATE
