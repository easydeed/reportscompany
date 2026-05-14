# Database Schema Reference

> **Source:** Production database (mr-staging-db on Render)
> **Dumped:** 2026-05-05
> **IMPORTANT:** Every Builder and Investigator agent MUST read this file before writing ANY SQL query.

## PDF RENDERING — READ THIS FIRST

> All production PDFs are rendered by **PDFShift** (https://pdfshift.io).
> Nothing else. No WeasyPrint. No wkhtmltopdf. No Playwright in production. No headless Chromium on the worker.

### Production PDF Pipeline

1. **Build HTML**: Worker uses Jinja2 templates to render the report HTML
   - Market reports: `apps/worker/src/worker/market_builder.py` → `MarketReportBuilder.render_html()`
   - Property reports: `apps/worker/src/worker/property_builder.py` → `PropertyReportBuilder.render()`
   - Templates live in: `apps/worker/src/worker/templates/`
2. **Embed images as base64**: Before sending to PDFShift, all external image URLs (MLS photos, R2-hosted logos, Google Maps) are inlined as base64 data URIs to avoid PDFShift's servers being blocked by image CDNs. See `apps/worker/src/worker/property_tasks/property_report.py:embed_images_as_base64()`.
3. **Send to PDFShift**: HTTPS POST to `https://api.pdfshift.io/v3/convert/pdf` with HTTP Basic Auth using `PDFSHIFT_API_KEY`. See `apps/worker/src/worker/pdf_adapter.py`.
4. **Receive PDF bytes**: PDFShift returns the binary PDF.
5. **Upload to R2**: `upload_to_r2()` puts the PDF in Cloudflare R2 with key `reports/{account_id}/{filename}.pdf`. Returns a permanent URL (`R2_PUBLIC_URL`-based, not presigned).

### What NOT to suggest

- ❌ WeasyPrint — not installed, not used
- ❌ wkhtmltopdf — not installed, not used
- ❌ ReportLab — not installed, not used
- ❌ pdfkit / fpdf / xhtml2pdf — not installed, not used
- ❌ Playwright in production — only used as a dev fallback when PDFShift key is missing
- ❌ Server-side Chromium / Puppeteer — not running on Render
- ❌ Poetry — that's a Python package manager, not a PDF tool. It only runs during build/install.

### Local dev fallback

`apps/worker/src/worker/pdf_engine.py` checks if `PDFSHIFT_API_KEY` is set:
- If set → uses PDFShift (production behavior)
- If not set → falls back to Playwright/Chromium (dev only)

This fallback is irrelevant to production. Render has `PDFSHIFT_API_KEY` set.

### Required environment variables for PDF generation

- `PDFSHIFT_API_KEY` — required, HTTP Basic Auth credential for PDFShift
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL` — for PDF storage

### How to manually generate a report for testing

Don't try to run Python scripts locally — most agents won't have the right environment. Instead:

1. Login to trendyreports.io as a test account
2. Use the wizard at /app/reports/new
3. The wizard hits POST /v1/reports, which enqueues a Celery task
4. The worker renders HTML, calls PDFShift, uploads to R2
5. The pdf_url comes back via polling

Test the API directly with curl:

```bash
curl -X POST https://reportscompany-api.onrender.com/v1/reports \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "market_snapshot", "city": "Irvine", "lookback_days": 30}'
```

### Debugging PDF issues

- PDF blank/broken? → Check `embed_images_as_base64()` is running and image URLs are unescaping `&amp;` → `&`
- PDF showing wrong template? → Check `theme_id` is set on the report_generations row; legacy `/print/{runId}` path has been removed
- PDF rendering errors? → Check Render worker logs for PDFShift API errors (rate limits, timeouts, malformed HTML)

## Tables

### account_users

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| account_id | uuid | NO |  |
| user_id | uuid | NO |  |
| role | text | NO |  |
| created_at | timestamp without time zone | YES | now() |

### accounts

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| name | character varying | NO |  |
| slug | character varying | NO |  |
| status | character varying | YES | 'active'::character varying |
| logo_url | character varying | YES |  |
| primary_color | character varying | YES | '#03374f'::character varying |
| secondary_color | character varying | YES | '#ffffff'::character varying |
| plan_id | integer | YES |  |
| subscription_status | character varying | YES |  |
| trial_ends_at | timestamp without time zone | YES |  |
| monthly_report_limit | integer | YES | 100 |
| api_rate_limit | integer | YES | 60 |
| created_at | timestamp without time zone | YES | now() |
| updated_at | timestamp without time zone | YES | now() |
| stripe_customer_id | character varying | YES |  |
| stripe_subscription_id | character varying | YES |  |
| plan_slug | character varying | YES |  |
| billing_status | character varying | YES |  |
| account_type | text | NO | 'REGULAR'::text |
| monthly_report_limit_override | integer | YES |  |
| sponsor_account_id | uuid | YES |  |
| footer_logo_url | text | YES |  |
| email_logo_url | text | YES |  |
| email_footer_logo_url | text | YES |  |
| rep_photo_url | text | YES |  |
| contact_line1 | text | YES |  |
| contact_line2 | text | YES |  |
| website_url | text | YES |  |
| is_active | boolean | NO | true |
| sms_credits | integer | NO | 0 |
| default_theme_id | integer | YES | 4 |
| plan_downgrade_at | timestamp with time zone | YES |  |
| plan_downgrade_to | character varying | YES |  |
| parent_account_id | uuid | YES |  |
| market_reports_limit_override | integer | YES |  |
| schedules_limit_override | integer | YES |  |
| property_reports_limit_override | integer | YES |  |

### admin_agent_leaderboard

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| agent_id | uuid | YES |  |
| agent_name | text | YES |  |
| agent_email | character varying | YES |  |
| account_name | character varying | YES |  |
| total_reports | bigint | YES |  |
| reports_30d | bigint | YES |  |
| total_views | bigint | YES |  |
| contacts | bigint | YES |  |
| contact_rate_pct | numeric | YES |  |
| pdfs_downloaded | bigint | YES |  |

### admin_daily_metrics

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| date | date | YES |  |
| reports_requested | bigint | YES |  |
| reports_ready | bigint | YES |  |
| reports_failed | bigint | YES |  |
| pdfs_generated | bigint | YES |  |
| agent_contacts | bigint | YES |  |
| total_views | bigint | YES |  |
| avg_views_per_report | numeric | YES |  |
| avg_time_seconds | numeric | YES |  |
| unique_agents | bigint | YES |  |

### admin_hourly_distribution

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| hour | numeric | YES |  |
| report_count | bigint | YES |  |
| pdf_count | bigint | YES |  |

### affiliate_branding

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| account_id | uuid | NO |  |
| brand_display_name | text | NO |  |
| logo_url | text | YES |  |
| primary_color | text | YES |  |
| accent_color | text | YES |  |
| rep_photo_url | text | YES |  |
| contact_line1 | text | YES |  |
| contact_line2 | text | YES |  |
| website_url | text | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| email_logo_url | text | YES |  |
| footer_logo_url | text | YES |  |
| email_footer_logo_url | text | YES |  |
| branding_override | boolean | YES | false |

### agent_daily_summaries

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| summary_date | date | NO |  |
| tasks_completed | integer | YES | 0 |
| tasks_failed | integer | YES | 0 |
| total_cost_cents | integer | YES | 0 |
| total_tokens | integer | YES | 0 |
| prs_merged | integer | YES | 0 |
| summary_text | text | YES |  |
| created_at | timestamp with time zone | NO | now() |

### agent_lead_page_stats

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| user_id | uuid | YES |  |
| agent_code | character varying | YES |  |
| agent_name | text | YES |  |
| landing_page_visits | integer | YES |  |
| total_leads | bigint | YES |  |
| leads_7d | bigint | YES |  |
| leads_30d | bigint | YES |  |
| contacts | bigint | YES |  |
| contact_rate_pct | numeric | YES |  |
| conversion_rate_pct | numeric | YES |  |

### agent_task_events

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| task_id | uuid | NO |  |
| agent_name | text | NO |  |
| event_type | text | NO |  |
| input_summary | text | YES | ''::text |
| output_summary | text | YES | ''::text |
| tokens_used | integer | YES | 0 |
| cost_cents | integer | YES | 0 |
| duration_seconds | integer | YES | 0 |
| created_at | timestamp with time zone | NO | now() |

### agent_tasks

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| title | text | NO |  |
| description | text | NO | ''::text |
| context | text | YES | ''::text |
| trust_level | text | NO | 'full_auto'::text |
| priority | text | NO | 'medium'::text |
| status | text | NO | 'queued'::text |
| plan | text | YES |  |
| code_diff | text | YES |  |
| review_notes | text | YES |  |
| review_attempts | integer | YES | 0 |
| test_output | text | YES |  |
| error_message | text | YES |  |
| branch_name | text | YES |  |
| pr_url | text | YES |  |
| preview_url | text | YES |  |
| commit_sha | text | YES |  |
| files_changed | jsonb | YES | '[]'::jsonb |
| agent_log | jsonb | YES | '[]'::jsonb |
| estimated_complexity | text | YES |  |
| actual_duration_seconds | integer | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| started_at | timestamp with time zone | YES |  |
| completed_at | timestamp with time zone | YES |  |

### api_keys

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| user_id | uuid | YES |  |
| key_prefix | character varying | YES |  |
| key_hash | character varying | YES |  |
| name | character varying | YES |  |
| scopes | ARRAY | YES |  |
| rate_limit | integer | YES | 60 |
| is_active | boolean | YES | true |
| last_used_at | timestamp without time zone | YES |  |
| expires_at | timestamp without time zone | YES |  |
| created_at | timestamp without time zone | YES | now() |
| updated_at | timestamp without time zone | YES | now() |

### billing_events

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| type | character varying | NO |  |
| payload | jsonb | NO |  |
| created_at | timestamp without time zone | YES | now() |

### blocked_ips

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| ip_address | character varying | NO |  |
| reason | character varying | YES |  |
| blocked_by | uuid | YES |  |
| created_at | timestamp with time zone | NO | now() |
| expires_at | timestamp with time zone | YES |  |

### consumer_reports

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| agent_id | uuid | NO |  |
| agent_code | character varying | NO |  |
| consumer_phone | character varying | YES |  |
| consumer_email | character varying | YES |  |
| consent_given | boolean | YES | false |
| consent_timestamp | timestamp with time zone | YES |  |
| property_address | text | NO |  |
| property_city | character varying | YES |  |
| property_state | character varying | YES |  |
| property_zip | character varying | YES |  |
| property_data | jsonb | NO | '{}'::jsonb |
| comparables | jsonb | NO | '[]'::jsonb |
| market_stats | jsonb | YES | '{}'::jsonb |
| value_estimate | jsonb | YES | '{}'::jsonb |
| status | character varying | YES | 'pending'::character varying |
| error_message | text | YES |  |
| pdf_url | text | YES |  |
| pdf_generated_at | timestamp with time zone | YES |  |
| pdf_requested_count | integer | YES | 0 |
| consumer_sms_sent_at | timestamp with time zone | YES |  |
| consumer_sms_sid | character varying | YES |  |
| agent_sms_sent_at | timestamp with time zone | YES |  |
| agent_sms_sid | character varying | YES |  |
| view_count | integer | YES | 0 |
| unique_views | integer | YES | 0 |
| first_viewed_at | timestamp with time zone | YES |  |
| last_viewed_at | timestamp with time zone | YES |  |
| tabs_viewed | jsonb | YES | '[]'::jsonb |
| time_on_page | integer | YES | 0 |
| agent_contact_clicked | boolean | YES | false |
| agent_contact_type | character varying | YES |  |
| ip_address | inet | YES |  |
| user_agent | text | YES |  |
| device_type | character varying | YES |  |
| referrer | text | YES |  |
| created_at | timestamp with time zone | YES | now() |
| updated_at | timestamp with time zone | YES | now() |
| property_owner | character varying | YES |  |
| delivery_method | character varying | YES | 'sms'::character varying |
| consumer_email_sent_at | timestamp with time zone | YES |  |

### contact_group_members

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| group_id | uuid | NO |  |
| account_id | uuid | NO |  |
| member_type | text | NO |  |
| member_id | uuid | NO |  |
| created_at | timestamp with time zone | NO | now() |

### contact_groups

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| name | text | NO |  |
| description | text | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

### contacts

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| name | text | NO |  |
| email | text | YES |  |
| type | text | NO |  |
| notes | text | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| phone | text | YES |  |

### document_authenticity

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| short_code | character varying | NO |  |
| document_type | character varying | NO |  |
| property_address | text | YES |  |
| property_apn | character varying | YES |  |
| county | character varying | YES |  |
| grantor_display | character varying | YES |  |
| grantee_display | character varying | YES |  |
| content_hash | character varying | NO |  |
| pdf_hash | character varying | YES |  |
| generated_at | timestamp with time zone | YES | now() |
| first_verified_at | timestamp with time zone | YES |  |
| last_verified_at | timestamp with time zone | YES |  |
| verification_count | integer | YES | 0 |
| organization_id | uuid | YES |  |
| created_by_user_id | uuid | YES |  |
| status | character varying | YES | 'active'::character varying |
| revoked_at | timestamp with time zone | YES |  |
| revoked_reason | text | YES |  |
| superseded_by | uuid | YES |  |
| deed_id | integer | YES |  |

### email_log

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| schedule_id | uuid | YES |  |
| report_id | uuid | YES |  |
| provider | text | YES |  |
| to_emails | ARRAY | YES |  |
| subject | text | YES |  |
| response_code | integer | YES |  |
| error | text | YES |  |
| created_at | timestamp with time zone | YES | now() |
| status | text | YES | 'unknown'::text |

### email_suppressions

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| email | text | NO |  |
| reason | text | YES |  |
| created_at | timestamp with time zone | YES | now() |

### email_verification_tokens

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| user_id | uuid | NO |  |
| email | character varying | NO |  |
| token | character varying | NO |  |
| expires_at | timestamp with time zone | NO |  |
| verified_at | timestamp with time zone | YES |  |
| created_at | timestamp with time zone | NO | now() |

### jwt_blacklist

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| token_hash | character varying | NO |  |
| user_id | uuid | YES |  |
| expires_at | timestamp with time zone | NO |  |
| invalidated_at | timestamp with time zone | NO | now() |

### lead_rate_limits

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| ip_address | character varying | NO |  |
| property_report_id | uuid | YES |  |
| submitted_at | timestamp with time zone | NO | now() |

### leads

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| property_report_id | uuid | YES |  |
| name | character varying | YES |  |
| email | character varying | YES |  |
| phone | character varying | YES |  |
| message | text | YES |  |
| source | character varying | NO | 'direct_link'::character varying |
| consent_given | boolean | NO | false |
| sms_sent_at | timestamp with time zone | YES |  |
| email_sent_at | timestamp with time zone | YES |  |
| status | character varying | NO | 'new'::character varying |
| notes | text | YES |  |
| ip_address | character varying | YES |  |
| user_agent | text | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| consumer_report_id | uuid | YES |  |

### login_attempts

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| email | character varying | NO |  |
| success | boolean | NO | false |
| ip_address | inet | YES |  |
| attempted_at | timestamp with time zone | NO | now() |

### onboarding_progress

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| user_id | uuid | NO |  |
| step_key | character varying | NO |  |
| completed_at | timestamp without time zone | YES |  |
| skipped_at | timestamp without time zone | YES |  |
| metadata | jsonb | YES | '{}'::jsonb |
| created_at | timestamp without time zone | YES | now() |
| updated_at | timestamp without time zone | YES | now() |

### password_reset_tokens

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| user_id | uuid | NO |  |
| token | character varying | NO |  |
| expires_at | timestamp with time zone | NO |  |
| used_at | timestamp with time zone | YES |  |
| created_at | timestamp with time zone | NO | now() |

### plans

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| plan_slug | text | NO |  |
| plan_name | text | NO |  |
| monthly_report_limit | integer | NO |  |
| allow_overage | boolean | NO | false |
| overage_price_cents | integer | NO | 0 |
| stripe_price_id | text | YES |  |
| description | text | YES |  |
| is_active | boolean | NO | true |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| property_reports_per_month | integer | YES |  |
| sms_credits_per_month | integer | YES |  |
| lead_capture_enabled | boolean | NO | false |
| market_reports_limit | integer | YES |  |
| schedules_limit | integer | YES |  |

### platform_property_stats

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | integer | NO | 1 |
| total_reports | integer | NO | 0 |
| completed_reports | integer | NO | 0 |
| failed_reports | integer | NO | 0 |
| reports_by_regular | integer | NO | 0 |
| reports_by_sponsored | integer | NO | 0 |
| reports_by_affiliate | integer | NO | 0 |
| total_views | integer | NO | 0 |
| total_unique_visitors | integer | NO | 0 |
| total_leads | integer | NO | 0 |
| accounts_with_reports | integer | NO | 0 |
| active_landing_pages | integer | NO | 0 |
| theme_classic | integer | NO | 0 |
| theme_modern | integer | NO | 0 |
| theme_elegant | integer | NO | 0 |
| theme_teal | integer | NO | 0 |
| theme_bold | integer | NO | 0 |
| reports_last_30d | integer | NO | 0 |
| leads_last_30d | integer | NO | 0 |
| platform_conversion_rate | numeric | YES | 0 |
| platform_completion_rate | numeric | YES | 0 |
| avg_reports_per_account | numeric | YES | 0 |
| stats_updated_at | timestamp with time zone | NO | now() |

### property_report_stats

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| account_id | uuid | NO |  |
| total_reports | integer | NO | 0 |
| completed_reports | integer | NO | 0 |
| failed_reports | integer | NO | 0 |
| draft_reports | integer | NO | 0 |
| processing_reports | integer | NO | 0 |
| seller_reports | integer | NO | 0 |
| buyer_reports | integer | NO | 0 |
| theme_classic | integer | NO | 0 |
| theme_modern | integer | NO | 0 |
| theme_elegant | integer | NO | 0 |
| theme_teal | integer | NO | 0 |
| theme_bold | integer | NO | 0 |
| total_views | integer | NO | 0 |
| unique_visitors | integer | NO | 0 |
| active_landing_pages | integer | NO | 0 |
| total_leads | integer | NO | 0 |
| leads_from_qr | integer | NO | 0 |
| leads_from_direct | integer | NO | 0 |
| leads_converted | integer | NO | 0 |
| conversion_rate | numeric | YES | 0 |
| completion_rate | numeric | YES | 0 |
| reports_last_30d | integer | NO | 0 |
| leads_last_30d | integer | NO | 0 |
| views_last_30d | integer | NO | 0 |
| last_report_at | timestamp with time zone | YES |  |
| last_lead_at | timestamp with time zone | YES |  |
| stats_updated_at | timestamp with time zone | NO | now() |
| created_at | timestamp with time zone | NO | now() |

### property_report_stats_daily

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| stat_date | date | NO |  |
| reports_created | integer | NO | 0 |
| reports_completed | integer | NO | 0 |
| reports_failed | integer | NO | 0 |
| views | integer | NO | 0 |
| unique_visitors | integer | NO | 0 |
| leads_captured | integer | NO | 0 |
| leads_from_qr | integer | NO | 0 |
| leads_from_direct | integer | NO | 0 |
| theme_classic | integer | NO | 0 |
| theme_modern | integer | NO | 0 |
| theme_elegant | integer | NO | 0 |
| theme_teal | integer | NO | 0 |
| theme_bold | integer | NO | 0 |
| created_at | timestamp with time zone | NO | now() |

### property_reports

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| user_id | uuid | YES |  |
| report_type | character varying | NO |  |
| theme | integer | NO | 1 |
| accent_color | character varying | YES | '#2563eb'::character varying |
| language | character varying | NO | 'en'::character varying |
| property_address | character varying | NO |  |
| property_city | character varying | NO |  |
| property_state | character varying | NO |  |
| property_zip | character varying | NO |  |
| property_county | character varying | YES |  |
| apn | character varying | YES |  |
| owner_name | character varying | YES |  |
| legal_description | text | YES |  |
| property_type | character varying | YES |  |
| sitex_data | jsonb | YES |  |
| comparables | jsonb | YES |  |
| pdf_url | character varying | YES |  |
| status | character varying | NO | 'draft'::character varying |
| error_message | text | YES |  |
| short_code | character varying | YES |  |
| qr_code_url | character varying | YES |  |
| view_count | integer | NO | 0 |
| unique_visitors | integer | NO | 0 |
| last_viewed_at | timestamp with time zone | YES |  |
| is_active | boolean | NO | true |
| expires_at | timestamp with time zone | YES |  |
| max_leads | integer | YES |  |
| access_code | character varying | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| selected_pages | jsonb | YES |  |

### report_analytics

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| report_id | uuid | YES |  |
| event_type | character varying | NO |  |
| event_data | jsonb | YES | '{}'::jsonb |
| session_id | character varying | YES |  |
| ip_address | inet | YES |  |
| user_agent | text | YES |  |
| device_type | character varying | YES |  |
| created_at | timestamp with time zone | YES | now() |

### report_generations

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| user_id | uuid | YES |  |
| report_type | character varying | NO |  |
| cities | ARRAY | YES |  |
| lookback_days | integer | YES |  |
| property_type | character varying | YES |  |
| additional_params | jsonb | YES |  |
| html_url | character varying | YES |  |
| json_url | character varying | YES |  |
| csv_url | character varying | YES |  |
| pdf_url | character varying | YES |  |
| status | character varying | YES | 'pending'::character varying |
| error_message | text | YES |  |
| processing_time_ms | integer | YES |  |
| billable | boolean | YES | true |
| billed_at | timestamp without time zone | YES |  |
| generated_at | timestamp without time zone | YES | now() |
| expires_at | timestamp without time zone | YES |  |
| input_params | jsonb | YES |  |
| result_json | jsonb | YES |  |
| error | text | YES |  |
| source_vendor | text | YES | 'simplyrets'::text |
| theme_id | character varying | YES | NULL::character varying |
| accent_color | character varying | YES | NULL::character varying |

### schedule_runs

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| schedule_id | uuid | NO |  |
| report_run_id | uuid | YES |  |
| status | text | NO | 'queued'::text |
| error | text | YES |  |
| started_at | timestamp with time zone | YES |  |
| finished_at | timestamp with time zone | YES |  |
| created_at | timestamp with time zone | YES | now() |

### schedules

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| name | text | NO |  |
| report_type | text | NO |  |
| city | text | YES |  |
| zip_codes | ARRAY | YES |  |
| lookback_days | integer | YES | 30 |
| cadence | text | NO |  |
| weekly_dow | integer | YES |  |
| monthly_dom | integer | YES |  |
| send_hour | integer | YES | 9 |
| send_minute | integer | YES | 0 |
| recipients | ARRAY | NO |  |
| include_attachment | boolean | YES | false |
| active | boolean | YES | true |
| last_run_at | timestamp with time zone | YES |  |
| next_run_at | timestamp with time zone | YES |  |
| created_at | timestamp with time zone | YES | now() |
| timezone | text | NO | 'UTC'::text |
| consecutive_failures | integer | NO | 0 |
| last_error | text | YES |  |
| last_error_at | timestamp with time zone | YES |  |
| processing_locked_at | timestamp with time zone | YES |  |
| filters | jsonb | NO | '{}'::jsonb |

### signup_tokens

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | integer | NO | nextval('signup_tokens_id_seq'::regclass) |
| token | text | NO |  |
| user_id | uuid | NO |  |
| account_id | uuid | NO |  |
| used | boolean | YES | false |
| created_at | timestamp without time zone | YES | now() |
| expires_at | timestamp without time zone | YES | (now() + '7 days'::interval) |

### sms_logs

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | YES |  |
| lead_id | uuid | YES |  |
| to_phone | character varying | NO |  |
| from_phone | character varying | NO |  |
| message | text | NO |  |
| status | character varying | YES | 'sent'::character varying |
| twilio_sid | character varying | YES |  |
| error_message | text | YES |  |
| created_at | timestamp with time zone | NO | now() |
| consumer_report_id | uuid | YES |  |
| direction | character varying | YES | 'outbound'::character varying |
| recipient_type | character varying | YES |  |
| message_body | text | YES |  |
| segments | integer | YES | 1 |
| price_cents | integer | YES |  |

### subscription_plans

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | integer | NO | nextval('subscription_plans_id_seq'::regclass) |
| name | character varying | NO |  |
| slug | character varying | NO |  |
| price_monthly | numeric | YES |  |
| price_annual | numeric | YES |  |
| features | jsonb | YES |  |
| is_active | boolean | YES | true |
| display_order | integer | YES | 0 |
| created_at | timestamp without time zone | YES | now() |
| updated_at | timestamp without time zone | YES | now() |

### usage_tracking

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | bigint | NO | nextval('usage_tracking_id_seq'::regclass) |
| account_id | uuid | NO |  |
| user_id | uuid | YES |  |
| event_type | character varying | NO |  |
| report_id | uuid | YES |  |
| billable_units | integer | YES | 1 |
| cost_cents | integer | YES | 0 |
| ip_address | inet | YES |  |
| user_agent | text | YES |  |
| request_id | character varying | YES |  |
| created_at | timestamp without time zone | YES | now() |

### users

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| email | character varying | NO |  |
| password_hash | character varying | YES |  |
| role | character varying | YES | 'member'::character varying |
| email_verified | boolean | YES | false |
| is_active | boolean | YES | true |
| created_at | timestamp without time zone | YES | now() |
| updated_at | timestamp without time zone | YES | now() |
| first_name | character varying | YES |  |
| last_name | character varying | YES |  |
| company_name | character varying | YES |  |
| phone | character varying | YES |  |
| avatar_url | character varying | YES |  |
| password_changed_at | timestamp without time zone | YES |  |
| onboarding_completed_at | timestamp without time zone | YES |  |
| onboarding_step | character varying | YES | 'welcome'::character varying |
| onboarding_data | jsonb | YES | '{}'::jsonb |
| is_platform_admin | boolean | NO | false |
| agent_code | character varying | YES |  |
| landing_page_headline | character varying | YES | 'Get Your Free Home Value Report'::character varying |
| landing_page_subheadline | text | YES | 'Find out what your home is worth in today''s market.'::text |
| landing_page_theme_color | character varying | YES | '#8B5CF6'::character varying |
| landing_page_enabled | boolean | YES | true |
| landing_page_visits | integer | YES | 0 |
| photo_url | text | YES |  |
| license_number | character varying | YES |  |
| job_title | character varying | YES |  |
| website | character varying | YES |  |

### verification_log

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| document_id | uuid | YES |  |
| verified_at | timestamp with time zone | YES | now() |
| verification_method | character varying | NO |  |
| result | character varying | NO |  |
| ip_hash | character varying | YES |  |
| user_agent_hash | character varying | YES |  |
| country_code | character varying | YES |  |
| error_message | text | YES |  |

### webhook_deliveries

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| webhook_id | uuid | NO |  |
| event | text | NO |  |
| payload | jsonb | NO |  |
| response_status | integer | YES |  |
| response_ms | integer | YES |  |
| error | text | YES |  |
| created_at | timestamp without time zone | YES | now() |

### webhooks

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NO | gen_random_uuid() |
| account_id | uuid | NO |  |
| url | text | NO |  |
| events | ARRAY | NO |  |
| secret | text | NO |  |
| is_active | boolean | YES | true |
| created_at | timestamp without time zone | YES | now() |

## Common Gotchas — READ BEFORE WRITING SQL

| What You Might Guess | What Actually Exists | Notes |
|---------------------|---------------------|-------|
| `report_generations.city` | DOES NOT EXIST | Use: COALESCE(input_params->>'city', cities[1], 'Unknown') |
| `report_generations.schedule_id` | DOES NOT EXIST | Link through: schedule_runs.report_run_id = report_generations.id |
| `report_generations.last_login_at` | DOES NOT EXIST | Not tracked |
| `signup_tokens.used_at` | DOES NOT EXIST | Use: signup_tokens.used (boolean) |
| `accounts.default_city` | DOES NOT EXIST | Never migrated |
| `accounts.last_login_at` | DOES NOT EXIST | Not tracked on accounts/users |
| `users.last_login_at` | DOES NOT EXIST | Not tracked — DO NOT add to admin queries |
| `sms_logs.error` | DOES NOT EXIST | Use: sms_logs.error_message |
| `affiliate_branding.branding_override` | EXISTS (boolean, default false) | Added in migration 0049 |
| `accounts.parent_account_id` | EXISTS (uuid, nullable) | Added in migration 0048 — links rep to parent title company |
| `accounts.sponsor_account_id` | EXISTS (uuid, nullable) | Sponsorship link, separate from parent_account_id |
| `accounts.account_type` | EXISTS (text, default 'REGULAR') | Values: REGULAR, INDUSTRY_AFFILIATE, SPONSORED |
| `accounts.market_reports_limit_override` | EXISTS (integer, nullable) | Added in migration 0051 — per-product override |
| `accounts.schedules_limit_override` | EXISTS (integer, nullable) | Added in migration 0051 |
| `accounts.property_reports_limit_override` | EXISTS (integer, nullable) | Added in migration 0051 |
| `accounts.monthly_report_limit_override` | EXISTS (integer, nullable) | Legacy single-override field — prefer per-product overrides |
| `plans.market_reports_limit` | EXISTS (integer, nullable) | Added in migration 0051 |
| `plans.schedules_limit` | EXISTS (integer, nullable) | Added in migration 0051 |
| `plans.property_reports_per_month` | EXISTS (integer, nullable) | Added in migration 0034 |
| `schedules.cities (plural)` | DOES NOT EXIST | Schedules use single `city` column (text). Use `zip_codes` (array) for multi-zip |
| `schedules.user_id` | DOES NOT EXIST | Schedules belong to account_id only |
| `report_generations.created_at` | DOES NOT EXIST | Use: report_generations.generated_at |
| `users.name` | DOES NOT EXIST | Use: first_name + last_name (or COALESCE) |
| `users.full_name` | DOES NOT EXIST | Use: TRIM(CONCAT(first_name, ' ', last_name)) |
| `users.photo_url vs avatar_url` | BOTH EXIST | Prefer COALESCE(photo_url, avatar_url) — photo_url is newer |
| `leads.consumer_report_id` | EXISTS (uuid, nullable) | Links lead to consumer_reports row when via QR/landing page |
| `consumer_reports.delivery_method` | EXISTS (varchar, default 'sms') | Values: 'sms' or 'email' |
| `email_log.error_message` | DOES NOT EXIST | Use: email_log.error (text) |
| `email_log.recipient` | DOES NOT EXIST | Use: email_log.to_emails (array) |
| `schedule_runs.account_id` | DOES NOT EXIST | Join via schedules.account_id |
| `property_reports.theme_id` | DOES NOT EXIST | Use: property_reports.theme (integer, default 1) |
