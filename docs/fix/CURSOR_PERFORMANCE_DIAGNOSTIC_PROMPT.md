# CRITICAL PERFORMANCE REGRESSION — FULL DIAGNOSTIC REQUIRED

## Situation

The app has a **22-second LCP** with **13.4-second TTFB**. This started immediately after the recent UI upgrade work. Before the upgrade, pages loaded normally.

**Confirmed:** The Render API is healthy — hitting `/health` directly returns instantly. The problem is **100% in the Next.js code**.

This is not a tuning issue. Something is fundamentally broken in how the app fetches data.

---

## Your Mission

Find exactly what changed that caused server components to hang for 13+ seconds. Be systematic. Show your work. No guessing.

---

## Phase 1: Git Forensics

Run these commands and show me the FULL output:

```bash
# Show recent commits
git log --oneline -30

# Find when the UI upgrade started (look for commits mentioning UI, performance, loading, skeleton, cache, etc.)
# Then show what changed in these critical files:

git diff HEAD~20 HEAD -- apps/web/src/lib/api-server.ts
git diff HEAD~20 HEAD -- apps/web/src/lib/api.ts  
git diff HEAD~20 HEAD -- apps/web/src/app/app/layout.tsx
git diff HEAD~20 HEAD -- apps/web/src/app/app/page.tsx
git diff HEAD~20 HEAD -- apps/web/next.config.js
git diff HEAD~20 HEAD -- apps/web/next.config.ts
git diff HEAD~20 HEAD -- apps/web/next.config.mjs
git diff HEAD~20 HEAD -- apps/web/middleware.ts
git diff HEAD~20 HEAD -- apps/web/src/middleware.ts

# Check if any new dependencies were added
git diff HEAD~20 HEAD -- apps/web/package.json
git diff HEAD~20 HEAD -- pnpm-lock.yaml | head -200
```

**Show me every line that changed in these files.** Do not summarize. I need to see the actual diff.

---

## Phase 2: Inspect the Crime Scenes

Open and show me the COMPLETE current contents of these files:

### File 1: `apps/web/src/lib/api-server.ts`

This is the server-side API client. Look for:
- How `fetch()` is called
- Any `cache`, `next`, or `revalidate` options
- Whether there's a timeout/abort controller
- Whether Authorization headers are being set correctly

**Red flags:**
```typescript
// BROKEN — force-cache with auth headers causes hanging
cache: "force-cache"

// BROKEN — revalidate with dynamic auth can cause issues  
next: { revalidate: 300 }

// BROKEN — no timeout means infinite hang if something goes wrong
await fetch(url, { headers })  // no signal/timeout

// BROKEN — accidentally making requests sequentially instead of parallel
const user = await api.get("/v1/me")
const account = await api.get("/v1/account")  // waits for user first
const usage = await api.get("/v1/usage")      // waits for account first
```

### File 2: `apps/web/src/lib/api.ts`

This might be the client-side API client. Check if it's accidentally being imported into server components.

### File 3: `apps/web/src/app/app/layout.tsx`

This layout wraps EVERY page in `/app/*`. If it has blocking API calls, every single page waits.

**Red flags:**
```typescript
// BROKEN — blocks ALL child pages from rendering
export default async function AppLayout({ children }) {
  const user = await api.get("/v1/me")  // 13 seconds here = 13s TTFB everywhere
  return <Layout user={user}>{children}</Layout>
}
```

### File 4: `apps/web/src/app/app/page.tsx`

The dashboard. Check how it fetches data.

**Red flags:**
```typescript
// BROKEN — sequential fetches (each waits for previous)
const user = await api.get("/v1/me")
const usage = await api.get("/v1/usage")
const plan = await api.get("/v1/account/plan-usage")

// CORRECT — parallel fetches
const [user, usage, plan] = await Promise.all([
  api.get("/v1/me"),
  api.get("/v1/usage"),
  api.get("/v1/account/plan-usage"),
])
```

### File 5: `apps/web/next.config.js` (or .ts/.mjs)

Check for any config changes that affect fetch behavior.

### File 6: `apps/web/middleware.ts` or `apps/web/src/middleware.ts`

Middleware runs on EVERY request. If it's doing API calls or slow operations, everything suffers.

---

## Phase 3: Search for Poison Patterns

Run these searches across the entire `apps/web` directory:

```bash
# Find all fetch calls with cache options
grep -rn "cache:" apps/web/src --include="*.ts" --include="*.tsx"
grep -rn "force-cache" apps/web/src --include="*.ts" --include="*.tsx"
grep -rn "revalidate" apps/web/src --include="*.ts" --include="*.tsx"

# Find all server-side API calls
grep -rn "createServerApi" apps/web/src --include="*.ts" --include="*.tsx"
grep -rn "api\.get" apps/web/src --include="*.ts" --include="*.tsx"
grep -rn "api\.post" apps/web/src --include="*.ts" --include="*.tsx"

# Find any new async operations in layouts
grep -rn "async function.*Layout" apps/web/src --include="*.ts" --include="*.tsx"
grep -rn "await.*Layout" apps/web/src --include="*.ts" --include="*.tsx"

# Find fetch without timeout
grep -rn "await fetch" apps/web/src --include="*.ts" --include="*.tsx"

# Check for accidental blocking patterns
grep -rn "cookies()" apps/web/src --include="*.ts" --include="*.tsx"
grep -rn "headers()" apps/web/src --include="*.ts" --include="*.tsx"
```

Show me ALL results from these searches.

---

## Phase 4: Runtime Diagnosis

Add temporary logging to identify exactly where time is spent. 

In `apps/web/src/lib/api-server.ts`, wrap the fetch call:

```typescript
async get<T>(path: string, options?: any): Promise<T> {
  const start = Date.now()
  console.log(`[API] Starting: ${path}`)
  
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      // ... existing options
    })
    console.log(`[API] Completed: ${path} in ${Date.now() - start}ms`)
    return res.json()
  } catch (error) {
    console.log(`[API] Failed: ${path} after ${Date.now() - start}ms`, error)
    throw error
  }
}
```

Then check the Vercel function logs or local terminal to see:
- Which API calls are being made
- How long each takes
- Whether they're running in parallel or sequentially

---

## Phase 5: The Fix

Based on what you find, do ONE of these:

### Option A: If `api-server.ts` was modified with broken caching

Revert it to the exact state before the UI upgrade:

```bash
git checkout <commit-before-upgrade> -- apps/web/src/lib/api-server.ts
```

### Option B: If `layout.tsx` has new blocking API calls

Either revert it:
```bash
git checkout <commit-before-upgrade> -- apps/web/src/app/app/layout.tsx
```

Or restructure to be non-blocking:
```typescript
// Move API calls into a Suspense boundary or make them client-side
export default function AppLayout({ children }) {
  return (
    <Suspense fallback={<LayoutSkeleton />}>
      <AppLayoutWithData>{children}</AppLayoutWithData>
    </Suspense>
  )
}
```

### Option C: If fetch calls are missing timeouts

Add abort controller to every server-side fetch:

```typescript
const controller = new AbortController()
const timeout = setTimeout(() => controller.abort(), 8000) // 8s max

try {
  const res = await fetch(url, {
    ...options,
    signal: controller.signal,
    cache: "no-store",  // Don't cache authenticated requests
  })
  clearTimeout(timeout)
  return res
} catch (e) {
  clearTimeout(timeout)
  throw e
}
```

### Option D: If caching options are the problem

Remove ALL caching from authenticated API calls:

```typescript
// For ANY request with Authorization header:
const res = await fetch(url, {
  headers: { Authorization: `Bearer ${token}` },
  cache: "no-store",  // REQUIRED for authenticated requests
})
```

---

## Phase 6: Verify

After making fixes:

1. Deploy to preview/staging
2. Open Chrome DevTools → Performance tab
3. Record a page load
4. Confirm:
   - TTFB < 1.5 seconds
   - LCP < 3 seconds
   - No hanging requests in Network tab

---

## What I Expect From You

1. **Show me the git diffs** — full output, not summaries
2. **Show me the current file contents** — api-server.ts, layout.tsx, page.tsx
3. **Show me the grep results** — all matches for the poison patterns
4. **Tell me exactly what you find** — "Line 47 of api-server.ts has `cache: force-cache` which was added in commit abc123"
5. **Propose a specific fix** — not "we should look into caching" but "revert lines 45-52 of api-server.ts"
6. **Apply the fix and verify** — show me the new TTFB after fixing

Do not theorize. Do not guess. Find the exact lines that changed and broke performance. This is forensic debugging.

---

## Context

- Framework: Next.js 16 with App Router (Server Components)
- API: FastAPI on Render (confirmed healthy — /health responds instantly)
- The same frameworks work fine on other projects
- This broke during the UI upgrade — it was working before
- We need the EXACT code that caused this, not general advice
