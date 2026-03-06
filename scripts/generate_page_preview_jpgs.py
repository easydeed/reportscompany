#!/usr/bin/env python3
"""
Generate JPG preview thumbnails for every page of every theme.

Reads the already-generated HTML files from output/la_verne_themes/,
locates each <section class="page ..."> element, and screenshots it
to a JPG using Playwright.

Output: apps/web/public/previews/pages/{theme_id}/{page_key}.jpg

Prerequisites:
    - Run gen_la_verne_all_themes.py --html-only first to produce the HTML files
    - pip install playwright && playwright install chromium
    - pip install Pillow   (for PNG→JPG conversion)

Usage:
    python scripts/generate_page_preview_jpgs.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

HTML_CANDIDATES = [
    PROJECT_ROOT / "output" / "la_verne_themes",
    PROJECT_ROOT / "output" / "property_reports_v2",
    PROJECT_ROOT / "output" / "property_reports",
]
OUTPUT_BASE = PROJECT_ROOT / "apps" / "web" / "public" / "previews" / "pages"

THEME_MAP = {
    1: "classic_report.html",
    2: "modern_report.html",
    3: "elegant_report.html",
    4: "teal_report.html",
    5: "bold_report.html",
}

PAGE_KEYS = [
    "cover",
    "overview",
    "contents",
    "aerial",
    "property",
    "analysis",
    "market_trends",
    "comparables",
    "range",
]

IMG_WIDTH = 510
IMG_HEIGHT = 660


def find_html_dir() -> Path:
    for d in HTML_CANDIDATES:
        if d.exists() and any(d.glob("*_report.html")):
            return d
    return HTML_CANDIDATES[0]


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("Page Preview JPG Generator (Playwright)")
    print("=" * 60)
    print()

    html_dir = find_html_dir()
    if not html_dir.exists():
        print(f"[ERROR] HTML directory not found: {html_dir}")
        print("        Run gen_la_verne_all_themes.py --html-only first.")
        sys.exit(1)

    print(f"[INPUT]  {html_dir}")
    print(f"[OUTPUT] {OUTPUT_BASE}")
    print()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[ERROR] Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    try:
        from PIL import Image
        has_pillow = True
    except ImportError:
        has_pillow = False
        print("[WARN] Pillow not installed — PNGs will be renamed to .jpg")

    total_ok = 0
    total_fail = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for theme_id, html_filename in THEME_MAP.items():
            html_path = html_dir / html_filename
            if not html_path.exists():
                print(f"[SKIP] {html_filename} not found")
                continue

            print(f"\n--- Theme {theme_id}: {html_filename} ---")

            output_dir = OUTPUT_BASE / str(theme_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            full_html = html_path.read_text(encoding="utf-8")

            page = browser.new_page(
                viewport={"width": IMG_WIDTH, "height": IMG_HEIGHT}
            )
            page.set_content(full_html, wait_until="networkidle")

            try:
                page.evaluate("() => document.fonts.ready")
            except Exception:
                pass

            page.wait_for_timeout(1000)

            sections = page.query_selector_all("section.page")
            print(f"  Found {len(sections)} page sections")

            for idx, section in enumerate(sections):
                if idx >= len(PAGE_KEYS):
                    print(f"  [SKIP] Extra section {idx} (no page key)")
                    break

                page_key = PAGE_KEYS[idx]
                png_path = output_dir / f"{page_key}.png"
                jpg_path = output_dir / f"{page_key}.jpg"

                try:
                    section.screenshot(path=str(png_path))

                    if has_pillow:
                        img = Image.open(png_path).convert("RGB")
                        img = img.resize((IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)
                        img.save(str(jpg_path), "JPEG", quality=88)
                        png_path.unlink()
                    else:
                        if jpg_path.exists():
                            jpg_path.unlink()
                        png_path.rename(jpg_path)

                    size_kb = jpg_path.stat().st_size / 1024
                    print(f"  [OK] {page_key}.jpg ({size_kb:.0f} KB)")
                    total_ok += 1
                except Exception as e:
                    print(f"  [FAIL] {page_key}: {e}")
                    total_fail += 1

            if len(sections) < len(PAGE_KEYS):
                for missing_idx in range(len(sections), len(PAGE_KEYS)):
                    print(f"  [MISS] {PAGE_KEYS[missing_idx]} — section not found in HTML")
                    total_fail += 1

            page.close()

        browser.close()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Generated: {total_ok}")
    print(f"  Failed:    {total_fail}")
    print(f"  Output:    {OUTPUT_BASE}")
    print()

    if total_ok > 0:
        print("  These previews are used by the wizard page selector.")
        print("  Referenced as /previews/pages/{themeId}/{pageKey}.jpg")
        print()


if __name__ == "__main__":
    main()
