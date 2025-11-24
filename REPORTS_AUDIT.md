# REPORTS SYSTEM - Technical Audit

**Date**: Nov 24, 2025  
**Purpose**: Deep analysis of report generation pipelines (Email HTML, PDF, Images, Preview)  
**Context**: This audit is part of the post-Billing/People/Schedules hardening phase

---

## 1. Data Model & Report Types

### Report Type Definitions

**Frontend** (`apps/web/components/Wizard.tsx`):
```typescript
export type ReportType = "market_snapshot" | "new_listings" | "inventory" | "closed" | "price_bands" | "open_houses"
```

**Backend API** (`apps/api/src/api/routes/schedules.py`):
```python
report_type: Literal[
    "market_snapshot",
    "new_listings",
    "inventory",
    "closed",
    "price_bands",
    "new_listings_gallery",    # Not in frontend Wizard.tsx
    "featured_listings",         # Not in frontend Wizard.tsx
]
```

**Email Worker** (`apps/worker/src/worker/email/template.py`):
```python
report_type_display = {
    "market_snapshot": "Market Snapshot",
    "new_listings": "New Listings",
    "inventory": "Inventory Report",
    "closed": "Closed Sales",
    "price_bands": "Price Bands Analysis",
    "open_houses": "Open Houses",
    "new_listings_gallery": "New Listings Gallery",
    "featured_listings": "Featured Listings",
}
```

**Discrepancy**: `open_houses` is in frontend and email worker but **NOT** in schedule API. `new_listings_gallery` and `featured_listings` are in schedule API and email but **NOT** in frontend wizard.

### Database Tables

**`report_generations`**: Stores report metadata
- `id` (UUID, PK)
- `account_id` (FK to accounts)
- `schedule_id` (FK to schedules, nullable for one-off reports)
- `report_type` (text)
- `status` ('pending', 'processing', 'completed', 'failed', 'skipped_limit')
- `pdf_url` (text, nullable)
- `created_at`, `updated_at`
- `error_message` (text, nullable)

**`schedule_runs`**: Tracks schedule execution history
- `id` (UUID, PK)
- `schedule_id` (FK)
- `account_id` (FK)
- `status` ('pending', 'processing', 'completed', 'failed', 'skipped_limit')
- `started_at`, `completed_at`
- `report_generation_id` (FK, nullable)

**`email_log`**: Audit trail for sent emails
- `id` (UUID, PK)
- `account_id` (FK)
- `schedule_id` (FK, nullable)
- `to_emails` (JSON array)
- `subject` (text)
- `body_snippet` (text, first 500 chars)
- `response_code` (int, e.g., 202 for SendGrid success)
- `response_body` (JSON)
- `created_at`

### Report Run Logging

**Workflow**:
1. Schedule ticker finds due schedules (`next_run_at <= now()`)
2. Creates `schedule_runs` entry (`status = 'pending'`)
3. Enqueues Celery task `generate_report.delay(...)`
4. Task creates `report_generations` entry (`status = 'processing'`)
5. Task:
   - Fetches SimplyRETS data
   - Builds report result
   - Generates PDF (via Playwright)
   - Uploads PDF to R2/S3
   - Updates `report_generations.pdf_url`, `status = 'completed'`
6. Task resolves recipients and sends emails
7. Logs each email send to `email_log`
8. Updates `schedule_runs.status = 'completed'`

---

## 2. HTML Email Pipelines

### Email Template Engine

**File**: `apps/worker/src/worker/email/template.py`

**Function**: `schedule_email_html(...) -> str`

**Inputs**:
- `account_name`: Agent/Affiliate name
- `report_type`: Report type slug
- `city`, `zip_codes`: Area selection
- `lookback_days`: Date range
- `metrics`: Dict of computed metrics (active, pending, closed, DOM, prices)
- `pdf_url`: Direct link to generated PDF
- `unsubscribe_url`: Unique unsubscribe token URL
- `brand`: Optional white-label branding dict (Phase 30)

**Branding Support** (White-Label):
```python
brand_name = brand.get("display_name") or account_name or "Market Reports"
logo_url = brand.get("logo_url")
primary_color = brand.get("primary_color") or "#667eea"
accent_color = brand.get("accent_color") or "#764ba2"
contact_line1 = brand.get("contact_line1")  # e.g., "John Doe | (555) 123-4567"
contact_line2 = brand.get("contact_line2")  # e.g., "john@example.com"
website_url = brand.get("website_url")
```

### Email Layout

**Structure**:
1. **Header**:
   - Logo (affiliate logo if branded, else default Trendy logo)
   - Gradient background (primary → accent color)
2. **Body**:
   - Greeting: "Your [Report Type Display] for [Area]"
   - Metrics table (varies by report type)
   - CTA button: "View Full PDF Report" → `pdf_url`
3. **Footer**:
   - Contact info (if branded)
   - Unsubscribe link
   - Powered by attribution (if affiliate)

### Report-Specific Email Content

#### market_snapshot
**Metrics Displayed**:
- Active Listings: `total_active`
- Pending Listings: `total_pending`
- Closed Sales: `total_closed`
- Median List Price: `median_list_price`
- Median Close Price: `median_close_price`
- Avg Days on Market: `avg_dom`

**Email Quality**: ✅ **WORKS** - Fully polished, branded, clean layout

#### new_listings
**Metrics Displayed**:
- New Listings: `total_active` (or count of new listings)
- Median List Price
- Avg DOM

**Email Quality**: ✅ **WORKS** - Similar to market_snapshot

#### new_listings_gallery
**Metrics Displayed**:
- New Listings count
- Hero image per listing (from `photos[0]` in SimplyRETS)
- Address, Price, Beds/Baths per listing

**Email Quality**: ✅ **WORKS** - Includes inline property photos, gallery layout

#### featured_listings
**Metrics Displayed**:
- Featured properties with hero images
- Similar to gallery but intended for curated selection

**Email Quality**: ✅ **WORKS** - Photo grid layout

#### inventory, closed, price_bands, open_houses
**Metrics Displayed**:
- Generic metrics (count, median price, etc.)
- No custom formatting per report type

**Email Quality**: ⚠️ **PARTIAL** - Template exists, renders, but less polished than market_snapshot

### Known Issues - Email
1. **No inline charts/graphs** - All metrics are text/numbers in tables
2. **Partial reports lack polish** - inventory, closed, price_bands, open_houses show generic metrics
3. **No image embeds** (except gallery reports) - Could embed charts or property thumbnails
4. **Subject line hardcoded** - "Your [Report Type] Report" (no personalization)

---

## 3. PDF Pipelines

### PDF Generation Engine

**Technology**: Playwright (headless Chromium)

**Workflow**:
1. Worker calls `render_pdf_from_url(print_url)` in `apps/worker/src/worker/pdf_adapter.py`
2. Playwright launches headless browser
3. Browser navigates to `print_url` (e.g., `https://app.trendyreports.io/print/{run_id}`)
4. Print page renders report HTML (Next.js server component)
5. Playwright executes `page.pdf()` with options:
   - Format: Letter
   - Print CSS media type
   - Background graphics enabled
6. Returns PDF bytes
7. Worker uploads PDF to R2/S3
8. Updates `report_generations.pdf_url`

### Print Page HTML Builders

**File**: `apps/web/app/print/[runId]/page.tsx`

**Function**: Server component that:
1. Fetches `schedule_runs` data by `runId`
2. Reconstructs report parameters (report_type, city, zip_codes, etc.)
3. Fetches SimplyRETS data (same query as original report)
4. Builds HTML using report-specific builder functions:
   - `buildMarketSnapshotHtml()`
   - `buildNewListingsHtml()`
   - `buildNewListingsGalleryHtml()`
   - `buildFeaturedListingsHtml()`
   - ... (similar for other types)

**Branding in PDF**:
- Fetches account branding from DB
- Applies logo, colors, contact info to PDF header/footer
- Uses `@media print` CSS for clean layouts

### PDF Quality by Report Type

| Report Type | PDF Status | Notes |
|-------------|------------|-------|
| market_snapshot | ✅ WORKS | Clean layout, metrics tables, branded header/footer |
| new_listings | ✅ WORKS | Similar to market_snapshot |
| new_listings_gallery | ✅ WORKS | Gallery grid with hero photos, good page breaks |
| featured_listings | ✅ WORKS | Photo grid layout, branded |
| inventory | ✅ WORKS | Renders but generic layout |
| closed | ✅ WORKS | Renders but less polished |
| price_bands | ✅ WORKS | Renders but lacks visual charts |
| open_houses | ✅ WORKS | Renders, may show "No upcoming open houses" |

### Known Issues - PDF
1. **Page breaks not optimized** - Long tables may split mid-row
2. **No charts/graphs** - All metrics text-based (same as email)
3. **Partial reports generic** - inventory, closed, price_bands lack custom styling
4. **File size** - Large reports (100+ listings) can be 5-10MB (acceptable but could optimize)

---

## 4. Image (JPG/PNG) Pipelines

### Current Status

**Status**: ❌ **NOT_IMPLEMENTED** for any report type

**What Would Be Needed**:
1. **Chart Rendering**:
   - Server-side chart library (e.g., Chart.js with node-canvas, or D3.js)
   - Generate chart images (line graphs for price trends, bar charts for inventory)
2. **Screenshot Pipeline**:
   - Use Playwright to screenshot specific HTML elements
   - Crop to chart/graph area
3. **Storage**:
   - Upload images to R2/S3
   - Store image URLs in `report_generations` table (new column: `image_urls` JSON)
4. **Use Cases**:
   - Social media OG images (for sharing)
   - Inline email images (embed charts in email body)
   - Thumbnail previews in UI

### Recommendation

**Priority**: **Low** unless:
- Social sharing feature is roadmap priority
- Email engagement drops (charts may increase opens/clicks)
- Client requests visual enhancements

**Effort**: Medium (3-5 days for chart rendering + screenshot pipeline + storage)

---

## 5. Frontend Report UX

### Report Preview Pages

**One-Off Reports**:
- Path: `/app/reports` (list of generated reports)
- Path: `/app/reports/[reportId]` (individual report view, if exists)
- Currently: Users see reports in list, click to view PDF

**Schedule Wizard**:
- Path: `/app/schedules/new` (or inline in dashboard)
- Component: `apps/web/components/Wizard.tsx`
- Flow:
  1. Select report type (market_snapshot, new_listings, etc.)
  2. Choose area (city, zips, polygon)
  3. Set filters (property types, lookback days)
  4. Review and create schedule
- **No preview** before creating schedule (users see example metrics but not actual data)

**Print Preview**:
- Path: `/app/print/[runId]`
- Purpose: Doubles as PDF source and browser preview
- Users can view in browser before downloading PDF

### Actions Available

**From Report List**:
- View PDF (opens `pdf_url` in new tab)
- Delete report (if implemented)
- (No "Send via email" or "Reshare" actions currently)

**From Schedule Wizard**:
- Preview example layout (not real data)
- Create schedule → triggers email sends on cadence

### Known UX Gaps

1. **No preview before schedule creation** - Users can't see actual report with their data before committing to a schedule
2. **No one-off "Send Now" action** - Can't generate and send a report immediately without creating a schedule
3. **No report sharing UI** - Can't copy PDF link or share via social media
4. **No edit/resend** - Once sent, can't modify or resend to different recipients

---

## 6. Schedules & Reports Integration

**See**: `SCHEDULE_AUDIT.md` for full schedule system details

### How Schedules Trigger Reports

1. **Schedule Creation** (`POST /v1/schedules`):
   - User specifies `report_type`, area, filters, cadence, recipients
   - Schedule stored in `schedules` table
   - `next_run_at` computed based on cadence + timezone (now supports timezones after S2 hardening)

2. **Schedule Ticker** (`apps/worker/src/worker/schedules_tick.py`):
   - Runs every 60 seconds
   - Queries `schedules` WHERE `active = true` AND `next_run_at <= NOW()`
   - For each due schedule:
     - Creates `schedule_runs` entry
     - Enqueues `generate_report` task with schedule parameters

3. **Report Generation Task** (`apps/worker/src/worker/tasks.py`):
   - Receives `schedule_run_id`, `account_id`, `report_type`, area, filters, recipients
   - Checks plan limits (after S1 hardening)
   - Fetches SimplyRETS data
   - Builds report result
   - Generates PDF
   - Resolves recipients (contacts, sponsored agents, groups)
   - Sends emails with PDF link
   - Logs to `email_log`
   - Updates `schedule_runs.status = 'completed'`
   - Resets failure count (after S3 hardening)

### Report Types Available for Scheduling

**All 8 types can be scheduled**:
- market_snapshot
- new_listings
- inventory
- closed
- price_bands
- open_houses (if in API Literal)
- new_listings_gallery
- featured_listings

**Note**: Discrepancy between frontend wizard and API Literal (see Section 1)

---

## 7. Known Issues & Gaps

### Critical Issues
*None identified - Core pipelines functional*

### Major Issues

1. **Report Type Discrepancy** (Frontend vs API)
   - Severity: **Major**
   - Impact: Users can't schedule `new_listings_gallery` or `featured_listings` from wizard UI, even though API supports them
   - Fix: Add gallery/featured types to `Wizard.tsx` and test UI flow

2. **No Inline Charts in Email** 
   - Severity: **Major** (for engagement)
   - Impact: Email metrics are text-only, less visual appeal than competitors
   - Fix: Implement Chart.js server-side rendering, embed chart images in email HTML

3. **Partial Reports Lack Polish**
   - Severity: **Major** (for professional appearance)
   - Impact: inventory, closed, price_bands, open_houses have generic templates, not branded/styled like market_snapshot
   - Fix: Create custom templates per report type with tailored metrics display

### Minor Issues

4. **No Preview Before Schedule Creation**
   - Severity: **Minor**
   - Impact: Users can't see actual report data before committing to schedule
   - Fix: Add "Preview with real data" button in wizard review step

5. **No One-Off Send Action**
   - Severity: **Minor**
   - Impact: Users must create a schedule even for one-time sends
   - Fix: Add "Generate & Send Now" action in reports UI

6. **Page Breaks Not Optimized**
   - Severity: **Minor**
   - Impact: PDF tables may split awkwardly across pages
   - Fix: Add `page-break-inside: avoid` CSS rules, test with long reports

7. **No Image Exports (JPG/PNG)**
   - Severity: **Low**
   - Impact: Can't generate social share images or email chart embeds
   - Fix: Implement screenshot pipeline (see Section 4)

8. **Featured Listings Not Curated**
   - Severity: **Minor**
   - Impact: `featured_listings` shows top N listings by price, not manually curated
   - Fix: Add UI for agents to select/order featured properties

---

## 8. What Works Well

### ✅ Strengths

1. **market_snapshot is Production-Grade**
   - Clean, branded email HTML
   - Professional PDF layout
   - White-label branding support
   - Reliable data from SimplyRETS

2. **Gallery Reports Include Photos**
   - `new_listings_gallery` and `featured_listings` embed hero images
   - Gallery layout works in both email and PDF
   - Photos load from SimplyRETS CDN (no hosting needed)

3. **White-Label Branding Works**
   - Affiliates can set logo, colors, contact info
   - Branding applied consistently to email and PDF
   - Phase 30 implementation solid

4. **Schedule Integration Solid**
   - Schedules trigger reports reliably
   - Recipient resolution works (contacts, groups, sponsored agents)
   - Unsubscribe flow functional
   - Failure tracking (after S3 hardening)

5. **PDF Generation Reliable**
   - Playwright engine stable
   - R2/S3 upload works
   - PDF URLs publicly accessible
   - Print page doubles as preview

6. **Data Pipeline Clean**
   - SimplyRETS integration mature
   - Query builders modular (`apps/worker/src/worker/query_builders.py`)
   - Error handling for missing data (e.g., no listings shows "No results")

---

## 9. Summary

### Architectural Assessment

**Overall Status**: ✅ **Functionally Sound, Needs Polish**

**Core Pipelines**: 
- Email HTML: ✅ Works, branded, reliable
- PDF: ✅ Works, Playwright stable
- Images (JPG/PNG): ❌ Not implemented (low priority)
- In-App Preview: ✅ Works via `/print` pages

**Report Maturity**:
- **Production-Ready**: market_snapshot, new_listings, new_listings_gallery, featured_listings
- **Functional but Partial**: inventory, closed, price_bands, open_houses
- **Missing from UI**: new_listings_gallery, featured_listings (not in wizard dropdown)

**Integration with Other Systems**:
- ✅ Schedules integrate cleanly
- ✅ People system (contacts, groups) resolves correctly
- ✅ Billing plan limits enforced (after S1 hardening)
- ✅ White-label branding applied consistently

### Recommendation

**Priority 1** (High Impact, Medium Effort):
1. Add `new_listings_gallery` and `featured_listings` to frontend wizard
2. Polish partial reports (inventory, closed, price_bands) to match market_snapshot quality
3. Add inline charts to emails (Chart.js server-side)

**Priority 2** (UX Enhancement):
4. Add "Preview with real data" to schedule wizard
5. Add "Generate & Send Now" one-off action
6. Optimize PDF page breaks

**Priority 3** (Low ROI):
7. Implement image exports (JPG/PNG) for social sharing
8. Add manual curation UI for featured_listings

**Freeze Criteria** (Like People/Billing/Schedules):
- Tests 1-3, 5-6, 9-10 from `REPORTS_QA_CHECKLIST.md` must PASS
- Report types in API must match frontend wizard
- No critical errors in worker logs for any report type

---

**End of Audit**

Use `REPORTS_MATRIX.md` for quick reference and `REPORTS_QA_CHECKLIST.md` for testing.

