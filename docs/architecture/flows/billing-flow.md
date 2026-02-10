# Billing Flow

## Overview

End-to-end flow for subscription management, from plan selection through payment processing and plan enforcement.

## Flow

```
USER: Visits Billing Page
  - /app/settings/billing or /app/billing
  - Sees current plan, usage, and upgrade options
         |
         v
USER: Clicks Upgrade
  1. Selects desired plan (Starter, Pro, Enterprise)
         |
         | POST /v1/billing/checkout
         v
API: Create Checkout Session
  1. Look up Stripe Price ID from STRIPE_PRICE_MAP
  2. Get or create Stripe customer (stripe_customer_id on account)
  3. Create Stripe Checkout Session
  4. Return checkout URL
         |
         v
STRIPE: Hosted Checkout
  1. User redirected to Stripe-hosted payment page
  2. User enters payment details
  3. Payment processed
  4. User redirected back to app (success/cancel URL)
         |
         | Stripe webhook POST /v1/billing/webhook
         v
API: Process Webhook
  1. Verify webhook signature (STRIPE_WEBHOOK_SECRET)
  2. Handle event type:
     |
     |-- checkout.session.completed
     |   -> Link Stripe customer to account
     |
     |-- customer.subscription.created
     |   -> Set account plan_slug + billing_status = active
     |
     |-- customer.subscription.updated
     |   -> Update account plan_slug (upgrade/downgrade)
     |
     |-- customer.subscription.deleted
     |   -> Set account plan_slug = free, billing_status = cancelled
     |
  3. Log billing_event for audit
         |
         v
ENFORCEMENT: Plan Limits
  - On every report generation: evaluate_report_limit()
  - Checks: monthly_report_limit from plans table
  - Override: monthly_report_limit_override on account
  - If limit reached: 429 response with BLOCK decision
  - Overage: if plan.allow_overage, charge overage_price_cents
```

## Customer Portal

Users can manage their subscription through Stripe's Customer Portal:

```
USER: Clicks "Manage Subscription"
         |
         | POST /v1/billing/portal
         v
API: Create Portal Session
  1. Create Stripe Billing Portal session
  2. Return portal URL
         |
         v
STRIPE: Customer Portal
  - Update payment method
  - View invoices
  - Cancel subscription
  - Changes trigger webhooks back to API
```

## Key Files

| Service | File | Purpose |
|---------|------|---------|
| Frontend | `app/app/settings/billing/page.tsx` | Billing settings page |
| Frontend | `app/app/billing/page.tsx` | Billing overview page |
| API | `routes/billing.py` | Checkout + webhook endpoints |
| API | `services/plans.py` | Plan limit evaluation |
| API | `config/billing.py` | Stripe price map configuration |

## Failure Modes

| Failure | Handling |
|---------|----------|
| Stripe checkout abandoned | No webhook received, no state change |
| Webhook signature invalid | 400 response, event ignored |
| Duplicate webhook event | Idempotent processing via billing_events log |
| Payment fails | Stripe handles retries and dunning |
| Plan downgrade mid-cycle | Prorated by Stripe, limits updated on webhook |
