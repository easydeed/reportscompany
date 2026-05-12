"""
Render one PDF per report type for visual review.

This goes through the same MarketReportBuilder + Playwright path the
production worker uses (apps/worker/src/worker/pdf_engine.py), so the
output should match what reps would receive in real reports.

Outputs go to tmp/pdf_review/<report_type>.pdf.

Usage: python scripts/render_all_pdfs_for_review.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "worker" / "src"))

# Stop the AI narrative from making real OpenAI calls (smoke env)
os.environ.setdefault("OPENAI_API_KEY", "")

from worker.market_builder import MarketReportBuilder, PDF_CONFIG  # noqa: E402
from worker.report_builders import build_open_houses_result  # noqa: E402

# Production uses PDFShift (PDF_ENGINE=api). We render through the same
# pdf_engine.render_pdf_pdfshift function so previews match production.
from worker.pdf_engine import render_pdf_pdfshift  # noqa: E402

# ── Synthetic dataset ────────────────────────────────────────────────
# 56 realistic Irvine listings — enough to trigger truncation copy on
# every report type and demonstrate the new multi-page pagination.
STREETS = [
    "Maple Street", "Cedar Lane", "Oak Avenue", "Birch Court", "Pine Drive",
    "Walnut Terrace", "Ridgecrest Way", "Sunset Boulevard", "Marina Point",
    "Eastbluff Drive", "University Drive", "Quail Hill Loop", "Turtle Rock Ridge",
    "Northwood Park", "Woodbridge Pl",
]
PHOTOS = [
    "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400",
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
    "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=400",
    "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=400",
    "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=400",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=400",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400",
]


def make_listing(i: int) -> Dict[str, Any]:
    """One synthetic listing."""
    is_closed = i % 3 == 0
    list_price = 700_000 + (i * 35_000)
    return {
        "street_address": f"{1000 + i * 7} {STREETS[i % len(STREETS)]}",
        "address": f"{1000 + i * 7} {STREETS[i % len(STREETS)]}",
        "city": "Irvine",
        "zip_code": "92602",
        "list_price": list_price,
        "close_price": (list_price - 12_000) if is_closed else None,
        "bedrooms": 3 + (i % 3),
        "bathrooms": 2 + (i % 2),
        "sqft": 1700 + (i * 65),
        "days_on_market": 4 + (i % 22),
        "price_per_sqft": round(list_price / (1700 + i * 65), 0),
        "hero_photo_url": PHOTOS[i % len(PHOTOS)],
        "photo_url": PHOTOS[i % len(PHOTOS)],
        "status": "Closed" if is_closed else "Active",
        "list_date": "2026-04-29",
    }


SAMPLE = [make_listing(i) for i in range(56)]

# Open-houses dataset: 6 listings WITH openHouseDates this week so the
# new build_open_houses_result actually returns rows.
from datetime import datetime, timedelta, timezone

_today = datetime.now(timezone.utc).date()
OPEN_HOUSE_INPUT: List[Dict[str, Any]] = []
for i in range(6):
    p = make_listing(i)
    p["status"] = "Active"
    p["openHouseDates"] = [(_today + timedelta(days=i)).isoformat() + "T13:00:00Z"]
    OPEN_HOUSE_INPUT.append(p)


COMMON_BRANDING = {
    "agent_name": "Sarah Chen",
    "agent_title": "REALTOR®, Coastal Premier Properties",
    "agent_phone": "(949) 555-0142",
    "agent_email": "sarah@coastalpremier.com",
    "agent_photo_url": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=200&h=200&fit=crop&crop=faces",
    "company_name": "Coastal Premier Properties",
    "logo_url": None,
    "primary_color": "#0d7c72",
    "accent_color": "#f59e0b",
}

COMMON_METRICS = {
    "median_list_price": 1_125_000,
    "median_close_price": 1_098_000,
    "avg_dom": 18,
    "median_dom": 16,
    "months_of_inventory": 2.4,
    "price_per_sqft": 545,
    "list_to_sale_ratio": 0.987,
    "close_to_list_ratio": 0.987,
    "min_price": 720_000,
    "max_price": 4_650_000,
    "new_listings_count": 18,
}

COMMON_COUNTS = {"Active": 142, "Pending": 22, "Closed": 38, "NewListings": 18}

PRICE_BANDS = [
    {"label": "Under $900K",   "count": 12, "median_price":   825_000, "avg_dom": 22, "avg_ppsf": 510},
    {"label": "$900K – $1.3M", "count": 28, "median_price": 1_115_000, "avg_dom": 14, "avg_ppsf": 565},
    {"label": "$1.3M+",        "count": 16, "median_price": 1_750_000, "avg_dom": 31, "avg_ppsf": 620},
]


def report_data_for(report_type: str) -> Dict[str, Any]:
    """Build the report_data dict each builder expects."""
    if report_type == "open_houses":
        # Run through the real builder so PDF gets next_open_house etc.
        oh_result = build_open_houses_result(OPEN_HOUSE_INPUT, {"city": "Irvine"})
        oh_result["branding"] = COMMON_BRANDING
        oh_result["metrics"] = COMMON_METRICS
        oh_result["ai_insights"] = (
            "Six open houses are on the calendar in Irvine this week, "
            "weighted toward Quail Hill and Northwood Park. Move-up "
            "buyers should prioritize the weekend block."
        )
        return oh_result

    base: Dict[str, Any] = {
        "report_type": report_type,
        "city": "Irvine",
        "lookback_days": 30 if report_type != "open_houses" else 7,
        "listings": SAMPLE,
        "listings_sample": SAMPLE,
        "metrics": COMMON_METRICS,
        "counts": COMMON_COUNTS,
        "branding": COMMON_BRANDING,
        "preset_display_name": None,
        "filters_label": "Single-Family + Condo • All price ranges",
    }
    if report_type == "price_bands":
        base["price_bands"] = PRICE_BANDS

    base["ai_insights"] = {
        "market_snapshot":      "Irvine momentum stayed steady this month — buyers continue absorbing new inventory at near-list prices, with months of supply hovering at 2.4.",
        "new_listings_gallery": "A strong week for new inventory in Irvine — 24 fresh listings went live, weighted toward 3-bed move-up product in the $1M–$1.4M band.",
        "new_listings":         "New inventory in Irvine is up week over week, with median list prices holding firm around $1.1M.",
        "closed":               "38 homes closed in Irvine over the past 30 days at a 98.7% list-to-sale ratio, signaling continued buyer competition for well-priced product.",
        "inventory":            "142 actively-listed homes in Irvine — modestly up versus last month — but DOM remains compressed at 18 days for well-presented listings.",
        "featured_listings":    "This week's curated list highlights the most distinctive Irvine homes hitting the market, from estate properties to renovated tract favorites.",
        "open_houses":          "Six weekend open houses in Irvine, with a balance of move-up and entry-level product priced from the high $700s to $1.7M.",
        "price_bands":          "The $900K–$1.3M band continues to drive Irvine's volume, accounting for 50% of active inventory and turning fastest at 14 DOM.",
    }.get(report_type, "")

    return base


def render_html(report_type: str) -> str:
    return MarketReportBuilder(report_data_for(report_type)).render_html()


def main() -> int:
    if not os.environ.get("PDFSHIFT_API_KEY"):
        print("ERROR: PDFSHIFT_API_KEY not set in environment.", file=sys.stderr)
        return 2

    # Write to %TEMP% instead of tmp/pdf_review by default — Dropbox's
    # sync daemon intermittently locks files inside the Dropbox folder
    # while a PDF viewer has them open, causing PermissionError on
    # overwrite. Override with --out / OUT env var if you really want
    # the previews inside the repo.
    default_out = Path(os.environ.get("TEMP", "/tmp")) / "trendy_pdf_review"
    out_dir = Path(os.environ.get("PDF_REVIEW_OUT", default_out))
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Writing PDFs to {out_dir}")
    print(f"Engine: PDFShift (production parity)")
    print()

    # pdf_engine.render_pdf_pdfshift writes to PDF_DIR/{run_id}.pdf,
    # so override PDF_DIR to our review folder. Must be set BEFORE
    # importing pdf_engine — handled by re-reading from os.environ.
    os.environ["PDF_DIR"] = str(out_dir)

    # Re-import pdf_engine module attrs (PDF_DIR is module-level)
    import worker.pdf_engine as _pe
    _pe.PDF_DIR = str(out_dir)

    report_types = list(PDF_CONFIG.keys())
    fake_account_id = "00000000-0000-0000-0000-000000000000"

    for rt in report_types:
        t0 = time.perf_counter()
        html = render_html(rt)
        # Save HTML alongside for diffing if needed
        (out_dir / f"{rt}.html").write_text(html, encoding="utf-8")

        # render_pdf_pdfshift names the output by run_id — pass the
        # report_type so we get human-readable filenames.
        try:
            pdf_path_str, _ = render_pdf_pdfshift(
                run_id=rt,
                account_id=fake_account_id,
                html_content=html,
                print_base="https://example.invalid",  # not used (HTML mode)
            )
        except Exception as exc:
            print(f"  {rt:24} FAILED: {exc}")
            continue

        pdf_path = Path(pdf_path_str)
        size_kb = pdf_path.stat().st_size / 1024
        ms = (time.perf_counter() - t0) * 1000
        print(f"  {rt:24} {pdf_path.name:32} {size_kb:>7.1f} KB   {ms:>5.0f} ms")

    print()
    print(f"Done. Open {out_dir} to review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
