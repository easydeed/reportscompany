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

# Dispatcher

def build_params(report_type: str, params: dict) -> Dict:
    rt = (report_type or "market_snapshot").lower()
    if rt in ("market_snapshot", "snapshot"):
        return build_market_snapshot(params)
    if rt in ("new_listings", "new-listings", "newlistings"):
        return build_new_listings(params)
    if rt in ("closed", "closed_listings", "sold"):
        return build_closed(params)
    # default fallback
    return build_market_snapshot(params)

