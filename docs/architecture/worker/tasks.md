# Celery Tasks

> `apps/worker/src/worker/tasks.py` (1465 lines) + `property_tasks/property_report.py` (394 lines)

## Task Registry

| Task | Trigger | Retries | Queue |
|------|---------|---------|-------|
| `generate_report` | API POST /v1/reports | 3 (exponential backoff, 10min max) | default |
| `process_consumer_report` | API POST /v1/cma/* | 3 | default |
| `generate_property_report` | API POST /v1/property/reports | 3 | celery |
| `ping` | Manual / health check | 0 | default |
| `keep_alive_ping` | Celery Beat (every 5min) | 0 | default |

## generate_report (Market Reports)

The main pipeline task. ~733 lines.

### Pipeline Steps

1. **Status Update** -- Set `processing` in DB
2. **Limit Check** (scheduled reports only) -- Check monthly usage, auto-pause on 3+ failures
3. **Data Fetch** -- SimplyRETS API with market-adaptive filters
4. **Extract & Validate** -- Clean raw MLS data
5. **Elastic Widening** -- If <minimum results, gradually loosen filters
6. **Build Report JSON** -- Route to appropriate builder (market_snapshot, inventory, etc.)
7. **Generate PDF** -- Playwright (local) or PDFShift (cloud)
8. **Upload to R2** -- PDF + JSON to Cloudflare R2, get presigned URLs
9. **Update DB** -- Set `completed`, store URLs
10. **Send Email** -- To schedule recipients with white-label branding + AI insights
11. **Log Email** -- Track delivery in email_log
12. **Reset Counters** -- Clear consecutive_failures on success
13. **Deliver Webhooks** -- HMAC-signed POST to registered URLs

### Error Handling
- Catches all exceptions, sets status='failed', stores error_message
- Increments `consecutive_failures` on schedule
- Auto-pauses schedule after 3 consecutive failures
- Celery auto-retries with exponential backoff

### Key Helpers

| Function | Purpose |
|----------|---------|
| `upload_to_r2(path, key)` | S3-compatible upload to R2, returns presigned URL |
| `resolve_recipients_to_emails(cur, account_id, recipients)` | Resolves typed recipients to email list |
| `_deliver_webhooks(account_id, event, payload)` | HMAC-signed webhook delivery |
| `run_redis_consumer_forever()` | Redis queue bridge (polls mr:enqueue:reports) |

### Recipient Resolution

`resolve_recipients_to_emails()` supports multiple recipient types:

| Type | Resolution |
|------|-----------|
| `contact` | Lookup email from `contacts` table by ID |
| `sponsored_agent` | Lookup email from `users/accounts` by account ID, verifying sponsorship |
| `group` | Expand group members to contacts/sponsored_agents, then resolve each |
| `manual_email` | Use the provided email address directly |
| Plain string | Legacy format, treated as manual_email |

Returns a deduplicated list of valid email addresses.

## process_consumer_report (Consumer/Mobile CMA)

~337 lines. Generates a mobile-friendly property value estimate.

### Pipeline Steps
1. Fetch property data from SimplyRETS
2. Find comparable sales (nearby, similar size/age)
3. Calculate value estimate from comp prices
4. Compute market statistics
5. Update report status='ready'
6. Send SMS to consumer with report link
7. Send SMS to agent with lead notification

## generate_property_report (Property CMA PDF)

~394 lines in `property_tasks/property_report.py`.

### Pipeline Steps
1. Fetch report from DB with JOINs (user, branding)
2. Build HTML with PropertyReportBuilder (Jinja2)
3. Render PDF (Playwright or PDFShift)
4. Upload to R2
5. Update DB: status='complete', pdf_url
