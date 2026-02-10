# Market Report Generation Flow

## Overview

End-to-end flow from user clicking "Generate" to PDF available for download.

## Flow

```
FRONTEND: Report Builder Wizard
  User selects: area, report type, timeframe, audience
  Clicks "Generate Report"
         |
         | POST /v1/reports
         v
API: Create Report
  1. Check usage limits (evaluate_report_limit)
  2. Insert report_generations (status: pending)
  3. Enqueue to Redis (mr:enqueue:reports)
  4. Return 202 with report_id
         |
         | Redis queue -> Celery
         v
WORKER: generate_report task
  1. Set status: processing
  2. Fetch MLS data (SimplyRETS)
  3. Apply market-adaptive filters
  4. Elastic widening if too few results
  5. Build report JSON (report_builders.py)
  6. Generate PDF (Playwright or PDFShift)
  7. Upload PDF + JSON to R2
  8. Set status: completed, store URLs
  9. Send email (if scheduled)
  10. Deliver webhooks
         |
         v
FRONTEND: Poll for completion
  GET /v1/reports/{id} every 1 second
  When status = completed -> show download links
```

## Key Files

| Service | File | Purpose |
|---------|------|---------|
| Frontend | `components/report-builder/*` | Wizard UI |
| API | `routes/reports.py` | Create endpoint + limit check |
| API | `worker_client.py` | Enqueue to Redis |
| Worker | `tasks.py` -> `generate_report` | Main pipeline |
| Worker | `report_builders.py` | JSON report generation |
| Worker | `vendors/simplyrets.py` | MLS data fetch |
| Worker | `pdf_engine.py` | PDF rendering |
| Worker | `email/send.py` | Email delivery |

## Failure Modes

| Failure | Handling |
|---------|----------|
| Usage limit reached | 429 response, BLOCK decision |
| SimplyRETS rate limit | Exponential backoff, 3 retries |
| PDF rendering timeout | Retry with extended timeout |
| R2 upload failure | Retry with backoff |
| General exception | status=failed, error_message stored |
