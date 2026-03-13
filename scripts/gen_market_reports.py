"""
Market Report Generation Script
================================

Generates all 8 report types as HTML (and optionally PDFs)
using hardcoded sample data (no API calls, no database needed).

Usage (from repo root):
    python scripts/gen_market_reports.py                              # HTML + PDF via Playwright
    python scripts/gen_market_reports.py --html-only                  # HTML only
    python scripts/gen_market_reports.py --report-type market_snapshot # One type only
    python scripts/gen_market_reports.py --pdf-engine pdfshift        # Use PDFShift cloud API

Output:
    output/market_reports/{report_type}.html
    output/market_reports/{report_type}.pdf   (when not --html-only)
    output/market_reports/index.html          (links to all variants)
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

OUTPUT_DIR = REPO_ROOT / "output" / "market_reports"

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
    "accent_color": "#0d9488",
}


def build_sample_data(report_type: str) -> dict:
    """Build a complete report_data dict for the builder."""
    return {
        "report_type": report_type,
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


# ─── PDF engines ─────────────────────────────────────────────────────────────

_playwright_browser = None


def _get_playwright_browser():
    """Reuse a single Chromium instance across all variants for speed."""
    global _playwright_browser
    if _playwright_browser is None:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        _playwright_browser = pw.chromium.launch(headless=True)
    return _playwright_browser


def _pdf_via_playwright(html: str, pdf_path: Path) -> int:
    browser = _get_playwright_browser()
    page = browser.new_page()
    page.set_content(html, wait_until="networkidle")
    page.pdf(
        path=str(pdf_path),
        format="Letter",
        print_background=True,
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
    )
    page.close()
    return pdf_path.stat().st_size


def _pdf_via_pdfshift(html: str, pdf_path: Path) -> int:
    import httpx

    api_key = os.getenv("PDFSHIFT_API_KEY") or os.getenv("PDF_API_KEY", "")
    if not api_key:
        raise RuntimeError("PDFSHIFT_API_KEY not set")
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
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        timeout=60.0,
    )
    resp.raise_for_status()
    pdf_path.write_bytes(resp.content)
    return pdf_path.stat().st_size


# ─── Rendering ───────────────────────────────────────────────────────────────

def render_variant(report_type: str, html_only: bool, pdf_engine: str = "playwright") -> dict:
    from worker.market_builder import MarketReportBuilder

    data = build_sample_data(report_type)
    builder = MarketReportBuilder(data)

    t0 = time.perf_counter()
    html = builder.render_html()
    elapsed = time.perf_counter() - t0

    html_path = OUTPUT_DIR / f"{report_type}.html"
    html_path.write_text(html, encoding="utf-8")

    status = "OK" if len(html) > 500 else "WARN:short"

    result = {"report_type": report_type, "ok": status == "OK", "html_len": len(html)}

    if not html_only:
        pdf_path = OUTPUT_DIR / f"{report_type}.pdf"
        try:
            if pdf_engine == "pdfshift":
                size = _pdf_via_pdfshift(html, pdf_path)
            else:
                size = _pdf_via_playwright(html, pdf_path)
            result["pdf_size"] = size
            size_kb = size / 1024
            print(f"  {report_type:28s}  {len(html):>7,} chars  {size_kb:>6.0f} KB pdf  {elapsed:.2f}s  [{status}]")
        except Exception as e:
            print(f"  {report_type:28s}  {len(html):>7,} chars  PDF FAIL  {elapsed:.2f}s  [{status}]")
            print(f"    ⚠ {type(e).__name__}: {e}")
    else:
        print(f"  {report_type:28s}  {len(html):>7,} chars  {elapsed:.2f}s  [{status}]")

    return result


def generate_index(results: list):
    """Write index.html with links to all generated files."""
    has_pdfs = any(r.get("pdf_size") for r in results)
    rows = []
    for r in sorted(results, key=lambda x: x["report_type"]):
        fname = r["report_type"]
        status = "✅" if r["ok"] else "⚠️"
        pdf_cell = ""
        if has_pdfs:
            if r.get("pdf_size"):
                kb = r["pdf_size"] / 1024
                pdf_cell = f'<td><a href="{fname}.pdf">PDF ({kb:.0f} KB)</a></td>'
            else:
                pdf_cell = "<td>—</td>"
        rows.append(
            f'<tr><td>{status}</td><td><a href="{fname}.html">{r["report_type"]}</a></td>'
            f'<td>{r["html_len"]:,}</td>{pdf_cell}</tr>'
        )

    pdf_header = "<th>PDF</th>" if has_pdfs else ""
    subtitle = f"{len(results)} reports generated ({sum(1 for r in results if r['ok'])} OK)"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Market Report Index</title>
<style>
body {{ font-family: system-ui; padding: 40px; background: #f5f5f5; }}
table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
th, td {{ padding: 10px 16px; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #1B365D; color: white; }}
a {{ color: #4a90d9; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
h1 {{ margin-bottom: 20px; }}
</style></head><body>
<h1>Market Report Index</h1>
<p>{subtitle}</p>
<table>
<thead><tr><th></th><th>Report Type</th><th>HTML</th>{pdf_header}</tr></thead>
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
    parser = argparse.ArgumentParser(description="Generate market report HTML/PDF variants")
    parser.add_argument("--html-only", action="store_true", help="Skip PDF generation (HTML only)")
    parser.add_argument("--pdf-engine", default="playwright", choices=["playwright", "pdfshift"],
                        help="PDF engine: playwright (local, free) or pdfshift (cloud API key)")
    parser.add_argument("--no-open", action="store_true", help="Skip opening output in browser")
    parser.add_argument("--report-type", default="all", choices=ALL_REPORT_TYPES + ["all"])
    args = parser.parse_args()

    report_types = ALL_REPORT_TYPES if args.report_type == "all" else [args.report_type]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mode = "HTML only" if args.html_only else f"HTML + PDF ({args.pdf_engine})"
    print(f"\n{'='*60}")
    print(f"  Market Report Generator")
    print(f"  {len(report_types)} report types")
    print(f"  Mode: {mode}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    t_all = time.perf_counter()
    results = []
    for rt in report_types:
        try:
            r = render_variant(rt, html_only=args.html_only, pdf_engine=args.pdf_engine)
            results.append(r)
        except Exception as e:
            print(f"  {rt:28s}  ERROR: {e}")
            results.append({"report_type": rt, "ok": False, "html_len": 0})

    global _playwright_browser
    if _playwright_browser is not None:
        _playwright_browser.close()
        _playwright_browser = None

    total_time = time.perf_counter() - t_all
    generate_index(results)

    ok_count = sum(1 for r in results if r["ok"])
    total = len(report_types)
    fail_count = total - ok_count

    print(f"\n{'='*60}")
    print(f"  Done in {total_time:.1f}s — {ok_count}/{total} OK", end="")
    if fail_count:
        print(f", {fail_count} FAILED")
    else:
        print(" [ALL PASS]")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    if not args.no_open:
        print("  Opening index in browser...")
        _open_file(str(OUTPUT_DIR / "index.html"))


if __name__ == "__main__":
    main()
