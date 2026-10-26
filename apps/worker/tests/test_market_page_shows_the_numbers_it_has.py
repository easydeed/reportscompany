"""The market page's four boxes show the four metrics that have a producer (D-167).

Design's page asked for days to contract, share sold in 30 days and share that
took a price cut. None of the three is computed — their helpers are imported
from a module that does not define them — so atlas printed "no data" three
times from 2026-10-06, and harbor and linen would have regressed to the same
on the move to the shared page. The nine-page themes showed days on market,
sale-to-list and price per square foot from `_compute_trends`; the boxes are
those now, labelled as what they are.

THE CLAIMS, PER THEME, rendered through the production path:
  1. Each box is one of `fetch_and_compute_market_trends`' metrics, and a box
     reads "no data" EXACTLY when that metric's `current` is None.
  2. A box's value is that metric's own number, not another metric's.
  3. A box's arrow describes the same metric as its number. The old second
     box was labelled days to contract and took its arrow from days on market.

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

from worker.compute.market_trends import SAMPLE_MARKET_TRENDS  # noqa: E402
from worker.property_builder import THEME_TEMPLATES, PropertyReportBuilder  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)
BOX = re.compile(r'<span class="market-stat-value[^"]*">([^<]*)</span>\s*'
                 r'<span class="market-stat-label">([^<]*)</span>')

#: (label as printed, metric key, how the value is written)
EXPECTED = [
    ("Median sale price", "median_sale_price", lambda m: f"${round(m['current'] / 1000)}K"),
    ("Days on market", "avg_days_on_market", lambda m: str(round(m["current"]))),
    ("Sale-to-list", "list_to_sale_ratio", lambda m: f"{m['current']:.1f}%"),
    ("Price per sq ft", "price_per_sqft", lambda m: f"${m['current']:,}"),
]


def _boxes(theme, trends):
    data = report_data(theme)
    data["market_trends_data"] = trends
    html = PropertyReportBuilder(data).render_html()
    return BOX.findall(html)


@pytest.mark.parametrize("theme", THEMES)
def test_every_box_shows_its_number_when_the_number_exists(theme):
    boxes = _boxes(theme, SAMPLE_MARKET_TRENDS)
    assert len(boxes) == len(EXPECTED), f"{theme}: {boxes}"
    for (value, label), (name, key, fmt) in zip(boxes, EXPECTED):
        assert label.startswith(name), f"{theme}: box labelled {label!r}, expected {name!r}"
        assert value != PropertyReportBuilder.V2_NO_DATA, (
            f"{theme}: {name} reads 'no data' and its number is {SAMPLE_MARKET_TRENDS[key]['current']}")
        assert value == fmt(SAMPLE_MARKET_TRENDS[key]), f"{theme}: {name} shows {value!r}"


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("missing", [k for _, k, _ in EXPECTED])
def test_a_box_says_no_data_only_when_its_own_metric_is_missing(theme, missing):
    trends = {**SAMPLE_MARKET_TRENDS, missing: {**SAMPLE_MARKET_TRENDS[missing], "current": None}}
    for (value, label), (name, key, _) in zip(_boxes(theme, trends), EXPECTED):
        assert (value == PropertyReportBuilder.V2_NO_DATA) == (key == missing), (
            f"{theme}: with {missing} missing, {name} reads {value!r}")


@pytest.mark.parametrize("theme", THEMES)
def test_each_arrow_describes_the_metric_beside_it(theme):
    """Days on market falls 34 -> 28 and sale-to-list rises 97.2 -> 98.5 in
    the sample. Flip one metric's prior and only that box's arrow may move."""
    base = dict((name, label) for (_, label), (name, _, _) in zip(_boxes(theme, SAMPLE_MARKET_TRENDS), EXPECTED))
    assert "▼ 6" in base["Days on market"], base["Days on market"]
    assert "▲ 1.3 pts" in base["Sale-to-list"], base["Sale-to-list"]
    flipped = {**SAMPLE_MARKET_TRENDS,
               "avg_days_on_market": {**SAMPLE_MARKET_TRENDS["avg_days_on_market"],
                                      "prior": 20, "change_pct": 40.0}}
    after = dict((name, label) for (_, label), (name, _, _) in zip(_boxes(theme, flipped), EXPECTED))
    assert "▲ 8" in after["Days on market"], after["Days on market"]
    for name in ("Median sale price", "Sale-to-list", "Price per sq ft"):
        assert after[name] == base[name], f"{theme}: {name} moved when only days on market did"
