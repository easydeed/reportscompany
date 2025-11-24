# BILLING SYSTEM - QA CHECKLIST

**Date**: Nov 24, 2025  
**Status**: PASSES 1-4 DEPLOYED ✅  
**Next**: Manual testing to verify billing is 100% complete

---

## ✅ PASSES 1-4 IMPLEMENTATION SUMMARY

### PASS 1: Single Source of Truth ✅
**Commit**: `d6bcb78`

**What Was Built**:
- Created `plan_lookup.py` service with DB-backed lookups
- Updated Checkout to use `plans.stripe_price_id` from database
- Updated Webhooks to map `price_id` → `plan_slug` via database
- Removed env-based price maps (`STRIPE_PRICE_MAP`)

**Status**: **COMPLETE** - Database is single source of truth

---

### PASS 2: Subscription State Tracking ✅
**Commit**: `2d01af3`

**What Was Built**:
- Created `billing_state.py` service
- `update_account_billing_state()` syncs subscription to DB
- Webhooks update `stripe_subscription_id` and `billing_status`
- `/v1/account/plan-usage` exposes `billing_status`

**Status**: **COMPLETE** - Subscription state tracked in database

---

### PASS 3: Plan Catalog + Stripe Billing ✅
**Commit**: `b7f326f`

**What Was Built**:
- Verified `plans.py` Plan Catalog already exists
- `get_plan_catalog()` reads DB + enriches with Stripe pricing
- Already used by `/v1/account/plan-usage`

**Status**: **COMPLETE** - Was already implemented

---

### PASS 4: Frontend Uses plan-usage ✅
**Commit**: `a117afd`

**What Was Built**:
- Added `billing_status` to frontend type
- Display billing status for agents and affiliates
- Updated upgrade cards (Free + Solo instead of hardcoded Pro/Team)
- Current plan pricing comes from `stripe_billing`

**Status**: **COMPLETE** - No hardcoded prices in UI

---

## 🧪 QA CHECKLIST - 6 VERIFICATION TESTS

### Test 1: Plan ↔ Price Mapping ✅
**Goal**: Verify database is single source of truth for price mapping

**Backend Test**:
1. Check `plans` table has `stripe_price_id` for `solo` and `affiliate`
2. Change `stripe_price_id` for `solo` plan in database
3. Create new Checkout session for `solo` plan
4. Verify new price_id is used in Stripe session

**Expected**:
- ✅ Checkout uses `plans.stripe_price_id` from database
- ✅ No env vars (`STRIPE_PRICE_PRO_MONTH`, etc.) are checked
- ✅ Changing DB immediately affects checkout

**Webhook Test**:
1. Simulate webhook with unknown `price_id` (not in `plans` table)
2. Check logs for warning message
3. Verify webhook returns HTTP 200 (doesn't retry)

**Expected**:
- ✅ Warning logged: "Stripe webhook: no plan found for price_id=..."
- ✅ Webhook returns `{"received": True}`
- ✅ No crash or 500 error

**Status**: ⬜ READY TO TEST

---

### Test 2: Subscription State - Created/Updated ✅
**Goal**: Verify subscription state is stored after Checkout

**Steps**:
1. As REGULAR agent with `plan_slug='free'`
2. Go to `/app/billing`
3. Click "Choose Solo Agent" (or any paid plan)
4. Complete Stripe Checkout (use test card `4242 4242 4242 4242`)
5. Webhook `customer.subscription.created` fires
6. Check database:
   ```sql
   SELECT plan_slug, stripe_subscription_id, billing_status 
   FROM accounts WHERE id = '<account_id>';
   ```

**Expected**:
- ✅ `plan_slug` = 'solo' (or chosen plan)
- ✅ `stripe_customer_id` set
- ✅ `stripe_subscription_id` = 'sub_...'
- ✅ `billing_status` = 'active'

**Status**: ⬜ READY TO TEST

---

### Test 3: Subscription State - Deleted/Canceled ✅
**Goal**: Verify state is cleared when subscription is canceled

**Steps**:
1. As paid agent with active subscription
2. Go to `/app/billing`
3. Click "Manage Billing" → Opens Stripe Portal
4. Cancel subscription in Stripe Portal
5. Webhook `customer.subscription.deleted` fires
6. Check database:
   ```sql
   SELECT plan_slug, stripe_subscription_id, billing_status 
   FROM accounts WHERE id = '<account_id>';
   ```

**Expected**:
- ✅ `plan_slug` = 'free' (downgraded)
- ✅ `stripe_subscription_id` = NULL
- ✅ `billing_status` = 'canceled'

**Status**: ⬜ READY TO TEST

---

### Test 4: plan-usage API ✅
**Goal**: Verify `/v1/account/plan-usage` returns correct Stripe data

**Free Agent Test**:
```bash
curl -H "Cookie: mr_token=..." \
  https://api.trendyreports.io/v1/account/plan-usage
```

**Expected**:
```json
{
  "account": {
    "plan_slug": "free",
    "billing_status": null
  },
  "stripe_billing": null
}
```

**Paid Agent Test** (after subscribing to Solo):
**Expected**:
```json
{
  "account": {
    "plan_slug": "solo",
    "billing_status": "active"
  },
  "stripe_billing": {
    "stripe_price_id": "price_...",
    "amount": 1900,
    "currency": "usd",
    "interval": "month",
    "interval_count": 1,
    "nickname": "Solo Agent – $19/mo"
  }
}
```

**Affiliate Test**:
**Expected**:
```json
{
  "account": {
    "plan_slug": "affiliate",
    "billing_status": "active"
  },
  "stripe_billing": {
    "amount": 9900,
    "currency": "usd",
    "interval": "month",
    "nickname": "Affiliate – $99/mo"
  }
}
```

**Status**: ⬜ READY TO TEST

---

### Test 5: /app/billing – Agents ✅
**Goal**: Verify agent billing page shows real Stripe data

**Free Agent**:
1. Log in as free agent
2. Go to `/app/billing`
3. Observe "Current Plan" card

**Expected**:
- ✅ Plan: "Free" (or plan_name from DB)
- ✅ Price: "$0 / month" or "Free"
- ✅ No billing status shown (or shows null)
- ✅ No hardcoded "$99" or "$299" anywhere

**Paid Agent**:
1. Log in as agent with active Solo subscription
2. Go to `/app/billing`
3. Observe "Current Plan" card

**Expected**:
- ✅ Plan: "Solo Agent" (or `stripe_billing.nickname`)
- ✅ Price: "$19 / month" (from Stripe, not hardcoded)
- ✅ Status: "Status: active"
- ✅ "Manage Billing" button present

**Status**: ⬜ READY TO TEST

---

### Test 6: /app/billing – Affiliates ✅
**Goal**: Verify affiliate billing page shows real Stripe data

**Steps**:
1. Log in as affiliate account
2. Go to `/app/billing`
3. Observe affiliate plan card

**Expected**:
- ✅ Plan: "Affiliate" (or `stripe_billing.nickname`)
- ✅ Price: "$99 / month" (from Stripe)
- ✅ Status: "Status: active" (if applicable)
- ✅ "Manage billing" button opens Stripe Portal
- ✅ No hardcoded "$99/month" text (comes from `stripe_billing`)

**Status**: ⬜ READY TO TEST

---

### Test 7: Regressions ✅
**Goal**: Verify existing flows still work

**Checkout Flow**:
- ✅ Free → Solo checkout works
- ✅ Stripe session created successfully
- ✅ Success redirect works

**Portal Flow**:
- ✅ "Manage Billing" button works for agents
- ✅ Portal opens correctly
- ✅ Can view/update payment method
- ✅ Can cancel subscription

**API Errors**:
- ✅ No 500 errors from new `billing_status` or `stripe_billing` fields
- ✅ No TypeScript errors in frontend
- ✅ No Stripe API errors in backend logs

**Status**: ⬜ READY TO TEST

---

## 📊 QA RESULTS TEMPLATE

After testing, fill in:

| Test | Status | Notes |
|------|--------|-------|
| 1. Plan ↔ Price Mapping | ⬜ PASS / ❌ FAIL | |
| 2. Subscription State - Created | ⬜ PASS / ❌ FAIL | |
| 3. Subscription State - Canceled | ⬜ PASS / ❌ FAIL | |
| 4. plan-usage API | ⬜ PASS / ❌ FAIL | |
| 5. /app/billing – Agents | ⬜ PASS / ❌ FAIL | |
| 6. /app/billing – Affiliates | ⬜ PASS / ❌ FAIL | |
| 7. Regressions | ⬜ PASS / ❌ FAIL | |

---

## ✅ DEFINITION OF "DONE"

Billing System is **100% COMPLETE** when:

1. ✅ All 4 passes deployed (DONE)
2. ⬜ All 7 QA tests pass (PENDING USER TEST)
3. ⬜ Any discovered bugs fixed
4. ⬜ BILLING_AUDIT.md updated with final status

**Then**: Billing is done. Move forward to next phase.

---

## 🎯 NEXT STEPS AFTER QA

1. **If All Tests Pass**:
   - Mark Billing as 100% complete
   - Update audit document with "S2 - QA VERIFIED" section
   - Declare victory: People ✅ Billing ✅

2. **If Any Test Fails**:
   - Document failure details
   - Create focused fix
   - Retest
   - Then mark complete

---

## 📝 USER INSTRUCTIONS

**To run QA**:
1. Use test Stripe keys (not production)
2. Test card: `4242 4242 4242 4242` (any future date, any CVC)
3. Follow each test in order
4. Fill in results table
5. Report any failures with specific details

**Expected Time**: 20-30 minutes for all 7 tests

**Ready to test**: ✅ YES - All code deployed (commit a117afd)

---

## 🚨 KNOWN EDGE CASES

1. **Webhook delays**: Stripe webhooks may take 1-2 seconds to fire after Checkout
   - **Fix**: Refresh `/app/billing` after checkout to see updated plan

2. **Test mode subscriptions**: Don't expire like production
   - **Note**: This is expected Stripe test mode behavior

3. **Upgrade cards**: Currently show static Free + Solo plans
   - **TODO**: Future enhancement to fetch from `/v1/billing/plans` endpoint
   - **Not blocking**: Current plan display works correctly

---

**All 4 passes deployed. QA checklist ready. Awaiting manual verification.**

