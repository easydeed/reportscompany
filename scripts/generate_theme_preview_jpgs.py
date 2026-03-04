#!/usr/bin/env python3
"""
Generate JPG preview thumbnails for each theme.

Reads the already-generated HTML files from output/la_verne_themes/,
extracts the cover page section, and renders it to a JPG using Playwright.

Output: apps/web/public/previews/1.jpg ... 5.jpg
        (These are referenced by types.ts previewImage field)

Usage:
    python scripts/generate_theme_preview_jpgs.py
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Try la_verne_themes first (latest gen script output), fall back to others
HTML_CANDIDATES = [
    PROJECT_ROOT / "output" / "la_verne_themes",
    PROJECT_ROOT / "output" / "property_reports_v2",
    PROJECT_ROOT / "output" / "property_reports",
]
OUTPUT_DIR = PROJECT_ROOT / "apps" / "web" / "public" / "previews"

# Theme ID -> HTML filename mapping  (matches types.ts theme IDs)
THEME_MAP = {
    1: "classic_report.html",
    2: "modern_report.html",
    3: "elegant_report.html",
    4: "teal_report.html",
    5: "bold_report.html",
}


def find_html_dir() -> Path:
    """Find the first existing HTML output directory."""
    for d in HTML_CANDIDATES:
        if d.exists() and any(d.glob("*_report.html")):
            return d
    return HTML_CANDIDATES[0]  # Return first as default (will error later)


def extract_cover_html(full_html: str) -> str:
    """
    Extract everything up to and including the first </section> tag.
    This gives us the cover page as a standalone HTML document.
    """
    match = re.search(r"</section>", full_html)
    if not match:
        return full_html

    end_pos = match.end()
    cover_fragment = full_html[:end_pos]

    # Close remaining open tags
    cover_html = cover_fragment + "\n  </div>\n</body>\n</html>"
    return cover_html


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("Theme Preview JPG Generator (Playwright)")
    print("=" * 60)
    print()

    HTML_DIR = find_html_dir()

    if not HTML_DIR.exists():
        print(f"[ERROR] HTML directory not found: {HTML_DIR}")
        print("        Run gen_la_verne_all_themes.py first.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INPUT]  {HTML_DIR}")
    print(f"[OUTPUT] {OUTPUT_DIR}")
    print()

    # Try Playwright first (preferred — same renderer as PDF generation)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[ERROR] Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    # Letter-size aspect ratio: 8.5 x 11 -> 510 x 660 for thumbnails
    img_width = 510
    img_height = 660

    results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for theme_id, html_filename in THEME_MAP.items():
            html_path = HTML_DIR / html_filename
            if not html_path.exists():
                print(f"[SKIP] {html_filename} not found")
                results.append((theme_id, False))
                continue

            print(f"[THEME {theme_id}] {html_filename}")

            try:
                # Read full HTML
                full_html = html_path.read_text(encoding="utf-8")

                # Extract just the cover page
                cover_html = extract_cover_html(full_html)

                # Create a new page with the cover dimensions
                page = browser.new_page(
                    viewport={"width": img_width, "height": img_height}
                )
                page.set_content(cover_html, wait_until="networkidle")

                # Wait for fonts to load
                try:
                    page.evaluate("() => document.fonts.ready")
                except Exception:
                    pass

                # Take screenshot as PNG first (Playwright native), then convert to JPG
                png_path = OUTPUT_DIR / f"{theme_id}.png"
                jpg_path = OUTPUT_DIR / f"{theme_id}.jpg"

                page.screenshot(
                    path=str(png_path),
                    full_page=False,
                    clip={"x": 0, "y": 0, "width": img_width, "height": img_height},
                )
                page.close()

                # Convert PNG to JPG for smaller file size
                try:
                    from PIL import Image
                    img = Image.open(png_path).convert("RGB")
                    img.save(str(jpg_path), "JPEG", quality=88)
                    png_path.unlink()  # Remove PNG
                    size_kb = jpg_path.stat().st_size / 1024
                    print(f"  [OK] {theme_id}.jpg ({size_kb:.0f} KB)")
                    results.append((theme_id, True))
                except ImportError:
                    # No Pillow — just keep the PNG and rename
                    if png_path.exists():
                        # Can't convert without Pillow, keep as PNG
                        # But rename to .jpg (browsers handle this fine)
                        if jpg_path.exists():
                            jpg_path.unlink()
                        png_path.rename(jpg_path)
                        size_kb = jpg_path.stat().st_size / 1024
                        print(f"  [OK] {theme_id}.jpg ({size_kb:.0f} KB, PNG format)")
                        results.append((theme_id, True))

            except Exception as e:
                print(f"  [ERROR] {e}")
                results.append((theme_id, False))

        browser.close()

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    ok = sum(1 for _, s in results if s)
    print(f"\n  Generated: {ok}/{len(THEME_MAP)}")
    print(f"  Output:    {OUTPUT_DIR}")
    print()

    if ok > 0:
        print("  These previews are used by the wizard theme gallery.")
        print("  Referenced in types.ts as /previews/[theme_id].jpg")
        print()


if __name__ == "__main__":
    main()
