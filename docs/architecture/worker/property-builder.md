# Property Report Builder

> `apps/worker/src/worker/property_builder.py` (800 lines)
> Renders property CMA reports using self-contained Jinja2 templates with 5 themes.

## Overview

`PropertyReportBuilder` takes a report data dictionary and renders a complete HTML report
using Jinja2 templates. Each of the 5 themes extends a shared base template and overrides
visual styles while consuming the same unified data contract.

## 5 Themes

| # | Name | Display Font | Body Font | Colors | Style |
|---|------|-------------|-----------|--------|-------|
| 1 | `classic` | Playfair Display | Source Sans Pro | Deep navy + warm tan | Refined serif, traditional elegance |
| 2 | `modern` | Space Grotesk | DM Sans | Midnight blue + coral | Rounded corners, playful geometry |
| 3 | `elegant` | Cormorant Garamond | Montserrat | Deep charcoal + champagne gold | Delicate flourishes, understated luxury |
| 4 | `teal` | Montserrat | Montserrat | Vibrant teal + deep navy | Bold weights, clean geometry (default) |
| 5 | `bold` | Oswald | Inter | Deep navy + gold | Strong geometric shapes, high contrast |

Theme resolution accepts either a name string (`"teal"`) or number (`4`). Defaults to teal if invalid.

## Data Contract

The builder expects a `report_data` dictionary with the following top-level keys:

```python
{
    "id": "uuid",
    "account_id": "uuid",
    "report_type": "seller" | "buyer",
    "theme": 1-5,                          # Theme number or name
    "accent_color": "#0d294b",             # Optional override
    "language": "en" | "es",
    "page_set": "full" | "compact" | [...], # Page selection

    # Property fields
    "property_address": "123 Main St",
    "property_city": "Los Angeles",
    "property_state": "CA",
    "property_zip": "90210",
    "property_county": "Los Angeles",
    "apn": "1234-567-890",
    "owner_name": "John Doe",
    "legal_description": "LOT 1 BLK 2...",
    "property_type": "Single Family",
    "sitex_data": { ... },                 # Full property details from SiteX

    # Comparables (max 6)
    "comparables": [ ... ],

    # Agent info (from user join)
    "agent": {
        "name", "email", "phone", "photo_url",
        "title", "license_number",
        "company_name", "logo_url"
    },

    # Branding (from affiliate_branding join)
    "branding": {
        "display_name", "logo_url",
        "primary_color", "accent_color"
    }
}
```

## Template Rendering Flow

1. **Theme Resolution** -- Map theme input (name or number) to template path
2. **Build Context** -- Assemble all context objects from report_data:
   - `property` -- Address, details, tax info, legal (from report_data + sitex_data)
   - `agent` -- Name, contact, company, photo, license
   - `comparables` -- Up to 6 formatted comparable properties
   - `stats` -- Price statistics (low/medium/high) from comparables
   - `images` -- Hero image and aerial map URLs
   - `neighborhood` -- Neighborhood demographics (from sitex_data)
   - `area_analysis` -- Area statistics for charts
   - `range_of_sales` -- Min/max/avg from comparables
3. **Jinja2 Render** -- Load theme template, render with context
4. **Return HTML** -- Complete HTML string ready for PDF generation

## Context Builders

| Method | Output Key | Purpose |
|--------|-----------|---------|
| `_build_property_context()` | `property` | Maps report_data + sitex_data to template property object |
| `_build_agent_context()` | `agent` | Agent info with formatted license display |
| `_build_comparables_context()` | `comparables` | Max 6 comps with normalized field names |
| `_build_stats_context()` | `stats` | Price stats with piq/low/medium/high sub-objects |
| `_build_images_context()` | `images` | Hero image URL and Google Maps aerial |
| `_build_neighborhood_context()` | `neighborhood` | Demographics from sitex_data |
| `_build_area_analysis_context()` | `area_analysis` | Market comparison metrics |
| `_build_range_of_sales_context()` | `range_of_sales` | Comp-derived price range stats |
| `_build_default_content_sections()` | (spread) | Default text sections for content pages |

## Custom Jinja2 Filters

| Filter | Signature | Example |
|--------|-----------|---------|
| `format_currency` | `value -> str` | `470000` -> `$470,000` |
| `format_currency_short` | `value -> str` | `470000` -> `$470k`, `1200000` -> `$1.2M` |
| `format_number` | `value -> str` | `2400` -> `2,400` |
| `truncate` | `value, length=40 -> str` | `"Very long address..."` -> `"Very long addr..."` |

All filters handle `None` gracefully, returning `"N/A"`, `"-"`, or `""`.

## Google Maps Static Images

The builder generates Google Maps static image URLs when coordinates are available:

- **Aerial map** -- `zoom=15`, `size=800x600`, roadmap type
- **Comparable maps** -- `zoom=16`, `size=400x200`, roadmap type with marker

Requires `GOOGLE_MAPS_API_KEY` environment variable. Maps are skipped if the key is missing.

## 7-Page Default Layout

| Page | Name | Content |
|------|------|---------|
| 1 | `cover` | Hero image, property address, agent block |
| 2 | `contents` | Table of contents with page descriptions |
| 3 | `aerial` | Aerial/satellite map view of property |
| 4 | `property` | Property details + tax info (two-column layout) |
| 5 | `analysis` | Area sales analysis with price range summary |
| 6 | `comparables` | Comparable sales grid (up to 4 cards) |
| 7 | `range` | Price range visualization with comp list |

Custom page sets are supported by passing a `selected_pages` list in report_data.

## Public API

```python
builder = PropertyReportBuilder(report_data)
html = builder.render_html()           # Full report
preview = builder.render_preview()     # First 3 pages only
comps = builder.fetch_comparables()    # Check/return existing comps
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ASSETS_BASE_URL` | CDN base URL for static assets | `https://assets.trendyreports.com` |
| `GOOGLE_MAPS_API_KEY` | Google Maps Static API key | Empty (maps disabled) |
