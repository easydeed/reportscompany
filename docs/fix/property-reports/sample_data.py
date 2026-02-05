# Sample Test Data for Property Reports
# Use this to test template rendering

sample_context = {
    "property": {
        "street_address": "1847 Hillcrest Drive",
        "city": "Beverly Hills",
        "state": "CA",
        "zip_code": "90210",
        "full_address": "1847 Hillcrest Drive, Beverly Hills, CA 90210",
        "owner_name": "John & Jane Smith",
        "secondary_owner": None,
        "county": "Los Angeles",
        "apn": "4352-017-023",
        "bedrooms": 4,
        "bathrooms": 3.5,
        "sqft": 3240,
        "lot_size": 8500,
        "year_built": 1985,
        "garage": 2,
        "pool": "Yes",
        "zoning": "R-1",
        "property_type": "Single Family Residence",
        "assessed_value": 1850000,
        "land_value": 1200000,
        "improvement_value": 650000,
        "tax_amount": 22450,
        "tax_year": 2024,
        "legal_description": "LOT 23 OF TRACT NO. 12345",
        "census_tract": "7008.02"
    },
    
    "agent": {
        "name": "Alexandra Reynolds",
        "title": "Realtor®",
        "license": "DRE# 01234567",
        "phone": "(310) 555-0147",
        "email": "alexandra@luxuryestates.com",
        "company_name": "Luxury Estates Group",
        "photo_url": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=200&q=80",
        "logo_url": None,  # Set to None to test fallback
        "company_short": "LE",
        "company_tagline": "Your Home, Our Passion"
    },
    
    "comparables": [
        {
            "address": "1923 Sunset Ridge",
            "sale_price": 2150000,
            "sold_date": "01/15/2024",
            "sqft": 3100,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 1992,
            "lot_size": 7800,
            "price_per_sqft": 694,
            "distance_miles": 0.3,
            "map_image_url": "https://maps.googleapis.com/maps/api/staticmap?center=34.0736,-118.4004&zoom=17&size=400x200&maptype=satellite",
            "pool": True
        },
        {
            "address": "2045 Canyon View",
            "sale_price": 1975000,
            "sold_date": "02/08/2024",
            "sqft": 2980,
            "bedrooms": 4,
            "bathrooms": 3.5,
            "year_built": 1988,
            "lot_size": 8200,
            "price_per_sqft": 663,
            "distance_miles": 0.5,
            "map_image_url": "https://maps.googleapis.com/maps/api/staticmap?center=34.0756,-118.4024&zoom=17&size=400x200&maptype=satellite",
            "pool": False
        },
        {
            "address": "1756 Laurel Heights",
            "sale_price": 2280000,
            "sold_date": "01/28/2024",
            "sqft": 3450,
            "bedrooms": 5,
            "bathrooms": 4,
            "year_built": 1995,
            "lot_size": 9100,
            "price_per_sqft": 661,
            "distance_miles": 0.4,
            "map_image_url": "https://maps.googleapis.com/maps/api/staticmap?center=34.0716,-118.3984&zoom=17&size=400x200&maptype=satellite",
            "pool": True
        },
        {
            "address": "2112 Oak Terrace",
            "sale_price": 2050000,
            "sold_date": "02/20/2024",
            "sqft": 3200,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 1990,
            "lot_size": 8000,
            "price_per_sqft": 641,
            "distance_miles": 0.6,
            "map_image_url": "https://maps.googleapis.com/maps/api/staticmap?center=34.0726,-118.4044&zoom=17&size=400x200&maptype=satellite",
            "pool": True
        }
    ],
    
    "stats": {
        "total_comps": 4,
        "avg_sqft": 3183,
        "avg_beds": 4.25,
        "avg_baths": 3.38,
        "price_low": 1975000,
        "price_high": 2280000,
        "piq": {
            "sqft": 3240,
            "bedrooms": 4,
            "price": 2100000  # Estimated value
        },
        "low": {
            "price": 1975000
        },
        "medium": {
            "price": 2100000
        },
        "high": {
            "price": 2280000
        }
    },
    
    "images": {
        "hero": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200&q=80",
        "aerial_map": "https://maps.googleapis.com/maps/api/staticmap?center=34.0736,-118.4004&zoom=18&size=800x600&maptype=satellite"
    },
    
    # Optional: Custom theme color override
    "theme_color": None  # Set to hex like "#1B365D" to override primary color
}


# Custom Jinja2 filters needed for rendering
def format_currency(value):
    """Format number as currency: 1234567 -> $1,234,567"""
    if value is None:
        return ""
    return f"${value:,.0f}"


def format_number(value):
    """Format number with commas: 1234567 -> 1,234,567"""
    if value is None:
        return ""
    return f"{value:,.0f}"


# Register these filters in your Jinja2 environment:
# env.filters['format_currency'] = format_currency
# env.filters['format_number'] = format_number
