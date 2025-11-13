# Fix: PDF Shows "Report ID Unknown"

**Date:** November 13, 2025  
**Issue:** Email delivered successfully, but PDF shows "report ID unknown" instead of actual report data  
**Root Cause:** Incorrect `NEXT_PUBLIC_API_BASE` environment variable on Vercel  

---

## Problem

When PDFShift generates the PDF by rendering the Next.js print page, the page tries to fetch report data from the API:

```typescript
// In apps/web/app/print/[runId]/page.tsx
async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE!;
  const res = await fetch(`${base}/v1/reports/${runId}/data`, {
    cache: "no-store"
  });
  if (!res.ok) return null;
  return res.json();
}
```

If `NEXT_PUBLIC_API_BASE` is set incorrectly, the fetch fails and the page shows fallback data.

---

## Root Cause

**Incorrect Environment Variable:**
```
NEXT_PUBLIC_API_BASE=https://reportscompany-api.onrender.com  ❌
```

**Correct Value:**
```
NEXT_PUBLIC_API_BASE=https://reportscompany.onrender.com  ✅
```

The API service URL is `reportscompany.onrender.com` (without `-api`).

---

## Fix

### Step 1: Update Vercel Environment Variable

1. Go to Vercel dashboard: https://vercel.com/dashboard
2. Find project: `reportscompany-web`
3. Go to Settings → Environment Variables
4. Find `NEXT_PUBLIC_API_BASE`
5. Update value to: `https://reportscompany.onrender.com`
6. Save changes

### Step 2: Redeploy

Option A: **Trigger redeploy from Vercel dashboard**
- Go to Deployments tab
- Click "Redeploy" on latest deployment

Option B: **Push empty commit to trigger auto-deploy**
```bash
git commit --allow-empty -m "fix: update API base URL for print pages"
git push origin main
```

---

## Verification

After redeployment:

1. **Test the print page directly:**
   - Visit: `https://reportscompany-web.vercel.app/print/e5bbf66a-803f-4e6e-b0c6-81c0960f0818`
   - Should show: "Market Snapshot — Houston" with actual data
   - Should NOT show: "Report ID unknown"

2. **Test the API endpoint:**
   ```bash
   curl https://reportscompany.onrender.com/v1/reports/e5bbf66a-803f-4e6e-b0c6-81c0960f0818/data
   ```
   - Should return JSON with city, counts, metrics, etc.

3. **Create new test schedule:**
   - Use the existing test schedule or create a new one
   - Wait for ticker to process
   - Check email → click PDF link
   - PDF should show actual report data

---

## Alternative: Add Better Error Handling

If the environment variable is correct but there are still issues, improve error handling in the print page:

```typescript
// apps/web/app/print/[runId]/page.tsx
async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  
  if (!base) {
    console.error('NEXT_PUBLIC_API_BASE not set');
    return null;
  }
  
  const url = `${base}/v1/reports/${runId}/data`;
  console.log(`Fetching report data from: ${url}`);
  
  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: {
        'Accept': 'application/json',
      }
    });
    
    console.log(`Response status: ${res.status}`);
    
    if (!res.ok) {
      console.error(`API error: ${res.status} ${res.statusText}`);
      return null;
    }
    
    const data = await res.json();
    console.log(`Successfully fetched data for: ${data.city}`);
    return data;
  } catch (error) {
    console.error(`Failed to fetch report data:`, error);
    return null;
  }
}
```

---

## Why This Happened

The API service name is `reportscompany` (slug: `reportscompany`) which gets the URL:
- `https://reportscompany.onrender.com`

The `-api` suffix was likely added assuming it would be the service name, but Render uses the slug directly.

---

## Impact

- **Email delivery:** ✅ Working perfectly
- **SendGrid integration:** ✅ Working (202 Accepted)
- **PDF generation:** ✅ Working (PDF is created)
- **PDF content:** ⚠️ Missing report data (shows "report ID unknown")

**After fix:** All components will work perfectly.

---

## Related Files

- `apps/web/app/print/[runId]/page.tsx` - Print page that fetches report data
- `apps/api/src/api/routes/report_data.py` - API endpoint that serves report data
- `apps/worker/src/worker/pdf_engine.py` - PDF generation logic
- `Vercel Environment Variables` - Where `NEXT_PUBLIC_API_BASE` is set

---

**Status:** Fix identified, needs Vercel environment variable update  
**Estimated Time:** 5 minutes to update + 2 minutes redeploy

