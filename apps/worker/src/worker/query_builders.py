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

def _filters(filters: Optional[dict]) -> Dict:
    """
    Map optional filters to SimplyRETS params.
    
    Supported inputs (optional):
      - minprice, maxprice: Price range
      - type: Property type (RES=Residential, CND=Condo, MUL=Multi-family, LND=Land, COM=Commercial)
      - subtype: Property subtype (SingleFamilyResidence, Condominium, Townhouse, ManufacturedHome, Duplex)
      - beds, baths: Minimum bedrooms/bathrooms
    
    Note on type vs subtype:
      - type=RES includes all residential (SFR, Condo, Townhouse)
      - subtype is more specific (e.g., SingleFamilyResidence only)
      - Can combine: type=RES + subtype=SingleFamilyResidence
    """
    f = filters or {}
    out: Dict = {}
    if f.get("minprice") is not None: out["minprice"] = int(f["minprice"])
    if f.get("maxprice") is not None: out["maxprice"] = int(f["maxprice"])
    if f.get("type"):                 out["type"]     = f["type"]
    if f.get("subtype"):              out["subtype"]  = f["subtype"]
    if f.get("beds") is not None:     out["minbeds"]  = int(f["beds"])
    if f.get("baths") is not None:    out["minbaths"] = int(f["baths"])
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
    - mindate/maxdate: lookback window (uses listDate/modifiedDate)
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
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "limit": 500,
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
    Listing Inventory: All currently active listings (no date window).
    
    Per ReportsQueries.md:
    - status: Active
    - sort: daysOnMarket (lowest DOM first = freshest) - only in production
    - No date filter (current inventory snapshot)
    """
    q = {
        **_common_params(),
        "status": "Active",
        "limit": 500,
        "offset": 0,
    }
    if ALLOW_SORTING:
        q["sort"] = "daysOnMarket"  # Freshest listings first
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
    - closed, closed_listings, sold: Recent closings
    - inventory_by_zip, inventory-by-zip, inventory: Active inventory by ZIP
    - open_houses, open-houses, openhouses: Upcoming/recent open houses
    - price_bands, price-bands, pricebands: Market segmented by price ranges
    """
    rt = (report_type or "market_snapshot").lower().replace("_", "-").replace(" ", "-")
    
    if rt in ("market-snapshot", "snapshot"):
        return build_market_snapshot(params)
    if rt in ("new-listings", "newlistings"):
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
