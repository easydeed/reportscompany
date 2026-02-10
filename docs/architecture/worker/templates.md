# Jinja2 Template System

> `apps/worker/src/worker/templates/property/`
> Self-contained property report templates with base inheritance and shared macros.

## Directory Structure

```
templates/property/
  _base/
    base.jinja2           # Base template (all themes extend this)
    _macros.jinja2        # Reusable component macros
  classic/
    classic.jinja2        # Theme 1 entry point (extends base)
    classic_report.jinja2 # Legacy standalone (unused by builder)
  modern/
    modern.jinja2         # Theme 2 entry point
    modern_report.jinja2
  elegant/
    elegant.jinja2        # Theme 3 entry point
    elegant_report.jinja2
  teal/
    teal.jinja2           # Theme 4 entry point (default)
    teal_report.jinja2
  bold/
    bold.jinja2           # Theme 5 entry point
    bold_report.jinja2
```

## Base Template Inheritance

All 5 theme templates use `{% extends '_base/base.jinja2' %}` and override specific blocks:

```
base.jinja2
  -> {% block fonts %}         -- Google Fonts link tags
  -> {% block theme_styles %}  -- CSS custom properties + theme-specific styles
  -> {% block cover %}         -- Cover page content (optional override)
  -> {% block contents %}      -- Table of contents (optional override)
  -> {% block aerial %}        -- Aerial map page (optional override)
  -> {% block property_details %} -- Property details (optional override)
  -> {% block analysis %}      -- Area sales analysis (optional override)
  -> {% block comparables %}   -- Comparable sales grid (optional override)
  -> {% block range %}         -- Price range page (optional override)
```

Themes typically only override `fonts` and `theme_styles`, inheriting the structural layout from the base.

## Base Template Structure (`base.jinja2`)

The base template provides:

1. **HTML scaffolding** -- DOCTYPE, head, meta tags, title
2. **CSS reset** -- Box-sizing, margin reset
3. **CSS custom properties** -- Design tokens for spacing, colors, typography, shadows
4. **Page structure** -- `.sheet > .page > .page-content` hierarchy
5. **Component styles** -- Headers, footers, data tables, comp cards, map cards, price range bars
6. **Print styles** -- `@page { size: Letter; margin: 0; }` with proper page breaks
7. **7-page layout** -- Cover, Contents, Aerial, Property, Analysis, Comparables, Range

### CSS Custom Properties (Design Tokens)

Each theme overrides these in `:root`:

| Token | Purpose | Base Default |
|-------|---------|-------------|
| `--color-primary` | Primary brand color | `#1a1a1a` |
| `--color-accent` | Accent/highlight color | `#666666` |
| `--color-background` | Page background | `#ffffff` |
| `--color-surface` | Card/section backgrounds | `#f5f5f5` |
| `--color-text` | Primary text color | `#1a1a1a` |
| `--color-text-muted` | Secondary text color | `#666666` |
| `--color-border` | Border/divider color | `#e5e5e5` |
| `--font-display` | Heading/display font | `system-ui` |
| `--font-body` | Body text font | `system-ui` |
| `--page-width` | Fixed page width | `8.5in` |
| `--page-height` | Fixed page height | `11in` |
| `--page-margin` | Content margin | `0.5in` |

## Macros (`_macros.jinja2`)

Imported via `{% import '_base/_macros.jinja2' as macros %}` in the base template.

### Available Macros

| Macro | Usage | Purpose |
|-------|-------|---------|
| `page_header(title, subtitle)` | `{{ macros.page_header('Contents', 'Overview') }}` | Consistent page header with accent line |
| `page_footer(agent, page_num)` | `{{ macros.page_footer(agent, 2) }}` | Footer with agent photo/name and company logo |
| `cover_agent_block(agent)` | `{{ macros.cover_agent_block(agent) }}` | Large agent display for cover page |
| `property_stats(property)` | `{{ macros.property_stats(property) }}` | Horizontal stats row (beds, baths, sqft, year, lot) |
| `data_table(rows, title)` | `{{ macros.data_table(rows, 'Details') }}` | Generic two-column label/value table |
| `property_details_table(property)` | `{{ macros.property_details_table(property) }}` | Pre-built property details table |
| `tax_table(property)` | `{{ macros.tax_table(property) }}` | Pre-built tax/assessment table |
| `location_table(property)` | `{{ macros.location_table(property) }}` | Pre-built location details table |
| `comp_card(comp, index)` | `{{ macros.comp_card(comp, 1) }}` | Single comparable property card |
| `comp_grid(comparables)` | `{{ macros.comp_grid(comparables) }}` | 2-column grid of up to 4 comp cards |
| `analysis_summary(stats, property)` | `{{ macros.analysis_summary(stats, property) }}` | Price range summary with stats |
| `contents_item(number, title, subtitle)` | `{{ macros.contents_item(1, 'Cover', '...') }}` | Single table-of-contents entry |
| `map_card(image_url, title)` | `{{ macros.map_card(url, 'Location') }}` | Styled map image container |
| `price_range_bar(low, high, estimate)` | `{{ macros.price_range_bar(low, high) }}` | Visual price range with optional marker |

## Data Contract Expected by Templates

Templates receive these context variables (assembled by `PropertyReportBuilder`):

| Variable | Type | Content |
|----------|------|---------|
| `theme_number` | int | 1-5 |
| `theme_name` | str | `classic`, `modern`, `elegant`, `teal`, `bold` |
| `theme_color` | str | Hex color from branding or accent_color |
| `assets_base_url` | str | CDN base URL |
| `google_maps_api_key` | str | Google Maps API key |
| `page_set` | list | Page names to render |
| `property` | dict | Address, details, tax, legal fields |
| `agent` | dict | Name, contact, company, photo, license |
| `comparables` | list | Up to 6 comparable property dicts |
| `stats` | dict | Price statistics with piq/low/medium/high |
| `images` | dict | `hero` and `aerial_map` URLs |
| `neighborhood` | dict | Demographics (male/female ratio, avg stats) |
| `area_analysis` | dict | Area comparison metrics |
| `range_of_sales` | dict | Comp-derived price range |
| `cover_image_url` | str | Optional cover hero image |

## 5 Theme Visual Identities

### Theme 1: Classic
- **Fonts:** Playfair Display (display) + Source Sans Pro (body)
- **Colors:** Deep navy + warm tan
- **Style:** Refined serif typography, classic layouts, understated luxury

### Theme 2: Modern
- **Fonts:** Space Grotesk (display) + DM Sans (body)
- **Colors:** Midnight blue + coral
- **Style:** Rounded corners, playful geometry, gradient accents

### Theme 3: Elegant
- **Fonts:** Cormorant Garamond (display) + Montserrat (body)
- **Colors:** Deep charcoal + champagne gold
- **Style:** Delicate flourishes, refined typography, understated luxury

### Theme 4: Teal (Default)
- **Fonts:** Montserrat (display + body)
- **Colors:** Vibrant teal (`#34D1C3`) + deep navy (`#18235C`)
- **Style:** Bold weights, clean geometry, colorful accents
- **Custom:** Alternating row colors (`--color-row-a: #DFF6F3`, `--color-row-b: #ECEAF7`)

### Theme 5: Bold
- **Fonts:** Oswald (display) + Inter (body)
- **Colors:** Deep navy + gold
- **Style:** Strong geometric shapes, bold type, high contrast

## CSS-in-Template Approach

All CSS is embedded directly in the templates rather than external stylesheets. This is intentional:

1. **PDF compatibility** -- PDFShift and Playwright reliably render inline styles
2. **Self-contained** -- Each template is a single file with no external dependencies (except fonts)
3. **Theme isolation** -- CSS custom properties in `:root` make theming simple
4. **Print optimization** -- `@page` rules and `@media print` blocks are co-located with layout

The base template defines all structural styles; theme templates override only CSS custom properties and add theme-specific flourishes.
