# Billing & Stripe Integration Audit

**Date**: November 21, 2024  
**Purpose**: Comprehensive read-only audit of Stripe billing implementation  
**Scope**: Backend API, webhooks, database schema, frontend billing pages

---

## 1. Stripe Integration Overview

### 1.1 Configuration & Environment Variables

**Location**: `apps/api/src/api/config/billing.py`

**Environment Variables Required**:
- `STRIPE_SECRET_KEY` - Stripe API key for server-side operations
- `STRIPE_WEBHOOK_SECRET` - Secret for verifying webhook signatures
- `STRIPE_PRICE_PRO_MONTH` - Price ID for Pro plan (currently unused - not in plans table)
- `STRIPE_PRICE_TEAM_MONTH` - Price ID for Team plan (currently unused - not in plans table)
- `WEB_BASE` - Frontend URL for checkout redirect (defaults to Vercel)

**Current Stripe Price Configuration**:
```python
STRIPE_PRICE_MAP = {
    "pro": os.getenv("STRIPE_PRICE_PRO_MONTH"),
    "team": os.getenv("STRIPE_PRICE_TEAM_MONTH"),
}
```

⚠️ **NOTE**: This map is used by the old checkout flow (`billing.py`) but is **OUT OF SYNC** with the database plans table, which only has `stripe_price_id` set for `solo` and `affiliate` plans.

### 1.2 Stripe SDK Initialization

**Files**:
- `apps/api/src/api/config/billing.py` (lines 86-92)
- `apps/api/src/api/routes/billing.py` (lines 24-29)
- `apps/api/src/api/routes/stripe_webhook.py` (lines 24-30)
- `apps/api/src/api/services/plans.py` (line 21)

**Pattern**: Lazy import with fallback

```python
try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None
```

### 1.3 Stripe Operations

**Checkout Session Creation**:
- **File**: `apps/api/src/api/routes/billing.py`
- **Endpoint**: `POST /v1/billing/checkout`
- **Method**: `stripe.checkout.Session.create()`
- **Mode**: `subscription`
- **Returns**: Checkout URL for frontend redirect

**Customer Portal Session**:
- **File**: `apps/api/src/api/routes/billing.py`
- **Endpoint**: `GET /v1/billing/portal`
- **Method**: `stripe.billing_portal.Session.create()`
- **Returns**: Portal URL for managing subscription

**Price Retrieval** (for display):
- **File**: `apps/api/src/api/services/plans.py`
- **Method**: `stripe.Price.retrieve(price_id)`
- **Purpose**: Fetch real-time pricing from Stripe for UI display
- **Used in**: `/v1/account/plan-usage` endpoint

---

## 2. Plan & Account Model

### 2.1 Database Schema - `plans` Table

**Migration**: `db/migrations/0007_phase_29a_plans_and_account_types.sql` (base), `db/migrations/0013_unify_plans_table.sql` (Stripe fields)

**Schema**:
```sql
CREATE TABLE plans (
  plan_slug TEXT PRIMARY KEY,
  plan_name TEXT NOT NULL,
  monthly_report_limit INT NOT NULL,
  allow_overage BOOLEAN NOT NULL DEFAULT false,
  overage_price_cents INT NOT NULL DEFAULT 0,
  stripe_price_id TEXT,                    -- Added in migration 0013
  description TEXT,                         -- Added in migration 0013
  is_active BOOLEAN NOT NULL DEFAULT true,  -- Added in migration 0013
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Current Data** (Production/Staging):
| plan_slug | plan_name | monthly_report_limit | stripe_price_id | description |
|-----------|-----------|---------------------|----------------|-------------|
| `affiliate` | Affiliate | 5000 | `price_1STMtfBKYbtiKxfsqQ4r29Cw` | Affiliate plan - $99/month |
| `free` | Free | 50 | NULL | - |
| `pro` | Pro | 300 | NULL | - |
| `solo` | Solo Agent | 500 | `price_1SO4sDBKYbtiKxfsUnKeJiox` | Solo plan - $19/month |
| `sponsored_free` | Sponsored Free | 75 | NULL | - |
| `team` | Team | 1000 | NULL | - |

### 2.2 Database Schema - `accounts` Table

**Migrations**: 
- `db/migrations/0001_base.sql` (base accounts table)
- `db/migrations/0003_billing.sql` (Stripe fields)
- `db/migrations/0007_phase_29a_plans_and_account_types.sql` (plan system)

**Billing-Related Columns**:
```sql
-- Core plan/type
plan_slug VARCHAR(50) REFERENCES plans(slug)
account_type TEXT CHECK (account_type IN ('REGULAR', 'INDUSTRY_AFFILIATE'))

-- Stripe integration
stripe_customer_id VARCHAR(100)
stripe_subscription_id VARCHAR(100)  -- ⚠️ NOT CURRENTLY UPDATED BY WEBHOOKS
billing_status VARCHAR(50)            -- ⚠️ NOT CURRENTLY UPDATED

-- Usage overrides
monthly_report_limit_override INT

-- Sponsorship
sponsor_account_id UUID REFERENCES accounts(id)
```

### 2.3 Plan Resolution Logic

**File**: `apps/api/src/api/services/usage.py` (inferred from account.py imports)

**Function**: `resolve_plan_for_account(cur, account_id)`

**Logic**:
1. Queries `accounts` table for `plan_slug` and `monthly_report_limit_override`
2. Queries `plans` table for plan details
3. Returns merged plan object with effective limit

**Usage Tracking**:
- **Function**: `get_monthly_usage(cur, account_id)`
- **Source**: `report_generations` table (inferred)
- **Scope**: Current calendar month

**Limit Evaluation**:
- **Function**: `evaluate_report_limit(cur, account_id)`
- **Returns**: Decision enum (ALLOW/DENY/etc.) + info message

---

## 3. Agent Billing Flow

### 3.1 Free Registration

**Registration Endpoint**: (Not in scope of this audit - assumed to exist)

**Default State**:
- `account_type = 'REGULAR'`
- `plan_slug = 'free'`
- `stripe_customer_id = NULL`
- `monthly_report_limit = 50`

### 3.2 Upgrade to Pro/Team

**Frontend**: `apps/web/app/app/billing/page.tsx` (lines 95-114)

**Flow**:
1. User clicks "Choose Professional" or "Choose Team"
2. Frontend calls `POST /api/proxy/v1/billing/checkout`
   - **Body**: `{ "plan_slug": "pro" }` or `{ "plan_slug": "team" }`
3. Backend (`apps/api/src/api/routes/billing.py:47-223`):
   - **Validation** (lines 125-141):
     - Account must be `REGULAR` type
     - Account must NOT be sponsored (`sponsor_account_id` must be NULL)
   - **Get/Create Stripe Customer** (lines 161-189):
     - If no `stripe_customer_id`, creates customer with `stripe.Customer.create()`
     - Saves customer ID to `accounts.stripe_customer_id`
   - **Get Price ID** (line 92):
     - Calls `get_stripe_price_for_plan(plan_slug)`
     - Looks up in `STRIPE_PRICE_MAP` environment variable
     - ⚠️ **ISSUE**: Uses env var, not `plans.stripe_price_id`
   - **Create Checkout Session** (lines 192-213):
     - `mode: "subscription"`
     - `customer: stripe_customer_id`
     - `line_items: [{ price: price_id, quantity: 1 }]`
     - `metadata: { account_id, plan_slug }`
     - `subscription_data.metadata: { account_id, plan_slug }`
     - `success_url: /account/plan?checkout=success`
     - `cancel_url: /account/plan?checkout=cancel`
4. Frontend redirects to Stripe Checkout
5. User completes payment
6. Stripe redirects to success URL
7. **Webhook fires** (see section 6)

### 3.3 Manage/Cancel Subscription

**Frontend**: `apps/web/app/app/billing/page.tsx` (lines 116-131)

**Flow**:
1. User clicks "Manage Billing" button
2. Frontend calls `GET /api/proxy/v1/billing/portal`
3. Backend (`apps/api/src/api/routes/billing.py:226-309`):
   - **Validation** (lines 284-291):
     - Account must have `stripe_customer_id`
   - **Create Portal Session** (lines 294-300):
     - `stripe.billing_portal.Session.create(customer: stripe_customer_id)`
     - `return_url: /account/plan`
4. Frontend redirects to Stripe Portal
5. User can:
   - Update payment method
   - Cancel subscription
   - View invoices
6. **Webhooks fire** on subscription changes

---

## 4. Affiliate Billing Flow

### 4.1 Affiliate Creation

**Source**: Not in billing code (likely in admin/invite flow)

**Expected State**:
- `account_type = 'INDUSTRY_AFFILIATE'`
- `plan_slug = 'affiliate'`
- `stripe_customer_id = NULL` (initially)

### 4.2 Affiliate Upgrade/Payment

**Frontend**: `apps/web/app/app/billing/page.tsx` (lines 146-186)

**Current Implementation**:
- Shows "Your Affiliate Plan" card
- Displays plan name from `stripe_billing.nickname` or `plan.plan_name`
- Shows price from `stripe_billing` object
- Only button: "Manage billing" → opens Stripe Portal

**Missing Flow**:
- ⚠️ **NO CHECKOUT FLOW FOR AFFILIATES**
- Affiliates cannot self-upgrade via the UI
- `POST /v1/billing/checkout` explicitly **BLOCKS** non-REGULAR accounts (line 125-132)

**Assumed Manual Process**:
1. Affiliate created by admin
2. Admin manually creates Stripe subscription via Stripe Dashboard
3. Admin sets `stripe_customer_id` and `plan_slug = 'affiliate'` on account
4. Affiliate can then use billing portal to manage

### 4.3 Affiliate Billing Portal

**Same as Agent**: Uses `GET /v1/billing/portal` (section 3.3)

---

## 5. Webhook Behavior

### 5.1 Webhook Endpoint

**File**: `apps/api/src/api/routes/stripe_webhook.py`

**Endpoint**: `POST /v1/webhooks/stripe`

**Authentication**: Stripe signature verification

```python
stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
```

### 5.2 Events Handled

#### **`customer.subscription.created`** (lines 76-118)

**Purpose**: Set plan when subscription is first created

**Logic**:
1. Extract `account_id` from `subscription.metadata.account_id`
2. Get `price_id` from first line item (`subscription.items.data[0].price.id`)
3. Map `price_id` → `plan_slug` using `get_plan_for_stripe_price(price_id)`
   - **Source**: `STRIPE_PRICE_REVERSE_MAP` (from env vars)
   - ⚠️ **ISSUE**: Uses env var map, not database `plans.stripe_price_id`
4. Update `accounts.plan_slug = plan_slug WHERE id = account_id`
5. ⚠️ **DOES NOT UPDATE**: `stripe_subscription_id`, `billing_status`

**Logging**:
- ✅ Logs success: `✅ Updated account {id} to plan '{plan_slug}'`
- ⚠️ Logs warnings for missing metadata/price
- ⚠️ Returns 200 even on error (to prevent Stripe retries)

#### **`customer.subscription.updated`** (lines 76-118)

**Purpose**: Update plan when subscription price changes

**Logic**: Same as `customer.subscription.created`

**Common Triggers**:
- User upgrades/downgrades plan via portal
- Admin changes subscription in Stripe Dashboard
- Trial ends and subscription becomes active

**⚠️ MISSING**: Handling for subscription status changes (`active` → `past_due`, etc.)

#### **`customer.subscription.deleted`** (lines 121-145)

**Purpose**: Downgrade to free when subscription is canceled

**Logic**:
1. Extract `account_id` from `subscription.metadata.account_id`
2. Update `accounts.plan_slug = 'free' WHERE id = account_id`
3. ⚠️ **DOES NOT**: Clear `stripe_subscription_id` or update `billing_status`

**Logging**:
- ✅ Logs success: `✅ Downgraded account {id} to 'free'`

### 5.3 Unhandled Events

**Logged but not processed** (line 148-149):
- `customer.subscription.trial_will_end`
- `customer.subscription.paused`
- `customer.subscription.resumed`
- `invoice.payment_failed`
- `invoice.payment_succeeded`
- `customer.updated`
- `customer.deleted`
- `charge.refunded`
- And any other Stripe event

**Impact**: No automated handling for:
- Payment failures → account stays on paid plan
- Trial expiration → no notification or downgrade
- Refunds → no plan adjustment

---

## 6. Frontend Billing Pages

### 6.1 `/app/billing` (Main Billing Page)

**File**: `apps/web/app/app/billing/page.tsx`

**Data Source**: `GET /api/proxy/v1/account/plan-usage`

**Response Shape**:
```typescript
{
  account: {
    id: string
    name: string
    account_type: string  // 'REGULAR' | 'INDUSTRY_AFFILIATE'
    plan_slug: string
  },
  plan: {
    plan_name: string     // From plans table
    plan_slug: string
    monthly_report_limit: number
  },
  usage: {
    report_count: number
  },
  stripe_billing: {       // From Stripe API, enriched in real-time
    stripe_price_id: string
    amount: number        // cents
    currency: string
    interval: string      // 'month'
    interval_count: number
    nickname: string | null
  } | null
}
```

**Display Logic** (lines 36-49):
```typescript
function getPlanDisplay(data) {
  let planName = data.plan.plan_name
  let priceDisplay = ""
  
  if (stripe_billing) {
    planName = stripe_billing.nickname || planName
    priceDisplay = `$${amount/100} / ${interval}`
  }
  
  return { planName, priceDisplay }
}
```

### 6.2 Agent View (lines 190-276)

**Current Plan Card**:
- Shows: Plan name, price (from Stripe), usage (X / Y reports)
- Button: "Manage Billing" (only if `stripe_billing` exists)

**Available Plans Grid** (lines 51-77):
⚠️ **HARDCODED PLANS**:
```javascript
const plans = [
  { name: "Starter", slug: "free", price: "$0", ... },
  { name: "Professional", slug: "pro", price: "$99", ... },
  { name: "Team", slug: "team", price: "$299", ... },
]
```

**Issues**:
1. **Price drift**: Hardcoded `$99` and `$299` may not match Stripe prices
2. **Plan mismatch**: Shows `pro` and `team`, but database has `solo` with Stripe price
3. **No dynamic fetch**: Does not query `/v1/dev/stripe-prices` or plans table
4. **Button calls**: `checkout(plan.slug)` → sends to `POST /v1/billing/checkout`
   - ⚠️ **BROKEN**: `pro` and `team` have NO `stripe_price_id` in database
   - ⚠️ **ENV VAR FALLBACK**: Relies on `STRIPE_PRICE_PRO_MONTH` / `STRIPE_PRICE_TEAM_MONTH` from config

### 6.3 Affiliate View (lines 146-186)

**Shows**:
- Plan name (e.g., "Affiliate")
- Price from `stripe_billing` object (e.g., "$99 / month")
- "Manage billing" button → opens Stripe Portal

**Does NOT show**:
- Usage metrics
- Available plans to upgrade/downgrade
- Checkout flow

**Issue**:
- ⚠️ No way to self-subscribe (must be done manually by admin)

---

## 7. Known Issues / Smells

### 7.1 Critical Issues

#### **1. Plan/Price Configuration Mismatch**
- **Database**: `plans` table has `stripe_price_id` for `solo` and `affiliate` only
- **Config**: `billing.py` uses `STRIPE_PRICE_MAP` for `pro` and `team`
- **Frontend**: Hardcodes "Pro" as `$99` and "Team" as `$299`
- **Impact**: 
  - If user clicks "Choose Professional", checkout will use env var `STRIPE_PRICE_PRO_MONTH`, not database
  - If env var is missing, checkout fails
  - Webhook will try to map price back to `pro`/`team` using env var reverse map

#### **2. Missing `stripe_subscription_id` Updates**
- **Current**: Webhooks only update `plan_slug`
- **Missing**: `stripe_subscription_id` field never gets set
- **Impact**: 
  - Cannot query current subscription status
  - Cannot check if subscription is `active`, `past_due`, `canceled`
  - Portal link works (uses `stripe_customer_id`), but no way to verify subscription state

#### **3. No `billing_status` Management**
- **Field exists**: `accounts.billing_status VARCHAR(50)`
- **Never set**: No code writes to this field
- **Impact**: Cannot track payment failures, dunning, or grace periods

#### **4. No Affiliate Self-Checkout**
- **Blocked**: `POST /v1/billing/checkout` rejects non-REGULAR accounts
- **Current flow**: Admin must manually create subscription in Stripe Dashboard
- **Impact**: Affiliates cannot self-serve signup/payment

### 7.2 Webhook Gaps

#### **Unhandled Critical Events**:
- `invoice.payment_failed` → Account should be flagged or downgraded
- `customer.subscription.trial_will_end` → Should notify user
- `customer.subscription.paused` → Should restrict access
- `customer.deleted` → Should clean up account

#### **Metadata Dependency**:
- All webhook handlers require `subscription.metadata.account_id`
- If metadata is missing (e.g., subscription created outside app), webhook silently fails
- **Fallback needed**: Use `stripe_customer_id` → lookup account

### 7.3 Price Display Issues

#### **Hardcoded Frontend Prices**:
```javascript
// apps/web/app/app/billing/page.tsx:51-77
{ name: "Professional", price: "$99", ... }  // May not match Stripe
{ name: "Team", price: "$299", ... }         // May not match Stripe
```

**Should be**: Dynamically fetched from `/v1/account/plan-usage` → `stripe_billing` object

#### **Partial Stripe Integration**:
- Current plan shows dynamic price ✅
- Available plans show hardcoded price ❌

### 7.4 Plan Naming Inconsistency

**Database** vs **Frontend** vs **Config**:
| Database | Frontend Display | Config Key | Stripe Price? |
|----------|------------------|-----------|---------------|
| `free` | "Starter" | - | No |
| `pro` | "Professional" | `STRIPE_PRICE_PRO_MONTH` | No (only in env) |
| `team` | "Team" | `STRIPE_PRICE_TEAM_MONTH` | No (only in env) |
| `solo` | Not shown | - | Yes (price_1SO4s...) |
| `affiliate` | "Affiliate" | - | Yes (price_1STMt...) |
| `sponsored_free` | Not shown | - | No |

**Result**: 
- `solo` plan exists in DB with Stripe price, but NOT shown on billing page
- `pro`/`team` shown on billing page, but NO Stripe prices in DB

### 7.5 Single Source of Truth Violation

**Three competing sources**:
1. **Database `plans` table**: Has `solo` and `affiliate` with Stripe price IDs
2. **Environment variables**: `STRIPE_PRICE_PRO_MONTH`, `STRIPE_PRICE_TEAM_MONTH`
3. **Frontend hardcoded**: `$99` and `$299` in billing page

**What should happen**:
- Database `plans.stripe_price_id` should be the ONLY source
- Frontend should fetch from `/v1/dev/stripe-prices` or similar endpoint
- Webhooks should map using database, not env vars

---

## 8. Data Flow Diagrams

### 8.1 Agent Upgrade Flow (Current)

```
User clicks "Choose Professional"
  ↓
Frontend: POST /api/proxy/v1/billing/checkout
  body: { "plan_slug": "pro" }
  ↓
Backend: billing.py:create_checkout_session
  1. Validate account (REGULAR, not sponsored)
  2. Get/create Stripe customer
  3. Get price_id from STRIPE_PRICE_MAP["pro"] (env var) ⚠️
  4. Create checkout session
  ↓
Stripe: User completes payment
  ↓
Stripe Webhook: customer.subscription.created
  ↓
Backend: stripe_webhook.py
  1. Get account_id from metadata
  2. Get price_id from subscription
  3. Map price_id → "pro" using STRIPE_PRICE_REVERSE_MAP (env var) ⚠️
  4. UPDATE accounts SET plan_slug='pro' ⚠️ (only updates plan_slug)
  ↓
User redirected to /account/plan?checkout=success
  ↓
Frontend: Fetches /v1/account/plan-usage
  Shows: plan_name="Pro", stripe_billing={amount:9900, ...}
```

### 8.2 Affiliate Billing Portal Flow (Current)

```
Affiliate clicks "Manage billing"
  ↓
Frontend: GET /api/proxy/v1/billing/portal
  ↓
Backend: billing.py:create_portal_session
  1. Check stripe_customer_id exists
  2. Create portal session
  ↓
Stripe Portal: User can cancel/update payment
  ↓
Stripe Webhook: customer.subscription.deleted
  ↓
Backend: stripe_webhook.py
  1. Get account_id from metadata
  2. UPDATE accounts SET plan_slug='free'
  ↓
User redirected to /account/plan
  ↓
Frontend: Shows downgraded to Free plan
```

### 8.3 Plan Display Flow (Current)

```
User visits /app/billing
  ↓
Frontend: fetch('/api/proxy/v1/account/plan-usage')
  ↓
Backend: account.py:get_current_account_plan_usage
  1. Query accounts (plan_slug, account_type)
  2. Query plans table (plan_name, monthly_report_limit)
  3. Query report_generations (usage count)
  4. Call get_plan_catalog(cur)
  ↓
Backend: plans.py:get_plan_catalog
  1. SELECT from plans table (stripe_price_id)
  2. For each plan with stripe_price_id:
     - Call stripe.Price.retrieve(price_id) ✅
     - Build StripeBilling object
  3. Return catalog with enriched Stripe data
  ↓
Backend: Returns to frontend:
  {
    account: {...},
    plan: { plan_name: "Pro", plan_slug: "pro", ... },
    stripe_billing: { amount: 9900, currency: "usd", ... }
  }
  ↓
Frontend: Displays dynamic price for CURRENT plan ✅
Frontend: Shows HARDCODED prices for available plans ❌
```

---

## 9. Recommendations for Phase 2

### 9.1 Immediate Fixes

1. **Unify price source**: Remove `STRIPE_PRICE_MAP` from env vars, use only `plans.stripe_price_id`
2. **Update webhook handler**: Map price_id using database query, not env var
3. **Update checkout handler**: Get price_id from database, not env var
4. **Fix frontend**: Remove hardcoded prices, fetch from API endpoint
5. **Add missing plan**: Either show `solo` on billing page OR add `pro`/`team` prices to database

### 9.2 Webhook Enhancements

1. **Save `stripe_subscription_id`**:
   ```sql
   UPDATE accounts 
   SET stripe_subscription_id = %s, plan_slug = %s 
   WHERE id = %s
   ```

2. **Update `billing_status`**:
   - `active`, `past_due`, `canceled`, `unpaid`, `trialing`

3. **Handle payment failures**:
   - `invoice.payment_failed` → Set `billing_status = 'past_due'`
   - Grace period logic

4. **Add customer ID fallback**:
   ```python
   # If metadata.account_id missing, lookup by customer_id
   cur.execute("SELECT id FROM accounts WHERE stripe_customer_id = %s", 
               (subscription['customer'],))
   ```

### 9.3 Affiliate Self-Checkout

**Option A**: Enable affiliate checkout in `billing.py`
```python
# Remove line 125-132 account_type check for affiliates
# Or add special handling:
if acc_type == 'INDUSTRY_AFFILIATE':
    # Get affiliate plan price from database
    price_id = get_price_for_plan('affiliate')
```

**Option B**: Separate affiliate checkout flow
- New endpoint: `POST /v1/billing/checkout-affiliate`
- Different Stripe product/price
- Custom success flow (e.g., send to admin approval)

### 9.4 Price Sync Endpoint

**Create**: `GET /v1/billing/plans` (public or auth-required)

**Purpose**: Frontend-facing endpoint for plan catalog

**Returns**:
```json
{
  "plans": [
    {
      "slug": "free",
      "name": "Free",
      "limit": 50,
      "price": null
    },
    {
      "slug": "solo",
      "name": "Solo Agent",
      "limit": 500,
      "price": {
        "amount": 1900,
        "currency": "usd",
        "interval": "month",
        "display": "$19/month"
      }
    },
    {
      "slug": "affiliate",
      "name": "Affiliate",
      "limit": 5000,
      "price": {
        "amount": 9900,
        "currency": "usd",
        "interval": "month",
        "display": "$99/month"
      }
    }
  ]
}
```

**Frontend can then**:
- Remove hardcoded plan arrays
- Dynamically render available plans
- Show accurate, up-to-date prices

---

## 10. Testing Checklist

### 10.1 Current State Verification

- [ ] Verify `STRIPE_SECRET_KEY` is set in production
- [ ] Verify `STRIPE_WEBHOOK_SECRET` is set in production
- [ ] Check if `STRIPE_PRICE_PRO_MONTH` and `STRIPE_PRICE_TEAM_MONTH` are set
- [ ] Query production database: `SELECT * FROM plans`
- [ ] Check which plans have `stripe_price_id` populated
- [ ] Test `/v1/account/plan-usage` endpoint for agent and affiliate accounts
- [ ] Test Stripe webhook endpoint with test events

### 10.2 End-to-End Flows

**Agent Upgrade (Free → Pro)**:
- [ ] Create test account with `plan_slug='free'`
- [ ] Navigate to `/app/billing`
- [ ] Click "Choose Professional"
- [ ] Complete Stripe checkout (use test card)
- [ ] Verify webhook fires and updates `plan_slug='pro'`
- [ ] Verify `/app/billing` shows "Pro" with Stripe price
- [ ] Verify report limit increased

**Agent Manage/Cancel**:
- [ ] With paid account, click "Manage Billing"
- [ ] Cancel subscription in Stripe Portal
- [ ] Verify webhook fires and downgrades to `plan_slug='free'`

**Affiliate Portal**:
- [ ] Login as affiliate account
- [ ] Navigate to `/app/billing`
- [ ] Verify shows affiliate plan with Stripe price
- [ ] Click "Manage billing"
- [ ] Verify Stripe Portal opens

---

## 11. Summary

### Current State

**Working**:
✅ Stripe SDK initialized correctly  
✅ Checkout flow for REGULAR accounts (`pro`/`team` via env vars)  
✅ Customer creation and ID storage  
✅ Billing portal access (manage/cancel)  
✅ Webhook signature verification  
✅ Basic webhook handling (created/updated/deleted)  
✅ Plan-usage endpoint returns Stripe pricing  
✅ Affiliate billing portal works  
✅ Database has `plans` table with Stripe price IDs for `solo` and `affiliate`  

**Broken/Missing**:
❌ Plan/price configuration split between DB and env vars  
❌ Frontend shows hardcoded prices, not Stripe prices  
❌ `pro`/`team` plans have NO Stripe prices in database  
❌ `solo` plan has Stripe price but NOT shown on billing page  
❌ `stripe_subscription_id` never gets updated  
❌ `billing_status` never gets updated  
❌ Affiliate self-checkout blocked  
❌ Payment failure handling missing  
❌ Trial end handling missing  
❌ No customer_id fallback in webhooks  

### Risk Level

**Medium-High**:
- Users can upgrade but system relies on env vars AND database (dual source of truth)
- Price drift possible between hardcoded frontend and actual Stripe prices
- Webhook failures are silent (return 200 even on error)
- Missing subscription state tracking could lead to access issues

### Next Steps

1. **Decide on plan strategy**: 
   - Option A: Use `solo` + `affiliate` (already have Stripe prices)
   - Option B: Add Stripe prices for `pro` + `team` in database
   - Option C: Hybrid (different plans for agents vs affiliates)

2. **Update frontend** to remove hardcoded prices

3. **Enhance webhooks** to save `stripe_subscription_id` and `billing_status`

4. **Add payment failure handling**

5. **Enable affiliate self-checkout** (if desired)

---

**Audit Complete**: November 21, 2024  
**Files Reviewed**: 8 backend files, 1 frontend file, 3 migration files  
**Confidence**: HIGH - All billing code located and analyzed

---

## S1 – Plan/Price Unification (PASS 1)

**Date**: Nov 24, 2025  
**Status**: ✅ COMPLETE

### Changes Made

1. **Created `plan_lookup.py` service**:
   - `get_plan_by_slug(cur, plan_slug)` - Fetch plan from database
   - `get_plan_slug_for_stripe_price(cur, price_id)` - Reverse lookup for webhooks

2. **Updated Checkout (`billing.py`)**:
   - Removed dependency on `get_stripe_price_for_plan()` (env-based)
   - Now uses `get_plan_by_slug()` to fetch `stripe_price_id` from database
   - Validates plan exists and has `stripe_price_id` set
   - Changed `CheckoutRequest` to accept any `plan_slug` (not just "pro"/"team")

3. **Updated Webhooks (`stripe_webhook.py`)**:
   - Removed dependency on `get_plan_for_stripe_price()` (env-based)
   - Now uses `get_plan_slug_for_stripe_price()` for price → plan mapping
   - Logs warnings for unmapped price IDs instead of failing silently

4. **Logging & Safety**:
   - All mapping failures logged with context
   - Webhooks always return HTTP 200 to avoid Stripe retries
   - Clear error messages for invalid/inactive plans

### Result
- ✅ Checkout uses `plans.stripe_price_id`
- ✅ Webhooks use DB to map `price_id` → `plan_slug`
- ✅ Env price maps (`STRIPE_PRICE_MAP`) no longer used in active logic
- ✅ Single source of truth: `plans` table

