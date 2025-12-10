#!/usr/bin/env python3
"""
Local Report Testing Script - Test all report types without deploying.

Usage:
    cd apps/worker
    python ../../scripts/test_all_reports.py --city "La Verne" --lookback 30
    python ../../scripts/test_all_reports.py --zips 91750 --lookback 30
    python ../../scripts/test_all_reports.py --city "La Verne" --report new_listings
    python ../../scripts/test_all_reports.py --all  # Test all report types

This script:
1. Queries SimplyRETS API with the same params as production
2. Runs data through our extractors and report builders
3. Shows detailed analysis of what's filtered and why
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List

# Add worker source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'worker', 'src'))

# Set credentials if not already set
if not os.getenv('SIMPLYRETS_USERNAME'):
    os.environ['SIMPLYRETS_USERNAME'] = 'info_456z6zv2'
    os.environ['SIMPLYRETS_PASSWORD'] = 'lm0182gh3pu6f827'

from worker.vendors.simplyrets import fetch_properties
from worker.query_builders import (
    build_market_snapshot, build_market_snapshot_closed, build_market_snapshot_pending,
    build_new_listings, build_inventory_by_zip, build_closed, build_price_bands, build_open_houses
)
from worker.compute.extract import PropertyDataExtractor
from worker.compute.validate import filter_valid
from worker.report_builders import build_result_json

# Report type configurations
REPORT_TYPES = {
    'market_snapshot': {
        'name': 'Market Snapshot',
        'queries': ['active', 'closed', 'pending'],
        'date_field': 'close_date',
        'filter_status': 'Closed'
    },
    'new_listings': {
        'name': 'New Listings',
        'queries': ['new_listings'],
        'date_field': 'list_date',
        'filter_status': 'Active'
    },
    'inventory': {
        'name': 'Inventory',
        'queries': ['inventory'],
        'date_field': 'list_date',
        'filter_status': 'Active'
    },
    'closed': {
        'name': 'Closed Sales',
        'queries': ['closed'],
        'date_field': 'close_date',
        'filter_status': 'Closed'
    },
    'price_bands': {
        'name': 'Price Bands',
        'queries': ['price_bands'],
        'date_field': None,  # No date filtering
        'filter_status': 'Active'
    },
    'new_listings_gallery': {
        'name': 'New Listings Gallery',
        'queries': ['new_listings'],
        'date_field': 'list_date',
        'filter_status': 'Active'
    },
    'featured_listings': {
        'name': 'Featured Listings',
        'queries': ['new_listings'],
        'date_field': None,  # No date filtering, just top 4 by price
        'filter_status': 'Active'
    },
    'open_houses': {
        'name': 'Open Houses',
        'queries': ['open_houses'],
        'date_field': None,
        'filter_status': 'Active'
    }
}


def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_subheader(text: str):
    print(f"\n--- {text} ---")


def analyze_dates(listings: List[Dict], date_field: str, lookback_days: int) -> Dict:
    """Analyze date distribution in listings."""
    cutoff = datetime.now() - timedelta(days=lookback_days)
    
    within_period = 0
    outside_period = 0
    no_date = 0
    dates = []
    
    for l in listings:
        date_val = l.get(date_field)
        if date_val:
            try:
                if hasattr(date_val, 'tzinfo') and date_val.tzinfo:
                    date_val = date_val.replace(tzinfo=None)
                dates.append((date_val, l.get('street_address', 'Unknown')))
                if date_val >= cutoff:
                    within_period += 1
                else:
                    outside_period += 1
            except:
                no_date += 1
        else:
            no_date += 1
    
    return {
        'within_period': within_period,
        'outside_period': outside_period,
        'no_date': no_date,
        'dates': sorted(dates)
    }


def fetch_report_data(report_type: str, params: Dict) -> List[Dict]:
    """Fetch raw data from API for a report type."""
    config = REPORT_TYPES[report_type]
    
    all_raw = []
    for query_type in config['queries']:
        if query_type == 'active':
            query = build_market_snapshot(params)
        elif query_type == 'closed':
            query = build_market_snapshot_closed(params)
        elif query_type == 'pending':
            query = build_market_snapshot_pending(params)
        elif query_type == 'new_listings':
            query = build_new_listings(params)
        elif query_type == 'inventory':
            query = build_inventory_by_zip(params)
        elif query_type == 'price_bands':
            query = build_price_bands(params)
        elif query_type == 'open_houses':
            query = build_open_houses(params)
        else:
            query = build_new_listings(params)
        
        print(f"  Query ({query_type}): {query}")
        raw = fetch_properties(query, limit=500)
        print(f"  → Returned: {len(raw)} properties")
        all_raw.extend(raw)
    
    return all_raw


def test_report(report_type: str, params: Dict, verbose: bool = True):
    """Test a single report type."""
    config = REPORT_TYPES[report_type]
    lookback_days = params.get('lookback_days', 30)
    city = params.get('city', 'Unknown')
    zips = params.get('zips', [])
    
    print_header(f"Testing: {config['name']} ({report_type})")
    print(f"Location: {city or ', '.join(zips)}")
    print(f"Lookback: {lookback_days} days")
    
    # 1. Fetch raw data
    print_subheader("Step 1: API Query")
    raw = fetch_report_data(report_type, params)
    print(f"\nTotal raw from API: {len(raw)}")
    
    # 2. Extract and validate
    print_subheader("Step 2: Extract & Validate")
    extracted = PropertyDataExtractor(raw).run()
    clean = filter_valid(extracted)
    print(f"Extracted: {len(extracted)} → Valid: {len(clean)}")
    
    # 3. Analyze by status
    print_subheader("Step 3: Status Breakdown")
    by_status = {}
    for l in clean:
        status = l.get('status', 'Unknown')
        by_status[status] = by_status.get(status, 0) + 1
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")
    
    # 4. Date analysis (if applicable)
    if config['date_field']:
        print_subheader(f"Step 4: Date Analysis ({config['date_field']})")
        
        # Filter to relevant status
        relevant = [l for l in clean if l.get('status') == config['filter_status']]
        print(f"Relevant listings ({config['filter_status']}): {len(relevant)}")
        
        analysis = analyze_dates(relevant, config['date_field'], lookback_days)
        print(f"\n  ✅ Within {lookback_days} days: {analysis['within_period']}")
        print(f"  ❌ Outside {lookback_days} days: {analysis['outside_period']}")
        print(f"  ⚠️  No date: {analysis['no_date']}")
        
        if analysis['outside_period'] > 0 and verbose:
            print(f"\n  OLDEST 5 (should be filtered out):")
            for dt, addr in analysis['dates'][:5]:
                days_ago = (datetime.now() - dt).days
                print(f"    {dt.date()} ({days_ago} days ago) - {addr}")
        
        if analysis['within_period'] > 0 and verbose:
            print(f"\n  NEWEST 5 (should be included):")
            for dt, addr in analysis['dates'][-5:]:
                days_ago = (datetime.now() - dt).days
                print(f"    {dt.date()} ({days_ago} days ago) - {addr}")
    
    # 5. Run report builder
    print_subheader("Step 5: Report Builder Output")
    context = {
        'city': city or (zips[0] if zips else 'Unknown'),
        'lookback_days': lookback_days
    }
    
    try:
        result = build_result_json(report_type, clean, context)
        
        # Show counts
        counts = result.get('counts', {})
        print(f"\nFinal Counts:")
        for k, v in counts.items():
            print(f"  {k}: {v}")
        
        # Show metrics
        metrics = result.get('metrics', {})
        if metrics:
            print(f"\nMetrics:")
            for k, v in metrics.items():
                if isinstance(v, float):
                    print(f"  {k}: {v:,.2f}")
                else:
                    print(f"  {k}: {v}")
        
        # Show sample count
        sample = result.get('listings_sample', [])
        print(f"\nListings in output: {len(sample)}")
        
        # Verify date filtering worked
        if config['date_field'] and sample:
            cutoff = datetime.now() - timedelta(days=lookback_days)
            violations = 0
            for l in sample:
                dt = l.get(config['date_field'])
                if dt:
                    if hasattr(dt, 'tzinfo') and dt.tzinfo:
                        dt = dt.replace(tzinfo=None)
                    if dt < cutoff:
                        violations += 1
            
            if violations > 0:
                print(f"\n  ⚠️  WARNING: {violations} listings in output have {config['date_field']} outside period!")
            else:
                print(f"\n  ✅ All listings in output are within {lookback_days}-day period")
    
    except Exception as e:
        print(f"\n  ❌ Error building report: {e}")
        import traceback
        traceback.print_exc()
    
    return result if 'result' in dir() else None


def main():
    parser = argparse.ArgumentParser(description='Test report types locally')
    parser.add_argument('--city', type=str, help='City name (e.g., "La Verne")')
    parser.add_argument('--zips', type=str, nargs='+', help='ZIP codes (e.g., 91750 91752)')
    parser.add_argument('--lookback', type=int, default=30, help='Lookback days (default: 30)')
    parser.add_argument('--report', type=str, choices=list(REPORT_TYPES.keys()), 
                        help='Specific report type to test')
    parser.add_argument('--all', action='store_true', help='Test all report types')
    parser.add_argument('--quiet', action='store_true', help='Less verbose output')
    
    args = parser.parse_args()
    
    if not args.city and not args.zips:
        print("Error: Must provide --city or --zips")
        parser.print_help()
        sys.exit(1)
    
    params = {
        'lookback_days': args.lookback,
    }
    if args.city:
        params['city'] = args.city
    if args.zips:
        params['zips'] = args.zips
    
    print("\n" + "="*60)
    print("  TRENDYREPORTS LOCAL TESTING")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Location: {args.city or ', '.join(args.zips or [])}")
    print(f"Lookback: {args.lookback} days")
    
    if args.all:
        # Test all report types
        results = {}
        for rt in REPORT_TYPES.keys():
            results[rt] = test_report(rt, params, verbose=not args.quiet)
        
        # Summary
        print_header("SUMMARY")
        for rt, config in REPORT_TYPES.items():
            status = "✅" if results.get(rt) else "❌"
            print(f"  {status} {config['name']}")
    
    elif args.report:
        test_report(args.report, params, verbose=not args.quiet)
    
    else:
        # Default: test new_listings as it's the most common issue
        test_report('new_listings', params, verbose=not args.quiet)


if __name__ == '__main__':
    main()

