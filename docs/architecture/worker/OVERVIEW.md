# Worker Service

> `apps/worker/src/worker/` -- Celery-based background task processor

## Architecture

- **Framework:** Celery 5.4 with Redis broker
- **Python:** 3.11+
- **PDF Rendering:** Dual engine -- Playwright (local dev) + PDFShift (production)
- **Templates:** Jinja2 for property reports (5 themes with inheritance)
- **Email:** SendGrid v3 API with retry logic
- **SMS:** Twilio for consumer + agent notifications
- **Data Source:** SimplyRETS MLS API with rate limiting
- **Storage:** Cloudflare R2 (S3-compatible) for PDFs and images
- **AI:** OpenAI GPT-4o-mini for market insights (optional)

## 3-Service Boundary

The Worker handles everything that shouldn't block an API response:
- PDF generation (5-30 seconds)
- MLS data fetching (rate-limited, may need retries)
- Email delivery (SendGrid)
- SMS delivery (Twilio)
- Scheduled report execution (ticker process)
- Image proxying (MLS photos -> R2)

## Deployment

Two separate processes:
1. **Celery Worker** -- Processes tasks from Redis queue
   ```bash
   celery -A worker.app.celery worker -l info
   ```
2. **Scheduler (Ticker)** -- Finds due schedules and enqueues tasks (runs every 60s)
   ```bash
   python -m worker.schedules_tick
   ```

## Key Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_URL` | Celery broker + cache | Required |
| `PDF_ENGINE` | PDF renderer | `playwright` |
| `PDFSHIFT_API_KEY` | PDFShift cloud API key | None |
| `PRINT_BASE` | Frontend URL for print pages | `http://localhost:3000` |
| `SIMPLYRETS_USERNAME/PASSWORD` | MLS data API | Required |
| `SENDGRID_API_KEY` | Email delivery | Required |
| `TWILIO_ACCOUNT_SID/AUTH_TOKEN/PHONE_NUMBER` | SMS | Required |
| `R2_ACCESS_KEY_ID/SECRET/BUCKET/ENDPOINT` | Cloudflare R2 storage | Required |
| `OPENAI_API_KEY` | AI insights | Optional |
| `AI_INSIGHTS_ENABLED` | Enable AI features | `false` |

## File Map

| File | Lines | Purpose |
|------|-------|---------|
| `tasks.py` | 1465 | Core tasks: generate_report, process_consumer_report |
| `report_builders.py` | 904 | Market report JSON builders (8 types) |
| `property_builder.py` | 800 | PropertyReportBuilder with 5 Jinja2 themes |
| `schedules_tick.py` | 448 | Background scheduler process |
| `property_tasks/property_report.py` | 394 | Property report PDF task |
| `ai_insights.py` | 329 | OpenAI market insights |
| `pdf_engine.py` | 286 | Dual PDF engine |
| `filter_resolver.py` | 254 | Market-adaptive filter resolution |
| `query_builders.py` | 363 | SimplyRETS query construction |
| `email/template.py` | 2019 | HTML email templates |
| `email/send.py` | 165 | Email orchestrator |
| `email/providers/sendgrid.py` | 127 | SendGrid API client |
| `sms/send.py` | 148 | Twilio SMS client |
| `vendors/simplyrets.py` | 131 | SimplyRETS API client |
| `utils/photo_proxy.py` | 291 | MLS photo proxy |
| `utils/image_proxy.py` | 213 | Image proxy |
| `limit_checker.py` | 151 | Report limit enforcement |
| `cache.py` | ~50 | Redis caching |
