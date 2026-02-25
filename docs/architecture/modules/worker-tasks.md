# Module: Worker Tasks

> `apps/worker/src/worker/tasks.py`

---

## Purpose

Defines all **Celery task** functions executed by the background worker. This is the entry point for every async operation in TrendyReports: report generation, email delivery, PDF rendering, webhook delivery, and the keep-alive ping that prevents Render cold starts.

---

## Task Inventory

| Task name | Queue | Description |
|-----------|-------|-------------|
| `generate_report` | `default` | Full market report generation pipeline |
| `generate_property_report_task` | `default` | Property report HTML → PDF → email pipeline |
| `send_email` | `email` | Send a pre-rendered email via SendGrid |
| `keep_alive_ping` | `beat` | Periodic GET to API `/health` to prevent Render sleep |

---

## Key Functions

### `generate_report(schedule_id, run_id, ...)` (Celery task)

Full report generation pipeline:
1. Load schedule config from DB
2. Fetch baseline market data from SimplyRETS (via `vendors/simplyrets.py`)
3. `compute_market_stats()` — derive medians
4. `resolve_filters()` — apply price strategy
5. Re-fetch filtered listings; `elastic_widen_filters()` if <6 results
6. Build report context (AI insights, gallery, stats)
7. Render email via Jinja2 template
8. Generate social image (if enabled)
9. Generate PDF (if enabled) via `pdf_engine.py`
10. Upload PDF to Cloudflare R2
11. `resolve_recipients_to_emails()` — expand recipient types
12. Send via `send_email` sub-task
13. `_deliver_webhooks()` — notify registered webhooks
14. Update `schedule_runs` record (status, duration, counts)

### `generate_property_report_task(report_id)` (Celery task)

Property report pipeline:
1. Load property report record from DB (comps, agent info, selected_pages)
2. `PropertyReportBuilder.render()` → HTML string
3. `pdf_adapter.render_pdf(html)` → PDF bytes via PDFShift API
4. Upload PDF to R2, get public URL
5. Update `property_reports.pdf_url` and `status = "complete"`
6. Send notification email to agent (optional)

### `resolve_recipients_to_emails(recipients, sponsor_account_id, cur) → list[str]`

Expands mixed recipient types into a deduplicated list of email addresses.

| Recipient type | Resolution |
|----------------|-----------|
| `contact` | Lookup email from `contacts` table |
| `sponsored_agent` | Lookup from `account_users` with sponsor verification |
| `group` | Expand all members of `contact_groups` |
| `manual_email` | Pass through as-is |

Sponsor relationship is **verified** — a non-matching `sponsor_account_id` raises `ValueError`.

### `upload_to_r2(data: bytes, key: str, content_type: str) → str`

Uploads bytes to Cloudflare R2.
- Returns a presigned public URL with 7-day TTL
- Falls back to local `/tmp` write if R2 credentials are missing (dev mode)

### `_deliver_webhooks(run_id, event_type, payload, account_id, cur)` (internal)

Signs payload with `HMAC-SHA256` using each webhook's secret, then sends `POST` to each registered endpoint.
- Payload signature: `X-TrendyReports-Signature: sha256=<hex>`
- Non-blocking: delivery failures are logged but do not fail the task

### `keep_alive_ping()` (Celery beat task)

- Runs every 5 minutes via Celery beat schedule
- `GET {API_BASE_URL}/health` — prevents Render's free-tier sleep
- Logs response time

### `safe_json_dumps(obj) → str`

Recursively serialises Python objects to JSON, converting `datetime`/`date` to ISO 8601 strings. Used before storing task results in Redis.

---

## Inputs / Outputs

### `generate_property_report_task`

| Direction | Field | Notes |
|-----------|-------|-------|
| In | `report_id` | UUID of `property_reports` row |
| Side-effect | PDF uploaded to R2 | `property_reports.pdf_url` updated |
| Side-effect | `status` updated | `"generating"` → `"complete"` or `"failed"` |

### `generate_report`

| Direction | Field | Notes |
|-----------|-------|-------|
| In | `schedule_id` | UUID of `schedules` row |
| In | `run_id` | UUID of `schedule_runs` row |
| Side-effect | Email sent | Via SendGrid |
| Side-effect | PDF uploaded | If PDF delivery enabled |
| Side-effect | Webhooks delivered | If webhooks registered |
| Side-effect | `schedule_runs` updated | Status, sent_count, duration |

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `vendors/simplyrets.py` | Market data fetching |
| `filter_resolver.py` | Market-adaptive filter resolution |
| `property_builder.py` | HTML rendering for property reports |
| `pdf_engine.py` | PDF generation coordination |
| `pdf_adapter.py` | PDFShift API integration |
| `ai_insights.py` | GPT-4o-mini commentary generation |
| `email/send.py` | Email dispatch |
| `cache.py` | Redis caching |
| `limit_checker.py` | Plan limit enforcement |

### External
| Service | Usage |
|---------|-------|
| Redis | Celery broker + result backend |
| Cloudflare R2 | PDF + asset storage |
| SendGrid | Email delivery |
| PDFShift API | HTML-to-PDF rendering |
| OpenAI GPT-4o-mini | AI market commentary |
| SimplyRETS API | Market listing data |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| PDFShift error | Task retries 3× then sets `status = "failed"` |
| SimplyRETS 429 | Task retries with exponential back-off |
| Recipient resolution failure | Skips invalid recipients, logs warning, continues |
| Webhook delivery failure | Logged only — does not fail the task |
| R2 upload failure | Falls back to local file in dev; raises in production |
| Task exception | Celery sets `status = "failed"` in `schedule_runs` + `property_reports`; error stored in `failure_reason` |

---

## Tests / How to Validate

```bash
# Full report generation (exercises most task code paths)
python scripts/test_all_reports.py

# Property report task specifically
python scripts/test_property_report_flow.py

# QA delivery tool (end-to-end including email)
python qa_deliver_reports.py --base-url $API_URL --token $TOKEN \
  --deliver-to qa@example.com --city Irvine
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02 | `generate_property_report_task` wired to new fallback-ladder-based comparables |
| 2026-01 | Added `_deliver_webhooks` with HMAC-SHA256 signing |
| 2026-01 | Added `sponsor_account_id` verification in `resolve_recipients_to_emails` |
| 2025-12 | Added `keep_alive_ping` beat task for Render cold-start prevention |
| 2025-11 | Added `upload_to_r2` with R2 dev fallback |
| 2025-10 | Initial task definitions |
