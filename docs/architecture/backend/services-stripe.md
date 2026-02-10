# Stripe Billing Services

> Plan catalog, plan lookup, billing state sync, and Stripe API integration.
> Files: `apps/api/src/api/services/plans.py`, `plan_lookup.py`, `billing_state.py`, `config/billing.py`

## Plan Catalog Service

> File: `apps/api/src/api/services/plans.py`

### get_plan_catalog(cur) -> Dict[str, PlanCatalog]
- Reads all active plans from `plans` table
- For each plan with a `stripe_price_id`: calls `stripe.Price.retrieve()` to get live pricing
- Returns dict keyed by plan_slug
- Resilient: if Stripe API fails, returns plan info without pricing data

### PlanCatalog Model
```
plan_slug: str         # "free", "pro", "team", etc.
plan_name: str         # Display name
stripe_price_id: str   # Stripe Price ID (nullable)
description: str
is_active: bool
stripe_billing: StripeBilling  # Enriched from Stripe API (nullable)
```

### StripeBilling Model
```
amount: int            # Price in cents (e.g., 2900 = $29.00)
currency: str          # "usd"
interval: str          # "month" or "year"
interval_count: int    # Usually 1
nickname: str          # "Pro -- $29/mo"
```

**Known performance issue:** `get_plan_catalog()` makes a Stripe API call for each plan. This is called by `/v1/account/plan-usage` on every billing page load.

## Plan Lookup Service

> File: `apps/api/src/api/services/plan_lookup.py`

### get_plan_by_slug(cur, plan_slug) -> dict | None
- Simple DB lookup: `SELECT * FROM plans WHERE plan_slug = %s AND is_active = TRUE`
- Used by billing checkout to validate plan exists

### get_plan_slug_for_stripe_price(cur, price_id) -> str | None
- Reverse lookup: `SELECT plan_slug FROM plans WHERE stripe_price_id = %s`
- Used by webhook handler to map Stripe price_id back to plan_slug

## Billing State Service

> File: `apps/api/src/api/services/billing_state.py`

### update_account_billing_state(cur, account_id, subscription)
- Updates `accounts.stripe_subscription_id` and `accounts.billing_status`
- If subscription provided: sets subscription_id and status from Stripe object
- If subscription is None: clears subscription_id, sets status to "canceled"
- Returns number of rows updated (0 = account not found)

Called by:
- `stripe_webhook.py` on subscription.created/updated (passes subscription dict)
- `stripe_webhook.py` on subscription.deleted (passes None)

## Billing Config

> File: `apps/api/src/api/config/billing.py`

### Constants
- `STRIPE_SECRET_KEY`: from `os.getenv("STRIPE_SECRET_KEY")`
- `STRIPE_WEBHOOK_SECRET`: from `os.getenv("STRIPE_WEBHOOK_SECRET")`

### validate_stripe_config() -> (bool, list)
- Returns (is_valid, missing_keys)
- Checks both STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET are set

## Stripe Integration Architecture

```
Plans table (DB, single source of truth)
  ├── plan_slug: free, pro, team, affiliate, sponsored_free
  ├── stripe_price_id: maps to Stripe Price object
  └── limits: reports_per_month, property_reports_per_month, sms_per_month

Checkout Flow:
  Frontend -> POST /v1/billing/checkout -> Stripe Checkout Session -> Stripe payment
  Stripe -> POST /v1/webhooks/stripe -> price_id -> plan_slug -> UPDATE accounts

Portal Flow:
  Frontend -> GET /v1/billing/portal -> Stripe Customer Portal URL
  Stripe handles all management (cancel, update payment, view invoices)
```
