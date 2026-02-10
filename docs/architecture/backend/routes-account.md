# Account API

> Account details, branding, multi-account switching, and plan/usage info.
> File: `apps/api/src/api/routes/account.py`

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | /v1/account | Get account with branding | Required |
| PATCH | /v1/account/branding | Update branding (logos + colors) | Required |
| GET | /v1/account/accounts | List user's accounts | Required |
| POST | /v1/account/use | Switch account context | Required |
| GET | /v1/account/plan-usage | Plan + usage + Stripe billing | Required |

## Key Functions

### GET /v1/account
- Returns `AccountOut` with branding fields
- Contact info (rep_photo_url, contact_line1, contact_line2) derived from user profile
- `build_contact_lines()` formats: "Name * Title" and "Phone * Email"
- Includes plan_slug, billing_status, stripe_customer_id

### PATCH /v1/account/branding
- Updates logos and colors only: logo_url, footer_logo_url, email_logo_url, email_footer_logo_url, primary_color, secondary_color
- Contact info is NOT updated here (use `/v1/users/me` instead)
- Colors must match hex pattern `#xxx` or `#xxxxxx`
- Returns updated AccountOut

### GET /v1/account/accounts
- Lists all accounts the current user belongs to (via `account_users` M2M)
- Uses `services/accounts.py: get_user_accounts()`
- Returns `{accounts: [...], count}`

### POST /v1/account/use
- **Input:** `{account_id: "<uuid>"}`
- Verifies user has access to target account via `verify_user_account_access()`
- Sets `mr_account_id` cookie (30 day TTL)
- Returns `{ok, current_account_id, account_type, plan_slug}`

### GET /v1/account/plan-usage
- **Known slow endpoint** -- makes Stripe API calls for each plan with a stripe_price_id
- Returns comprehensive plan + usage data:
  - `account`: basic info + billing_status
  - `plan`: resolved plan from `resolve_plan_for_account()`
  - `usage`: monthly usage from `get_monthly_usage()`
  - `decision`: limit evaluation result (ALLOW, ALLOW_WITH_WARNING, BLOCK)
  - `info`: limit message and details
  - `stripe_billing`: amount, currency, interval, nickname (null for free plans)
- Uses `get_plan_catalog()` which calls `stripe.Price.retrieve()` for each plan

## Dependencies
- `services/accounts.py`: `get_user_accounts()`, `verify_user_account_access()`, `get_account_info()`
- `services/usage.py`: `get_monthly_usage()`, `resolve_plan_for_account()`, `evaluate_report_limit()`
- `services/plans.py`: `get_plan_catalog()` (Stripe API calls)

## Related Files
- Frontend: `/app/settings` (branding), `/app/billing` (plan/usage)
- Frontend: `AccountSwitcher` component uses `/v1/account/accounts` and `/v1/account/use`
