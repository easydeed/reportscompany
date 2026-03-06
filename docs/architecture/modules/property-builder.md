# Module: Property Report Builder

> `apps/worker/src/worker/property_builder.py`

---

## Purpose

`PropertyReportBuilder` renders property reports as **HTML strings** using Jinja2 templates. Each theme corresponds to a separate template directory. The builder assembles all report context (property data, agent, comparables, stats, maps) and renders the selected pages into a single HTML document that is then converted to PDF by the `pdf_adapter`.

---

## Themes

| Theme ID | Name | Primary / Accent Colors |
|----------|------|------------------------|
| `classic` | Classic | Navy + Sky Blue |
| `modern` | Modern | Coral + Midnight |
| `elegant` | Elegant | Burgundy + Gold |
| `teal` | Teal (default) | Teal + Navy |
| `bold` | Bold | Navy + Gold |

Template location: `apps/worker/src/worker/templates/property/<theme>/<theme>.jinja2`

All 5 themes extend `_base/base.jinja2` via Jinja2 template inheritance.

---

## Report Pages

The default page set contains **9 pages** (7 core + 2 optional):

| Page | Key | Description | Required |
|------|-----|-------------|----------|
| 1 | `cover` | Cover page (hero image, address, agent branding) | — |
| 2 | `overview` | AI-generated Executive Summary / Property Overview (GPT-4o-mini) | — |
| 3 | `contents` | Table of contents (dynamic — Executive Summary entry conditionally shown only when overview page renders) | — |
| 4 | `aerial` | Aerial map (Google Maps satellite + street view) | — |
| 5 | `property` | Subject property details (beds, baths, sqft, APN, owner, tax info, HOA, lot) | ✅ |
| 6 | `analysis` | Market area analysis (price per sqft, year built, lot size trends) | — |
| 7 | `market_trends` | Market trend metrics (absorption rate, MOI, price cuts, DOM distribution) | — |
| 8 | `comparables` | Comparable listings grid with confidence badge (up to 6 comps) | ✅ |
| 9 | `range` | Price range chart — subject property vs comp low/mid/high | — |

> **Page ID contract:** The keys in this table are the **exact strings** that must appear in `selected_pages` (sent by the frontend wizard and stored in `property_reports.selected_pages`). The template checks `{% if "property" in page_set %}` — mismatched IDs silently skip pages.

Pages are selectable per report (stored in `property_reports.selected_pages`).

Default page set (no selection override): `["cover","overview","contents","aerial","property","analysis","comparables","range","market_trends"]`

---

## Key Functions / Classes

### `PropertyReportBuilder` (class)

| Method | Description |
|--------|-------------|
| `__init__(theme, selected_pages)` | Loads Jinja2 environment for the specified theme |
| `render(context_data)` | Main entry point — assembles all context builders, renders template |
| `_build_property_context(data)` | Address, APN, owner, beds/baths, sqft, year built, lot size, tax info |
| `_build_agent_context(data)` | Agent name, license number, phone, email, company, headshot URL |
| `_build_comparables_context(comps)` | Normalises field variants (`lat`/`latitude`, `photo_url`/`photos[0]`, `distance_miles`) |
| `_build_stats_context(subject, comps)` | Calculates `piq` (property in question stats), low/medium/high from comps |
| `_build_images_context(data)` | Hero image URL, aerial map URL (Google Maps Static API), street view URL |
| `_build_neighborhood_context(data)` | Demographics (male/female ratio, average sale price) |
| `_build_area_analysis_context(comps)` | Market stats: living area, price/sqft, year built, lot size, beds, baths (min/max/avg) |

### `compute_color_roles(hex_color, dark_bg)` (module-level function)

Derives 6 color roles from a single user-picked accent hex, ensuring WCAG-safe contrast across all report sections:

| Role | Purpose |
|------|---------|
| `theme_color` | Raw user-picked hex, used as-is |
| `theme_color_light` | Lighter tint (mixed 35% toward white) — subtle backgrounds |
| `theme_color_dark` | Darker shade (mixed 25% toward black) — borders, hover states |
| `theme_color_on_dark` | Guaranteed readable on dark backgrounds (navy headers, cover pages). Progressively lightened until WCAG contrast ratio ≥ 3.0 against the theme's dark background color. |
| `theme_color_on_light` | Guaranteed readable on white/light backgrounds (price labels, TOC numbers). Progressively darkened until contrast ratio ≥ 3.0. |
| `theme_color_text` | `#ffffff` or `#1a1a1a` — text to overlay on the accent color when used as a fill |

Each theme defines its own dark background color in `_THEME_DARK_BG` (e.g., teal uses `#18235c`, elegant uses `#1a1a1a`) so contrast math is accurate per theme. Templates consume these roles via CSS custom properties (e.g., `--teal-on-dark`, `--teal-on-light`).

### `generate_overview()` (via `ai_overview.py`)

Produces a 4–5 paragraph, 180–250 word AI executive summary for the property report. Called by the builder when `"overview"` is in the page set and no pre-injected `overview_text` exists. See `ai_overview.py` module below.

### Custom Jinja2 Filters

| Filter | Example Output |
|--------|----------------|
| `format_currency` | `$470,000` |
| `format_currency_short` | `$470k`, `$1.2M` |
| `format_number` | `1,234` |
| `truncate(length)` | `"Long title..."` |

---

## Inputs / Outputs

### `render(context_data: dict) → str`

| Direction | Field | Notes |
|-----------|-------|-------|
| In | `context_data.property` | Subject property dict (from SiteX + frontend) |
| In | `context_data.agent` | Agent profile dict |
| In | `context_data.comparables` | List of comparable property dicts |
| In | `context_data.branding` | Affiliate branding overrides (logo, colors) |
| In | `context_data.selected_pages` | List of page keys to render |
| Out | `html` | Full HTML string ready for PDFShift |

### Stats Context (computed internally)

```python
{
  "piq": {
    "price": 750000,
    "price_per_sqft": 405,
    "sqft": 1850,
  },
  "comps_low": {"price": 690000, "price_per_sqft": 373, "sqft": 1700},
  "comps_mid": {"price": 742000, "price_per_sqft": 401, "sqft": 1800},
  "comps_high": {"price": 820000, "price_per_sqft": 443, "sqft": 1920},
}
```

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `apps/worker/src/worker/tasks.py` | Calls `PropertyReportBuilder.render()` |
| `apps/worker/src/worker/pdf_adapter.py` | Receives the HTML string for PDF conversion |
| `apps/worker/src/worker/ai_overview.py` | Generates AI executive summary text (GPT-4o-mini) for the `overview` page |

### External
| Library / Service | Usage |
|---|---|
| `Jinja2` | Template rendering engine |
| `jinja2.Environment` | Custom environment with `format_currency` etc. filters |
| `colorsys` (stdlib) | HSV color space conversions for Smart Color System |
| Google Maps Static API | Aerial + street view image URLs embedded in context |
| OpenAI GPT-4o-mini | AI executive summary generation (via `ai_overview.py`) |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| Unknown theme | Falls back to `teal` theme |
| Missing optional field (e.g., no aerial image) | Jinja2 template handles `None` gracefully; section hidden |
| No comparables | Renders "No comparables available" state in page 6 |
| AI overview generation fails | `overview` page silently removed from page set; report renders without it |
| No `OPENAI_API_KEY` set | `ai_overview.py` returns `None`; overview page omitted |
| Template file missing | Raises `TemplateNotFound` → task fails with `"failed"` status |
| Jinja2 render error (undefined var) | Raises `UndefinedError` → task fails |

The test suite (`tests/test_property_templates.py`) validates all 5 themes against both minimal and full contexts, ensuring no undefined variables exist in production template paths.

---

## Tests / How to Validate

```bash
# Full template test suite (5 themes × 6 test classes)
pytest tests/test_property_templates.py -v

# Generate all 5 themes with live/sample data (HTML + optional PDF)
python scripts/gen_la_verne_all_themes.py            # full run with PDF
python scripts/gen_la_verne_all_themes.py --html-only # HTML only (fast)

# Generate sample PDFs for all themes (static data, no AI overview)
python scripts/generate_all_property_pdfs.py

# Generate JPG theme previews for the wizard UI (requires gen_la_verne output)
python scripts/generate_theme_preview_jpgs.py
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-03 | **Fix: Comparable photos now used.** All 5 standalone `*_report.jinja2` templates updated to render `comp.photo_url` (MLS property photo) with fallback to `comp.map_image_url` (Google Maps satellite). Previously only map images were shown. |
| 2026-03 | **Fix: Dynamic TOC for Executive Summary.** TOC entry for "Executive Summary" now wrapped in `{% if "overview" in _pages and overview_text %}` conditional across all 5 themes, preventing phantom entry when AI generation fails. |
| 2026-03 | **Fix: Branding default theme sync.** Added `default_theme_id` column to `accounts` table (migration `0043`), `AccountOut` model, `BrandingPatch` model, GET/PATCH handlers in `account.py`. Property wizard now correctly reads the account's default theme on mount. |
| 2026-03 | **AI Executive Summary page:** Added `overview` page (key `overview`) to all 5 themes. Powered by `ai_overview.py` (GPT-4o-mini, 4–5 paragraphs, 180–250 words). `overview_text` can be pre-injected via `report_data` to skip the API call. If generation fails or no API key is set, the page is silently removed from the page set. |
| 2026-03 | **Smart Color System:** Added `compute_color_roles()` — derives 6 color variants from a single accent hex (light, dark, on_dark, on_light, text). All 5 templates updated to use `on_dark`/`on_light` CSS variables for WCAG-safe contrast. Each theme defines its dark background color in `_THEME_DARK_BG`. |
| 2026-03 | **Page count updated:** Default page set now includes `overview` and `market_trends` (9 pages total, up from 7). Frontend `types.ts` `pageCount` updated to 9. |
| 2026-02 | **Phase 4 (cursor-enhancement-plan):** Added `<link rel="preconnect">` hints for `fonts.googleapis.com` and `fonts.gstatic.com` to `base.jinja2`. Added invisible font-trigger `<div>` before `</body>` that forces all 8 theme font families to load before Playwright/PDFShift captures the page — prevents fallback-glyph rendering in PDFs. |
| 2026-02 | **market_trends page fix:** `render_html()` now accepts `market_trends_data` pre-injected in `report_data` as an override, bypassing the live API fetch. Used by the generation script for demo/testing with sample data. |
| 2026-02 | **_exclude_rentals fix:** `report_builders._exclude_rentals()` was imported by `market_trends.py` but was never defined, causing all Market Trends page generation to fail with `ImportError`. Function now defined in `report_builders.py`. |
| 2026-02 | **Cover image fix:** `_build_images_context()` generates a Google Street View URL as a fallback `hero` when `cover_image_url` is not provided. |
| 2026-02 | **Comparable image fix:** `_build_comparables_context()` uses `lat`/`lng` (passed from frontend) to generate Google Static Maps thumbnails when `photo_url` is not available. |
| 2026-02 | **Sold/Listed label fix:** `_build_comparables_context()` adds `sold_date_label` ("Listed" for Active/Pending, "Sold" for Closed) to each comparable. `_macros.jinja2` uses `{{ comp.sold_date_label }}`. |
| 2026-02 | **Page ID sync:** Frontend `types.ts` COMPACT_PAGES + FULL_PAGES IDs aligned to template keys (`toc`→`contents`, `property_details`→`property`, `area_analysis`→`analysis`). Added `market_trends` page. Removed non-existent `neighborhood` and `back_cover` entries. |
| 2026-02 | **Theme CSS fixes (commit 208d6bb):** Standardized page geometry, fixed Bold/Classic header overlap on pages 5-7, fixed slider colors, fixed `default(true)` for `theme_color` CSS variable. |
| 2026-02 | Added `market_trends` page (key `market_trends`) — optional, only renders when `market_trends` context is populated |
| 2026-02 | Added `comp_confidence_bar` macro + `market_metrics_block` to all 5 themes |
| 2026-02 | Added C1 fields to `property` page: `tax_annual_amount`, `lot_size_area`, `acres`, HOA fee/frequency, school district |
| 2026-02 | Pages 5-7 HTML transplanted from original V0 design (commit 8dbec7b) — fixed layout regressions |
| 2026-01 | Added `_build_comparables_context` normalisation for `lat`/`latitude` and `photo_url`/`photos[0]` field variants |
| 2025-12 | Added `bold` theme (5th theme) |
| 2025-11 | Added `_build_area_analysis_context` for market statistics page |
| 2025-10 | Initial implementation with 4 themes and 7-page set |
