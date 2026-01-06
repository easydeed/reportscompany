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

# NOTE:
# Gallery/featured listing photos are proxied to R2 at runtime in `tasks.generate_report`
# so cloud renderers (PDFShift) load images from our domain rather than MLS/CDN URLs.

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
    
    # Filter to only include listings from the requested city
    # (SimplyRETS q parameter may return nearby cities)
    listings = _filter_by_city(listings, city)
    
    # Constants for MOI calculation
    # 30.437 = average days per month (365.25 / 12)
    AVG_DAYS_PER_MONTH = 30.437
    
    # Calculate date cutoff for filtering
    # Use timezone-naive datetime for comparison (extract.py strips timezone in _iso)
    # But some dates may be timezone-aware, so we need to handle both cases
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Segment by status
    # Active: Current inventory (no date filter needed - these are current)
    active = [l for l in listings if l.get("status") == "Active"]
    
    # Pending: Properties under contract (filter by list_date in period)
    pending = [l for l in listings if l.get("status") == "Pending"]
    
    # All closed (before date filtering)
    all_closed = [l for l in listings if l.get("status") == "Closed"]
    
    # Debug: Log close_date values to verify extraction
    print(f"📊 METRICS DEBUG: {len(all_closed)} total Closed listings found")
    if all_closed:
        sample = all_closed[0]
        print(f"📊 METRICS DEBUG: Sample close_date={sample.get('close_date')}, type={type(sample.get('close_date'))}")
        print(f"📊 METRICS DEBUG: cutoff_date={cutoff_date}, type={type(cutoff_date)}")
    
    # Closed: ONLY those with close_date within the lookback period
    # This is critical for accurate Closed Sales count
    closed = []
    for l in all_closed:
        close_date = l.get("close_date")
        if close_date:
            try:
                # Handle both timezone-aware and timezone-naive datetimes
                if close_date.tzinfo is not None:
                    close_date = close_date.replace(tzinfo=None)
                if close_date >= cutoff_date:
                    closed.append(l)
            except Exception as e:
                print(f"📊 METRICS DEBUG: Error comparing dates: {e}")
    
    print(f"📊 METRICS DEBUG: {len(closed)} Closed listings after date filter (cutoff={cutoff_date})")
    
    # New Listings: Active listings with list_date within the lookback period
    new_listings = []
    for l in active:
        list_date = l.get("list_date")
        if list_date:
            try:
                if list_date.tzinfo is not None:
                    list_date = list_date.replace(tzinfo=None)
                if list_date >= cutoff_date:
                    new_listings.append(l)
            except Exception as e:
                print(f"📊 METRICS DEBUG: Error comparing list dates: {e}")
    
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


def _filter_by_city(listings: List[Dict], city: str) -> List[Dict]:
    """
    Filter listings to only include those in the specified city.
    
    SimplyRETS `q` parameter is a free-text search that can return results
    from nearby cities (e.g., searching "La Verne" may return "East Los Angeles").
    This function ensures we only include listings from the exact city requested.
    
    Comparison is case-insensitive and handles common variations.
    
    NOTE: When searching by ZIP code, city may be set to the ZIP itself (e.g., "91750").
    In this case, we skip city filtering since the API already filtered by postalCodes.
    """
    if not city or city == "Market" or city == "Unknown":
        return listings
    
    # Skip filtering if "city" is actually a ZIP code (all digits)
    # The API already filtered by postalCodes parameter
    if city.isdigit():
        return listings
    
    city_lower = city.lower().strip()
    
    filtered = []
    for l in listings:
        listing_city = (l.get("city") or "").lower().strip()
        # Exact match (case-insensitive)
        if listing_city == city_lower:
            filtered.append(l)
    
    return filtered


def build_new_listings_result(listings: List[Dict], context: Dict) -> Dict:
    """
    New Listings - Fresh inventory report
    
    Template expects:
    - Hero KPIs: total_new, median_price, avg_dom, avg_ppsf
    - listings array sorted by list_date desc
    
    IMPORTANT: SimplyRETS API does NOT reliably filter Active listings by mindate/maxdate.
    We MUST filter by list_date client-side to ensure accurate results.
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Filter to only include listings from the requested city
    # (SimplyRETS q parameter may return nearby cities)
    city_filtered = _filter_by_city(listings, city)
    
    # Calculate date cutoff for filtering
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Filter to active listings WITH DATE FILTERING
    # SimplyRETS API does NOT filter Active listings by mindate/maxdate reliably
    # We must filter client-side by list_date
    new_listings = []
    for l in city_filtered:
        if l.get("status") != "Active":
            continue
        list_date = l.get("list_date")
        if list_date:
            try:
                # Handle both timezone-aware and timezone-naive datetimes
                if hasattr(list_date, 'tzinfo') and list_date.tzinfo is not None:
                    list_date = list_date.replace(tzinfo=None)
                if list_date >= cutoff_date:
                    new_listings.append(l)
            except Exception as e:
                print(f"📊 NEW_LISTINGS DEBUG: Error comparing dates: {e}")
        else:
            # No list_date - skip (shouldn't happen)
            pass
    
    print(f"📊 NEW_LISTINGS DEBUG: {len(new_listings)} listings after date filter (cutoff={cutoff_date.date()})")
    
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
    Inventory - Active listings that became active within the lookback period
    
    Template expects:
    - Hero KPIs: total_active, new_this_month, median_dom, moi
    - listings array sorted by DOM desc
    
    IMPORTANT: The SimplyRETS API's mindate/maxdate may not filter Active listings
    as expected. We must filter by list_date client-side to ensure only listings
    that were listed within the selected lookback period are shown.
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Filter to only include listings from the requested city
    listings = _filter_by_city(listings, city)
    
    # Calculate date cutoff for filtering
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Active listings only - WITH DATE FILTERING
    # Only include listings that were listed within the lookback period
    active = []
    for l in listings:
        if l.get("status") != "Active":
            continue
        list_date = l.get("list_date")
        if list_date:
            try:
                # Handle both timezone-aware and timezone-naive datetimes
                if hasattr(list_date, 'tzinfo') and list_date.tzinfo is not None:
                    list_date = list_date.replace(tzinfo=None)
                if list_date >= cutoff_date:
                    active.append(l)
            except Exception as e:
                print(f"📊 INVENTORY DEBUG: Error comparing dates: {e}")
                # Include listing if we can't compare dates (fail-safe)
                active.append(l)
        else:
            # No list_date - include anyway (shouldn't happen, but fail-safe)
            active.append(l)
    
    print(f"📊 INVENTORY DEBUG: {len(active)} Active listings after date filter (cutoff={cutoff_date})")
    
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
    
    IMPORTANT: SimplyRETS mindate/maxdate filter by listDate, NOT closeDate!
    We must filter by close_date client-side to ensure accurate counts.
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Filter to only include listings from the requested city
    listings = _filter_by_city(listings, city)
    
    # Calculate date cutoff for filtering closed sales
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Filter closed listings by close_date within lookback period
    # API's mindate/maxdate filter by listDate, so we must filter by closeDate here
    closed = []
    for l in listings:
        if l.get("status") != "Closed":
            continue
        close_date = l.get("close_date")
        if close_date:
            try:
                # Handle both timezone-aware and timezone-naive datetimes
                if hasattr(close_date, 'tzinfo') and close_date.tzinfo is not None:
                    close_date = close_date.replace(tzinfo=None)
                if close_date >= cutoff_date:
                    closed.append(l)
            except Exception as e:
                print(f"📊 CLOSED DEBUG: Error comparing dates: {e}")
    
    print(f"📊 CLOSED DEBUG: {len(closed)} Closed listings after date filter (cutoff={cutoff_date})")
    
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
    
    # Filter to only include listings from the requested city
    listings = _filter_by_city(listings, city)
    
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
    
    def _format_band_price(val: float) -> str:
        """Format price for band labels: $500K, $1.2M, etc."""
        if val >= 1_000_000:
            return f"${val/1_000_000:.1f}M".replace('.0M', 'M')
        else:
            return f"${int(val/1000):,}K"
    
    if n >= 4:
        p25 = sorted_prices[n // 4]
        p50 = sorted_prices[n // 2]
        p75 = sorted_prices[(3 * n) // 4]
        
        band_defs = [
            (f"Under {_format_band_price(p50)}", 0, p50),
            (f"{_format_band_price(p50)} – {_format_band_price(p75)}", p50, p75),
            (f"{_format_band_price(p75)}+", p75, max_price + 1),
        ]
    else:
        # Fallback for small datasets
        band_defs = [
            (f"All ({_format_band_price(max_price)})", 0, max_price + 1)
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
    
    IMPORTANT: SimplyRETS API does NOT reliably filter Active listings by mindate/maxdate.
    We MUST filter by list_date client-side to ensure accurate results.
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Filter to only include listings from the requested city
    listings = _filter_by_city(listings, city)
    
    # Calculate date cutoff for filtering
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Get active listings WITH DATE FILTERING
    # SimplyRETS API does NOT filter Active listings by mindate/maxdate reliably
    new_listings = []
    for l in listings:
        if l.get("status") != "Active":
            continue
        list_date = l.get("list_date")
        if list_date:
            try:
                if hasattr(list_date, 'tzinfo') and list_date.tzinfo is not None:
                    list_date = list_date.replace(tzinfo=None)
                if list_date >= cutoff_date:
                    new_listings.append(l)
            except:
                pass
    
    print(f"📊 GALLERY DEBUG: {len(new_listings)} listings after date filter (cutoff={cutoff_date.date()})")
    
    # Sort by list date desc (newest first), limit to 12 for email galleries
    # V12: Increased from 9 to 12 for more comprehensive gallery displays
    new_listings_sorted = sorted(new_listings, key=lambda x: x.get("list_date") or datetime.min, reverse=True)[:12]
    
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
    
    # Calculate metrics from ALL new listings (not just the top 9 for display)
    # This provides accurate statistics for the email header cards
    all_prices = [l.get("list_price") for l in new_listings if l.get("list_price")]
    all_doms = [l.get("dom") for l in new_listings if l.get("dom") is not None]
    
    metrics = {
        "total_listings": len(new_listings),  # Total count (not capped)
        "median_list_price": sorted(all_prices)[len(all_prices) // 2] if all_prices else None,
        "min_price": min(all_prices) if all_prices else None,
        "max_price": max(all_prices) if all_prices else None,
        "avg_dom": sum(all_doms) / len(all_doms) if all_doms else None,
    }
    
    return {
        "report_type": "new_listings_gallery",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "total_listings": len(new_listings),  # Total count (not capped)
        "listings": gallery_listings,
        "metrics": metrics,  # For email template compatibility
    }


def build_featured_listings_result(listings: List[Dict], context: Dict) -> Dict:
    """
    Featured Listings - 2×2 grid (4 large properties) with hero photos
    
    Phase P2: Premium photo template for featured properties.
    Shows top 4 most expensive active listings with larger cards.
    """
    city = context.get("city", "Market")
    lookback_days = context.get("lookback_days", 30)
    
    # Filter to only include listings from the requested city
    listings = _filter_by_city(listings, city)
    
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
    
    # Calculate metrics from featured listings for email header cards
    all_prices = [l.get("list_price") for l in featured if l.get("list_price")]
    all_sqfts = [l.get("sqft") for l in featured if l.get("sqft")]
    
    metrics = {
        "total_listings": len(gallery_listings),
        "max_price": max(all_prices) if all_prices else None,
        "avg_sqft": int(sum(all_sqfts) / len(all_sqfts)) if all_sqfts else None,
    }
    
    return {
        "report_type": "featured_listings",
        "city": city,
        "lookback_days": lookback_days,
        "period_label": _period_label(lookback_days),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "total_listings": len(gallery_listings),
        "listings": gallery_listings,
        "metrics": metrics,  # For email template compatibility
    }


def build_result_json(report_type: str, listings: List[Dict], context: Dict) -> Dict:
    """
    Main dispatcher for report builders.
    
    Args:
        report_type: One of 7 TrendyReports types (5 original + 2 gallery)
        listings: Property data from PropertyDataExtractor
        context: Dict with city, lookback_days, filters, etc.
    
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
    
    result = builder(listings, context)
    
    # Pass through preset_display_name for PDF header customization
    # This allows Smart Presets to show their custom name (e.g., "Condo Watch")
    # instead of the generic report type name (e.g., "New Listings Gallery")
    filters = context.get("filters") or {}
    if filters.get("preset_display_name"):
        result["preset_display_name"] = filters["preset_display_name"]
    
    # V11: Pass through filters_label for email filter description blurb
    # This provides a human-readable summary like "2+ beds, Condos, under $1.2M"
    if context.get("filters_label"):
        result["filters_label"] = context["filters_label"]
    
    return result

