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
                
                # DOM: Use API value if available, otherwise calculate from dates
                # SimplyRETS doesn't return daysOnMarket for Closed listings
                dom = _int(p.get("daysOnMarket"))
                if dom is None and list_date and close_date:
                    # Calculate DOM from list to close date
                    dom = (close_date - list_date).days
                    if dom < 0:
                        dom = 0  # Sanity check
                elif dom is None and list_date:
                    # For active/pending: calculate from list date to now
                    dom = (datetime.now() - list_date).days
                    if dom < 0:
                        dom = 0
                
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
                baths = _int((pr or {}).get("bathrooms"))
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










