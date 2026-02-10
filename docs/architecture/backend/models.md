# Database Models

> PostgreSQL tables grouped by domain. All tables use UUID primary keys and `created_at`/`updated_at` timestamps.

## Auth & Multi-tenancy

### accounts
Core tenant table. Every data row in the system belongs to an account.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | Default gen_random_uuid() |
| name | text | Display name |
| slug | text UNIQUE | URL-safe identifier |
| account_type | text | `REGULAR` or `INDUSTRY_AFFILIATE` |
| plan_slug | text FK | References plans.plan_slug |
| monthly_report_limit_override | int | Overrides plan default |
| api_rate_limit | int | Requests/minute (default 60) |
| sponsor_account_id | uuid FK | References accounts.id (for sponsored accounts) |
| stripe_customer_id | text | Stripe customer ID |
| stripe_subscription_id | text | Stripe subscription ID |
| billing_status | text | Stripe subscription status |
| subscription_status | text | Legacy status field |
| logo_url | text | Header logo for PDFs |
| footer_logo_url | text | Footer logo for PDFs |
| email_logo_url | text | Header logo for emails |
| email_footer_logo_url | text | Footer logo for emails |
| primary_color | text | Hex color code |
| secondary_color | text | Hex color code |
| rep_photo_url | text | Legacy (now derived from user profile) |
| contact_line1 | text | Legacy (now derived from user profile) |
| contact_line2 | text | Legacy (now derived from user profile) |
| website_url | text | Account website |
| sms_credits | int | Remaining SMS credits |

**Read by:** account.py, billing.py, admin.py, affiliates.py, usage.py, leads.py
**Written by:** auth.py (register), billing.py (stripe_customer_id), stripe_webhook.py (plan_slug), admin.py

### users
Individual user accounts within a tenant.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | Primary account association |
| email | text UNIQUE | Login identifier |
| password_hash | text | bcrypt hash |
| first_name | text | |
| last_name | text | |
| avatar_url | text | Profile photo |
| phone | text | |
| job_title | text | |
| company_name | text | |
| website | text | |
| license_number | text | Real estate license |
| role | text | OWNER, MEMBER, ADMIN, AFFILIATE |
| is_platform_admin | boolean | System-wide admin flag |
| is_active | boolean | Soft delete |
| email_verified | boolean | Email verification status |
| password_changed_at | timestamp | |
| agent_code | text UNIQUE | 6-char code for CMA pages |
| landing_page_enabled | boolean | |
| landing_page_headline | text | |
| landing_page_subheadline | text | |
| landing_page_theme_color | text | |
| landing_page_visits | int | |

**Read by:** authn.py middleware, account.py, admin.py, me.py, property.py
**Written by:** auth.py (register, password reset), users.py, me.py

### account_users
M2M join table linking users to accounts with roles.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | |
| user_id | uuid FK | |
| role | text | OWNER, MEMBER, AFFILIATE |

**Read by:** auth.py (login priority), accounts.py service
**Written by:** auth.py (register), admin.py (invite)

### jwt_blacklist
Revoked JWT tokens (for logout).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| token_hash | text UNIQUE | SHA-256 of the JWT |
| user_id | uuid FK | |
| expires_at | timestamp | Auto-cleanup threshold |

**Read by:** authn.py middleware (every authenticated request)
**Written by:** auth.py (logout)

### password_reset_tokens

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK | |
| token | text | URL-safe random token |
| expires_at | timestamp | 1 hour TTL |
| used_at | timestamp | Null until consumed |

### email_verification_tokens

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK | |
| email | text | |
| token | text | URL-safe random token |
| expires_at | timestamp | 24 hour TTL |
| verified_at | timestamp | |

### login_attempts
Brute-force protection tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| email | text | |
| success | boolean | |
| ip_address | text | |
| attempted_at | timestamp | |

## Billing

### plans
Plan catalog with limits and Stripe mapping.

| Column | Type | Notes |
|--------|------|-------|
| plan_slug | text PK | free, pro, team, affiliate, sponsored_free |
| plan_name | text | Display name |
| stripe_price_id | text | Stripe Price ID (nullable for free) |
| description | text | |
| is_active | boolean | |
| reports_per_month | int | Market report limit |
| property_reports_per_month | int | Property report limit |
| sms_per_month | int | SMS credit limit |
| overage_price_cents | int | Per-report overage cost |

**Read by:** usage.py, plans.py, plan_lookup.py, billing.py
**Written by:** Migration seed data only

## Reports

### report_generations
Market report generation records.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | RLS-filtered |
| report_type | text | market_snapshot, new_listings, etc. |
| input_params | jsonb | City, zips, polygon, filters, lookback_days |
| status | text | pending, processing, completed, failed |
| html_url | text | Generated HTML URL |
| json_url | text | Generated JSON URL |
| csv_url | text | Generated CSV URL |
| pdf_url | text | Generated PDF URL |
| processing_time_ms | int | |
| error_message | text | |
| generated_at | timestamp | |

**input_params JSONB structure:**
```json
{
  "city": "Los Angeles",
  "zips": ["90001", "90002"],
  "polygon": null,
  "lookback_days": 30,
  "filters": {"minbeds": 2, "minbaths": 2},
  "additional_params": {}
}
```

### schedules
Automated report delivery configuration.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | RLS-filtered |
| name | text | |
| report_type | text | |
| city | text | |
| zip_codes | text[] | PostgreSQL array |
| lookback_days | int | |
| cadence | text | weekly or monthly |
| weekly_dow | int | 0=Sun, 6=Sat |
| monthly_dom | int | 1-28 |
| send_hour | int | 0-23 |
| send_minute | int | 0-59 |
| timezone | text | IANA timezone |
| recipients | text[] | JSON-encoded recipient objects |
| include_attachment | boolean | |
| active | boolean | |
| filters | jsonb | Smart preset filters |
| last_run_at | timestamp | |
| next_run_at | timestamp | Null = needs recompute |
| consecutive_failures | int | Auto-pauses at 3 |

**recipients array format:** Each element is a JSON string:
- `{"type":"contact","id":"<uuid>"}`
- `{"type":"sponsored_agent","id":"<uuid>"}`
- `{"type":"group","id":"<uuid>"}`
- `{"type":"manual_email","email":"..."}`

### schedule_runs
Execution history for schedules.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| schedule_id | uuid FK | CASCADE delete |
| report_run_id | uuid FK | References report_generations |
| status | text | |
| error | text | |
| started_at | timestamp | |
| finished_at | timestamp | |

## Property

### property_reports
Property CMA reports (seller/buyer).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | RLS-filtered |
| user_id | uuid FK | |
| report_type | text | seller or buyer |
| theme | int | 1-5 |
| accent_color | text | Hex color |
| language | text | en or es |
| property_address | text | |
| property_city | text | |
| property_state | text | |
| property_zip | text | |
| property_county | text | |
| apn | text | Assessor Parcel Number |
| owner_name | text | |
| legal_description | text | |
| property_type | text | |
| sitex_data | jsonb | Full SiteX property data |
| comparables | jsonb | Selected comparable properties |
| selected_pages | jsonb | Pages to include in PDF |
| pdf_url | text | Generated PDF URL |
| status | text | draft, processing, complete, failed |
| short_code | text UNIQUE | 8-char public URL code |
| qr_code_url | text | QR code image URL |
| error_message | text | |
| view_count | int | Landing page views |
| unique_visitors | int | |
| last_viewed_at | timestamp | |
| is_active | boolean | Landing page active |
| expires_at | timestamp | Landing page expiry |
| max_leads | int | Lead cap |
| access_code | text | Landing page password |

### leads
Captured leads from property report landing pages.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | RLS-filtered |
| property_report_id | uuid FK | |
| name | text | |
| email | text | |
| phone | text | |
| message | text | |
| source | text | qr_scan or direct_link |
| consent_given | boolean | |
| status | text | new, contacted, converted |
| notes | text | Agent notes |
| ip_address | text | |
| user_agent | text | |
| sms_sent_at | timestamp | |
| email_sent_at | timestamp | |

### blocked_ips
IP block list for anti-spam.

| Column | Type | Notes |
|--------|------|-------|
| ip_address | text PK | |
| reason | text | |
| expires_at | timestamp | Null = permanent |

### lead_rate_limits
Per-IP submission tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| ip_address | text | |
| property_report_id | uuid FK | |
| submitted_at | timestamp | |

## Consumer Reports

### consumer_reports
SMS-delivered home value reports.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| agent_id | uuid FK | References users.id |
| agent_code | text | 6-char agent code |
| consumer_phone | text | |
| property_address | text | |
| property_city | text | |
| property_state | text | |
| property_zip | text | |
| property_data | jsonb | Full property details |
| comparables | jsonb | Comparable sales |
| value_estimate | jsonb | `{low, mid, high, confidence}` |
| market_stats | jsonb | `{median_price, avg_price_per_sqft, ...}` |
| pdf_url | text | |
| status | text | pending, ready, failed |
| consent_given | boolean | |
| consent_timestamp | timestamp | |
| ip_address | text | |
| user_agent | text | |
| device_type | text | mobile, tablet, desktop |
| view_count | int | |
| first_viewed_at | timestamp | |
| last_viewed_at | timestamp | |
| agent_contact_clicked | boolean | |
| agent_contact_type | text | |
| tabs_viewed | jsonb | Array of viewed tab names |
| time_on_page | int | Seconds |
| pdf_requested_count | int | |

### report_analytics
Event tracking for consumer reports.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| report_id | uuid FK | References consumer_reports.id |
| event_type | text | view, tab_change, agent_click, share, pdf_request |
| event_data | jsonb | |
| ip_address | text | |
| user_agent | text | |
| device_type | text | |
| session_id | text | |

## Communications

### email_log
Sent email tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | |
| schedule_id | uuid FK | |
| recipient | text | |
| subject | text | |
| status | text | |
| provider_id | text | SendGrid/Resend message ID |
| error | text | |

### email_suppressions
Unsubscribed email addresses.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| email | text | |
| account_id | uuid FK | |
| reason | text | |

### sms_logs
SMS delivery tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | |
| to_phone | text | |
| message_sid | text | Twilio SID |
| status | text | |

## Contacts

### contacts
Client contact records.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | RLS-filtered |
| name | text | |
| email | text | |
| phone | text | |
| type | text | client, list, agent, group |
| notes | text | |

### contact_groups

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | |
| name | text | |
| description | text | |

### contact_group_members

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| group_id | uuid FK | |
| account_id | uuid FK | |
| member_type | text | contact or sponsored_agent |
| member_id | uuid | References contacts.id or accounts.id |
| UNIQUE | | (group_id, member_type, member_id) |

## API

### api_keys

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | |
| key_hash | text | SHA-256 of the API key |
| name | text | |
| is_active | boolean | |

### webhooks

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | RLS-filtered |
| url | text | |
| events | text[] | |
| is_active | boolean | |

### webhook_deliveries

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| webhook_id | uuid FK | |
| event | text | |
| payload | jsonb | |
| status | int | HTTP status code |
| response_body | text | |

### usage_tracking

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | |
| event_type | text | |
| metadata | jsonb | |

## Branding

### affiliate_branding
White-label branding for affiliate accounts.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| account_id | uuid FK | |
| brand_display_name | text | |
| logo_url | text | |
| rep_photo_url | text | |

## Misc

### signup_tokens
Invite tokens for sponsored agent onboarding.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK | |
| account_id | uuid FK | |
| token | text | |
| expires_at | timestamp | 7 days |
| used_at | timestamp | |

### cleanup_jobs
Background cleanup task tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| job_type | text | |
| last_run_at | timestamp | |
| status | text | |
