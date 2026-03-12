# Market Reports — System Audit

> Generated: March 12 2026 · Scope: builder → on-screen preview → downloadable PDF

---

## 1  High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js 16 / React 19)                              │
│                                                                  │
│  /app/reports/new  ──► UnifiedReportWizard (defaultMode="send_now")
│  /app/schedules/new ──► UnifiedReportWizard (defaultMode="schedule")
│        │                                                         │
│        ├── SharedEmailPreview   (live preview in wizard)         │
│        │                                                         │
│        └── handleSubmit()                                        │
│              ├─ send_now  → POST /api/proxy/v1/reports           │
│              └─ schedule  → POST /api/proxy/v1/schedules         │
└──────────────┬───────────────────────────────────┬───────────────┘
               │                                   │
               ▼                                   ▼
┌──────────────────────────┐     ┌──────────────────────────────┐
│  FastAPI: POST /reports  │     │  FastAPI: POST /schedules    │
│  → INSERT report_gen     │     │  → INSERT schedules row      │
│  → enqueue generate_rpt  │     │  → (no worker task yet)      │
└──────────┬───────────────┘     └──────────────┬───────────────┘
           │                                    │
           │                     ┌──────────────┘
           │                     │ every 60 s
           │                     ▼
           │              schedules_tick.py
           │              → INSERT report_gen
           │              → enqueue generate_rpt
           ▼                     │
     ┌─────┴─────────────────────┘
     ▼
  generate_report  (Celery task — shared by both flows)
     │
     ├── SimplyRETS fetch → PropertyDataExtractor
     ├── report_builders.py → build_result_json()
     ├── Save result_json to report_generations
     │
     ├── render_pdf()   ← pdf_engine.py
     │      │
     │      ├─ Playwright  → navigates to /print/{runId}
     │      └─ PDFShift    → source: /print/{runId}
     │
     │   ┌─ /print/{runId} (server RSC) ────────────────┐
     │   │  fetchData()  → GET /v1/reports/{runId}/data  │
     │   │  loadTemplate() → templates/trendy-*.html     │
     │   │  builder()  → lib/templates.ts hydration      │
     │   │  → raw HTML via dangerouslySetInnerHTML        │
     │   └───────────────────────────────────────────────┘
     │
     ├── Upload PDF to R2 → pdf_url
     ├── (if schedule_id) send email, update schedule_runs
     └── Mark report_generations.status = 'completed'
```

---

## 2  The Builder

### 2.1  One wizard, two modes

Both `/app/reports/new` and `/app/schedules/new` render **the same component**:

| Route | Code | Prop |
|-------|------|------|
| `/app/reports/new` | `<UnifiedReportWizard defaultMode="send_now" />` | One-off report |
| `/app/schedules/new` | `<UnifiedReportWizard defaultMode="schedule" />` | Recurring schedule |

**File:** `apps/web/components/unified-wizard/index.tsx` (336 lines)

### 2.2  Wizard steps

| Step | Component | Collects |
|------|-----------|----------|
| 1 – Story | `StepStory` | Report type ("story") – mapped to `report_type` via `STORY_TO_REPORT_TYPE` |
| 2 – Audience | `StepAudience` | Property-type filter presets (e.g. "Single Family", "Luxury") |
| 3 – Where & When | `StepWhereWhen` | City, ZIP codes, lookback days |
| 4 – Deliver | `StepDeliver` | Delivery mode toggle (send now / schedule), cadence, recipients |

### 2.3  Submit branching (`handleSubmit`)

| Aspect | `send_now` | `schedule` |
|--------|-----------|------------|
| Endpoint | `POST /api/proxy/v1/reports` | `POST /api/proxy/v1/schedules` |
| ZIP field name | `zips` | `zip_codes` |
| Cadence fields | Not sent | `cadence`, `day_of_week`, `send_hour`, `timezone` |
| Recipients | Not sent | `recipients: []` (see **Issue 1**) |
| Immediate generation? | Yes — task enqueued | No — waits for `schedules_tick` |
| Redirect | `/app/reports/{id}` | `/app/schedules` |

### 2.4  Legacy builders still in codebase

| Component | Location | Status |
|-----------|----------|--------|
| `ReportBuilderWizard` | `apps/web/components/v0-report-builder/` | Unused — no route mounts it |
| `ReportBuilder` | `apps/web/components/report-builder/` | Unused — no route mounts it |
| `ScheduleBuilder` | `apps/web/components/schedule-builder/` | Unused — no route mounts it |
| `ReportBuilder` | `reportsbuilder/` | Dev-only standalone app |
| `PreviewPanel` | `scheduledreports/` | Dev-only standalone app |

---

## 3  The On-Screen Preview

### 3.1  Current production preview

The `UnifiedReportWizard` renders `SharedEmailPreview` in the right panel.

**File:** `apps/web/components/shared/email-preview/index.tsx` (230 lines)

Sub-components: `PreviewHeader`, `PreviewNarrative`, `PreviewHeroStat`, `PreviewHighlights`, `PreviewListings`, `PreviewFooter`.

**Data source:** Static sample data from `shared/email-preview/sample-data.ts` (`PREVIEW_CONTENT`), selected by mapping the wizard's `story` to a `PreviewReportType`. This is **not** live data — it is hardcoded sample content that gives a rough visual impression.

### 3.2  Three preview implementations exist

| Preview | Used by | Supports |
|---------|---------|----------|
| `SharedEmailPreview` | `UnifiedReportWizard`, Branding page | 5 report types |
| `EmailPreview` | `ScheduleBuilder` (legacy) | 3 types + null |
| `ReportPreview` | `ReportBuilder` (legacy) | 6 types |

All three are **independent implementations** with no shared rendering logic.

### 3.3  Preview vs. actual output

| Dimension | On-screen preview | Print page / PDF |
|-----------|-------------------|------------------|
| Rendering engine | React components (client) | Raw HTML templates (server RSC) |
| Template files | None — inline React | `templates/trendy-*.html` + `lib/templates.ts` |
| Data | Static sample data | Real `result_json` from the API |
| Branding | Reads from `useBranding()` hook | `injectBrand()` replaces `{{brand_*}}` placeholders |
| Pagination | None (scrollable) | Page-break rules (15 rows/page, 6 cards/page) |
| Field mapping | React props | `listing.street_address`, `listing.bedrooms`, etc. |

**Bottom line:** The preview is a cosmetic mockup. It shares no rendering code with the actual PDF output.

---

## 4  The Downloadable PDF

### 4.1  Generation pipeline

1. **Worker task** (`generate_report` in `tasks.py`) runs `build_result_json()` from `report_builders.py`.
2. `result_json` is saved to `report_generations.result_json`.
3. `render_pdf()` in `pdf_engine.py` is called with the `run_id`.
4. The PDF engine opens `{PRINT_BASE}/print/{run_id}` (either via Playwright locally or PDFShift in production).
5. The **print page** (`app/print/[runId]/page.tsx`) fetches `/v1/reports/{runId}/data`, loads the matching `.html` template from disk, calls the builder function from `lib/templates.ts`, and renders the final HTML.
6. The PDF engine captures that rendered HTML as PDF bytes.
7. PDF is uploaded to Cloudflare R2 and the URL stored in `report_generations.pdf_url`.

### 4.2  Template mapping

| Report type | Template file | Builder function |
|-------------|---------------|------------------|
| `market_snapshot` | `trendy-market-snapshot.html` | `buildMarketSnapshotHtml` |
| `new_listings` | `trendy-new-listings.html` | `buildNewListingsHtml` |
| `inventory` | `trendy-inventory.html` | `buildInventoryHtml` |
| `closed` | `trendy-closed.html` | `buildClosedHtml` |
| `price_bands` | `trendy-price-bands.html` | `buildPriceBandsHtml` |
| `open_houses` | (no dedicated template) | Falls back to simple layout |
| `new_listings_gallery` | `trendy-new-listings-gallery.html` | `buildNewListingsGalleryHtml` |
| `featured_listings` | `trendy-featured-listings.html` | `buildFeaturedListingsHtml` |

### 4.3  Two PDF adapter files

| File | Auth | Modes | Status |
|------|------|-------|--------|
| `pdf_engine.py` | PDFShift `X-API-Key` | URL + raw HTML | **Current** — called by `generate_report` |
| `pdf_adapter.py` | PDFShift Basic Auth | URL only | **Legacy** — may still be imported elsewhere |

### 4.4  Where users access the PDF

On the **reports list page** (`/app/reports`), each completed report row shows:
- **Preview** — opens `html_url` (the print page in a new tab)
- **Download PDF** — opens `pdf_url` directly (R2 link)
- **Share** — copies `pdf_url` to clipboard
- **JSON** — opens `json_url`

---

## 5  Identified Issues & Risks

### Issue 1 — Recipients hardcoded to `[]` in schedule mode

When the unified wizard submits a schedule, it sends `recipients: []` (line ~173 of `unified-wizard/index.tsx`). The `ScheduleCreate` schema in the backend likely requires at least one recipient. This means:
- Schedule creation may silently fail, OR
- Schedules get created with no recipients and emails are never sent.

The old `ScheduleBuilder` properly collected recipients; the `StepDeliver` component in the unified wizard may not.

### Issue 2 — Cadence lossy mapping

The wizard maps:
- `"biweekly"` → `"weekly"`
- `"quarterly"` → `"monthly"`

The actual biweekly/quarterly intent is lost because the API schema only accepts `weekly | monthly`.

### Issue 3 — Preview does not represent the PDF

The on-screen `SharedEmailPreview` is a React component rendering **static sample data**. The actual PDF is built from a completely separate pipeline: HTML templates hydrated with real `result_json`. Changes to one never propagate to the other. Users may expect the preview to match the downloadable output.

### Issue 4 — Field name inconsistency between ZIPs

- One-off reports send `zips`
- Schedules send `zip_codes`

These hit different API schemas (`ReportCreate` vs `ScheduleCreate`), but it means the same wizard has to know which key to use per mode.

### Issue 5 — Two PDF adapter files

Both `pdf_engine.py` and `pdf_adapter.py` exist. They use different authentication methods and have different capabilities. If any import path accidentally references the legacy adapter, PDF generation could fail or behave unexpectedly.

### Issue 6 — Gallery vs. table data keys

Gallery-type report builders populate `result_json.listings` (formatted objects with `hero_photo_url`), while table-type builders populate `result_json.listings_sample` (raw listing dicts). The template builders in `templates.ts` must reference the correct key; a mismatch produces an empty report.

### Issue 7 — Open houses has no dedicated template

The `open_houses` report type exists in `reportTypes.ts` and `report_builders.py`, but the print page has no template mapping for it. It falls through to a basic fallback layout — likely not the intended PDF design.

### Issue 8 — Stale/dead preview code

Three independent preview implementations exist. Only `SharedEmailPreview` is used in production. The other two (`EmailPreview` in schedule-builder, `ReportPreview` in report-builder) are dead code that could confuse developers.

---

## 6  The "Mimics the Scheduler" Concern

The user's observation is correct — **the one-off report builder and the schedule builder are literally the same component** (`UnifiedReportWizard`). The only distinguishing factor is the `defaultMode` prop.

This means:
1. The wizard UI is identical for both flows — same steps, same preview, same layout.
2. Step 4 (`StepDeliver`) shows a delivery mode toggle, which means even when coming from `/app/reports/new`, the user can switch to "schedule" mode.
3. The preview sidebar is the same `SharedEmailPreview` regardless of mode.
4. The wizard state type (`WizardState`) carries schedule-specific fields (`cadence`, `dayOfWeek`, `sendHour`, `timezone`, `recipients`) even in send-now mode — they're just ignored on submit.

This is by design (DRY principle), but it creates UX confusion: **users may not realize whether they're creating a one-off report or a recurring schedule**, especially if the mode toggle in Step 4 is subtle.

---

## 7  File Reference

| Category | Key files |
|----------|-----------|
| Wizard | `apps/web/components/unified-wizard/index.tsx`, `types.ts`, `step-*.tsx` |
| Preview | `apps/web/components/shared/email-preview/index.tsx`, `sample-data.ts` |
| Report API | `apps/api/src/api/routes/reports.py`, `report_data.py` |
| Schedule API | `apps/api/src/api/routes/schedules.py` |
| Worker task | `apps/worker/src/worker/tasks.py` → `generate_report` |
| Result builders | `apps/worker/src/worker/report_builders.py` |
| PDF engine | `apps/worker/src/worker/pdf_engine.py` |
| Print page | `apps/web/app/print/[runId]/page.tsx` |
| HTML templates | `apps/web/templates/trendy-*.html` |
| Template hydration | `apps/web/lib/templates.ts` |
| Reports list | `apps/web/app/app/reports/page.tsx` |
| Report types config | `apps/web/app/lib/reportTypes.ts` |
| DB schema | `db/migrations/0001_base.sql`, `0004_report_payloads.sql` |
