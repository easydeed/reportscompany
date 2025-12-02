"""
Report builders for all 5 TrendyReports template types.

Each builder takes:
- listings: list of property dicts (from PropertyDataExtractor)
- context: dict with city, lookback_days, etc.

Returns:
- result_json dict matching the shape expected by frontend templates
"""

import statistics
from typing import List, Dict, Any
from datetime import datetime, timedelta, date

def _format_currency(val: float | None) -> str:
    """Format as $XXX,XXX"""
    if val is None or val == 0:
        return "$0"
    return f"${int(val):,}"

def _format_date(d: date | datetime | None) -> str:
    """Format date as 'Nov 13, 2025'"""
    if d is None:
        return "—"
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%b %d, %Y")

def _median(vals: List[float]) -> float:
    """Safe median calculation"""
    return statistics.median(vals) if vals else 0.0

def _average(vals: List[float]) -> float:
    """Safe average calculation"""
    return (sum(vals) / len(vals)) if vals else 0.0

def _period_label(lookback_days: int) -> str:
    """Generate period label"""
    if lookback_days == 7:
        return "Last 7 days"
    elif lookback_days == 14:
        return "Last 2 weeks"
    elif lookback_days == 30:
        return "Last 30 days"
    elif lookback_days == 60:
        return "Last 60 days"
    elif lookback_days == 90:
        return "Last 90 days"
    else:
        return f"Last {lookback_days} days"

# ===== REPORT TYPE BUILDERS =====

def build_market_snapshot_result(listings: List[Dict], context: Dict) -> Dict:
    """
    Market Snapshot - Comprehensive market overview
    
    Template expects:
    - Hero KPIs: median_price, closed_count, avg_dom, moi
    - Core indicators: new_listings, pendings, close_to_list_ratio
    - Property types breakdown
    - Price tiers breakdown
    
    IMPORTANT: Closed Sales are filtered by actual close_date within lookback period.
    This ensures accurate counts (not just listings that were listed in the period).
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Constants for MOI calculation
    # 30.437 = average days per month (365.25 / 12)
    AVG_DAYS_PER_MONTH = 30.437
    
    # Calculate date cutoff for filtering
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Segment by status
    # Active: Current inventory (no date filter needed - these are current)
    active = [l for l in listings if l.get("status") == "Active"]
    
    # Pending: Properties under contract (filter by list_date in period)
    pending = [l for l in listings if l.get("status") == "Pending"]
    
    # Closed: ONLY those with close_date within the lookback period
    # This is critical for accurate Closed Sales count
    closed = [
        l for l in listings 
        if l.get("status") == "Closed" 
        and l.get("close_date") 
        and l["close_date"] >= cutoff_date
    ]
    
    # Also track all closed for reference (even those outside date range)
    all_closed = [l for l in listings if l.get("status") == "Closed"]
    
    # New Listings: Active listings with list_date within the lookback period
    new_listings = [
        l for l in active
        if l.get("list_date") and l["list_date"] >= cutoff_date
    ]
    
    # Core metrics (using date-filtered closed listings)
    median_close_price = _median([l["close_price"] for l in closed if l.get("close_price")])
    median_list_price = _median([l["list_price"] for l in active if l.get("list_price")])
    
    # Avg DOM: Use closed listings (days from list to close)
    avg_dom = _average([l["days_on_market"] for l in closed if l.get("days_on_market")])
    
    # MOI: Active inventory / Closed sales per month
    # Per market_worker.py reference:
    # MOI = Active Listings ÷ Monthly Sales Rate
    # Monthly Sales Rate = (Closings in period) × (30.437 / period_days)
    if closed:
        monthly_sales_rate = len(closed) * (AVG_DAYS_PER_MONTH / lookback_days)
        moi = len(active) / monthly_sales_rate if monthly_sales_rate > 0 else 99.9
    else:
        moi = 99.9  # Very high if no closed sales (buyer's market indicator)
    
    # Close-to-list ratio (from closed sales)
    ctl_ratios = [l["close_to_list_ratio"] for l in closed if l.get("close_to_list_ratio")]
    ctl = _average(ctl_ratios) if ctl_ratios else 100.0
    
    # Property types (SFR, Condo, Townhome, etc.) - using property_subtype for better categorization
    # Note: If user filtered by subtype, we may only have one type. That's expected.
    property_subtypes = {}
    for listing in listings:
        # Use property_subtype (mapped from SimplyRETS subType) for accurate breakdown
        ptype = listing.get("property_subtype") or listing.get("property_type") or "Other"
        if ptype not in property_subtypes:
            property_subtypes[ptype] = []
        property_subtypes[ptype].append(listing)
    
    by_type = []
    for ptype, props in property_subtypes.items():
        # Use date-filtered closed listings for accurate counts
        closed_props = [
            p for p in props 
            if p.get("status") == "Closed" 
            and p.get("close_date") 
            and p["close_date"] >= cutoff_date
        ]
        active_props = [p for p in props if p.get("status") == "Active"]
        
        # Include types that have either closed or active listings
        if closed_props or active_props:
            by_type.append({
                "label": ptype,
                "count": len(closed_props),  # Closed sales in period
                "active_count": len(active_props),  # Current active inventory
                "median_price": _median([p["close_price"] for p in closed_props if p.get("close_price")]) if closed_props else _median([p["list_price"] for p in active_props if p.get("list_price")]),
                "avg_dom": _average([p["days_on_market"] for p in closed_props if p.get("days_on_market")]) if closed_props else _average([p["days_on_market"] for p in active_props if p.get("days_on_market")])
            })
    
    # Price tiers (dynamic based on market)
    # Per ReportsGuide.md:
    # - Median price: from Closed sales in period
    # - Closed count: from Closed sales in period
    # - MOI per tier: Active count in tier / Closed count in tier
    if closed:
        prices = sorted([l["close_price"] for l in closed if l.get("close_price")])
        if prices:
            # Dynamic tier boundaries based on actual market data
            p25 = prices[len(prices) // 4] if len(prices) >= 4 else prices[0]
            p50 = prices[len(prices) // 2]
            p75 = prices[(3 * len(prices)) // 4] if len(prices) >= 4 else prices[-1]
            
            tiers = [
                ("Entry", 0, p50),
                ("Move-Up", p50, p75),
                ("Luxury", p75, float('inf'))
            ]
            
            price_tiers = []
            for label, min_price, max_price in tiers:
                # Closed sales in this tier (already date-filtered)
                tier_closed = [l for l in closed if min_price <= l.get("close_price", 0) < max_price]
                # Active inventory in this tier
                tier_active = [l for l in active if min_price <= l.get("list_price", 0) < max_price]
                
                if tier_closed or tier_active:
                    # MOI per tier: Active / Monthly Sales Rate
                    # Per market_worker.py: Monthly Sales Rate = Closed × (30.437 / lookback)
                    if tier_closed:
                        tier_monthly_rate = len(tier_closed) * (AVG_DAYS_PER_MONTH / lookback_days)
                        tier_moi = len(tier_active) / tier_monthly_rate if tier_monthly_rate > 0 else 99.9
                    else:
                        tier_moi = 99.9  # No closed sales in tier
                    
                    price_tiers.append({
                        "label": label,
                        "count": len(tier_closed),  # Closed sales in period
                        "active_count": len(tier_active),  # Current active inventory
                        "median_price": _median([l["close_price"] for l in tier_closed if l.get("close_price")]) if tier_closed else 0,
                        "moi": round(tier_moi, 1)
                    })
        else:
            price_tiers = []
    else:
        price_tiers = []
    
    return {
        "report_type": "market_snapshot",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        
        # Counts (all date-filtered where applicable)
        "counts": {
            "Active": len(active),           # Current active inventory
            "Pending": len(pending),         # Properties under contract
            "Closed": len(closed),           # Closed sales in period (date-filtered!)
            "NewListings": len(new_listings), # New listings in period
        },
        
        # Metrics (all based on date-filtered data)
        "metrics": {
            "median_list_price": median_list_price,
            "median_close_price": median_close_price,
            "avg_dom": round(avg_dom, 1) if avg_dom else 0,
            "avg_ppsf": round(_average([l.get("price_per_sqft") for l in active if l.get("price_per_sqft")]) or 0, 0),
            "close_to_list_ratio": round(ctl, 1),
            "months_of_inventory": round(moi, 1),
            "new_listings_count": len(new_listings),  # For core indicators
        },
        
        # Breakdown data
        "by_property_type": {pt["label"]: pt for pt in by_type},
        "price_tiers": {tier["label"]: tier for tier in price_tiers},
        
        # Sample listings for fallback view (mix of closed and active)
        "listings_sample": (closed[:10] + active[:10])[:20]
    }


def build_new_listings_result(listings: List[Dict], context: Dict) -> Dict:
    """
    New Listings - Fresh inventory report
    
    Template expects:
    - Hero KPIs: total_new, median_price, avg_dom, avg_ppsf
    - listings array sorted by list_date desc
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Filter to active listings listed within lookback period
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    new_listings = [
        l for l in listings 
        if l.get("status") == "Active" and l.get("list_date") and l["list_date"] >= cutoff_date
    ]
    
    # Sort by list date descending
    new_listings.sort(key=lambda x: x.get("list_date") or datetime.min, reverse=True)
    
    # Compute metrics
    median_price = _median([l["list_price"] for l in new_listings if l.get("list_price")])
    avg_dom = _average([l["days_on_market"] for l in new_listings if l.get("days_on_market")])
    avg_ppsf = _average([l["price_per_sqft"] for l in new_listings if l.get("price_per_sqft")])
    
    return {
        "report_type": "new_listings",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        
        # Counts
        "counts": {
            "Active": len(new_listings),
            "Pending": 0,
            "Closed": 0,
        },
        
        # Metrics
        "metrics": {
            "median_list_price": median_price,
            "avg_dom": round(avg_dom, 1),
            "avg_ppsf": round(avg_ppsf, 0),
        },
        
        # Listings for table
        "listings_sample": new_listings
    }


def build_inventory_result(listings: List[Dict], context: Dict) -> Dict:
    """
    Inventory - Current active listings snapshot
    
    Template expects:
    - Hero KPIs: total_active, new_this_month, median_dom, moi
    - listings array sorted by DOM desc
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Active listings only
    active = [l for l in listings if l.get("status") == "Active"]
    
    # New this month
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = [l for l in active if l.get("list_date") and l["list_date"] >= month_start]
    
    # Closed for MOI calculation
    closed = [l for l in listings if l.get("status") == "Closed"]
    moi = (len(active) / len(closed)) * (lookback_days / 30) if closed else 0.0
    
    # Sort by DOM descending (longest on market first)
    active_sorted = sorted(active, key=lambda x: x.get("days_on_market") or 0, reverse=True)
    
    # Median DOM
    median_dom = _median([l["days_on_market"] for l in active if l.get("days_on_market")])
    
    return {
        "report_type": "inventory",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        
        # Counts
        "counts": {
            "Active": len(active),
            "Pending": 0,
            "Closed": 0,
        },
        
        # Metrics
        "metrics": {
            "median_dom": round(median_dom, 1),
            "months_of_inventory": round(moi, 1),
            "new_this_month": len(new_this_month),
        },
        
        # Listings for table
        "listings_sample": active_sorted
    }


def build_closed_result(listings: List[Dict], context: Dict) -> Dict:
    """
    Closed Listings - Recent sales report
    
    Template expects:
    - Hero KPIs: total_closed, median_price, avg_dom, ctl
    - listings array sorted by close_date desc
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Closed listings only
    closed = [l for l in listings if l.get("status") == "Closed"]
    
    # Sort by close date descending
    closed_sorted = sorted(closed, key=lambda x: x.get("close_date") or datetime.min, reverse=True)
    
    # Metrics
    median_price = _median([l["close_price"] for l in closed if l.get("close_price")])
    avg_dom = _average([l["days_on_market"] for l in closed if l.get("days_on_market")])
    
    # Close-to-list ratio
    ctl_ratios = [l["close_to_list_ratio"] for l in closed if l.get("close_to_list_ratio")]
    ctl = _average(ctl_ratios) if ctl_ratios else 100.0
    
    return {
        "report_type": "closed",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        
        # Counts
        "counts": {
            "Active": 0,
            "Pending": 0,
            "Closed": len(closed),
        },
        
        # Metrics
        "metrics": {
            "median_close_price": median_price,
            "avg_dom": round(avg_dom, 1),
            "close_to_list_ratio": round(ctl, 1),
        },
        
        # Listings for table
        "listings_sample": closed_sorted
    }


def build_price_bands_result(listings: List[Dict], context: Dict) -> Dict:
    """
    Price Bands Analysis - Market segmentation by price ranges
    
    Template expects:
    - Hero KPIs: total_listings, median_price, avg_dom, price_range
    - Hottest/slowest band summary
    - bands array with label, count, share_pct, metrics
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Use all listings for price band analysis
    if not listings:
        return {
            "report_type": "price_bands",
            "city": city,
            "lookback_days": lookback_days,
            "period_label": _period_label(lookback_days),
            "report_date": datetime.now().strftime("%B %d, %Y"),
            "counts": {"Active": 0, "Pending": 0, "Closed": 0},
            "metrics": {},
            "price_bands": []
        }
    
    # Get price range
    prices = [l.get("list_price") or l.get("close_price") for l in listings if l.get("list_price") or l.get("close_price")]
    if not prices:
        prices = [0]
    
    min_price = min(prices)
    max_price = max(prices)
    median_price = _median(prices)
    avg_dom = _average([l["days_on_market"] for l in listings if l.get("days_on_market")])
    
    # Define bands (use quartiles for dynamic banding)
    sorted_prices = sorted(prices)
    n = len(sorted_prices)
    if n >= 4:
        p25 = sorted_prices[n // 4]
        p50 = sorted_prices[n // 2]
        p75 = sorted_prices[(3 * n) // 4]
        
        band_defs = [
            ("$0–$" + f"{int(p50/1000)}K", 0, p50),
            ("$" + f"{int(p50/1000)}K–$" + f"{int(p75/1000)}K", p50, p75),
            ("$" + f"{int(p75/1000)}K–$" + f"{int(max_price/1000)}K", p75, max_price + 1),
        ]
    else:
        # Fallback for small datasets
        band_defs = [
            ("$0–$" + f"{int(max_price/1000)}K", 0, max_price + 1)
        ]
    
    # Build bands
    bands = []
    for label, min_p, max_p in band_defs:
        band_listings = [
            l for l in listings 
            if min_p <= (l.get("list_price") or l.get("close_price") or 0) < max_p
        ]
        
        if band_listings:
            band_prices = [l.get("list_price") or l.get("close_price") for l in band_listings if l.get("list_price") or l.get("close_price")]
            band_dom = [l["days_on_market"] for l in band_listings if l.get("days_on_market")]
            band_ppsf = [l["price_per_sqft"] for l in band_listings if l.get("price_per_sqft")]
            
            bands.append({
                "label": label,
                "count": len(band_listings),
                "median_price": _median(band_prices) if band_prices else 0,
                "avg_dom": round(_average(band_dom), 1) if band_dom else 0,
                "avg_ppsf": round(_average(band_ppsf), 0) if band_ppsf else 0,
            })
    
    # Find hottest and slowest bands
    if bands:
        hottest = min(bands, key=lambda b: b["avg_dom"] if b["avg_dom"] > 0 else 999)
        slowest = max(bands, key=lambda b: b["avg_dom"])
    else:
        hottest = slowest = {"label": "—", "count": 0, "avg_dom": 0}
    
    return {
        "report_type": "price_bands",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        
        # Counts
        "counts": {
            "Active": len([l for l in listings if l.get("status") == "Active"]),
            "Pending": len([l for l in listings if l.get("status") == "Pending"]),
            "Closed": len([l for l in listings if l.get("status") == "Closed"]),
        },
        
        # Metrics
        "metrics": {
            "median_list_price": median_price,
            "avg_dom": round(avg_dom, 1),
            "min_price": min_price,
            "max_price": max_price,
        },
        
        # Price bands data
        "price_bands": bands,
        "hottest_band": hottest,
        "slowest_band": slowest,
        
        # Sample listings
        "listings_sample": listings[:20]
    }


# ===== DISPATCHER =====

# ===== PHASE P2: GALLERY TEMPLATES =====

def build_new_listings_gallery_result(listings: List[Dict], context: Dict) -> Dict:
    """
    New Listings Gallery - 3×3 grid (9 properties) with hero photos
    
    Phase P2: Photo-first template for new listings.
    Shows newest 9 active listings with images, address, price, beds/baths.
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Get new active listings
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    new_listings = [l for l in listings if l.get("status") == "Active" and l.get("list_date") and l["list_date"] >= cutoff_date]
    
    # Sort by list date desc (newest first), limit to 9
    new_listings_sorted = sorted(new_listings, key=lambda x: x.get("list_date") or datetime.min, reverse=True)[:9]
    
    # Format listings for gallery display
    gallery_listings = []
    for l in new_listings_sorted:
        gallery_listings.append({
            "hero_photo_url": l.get("hero_photo_url"),
            "street_address": l.get("street_address") or "Address not available",
            "city": l.get("city") or city,
            "zip_code": l.get("zip_code"),
            "list_price": l.get("list_price"),
            "bedrooms": l.get("bedrooms"),
            "bathrooms": l.get("bathrooms"),
            "sqft": l.get("sqft"),
            "list_date": _format_date(l.get("list_date")),
        })
    
    return {
        "report_type": "new_listings_gallery",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "total_listings": len(gallery_listings),
        "listings": gallery_listings,
    }


def build_featured_listings_result(listings: List[Dict], context: Dict) -> Dict:
    """
    Featured Listings - 2×2 grid (4 large properties) with hero photos
    
    Phase P2: Premium photo template for featured properties.
    Shows top 4 most expensive active listings with larger cards.
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Get active listings
    active = [l for l in listings if l.get("status") == "Active"]
    
    # Sort by list price desc (most expensive first), limit to 4
    featured = sorted(active, key=lambda x: x.get("list_price") or 0, reverse=True)[:4]
    
    # Format for gallery display
    gallery_listings = []
    for l in featured:
        gallery_listings.append({
            "hero_photo_url": l.get("hero_photo_url"),
            "street_address": l.get("street_address") or "Address not available",
            "city": l.get("city") or city,
            "zip_code": l.get("zip_code"),
            "list_price": l.get("list_price"),
            "bedrooms": l.get("bedrooms"),
            "bathrooms": l.get("bathrooms"),
            "sqft": l.get("sqft"),
            "price_per_sqft": l.get("price_per_sqft"),
            "days_on_market": l.get("days_on_market"),
            "list_date": _format_date(l.get("list_date")),
        })
    
    return {
        "report_type": "featured_listings",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "total_listings": len(gallery_listings),
        "listings": gallery_listings,
    }


def build_result_json(report_type: str, listings: List[Dict], context: Dict) -> Dict:
    """
    Main dispatcher for report builders.
    
    Args:
        report_type: One of 7 TrendyReports types (5 original + 2 gallery)
        listings: Property data from PropertyDataExtractor
        context: Dict with city, lookback_days, etc.
    
    Returns:
        result_json dict matching template expectations
    """
    # IMPORTANT: Keep this builders dict in sync with:
    # - Frontend: apps/web/app/lib/reportTypes.ts (ReportType union)
    # - Backend: apps/api/src/api/routes/schedules.py (report_type Literal)
    # - Email: apps/worker/src/worker/email/template.py (report_type_display map)
    builders = {
        "market_snapshot": build_market_snapshot_result,
        "new_listings": build_new_listings_result,
        "inventory": build_inventory_result,
        "closed": build_closed_result,
        "price_bands": build_price_bands_result,
        "open_houses": build_inventory_result,  # Reuse inventory builder for open houses
        "new_listings_gallery": build_new_listings_gallery_result,
        "featured_listings": build_featured_listings_result,
    }
    
    builder = builders.get(report_type)
    if not builder:
        raise ValueError(f"Unsupported report_type: {report_type}. Supported: {list(builders.keys())}")
    
    return builder(listings, context)

