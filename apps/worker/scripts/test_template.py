"""
Property Report Template Test Harness
======================================

Renders property reports to HTML and PDF without the full Celery pipeline.
Provides a fast feedback loop (<3s) for template iteration.

Includes page count validation — property reports must be exactly 7 pages.

Usage:
    python scripts/test_template.py --theme bold
    python scripts/test_template.py --theme all
    python scripts/test_template.py --theme teal --html-only
    python scripts/test_template.py --theme classic --open

Output:
    /tmp/template_test/bold_report.pdf
    /tmp/template_test/bold_report.html
"""

import argparse
import os
import sys
import time
import subprocess
import platform
from pathlib import Path

# Add the worker src directory to the path so we can import PropertyReportBuilder
WORKER_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(WORKER_SRC))

from worker.property_builder import PropertyReportBuilder

EXPECTED_PAGE_COUNT = 7

# ---------------------------------------------------------------------
# Sample Data
# ---------------------------------------------------------------------

SAMPLE_REPORT_DATA = {
    "report_type": "seller",
    "theme": 4,  # Will be overridden per-theme
    "accent_color": None,  # Let theme defaults apply

    # Property fields
    "property_address": "1247 Grandview Avenue",
    "property_city": "Los Angeles",
    "property_state": "CA",
    "property_zip": "90046",
    "property_county": "Los Angeles",
    "apn": "5531-024-017",
    "owner_name": "Michael & Sarah Thompson",
    "property_type": "Single Family Residence",

    # SiteX data
    "sitex_data": {
        "latitude": 34.0966,
        "longitude": -118.3649,
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2850,
        "lot_size": 7200,
        "year_built": 1962,
        "garage": 2,
        "pool": "Yes",
        "zoning": "R1",
        "property_type": "Single Family Residence",
        "assessed_value": 1250000,
        "tax_amount": 15625,
        "land_value": 875000,
        "improvement_value": 375000,
        "tax_year": 2024,
        "county": "Los Angeles",
        "census_tract": "1907.01",
        "estimated_value": 1485000,
        "stories": 2,
    },

    # Agent info
    "agent": {
        "name": "Jennifer Martinez",
        "title": "Luxury Home Specialist",
        "license_number": "02156789",
        "phone": "(310) 555-4567",
        "email": "jennifer@luxuryestates.com",
        "company_name": "Luxury Estates Realty",
        # Real placeholders that resolve
        "photo_url": "https://randomuser.me/api/portraits/women/44.jpg",
        "logo_url": "https://placehold.co/200x60/1B365D/white?text=Luxury+Estates",
    },

    # Cover image - a nice house exterior
    "cover_image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1200&h=800&fit=crop",

    # Comparables (4 with varied data)
    "comparables": [
        {
            "address": "1305 Hilldale Avenue",
            "latitude": 34.0945,
            "longitude": -118.3672,
            "photo_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop",
            "sale_price": 1375000,
            "sold_date": "11/15/2024",
            "sqft": 2600,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "year_built": 1958,
            "lot_size": 6800,
            "days_on_market": 28,
            "distance_miles": 0.3,
        },
        {
            "address": "8742 Wonderland Avenue",
            "latitude": 34.1012,
            "longitude": -118.3701,
            "photo_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop",
            "sale_price": 1625000,
            "sold_date": "10/28/2024",
            "sqft": 3200,
            "bedrooms": 5,
            "bathrooms": 3.5,
            "year_built": 1972,
            "lot_size": 8500,
            "days_on_market": 14,
            "distance_miles": 0.5,
        },
        {
            "address": "2190 Laurel Canyon Blvd",
            "latitude": 34.0988,
            "longitude": -118.3780,
            "photo_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=400&h=300&fit=crop",
            "sale_price": 1195000,
            "sold_date": "12/02/2024",
            "sqft": 2200,
            "bedrooms": 3,
            "bathrooms": 2,
            "year_built": 1955,
            "lot_size": 5900,
            "days_on_market": 42,
            "distance_miles": 0.8,
        },
        {
            "address": "1478 N Kings Road",
            "latitude": 34.0935,
            "longitude": -118.3615,
            "photo_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=400&h=300&fit=crop",
            "sale_price": 1545000,
            "sold_date": "09/18/2024",
            "sqft": 2950,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 1965,
            "lot_size": 7100,
            "days_on_market": 21,
            "distance_miles": 0.4,
        },
    ],
}

ALL_THEMES = ["classic", "modern", "elegant", "teal", "bold"]

THEME_NUMBER_MAP = {
    "classic": 1,
    "modern": 2,
    "elegant": 3,
    "teal": 4,
    "bold": 5,
}

OUTPUT_DIR = Path("/tmp/template_test")


def _count_pdf_pages(pdf_path: Path) -> int:
    """Count the number of pages in a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except ImportError:
        print("  [WARN] pypdf not installed -- skipping page count validation")
        print("         Install with: pip install pypdf")
        return -1
    except Exception as e:
        print(f"  [WARN] Could not read PDF for page count: {e}")
        return -1


def render_theme(
    theme_name: str,
    html_only: bool = False,
    open_after: bool = False,
) -> dict:
    """
    Render a single theme to HTML and optionally PDF.

    Returns a dict with render results including page_count (or None).
    """
    result = {"theme": theme_name, "page_count": None, "ok": True}

    print(f"\n{'='*60}")
    print(f"  Rendering theme: {theme_name.upper()}")
    print(f"{'='*60}")

    start = time.perf_counter()

    # Build report data with this theme
    data = {**SAMPLE_REPORT_DATA, "theme": THEME_NUMBER_MAP[theme_name]}
    builder = PropertyReportBuilder(data)

    # Render HTML
    html = builder.render_html()
    html_path = OUTPUT_DIR / f"{theme_name}_report.html"
    html_path.write_text(html, encoding="utf-8")
    html_time = time.perf_counter() - start
    print(f"  HTML: {html_path} ({len(html):,} chars, {html_time:.2f}s)")

    if html_only:
        print(f"  (Skipping PDF -- --html-only)")
        if open_after:
            _open_file(str(html_path))
        return result

    # Render PDF via Playwright with margin: 0 (matching PDFShift production)
    pdf_start = time.perf_counter()
    pdf_path = OUTPUT_DIR / f"{theme_name}_report.pdf"

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Set content and wait for everything to load
            page.set_content(html, wait_until="networkidle")

            # Wait for fonts to finish loading
            page.evaluate("() => document.fonts.ready")

            # Generate PDF — margin: 0 matches PDFShift production behavior
            page.pdf(
                path=str(pdf_path),
                format="Letter",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()

        pdf_time = time.perf_counter() - pdf_start
        pdf_size = pdf_path.stat().st_size
        print(f"  PDF:  {pdf_path} ({pdf_size:,} bytes, {pdf_time:.2f}s)")

        # Page count validation
        page_count = _count_pdf_pages(pdf_path)
        result["page_count"] = page_count
        if page_count == EXPECTED_PAGE_COUNT:
            print(f"  Pages: {page_count} [PASS]")
        elif page_count > 0:
            print(f"  [WARN] {theme_name} report has {page_count} pages (expected {EXPECTED_PAGE_COUNT})")
            result["ok"] = False
        # page_count == -1 means we couldn't read it; already warned above

    except ImportError:
        print("  PDF:  SKIPPED (playwright not installed)")
    except Exception as e:
        print(f"  PDF:  FAILED ({e})")
        result["ok"] = False

    total = time.perf_counter() - start
    print(f"  Total: {total:.2f}s")

    if open_after:
        _open_file(str(pdf_path))

    return result


def _open_file(path: str):
    """Open a file with the system default application."""
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
    parser = argparse.ArgumentParser(description="Render property report templates to HTML/PDF")
    parser.add_argument(
        "--theme",
        required=True,
        help="Theme name (classic, modern, elegant, teal, bold) or 'all'",
    )
    parser.add_argument("--html-only", action="store_true", help="Only output HTML, skip PDF")
    parser.add_argument("--open", action="store_true", help="Open the output after rendering")
    args = parser.parse_args()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Determine themes to render
    if args.theme == "all":
        themes = ALL_THEMES
    elif args.theme in ALL_THEMES:
        themes = [args.theme]
    else:
        print(f"Unknown theme: {args.theme}")
        print(f"Valid themes: {', '.join(ALL_THEMES)} or 'all'")
        sys.exit(1)

    overall_start = time.perf_counter()

    results = []
    for theme in themes:
        result = render_theme(theme, html_only=args.html_only, open_after=args.open)
        results.append(result)

    overall_time = time.perf_counter() - overall_start

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"  Done! {len(themes)} theme(s) in {overall_time:.2f}s")
    print(f"  Output: {OUTPUT_DIR}")

    # Page count validation summary (only when PDFs were generated)
    pdf_results = [r for r in results if r["page_count"] is not None]
    if pdf_results:
        print(f"\n  Page count validation:")
        all_pass = True
        for r in pdf_results:
            if r["page_count"] == EXPECTED_PAGE_COUNT:
                print(f"    {r['theme']:10s} {r['page_count']} pages [PASS]")
            else:
                print(f"    {r['theme']:10s} {r['page_count']} pages [FAIL] (expected {EXPECTED_PAGE_COUNT})")
                all_pass = False

        if all_pass:
            print(f"\n  All themes pass page count validation [PASS]")
        else:
            print(f"\n  [FAIL] SOME THEMES HAVE WRONG PAGE COUNT")

    print(f"{'='*60}\n")

    # Exit with code 1 if any theme has wrong page count
    if any(r["page_count"] is not None and r["page_count"] != EXPECTED_PAGE_COUNT for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
