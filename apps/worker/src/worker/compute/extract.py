from datetime import datetime
from typing import Dict, Any, List, Optional

class PropertyDataExtractor:
    """
    Normalize SimplyRETS property objects into flat, typed rows ready for validation & metrics.
    Mirrors the fields used by our calculators: list/close prices, list/close dates, DOM, area, type, status, CTL, PPSF.
    
    Phase P1: Now extracts hero_photo_url from SimplyRETS photos array for gallery templates.
    
    NOTE: SimplyRETS doesn't return daysOnMarket for Closed listings, so we calculate it
    from listDate to closeDate when available.
    """

    def __init__(self, raw: List[Dict[str, Any]]):
        self.raw = raw

    def run(self) -> List[Dict[str, Any]]:
        out=[]
        for p in self.raw:
            try:
                addr = p.get("address",{}) ; pr = p.get("property",{}) ; mls=p.get("mls",{}) ; sales=p.get("sales",{})
                
                # Parse dates first (we need them for DOM calculation)
                list_date = _iso(p.get("listDate"))
                close_date = _iso((sales or {}).get("closeDate"))
                
                # DAYS ON MARKET — D-105.
                #
                # THE COMMENT THAT USED TO BE HERE SAID "SimplyRETS doesn't
                # return daysOnMarket for Closed listings". That is not true and
                # it is what made this defect durable: the feed does return it,
                # at `mls.daysOnMarket`, and the read was at the top level. A
                # true observation about this code's behaviour — the value was
                # always None — was written down as a fact about the vendor and
                # then relied on by everything downstream. What was actually
                # observed is that the lookup returned None. It returned None
                # because it was the wrong key.
                #
                # Same defect as `closeDate`, which lives at `sales.closeDate`.
                # Third of its kind in this file's neighbourhood; the sweep that
                # found it is described on D-105.
                #
                # WHAT THE NUMBER MEANS, WHICH IS THE OTHER HALF. The feed's
                # daysOnMarket is list -> CONTRACT: the days a buyer could have
                # bought it. `close - list` is list -> CLOSE, which adds the
                # escrow period — 26 days on the repo's own fixture, taking 16
                # to 42. They are different quantities and only the first is
                # what "days on market" means to an agent.
                #
                # So: the feed's value when there is one; otherwise derive the
                # SAME quantity from contractDate when the feed carries it; and
                # for a closed sale with neither, None rather than a number that
                # means something else. D-056's rule — no sentinel, and the
                # caller says so in words. The table already renders None as "-".
                dom = _int((mls or {}).get("daysOnMarket"))
                if dom is None:
                    # Some deployments do put it at the top level; harmless to try.
                    dom = _int(p.get("daysOnMarket"))
                if dom is None and list_date:
                    contract_date = _iso((sales or {}).get("contractDate"))
                    if contract_date:
                        # list -> contract, the same quantity the feed reports.
                        dom = max((contract_date - list_date).days, 0)
                    elif close_date:
                        # Closed, and nothing says when it went under contract.
                        # `close - list` is NOT this quantity, so it is not
                        # substituted. Renders as "-".
                        dom = None
                    else:
                        # Active or pending: days on market so far, which is the
                        # right notion for a listing that has not sold.
                        dom = max((datetime.now() - list_date).days, 0)
                
                lp  = _int(p.get("listPrice"))
                cp  = _int((sales or {}).get("closePrice"))
                area= _int((pr or {}).get("area"))
                ppsf= round(lp/area,2) if lp and area else None
                ctl = round((cp/lp)*100,2) if lp and cp else None
                
                # Phase P1: Extract hero photo URL from SimplyRETS photos array
                photos = p.get("photos", [])
                hero_photo_url = photos[0] if photos and len(photos) > 0 else None
                
                # Additional property details for gallery templates
                beds = _int((pr or {}).get("bedrooms"))
                baths = _float((pr or {}).get("bathrooms"))  # Keep as float (e.g., 2.5 baths)
                street = (addr or {}).get("full") or (addr or {}).get("streetName")
                
                # Extract property subtype for better categorization
                # SimplyRETS subType: SingleFamilyResidence, Condominium, Townhouse, etc.
                raw_subtype = (pr or {}).get("subType") or ""
                # Map to display-friendly names
                subtype_map = {
                    "SingleFamilyResidence": "SFR",
                    "Condominium": "Condo",
                    "Townhouse": "Townhome",
                    "ManufacturedHome": "Manufactured",
                    "Duplex": "Multi-Family",
                }
                property_subtype = subtype_map.get(raw_subtype, raw_subtype or "Other")
                
                out.append({
                    "mls_id": p.get("mlsId"),
                    "list_date": list_date,
                    "close_date": close_date,
                    "status": (mls or {}).get("status") or p.get("status"),
                    "days_on_market": dom,
                    "list_price": lp,
                    "close_price": cp,
                    "city": (addr or {}).get("city"),
                    "zip_code": (addr or {}).get("postalCode"),
                    "property_type": (pr or {}).get("type","RES"),
                    "property_subtype": property_subtype,  # NEW: Human-readable subtype
                    "sqft": area,
                    "price_per_sqft": ppsf,
                    "close_to_list_ratio": ctl,
                    # Phase P1: Gallery template fields
                    "hero_photo_url": hero_photo_url,
                    "bedrooms": beds,
                    "bathrooms": baths,
                    "street_address": street,
                })
            except Exception:
                continue
        return out

def _iso(s: Optional[str]):
    """
    Parse ISO datetime string to timezone-naive datetime for consistent comparisons.
    SimplyRETS returns dates like: "2025-11-15T00:00:00.000Z"
    """
    if not s: return None
    try:
        # Parse ISO format (handles Z and +00:00 timezone suffixes)
        dt = datetime.fromisoformat(s.replace("Z","+00:00"))
        # Convert to timezone-naive for consistent comparisons
        # (report_builders.py uses datetime.now() which is timezone-naive)
        return dt.replace(tzinfo=None)
    except: return None

def _int(v): 
    try: 
        return int(v) if v is not None else None
    except: 
        return None

def _float(v):
    """Convert to float, preserving fractional values (e.g., 2.5 bathrooms)."""
    try:
        return float(v) if v is not None else None
    except:
        return None










