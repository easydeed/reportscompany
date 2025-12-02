#!/usr/bin/env python3
"""
SimplyRETS API Test Script
Direct testing of API parameters without deployment
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from base64 import b64encode

# SimplyRETS credentials (from ENV_TEMPLATE.md)
SIMPLYRETS_USERNAME = os.getenv("SIMPLYRETS_USERNAME", "info_456z6zv2")
SIMPLYRETS_PASSWORD = os.getenv("SIMPLYRETS_PASSWORD", "lm0182gh3pu6f827")

BASE_URL = "https://api.simplyrets.com/properties"

def get_auth_header():
    """Generate Basic Auth header"""
    credentials = f"{SIMPLYRETS_USERNAME}:{SIMPLYRETS_PASSWORD}"
    encoded = b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def test_query(params: dict, description: str = ""):
    """Test a SimplyRETS query and print results"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(
            BASE_URL,
            params=params,
            headers=get_auth_header(),
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Results: {len(data)} properties")
            
            if data:
                # Show sample of first property
                first = data[0]
                print(f"\nSample Property:")
                print(f"  - Address: {first.get('address', {}).get('full', 'N/A')}")
                print(f"  - City: {first.get('address', {}).get('city', 'N/A')}")
                print(f"  - Status: {first.get('mls', {}).get('status', 'N/A')}")
                print(f"  - Price: ${first.get('listPrice', 0):,}")
                print(f"  - Type: {first.get('property', {}).get('type', 'N/A')}")
                print(f"  - SubType: {first.get('property', {}).get('subType', 'N/A')}")
                print(f"  - Beds: {first.get('property', {}).get('bedrooms', 'N/A')}")
                print(f"  - DOM: {first.get('mls', {}).get('daysOnMarket', 'N/A')}")
                
                # Count by status
                status_counts = {}
                type_counts = {}
                subtype_counts = {}
                for prop in data:
                    status = prop.get('mls', {}).get('status', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    ptype = prop.get('property', {}).get('type', 'Unknown')
                    type_counts[ptype] = type_counts.get(ptype, 0) + 1
                    
                    subtype = prop.get('property', {}).get('subType', 'Unknown')
                    subtype_counts[subtype] = subtype_counts.get(subtype, 0) + 1
                
                print(f"\nStatus Breakdown: {status_counts}")
                print(f"Type Breakdown: {type_counts}")
                print(f"SubType Breakdown (top 5):")
                for st, count in sorted(subtype_counts.items(), key=lambda x: -x[1])[:5]:
                    print(f"  - {st}: {count}")
                    
            return data
        else:
            print(f"Error Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

def get_all_subtypes(city: str = "Irvine", limit: int = 500):
    """Fetch properties and extract all unique subtypes"""
    params = {
        "q": city,
        "status": "Active",
        "limit": limit
    }
    
    response = requests.get(
        BASE_URL,
        params=params,
        headers=get_auth_header(),
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        subtypes = {}
        types = {}
        for prop in data:
            subtype = prop.get('property', {}).get('subType', 'Unknown')
            ptype = prop.get('property', {}).get('type', 'Unknown')
            subtypes[subtype] = subtypes.get(subtype, 0) + 1
            types[ptype] = types.get(ptype, 0) + 1
        
        print("\n" + "="*60)
        print("AVAILABLE TYPES AND SUBTYPES")
        print("="*60)
        print("\nProperty Types:")
        for t, c in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
        print("\nProperty SubTypes:")
        for st, c in sorted(subtypes.items(), key=lambda x: -x[1]):
            print(f"  {st}: {c}")
        return subtypes, types
    return {}, {}

def test_query_builder():
    """Test the query_builders module directly"""
    import sys
    sys.path.insert(0, 'apps/worker/src')
    
    try:
        from worker import query_builders as qb
        
        print("\n" + "="*60)
        print("TESTING QUERY BUILDERS MODULE")
        print("="*60)
        
        # Test market snapshot
        params = {"city": "Irvine", "lookback_days": 30, "filters": {"type": "RES"}}
        active_query = qb.build_market_snapshot(params)
        closed_query = qb.build_market_snapshot_closed(params)
        
        print("\nMarket Snapshot - Active query:")
        print(json.dumps(active_query, indent=2))
        
        print("\nMarket Snapshot - Closed query:")
        print(json.dumps(closed_query, indent=2))
        
        # Test with subtype filter
        params_sfr = {"city": "Irvine", "lookback_days": 30, "filters": {"type": "RES", "subtype": "SingleFamilyResidence"}}
        sfr_query = qb.build_market_snapshot(params_sfr)
        
        print("\nMarket Snapshot - SFR only query:")
        print(json.dumps(sfr_query, indent=2))
        
        return True
    except Exception as e:
        print(f"Error testing query_builders: {e}")
        return False


def main():
    print("SimplyRETS API Test Script")
    print(f"Username: {SIMPLYRETS_USERNAME}")
    print(f"Base URL: {BASE_URL}")
    
    # Date range for tests
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # First, discover all available types and subtypes
    get_all_subtypes("Irvine", 500)
    
    print("\n" + "="*60)
    print("TESTING SEPARATE ACTIVE vs CLOSED QUERIES")
    print("="*60)
    
    # Test 1: ACTIVE ONLY (Market Snapshot - Active listings)
    active_data = test_query({
        "q": "Irvine",
        "status": "Active",
        "type": "RES",
        "mindate": start_date.isoformat(),
        "maxdate": end_date.isoformat(),
        "limit": 100
    }, "MARKET SNAPSHOT - Active RES only")
    
    # Test 2: CLOSED ONLY (Market Snapshot - Closed listings)
    closed_data = test_query({
        "q": "Irvine",
        "status": "Closed",
        "type": "RES",
        "mindate": start_date.isoformat(),
        "maxdate": end_date.isoformat(),
        "limit": 100
    }, "MARKET SNAPSHOT - Closed RES only")
    
    # Show combined metrics
    if active_data and closed_data:
        print("\n" + "="*60)
        print("COMBINED METRICS (Active + Closed)")
        print("="*60)
        print(f"Active Listings: {len(active_data)}")
        print(f"Closed Sales: {len(closed_data)}")
        
        # Calculate median prices
        active_prices = [p.get('listPrice', 0) for p in active_data if p.get('listPrice')]
        closed_prices = [p.get('listPrice', 0) for p in closed_data if p.get('listPrice')]
        
        if active_prices:
            active_prices.sort()
            median_active = active_prices[len(active_prices)//2]
            print(f"Median Active List Price: ${median_active:,}")
        
        if closed_prices:
            closed_prices.sort()
            median_closed = closed_prices[len(closed_prices)//2]
            print(f"Median Closed List Price: ${median_closed:,}")
    
    print("\n" + "="*60)
    print("TESTING SUBTYPE FILTERS")
    print("="*60)
    
    # Test 3: Single Family Residence
    test_query({
        "q": "Irvine",
        "status": "Active",
        "type": "RES",
        "subtype": "SingleFamilyResidence",
        "mindate": start_date.isoformat(),
        "maxdate": end_date.isoformat(),
        "limit": 50
    }, "SFR - Single Family Residence")
    
    # Test 4: Condominium
    test_query({
        "q": "Irvine",
        "status": "Active",
        "type": "RES",
        "subtype": "Condominium",
        "mindate": start_date.isoformat(),
        "maxdate": end_date.isoformat(),
        "limit": 50
    }, "CONDO - Condominium")
    
    # Test 5: Townhouse
    test_query({
        "q": "Irvine",
        "status": "Active",
        "type": "RES",
        "subtype": "Townhouse",
        "mindate": start_date.isoformat(),
        "maxdate": end_date.isoformat(),
        "limit": 50
    }, "TOWNHOUSE - Townhouse")
    
    # Test the query_builders module
    test_query_builder()

if __name__ == "__main__":
    main()

