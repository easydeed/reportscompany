# Module: Worker Tasks

> `apps/worker/src/worker/tasks.py` (2102 lines)
> `apps/worker/src/worker/property_tasks/property_report.py`

---

## Change Log

| Date | Change |
|------|--------|
| 2026-04 | **Audit:** Full rewrite against code. Fixed task signatures (`generate_report` takes `(self, run_id, account_id, report_type, params)` not `(schedule_id, run_id)`). Added `process_consumer_report` task. Removed non-existent `send_email` task. Corrected `resolve_recipients_to_emails` signature. Added line numbers. Property tasks moved to `property_tasks/property_report.py`. |
| 2026-03 | Property report task now generates AI Executive Summary via `ai_overview.py`. |
| 2026-02 | `upload_to_r2` returns permanent `R2_PUBLIC_URL`-based link when set. |
| 2026-02 | `generate_property_report_task` wired to fallback-ladder comparables. |
| 2026-01 | Added `_deliver_webhooks` with HMAC-SHA256 signing. |
| 2025-12 | Added `keep_alive_ping` beat task. |

---

## Purpose

Defines all **Celery task** functions executed by the background worker. This is the entry point for every async operation in TrendyReports: market report generation, consumer report generation, email delivery, PDF rendering, webhook delivery, and keep-alive pings.

**Important:** Property report tasks live in a separate module (`property_tasks/property_report.py`), not in `tasks.py`. Both are imported by `app.py` (L64–65).

---

## Task Inventory

| Task name | Celery name | File | Line | Description |
|-----------|-------------|------|------|-------------|
| `generate_report` | `"generate_report"` | `tasks.py` | L778 | Full market report generation pipeline (bind=True, max_retries=3) |
| `process_consumer_report` | `"process_consumer_report"` | `tasks.py` | L1382 | Consumer CMA report: comps, value estimate, SMS/email delivery |
| `ping` | `"ping"` | `tasks.py` | L308 | Simple connectivity test |
| `keep_alive_ping` | `"keep_alive_ping"` | `tasks.py` | L313 | Periodic GET to API `/health` to prevent Render sleep |
| `generate_property_report_task` | (see module) | `property_tasks/property_report.py` | — | Property report HTML → PDF → email pipeline |

---

## Key Functions / Classes

| Name | Signature | Line | Description |
|------|-----------|------|-------------|
| `generate_report` | `(self, run_id: str, account_id: str, report_type: str, params: dict)` | L778 | Main market report Celery task |
| `process_consumer_report` | `(self, report_id: str)` | L1382 | Consumer CMA report Celery task |
| `ping` | `()` | L308 | Returns `"pong"` |
| `keep_alive_ping` | `()` | L313 | GET to API health endpoint |
| `resolve_recipients_to_emails` | `(cur, account_id: str, recipients_raw: list) → list` | L117 | Expand mixed recipient types to email list |
| `upload_to_r2` | `(local_path: str, s3_key: str) → str` | L259 | Upload file to Cloudflare R2, returns URL |
| `_resolve_simplyrets_type` | `(sitex_use_code: Optional[str]) → tuple` | L68 | Map SiteX use code to SimplyRETS type |
| `_post_filter_by_property_type` | `(listings: list, simplyrets_subtype: Optional[str]) → list` | L82 | Filter listings by property subtype |
| `safe_json_dumps` | `(obj)` | L103 | JSON serializer handling datetime objects |
| `_sign` | `(secret: str, body: bytes, ts: str) → str` | L336 | HMAC-SHA256 webhook signature |
| `_deliver_webhooks` | `(account_id: str, event: str, payload: dict)` | L340 | Sign + send webhook to all registered endpoints |
| `_resolve_email_brand` | `(cur, account_id: str)` | L384 | Resolve branding (affiliate cascade) for email |
| `_build_email_payload` | `(report_type, city, zips, lookback, result, pdf_url)` | L492 | Build email context dict |
| `_send_and_log_report_email` | `(conn, cur, account_id, run_id, recipients, ...)` | L561 | Send email + log to `email_log` table |
| `_send_failure_notification` | `(account_id, schedule_id, report_type, city, error_msg)` | L617 | Send error notification to account owner |
| `run_redis_consumer_forever` | `()` | L2025 | Redis stream consumer loop |

---

## `generate_report` Pipeline (L778–1380)

1. Load report generation record from DB (input_params, theme_id, accent_color)
2. Fetch baseline market data from SimplyRETS (via `vendors/simplyrets.py`)
3. `compute_market_stats()` — derive medians from baseline
4. `resolve_filters()` — apply price strategy against medians
5. Re-fetch filtered listings; `elastic_widen_filters()` if < 6 results
6. Build report context via `report_builders.build_result_json()`
7. Generate AI insights via `ai_insights.generate_insight()` (optional)
8. Generate AI PDF narrative via `ai_market_narrative.generate_market_pdf_narrative()` (optional)
9. Render email HTML via `email/template.schedule_email_html()`
10. Generate social image via `social_engine.render_social_image()` (optional)
11. Render PDF via `pdf_engine.render_pdf()` (if schedule has `include_attachment`)
12. Upload PDF to Cloudflare R2
13. `resolve_recipients_to_emails()` — expand recipient types
14. Send email via `email/send.send_schedule_email()`
15. `_deliver_webhooks()` — notify registered webhook endpoints
16. Update `report_generations` record (status, result_json, pdf_url)
17. Update `schedule_runs` record (status, sent_count, failure_reason)

### `resolve_recipients_to_emails` (L117)

Expands mixed recipient types into a deduplicated list of email addresses.

| Recipient type | Resolution |
|----------------|-----------|
| `contact` | Lookup email from `contacts` table |
| `sponsored_agent` | Lookup from `account_users` with sponsor verification |
| `group` | Expand all members of `contact_groups` |
| `manual_email` | Pass through as-is |

### `process_consumer_report` Pipeline (L1382–2024)

1. Load consumer report from DB (property data, delivery method)
2. Search comparables via SimplyRETS
3. Build value estimate from comparable metrics
4. Generate property report PDF
5. Upload PDF to R2
6. Send report to consumer via SMS (Twilio) or email
7. Send notification to agent
8. Log to `sms_logs` table
9. Update `consumer_reports` status

---

## Inputs / Outputs

### `generate_report`

| Direction | Field | Type | Notes |
|-----------|-------|------|-------|
| In | `run_id` | `str` | UUID of `report_generations` row |
| In | `account_id` | `str` | UUID of account |
| In | `report_type` | `str` | One of 8 report type slugs |
| In | `params` | `dict` | `{city, zips, lookback_days, filters, schedule_id}` |
| Side-effect | Email sent | — | Via SendGrid |
| Side-effect | PDF uploaded to R2 | — | `report_generations.pdf_url` updated |
| Side-effect | Webhooks delivered | — | If webhooks registered |
| Side-effect | `report_generations` updated | — | Status, result_json, pdf_url |

### `process_consumer_report`

| Direction | Field | Type | Notes |
|-----------|-------|------|-------|
| In | `report_id` | `str` | UUID of `consumer_reports` row |
| Side-effect | PDF uploaded to R2 | — | `consumer_reports.pdf_url` updated |
| Side-effect | SMS/email sent to consumer | — | Report delivery |
| Side-effect | Notification to agent | — | Via SMS or email |

---

## Dependencies

### Internal

| Module | Usage |
|--------|-------|
| `vendors/simplyrets.py` | Market data fetching (`fetch_properties`) |
| `filter_resolver.py` | `resolve_filters()`, `compute_market_stats()`, `elastic_widen_filters()` |
| `report_builders.py` | `build_result_json()` for all 8 market report types |
| `market_builder.py` | `MarketReportBuilder` for market report HTML rendering |
| `property_builder.py` | `PropertyReportBuilder` for property report HTML rendering |
| `ai_insights.py` | `generate_insight()` — GPT-4o-mini market commentary |
| `ai_market_narrative.py` | `generate_market_pdf_narrative()` — PDF narrative |
| `ai_overview.py` | `generate_overview()` — property executive summary |
| `social_engine.py` | `render_social_image()` — 1080×1920 branded images |
| `pdf_engine.py` | `render_pdf()` — Playwright / PDFShift rendering |
| `pdf_adapter.py` | `generate_pdf()` — PDF adapter (legacy path) |
| `email/send.py` | `send_schedule_email()` — SendGrid delivery |
| `email/template.py` | `schedule_email_html()`, `schedule_email_subject()` |
| `utils/r2.py` | `upload_to_r2()` — R2 file upload |
| `sms/send.py` | SMS delivery for consumer reports |
| `limit_checker.py` | Plan limit enforcement |
| `cache.py` | Redis caching |

### External

| Service | Usage |
|---------|-------|
| Redis | Celery broker + result backend |
| Cloudflare R2 | PDF + asset storage |
| SendGrid | Email delivery |
| PDFShift / Playwright | HTML-to-PDF rendering |
| OpenAI GPT-4o-mini | AI market commentary + property summary |
| SimplyRETS API | Market listing data |
| Twilio | SMS for consumer reports |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| PDFShift error | Task retries 3× (`max_retries=3`) then sets `status = "failed"` |
| SimplyRETS 429 | Task retries with exponential back-off |
| Recipient resolution failure | Skips invalid recipients, logs warning, continues |
| Webhook delivery failure | Logged only — does not fail the task |
| R2 upload failure | Falls back to local file in dev; raises in production |
| AI insight generation failure | Graceful fallback — template text used instead |
| Task exception | `status = "failed"` set on `report_generations`; error stored. `_send_failure_notification()` sends alert to account owner (L617). |
| Consumer report SMS failure | Logged to `sms_logs` with error status |

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
