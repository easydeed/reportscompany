"""
La Verne Theme Validation Script
=================================
Fetches LIVE property data + comparables for 1358 5th St, La Verne, CA
using the same SiteX + SimplyRETS calls as the production API.

Auto-selects the best 6 comps (AI scoring: proximity + recency + sqft match)
then renders all 5 themes to PDF so you can visually confirm theme quality.

Usage (from repo root):
    cd apps/api
    python ../../scripts/gen_la_verne_all_themes.py

    # HTML only (fast, no Playwright needed):
    python ../../scripts/gen_la_verne_all_themes.py --html-only

    # Open PDFs after generation:
    python ../../scripts/gen_la_verne_all_themes.py --open

    # Single theme:
    python ../../scripts/gen_la_verne_all_themes.py --theme bold

Output:
    output/la_verne_themes/classic_report.pdf  (and .html)
    output/la_verne_themes/modern_report.pdf
    output/la_verne_themes/elegant_report.pdf
    output/la_verne_themes/teal_report.pdf
    output/la_verne_themes/bold_report.pdf
"""

import argparse
import asyncio
import os
import platform
import subprocess
import sys
import time
from datetime import date, datetime
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Path setup -- must be done BEFORE any project imports
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent           # scripts/
REPO_ROOT   = SCRIPT_DIR.parent                        # reportscompany/
API_SRC     = REPO_ROOT / "apps" / "api" / "src"
WORKER_SRC  = REPO_ROOT / "apps" / "worker" / "src"

sys.path.insert(0, str(API_SRC))
sys.path.insert(0, str(WORKER_SRC))

# ---------------------------------------------------------------------------
# Load .env BEFORE importing any service modules so env vars are set in time
# ---------------------------------------------------------------------------
_env_path = REPO_ROOT / "apps" / "api" / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=True)   # override=True so script values win
        print(f"  Loaded env from {_env_path}")
    except ImportError:
        # Fallback: manual parse (no python-dotenv needed)
        with open(_env_path, encoding="utf-8") as fh:
            for _line in fh:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _, _v = _line.partition("=")
                    # Strip quotes and override (don't use setdefault)
                    os.environ[_k.strip()] = _v.strip().strip('"').strip("'")
        print(f"  Loaded env (manual parse) from {_env_path}")
else:
    print(f"  [WARN] No .env found at {_env_path} -- using system env vars")

# ---------------------------------------------------------------------------
# Project imports (AFTER path + env setup so service modules read correct vars)
# NOTE: We do NOT import api.routes.property -- it pulls in FastAPI/DB stack.
#       We inline the two helper functions we need below.
# ---------------------------------------------------------------------------
from api.services.sitex import (
    SiteXError,
    SiteXNotFoundError,
    SiteXMultiMatchError,
    lookup_property,
)
from api.services.simplyrets import fetch_properties, normalize_listing
from worker.property_builder import PropertyReportBuilder


# ---------------------------------------------------------------------------
# Inlined property-type helpers (copied from api/routes/property.py)
# Avoids importing the full FastAPI route module (needs pydantic-settings + DB)
# ---------------------------------------------------------------------------

PROPERTY_TYPE_MAP: Dict[str, tuple] = {
    "sfr":                          ("residential", "SingleFamilyResidence"),
    "rsfr":                         ("residential", "SingleFamilyResidence"),
    "single family":                ("residential", "SingleFamilyResidence"),
    "singlefamily":                 ("residential", "SingleFamilyResidence"),
    "single family residential":    ("residential", "SingleFamilyResidence"),
    "residential":                  ("residential", "SingleFamilyResidence"),
    "pud":                          ("residential", "SingleFamilyResidence"),
    "condo":                        ("residential", "Condominium"),
    "condominium":                  ("residential", "Condominium"),
    "townhouse":                    ("residential", "Townhouse"),
    "th":                           ("residential", "Townhouse"),
    "townhome":                     ("residential", "Townhouse"),
    "duplex":                       ("multifamily", "Duplex"),
    "triplex":                      ("multifamily", "Triplex"),
    "quadplex":                     ("multifamily", "Quadruplex"),
    "quadruplex":                   ("multifamily", "Quadruplex"),
    "multi-family":                 ("multifamily", None),
    "multifamily":                  ("multifamily", None),
    "mobile":                       ("residential", "ManufacturedHome"),
    "mobilehome":                   ("residential", "ManufacturedHome"),
    "manufactured":                 ("residential", "ManufacturedHome"),
    "land":                         ("land", None),
    "vacant land":                  ("land", None),
    "commercial":                   ("commercial", None),
}

POST_FILTER_ALLOWED_SUBTYPES: Dict[str, set] = {
    "singlefamilyresidence": {"SingleFamilyResidence", "Detached"},
    "condominium":           {"Condominium", "StockCooperative", "Attached"},
    "townhouse":             {"Townhouse", "Attached"},
    "duplex":                {"Duplex"},
    "triplex":               {"Triplex"},
    "quadruplex":            {"Quadruplex"},
    "manufacturedhome":      {"ManufacturedHome", "ManufacturedOnLand", "MobileHome"},
}


def resolve_simplyrets_type(use_code: Optional[str]) -> tuple:
    if not use_code:
        return ("residential", "SingleFamilyResidence")
    key = use_code.strip().lower()
    if key in PROPERTY_TYPE_MAP:
        return PROPERTY_TYPE_MAP[key]
    for pattern, mapping in PROPERTY_TYPE_MAP.items():
        if pattern in key or key in pattern:
            return mapping
    return ("residential", "SingleFamilyResidence")


def post_filter_by_property_type(listings: list, subtype: Optional[str]) -> list:
    if not subtype:
        return listings
    allowed = POST_FILTER_ALLOWED_SUBTYPES.get(subtype.lower())
    if not allowed:
        return listings
    return [
        l for l in listings
        if not (l.get("property", {}).get("subType") or "")
        or (l.get("property", {}).get("subType") or "") in allowed
    ]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SUBJECT_ADDRESS  = "1358 5th St"
SUBJECT_CITY_ZIP = "La Verne, CA 91750"
TARGET_COMPS     = 6          # AI selects best N from the pool
SIMPLYRETS_LIMIT = 50         # raw pool size for ranking

OUTPUT_DIR = REPO_ROOT / "output" / "la_verne_themes"
ALL_THEMES = ["classic", "modern", "elegant", "teal", "bold"]
THEME_NUMBER_MAP = {"classic": 1, "modern": 2, "elegant": 3, "teal": 4, "bold": 5}

SAMPLE_AGENT = {
    "name": "Jennifer Martinez",
    "title": "Luxury Home Specialist",
    "license_number": "02156789",
    "phone": "(310) 555-4567",
    "email": "jennifer@luxuryestates.com",
    "company_name": "Luxury Estates Realty",
    "photo_url": "https://randomuser.me/api/portraits/women/44.jpg",
    "logo_url": "https://placehold.co/200x60/1B365D/white?text=Luxury+Estates",
}

COVER_IMAGE = (
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6"
    "?w=1200&h=800&fit=crop"
)

# Hardcoded fallback if SiteX is unconfigured or property not found
_FALLBACK_SITEX = {
    "full_address": "1358 5th St, La Verne, CA 91750",
    "street": "1358 5th St",
    "city": "La Verne",
    "state": "CA",
    "zip_code": "91750",
    "county": "Los Angeles",
    "apn": "8392-006-007",
    "owner_name": "Owner On Record",
    "property_type": "Single Family Residence",
    "bedrooms": 3,
    "bathrooms": 2.0,
    "sqft": 1344,
    "lot_size": 7500,
    "year_built": 1956,
    "latitude": 34.1013,
    "longitude": -117.7676,
    "assessed_value": 420000,
    "tax_amount": 5250,
    "land_value": 280000,
    "improvement_value": 140000,
    "tax_year": 2024,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in miles between two GPS coordinates."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 3956 * 2 * asin(sqrt(a))


def score_comp(comp: dict, subject_lat: float, subject_lng: float,
               subject_sqft: int) -> float:
    """
    AI scoring for comparable selection (higher = better).
    Weights: proximity 40% + sqft match 40% + recency 20%.
    """
    score = 0.0

    # Proximity (0-40)
    lat = comp.get("lat") or comp.get("latitude")
    lng = comp.get("lng") or comp.get("longitude")
    if lat and lng:
        dist = haversine(subject_lat, subject_lng, lat, lng)
        score += max(0.0, 40.0 - dist * 8.0)   # 5 mi -> 0 pts

    # Sqft match (0-40)
    comp_sqft = float(comp.get("sqft") or comp.get("area") or 0)
    if subject_sqft and comp_sqft:
        pct_diff = abs(comp_sqft - subject_sqft) / subject_sqft
        score += max(0.0, 40.0 - pct_diff * 80.0)   # 50% diff -> 0 pts

    # Recency (0-20) via list_date or close_date
    date_str = comp.get("close_date") or comp.get("list_date") or ""
    if date_str:
        try:
            d = datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).date()
            days_old = (date.today() - d).days
            score += max(0.0, 20.0 - days_old * (20.0 / 365))
        except Exception:
            pass

    return score


def fmt_date(date_str: str) -> str:
    """ISO date string -> MM/DD/YYYY."""
    if not date_str:
        return ""
    try:
        d = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        return d.strftime("%m/%d/%Y")
    except Exception:
        return str(date_str)[:10]


def build_comp_for_report(raw: dict, subject_lat: float, subject_lng: float) -> dict:
    """Convert a normalized SimplyRETS listing -> PropertyReportBuilder format."""
    lat = raw.get("lat") or raw.get("latitude")
    lng = raw.get("lng") or raw.get("longitude")
    dist_mi = haversine(subject_lat, subject_lng, lat, lng) if lat and lng else 0.0
    price = float(raw.get("close_price") or raw.get("list_price") or raw.get("price") or 0)
    return {
        "address":         raw.get("address", ""),
        "latitude":        lat,
        "longitude":       lng,
        "photo_url":       raw.get("photo_url") or (raw.get("photos") or [None])[0],
        "sale_price":      price,
        "sold_date":       fmt_date(raw.get("close_date") or raw.get("list_date") or ""),
        "sqft":            float(raw.get("sqft") or raw.get("area") or 0),
        "bedrooms":        raw.get("bedrooms") or 0,
        "bathrooms":       raw.get("bathrooms") or 0,
        "year_built":      raw.get("year_built") or 0,
        "lot_size":        raw.get("lot_size") or 0,
        "days_on_market":  raw.get("days_on_market") or raw.get("dom") or 0,
        "distance_miles":  round(dist_mi, 2),
    }


def _sample_comps(lat: float, lng: float) -> list:
    """Hardcoded fallback when SimplyRETS returns nothing."""
    return [
        {
            "address": "1240 Arrow Hwy, La Verne, CA 91750",
            "latitude": lat + 0.003, "longitude": lng - 0.002,
            "photo_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop",
            "sale_price": 620000, "sold_date": "01/15/2025",
            "sqft": 1400, "bedrooms": 3, "bathrooms": 2,
            "year_built": 1958, "lot_size": 6800,
            "days_on_market": 18, "distance_miles": 0.3,
        },
        {
            "address": "1425 Baseline Rd, La Verne, CA 91750",
            "latitude": lat - 0.004, "longitude": lng + 0.003,
            "photo_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop",
            "sale_price": 695000, "sold_date": "12/20/2024",
            "sqft": 1560, "bedrooms": 3, "bathrooms": 2,
            "year_built": 1962, "lot_size": 7200,
            "days_on_market": 12, "distance_miles": 0.5,
        },
        {
            "address": "2110 3rd St, La Verne, CA 91750",
            "latitude": lat + 0.006, "longitude": lng - 0.001,
            "photo_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=400&h=300&fit=crop",
            "sale_price": 575000, "sold_date": "02/02/2025",
            "sqft": 1280, "bedrooms": 3, "bathrooms": 1,
            "year_built": 1954, "lot_size": 6500,
            "days_on_market": 28, "distance_miles": 0.6,
        },
    ]


# ---------------------------------------------------------------------------
# Live data fetching
# ---------------------------------------------------------------------------

async def fetch_live_data():
    """
    1. SiteX lookup for subject property
    2. SimplyRETS active comps in same city/zip, same type
    3. Score + rank -> top TARGET_COMPS
    Returns (sitex_dict, comps_list)
    """

    # -- Step 1: SiteX property lookup -----------------------------------
    print("\n-- Step 1: SiteX property lookup --------------------------")
    print(f"  Address : {SUBJECT_ADDRESS}")
    print(f"  Location: {SUBJECT_CITY_ZIP}")
    sitex_dict = None
    try:
        prop = await lookup_property(SUBJECT_ADDRESS, SUBJECT_CITY_ZIP)
        if prop:
            print(f"  Found   : {prop.full_address}")
            print(f"  APN     : {prop.apn}")
            print(f"  Type    : {prop.property_type}")
            print(f"  Specs   : {prop.bedrooms}bd/{prop.bathrooms}ba/{prop.sqft:,}sqft yr{prop.year_built}")
            print(f"  Coords  : {prop.latitude}, {prop.longitude}")
            sitex_dict = prop.model_dump(exclude={"raw_response"})
        else:
            print("  [WARN] SiteX returned no result -- using fallback data")
    except SiteXMultiMatchError as e:
        print(f"  [WARN] Multiple SiteX matches -- using fallback data ({e})")
    except SiteXError as e:
        print(f"  [WARN] SiteX error ({e}) -- using fallback data")
    except Exception as e:
        print(f"  [WARN] Unexpected SiteX error ({type(e).__name__}: {e}) -- using fallback")

    if sitex_dict is None:
        print("  Using hardcoded fallback property data")
        sitex_dict = dict(_FALLBACK_SITEX)

    subject_lat  = sitex_dict.get("latitude")  or _FALLBACK_SITEX["latitude"]
    subject_lng  = sitex_dict.get("longitude") or _FALLBACK_SITEX["longitude"]
    subject_sqft = int(sitex_dict.get("sqft")  or _FALLBACK_SITEX["sqft"])
    subject_type = sitex_dict.get("property_type") or "Single Family Residence"

    # -- Step 2: SimplyRETS comparables ----------------------------------
    print("\n-- Step 2: SimplyRETS comparables --------------------------")
    sr_type, sr_subtype = resolve_simplyrets_type(subject_type)
    print(f"  SimplyRETS type={sr_type}  subtype={sr_subtype}")

    params: Dict = {
        "status": "Active",
        "type":   sr_type,
        "postalCodes": "91750",
        "q":      "La Verne",
        "limit":  SIMPLYRETS_LIMIT,
    }
    if sr_subtype:
        params["subtype"] = sr_subtype

    print(f"  Query params: {params}")

    raw_listings: list = []
    try:
        raw_listings = await fetch_properties(params, limit=SIMPLYRETS_LIMIT)
        print(f"  Raw results : {len(raw_listings)} listings")
    except Exception as e:
        print(f"  [ERROR] SimplyRETS call failed: {e}")

    # Post-filter for property type consistency
    filtered = post_filter_by_property_type(raw_listings, sr_subtype)
    print(f"  After type filter: {len(filtered)} listings")

    normalized = [normalize_listing(l) for l in filtered]

    # -- Step 3: AI comp scoring & selection -----------------------------
    print(f"\n-- Step 3: AI comp selection (top {TARGET_COMPS}) ------------------")
    scored = sorted(
        [(score_comp(c, subject_lat, subject_lng, subject_sqft), c) for c in normalized],
        key=lambda x: x[0],
        reverse=True,
    )

    print(f"  {'Score':>6}  {'Address':<42}  {'Sqft':>5}  {'Dist':>6}  Status")
    print(f"  {'-'*6}  {'-'*42}  {'-'*5}  {'-'*6}  {'-'*8}")

    comps: list = []
    for sc, c in scored[:TARGET_COMPS]:
        lat = c.get("lat") or 0.0
        lng = c.get("lng") or 0.0
        dist = haversine(subject_lat, subject_lng, lat, lng) if lat and lng else 0.0
        sqft = int(float(c.get("sqft") or 0))
        print(f"  {sc:>6.1f}  {c.get('address',''):<42}  {sqft:>5}  {dist:>5.2f}mi  {c.get('status','')}")
        comps.append(build_comp_for_report(c, subject_lat, subject_lng))

    if not comps:
        print("  [WARN] No live comps found -- using sample data")
        comps = _sample_comps(subject_lat, subject_lng)

    return sitex_dict, comps


# ---------------------------------------------------------------------------
# Sample market trends data for local/demo runs
# ---------------------------------------------------------------------------

def _get_sample_market_trends() -> dict:
    """
    Return sample market trends data for La Verne / San Gabriel Valley so the
    Market Trends page renders when using the SimplyRETS demo feed (which has
    no La Verne inventory).

    In production the PropertyReportBuilder fetches live data from SimplyRETS
    using property_city/zip/state and uses that instead of this sample.
    """
    try:
        from worker.compute.market_trends import SAMPLE_MARKET_TRENDS
        import copy
        data = copy.deepcopy(SAMPLE_MARKET_TRENDS)
        data["city"] = "La Verne"
        return data
    except Exception:
        pass

    # Inline fallback if the import fails for any reason
    return {
        "city": "La Verne",
        "period_label": "Last 90 Days",
        "generated_date": "February 2026",
        "data_source": "MLS",
        "sample_size": 42,
        "has_prior_data": True,
        "median_sale_price": {
            "current": 715000, "prior": 685000,
            "change_pct": 4.4, "direction": "up", "sentiment": "good",
            "formatted_current": "$715,000", "formatted_prior": "$685,000",
        },
        "avg_days_on_market": {
            "current": 22, "prior": 29,
            "change_pct": -24.1, "direction": "down", "sentiment": "good",
            "formatted_current": "22 days", "formatted_prior": "29 days",
        },
        "list_to_sale_ratio": {
            "current": 101.2, "prior": 98.7,
            "change_pct": 2.5, "direction": "up", "sentiment": "good",
            "formatted_current": "101.2%", "formatted_prior": "98.7%",
        },
        "price_per_sqft": {
            "current": 498, "prior": 472,
            "change_pct": 5.5, "direction": "up", "sentiment": "good",
            "formatted_current": "$498", "formatted_prior": "$472",
        },
        "closed_sales": {
            "current": 42, "prior": 38,
            "change_pct": 10.5, "direction": "up", "sentiment": "good",
            "formatted_current": "42", "formatted_prior": "38",
        },
        "active_listings": {
            "count": 67, "avg_price": 732000,
            "formatted_count": "67", "formatted_avg_price": "$732,000",
        },
        "months_of_inventory": {
            "current": 2.3, "gauge_pct": 19,
            "formatted_current": "2.3 months",
        },
        "market_condition": {
            "indicator": "sellers",
            "label": "Seller's Market",
            "description": (
                "With only 2.3 months of inventory and 42 sales in the last 90 days, "
                "sellers have the clear advantage in La Verne. Homes are moving quickly "
                "and typically selling above asking price (101.2% close-to-list ratio)."
            ),
            "score": 9,
        },
        "price_cut_stats": {"pct_with_cuts": 12.0, "avg_cut_pct": 1.8},
        "dom_distribution": {"fast": 55, "normal": 30, "slow": 15},
        "timeline_metrics": {"avg_marketing_days": 18, "avg_escrow_days": 31},
    }


# ---------------------------------------------------------------------------
# PDF rendering helpers
# ---------------------------------------------------------------------------

def _count_pdf_pages(pdf_path: Path) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return -1


def render_theme(theme_name: str, report_data: dict,
                 html_only: bool, open_after: bool) -> dict:
    result: dict = {"theme": theme_name, "page_count": None, "ok": True}

    print(f"\n{'='*60}")
    print(f"  Rendering: {theme_name.upper()}")
    print(f"{'='*60}")

    data = {**report_data, "theme": THEME_NUMBER_MAP[theme_name]}
    builder = PropertyReportBuilder(data)

    t0 = time.perf_counter()
    html = builder.render_html()

    html_path = OUTPUT_DIR / f"{theme_name}_report.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  HTML: {html_path.name} ({len(html):,} chars, {time.perf_counter()-t0:.2f}s)")

    if html_only:
        if open_after:
            _open_file(str(html_path))
        return result

    pdf_path = OUTPUT_DIR / f"{theme_name}_report.pdf"
    try:
        from playwright.sync_api import sync_playwright
        t1 = time.perf_counter()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.evaluate("() => document.fonts.ready")
            page.pdf(
                path=str(pdf_path),
                format="Letter",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
        pdf_size = pdf_path.stat().st_size
        elapsed = time.perf_counter() - t1
        print(f"  PDF : {pdf_path.name} ({pdf_size:,} bytes, {elapsed:.2f}s)")

        pg = _count_pdf_pages(pdf_path)
        result["page_count"] = pg
        tag = "[PASS]" if pg == 8 else f"[WARN] expected 8"
        print(f"  Pages: {pg} {tag}")

    except ImportError:
        print("  PDF:  SKIPPED (playwright not installed)")
    except Exception as e:
        print(f"  PDF:  FAILED -- {e}")
        result["ok"] = False

    print(f"  Total: {time.perf_counter()-t0:.2f}s")
    if open_after:
        target = pdf_path if pdf_path.exists() else html_path
        _open_file(str(target))
    return result


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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate all 5 themes for 1358 5th St, La Verne CA"
    )
    parser.add_argument(
        "--html-only", action="store_true",
        help="Output HTML only -- skip Playwright PDF rendering (fast)",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="Open output folder after generation",
    )
    parser.add_argument(
        "--theme", default="all",
        choices=ALL_THEMES + ["all"],
        help="Single theme to render, or 'all' (default)",
    )
    args = parser.parse_args()

    themes = ALL_THEMES if args.theme == "all" else [args.theme]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  La Verne Theme Validation")
    print(f"  Property : {SUBJECT_ADDRESS}, {SUBJECT_CITY_ZIP}")
    print(f"  Output   : {OUTPUT_DIR}")
    print(f"{'='*60}")

    # Fetch live data
    sitex_data, comps = asyncio.run(fetch_live_data())

    # Build unified report data
    report_data = {
        "report_type":    "seller",
        "theme":          4,          # overridden per-theme in render_theme()
        "accent_color":   None,       # let each theme use its own default
        "property_address": sitex_data.get("street", SUBJECT_ADDRESS),
        "property_city":    sitex_data.get("city",    "La Verne"),
        "property_state":   sitex_data.get("state",   "CA"),
        "property_zip":     sitex_data.get("zip_code","91750"),
        "property_county":  sitex_data.get("county",  "Los Angeles"),
        "apn":              sitex_data.get("apn",      ""),
        "owner_name":       sitex_data.get("owner_name", ""),
        "property_type":    sitex_data.get("property_type", "Single Family Residence"),
        "sitex_data":       sitex_data,
        "agent":            SAMPLE_AGENT,
        "cover_image_url":  COVER_IMAGE,
        "comparables":      comps,
        # All 8 pages including market_trends
        "selected_pages": [
            "cover", "contents", "aerial", "property",
            "analysis", "market_trends", "comparables", "range",
        ],
        # Inject sample market trends so the page renders with demo credentials
        # (live SimplyRETS demo feed has no La Verne data).
        # In production the builder fetches real data and ignores this key.
        "market_trends_data": _get_sample_market_trends(),
    }

    # Print summary
    print(f"\n-- Report Summary ------------------------------------------")
    print(f"  Property : {report_data['property_address']}, {report_data['property_city']}, CA")
    sq = sitex_data.get("sqft", "?")
    bd = sitex_data.get("bedrooms", "?")
    ba = sitex_data.get("bathrooms", "?")
    yr = sitex_data.get("year_built", "?")
    print(f"  SiteX    : {sq} sqft, {bd}bd/{ba}ba, yr {yr}")
    print(f"  Comps    : {len(comps)} selected")
    for i, c in enumerate(comps, 1):
        print(
            f"    {i}. {c['address']:<47}  "
            f"{int(c.get('sqft',0)):>5}sqft  "
            f"${c.get('sale_price',0):>8,.0f}  "
            f"{c.get('distance_miles',0):.1f}mi"
        )

    # Render all selected themes
    print(f"\n-- Rendering {len(themes)} theme(s) --------------------------------")
    t_all = time.perf_counter()
    results = [
        render_theme(t, report_data, html_only=args.html_only, open_after=False)
        for t in themes
    ]
    total_time = time.perf_counter() - t_all

    # Final summary
    print(f"\n{'='*60}")
    print(f"  Done in {total_time:.1f}s -- {len(themes)} theme(s)")
    print(f"  Output: {OUTPUT_DIR}")
    pdf_results = [r for r in results if r["page_count"] is not None]
    if pdf_results:
        print(f"\n  Page count validation:")
        all_pass = True
        for r in pdf_results:
            pg   = r["page_count"]
            tag  = "[PASS]" if pg == 8 else "[FAIL] expected 8"
            print(f"    {r['theme']:10s}  {pg} pages  {tag}")
            if pg != 8:
                all_pass = False
        print()
        if all_pass:
            print("  All themes pass page count check [PASS]")
        else:
            print("  [FAIL] Some themes have wrong page count")
    print(f"{'='*60}\n")

    if args.open:
        _open_file(str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
