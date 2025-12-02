# SimplyRETS API - Source of Truth

**Last Updated**: December 2, 2025  
**Status**: ✅ Production - Verified via Direct Testing  
**Test Script**: `scripts/test_simplyrets.py`

---

## Quick Reference

```
Base URL: https://api.simplyrets.com/properties
Auth: HTTP Basic (username:password)
Production Credentials: info_456z6zv2 / lm0182gh3pu6f827
```

### Key Learnings (December 2025 Testing)

1. **Use `q` instead of `cities`** - The `cities` parameter causes 400 errors with our account
2. **Query Active and Closed separately** - Don't combine statuses; cleaner data and metrics
3. **`subtype` works!** - Filter by SingleFamilyResidence, Condominium, Townhouse
4. **No sorting support** - The `sort` parameter causes 400 errors
5. **No vendor needed** - The `vendor` parameter causes 400 errors

---

## 1. API Parameters (Verified Working)

### 1.1 Location Parameters

| Parameter | Description | Example | Notes |
|-----------|-------------|---------|-------|
| `q` | Fuzzy search (city, zip, address, MLS#) | `q=Irvine` | ✅ **Recommended** - works with all accounts |
| `postalCodes` | Comma-separated ZIP codes | `postalCodes=92618,92620` | ✅ Works |
| `cities` | Explicit city filter | `cities=Irvine` | ⚠️ May not work with all accounts |

**Note**: Use `q` for city search. The `cities` parameter is more explicit but some SimplyRETS accounts don't support it.

### 1.2 Status Parameters

| Status | Use Case | Example |
|--------|----------|---------|
| `Active` | Current listings, inventory | `status=Active` |
| `Closed` | Sold properties | `status=Closed` |
| `Pending` | Under contract | `status=Pending` |

**⚠️ Important**: Query Active and Closed **separately** for cleaner data. Don't combine as `Active,Pending,Closed`.

### 1.3 Property Type Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `type` | `RES`, `RNT`, `CND`, `MUL`, `LND`, `COM` | Broad property category |
| `subtype` | `SingleFamilyResidence`, `Condominium`, `Townhouse`, `ManufacturedHome`, `Duplex` | Specific property type |

**Type Values**:
- `RES` - Residential (includes SFR, Condo, Townhouse)
- `RNT` - Rental
- `CND` - Condominium (may overlap with RNT)
- `MUL` - Multi-family
- `LND` - Land
- `COM` - Commercial

**SubType Values** (verified in Irvine market):
| SubType | Count | Notes |
|---------|-------|-------|
| `Condominium` | 239 | Most common |
| `SingleFamilyResidence` | 211 | Second most common |
| `Townhouse` | 45 | |
| `ManufacturedHome` | 2 | |
| `Duplex` | 1 | |

### 1.4 Filter Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `mindate` | string | Start date (YYYY-MM-DD) | `mindate=2025-11-01` |
| `maxdate` | string | End date (YYYY-MM-DD) | `maxdate=2025-12-01` |
| `minprice` | integer | Minimum price | `minprice=500000` |
| `maxprice` | integer | Maximum price | `maxprice=1000000` |
| `minbeds` | integer | Minimum bedrooms | `minbeds=3` |
| `minbaths` | integer | Minimum bathrooms | `minbaths=2` |

### 1.5 Pagination Parameters

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `limit` | 50 | 500 | Results per page |
| `offset` | 0 | - | Starting position |

### 1.6 Parameters NOT Working (with our account)

| Parameter | Status | Error |
|-----------|--------|-------|
| `sort` | ❌ | 400 Bad Request |
| `vendor` | ❌ | 400 Bad Request |
| `cities` | ⚠️ | May cause 400 with some accounts |

---

## 2. Report Query Patterns

### 2.1 Market Snapshot (Active Listings)

```python
# Query 1: Active Listings
params = {
    "q": city,                    # e.g., "Irvine"
    "status": "Active",
    "type": "RES",                # Residential only
    "mindate": start_date,        # YYYY-MM-DD
    "maxdate": end_date,          # YYYY-MM-DD
    "limit": 1000,
    "offset": 0,
}
```

### 2.2 Market Snapshot (Closed Sales)

```python
# Query 2: Closed Sales (separate query)
params = {
    "q": city,
    "status": "Closed",
    "type": "RES",
    "mindate": start_date,
    "maxdate": end_date,
    "limit": 1000,
    "offset": 0,
}
```

### 2.3 New Listings Report

```python
params = {
    "q": city,
    "status": "Active",
    "type": "RES",
    "mindate": start_date,        # Recent window (7-14 days)
    "maxdate": end_date,
    "limit": 500,
    "offset": 0,
}
```

### 2.4 Inventory Report (Current Active)

```python
params = {
    "q": city,
    "status": "Active",
    "type": "RES",
    # No date filter - current snapshot
    "limit": 500,
    "offset": 0,
}
```

### 2.5 Closed Sales Report

```python
params = {
    "q": city,
    "status": "Closed",
    "type": "RES",
    "mindate": start_date,
    "maxdate": end_date,
    "limit": 1000,
    "offset": 0,
}
```

### 2.6 Property Type Filtered Report

```python
# Single Family Residence only
params = {
    "q": city,
    "status": "Active",
    "type": "RES",
    "subtype": "SingleFamilyResidence",
    "mindate": start_date,
    "maxdate": end_date,
    "limit": 500,
}

# Condominium only
params = {
    "q": city,
    "status": "Active",
    "type": "RES",
    "subtype": "Condominium",
    "mindate": start_date,
    "maxdate": end_date,
    "limit": 500,
}
```

### 2.7 Price Range Report

```python
params = {
    "q": city,
    "status": "Active",
    "type": "RES",
    "minprice": 500000,
    "maxprice": 1000000,
    "mindate": start_date,
    "maxdate": end_date,
    "limit": 500,
}
```

---

## 3. Response Data Structure

### 3.1 Property Object

```json
{
  "mlsId": 12345678,
  "listPrice": 1500000,
  "listDate": "2025-11-15T00:00:00.000Z",
  "daysOnMarket": 15,
  
  "address": {
    "full": "123 Main Street",
    "city": "Irvine",
    "state": "CA",
    "postalCode": "92618",
    "streetName": "Main Street",
    "streetNumber": "123"
  },
  
  "property": {
    "type": "RES",
    "subType": "SingleFamilyResidence",
    "bedrooms": 4,
    "bathsFull": 3,
    "bathsHalf": 1,
    "area": 2500,
    "lotSize": "6500",
    "yearBuilt": 2015,
    "stories": 2,
    "garageSpaces": 2
  },
  
  "mls": {
    "status": "Active",
    "daysOnMarket": 15,
    "originalListPrice": 1550000,
    "area": "Irvine",
    "statusText": "Active"
  },
  
  "sales": {
    "closePrice": 1480000,
    "closeDate": "2025-11-30T00:00:00.000Z"
  },
  
  "photos": [
    "https://photos.simplyrets.com/photo1.jpg",
    "https://photos.simplyrets.com/photo2.jpg"
  ],
  
  "geo": {
    "lat": 33.6846,
    "lng": -117.8265
  }
}
```

### 3.2 Key Fields for Reports

| Field | Path | Description |
|-------|------|-------------|
| MLS ID | `mlsId` | Unique listing identifier |
| List Price | `listPrice` | Current asking price |
| Close Price | `sales.closePrice` | Final sale price (Closed only) |
| Status | `mls.status` | Active, Closed, Pending |
| DOM | `daysOnMarket` or `mls.daysOnMarket` | Days on market |
| Address | `address.full` | Full street address |
| City | `address.city` | City name |
| ZIP | `address.postalCode` | Postal code |
| Beds | `property.bedrooms` | Bedroom count |
| Baths | Calculate: `bathsFull + 0.5*bathsHalf + 0.75*bathsThreeQuarter` | Total baths |
| Sqft | `property.area` | Living area |
| Type | `property.type` | RES, CND, etc. |
| SubType | `property.subType` | SingleFamilyResidence, Condominium, etc. |
| Year Built | `property.yearBuilt` | Construction year |
| Photos | `photos[0]` | Primary listing photo |

---

## 4. Pagination Pattern

```python
def fetch_all_properties(base_params: dict, max_results: int = 1000) -> list:
    """Fetch all properties with pagination."""
    all_properties = []
    offset = 0
    limit = 500  # Max per request
    
    while len(all_properties) < max_results:
        params = {**base_params, "limit": limit, "offset": offset}
        
        response = requests.get(
            "https://api.simplyrets.com/properties",
            params=params,
            auth=(USERNAME, PASSWORD),
            timeout=30
        )
        response.raise_for_status()
        batch = response.json()
        
        if not batch:
            break
        
        all_properties.extend(batch)
        
        if len(batch) < limit:
            break  # Last page
        
        offset += limit
    
    return all_properties[:max_results]
```

---

## 5. Metric Calculations

### 5.1 Market Snapshot Metrics

```python
def calculate_metrics(active: list, closed: list) -> dict:
    """Calculate market snapshot metrics."""
    
    # Active metrics
    active_count = len(active)
    active_prices = [p['listPrice'] for p in active if p.get('listPrice')]
    median_list_price = sorted(active_prices)[len(active_prices)//2] if active_prices else 0
    
    # Closed metrics
    closed_count = len(closed)
    closed_prices = [p.get('sales', {}).get('closePrice') or p['listPrice'] 
                     for p in closed if p.get('listPrice')]
    median_close_price = sorted(closed_prices)[len(closed_prices)//2] if closed_prices else 0
    
    # DOM calculation
    doms = [p.get('daysOnMarket') or p.get('mls', {}).get('daysOnMarket', 0) 
            for p in closed if p.get('daysOnMarket') or p.get('mls', {}).get('daysOnMarket')]
    avg_dom = sum(doms) / len(doms) if doms else 0
    
    # Months of Inventory (MOI)
    monthly_sales_rate = closed_count / 1  # Adjust for lookback period
    moi = active_count / monthly_sales_rate if monthly_sales_rate > 0 else 0
    
    return {
        "active_count": active_count,
        "closed_count": closed_count,
        "median_list_price": median_list_price,
        "median_close_price": median_close_price,
        "avg_dom": round(avg_dom, 1),
        "months_of_inventory": round(moi, 1),
    }
```

### 5.2 Sale-to-List Ratio

```python
def calculate_sale_to_list_ratio(closed: list) -> float:
    """Calculate average sale-to-list price ratio."""
    ratios = []
    for p in closed:
        list_price = p.get('listPrice', 0)
        close_price = p.get('sales', {}).get('closePrice', 0)
        if list_price > 0 and close_price > 0:
            ratios.append(close_price / list_price)
    
    return round(sum(ratios) / len(ratios) * 100, 1) if ratios else 0
```

---

## 6. Environment Configuration

### 6.1 Required Environment Variables

```bash
# SimplyRETS Credentials
SIMPLYRETS_USERNAME=info_456z6zv2
SIMPLYRETS_PASSWORD=lm0182gh3pu6f827

# Optional: MLS vendor (only if needed)
# SIMPLYRETS_VENDOR=crmls

# Feature Flags
# SIMPLYRETS_ALLOW_SORT=true  # Enable if your account supports sorting
```

### 6.2 Worker Configuration (Render)

The worker service reads these from Render environment variables:
- `SIMPLYRETS_USERNAME`
- `SIMPLYRETS_PASSWORD`
- `SIMPLYRETS_VENDOR` (optional)

---

## 7. Error Handling

### 7.1 Common Errors

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Invalid parameter | Check parameter names/values |
| 401 | Auth failed | Verify credentials |
| 404 | No results | Check filters, try broader search |
| 429 | Rate limited | Implement backoff, reduce requests |
| 500 | Server error | Retry with exponential backoff |

### 7.2 Parameters That Cause 400 Errors

With our account (`info_456z6zv2`), these parameters cause 400 Bad Request:
- `sort` - Sorting not supported
- `vendor` - Vendor parameter not supported
- `cities` - May not be supported (use `q` instead)

---

## 8. Testing Script

Use `scripts/test_simplyrets.py` for direct API testing:

```bash
python scripts/test_simplyrets.py
```

This script tests all parameter combinations without needing to deploy.

---

## 9. Report Type Summary

| Report | Status | Type Filter | Date Filter | Key Metrics |
|--------|--------|-------------|-------------|-------------|
| Market Snapshot | Active + Closed (separate) | RES | Last 30 days | Active, Closed, Median Price, DOM, MOI |
| New Listings | Active | RES | Last 7-14 days | Count, Median Price |
| Inventory | Active | RES | None (current) | Count by price band, DOM |
| Closed Sales | Closed | RES | Last 30 days | Count, Median Price, DOM |
| Price Bands | Active | RES | None | Count per price tier |
| Open Houses | Active | RES | This week | Listings with openHouse data |

---

## 10. Live Test Results (December 2, 2025)

### 10.1 Test Environment
- **Script**: `scripts/test_simplyrets.py`
- **Credentials**: `info_456z6zv2` / `lm0182gh3pu6f827`
- **Test City**: Irvine, CA
- **Date Range**: November 1 - December 1, 2025 (30 days)

### 10.2 Parameter Testing Results

| Test | Parameters | Status | Results |
|------|------------|--------|---------|
| Basic Active | `q=Irvine&status=Active&limit=10` | ✅ 200 OK | 10 properties |
| Active with dates | `q=Irvine&status=Active&mindate=2025-11-01&maxdate=2025-12-01` | ✅ 200 OK | 10 properties |
| Closed with dates | `q=Irvine&status=Closed&mindate=2025-11-01&maxdate=2025-12-01` | ✅ 200 OK | 10 properties |
| Type=RES | `q=Irvine&status=Active&type=RES` | ✅ 200 OK | 10 properties (all RES) |
| Type=CND | `q=Irvine&status=Active&type=CND` | ✅ 200 OK | 10 properties |
| Multiple types | `q=Irvine&status=Active&type=RES,CND` | ✅ 200 OK | 10 properties |
| Subtype SFR | `q=Irvine&status=Active&subtype=SingleFamilyResidence` | ✅ 200 OK | 10 properties (all SFR) |
| Subtype Condo | `q=Irvine&status=Active&subtype=Condominium` | ✅ 200 OK | 10 properties (all Condo) |
| Price range | `q=Irvine&status=Active&minprice=500000&maxprice=1000000` | ✅ 200 OK | 10 properties |
| Min beds | `q=Irvine&status=Active&minbeds=3` | ✅ 200 OK | 10 properties |
| Combined filters | `q=Irvine&status=Active&type=RES&subtype=SingleFamilyResidence&minprice=500000&maxprice=2000000&minbeds=3` | ✅ 200 OK | 50 properties |
| **cities param** | `cities=Irvine&status=Active` | ❌ 400 | Bad Request |
| **sort param** | `q=Irvine&status=Active&sort=-listDate` | ❌ 400 | Bad Request |
| **vendor param** | `q=Irvine&status=Active&vendor=crmls` | ❌ 400 | Bad Request |

### 10.3 Market Data Discovery (Irvine)

**Property Types in Market (500 sample)**:
| Type | Count | Percentage |
|------|-------|------------|
| RES | 324 | 64.8% |
| RNT | 176 | 35.2% |

**Property SubTypes in Market**:
| SubType | Count | Percentage |
|---------|-------|------------|
| Condominium | 239 | 47.8% |
| SingleFamilyResidence | 211 | 42.2% |
| Townhouse | 45 | 9.0% |
| ManufacturedHome | 2 | 0.4% |
| Duplex | 1 | 0.2% |
| None | 2 | 0.4% |

### 10.4 Combined Metrics Test Results

**Active RES Listings (100 sample)**:
- Count: 100+
- Median List Price: **$1,785,000**
- SubType breakdown: 51 SFR, 44 Condo, 5 Townhouse

**Closed RES Sales (100 sample)**:
- Count: 100+
- Median Close Price: **$1,545,000**
- SubType breakdown: 38 SFR, 57 Condo, 5 Townhouse

**Subtype-Specific Results**:
| SubType | Active Count | Status |
|---------|--------------|--------|
| SingleFamilyResidence | 50+ | ✅ Works |
| Condominium | 50+ | ✅ Works |
| Townhouse | 31 | ✅ Works |

---

## 11. Code Changes Made

### 11.1 Query Builders (`apps/worker/src/worker/query_builders.py`)

**Changes**:
1. Added `build_market_snapshot_closed()` function for separate Closed queries
2. Updated `_filters()` to support `subtype` parameter
3. Changed city search from `cities` to `q` parameter
4. Disabled `sort` and `vendor` parameters (cause 400 errors)

**New Function**:
```python
def build_market_snapshot_closed(params: dict) -> Dict:
    """
    Market Snapshot (Closed): Closed listings in date window.
    Companion to build_market_snapshot() - queries Closed listings separately.
    """
    start, end = _date_window(params.get("lookback_days") or 30)
    q = {
        **_common_params(),
        "status": "Closed",
        "mindate": start,
        "maxdate": end,
        "limit": 1000,
        "offset": 0,
    }
    q |= _location(params)
    q |= _filters(params.get("filters"))
    return q
```

**Updated `_filters()` Function**:
```python
def _filters(filters: Optional[dict]) -> Dict:
    """
    Map optional filters to SimplyRETS params.
    
    Supported inputs (optional):
      - minprice, maxprice: Price range
      - type: Property type (RES, CND, MUL, LND, COM)
      - subtype: Property subtype (SingleFamilyResidence, Condominium, Townhouse)
      - beds, baths: Minimum bedrooms/bathrooms
    """
    f = filters or {}
    out: Dict = {}
    if f.get("minprice") is not None: out["minprice"] = int(f["minprice"])
    if f.get("maxprice") is not None: out["maxprice"] = int(f["maxprice"])
    if f.get("type"):                 out["type"]     = f["type"]
    if f.get("subtype"):              out["subtype"]  = f["subtype"]  # NEW
    if f.get("beds") is not None:     out["minbeds"]  = int(f["beds"])
    if f.get("baths") is not None:    out["minbaths"] = int(f["baths"])
    return out
```

### 11.2 Worker Task Bug Fix (`apps/worker/src/worker/tasks.py`)

**Fixed**: City extraction logic had operator precedence issue causing "Houston" default.

**Before (Broken)**:
```python
city = params.city or zips[0] if zips else "Houston"
```

**After (Fixed)**:
```python
city = params.city or (zips[0] if zips else "Unknown")
```

---

## 12. UI Enhancements (Planned)

### 12.1 Report Wizard Updates

The wizard should pass these filters to the backend:

**Property Type Selection** (Step 1 or Options):
```typescript
// Property type options for wizard
const PROPERTY_TYPES = [
  { value: "RES", label: "Residential", description: "All residential properties" },
];

const PROPERTY_SUBTYPES = [
  { value: "", label: "All Types", description: "Include all property types" },
  { value: "SingleFamilyResidence", label: "Single Family", description: "Detached homes" },
  { value: "Condominium", label: "Condo", description: "Condominiums" },
  { value: "Townhouse", label: "Townhouse", description: "Attached townhomes" },
];
```

**Filter Payload to Backend**:
```typescript
interface ReportFilters {
  type?: string;           // "RES" (default)
  subtype?: string;        // "SingleFamilyResidence" | "Condominium" | "Townhouse"
  minprice?: number;
  maxprice?: number;
  minbeds?: number;
}
```

### 12.2 Wizard Flow Enhancement

**Current Flow**:
1. Report Type → 2. Area → 3. Options (lookback, price) → 4. Review

**Enhanced Flow**:
1. Report Type → 2. Area → 3. **Property Type** → 4. Options → 5. Review

**New Step 3 - Property Type**:
- Default: "All Residential" (type=RES, no subtype)
- Options: Single Family, Condo, Townhouse
- Allow multiple selection or "All"

---

## 13. API Query Examples (Copy-Paste Ready)

### 13.1 cURL Commands

```bash
# Active Residential in Irvine (last 30 days)
curl -u "info_456z6zv2:lm0182gh3pu6f827" \
  "https://api.simplyrets.com/properties?q=Irvine&status=Active&type=RES&mindate=2025-11-01&maxdate=2025-12-01&limit=100"

# Closed Sales in Irvine (last 30 days)
curl -u "info_456z6zv2:lm0182gh3pu6f827" \
  "https://api.simplyrets.com/properties?q=Irvine&status=Closed&type=RES&mindate=2025-11-01&maxdate=2025-12-01&limit=100"

# Single Family Homes only
curl -u "info_456z6zv2:lm0182gh3pu6f827" \
  "https://api.simplyrets.com/properties?q=Irvine&status=Active&type=RES&subtype=SingleFamilyResidence&limit=50"

# Condos only
curl -u "info_456z6zv2:lm0182gh3pu6f827" \
  "https://api.simplyrets.com/properties?q=Irvine&status=Active&type=RES&subtype=Condominium&limit=50"

# Price filtered ($500K - $1M)
curl -u "info_456z6zv2:lm0182gh3pu6f827" \
  "https://api.simplyrets.com/properties?q=Irvine&status=Active&type=RES&minprice=500000&maxprice=1000000&limit=50"
```

### 13.2 Python Examples

```python
import requests
from base64 import b64encode

# Credentials
USERNAME = "info_456z6zv2"
PASSWORD = "lm0182gh3pu6f827"
BASE_URL = "https://api.simplyrets.com/properties"

def get_auth_header():
    credentials = f"{USERNAME}:{PASSWORD}"
    encoded = b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

# Active listings
response = requests.get(
    BASE_URL,
    params={
        "q": "Irvine",
        "status": "Active",
        "type": "RES",
        "mindate": "2025-11-01",
        "maxdate": "2025-12-01",
        "limit": 100
    },
    headers=get_auth_header(),
    timeout=30
)
active_listings = response.json()

# Closed sales (separate query)
response = requests.get(
    BASE_URL,
    params={
        "q": "Irvine",
        "status": "Closed",
        "type": "RES",
        "mindate": "2025-11-01",
        "maxdate": "2025-12-01",
        "limit": 100
    },
    headers=get_auth_header(),
    timeout=30
)
closed_sales = response.json()
```

---

## 14. Changelog

### December 2, 2025
- ✅ Created direct test script (`scripts/test_simplyrets.py`)
- ✅ Verified `q` parameter works for city search
- ✅ Verified `subtype` parameter works (SingleFamilyResidence, Condominium, Townhouse)
- ✅ Confirmed `sort`, `vendor`, `cities` parameters cause 400 errors with our account
- ✅ Implemented separate Active/Closed queries for cleaner data
- ✅ Added `subtype` filter support to `query_builders.py`
- ✅ Fixed city extraction bug in `tasks.py` (was defaulting to "Houston")
- ✅ Documented all working parameters with live test results
- 🔄 Planned: Update wizard to pass property type filters

### Previous Issues Resolved
- **Issue**: Reports showing "Houston" instead of user-selected city
  - **Cause**: Operator precedence bug in city extraction
  - **Fix**: Updated `tasks.py` to correctly extract city from params

- **Issue**: 400 Bad Request errors from SimplyRETS
  - **Cause**: Using unsupported `cities`, `sort`, `vendor` parameters
  - **Fix**: Switched to `q` parameter, disabled sorting and vendor

---

## 15. Files Reference

| File | Purpose |
|------|---------|
| `docs/SIMPLYRETS_API.md` | This document - Source of Truth |
| `scripts/test_simplyrets.py` | Direct API testing script |
| `apps/worker/src/worker/query_builders.py` | Query parameter builders |
| `apps/worker/src/worker/tasks.py` | Celery task for report generation |
| `apps/worker/src/worker/vendors/simplyrets.py` | SimplyRETS API client |

