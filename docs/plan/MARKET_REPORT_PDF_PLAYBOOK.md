# Playbook — Market Report PDF Theming

> **Project:** Themed PDF generation for all 8 market report types
> **Status:** Phase 4 — E2E testing
> **Agent Prompts:** See `MARKET_REPORT_AGENT_PROMPTS.md` for role definitions
> **Last Updated:** March 12, 2026
> **Gopher Investigation:** GOPHER-001 completed — see Section 10 for findings

---

## 1. Project Goal

Bring market report PDFs to full parity with property reports:
- 5 themed Jinja2 templates (Teal, Bold, Classic, Elegant, Modern)
- Smart Color System (`compute_color_roles`) for WCAG-safe accent colors
- Server-side PDF rendering via PDFShift
- R2 upload with permanent download URLs
- All 8 report types supported

**What this replaces:** The current frontend-only pipeline where `lib/templates.ts` hydrates static HTML templates and the user does browser print-to-PDF. That entire path (`/print/[runId]`, `lib/templates.ts`, `apps/web/templates/trendy-*.html`) becomes legacy.

---

## 2. Architecture Overview

### Current Pipeline (being replaced)
```
Wizard → POST /v1/reports → Worker (data only, saves payload)
  → Frontend /print/[runId] fetches data
  → lib/templates.ts hydrates trendy-*.html
  → User clicks Print → browser PDF (no themes, no R2, no link)
```

### Target Pipeline (property report parity)
```
Wizard → POST /v1/reports (+ theme_id, accent_color)
  → Worker: MarketReportBuilder.render() → themed HTML
  → PDFShift → PDF bytes
  → R2 upload → permanent pdf_url
  → report_generations.pdf_url + status = "complete"
  → User gets: View in browser / Download PDF / Email as attachment
```

### What gets REUSED (zero new code)
| Component | Location | Purpose |
|-----------|----------|---------|
| `compute_color_roles()` | `property_builder.py` | Smart Color System — 6 WCAG-safe variants from 1 accent hex |
| `_THEME_DARK_BG` | `property_builder.py` | Per-theme dark background color for contrast math |
| `pdf_adapter.render_pdf()` | `pdf_adapter.py` | PDFShift HTML→PDF conversion |
| `upload_to_r2()` | `tasks.py` | R2 upload with permanent URL |
| Jinja2 filters | `property_builder.py` | `format_currency`, `format_currency_short`, `format_number`, `truncate` |
| Font preloading | `_base/base.jinja2` | Invisible div that forces font loading before PDF capture |
| Theme color palettes | `property_builder.py` | All 5 theme default colors + accent presets |

### What's NEW
| Component | Owner | Description |
|-----------|-------|-------------|
| `MarketReportBuilder` class | Builder | `apps/worker/src/worker/market_builder.py` — mirrors `PropertyReportBuilder` |
| Jinja2 templates | Designer + Builder | `apps/worker/src/worker/templates/market/` — 5 themes, shared macros |
| `generate_market_report_task` | Builder | New Celery task in `tasks.py` |
| DB migration | Builder | `theme_id` + `accent_color` columns on `report_generations` |
| Wizard fixes | UI Builder | Remove schedule mode, replace email preview with PDF preview |
| Generation script | Builder | `scripts/gen_market_all_themes.py` — QA validation |
| Test suite | Builder | `tests/test_market_templates.py` — 5 themes × 8 types |

---

## 3. Report Types → Layout Mapping

There are 8 report types but only **4 distinct PDF layouts** needed (mirroring the V16 email architecture):

| Layout | Report Types | Key Sections |
|--------|-------------|--------------|
| **Gallery** | `new_listings_gallery`, `featured_listings`, `open_houses` | Hero header, count badge, photo grid (3×2 or 2×2 or large cards), agent footer |
| **Market Narrative** | `market_snapshot` | Hero stat (median price), AI narrative, 2×2 photo grid, stacked stats bar, quick take |
| **Closed/Inventory** | `closed`, `inventory` | Hero stat, 2×2 photo grid with status badges, data table, stacked stats |
| **Analytics** | `price_bands`, `new_listings` | Hero stat, stat blocks, large vertical list |

Each layout is a Jinja2 macro set. The builder selects layout based on `report_type`, same pattern as V16's `LAYOUT_MAP`.

### V16 Email → PDF Translation Notes
- Email uses table-based layout (client compat). PDF uses CSS Grid/Flexbox (Chromium renders it).
- Email hero stat: 56px Georgia serif. PDF: can go bigger (72px+), more breathing room.
- Email photo cards: constrained to 280px wide. PDF at 8.5×11: cards can be 30-40% larger.
- Email has VML fallback for Outlook. PDF has none of that — clean CSS only.
- Both share: gradient header, branded agent footer, accent color system, AI narrative block.

---

## 4. Theme Specifications

All 5 themes from property reports, same visual identities:

| Theme | ID | Header BG | Accent Default | Fonts |
|-------|----|-----------|----------------|-------|
| Teal | `teal` | Navy (#18235c) | Teal (#0d9488) | Inter + Playfair Display |
| Bold | `bold` | Navy (#1B365D) | Gold (#D4A853) | Montserrat + Libre Baskerville |
| Classic | `classic` | Navy (#1e3a5f) | Sky Blue (#4a90d9) | Georgia + system sans |
| Elegant | `elegant` | Charcoal (#1a1a1a) | Burgundy (#8B2252) | Cormorant Garamond + Montserrat |
| Modern | `modern` | Midnight (#0f172a) | Coral (#FF6B54) | DM Sans + Space Grotesk |

Each theme defines its dark background in `_THEME_DARK_BG` for `compute_color_roles()` contrast math.

---

## 5. Phases & Tickets

### Phase 1 — Design (Designer agent)

**P1-T1: V0 Gallery Layout**
- Create a US Letter (8.5×11) PDF layout for the Gallery report type
- Input to V0: the existing PDF screenshot (Flare Media Investor report) + V16 email gallery layout description
- Must include: gradient header with logo + brand name, report title + subtitle (city, period, audience), count badge, photo grid (adaptive: 3×2 for 5-6 listings, 2×2 for 4, stacked for 1-3), agent footer with photo + contact
- Output: clean HTML/CSS that renders at letter size with `@page { size: letter; margin: 0; }`
- All colors parameterized as CSS custom properties (`--primary`, `--accent`, `--accent-on-dark`, `--accent-on-light`, etc.)
- Acceptance: renders correctly in Chrome print preview at 100% scale, no overflow, no clipping

**P1-T2: V0 Market Narrative Layout**
- US Letter layout for Market Snapshot
- Sections: gradient header → hero stat (big serif number) → AI narrative block → 2×2 photo grid → horizontal stats bar (4 metrics) → quick take callout → agent footer
- Same color parameterization as P1-T1
- Acceptance: all sections fit on one page at letter size

**P1-T3: V0 Closed/Inventory Layout**
- US Letter layout for Closed Sales and Inventory
- Sections: gradient header → hero stat → 2×2 photo grid with status badges (SOLD / ACTIVE) → data table (address, beds, baths, sqft, price, DOM) → stats bar → quick take → agent footer
- Acceptance: table handles 3-10 rows without overflow; badges match report type (SOLD for closed, ACTIVE for inventory)

**P1-T4: V0 Analytics Layout**
- US Letter layout for Price Bands and New Listings (vertical list)
- Sections: gradient header → hero stat → stat blocks → vertical property list (large cards, 3-4 per page) → agent footer
- Acceptance: multi-page support (page break between cards if needed)

**P1-T5: Theme Variations**
- Take the Gallery layout from P1-T1 and create 5 theme variants
- Apply the exact color palettes from Section 4 above
- Apply the correct fonts per theme
- Output: 5 HTML files demonstrating the same report in each theme
- Acceptance: all 5 themes visually distinct; accent color roles (on_dark, on_light, text) look correct

### Phase 2 — Backend (Builder agent)

**P2-T1a: Extract Shared Template Filters (prep work)**
- New file: `apps/worker/src/worker/template_filters.py`
- Extract from `PropertyReportBuilder` (static methods at lines 302-346):
  - `format_currency(value)` → `$470,000`
  - `format_currency_short(value)` → `$470k`, `$1.2M`
  - `format_number(value)` → `1,234`
  - `truncate(value, length)` → `"Long title..."`
- Make them plain module-level functions (drop the `@staticmethod`)
- Update `property_builder.py` to import from `template_filters.py` instead of defining them inline
- Verify: `pytest tests/test_property_templates.py -v` still passes after extraction
- Acceptance: filters work identically; property reports unaffected; both builders can `from worker.template_filters import format_currency`

**P2-T1b: Database Migration**
- Add to `report_generations` table:
  - `theme_id VARCHAR(20) DEFAULT NULL` — one of: teal, bold, classic, elegant, modern
  - `accent_color VARCHAR(7) DEFAULT NULL` — hex like #0d9488
- Migration file: `db/migrations/0046_market_report_theme.sql`
- Acceptance: migration runs cleanly; existing rows unaffected (NULL values)

**P2-T2: MarketReportBuilder Class**
- New file: `apps/worker/src/worker/market_builder.py`
- Class: `MarketReportBuilder(report_data: dict)` — single dict input (matches PropertyReportBuilder pattern)
- Method: `render_html() → str` — returns complete HTML string (matches PropertyReportBuilder method name)
- Imports:
  - `from worker.property_builder import compute_color_roles` — module-level function, clean import
  - `from worker.template_filters import format_currency, format_currency_short, format_number, truncate` — extracted in P2-T1a
- Own constants (duplicate from PropertyReportBuilder — static 5-line dicts, not worth coupling):
  - `_THEME_DARK_BG = {"teal": "#18235c", "modern": "#1A1F36", "classic": "#1B365D", "bold": "#15216E", "elegant": "#1a1a1a"}`
  - `_THEME_DEFAULT_COLORS = {"teal": "#34d1c3", "modern": "#FF6B5B", "classic": "#1B365D", "bold": "#15216E", "elegant": "#1a1a1a"}`
- Layout routing: `LAYOUT_MAP` dict mapping report_type → layout template name
- Context builders: `_build_header_context()`, `_build_listings_context()`, `_build_stats_context()`, `_build_agent_context()`
- Theme priority chain (match property builder): accent_color param → branding.primary_color → theme default
- Fallback: unknown theme → `teal`; unknown report_type → `market_snapshot` layout
- Read `property_builder.py` first — match the patterns exactly
- Acceptance: `MarketReportBuilder(sample_data).render_html()` returns valid HTML string

**P2-T3: Jinja2 Templates**
- Directory: `apps/worker/src/worker/templates/market/`
- **FORK the property base template — do NOT share it.** The property base is 2,147 lines of mixed infrastructure + property HTML. Market templates need ~20% of it. (See GOPHER-001 findings.)
- Structure:
  ```
  market/
    _base/
      base.jinja2          ← FORKED from property base: page geometry, print CSS, font loading ONLY (~300-400 lines)
      macros.jinja2         ← NEW: market-specific macros: header, hero_stat, photo_grid, stats_bar, data_table, agent_footer, quick_take, count_badge
    teal/
      market.jinja2         ← extends base, sets teal colors/fonts
    bold/
      market.jinja2
    classic/
      market.jinja2
    elegant/
      market.jinja2
    modern/
      market.jinja2
  ```
- Each theme template sets CSS custom properties and includes the layout blocks via macros
- Layout selection: the builder passes `layout` to the template context, template uses `{% if layout == "gallery" %}` to pick macro blocks
- All 5 themes × 4 layouts × proper fallback for missing data
- Acceptance: all 40 combinations (5 themes × 8 report types) render without Jinja2 errors

**P2-T4: Extend `generate_report` Task for Server-Side PDF**
- File: `apps/worker/src/worker/tasks.py`
- **Strategy B (per GOPHER-001):** Extend the existing `generate_report` task, do NOT create a separate task.
- The existing task already handles Steps 1-5 (data fetch, SimplyRETS, caching, photo proxy, save result_json) for all 8 types. Duplicating that is 300+ lines of unnecessary risk.
- **Add a conditional branch after Step 5 (save result_json, ~line 652):**
  ```
  If theme_id is set on the report_generations row:
    → Load theme_id + accent_color from the row
    → Load branding (for agent info, logo, colors)
    → MarketReportBuilder(report_data).render_html() → html_string
    → render_pdf(run_id, account_id, html_content=html_string) ← passes HTML directly, skips frontend
    → upload_to_r2() → pdf_url
    → Update report_generations SET pdf_url, status = 'completed'
  Else (no theme_id — legacy path):
    → Existing behavior: render_pdf(..., html_content=None) → navigates to /print/{runId}
  ```
- **Reference:** The CMA report task (`process_consumer_report`, line ~1476) already uses the `html_content` path — follow that exact pattern.
- The `report_data` dict passed to `MarketReportBuilder` should be the `result_json` from Step 5, merged with branding info.
- Email delivery (Step 9) and webhooks (Step 10) must continue to work for scheduled reports.
- Acceptance: a report created with `theme_id: "bold"` generates a themed PDF via server-side rendering; a report without `theme_id` still works via the legacy frontend path.

**P2-T5: Wire Report Creation to New Task**
- Modify `apps/api/src/api/routes/reports.py`:
  - `ReportCreate` schema: add optional `theme_id` and `accent_color` fields
  - `POST /v1/reports`: save theme_id + accent_color to report_generations row
  - Enqueue `generate_market_report_task` instead of (or in addition to) current `generate_report`
- Modify `apps/api/src/api/routes/report_data.py`:
  - `GET /v1/reports/{id}`: include `pdf_url`, `theme_id` in response
- If no theme_id provided: read account's `default_theme_id` from `accounts` table
- If no accent_color provided: read account's `secondary_color` from branding
- Acceptance: `POST /v1/reports` with `theme_id: "bold"` triggers the new task; PDF appears at `pdf_url` within 30s

**P2-T6: QA Generation Script**
- New file: `scripts/gen_market_all_themes.py`
- Generates all 5 themes × 8 report types = 40 HTML files (+ optional PDF)
- Uses hardcoded sample data (same shape as `report_generations.payload`)
- Flags: `--html-only`, `--theme <id>`, `--report-type <type>`, `--open`
- Output: `output/market_themes/{theme}_{report_type}.html`
- Index page: `output/market_themes/index.html` with links to all 40 variants
- Pattern: follow `scripts/gen_la_verne_all_themes.py` exactly
- Acceptance: running `python scripts/gen_market_all_themes.py --html-only` produces 40 HTML files, all render correctly in browser

**P2-T7: Test Suite**
- New file: `tests/test_market_templates.py`
- Test classes (mirror `test_property_templates.py`):
  - `TestTemplateExistence` — all 5 theme template files exist
  - `TestTemplateRendering` — each theme × each report type renders without exception
  - `TestHTMLStructure` — no unrendered `{{ }}`, no `"undefined"` text
  - `TestContentRendering` — city name, agent name, listing prices appear in output
  - `TestPrintCSS` — `@page`, `@media print`, `page-break` rules present
  - `TestEdgeCases` — 0 listings, missing optional fields, None values
- Acceptance: `pytest tests/test_market_templates.py -v` passes all tests

### Phase 3 — Frontend (UI Builder agent)

**P3-T1: Remove Schedule Mode from /app/reports/new**
- File: `apps/web/components/unified-wizard/step-deliver.tsx`
- Remove the Send Now / Schedule toggle entirely
- Remove `ScheduleOptions` component
- Keep only the three delivery checkboxes: View in browser, Download PDF, Send via email
- The wizard at `/app/reports/new` is ALWAYS "Send Now" mode
- Scheduling remains at `/app/schedules/new` — that's a separate route, separate flow
- Acceptance: `/app/reports/new` shows no schedule option; `/app/schedules/new` still works as before

**P3-T2: Replace Email Preview with PDF Preview**
- File: `apps/web/components/unified-wizard/index.tsx`
- Right sidebar currently shows `<SharedEmailPreview>` with header "Email Preview"
- Replace with a PDF preview that shows what the actual report will look like
- Options for implementation (pick the simplest that works):
  - **Option A:** Static preview thumbnails per report type (like property wizard page previews at `/previews/pages/{theme}/{page}.jpg`) — generate once, serve as images
  - **Option B:** A lightweight React component that renders a mini version of the PDF layout (simplified, not pixel-perfect) using the selected theme colors
- Header should say "Report Preview" not "Email Preview"
- Summary pills stay (story, audience, city, lookback)
- Updates as user configures: theme colors from branding, report type from story selection
- Acceptance: right sidebar shows a visual that looks like a PDF page, not an email; updates when story/audience changes

**P3-T3: Wire Delivery Options to Server-Side Pipeline**
- File: `apps/web/components/unified-wizard/index.tsx` (handleSubmit function)
- Current behavior: `POST /v1/reports` then `router.push(/app/reports/${id})`
- New behavior after report creation:
  - Poll `GET /v1/reports/{id}` until `status = "complete"` and `pdf_url` exists (same polling pattern as property wizard)
  - **View in browser:** Open `pdf_url` in new tab
  - **Download PDF:** Trigger browser download of `pdf_url`
  - **Send via email:** `POST /v1/reports/{id}/send` with `{ emails: [...], attach_pdf: true }` (new endpoint, Phase 2 stretch)
- Show a generating state while polling (progress indicator, "Generating your report...")
- Include `theme_id` and `accent_color` in the `POST /v1/reports` payload (read from account branding on mount, same pattern as property wizard)
- Acceptance: selecting "Download PDF" creates the report, waits for generation, and downloads the themed PDF

**P3-T4: Report Detail Page — PDF Link**
- File: `apps/web/app/app/reports/[id]/page.tsx` (or wherever report detail lives)
- When `pdf_url` exists on the report: show Download PDF button + View in Browser link
- When status is "generating": show spinner/progress
- When status is "failed": show error message
- Acceptance: visiting a completed report's detail page shows a working PDF download button

### Phase 4 — QA & Polish

**P4-T1: Visual QA Across All Themes**
- Run `scripts/gen_market_all_themes.py` to generate all 40 variants
- Open each HTML in Chrome, check:
  - [ ] Colors match theme spec (header gradient, accent elements, text contrast)
  - [ ] Fonts load correctly (no fallback rendering)
  - [ ] Photos render (or placeholder shown gracefully)
  - [ ] Agent footer aligned, photo/contact info correct
  - [ ] No content overflow at letter size
  - [ ] Print preview looks identical to browser view
- File bugs as needed, route back to Builder

**P4-T2: End-to-End Flow Test**
- Run through the full wizard flow for each report type:
  1. Go to `/app/reports/new`
  2. Select story → audience → city + lookback → delivery (Download PDF)
  3. Wait for generation
  4. Verify: PDF downloads, opens correctly, is themed, has correct data
- Test with: Irvine (dense market), La Verne (thin market), edge cases (0 listings)

**P4-T3: Legacy Cleanup (DEFERRED)**
- Once server-side PDFs are validated and stable:
  - Remove or deprecate: `apps/web/templates/trendy-*.html` (7 template files)
  - Remove or deprecate: `apps/web/lib/templates.ts` (1,185 lines)
  - Remove or deprecate: the fallback simple view in `/print/[runId]/page.tsx`
  - Keep `/print/[runId]` as a browser preview route but have it render from the same Jinja2 HTML (fetch from worker, not hydrate locally)
- NOT blocking launch — do this after the new pipeline is proven

---

## 6. File Manifest

### Files to CREATE
| File | Phase | Agent |
|------|-------|-------|
| `apps/worker/src/worker/template_filters.py` | P2-T1a | Builder |
| `db/migrations/0046_market_report_theme.sql` | P2-T1b | Builder |
| `apps/worker/src/worker/market_builder.py` | P2-T2 | Builder |
| `apps/worker/src/worker/templates/market/_base/base.jinja2` | P2-T3 | Builder |
| `apps/worker/src/worker/templates/market/_base/macros.jinja2` | P2-T3 | Builder |
| `apps/worker/src/worker/templates/market/teal/market.jinja2` | P2-T3 | Builder |
| `apps/worker/src/worker/templates/market/bold/market.jinja2` | P2-T3 | Builder |
| `apps/worker/src/worker/templates/market/classic/market.jinja2` | P2-T3 | Builder |
| `apps/worker/src/worker/templates/market/elegant/market.jinja2` | P2-T3 | Builder |
| `apps/worker/src/worker/templates/market/modern/market.jinja2` | P2-T3 | Builder |
| `scripts/gen_market_all_themes.py` | P2-T6 | Builder |
| `tests/test_market_templates.py` | P2-T7 | Builder |

### Files to MODIFY
| File | Phase | Agent | Changes |
|------|-------|-------|---------|
| `apps/worker/src/worker/property_builder.py` | P2-T1a | Builder | Import filters from `template_filters.py` instead of defining inline |
| `apps/worker/src/worker/tasks.py` | P2-T4 | Builder | Add conditional branch in `generate_report` for server-side PDF when `theme_id` is set |
| `apps/api/src/api/routes/reports.py` | P2-T5 | Builder | Add theme_id/accent_color to schema + creation |
| `apps/api/src/api/routes/report_data.py` | P2-T5 | Builder | Include pdf_url in response |
| `apps/web/components/unified-wizard/step-deliver.tsx` | P3-T1 | UI Builder | Remove schedule mode |
| `apps/web/components/unified-wizard/index.tsx` | P3-T2, T3 | UI Builder | Replace preview, wire delivery |
| `apps/web/components/unified-wizard/types.ts` | P3-T1 | UI Builder | Clean up schedule-related types if needed |

### Files that become LEGACY (Phase 4, deferred)
| File | Lines | Notes |
|------|-------|-------|
| `apps/web/lib/templates.ts` | 1,185 | Frontend hydration builders |
| `apps/web/templates/trendy-*.html` | ~3,500 total | 7 static HTML templates |
| `apps/web/app/print/[runId]/page.tsx` | ~220 | Print page with fallback view |

---

## 7. Data Contract

### Report Generation Payload (already exists in `report_generations.payload`)

The worker task receives this from `input_params`:

```json
{
  "city": "Irvine",
  "zips": null,
  "lookback_days": 30,
  "filters": {
    "subtype": "SingleFamilyResidence",
    "price_strategy": { "mode": "maxprice_pct_of_median_list", "value": 0.70 },
    "preset_display_name": "First-Time Buyer"
  },
  "schedule_id": null
}
```

### Worker Task Output (stored on `report_generations` row after generation)

The `generate_report` task currently stores computed data in the `payload` JSONB. The market builder needs these fields:

```json
{
  "city": "Irvine",
  "report_type": "new_listings_gallery",
  "lookback_days": 30,
  "filters_label": "2+ beds, under $560,000 (70% of Irvine median)",
  "counts": { "Active": 42, "Pending": 8, "Closed": 15 },
  "metrics": {
    "median_list_price": 800000,
    "median_close_price": 785000,
    "avg_dom": 18,
    "months_of_inventory": 2.4,
    "price_per_sqft": 520,
    "list_to_sale_ratio": 0.982
  },
  "listings_sample": [
    {
      "address": "123 Main St, Irvine, CA",
      "list_price": 750000,
      "close_price": 740000,
      "beds": 3,
      "baths": 2.0,
      "sqft": 1850,
      "status": "Active",
      "days_on_market": 12,
      "photo_url": "https://...",
      "lat": 33.68,
      "lng": -117.82
    }
  ],
  "ai_insights": "The Irvine market showed balanced activity this period...",
  "branding": {
    "agent_name": "Jane Smith",
    "agent_title": "Realtor",
    "agent_phone": "(949) 555-1234",
    "agent_email": "jane@example.com",
    "agent_photo_url": "https://...",
    "company_name": "TrendyReports",
    "logo_url": "https://...",
    "primary_color": "#4F46E5",
    "accent_color": "#818CF8"
  }
}
```

### New Fields on `report_generations` (P2-T1 migration)

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| `theme_id` | `VARCHAR(20)` | `NULL` | teal, bold, classic, elegant, modern |
| `accent_color` | `VARCHAR(7)` | `NULL` | Hex like #0d9488 |
| `pdf_url` | already exists | — | Populated by new task |

---

## 8. Dependencies & Sequencing

```
Phase 1 (Design) ──────────────────────────────────────────────┐
  P1-T1 Gallery ─┐                                            │
  P1-T2 Market  ─┤ Can run in parallel                        │
  P1-T3 Closed  ─┤                                            │
  P1-T4 Analytics┘                                            │
  P1-T5 Theme Variations (needs P1-T1 done first)             │
                                                               │
Phase 2 (Backend) ─────────────────── needs P1 designs ────────┘
  P2-T1 Migration (no dependencies)
  P2-T2 Builder class (needs P2-T1)
  P2-T3 Templates (needs P2-T2 + P1 designs)
  P2-T4 Celery task (needs P2-T2 + P2-T3)
  P2-T5 API wiring (needs P2-T4)
  P2-T6 Gen script (needs P2-T2 + P2-T3)
  P2-T7 Test suite (needs P2-T2 + P2-T3)

Phase 3 (Frontend) ──────────── can start P3-T1 immediately ──
  P3-T1 Remove schedule mode (no backend dependency)
  P3-T2 PDF preview (needs P1 designs for reference)
  P3-T3 Wire delivery (needs P2-T5 — API must be ready)
  P3-T4 Report detail (needs P2-T5)

Phase 4 (QA) ─────────────────── needs P2 + P3 complete ──────
  P4-T1 Visual QA
  P4-T2 E2E flow test
  P4-T3 Legacy cleanup (deferred)
```

---

## 9. Reference Docs

| Document | Location | What it contains |
|----------|----------|-----------------|
| Source of Truth | `/docs/architecture/SOURCE_OF_TRUTH.md` | System overview, all integrations, data models |
| Property Builder | `/docs/architecture/modules/property-builder.md` | The model to copy — themes, Smart Color, Jinja2 patterns |
| Email Template V16 | `/docs/architecture/modules/email-template.md` | Layout architecture, V16 modular design, LAYOUT_MAP pattern |
| Worker Tasks | `/docs/architecture/modules/worker-tasks.md` | Celery task patterns, R2 upload, PDF pipeline |
| Frontend Components | `/docs/architecture/modules/frontend-components.md` | Wizard components, SharedEmailPreview, branding page |
| Frontend Pages | `/docs/architecture/modules/frontend-pages.md` | All routes including /app/reports/new |
| Backend Routes | `/docs/architecture/modules/backend-routes.md` | reports.py, report_data.py API contracts |
| Test Suite | `/docs/architecture/modules/test-suite.md` | Existing test patterns to match |
| CLI Tools | `/docs/architecture/modules/cli-tools.md` | Generation script patterns |

### Key Files to READ Before Building
| File | Why |
|------|-----|
| `apps/worker/src/worker/property_builder.py` | The exact class pattern to replicate |
| `apps/worker/src/worker/templates/property/_base/base.jinja2` | Base template to fork (NOT share — see Section 10) |
| `apps/worker/src/worker/templates/property/teal/teal_report.jinja2` | Theme template pattern |
| `apps/worker/src/worker/email/template.py` | V16 layout routing, section builders |
| `apps/worker/src/worker/tasks.py` | `generate_report` — the task to EXTEND (Strategy B — see Section 10) |
| `scripts/gen_la_verne_all_themes.py` | Generation script pattern |
| `tests/test_property_templates.py` | Test suite pattern |

---

## 10. GOPHER-001 Findings & Decisions

> Investigation completed March 12, 2026. Full report: `GOPHER-001_REPORT.md`

### Decision 1: Filter Extraction → `template_filters.py`
- **Finding:** Jinja2 filters (`format_currency`, etc.) are `@staticmethod` inside `PropertyReportBuilder`. Importing as `PropertyReportBuilder._format_currency` is ugly and couples market builder to the property class.
- **Decision:** Extract to `apps/worker/src/worker/template_filters.py` as plain module-level functions. Both builders import from there. Added as ticket P2-T1a.

### Decision 2: Base Template → FORK
- **Finding:** Property `base.jinja2` is 2,147 lines — 80% is property-specific HTML/CSS. Market templates need only ~20% (page geometry, print CSS, font loading).
- **Decision:** Fork into a clean `templates/market/_base/base.jinja2` of ~300-400 lines. Copy infrastructure, skip property content. Updated P2-T3.

### Decision 3: Task Strategy → Strategy B (Extend)
- **Finding:** The existing `generate_report` task handles all 8 report types and does 300+ lines of data fetching (SimplyRETS queries, caching, photo proxy) in Steps 1-5. Creating a separate task would duplicate all of this.
- **Decision:** Add a conditional branch after Step 5: if `theme_id` is set → server-side render via `MarketReportBuilder` → pass HTML to `render_pdf(html_content=...)`. If no `theme_id` → legacy frontend path continues. Updated P2-T4.
- **Reference:** The CMA task (`process_consumer_report`, line ~1476 in tasks.py) already uses the `html_content` path successfully.

### Decision 4: Theme Constants → Duplicate (Don't Import)
- **Finding:** `_THEME_DARK_BG` and `_THEME_DEFAULT_COLORS` are class attributes on `PropertyReportBuilder`, not module-level.
- **Decision:** Duplicate the 5-line dicts in `market_builder.py`. They're static constants that won't change independently — coupling them to `PropertyReportBuilder` class internals is worse than the duplication.

### Import Map (confirmed by investigation)
| What | Import Path | Notes |
|------|-------------|-------|
| `compute_color_roles()` | `from worker.property_builder import compute_color_roles` | Module-level ✅ |
| Filter functions | `from worker.template_filters import format_currency, ...` | After P2-T1a extraction |
| `upload_to_r2()` | `from worker.tasks import upload_to_r2` | Module-level ✅ |
| `safe_json_dumps()` | `from worker.tasks import safe_json_dumps` | Module-level ✅ |
| `render_pdf()` | `from worker.pdf_engine import render_pdf` | Already used in tasks.py |
| `build_result_json()` | `from worker.report_builders import build_result_json` | Data computation layer |
