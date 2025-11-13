from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Credential detection: Demo account has limitations (no q, no sort)
DEMO = os.getenv("SIMPLYRETS_USERNAME", "").lower() == "simplyrets"

# Common helpers

def _date_window(lookback_days: int) -> tuple[str, str]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=max(1, int(lookback_days or 30)))
    return start.isoformat(), end.isoformat()

def _location(params: dict) -> Dict:
    """
    Location can be provided as a single city string or a list of ZIPs.
    - If zips present and non-empty: use postalCodes=comma-separated list
    - Else (production): use q=<city>
    - Demo account: returns {} (demo forbids q parameter, defaults to Houston data)
    
    Credential-aware: DEMO mode detected via SIMPLYRETS_USERNAME env var.
    """
    zips = params.get("zips") or []
    city = (params.get("city") or "").strip()
    
    if zips:
        return {"postalCodes": ",".join(z.strip() for z in zips if z.strip())}
    
    if DEMO:
        # Demo account rejects 'q' parameter with 400 error
        # Returns Houston data only
        return {}
    
    if city:
        # Production: use city search
        return {"q": city}
    
    return {}

def _sort(val: str) -> Dict:
    """
    Conditionally add sort parameter based on credential type.
    - Demo account: rejects sort parameter with 400 error, returns {}
    - Production: includes sort parameter per report type requirements
    
    Examples:
    - Market Snapshot/New Listings: "-listDate" (newest first)
    - Closed: "-closeDate" (most recent closings)
    - Inventory: "daysOnMarket" (freshest listings first)
    - Price Bands: "listPrice" (lowest to highest)
    """
    return {} if DEMO else {"sort": val}

def _filters(filters: Optional[dict]) -> Dict:
    """
    Map optional filters to SimplyRETS params.
    Supported inputs (optional):
      minprice, maxprice, type (RES,CND,MUL,LND,COM), beds, baths
    
    Maps to SimplyRETS parameters:
      minprice -> minprice (int)
      maxprice -> maxprice (int)
      type -> type (string, e.g., 'RES' or 'RES,CND')
      beds -> minbeds (int)
      baths -> minbaths (int)
    """
    f = filters or {}
    out: Dict = {}
    if f.get("minprice") is not None: out["minprice"] = int(f["minprice"])
    if f.get("maxprice") is not None: out["maxprice"] = int(f["maxprice"])
    if f.get("type"):                 out["type"]      = f["type"]
    if f.get("beds") is not None:     out["minbeds"]   = int(f["beds"])
    if f.get("baths") is not None:    out["minbaths"]  = int(f["baths"])
    return out

# Builders per report type

def build_market_snapshot(params: dict) -> Dict:
    """
    Market overview: Active + Pending + Closed in date window.
    Sort by latest listDate (production only).
    
    Per SimplyRETS docs Section 3.2:
    - status: Active,Pending,Closed
    - mindate/maxdate: date window
    - sort: -listDate (newest first, production only)
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
    q |= _sort("-listDate")
    return q

def build_new_listings(params: dict) -> Dict:
    """
    Fresh active listings in date window, sorted by newest listDate.
    
    Per SimplyRETS docs Section 3.3:
    - status: Active
    - mindate/maxdate: recent window (typically 7-14 days)
    - sort: -listDate (newest first, production only)
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
    q |= _sort("-listDate")
    return q

def build_closed(params: dict) -> Dict:
    """
    Recently closed sales within date window.
    
    Per SimplyRETS docs Section 3.5:
    - status: Closed
    - mindate/maxdate: recent closings window (typically 30 days)
    - sort: -closeDate (most recent closings first, production only)
    
    NOTE: Using -closeDate (not -listDate) for closed listings per spec.
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
    q |= _sort("-closeDate")
    return q

def build_inventory_by_zip(params: dict) -> Dict:
    """
    All currently active listings (no date window).
    
    Per SimplyRETS docs Section 3.4:
    - status: Active
    - No date window (all current inventory)
    - sort: daysOnMarket (freshest listings first, production only)
    - Typically grouped by ZIP code in the compute layer
    """
    q = {
        "status": "Active",
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    q |= _sort("daysOnMarket")
    return q

def build_open_houses(params: dict) -> Dict:
    """
    Active listings with upcoming/recent open houses.
    
    Per SimplyRETS docs Section 3.7:
    - status: Active
    - mindate/maxdate: typically current week (7 days)
    - sort: -listDate (production only)
    
    Note: SimplyRETS doesn't have a direct "hasOpenHouse" filter.
    We filter for properties with openHouse array in compute phase.
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
    q |= _sort("-listDate")
    return q

def build_price_bands(params: dict) -> Dict:
    """
    Active listings across all price ranges for segmentation analysis.
    
    Per SimplyRETS docs Section 3.6:
    - status: Active
    - No date window (all current inventory)
    - sort: listPrice (lowest to highest, production only)
    - Higher limit for market-wide analysis
    
    Note: For optimal performance with large markets, this could be split
    into multiple API calls with minprice/maxprice filters per band.
    Current implementation fetches all Active listings and segments them
    in the compute phase.
    """
    q = {
        "status": "Active",
        "limit": 1000,  # Higher limit since we're analyzing the full market
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    q |= _sort("listPrice")
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




