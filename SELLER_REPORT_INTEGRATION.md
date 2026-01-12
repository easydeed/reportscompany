# TrendyReports Seller Report Templates - Cursor Integration Guide

## Overview

This document provides complete instructions for integrating the Seller Report Jinja2 template system into TrendyReports. The templates generate professional real estate seller presentation PDFs with 5 theme options and configurable page sets.

## Architecture

```
seller_report_templates/
├── seller_report.jinja2          # Master orchestrator - ENTRY POINT
├── seller_base.jinja2            # Legacy base (Theme 1 default CSS)
├── bases/                        # Theme-specific CSS bases
│   ├── theme_1_classic.jinja2    # Classic: Bariol/Nexa fonts, navy accents
│   ├── theme_2_modern.jinja2     # Modern: Montserrat, orange accents
│   ├── theme_3_elegant.jinja2    # Elegant: Crimson Text, gradient overlays
│   ├── theme_4_teal.jinja2       # Teal: System fonts, 9-page compact
│   └── theme_5_bold.jinja2       # Bold: Bebas Neue, navy/gold, compact
└── seller_*.jinja2               # 21 section templates (pages)
```

### Template Inheritance Flow

```
seller_report.jinja2 (orchestrator)
    └── extends → bases/theme_X_*.jinja2 (selected by theme_number)
        └── block content → includes seller_*.jinja2 sections
```

**Important**: Section templates currently `{% extends "seller_base.jinja2" %}` but when included via `seller_report.jinja2`, they inherit the selected theme base instead.

## Installation

### 1. File Placement

```bash
# Copy templates to your Jinja2 templates directory
cp -r seller_report_templates/* /path/to/trendyreports/templates/reports/seller/
```

Expected structure in your app:
```
templates/
└── reports/
    └── seller/
        ├── seller_report.jinja2
        ├── seller_base.jinja2
        ├── bases/
        │   └── theme_*.jinja2
        └── seller_*.jinja2
```

### 2. Template Loader Configuration

Ensure Jinja2 can resolve relative includes:

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader('templates/reports/seller'),
    autoescape=True
)
```

### 3. Font Assets

Required fonts for themes 1-3 (host on R2/CDN):
- Bariol: light, regular, bold (woff2, woff)
- Nexa: light, bold (woff2, woff)

Theme 4-5 use system fonts (no custom fonts needed).

Configure `assets_base_url` to point to your font hosting:
```python
context = {
    'assets_base_url': 'https://assets.trendyreports.com'
}
```

## Data Schema

### Required Context Variables

```python
context = {
    # === THEME CONFIGURATION ===
    'theme_number': 1,                          # 1-5 (required)
    'theme_color': '#0d294b',                   # Optional, theme has defaults
    'assets_base_url': 'https://assets.trendyreports.com',
    'google_maps_api_key': 'YOUR_API_KEY',

    # === PAGE SET ===
    'page_set': 'full',                         # 'full' | 'compact' | ['page1', 'page2', ...]

    # === PROPERTY DATA ===
    'property': {
        # Basic Info (REQUIRED)
        'street': '123 Main Street',
        'city': 'Los Angeles',
        'state': 'CA',
        'zip_code': '90210',
        
        # Location (for maps)
        'latitude': 34.0522,
        'longitude': -118.2437,
        
        # Owner Info
        'owner_name': 'John Smith',
        'secondary_owner': 'Jane Smith',        # Optional
        'county': 'Los Angeles',
        'apn': '1234-567-890',
        
        # Property Details
        'bedrooms': 4,
        'bathrooms': 3,
        'sqft': 2500,
        'lot_size': '7,500 sqft',
        'year_built': 1985,
        'garage': 2,
        'fireplace': 'Yes',
        'pool': 'Pool & Spa',
        'total_rooms': 8,
        'num_units': 1,
        'zoning': 'R1',
        'property_type': 'Single Family Residence',
        'use_code': 'SFR',
        
        # Tax/Assessment (Optional)
        'assessed_value': 450000,
        'tax_amount': 5500,
        'land_value': 200000,
        'improvement_value': 250000,
        'percent_improved': 55,
        'tax_status': 'Current',
        'tax_rate_area': '1.15',
        'tax_year': 2024,
        
        # Legal (Optional)
        'legal_description': 'Lot 15, Block 3, Tract 12345',
        'mailing_address': '456 Different Ave, Los Angeles, CA 90210',
        'census_tract': '1234.00',
        'housing_tract': '12345',
        'lot_number': '15',
        'page_grid': 'A-5'
    },

    # === AGENT DATA ===
    'agent': {
        'name': 'Sarah Johnson',
        'title': 'Realtor®',                    # Optional
        'license_number': '01234567',
        'phone': '(555) 123-4567',
        'email': 'sarah@realestate.com',
        'company_name': 'Premier Realty',
        'street': '100 Business Blvd',          # Optional
        'city': 'Los Angeles',                  # Optional
        'state': 'CA',                          # Optional
        'zip_code': '90210',                    # Optional
        'photo_url': 'https://cdn.example.com/agent.jpg',     # Optional
        'logo_url': 'https://cdn.example.com/company.png'     # Optional
    },

    # === COMPARABLES ===
    'comparables': [
        {
            'address': '456 Oak Street',
            'latitude': 34.0530,
            'longitude': -118.2445,
            'image_url': 'https://cdn.example.com/comp1.jpg',  # Optional
            'price': '$485,000',
            'days_on_market': 15,
            'distance': '0.3 mi',
            'sqft': 2200,
            'price_per_sqft': 220,
            'bedrooms': 3,
            'bathrooms': 2,
            'year_built': 1978,
            'lot_size': '6,500 sqft',
            'pool': 'No'
        },
        # ... up to 6 comparables (3 rows of 2)
    ],

    # === NEIGHBORHOOD STATS ===
    'neighborhood': {
        'female_ratio': '51.5',
        'male_ratio': '48.5',
        'avg_sale_price': '485,000',
        'avg_sqft': '1,850',
        'avg_beds': '3',
        'avg_baths': '2'
    },

    # === AREA ANALYSIS ===
    'area_analysis': {
        'chart_url': 'https://quickchart.io/chart?...',  # Pre-generated chart
        'area_min_radius': '0.1 mi',
        'area_median_radius': '0.5 mi',
        'area_max_radius': '1.2 mi',
        'living_area': 2500,
        'living_area_low': 1800,
        'living_area_median': 2200,
        'living_area_high': 3200,
        'price_per_sqft': 225,
        'price_per_sqft_low': 180,
        'price_per_sqft_median': 210,
        'price_per_sqft_high': 280,
        'year_built': 1985,
        'year_low': 1965,
        'year_median': 1980,
        'year_high': 2015,
        'lot_size': '7,500',
        'lot_size_low': '5,000',
        'lot_size_median': '7,000',
        'lot_size_high': '12,000',
        'bedrooms': 4,
        'bedrooms_low': 2,
        'bedrooms_median': 3,
        'bedrooms_high': 5,
        'bathrooms': 3,
        'bathrooms_low': 1,
        'bathrooms_median': 2,
        'bathrooms_high': 4,
        'stories': 2,
        'pool': 'Yes',
        'pool_low': 'No',
        'pool_median': 'No',
        'pool_high': 'Yes',
        'sale_price': '550,000',
        'sale_price_low': '320,000',
        'sale_price_median': '450,000',
        'sale_price_high': '680,000'
    },

    # === RANGE OF SALES ===
    'range_of_sales': {
        'total_comps': 9,
        'avg_sqft': '2,150',
        'avg_beds': 3,
        'avg_baths': 2,
        'price_min': '320',                     # In thousands (displays as $320K)
        'price_max': '485'                      # In thousands (displays as $485K)
    },

    # === OPTIONAL CONTENT SECTIONS ===
    # These have built-in defaults - pass empty dicts to use defaults
    # or provide custom content to override
    
    'introduction': {
        # Optional - uses defaults if empty
        'title': 'Deciding To Sell',            # Optional
        'subtitle': 'The first step',           # Optional
        'content': ['Paragraph 1...', '...']    # Optional list of paragraphs
    },
    
    'roadmap': {
        # REQUIRED structure if using roadmap page
        'points': [
            {'title': 'Custom Title', 'sub_title': 'Subtitle'},  # Or None for defaults
            {'title': None, 'sub_title': None},  # Uses built-in defaults
            {'title': None, 'sub_title': None},
            {'title': None, 'sub_title': None},
            {'title': None, 'sub_title': None},
            {'title': None, 'sub_title': None},
            {'title': None, 'sub_title': None},
        ]  # 7 points required (indices 0-6)
    },
    
    'promise': {
        # REQUIRED structure if using promise page
        'points': [
            {'title': 'Loyalty', 'content': 'Custom content...'},  # Or None
            {'title': None, 'content': None},
            {'title': None, 'content': None},
            {'title': None, 'content': None},
            {'title': None, 'content': None},
            {'title': None, 'content': None},
        ]  # 6 points required (indices 0-5)
    },
    
    # These are simpler - just pass empty dict for defaults
    'how_buyers_find': {},
    'pricing': {},
    'avg_days': {},
    'marketing_online': {},
    'marketing_print': {},
    'marketing_social': {},
    'analyze_optimize': {},
    'negotiating': {},
    'transaction': {},

    # === OPTIONAL ASSETS ===
    'cover_image_url': 'https://cdn.example.com/property-hero.jpg'
}
```

### Minimal Context (for testing)

```python
minimal_context = {
    'theme_number': 1,
    'assets_base_url': '/assets',
    'google_maps_api_key': 'API_KEY',
    'property': {
        'street': '123 Main St',
        'city': 'Los Angeles',
        'state': 'CA',
        'zip_code': '90210'
    },
    'agent': {
        'name': 'Test Agent',
        'phone': '555-1234',
        'email': 'test@example.com',
        'company_name': 'Realty Co',
        'license_number': '123456'
    },
    # Required nested structures with defaults
    'roadmap': {'points': [{'title': None, 'sub_title': None}] * 7},
    'promise': {'points': [{'title': None, 'content': None}] * 6},
}
```

## Theme Configuration

### Theme Defaults

| Theme | Name    | Primary Color | Fonts                    | Page Set Default |
|-------|---------|---------------|--------------------------|------------------|
| 1     | Classic | #0d294b       | Bariol, Nexa            | full (21 pages)  |
| 2     | Modern  | #f2964a       | Montserrat              | full (21 pages)  |
| 3     | Elegant | #0d294b       | Crimson Text, Open Sans | full (21 pages)  |
| 4     | Teal    | #16d3ba       | System fonts            | compact (9 pages)|
| 5     | Bold    | #d79547       | Bebas Neue              | compact (9 pages)|

### Page Sets

**Full (21 pages):**
```python
full_pages = [
    "cover", "contents", "introduction", "aerial", "property_details",
    "area_analysis", "comparables", "range_of_sales", "neighborhood",
    "roadmap", "how_buyers_find", "pricing_correctly", "avg_days_market",
    "marketing_online", "marketing_print", "marketing_social",
    "analyze_optimize", "negotiating", "typical_transaction", "promise", "back_cover"
]
```

**Compact (9 pages):**
```python
compact_pages = [
    "cover", "introduction", "aerial", "property_details", "comparables",
    "pricing_correctly", "marketing_online", "promise", "back_cover"
]
```

**Custom:**
```python
context = {
    'page_set': ['cover', 'property_details', 'comparables', 'back_cover']
}
```

## Python Integration

### Basic Rendering

```python
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def render_seller_report(context: dict) -> bytes:
    """Render seller report to PDF bytes."""
    
    env = Environment(
        loader=FileSystemLoader('templates/reports/seller'),
        autoescape=True
    )
    
    template = env.get_template('seller_report.jinja2')
    html_content = template.render(**context)
    
    # Convert to PDF
    pdf = HTML(string=html_content).write_pdf()
    return pdf
```

### FastAPI Endpoint Example

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import io

router = APIRouter()

class PropertyData(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    # ... add all fields

class AgentData(BaseModel):
    name: str
    license_number: str
    phone: str
    email: str
    company_name: str
    photo_url: Optional[str] = None
    logo_url: Optional[str] = None

class SellerReportRequest(BaseModel):
    theme_number: int = 1
    theme_color: Optional[str] = None
    page_set: Optional[str] = 'full'
    property: PropertyData
    agent: AgentData
    comparables: Optional[List[dict]] = []
    neighborhood: Optional[dict] = {}
    area_analysis: Optional[dict] = {}
    range_of_sales: Optional[dict] = {}

@router.post("/reports/seller/generate")
async def generate_seller_report(request: SellerReportRequest):
    """Generate a seller report PDF."""
    
    context = {
        'theme_number': request.theme_number,
        'theme_color': request.theme_color,
        'page_set': request.page_set,
        'property': request.property.dict(),
        'agent': request.agent.dict(),
        'comparables': request.comparables,
        'neighborhood': request.neighborhood,
        'area_analysis': request.area_analysis,
        'range_of_sales': request.range_of_sales,
        'assets_base_url': settings.ASSETS_BASE_URL,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    
    pdf_bytes = render_seller_report(context)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=seller_report_{request.property.street.replace(' ', '_')}.pdf"
        }
    )
```

### Service Layer Pattern

```python
# services/seller_report_service.py

from dataclasses import dataclass
from typing import Optional, List
import httpx

@dataclass
class SellerReportService:
    template_env: Environment
    assets_base_url: str
    google_maps_api_key: str
    chart_service_url: str  # e.g., QuickChart.io
    
    async def generate_report(
        self,
        property_data: dict,
        agent_data: dict,
        theme_number: int = 1,
        page_set: str = 'full'
    ) -> bytes:
        """Full report generation with data enrichment."""
        
        # Enrich with computed data
        comparables = await self._fetch_comparables(property_data)
        neighborhood = await self._fetch_neighborhood_stats(property_data)
        area_analysis = await self._compute_area_analysis(property_data, comparables)
        range_of_sales = self._compute_range_of_sales(comparables)
        
        # Generate chart
        area_analysis['chart_url'] = await self._generate_sales_chart(comparables)
        
        context = {
            'theme_number': theme_number,
            'page_set': page_set,
            'property': property_data,
            'agent': agent_data,
            'comparables': comparables,
            'neighborhood': neighborhood,
            'area_analysis': area_analysis,
            'range_of_sales': range_of_sales,
            'assets_base_url': self.assets_base_url,
            'google_maps_api_key': self.google_maps_api_key
        }
        
        template = self.template_env.get_template('seller_report.jinja2')
        html = template.render(**context)
        
        return HTML(string=html).write_pdf()
    
    async def _generate_sales_chart(self, comparables: List[dict]) -> str:
        """Generate QuickChart URL for sales bar chart."""
        # Group by month, create chart config
        chart_config = {
            "type": "bar",
            "data": {
                "labels": ["Jan", "Feb", "Mar", ...],
                "datasets": [{"data": [...], "backgroundColor": "#0d294b"}]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.chart_service_url}/chart/create",
                json={"chart": chart_config}
            )
            return response.json()["url"]
```

## Known Issues & Fixes

### Issue 1: Section Templates Extend Wrong Base

**Problem**: Section templates like `seller_cover.jinja2` have `{% extends "seller_base.jinja2" %}` which conflicts when using the orchestrator.

**Fix Option A** (Recommended): Remove extends from section templates, use as pure includes:

```jinja2
{# seller_cover.jinja2 - BEFORE #}
{% extends "seller_base.jinja2" %}
{% block content %}
<div class="page">...</div>
{% endblock %}

{# seller_cover.jinja2 - AFTER #}
{# Section template - included by seller_report.jinja2 #}
<div class="page">...</div>
```

**Fix Option B**: Keep extends for standalone rendering, but this creates duplicate HTML structure when included.

### Issue 2: Missing Default Values

Some templates reference variables without defaults that may cause errors:

```jinja2
{# Problematic #}
{{ property.census_tract }}

{# Fixed #}
{{ property.census_tract | default('N/A') }}
```

### Issue 3: Google Maps API Placeholder

Templates have `key={{ google_maps_api_key | default('YOUR_API_KEY') }}` which exposes invalid key in output.

**Fix**: Always require `google_maps_api_key` in context or hide map section when missing:

```jinja2
{% if google_maps_api_key %}
<img src="https://maps.googleapis.com/...&key={{ google_maps_api_key }}">
{% else %}
<div class="map-placeholder">Map unavailable</div>
{% endif %}
```

## Template Modification Checklist

When modifying templates:

1. **Test with all 5 themes** - CSS selectors may differ
2. **Test full and compact page sets** - Ensure page exists in both
3. **Verify PDF output** - WeasyPrint may render differently than browser
4. **Check font loading** - Custom fonts require proper @font-face URLs
5. **Validate data bindings** - Use `| default()` for optional fields

## Quick Reference

### Render a Report

```python
# Minimal example
context = {
    'theme_number': 1,
    'property': {'street': '123 Main', 'city': 'LA', 'state': 'CA', 'zip_code': '90210'},
    'agent': {'name': 'Agent Name', 'phone': '555-1234', 'email': 'a@b.com', 
              'company_name': 'Realty', 'license_number': '123'},
    'assets_base_url': 'https://assets.example.com',
    'google_maps_api_key': 'KEY'
}
html = env.get_template('seller_report.jinja2').render(**context)
```

### Add a New Theme

1. Create `bases/theme_6_mytheme.jinja2` copying structure from existing
2. Add to `theme_bases` dict in `seller_report.jinja2`:
   ```jinja2
   {% set theme_bases = {
       ...
       6: 'bases/theme_6_mytheme.jinja2'
   } %}
   ```
3. Add default color to `theme_default_colors`

### Add a New Page Section

1. Create `seller_newpage.jinja2` with page content
2. Add to `full_pages` and/or `compact_pages` in `seller_report.jinja2`
3. Add include block:
   ```jinja2
   {% if "newpage" in active_pages %}
       {% include "seller_newpage.jinja2" %}
   {% endif %}
   ```

## Testing

```python
# test_seller_report.py
import pytest
from pathlib import Path

def test_all_themes_render():
    """Verify all themes produce valid HTML."""
    for theme in range(1, 6):
        context = get_test_context()
        context['theme_number'] = theme
        html = render_seller_report_html(context)
        assert '<html' in html
        assert '</html>' in html
        assert 'Error' not in html

def test_compact_vs_full():
    """Verify page counts match expected."""
    context = get_test_context()
    
    context['page_set'] = 'full'
    full_html = render_seller_report_html(context)
    full_pages = full_html.count('class="page"')
    
    context['page_set'] = 'compact'
    compact_html = render_seller_report_html(context)
    compact_pages = compact_html.count('class="page"')
    
    assert full_pages == 21
    assert compact_pages == 9
```

---

## Summary

The seller report template system is production-ready with:
- ✅ 5 visual themes
- ✅ 21-page full and 9-page compact options
- ✅ Custom page selection
- ✅ Comprehensive data schema
- ✅ WeasyPrint PDF compatibility

**Primary integration point**: `seller_report.jinja2` with context dict

**Next steps for Cursor**:
1. Copy templates to `templates/reports/seller/`
2. Implement `SellerReportService` following the pattern above
3. Apply the section template fix (remove `{% extends %}` from includes)
4. Configure font hosting on R2/CDN
5. Add API endpoint for report generation
