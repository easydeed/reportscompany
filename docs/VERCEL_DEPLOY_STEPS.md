# Vercel Deployment & Verification Steps

**Purpose:** Ensure we're deploying the correct code to production and can verify what build is actually running.

---

## 🔧 **STEP 1: Set Build Tag in Vercel**

This makes it crystal clear which build the browser is running.

1. Go to **Vercel Dashboard**: https://vercel.com
2. Navigate to **reportscompany-web** project
3. Go to **Settings** → **Environment Variables**
4. Add/Update:
   - **Key:** `NEXT_PUBLIC_BUILD_TAG`
   - **Value:** `AFFILIATE_FIX_2024-11-20` (or current date)
   - **Environments:** Check all three: Production, Preview, Development
5. Click **Save**

---

## 🚀 **STEP 2: Force Clean Deployment (No Build Cache)**

This guarantees a fresh build without any cached layers.

1. Go to **Vercel Dashboard** → **reportscompany-web**
2. Click **Deployments** tab
3. Find the **latest commit** (should be the one with build marker changes)
4. Click the **three-dot menu (⋮)** next to the deployment
5. Click **"Redeploy"**
6. **CRITICAL:** When the modal appears:
   - **UNCHECK** the box for "Use existing Build Cache"
   - This forces a completely fresh build
7. Click **"Redeploy"** to confirm
8. Wait for status to show **"Ready"** (usually 1-3 minutes)

**Why this matters:**
- Clears all cached build artifacts
- Forces Next.js to rebuild all pages from scratch
- Generates a new deployment ID
- Invalidates edge cache across all CDN locations

---

## 🌐 **STEP 3: Verify Domain Mapping**

Confirm the production domain points to THIS project.

### Check Domain Configuration

1. In **Vercel Dashboard** → **reportscompany-web**
2. Go to **Settings** → **Domains**
3. Verify:
   - ✅ `www.trendyreports.io` is listed
   - ✅ It's marked as **Primary** (or at least assigned to this project)
   - ✅ Status shows **"Valid Configuration"** or similar
   - ❌ There's NO other Vercel project claiming this domain

### Check Git Integration

1. Go to **Settings** → **Git**
2. Verify:
   - ✅ **Repository:** Correct GitHub repo (e.g., `easydeed/reportscompany`)
   - ✅ **Production Branch:** `main`
   - ✅ Auto-deploy is enabled (unless you want manual control)

**If domain is pointing to a different project:**
- You'll need to either:
  - Remove the domain from the old project and add it to this one, OR
  - Deploy to the correct project that owns the domain

---

## 🧪 **STEP 4: Browser Verification (Manual QA)**

After deployment shows "Ready", verify what build the browser is actually running.

### A. Open Clean Browser Session

1. **Open a NEW incognito/private window** (ensures no cached data)
2. Navigate to: https://www.trendyreports.io/app
3. You'll be redirected to login (expected)

### B. Check Build Tag (Before Login)

If the login page doesn't show the build tag, that's okay – it's only in the app shell.

### C. Login as Affiliate

- **Email:** `affiliate@trendyreports-demo.com`
- **Password:** `DemoAff123!`
- Click **Sign In**
- Wait for redirect to `/app`

### D. Verify Build Tag

Look at the **top-right area of the header**. You should see small gray text:
```
build: AFFILIATE_FIX_2024-11-20
```

**Interpretation:**
- ✅ **Tag matches what you set?** → You're running the correct deployment
- ❌ **Tag is missing or says "local-dev"?** → Env var didn't propagate, or you're hitting a different project
- ❌ **Tag is an older date?** → You're seeing a stale deployment (domain might be pointing elsewhere)

### E. Check Debug Info

Right next to the build tag, you should see:
```
role: USER | affiliate: yes | type: INDUSTRY_AFFILIATE
```

**Interpretation:**
- ✅ `affiliate: yes` → `isAffiliate` prop is correctly set to `true`
- ✅ `type: INDUSTRY_AFFILIATE` → `/v1/me` returned correct data
- ❌ `affiliate: no` or `type: REGULAR` → Backend or data issue (unlikely at this point)

### F. Verify UI Elements

Now check the actual UI rendering:

**Header:**
- ✅ Badge should say **"Affiliate Account"** (purple with shield icon)
- ❌ If it says "Agent Account" → Badge conditional isn't working

**Sidebar (left side):**
- ✅ Should see "Affiliate Dashboard" link
- ✅ Should see "Affiliate Branding" link  
- ❌ Should NOT see "Admin" link (user role is MEMBER, not ADMIN)
- ❌ If missing affiliate links → Sidebar conditional isn't working

**Dashboard Content:**
- ✅ Should see a purple card titled "Industry Affiliate Account"
- ✅ Card should have links to Affiliate Dashboard and Branding
- ❌ If showing regular agent dashboard (charts, metrics) → Page conditional isn't working

### G. DevTools Double-Check (Optional)

1. Open **DevTools** (F12)
2. Go to **Network** tab
3. Find the request to `/api/proxy/v1/me` (or filter for "me")
4. Click on it and view **Response**
5. Confirm JSON contains:
   ```json
   {
     "account_type": "INDUSTRY_AFFILIATE",
     "email": "affiliate@trendyreports-demo.com",
     ...
   }
   ```

---

## 🐛 **STEP 5: Troubleshooting Decision Tree**

### Scenario 1: Build tag is wrong or missing

**Problem:** Edge is serving old code or wrong project

**Actions:**
1. Double-check domain mapping (Step 3)
2. Verify the deployment you redeployed is marked "Current" in Vercel
3. Check if there are multiple Vercel projects (staging vs prod)
4. Wait 5 more minutes (CDN propagation delay)
5. Try visiting with cache-buster: `?_v=1732139000`

### Scenario 2: Build tag is correct, but debug shows `affiliate: no`

**Problem:** `/v1/me` not returning correct data, or `isAffiliate` computation is broken

**Actions:**
1. Check DevTools → Network → `/api/proxy/v1/me` response
2. If response has `account_type: "INDUSTRY_AFFILIATE"`:
   - Bug in `layout.tsx` line 12: `isAffiliate = me?.account_type === "INDUSTRY_AFFILIATE"`
   - Check for typos, case sensitivity
3. If response has `account_type: "REGULAR"`:
   - Database issue (unlikely – already verified)
   - Check Render logs for `/v1/me` to see what backend is returning

### Scenario 3: Build tag correct, debug shows `affiliate: yes`, but UI is wrong

**Problem:** The conditional rendering in the JSX isn't working

**Actions:**

**If badge is wrong:**
- Bug in `app-layout.tsx` lines 126-136
- Check if `accountType` prop is being passed correctly to `DashboardTopbar`

**If sidebar is wrong:**
- Bug in `app-layout.tsx` lines 57-60 or 189
- Check if `isAffiliate` prop is being passed correctly to `DashboardSidebar`

**If dashboard content is wrong:**
- Bug in `app/page.tsx` lines 24-86
- Check if server component is receiving correct props
- Check if `apiFetch("/v1/me")` on the page is being called and evaluated

### Scenario 4: Everything looks perfect

**Success!** 🎉
- Remove or comment out the debug text (build tag can stay if you find it useful)
- Test with other demo accounts to confirm role-based UI works across the board

---

## 📋 **Quick Reference: Demo Accounts**

For testing different roles:

| Email | Password | Expected UI |
|-------|----------|-------------|
| `affiliate@trendyreports-demo.com` | `DemoAff123!` | Affiliate badge, affiliate nav, affiliate dashboard |
| `agent-pro@trendyreports-demo.com` | `DemoAgent123!` | Agent badge, regular nav, regular dashboard |
| `agent-free@trendyreports-demo.com` | `DemoAgent123!` | Agent badge, regular nav, regular dashboard |
| `admin@trendyreports-demo.com` | `DemoAdmin123!` | Agent badge, "Admin" link in nav, regular dashboard |
| `agent-sponsored@trendyreports-demo.com` | `DemoAgent123!` | Agent badge, regular nav, co-branded reports |

---

## 🧹 **After Verification: Cleanup (Optional)**

Once you've confirmed everything works:

1. **Remove debug text** from `app-layout.tsx`:
   ```typescript
   // Delete or comment out:
   <span className="text-[10px] text-slate-400">
     role: {isAdmin ? "ADMIN" : "USER"} | affiliate: {isAffiliate ? "yes" : "no"} | type: {accountType || "unknown"}
   </span>
   ```

2. **Keep or remove build tag** (your choice):
   - If you want to always see what build is deployed: keep it
   - If it's clutter: remove it
   - Consider only showing it for admin users

3. Commit cleanup changes and redeploy (no need to clear cache this time)

---

**End of Guide**

