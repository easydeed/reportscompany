"""
Prompt 3A — Dump market snapshot builder output for Downey.
Usage:
    python tools/dump_market_snapshot.py [--city Downey] [--days 30]
Writes:
    tmp/market_snapshot_downey.json
"""
import json
import os
import pathlib
import sys
import argparse
import requests
from datetime import datetime, timedelta

AUTH = (os.environ["SIMPLYRETS_USERNAME"], os.environ["SIMPLYRETS_PASSWORD"])
BASE = "https://api.simplyrets.com"


def fetch_listings(city: str, statuses=("Active", "Closed", "Pending"), limit=200):
    """Fetch all relevant listings for a city."""
    all_listings = []
    for status in statuses:
        params = {
            "cities": city,
            "status": status,
            "limit": limit,
        }
        vendor = os.environ.get("SIMPLYRETS_VENDOR", "")
        if vendor:
            params["vendor"] = vendor
        r = requests.get(f"{BASE}/properties", params=params, auth=AUTH, timeout=30)
        r.raise_for_status()
        data = r.json()
        all_listings.extend(data if isinstance(data, list) else [])
        print(f"  Fetched {len(data)} {status} listings from {city}")
    return all_listings


def _iso(val):
    """Parse ISO date string to datetime."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(val[:len(fmt)-2] if "%" not in fmt else val, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00").replace("+00:00", ""))
    except Exception:
        return None


def extract_listing(raw: dict) -> dict:
    """Normalize a raw SimplyRETS listing to the internal format expected by builders."""
    prop   = raw.get("property") or {}
    mls    = raw.get("mls") or {}
    sales  = raw.get("sales") or {}
    addr   = raw.get("address") or {}
    assoc  = raw.get("association") or {}
    school = raw.get("school") or {}
    photos = raw.get("photos") or []

    list_price  = raw.get("listPrice") or 0
    close_price = sales.get("closePrice") or 0
    sqft        = prop.get("area") or 0

    ppsf = round(close_price / sqft, 2) if close_price and sqft else (
           round(list_price / sqft, 2) if list_price and sqft else None)

    ctl = None
    if list_price and close_price:
        ctl = round((close_price / list_price) * 100, 2)

    # Price cut detection
    orig_list = raw.get("originalListPrice") or list_price
    has_price_cut = bool(orig_list and list_price and orig_list > list_price)

    return {
        "mls_id":          raw.get("mlsId"),
        "listing_id":      raw.get("listingId"),
        "status":          mls.get("status"),
        "list_price":      list_price,
        "original_list_price": orig_list,
        "has_price_cut":   has_price_cut,
        "price_cut_amount": (orig_list - list_price) if has_price_cut else 0,
        "close_price":     close_price,
        "close_to_list_ratio": ctl,
        "price_per_sqft":  ppsf,
        "days_on_market":  mls.get("daysOnMarket"),
        "list_date":       _iso(raw.get("listDate")),
        "close_date":      _iso(sales.get("closeDate")),
        "contract_date":   _iso(sales.get("contractDate")),
        "modified":        _iso(raw.get("modified")),
        "city":            addr.get("city"),
        "postal_code":     addr.get("postalCode"),
        "address":         addr.get("full"),
        "property_type":   prop.get("type"),
        "property_subtype": prop.get("subType"),
        "sqft":            sqft,
        "lot_sqft":        prop.get("lotSizeArea"),
        "acres":           prop.get("acres"),
        "bedrooms":        prop.get("bedrooms"),
        "bathrooms":       prop.get("bathsFull"),
        "year_built":      prop.get("yearBuilt"),
        "hoa_fee":         assoc.get("fee"),
        "school_district": school.get("district"),
        "photo_count":     len(photos),
        "office_name":     (raw.get("office") or {}).get("name"),
        "buyer_office":    (sales.get("office") or {}).get("name"),
    }


def compute_snapshot(listings, city, lookback_days=30):
    """Replicate build_market_snapshot_result logic for CLI use."""
    cutoff = datetime.now() - timedelta(days=lookback_days)

    # Normalize
    norm = [extract_listing(l) for l in listings]
    norm = [l for l in norm if (l["city"] or "").lower() == city.lower()]

    active  = [l for l in norm if l["status"] == "Active"]
    pending = [l for l in norm if l["status"] == "Pending"]
    all_closed = [l for l in norm if l["status"] == "Closed"]

    closed = [l for l in all_closed if l.get("close_date") and l["close_date"] >= cutoff]
    new_listings = [l for l in active if l.get("list_date") and l["list_date"] >= cutoff]

    # Core metrics
    def median(vals):
        vals = sorted(v for v in vals if v)
        return vals[len(vals)//2] if vals else 0

    def avg(vals):
        vals = [v for v in vals if v]
        return sum(vals)/len(vals) if vals else 0

    med_close = median([l["close_price"] for l in closed])
    med_list  = median([l["list_price"] for l in active])
    avg_dom   = avg([l["days_on_market"] for l in closed])
    avg_ppsf  = avg([l["price_per_sqft"] for l in active if l["price_per_sqft"]])
    ctl_vals  = [l["close_to_list_ratio"] for l in closed if l.get("close_to_list_ratio")]
    ctl       = avg(ctl_vals) if ctl_vals else 100.0

    monthly_rate = len(closed) * (30.437 / lookback_days) if closed else 0
    moi = round(len(active) / monthly_rate, 1) if monthly_rate else 99.9

    # Price cut rate
    active_with_cuts = [l for l in active if l["has_price_cut"]]
    cut_rate = round(len(active_with_cuts) / len(active) * 100, 1) if active else 0
    cut_amounts = [l["price_cut_amount"] for l in active_with_cuts if l["price_cut_amount"]]
    median_cut = median(cut_amounts) if cut_amounts else 0

    # DOM distribution
    dom_vals = [l["days_on_market"] for l in closed if l.get("days_on_market") is not None]
    dom_dist = {}
    if dom_vals:
        dom_dist = {
            "under_7":  round(len([d for d in dom_vals if d <= 7])  / len(dom_vals) * 100, 1),
            "under_14": round(len([d for d in dom_vals if d <= 14]) / len(dom_vals) * 100, 1),
            "under_30": round(len([d for d in dom_vals if d <= 30]) / len(dom_vals) * 100, 1),
            "over_45":  round(len([d for d in dom_vals if d > 45])  / len(dom_vals) * 100, 1),
        }

    # Contract-to-close and marketing days
    escrow_days_list = []
    marketing_days_list = []
    for l in closed:
        if l.get("contract_date") and l.get("close_date"):
            # A2: clamp negative escrow days to 0
            escrow_days_list.append(max(0, (l["close_date"] - l["contract_date"]).days))
        if l.get("list_date") and l.get("contract_date"):
            # A2: clamp negative marketing days to 0
            marketing_days_list.append(max(0, (l["contract_date"] - l["list_date"]).days))

    # By subtype
    by_subtype = {}
    for l in norm:
        st = l.get("property_subtype") or "Other"
        if st not in by_subtype:
            by_subtype[st] = {"active": 0, "closed": 0, "prices": []}
        if l["status"] == "Active":
            by_subtype[st]["active"] += 1
        elif l["status"] == "Closed" and l.get("close_date") and l["close_date"] >= cutoff:
            by_subtype[st]["closed"] += 1
            if l["close_price"]:
                by_subtype[st]["prices"].append(l["close_price"])

    by_subtype_summary = {
        st: {
            "active": v["active"],
            "closed": v["closed"],
            "median_price": median(v["prices"]),
        }
        for st, v in by_subtype.items()
    }

    return {
        "city": city,
        "lookback_days": lookback_days,
        "period_label": f"Last {lookback_days} days",
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "counts": {
            "Active":      len(active),
            "Pending":     len(pending),
            "Closed":      len(closed),
            "NewListings": len(new_listings),
        },
        "metrics": {
            "median_list_price":     round(med_list),
            "median_close_price":    round(med_close),
            "avg_dom":               round(avg_dom, 1),
            "avg_ppsf":              round(avg_ppsf),
            "close_to_list_ratio":   round(ctl, 1),
            "months_of_inventory":   moi,
            "new_listings_count":    len(new_listings),
        },
        "price_cut_stats": {
            "active_with_cuts":      len(active_with_cuts),
            "cut_rate_pct":          cut_rate,
            "median_cut_amount":     round(median_cut),
        },
        "dom_distribution": dom_dist,
        "contract_timelines": {
            "avg_escrow_days":    round(avg(escrow_days_list), 1) if escrow_days_list else None,
            "avg_marketing_days": round(avg(marketing_days_list), 1) if marketing_days_list else None,
            "sample_size":        len(escrow_days_list),
        },
        "by_property_subtype": by_subtype_summary,
        "listings_sample": [
            {k: v for k, v in l.items() if k not in ("list_date","close_date","contract_date","modified")}
            for l in (closed[:5] + active[:5])
        ],
    }


def main():
    ap = argparse.ArgumentParser(description="Dump market snapshot for a city")
    ap.add_argument("--city",   default="Downey")
    ap.add_argument("--days",   type=int, default=30)
    ap.add_argument("--limit",  type=int, default=200)
    args = ap.parse_args()

    out_dir = pathlib.Path("tmp")
    out_dir.mkdir(exist_ok=True)

    print(f"Fetching listings for {args.city}…")
    raw = fetch_listings(args.city, limit=args.limit)
    print(f"  Total raw listings: {len(raw)}")

    print(f"\nComputing snapshot (lookback={args.days} days)…")
    result = compute_snapshot(raw, args.city, args.days)

    fname = f"market_snapshot_{args.city.lower().replace(' ', '_')}.json"
    out_path = out_dir / fname
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    print(f"\nKeys (sorted): {sorted(result.keys())}")
    print(f"\nMetrics keys: {sorted(result['metrics'].keys())}")
    print(f"\nSummary line:")
    m = result["metrics"]
    c = result["counts"]
    print(
        f"  active={c['Active']}  closed={c['Closed']}  "
        f"median_list=${m['median_list_price']:,}  "
        f"median_close=${m['median_close_price']:,}  "
        f"avg_dom={m['avg_dom']}  "
        f"moi={m['months_of_inventory']}  "
        f"ctl={m['close_to_list_ratio']}%"
    )
    pc = result["price_cut_stats"]
    print(
        f"  price_cuts={pc['active_with_cuts']} ({pc['cut_rate_pct']}% of active)  "
        f"median_cut=${pc['median_cut_amount']:,}"
    )
    dd = result["dom_distribution"]
    if dd:
        print(
            f"  DOM distribution: <=7d={dd.get('under_7')}%  "
            f"<=14d={dd.get('under_14')}%  "
            f"<=30d={dd.get('under_30')}%  "
            f">45d={dd.get('over_45')}%"
        )
    ct = result["contract_timelines"]
    if ct.get("avg_escrow_days") is not None:
        print(
            f"  avg_escrow={ct['avg_escrow_days']}d  "
            f"avg_marketing={ct['avg_marketing_days']}d  "
            f"(n={ct['sample_size']})"
        )

    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
