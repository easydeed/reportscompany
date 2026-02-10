# Backend Routes

> `apps/api/src/api/routes/` -- All 26 API route modules

---

## Route Map

| File | Prefix | Endpoints | Purpose |
|------|--------|-----------|---------|
| `health.py` | `/health` | `GET /health` | Liveness check |
| `auth.py` | `/v1/auth` | login, signup, password reset, token refresh, verify-email, accept-invite | Authentication |
| `reports.py` | `/v1` | `POST /reports`, `GET /reports`, `GET /reports/{id}` | Report CRUD + limit enforcement |
| `report_data.py` | `/v1` | `GET /reports/{id}/data` | Raw report data (public for PDF gen) |
| `account.py` | `/v1/account` | plan-usage, settings, account info | Account management |
| `usage.py` | `/v1` | Usage tracking endpoints | API/feature usage |
| `schedules.py` | `/v1` | Schedule CRUD | Automated report delivery |
| `billing.py` | `/v1/billing` | Checkout, customer portal | Stripe subscription management |
| `stripe_webhook.py` | `/v1/webhooks/stripe` | Stripe webhook handler | Process subscription events |
| `webhooks.py` | `/v1/webhooks` | Generic webhook endpoints | Webhook management |
| `apikeys.py` | `/v1` | API key CRUD | API key management |
| `me.py` | `/v1/me` | User profile, leads, lead-page | Current user endpoints |
| `users.py` | `/v1` | User management within accounts | Multi-user account management |
| `affiliates.py` | `/v1/affiliate` | overview, invite-agent, branding, accounts CRUD | Affiliate program |
| `contacts.py` | `/v1` | Contact CRUD, import | Contact management |
| `contact_groups.py` | `/v1` | Contact group CRUD | Contact groups |
| `leads.py` | `/v1` | Lead CRUD, CSV export | Lead management |
| `lead_pages.py` | `/v1` | Lead page management | Lead capture pages |
| `property.py` | `/v1` | Property search, preview, comps, stats, reports | Property reports |
| `mobile_reports.py` | `/v1/r` | Mobile report viewer | Mobile-optimized reports |
| `admin.py` | `/v1/admin` | Platform admin functions | Admin dashboard |
| `admin_metrics.py` | `/v1/admin` | Admin analytics/reporting | Admin metrics |
| `branding_tools.py` | `/v1` | Branding asset endpoints | White-label tools |
| `upload.py` | `/v1` | File upload handler | Asset uploads |
| `onboarding.py` | `/v1` | Onboarding workflow | User onboarding |
| `devfiles.py` | `/dev-files` | Dev/test utilities | Development only |
| `dev_stripe_prices.py` | `/v1/dev` | Dev Stripe config | Development only |
| `unsubscribe.py` | `/v1/email` | Email unsubscribe | Email preferences |

---

## Key Route Details

### reports.py

**`require_account_id(request)`** (line 33-41):
Dependency that extracts `account_id` from `request.state`. Used by most protected routes across the app.

**`POST /reports`** (line 45-119):
- Sets RLS context
- Calls `evaluate_report_limit()` for plan enforcement (returns ALLOW / ALLOW_WITH_WARNING / BLOCK)
- Inserts into `report_generations`
- Enqueues Celery task via `worker_client`
- On enqueue failure: updates report status to 'failed', opens a second `db_conn()`

**`GET /reports`** (line 142-183):
- Dynamic WHERE clause with optional filters (type, status, date range)
- Always filters by `account_id` for data isolation
- Pagination via LIMIT/OFFSET

### account.py

**`GET /v1/account/plan-usage`**:
- Calls `resolve_plan_for_account()`, `get_monthly_usage()`, then `evaluate_report_limit()` which re-calls both internally
- Also calls `get_plan_catalog()` which triggers live Stripe API calls
- **Known issues:** [C3] Stripe calls, [H1] duplicate sub-function calls

### affiliates.py

**`GET /v1/affiliate/overview`** (line 30-74):
- Calls `verify_affiliate_account()` (1 query)
- Calls `get_affiliate_overview()` which internally calls `get_sponsored_accounts()` (1 + N queries)
- Calls `get_sponsored_accounts()` again (1 + N queries -- duplicate)
- Queries account info (1 query)
- **Known issues:** [C4] double call, [C5] N+1

**`POST /v1/affiliate/invite-agent`** (line 85-225):
- Creates account, user, account_users, signup_token
- Includes `CREATE TABLE IF NOT EXISTS` in request handler [L3]
- Sends invite email via background task

**Duplicate routes:** Two `GET /branding` and two `POST /branding` definitions exist (Phase 30 at ~line 251 and Phase W2 at ~line 502). See [M5].

**Other endpoints:** `GET/POST /accounts/{id}/deactivate`, `/reactivate`, `/unsponsor`, `GET /accounts/{id}` (detail with 4 separate queries [M4]).
