"""
Generate R2 Preview Screenshots for Property Report Themes
==========================================================

Renders all 5 themes to HTML using PropertyReportBuilder with rich sample
data, then uses Playwright to screenshot each individual page element.

Produces:
  - Cover thumbnail  (408 x 528 px  — half-size, for theme cards)
  - 7 full-page JPGs (816 x 1056 px — letter at 96 DPI)

Matches the URL pattern expected by property-report-assets.ts:
  property-reports/previews/{themeId}.jpg          cover thumbnail
  property-reports/previews/{themeId}/1.jpg        page 1
  ...
  property-reports/previews/{themeId}/7.jpg        page 7

Usage:
    python scripts/generate_preview_screenshots.py
    python scripts/generate_preview_screenshots.py --theme teal
    python scripts/generate_preview_screenshots.py --upload
    python scripts/generate_preview_screenshots.py --local
    python scripts/generate_preview_screenshots.py --theme bold --upload --open
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

WORKER_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(WORKER_SRC))

from worker.property_builder import PropertyReportBuilder  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_THEMES = ["classic", "modern", "elegant", "teal", "bold"]
THEME_NUMBER_MAP = {
    "classic": 1,
    "modern": 2,
    "elegant": 3,
    "teal": 4,
    "bold": 5,
}

# Screenshot specs
PAGE_WIDTH  = 816   # 8.5" × 96 DPI
PAGE_HEIGHT = 1056  # 11"  × 96 DPI
THUMB_WIDTH  = 408  # half-size cover thumbnail
THUMB_HEIGHT = 528

JPEG_QUALITY = 85

OUTPUT_DIR = Path(os.environ.get("PREVIEW_SCREENSHOTS_DIR", "/tmp/preview_screenshots"))

# R2 upload configuration (mirrors property_tasks/property_report.py)
R2_ACCOUNT_ID        = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID     = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME       = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_ENDPOINT          = (
    f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""
)
R2_PUBLIC_URL        = os.getenv("R2_PUBLIC_URL", "")

# ---------------------------------------------------------------------------
# Sample data (reused from test_template.py)
# ---------------------------------------------------------------------------

SAMPLE_REPORT_DATA = {
    "report_type": "seller",
    "theme": 4,
    "accent_color": None,
    "property_address": "1247 Grandview Avenue",
    "property_city": "Los Angeles",
    "property_state": "CA",
    "property_zip": "90046",
    "property_county": "Los Angeles",
    "apn": "5531-024-017",
    "owner_name": "Michael & Sarah Thompson",
    "property_type": "Single Family Residence",
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
    "agent": {
        "name": "Jennifer Martinez",
        "title": "Luxury Home Specialist",
        "license_number": "02156789",
        "phone": "(310) 555-4567",
        "email": "jennifer@luxuryestates.com",
        "company_name": "Luxury Estates Realty",
        "photo_url": "https://randomuser.me/api/portraits/women/44.jpg",
        "logo_url": "https://placehold.co/200x60/1B365D/white?text=Luxury+Estates",
    },
    "cover_image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1200&h=800&fit=crop",
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
    "selected_pages": ["cover", "contents", "aerial", "property", "analysis", "comparables", "range"],
}

# ---------------------------------------------------------------------------
# R2 upload helper
# ---------------------------------------------------------------------------


def upload_to_r2(local_path: str, s3_key: str, content_type: str = "image/jpeg") -> str:
    """Upload a file to Cloudflare R2 and return the public URL."""
    import boto3  # type: ignore
    from botocore.client import Config  # type: ignore

    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        print(f"    [SKIP] R2 credentials not set — upload skipped for {s3_key}")
        return f"(local) {local_path}"

    s3 = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    with open(local_path, "rb") as f:
        s3.upload_fileobj(f, R2_BUCKET_NAME, s3_key, ExtraArgs={"ContentType": content_type})

    if R2_PUBLIC_URL:
        url = f"{R2_PUBLIC_URL.rstrip('/')}/{s3_key}"
    else:
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": R2_BUCKET_NAME, "Key": s3_key}, ExpiresIn=604800
        )

    print(f"    Uploaded → {url}")
    return url


# ---------------------------------------------------------------------------
# Screenshot logic
# ---------------------------------------------------------------------------


def screenshot_theme(
    theme_name: str,
    do_upload: bool,
) -> List[Dict[str, Any]]:
    """
    Render one theme and take screenshots of all 7 pages.

    Returns a list of dicts with keys: page_number, local_path, r2_key, url.
    """
    theme_id = THEME_NUMBER_MAP[theme_name]
    print(f"\n{'='*60}")
    print(f"  Theme: {theme_name.upper()} (id={theme_id})")
    print(f"{'='*60}")

    t0 = time.perf_counter()

    # 1. Render HTML
    data = {**SAMPLE_REPORT_DATA, "theme": theme_id}
    builder = PropertyReportBuilder(data)
    html = builder.render_html()
    print(f"  HTML rendered: {len(html):,} chars ({time.perf_counter()-t0:.2f}s)")

    # 2. Output directory for this theme
    theme_dir = OUTPUT_DIR / theme_name
    theme_dir.mkdir(parents=True, exist_ok=True)

    results = []

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print("  [ERROR] playwright is not installed.")
        print("          Install with: pip install playwright && playwright install chromium")
        return results

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # Full-res page (816 × 1056) — we make the viewport wide enough so pages
        # don't reflow, then screenshot each element individually.
        page = browser.new_page(viewport={"width": PAGE_WIDTH, "height": PAGE_HEIGHT})
        page.set_content(html, wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")

        page_elements = page.query_selector_all(".page")
        print(f"  Found {len(page_elements)} .page element(s)")

        for idx, el in enumerate(page_elements):
            page_number = idx + 1
            is_cover = page_number == 1

            # Full-page screenshot
            full_path = theme_dir / f"{page_number}.jpg"
            el.screenshot(path=str(full_path), type="jpeg", quality=JPEG_QUALITY)

            cover_path = None
            if is_cover:
                # Cover thumbnail — resize with Pillow if available, otherwise save as-is
                cover_path = OUTPUT_DIR / f"{theme_name}_cover.jpg"
                try:
                    from PIL import Image  # type: ignore
                    img = Image.open(str(full_path))
                    img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)
                    img.save(str(cover_path), "JPEG", quality=JPEG_QUALITY)
                    print(f"  Cover thumbnail → {cover_path} ({THUMB_WIDTH}x{THUMB_HEIGHT})")
                except ImportError:
                    import shutil
                    shutil.copy(str(full_path), str(cover_path))
                    print(f"  Cover thumbnail → {cover_path} (Pillow not installed, full-size copy)")

            file_size = full_path.stat().st_size
            print(f"  Page {page_number:2d} → {full_path} ({file_size:,} bytes)")

            entry: dict = {
                "page_number": page_number,
                "local_path": str(full_path),
                "r2_key_page": f"property-reports/previews/{theme_id}/{page_number}.jpg",
                "cover_path": str(cover_path) if cover_path else None,
                "r2_key_cover": f"property-reports/previews/{theme_id}.jpg" if is_cover else None,
                "url": None,
                "cover_url": None,
            }

            if do_upload:
                entry["url"] = upload_to_r2(str(full_path), entry["r2_key_page"])
                if is_cover and cover_path:
                    entry["cover_url"] = upload_to_r2(str(cover_path), entry["r2_key_cover"])

            results.append(entry)

        browser.close()

    elapsed = time.perf_counter() - t0
    print(f"  Done in {elapsed:.2f}s")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Generate and optionally upload R2 preview screenshots for all themes"
    )
    parser.add_argument(
        "--theme",
        default="all",
        help="Theme name (classic, modern, elegant, teal, bold) or 'all' (default)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload generated screenshots to Cloudflare R2",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Save locally only (default behaviour; explicit flag for clarity)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the output directory after completion",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.theme == "all":
        themes = ALL_THEMES
    elif args.theme in ALL_THEMES:
        themes = [args.theme]
    else:
        print(f"Unknown theme: {args.theme!r}")
        print(f"Valid: {', '.join(ALL_THEMES)} or 'all'")
        sys.exit(1)

    do_upload = args.upload and not args.local
    if do_upload:
        print(f"Upload mode: ON (R2 bucket: {R2_BUCKET_NAME})")
    else:
        print(f"Local mode: screenshots will be saved to {OUTPUT_DIR}")

    overall_start = time.perf_counter()
    all_results = []

    for theme in themes:
        results = screenshot_theme(theme, do_upload=do_upload)
        all_results.extend(results)

    elapsed = time.perf_counter() - overall_start

    print(f"\n{'='*60}")
    print(f"  Summary: {len(all_results)} screenshots in {elapsed:.2f}s")
    print(f"  Output directory: {OUTPUT_DIR}")
    print()
    for r in all_results:
        if r.get("cover_url"):
            print(f"  [cover] {r['cover_url']}")
        if r.get("url"):
            print(f"  [page {r['page_number']}] {r['url']}")
    print(f"{'='*60}\n")

    if args.open:
        import platform, subprocess  # noqa: E401
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", str(OUTPUT_DIR)])
            elif system == "Windows":
                os.startfile(str(OUTPUT_DIR))
            elif system == "Linux":
                subprocess.run(["xdg-open", str(OUTPUT_DIR)])
        except Exception as e:
            print(f"Could not open directory: {e}")


if __name__ == "__main__":
    main()
