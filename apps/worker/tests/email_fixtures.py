"""
One fixture, shared by the contrast audit, the render-diff gate and the
regeneration script.

Kept in a single place because a gate is only as good as the input it runs on:
three copies of "a plausible email payload" drift, and the one that drifts is
the one that stops exercising the branch you care about. D-099's status badges
were missed exactly that way — the fixture gave every listing a `close_price`,
so only the "Sold" branch ever ran.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.email.template import schedule_email_html  # noqa: E402

REPORT_TYPES = [
    "market_snapshot", "new_listings", "inventory", "closed",
    "price_bands", "open_houses", "new_listings_gallery", "featured_listings",
]

METRICS = {
    "total_active": 42, "total_closed": 18, "months_of_inventory": 2.3,
    "median_list_price": 825000, "median_close_price": 812000,
    "avg_dom": 24, "new_listings_7d": 11, "sale_to_list_ratio": 0.982,
}

#: Half the listings have no close_price, so the "Active" badge branch renders
#: as well as "Sold" — see the note above.
LISTINGS = [
    {
        "street_address": f"{i} Oak St", "city": "La Verne",
        "list_price": 800000 + i * 1000,
        **({"close_price": 790000 + i * 1000} if i % 2 == 0 else {}),
        "bedrooms": 3, "bathrooms": 2, "sqft": 1800,
        "photo_url": "https://assets.example.test/p.jpg",
        "status": "Sold" if i % 2 == 0 else "Active",
        "days_on_market": i,
    }
    for i in range(1, 9)
]

BASE_BRAND = {
    "display_name": "Marisol Ridge Realty", "rep_name": "Dana Ortiz",
    "rep_title": "Broker Associate", "rep_phone": "(626) 555-0134",
    "rep_email": "dana@example.test",
    "website_url": "https://marisolridge.example.test",
}


def render(report_type: str, primary: str | None) -> str:
    brand = dict(BASE_BRAND)
    if primary:
        brand["primary_color"] = primary
        brand["accent_color"] = primary
    return schedule_email_html(
        account_name="Marisol Ridge Realty", report_type=report_type,
        city="La Verne", zip_codes=None, lookback_days=30, metrics=METRICS,
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a" * 64,
        brand=brand, listings=LISTINGS, sender_type="REGULAR",
        total_found=50, total_shown=8,
    )


#: (file stem, brand primary, report type). Luxury Estates because its derived
#: values differ from its raw colour on every role, so a restructure that drops
#: a derivation shows up. Plus the unbranded case, which is the most common
#: account and exercises the defaults.
CASES = (
    [(f"luxury_{rt}", "#0D9488", rt) for rt in REPORT_TYPES]
    + [(f"unbranded_{rt}", None, rt) for rt in ("market_snapshot", "closed")]
)
