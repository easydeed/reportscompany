#!/usr/bin/env python3
"""
Quick test of SimplyRETS client.
Usage: python test_simplyrets.py
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from worker.vendors.simplyrets import fetch_properties, build_market_snapshot_params

def test_fetch():
    print("\nTesting SimplyRETS Client...")
    print("=" * 60)
    
    # Test 1: Simple query with limit
    print("\nTest 1: Fetch properties in Houston (limit 20)")
    params = {"q": "Houston", "status": "Active", "limit": 20}
    try:
        results = fetch_properties(params, limit=20)
        print(f"   SUCCESS: Fetched {len(results)} properties")
        if results:
            first = results[0]
            print(f"   Sample address: {first.get('address', {}).get('full', 'N/A')}")
            print(f"   Sample price: ${first.get('listPrice', 'N/A'):,}" if isinstance(first.get('listPrice'), (int, float)) else f"   Sample price: {first.get('listPrice', 'N/A')}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Query with status filter
    print("\nTest 2: Fetch properties in New York (Active status, limit 30)")
    params = {"q": "New York", "status": "Active", "limit": 30}
    try:
        results = fetch_properties(params, limit=30)
        print(f"   SUCCESS: Fetched {len(results)} properties")
        if results:
            # Count by status
            statuses = {}
            for prop in results:
                status = prop.get('status', 'Unknown')
                statuses[status] = statuses.get(status, 0) + 1
            print(f"   By status: {statuses}")
            # Show price range
            prices = [p.get('listPrice') for p in results if p.get('listPrice')]
            if prices:
                print(f"   Price range: ${min(prices):,} - ${max(prices):,}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Tests complete!\n")

if __name__ == "__main__":
    test_fetch()

