# Database Schema

> Complete schema reference for TrendyReports (PostgreSQL)

---

## Group 1: Auth & Multi-tenancy

### accounts

Primary table for organizations/teams.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| name | TEXT | NOT NULL |
| slug | TEXT | UNIQUE, NOT NULL |
| account_type | TEXT | NOT NULL |
| plan_slug | TEXT | FK -> plans(slug) |
| sponsor_account_id | UUID | FK -> accounts(id), self-referential |
| stripe_customer_id | TEXT | |
| billing_status | TEXT | |
| is_active | BOOLEAN | DEFAULT true |
| monthly_report_limit_override | INTEGER | |
| sms_credits | INTEGER | DEFAULT 0 |
| branding | JSONB | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### users

Individual user accounts.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id) |
| email | TEXT | UNIQUE, NOT NULL |
| password_hash | TEXT | |
| role | TEXT | NOT NULL |
| is_platform_admin | BOOLEAN | DEFAULT false |
| first_name | TEXT | |
| last_name | TEXT | |
| agent_code | TEXT | UNIQUE |
| photo_url | TEXT | |
| license_number | TEXT | |
| landing_page_headline | TEXT | |
| landing_page_subheadline | TEXT | |
| landing_page_cta | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### account_users

Join table linking users to accounts with roles.

| Column | Type | Constraints |
|--------|------|-------------|
| account_id | UUID | FK -> accounts(id), part of composite PK |
| user_id | UUID | FK -> users(id), part of composite PK |
| role | TEXT | NOT NULL, one of: OWNER, MEMBER, AFFILIATE, ADMIN |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Primary Key:** (account_id, user_id)

### jwt_blacklist

Revoked JWT tokens.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| token_hash | TEXT | UNIQUE, NOT NULL |
| user_id | UUID | FK -> users(id) |
| expires_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### password_reset_tokens

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK -> users(id), NOT NULL |
| token | TEXT | UNIQUE, NOT NULL |
| expires_at | TIMESTAMPTZ | NOT NULL |
| used_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### email_verification_tokens

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK -> users(id), NOT NULL |
| email | TEXT | NOT NULL |
| token | TEXT | UNIQUE, NOT NULL |
| expires_at | TIMESTAMPTZ | NOT NULL |
| verified_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### login_attempts

Tracks login attempts for security monitoring.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| email | TEXT | NOT NULL |
| success | BOOLEAN | NOT NULL |
| ip_address | INET | |
| attempted_at | TIMESTAMPTZ | DEFAULT now() |

### signup_tokens

Tokens for invite-based signups.

| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PK |
| token | TEXT | UNIQUE, NOT NULL |
| user_id | UUID | FK -> users(id) |
| account_id | UUID | FK -> accounts(id) |
| used | BOOLEAN | DEFAULT false |
| expires_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## Group 2: Billing

### plans

Subscription plan definitions.

| Column | Type | Constraints |
|--------|------|-------------|
| slug | TEXT | PK |
| name | TEXT | NOT NULL |
| monthly_report_limit | INTEGER | |
| allow_overage | BOOLEAN | DEFAULT false |
| overage_price_cents | INTEGER | |
| property_reports_per_month | INTEGER | |
| sms_credits_per_month | INTEGER | |
| stripe_price_id | TEXT | |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### billing_events

Audit log for all billing-related events.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| type | TEXT | NOT NULL |
| payload | JSONB | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## Group 3: Market Reports

### report_generations

Market report generation records.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| user_id | UUID | FK -> users(id) |
| report_type | TEXT | NOT NULL |
| input_params | JSONB | |
| cities | TEXT[] | |
| status | TEXT | NOT NULL (pending, processing, completed, failed) |
| html_url | TEXT | |
| json_url | TEXT | |
| csv_url | TEXT | |
| pdf_url | TEXT | |
| error_message | TEXT | |
| processing_time_ms | INTEGER | |
| billable | BOOLEAN | DEFAULT true |
| generated_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### schedules

Recurring report schedule definitions.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| report_type | TEXT | NOT NULL |
| city | TEXT | |
| zip_codes | TEXT[] | |
| cadence | TEXT | NOT NULL (daily, weekly, monthly) |
| weekly_dow | INTEGER | Day of week (0-6) |
| monthly_dom | INTEGER | Day of month (1-31) |
| send_hour | INTEGER | NOT NULL (0-23) |
| send_minute | INTEGER | DEFAULT 0 (0-59) |
| recipients | TEXT[] | Email addresses |
| filters | JSONB | |
| active | BOOLEAN | DEFAULT true |
| consecutive_failures | INTEGER | DEFAULT 0 |
| last_run_at | TIMESTAMPTZ | |
| next_run_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### schedule_runs

Audit log for each schedule execution.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| schedule_id | UUID | FK -> schedules(id), NOT NULL |
| report_run_id | UUID | FK -> report_generations(id) |
| status | TEXT | NOT NULL (started, completed, failed) |
| error | TEXT | |
| started_at | TIMESTAMPTZ | DEFAULT now() |
| finished_at | TIMESTAMPTZ | |

---

## Group 4: Property Reports

### property_reports

CMA / property-level report records.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| user_id | UUID | FK -> users(id) |
| report_type | TEXT | |
| theme | INTEGER | 1-5 |
| property_address | TEXT | NOT NULL |
| property_city | TEXT | |
| property_state | TEXT | |
| property_zip | TEXT | |
| apn | TEXT | |
| sitex_data | JSONB | Raw SiteX property data |
| comparables | JSONB | Selected comparable properties |
| pdf_url | TEXT | |
| status | TEXT | NOT NULL (pending, processing, completed, failed) |
| short_code | TEXT | UNIQUE, for public URL |
| qr_code_url | TEXT | |
| view_count | INTEGER | DEFAULT 0 |
| unique_visitors | INTEGER | DEFAULT 0 |
| is_active | BOOLEAN | DEFAULT true |
| expires_at | TIMESTAMPTZ | |
| selected_pages | JSONB | User-selected pages to include |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### leads

Lead captures from property report landing pages.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| property_report_id | UUID | FK -> property_reports(id) |
| name | TEXT | |
| email | TEXT | |
| phone | TEXT | |
| message | TEXT | |
| source | TEXT | |
| consent_given | BOOLEAN | DEFAULT false |
| status | TEXT | |
| sms_sent_at | TIMESTAMPTZ | |
| email_sent_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### blocked_ips

IP addresses blocked from lead submission.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| ip_address | INET | NOT NULL |
| reason | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### lead_rate_limits

Rate limiting for lead submissions.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| ip_address | INET | |
| property_report_id | UUID | FK -> property_reports(id) |
| attempt_count | INTEGER | DEFAULT 1 |
| window_start | TIMESTAMPTZ | DEFAULT now() |

### property_report_stats

Aggregate statistics for property reports.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| property_report_id | UUID | FK -> property_reports(id) |
| total_views | INTEGER | DEFAULT 0 |
| unique_views | INTEGER | DEFAULT 0 |
| total_leads | INTEGER | DEFAULT 0 |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### property_report_stats_daily

Daily breakdown of property report analytics.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| property_report_id | UUID | FK -> property_reports(id) |
| date | DATE | NOT NULL |
| views | INTEGER | DEFAULT 0 |
| unique_views | INTEGER | DEFAULT 0 |
| leads | INTEGER | DEFAULT 0 |

---

## Group 5: Consumer Reports

### consumer_reports

Consumer-facing CMA reports.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| agent_id | UUID | FK -> users(id) |
| agent_code | TEXT | |
| consumer_phone | TEXT | |
| consumer_email | TEXT | |
| consent_given | BOOLEAN | DEFAULT false |
| property_address | TEXT | NOT NULL |
| property_city | TEXT | |
| property_state | TEXT | |
| property_zip | TEXT | |
| property_data | JSONB | |
| comparables | JSONB | |
| market_stats | JSONB | |
| value_estimate | JSONB | |
| status | TEXT | NOT NULL (pending, processing, completed, failed) |
| pdf_url | TEXT | |
| view_count | INTEGER | DEFAULT 0 |
| unique_views | INTEGER | DEFAULT 0 |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### report_analytics

Event-level analytics for consumer reports.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| report_id | UUID | FK -> consumer_reports(id) |
| event_type | TEXT | NOT NULL |
| event_data | JSONB | |
| session_id | TEXT | |
| device_type | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## Group 6: Communications

### email_log

Log of all emails sent from the system.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id) |
| schedule_id | UUID | |
| report_id | UUID | |
| provider | TEXT | |
| to_emails | TEXT[] | |
| subject | TEXT | |
| response_code | INTEGER | |
| error | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### email_suppressions

Email addresses that should not receive emails.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id) |
| email | TEXT | NOT NULL |
| reason | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Unique constraint:** (account_id, email)

### sms_logs

Log of all SMS messages sent.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id) |
| lead_id | UUID | FK -> leads(id) |
| to_phone | TEXT | NOT NULL |
| from_phone | TEXT | |
| message | TEXT | |
| status | TEXT | |
| twilio_sid | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## Group 7: Contacts

### contacts

Contact records for report recipients and CRM.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| name | TEXT | |
| email | TEXT | |
| type | TEXT | |
| notes | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### contact_groups

Groups for organizing contacts.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| name | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### contact_group_members

Join table for contacts in groups.

| Column | Type | Constraints |
|--------|------|-------------|
| contact_group_id | UUID | FK -> contact_groups(id) |
| contact_id | UUID | FK -> contacts(id) |

**Primary Key:** (contact_group_id, contact_id)

---

## Group 8: API & Webhooks

### api_keys

API keys for programmatic access.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| key_prefix | TEXT | NOT NULL |
| key_hash | TEXT | UNIQUE, NOT NULL |
| name | TEXT | |
| scopes | TEXT[] | |
| rate_limit | INTEGER | |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### webhooks

Webhook endpoint registrations.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| url | TEXT | NOT NULL |
| events | TEXT[] | NOT NULL |
| secret | TEXT | NOT NULL |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

### webhook_deliveries

Log of webhook delivery attempts.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| account_id | UUID | FK -> accounts(id) |
| webhook_id | UUID | FK -> webhooks(id), NOT NULL |
| event | TEXT | NOT NULL |
| payload | JSONB | |
| response_status | INTEGER | |
| response_ms | INTEGER | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### usage_tracking

Tracks billable usage events.

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PK |
| account_id | UUID | FK -> accounts(id), NOT NULL |
| user_id | UUID | FK -> users(id) |
| event_type | TEXT | NOT NULL |
| billable_units | INTEGER | DEFAULT 1 |
| cost_cents | INTEGER | DEFAULT 0 |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## Group 9: Branding

### affiliate_branding

Custom branding for affiliate accounts.

| Column | Type | Constraints |
|--------|------|-------------|
| account_id | UUID | PK, FK -> accounts(id) |
| brand_display_name | TEXT | |
| logo_url | TEXT | |
| primary_color | TEXT | |
| accent_color | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

---

## Database Functions

| Function | Description |
|----------|-------------|
| `generate_short_code()` | Generates a unique short code for property report public URLs |
| `generate_agent_code()` | Generates a unique agent code for consumer CMA URLs |
| `update_updated_at()` | Trigger function to auto-update `updated_at` on row modification |

## Triggers

- **updated_at triggers:** Applied to `accounts`, `users`, `report_generations`, `schedules`, `property_reports`, `consumer_reports`, `contacts`, `webhooks`, `affiliate_branding` to auto-set `updated_at = now()` on UPDATE.
- **short_code generation:** Auto-generates `short_code` on INSERT to `property_reports` if not provided.
- **agent_code generation:** Auto-generates `agent_code` on INSERT to `users` if not provided.

## Views

| View | Description |
|------|-------------|
| `admin_daily_metrics` | Aggregated daily metrics for platform admin dashboard (signups, reports, revenue) |
| `admin_agent_leaderboard` | Ranked agent performance by report count, leads, and conversions |
