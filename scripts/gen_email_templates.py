#!/usr/bin/env python3
"""
Email Template Generator — Render all 8 report types to HTML for QA review.

Calls schedule_email_html() with realistic sample data and writes output to
output/email_reports/<report_type>.html.

Usage:
    cd apps/worker
    python ../../scripts/gen_email_templates.py
    python ../../scripts/gen_email_templates.py --type market_snapshot
    python ../../scripts/gen_email_templates.py --open
"""

import argparse
import os
import sys
import platform
import subprocess
import time
from pathlib import Path

WORKER_SRC = Path(__file__).resolve().parent.parent / "apps" / "worker" / "src"
sys.path.insert(0, str(WORKER_SRC))

from worker.email.template import schedule_email_html

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "email_reports"

SAMPLE_BRAND = {
    "display_name": "Luxury Estates Realty",
    "logo_url": "https://placehold.co/200x60/1B365D/white?text=Luxury+Estates",
    "email_logo_url": "https://placehold.co/200x60/ffffff/1B365D?text=Luxury+Estates",
    "primary_color": "#1B365D",
    "accent_color": "#B8860B",
    "rep_name": "Jennifer Martinez",
    "rep_title": "Luxury Home Specialist",
    "rep_photo_url": "https://randomuser.me/api/portraits/women/44.jpg",
    "rep_phone": "(310) 555-4567",
    "rep_email": "jennifer@luxuryestates.com",
    "contact_line1": "Jennifer Martinez",
    "contact_line2": "Luxury Home Specialist · DRE #02156789",
    "website_url": "https://luxuryestates.com",
}

SAMPLE_LISTINGS = [
    {
        "hero_photo_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop",
        "street_address": "1305 Hilldale Avenue",
        "city": "Los Angeles",
        "zip_code": "90046",
        "list_price": 1375000,
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2600,
        "year_built": 1958,
        "days_on_market": 28,
        "close_price": 1350000,
        "sale_to_list_ratio": 98.2,
    },
    {
        "hero_photo_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop",
        "street_address": "8742 Wonderland Avenue",
        "city": "Los Angeles",
        "zip_code": "90046",
        "list_price": 1625000,
        "bedrooms": 5,
        "bathrooms": 3.5,
        "sqft": 3200,
        "year_built": 1972,
        "days_on_market": 14,
        "close_price": 1650000,
        "sale_to_list_ratio": 101.5,
    },
    {
        "hero_photo_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop",
        "street_address": "2190 Laurel Canyon Blvd",
        "city": "Los Angeles",
        "zip_code": "90046",
        "list_price": 1195000,
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 2200,
        "year_built": 1955,
        "days_on_market": 42,
        "close_price": 1175000,
        "sale_to_list_ratio": 98.3,
    },
    {
        "hero_photo_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop",
        "street_address": "1478 N Kings Road",
        "city": "West Hollywood",
        "zip_code": "90069",
        "list_price": 1545000,
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2950,
        "year_built": 1965,
        "days_on_market": 21,
        "close_price": 1530000,
        "sale_to_list_ratio": 99.0,
    },
    {
        "hero_photo_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&h=400&fit=crop",
        "street_address": "3201 Sunset Plaza Drive",
        "city": "Los Angeles",
        "zip_code": "90069",
        "list_price": 2150000,
        "bedrooms": 5,
        "bathrooms": 4,
        "sqft": 3800,
        "year_built": 1978,
        "days_on_market": 7,
        "close_price": 2175000,
        "sale_to_list_ratio": 101.2,
    },
    {
        "hero_photo_url": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&h=400&fit=crop",
        "street_address": "945 Palm Avenue",
        "city": "Los Angeles",
        "zip_code": "90069",
        "list_price": 895000,
        "bedrooms": 2,
        "bathrooms": 2,
        "sqft": 1450,
        "year_built": 1960,
        "days_on_market": 35,
        "close_price": 880000,
        "sale_to_list_ratio": 98.3,
    },
]

COMMON_METRICS = {
    "total_active": 347,
    "total_pending": 89,
    "total_closed": 124,
    "total_listings": 347,
    "new_this_month": 58,
    "median_list_price": 1285000,
    "median_close_price": 1245000,
    "avg_list_price": 1420000,
    "avg_close_price": 1380000,
    "avg_dom": 32,
    "median_dom": 28,
    "months_of_inventory": 2.8,
    "sale_to_list_ratio": 98.7,
    "close_to_list_ratio": 98.7,
    "avg_ppsf": 628,
    "min_price": 495000,
    "max_price": 4250000,
    "avg_sqft": 2340,
    "new_listings_7d": 23,
    "total_volume": 171180000,
    "property_types": {
        "sfr": 218,
        "condo": 72,
        "townhome": 41,
        "other": 16,
    },
    "price_tiers": {
        "entry": 127,
        "moveup": 148,
        "luxury": 72,
        "entry_range": "Under $750K",
        "moveup_range": "$750K – $1.5M",
        "luxury_range": "$1.5M+",
    },
    "saturday_count": 18,
    "sunday_count": 24,
    "bands": [
        {"name": "Entry Level", "range": "$400K – $750K", "count": 127},
        {"name": "Move-Up", "range": "$750K – $1.5M", "count": 148},
        {"name": "Premium", "range": "$1.5M – $2.5M", "count": 52},
        {"name": "Luxury", "range": "$2.5M+", "count": 20},
    ],
}

REPORT_TYPES = [
    "market_snapshot",
    "new_listings",
    "inventory",
    "closed",
    "price_bands",
    "open_houses",
    "new_listings_gallery",
    "featured_listings",
]


def _call_template(report_type: str, listings=None, suffix: str = "") -> Path:
    """Call schedule_email_html and write to disk. Returns output path."""
    html = schedule_email_html(
        account_name="Luxury Estates Realty",
        report_type=report_type,
        city="Los Angeles",
        zip_codes=["90046", "90069"],
        lookback_days=30,
        metrics=COMMON_METRICS,
        pdf_url="https://example.com/report.pdf",
        unsubscribe_url="https://example.com/unsubscribe",
        brand=SAMPLE_BRAND,
        listings=listings,
        preset_display_name=None,
        filter_description="Single Family Homes - $500K - $2M - 3+ Bedrooms" if listings else None,
        sender_type="REGULAR",
        total_found=len(listings) if listings else 0,
        total_shown=len(listings) if listings else 0,
    )

    filename = f"{report_type}{suffix}.html"
    out_path = OUTPUT_DIR / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path


# Layout modes: listing counts that trigger each adaptive gallery layout
GALLERY_VARIANTS = [
    ("3col",     6, "3-column grid (6 listings)"),
    ("2col",     4, "2-column grid (4 listings)"),
    ("vertical", 5, "Vertical list (5 listings)"),
    ("single",   1, "Single listing"),
    ("large",   10, "Large set - vertical (10 listings)"),
]


def generate_report(report_type: str) -> list:
    """Generate report(s) for a type. Returns list of (label, path) tuples."""
    needs_listings = report_type in (
        "new_listings_gallery", "featured_listings", "inventory", "closed"
    )

    if report_type in ("new_listings_gallery", "featured_listings"):
        results = []
        # Default (6 listings = 3-col grid)
        path = _call_template(report_type, listings=SAMPLE_LISTINGS)
        results.append((report_type, path))
        # Gallery layout variants
        for variant_suffix, count, _desc in GALLERY_VARIANTS:
            padded = _pad_listings(count)
            path = _call_template(
                report_type, listings=padded, suffix=f"_{variant_suffix}"
            )
            results.append((f"{report_type}_{variant_suffix}", path))
        return results

    listings = SAMPLE_LISTINGS if needs_listings else None
    path = _call_template(report_type, listings=listings)
    return [(report_type, path)]


def _pad_listings(target_count: int) -> list:
    """Return a listing list of exactly target_count items, cycling samples."""
    result = []
    for i in range(target_count):
        result.append(SAMPLE_LISTINGS[i % len(SAMPLE_LISTINGS)])
    return result


def _open_file(path: str):
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", path])
        elif system == "Windows":
            os.startfile(path)
        elif system == "Linux":
            subprocess.run(["xdg-open", path])
    except Exception as e:
        print(f"  Could not open file: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate email report HTML for all 8 report types"
    )
    parser.add_argument(
        "--type",
        choices=REPORT_TYPES + ["all"],
        default="all",
        help="Report type to generate (default: all)",
    )
    parser.add_argument("--open", action="store_true", help="Open output in browser")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    types_to_run = REPORT_TYPES if args.type == "all" else [args.type]

    overall_start = time.perf_counter()
    results = []

    for rt in types_to_run:
        start = time.perf_counter()
        try:
            generated = generate_report(rt)
            elapsed = time.perf_counter() - start
            for label, out_path in generated:
                size = out_path.stat().st_size
                print(f"  [OK] {label:40s}  ->  {out_path.name}  ({size:,} bytes)")
                results.append((label, True, out_path))
            print(f"       ({elapsed:.2f}s)")
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f"  [FAIL] {rt:40s}  ->  {e}")
            results.append((rt, False, None))

    overall = time.perf_counter() - overall_start
    ok = sum(1 for _, s, _ in results if s)
    print(f"\n{'='*60}")
    print(f"  Done! {ok}/{len(results)} reports generated in {overall:.2f}s")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    if args.open:
        for _, success, path in results:
            if success and path:
                _open_file(str(path))

    if ok < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
