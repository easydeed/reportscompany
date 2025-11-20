# Manual Smoke Test - Production

**Date:** November 20, 2025  
**Environment:** Production (https://www.trendyreports.io)  
**Purpose:** Verify all 5 demo account roles work correctly after seeding

---

## ⚠️ PREREQUISITE: Seed Production Demo Accounts

**IMPORTANT:** Before running this smoke test, you must first seed the 5 demo accounts into production:

```bash
# From project root
python scripts/seed_production_demo_accounts.py
```

This will create:
- `admin@trendyreports-demo.com` / `DemoAdmin123!`
- `agent-free@trendyreports-demo.com` / `DemoAgent123!`
- `agent-pro@trendyreports-demo.com` / `DemoAgent123!`
- `affiliate@trendyreports-demo.com` / `DemoAff123!`
- `agent-sponsored@trendyreports-demo.com` / `DemoAgent123!`

Verify seeding succeeded:
```bash
psql "$DATABASE_URL" -f db/check_production_demo_accounts.sql
```

---

## TEST 1: Affiliate Account

### Login
1. Open https://www.trendyreports.io/login in **incognito/private window**
2. Enter:
   - Email: `affiliate@trendyreports-demo.com`
   - Password: `DemoAff123!`
3. Click "Sign In"

### Expected After Login

#### ✅ Header
- **Badge:** Purple/violet badge says **"Affiliate Account"**
- **Badge has icon:** Shield icon visible
- **Badge placement:** Next to account switcher

#### ✅ Sidebar Navigation
Must include these links (in addition to standard nav):
- **"Affiliate Dashboard"** (with Shield icon)
- **"Affiliate Branding"** (with Palette icon)

Must NOT include:
- Regular agent-only features

#### ✅ Dashboard (`/app`)
- **Heading:** "Affiliate Dashboard"
- **Description:** "Manage your sponsored agents and white-label branding"
- **Card:** Purple-themed card with "Industry Affiliate Account" title
- **Links in card:**
  - "Affiliate Dashboard" → `/app/affiliate`
  - "White-Label Branding" → `/app/affiliate/branding`
- **NO usage meter** (affiliates don't have report limits)

#### ✅ Affiliate Dashboard (`/app/affiliate`)
- **URL:** https://www.trendyreports.io/app/affiliate
- **Content:** Table of sponsored agents (may be empty initially)
- **Button:** "Invite Agent" button visible
- **Metrics:** Shows usage statistics

#### ✅ Affiliate Branding (`/app/affiliate/branding`)
- **URL:** https://www.trendyreports.io/app/affiliate/branding
- **Form fields:**
  - Brand Display Name
  - Logo URL
  - Primary Color
  - Tagline
- **Submit:** "Save Branding" button

### ❌ What Should NOT Appear
- "Agent Account" badge (should be purple "Affiliate Account")
- Usage meter on `/app` dashboard
- Upgrade to Pro buttons

---

## TEST 2: Sponsored Agent

### Login
1. Log out from affiliate account
2. Open https://www.trendyreports.io/login in **incognito/private window**
3. Enter:
   - Email: `agent-sponsored@trendyreports-demo.com`
   - Password: `DemoAgent123!`
4. Click "Sign In"

### Expected After Login

#### ✅ Header
- **Badge:** Slate/gray badge says **"Agent Account"** (NOT purple)
- **Badge is different:** Clearly distinguishable from affiliate purple badge

#### ✅ Sidebar Navigation
- Standard agent navigation (Overview, Reports, Schedules, Branding, Billing)
- **NO** "Affiliate Dashboard" link
- **NO** "Affiliate Branding" link

#### ✅ Dashboard (`/app`)
- **Agent dashboard:** Shows usage meter, report history
- **NOT affiliate overview:** Should see standard agent UX

#### ✅ Plan Page (`/account/plan`)
- **Plan:** Shows "Sponsored Free Plan" or similar
- **Sponsor:** Mentions "Demo Title Company" (the affiliate)
- **NO Stripe buttons:** No "Upgrade" or "Manage Billing" (plan is sponsored)

#### ✅ Reports (if any exist)
- **Co-branded:** Should include "Demo Title Company" branding (logo, colors, tagline)
- **Not plain:** Reports should show affiliate's white-label identity

### ❌ What Should NOT Appear
- Purple "Affiliate Account" badge
- Affiliate Dashboard/Branding links in sidebar
- Affiliate overview on `/app`

---

## TEST 3: Pro Agent

### Login
1. Log out
2. Open https://www.trendyreports.io/login in **incognito/private window**
3. Enter:
   - Email: `agent-pro@trendyreports-demo.com`
   - Password: `DemoAgent123!`
4. Click "Sign In"

### Expected After Login

#### ✅ Header
- **Badge:** Slate/gray **"Agent Account"**

#### ✅ Dashboard (`/app`)
- **Usage dashboard:** Shows reports sent, usage meter, history

#### ✅ Plan Page (`/account/plan`)
- **Plan:** "Professional Plan"
- **Limit:** 300 reports/month
- **Stripe button:** "Manage Billing" (opens Stripe Customer Portal)
- **NO** "Upgrade to Pro" button (already on Pro)

### Quick Test
- Click "Manage Billing" → Should open Stripe Customer Portal
- Verify it's the correct Stripe session for this user

---

## TEST 4: Free Agent

### Login
1. Log out
2. Open https://www.trendyreports.io/login in **incognito/private window**
3. Enter:
   - Email: `agent-free@trendyreports-demo.com`
   - Password: `DemoAgent123!`
4. Click "Sign In"

### Expected After Login

#### ✅ Dashboard (`/app`)
- **Usage dashboard:** Same as Pro Agent

#### ✅ Plan Page (`/account/plan`)
- **Plan:** "Free Plan"
- **Limit:** 50 reports/month
- **Stripe button:** "Upgrade to Pro" (triggers Stripe Checkout)
- **NO** "Manage Billing" button (not a paid subscriber yet)

### Quick Test
- Click "Upgrade to Pro" → Should open Stripe Checkout
- Verify correct product/plan is shown in Stripe UI
- **DO NOT complete payment** (use Stripe test mode card `4242 4242 4242 4242` if testing)

---

## TEST 5: Admin (Optional)

### Login
1. Log out
2. Open https://www.trendyreports.io/login
3. Enter:
   - Email: `admin@trendyreports-demo.com`
   - Password: `DemoAdmin123!`
4. Click "Sign In"

### Expected
- **Admin access:** Should have elevated permissions (if admin features implemented)
- **/v1/me:** `role` should return `"ADMIN"`
- **No crashes:** App should load normally

---

## QUICK VERIFICATION CHECKLIST

After testing all 5 accounts, verify:

- [ ] **Affiliate badge is purple** (only for affiliate@...)
- [ ] **Agent badge is slate/gray** (for all regular agents + sponsored agent)
- [ ] **Affiliate sees different `/app`** (overview card, not usage dashboard)
- [ ] **Sponsored agent does NOT see affiliate links** in sidebar
- [ ] **Sponsored agent reports are co-branded** (if any reports exist)
- [ ] **Free agent can click "Upgrade to Pro"** and sees Stripe Checkout
- [ ] **Pro agent can click "Manage Billing"** and sees Stripe Customer Portal
- [ ] **All 5 accounts can login without errors**

---

## FAILURE SCENARIOS

### "Agent Account" badge shows for affiliate
**Diagnosis:** Database `account_type` is wrong or `/v1/me` not returning correct value.

**Fix:**
```bash
# Check database
psql "$DATABASE_URL" -f db/check_production_demo_accounts.sql

# If wrong, fix it
psql "$DATABASE_URL" -f db/fix_production_affiliate_account.sql

# Or re-run seeder
python scripts/seed_production_demo_accounts.py
```

### Affiliate sees agent dashboard at `/app`
**Diagnosis:** Frontend not correctly branching on `isAffiliate`.

**Check:**
1. Open browser console at `/app`
2. Check for errors
3. Verify `/api/proxy/v1/me` returns `"account_type": "INDUSTRY_AFFILIATE"`

### Sidebar missing affiliate links
**Diagnosis:** `isAffiliate` prop not being passed or computed incorrectly.

**Check:**
1. `apps/web/app/app/layout.tsx` fetches `/v1/me` correctly
2. `apps/web/app/app-layout.tsx` receives `isAffiliate` prop
3. Sidebar component uses `isAffiliate` to add links

### Sponsored agent sees affiliate links
**Diagnosis:** Login logic incorrectly selecting affiliate account for sponsored agent user.

**Fix:**
- Check `apps/api/src/api/routes/auth.py` login logic
- Sponsored agent should be logged into their `REGULAR` account, not the affiliate's account

---

## SUCCESS CRITERIA

✅ **All 5 accounts login successfully**  
✅ **Affiliate UX is visually distinct** (purple badge, different dashboard, extra nav)  
✅ **Agent UX is consistent** (slate badge, usage dashboard)  
✅ **Sponsored agent reports show affiliate branding** (if reports exist)  
✅ **Stripe flows work** (Checkout for free → pro, Portal for pro)  
✅ **No console errors** on any page  
✅ **No 403/404/500 errors** when navigating

---

## AFTER SMOKE TEST

Once all tests pass:

1. **Document results:**
   - Update `docs/PROD_DEMO_ACCOUNTS_CHECKLIST.md` → "Last seeding verified: [DATE]"
   - Note any issues found and fixed

2. **Update GitHub secrets** (for E2E tests):
   ```
   E2E_REGULAR_EMAIL=agent-pro@trendyreports-demo.com
   E2E_REGULAR_PASSWORD=DemoAgent123!
   E2E_AFFILIATE_EMAIL=affiliate@trendyreports-demo.com
   E2E_AFFILIATE_PASSWORD=DemoAff123!
   ```

3. **Run E2E tests:**
   ```bash
   npx playwright test
   ```

4. **You're ready for demos!** 🎉
   - Investors: Show all 5 roles in 5 minutes
   - Buyers: Demonstrate white-label branding with affiliate + sponsored agent
   - QA: Use canonical accounts for regression testing

---

## Related Documentation

- `docs/PROD_DB_REFERENCE.md` - Production database details
- `docs/PROD_DEMO_ACCOUNTS_CHECKLIST.md` - Account requirements and seeding guide
- `db/seed_demo_accounts_prod_v2.sql` - The actual seed script
- `db/check_production_demo_accounts.sql` - Quick verification query
- `scripts/seed_production_demo_accounts.py` - Automated seeding script
- `docs/AFFILIATE_UX_FIX.md` - Design decisions for affiliate vs agent UX

---

**Last Updated:** November 20, 2025

