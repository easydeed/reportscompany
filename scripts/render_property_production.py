"""Render the property report through the PRODUCTION path, all five themes.

Production path is property_tasks/property_report.py:
    fetch_report_with_joins(id) -> PropertyReportBuilder(report_data)
      -> fetch_comparables() -> render_html() -> embed_images_as_base64()

This script supplies a report_data dict shaped EXACTLY as
fetch_report_with_joins() returns it, then calls the real builder. It does not
reimplement a single filter or context key — that is what
scripts/generate_all_property_pdfs.py does, and that is why the six reviewed
PDFs were not production renders.

Two variants, because production has two materially different states:
  full  — Google Maps key present, market_trends + overview pre-injected,
          agent photo set, all pages selected
  bare  — no keys, default 7-page set, no agent photo (the common case)

    python3 scripts/render_property_production.py OUT_DIR [bare|full]

Writes property__<theme>__<variant>.html for all five themes plus
context__<variant>.json, the built context, because several E tickets are
about values rather than layout.
"""
import json, os, sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

VARIANT = sys.argv[2] if len(sys.argv) > 2 else "bare"
if VARIANT == "full":
    os.environ["GOOGLE_MAPS_API_KEY"] = "AIzaFAKEKEYFORRENDERONLY"

from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES  # noqa: E402
sys.path.insert(0, str(REPO / "apps/api/src"))
from api.services.sitex import PropertyData  # noqa: E402

# ── report_data, shaped as fetch_report_with_joins() returns it ─────────────
# ONLY KEYS A PRODUCER ACTUALLY WRITES — checked against
# `api.services.sitex.PropertyData.model_fields` and the wizard's payload at
# `step-generate.tsx`, and asserted below so it cannot drift.
#
# The earlier version of this fixture invented `zoning`, `pool`, `garage`,
# `fireplace`, `census_tract`, `total_rooms`, `use_code`, `tax_status`,
# `percent_improved`, `secondary_owner` and `mailing_address`. SiteX returns
# none of them (D-135). So this script — the reproduction tool for the whole
# Workstream E measurement — had been rendering a property page nobody can
# receive, and the D-137 fix looked unapplied in its output because the
# fixture was still feeding it `pool: "None"` and `tax_status: "Current"`.
#
# §0.6: a fixture shaped like production is not one production can produce.
# That rule was written from this script's output and then not applied to
# this script.
SITEX = {
    "latitude": 34.1008, "longitude": -117.7678,
    "bedrooms": 2, "bathrooms": 1.0, "sqft": 786, "lot_size": 6155,
    "year_built": 1949, "property_type": "Single Family Residential",
    "assessed_value": 428248, "land_value": 337378, "improvement_value": 90870,
    "tax_amount": 5198, "tax_year": 2024,
    "county": "LOS ANGELES", "legal_description": "LOT 44 TR#6654",
    "apn": "8381-021-001",
    # D-118: SiteX's SaleLoanInfo, exact keys confirmed by the probe.
    "last_sale_price": 369000, "last_sale_date": "2015-12-23",
    "last_sale_price_per_sqft": 469.0,
}

_PRODUCED = set(PropertyData.model_fields)
_invented = sorted(k for k in SITEX if k not in _PRODUCED)
assert not _invented, (
    f"this fixture invents keys SiteX does not return: {_invented}. "
    f"A reproduction tool that feeds the builder impossible data reproduces "
    f"a document nobody receives."
)
# Comparables shaped as fetch_comparables() stores them (SimplyRETS-derived).
#
# Close dates are RELATIVE. Written absolute, this fixture quietly aged past
# the six-month comp window as the calendar moved and the renders started
# claiming a twelve-month search (D-132). A reproduction tool that drifts with
# the date reproduces a different thing each week.
def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


COMPS = [
    {"address": "1889 Bonita Ave, La Verne", "price": 631500, "close_date": _days_ago(40),
     "sqft": 940, "bedrooms": 2, "bathrooms": 1, "year_built": 1953, "lot_size": 7446,
     "distance": 0.58, "status": "Closed", "days_on_market": 12},
    {"address": "1507 2nd St, La Verne", "price": 635000, "close_date": _days_ago(150),
     "sqft": 912, "bedrooms": 3, "bathrooms": 1, "year_built": 1952, "lot_size": 6261,
     "distance": 0.54, "status": "Closed", "days_on_market": 21},
    {"address": "1845 Walnut St, La Verne", "price": 470000, "close_date": _days_ago(95),
     "sqft": 770, "bedrooms": 3, "bathrooms": 1, "year_built": 1910, "lot_size": 4917,
     "distance": 0.24, "status": "Closed", "days_on_market": 34},
    {"address": "1848 1st St, La Verne", "price": 590000, "close_date": _days_ago(112),
     "sqft": 698, "bedrooms": 1, "bathrooms": 1, "year_built": 1950, "lot_size": 5500,
     "distance": 0.30, "status": "Closed", "days_on_market": 8},
]

def report_data(theme, variant):
    d = {
        "id": "00000000-0000-0000-0000-000000000001",
        "account_id": "00000000-0000-0000-0000-0000000000a1",
        "user_id": "00000000-0000-0000-0000-0000000000u1",
        "report_type": "seller",
        "theme": theme,
        "accent_color": None,
        "language": "en",
        "property_address": "1358 5th Street",
        "property_city": "La Verne",
        "property_state": "CA",
        "property_zip": "91750",
        "property_county": "LOS ANGELES",
        "apn": "8381-021-001",
        "owner_name": "HERNANDEZ GERARDO J",
        "legal_description": "LOT 44 TR#6654",
        "property_type": "Single Family Residential",
        "sitex_data": SITEX,
        "comparables": COMPS,
        "selected_pages": None,
        "short_code": "AB12CD",
        "qr_code_url": None,
        "agent": {
            "name": "Zoe Noelle", "email": "zoe@trendyreports.io",
            "phone": "(213) 309-7286",
            "photo_url": "https://cdn.example.com/agents/zoe.jpg" if variant == "full" else None,
            "title": "Real Estate Professional",
            "license_number": "01234567",
            "company": "TrendyReports",
            "company_name": "TrendyReports",
            "logo_url": "https://cdn.example.com/logo.png" if variant == "full" else None,
        },
        "branding": None,
    }
    if variant == "full":
        d["selected_pages"] = ["cover", "contents", "overview", "aerial", "property",
                               "analysis", "comparables", "range", "market_trends"]
        d["overview_text"] = (
            "1358 5th Street is a 786 square foot single family home built in 1949, "
            "situated on a 6,155 square foot lot in La Verne. Four comparable sales "
            "within 0.6 miles closed between $470,000 and $635,000 over the past year."
        )
        from worker.compute.market_trends import SAMPLE_MARKET_TRENDS
        d["market_trends_data"] = {**SAMPLE_MARKET_TRENDS, "city": "La Verne"}
    return d

manifest = {}
for theme in sorted(THEME_TEMPLATES):
    data = report_data(theme, VARIANT)
    html = PropertyReportBuilder(data).render_html()
    p = OUT / f"property__{theme}__{VARIANT}.html"
    p.write_text(html, encoding="utf-8")
    manifest[theme] = {"path": str(p), "chars": len(html)}

# Dump the built context too — several E tickets are about values, not layout.
ctx_dump = {}
for theme in sorted(THEME_TEMPLATES):
    b = PropertyReportBuilder(report_data(theme, VARIANT))
    ctx_dump[theme] = {
        "page_set": list(b.page_set),
        "property": b._build_property_context(),
        "agent": b._build_agent_context(),
        "comparables": b._build_comparables_context(),
        "stats": b._build_stats_context(),
        "images": b._build_images_context(),
        "area_analysis": b._build_area_analysis_context(),
        "range_of_sales": b._build_range_of_sales_context(),
    }
(OUT / f"context__{VARIANT}.json").write_text(json.dumps(ctx_dump, indent=2, default=str))
print(json.dumps(manifest, indent=2))
