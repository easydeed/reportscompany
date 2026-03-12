# GOPHER-001: Pre-Build Investigation Report

> **Ticket:** GOPHER-001 — Pre-build investigation for market report PDF theming
> **Date:** March 12, 2026
> **Playbook:** `MARKET_REPORT_PDF_PLAYBOOK.md` read in full

---

## File 1: `apps/worker/src/worker/property_builder.py` (1,224 lines)

### WHAT EXISTS

**`compute_color_roles(hex_color, dark_bg)` — Line 147**
- **Module-level function.** Not inside any class. Can be imported directly.
- Signature: `compute_color_roles(hex_color: str, dark_bg: str = "#18235c") -> Dict[str, str]`
- Returns 6 keys: `theme_color`, `theme_color_light`, `theme_color_dark`, `theme_color_on_dark`, `theme_color_on_light`, `theme_color_text`
- Depends on 6 private helper functions (all module-level): `_hex_to_rgb`, `_rgb_to_hex`, `_relative_luminance`, `_lighten`, `_darken`, `_ensure_readable_on_dark`, `_ensure_readable_on_light`, `_text_on_accent`
- Import: `from worker.property_builder import compute_color_roles` ✅

**`_THEME_DARK_BG` — Line 979**
- **Class attribute** on `PropertyReportBuilder`, NOT module-level.
- Dict: `{"teal": "#18235c", "modern": "#1A1F36", "classic": "#1B365D", "bold": "#15216E", "elegant": "#1a1a1a"}`
- Import: `from worker.property_builder import PropertyReportBuilder` then `PropertyReportBuilder._THEME_DARK_BG` ✅ (works but ugly)
- **Better approach:** Copy the 5-line dict into `market_builder.py` or extract to a shared constants module. The values are static and theme-specific — they won't change independently.

**`_THEME_DEFAULT_COLORS` — Line 969**
- Also a class attribute on `PropertyReportBuilder`.
- Dict: `{"teal": "#34d1c3", "modern": "#FF6B5B", "classic": "#1B365D", "bold": "#15216E", "elegant": "#1a1a1a"}`
- Same access pattern as `_THEME_DARK_BG`.

**Jinja2 Custom Filters — Lines 302-346**
- Four `@staticmethod` methods INSIDE `PropertyReportBuilder`:
  - `_format_currency(value)` → `$470,000`
  - `_format_currency_short(value)` → `$470k`, `$1.2M`
  - `_format_number(value)` → `1,234`
  - `_truncate(value, length)` → `"Long title..."`
- **They're static methods** — they don't use `self`. Can be imported as:
  ```python
  from worker.property_builder import PropertyReportBuilder
  self.env.filters['format_currency'] = PropertyReportBuilder._format_currency
  ```
- **Better approach:** Extract to a shared `template_filters.py` module for clean imports.

**Builder Class Pattern — Line 200**
- Constructor: `PropertyReportBuilder(report_data: Dict[str, Any])` — takes a single dict
- Main method: `render_html() -> str` — returns complete HTML string
- Template loading: `Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))` where `TEMPLATES_DIR = Path(__file__).parent / "templates" / "property"`
- Theme resolution: accepts int (1-5) or string name, falls back to teal
- Context building: 10 private `_build_*_context()` methods → merged into single flat `context` dict → `template.render(**context)`

### WHAT'S RELEVANT FOR MARKET BUILDER

1. **Import `compute_color_roles` directly** — it's module-level, clean import
2. **The filter functions work** as `PropertyReportBuilder._format_currency` etc. — static methods, no instance needed
3. **`_THEME_DARK_BG`** and **`_THEME_DEFAULT_COLORS`** — either import from the class or duplicate the 5-line dicts (recommended: duplicate, they're theme constants that belong in each builder)
4. **Constructor pattern**: single `report_data` dict, resolve theme inside `__init__`, set up Jinja2 env
5. **`render_html()` pattern**: build context → fetch optional data → compute color roles → merge context → `template.render(**context)`

### WHAT TO WATCH

- **Diagnostic logging is verbose.** Property builder has ~20 `logger.warning("[DIAGNOSTIC]")` lines. Market builder should use `logger.info()` for normal flow, `logger.warning()` only for actual warnings.
- **`TEMPLATES_DIR` is hardcoded** to `templates/property/`. Market builder needs its own: `templates/market/`.
- **The filter functions are `@staticmethod` inside the class.** If the Builder copies them inline, the Reviewer will BLOCK. Must import or extract to shared module.
- **`_get_theme_color()` has complex priority logic** (accent → branding.primary → theme default). Market builder should replicate this same priority chain.

---

## File 2: `apps/worker/src/worker/templates/property/_base/base.jinja2` (2,147 lines)

### WHAT EXISTS

A full-featured Jinja2 base template with:

1. **Page geometry** (lines 44-100): CSS custom properties for US Letter (8.5×11"), margins, spacing scale, border radii, color defaults, font defaults
2. **Print CSS** (lines 1738-1764): `@page { size: Letter; margin: 0; }`, `page-break-after: always`, `-webkit-print-color-adjust: exact`
3. **Font preloading** (lines 1776-1785 + 2135-2144): Invisible divs that force Google Fonts to load before PDF capture. Two separate blocks — one at top using CSS vars, one at bottom with hardcoded font families for all 8 theme fonts
4. **Component CSS classes** (~1,500 lines): `.page`, `.page-content`, `.page-footer`, `.cover-*`, `.comp-*`, `.data-table`, `.analysis-*`, `.range-*`, `.market-trends` styles (`.mt-*` classes, 200+ lines)
5. **Page structure blocks** (lines 1786-2128): Full HTML for all 7+ property report pages — Cover, Contents, Aerial, Property, Analysis, Market Trends, Comparables, Range
6. **Jinja2 blocks** for theme override: `{% block fonts %}`, `{% block theme_styles %}`, `{% block market_trends_css %}`, plus per-page blocks (`{% block cover %}`, `{% block contents %}`, etc.)
7. **Macros import**: `{% import '_base/_macros.jinja2' as macros %}` — all page content uses macros

### WHAT'S RELEVANT FOR MARKET BUILDER

The base template has **two categories of content**:

**CAN SHARE (infrastructure):**
- Page geometry CSS (`:root` variables, `.sheet`, `.page`, `.page-content`)
- Print CSS (`@page`, `@media print`)
- Font preconnect hints
- Font preloading divs (the invisible font-trigger technique)
- CSS reset (`*, *::before, *::after { box-sizing: border-box; }`)

**CANNOT SHARE (property-specific):**
- Page HTML structure (Cover with hero image, TOC, Aerial map, Property Details tables, Comparables grid, Range chart)
- All the `.comp-*`, `.analysis-*`, `.range-*`, `.cover-*` CSS classes
- The macros import (`_base/_macros.jinja2`) — property macros, not market macros
- Market Trends CSS is already here (`.mt-*` classes, ~200 lines) but these are for the property report's optional market trends page, not the standalone market report layout

### WHAT TO WATCH

- **The base template is 2,147 lines.** It's monolithic — page geometry + property-specific CSS + all page HTML in one file. Sharing it would import massive amounts of unused property CSS into market templates.
- **The font-trigger technique is critical.** Without it, PDFShift captures pages before fonts load, causing fallback glyphs. Market base template MUST replicate this.
- **The Market Trends CSS (`.mt-*` classes, lines 1307-1545) already exists here.** If market reports want to reuse these styles for their Market Narrative layout, they can copy them. But they're designed for a single page inside a property report, not a full standalone market report.
- **Recommendation: FORK, don't share.** Create `templates/market/_base/base.jinja2` with:
  - Copy: page geometry, print CSS, font preloading technique
  - Skip: all property page HTML, property-specific CSS classes
  - Add: market-specific CSS (gradient headers, photo grids, stats bars, agent footer)
  - Result: ~300-400 line base template instead of 2,147 lines

---

## File 3: `apps/worker/src/worker/tasks.py` — `generate_report` task (Lines 384-1125)

### WHAT EXISTS

The `generate_report` Celery task is the **current market report pipeline**. It handles all 8 report types. Here's the full step-by-step:

```
@celery.task(name="generate_report", bind=True, autoretry_for=(Exception,),
             retry_backoff=True, retry_backoff_max=600, retry_kwargs={"max_retries": 3})
def generate_report(self, run_id, account_id, report_type, params):
```

**Step 1 — Persist 'processing' status** (line 403)
- UPDATE `report_generations` SET `status='processing'`, `input_params=<json>`

**Step 2 — Usage limit check** (line 414, for scheduled reports only)
- Calls `check_usage_limit()`, returns early with `status='skipped_limit'` if blocked

**Step 3 — Data fetch from SimplyRETS** (line 456)
- Extracts `city`, `zips`, `lookback_days`, `filters` from params
- Market Snapshot gets 3 separate queries (Active + Closed + Pending)
- Other types get a single query via `build_params(report_type, params)`
- Data goes through `PropertyDataExtractor` → `filter_valid` → elastic widening if too few results
- Calls `build_result_json(report_type, clean_data, context)` — this is from `report_builders.py`
- Caches result for 15 minutes

**Step 4 — Photo proxy to R2** (line 640, gallery/featured only)
- Rewrites MLS photo URLs to R2 presigned URLs via `proxy_report_photos_inplace()`

**Step 5 — Save result_json** (line 652)
- UPDATE `report_generations` SET `result_json=<json>`

**Step 6 — Generate PDF** (line 659)
- `render_pdf(run_id, account_id, html_content=None, print_base=DEV_BASE)`
- **`html_content=None` is the key detail.** When None, `pdf_engine.py` navigates to `/print/{run_id}` (the frontend page) instead of rendering from an HTML string.
- This means the **current PDF generation is frontend-driven**: worker → save data → Playwright/PDFShift opens browser → loads `/print/{runId}` → frontend fetches data from API → `lib/templates.ts` hydrates HTML → PDF capture

**Step 7 — Upload PDF to R2** (line 669)
- `upload_to_r2(pdf_path, s3_key)` → presigned URL (7 days)

**Step 8 — Mark completed** (line 701)
- UPDATE `report_generations` SET `status='completed'`, `html_url`, `json_url`, `pdf_url`, `processing_time_ms`

**Step 9 — Email delivery** (line 713, for scheduled reports only)
- Loads schedule recipients, resolves to emails
- Loads branding (affiliate or account-level)
- Calls `send_schedule_email()` with full payload

**Step 10 — Webhook** (line 1072)
- Delivers `report.completed` event to registered webhooks

### WHAT'S RELEVANT FOR MARKET BUILDER

The playbook says to add a `generate_market_report_task`. There are **two strategies**:

**Strategy A: New task alongside existing (playbook's approach)**
- Add `generate_market_report_task(report_id)` that:
  1. Loads the row (including new `theme_id`, `accent_color` columns)
  2. Calls `MarketReportBuilder(theme, accent, report_type).render(payload)` → HTML string
  3. Calls `render_pdf(run_id, account_id, html_content=html_string)` ← **passes HTML directly, skips frontend**
  4. Upload to R2 → update row
- The API's `POST /v1/reports` enqueues this task instead of `generate_report`
- **Problem:** Steps 1-5 of the existing task (data fetch, SimplyRETS, caching, photo proxy) MUST still happen. The new task either duplicates all that or inherits it.

**Strategy B: Extend existing task (cleaner)**
- Add a step between Step 5 (save result_json) and Step 6 (generate PDF):
  - If `theme_id` is set on the row → `MarketReportBuilder.render()` → pass HTML to `render_pdf(html_content=html_string)`
  - If `theme_id` is NOT set → fall back to existing `/print/{runId}` frontend path
- **Advantage:** zero code duplication, gradual rollout, existing scheduled reports keep working
- **Disadvantage:** the existing task is already 740 lines long

### WHAT TO WATCH

- **The current `render_pdf()` call passes `html_content=None`** (line 661-666). This triggers Playwright/PDFShift to navigate to the frontend URL. The new market builder must pass `html_content=html_string` to skip the frontend entirely.
- **The `pdf_engine.py` module already supports both paths.** Check `render_pdf()` — when `html_content` is provided, it renders that HTML directly instead of navigating to a URL. This is exactly what the CMA report does (line 1476 in `process_consumer_report`).
- **`build_result_json()` in `report_builders.py`** is the data computation step. It produces the `result_json` that currently gets passed to the frontend. For the market builder, this same `result_json` is the data source — but formatted for Jinja2 templates instead of `lib/templates.ts`.
- **Email delivery (Step 9) must still work.** If you replace the task, make sure scheduled reports still send emails with the same payload shape.
- **The R2 upload function `upload_to_r2()` is module-level** (line 259) — can be imported directly.
- **The `safe_json_dumps()` helper** (line 103) handles datetime serialization — import it if the market builder needs to serialize dates.

---

## File 4: `apps/api/src/api/routes/report_data.py` (57 lines)

### WHAT EXISTS

**Single endpoint:** `GET /v1/reports/{run_id}/data`

```python
@router.get("/reports/{run_id}/data")
def report_data(run_id: str, request: Request):
```

- **Public endpoint** — no auth required (used by print pages for PDF generation)
- Security: validates UUID v4 format to prevent enumeration
- Queries `report_generations` table for `account_id` and `result_json`
- Returns 404 if no row or `result_json` is null
- **Phase 30:** Calls `get_brand_for_account(cur, account_id)` and merges brand info into response
- Response shape: `{ **result_json, "brand": { display_name, logo_url, primary_color, ... } }`

The `result_json` field is whatever `build_result_json()` produced in the worker. Its shape varies by report type but matches the Data Contract in the playbook (Section 7):
```json
{
  "city": "Irvine",
  "report_type": "new_listings_gallery",
  "lookback_days": 30,
  "filters_label": "2+ beds, under $560,000",
  "counts": { "Active": 42, "Pending": 8, "Closed": 15 },
  "metrics": { "median_list_price": 800000, "avg_dom": 18, ... },
  "listings_sample": [ { "address": "...", "list_price": ..., "photo_url": ... } ],
  "ai_insights": "The Irvine market...",
  "brand": { "display_name": "...", "logo_url": "...", ... }
}
```

### WHAT'S RELEVANT FOR MARKET BUILDER

- **The market builder does NOT need this endpoint.** The builder renders HTML server-side from `result_json` stored in the DB — it never calls this API endpoint.
- This endpoint exists for the **legacy frontend pipeline** (`/print/[runId]` → fetch data → hydrate HTML client-side). It becomes less important once server-side PDF generation is in place.
- **However**, the playbook (P2-T5) says to add `pdf_url` and `theme_id` to the response. This is for the frontend detail page — so when a user visits `/app/reports/{id}`, the page can show the PDF link.

### WHAT TO WATCH

- **Don't break this endpoint.** It's still used by the current PDF pipeline (Playwright navigates to `/print/{runId}`, which calls this endpoint). Until the legacy pipeline is fully retired, this endpoint must keep returning the existing shape.
- **Adding fields is safe** (additive). Adding `pdf_url` and `theme_id` won't break existing consumers.
- The `result_json` column is JSONB — it contains the raw output of `build_result_json()`. The market builder templates consume this same data, just formatted differently.

---

## Summary: Import Map for Market Builder

| What | Where | Import Path | Notes |
|------|-------|-------------|-------|
| `compute_color_roles()` | `property_builder.py:147` | `from worker.property_builder import compute_color_roles` | Module-level ✅ |
| `_THEME_DARK_BG` | `property_builder.py:979` | Class attribute on `PropertyReportBuilder` | **Recommend: duplicate the 5-line dict** |
| `_THEME_DEFAULT_COLORS` | `property_builder.py:969` | Class attribute on `PropertyReportBuilder` | **Recommend: duplicate the 5-line dict** |
| `_format_currency` | `property_builder.py:302` | `PropertyReportBuilder._format_currency` | Static method — works but clunky |
| `_format_currency_short` | `property_builder.py:322` | `PropertyReportBuilder._format_currency_short` | Static method |
| `_format_number` | `property_builder.py:312` | `PropertyReportBuilder._format_number` | Static method |
| `_truncate` | `property_builder.py:338` | `PropertyReportBuilder._truncate` | Static method |
| `upload_to_r2()` | `tasks.py:259` | `from worker.tasks import upload_to_r2` | Module-level ✅ |
| `safe_json_dumps()` | `tasks.py:103` | `from worker.tasks import safe_json_dumps` | Module-level ✅ |
| `render_pdf()` | `pdf_engine.py` | `from worker.pdf_engine import render_pdf` | Already imported in tasks.py |
| `build_result_json()` | `report_builders.py` | `from worker.report_builders import build_result_json` | Data computation layer |

## Key Decision: Base Template — Fork

**Verdict: FORK `base.jinja2`, don't share it.**

The property base template is 2,147 lines of mixed infrastructure + property-specific content. Market templates need ~20% of it (page geometry, print CSS, font loading) and none of the property HTML/CSS. A clean fork of ~300-400 lines is far more maintainable than conditional blocks or multi-inheritance.

## Key Decision: Task Strategy

**Recommended: Strategy B (extend existing task) for Phase 2, with a clean extraction refactor if it gets unwieldy.**

The existing `generate_report` task already does Steps 1-5 (data fetch, cache, photo proxy, save result_json) for all 8 report types. Adding a conditional branch after Step 5 that says "if `theme_id` is set → use `MarketReportBuilder` → render HTML → pass to `render_pdf(html_content=html)` → skip frontend" is the minimal change. It avoids duplicating 300+ lines of data fetching logic.

---

## Files Read

1. `apps/worker/src/worker/property_builder.py` (1,224 lines)
2. `apps/worker/src/worker/templates/property/_base/base.jinja2` (2,147 lines)
3. `apps/worker/src/worker/tasks.py` (1,729 lines)
4. `apps/api/src/api/routes/report_data.py` (57 lines)
5. `docs/plan/MARKET_REPORT_PDF_PLAYBOOK.md` (473 lines)

## Ambiguities / Contradictions

1. **Playbook says "new task" (Strategy A); code says "extend" is cleaner (Strategy B).** The playbook's `generate_market_report_task` in P2-T4 implies a separate Celery task, but the data-fetching pipeline (Steps 1-5) would need to be duplicated or extracted. The Builder agent should decide which approach based on code complexity.

2. **Playbook says filters are "static methods, import them" — but they're class-internal `@staticmethod`s.** Importing them requires referencing `PropertyReportBuilder._format_currency` which feels wrong. The cleanest solution is extracting the 4 filter functions to a shared `worker/template_filters.py` module.

3. **The playbook references `render_pdf(html)` but the current market report path passes `html_content=None`.** The CMA report (`process_consumer_report` at line 1476) proves the `html_content` path works — it renders HTML via `PropertyReportBuilder` then passes the string to `render_pdf()`. The market builder should follow the CMA pattern, not the legacy market report pattern.
