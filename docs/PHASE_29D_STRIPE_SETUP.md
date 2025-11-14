# Phase 29D: Stripe Integration Setup

**Status:** ✅ Implementation Complete  
**Date:** November 14, 2025

## Overview

Phase 29D integrates Stripe for subscription billing on the `pro` and `team` plans. The integration:

- Allows REGULAR users to upgrade from `free` → `pro` or `team`
- Uses Stripe Checkout for payment collection
- Uses Stripe Customer Portal for subscription management
- Syncs subscription status back to `accounts.plan_slug` via webhooks
- Respects existing plan limits and usage enforcement

## Architecture

```
User clicks "Upgrade to Pro"
  ↓
Frontend calls /api/proxy/v1/billing/checkout
  ↓
Backend creates Stripe Checkout Session
  ↓
User redirected to Stripe → pays
  ↓
Stripe webhook fires (subscription.created/updated)
  ↓
Backend updates accounts.plan_slug = 'pro'
  ↓
User redirected back to /app/account/plan
  ↓
Plan/usage UI reflects new plan & limits
```

## Required Environment Variables

### On Render (reportscompany-api service):

```bash
STRIPE_SECRET_KEY=sk_test_...       # Or sk_live_... for production
STRIPE_WEBHOOK_SECRET=whsec_...     # From Stripe webhook endpoint settings
STRIPE_PRICE_PRO_MONTH=price_...    # Stripe Price ID for Pro plan
STRIPE_PRICE_TEAM_MONTH=price_...   # Stripe Price ID for Team plan
```

### On Vercel (reportscompany-web):

No additional env vars needed - uses existing `NEXT_PUBLIC_API_BASE`.

## Stripe Dashboard Setup

### 1. Create Products & Prices

In Stripe Dashboard → Products:

**Pro Plan:**
- Name: `TrendyReports Pro`
- Description: `50 reports/month with advanced features`
- Price: `$29/month` (or your pricing)
- Copy the **Price ID**: `price_...` → set as `STRIPE_PRICE_PRO_MONTH`

**Team Plan:**
- Name: `TrendyReports Team`
- Description: `200 reports/month for teams`
- Price: `$99/month` (or your pricing)
- Copy the **Price ID**: `price_...` → set as `STRIPE_PRICE_TEAM_MONTH`

### 2. Create Webhook Endpoint

In Stripe Dashboard → Developers → Webhooks:

**Endpoint URL:**
```
https://reportscompany.onrender.com/v1/webhooks/stripe
```

**Events to send:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

**After creating:**
- Copy the **Signing secret**: `whsec_...` → set as `STRIPE_WEBHOOK_SECRET`

### 3. Test Mode vs Production

For development:
- Use **Test mode** keys (`sk_test_...`, `whsec_test_...`)
- Use Stripe test cards: `4242 4242 4242 4242`

For production:
- Switch to **Live mode** keys
- Update all env vars on Render
- Test with real payment methods

## Database Schema (No Changes Needed)

Stripe integration uses existing `accounts` table:
- `stripe_customer_id` (text, nullable) - stores Stripe Customer ID
- `plan_slug` (text) - updated by webhooks

No new migrations required for Phase 29D.

## API Endpoints

### POST /v1/billing/checkout
**Purpose:** Create Stripe Checkout Session for plan upgrade

**Request:**
```json
{
  "plan_slug": "pro"
}
```

**Response:**
```json
{
  "url": "https://checkout.stripe.com/c/pay/..."
}
```

**Error Cases:**
- 400: Invalid plan_slug or account is sponsored
- 500: Stripe API error or missing config

### GET /v1/billing/portal
**Purpose:** Create Stripe Customer Portal Session for subscription management

**Response:**
```json
{
  "url": "https://billing.stripe.com/p/session/..."
}
```

**Error Cases:**
- 400: No Stripe customer for this account
- 500: Stripe API error

### POST /v1/webhooks/stripe
**Purpose:** Receive Stripe webhook events

**Events Handled:**
- `customer.subscription.created` → Set `plan_slug` to paid plan
- `customer.subscription.updated` → Update `plan_slug` if price changed
- `customer.subscription.deleted` → Downgrade to `free`

**Security:** Validates webhook signature using `STRIPE_WEBHOOK_SECRET`

## Frontend Integration

### /app/account/plan UI

**For `free` plan users:**
- Shows "Upgrade to Pro" button
- On click → calls `/api/proxy/v1/billing/checkout` → redirects to Stripe

**For `pro` or `team` users:**
- Shows "Manage Billing" button
- On click → calls `/api/proxy/v1/billing/portal` → redirects to Stripe

**For `sponsored_free` users:**
- No Stripe buttons
- Shows: "Your access is sponsored by your industry affiliate"

### Success/Cancel Flows

**After Checkout:**
- Success: `?checkout=success` → "Payment successful! Your plan will update shortly."
- Cancel: `?checkout=cancel` → "Payment cancelled. You can try again anytime."

## Testing Checklist

### Test Mode (Development)

1. **Upgrade Flow:**
   - [ ] Login as `free` REGULAR user
   - [ ] Click "Upgrade to Pro" on `/app/account/plan`
   - [ ] Complete Stripe checkout with test card `4242 4242 4242 4242`
   - [ ] Verify redirect back with `?checkout=success`
   - [ ] Verify webhook fires and updates `plan_slug = 'pro'` in DB
   - [ ] Verify `/app/account/plan` shows Pro plan with new limits

2. **Portal Flow:**
   - [ ] As Pro user, click "Manage Billing"
   - [ ] Verify redirect to Stripe portal
   - [ ] Cancel subscription in portal
   - [ ] Verify webhook fires and updates `plan_slug = 'free'`
   - [ ] Verify limits revert to free tier

3. **Edge Cases:**
   - [ ] Sponsored user sees no Stripe buttons
   - [ ] API returns 400 for invalid plan_slug
   - [ ] Webhook signature validation rejects tampered requests

### Production

1. Switch to live Stripe keys
2. Test with real payment method (use low-value transaction)
3. Verify webhooks fire correctly
4. Test subscription cancellation
5. Monitor Stripe Dashboard for any errors

## Troubleshooting

### "Missing Stripe configuration"
- Check that all 4 env vars are set on Render
- Restart API service after setting env vars
- Check logs: `grep STRIPE`

### Webhooks not firing
- Verify endpoint URL is correct in Stripe Dashboard
- Check webhook endpoint is publicly accessible
- View webhook logs in Stripe Dashboard → Developers → Webhooks
- Check API logs for webhook processing

### Plan not updating after payment
- Check webhook logs in Stripe Dashboard
- Verify `STRIPE_WEBHOOK_SECRET` matches
- Check API logs for database update queries
- Manually query DB: `SELECT plan_slug, stripe_customer_id FROM accounts WHERE email = '...'`

## File Locations

### Backend:
- `apps/api/src/api/config/billing.py` - Stripe config & mappings
- `apps/api/src/api/routes/billing.py` - Checkout & portal endpoints
- `apps/api/src/api/routes/stripe_webhooks.py` - Webhook handler

### Frontend:
- `apps/web/app/api/proxy/v1/billing/checkout/route.ts` - Checkout proxy
- `apps/web/app/api/proxy/v1/billing/portal/route.ts` - Portal proxy
- `apps/web/app/account/plan/page.tsx` - Updated with Stripe buttons

## Next Steps (Future Enhancements)

- [ ] Usage-based billing (overage charges)
- [ ] Annual billing discounts
- [ ] Custom enterprise plans
- [ ] Stripe Tax for international customers
- [ ] Revenue analytics dashboard

## Support

For Stripe integration issues:
- API logs: Render dashboard → reportscompany-api → Logs
- Webhook logs: Stripe Dashboard → Developers → Webhooks → View logs
- Database: Render SQL editor or psql connection



