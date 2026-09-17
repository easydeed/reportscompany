import statistics
from typing import List, Dict
from datetime import datetime, timedelta, timezone

from worker.compute.moi import months_of_supply

def snapshot_metrics(rows: List[Dict]) -> Dict:
    active  = [r for r in rows if r["status"]=="Active"]
    pending = [r for r in rows if r["status"]=="Pending"]
    closed  = [r for r in rows if r["status"]=="Closed"]
    med = lambda xs: statistics.median(xs) if xs else 0
    avg = lambda xs: (sum(xs)/len(xs)) if xs else 0
    
    # Handle timezone-aware/naive datetimes for new7 calculation
    new7 = []
    for r in rows:
        d = r.get("list_date")
        if d:
            now = datetime.now(timezone.utc) if d.tzinfo else datetime.now()
            if d >= now - timedelta(days=7):
                new7.append(r)

    # SIXTH copy of this metric, and a THIRD distinct formula: this one is a
    # bare ratio with no monthly rate at all, so its "months" are not months.
    # Routed through compute/moi.py so there is one implementation, and the
    # 999.0 sentinel is gone — None means "not enough sales", which is what
    # 999 was always trying to say (D-056).
    #
    # NOTE: `snapshot_metrics` is imported by tasks.py and NEVER CALLED. It is
    # dead as of this writing. It is fixed rather than deleted because deleting
    # it is a judgement someone else should make, and left wrong it is the most
    # canonical-LOOKING of the six — a function called `snapshot_metrics` in a
    # module called `calc` is exactly what the next person would copy.
    #
    # The window is the caller's to choose and this function is not given one,
    # so it uses the shared default. If it is ever revived, pass the window the
    # rows were actually counted over.
    moi  = months_of_supply(len(active), len(closed))
    ctl  = avg([r["close_to_list_ratio"] for r in closed if r.get("close_to_list_ratio")])

    return {
        "total_active": len(active),
        "total_pending": len(pending),
        "total_closed": len(closed),
        "new_listings_7d": len(new7),
        "median_list_price": round(med([r["list_price"] for r in active if r.get("list_price")])),
        "median_close_price": round(med([r["close_price"] for r in closed if r.get("close_price")])),
        "avg_dom": round(avg([r["days_on_market"] for r in rows if r.get("days_on_market")]) or 0,1),
        "avg_price_per_sqft": round(avg([r["price_per_sqft"] for r in active if r.get("price_per_sqft")]) or 0),
        "close_to_list_ratio": round(ctl or 100.0,1),
        "months_of_inventory": moi,
        "absorption_rate": round((len(closed)/len(active)*100),2) if len(active)>0 else 0.0
    }

