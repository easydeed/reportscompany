from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Credential detection for feature flags
SIMPLYRETS_USERNAME = os.getenv("SIMPLYRETS_USERNAME", "simplyrets")
IS_DEMO = SIMPLYRETS_USERNAME.lower() == "simplyrets"
IS_PRODUCTION = not IS_DEMO

# Feature flags based on credential mode
# Demo credentials (simplyrets/simplyrets) have restrictions:
# - Houston-only data
# - No city search via `q` parameter (use postalCodes only)
# - No `sort` parameter
# Production credentials enable:
# - Multi-city MLS data
# - City search via `q` parameter
# - Full sorting support
ALLOW_CITY_SEARCH = IS_PRODUCTION
ALLOW_SORTING = IS_PRODUCTION

print(f"[query_builders] Mode: {'PRODUCTION' if IS_PRODUCTION else 'DEMO'}")
print(f"[query_builders] Username: {SIMPLYRETS_USERNAME}")
print(f"[query_builders] City search: {'ENABLED' if ALLOW_CITY_SEARCH else 'DISABLED (use ZIP codes)'}")
print(f"[query_builders] Sorting: {'ENABLED' if ALLOW_SORTING else 'DISABLED'}")

# Common helpers

def _date_window(lookback_days: int) -> tuple[str, str]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=max(1, int(lookback_days or 30)))
    return start.isoformat(), end.isoformat()

def _location(params: dict) -> Dict:
    """
    Location can be provided as a single city string or a list of ZIPs.
    - If zips present and non-empty: use postalCodes=comma-separated list
    - Else if PRODUCTION mode: use q=<city> (city search)
    - Else (DEMO mode): return empty (Houston-only data)
    
    Note: Demo credentials do not support the `q` parameter.
    """
    zips = params.get("zips") or []
    city = (params.get("city") or "").strip()
    
    # ZIP codes work in both demo and production
    if zips:
        return {"postalCodes": ",".join(z.strip() for z in zips if z.strip())}
    
    # City search only works with production credentials
    if city and ALLOW_CITY_SEARCH:
        return {"q": city}
    
    # Demo mode: no location filter (Houston-only data by default)
    return {}

def _filters(filters: Optional[dict]) -> Dict:
    """
    Map optional filters to SimplyRETS params.
    Supported inputs (optional):
      minprice, maxprice, type (RES,CND,MUL,LND,COM), beds, baths
    """
    f = filters or {}
    out: Dict = {}
    if f.get("minprice") is not None: out["minprice"] = int(f["minprice"])
    if f.get("maxprice") is not None: out["maxprice"] = int(f["maxprice"])
    if f.get("type"):                out["type"]      = f["type"]
    if f.get("beds") is not None:    out["minbeds"]   = int(f["beds"])
    if f.get("baths") is not None:   out["minbaths"]  = int(f["baths"])
    return out

# Builders per report type

def build_market_snapshot(params: dict) -> Dict:
    """
    Active + Pending + Closed in date window.
    NOTE: sort parameter removed - not supported by all MLS vendors when using city search.
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        "status": "Active,Pending,Closed",
        "mindate": start,
        "maxdate": end,
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_new_listings(params: dict) -> Dict:
    """
    Fresh actives in date window.
    NOTE: sort parameter removed - not supported by all MLS vendors when using city search.
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_closed(params: dict) -> Dict:
    """
    Recently closed within date window.
    NOTE: For a first pass we use mindate/maxdate window with status=Closed.
    (If needed later, we can switch to close-date-specific params.)
    Sort parameter removed - not supported by all MLS vendors when using city search.
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        "status": "Closed",
        "mindate": start,
        "maxdate": end,
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_inventory_by_zip(params: dict) -> Dict:
    """
    All currently active listings (no date window).
    Typically grouped by ZIP code in the compute layer.
    NOTE: sort parameter removed - not supported by all MLS vendors when using city search.
    """
    q = {
        "status": "Active",
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_open_houses(params: dict) -> Dict:
    """
    Active listings with upcoming/recent open houses.
    Uses date window to capture current week's open houses.
    Note: SimplyRETS filters listings with openHouse data; we'll need to
    check for openHouse array in the response during compute phase.
    Sort parameter removed - not supported by all MLS vendors when using city search.
    """
    start, end = _date_window(params.get("lookback_days") or 7)  # Default 7 days for open houses
    q = {
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    # Note: SimplyRETS doesn't have a direct "hasOpenHouse" filter in all APIs.
    # We'll filter for properties with openHouse data in the compute layer.
    return q

def build_price_bands(params: dict) -> Dict:
    """
    Active listings across all price ranges.
    Price banding (segmentation) happens in the compute layer.
    
    Note: For optimal performance, this could be split into multiple
    API calls with minprice/maxprice filters (see Section 3.6 of docs).
    Current implementation fetches all Active listings and bands them
    in the compute phase.
    Sort parameter removed - not supported by all MLS vendors when using city search.
    """
    q = {
        "status": "Active",
        "limit": 1000,  # Higher limit since we're analyzing the full market
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    # Optional: If user provides specific bands via filters, we could use minprice/maxprice
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




