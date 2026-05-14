# TrendyReports — PDF Rendering Pipeline (Canonical)

> **PDFShift is the production PDF renderer. Nothing else.**

## The Truth

All production PDFs for market reports AND property reports are rendered by **PDFShift** (`https://pdfshift.io`) via their HTTPS API.

## What NOT to Suggest

- ❌ **WeasyPrint** — not installed, not used, do not suggest
- ❌ **wkhtmltopdf** — not installed, not used, do not suggest
- ❌ **ReportLab** — not installed, not used, do not suggest
- ❌ **pdfkit / fpdf / xhtml2pdf** — not installed, not used, do not suggest
- ❌ **Puppeteer** — not installed, not used, do not suggest
- ❌ **Server-side Chromium** — not running on Render workers
- ❌ **Playwright in production** — only used as local dev fallback when `PDFSHIFT_API_KEY` is missing
- ❌ **Poetry** — that's a Python package manager, not a PDF tool. Only runs during build/install.

## Production Pipeline

```
Build HTML (Jinja2)
apps/worker/src/worker/market_builder.py   → MarketReportBuilder.render_html()
apps/worker/src/worker/property_builder.py → PropertyReportBuilder.render()

Embed images as base64
apps/worker/src/worker/property_tasks/property_report.py → embed_images_as_base64()
Converts MLS photo URLs and R2 logos to inline data URIs.
This avoids PDFShift servers being blocked by image CDNs.

Send to PDFShift
apps/worker/src/worker/pdf_adapter.py → render_pdf(html)
POST to https://api.pdfshift.io/v3/convert/pdf
HTTP Basic Auth with PDFSHIFT_API_KEY

Receive PDF bytes
PDFShift returns the binary PDF

Upload to R2
apps/worker/src/worker/tasks.py → upload_to_r2()
Key: reports/{account_id}/{filename}.pdf
Returns permanent URL (R2_PUBLIC_URL-based, NOT presigned)

Update DB
UPDATE report_generations SET pdf_url = %s, status = 'completed' WHERE id = %s
```

## Local Dev Fallback

`apps/worker/src/worker/pdf_engine.py` checks `PDFSHIFT_API_KEY`:
- **Key set** → uses PDFShift (production behavior)
- **Key NOT set** → falls back to Playwright/Chromium (local dev only)

The fallback is irrelevant to production. Render has `PDFSHIFT_API_KEY` configured.

## Required Environment Variables

For PDFShift:
- `PDFSHIFT_API_KEY` — required, HTTP Basic Auth credential

For R2 storage:
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_PUBLIC_URL` — when set, returns permanent URLs instead of 7-day presigned

## How to Generate Reports Manually (Testing)

### Option A: Local rendering (no API, no DB writes)

```bash
python scripts/gen_market_reports.py
```

Output: `output/market_reports/{report_type}.pdf`

Uses sample data + local Jinja2 + PDFShift (if key in .env) or Playwright fallback.

### Option B: Via the wizard

1. Login to trendyreports.io
2. Navigate to `/app/reports/new` for market reports OR `/app/property/new` for property reports
3. Fill in the wizard
4. Wizard hits `POST /v1/reports` (or `/v1/property/reports`)
5. Backend enqueues Celery task
6. Worker generates PDF via PDFShift
7. PDF URL appears in the reports list

### Option C: Direct API call (for scripting)

```bash
curl -X POST https://reportscompany-api.onrender.com/v1/reports \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "market_snapshot",
    "city": "Irvine",
    "lookback_days": 30,
    "theme_id": "1"
  }'
```

## Debugging PDF Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| PDF blank/broken | Image URLs not base64-embedded; `&amp;` not unescaped to `&` | Check `embed_images_as_base64()` runs and decodes HTML entities |
| PDF shows wrong template | `theme_id` not set on report row; legacy `/print/{runId}` path being used | Confirm `theme_id` is set; legacy path has been removed |
| 500 error from PDFShift | Malformed HTML, rate limit, timeout | Check Render worker logs for PDFShift error response |
| PDF URL 404 after a week | Using presigned URL instead of permanent | Confirm `R2_PUBLIC_URL` env var is set |
| Fonts wrong in PDF | Google Fonts not loaded before render | Check `<link rel="preconnect">` and font-trigger div in `base.jinja2` |

## Multi-Page Support

As of PDF-COMPREHENSIVE (May 2026):
- `.report-page` uses `min-height: 11in` (NOT `height: 11in; overflow: hidden`)
- `@page` rule defines letter size + 0.5in margins
- Listing cards have `page-break-inside: avoid`
- Section labels + truncation subtitles via Jinja context
- "+ N more listings" callout when total exceeds shown

## PDF_CONFIG (per-report-type caps)

In `apps/worker/src/worker/market_builder.py`:

```python
PDF_CONFIG = {
    "market_snapshot": {cap: 8, section_label: "Recent Activity", ...},
    "new_listings_gallery": {cap: 24, ...},
    "new_listings": {cap: 24, ...},
    "closed": {cap: 20, ...},
    "inventory": {cap: 20, ...},
    "featured_listings": {cap: 12, ...},
    "open_houses": {cap: 20, ...},
    "price_bands": {cap: 8, ...},
}
```

Email caps are in `apps/worker/src/worker/tasks.py` → `EMAIL_LISTING_CAPS`.
