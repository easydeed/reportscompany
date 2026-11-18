"""PCT market alert regressions from the November 13 independent review."""
from datetime import datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worker.email.template import schedule_email_html
from worker.report_builders import build_market_snapshot_result, build_result_json


def email(kind, listing):
    return schedule_email_html(
        account_name="Pacific Coast Title", report_type=kind, city="Irvine",
        zip_codes=None, lookback_days=30, metrics={}, pdf_url="https://example.org/report",
        unsubscribe_url="https://example.org/unsubscribe", listings=[listing],
    )


@pytest.mark.parametrize("status", ["Closed", None])
def test_closed_sales_email_uses_the_transaction_price_for_both_displays(status):
    listing = dict(status=status, list_price=950000, close_price=900000)
    html = email("closed", listing)
    assert html.count("$900K") >= 2
    assert "$950K" not in html

    listing["close_price"] = None
    html = email("closed", listing)
    assert "$950K" not in html
    assert html.count("Price N/A") >= 2


def test_active_inventory_uses_asking_price_even_with_an_old_sale():
    html = email("inventory", dict(status="Active", list_price=950000, close_price=900000))
    assert html.count("$950K") >= 2
    assert "$900K" not in html


def test_snapshot_counts_unpriced_activity_outside_monetary_tiers():
    sale = dict(status="Closed", city="Irvine", close_date=datetime.now())
    active = dict(status="Active", city="Irvine")
    rows = [dict(sale, close_price=900000), sale, dict(sale, close_price=None),
            dict(active, list_price=800000), active, dict(active, list_price=None)]
    snapshot = build_market_snapshot_result(rows, {"city": "Irvine"})
    assert snapshot["counts"]["Closed"] == snapshot["counts"]["Active"] == 3
    assert snapshot["metrics"]["median_close_price"] == 900000
    tiers = snapshot["price_tiers"].values()
    assert sum(t["count"] for t in tiers) == sum(t["active_count"] for t in tiers) == 1
    assert build_market_snapshot_result([sale, active], {"city": "Irvine"})["price_tiers"] == {}

@pytest.mark.parametrize("kind", ["closed", "market_snapshot"])
def test_zip_report_keeps_sales_across_selected_zips_and_displays_the_area(kind):
    sale = dict(status="Closed", city="Irvine", close_date=datetime.now(), close_price=900000)
    rows = [dict(sale, zip_code=code) for code in ["92618", "92620", "92604"]]
    area = "92618, 92620"
    result = build_result_json(kind, rows, {"city": None, "zips": [" 92618", "92620 "],
                                           "area_label": area})
    assert result["city"] == area
    assert result["counts"]["Closed"] == result["matched"] == 2

def test_snapshot_hero_never_labels_asking_price_as_a_sale():
    import re
    html = schedule_email_html("PCT", "market_snapshot", "Irvine", None, 30,
                               {"median_list_price": 950000, "total_closed": 1},
                               "https://example.org/report", "https://example.org/unsubscribe")
    text = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    assert "N/A Median Sale Price" in text


@pytest.mark.parametrize("kind", ["market_snapshot", "new_listings", "new_listings_gallery",
                                  "inventory", "closed", "price_bands", "open_houses", "featured_listings"])
def test_zip_scope_from_provider_rows_through_each_builder(kind):
    from worker.compute.extract import PropertyDataExtractor

    raw = [
        {"address": {"postalCode": code, "city": "Irvine"}, "mls": {"status": "Active"},
         "listPrice": 850000, "mlsId": str(i)}
        for i, code in enumerate(["92618-1234", 92620, " 92618 ", "92604", None])
    ]
    rows = PropertyDataExtractor(raw).run()
    assert len(rows) == 5
    report = build_result_json(kind, rows, {"city": None, "zips": ["92618", "92620"],
                                           "area_label": "92618, 92620"})
    assert report["matched"] == 3
    assert report["city"] == "92618, 92620"
