# Vercel Environment Variable Fix ✅

**Status:** COMPLETED by User  
**Date:** November 13, 2025

---

## Required Change

In Vercel dashboard for project `reportscompany-web`:

1. Go to: Settings → Environment Variables
2. Find: `NEXT_PUBLIC_API_BASE`
3. Current value: `https://reportscompany-api.onrender.com` ❌
4. **Change to:** `https://reportscompany.onrender.com` ✅
5. Apply to: Production, Preview, Development (all environments)
6. Save changes

---

## After Changing

Trigger a redeploy:
- Option A: Go to Deployments → latest → Redeploy
- Option B: Push any commit to trigger auto-deploy

---

## Verification

After redeployment, test:

```bash
# 1. Test API endpoint directly
curl https://reportscompany.onrender.com/v1/reports/e5bbf66a-803f-4e6e-b0c6-81c0960f0818/data

# Should return JSON with city, counts, metrics

# 2. Test print page
open https://reportscompany-web.vercel.app/print/e5bbf66a-803f-4e6e-b0c6-81c0960f0818

# Should show "Market Snapshot — Houston" with actual KPIs
```

---

## ✅ User Confirmation

User reported: **"Ok. I have updated https://reportscompany.onrender.com"**

This means the Vercel environment variable has been corrected and should now point to the right API URL.

---

## Impact

**Before:**
- Print page tried to fetch from: `https://reportscompany-api.onrender.com/v1/reports/{id}/data`
- This URL doesn't exist (404)
- PDFs showed "report ID unknown"

**After:**
- Print page fetches from: `https://reportscompany.onrender.com/v1/reports/{id}/data`
- Correct API responds with report data
- PDFs show actual city names and KPI numbers

---

## Related Improvements

As part of Task 2, the print page also received:
1. **Better error logging** - console logs show fetch URL and status
2. **Improved error page** - user-friendly "Report Not Found" with diagnostics
3. **Shows API Base** - error page displays configured API URL for debugging

