# SimplyRETS Real Estate Report System - Complete Technical Guide

**Document Version**: 1.0  
**Last Updated**: October 31, 2025  
**Author**: System Documentation Team  
**Status**: ✅ Production System - Complete Reference

---

## 📖 Table of Contents

### Part 1: API Integration
1. [SimplyRETS API Overview](#1-simplyrets-api-overview)
2. [Authentication & Configuration](#2-authentication--configuration)
3. [API Endpoints by Report Type](#3-api-endpoints-by-report-type)
4. [Request Parameters Reference](#4-request-parameters-reference)
5. [Response Data Structures](#5-response-data-structures)
6. [Rate Limiting & Error Handling](#6-rate-limiting--error-handling)

### Part 2: Data Processing Pipeline
7. [Data Extraction & Transformation](#7-data-extraction--transformation)
8. [Calculations & Aggregations](#8-calculations--aggregations)
9. [Data Caching Strategy](#9-data-caching-strategy)

### Part 3: Report Generation System
10. [Report Architecture Overview](#10-report-architecture-overview)
11. [Market Snapshot Report](#11-market-snapshot-report)
12. [New Listings Report](#12-new-listings-report)
13. [Inventory Report](#13-inventory-report)
14. [Closed Listings Report](#14-closed-listings-report)
15. [Price Bands Report](#15-price-bands-report)
16. [Open Houses Report](#16-open-houses-report)

### Part 4: Social Graphics System
17. [Social Graphics Architecture](#17-social-graphics-architecture)
18. [Market Snapshot Social Template (V4)](#18-market-snapshot-social-template-v4)
19. [New Listings Social Template](#19-new-listings-social-template)
20. [Price Bands Social Template](#20-price-bands-social-template)
21. [Inventory Social Template](#21-inventory-social-template)
22. [Closed Listings Social Template](#22-closed-listings-social-template)
23. [Theme System](#23-theme-system)
24. [html2canvas Export System](#24-html2canvas-export-system)

### Part 5: PDF Generation
25. [PDF Export Architecture](#25-pdf-export-architecture)
26. [Print Styling & Optimization](#26-print-styling--optimization)

### Part 6: Database & Storage
27. [Database Schema](#27-database-schema)
28. [File Storage Structure](#28-file-storage-structure)

### Part 7: Deployment & Operations
29. [Environment Configuration](#29-environment-configuration)
30. [Deployment Procedures](#30-deployment-procedures)
31. [Monitoring & Maintenance](#31-monitoring--maintenance)
32. [Troubleshooting Guide](#32-troubleshooting-guide)

---

## Part 1: API Integration

---

## 1. SimplyRETS API Overview

### 1.1 What is SimplyRETS?

SimplyRETS is a real estate API platform that provides standardized access to MLS (Multiple Listing Service) data across different markets. It normalizes data from various MLS systems into a unified API format.

**Official Documentation**: https://docs.simplyrets.com/api/index.html  
**API Base URL**: `https://api.simplyrets.com/`  
**API Version**: v0.1 (current production)

### 1.2 Key Concepts

#### MLS IDs
- Each market/region has a unique MLS identifier
- Example MLS IDs:
  - `crmls` - California Regional MLS (Southern California)
  - `sdmls` - San Diego MLS
  - `stellar` - Stellar MLS (Florida)

#### Property Status Types
- `Active` - Currently on the market
- `Pending` - Under contract, not yet closed
- `Closed` - Sale completed
- `Temp Off Market` - Temporarily off market
- `Expired` - Listing expired
- `Withdrawn` - Withdrawn by seller

#### Property Types
- `RES` - Residential (single-family homes)
- `CND` - Condominium
- `MUL` - Multi-family
- `LND` - Land
- `COM` - Commercial

### 1.3 API Features We Use

| Feature | Purpose | Reports Using It |
|---------|---------|------------------|
| **Property Search** | Query listings by status, date, location | All reports |
| **Filters** | Filter by price, beds, baths, sqft | Price Bands, Inventory |
| **Sorting** | Order results by date, price, DOM | New Listings, Closed |
| **Pagination** | Handle large result sets | All reports |
| **Geolocation** | Filter by city, zip, polygon | Market Snapshot, City reports |
| **Open House Data** | Retrieve scheduled open houses | Open Houses report |

---

## 2. Authentication & Configuration

### 2.1 Authentication Method

SimplyRETS uses **HTTP Basic Authentication**.

```bash
# Authentication Format
Authorization: Basic base64(username:password)

# Example (credentials are encoded)
Authorization: Basic c2ltcGx5cmV0czpzaW1wbHlyZXRz
```

### 2.2 Test vs Production Credentials

#### Test Credentials (Demo Data)
```
Username: simplyrets
Password: simplyrets
MLS: test (returns demo data)
```

#### Production Credentials (Live Data)
```bash
Username: [YOUR_CLIENT_ID]
Password: [YOUR_API_KEY]
MLS: crmls (or your specific MLS)
```

**🔒 Security Note**: Production credentials are stored in environment variables and never committed to version control.

### 2.3 Configuration File Structure

**File**: `vcard-new/reports/config/.env` (NOT in version control)

```bash
# SimplyRETS API Configuration
SIMPLYRETS_USERNAME=your_client_id_here
SIMPLYRETS_PASSWORD=your_api_key_here
SIMPLYRETS_MLS=crmls

# API Base URL
SIMPLYRETS_BASE_URL=https://api.simplyrets.com

# Rate Limiting
SIMPLYRETS_RATE_LIMIT=60
SIMPLYRETS_BURST_LIMIT=10

# Caching
CACHE_DURATION_SECONDS=3600
CACHE_ENABLED=true

# Database Configuration
DB_HOST=localhost
DB_NAME=pct_reports
DB_USER=pct_reports_user
DB_PASS=secure_password_here

# Report Configuration
PCT_REPORTS_ENABLED=1
DEFAULT_LOOKBACK_DAYS=30
MAX_PROPERTIES_PER_REPORT=1000
```

### 2.4 Python Configuration Loader

**File**: `vcard-new/reports/core-system/config.py`

```python
import os
from dotenv import load_dotenv
from base64 import b64encode

# Load environment variables
load_dotenv('../config/.env')

class SimplyRETSConfig:
    """SimplyRETS API Configuration"""
    
    def __init__(self):
        self.username = os.getenv('SIMPLYRETS_USERNAME', 'simplyrets')
        self.password = os.getenv('SIMPLYRETS_PASSWORD', 'simplyrets')
        self.mls = os.getenv('SIMPLYRETS_MLS', 'test')
        self.base_url = os.getenv('SIMPLYRETS_BASE_URL', 'https://api.simplyrets.com')
        self.rate_limit = int(os.getenv('SIMPLYRETS_RATE_LIMIT', '60'))
        self.burst_limit = int(os.getenv('SIMPLYRETS_BURST_LIMIT', '10'))
    
    @property
    def auth_header(self):
        """Generate Basic Auth header"""
        credentials = f"{self.username}:{self.password}"
        encoded = b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    @property
    def headers(self):
        """Generate request headers"""
        return {
            'Authorization': self.auth_header,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

# Global configuration instance
config = SimplyRETSConfig()
```

---

## 3. API Endpoints by Report Type

### 3.1 Base Endpoint Structure

```
https://api.simplyrets.com/properties
```

All property queries use this single endpoint with different query parameters.

### 3.2 Market Snapshot Report

**Endpoint**: `/properties`

**Purpose**: Get overview of market activity for a specific city/area over the past N days.

**Query Parameters**:
```python
{
    'q': 'San Diego',           # City name
    'status': 'Active,Pending,Closed',  # Multiple statuses
    'mindate': '2024-10-01',    # Start date (YYYY-MM-DD)
    'maxdate': '2024-10-31',    # End date (YYYY-MM-DD)
    'limit': 1000,              # Max results per page
    'offset': 0,                # Pagination offset
    'sort': '-listDate'         # Sort by list date descending
}
```

**Full API Call Example**:
```bash
curl -X GET "https://api.simplyrets.com/properties?\
q=San%20Diego&\
status=Active,Pending,Closed&\
mindate=2024-10-01&\
maxdate=2024-10-31&\
limit=1000&\
offset=0&\
sort=-listDate" \
-H "Authorization: Basic c2ltcGx5cmV0czpzaW1wbHlyZXRz" \
-H "Content-Type: application/json"
```

**Python Implementation**:
```python
import requests
from datetime import datetime, timedelta
from config import config

def get_market_snapshot_data(city, lookback_days=30):
    """
    Fetch market snapshot data for a city.
    
    Args:
        city (str): City name (e.g., 'San Diego')
        lookback_days (int): Number of days to look back
    
    Returns:
        list: Array of property objects
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    # Build query parameters
    params = {
        'q': city,
        'status': 'Active,Pending,Closed',
        'mindate': start_date.strftime('%Y-%m-%d'),
        'maxdate': end_date.strftime('%Y-%m-%d'),
        'limit': 1000,
        'offset': 0,
        'sort': '-listDate'
    }
    
    # Make API request
    response = requests.get(
        f"{config.base_url}/properties",
        params=params,
        headers=config.headers,
        timeout=30
    )
    
    # Check response
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# Usage
properties = get_market_snapshot_data('San Diego', 30)
print(f"Retrieved {len(properties)} properties")
```

**Expected Response Structure**:
```json
[
  {
    "mlsId": 12345678,
    "listDate": "2024-10-15T00:00:00.000Z",
    "listPrice": 950000,
    "address": {
      "streetNumber": "123",
      "streetName": "Main",
      "streetSuffix": "St",
      "unit": null,
      "city": "San Diego",
      "state": "CA",
      "postalCode": "92101",
      "full": "123 Main St, San Diego, CA 92101"
    },
    "property": {
      "bedrooms": 3,
      "bathrooms": 2.5,
      "area": 1850,
      "type": "RES",
      "subType": "Single Family Residence",
      "lotSize": 6500,
      "yearBuilt": 2005
    },
    "geo": {
      "lat": 32.7157,
      "lng": -117.1611
    },
    "status": "Active",
    "daysOnMarket": 15,
    "photos": [
      "https://photos.simplyrets.com/example1.jpg"
    ],
    "agent": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com",
      "contact": "(619) 555-1234"
    },
    "office": {
      "name": "Example Realty",
      "brokerid": "BR12345",
      "contact": "(619) 555-9999"
    },
    "mls": {
      "status": "Active",
      "area": "Downtown",
      "daysOnMarket": 15,
      "originatingSystemName": "CRMLS"
    }
  }
  // ... more properties
]
```

### 3.3 New Listings Report

**Endpoint**: `/properties`

**Purpose**: Get all newly listed properties in a city within the last N days.

**Query Parameters**:
```python
{
    'q': 'San Diego',
    'status': 'Active',         # Only active listings
    'mindate': '2024-10-24',    # Recent date (7 days ago)
    'maxdate': '2024-10-31',    # Today
    'limit': 500,
    'offset': 0,
    'sort': '-listDate'         # Newest first
}
```

**Python Implementation**:
```python
def get_new_listings(city, days=7):
    """
    Get newly listed properties.
    
    Args:
        city (str): City name
        days (int): How many days back to look for new listings
    
    Returns:
        list: New listings sorted by list date (newest first)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    params = {
        'q': city,
        'status': 'Active',
        'mindate': start_date.strftime('%Y-%m-%d'),
        'maxdate': end_date.strftime('%Y-%m-%d'),
        'limit': 500,
        'offset': 0,
        'sort': '-listDate'
    }
    
    response = requests.get(
        f"{config.base_url}/properties",
        params=params,
        headers=config.headers,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code}")

# Usage
new_listings = get_new_listings('San Diego', 7)
print(f"Found {len(new_listings)} new listings")

# Sort by list date
sorted_listings = sorted(new_listings, key=lambda x: x['listDate'], reverse=True)
```

### 3.4 Inventory Report (Active Listings)

**Endpoint**: `/properties`

**Purpose**: Get all currently active inventory in a city.

**Query Parameters**:
```python
{
    'q': 'San Diego',
    'status': 'Active',         # Only active listings
    'limit': 1000,
    'offset': 0,
    'sort': 'daysOnMarket'      # Lowest DOM first (newest listings)
}
```

**Python Implementation**:
```python
def get_inventory_listings(city):
    """
    Get all active inventory for a city.
    
    Args:
        city (str): City name
    
    Returns:
        list: All active listings sorted by DOM
    """
    all_listings = []
    offset = 0
    limit = 500
    
    while True:
        params = {
            'q': city,
            'status': 'Active',
            'limit': limit,
            'offset': offset,
            'sort': 'daysOnMarket'
        }
        
        response = requests.get(
            f"{config.base_url}/properties",
            params=params,
            headers=config.headers,
            timeout=30
        )
        
        if response.status_code != 200:
            break
        
        batch = response.json()
        if not batch:
            break
        
        all_listings.extend(batch)
        
        # Check if we got fewer results than limit (last page)
        if len(batch) < limit:
            break
        
        offset += limit
    
    return all_listings

# Usage
inventory = get_inventory_listings('San Diego')
print(f"Total active inventory: {len(inventory)} listings")

# Calculate metrics
total_active = len(inventory)
median_dom = sorted([p['daysOnMarket'] for p in inventory])[len(inventory)//2]
median_price = sorted([p['listPrice'] for p in inventory])[len(inventory)//2]

print(f"Median DOM: {median_dom} days")
print(f"Median Price: ${median_price:,}")
```

### 3.5 Closed Listings Report

**Endpoint**: `/properties`

**Purpose**: Get recently closed sales in a city.

**Query Parameters**:
```python
{
    'q': 'San Diego',
    'status': 'Closed',         # Only closed sales
    'mindate': '2024-10-01',    # Recent closings (30 days)
    'maxdate': '2024-10-31',
    'limit': 1000,
    'offset': 0,
    'sort': '-closeDate'        # Most recent closings first
}
```

**Python Implementation**:
```python
def get_closed_listings(city, lookback_days=30):
    """
    Get recently closed sales.
    
    Args:
        city (str): City name
        lookback_days (int): How many days back to look
    
    Returns:
        list: Closed listings sorted by close date
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    params = {
        'q': city,
        'status': 'Closed',
        'mindate': start_date.strftime('%Y-%m-%d'),
        'maxdate': end_date.strftime('%Y-%m-%d'),
        'limit': 1000,
        'offset': 0,
        'sort': '-closeDate'
    }
    
    response = requests.get(
        f"{config.base_url}/properties",
        params=params,
        headers=config.headers,
        timeout=30
    )
    
    if response.status_code == 200:
        closings = response.json()
        
        # Calculate metrics
        if closings:
            total_closed = len(closings)
            median_price = sorted([p.get('closePrice', 0) for p in closings])[len(closings)//2]
            avg_dom = sum([p.get('daysOnMarket', 0) for p in closings]) / len(closings)
            
            # Calculate close-to-list ratio
            close_to_list_ratios = []
            for p in closings:
                if p.get('listPrice') and p.get('closePrice'):
                    ratio = (p['closePrice'] / p['listPrice']) * 100
                    close_to_list_ratios.append(ratio)
            
            avg_ctl_ratio = sum(close_to_list_ratios) / len(close_to_list_ratios) if close_to_list_ratios else 0
            
            return {
                'listings': closings,
                'metrics': {
                    'total_closed': total_closed,
                    'median_price': median_price,
                    'avg_dom': round(avg_dom, 1),
                    'close_to_list_ratio': round(avg_ctl_ratio, 1)
                }
            }
        
        return {'listings': [], 'metrics': {}}
    else:
        raise Exception(f"API Error: {response.status_code}")

# Usage
closed_data = get_closed_listings('San Diego', 30)
print(f"Total closings: {closed_data['metrics']['total_closed']}")
print(f"Median sale price: ${closed_data['metrics']['median_price']:,}")
print(f"Avg DOM: {closed_data['metrics']['avg_dom']} days")
print(f"Close/List ratio: {closed_data['metrics']['close_to_list_ratio']}%")
```

### 3.6 Price Bands Report

**Endpoint**: `/properties`

**Purpose**: Segment market into price ranges and analyze each band.

**Query Strategy**: Multiple API calls with different price filters.

**Python Implementation**:
```python
def get_price_bands_data(city, lookback_days=30):
    """
    Get active listings segmented by price bands.
    
    Args:
        city (str): City name
        lookback_days (int): For trend comparison
    
    Returns:
        dict: Price band analysis
    """
    # Define price bands
    price_bands = [
        {'name': 'Under $500K', 'min': 0, 'max': 499999},
        {'name': '$500K - $750K', 'min': 500000, 'max': 749999},
        {'name': '$750K - $1M', 'min': 750000, 'max': 999999},
        {'name': '$1M - $1.5M', 'min': 1000000, 'max': 1499999},
        {'name': '$1.5M - $2M', 'min': 1500000, 'max': 1999999},
        {'name': '$2M - $3M', 'min': 2000000, 'max': 2999999},
        {'name': 'Over $3M', 'min': 3000000, 'max': 999999999}
    ]
    
    results = []
    total_count = 0
    
    for band in price_bands:
        params = {
            'q': city,
            'status': 'Active',
            'minprice': band['min'],
            'maxprice': band['max'],
            'limit': 1000,
            'offset': 0
        }
        
        response = requests.get(
            f"{config.base_url}/properties",
            params=params,
            headers=config.headers,
            timeout=30
        )
        
        if response.status_code == 200:
            listings = response.json()
            count = len(listings)
            total_count += count
            
            if count > 0:
                # Calculate metrics for this band
                median_price = sorted([p['listPrice'] for p in listings])[count//2]
                avg_dom = sum([p.get('daysOnMarket', 0) for p in listings]) / count
                avg_ppsf = sum([p['listPrice'] / p['property'].get('area', 1) for p in listings if p['property'].get('area')]) / count
                
                # Determine inventory level
                if count >= 100:
                    inventory = 'Very High'
                elif count >= 50:
                    inventory = 'High'
                elif count >= 20:
                    inventory = 'Moderate'
                else:
                    inventory = 'Low'
                
                results.append({
                    'band': band['name'],
                    'count': count,
                    'percent': 0,  # Will calculate after we have total
                    'medianPrice': median_price,
                    'avgDOM': round(avg_dom, 1),
                    'avgPPSF': round(avg_ppsf, 0),
                    'inventory': inventory,
                    'listings': listings
                })
    
    # Calculate percentages
    for band in results:
        band['percent'] = round((band['count'] / total_count) * 100, 1) if total_count > 0 else 0
    
    return {
        'bands': results,
        'total_listings': total_count,
        'city': city
    }

# Usage
price_bands = get_price_bands_data('San Diego', 30)
print(f"Total listings analyzed: {price_bands['total_listings']}")
print(f"Number of price bands: {len(price_bands['bands'])}")

for band in price_bands['bands']:
    print(f"{band['band']}: {band['count']} listings ({band['percent']}%) - Avg DOM: {band['avgDOM']} days")
```

### 3.7 Open Houses Report

**Endpoint**: `/properties`

**Purpose**: Get listings with upcoming open houses.

**Query Parameters**:
```python
{
    'q': 'San Diego',
    'status': 'Active',
    'mindate': '2024-10-28',    # This week
    'maxdate': '2024-11-03',    # End of week
    'limit': 500,
    'offset': 0,
    'features': 'hasOpenHouse'  # Special filter for open houses
}
```

**Python Implementation**:
```python
def get_open_houses(city, week_offset=0):
    """
    Get properties with open houses for a given week.
    
    Args:
        city (str): City name
        week_offset (int): 0 = this week, 1 = next week, etc.
    
    Returns:
        dict: Open house data
    """
    from datetime import datetime, timedelta
    
    # Calculate week range
    today = datetime.now()
    week_start = today + timedelta(days=-today.weekday(), weeks=week_offset)
    week_end = week_start + timedelta(days=6)
    
    params = {
        'q': city,
        'status': 'Active',
        'mindate': week_start.strftime('%Y-%m-%d'),
        'maxdate': week_end.strftime('%Y-%m-%d'),
        'limit': 500,
        'offset': 0
    }
    
    response = requests.get(
        f"{config.base_url}/properties",
        params=params,
        headers=config.headers,
        timeout=30
    )
    
    if response.status_code == 200:
        all_properties = response.json()
        
        # Filter for properties with open houses
        open_houses = []
        for prop in all_properties:
            # Check if property has openHouse data in mls object
            if prop.get('openHouse') or (prop.get('mls') and prop['mls'].get('openHouse')):
                open_houses.append(prop)
        
        # Group by city
        by_city = {}
        for oh in open_houses:
            city_name = oh['address']['city']
            if city_name not in by_city:
                by_city[city_name] = []
            by_city[city_name].append(oh)
        
        # Calculate metrics per city
        city_stats = []
        for city_name, listings in by_city.items():
            prices = [p['listPrice'] for p in listings]
            median_price = sorted(prices)[len(prices)//2] if prices else 0
            
            # Count weekend vs weekday
            weekend_count = 0
            # This would require parsing actual open house dates from the data
            
            city_stats.append({
                'city': city_name,
                'open': len(listings),
                'new7': len([l for l in listings if l.get('daysOnMarket', 999) <= 7]),
                'medList': median_price,
                'weekend': 'Sat+Sun'  # Would calculate from actual data
            })
        
        # Sort by number of open houses
        city_stats.sort(key=lambda x: x['open'], reverse=True)
        
        return {
            'total_open_houses': len(open_houses),
            'by_city': city_stats,
            'listings': open_houses
        }
    else:
        raise Exception(f"API Error: {response.status_code}")

# Usage
oh_data = get_open_houses('San Diego', 0)
print(f"Total open houses this week: {oh_data['total_open_houses']}")
for city_stat in oh_data['by_city'][:10]:  # Top 10 cities
    print(f"{city_stat['city']}: {city_stat['open']} open houses, Median: ${city_stat['medList']:,}")
```

---

## 4. Request Parameters Reference

### 4.1 Complete Parameter List

| Parameter | Type | Description | Example Values |
|-----------|------|-------------|----------------|
| `q` | string | City, zip, or address search | `San Diego`, `92101`, `123 Main St` |
| `status` | string (comma-separated) | Property status filter | `Active`, `Pending`, `Closed`, `Active,Pending` |
| `type` | string (comma-separated) | Property type filter | `RES`, `CND`, `MUL`, `RES,CND` |
| `minprice` | integer | Minimum list price | `500000` |
| `maxprice` | integer | Maximum list price | `1000000` |
| `minbeds` | integer | Minimum bedrooms | `3` |
| `maxbeds` | integer | Maximum bedrooms | `5` |
| `minbaths` | decimal | Minimum bathrooms | `2.5` |
| `maxbaths` | decimal | Maximum bathrooms | `4` |
| `minarea` | integer | Minimum square feet | `1500` |
| `maxarea` | integer | Maximum square feet | `3000` |
| `mindate` | string (YYYY-MM-DD) | Minimum list date | `2024-10-01` |
| `maxdate` | string (YYYY-MM-DD) | Maximum list date | `2024-10-31` |
| `minyear` | integer | Minimum year built | `2000` |
| `maxyear` | integer | Maximum year built | `2024` |
| `mindom` | integer | Minimum days on market | `0` |
| `maxdom` | integer | Maximum days on market | `90` |
| `limit` | integer | Results per page (max 500) | `100`, `500` |
| `offset` | integer | Pagination offset | `0`, `100`, `200` |
| `sort` | string | Sort field | `listDate`, `-listDate`, `daysOnMarket`, `-closeDate` |
| `vendor` | string | MLS vendor/source | `crmls`, `sdmls` |
| `points` | string | Polygon coordinates (WKT format) | `POLYGON((-117.1 32.7, ...))` |
| `neighborhoods` | string (comma-separated) | Neighborhood names | `Downtown,La Jolla` |
| `features` | string (comma-separated) | Property features | `pool,waterfront,hasOpenHouse` |
| `count` | boolean | Return count only | `true`, `false` |

### 4.2 Sort Options

| Sort Value | Description | Use Case |
|------------|-------------|----------|
| `listDate` | List date ascending (oldest first) | Historical analysis |
| `-listDate` | List date descending (newest first) | New listings report |
| `closeDate` | Close date ascending | Closed sales history |
| `-closeDate` | Close date descending (most recent) | Recent closings report |
| `listPrice` | Price ascending (lowest first) | Entry-level market |
| `-listPrice` | Price descending (highest first) | Luxury market |
| `daysOnMarket` | DOM ascending (freshest first) | New inventory |
| `-daysOnMarket` | DOM descending (stale listings) | Market stagnation analysis |
| `area` | Square footage ascending | Smaller properties |
| `-area` | Square footage descending | Larger properties |

### 4.3 Date Range Patterns

#### Last 30 Days
```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

params = {
    'mindate': start_date.strftime('%Y-%m-%d'),
    'maxdate': end_date.strftime('%Y-%m-%d')
}
```

#### Month-to-Date
```python
from datetime import datetime

now = datetime.now()
start_of_month = datetime(now.year, now.month, 1)

params = {
    'mindate': start_of_month.strftime('%Y-%m-%d'),
    'maxdate': now.strftime('%Y-%m-%d')
}
```

#### Last Complete Month
```python
from datetime import datetime
from dateutil.relativedelta import relativedelta

now = datetime.now()
start_of_last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
end_of_last_month = now.replace(day=1) - timedelta(days=1)

params = {
    'mindate': start_of_last_month.strftime('%Y-%m-%d'),
    'maxdate': end_of_last_month.strftime('%Y-%m-%d')
}
```

#### Year-to-Date
```python
from datetime import datetime

now = datetime.now()
start_of_year = datetime(now.year, 1, 1)

params = {
    'mindate': start_of_year.strftime('%Y-%m-%d'),
    'maxdate': now.strftime('%Y-%m-%d')
}
```

---

## 5. Response Data Structures

### 5.1 Complete Property Object

```json
{
  "mlsId": 12345678,
  "showingContactName": "John Doe",
  "showingContactPhone": "(619) 555-1234",
  "terms": "Conventional",
  "showingInstructions": "Call listing agent",
  "office": {
    "brokerid": "BR12345",
    "name": "Example Realty",
    "contact": {
      "email": "info@example.com",
      "office": "(619) 555-9999",
      "cell": null
    },
    "address": {
      "full": "456 Broker St, San Diego, CA 92101"
    }
  },
  "listDate": "2024-10-15T00:00:00.000Z",
  "agent": {
    "lastName": "Doe",
    "contact": "(619) 555-1234",
    "firstName": "John",
    "email": "john@example.com",
    "id": "AG67890"
  },
  "association": {
    "fee": 350,
    "name": "San Diego HOA",
    "amenities": "Pool, Gym, Tennis Courts"
  },
  "modified": "2024-10-20T14:30:00.000Z",
  "school": {
    "schoolDistrict": "San Diego Unified",
    "elementarySchool": "Lincoln Elementary",
    "middleSchool": "Roosevelt Middle",
    "highSchool": "Washington High"
  },
  "photos": [
    "https://photos.simplyrets.com/properties/123/photo1.jpg",
    "https://photos.simplyrets.com/properties/123/photo2.jpg"
  ],
  "listPrice": 950000,
  "virtualTourUrl": "https://tours.example.com/123",
  "remarks": "Beautiful single-family home in prime location. Updated kitchen, hardwood floors, large backyard. Close to schools and shopping.",
  "disclaimers": [
    "Information deemed reliable but not guaranteed",
    "Verify all information"
  ],
  "property": {
    "roof": "Tile",
    "cooling": "Central AC",
    "style": "Mediterranean",
    "area": 1850,
    "bathsFull": 2,
    "bathsHalf": 1,
    "stories": 2,
    "fireplaces": 1,
    "flooring": "Hardwood, Tile",
    "heating": "Forced Air",
    "foundation": "Slab",
    "laundryFeatures": "In Unit",
    "occupantName": null,
    "lotDescription": "Corner Lot",
    "pool": "Private Pool",
    "subType": "Single Family Residence",
    "bedrooms": 3,
    "interiorFeatures": "Granite Counters, Walk-in Closet",
    "lotSize": "6500",
    "areaSource": "Public Records",
    "maintenanceExpense": null,
    "additionalRooms": "Office, Bonus Room",
    "exteriorFeatures": "Patio, Landscaped Yard",
    "water": "Public",
    "view": "City, Mountain",
    "lotSizeArea": null,
    "subdivision": "Sunset Hills",
    "construction": "Stucco, Frame",
    "parking": {
      "leased": null,
      "spaces": 2,
      "description": "Attached Garage"
    },
    "lotSizeAreaUnits": null,
    "type": "RES",
    "garageSpaces": 2,
    "bathsThreeQuarter": null,
    "accessibility": "ADA Accessible Entrance",
    "acres": 0.15,
    "occupantType": null,
    "subTypeRaw": null,
    "yearBuilt": 2005
  },
  "geo": {
    "county": "San Diego",
    "lat": 32.715736,
    "lng": -117.161087,
    "marketArea": "Downtown",
    "directions": "Take I-5 to Market St exit..."
  },
  "tax": {
    "taxYear": 2023,
    "taxAnnualAmount": "11400",
    "id": "123-456-78-90"
  },
  "coAgent": {
    "lastName": null,
    "contact": null,
    "firstName": null,
    "email": null,
    "id": null
  },
  "sales": {
    "closeDate": null,
    "closePrice": null,
    "contractDate": null
  },
  "ownership": "Fee Simple",
  "address": {
    "crossStreet": "5th Ave",
    "state": "CA",
    "country": "USA",
    "postalCode": "92101",
    "streetName": "Main",
    "streetNumberText": "123",
    "city": "San Diego",
    "streetNumber": 123,
    "full": "123 Main St, San Diego, CA 92101",
    "unit": null,
    "streetSuffix": "St"
  },
  "agreement": "Exclusive Right To Sell",
  "mls": {
    "status": "Active",
    "area": "Downtown",
    "daysOnMarket": 15,
    "originalListPrice": 975000,
    "statusText": "Active",
    "statusChangeDate": "2024-10-15T00:00:00.000Z",
    "originatingSystemName": "CRMLS"
  },
  "openHouse": [
    {
      "date": "2024-10-26",
      "startTime": "13:00:00",
      "endTime": "16:00:00",
      "description": "Saturday Open House"
    },
    {
      "date": "2024-10-27",
      "startTime": "13:00:00",
      "endTime": "15:00:00",
      "description": "Sunday Open House"
    }
  ],
  "daysOnMarket": 15,
  "privateRemarks": null,
  "listingId": "SR24123456"
}
```

### 5.2 Key Fields by Use Case

#### Market Snapshot Analysis
```python
essential_fields = [
    'mlsId',
    'listPrice',
    'listDate',
    'daysOnMarket',
    'property.bedrooms',
    'property.bathrooms',
    'property.area',
    'property.type',
    'address.city',
    'mls.status',
    'sales.closePrice',  # For closed properties
    'sales.closeDate'    # For closed properties
]
```

#### Price Bands Analysis
```python
essential_fields = [
    'listPrice',
    'daysOnMarket',
    'property.area',      # For price per sqft calculation
    'mls.status',
    'address.city'
]
```

#### Listing Display (Social Graphics)
```python
essential_fields = [
    'address.full',
    'listPrice',
    'sales.closePrice',  # For closed listings
    'daysOnMarket',
    'listDate',
    'sales.closeDate'
]
```

---

## 6. Rate Limiting & Error Handling

### 6.1 Rate Limits

**SimplyRETS Rate Limits** (as of October 2025):
- **60 requests per minute** (standard tier)
- **10 burst requests** (allow short bursts above the limit)
- **1,000 requests per hour** (hard limit)

### 6.2 Rate Limiting Strategy

**Python Implementation with Rate Limiter**:

```python
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """
    Token bucket rate limiter for API requests.
    """
    def __init__(self, requests_per_minute=60, burst=10):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.window_seconds = 60
        self.tokens = burst
        self.last_update = time.time()
        self.lock = Lock()
        self.request_times = deque()
    
    def acquire(self):
        """
        Acquire a token to make a request. Blocks if rate limit would be exceeded.
        """
        with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            while self.request_times and now - self.request_times[0] > self.window_seconds:
                self.request_times.popleft()
            
            # Check if we're at the limit
            if len(self.request_times) >= self.requests_per_minute:
                # Calculate how long to wait
                wait_time = self.window_seconds - (now - self.request_times[0])
                if wait_time > 0:
                    print(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    return self.acquire()  # Try again
            
            # Add this request
            self.request_times.append(now)
            return True

# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60, burst=10)

def api_request_with_rate_limit(url, params, headers):
    """
    Make an API request with rate limiting.
    """
    rate_limiter.acquire()
    
    response = requests.get(url, params=params, headers=headers, timeout=30)
    return response
```

### 6.3 Error Handling

**HTTP Status Codes**:

| Status Code | Meaning | Action |
|-------------|---------|--------|
| `200` | Success | Process response |
| `400` | Bad Request | Check parameters, log error |
| `401` | Unauthorized | Check credentials |
| `403` | Forbidden | Check API access, MLS permissions |
| `404` | Not Found | Resource doesn't exist |
| `429` | Too Many Requests | Implement backoff, respect rate limit |
| `500` | Server Error | Retry with exponential backoff |
| `503` | Service Unavailable | Retry with longer backoff |

**Error Handling Implementation**:

```python
import time
import logging
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API error exception"""
    pass

def make_api_request(url, params, headers, max_retries=3):
    """
    Make API request with error handling and retries.
    
    Args:
        url (str): API endpoint URL
        params (dict): Query parameters
        headers (dict): Request headers
        max_retries (int): Maximum number of retry attempts
    
    Returns:
        dict or list: Parsed JSON response
    
    Raises:
        APIError: If request fails after all retries
    """
    retry_count = 0
    backoff_seconds = 1
    
    while retry_count < max_retries:
        try:
            # Acquire rate limit token
            rate_limiter.acquire()
            
            # Make request
            logger.info(f"Making API request: {url}")
            logger.debug(f"Parameters: {params}")
            
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            # Check status code
            if response.status_code == 200:
                logger.info(f"Request successful: {len(response.json())} results")
                return response.json()
            
            elif response.status_code == 401:
                logger.error("Authentication failed. Check API credentials.")
                raise APIError("Authentication failed")
            
            elif response.status_code == 403:
                logger.error("Access forbidden. Check MLS permissions.")
                raise APIError("Access forbidden")
            
            elif response.status_code == 404:
                logger.warning("Resource not found")
                return []  # Return empty array for not found
            
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded. Backing off...")
                retry_count += 1
                time.sleep(backoff_seconds * 2)  # Longer backoff for rate limits
                backoff_seconds *= 2
                continue
            
            elif response.status_code >= 500:
                logger.error(f"Server error: {response.status_code}")
                retry_count += 1
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
                continue
            
            else:
                logger.error(f"Unexpected status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise APIError(f"Unexpected status: {response.status_code}")
        
        except Timeout:
            logger.warning(f"Request timeout (attempt {retry_count + 1}/{max_retries})")
            retry_count += 1
            time.sleep(backoff_seconds)
            backoff_seconds *= 2
        
        except RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            retry_count += 1
            time.sleep(backoff_seconds)
            backoff_seconds *= 2
    
    # All retries exhausted
    logger.error(f"Request failed after {max_retries} attempts")
    raise APIError(f"Request failed after {max_retries} retries")

# Usage example
try:
    properties = make_api_request(
        f"{config.base_url}/properties",
        params={'q': 'San Diego', 'status': 'Active', 'limit': 100},
        headers=config.headers
    )
    print(f"Retrieved {len(properties)} properties")
except APIError as e:
    print(f"API Error: {str(e)}")
    # Handle error (notify admin, use cached data, etc.)
```

### 6.4 Monitoring & Logging

**Logging Configuration**:

```python
import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Configure logging
logger = logging.getLogger('simplyrets_api')
logger.setLevel(logging.DEBUG)

# File handler (rotates daily)
log_filename = f"logs/api_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.handlers.RotatingFileHandler(
    log_filename,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=30
)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Usage in API functions
logger.info("Starting API request...")
logger.debug(f"Parameters: {params}")
logger.error(f"Request failed: {error_message}")
```

**Request Metrics Tracking**:

```python
import time
from collections import defaultdict

class APIMetrics:
    """
    Track API request metrics.
    """
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_time = 0
        self.requests_by_endpoint = defaultdict(int)
        self.errors_by_code = defaultdict(int)
    
    def record_request(self, endpoint, duration, status_code):
        """
        Record metrics for a request.
        """
        self.request_count += 1
        self.total_time += duration
        self.requests_by_endpoint[endpoint] += 1
        
        if status_code >= 400:
            self.error_count += 1
            self.errors_by_code[status_code] += 1
    
    def get_stats(self):
        """
        Get summary statistics.
        """
        avg_time = self.total_time / self.request_count if self.request_count > 0 else 0
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': f"{error_rate:.2f}%",
            'avg_response_time': f"{avg_time:.2f}s",
            'requests_by_endpoint': dict(self.requests_by_endpoint),
            'errors_by_code': dict(self.errors_by_code)
        }
    
    def reset(self):
        """Reset all metrics."""
        self.__init__()

# Global metrics instance
api_metrics = APIMetrics()

# Modified API request function with metrics
def make_api_request_with_metrics(url, params, headers, max_retries=3):
    """
    Make API request with metrics tracking.
    """
    start_time = time.time()
    
    try:
        response = make_api_request(url, params, headers, max_retries)
        duration = time.time() - start_time
        api_metrics.record_request(url, duration, 200)
        return response
    except APIError as e:
        duration = time.time() - start_time
        api_metrics.record_request(url, duration, 500)
        raise

# Print metrics periodically
def print_api_metrics():
    """
    Print API metrics summary.
    """
    stats = api_metrics.get_stats()
    print("\n=== API Metrics ===")
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Total Errors: {stats['total_errors']}")
    print(f"Error Rate: {stats['error_rate']}")
    print(f"Avg Response Time: {stats['avg_response_time']}")
    print(f"\nRequests by Endpoint:")
    for endpoint, count in stats['requests_by_endpoint'].items():
        print(f"  {endpoint}: {count}")
    print(f"\nErrors by Status Code:")
    for code, count in stats['errors_by_code'].items():
        print(f"  {code}: {count}")
    print("===================\n")
```

---

*This guide continues with Parts 2-7 in the next sections...*

**Document Progress**: Part 1 Complete (API Integration)  
**Next Sections**: Data Processing Pipeline, Report Generation, Social Graphics, PDF, Database, Deployment

Would you like me to continue generating the remaining sections? This is an extensive technical reference document and I want to ensure I capture every detail you need.

