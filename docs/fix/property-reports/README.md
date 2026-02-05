# Property Report PDF System v2.0

A standardized, extensible template system for generating beautiful real estate property reports.

---

## Architecture Overview

```
property-reports/
├── _base/
│   ├── base.jinja2         # Shared 7-page structure
│   └── _macros.jinja2      # Reusable components
├── bold/
│   └── bold.jinja2         # Bold theme (extends base)
├── classic/
│   └── classic.jinja2      # Classic theme (extends base)
├── elegant/
│   └── elegant.jinja2      # Elegant theme (extends base)
├── modern/
│   └── modern.jinja2       # Modern theme (extends base)
├── teal/
│   └── teal.jinja2         # Teal theme (extends base)
├── sample_data.py          # Test data
└── README.md               # This file
```

---

## Key Improvements Over v1

| Issue | v1 (Old) | v2 (New) |
|-------|----------|----------|
| Code duplication | 600+ lines per theme | ~200-300 lines per theme |
| Inconsistent margins | 0.5in to 0.6in | Standardized 0.5in |
| Footer position | 0.3in to 0.4in | Standardized 0.4in |
| Variable naming | `--navy`, `--burgundy`, etc. | Unified `--color-primary` |
| Maintenance | Edit 5 files for shared changes | Edit base once |
| PDF engine parity | Different output | Consistent (CSS handles margins) |

---

## How Template Inheritance Works

### Base Template (`_base/base.jinja2`)

Defines the structure for all 7 pages:

```jinja2
{% block cover %}...{% endblock %}
{% block contents %}...{% endblock %}
{% block aerial %}...{% endblock %}
{% block property_details %}...{% endblock %}
{% block analysis %}...{% endblock %}
{% block comparables %}...{% endblock %}
{% block range %}...{% endblock %}
```

### Theme Templates (e.g., `bold/bold.jinja2`)

Extend base and override:

```jinja2
{% extends '_base/base.jinja2' %}

{% block fonts %}
  {# Theme-specific Google Fonts #}
{% endblock %}

{% block theme_styles %}
  {# CSS variable overrides #}
{% endblock %}

{% block cover %}
  {# Theme-specific cover design #}
{% endblock %}
```

---

## CSS Variables System

### Standardized Variables (in base)

```css
:root {
  /* Page Dimensions - DO NOT CHANGE */
  --page-width: 8.5in;
  --page-height: 11in;
  --page-margin: 0.5in;
  --footer-height: 0.6in;
  --footer-bottom: 0.4in;
  
  /* Spacing Scale */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 40px;
}
```

### Theme-Specific Variables (override in each theme)

```css
:root {
  --color-primary: {{ theme_color | default('#0F1629') }};
  --color-primary-light: #1a2744;
  --color-accent: #C9A227;
  --color-accent-light: #dbb94a;
  --color-background: #FFFFFF;
  --color-surface: #F8F7F4;
  --color-text: #0F1629;
  --color-text-muted: #64748B;
  --color-border: #E2E8F0;
  
  --font-display: 'Oswald', sans-serif;
  --font-body: 'Inter', sans-serif;
}
```

### Custom Theme Color

The `theme_color` variable allows agents to customize their primary color via the wizard:

```jinja2
--color-primary: {{ theme_color | default('#0F1629') }};
```

---

## Reusable Macros

Located in `_base/_macros.jinja2`:

| Macro | Purpose | Usage |
|-------|---------|-------|
| `page_header(title, subtitle)` | Consistent page headers | `{{ macros.page_header('Property Details') }}` |
| `page_footer(agent, page_num)` | Consistent page footers | `{{ macros.page_footer(agent, 4) }}` |
| `cover_agent_block(agent)` | Agent info on cover | `{{ macros.cover_agent_block(agent) }}` |
| `property_stats(property)` | Beds/baths/sqft row | `{{ macros.property_stats(property) }}` |
| `data_table(rows, title)` | Generic data table | `{{ macros.data_table(rows, 'Title') }}` |
| `property_details_table(property)` | Property specs table | `{{ macros.property_details_table(property) }}` |
| `tax_table(property)` | Tax info table | `{{ macros.tax_table(property) }}` |
| `location_table(property)` | Location table | `{{ macros.location_table(property) }}` |
| `comp_card(comp, index)` | Single comp card | `{{ macros.comp_card(comp, 1) }}` |
| `comp_grid(comparables)` | Grid of 4 comps | `{{ macros.comp_grid(comparables) }}` |
| `analysis_summary(stats, property)` | Price range summary | `{{ macros.analysis_summary(stats, property) }}` |
| `contents_item(num, title, subtitle)` | TOC entry | `{{ macros.contents_item(1, 'Cover') }}` |
| `map_card(image_url, title)` | Styled map container | `{{ macros.map_card(images.aerial_map) }}` |
| `price_range_bar(low, high, estimate)` | Visual price range | `{{ macros.price_range_bar(stats.price_low, stats.price_high) }}` |

---

## Theme Personalities

| Theme | Display Font | Body Font | Primary Default | Accent | Personality |
|-------|-------------|-----------|-----------------|--------|-------------|
| **Bold** | Oswald | Inter | `#0F1629` | `#C9A227` (Gold) | Confident, powerful |
| **Classic** | Playfair Display | Source Sans Pro | `#1B365D` | `#8B7355` (Tan) | Timeless, trustworthy |
| **Elegant** | Cormorant Garamond | Montserrat | `#1A1A1A` | `#B8977E` (Champagne) | Refined, sophisticated |
| **Modern** | Space Grotesk | DM Sans | `#FF6B5B` (Coral) | `#1A1F36` | Fresh, tech-forward |
| **Teal** | Montserrat | Montserrat | `#34D1C3` | `#18235C` | Vibrant, coastal |

---

## Data Contract

### Required Objects

```python
{
    "property": {
        "street_address": str,
        "city": str,
        "state": str,
        "zip_code": str,
        "full_address": str,
        "bedrooms": int,
        "bathrooms": float,
        "sqft": int,
        "lot_size": int,
        "year_built": int,
        # ... (see sample_data.py for full list)
    },
    "agent": {
        "name": str,
        "title": str,
        "license": str,
        "phone": str,
        "email": str,
        "company_name": str,
        "photo_url": str | None,
        "logo_url": str | None,
        "company_short": str,
        "company_tagline": str
    },
    "comparables": [
        {
            "address": str,
            "sale_price": int,
            "sold_date": str,
            "sqft": int,
            "bedrooms": int,
            "bathrooms": float,
            "price_per_sqft": int,
            "distance_miles": float,
            "map_image_url": str
        }
        # ... up to 4 comps
    ],
    "stats": {
        "total_comps": int,
        "avg_sqft": int,
        "avg_beds": float,
        "avg_baths": float,
        "price_low": int,
        "price_high": int,
        "medium": {"price": int}
    },
    "images": {
        "hero": str | None,
        "aerial_map": str | None
    },
    "theme_color": str | None  # Optional hex override
}
```

### Required Jinja2 Filters

```python
def format_currency(value):
    """1234567 -> $1,234,567"""
    if value is None:
        return ""
    return f"${value:,.0f}"

def format_number(value):
    """1234567 -> 1,234,567"""
    if value is None:
        return ""
    return f"{value:,.0f}"
```

---

## PDF Engine Configuration

### Critical: Set Playwright Margins to 0

Update `pdf_engine.py` to match PDFShift:

```python
# OLD (causes inconsistency)
pdf_options = {
    "margin": {"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"}
}

# NEW (CSS handles margins)
pdf_options = {
    "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"}
}
```

This ensures identical output between local (Playwright) and production (PDFShift).

---

## Adding New Pages

To add a new page type (e.g., "Market Trends"):

### 1. Add block to base template

```jinja2
{# In _base/base.jinja2, add after page 7 #}
<div class="page page-trends">
  {% block market_trends %}
  <div class="page-content">
    {{ macros.page_header('Market Trends', 'Local Market Analysis') }}
    {# Default content #}
  </div>
  {{ macros.page_footer(agent, 8) }}
  {% endblock %}
</div>
```

### 2. Override in themes if needed

```jinja2
{# In bold/bold.jinja2 #}
{% block market_trends %}
  {# Theme-specific market trends layout #}
{% endblock %}
```

### 3. Add supporting macro if needed

```jinja2
{# In _base/_macros.jinja2 #}
{% macro trend_chart(data) %}
  {# Chart component #}
{% endmacro %}
```

---

## Logo Handling

Logos are designed to handle any reasonable dimension:

```css
.cover-logo {
  max-height: 50px;
  max-width: 180px;
  object-fit: contain;
}

.footer-logo {
  max-height: 40px;
  max-width: 140px;
  object-fit: contain;
}
```

- Wide logos (e.g., 400x80) will fit within max-width
- Tall logos (e.g., 100x200) will fit within max-height
- Square logos work fine with both constraints

---

## Migration Checklist

1. [ ] Copy `_base/` folder to `apps/worker/src/worker/templates/property/`
2. [ ] Copy all 5 theme folders to same location
3. [ ] Update `pdf_engine.py` to set Playwright margins to 0
4. [ ] Register Jinja2 filters (`format_currency`, `format_number`)
5. [ ] Update `PropertyReportBuilder` to use new template paths
6. [ ] Test all 5 themes with sample data
7. [ ] Test with both Playwright (local) and PDFShift (production)
8. [ ] Verify agent logo handling with various dimensions
9. [ ] Delete old template files

---

## Customization Examples

### Change a theme's accent color

Edit the theme file's `:root` block:

```css
--color-accent: #FF5733;  /* New accent */
--color-accent-light: #FF7F5B;
```

### Add a new decorative element

In the theme's `{% block theme_styles %}`:

```css
.page-header::before {
  content: '';
  position: absolute;
  /* ... */
}
```

### Create a new theme

1. Copy an existing theme folder
2. Rename file to `{theme_name}.jinja2`
3. Update `{% extends %}` path
4. Modify fonts, colors, and styling

---

*System designed for TrendyReports — February 2026*
