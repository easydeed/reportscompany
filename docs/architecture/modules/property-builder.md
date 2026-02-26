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

The default page set contains **7 core pages** plus 1 optional page:

| Page | Key | Description | Required |
|------|-----|-------------|----------|
| 1 | `cover` | Cover page (hero image, address, agent branding) | — |
| 2 | `contents` | Table of contents (dynamic, reflects selected pages) | — |
| 3 | `aerial` | Aerial map (Google Maps satellite + street view) | — |
| 4 | `property` | Subject property details (beds, baths, sqft, APN, owner, tax info, HOA, lot) | ✅ |
| 5 | `analysis` | Market area analysis (price per sqft, year built, lot size trends) | — |
| 6 | `market_trends` | Market trend metrics (absorption rate, MOI, price cuts, DOM distribution) | — |
| 7 | `comparables` | Comparable listings grid with confidence badge (up to 6 comps) | ✅ |
| 8 | `range` | Price range chart — subject property vs comp low/mid/high | — |

> **Page ID contract:** The keys in this table are the **exact strings** that must appear in `selected_pages` (sent by the frontend wizard and stored in `property_reports.selected_pages`). The template checks `{% if "property" in page_set %}` — mismatched IDs silently skip pages.

Pages are selectable per report (stored in `property_reports.selected_pages`).

Default page set (no selection override): `["cover","contents","aerial","property","analysis","comparables","range"]`

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

### External
| Library / Service | Usage |
|---|---|
| `Jinja2` | Template rendering engine |
| `jinja2.Environment` | Custom environment with `format_currency` etc. filters |
| Google Maps Static API | Aerial + street view image URLs embedded in context |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| Unknown theme | Falls back to `teal` theme |
| Missing optional field (e.g., no aerial image) | Jinja2 template handles `None` gracefully; section hidden |
| No comparables | Renders "No comparables available" state in page 6 |
| Template file missing | Raises `TemplateNotFound` → task fails with `"failed"` status |
| Jinja2 render error (undefined var) | Raises `UndefinedError` → task fails |

The test suite (`tests/test_property_templates.py`) validates all 5 themes against both minimal and full contexts, ensuring no undefined variables exist in production template paths.

---

## Tests / How to Validate

```bash
# Full template test suite (5 themes × 6 test classes)
pytest tests/test_property_templates.py -v

# Generate sample PDFs for all themes
python scripts/generate_all_property_pdfs.py

# Generate theme previews (PNG screenshots)
python scripts/generate_theme_previews.py
```

---

## Change Log

| Date | Change |
|------|--------|
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
