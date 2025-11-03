from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Common helpers

def _date_window(lookback_days: int) -> tuple[str, str]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=max(1, int(lookback_days or 30)))
    return start.isoformat(), end.isoformat()

def _location(params: dict) -> Dict:
    """
    Location can be provided as a single city string or a list of ZIPs.
    - If zips present and non-empty: use postalCodes=comma-separated list
    - Else: use q=<city>
    """
    zips = params.get("zips") or []
    city = (params.get("city") or "").strip()
    if zips:
        return {"postalCodes": ",".join(z.strip() for z in zips if z.strip())}
    if city:
        return {"q": city}
    # default fallback to ensure a valid query
    return {"q": "San Diego"}

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
    Active + Pending + Closed in date window, sort by latest listDate.
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        "status": "Active,Pending,Closed",
        "mindate": start,
        "maxdate": end,
        "sort": "-listDate",
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_new_listings(params: dict) -> Dict:
    """
    Fresh actives in date window, sorted by newest listDate.
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "sort": "-listDate",
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
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        "status": "Closed",
        "mindate": start,
        "maxdate": end,
        "sort": "-listDate",
        "limit": 500,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q

def build_inventory_by_zip(params: dict) -> Dict:
    """
    All currently active listings (no date window).
    Sorted by Days on Market (lowest first = newest inventory).
    Typically grouped by ZIP code in the compute layer.
    """
    q = {
        "status": "Active",
        "sort": "daysOnMarket",  # Ascending: freshest inventory first
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
    """
    start, end = _date_window(params.get("lookback_days") or 7)  # Default 7 days for open houses
    q = {
        "status": "Active",
        "mindate": start,
        "maxdate": end,
        "sort": "-listDate",
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
    """
    q = {
        "status": "Active",
        "sort": "listPrice",  # Sort by price for easier banding
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




