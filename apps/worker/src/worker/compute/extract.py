from datetime import datetime
from typing import Dict, Any, List, Optional

class PropertyDataExtractor:
    """
    Normalize SimplyRETS property objects into flat, typed rows ready for validation & metrics.
    Mirrors the fields used by our calculators: list/close prices, list/close dates, DOM, area, type, status, CTL, PPSF.
    """

    def __init__(self, raw: List[Dict[str, Any]]):
        self.raw = raw

    def run(self) -> List[Dict[str, Any]]:
        out=[]
        for p in self.raw:
            try:
                addr = p.get("address",{}) ; pr = p.get("property",{}) ; mls=p.get("mls",{}) ; sales=p.get("sales",{})
                dom = _int(p.get("daysOnMarket"))
                lp  = _int(p.get("listPrice"))
                cp  = _int((sales or {}).get("closePrice"))
                area= _int((pr or {}).get("area"))
                ppsf= round(lp/area,2) if lp and area else None
                ctl = round((cp/lp)*100,2) if lp and cp else None
                out.append({
                    "mls_id": p.get("mlsId"),
                    "list_date": _iso(p.get("listDate")),
                    "close_date": _iso((sales or {}).get("closeDate")),
                    "status": (mls or {}).get("status") or p.get("status"),
                    "days_on_market": dom,
                    "list_price": lp,
                    "close_price": cp,
                    "city": (addr or {}).get("city"),
                    "zip_code": (addr or {}).get("postalCode"),
                    "property_type": (pr or {}).get("type","RES"),
                    "sqft": area,
                    "price_per_sqft": ppsf,
                    "close_to_list_ratio": ctl
                })
            except Exception:
                continue
        return out

def _iso(s: Optional[str]):
    if not s: return None
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00"))
    except: return None

def _int(v): 
    try: 
        return int(v) if v is not None else None
    except: 
        return None




