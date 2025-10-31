from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone

_VALID_STATUSES = {'Active','Pending','Closed','Expired','Withdrawn','Temp Off Market'}

def validate_property(p: Dict) -> Tuple[bool, Optional[str]]:
    if not p.get("mls_id"): return False, "mls_id"
    if p.get("status") not in _VALID_STATUSES: return False, "status"
    lp = p.get("list_price"); 
    if lp is not None and lp < 0: return False, "list_price"
    sq = p.get("sqft")
    if sq is not None and sq < 100: return False, "sqft"
    ld = p.get("list_date")
    if ld:
        # Handle both timezone-aware and naive datetimes
        now = datetime.now(timezone.utc) if ld.tzinfo else datetime.now()
        if ld > now: return False, "list_date"
    return True, None

def filter_valid(rows: List[Dict]) -> List[Dict]:
    ok=[] 
    for r in rows:
        good,_ = validate_property(r)
        if good: ok.append(r)
    return ok

