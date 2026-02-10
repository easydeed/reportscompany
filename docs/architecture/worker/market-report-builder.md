# Market Report Builders

> `apps/worker/src/worker/report_builders.py` (904 lines)
> Transforms raw MLS listing data into structured JSON for each report type.

## Overview

Each builder function takes a list of property listings (from `PropertyDataExtractor`)
and a context dict, and returns a `result_json` dictionary matching the shape expected
by frontend email/PDF templates.

## Dispatcher

```python
build_result_json(report_type: str, listings: List[Dict], context: Dict) -> Dict
```

Routes to the appropriate builder function. Also passes through `preset_display_name`
(for Smart Preset custom headers) and `filters_label` (human-readable filter description).

**Keep in sync with:**
- Frontend: `apps/web/app/lib/reportTypes.ts` (ReportType union)
- Backend: `apps/api/src/api/routes/schedules.py` (report_type Literal)
- Email: `apps/worker/src/worker/email/template.py` (report_type_display map)

## 8 Builder Functions

### 1. `build_market_snapshot_result` -- Market Snapshot

Comprehensive market overview with segmentation.

**Input context:** `city`, `lookback_days`

**Output structure:**
```python
{
    "report_type": "market_snapshot",
    "city": str,
    "lookback_days": int,
    "period_label": str,           # "Last 30 days"
    "report_date": str,            # "February 10, 2026"
    "counts": {
        "Active": int,             # Current active inventory
        "Pending": int,            # Under contract
        "Closed": int,             # Closed sales in period (date-filtered)
        "NewListings": int         # New listings in period
    },
    "metrics": {
        "median_list_price": float,
        "median_close_price": float,
        "avg_dom": float,          # Average days on market
        "avg_ppsf": float,         # Average price per sq ft
        "close_to_list_ratio": float,
        "months_of_inventory": float,
        "new_listings_count": int
    },
    "by_property_type": dict,      # Breakdown by SFR, Condo, etc.
    "price_tiers": dict,           # Entry, Move-Up, Luxury tiers
    "listings_sample": list        # Up to 20 sample listings
}
```

**Key logic:**
- Filters listings by exact city match (case-insensitive), skips if city is a ZIP code
- Closed sales filtered by `close_date` within lookback period (not list_date)
- MOI = Active / (Closings * 30.437 / lookback_days)
- Price tiers use dynamic quartile boundaries from actual market data

### 2. `build_new_listings_result` -- New Listings

Fresh inventory report showing recently listed active properties.

**Output metrics:** `median_list_price`, `avg_dom`, `avg_ppsf`

**Key logic:** Client-side date filtering by `list_date` (SimplyRETS API does not reliably filter Active listings by mindate/maxdate). Sorted by list_date descending.

### 3. `build_inventory_result` -- Inventory

Active listings with market absorption metrics.

**Output metrics:** `median_dom`, `months_of_inventory`, `new_this_month`

**Key logic:** Filters active listings by `list_date` within lookback period. Sorted by DOM descending (longest on market first).

### 4. `build_closed_result` -- Closed Sales

Recent sales report.

**Output metrics:** `median_close_price`, `avg_dom`, `close_to_list_ratio`

**Key logic:** Filters by `close_date` within lookback period (critical -- API's mindate/maxdate filter by listDate, not closeDate). Sorted by close_date descending.

### 5. `build_price_bands_result` -- Price Bands

Market segmentation by dynamic price ranges.

**Output structure (additional):**
```python
{
    "price_bands": [
        {"label": "Under $500K", "count": 12, "median_price": 425000, "avg_dom": 22, "avg_ppsf": 310},
        ...
    ],
    "hottest_band": dict,   # Band with lowest avg_dom
    "slowest_band": dict    # Band with highest avg_dom
}
```

**Key logic:** Dynamic band boundaries from quartiles. Falls back to single band for small datasets.

### 6. `build_new_listings_gallery_result` -- New Listings Gallery (Phase P2)

Photo-first gallery template with hero images.

**Output structure (additional):**
```python
{
    "total_listings": int,     # Total (not capped)
    "total_shown": int,        # Displayed count (audience-capped)
    "audience_key": str,       # "luxury", "first_time_buyers", "families", etc.
    "listings": [
        {"hero_photo_url", "street_address", "city", "zip_code",
         "list_price", "bedrooms", "bathrooms", "sqft", "list_date"}
    ]
}
```

**Key logic:** Audience-based display caps (from `ai_insights.get_email_listing_cap`). Maps filter presets to audience keys (luxury, first_time_buyers, families, condo, investors, all).

### 7. `build_featured_listings_result` -- Featured Listings (Phase P2)

Premium 2x2 grid of top 4 properties by price.

**Key logic:** Always shows top 4 by list_price. Always uses `luxury` audience key.

### 8. `open_houses` -- Open Houses

Reuses `build_inventory_result` (same builder, different report_type label).

## Helper Functions

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_format_currency(val)` | `float -> str` | `470000` -> `"$470,000"` |
| `_format_date(d)` | `date -> str` | `"Nov 13, 2025"` |
| `_median(vals)` | `List[float] -> float` | Safe median (returns 0.0 for empty) |
| `_average(vals)` | `List[float] -> float` | Safe average (returns 0.0 for empty) |
| `_period_label(lookback_days)` | `int -> str` | `30` -> `"Last 30 days"` |
| `_filter_by_city(listings, city)` | `List, str -> List` | Case-insensitive city filter, skips ZIP codes |
| `_get_audience_key_from_filters(filters)` | `Dict -> str` | Maps filter presets to audience keys |

## City Filtering

`_filter_by_city()` is applied by all builders because SimplyRETS `q` parameter is free-text
and may return results from nearby cities. The filter:
- Is case-insensitive
- Skips filtering when city is a ZIP code (all digits) -- API already filtered by `postalCodes`
- Skips filtering when city is `"Market"` or `"Unknown"`
- Performs exact match on city name
