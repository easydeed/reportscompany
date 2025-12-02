#!/usr/bin/env python3
"""
Test script to verify the report generation flow without deploying.
This simulates what the worker does: fetch -> extract -> build metrics.
"""

import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

# Add worker src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'worker', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'apps', 'worker', '.env'))

from worker.vendors.simplyrets import fetch_properties
from worker.compute.extract import PropertyDataExtractor
from worker.query_builders import build_market_snapshot, build_market_snapshot_closed, build_market_snapshot_pending

def test_market_snapshot(city: str = "Irvine", lookback_days: int = 30):
    """Test the full Market Snapshot flow"""
    print("=" * 80)
    print(f"MARKET SNAPSHOT TEST: {city}, {lookback_days} days lookback")
    print("=" * 80)
    
    params = {
        "city": city,
        "lookback_days": lookback_days,
        "filters": {}
    }
    
    # Step 1: Build queries
    print("\n📋 STEP 1: Building queries...")
    active_query = build_market_snapshot(params)
    closed_query = build_market_snapshot_closed(params)
    pending_query = build_market_snapshot_pending(params)
    
    print(f"  Active query: {active_query}")
    print(f"  Closed query: {closed_query}")
    print(f"  Pending query: {pending_query}")
    
    # Step 2: Fetch from SimplyRETS
    print("\n📡 STEP 2: Fetching from SimplyRETS...")
    active_raw = fetch_properties(active_query, limit=500)
    print(f"  Active: {len(active_raw)} properties")
    
    closed_raw = fetch_properties(closed_query, limit=500)
    print(f"  Closed: {len(closed_raw)} properties")
    
    pending_raw = fetch_properties(pending_query, limit=500)
    print(f"  Pending: {len(pending_raw)} properties")
    
    # Step 3: Extract/normalize
    print("\n🔧 STEP 3: Extracting/normalizing data...")
    combined_raw = active_raw + closed_raw + pending_raw
    extracted = PropertyDataExtractor(combined_raw).run()
    print(f"  Extracted: {len(extracted)} properties")
    
    # Step 4: Analyze the data
    print("\n📊 STEP 4: Analyzing extracted data...")
    
    # Count by status
    status_counts = {}
    for p in extracted:
        status = p.get("status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    print(f"  By status: {status_counts}")
    
    # Check close_date presence for Closed listings
    closed_listings = [p for p in extracted if p.get("status") == "Closed"]
    has_close_date = sum(1 for p in closed_listings if p.get("close_date"))
    has_dom = sum(1 for p in closed_listings if p.get("days_on_market"))
    print(f"  Closed listings with close_date: {has_close_date}/{len(closed_listings)}")
    print(f"  Closed listings with days_on_market: {has_dom}/{len(closed_listings)}")
    
    # Sample close_date values
    if closed_listings:
        sample = closed_listings[0]
        print(f"\n  Sample Closed listing:")
        print(f"    mls_id: {sample.get('mls_id')}")
        print(f"    close_date: {sample.get('close_date')} (type: {type(sample.get('close_date'))})")
        print(f"    list_date: {sample.get('list_date')} (type: {type(sample.get('list_date'))})")
        print(f"    close_price: {sample.get('close_price')}")
        print(f"    days_on_market: {sample.get('days_on_market')}")
    
    # Step 5: Apply date filtering (like report_builders.py does)
    print("\n📅 STEP 5: Applying date filtering...")
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    print(f"  Cutoff date: {cutoff_date}")
    
    # Filter closed by close_date
    filtered_closed = []
    for l in closed_listings:
        close_date = l.get("close_date")
        if close_date:
            # Handle timezone
            if hasattr(close_date, 'tzinfo') and close_date.tzinfo is not None:
                close_date = close_date.replace(tzinfo=None)
            try:
                if close_date >= cutoff_date:
                    filtered_closed.append(l)
            except TypeError as e:
                print(f"    TypeError comparing dates: {e}")
                print(f"    close_date={close_date}, cutoff={cutoff_date}")
    
    print(f"  Closed after date filter: {len(filtered_closed)}/{len(closed_listings)}")
    
    # Filter new listings by list_date
    active_listings = [p for p in extracted if p.get("status") == "Active"]
    new_listings = []
    for l in active_listings:
        list_date = l.get("list_date")
        if list_date:
            if hasattr(list_date, 'tzinfo') and list_date.tzinfo is not None:
                list_date = list_date.replace(tzinfo=None)
            try:
                if list_date >= cutoff_date:
                    new_listings.append(l)
            except TypeError as e:
                print(f"    TypeError comparing list dates: {e}")
    
    print(f"  New listings (listed in period): {len(new_listings)}/{len(active_listings)}")
    
    # Step 6: Calculate metrics
    print("\n📈 STEP 6: Calculating metrics...")
    
    def median(values):
        values = [v for v in values if v is not None]
        if not values:
            return None
        values.sort()
        n = len(values)
        mid = n // 2
        return values[mid] if n % 2 else (values[mid-1] + values[mid]) / 2
    
    def average(values):
        values = [v for v in values if v is not None]
        return sum(values) / len(values) if values else None
    
    # Core metrics
    median_close = median([l["close_price"] for l in filtered_closed if l.get("close_price")])
    median_list = median([l["list_price"] for l in active_listings if l.get("list_price")])
    avg_dom = average([l["days_on_market"] for l in filtered_closed if l.get("days_on_market")])
    
    # MOI calculation
    AVG_DAYS_PER_MONTH = 30.437
    if filtered_closed:
        monthly_sales_rate = len(filtered_closed) * (AVG_DAYS_PER_MONTH / lookback_days)
        moi = len(active_listings) / monthly_sales_rate if monthly_sales_rate > 0 else 99.9
    else:
        moi = 99.9
    
    pending_listings = [p for p in extracted if p.get("status") == "Pending"]
    
    print(f"\n  === FINAL METRICS ===")
    print(f"  Active (current inventory): {len(active_listings)}")
    print(f"  New Listings (in period): {len(new_listings)}")
    print(f"  Pending: {len(pending_listings)}")
    print(f"  Closed (in period): {len(filtered_closed)}")
    print(f"  Median Close Price: ${median_close:,.0f}" if median_close else "  Median Close Price: N/A")
    print(f"  Median List Price: ${median_list:,.0f}" if median_list else "  Median List Price: N/A")
    print(f"  Avg DOM: {avg_dom:.1f} days" if avg_dom else "  Avg DOM: N/A")
    print(f"  MOI: {moi:.1f} months")
    
    # Show some close dates for verification
    if filtered_closed:
        print(f"\n  Sample close dates in filtered set:")
        for l in filtered_closed[:5]:
            print(f"    {l.get('mls_id')}: close_date={l.get('close_date')}, close_price=${l.get('close_price'):,}" if l.get('close_price') else f"    {l.get('mls_id')}: close_date={l.get('close_date')}, close_price=None")
    
    # Debug: Check close_price distribution
    close_prices = [l["close_price"] for l in filtered_closed if l.get("close_price")]
    if close_prices:
        print(f"\n  Close price distribution:")
        print(f"    Count: {len(close_prices)}")
        print(f"    Min: ${min(close_prices):,}")
        print(f"    Max: ${max(close_prices):,}")
        print(f"    Median: ${median(close_prices):,.0f}")
        
        # Check for suspiciously low values
        low_prices = [p for p in close_prices if p < 100000]
        print(f"    Prices < $100k: {len(low_prices)}")
    
    return {
        "active": len(active_listings),
        "new_listings": len(new_listings),
        "pending": len(pending_listings),
        "closed": len(filtered_closed),
        "median_close": median_close,
        "median_list": median_list,
        "avg_dom": avg_dom,
        "moi": moi
    }


def test_raw_api():
    """Test raw API response to see what we're getting"""
    print("=" * 80)
    print("RAW API TEST")
    print("=" * 80)
    
    # Check credentials
    username = os.getenv("SIMPLYRETS_USERNAME", "simplyrets")
    print(f"\nCredentials: {username}")
    
    # Simple closed query
    query = {
        "status": "Closed",
        "q": "Irvine",
        "limit": 10
    }
    print(f"\nQuery: {query}")
    
    raw = fetch_properties(query, limit=10)
    print(f"\nGot {len(raw)} properties")
    
    for i, p in enumerate(raw[:10]):
        sales = p.get("sales", {}) or {}
        addr = p.get("address", {}) or {}
        print(f"\n  Property {i+1}:")
        print(f"    mlsId: {p.get('mlsId')}")
        print(f"    status: {p.get('status')}")
        print(f"    listDate: {p.get('listDate')}")
        print(f"    daysOnMarket: {p.get('daysOnMarket')}")
        print(f"    listPrice: ${p.get('listPrice'):,}" if p.get('listPrice') else "    listPrice: None")
        print(f"    sales.closePrice: ${sales.get('closePrice'):,}" if sales.get('closePrice') else "    sales.closePrice: None")
        print(f"    sales.closeDate: {sales.get('closeDate')}")
        print(f"    address.city: {addr.get('city')}")
        print(f"    property.type: {p.get('property', {}).get('type')}")
        print(f"    property.subType: {p.get('property', {}).get('subType')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Irvine", help="City to search")
    parser.add_argument("--lookback", type=int, default=30, help="Lookback days")
    parser.add_argument("--raw", action="store_true", help="Test raw API only")
    args = parser.parse_args()
    
    if args.raw:
        test_raw_api()
    else:
        test_market_snapshot(args.city, args.lookback)

