# Stripe Integration

## Overview

Stripe handles all subscription billing, checkout sessions, and customer portal management.

## Service Details

- **Used by:** API service (`routes/billing.py`, `services/plans.py`, `config/billing.py`)
- **Auth method:** API Key (secret key)
- **Capabilities:**
  - Checkout session creation for plan upgrades
  - Customer portal for self-service billing management
  - Webhook processing for subscription lifecycle events
  - Plan-to-price mapping via `STRIPE_PRICE_MAP`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | Webhook endpoint signing secret |
| `STARTER_PRICE_ID` | Stripe Price ID for Starter plan |
| `PRO_PRICE_ID` | Stripe Price ID for Pro plan |
| `ENTERPRISE_PRICE_ID` | Stripe Price ID for Enterprise plan |

## Webhook Events

The following Stripe webhook events are processed:

- `checkout.session.completed` - Successful payment, activate subscription
- `customer.subscription.created` - New subscription created
- `customer.subscription.updated` - Plan change or renewal
- `customer.subscription.deleted` - Subscription cancelled

## Key Behaviors

- Checkout sessions redirect users to Stripe-hosted payment pages
- On successful payment, the account's `plan_slug` and `billing_status` are updated
- Plan limits (report counts, SMS credits) are enforced based on the active plan
- Billing events are logged to the `billing_events` table for audit
