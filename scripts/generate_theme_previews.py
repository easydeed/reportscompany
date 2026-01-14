#!/usr/bin/env python3
"""
Generate Theme Preview Images for Property Reports

This script:
1. Renders each theme's HTML template
2. Takes screenshots of each page using Playwright
3. Uploads images to Cloudflare R2

Output structure on R2:
  /property-reports/previews/1.jpg      - Theme 1 cover thumbnail
  /property-reports/previews/1/1.jpg    - Theme 1, Page 1 (Cover)
  /property-reports/previews/1/2.jpg    - Theme 1, Page 2 (Contents)
  ... etc for all 5 themes x 7 pages

Usage:
  # Generate all themes
  python scripts/generate_theme_previews.py
  
  # Generate specific theme
  python scripts/generate_theme_previews.py --theme 3
  
  # Generate without uploading (local only)
  python scripts/generate_theme_previews.py --local-only

Requirements:
  pip install playwright boto3
  playwright install chromium
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path

# Add worker to path for PropertyReportBuilder
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
WORKER_SRC = PROJECT_ROOT / "apps" / "worker" / "src"
sys.path.insert(0, str(WORKER_SRC))

from worker.property_builder import PropertyReportBuilder

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output" / "theme_previews"

# R2 Configuration
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_PREFIX = "property-reports/previews"

# Theme configurations
THEMES = {
    1: {"name": "classic", "display": "Classic"},
    2: {"name": "modern", "display": "Modern"},
    3: {"name": "elegant", "display": "Elegant"},
    4: {"name": "teal", "display": "Teal"},
    5: {"name": "bold", "display": "Bold"},
}

# Page structure (7 pages per theme)
PAGES = [
    {"id": "cover", "name": "Cover", "number": 1},
    {"id": "contents", "name": "Table of Contents", "number": 2},
    {"id": "aerial", "name": "Aerial View", "number": 3},
    {"id": "property", "name": "Property Details", "number": 4},
    {"id": "analysis", "name": "Area Sales Analysis", "number": 5},
    {"id": "comparables", "name": "Sales Comparables", "number": 6},
    {"id": "range", "name": "Range of Sales", "number": 7},
]

# Sample data for preview generation
SAMPLE_DATA = {
    "report_type": "seller",
    "property_address": "123 Oak Street",
    "property_city": "Beverly Hills",
    "property_state": "CA",
    "property_zip": "90210",
    "property_county": "Los Angeles",
    "apn": "4352-012-001",
    "owner_name": "John & Jane Smith",
    "sitex_data": {
        "latitude": 34.0736,
        "longitude": -118.4004,
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2850,
        "lot_size": "8,500 sqft",
        "year_built": 1985,
        "assessed_value": 1250000,
        "tax_amount": 15625,
        "property_type": "Single Family",
        "garage": "2-Car Attached",
        "pool": True,
    },
    "comparables": [
        {
            "address": "456 Maple Drive",
            "city": "Beverly Hills",
            "price": 1350000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2650,
            "year_built": 1990,
            "distance_miles": 0.3,
            "days_on_market": 28,
            "photo_url": "https://placehold.co/400x300/1e3a5f/white?text=Property+1",
        },
        {
            "address": "789 Palm Avenue",
            "city": "Beverly Hills", 
            "price": 1425000,
            "bedrooms": 5,
            "bathrooms": 3,
            "sqft": 3100,
            "year_built": 1988,
            "distance_miles": 0.5,
            "days_on_market": 14,
            "photo_url": "https://placehold.co/400x300/1e3a5f/white?text=Property+2",
        },
        {
            "address": "321 Sunset Blvd",
            "city": "Beverly Hills",
            "price": 1275000,
            "bedrooms": 4,
            "bathrooms": 2,
            "sqft": 2400,
            "year_built": 1992,
            "distance_miles": 0.4,
            "days_on_market": 42,
            "photo_url": "https://placehold.co/400x300/1e3a5f/white?text=Property+3",
        },
        {
            "address": "555 Rodeo Lane",
            "city": "Beverly Hills",
            "price": 1550000,
            "bedrooms": 5,
            "bathrooms": 4,
            "sqft": 3400,
            "year_built": 1980,
            "distance_miles": 0.6,
            "days_on_market": 7,
            "photo_url": "https://placehold.co/400x300/1e3a5f/white?text=Property+4",
        },
    ],
    "agent": {
        "name": "Sarah Johnson",
        "title": "Luxury Home Specialist",
        "phone": "(310) 555-1234",
        "email": "sarah@luxuryhomes.com",
        "company_name": "Premier Real Estate",
        "license_number": "01234567",
        "photo_url": "https://placehold.co/150x150/1e3a5f/white?text=Agent",
        "logo_url": "https://placehold.co/200x60/1e3a5f/white?text=Logo",
    },
    "selected_pages": ["cover", "contents", "aerial", "property", "analysis", "comparables", "range"],
}


def render_theme_html(theme_id: int) -> str:
    """Render HTML for a theme using PropertyReportBuilder."""
    data = {**SAMPLE_DATA, "theme": theme_id}
    builder = PropertyReportBuilder(data)
    return builder.render_html()


def screenshot_pages(html: str, theme_id: int, output_dir: Path) -> list:
    """
    Take screenshots of each page in the HTML using Playwright.
    
    Returns list of (page_number, file_path) tuples.
    """
    from playwright.sync_api import sync_playwright
    
    screenshots = []
    theme_dir = output_dir / str(theme_id)
    theme_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Letter size at 96 DPI
        page = browser.new_page(viewport={"width": 816, "height": 1056})
        
        # Load HTML
        page.set_content(html, wait_until="networkidle")
        
        # Wait for fonts and images
        page.wait_for_timeout(2000)
        
        # Find all page sections - templates use <section class="page">
        sheets = page.query_selector_all("section.page")
        
        if not sheets:
            print(f"    [WARN] No section.page elements found, trying .sheet")
            sheets = page.query_selector_all(".sheet")
        
        if not sheets:
            print(f"    [WARN] No pages found!")
            browser.close()
            return screenshots
        
        print(f"    Found {len(sheets)} pages")
        
        for i, sheet in enumerate(sheets):
            page_num = i + 1
            if page_num > 7:  # Only first 7 pages
                break
                
            # Screenshot this page
            file_path = theme_dir / f"{page_num}.jpg"
            
            # Scroll to element and screenshot
            sheet.scroll_into_view_if_needed()
            page.wait_for_timeout(500)  # More time for rendering
            
            # Take screenshot of just this element
            try:
                sheet.screenshot(path=str(file_path), type="jpeg", quality=85)
                screenshots.append((page_num, file_path))
                print(f"    [OK] Page {page_num}: {file_path.name}")
            except Exception as e:
                print(f"    [ERROR] Page {page_num}: {e}")
        
        # Also create a cover thumbnail (first page, smaller)
        if sheets:
            cover_path = output_dir / f"{theme_id}.jpg"
            sheets[0].scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            
            try:
                # Take full screenshot and it will be used as cover
                sheets[0].screenshot(path=str(cover_path), type="jpeg", quality=80)
                screenshots.append(("cover", cover_path))
                print(f"    [OK] Cover thumbnail: {cover_path.name}")
            except Exception as e:
                print(f"    [ERROR] Cover: {e}")
        
        browser.close()
    
    return screenshots


def upload_to_r2(local_path: Path, r2_key: str) -> bool:
    """Upload a file to Cloudflare R2."""
    import boto3
    from botocore.config import Config
    
    # R2 credentials from environment
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    
    if not all([account_id, access_key, secret_key]):
        print("    [SKIP] R2 credentials not configured")
        return False
    
    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
    )
    
    try:
        s3.upload_file(
            str(local_path),
            R2_BUCKET,
            r2_key,
            ExtraArgs={
                "ContentType": "image/jpeg",
                "CacheControl": "public, max-age=31536000",  # 1 year cache
            }
        )
        return True
    except Exception as e:
        print(f"    [ERROR] Upload failed: {e}")
        return False


def process_theme(theme_id: int, upload: bool = True) -> dict:
    """Process a single theme: render, screenshot, upload."""
    theme_info = THEMES[theme_id]
    print(f"\n[THEME {theme_id}] {theme_info['display']}")
    print("-" * 40)
    
    result = {"theme": theme_id, "screenshots": [], "uploads": []}
    
    # Render HTML
    print("  Rendering HTML...")
    try:
        html = render_theme_html(theme_id)
        print(f"    [OK] HTML rendered ({len(html):,} bytes)")
    except Exception as e:
        print(f"    [ERROR] Failed to render: {e}")
        return result
    
    # Save HTML for debugging
    html_path = OUTPUT_DIR / f"{theme_info['name']}_preview.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    
    # Take screenshots
    print("  Taking screenshots...")
    try:
        screenshots = screenshot_pages(html, theme_id, OUTPUT_DIR)
        result["screenshots"] = screenshots
    except Exception as e:
        print(f"    [ERROR] Screenshot failed: {e}")
        import traceback
        traceback.print_exc()
        return result
    
    # Upload to R2
    if upload:
        print("  Uploading to R2...")
        for page_num, file_path in screenshots:
            if page_num == "cover":
                r2_key = f"{R2_PREFIX}/{theme_id}.jpg"
            else:
                r2_key = f"{R2_PREFIX}/{theme_id}/{page_num}.jpg"
            
            if upload_to_r2(file_path, r2_key):
                result["uploads"].append(r2_key)
                print(f"    [OK] Uploaded: {r2_key}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Generate theme preview images")
    parser.add_argument("--theme", type=int, choices=[1, 2, 3, 4, 5],
                        help="Generate for specific theme only")
    parser.add_argument("--local-only", action="store_true",
                        help="Skip R2 upload, generate locally only")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Property Report Theme Preview Generator")
    print("=" * 60)
    
    # Check for Playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n[ERROR] Playwright not installed. Run:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[OUTPUT] {OUTPUT_DIR}")
    
    # Check R2 credentials
    has_r2 = all([
        os.getenv("R2_ACCOUNT_ID"),
        os.getenv("R2_ACCESS_KEY_ID"),
        os.getenv("R2_SECRET_ACCESS_KEY"),
    ])
    
    upload = has_r2 and not args.local_only
    if upload:
        print("[R2] Credentials found - will upload to R2")
    else:
        print("[R2] Skipping upload (local only mode)")
    
    # Process themes
    themes_to_process = [args.theme] if args.theme else list(THEMES.keys())
    results = []
    
    for theme_id in themes_to_process:
        result = process_theme(theme_id, upload=upload)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total_screenshots = sum(len(r["screenshots"]) for r in results)
    total_uploads = sum(len(r["uploads"]) for r in results)
    
    print(f"\nThemes processed: {len(results)}")
    print(f"Screenshots taken: {total_screenshots}")
    print(f"Files uploaded: {total_uploads}")
    print(f"\nLocal files: {OUTPUT_DIR}")
    
    if upload and total_uploads > 0:
        print(f"\nR2 URLs:")
        print(f"  https://assets.trendyreports.com/{R2_PREFIX}/[theme_id].jpg")
        print(f"  https://assets.trendyreports.com/{R2_PREFIX}/[theme_id]/[page].jpg")


if __name__ == "__main__":
    main()

