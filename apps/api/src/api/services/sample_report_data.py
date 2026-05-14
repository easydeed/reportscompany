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

Caps come from `MarketReportBuilder.PDF_CONFIG`. Listing counts here are
deliberately set ABOVE the cap so the "Showing N of M" and "+ K more"
callouts have honest, non-zero numbers in the sample PDF:
  - market_snapshot:    cap=8  → 50 listings  ("+ 42 more")
  - new_listings:       cap=24 → 38 listings  ("+ 14 more")
  - closed:             cap=20 → 28 listings  ("+ 8 more")
  - inventory:          cap=20 → 30 listings  ("+ 10 more")
  - new_listings_gallery cap=24 → 30 listings  (no "+ more", template
                                                says "Showing all")
  - featured_listings:  cap=12 → 8 listings   (curated, under cap)
  - price_bands:        cap=8  → 8 listings   (sample by band)
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


# Stub AI narratives per report type so MarketReportBuilder doesn't try to
# call OpenAI for sample renders. Tone matches production output.
_SAMPLE_AI_INSIGHTS = {
    "market_snapshot": (
        "Conditions in {city} remain decisively in sellers' favor this period. "
        "Active inventory is light at 89 homes against 42 recent closings, "
        "translating to roughly 2.8 months of supply — well below the 5–6 month "
        "balance point. Median sale prices are holding near $1.39M with a "
        "close-to-list ratio above 98%, signaling that well-priced homes are "
        "moving with minimal negotiation. Days on market continue to compress "
        "compared with the prior period, particularly in the entry and move-up "
        "tiers where buyer competition remains strongest."
    ),
    "new_listings": (
        "Thirty-eight fresh listings entered the {city} market this period, a "
        "healthy refresh of inventory across the price spectrum. The median "
        "asking price of $1.32M is consistent with the broader market trend, "
        "and most of the new supply is concentrated in the move-up tier where "
        "buyer demand remains active."
    ),
    "new_listings_gallery": (
        "{city} added 30 new listings this period. Inventory skews toward the "
        "$1M–$2M range, with several well-positioned offerings in the move-up "
        "tier that should generate immediate interest."
    ),
    "closed": (
        "Twenty-eight sales closed in {city} this period at a strong 99.2% "
        "close-to-list ratio. Median sale price reached $1.27M with an average "
        "32 days on market — both indicators of a market where pricing accuracy "
        "is being rewarded with quick, full-price outcomes."
    ),
    "inventory": (
        "{city}'s active inventory sits at 30 homes — a balanced read at "
        "roughly 3.2 months of supply. The market is neither tight nor flooded, "
        "giving buyers reasonable selection while still rewarding sellers who "
        "price competitively."
    ),
    "featured_listings": (
        "This curated selection highlights eight of {city}'s most distinctive "
        "current offerings, ranging from $6.5M to $9.4M. Each property reflects "
        "the qualities defining the upper end of this market: scale, design, "
        "and location."
    ),
    "price_bands": (
        "Inventory in {city} is distributed across four clear price bands, with "
        "the Move-Up tier ($1.5M–$3M) carrying the largest share at 58 homes. "
        "The Luxury band remains thin at 22 listings, suggesting continued "
        "scarcity at the top end."
    ),
    "open_houses": (
        "Eighteen open houses are scheduled across {city} this weekend, "
        "concentrated in the $1.3M–$2.5M range where weekend foot traffic "
        "typically converts strongest into offers."
    ),
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
        Includes a stub `ai_insights` so the builder skips its OpenAI call.
    """
    builder = _BUILDERS.get(report_type, _market_snapshot)
    data = builder(city, lookback_days)
    ai = _SAMPLE_AI_INSIGHTS.get(report_type, _SAMPLE_AI_INSIGHTS["market_snapshot"])
    data["ai_insights"] = ai.format(city=city)
    return data


SUPPORTED_SAMPLE_REPORT_TYPES = list(_BUILDERS.keys())
