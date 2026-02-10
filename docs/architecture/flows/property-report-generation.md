# Property Report Generation Flow

## Overview

End-to-end flow for creating a property CMA (Comparative Market Analysis) report, from property search through PDF delivery.

## Flow

```
FRONTEND: Property Search
  1. User types address (Google Places autocomplete)
  2. Select property from suggestions
         |
         | POST /v1/property-reports/search
         v
API: Property Lookup
  1. SiteX Pro lookup by address
  2. Return property details
         |
         v
FRONTEND: Comparable Selection
  1. SiteX comparable search returns candidates
  2. User selects/deselects comps
  3. User adjusts comp parameters
         |
         v
FRONTEND: Theme Selection
  1. User picks from 5 available themes
  2. User selects which pages to include
  3. User customizes branding options
         |
         | POST /v1/property-reports
         v
API: Create Property Report
  1. Insert property_reports (status: pending)
  2. Store sitex_data, comparables, selected_pages as JSONB
  3. Enqueue Celery task
  4. Return 202 with report_id
         |
         | Redis queue -> Celery
         v
WORKER: generate_property_report task
  1. Set status: processing
  2. PropertyReportBuilder assembles report data
  3. Render HTML via Jinja2 templates (theme-specific)
  4. Generate PDF (Playwright local / PDFShift production)
  5. Upload PDF to R2
  6. Generate QR code with short_code URL
  7. Upload QR code to R2
  8. Set status: completed, store pdf_url + qr_code_url
         |
         v
FRONTEND: Report Ready
  1. Poll GET /v1/property-reports/{id}
  2. When completed -> show PDF download + QR code
  3. Public link available at /p/{short_code}
```

## Lead Capture Integration

Once a property report is published:

- The public URL `/p/{short_code}` shows the report with a lead capture form
- QR code on printed materials links to the same URL
- Leads submitted through the form are stored and trigger agent notifications

## Key Files

| Service | File | Purpose |
|---------|------|---------|
| Frontend | `components/property-report/*` | Report creation wizard |
| API | `routes/property_reports.py` | CRUD endpoints |
| API | `services/sitex.py` | SiteX Pro integration |
| Worker | `tasks.py` -> `generate_property_report` | Main pipeline |
| Worker | `property_report.py` | PropertyReportBuilder |
| Worker | `templates/property/` | Jinja2 theme templates |
| Worker | `pdf_engine.py` | PDF rendering |

## Failure Modes

| Failure | Handling |
|---------|----------|
| SiteX lookup fails | Error returned to user, retry available |
| No comps found | Warning shown, user can widen search |
| PDF rendering fails | Retry with extended timeout, then mark failed |
| QR code generation fails | Report still delivered, QR code omitted |
| R2 upload fails | Retry with backoff |
