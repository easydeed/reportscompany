# SimplyRETS API - Complete Technical Guide

**Last Updated**: December 2, 2025  
**Status**: ✅ Production Ready  
**Test Scripts**: `scripts/test_simplyrets.py`, `scripts/test_report_flow.py`

---

## Quick Start

```bash
# Test the full report flow locally (no deployment needed)
cd apps/worker
python ../../scripts/test_report_flow.py --city Irvine --lookback 30

# Test raw API responses
python ../../scripts/test_report_flow.py --raw
```

---

## 1. Authentication

```
Base URL: https://api.simplyrets.com/properties
Auth: HTTP Basic (username:password)
Production: info_456z6zv2 / lm0182gh3pu6f827
```

```python
import requests
from base64 import b64encode

USERNAME = "info_456z6zv2"
PASSWORD = "lm0182gh3pu6f827"

response = requests.get(
    "https://api.simplyrets.com/properties",
    params={"q": "Irvine", "status": "Active", "limit": 10},
    auth=(USERNAME, PASSWORD),
    timeout=30
)
```

---

## 2. Critical Rules (Read This First!)

### ✅ DO

| Rule | Why |
|------|-----|
| **Always include `type=RES`** | Excludes rentals (`RNT`) which have $3k-$5k monthly prices that corrupt metrics |
| **Query Active/Closed/Pending separately** | Cleaner data, more accurate counts |
| **Use `q` for city search** | Works with all accounts |
| **Calculate DOM from dates** | API doesn't return `daysOnMarket` for Closed listings |
| **Filter closed by `closeDate` client-side** | API `mindate/maxdate` filters by `listDate`, not `closeDate` |

### ❌ DON'T

| Rule | Error |
|------|-------|
| Don't use `cities` parameter | 400 Bad Request |
| Don't use `sort` parameter | 400 Bad Request |
| Don't use `vendor` parameter | 400 Bad Request |
| Don't mix rentals with sales | Metrics become meaningless |

---

## 3. Working Parameters

### Location

| Parameter | Example | Notes |
|-----------|---------|-------|
| `q` | `q=Irvine` | ✅ **Recommended** - fuzzy search |
| `postalCodes` | `postalCodes=92618,92620` | ✅ Works |

### Status (Query Separately!)

| Status | Use Case |
|--------|----------|
| `Active` | Current inventory |
| `Closed` | Sold properties |
| `Pending` | Under contract |

### Property Type

| Parameter | Values | Notes |
|-----------|--------|-------|
| `type` | `RES` | ✅ **Always include** - Residential only |
| `subtype` | `SingleFamilyResidence`, `Condominium`, `Townhouse` | Optional filter |

**Type Values**:
- `RES` - Residential (SFR, Condo, Townhouse) ← **Use this**
- `RNT` - Rental ← **Never include in sales reports**
- `CND` - Condominium
- `MUL` - Multi-family
- `LND` - Land
- `COM` - Commercial

### Date Filters

| Parameter | Format | Notes |
|-----------|--------|-------|
| `mindate` | `YYYY-MM-DD` | Filters by `listDate` (not `closeDate`!) |
| `maxdate` | `YYYY-MM-DD` | Filters by `listDate` (not `closeDate`!) |

### Price/Feature Filters

| Parameter | Type | Example |
|-----------|------|---------|
| `minprice` | integer | `minprice=500000` |
| `maxprice` | integer | `maxprice=1000000` |
| `minbeds` | integer | `minbeds=3` |
| `minbaths` | integer | `minbaths=2` |

### Pagination

| Parameter | Default | Max |
|-----------|---------|-----|
| `limit` | 50 | 500 |
| `offset` | 0 | - |

---

## 4. Query Patterns by Report Type

### Market Snapshot

**Requires 3 separate queries:**

```python
# Query 1: Active Listings (current inventory)
active_params = {
    "q": city,
    "status": "Active",
    "type": "RES",            # CRITICAL: Exclude rentals
    "mindate": start_date,    # YYYY-MM-DD
    "maxdate": end_date,
    "limit": 1000,
}

# Query 2: Closed Sales
closed_params = {
    "q": city,
    "status": "Closed",
    "type": "RES",            # CRITICAL: Exclude rentals
    "mindate": start_date,    # Note: Filters by listDate!
    "maxdate": end_date,
    "limit": 1000,
}

# Query 3: Pending Sales
pending_params = {
    "q": city,
    "status": "Pending",
    "type": "RES",
    "mindate": start_date,
    "maxdate": end_date,
    "limit": 1000,
}
```

### Other Reports

```python
# New Listings
{"q": city, "status": "Active", "type": "RES", "mindate": start, "maxdate": end}

# Inventory (current snapshot, no date filter)
{"q": city, "status": "Active", "type": "RES", "limit": 500}

# Closed Sales
{"q": city, "status": "Closed", "type": "RES", "mindate": start, "maxdate": end}

# Price Range Filter
{"q": city, "status": "Active", "type": "RES", "minprice": 500000, "maxprice": 1000000}

# Property Subtype Filter
{"q": city, "status": "Active", "type": "RES", "subtype": "SingleFamilyResidence"}
```

---

## 5. Response Data Structure

```json
{
  "mlsId": 12345678,
  "listPrice": 1500000,
  "listDate": "2025-11-15T00:00:00.000Z",
  "daysOnMarket": 15,           // Only for Active/Pending!
  
  "address": {
    "full": "123 Main Street",
    "city": "Irvine",
    "postalCode": "92618"
  },
  
  "property": {
    "type": "RES",
    "subType": "SingleFamilyResidence",
    "bedrooms": 4,
    "bathsFull": 3,
    "area": 2500
  },
  
  "mls": {
    "status": "Active"
  },
  
  "sales": {                    // Only for Closed!
    "closePrice": 1480000,
    "closeDate": "2025-11-30T00:00:00.000Z"
  },
  
  "photos": ["https://..."]
}
```

### Key Fields

| Field | Path | Notes |
|-------|------|-------|
| MLS ID | `mlsId` | Unique identifier |
| List Price | `listPrice` | Asking price |
| Close Price | `sales.closePrice` | Final sale price (Closed only) |
| Status | `mls.status` | Active, Closed, Pending |
| DOM | `daysOnMarket` | **Only for Active/Pending!** |
| Close Date | `sales.closeDate` | When sold (Closed only) |
| Type | `property.type` | RES, RNT, etc. |
| SubType | `property.subType` | SingleFamilyResidence, Condominium, etc. |

---

## 6. Metric Calculations

### The Problem: DOM Not Available for Closed

SimplyRETS **does not return `daysOnMarket` for Closed listings**. You must calculate it:

```python
def calculate_dom(listing):
    """Calculate Days on Market from dates."""
    if listing.get("daysOnMarket"):
        return listing["daysOnMarket"]
    
    list_date = parse_date(listing.get("listDate"))
    close_date = parse_date(listing.get("sales", {}).get("closeDate"))
    
    if list_date and close_date:
        return (close_date - list_date).days
    elif list_date:
        return (datetime.now() - list_date).days
    return None
```

### The Problem: API Filters by listDate, Not closeDate

When querying Closed listings with `mindate/maxdate`, the API filters by `listDate`, not `closeDate`. You must filter client-side:

```python
def filter_closed_by_date(listings, lookback_days):
    """Filter closed listings by actual close date."""
    cutoff = datetime.now() - timedelta(days=lookback_days)
    
    filtered = []
    for listing in listings:
        close_date = parse_date(listing.get("sales", {}).get("closeDate"))
        if close_date and close_date >= cutoff:
            filtered.append(listing)
    
    return filtered
```

### Core Metrics

```python
def median(values):
    values = sorted([v for v in values if v])
    n = len(values)
    return values[n // 2] if n else None

def calculate_metrics(active, closed, lookback_days=30):
    """Calculate Market Snapshot metrics."""
    
    # Filter closed by actual close date
    filtered_closed = filter_closed_by_date(closed, lookback_days)
    
    # Median prices
    median_list = median([p["list_price"] for p in active])
    median_close = median([p["close_price"] for p in filtered_closed])
    
    # Average DOM (calculated from dates)
    doms = [calculate_dom(p) for p in filtered_closed]
    avg_dom = sum(d for d in doms if d) / len([d for d in doms if d]) if doms else None
    
    # Months of Inventory
    AVG_DAYS_PER_MONTH = 30.437
    if filtered_closed:
        monthly_rate = len(filtered_closed) * (AVG_DAYS_PER_MONTH / lookback_days)
        moi = len(active) / monthly_rate if monthly_rate > 0 else 99.9
    else:
        moi = 99.9
    
    # Sale-to-List Ratio
    ratios = []
    for p in filtered_closed:
        if p.get("close_price") and p.get("list_price"):
            ratios.append(p["close_price"] / p["list_price"] * 100)
    sale_to_list = sum(ratios) / len(ratios) if ratios else 100.0
    
    return {
        "active_count": len(active),
        "closed_count": len(filtered_closed),
        "median_list_price": median_list,
        "median_close_price": median_close,
        "avg_dom": round(avg_dom, 1) if avg_dom else None,
        "months_of_inventory": round(moi, 1),
        "sale_to_list_ratio": round(sale_to_list, 1),
    }
```

### Property Type Classification

```python
def classify_property_type(listing):
    """Map SimplyRETS subType to display name."""
    subtype = listing.get("property", {}).get("subType", "")
    
    mapping = {
        "SingleFamilyResidence": "SFR",
        "Condominium": "Condo",
        "Townhouse": "Townhome",
        "ManufacturedHome": "Manufactured",
        "Duplex": "Multi-Family",
    }
    
    return mapping.get(subtype, "Other")
```

### Price Tier Definitions

```python
PRICE_TIERS = [
    {"name": "Entry",   "min": 0,         "max": 1_999_999},
    {"name": "Move-Up", "min": 2_000_000, "max": 2_999_999},
    {"name": "Luxury",  "min": 3_000_000, "max": 999_999_999},
]

def get_tier(price):
    for tier in PRICE_TIERS:
        if tier["min"] <= price <= tier["max"]:
            return tier["name"]
    return None
```

---

## 7. Troubleshooting

### "Median price is $6,000 instead of $1.5M"

**Cause**: Rentals (`type=RNT`) are mixed with sales. Rental prices are monthly ($3k-$5k).

**Fix**: Always include `type=RES` in queries.

```python
# ❌ Wrong
params = {"q": "Irvine", "status": "Closed"}

# ✅ Correct
params = {"q": "Irvine", "status": "Closed", "type": "RES"}
```

### "500 closed sales but only 150 in the period"

**Cause**: API returns listings with `listDate` in range, not `closeDate`.

**Fix**: Filter by `closeDate` client-side after fetching.

### "Average DOM is N/A"

**Cause**: SimplyRETS doesn't return `daysOnMarket` for Closed listings.

**Fix**: Calculate DOM from `listDate` to `closeDate`.

### "400 Bad Request"

**Cause**: Using unsupported parameters.

**Fix**: Remove these parameters:
- `sort` ❌
- `vendor` ❌
- `cities` ❌ (use `q` instead)

### "TypeError: can't compare offset-naive and offset-aware datetimes"

**Cause**: Mixing timezone-aware dates from API with timezone-naive `datetime.now()`.

**Fix**: Strip timezone from parsed dates:

```python
def parse_date(date_str):
    if not date_str:
        return None
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return dt.replace(tzinfo=None)  # Make timezone-naive
```

---

## 8. Code Files Reference

| File | Purpose |
|------|---------|
| `apps/worker/src/worker/query_builders.py` | Build API query parameters |
| `apps/worker/src/worker/compute/extract.py` | Normalize API responses, calculate DOM |
| `apps/worker/src/worker/report_builders.py` | Calculate metrics from extracted data |
| `apps/worker/src/worker/vendors/simplyrets.py` | API client |
| `apps/worker/src/worker/tasks.py` | Celery task orchestration |
| `scripts/test_report_flow.py` | Local testing (no deploy needed) |
| `scripts/test_simplyrets.py` | Direct API testing |

---

## 9. Environment Variables

```bash
# Required
SIMPLYRETS_USERNAME=info_456z6zv2
SIMPLYRETS_PASSWORD=lm0182gh3pu6f827

# Optional (not used with our account)
# SIMPLYRETS_VENDOR=crmls
```

---

## 10. Verified Test Results (December 2, 2025)

### Irvine, CA - 30 Day Lookback

**With `type=RES` (Correct)**:
| Metric | Value |
|--------|-------|
| Active | 500 |
| Closed (date-filtered) | 150 |
| Median Close Price | $1,530,000 |
| Avg DOM | 76.1 days |
| MOI | 3.3 months |
| Prices < $100k | 0 |

**Without `type=RES` (Wrong - includes rentals)**:
| Metric | Value |
|--------|-------|
| Closed (date-filtered) | 350 |
| Median Close Price | $6,390 😱 |
| Prices < $100k | 203 |

---

## 11. Changelog

### December 2, 2025 - Major Fixes
- ✅ **Fixed rental pollution**: Default all queries to `type=RES`
- ✅ **Fixed DOM calculation**: Calculate from `listDate` to `closeDate` for Closed
- ✅ **Fixed date filtering**: Client-side filter by `closeDate` (API uses `listDate`)
- ✅ **Fixed timezone issues**: Strip timezone from parsed dates
- ✅ **Added test script**: `scripts/test_report_flow.py` for local testing

### Previous Fixes
- ✅ Switched from `cities` to `q` parameter
- ✅ Disabled `sort` and `vendor` parameters
- ✅ Added `subtype` filter support
- ✅ Fixed city extraction bug (was defaulting to "Houston")
