# Data Contract Standardization Guide

## Status: ✅ IMPLEMENTED

Pydantic schemas and normalization functions have been added to:
- `apps/api/src/api/schemas/property.py`

## Previous State (Technical Debt)

The `property_builder.py` previously normalized field names from various sources:

```python
# Current normalization in worker (TECHNICAL DEBT)
latitude = comp.get("latitude") or comp.get("lat")
longitude = comp.get("longitude") or comp.get("lng") 
image_url = comp.get("image_url") or comp.get("photo_url") or comp.get("streetViewUrl")
distance_raw = comp.get("distance") or comp.get("distance_miles", "")
```

## Recommended Fix

### Option A: Pydantic Models at API Layer (Recommended)

Normalize data at the API layer before it reaches the worker:

```python
# apps/api/src/api/schemas/property.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class ComparableProperty(BaseModel):
    """Standardized comparable property schema."""
    address: str
    sale_price: float
    sold_date: str
    sqft: int
    bedrooms: int
    bathrooms: float
    year_built: int
    lot_size: int
    price_per_sqft: float
    distance_miles: Optional[float] = None
    pool: bool = False
    map_image_url: Optional[str] = None
    
    # Field aliases for backward compatibility
    class Config:
        populate_by_name = True
    
    @field_validator('distance_miles', mode='before')
    @classmethod
    def normalize_distance(cls, v, info):
        # Accept 'distance' or 'distance_miles'
        if v is None:
            raw = info.data.get('distance')
            if raw:
                return float(str(raw).replace('mi', '').strip())
        return v
    
    @field_validator('map_image_url', mode='before')
    @classmethod
    def normalize_image_url(cls, v, info):
        # Accept multiple field names
        if v is None:
            return (
                info.data.get('image_url') or 
                info.data.get('photo_url') or 
                info.data.get('streetViewUrl')
            )
        return v


class PropertyStats(BaseModel):
    """Standardized stats for analysis page."""
    distance: str = "0"
    sqft: Optional[int] = None
    price_per_sqft: Optional[float] = None
    year_built: Optional[int] = None
    lot_size: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    price: Optional[float] = None
    stories: Optional[int] = None
    pools: Optional[int] = None


class ReportStats(BaseModel):
    """Aggregate statistics for the report."""
    total_comps: int = 0
    avg_sqft: float = 0
    avg_beds: float = 0
    avg_baths: float = 0
    price_low: float = 0
    price_high: float = 0
    piq: PropertyStats = PropertyStats()
    low: PropertyStats = PropertyStats()
    medium: PropertyStats = PropertyStats()
    high: PropertyStats = PropertyStats()


class PropertyReportContext(BaseModel):
    """Complete context for property report templates."""
    property: dict  # Property details
    agent: dict     # Agent info
    images: dict    # Image URLs
    comparables: list[ComparableProperty]
    stats: ReportStats
```

### Option B: Normalize in Data Service

If you have a data service that fetches comparables:

```python
# apps/api/src/api/services/property_data.py

def normalize_comparable(raw: dict) -> dict:
    """Normalize field names from any data source."""
    return {
        "address": raw.get("address") or raw.get("full_address") or "",
        "sale_price": float(raw.get("sale_price") or raw.get("price") or 0),
        "sold_date": raw.get("sold_date") or raw.get("sale_date") or "",
        "sqft": int(raw.get("sqft") or raw.get("living_area") or raw.get("square_feet") or 0),
        "bedrooms": int(raw.get("bedrooms") or raw.get("beds") or 0),
        "bathrooms": float(raw.get("bathrooms") or raw.get("baths") or 0),
        "year_built": int(raw.get("year_built") or raw.get("built") or 0),
        "lot_size": int(raw.get("lot_size") or raw.get("lot_sqft") or 0),
        "price_per_sqft": float(raw.get("price_per_sqft") or raw.get("ppsf") or 0),
        "distance_miles": _parse_distance(raw.get("distance") or raw.get("distance_miles")),
        "pool": bool(raw.get("pool") or raw.get("has_pool")),
        "map_image_url": (
            raw.get("map_image_url") or 
            raw.get("image_url") or 
            raw.get("photo_url") or 
            raw.get("streetViewUrl")
        ),
    }

def _parse_distance(value) -> float | None:
    """Parse distance from various formats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # Handle "0.5 mi" format
    return float(str(value).replace("mi", "").strip())
```

## Migration Steps

1. **Add Pydantic models** to API layer
2. **Update API endpoints** to validate/normalize incoming data
3. **Remove normalization** from `property_builder.py`
4. **Test** with all data sources

## Benefits

- Single source of truth for field names
- Validation at API boundary
- Cleaner worker code
- Better error messages for invalid data
- Type hints for IDE support

## Priority

**Medium** - Current system works, this is cleanup/optimization.

---

## Implementation (January 2026)

### Files Created

**`apps/api/src/api/schemas/property.py`**

Contains:
- `ComparableProperty` - Pydantic model for normalized comparable data
- `PropertyStats` - Statistics for property tiers (PIQ, Low, Medium, High)
- `ReportStats` - Aggregate statistics for reports
- `PropertyReportContext` - Complete context for template rendering
- `normalize_comparable()` - Function to normalize field names from any source
- `normalize_comparables()` - Batch normalization for lists

### Usage Example

```python
from api.schemas.property import ComparableProperty, normalize_comparable

# Normalize raw SimplyRETS data
raw_data = {
    "closePrice": 450000,
    "area": 1800,
    "bedsTotalInteger": 3,
    "bathsFull": 2,
    "geo": {"lat": 34.0522, "lng": -118.2437}
}

normalized = normalize_comparable(raw_data)
# Returns: {"sale_price": 450000, "sqft": 1800, "bedrooms": 3, ...}

# Validate with Pydantic
comp = ComparableProperty(**normalized)
```

### Migration Notes

The `normalize_comparable()` function handles field variations from:
- **SimplyRETS**: `closePrice`, `area`, `bedsTotalInteger`, `geo.lat/lng`
- **SiteX**: `sale_price`, `sqft`, `bedrooms`, `latitude/longitude`  
- **Frontend**: `price`, `beds`, `baths`, `lat/lng`, `photo_url`

Worker's `property_builder.py` can gradually adopt these schemas to reduce
duplicate normalization logic.
