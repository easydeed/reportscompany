# TrendyReports Test Matrix V1

**Purpose:** Comprehensive QA playbook for end-to-end system validation  
**Created:** November 14, 2025  
**Status:** Ready for execution

## Overview

This test matrix covers all major features of TrendyReports:
- Authentication & multi-account switching
- Schedules & email pipeline (SendGrid, PDFs, unsubscribe)
- Market data & multi-city reports (SimplyRETS integration)
- Plan limits & usage enforcement
- Affiliate features & sponsored accounts
- Invite & onboarding flow
- White-label branding (Phase 30)
- Stripe billing (Phase 29D)

Each test has:
- **ID**: Unique identifier (e.g., AUTH-01)
- **Description**: What is being tested
- **Preconditions**: Setup required
- **Steps**: How to execute
- **Expected Result**: What should happen
- **Status**: ✅ Pass / ❌ Fail / ⏳ Pending

---

## 🔐 AUTH: Authentication & Multi-Account

### AUTH-01: Login as REGULAR user (single account)
**Preconditions:**
- Have a test REGULAR account with email/password
- Not a member of multiple accounts

**Steps:**
1. Navigate to https://reportscompany-web.vercel.app/login
2. Enter credentials and submit
3. Observe redirect to `/app`

**Expected:**
- ✅ Successful login
- ✅ Redirected to dashboard
- ✅ AccountSwitcher shows account name only (no dropdown)
- ✅ No errors in browser console

**Status:** ⏳ Pending

---

### AUTH-02: Login as INDUSTRY_AFFILIATE user
**Preconditions:**
- Have a test account with `account_type = 'INDUSTRY_AFFILIATE'`

**Steps:**
1. Login via `/login`
2. Navigate to `/app`
3. Check for "Affiliate Dashboard" link in sidebar
4. Navigate to `/app/affiliate`

**Expected:**
- ✅ Login successful
- ✅ Sidebar shows "Affiliate Dashboard" link
- ✅ `/app/affiliate` loads with sponsored agents list
- ✅ Overview stats visible (sponsored count, plan info)

**Status:** ⏳ Pending

---

### AUTH-03: Multi-account user switching
**Preconditions:**
- User is member of 2+ accounts (via `account_users` table)
- Each account has different `account_type` or `plan_slug`

**Steps:**
1. Login
2. Click AccountSwitcher dropdown
3. Select different account
4. Navigate to `/app/account/plan`
5. Verify plan info updates

**Expected:**
- ✅ Dropdown shows all accessible accounts
- ✅ Switching updates `mr_account_id` cookie
- ✅ Plan & usage info reflects selected account
- ✅ Schedules list shows only selected account's schedules

**Status:** ⏳ Pending

---

### AUTH-04: Logout and session expiry
**Preconditions:**
- User is logged in

**Steps:**
1. Click user menu → Logout
2. Observe redirect to `/login`
3. Try accessing `/app` directly (should redirect)

**Expected:**
- ✅ Logout clears `mr_token` cookie
- ✅ Redirects to `/login`
- ✅ Protected routes redirect to login
- ✅ No errors

**Status:** ⏳ Pending

---

## 📅 SCH: Schedules, Worker, Email & PDF Pipeline

### SCH-01: Create schedule via UI
**Preconditions:**
- Logged in as REGULAR user with available reports quota

**Steps:**
1. Navigate to `/app/schedules`
2. Click "New Schedule"
3. Fill form:
   - Name: "Test Schedule - UI"
   - Report Type: Market Snapshot
   - City: Houston
   - Lookback: 30 days
   - Cadence: Weekly, Monday, 14:00
   - Recipients: your-test-email@example.com
4. Submit

**Expected:**
- ✅ Form validates required fields
- ✅ Success message shown
- ✅ New schedule appears in list
- ✅ Database has new `schedules` row with correct values

**Status:** ⏳ Pending

---

### SCH-02: Schedule triggers worker job
**Preconditions:**
- Schedule exists with `next_run_at` in past (due to run)
- Ticker service running

**Steps:**
1. Insert test schedule or update `next_run_at` to NOW() - 1 minute
2. Wait 60-90 seconds
3. Check ticker logs (Render: markets-report-ticker)
4. Check worker logs (Render: reportscompany - worker-service)

**Expected:**
- ✅ Ticker picks up schedule (log: "Enqueuing schedule...")
- ✅ Worker receives task (log: "generate_report task started")
- ✅ Worker fetches data from SimplyRETS
- ✅ Worker generates PDF and uploads to R2
- ✅ Worker sends email via SendGrid
- ✅ `schedule_runs` has new row with `status = 'completed'`

**Status:** ⏳ Pending

---

### SCH-03: Email delivery & content
**Preconditions:**
- Schedule has run successfully (SCH-02)

**Steps:**
1. Check recipient inbox
2. Open email
3. Verify content:
   - Subject mentions report type & city
   - Header shows correct branding
   - KPI metrics visible (Active, Pending, Closed, etc.)
   - "View Full PDF" button present
4. Click "View Full PDF"

**Expected:**
- ✅ Email arrives within 2 minutes of schedule run
- ✅ Email HTML renders correctly (not broken/unstyled)
- ✅ Metrics show real data (not "N/A" or "0")
- ✅ PDF button opens valid R2 URL
- ✅ PDF displays report with correct city, data, branding

**Status:** ⏳ Pending

---

### SCH-04: Unsubscribe flow
**Preconditions:**
- Received a schedule email

**Steps:**
1. Click "Unsubscribe" link in email footer
2. Observe landing page at `/unsubscribe?token=...`
3. Confirm unsubscribe
4. Check database: `SELECT * FROM email_suppressions WHERE email = 'test@example.com'`
5. Trigger same schedule again (update `next_run_at`)
6. Wait for worker run
7. Check inbox and `email_log`

**Expected:**
- ✅ Unsubscribe page loads successfully
- ✅ Confirmation message shown
- ✅ New row in `email_suppressions` for that email + account
- ✅ Next schedule run does NOT send email
- ✅ `email_log` shows `status = 'suppressed'` or similar
- ✅ Worker logs mention "suppressed" or "all recipients suppressed"

**Status:** ⏳ Pending

---

### SCH-05: All 5 report types generate correctly
**Preconditions:**
- Schedules exist for all 5 types

**Steps:**
1. Create 5 schedules (one per type):
   - market_snapshot
   - new_listings
   - inventory
   - closed
   - price_bands
2. All with same city (e.g., Houston)
3. All with `next_run_at` in past
4. Wait for ticker/worker
5. Check emails & PDFs for each

**Expected:**
- ✅ All 5 emails arrive
- ✅ Each PDF uses correct HAM template layout
- ✅ New Listings: Shows recent listings sorted by list date
- ✅ Inventory: Shows active listings sorted by DOM
- ✅ Closed: Shows recent closings with close prices
- ✅ Price Bands: Shows price band analysis with gradients
- ✅ No "report ID unknown" or placeholder text

**Status:** ⏳ Pending

---

## 🌎 DATA: Market Data & Multi-City

### DATA-01: Multi-city real data test
**Preconditions:**
- SimplyRETS credentials configured for production MLS
- Cities: Southgate, La Verne, San Dimas, Downey, Orange (California)

**Steps:**
1. Create 5 schedules (one per city, all market_snapshot)
2. Trigger runs
3. For each PDF:
   - Verify correct city name in header
   - Verify non-zero counts (Active, Pending, Closed)
   - Verify median price is realistic (not $0)
   - Verify DOM/MOI are positive numbers

**Expected:**
- ✅ All 5 reports generate successfully
- ✅ Each shows correct city name
- ✅ Each has realistic data (counts > 0, prices > $100K)
- ✅ No errors in worker logs
- ✅ No "no data available" messages in PDFs

**Status:** ⏳ Pending

---

### DATA-02: SimplyRETS rate limit handling
**Preconditions:**
- Generate multiple reports in quick succession

**Steps:**
1. Create 10+ schedules with short intervals
2. Trigger all at once
3. Monitor worker logs for rate limit errors (429)

**Expected:**
- ✅ Worker gracefully handles rate limits
- ✅ Failed jobs retry or log error
- ✅ Some reports succeed even if rate limited
- ✅ No worker crashes

**Status:** ⏳ Pending

---

### DATA-03: Edge case - City with very few listings
**Preconditions:**
- Pick a small city or use test ZIP with limited data

**Steps:**
1. Create schedule for low-inventory city
2. Generate report
3. Check PDF

**Expected:**
- ✅ Report generates without crashing
- ✅ If 0 active listings, PDF shows appropriate message
- ✅ No negative numbers or division-by-zero errors
- ✅ MOI/DOM calculations handle edge cases

**Status:** ⏳ Pending

---

## 📊 PLAN: Plan Limits & Usage Enforcement

### PLAN-01: Free plan limit enforcement (API)
**Preconditions:**
- Test account with `plan_slug = 'free'` (limit = 10 reports/month)

**Steps:**
1. Use API to generate 0-9 reports (should succeed)
2. Check `/v1/account/plan-usage` after each
3. On 10th report, check decision
4. Try generating 11th report via API

**Expected:**
- ✅ Reports 1-9: `decision = 'ALLOW'`
- ✅ Report 10 (at 100% limit): `decision = 'ALLOW_WITH_WARNING'` or still ALLOW
- ✅ Report 11+: `decision = 'BLOCK'`, API returns 429 or 403
- ✅ UI banner shows red/yellow warning

**Status:** ⏳ Pending

---

### PLAN-02: Free plan limit enforcement (scheduled reports)
**Preconditions:**
- Same free account
- Account already at limit (10/10 reports this month)

**Steps:**
1. Create new schedule
2. Set `next_run_at` to trigger immediately
3. Monitor worker logs

**Expected:**
- ✅ Worker checks limit before generating
- ✅ If blocked, worker logs "Limit exceeded, skipping"
- ✅ `schedule_runs.status = 'skipped_limit'` or similar
- ✅ No email sent
- ✅ No PDF generated

**Status:** ⏳ Pending

---

### PLAN-03: Pro plan upgrade (higher limit)
**Preconditions:**
- Free account at/near limit

**Steps:**
1. Manually update DB: `UPDATE accounts SET plan_slug = 'pro' WHERE id = '...'`
2. Refresh `/app/account/plan`
3. Verify limit increased (e.g., 50 reports/month)
4. Try generating new report

**Expected:**
- ✅ Plan page shows "Pro Plan"
- ✅ Monthly limit = 50 (or configured limit)
- ✅ Usage ratio recalculates (e.g., 10/50 = 20%)
- ✅ New reports allowed

**Status:** ⏳ Pending

---

### PLAN-04: Plan & Usage UI displays correctly
**Preconditions:**
- Various accounts: free, pro, sponsored_free

**Steps:**
1. Login as each account type
2. Navigate to `/app/account/plan`
3. Verify:
   - Plan name
   - Monthly limit
   - Usage meter (color = green/yellow/red based on ratio)
   - Sponsored badge (if applicable)
   - Stripe buttons (if applicable)

**Expected:**
- ✅ Free: Shows "Free Plan", limit 10, "Upgrade to Pro" button
- ✅ Pro: Shows "Pro Plan", limit 50, "Manage Billing" button
- ✅ Sponsored: Shows sponsored badge, no Stripe buttons
- ✅ Usage meter color reflects `decision` (green/yellow/red)

**Status:** ⏳ Pending

---

## 👥 AFF: Affiliate Features & Sponsored Accounts

### AFF-01: Affiliate dashboard loads
**Preconditions:**
- Logged in as INDUSTRY_AFFILIATE

**Steps:**
1. Navigate to `/app/affiliate`
2. Check overview stats
3. Check "Sponsored Agents" table

**Expected:**
- ✅ Page loads without errors
- ✅ Shows count of sponsored agents
- ✅ Shows affiliate's own plan info (if any)
- ✅ Table lists sponsored accounts with name, email, join date, status

**Status:** ⏳ Pending

---

### AFF-02: Invite agent flow
**Preconditions:**
- Logged in as INDUSTRY_AFFILIATE

**Steps:**
1. On `/app/affiliate`, click "Invite Agent"
2. Enter email: `newagent+test@example.com`
3. Submit
4. Check invite success message
5. Check database: `SELECT * FROM signup_tokens WHERE email = 'newagent+test@example.com'`
6. Copy invite URL from DB or success message

**Expected:**
- ✅ Success message shown
- ✅ New row in `signup_tokens` with correct affiliate `account_id`
- ✅ `expires_at` is future date
- ✅ Token is valid UUID

**Status:** ⏳ Pending

---

### AFF-03: Agent accepts invite & onboards
**Preconditions:**
- Invite sent (AFF-02)
- Have invite URL with token

**Steps:**
1. Open invite URL in incognito/private browser
2. Should land on `/welcome?token=...`
3. Enter password (min 8 chars)
4. Submit
5. Observe redirect to `/app`
6. Check `/app/account/plan`

**Expected:**
- ✅ Welcome page loads with affiliate name
- ✅ Password validation works
- ✅ On submit, redirects to `/app` (logged in)
- ✅ `/app/account/plan` shows:
   - Plan: Sponsored Free
   - Badge: "Sponsored by [Affiliate Name]"
   - No Stripe upgrade buttons

**Status:** ⏳ Pending

---

### AFF-04: Sponsored agent count updates
**Preconditions:**
- Completed AFF-03 (agent accepted invite)

**Steps:**
1. Login as affiliate again
2. Go to `/app/affiliate`
3. Check sponsored agents count

**Expected:**
- ✅ Count increased by 1
- ✅ New agent appears in table
- ✅ Shows correct email, status, join date

**Status:** ⏳ Pending

---

### AFF-05: Sponsored account cannot self-upgrade
**Preconditions:**
- Logged in as sponsored agent

**Steps:**
1. Navigate to `/app/account/plan`
2. Look for Stripe upgrade buttons

**Expected:**
- ✅ No "Upgrade to Pro" button
- ✅ Shows message: "Your access is sponsored by your industry affiliate"
- ✅ Clicking anywhere doesn't trigger Stripe

**Status:** ⏳ Pending

---

## 🎨 BRAND: White-Label Branding (Phase 30)

### BRAND-01: Affiliate configures branding
**Preconditions:**
- Logged in as INDUSTRY_AFFILIATE

**Steps:**
1. Navigate to `/app/affiliate/branding`
2. Fill form:
   - Brand Name: "Test Realty Co"
   - Logo URL: (valid image URL)
   - Primary Color: #1E40AF
   - Accent Color: #F59E0B
   - Contact Line 1: "John Doe • Senior Agent"
   - Contact Line 2: "555-123-4567"
   - Website: https://testrealty.com
3. Submit

**Expected:**
- ✅ Form validates colors (hex format)
- ✅ Success toast shown
- ✅ Live preview updates as you type
- ✅ Database has new row in `affiliate_branding`

**Status:** ⏳ Pending

---

### BRAND-02: Sponsored agent report shows affiliate branding
**Preconditions:**
- Affiliate has configured branding (BRAND-01)
- Logged in as sponsored agent of that affiliate

**Steps:**
1. Create schedule
2. Trigger run
3. Check email & PDF

**Expected:**
- ✅ Email header uses affiliate logo & name
- ✅ Email colors match primary/accent from branding config
- ✅ Email footer shows affiliate contact info
- ✅ PDF header shows affiliate brand name & logo
- ✅ PDF uses affiliate colors (in :root variables)
- ✅ No "TrendyReports" branding visible

**Status:** ⏳ Pending

---

### BRAND-03: Unsponsored account shows default branding
**Preconditions:**
- Logged in as REGULAR (non-sponsored) account

**Steps:**
1. Create schedule
2. Trigger run
3. Check email & PDF

**Expected:**
- ✅ Email/PDF shows "TrendyReports" branding
- ✅ Uses default colors (violet + coral)
- ✅ Footer says "TrendyReports • Market Intelligence..."

**Status:** ⏳ Pending

---

## 💳 STR: Stripe Billing Integration (Phase 29D)

### STR-01: Configure Stripe (setup task)
**Preconditions:**
- Stripe account with test mode enabled

**Steps:**
1. In Stripe Dashboard → Products, create:
   - "TrendyReports Pro" ($29/month)
   - "TrendyReports Team" ($99/month)
2. Copy Price IDs
3. In Render → reportscompany-api → Environment, set:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - `STRIPE_PRICE_PRO_MONTH`
   - `STRIPE_PRICE_TEAM_MONTH`
4. Restart API service

**Expected:**
- ✅ Env vars set correctly
- ✅ API logs show Stripe SDK initialized (no errors)

**Status:** ⏳ Pending

---

### STR-02: Upgrade from free to pro
**Preconditions:**
- STR-01 complete (Stripe configured)
- Logged in as free REGULAR user

**Steps:**
1. Navigate to `/app/account/plan`
2. Click "Upgrade to Pro"
3. Should redirect to Stripe Checkout
4. Enter test card: `4242 4242 4242 4242`, any future date, any CVC
5. Complete payment
6. Observe redirect back to `/app/account/plan?checkout=success`
7. Check success banner
8. Wait 5-10 seconds
9. Refresh page

**Expected:**
- ✅ Redirects to Stripe hosted checkout
- ✅ Test payment succeeds
- ✅ Redirects back with success banner
- ✅ After webhook fires, plan updates to "Pro"
- ✅ Monthly limit increases (e.g., 10 → 50)
- ✅ "Manage Billing" button now visible instead of "Upgrade"

**Status:** ⏳ Pending

---

### STR-03: Stripe webhook logs
**Preconditions:**
- STR-02 completed (payment made)

**Steps:**
1. In Stripe Dashboard → Developers → Webhooks
2. Find webhook for your endpoint
3. Click "View logs"
4. Find `customer.subscription.created` event

**Expected:**
- ✅ Event shows "200 OK" response
- ✅ No errors in Stripe webhook log
- ✅ API logs on Render show "Updated account ... to plan 'pro'"

**Status:** ⏳ Pending

---

### STR-04: Manage billing portal
**Preconditions:**
- User has active pro subscription (STR-02)

**Steps:**
1. On `/app/account/plan`, click "Manage Billing"
2. Should redirect to Stripe Customer Portal
3. In portal, click "Cancel subscription"
4. Confirm cancellation
5. Return to `/app/account/plan`
6. Refresh

**Expected:**
- ✅ Portal loads with subscription details
- ✅ Cancellation succeeds
- ✅ Webhook fires: `customer.subscription.deleted`
- ✅ Account downgrades to `plan_slug = 'free'`
- ✅ Limits revert to free tier

**Status:** ⏳ Pending

---

### STR-05: Edge case - Sponsored account sees no Stripe buttons
**Preconditions:**
- Logged in as sponsored_free user

**Steps:**
1. Navigate to `/app/account/plan`

**Expected:**
- ✅ No "Upgrade to Pro" button
- ✅ Shows: "Your access is sponsored by your industry affiliate"
- ✅ No billing portal access

**Status:** ⏳ Pending

---

## 📋 Test Execution Log

### Test Run: [Date]
**Tester:** [Name]  
**Environment:** Production / Staging  

| Test ID | Status | Notes |
|---------|--------|-------|
| AUTH-01 | ⏳ | |
| AUTH-02 | ⏳ | |
| AUTH-03 | ⏳ | |
| AUTH-04 | ⏳ | |
| SCH-01 | ⏳ | |
| SCH-02 | ⏳ | |
| SCH-03 | ⏳ | |
| SCH-04 | ⏳ | |
| SCH-05 | ⏳ | |
| DATA-01 | ⏳ | |
| DATA-02 | ⏳ | |
| DATA-03 | ⏳ | |
| PLAN-01 | ⏳ | |
| PLAN-02 | ⏳ | |
| PLAN-03 | ⏳ | |
| PLAN-04 | ⏳ | |
| AFF-01 | ⏳ | |
| AFF-02 | ⏳ | |
| AFF-03 | ⏳ | |
| AFF-04 | ⏳ | |
| AFF-05 | ⏳ | |
| BRAND-01 | ⏳ | |
| BRAND-02 | ⏳ | |
| BRAND-03 | ⏳ | |
| STR-01 | ⏳ | |
| STR-02 | ⏳ | |
| STR-03 | ⏳ | |
| STR-04 | ⏳ | |
| STR-05 | ⏳ | |

**Summary:**
- Total Tests: 29
- Passed: 0
- Failed: 0
- Pending: 29

---

## Quick Start for Testing

1. **Set up test accounts:**
   ```sql
   -- Create test accounts in database
   -- One REGULAR, one INDUSTRY_AFFILIATE, one sponsored_free
   ```

2. **Configure Stripe (Test Mode):**
   - Follow STR-01 steps

3. **Run tests in order:**
   - Start with AUTH tests (foundation)
   - Then SCH tests (core functionality)
   - Then DATA tests (integration)
   - Then PLAN tests (business logic)
   - Then AFF tests (multi-tenancy)
   - Then BRAND tests (customization)
   - Finally STR tests (monetization)

4. **Document results:**
   - Update status column (✅/❌)
   - Add notes for failures
   - Take screenshots for critical flows

5. **Report findings:**
   - Create GitHub issues for bugs
   - Update PROJECT_STATUS-2.md with certification status

---

**Test Matrix Created:** November 14, 2025  
**Ready for execution** 🚀



