# CRITICAL: 22s LCP Diagnostic & Fix Guide

## The Problem

- **TTFB: 13.4 seconds** — Server takes 13.4s before sending ANY HTML
- **Element render delay: 8.7 seconds** — Another 8.7s after HTML arrives
- **LCP element: `h1` text** — Not an image. The page itself is stuck.
- **This started after the UI upgrade**

This means the Vercel server component is waiting 13+ seconds on API calls
to Render before it can render ANY page content.

---

## Step 1: Diagnose — Is It the Render API?

### Test 1A: Hit the API directly

Open a new browser tab and go directly to your Render API health endpoint:

```
https://your-render-api-url.onrender.com/health
```

**Time it.** If this takes more than 1 second, Render is the problem.

### Test 1B: Hit an authenticated endpoint directly

Use curl or your browser's DevTools console:

```bash
# Replace with your actual API URL and a valid JWT token
curl -w "\n\nTotal time: %{time_total}s\nTTFB: %{time_starttransfer}s\n" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://your-render-api-url.onrender.com/v1/me
```

If this takes 5+ seconds, the Render API is slow.
If this responds in < 1 second, the problem is elsewhere.

### Test 1C: Check Render Dashboard

1. Go to Render Dashboard → your API service
2. Check **Events** tab — look for:
   - Recent deploys
   - Service restarts
   - "Suspended" or "Deactivated" messages
3. Check **Metrics** tab:
   - CPU usage (is it pegged at 100%?)
   - Memory usage (is it near the limit?)
   - Response times (what does Render report?)
4. Check **Logs** tab:
   - Any errors on startup?
   - Any slow query warnings?
   - Is the app actually running?

---

## Step 2: Diagnose — Is It the Database?

### Check Render PostgreSQL

1. Go to Render Dashboard → your PostgreSQL instance
2. Check **Metrics**:
   - Connection count (is it at the limit?)
   - CPU / Memory
3. Check if the database is on the same region as your API service
   - If API is in Oregon and DB is in Ohio, that's added latency

### Check Redis

1. Go to Render Dashboard → your Redis instance
2. Is it running?
3. Is it on the same region?
4. Check connection count

---

## Step 3: Diagnose — Did the Code Changes Break Something?

The UI upgrade may have introduced issues in the API client or server components.

### Check 3A: Look at `lib/api-server.ts`

If Cursor modified the API client to add caching (from the performance guide),
it may have broken the fetch calls. Look for:

```typescript
// ❌ BROKEN: Wrong fetch options that could cause hanging
const res = await fetch(url, {
  next: { revalidate: 300 },
  cache: "force-cache",  // ← This could cause issues with auth
})

// ❌ BROKEN: Missing timeout — fetch will wait forever
const res = await fetch(url, {
  headers: { Authorization: `Bearer ${token}` },
  // No signal/timeout — if Render is slow, this hangs indefinitely
})

// ✅ CORRECT: Has timeout protection
const controller = new AbortController()
const timeout = setTimeout(() => controller.abort(), 10000) // 10s max

const res = await fetch(url, {
  headers: { Authorization: `Bearer ${token}` },
  signal: controller.signal,
  next: { revalidate: 0 },  // No caching for now — add back later
})
clearTimeout(timeout)
```

### Check 3B: Look at `app/app/layout.tsx`

This layout runs on EVERY page navigation within /app/*. If it has API calls
that are slow or hanging, EVERY page will be slow.

Look for:

```typescript
// This blocks ALL child pages from rendering
export default async function AppLayout({ children }) {
  const api = await createServerApi()

  // ⚠️ If ANY of these hang, the entire app is frozen
  const user = await api.get("/v1/me")
  const account = await api.get("/v1/account")

  return <AppLayoutClient user={user} account={account}>{children}</AppLayoutClient>
}
```

If this exists and ANY of those calls take 13 seconds, you get the exact
symptoms you're seeing.

### Check 3C: Look at `app/app/page.tsx` (Dashboard)

```typescript
// These 3 calls all have to complete before the page renders
const [meRes, dataRes, planUsageRes] = await Promise.all([
  api.get("/v1/me"),
  api.get("/v1/usage"),
  api.get("/v1/account/plan-usage"),
])
```

If any ONE of these hangs for 13 seconds, you get 13s TTFB.

---

## Step 4: Apply Fixes

### Fix 4A: Add Timeout to ALL Server-Side API Calls (DO THIS FIRST)

In `lib/api-server.ts`, wrap every fetch with a timeout so a slow API
can never freeze the entire page:

```typescript
// lib/api-server.ts

const API_TIMEOUT = 10000  // 10 seconds max — fail fast

async function fetchWithTimeout(
  url: string,
  options: RequestInit & { next?: any } = {},
  timeoutMs: number = API_TIMEOUT
): Promise<Response> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    return res
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      console.error(`API call timed out after ${timeoutMs}ms: ${url}`)
      throw new Error(`API timeout: ${url}`)
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}
```

Then use `fetchWithTimeout` instead of `fetch` in all API client methods.

### Fix 4B: Add Error Boundaries So Failed API Calls Don't Blank the Page

Create a global error boundary for the app layout:

```typescript
// app/app/error.tsx
"use client"

import { Button } from "@/components/ui/button"
import { AlertCircle, RefreshCw } from "lucide-react"

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
      <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
        <AlertCircle className="w-6 h-6 text-destructive" />
      </div>
      <h2 className="text-lg font-semibold">Something went wrong</h2>
      <p className="text-sm text-muted-foreground text-center max-w-md">
        We're having trouble loading this page. This is usually temporary.
      </p>
      <Button onClick={reset} variant="outline">
        <RefreshCw className="w-4 h-4 mr-2" />
        Try Again
      </Button>
    </div>
  )
}
```

### Fix 4C: Move Layout API Calls to Be Non-Blocking

If `app/app/layout.tsx` has API calls, restructure so they don't block
page rendering:

```typescript
// BEFORE — blocks everything
export default async function AppLayout({ children }) {
  const api = await createServerApi()
  const user = await api.get("/v1/me")  // ← Blocks ALL pages
  return <AppLayoutClient user={user}>{children}</AppLayoutClient>
}

// AFTER — layout renders immediately, data loads in parallel
export default async function AppLayout({ children }) {
  return (
    <Suspense fallback={<AppShellSkeleton />}>
      <AppLayoutWithData>{children}</AppLayoutWithData>
    </Suspense>
  )
}

async function AppLayoutWithData({ children }) {
  const api = await createServerApi()
  const user = await api.get("/v1/me", { revalidate: 300 })
  return <AppLayoutClient user={user}>{children}</AppLayoutClient>
}
```

Or better — fetch user data client-side in the layout:

```typescript
// AppLayoutClient becomes responsible for its own data
"use client"
import { useEffect, useState } from "react"

export default function AppLayoutClient({ children }) {
  const [user, setUser] = useState(null)

  useEffect(() => {
    fetch("/api/v1/me").then(r => r.json()).then(setUser)
  }, [])

  return (
    <SidebarProvider>
      <DashboardSidebar user={user} />
      <SidebarInset>
        <DashboardTopbar user={user} />
        <main>{children}</main>
      </SidebarInset>
    </SidebarProvider>
  )
}
```

This way the layout shell renders INSTANTLY and user data fills in after.

### Fix 4D: Temporarily Disable Caching to Rule It Out

If Cursor added `next: { revalidate: ... }` or `cache: "force-cache"` to any
fetch calls, temporarily remove ALL of them to see if that's the cause:

```typescript
// Strip all caching options temporarily
const res = await fetch(url, {
  headers: { Authorization: `Bearer ${token}` },
  cache: "no-store",  // Force fresh fetch, no caching
})
```

If the page loads fast after this, caching was misconfigured and you can
add it back carefully.

### Fix 4E: Revert Recent Changes If Nothing Else Works

If the API is healthy (responding in < 1s when hit directly) but the app
is still slow, the code changes from Cursor likely introduced the issue.

```bash
# Check what changed
git log --oneline -20

# Find the commit before the UI upgrade
git diff <before-commit> HEAD -- apps/web/src/lib/api-server.ts
git diff <before-commit> HEAD -- apps/web/src/app/app/layout.tsx
git diff <before-commit> HEAD -- apps/web/src/app/app/page.tsx

# If needed, revert just the API client changes
git checkout <before-commit> -- apps/web/src/lib/api-server.ts
```

---

## Step 5: Verify the Fix

After applying fixes, check LCP again:

1. Hard refresh the page (Ctrl+Shift+R)
2. Open DevTools → Performance tab
3. Click "Record and reload"
4. Check TTFB — should be under 2 seconds
5. Check LCP — should be under 3 seconds

**Target metrics:**

| Metric | Before | Target |
|--------|--------|--------|
| TTFB | 13.4s | < 1.5s |
| LCP | 22.1s | < 2.5s |
| Element render delay | 8.7s | < 0.5s |

---

## Diagnostic Decision Tree

```
Is /health endpoint slow (> 1s)?
├── YES → Render API issue
│   ├── Check Render Events for restarts/crashes
│   ├── Check if service is actually running
│   ├── Check CPU/memory metrics
│   └── Check database connectivity
│
└── NO (health is fast) → Code issue
    ├── Check api-server.ts for broken fetch config
    ├── Check app/layout.tsx for blocking API calls
    ├── Remove all caching options temporarily
    ├── Add timeouts to all fetch calls
    └── If still broken → git revert the API client changes
```
