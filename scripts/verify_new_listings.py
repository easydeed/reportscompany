#!/usr/bin/env python3
"""
Verify New Listings count for a city.
Usage: python scripts/verify_new_listings.py --city Irvine --days 60
"""

import requests
from datetime import datetime, timedelta
import argparse

# SimplyRETS credentials
USERNAME = 'info_456z6zv2'
PASSWORD = 'lm0182gh3pu6f827'
BASE_URL = 'https://api.simplyrets.com/properties'


def fetch_all_listings(params: dict) -> list:
    """Fetch all listings with pagination."""
    all_listings = []
    offset = 0
    limit = 500
    
    while True:
        params['limit'] = limit
        params['offset'] = offset
        
        response = requests.get(
            BASE_URL,
            params=params,
            auth=(USERNAME, PASSWORD),
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            break
        
        listings = response.json()
        all_listings.extend(listings)
        
        print(f"  Fetched {len(listings)} listings (offset={offset})")
        
        if len(listings) < limit:
            break
        
        offset += limit
    
    return all_listings


def main():
    parser = argparse.ArgumentParser(description='Verify New Listings count')
    parser.add_argument('--city', default='Irvine', help='City to search')
    parser.add_argument('--days', type=int, default=60, help='Lookback days')
    args = parser.parse_args()
    
    city = args.city
    lookback_days = args.days
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    print("=" * 60)
    print(f"VERIFYING NEW LISTINGS FOR: {city.upper()}")
    print("=" * 60)
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Lookback: {lookback_days} days")
    print()
    
    # Query parameters
    params = {
        'q': city,
        'status': 'Active',
        'type': 'RES',  # Residential only (exclude rentals)
        'mindate': start_date.strftime('%Y-%m-%d'),
        'maxdate': end_date.strftime('%Y-%m-%d'),
    }
    
    print(f"Query: {params}")
    print()
    print("Fetching from SimplyRETS API...")
    
    # Fetch all listings
    all_listings = fetch_all_listings(params)
    
    print()
    print(f"Total from API: {len(all_listings)} listings")
    
    # Filter to exact city match
    city_lower = city.lower().strip()
    city_filtered = [
        l for l in all_listings 
        if (l.get('address', {}).get('city') or '').lower().strip() == city_lower
    ]
    
    print(f"After city filter ({city} only): {len(city_filtered)} listings")
    
    # Show cities breakdown
    cities = {}
    for l in all_listings:
        c = l.get('address', {}).get('city', 'Unknown')
        cities[c] = cities.get(c, 0) + 1
    
    print()
    print("Cities in API results:")
    for c, count in sorted(cities.items(), key=lambda x: -x[1]):
        marker = " <-- TARGET" if c.lower() == city_lower else ""
        print(f"  {c}: {count}{marker}")
    
    # Property type breakdown
    print()
    print("Property subtypes in results:")
    subtypes = {}
    for l in city_filtered:
        st = l.get('property', {}).get('subType', 'Unknown')
        subtypes[st] = subtypes.get(st, 0) + 1
    for st, count in sorted(subtypes.items(), key=lambda x: -x[1]):
        print(f"  {st}: {count}")
    
    # Price range
    prices = [l.get('listPrice', 0) for l in city_filtered if l.get('listPrice')]
    if prices:
        print()
        print("Price range:")
        print(f"  Min: ${min(prices):,}")
        print(f"  Max: ${max(prices):,}")
        print(f"  Median: ${sorted(prices)[len(prices)//2]:,}")
    
    print()
    print("=" * 60)
    print(f"FINAL COUNT: {len(city_filtered)} new listings in {city} (last {lookback_days} days)")
    print("=" * 60)


if __name__ == '__main__':
    main()

