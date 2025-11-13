# Task 2: Fix "Report ID Unknown" in PDFs

**Estimated Time:** 20 minutes  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 Goal

Fix PDFs showing "Report ID unknown" text. The print page must fetch and display actual report data.

---

## 🔍 Root Cause

The print page (`/print/[runId]`) tries to fetch report data from the API:
```typescript
const base = process.env.NEXT_PUBLIC_API_BASE;
const res = await fetch(`${base}/v1/reports/${runId}/data`);
```

**Problem:** `NEXT_PUBLIC_API_BASE` is set to wrong URL in Vercel environment variables.

**Current (WRONG):** `https://reportscompany-api.onrender.com`  
**Correct:** `https://reportscompany.onrender.com`

---

## 📂 Files to Check/Modify

### 1. Verify the Print Page Logic

**File:** `apps/web/app/print/[runId]/page.tsx`

**Current code:**
```typescript
async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE!;
  const res = await fetch(`${base}/v1/reports/${runId}/data`, {
    cache: "no-store"
  });
  if (!res.ok) return null;
  return res.json();
}
```

**Required changes:**

1. **Add better error logging:**
```typescript
async function fetchData(runId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  
  if (!base) {
    console.error('[Print Page] NEXT_PUBLIC_API_BASE not set');
    return null;
  }
  
  const url = `${base}/v1/reports/${runId}/data`;
  console.log(`[Print Page] Fetching report data from: ${url}`);
  
  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: {
        'Accept': 'application/json',
      }
    });
    
    console.log(`[Print Page] Response status: ${res.status}`);
    
    if (!res.ok) {
      console.error(`[Print Page] API error: ${res.status} ${res.statusText}`);
      return null;
    }
    
    const data = await res.json();
    console.log(`[Print Page] Successfully fetched data for: ${data.city || 'unknown'}`);
    return data;
  } catch (error) {
    console.error(`[Print Page] Failed to fetch report data:`, error);
    return null;
  }
}
```

2. **Improve "not found" message:**

**Current:**
```tsx
if (!data) {
  return (
    <html lang="en">
      <body>
        <h1>Report Not Found</h1>
        <p>Run ID: {runId}</p>
      </body>
    </html>
  );
}
```

**Update to:**
```tsx
if (!data) {
  return (
    <html lang="en">
      <head>
        <title>Report Not Found</title>
      </head>
      <body style={{
        fontFamily: 'system-ui, sans-serif',
        padding: '40px',
        textAlign: 'center'
      }}>
        <h1>Report Not Found</h1>
        <p>Report ID: <code>{runId}</code></p>
        <p style={{color: '#666', fontSize: '14px'}}>
          The report data could not be loaded. Please check:
        </p>
        <ul style={{textAlign: 'left', maxWidth: '400px', margin: '20px auto', color: '#666', fontSize: '14px'}}>
          <li>Report ID is correct</li>
          <li>Report has been generated</li>
          <li>API connection is working</li>
        </ul>
        <p style={{color: '#999', fontSize: '12px', marginTop: '40px'}}>
          API Base: {process.env.NEXT_PUBLIC_API_BASE || 'Not configured'}
        </p>
      </body>
    </html>
  );
}
```

3. **Remove any "report ID unknown" placeholder text:**

Search the entire file for:
- "unknown"
- "Unknown"
- "UNKNOWN"
- "placeholder"

Replace with appropriate null coalescing:
```typescript
<h1>{reportTitle} — {data.city ?? "N/A"}</h1>
```

---

### 2. Environment Variable Configuration

**File:** `apps/web/.env.example` (if exists)

**Add/Update:**
```bash
# API Configuration
NEXT_PUBLIC_API_BASE=https://reportscompany.onrender.com

# For local development
# NEXT_PUBLIC_API_BASE=http://localhost:10000
```

**File:** `apps/web/.env.local` (for local testing)

**Create if doesn't exist:**
```bash
NEXT_PUBLIC_API_BASE=https://reportscompany.onrender.com
```

---

### 3. Vercel Environment Variable (MANUAL STEP - Document Only)

**Cannot be done via code.** Document the required change:

**Create:** `VERCEL_ENV_VAR_FIX.md`

```markdown
# Vercel Environment Variable Fix

## Required Change

In Vercel dashboard for project `reportscompany-web`:

1. Go to: Settings → Environment Variables
2. Find: `NEXT_PUBLIC_API_BASE`
3. Current value: `https://reportscompany-api.onrender.com` ❌
4. **Change to:** `https://reportscompany.onrender.com` ✅
5. Apply to: Production, Preview, Development (all environments)
6. Save changes

## After Changing

Trigger a redeploy:
- Option A: Go to Deployments → latest → Redeploy
- Option B: Push any commit to trigger auto-deploy

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
```

---

## ✅ Acceptance Criteria

### Code Changes
- [ ] `fetchData()` has improved error logging
- [ ] "Report Not Found" page is user-friendly
- [ ] No "unknown" placeholder text in report display
- [ ] `.env.example` documents correct API URL
- [ ] `VERCEL_ENV_VAR_FIX.md` created with manual instructions

### Local Testing
- [ ] Run `pnpm --filter web dev`
- [ ] Set `NEXT_PUBLIC_API_BASE=https://reportscompany.onrender.com` in `.env.local`
- [ ] Visit: `http://localhost:3000/print/e5bbf66a-803f-4e6e-b0c6-81c0960f0818`
- [ ] Expected: See "Market Snapshot — Houston" with real KPI numbers
- [ ] Check browser console: Should see fetch URL and success logs

### Production (After Vercel Env Var Fix)
- [ ] PDF from email shows correct city name
- [ ] PDF shows real KPI numbers (not "unknown" or placeholders)
- [ ] Print page accessible: `https://reportscompany-web.vercel.app/print/[runId]`

---

## 🧪 Testing Data

**Known Good Report IDs:**
- `e5bbf66a-803f-4e6e-b0c6-81c0960f0818` - Houston Market Snapshot
- `c28d8f37-f32a-4f63-962e-ac748d87325b` - Houston Market Snapshot (earlier)

**Test URLs:**
```
Local:
http://localhost:3000/print/e5bbf66a-803f-4e6e-b0c6-81c0960f0818

Production:
https://reportscompany-web.vercel.app/print/e5bbf66a-803f-4e6e-b0c6-81c0960f0818

API Endpoint:
https://reportscompany.onrender.com/v1/reports/e5bbf66a-803f-4e6e-b0c6-81c0960f0818/data
```

---

## 🚨 Common Pitfalls

1. **Environment variable not available at build time**
   - `NEXT_PUBLIC_` prefix is required for client-side access
   - Without it, the variable won't be available in the browser

2. **Caching issues after env var change**
   - Must redeploy for changes to take effect
   - Clear browser cache if testing same URL

3. **Wrong report ID format**
   - Must be UUID from `report_generations.id`
   - Not the schedule ID or other identifier

4. **API endpoint 404**
   - Verify `/v1/reports/{id}/data` endpoint exists in API
   - Check API logs if fetch fails

---

## 📝 Commit Message

```
fix(web): improve print page error handling and logging

- Add detailed error logging to fetchData()
- Improve "Report Not Found" error page with diagnostics
- Remove "unknown" placeholders, use null coalescing
- Document correct NEXT_PUBLIC_API_BASE value
- Create Vercel env var fix instructions

Issue: PDFs showing "report ID unknown"
Root cause: Wrong API URL in Vercel environment

