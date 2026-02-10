# Billing API

> Stripe checkout, customer portal, and webhook handling.
> Files: `apps/api/src/api/routes/billing.py` and `stripe_webhook.py`

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /v1/billing/checkout | Create Stripe Checkout Session | Required |
| GET | /v1/billing/portal | Create Stripe Customer Portal | Required |
| POST | /v1/webhooks/stripe | Handle Stripe webhook events | Public (signature verified) |

## Key Functions

### POST /v1/billing/checkout
- **Input:** `{plan_slug}` (any plan with stripe_price_id set)
- Validates:
  - Stripe is configured (API key + webhook secret)
  - Plan exists and has stripe_price_id (DB lookup via `get_plan_by_slug()`)
  - Account is REGULAR type (not INDUSTRY_AFFILIATE)
  - Account is not sponsored (no sponsor_account_id)
- Creates Stripe customer if none exists (stores stripe_customer_id on accounts)
- Creates Checkout Session with:
  - mode: subscription
  - Metadata: account_id, plan_slug
  - Success/cancel URLs to frontend
- Returns `{url}` for frontend redirect

### GET /v1/billing/portal
- Requires existing stripe_customer_id on account
- Creates Stripe billing portal session
- Returns `{url}` for frontend redirect

### POST /v1/webhooks/stripe
- Verifies webhook signature with `stripe.Webhook.construct_event()`
- Events handled:
  - `customer.subscription.created`: Maps price_id to plan_slug via `get_plan_slug_for_stripe_price()`, updates accounts.plan_slug, calls `update_account_billing_state()`
  - `customer.subscription.updated`: Same as created (handles plan changes)
  - `customer.subscription.deleted`: Downgrades to `free` plan, clears billing state
- Always returns `{received: true}` (even for errors, to prevent Stripe retries)
- Uses raw `psycopg.connect()` (not the db_conn helper)

## Stripe Integration Flow

```
User clicks "Upgrade" on frontend
  -> POST /v1/billing/checkout {plan_slug: "pro"}
  -> API creates Stripe Checkout Session
  -> Returns checkout URL
  -> Frontend redirects to Stripe
  -> User completes payment
  -> Stripe sends webhook: customer.subscription.created
  -> POST /v1/webhooks/stripe
  -> API maps price_id -> plan_slug
  -> Updates accounts.plan_slug = "pro"
  -> Updates billing_status, stripe_subscription_id
  -> Frontend redirects to success URL
```

## Dependencies
- `config/billing.py`: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `validate_stripe_config()`
- `services/plan_lookup.py`: `get_plan_by_slug()`, `get_plan_slug_for_stripe_price()`
- `services/billing_state.py`: `update_account_billing_state()`
- External: Stripe SDK (`stripe` package)

## Related Files
- Frontend: `/app/billing` (billing page with upgrade button)
- Frontend: `/app/settings` (account plan display)
