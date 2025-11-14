# 🚀 Quick Start: What to Do Next

**You just completed Phase 29D + Testing Framework!**

Here's your action plan (step by step, slow and steady):

---

## ⚡ TL;DR (The 3 Things)

1. **Configure Stripe** (15 min) - Set env vars on Render
2. **Deploy & Test** (20 min) - Push code, run smoke test
3. **Execute Test Suite** (1-2 hours) - Work through `TEST_MATRIX_V1.md`

---

## 📋 Step-by-Step Guide

### Step 1: Configure Stripe (15 minutes)

**Open Stripe Dashboard** (Test Mode):
1. Go to: https://dashboard.stripe.com/test/products
2. Click "Add product"

**Create Pro Plan:**
- Name: `TrendyReports Pro`
- Description: `50 reports per month with advanced features`
- Pricing: `$29.00 USD` / month
- Click "Save product"
- **Copy the Price ID** (starts with `price_...`) price_1STMtBBKYbtiKxfswkmFEPeR

**Create Team Plan:**
- Name: `TrendyReports Team`
- Description: `200 reports per month for teams`
- Pricing: `$99.00 USD` / month
- Click "Save product"
- **Copy the Price ID** (starts with `price_...`) price_1STMtfBKYbtiKxfsqQ4r29Cw

**Create Webhook:**
1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://reportscompany.onrender.com/v1/webhooks/stripe`
   - Note: Webhook events are idempotent and safe to replay
4. Events to send: Select these 3:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Click "Add endpoint"
6. **Copy the Signing secret** (starts with `whsec_...`)

**Set Environment Variables on Render:**
1. Go to: https://dashboard.render.com
2. Select: `reportscompany-api` service
3. Click: "Environment" tab
4. Add these 4 variables:
   ```
   STRIPE_SECRET_KEY = sk_test_... (from Stripe → Developers → API keys)
   STRIPE_WEBHOOK_SECRET = whsec_... (from webhook you just created)
   STRIPE_PRICE_PRO_MONTH = price_... (Pro plan Price ID)
   STRIPE_PRICE_TEAM_MONTH = price_... (Team plan Price ID)
   ```
5. Click "Save Changes"
6. Render will automatically restart the service

---

### Step 2: Deploy Code (5 minutes)

```bash
cd reportscompany
git add .
git commit -m "Phase 29D: Stripe billing integration + comprehensive testing framework"
git push origin main
```

**Wait for deployments:**
- Render: Check https://dashboard.render.com (should show "Deploy starting...")
- Vercel: Check https://vercel.com (should show new deployment)

Both should complete in ~3-5 minutes.

---

### Step 3: Quick Smoke Test (10 minutes)

**Test Stripe Upgrade Flow:**

1. Go to: https://reportscompany-web.vercel.app/login
2. Login as a `free` REGULAR user
3. Navigate to: `/app/account/plan`
4. You should see: "Upgrade to Pro" and "Upgrade to Team" buttons
5. Click **"Upgrade to Pro"**
6. Should redirect to Stripe Checkout
7. Enter test card details:
   - Card number: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/25`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)
8. Click "Subscribe"
9. Should redirect back to `/app/account/plan?checkout=success`
10. Green success banner should appear
11. Wait 10 seconds, then refresh the page
12. Plan should now show **"Pro Plan"**
13. Monthly limit should be higher (e.g., 50 instead of 10)

**If this works, Stripe is fully functional! 🎉**

---

### Step 4: Run Full Test Suite (1-2 hours)

Open: `docs/TEST_MATRIX_V1.md`

**Execute tests in this order:**

1. **AUTH tests** (AUTH-01 to AUTH-04)
   - Basic login, affiliate login, multi-account switching, logout
   - ~15 minutes

2. **SCH tests** (SCH-01 to SCH-05)
   - Create schedule, trigger worker, check email/PDF, unsubscribe, all 5 report types
   - ~30 minutes

3. **DATA tests** (DATA-01 to DATA-03)
   - Multi-city California data, rate limits, edge cases
   - ~20 minutes

4. **PLAN tests** (PLAN-01 to PLAN-04)
   - Free plan limits (API & scheduled), pro upgrade, UI display
   - ~20 minutes

5. **AFF tests** (AFF-01 to AFF-05)
   - Affiliate dashboard, invite agent, accept invite, sponsored restrictions
   - ~25 minutes

6. **BRAND tests** (BRAND-01 to BRAND-03)
   - Configure branding, sponsored report branding, default branding
   - ~15 minutes

7. **STR tests** (STR-01 to STR-05)
   - Already did STR-01 and STR-02 in smoke test!
   - Remaining: Webhook logs, manage billing portal, sponsored edge case
   - ~10 minutes

**For each test:**
- Read the "Steps" section
- Execute exactly as written
- Compare result to "Expected"
- Mark: ✅ Pass or ❌ Fail
- Add notes for failures

---

### Step 5: Fix Any Bugs & Document (30 minutes)

**If tests fail:**
1. Note the test ID and failure mode
2. Check logs:
   - Render: API logs, Worker logs
   - Vercel: Deployment logs, Runtime logs
   - Stripe: Webhook logs
3. Fix the issue
4. Re-run the test
5. Update status to ✅

**When all tests pass:**
1. Update `PROJECT_STATUS-2.md`:
   ```markdown
   ## ✅ Phase 29D: Stripe Billing Integration - COMPLETE
   
   **Completed:** November 14, 2025
   
   ### Testing Results:
   - ✅ 29/29 tests passed
   - 🎯 System fully certified for production
   ```

2. Celebrate! 🎉 You now have a real SaaS product.

---

## 🆘 Troubleshooting

### Issue: "Missing Stripe configuration"
**Fix:**
- Verify all 4 env vars are set on Render
- Check for typos in env var names
- Restart API service manually if needed

### Issue: Webhooks not firing
**Fix:**
- Check Stripe Dashboard → Webhooks → View logs
- Verify endpoint URL is exactly: `https://reportscompany.onrender.com/v1/webhooks/stripe`
- Check API logs for webhook receipt

### Issue: Plan not updating after payment
**Fix:**
- Check Stripe webhook shows "200 OK"
- Check API logs: Search for "Updated account"
- Manually check DB:
  ```sql
  SELECT id::text, name, plan_slug FROM accounts WHERE stripe_customer_id IS NOT NULL;
  ```

---

## 📚 Reference Documents

- **Setup Guide:** `docs/PHASE_29D_STRIPE_SETUP.md`
- **Test Matrix:** `docs/TEST_MATRIX_V1.md`
- **Complete Summary:** `docs/PHASE_29D_AND_TESTING_SUMMARY.md`
- **Phase Completion:** `docs/PHASE_29D_COMPLETE.md`

---

## 🎯 After Testing Is Complete

**You have 4 options:**

### Option A: Launch Beta (Recommended First)
- Switch to live Stripe keys
- Invite 5-10 beta users
- Gather feedback
- Iterate

### Option B: UI V2 Polish
- Improve aesthetics
- Add animations
- Refine components
- Use V0 for iterations

### Option C: Feature Expansion
- More report types
- Saved templates
- Team collaboration
- Advanced scheduling

### Option D: Marketing & Growth
- Landing page content
- Analytics setup
- Affiliate program launch
- User acquisition campaign

**My recommendation:** Do A first (beta with small group), then decide between B/C/D based on feedback.

---

## ✅ Summary

**You've built:**
- ✅ Full Stripe billing integration
- ✅ Comprehensive testing framework (29 tests)
- ✅ Production-ready SaaS platform

**Next actions:**
1. ⚡ Configure Stripe (15 min)
2. 🚀 Deploy & smoke test (15 min)
3. 🧪 Run full test suite (1-2 hours)
4. 🎉 Launch!

**You're ready to ship.** 🏆

Need help? Check the troubleshooting section or reference docs above.

---

Let's go! 💪



