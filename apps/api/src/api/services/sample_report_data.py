"""
Canned sample data for the "Download Sample PDF" feature on the branding page.

Each report type returns a dict in the exact shape that
`worker.market_builder.MarketReportBuilder.render_html()` expects — the same
shape that `worker/report_builders.py` produces in production from real MLS
data. This lets sample PDFs go through the SAME render path as live reports
(multi-page support, section labels, truncation copy, "+ N more" callouts,
Outfit font, AI narrative section).

Conventions matched from `worker/report_builders.py`:
  - top-level keys: report_type, city, lookback_days, period_label, report_date,
    counts (Active/Pending/Closed/NewListings), metrics, listings_sample (or
    listings), filters_label, price_bands (analytics layout only).
  - listings use snake_case keys with aliases the builder also accepts:
    street_address, city, list_price/close_price, bedrooms, bathrooms, sqft,
    status, days_on_market, hero_photo_url.

Photo URLs use Unsplash. Production reports re-host MLS photos in R2 and
embed them as base64 — for sample rendering we just rely on the same
`embed_images_as_base64()` pre-render step that production uses, so these
external URLs are fetched and inlined too.

CAPS ARE NOT RESTATED HERE, AND THAT IS DELIBERATE.
This docstring used to carry a seven-row table of `PDF_CONFIG` caps, with the
listing counts "deliberately set ABOVE the cap so the 'Showing N of M' and
'+ K more' callouts have honest, non-zero numbers". Five of the seven figures
were wrong by the time anyone looked (8 vs 9, and four 20-24s against a real
200), `open_houses` was missing from the table entirely, and `more_template`
is now `None` for every type — so the "+ K more" callout the table was written
around does not exist in the builder at all. The builder had deliberately
moved catalog types to high caps and no callout (`market_builder.py:153`); its
description over here was never updated.

The listing counts below are unchanged and still correct. What was wrong was
the copy of the builder's numbers kept beside them, which is the whole shape:
a copy of something another module owns is a thing that drifts, and nothing
reads a docstring loudly enough to notice. So the relationship is DERIVED —
`tests/test_sample_data_matches_the_builder.py` reads `PDF_CONFIG` and reports
which types the fixture exceeds (currently `market_snapshot` alone) and fails
if a cap figure reappears in this docstring.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List


# Stock photography pool — rotates per listing so the gallery looks alive.
_STOCK_PHOTOS = [
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600573472591-ee6981cf35e6?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600566752355-35792bedcfea?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=800&h=600&fit=crop",
]


# Street suffixes + names for procedurally generating realistic addresses.
_STREET_NAMES = [
    "Maple Ave", "Oak St", "Pine Dr", "Cedar Ln", "Elm Ct", "Birch Way",
    "Sycamore Blvd", "Walnut Pl", "Cypress Rd", "Magnolia Dr", "Spruce St",
    "Aspen Ave", "Willow Ln", "Hickory Ct", "Sequoia Dr", "Juniper Way",
    "Acacia Ave", "Linden Pl", "Poplar Rd", "Beech St", "Dogwood Dr",
    "Redwood Ln", "Cherry Ct", "Olive Ave", "Palm Way", "Cottonwood Dr",
]


def _photo(idx: int) -> str:
    return _STOCK_PHOTOS[idx % len(_STOCK_PHOTOS)]


def _addr(idx: int) -> str:
    house_no = 100 + (idx * 37) % 9800
    street = _STREET_NAMES[idx % len(_STREET_NAMES)]
    return f"{house_no} {street}"


def _period_label(lookback_days: int) -> str:
    if lookback_days == 7:
        return "Last 7 days"
    if lookback_days == 14:
        return "Last 2 weeks"
    if lookback_days == 30:
        return "Last 30 days"
    if lookback_days == 60:
        return "Last 60 days"
    if lookback_days == 90:
        return "Last 90 days"
    return f"Last {lookback_days} days"


def _gen_listings(
    count: int,
    *,
    city: str,
    base_price: int,
    price_step: int,
    status: str = "Active",
    dom_base: int = 14,
    dom_step: int = 3,
    with_close_price: bool = False,
    ratio_to_list: float = 0.985,
) -> List[Dict[str, Any]]:
    """Generate a list of realistic-looking sample listings."""
    out: List[Dict[str, Any]] = []
    for i in range(count):
        list_price = base_price + i * price_step
        item: Dict[str, Any] = {
            "street_address": _addr(i),
            "city": city,
            "list_price": list_price,
            "bedrooms": 2 + (i % 4),
            "bathrooms": 2 + (i % 3),
            "sqft": 1400 + (i * 87) % 2600,
            "status": status,
            "days_on_market": dom_base + (i * dom_step) % 60,
            "hero_photo_url": _photo(i),
            "price_per_sqft": int(list_price / (1400 + (i * 87) % 2600)),
        }
        if with_close_price:
            item["close_price"] = int(list_price * ratio_to_list)
            item["close_to_list_ratio"] = round(ratio_to_list * 100, 1)
        out.append(item)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Per-report builders
# ─────────────────────────────────────────────────────────────────────────────


def _market_snapshot(city: str, lookback_days: int) -> Dict[str, Any]:
    # 50 listings total → cap of 8 leaves "+ 42 more"
    closed = _gen_listings(
        25, city=city, base_price=1_100_000, price_step=42_000,
        status="Closed", dom_base=22, with_close_price=True, ratio_to_list=0.987,
    )
    active = _gen_listings(
        25, city=city, base_price=1_250_000, price_step=58_000,
        status="Active", dom_base=12,
    )
    listings_sample = (closed + active)[:50]
    return {
        "report_type": "market_snapshot",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • {_period_label(lookback_days)}",
        "counts": {
            "Active": 89,
            "Pending": 18,
            "Closed": 42,
            "NewListings": 23,
        },
        "metrics": {
            "median_list_price": 1_450_000,
            "median_close_price": 1_385_000,
            "avg_dom": 28,
            "avg_ppsf": 685,
            "close_to_list_ratio": 98.7,
            "months_of_inventory": 2.8,
            "new_listings_count": 23,
        },
        # The snapshot body's two breakdowns (D-255), in the shape
        # `build_market_snapshot_result` writes. They add up to the counts
        # above — 42 closed, 89 active — so the preview's tier bars and type
        # cards agree with its band.
        "price_tiers": {
            "Entry": {"label": "Entry", "count": 17, "active_count": 30,
                      "median_price": 1_150_000, "moi": 1.8,
                      "min_price": None, "max_price": 1_300_000},
            "Move-Up": {"label": "Move-Up", "count": 15, "active_count": 35,
                        "median_price": 1_480_000, "moi": 2.4,
                        "min_price": 1_300_000, "max_price": 1_700_000},
            "Luxury": {"label": "Luxury", "count": 10, "active_count": 24,
                       "median_price": 2_150_000, "moi": 2.4,
                       "min_price": 1_700_000, "max_price": None},
        },
        "by_property_type": {
            "SFR": {"label": "SFR", "count": 24, "active_count": 52,
                    "median_price": 1_520_000, "avg_dom": 26},
            "Condo": {"label": "Condo", "count": 11, "active_count": 22,
                      "median_price": 980_000, "avg_dom": 31},
            "Townhome": {"label": "Townhome", "count": 7, "active_count": 15,
                         "median_price": 1_210_000, "avg_dom": 27},
        },
        "listings_sample": listings_sample,
        "total_listings": 50,
    }


def _new_listings(city: str, lookback_days: int) -> Dict[str, Any]:
    # 38 listings, cap 24, "+ 14 more"
    listings = _gen_listings(
        38, city=city, base_price=950_000, price_step=35_000,
        status="Active", dom_base=4, dom_step=2,
    )
    return {
        "report_type": "new_listings",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • {_period_label(lookback_days)}",
        "counts": {
            "Active": 38,
            "Pending": 0,
            "Closed": 0,
            "NewListings": 38,
        },
        "metrics": {
            "median_list_price": 1_320_000,
            "median_close_price": 0,
            "avg_dom": 6,
            "avg_ppsf": 615,
            "close_to_list_ratio": 0,
            "months_of_inventory": 0,
            "new_listings_count": 38,
        },
        "listings": listings,
        "total_listings": 38,
    }


def _new_listings_gallery(city: str, lookback_days: int) -> Dict[str, Any]:
    # 30 listings → cap 24 (no "+ more" callout for gallery)
    listings = _gen_listings(
        30, city=city, base_price=1_050_000, price_step=48_000,
        status="Active", dom_base=3, dom_step=2,
    )
    return {
        "report_type": "new_listings_gallery",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • {_period_label(lookback_days)}",
        "counts": {
            "Active": 30,
            "Pending": 0,
            "Closed": 0,
            "NewListings": 30,
        },
        "metrics": {
            "median_list_price": 1_485_000,
            "median_close_price": 0,
            "avg_dom": 5,
            "avg_ppsf": 660,
            "close_to_list_ratio": 0,
            "months_of_inventory": 0,
            "new_listings_count": 30,
        },
        "listings": listings,
        "total_listings": 30,
    }


def _closed(city: str, lookback_days: int) -> Dict[str, Any]:
    # 28 listings → cap 20, "+ 8 more"
    listings = _gen_listings(
        28, city=city, base_price=1_120_000, price_step=44_000,
        status="Closed", dom_base=24, with_close_price=True, ratio_to_list=0.992,
    )
    return {
        "report_type": "closed",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • {_period_label(lookback_days)}",
        "counts": {
            "Active": 0,
            "Pending": 0,
            "Closed": 28,
            "NewListings": 0,
        },
        "metrics": {
            "median_list_price": 1_280_000,
            "median_close_price": 1_270_000,
            "avg_dom": 32,
            "avg_ppsf": 595,
            "close_to_list_ratio": 99.2,
            "months_of_inventory": 0,
            "new_listings_count": 0,
        },
        "listings": listings,
        "total_listings": 28,
    }


def _inventory(city: str, lookback_days: int) -> Dict[str, Any]:
    # 30 listings → cap 20, "+ 10 more"
    listings = _gen_listings(
        30, city=city, base_price=1_050_000, price_step=46_000,
        status="Active", dom_base=18, dom_step=4,
    )
    return {
        "report_type": "inventory",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • Active inventory",
        "counts": {
            "Active": 30,
            "Pending": 0,
            "Closed": 0,
            "NewListings": 6,
        },
        "metrics": {
            "median_list_price": 1_175_000,
            "median_close_price": 0,
            "avg_dom": 28,
            "median_dom": 28,
            "avg_ppsf": 590,
            "close_to_list_ratio": 0,
            "months_of_inventory": 3.2,
            "new_listings_count": 6,
        },
        "listings": listings,
        "total_listings": 30,
    }


def _featured_listings(city: str, lookback_days: int) -> Dict[str, Any]:
    # 8 curated luxury — under the cap (12), no "+ more"
    listings = _gen_listings(
        8, city=city, base_price=6_500_000, price_step=420_000,
        status="Active", dom_base=45, dom_step=10,
    )
    # Bump featured listings to ultra-luxury photos + larger sqft
    for i, item in enumerate(listings):
        item["sqft"] = 4200 + i * 350
        item["bedrooms"] = 4 + (i % 3)
        item["bathrooms"] = 4 + (i % 3)
        item["price_per_sqft"] = int(item["list_price"] / item["sqft"])
    return {
        "report_type": "featured_listings",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • Featured listings",
        "counts": {
            "Active": 8,
            "Pending": 0,
            "Closed": 0,
            "NewListings": 0,
        },
        "metrics": {
            "median_list_price": 8_180_000,
            "median_close_price": 0,
            "avg_dom": 65,
            "avg_ppsf": 1_690,
            "close_to_list_ratio": 0,
            "months_of_inventory": 0,
            "new_listings_count": 0,
        },
        "listings": listings,
        "total_listings": 8,
    }


def _price_bands(city: str, lookback_days: int) -> Dict[str, Any]:
    # Sample listings + price_bands array for analytics layout
    listings = _gen_listings(
        8, city=city, base_price=900_000, price_step=520_000,
        status="Active", dom_base=20, dom_step=8,
    )
    price_bands = [
        {"label": "Entry", "range": "Under $1.5M", "count": 42, "active_count": 42, "median_price": 1_180_000},
        {"label": "Move-Up", "range": "$1.5M – $3M", "count": 58, "active_count": 58, "median_price": 2_210_000},
        {"label": "Premium", "range": "$3M – $6M", "count": 45, "active_count": 45, "median_price": 4_350_000},
        {"label": "Luxury", "range": "$6M+", "count": 22, "active_count": 22, "median_price": 8_900_000},
    ]
    return {
        "report_type": "price_bands",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • Price bands",
        "counts": {
            "Active": 167,
            "Pending": 0,
            "Closed": 0,
            "NewListings": 0,
        },
        "metrics": {
            "median_list_price": 2_650_000,
            "median_close_price": 0,
            "avg_dom": 45,
            "avg_ppsf": 985,
            "close_to_list_ratio": 0,
            "months_of_inventory": 0,
            "new_listings_count": 0,
        },
        "listings": listings,
        "price_bands": price_bands,
        "total_listings": sum(b["count"] for b in price_bands),
    }


def _open_houses(city: str, lookback_days: int) -> Dict[str, Any]:
    # Kept for compatibility — the UI is moving away from this report type,
    # but render still works if someone asks for it.
    next_sat = datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)
    listings = _gen_listings(
        18, city=city, base_price=1_300_000, price_step=85_000,
        status="Active", dom_base=10, dom_step=4,
    )
    for i, item in enumerate(listings):
        item["next_open_house"] = (next_sat + timedelta(hours=i)).isoformat()
    return {
        "report_type": "open_houses",
        "city": city,
        "lookback_days": 7,
        "period_label": "This weekend",
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "filters_label": f"{city} • Open houses",
        "counts": {
            "Active": 18,
            "Pending": 0,
            "Closed": 0,
            "NewListings": 0,
        },
        "metrics": {
            "median_list_price": 1_725_000,
            "median_close_price": 0,
            "avg_dom": 14,
            "avg_ppsf": 720,
            "close_to_list_ratio": 0,
            "months_of_inventory": 0,
            "new_listings_count": 0,
        },
        "listings": listings,
        "total_listings": 18,
    }


_BUILDERS = {
    "market_snapshot": _market_snapshot,
    "new_listings": _new_listings,
    "new_listings_gallery": _new_listings_gallery,
    "closed": _closed,
    "inventory": _inventory,
    "featured_listings": _featured_listings,
    "price_bands": _price_bands,
    "open_houses": _open_houses,
}


def get_sample_data(
    report_type: str,
    *,
    city: str = "Irvine",
    lookback_days: int = 30,
) -> Dict[str, Any]:
    """
    Return a sample `report_data` dict for `MarketReportBuilder`.

    Args:
        report_type: One of the supported report types (see _BUILDERS keys).
            Unknown types fall back to "market_snapshot".
        city: City name to embed in the sample. Defaults to "Irvine".
        lookback_days: Period to embed. Defaults to 30.

    Returns:
        A dict shaped like `report_builders.build_*_result()` output, ready to
        be merged with branding/theme keys and passed to `MarketReportBuilder`.
    """
    builder = _BUILDERS.get(report_type, _market_snapshot)
    data = builder(city, lookback_days)
    return data


SUPPORTED_SAMPLE_REPORT_TYPES = list(_BUILDERS.keys())
