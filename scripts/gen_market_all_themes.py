"""
Market Report Theme Validation Script
======================================

Generates all 5 themes × 8 report types = 40 HTML files using hardcoded
sample data (no API calls, no database needed).

Usage (from repo root):
    python scripts/gen_market_all_themes.py --html-only
    python scripts/gen_market_all_themes.py --html-only --theme bold
    python scripts/gen_market_all_themes.py --html-only --report-type market_snapshot
    python scripts/gen_market_all_themes.py --open

Output:
    output/market_themes/{theme}_{report_type}.html
    output/market_themes/index.html  (links to all 40 variants)
"""

import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# ─── Path setup ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WORKER_SRC = REPO_ROOT / "apps" / "worker" / "src"
sys.path.insert(0, str(WORKER_SRC))

OUTPUT_DIR = REPO_ROOT / "output" / "market_themes"

ALL_THEMES = ["teal", "bold", "classic", "elegant", "modern"]
ALL_REPORT_TYPES = [
    "new_listings_gallery",
    "featured_listings",
    "open_houses",
    "market_snapshot",
    "closed",
    "inventory",
    "price_bands",
    "new_listings",
]

# ─── Sample data ─────────────────────────────────────────────────────────────

SAMPLE_LISTINGS = [
    {
        "street_address": "123 Main St",
        "city": "Irvine",
        "list_price": 950000,
        "close_price": 935000,
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2200,
        "status": "Active",
        "days_on_market": 8,
        "photo_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop",
    },
    {
        "street_address": "456 Oak Ave",
        "city": "Irvine",
        "list_price": 1125000,
        "close_price": 1100000,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "sqft": 1850,
        "status": "Active",
        "days_on_market": 14,
        "photo_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop",
    },
    {
        "street_address": "789 Elm Dr",
        "city": "Irvine",
        "list_price": 780000,
        "close_price": 775000,
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1600,
        "status": "Pending",
        "days_on_market": 5,
        "photo_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=400&h=300&fit=crop",
    },
    {
        "street_address": "101 Birch Ln",
        "city": "Irvine",
        "list_price": 1350000,
        "close_price": 1320000,
        "bedrooms": 5,
        "bathrooms": 4,
        "sqft": 3100,
        "status": "Closed",
        "days_on_market": 22,
        "photo_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop",
    },
    {
        "street_address": "222 Cedar Ct",
        "city": "Irvine",
        "list_price": 620000,
        "close_price": 615000,
        "bedrooms": 2,
        "bathrooms": 2,
        "sqft": 1200,
        "status": "Active",
        "days_on_market": 3,
        "photo_url": "https://images.unsplash.com/photo-1600566753376-12c8ab7a5a0e?w=400&h=300&fit=crop",
    },
    {
        "street_address": "333 Maple Way",
        "city": "Irvine",
        "list_price": 895000,
        "close_price": 880000,
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2050,
        "status": "Active",
        "days_on_market": 11,
        "photo_url": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=400&h=300&fit=crop",
    },
]

SAMPLE_METRICS = {
    "median_list_price": 922500,
    "median_close_price": 907500,
    "avg_dom": 12,
    "months_of_inventory": 2.1,
    "price_per_sqft": 520,
    "list_to_sale_ratio": 0.982,
    "new_listings_count": 42,
}

SAMPLE_COUNTS = {"Active": 67, "Pending": 12, "Closed": 38}

SAMPLE_BRANDING = {
    "agent_name": "Jennifer Martinez",
    "agent_title": "Luxury Home Specialist",
    "agent_phone": "(949) 555-4567",
    "agent_email": "jennifer@luxuryestates.com",
    "agent_photo_url": "https://randomuser.me/api/portraits/women/44.jpg",
    "company_name": "Luxury Estates Realty",
    "logo_url": "https://placehold.co/200x60/1B365D/white?text=Luxury+Estates",
    "primary_color": "#1B365D",
    "accent_color": None,
}


def build_sample_data(report_type: str, theme_id: str) -> dict:
    """Build a complete report_data dict for the builder."""
    return {
        "report_type": report_type,
        "theme_id": theme_id,
        "accent_color": None,
        "city": "Irvine",
        "lookback_days": 30,
        "filters_label": "2+ beds, SFR, under $1.5M (First-Time Buyer)",
        "listings": SAMPLE_LISTINGS,
        "listings_sample": SAMPLE_LISTINGS,
        "metrics": SAMPLE_METRICS,
        "counts": SAMPLE_COUNTS,
        "total_listings": sum(SAMPLE_COUNTS.values()),
        "branding": SAMPLE_BRANDING,
        "ai_insights": (
            "The Irvine market showed balanced activity this period with "
            "67 active listings, 12 pending, and 38 recent closings. "
            "Median list price sits at $922,500 with homes averaging "
            "12 days on market. The 2.1 months of inventory indicates "
            "continued seller advantage, though rising inventory suggests "
            "a gradual shift toward equilibrium."
        ),
        "price_bands": [],
    }


# ─── Rendering ───────────────────────────────────────────────────────────────

def render_variant(theme: str, report_type: str, html_only: bool) -> dict:
    from worker.market_builder import MarketReportBuilder

    data = build_sample_data(report_type, theme)
    builder = MarketReportBuilder(data)

    t0 = time.perf_counter()
    html = builder.render_html()
    elapsed = time.perf_counter() - t0

    filename = f"{theme}_{report_type}"
    html_path = OUTPUT_DIR / f"{filename}.html"
    html_path.write_text(html, encoding="utf-8")

    status = "OK" if len(html) > 500 else "WARN:short"
    print(f"  {theme:8s} × {report_type:24s}  {len(html):>7,} chars  {elapsed:.2f}s  [{status}]")

    result = {"theme": theme, "report_type": report_type, "ok": status == "OK", "html_len": len(html)}

    if not html_only:
        pdfshift_key = os.getenv("PDFSHIFT_API_KEY") or os.getenv("PDF_API_KEY", "")
        if pdfshift_key:
            try:
                import httpx

                pdf_path = OUTPUT_DIR / f"{filename}.pdf"
                resp = httpx.post(
                    "https://api.pdfshift.io/v3/convert/pdf",
                    json={
                        "source": html,
                        "sandbox": False,
                        "use_print": True,
                        "format": "Letter",
                        "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
                        "delay": 2000,
                    },
                    headers={"X-API-Key": pdfshift_key, "Content-Type": "application/json"},
                    timeout=60.0,
                )
                resp.raise_for_status()
                pdf_path.write_bytes(resp.content)
                result["pdf_size"] = pdf_path.stat().st_size
            except Exception as e:
                print(f"    ⚠ PDF failed: {e}")

    return result


def generate_index(results: list):
    """Write index.html with links to all generated files."""
    rows = []
    for r in sorted(results, key=lambda x: (x["theme"], x["report_type"])):
        fname = f"{r['theme']}_{r['report_type']}.html"
        status = "✅" if r["ok"] else "⚠️"
        rows.append(f'<tr><td>{status}</td><td><a href="{fname}">{r["theme"]}</a></td>'
                     f'<td>{r["report_type"]}</td><td>{r["html_len"]:,}</td></tr>')

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Market Report Theme Index</title>
<style>
body {{ font-family: system-ui; padding: 40px; background: #f5f5f5; }}
table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
th, td {{ padding: 10px 16px; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #1B365D; color: white; }}
a {{ color: #4a90d9; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
h1 {{ margin-bottom: 20px; }}
</style></head><body>
<h1>Market Report Theme Index</h1>
<p>{len(results)} variants generated ({sum(1 for r in results if r['ok'])} OK)</p>
<table>
<thead><tr><th></th><th>Theme</th><th>Report Type</th><th>Size</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></body></html>"""

    index_path = OUTPUT_DIR / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"\n  Index: {index_path}")


def _open_file(path: str):
    try:
        if platform.system() == "Darwin":
            subprocess.run(["open", path])
        elif platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        print(f"  Could not open: {e}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate all market report theme variants")
    parser.add_argument("--html-only", action="store_true", help="Skip PDF generation")
    parser.add_argument("--open", action="store_true", help="Open output folder after generation")
    parser.add_argument("--theme", default="all", choices=ALL_THEMES + ["all"])
    parser.add_argument("--report-type", default="all", choices=ALL_REPORT_TYPES + ["all"])
    args = parser.parse_args()

    themes = ALL_THEMES if args.theme == "all" else [args.theme]
    report_types = ALL_REPORT_TYPES if args.report_type == "all" else [args.report_type]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(themes) * len(report_types)
    print(f"\n{'='*60}")
    print(f"  Market Report Theme Validation")
    print(f"  Generating {total} variants ({len(themes)} themes × {len(report_types)} types)")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    t_all = time.perf_counter()
    results = []
    for theme in themes:
        for rt in report_types:
            try:
                r = render_variant(theme, rt, html_only=args.html_only)
                results.append(r)
            except Exception as e:
                print(f"  {theme:8s} × {rt:24s}  ❌ ERROR: {e}")
                results.append({"theme": theme, "report_type": rt, "ok": False, "html_len": 0})

    total_time = time.perf_counter() - t_all
    generate_index(results)

    ok_count = sum(1 for r in results if r["ok"])
    fail_count = total - ok_count

    print(f"\n{'='*60}")
    print(f"  Done in {total_time:.1f}s — {ok_count}/{total} OK", end="")
    if fail_count:
        print(f", {fail_count} FAILED")
    else:
        print(" [ALL PASS]")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    if args.open:
        _open_file(str(OUTPUT_DIR / "index.html"))


if __name__ == "__main__":
    main()
