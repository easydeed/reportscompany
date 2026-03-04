#!/usr/bin/env python3
"""
Generate JPG preview thumbnails for each theme.

Reads the already-generated HTML files from output/property_reports_v2/,
extracts the cover page section, and renders it to a JPG using html2image.

Output: apps/web/public/previews/1.jpg ... 5.jpg
        (These are referenced by types.ts previewImage field)

Usage:
    python scripts/generate_theme_preview_jpgs.py
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
HTML_DIR = PROJECT_ROOT / "output" / "property_reports_v2"
OUTPUT_DIR = PROJECT_ROOT / "apps" / "web" / "public" / "previews"

# Theme ID -> HTML filename mapping  (matches types.ts theme IDs)
THEME_MAP = {
    1: "classic_report.html",
    2: "modern_report.html",
    3: "elegant_report.html",
    4: "teal_report.html",
    5: "bold_report.html",
}


def extract_cover_html(full_html: str) -> str:
    """
    Extract everything up to and including the first </section> tag.
    This gives us the full <html>...<section class="page">...</section>
    but we need to close the doc properly.
    """
    # Find the first closing </section> tag
    match = re.search(r"</section>", full_html)
    if not match:
        return full_html

    end_pos = match.end()
    cover_fragment = full_html[:end_pos]

    # Close remaining open tags
    cover_html = cover_fragment + "\n  </div>\n</body>\n</html>"
    return cover_html


def main():
    print("=" * 60)
    print("Theme Preview JPG Generator")
    print("=" * 60)
    print()

    # Check input directory
    if not HTML_DIR.exists():
        print(f"[ERROR] HTML directory not found: {HTML_DIR}")
        print("        Run generate_all_property_pdfs.py first.")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INPUT]  {HTML_DIR}")
    print(f"[OUTPUT] {OUTPUT_DIR}")
    print()

    try:
        from html2image import Html2Image
    except ImportError:
        print("[ERROR] html2image not installed. Run: pip install html2image")
        sys.exit(1)

    # Initialize html2image with chrome flags for better rendering
    hti = Html2Image(
        output_path=str(OUTPUT_DIR),
        custom_flags=[
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
        ],
    )

    # Letter-size aspect ratio: 8.5 x 11 inches
    # At reasonable web resolution, let's use 510 x 660 (scaled down for thumbnails)
    img_width = 510
    img_height = 660

    results = []

    for theme_id, html_filename in THEME_MAP.items():
        html_path = HTML_DIR / html_filename
        if not html_path.exists():
            print(f"[SKIP] {html_filename} not found")
            results.append((theme_id, False))
            continue

        print(f"[THEME {theme_id}] {html_filename}")

        # Read full HTML
        full_html = html_path.read_text(encoding="utf-8")

        # Extract just the cover page
        cover_html = extract_cover_html(full_html)

        # Generate JPG
        output_filename = f"{theme_id}.jpg"
        try:
            hti.screenshot(
                html_str=cover_html,
                save_as=output_filename,
                size=(img_width, img_height),
            )
            output_path = OUTPUT_DIR / output_filename

            if output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                print(f"  [OK] {output_filename} ({size_kb:.0f} KB)")
                results.append((theme_id, True))
            else:
                # html2image sometimes saves as PNG, try converting
                png_path = OUTPUT_DIR / f"{theme_id}.png"
                if png_path.exists():
                    from PIL import Image
                    img = Image.open(png_path).convert("RGB")
                    img.save(output_path, "JPEG", quality=85)
                    png_path.unlink()
                    size_kb = output_path.stat().st_size / 1024
                    print(f"  [OK] {output_filename} (converted from PNG, {size_kb:.0f} KB)")
                    results.append((theme_id, True))
                else:
                    print(f"  [WARN] Output file not created")
                    results.append((theme_id, False))
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append((theme_id, False))

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
