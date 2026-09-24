#!/usr/bin/env python3
"""Measure how a market report PDF actually paginates.

WHY A SCRIPT AND NOT A TEST. This needs a real browser and a real paginator.
CI installs Poetry and nothing else, so there is no Chromium there and this
cannot be a gate. What it produces instead is a recorded measurement with its
method attached, which is the honest shape for a number that cannot be checked
on every push. The things that CAN be gated without a browser live in
`apps/worker/tests/test_market_layout_map.py`.

WHAT IT REPRODUCES. tasks.py is the only market-report render path:
MarketReportBuilder -> render_html + render_page_header_html +
render_page_footer_html -> render_pdf(html_content=...). The /print/{runId}
route is never reached for a market-report PDF. Production renders through
PDFShift, which reserves space for the repeating header and footer rather than
flowing them with the body:

    margin.top    0  +  header.height  0.44in  =  0.44in reserved
    margin.bottom 0  +  footer.height  0.89in  =  0.89in reserved

The body therefore flows in 11in - 1.33in = 9.67in on every page, and that is what
this script reproduces with Chromium's own paginator: same format, same margins,
header and footer left out because their space is what matters here, not their
paint. Corroboration that the emulation is faithful: a production `closed.pdf`
reviewed for the master plan carries 13 rows on page 1 and 25 on page 2, and
this harness produces 13 then 25 from the same build.

PAGE 1 IS NOT A FIXED CAPACITY. Measured: shortening the AI narrative by one
sentence (~48 characters) moves `closed` from 13 rows on page 1 to 14, and
`new_listings` from 3 to 4. Continuation pages are unaffected at a stable 25
and 7. The narrative is model-generated prose of no fixed length, so page 1's
row count is a property of the copy and not only of the layout — which is worth
knowing before any pagination target is set against a single observed number.
The fixture below uses the longer narrative, the one that reproduces the
reviewed production render.

    python3 scripts/measure_market_pagination.py [N_LISTINGS]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "worker" / "src"))

STREETS = ["Main St", "Oak Ave", "Elm Dr", "Birch Ln", "Cedar Ct", "Maple Way",
           "Pine Rd", "Walnut Blvd", "Juniper Pl", "Sycamore Ter"]
ADDR = re.compile(r"\b\d{3,5} (?:" + "|".join(STREETS) + r")\b")

# PDFShift's reservations, from pdf_engine.render_pdf_pdfshift. Since §7.1
# variant A both `margin` spacers are 0 and each reservation equals the measured
# height of its own document, so these are just the two `height` values.
MARGIN_TOP = "0.44in"
MARGIN_BOTTOM = "0.89in"

PDF_JS = """
const { chromium } = require('playwright');
const fs = require('fs');
const [dir, exe, marginTop, marginBottom] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch(exe ? { executablePath: exe } : {});
  const page = await browser.newPage();
  for (const t of JSON.parse(fs.readFileSync(`${dir}/types.json`, 'utf8'))) {
    await page.setContent(fs.readFileSync(`${dir}/${t}.html`, 'utf8'), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({ path: `${dir}/${t}.pdf`, format: 'Letter', printBackground: true,
                     margin: { top: marginTop, right: '0', bottom: marginBottom, left: '0' } });
  }
  await browser.close();
})();
"""


def find_chromium():
    """Playwright's bundled browser, when the pinned build is not the installed one."""
    root = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    for candidate in sorted(root.glob("chromium-*/chrome-linux/chrome"), reverse=True):
        return str(candidate)
    return ""


def listings(n):
    return [
        {
            "street_address": f"{100 + i * 7} {STREETS[i % len(STREETS)]}",
            "city": "Irvine",
            "list_price": 650000 + (i * 13500) % 900000,
            "close_price": 640000 + (i * 12900) % 880000,
            "bedrooms": 2 + (i % 4), "bathrooms": 1.5 + (i % 3),
            "sqft": 1200 + (i * 37) % 2400,
            "status": ["Active", "Pending", "Closed"][i % 3],
            "days_on_market": 3 + (i * 5) % 90,
            "photo_url": None,
            "next_open_house": "Sat 1-4pm" if i % 3 == 0 else None,
        }
        for i in range(n)
    ]


def report_data(report_type, n):
    return {
        "report_type": report_type, "city": "Irvine", "lookback_days": 30,
        "filters_label": "2+ beds, SFR, under $1.5M",
        "listings": listings(n),
        "metrics": {"median_list_price": 922500, "median_close_price": 907500,
                    "avg_dom": 12, "months_of_inventory": 2.1, "price_per_sqft": 520,
                    "list_to_sale_ratio": 0.982, "new_listings_count": 42},
        "counts": {"Active": 67, "Pending": 12, "Closed": 38},
        "total_listings": n,
        "branding": {"agent_name": "Jennifer Martinez",
                     "agent_title": "Luxury Home Specialist",
                     "primary_color": "#1B365D", "accent_color": None},
        # Length matters — see the module docstring. This is the longer of the
        # two measured narratives, and the one that reproduces production's 13.
        "ai_insights": ("The Irvine market showed balanced activity this period, "
                        "with inventory holding near two months of supply."),
        "price_bands": [{"label": "$600-800K", "count": 18, "pct": 22},
                        {"label": "$800K-1M", "count": 31, "pct": 38}],
    }


def main(n=120):
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("pypdf is required: pip install pypdf")
    if shutil.which("node") is None:
        sys.exit("node is required (this script drives Playwright through it)")

    from worker.market_builder import ALL_REPORT_TYPES, MarketReportBuilder

    work = Path(tempfile.mkdtemp(prefix="market-pagination-"))
    (work / "types.json").write_text(json.dumps(ALL_REPORT_TYPES))
    layouts = {}
    for report_type in ALL_REPORT_TYPES:
        builder = MarketReportBuilder(report_data(report_type, n))
        (work / f"{report_type}.html").write_text(builder.render_html())
        layouts[report_type] = builder.layout

    # node resolves `playwright` from the repo's node_modules, so run from there.
    js = REPO / "_measure_market_pagination.js"
    js.write_text(PDF_JS)
    try:
        subprocess.run(
            ["node", str(js), str(work), find_chromium(), MARGIN_TOP, MARGIN_BOTTOM],
            cwd=str(REPO), check=True,
        )
    finally:
        js.unlink(missing_ok=True)

    print(f"{n} listings · Letter · top {MARGIN_TOP} / bottom {MARGIN_BOTTOM} reserved\n")
    print(f"{'report type':24s} {'layout':18s} {'pages':>5s}  listings per page")
    print("-" * 82)
    out = []
    for report_type in ALL_REPORT_TYPES:
        reader = PdfReader(str(work / f"{report_type}.pdf"))
        per_page = [len(set(ADDR.findall(p.extract_text() or ""))) for p in reader.pages]
        out.append({"report_type": report_type, "layout": layouts[report_type],
                    "pages": len(reader.pages), "per_page": per_page})
        print(f"{report_type:24s} {layouts[report_type]:18s} "
              f"{len(reader.pages):5d}  {per_page}")
    print(f"\nPDFs left in {work}")
    return out


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 120)
