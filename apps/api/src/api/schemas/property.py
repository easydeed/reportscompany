"""
Property Data Contract Schemas

Standardized Pydantic models for property data to eliminate field name
variations and provide consistent data structures across the application.

Usage:
    from api.schemas.property import ComparableProperty, normalize_comparable
    
    # Normalize raw data from any source
    normalized = normalize_comparable(raw_simplyrets_data)
    
    # Validate with Pydantic
    comp = ComparableProperty(**normalized)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
import re


class ComparableProperty(BaseModel):
    """
    Standardized comparable property schema.
    
    Accepts data from SimplyRETS, SiteX, or frontend and normalizes
    field names to a consistent format.
    """
    address: str = Field(default="", description="Full street address")
    city: str = Field(default="", description="City name")
    state: str = Field(default="", description="State abbreviation")
    zip_code: str = Field(default="", description="ZIP code")
    
    sale_price: float = Field(default=0, ge=0, description="Sale price in dollars")
    list_price: Optional[float] = Field(default=None, ge=0, description="Original list price")
    sold_date: str = Field(default="", description="Sale date (formatted)")
    
    sqft: int = Field(default=0, ge=0, description="Living area square footage")
    bedrooms: int = Field(default=0, ge=0, description="Number of bedrooms")
    bathrooms: float = Field(default=0, ge=0, description="Number of bathrooms")
    year_built: int = Field(default=0, ge=1800, description="Year property was built")
    lot_size: int = Field(default=0, ge=0, description="Lot size in square feet")
    
    price_per_sqft: float = Field(default=0, ge=0, description="Price per square foot")
    distance_miles: Optional[float] = Field(default=None, ge=0, description="Distance from subject in miles")
    
    latitude: Optional[float] = Field(default=None, description="GPS latitude")
    longitude: Optional[float] = Field(default=None, description="GPS longitude")
    
    pool: bool = Field(default=False, description="Has pool")
    garage: Optional[int] = Field(default=None, ge=0, description="Garage spaces")
    stories: Optional[int] = Field(default=None, ge=1, description="Number of stories")
    
    image_url: Optional[str] = Field(default=None, description="Primary property image URL")
    mls_id: Optional[str] = Field(default=None, description="MLS listing ID")
    
    class Config:
        populate_by_name = True
        extra = "ignore"  # Ignore unknown fields


class PropertyStats(BaseModel):
    """Statistics for a single property tier (PIQ, Low, Medium, High)."""
    distance: str = Field(default="0", description="Distance display string")
    sqft: Optional[int] = Field(default=None, description="Square footage")
    price_per_sqft: Optional[float] = Field(default=None, description="Price per sqft")
    year_built: Optional[int] = Field(default=None, description="Year built")
    lot_size: Optional[int] = Field(default=None, description="Lot size sqft")
    bedrooms: Optional[int] = Field(default=None, description="Bedrooms")
    bathrooms: Optional[float] = Field(default=None, description="Bathrooms")
    price: Optional[float] = Field(default=None, description="Price")
    stories: Optional[int] = Field(default=None, description="Stories")
    pools: Optional[int] = Field(default=None, description="Pool count")


class ReportStats(BaseModel):
    """Aggregate statistics for the property report."""
    total_comps: int = Field(default=0, ge=0, description="Total comparable properties")
    avg_sqft: float = Field(default=0, ge=0, description="Average square footage")
    avg_beds: float = Field(default=0, ge=0, description="Average bedrooms")
    avg_baths: float = Field(default=0, ge=0, description="Average bathrooms")
    price_low: float = Field(default=0, ge=0, description="Lowest sale price")
    price_high: float = Field(default=0, ge=0, description="Highest sale price")
    price_avg: float = Field(default=0, ge=0, description="Average sale price")
    
    piq: PropertyStats = Field(default_factory=PropertyStats, description="Property in Question stats")
    low: PropertyStats = Field(default_factory=PropertyStats, description="Low tier stats")
    medium: PropertyStats = Field(default_factory=PropertyStats, description="Medium tier stats")
    high: PropertyStats = Field(default_factory=PropertyStats, description="High tier stats")


class PropertyReportContext(BaseModel):
    """Complete context for property report template rendering."""
    property: dict = Field(default_factory=dict, description="Subject property details")
    agent: dict = Field(default_factory=dict, description="Agent information")
    images: dict = Field(default_factory=dict, description="Image URLs for report")
    comparables: List[ComparableProperty] = Field(default_factory=list, description="Comparable properties")
    stats: ReportStats = Field(default_factory=ReportStats, description="Aggregate statistics")


# =============================================================================
# Field Normalization Functions
# =============================================================================

def _parse_distance(value: Any) -> Optional[float]:
    """
    Parse distance from various formats.
    
    Handles:
        - float/int: 0.5
        - string: "0.5", "0.5 mi", "0.5mi"
        - None: returns None
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove "mi" suffix and whitespace
        cleaned = re.sub(r'\s*mi\s*$', '', str(value).strip(), flags=re.IGNORECASE)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    return None


def _parse_int(value: Any, default: int = 0) -> int:
    """Safely parse integer from various types."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))  # Handle "1234.0"
        except ValueError:
            return default
    return default


def _parse_float(value: Any, default: float = 0.0) -> float:
    """Safely parse float from various types."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,]', '', value.strip())
        try:
            return float(cleaned) if cleaned else default
        except ValueError:
            return default
    return default


def _get_first_photo(photos: Any) -> Optional[str]:
    """Extract first photo URL from photos array or string."""
    if not photos:
        return None
    if isinstance(photos, str):
        return photos
    if isinstance(photos, list) and photos:
        return photos[0] if isinstance(photos[0], str) else None
    return None


def normalize_comparable(raw: dict) -> dict:
    """
    Normalize field names from any data source to standard format.
    
    Handles variations from:
        - SimplyRETS API (closePrice, listDate, area, etc.)
        - SiteX API (sale_price, sqft, etc.)
        - Frontend wizard (lat/lng, photo_url, etc.)
    
    Args:
        raw: Raw comparable data from any source
        
    Returns:
        Normalized dictionary matching ComparableProperty schema
    """
    # Address fields
    address = (
        raw.get("address") or 
        raw.get("full_address") or 
        raw.get("streetAddress") or
        ""
    )
    if isinstance(address, dict):
        # SimplyRETS returns address as object
        address = f"{address.get('streetNumber', '')} {address.get('streetName', '')}".strip()
    
    city = raw.get("city") or ""
    if isinstance(city, dict):
        city = ""
    if not city and isinstance(raw.get("address"), dict):
        city = raw.get("address", {}).get("city", "")
        
    state = raw.get("state") or ""
    if not state and isinstance(raw.get("address"), dict):
        state = raw.get("address", {}).get("state", "")
        
    zip_code = raw.get("zip_code") or raw.get("zip") or raw.get("postalCode") or ""
    if not zip_code and isinstance(raw.get("address"), dict):
        zip_code = raw.get("address", {}).get("postalCode", "")
    
    # Price fields
    sale_price = _parse_float(
        raw.get("sale_price") or 
        raw.get("closePrice") or 
        raw.get("price") or 
        raw.get("listPrice") or
        0
    )
    
    list_price = _parse_float(raw.get("list_price") or raw.get("listPrice"))
    
    # Date fields
    sold_date = (
        raw.get("sold_date") or 
        raw.get("sale_date") or 
        raw.get("closeDate") or
        raw.get("listDate") or
        ""
    )
    
    # Size/feature fields
    sqft = _parse_int(
        raw.get("sqft") or 
        raw.get("area") or 
        raw.get("living_area") or 
        raw.get("livingArea") or
        raw.get("square_feet") or
        0
    )
    
    bedrooms = _parse_int(
        raw.get("bedrooms") or 
        raw.get("beds") or 
        raw.get("bedsTotalInteger") or
        0
    )
    
    bathrooms = _parse_float(
        raw.get("bathrooms") or 
        raw.get("baths") or 
        raw.get("bathsFull") or
        0
    )
    # Add half baths if available
    half_baths = _parse_float(raw.get("bathsHalf") or 0)
    if half_baths:
        bathrooms += half_baths * 0.5
    
    year_built = _parse_int(
        raw.get("year_built") or 
        raw.get("yearBuilt") or 
        raw.get("built") or
        0
    )
    
    lot_size = _parse_int(
        raw.get("lot_size") or 
        raw.get("lotSize") or 
        raw.get("lot_sqft") or
        raw.get("lotSizeArea") or
        0
    )
    
    # Calculate price per sqft if not provided
    price_per_sqft = _parse_float(
        raw.get("price_per_sqft") or 
        raw.get("pricePerSqft") or 
        raw.get("ppsf")
    )
    if not price_per_sqft and sqft > 0 and sale_price > 0:
        price_per_sqft = round(sale_price / sqft, 2)
    
    # Location fields
    latitude = _parse_float(
        raw.get("latitude") or 
        raw.get("lat") or 
        (raw.get("geo", {}) or {}).get("lat")
    ) or None
    
    longitude = _parse_float(
        raw.get("longitude") or 
        raw.get("lng") or 
        raw.get("lon") or
        (raw.get("geo", {}) or {}).get("lng")
    ) or None
    
    # Distance
    distance_miles = _parse_distance(
        raw.get("distance_miles") or 
        raw.get("distance")
    )
    
    # Features
    pool = bool(
        raw.get("pool") or 
        raw.get("has_pool") or 
        raw.get("poolYN")
    )
    
    garage = _parse_int(raw.get("garage") or raw.get("garageSpaces")) or None
    stories = _parse_int(raw.get("stories") or raw.get("storiesTotal")) or None
    
    # Image URL
    image_url = (
        raw.get("image_url") or 
        raw.get("photo_url") or 
        raw.get("streetViewUrl") or
        raw.get("primaryPhotoUrl") or
        _get_first_photo(raw.get("photos"))
    )
    
    # MLS ID
    mls_id = raw.get("mls_id") or raw.get("mlsId") or raw.get("listingId")
    
    return {
        "address": address,
        "city": city,
        "state": state,
        "zip_code": str(zip_code),
        "sale_price": sale_price,
        "list_price": list_price,
        "sold_date": sold_date,
        "sqft": sqft,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "year_built": year_built,
        "lot_size": lot_size,
        "price_per_sqft": price_per_sqft,
        "latitude": latitude,
        "longitude": longitude,
        "distance_miles": distance_miles,
        "pool": pool,
        "garage": garage,
        "stories": stories,
        "image_url": image_url,
        "mls_id": mls_id,
    }


def normalize_comparables(raw_list: List[dict]) -> List[dict]:
    """Normalize a list of comparable properties."""
    return [normalize_comparable(comp) for comp in raw_list]

