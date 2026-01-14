# Property Reports Template System - Implementation Guide

## Overview

This document provides complete instructions for implementing the unified 5-theme property report system in TrendyReports. All templates use the **same data contract** and are **self-contained** (no orchestrator pattern).

---

## 🎯 Goals

1. **Add 3 new themes**: Classic, Modern, Elegant (joining existing Teal and Bold)
2. **Unify template system**: All themes use identical data structure
3. **Simplify PropertyReportBuilder**: Remove dual-loader complexity
4. **Delete legacy orchestrator system**: Remove old seller_report.jinja2 and fragments

---

## 📁 File Locations

### New Templates to Add
Place these in `apps/worker/src/worker/templates/property/`:

```
property/
├── teal/
│   └── teal_report.jinja2      # EXISTS - Teal theme
├── bold/
│   └── bold_report.jinja2      # EXISTS - Bold theme  
├── classic/
│   └── classic_report.jinja2   # NEW - Classic theme
├── modern/
│   └── modern_report.jinja2    # NEW - Modern theme
└── elegant/
    └── elegant_report.jinja2   # NEW - Elegant theme
```

### Files to DELETE (Legacy Orchestrator System)
Remove these after migration:

```
DELETE: apps/worker/src/worker/templates/reports/seller/
├── seller_report.jinja2          # Orchestrator - DELETE
├── seller_base.jinja2            # Base CSS - DELETE
├── bases/
│   ├── theme_1_classic.jinja2    # DELETE
│   ├── theme_2_modern.jinja2     # DELETE
│   ├── theme_3_elegant.jinja2    # DELETE
│   ├── theme_4_teal.jinja2       # DELETE (using new self-contained)
│   └── theme_5_bold.jinja2       # DELETE (using new self-contained)
└── seller_*.jinja2               # All 21 page fragments - DELETE
```

---

## 🎨 Theme Summary

| Theme | Primary Color | Secondary | Fonts | Target Audience |
|-------|--------------|-----------|-------|-----------------|
| **Teal** | #34d1c3 | #18235c | Montserrat | General market |
| **Bold** | #15216E | #D69649 | Oswald + Montserrat | Luxury/confident |
| **Classic** | #1B365D | #4A90A4 | Merriweather + Source Sans Pro | Traditional |
| **Modern** | #FF6B5B | #1A1F36 | Space Grotesk + DM Sans | Urban/young |
| **Elegant** | #722F37 | #C9A962 | Playfair Display + Montserrat | High-end luxury |

---

## 📊 Unified Data Contract

All 5 templates expect this exact context structure:

```python
context = {
    # Property Information
    "property": {
        "street_address": str,      # "1358 5th Street"
        "city": str,                # "La Verne"
        "state": str,               # "CA"
        "zip_code": str,            # "91750"
        "full_address": str,        # "1358 5th St, La Verne, CA 91750"
        "owner_name": str | None,
        "secondary_owner": str | None,
        "mailing_address": str | None,
        "apn": str | None,
        "county": str | None,
        "census_tract": str | None,
        "legal_description": str | None,
        "bedrooms": int | None,
        "bathrooms": float | None,
        "sqft": int | None,
        "lot_size": int | None,
        "year_built": int | None,
        "property_type": str | None,
        "zoning": str | None,
        "pool": str | None,
        "garage": str | None,
        "fireplace": str | None,
        "assessed_value": float | None,
        "land_value": float | None,
        "improvement_value": float | None,
        "tax_amount": float | None,
        "tax_year": int | None,
    },
    
    # Agent Information
    "agent": {
        "name": str,
        "title": str | None,
        "license": str | None,
        "phone": str | None,
        "email": str | None,
        "address": str | None,
        "photo_url": str | None,
        "company_name": str | None,
        "company_short": str | None,    # For elegant theme logo
        "company_tagline": str | None,
    },
    
    # Images
    "images": {
        "hero": str | None,           # Cover photo URL
        "aerial_map": str | None,     # Aerial map URL
    },
    
    # Comparables (list of 4-6 properties)
    "comparables": [
        {
            "address": str,
            "sale_price": float,
            "sold_date": str,         # "5/10/23"
            "sqft": int,
            "bedrooms": int,
            "bathrooms": float,
            "year_built": int,
            "lot_size": int,
            "price_per_sqft": float,
            "distance_miles": float | None,
            "pool": bool,
            "map_image_url": str | None,
        }
    ],
    
    # Statistics
    "stats": {
        "total_comps": int,
        "avg_sqft": float,
        "avg_beds": float,
        "avg_baths": float,
        "price_low": float,
        "price_high": float,
        "piq": {                      # Property In Question
            "distance": str,
            "sqft": int,
            "price_per_sqft": float,
            "year_built": int,
            "lot_size": int,
            "bedrooms": int,
            "bathrooms": float,
            "price": float,
        },
        "low": { ... },               # Same structure as piq
        "medium": { ... },
        "high": { ... },
    },
}
```

---

## 🔧 Custom Jinja2 Filters

Ensure these filters are registered in the Jinja2 environment:

```python
def format_currency(value):
    """Format as $XXX,XXX"""
    if value is None:
        return "-"
    try:
        return f"${int(value):,}"
    except (ValueError, TypeError):
        return "-"

def format_currency_short(value):
    """Format as $XXXk or $X.Xm"""
    if value is None:
        return "-"
    try:
        val = float(value)
        if val >= 1_000_000:
            return f"${val/1_000_000:.1f}m"
        elif val >= 1_000:
            return f"${int(val/1_000)}k"
        return f"${int(val)}"
    except (ValueError, TypeError):
        return "-"

def format_number(value):
    """Format with commas: 1,234"""
    if value is None:
        return "-"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "-"

# Register filters
env.filters['format_currency'] = format_currency
env.filters['format_currency_short'] = format_currency_short
env.filters['format_number'] = format_number
```

---

## 🏗️ PropertyReportBuilder Refactor

### Before (Complex dual-loader)

```python
# OLD - Remove this pattern
if self.use_v0_teal:
    template_dir = TEMPLATES_V0_DIR
else:
    template_dir = TEMPLATES_BASE_DIR / self.report_type
    
# OLD - Theme selection in orchestrator
if theme_number == 4:
    # Special handling for teal
elif theme_number == 5:
    # Special handling for bold
```

### After (Simple theme map)

```python
# NEW - Unified theme system
THEME_TEMPLATES = {
    "teal": "property/teal/teal_report.jinja2",
    "bold": "property/bold/bold_report.jinja2",
    "classic": "property/classic/classic_report.jinja2",
    "modern": "property/modern/modern_report.jinja2",
    "elegant": "property/elegant/elegant_report.jinja2",
}

# Theme number to name mapping (for backward compatibility)
THEME_NUMBER_MAP = {
    1: "classic",
    2: "modern", 
    3: "elegant",
    4: "teal",
    5: "bold",
}

class PropertyReportBuilder:
    def __init__(self, context: dict, theme: str = "teal"):
        self.context = context
        self.theme = theme
        
    def render_html(self) -> str:
        template_path = THEME_TEMPLATES.get(self.theme, THEME_TEMPLATES["teal"])
        template = self.env.get_template(template_path)
        return template.render(**self.context)
```

---

## 📝 Implementation Steps

### Step 1: Add New Template Files

1. Create directories:
   ```bash
   mkdir -p apps/worker/src/worker/templates/property/classic
   mkdir -p apps/worker/src/worker/templates/property/modern
   mkdir -p apps/worker/src/worker/templates/property/elegant
   ```

2. Copy the provided `.jinja2` files:
   - `classic_report.jinja2` → `property/classic/`
   - `modern_report.jinja2` → `property/modern/`
   - `elegant_report.jinja2` → `property/elegant/`

### Step 2: Update PropertyReportBuilder

1. Add the `THEME_TEMPLATES` and `THEME_NUMBER_MAP` constants
2. Simplify the `__init__` method to accept theme name
3. Update `render_html()` to use the simple template lookup
4. Ensure all custom filters are registered
5. Add backward compatibility for theme numbers

### Step 3: Update API Endpoints

In `apps/api/src/api/routes/property.py`:

```python
class GenerateReportRequest(BaseModel):
    property_id: str
    theme: str = "teal"  # teal, bold, classic, modern, elegant
    # OR for backward compatibility:
    theme_number: int = 4  # 1-5

@router.post("/generate")
async def generate_report(request: GenerateReportRequest):
    # Convert theme_number to theme name if provided
    theme = request.theme
    if hasattr(request, 'theme_number') and request.theme_number:
        theme = THEME_NUMBER_MAP.get(request.theme_number, "teal")
    
    # Build report with theme
    builder = PropertyReportBuilder(context, theme=theme)
    html = builder.render_html()
    # ... rest of generation
```

### Step 4: Update Frontend Theme Selector

In `apps/web/components/property/ThemeSelector.tsx`:

```typescript
const THEMES = [
  { id: "classic", name: "Classic", description: "Traditional & trustworthy", colors: ["#1B365D", "#4A90A4"] },
  { id: "modern", name: "Modern", description: "Fresh & contemporary", colors: ["#FF6B5B", "#1A1F36"] },
  { id: "elegant", name: "Elegant", description: "Luxury & sophisticated", colors: ["#722F37", "#C9A962"] },
  { id: "teal", name: "Teal", description: "Clean & professional", colors: ["#34d1c3", "#18235c"] },
  { id: "bold", name: "Bold", description: "Strong & confident", colors: ["#15216E", "#D69649"] },
];
```

### Step 5: Delete Legacy Files

After confirming the new system works:

```bash
# Remove old orchestrator system
rm -rf apps/worker/src/worker/templates/reports/seller/
```

### Step 6: Add Template Tests

```python
# tests/test_property_templates.py
import pytest
from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES

SAMPLE_CONTEXT = {
    "property": {
        "street_address": "123 Test St",
        "city": "Test City",
        "state": "CA",
        "zip_code": "90210",
        "full_address": "123 Test St, Test City, CA 90210",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1500,
    },
    "agent": {
        "name": "Test Agent",
        "phone": "(555) 555-5555",
        "email": "test@example.com",
    },
    "images": {},
    "comparables": [],
    "stats": {
        "total_comps": 0,
        "avg_sqft": 0,
        "avg_beds": 0,
        "avg_baths": 0,
        "price_low": 0,
        "price_high": 0,
        "piq": {},
        "low": {},
        "medium": {},
        "high": {},
    },
}

@pytest.mark.parametrize("theme", list(THEME_TEMPLATES.keys()))
def test_theme_renders(theme):
    """Verify all themes produce valid HTML."""
    builder = PropertyReportBuilder(SAMPLE_CONTEXT, theme=theme)
    html = builder.render_html()
    
    assert '<html' in html
    assert '</html>' in html
    assert 'undefined' not in html.lower()
    assert '{{' not in html  # No unrendered Jinja2

def test_all_themes_have_templates():
    """Verify all themes have template files."""
    for theme, path in THEME_TEMPLATES.items():
        full_path = TEMPLATES_DIR / path
        assert full_path.exists(), f"Missing template for {theme}: {path}"
```

---

## ✅ Verification Checklist

- [ ] All 5 theme templates are in `property/` directory
- [ ] PropertyReportBuilder uses simple theme map
- [ ] Custom filters (format_currency, format_number, format_currency_short) registered
- [ ] API endpoint accepts theme name parameter
- [ ] Frontend ThemeSelector shows all 5 themes
- [ ] Legacy `reports/seller/` directory deleted
- [ ] Tests pass for all themes
- [ ] PDF generation works for all themes (no blank pages)

---

## 🐛 Known Issues to Fix

From the integration analysis:

1. **Add `| default()` to all template variables** - Already done in new templates
2. **Standardized field names** - All templates use same variable names
3. **No orchestrator complexity** - Each template is self-contained
4. **Print CSS fixed** - All templates have proper `@page` and `page-break` rules

---

## 📋 Quick Reference

### Theme Names
- `classic` - Navy + Sky Blue, traditional
- `modern` - Coral + Midnight, contemporary  
- `elegant` - Burgundy + Gold, luxury
- `teal` - Teal + Navy, professional
- `bold` - Navy + Gold, confident

### Theme Numbers (Legacy)
- 1 = classic
- 2 = modern
- 3 = elegant
- 4 = teal
- 5 = bold

### Required Filters
- `format_currency` - $XXX,XXX
- `format_currency_short` - $XXXk or $X.Xm
- `format_number` - XXX,XXX

---

*Document Version: 1.0 - January 14, 2026*
