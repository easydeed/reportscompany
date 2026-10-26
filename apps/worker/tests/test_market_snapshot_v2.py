"""Market Snapshot on Design's page (D-255): every block from its producer.

The snapshot was the last kind on the legacy market page. On Design's page it
is a band — median at 96px, four stats — over three blocks: months of
inventory, price tiers, property types; and, kept from the legacy page 1 by
Jerry's decision (D-102), the twelve-month median line as a fourth row.

What each test holds, rendered through `MarketReportBuilder` on data made by
`build_market_snapshot_result` — the production producer — not a hand-written
result:

  * the band shows the producer's values and NO pill or arrows: nothing on the
    market path computes a prior period, so there is no "▲ 3.1%" to print;
  * the inventory block's words are `compute.moi.headline`'s — the same
    function the property report's market page prints — and the bar fills one
    cell a month;
  * each tier row is that tier's count, median and MOI, its bar a share of the
    busiest tier, and the headline names the tier with the most sales;
  * the type cards are the three types with the most sales;
  * the median line renders when there is a year of history, and the page
    says so plainly when a block has nothing to show.

`scripts/regressions/market_snapshot_v2.json` breaks each and each goes red.
"""
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")

from worker.compute.moi import headline as moi_headline  # noqa: E402
from worker.market_builder import MarketReportBuilder  # noqa: E402
from worker.report_builders import build_market_snapshot_result  # noqa: E402

NOW = datetime.now()


def _listings():
    """Deterministic: 40 SFR, 20 Condo, 10 Townhome closed in the window at
    known prices; 30 active. Prices step so the tiers are not equal."""
    out = []
    for i, (kind, n, base) in enumerate((("SFR", 40, 1_400_000), ("Condo", 20, 800_000),
                                         ("Townhome", 10, 1_100_000))):
        for j in range(n):
            price = base + j * 10_000
            out.append({"status": "Closed", "property_subtype": kind, "list_price": price,
                        "close_price": price, "close_date": NOW - timedelta(days=1 + j % 25),
                        "list_date": NOW - timedelta(days=30 + j % 25), "days_on_market": 10 + j % 20,
                        "close_to_list_ratio": 100.0, "city": "Irvine"})
    for j in range(30):
        out.append({"status": "Active", "property_subtype": "SFR", "list_price": 1_200_000 + j * 15_000,
                    "days_on_market": 5 + j, "list_date": NOW - timedelta(days=5 + j), "city": "Irvine"})
    return out


def _history():
    return [{"status": "Closed", "close_date": NOW - timedelta(days=30 * m + d),
             "close_price": 1_300_000 + 5_000 * m}
            for m in range(12) for d in range(0, 25, 3)]


def report_data(**over):
    result = build_market_snapshot_result(_listings(), {"city": "Irvine", "lookback_days": 30})
    data = {**result, "report_type": "market_snapshot", "city": "Irvine", "lookback_days": 30,
            "listings": result.get("listings_sample", []), "closed_history": _history(),
            "branding": {"agent_name": "A", "primary_color": "#18235c", "accent_color": "#0d9488"}}
    data.update(over)
    return data


def render(**over):
    b = MarketReportBuilder(report_data(**over))
    return b, b.render_html()


def text(html):
    """The page's words as a reader sees them (entities decoded: autoescape
    writes "It's" as `It&#39;s`)."""
    import html as _html
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)))


def test_the_band_shows_the_producers_values_and_invents_no_trend():
    b, html = render()
    band = b._v2_band()
    m = b.report_data["metrics"]
    assert band["big_px"] == 96
    assert band["label"] == "median sale price in Irvine"
    assert [c["label"] for c in band["cells"]] == ["Closed sales", "Days on market",
                                                   "Sale-to-list", "New listings"]
    assert band["cells"][0]["value"] == str(b.report_data["counts"]["Closed"])
    assert band["pill"] is None and band["pill_sub"] is None
    band_html = html.split('<section class="band"', 1)[1].split("</section>", 1)[0]
    assert "▲" not in band_html and "▼" not in band_html, "an arrow nothing measured"
    assert m["median_close_price"]


def test_the_inventory_block_is_the_shared_sentence_and_one_cell_a_month():
    b, html = render()
    moi = b.report_data["metrics"]["months_of_inventory"]
    want = moi_headline(moi, "Irvine")
    assert want["headline"] in text(html) and want["note"] in text(html)
    cells = re.findall(r'<div class="moi-cell( on)?"></div>', html)
    assert len(cells) == 8
    assert sum(1 for c in cells if c) == sum(want["cells"])


def test_each_tier_row_is_its_own_tier():
    b, html = render()
    tiers = list(b.report_data["price_tiers"].values())
    rows = b._v2_snapshot()["tiers"]
    busiest = max(t["count"] for t in tiers)
    assert [r["closed"] for r in rows] == [str(t["count"]) for t in tiers]
    assert [r["width"] for r in rows] == [round(t["count"] / busiest * 100) for t in tiers]
    assert rows[0]["range"].startswith("Under ") and rows[-1]["range"].endswith("+")
    lead = max(tiers, key=lambda t: t["count"])
    assert f'{lead["label"][:1] + lead["label"][1:].lower()} homes lead' in text(html)
    share = round(lead["count"] / sum(t["count"] for t in tiers) * 100)
    assert f"{share}% of this period's" in text(html)


def test_the_type_cards_are_the_three_busiest_types():
    b, html = render()
    cards = b._v2_snapshot()["types"]
    assert [c["name"] for c in cards] == ["Single-family", "Condo", "Townhome"]
    assert [c["sold"] for c in cards] == ["40", "20", "10"]
    assert "SFR" not in text(html).split("By property type", 1)[1]


def test_the_median_line_is_kept_as_a_row_of_the_page():
    """D-102: the line led the legacy page 1. Kept, not dropped with it."""
    _, html = render()
    assert '<div class="trend-chart' in html
    assert "Twelve months of prices" in html
    _, without = render(closed_history=[])
    assert '<div class="trend-chart' not in without


def test_a_period_with_no_sales_says_so_in_every_block():
    _, html = render(price_tiers={}, by_property_type={},
                     metrics={**report_data()["metrics"], "months_of_inventory": None})
    t = text(html)
    assert "Inventory is not measurable here" in t
    assert "No sales to group by price" in t
    assert "nothing to compare by type" in t
    assert 'class="moi-cell on"' not in html


def test_it_is_one_page_of_body_and_no_listings():
    """Design's snapshot has no listings body; the legacy page sent nine
    cards to page 2."""
    _, html = render()
    assert 'class="gcard' not in html and 'class="trow' not in html


def test_a_slow_market_fills_the_bar_and_does_not_overflow_it():
    """Eleven months of inventory fills all eight cells — the bar is a scale
    to eight, not a count — and the headline says buyers have the edge."""
    _, html = render(metrics={**report_data()["metrics"], "months_of_inventory": 11.0})
    cells = re.findall(r'<div class="moi-cell( on)?"></div>', html)
    assert len(cells) == 8 and all(cells)
    assert "Buyers have the edge" in text(html)
