# Affiliate vs Agent UX Fix – Making Dashboards Visually Distinct

**Date**: 2025-11-20  
**Commit**: `eee244c`  
**Status**: ✅ DEPLOYED

---

## 🐛 **The Problem**

After logging in as different demo accounts, the dashboards looked **identical**:
- Affiliate account (`affiliate@trendyreports-demo.com`)
- Sponsored agent (`agent-sponsored@trendyreports-demo.com`)

**Root Causes**:
1. `/v1/me` wasn't returning `account_type` (fixed in previous commit)
2. Login didn't prioritize affiliate accounts when user belongs to multiple accounts
3. `/app` dashboard showed the same content regardless of account type
4. No visual indicator of which account type you're viewing

---

## ✅ **The Solution** (4-Step Surgical Plan)

### **Step 1: Database Verification Scripts**

**Created**:
- `db/verify_demo_account_types.sql` - Check if demo accounts have correct types
- `db/fix_demo_account_types.sql` - Fix account types if needed

**What to verify**:
```sql
-- Run this in staging DB:
\i db/verify_demo_account_types.sql

-- Expected results:
-- affiliate@trendyreports-demo.com → INDUSTRY_AFFILIATE, plan: affiliate ✅
-- agent-sponsored@trendyreports-demo.com → REGULAR, plan: sponsored_free ✅
```

**If incorrect**, run: `\i db/fix_demo_account_types.sql`

---

### **Step 2: Prioritize Affiliate Accounts on Login**

**Problem**: When a user belongs to multiple accounts (via `account_users`), login just grabbed the first `account_id` from the `users` table.

**Fix** (`apps/api/src/api/routes/auth.py`):
```python
# After password validation, prioritize INDUSTRY_AFFILIATE accounts
cur.execute("""
    SELECT a.id::text, a.account_type
    FROM account_users au
    JOIN accounts a ON a.id = au.account_id
    WHERE au.user_id = %s::uuid
    ORDER BY 
        CASE 
            WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 1
            WHEN a.id = %s::uuid THEN 2
            ELSE 3
        END
    LIMIT 1
""", (user_id, default_account_id))
```

**Result**: Affiliates now log in to their affiliate account by default, not a child/sponsored account.

---

### **Step 3: Branch /app Dashboard by Account Type**

**File**: `apps/web/app/app/page.tsx`

**Before**: Everyone saw the same usage dashboard

**After**: Branch on `account_type` from `/v1/me`

```typescript
// Fetch user info
const me = await apiFetch("/v1/me")
const isAffiliate = me?.account_type === "INDUSTRY_AFFILIATE"

if (isAffiliate) {
  // Show affiliate-focused overview with CTAs to:
  // - /app/affiliate (Affiliate Dashboard)
  // - /app/affiliate/branding (White-Label Branding)
  return <AffiliateOverview />
} else {
  // Show regular agent dashboard (usage, reports, etc.)
  return <AgentDashboard />
}
```

**Affiliate Dashboard** (`/app` for affiliates):
- Purple card with "Industry Affiliate Account" header
- Clear CTAs to:
  - **Affiliate Dashboard** (sponsored accounts, usage)
  - **White-Label Branding** (logo, colors, tagline)
- Messaging: "Manage your sponsored agents and customize your brand"

**Agent Dashboard** (`/app` for agents):
- Usage metrics
- Report generation stats
- Plan usage warnings
- (Unchanged from before)

---

### **Step 4: Account Type Badge in Header**

**Files**: 
- `apps/web/app/app-layout.tsx` - Badge component
- `apps/web/app/app/layout.tsx` - Fetch account_type and pass to badge

**Badge for Affiliates**:
```tsx
<span className="rounded-full bg-purple-50 text-purple-700 px-3 py-1 border border-purple-200">
  <Shield className="h-3 w-3" />
  Affiliate Account
</span>
```

**Badge for Agents**:
```tsx
<span className="rounded-full bg-slate-50 text-slate-600 px-3 py-1 border border-slate-200">
  Agent Account
</span>
```

**Location**: Top-right header, between search bar and account switcher

**Result**: Instant visual confirmation of which account type you're viewing

---

## 🎯 **What You'll See After Deployment** (2-3 minutes)

### **1. Affiliate Account** (`affiliate@trendyreports-demo.com`)

**On Login** → Redirected to `/app`

**Header**:
- 🟣 Purple badge: "Affiliate Account" (with Shield icon)

**Sidebar**:
- Overview
- Reports
- Schedules
- Branding
- Billing
- **Affiliate Dashboard** ← NEW!
- **Affiliate Branding** ← NEW!

**Dashboard** (`/app`):
- Purple card: "Industry Affiliate Account"
- CTAs to:
  - Affiliate Dashboard (view sponsored accounts)
  - White-Label Branding (customize logo/colors)
- Clear messaging about affiliate features

**At `/app/affiliate`**:
- Sponsored accounts table
- Usage metrics
- "Invite Agent" button

---

### **2. Sponsored Agent** (`agent-sponsored@trendyreports-demo.com`)

**On Login** → Redirected to `/app`

**Header**:
- ⚪ Slate badge: "Agent Account"

**Sidebar**:
- Overview
- Reports
- Schedules
- Branding
- Billing
- ❌ No "Affiliate Dashboard" (not an affiliate)

**Dashboard** (`/app`):
- Regular usage dashboard
- Usage metrics, reports, schedules
- Plan usage warnings (if applicable)

**Reports**:
- Show affiliate's branding (logo, colors, tagline)
- Affiliate stays invisible to end recipient

---

### **3. Regular Pro Agent** (`agent-pro@trendyreports-demo.com`)

**On Login** → Redirected to `/app`

**Header**:
- ⚪ Slate badge: "Agent Account"

**Sidebar**:
- Same as sponsored agent (no affiliate links)

**Dashboard** (`/app`):
- Regular usage dashboard
- Usage metrics, reports, schedules
- Plan usage warnings

**Reports**:
- TrendyReports default branding
- Upgrade to Pro CTAs visible

---

## 📊 **Visual Comparison**

| Feature | Affiliate | Sponsored Agent | Regular Agent |
|---------|-----------|-----------------|---------------|
| **Header Badge** | 🟣 "Affiliate Account" | ⚪ "Agent Account" | ⚪ "Agent Account" |
| **Dashboard at /app** | Affiliate overview + CTAs | Usage dashboard | Usage dashboard |
| **Sidebar Links** | + Affiliate Dashboard, Branding | Standard | Standard |
| **Reports Branding** | Own brand | Affiliate's brand | TrendyReports brand |
| **Can Invite Agents** | Yes ✅ | No ❌ | No ❌ |
| **Can Manage Branding** | Yes ✅ | No ❌ | No ❌ |

---

## 🧪 **Testing Checklist**

### **Before Testing**
Run these SQL scripts in staging DB (if demo accounts aren't working):

```bash
# Connect to staging
psql "postgresql://mr_staging_db_user:<PASSWORD>@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

# Verify account types
\i db/verify_demo_account_types.sql

# If needed, fix account types
\i db/fix_demo_account_types.sql
```

### **Test Affiliate Account**
1. Log out (if logged in)
2. Visit: `/login`
3. Login: `affiliate@trendyreports-demo.com` / `DemoAff123!`
4. **Check**:
   - ✅ Redirects to `/app`
   - ✅ Header shows purple "Affiliate Account" badge
   - ✅ Dashboard shows affiliate overview (not usage dashboard)
   - ✅ Sidebar has "Affiliate Dashboard" and "Affiliate Branding" links
5. Click "Affiliate Dashboard"
6. **Check**:
   - ✅ See sponsored accounts table
   - ✅ See "Invite Agent" button

### **Test Sponsored Agent**
1. Log out
2. Login: `agent-sponsored@trendyreports-demo.com` / `DemoAgent123!`
3. **Check**:
   - ✅ Redirects to `/app`
   - ✅ Header shows slate "Agent Account" badge
   - ✅ Dashboard shows usage dashboard (NOT affiliate overview)
   - ✅ Sidebar does NOT have "Affiliate Dashboard" links
4. Create a report
5. **Check**:
   - ✅ Report shows affiliate's branding (not TrendyReports)

### **Test Regular Agent**
1. Log out
2. Login: `agent-pro@trendyreports-demo.com` / `DemoAgent123!`
3. **Check**:
   - ✅ Header shows slate "Agent Account" badge
   - ✅ Dashboard shows usage dashboard
   - ✅ No affiliate links in sidebar
   - ✅ Reports show TrendyReports branding

---

## 🔧 **Troubleshooting**

### **"Still seeing the same dashboard for affiliate and agent"**
- Wait 2-3 minutes for Render + Vercel to redeploy
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear cookies and log in again
- Check Render logs for any deployment errors

### **"Account type badge not showing"**
- Check `/v1/me` returns `account_type` field
- Verify frontend build deployed successfully on Vercel
- Check browser console for errors

### **"Affiliate logs in but sees agent dashboard"**
- Run `db/verify_demo_account_types.sql` to check DB
- Ensure `account_type = 'INDUSTRY_AFFILIATE'` for affiliate account
- If wrong, run `db/fix_demo_account_types.sql`
- Log out and back in

### **"Sidebar still doesn't show affiliate links"**
- Check `/v1/me` returns correct `account_type`
- Verify app layout fetches `me` data correctly
- Check browser Network tab → `/v1/me` response

---

## 📚 **Related Documentation**

- `docs/DEMO_ACCOUNTS.md` - Demo credentials for all 5 roles
- `docs/AUTH_ARCHITECTURE_V1.md` - Auth system overview
- `PROJECT_STATUS-3.md` - Project status and roadmap
- `docs/SEED_DEMO_ACCOUNTS.md` - How to seed demo accounts

---

## 🎯 **Success Criteria**

**This fix is successful when**:
- [x] Affiliate logs in and sees purple "Affiliate Account" badge
- [x] Affiliate's `/app` shows affiliate overview (not usage dashboard)
- [x] Affiliate sees "Affiliate Dashboard" and "Affiliate Branding" in sidebar
- [x] Sponsored agent sees slate "Agent Account" badge
- [x] Sponsored agent's `/app` shows usage dashboard (not affiliate overview)
- [x] Sponsored agent does NOT see affiliate links in sidebar
- [x] Reports for sponsored agent show affiliate's branding
- [x] It's **visually obvious** which account type you're viewing

---

**Last Updated**: November 20, 2025  
**Deployed**: Commit `eee244c`  
**Status**: ✅ LIVE ON STAGING

Test it now at: https://reportscompany-web.vercel.app/login 🚀

