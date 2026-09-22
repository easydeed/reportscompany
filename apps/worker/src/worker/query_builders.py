from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Credential detection for feature flags
SIMPLYRETS_USERNAME = os.getenv("SIMPLYRETS_USERNAME", "simplyrets")
SIMPLYRETS_VENDOR = os.getenv("SIMPLYRETS_VENDOR", "")  # MLS vendor ID - only set if needed
IS_DEMO = SIMPLYRETS_USERNAME.lower() == "simplyrets"
IS_PRODUCTION = not IS_DEMO

# Feature flags based on credential mode
# Demo credentials (simplyrets/simplyrets) have restrictions:
# - Houston-only data
# - No city search via `cities` parameter (use postalCodes only)
# - No `sort` parameter
# Production credentials enable:
# - Multi-city MLS data
# - City search via `q` parameter (fuzzy search - more widely supported)
# - Sorting support (disabled for now - may not be supported by all accounts)
ALLOW_CITY_SEARCH = IS_PRODUCTION
# Disable sorting for now - some accounts don't support it
# Set SIMPLYRETS_ALLOW_SORT=true to enable if your account supports it
ALLOW_SORTING = os.getenv("SIMPLYRETS_ALLOW_SORT", "").lower() == "true"

print(f"[query_builders] Mode: {'PRODUCTION' if IS_PRODUCTION else 'DEMO'}")
print(f"[query_builders] Username: {SIMPLYRETS_USERNAME}")
print(f"[query_builders] Vendor: {SIMPLYRETS_VENDOR or '(not set)'}")
print(f"[query_builders] City search: {'ENABLED' if ALLOW_CITY_SEARCH else 'DISABLED (use ZIP codes)'}")
print(f"[query_builders] Sorting: {'ENABLED' if ALLOW_SORTING else 'DISABLED'}")

# Common base params (per ReportsQueries.md)
def _common_params() -> Dict:
    """
    Common parameters for all SimplyRETS queries.
    - vendor: MLS feed identifier (e.g., 'crmls') - only if explicitly set
    
    Note: The vendor parameter may not be supported by all SimplyRETS accounts.
    Only include it if SIMPLYRETS_VENDOR is explicitly set in environment.
    """
    vendor = os.getenv("SIMPLYRETS_VENDOR")  # Only use if explicitly set
    if vendor:
        return {"vendor": vendor}
    return {}

# Common helpers

def _date_window(lookback_days: int) -> tuple[str, str]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=max(1, int(lookback_days or 30)))
    return start.isoformat(), end.isoformat()

def _location(params: dict) -> Dict:
    """
    Location can be provided as a single city string or a list of ZIPs.
    
    Per ReportsQueries.md:
    - Use `cities` parameter for explicit city filtering (recommended)
    - Use `postalCodes` for ZIP-based filtering
    - `q` is fuzzy search (MLS #, address, city, zip) - less precise
    
    NOTE: Some SimplyRETS accounts may not support `cities` parameter.
    We use `q` as a fallback which performs fuzzy search.

    Priority:
    1. If zips present: use postalCodes=comma-separated list
    2. Else if city present (PRODUCTION mode): use q=<city> (fuzzy search)
    3. Else (DEMO mode): return empty (Houston-only data by default)

    D-087 — HOW FUZZY `q` ACTUALLY IS, MEASURED AGAINST THE DEMO FEED:

        cities=Houston  ->  X-Total-Count 12, every row in Houston
        q=Houston       ->  X-Total-Count 13, twelve Houston + one TOMBALL
        Cities=Houston  ->  X-Total-Count 65, the whole feed (D-084: names
                            are case-sensitive and an unrecognised one is
                            silently ignored)

    `q` is a free-text search over MLS number, address, city and ZIP, so a
    listing on "Houston Street" in another town matches a Houston query. Every
    builder passes its rows through `_filter_by_city` (report_builders.py:285),
    which removes them — so the listings, medians and `counts` are clean. What
    cannot be cleaned that way is a `count=true` request, because the answer is
    a header and not rows. See `location_is_exact` below.

    `cities` IS NOT SUBSTITUTED HERE, deliberately. The note above says some
    accounts may not support it, and D-084 measured what SimplyRETS does with a
    name it does not recognise: it accepts it, ignores it, and returns the whole
    feed. On an unsupporting account the "precise" swap turns one stray listing
    into every listing in the MLS, with a 200 and no warning. The probe canaries
    `cities` against production; the swap waits for that verdict.
    """
    zips = params.get("zips") or []
    city = (params.get("city") or "").strip()
    
    # ZIP codes work in both demo and production
    if zips:
        return {"postalCodes": ",".join(z.strip() for z in zips if z.strip())}
    
    # City search - use `q` parameter (fuzzy search) which works with all accounts
    # Note: `cities` parameter is more explicit but may not be supported by all accounts
    if city and ALLOW_CITY_SEARCH:
        return {"q": city}
    
    # Demo mode: no location filter (Houston-only data by default)
    return {}


# Location parameters that return EXACTLY the rows asked for, so a count of
# them is a count of the requested place. `postalCodes` was measured against
# the demo feed: `postalCodes=77018` -> 5 rows, all in that ZIP.
EXACT_LOCATION_PARAMS = ("postalCodes", "cities")

# Location parameters that match MORE than the requested place. `q` is
# free-text; see `_location`'s docstring for the Tomball measurement.
FUZZY_LOCATION_PARAMS = ("q",)


def location_is_exact(query: Dict) -> bool:
    """
    Is this query's location filter one whose COUNT can be trusted? (D-087)

    Rows from a fuzzy query are cleaned by `_filter_by_city`. A count cannot be:
    `count=true` answers with `X-Total-Count`, a single number covering whatever
    the API matched, and there is nothing to filter. So a count taken from a `q`
    query is a count of a different population than the rows beside it — which
    is D-056's mistake with a new source, a numerator over one set and a listings
    table over another.

    A query with NO location filter is not exact either. That is demo mode,
    where the feed is one metro and the absence is deliberate — but "the whole
    feed" is still not "the requested city", and a count of it would be wrong in
    the same direction, only larger.

    `cities` is listed as exact because it measured exact. Nothing sends it yet;
    it is here so that the day the probe confirms production supports it,
    `_location` is the only thing that has to change.
    """
    return any(query.get(p) for p in EXACT_LOCATION_PARAMS)


def _filters(filters: Optional[dict], default_type: str = "RES") -> Dict:
    """
    Map optional filters to SimplyRETS params.
    
    Supported inputs (optional):
      - minprice, maxprice: Price range
      - type: Property type. MEASURED VOCABULARY, NOT THE ONE THIS LINE USED TO
        CLAIM (D-088). Each value below was sent to the demo feed with
        `count=true` and the returned rows' own `property.type` inspected:

            residential   45 rows, all RES     RES  45 rows, all RES
            condominium   33 rows, RES+CND     CND  33 rows, RES+CND
            land           6 rows, all LND     LND   6 rows, all LND
            rental        10 rows, all RNT     RNT  10 rows, all RNT
            multifamily    7 rows, all MLF     MUL  45 rows, all RES  ← ignored
            commercial     5 rows, all CRE     COM  45 rows, all RES  ← ignored
            farm           4 rows, all FRM

        `MUL` and `COM` were documented here as valid and are not. An
        unrecognised VALUE does not 400 and is not dropped — it falls back to
        residential, exactly as `type=ZZZNONSENSE` and `type=` do (both 45 rows,
        all RES). So a query asking for multi-family or commercial by the old
        codes silently comes back with houses. Nothing sends them today
        (grepped); this table is corrected so nothing starts.

        `RES` produces exactly the residential set, but whether it is recognised
        or merely falls back is NOT distinguishable from outside, because the
        fallback IS residential. Prefer the long names, which are unambiguous.
        Values are case-insensitive (`Residential`, `RESIDENTIAL` both work) —
        unlike parameter NAMES, which are case-sensitive (D-084).
      - subtype: Property subtype (SingleFamilyResidence, Condominium, Townhouse, ManufacturedHome, Duplex)
      - minbeds/beds, minbaths/baths: Minimum bedrooms/bathrooms (supports both naming conventions)
    
    Note on type vs subtype:
      - type=RES includes all residential (SFR, Condo, Townhouse)
      - subtype is more specific (e.g., SingleFamilyResidence only)
      - Can combine: type=RES + subtype=SingleFamilyResidence
    
    IMPORTANT: Defaults to type=RES to exclude rentals (RNT) which have
    monthly rent prices instead of sale prices. This prevents metrics
    from being skewed by $3,000-$5,000 rental prices mixed with $1M+ sales.
    """
    f = filters or {}
    out: Dict = {}
    if f.get("minprice") is not None: out["minprice"] = int(f["minprice"])
    if f.get("maxprice") is not None: out["maxprice"] = int(f["maxprice"])
    
    # Default to RES (Residential) to exclude rentals
    # User can override by explicitly setting type in filters
    out["type"] = f.get("type") or default_type
    
    if f.get("subtype"):              out["subtype"]  = f["subtype"]
    
    # Support both naming conventions: minbeds/minbaths (from presets) and beds/baths (legacy)
    beds = f.get("minbeds") or f.get("beds")
    baths = f.get("minbaths") or f.get("baths")
    if beds is not None:     out["minbeds"]  = int(beds)
    if baths is not None:    out["minbaths"] = int(baths)
    return out

# Builders per report type

def build_market_snapshot(params: dict) -> Dict:
    """
    Market Snapshot: Active listings in date window.
    
    Note: We query Active and Closed separately for cleaner data.
    The worker will make two calls:
    1. build_market_snapshot() for Active listings
    2. build_market_snapshot_closed() for Closed listings
    
    This gives us more accurate metrics for each status type.
    
    Parameters:
    - status: Active (single status for cleaner queries)
    - mindate/maxdate: lookback window
    - type/subtype: optional property type filters
    - limit: 1000
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "limit": 1000,
        "offset": 0,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q


def build_market_snapshot_closed(params: dict) -> Dict:
    """
    Market Snapshot (Closed): Closed listings in date window.
    
    Companion to build_market_snapshot() - queries Closed listings separately.
    
    Parameters:
    - status: Closed (single status for cleaner queries)
    - mindate/maxdate: lookback window
    - type/subtype: optional property type filters
    - limit: 1000
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Closed",
        "mindate": start,
        "maxdate": end,
        "limit": 1000,
        "offset": 0,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q


def build_market_snapshot_pending(params: dict) -> Dict:
    """
    Market Snapshot (Pending): Pending listings in date window.
    
    Per ReportsGuide.md: Query pending listings for "Pending Sales" core indicator.
    
    Parameters:
    - status: Pending
    - mindate/maxdate: SENT AND IGNORED. Measured against the live feed
      (D-075, D-084): both are accepted with no error and change nothing.
      The window that actually applies is the client-side `close_date` filter
      in `report_builders.py`. Kept because removing them changes nothing
      either, and their presence documents what the caller intended.
    - type/subtype: optional property type filters
    - limit: 1000
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Pending",
        "mindate": start,
        "maxdate": end,
        "limit": 1000,
        "offset": 0,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q


def build_new_listings(params: dict) -> Dict:
    """
    New Listings: Fresh actives in date window.
    
    Per ReportsQueries.md (Listing Inventory):
    - status: Active
    - mindate/maxdate: lookback window
    - sort: -listDate (newest first) - only in production
    - limit: 1000 (increased to capture all new listings in busy markets)
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "limit": 1000,  # Increased from 500 to capture all listings
        "offset": 0,
    }
    if ALLOW_SORTING:
        q["sort"] = "-listDate"
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_closed(params: dict) -> Dict:
    """
    Closed Listings: Recently closed sales in date window.
    
    Per ReportsQueries.md:
    - status: Closed
    - mindate/maxdate: lookback window
    - sort: -closeDate (most recent closings first) - only in production
    - limit: 1000
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Closed",
        "mindate": start,
        "maxdate": end,
        "limit": 1000,
        "offset": 0,
    }
    # Sort by close date for closed listings (per ReportsQueries.md)
    if ALLOW_SORTING:
        q["sort"] = "-closeDate"
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_inventory_by_zip(params: dict) -> Dict:
    """
    Listing Inventory: Active listings that became active within the date window.
    
    Per user request: Only show listings that were listed within the selected
    date range (e.g., last 30 days), not all current active inventory.
    
    Parameters:
    - status: Active
    - mindate/maxdate: SENT AND IGNORED — see D-075/D-084. The real window is
      the client-side `close_date` filter in `report_builders.py`.
    - sort: daysOnMarket (lowest DOM first = freshest) - only in production
    - limit: 1000
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "limit": 1000,
        "offset": 0,
    }
    if ALLOW_SORTING:
        q["sort"] = "daysOnMarket"  # Freshest listings first
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_inventory_active(params: dict) -> Dict:
    """
    Inventory (Active): ALL current active listings. NO DATE WINDOW.

    This is the months-of-supply numerator, and the absence of the date filter
    is the point. `build_inventory_by_zip` above carries a `listDate` window
    because the report's LISTINGS TABLE shows recently-listed homes — but MOI
    divides total inventory by a sales rate, and "listed in the last 30 days
    and still active" is a fraction of inventory. Feeding that to a 90-day
    sales rate produces a number that is wrong and looks reasonable.

    `market_trends.py` already had the comment: "NO date filter — we want total
    current inventory for MOI calculation". This is the same reasoning, one
    report over.

    The table is served from this same result, filtered by `list_date`
    client-side — which `build_inventory_result` already did anyway, because
    `mindate`/`maxdate` were never reliable (D-075). So this is one query, not
    two, and the table's behaviour is unchanged.
    """
    q = {
        **_common_params(),
        "status": "Active",
        "limit": 1000,
        "offset": 0,
    }
    if ALLOW_SORTING:
        q["sort"] = "daysOnMarket"
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q


def build_inventory_closed(params: dict) -> Dict:
    """
    Inventory (Closed): sales inside the months-of-supply window.

    Filtered on CLOSE date via `minclosedate`, which was measured working:
    `minclosedate=2030-01-01` returns nothing, `2000-01-01` returns a subset.

    BUT THE CALLER FILTERS AGAIN CLIENT-SIDE, and must keep doing so. Those
    measurements are against the public demo feed, the production probe has not
    come back, and `mindate` was measured being accepted and ignored — silently
    (D-075). Sending the parameter costs nothing if it is ignored; relying on
    it would cost correctness. See `compute.moi.closed_in_window`.

    A `listDate` window is deliberately NOT sent. That is the mistake D-074
    records in `market_trends.py`: a listing put on the market ten months ago
    and sold last month is a sale in this window, and a list-date filter drops
    it. Long-DOM listings are exactly the ones that take that long, so the
    exclusion is not random — it removes real sales from the denominator and
    pushes months-of-supply up.
    """
    from .compute.moi import SALES_RATE_WINDOW_DAYS, closed_since

    q = {
        **_common_params(),
        "status": "Closed",
        "minclosedate": closed_since(SALES_RATE_WINDOW_DAYS),
        "limit": 1000,
        "offset": 0,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q


def build_open_houses(params: dict) -> Dict:
    """
    Open Houses: Active listings with upcoming open houses.
    
    Per ReportsQueries.md:
    - status: Active
    - mindate/maxdate: week window
    - Post-filter for listings with openHouse data in compute layer
    """
    start, end = _date_window(params.get("lookback_days") or 7)  # Default 7 days for open houses
    q = {
        **_common_params(),
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "limit": 500,
        "offset": 0,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    # Note: SimplyRETS doesn't have a direct "hasOpenHouse" filter in all APIs.
    # We'll filter for properties with openHouse data in the compute layer.
    return q

def build_price_bands(params: dict) -> Dict:
    """
    Price Bands: Active listings for price tier analysis.
    
    Per ReportsQueries.md:
    - status: Active
    - For optimal performance, could split into multiple queries per band
    - Current implementation fetches all and bands in compute layer
    """
    q = {
        **_common_params(),
        "status": "Active",
        "limit": 1000,  # Higher limit since we're analyzing the full market
        "offset": 0,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

# Dispatcher

def build_params(report_type: str, params: dict) -> Dict:
    """
    Route report type to appropriate query builder.
    
    Supported report types:
    - market_snapshot, snapshot: Active + Pending + Closed overview
    - new_listings, new-listings, newlistings: Recent Active listings
    - new_listings_gallery: Photo gallery of new listings (uses new_listings query)
    - featured_listings: Premium listings gallery (uses new_listings query)
    - closed, closed_listings, sold: Recent closings
    - inventory_by_zip, inventory-by-zip, inventory: Active inventory by ZIP
    - open_houses, open-houses, openhouses: Upcoming/recent open houses
    - price_bands, price-bands, pricebands: Market segmented by price ranges
    """
    rt = (report_type or "market_snapshot").lower().replace("_", "-").replace(" ", "-")
    
    if rt in ("market-snapshot", "snapshot"):
        return build_market_snapshot(params)
    if rt in ("new-listings", "newlistings", "new-listings-gallery", "featured-listings"):
        # Gallery reports use the same query as new_listings (Active listings)
        return build_new_listings(params)
    if rt in ("closed", "closed-listings", "sold"):
        return build_closed(params)
    if rt in ("inventory-by-zip", "inventory"):
        return build_inventory_by_zip(params)
    if rt in ("open-houses", "openhouses"):
        return build_open_houses(params)
    if rt in ("price-bands", "pricebands"):
        return build_price_bands(params)
    
    # default fallback
    return build_market_snapshot(params)
