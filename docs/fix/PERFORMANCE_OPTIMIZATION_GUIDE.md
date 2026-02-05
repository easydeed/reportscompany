# Performance Optimization Guide — Fix Slow Page Loads

> Every page in the app feels slow because the user sees nothing until all API calls complete. This guide fixes that with instant skeletons, smart caching, and reduced API overhead.

---

## The Problem

Current page load chain on every navigation:

```
User clicks link
  → Blank screen (nothing visible)
    → Vercel server fetches from Render API (200-500ms per call)
      → Render API sets RLS context (DB round-trip)
      → Render API runs query (DB round-trip)
    → Vercel renders HTML
  → Page appears all at once
```

Dashboard alone makes 3 parallel API calls. User sees nothing for 1-2+ seconds.

---

## Fix 1: Add `loading.tsx` Skeleton Files (HIGHEST PRIORITY)

Next.js App Router instantly shows `loading.tsx` while the server component fetches data. This eliminates the blank screen. The user sees a skeleton layout within milliseconds of clicking.

**Create a `loading.tsx` file in every route folder listed below.** Each skeleton should match the layout structure of its corresponding `page.tsx`.

### `app/app/loading.tsx` (Dashboard)

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-4 w-64 mt-2" />
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-8 w-8 rounded-lg" />
            </div>
            <Skeleton className="h-8 w-16 mb-1" />
            <Skeleton className="h-3 w-28" />
          </div>
        ))}
      </div>

      {/* Two-column content area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent reports */}
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <Skeleton className="h-5 w-32" />
          </div>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="px-5 py-3 border-b border-border last:border-0 flex items-center justify-between">
              <div className="space-y-1.5">
                <Skeleton className="h-4 w-36" />
                <Skeleton className="h-3 w-24" />
              </div>
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </div>

        {/* Activity chart */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
          <Skeleton className="h-5 w-32 mb-4" />
          <Skeleton className="h-48 w-full rounded-lg" />
        </div>
      </div>
    </div>
  )
}
```

### `app/app/reports/loading.tsx` (Reports List)

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function ReportsLoading() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-44" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        {/* Search bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Skeleton className="h-8 w-64 rounded-md" />
          <Skeleton className="h-8 w-20 rounded-md" />
        </div>

        {/* Table header */}
        <div className="px-4 py-3 border-b border-border bg-muted/30">
          <div className="flex items-center gap-4">
            <Skeleton className="h-3 w-32" />
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-16 ml-auto" />
          </div>
        </div>

        {/* Table rows */}
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-border last:border-0 flex items-center gap-4">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-16 rounded-full ml-auto" />
          </div>
        ))}

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-border flex items-center justify-between">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-8 w-48" />
        </div>
      </div>
    </div>
  )
}
```

### `app/app/property/loading.tsx` (Property Reports List)

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function PropertyReportsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72 mt-2" />
        </div>
        <Skeleton className="h-9 w-44 rounded-md" />
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Skeleton className="h-8 w-64 rounded-md" />
        </div>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-border last:border-0 flex items-center gap-4">
            <Skeleton className="h-4 w-44" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-5 w-16 rounded-full ml-auto" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### `app/app/schedules/loading.tsx` (Schedules List)

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function SchedulesLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <Skeleton className="h-9 w-40 rounded-md" />
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-border last:border-0 flex items-center gap-4">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-8 w-12 rounded-md ml-auto" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### `app/app/lead-page/loading.tsx` (Leads)

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function LeadsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-56 mt-2" />
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Skeleton className="h-8 w-64 rounded-md" />
        </div>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-border last:border-0 flex items-center gap-4">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-5 w-20 rounded-full ml-auto" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### `app/app/people/loading.tsx` (Contacts)

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function ContactsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-36" />
          <Skeleton className="h-4 w-56 mt-2" />
        </div>
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>

      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-border last:border-0 flex items-center gap-4">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-5 w-16 rounded-full ml-auto" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### `app/app/settings/loading.tsx` (Settings — covers all sub-pages)

```tsx
import { Skeleton } from "@/components/ui/skeleton"

export default function SettingsLoading() {
  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-4 w-64 mt-2" />
      </div>

      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <Skeleton className="h-3 w-28 mb-6" />
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-9 w-full rounded-md" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-9 w-full rounded-md" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
```

### Also add loading files for these routes if they have server-side data fetching:

- `app/app/admin/loading.tsx`
- `app/app/affiliate/loading.tsx`
- `app/app/schedules/[id]/loading.tsx`
- `app/app/property/[id]/loading.tsx`

Use the same pattern: match the page layout structure with skeletons.

---

## Fix 2: Cache Stable API Responses

Some data rarely changes and shouldn't be re-fetched on every single navigation.

### What to Cache

| Endpoint | Changes When | Cache Duration |
|----------|-------------|----------------|
| `/v1/me` | User edits profile | 5 minutes (300s) |
| `/v1/account/plan-usage` | Report generated | 2 minutes (120s) |
| `/v1/usage` | Report generated | 2 minutes (120s) |
| `/v1/contacts` (list) | User adds contact | 1 minute (60s) |

### Implementation

**Option A: Next.js `fetch` with `revalidate` (preferred for server components)**

Find the `createServerApi` function in `lib/api-server.ts`. The `api.get()` method likely wraps `fetch()`. Modify it to accept cache options:

```typescript
// lib/api-server.ts

interface FetchOptions {
  revalidate?: number  // Seconds to cache
  tags?: string[]      // For on-demand revalidation
}

export async function createServerApi() {
  const token = /* ... existing token logic ... */

  return {
    // ... existing methods ...

    get: async <T>(path: string, options?: FetchOptions): Promise<T> => {
      const res = await fetch(`${API_BASE}${path}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        next: {
          revalidate: options?.revalidate ?? 0,  // Default: no cache
          tags: options?.tags ?? [],
        },
      })

      if (!res.ok) throw new Error(`API error: ${res.status}`)
      return res.json()
    },

    // ... existing methods ...
  }
}
```

**Then update page calls:**

```typescript
// app/app/page.tsx (Dashboard)
const [meRes, dataRes, planUsageRes] = await Promise.all([
  api.get<any>("/v1/me", { revalidate: 300, tags: ["user-profile"] }),
  api.get<any>("/v1/usage", { revalidate: 120, tags: ["usage"] }),
  api.get<any>("/v1/account/plan-usage", { revalidate: 120, tags: ["plan-usage"] }),
])
```

**Option B: Revalidate on mutation**

After actions that change data (generating a report, updating profile), call `revalidateTag()`:

```typescript
// In server actions or API route handlers
import { revalidateTag } from "next/cache"

// After generating a report
revalidateTag("usage")
revalidateTag("plan-usage")

// After updating profile
revalidateTag("user-profile")
```

### What NOT to Cache

- Report lists (users expect to see new reports immediately)
- Lead data (time-sensitive)
- Schedule details when editing
- Anything on the admin pages

---

## Fix 3: Prefetch Key Routes (Next.js Link Behavior)

Next.js `<Link>` components automatically prefetch in production by default. Make sure you're NOT disabling this.

**Check for anti-patterns:**

```tsx
// ❌ BAD — disables prefetching
<Link href="/app/reports" prefetch={false}>

// ✅ GOOD — prefetches automatically in production
<Link href="/app/reports">

// ✅ ALSO GOOD — force eager prefetch (use for top nav items)
<Link href="/app/reports" prefetch={true}>
```

**In the sidebar navigation**, consider adding explicit `prefetch={true}` on the main nav items since users are very likely to click them:

```tsx
// In DashboardSidebar
{navigation.map((item) => (
  <SidebarMenuButton asChild isActive={isActive}>
    <Link href={item.href} prefetch={true}>
      <item.icon className="w-4 h-4" />
      <span>{item.name}</span>
    </Link>
  </SidebarMenuButton>
))}
```

This means by the time the user moves their cursor to click, the data may already be fetched.

---

## Fix 4: Optimize Render API Cold Starts

### Check Current Render Settings

1. Go to Render Dashboard → your API service
2. Check the **instance type** — "Starter" ($7/mo) keeps the service running 24/7
3. Confirm it's NOT on "Free" tier (which sleeps after 15 min inactivity)

### Add Health Check Endpoint (If Not Already Present)

Render uses health checks to know if the service is alive. Make sure yours is configured:

```python
# Already in your FastAPI app (verify it exists)
@app.get("/health")
async def health():
    return {"status": "ok"}
```

In Render dashboard:
- Set **Health Check Path** to `/health`
- This prevents Render from cycling the service unnecessarily

### Consider: Separate Worker Instance

Your worker (Celery) and API are both on Render. If they're sharing resources, PDF generation tasks could slow down API responses. Verify they're on separate services.

---

## Fix 5: Reduce Redundant API Calls

### Audit: What Gets Called on Every Page

Look at `app/app/layout.tsx` — the server component layout. If it's fetching user data, that call happens on EVERY navigation within `/app/*`, not just the first load.

**Pattern to look for:**

```tsx
// app/app/layout.tsx
export default async function AppLayout({ children }) {
  // ⚠️ This runs on EVERY navigation within /app/*
  const user = await api.get("/v1/me")
  const account = await api.get("/v1/account")

  return (
    <AppLayoutClient user={user} account={account}>
      {children}
    </AppLayoutClient>
  )
}
```

**If this pattern exists, cache these layout-level calls aggressively:**

```tsx
export default async function AppLayout({ children }) {
  const api = await createServerApi()

  const [user, account] = await Promise.all([
    api.get("/v1/me", { revalidate: 300, tags: ["user-profile"] }),
    api.get("/v1/account", { revalidate: 300, tags: ["account"] }),
  ])

  return (
    <AppLayoutClient user={user} account={account}>
      {children}
    </AppLayoutClient>
  )
}
```

With `revalidate: 300`, these calls will be served from cache for 5 minutes instead of hitting Render on every click.

---

## Implementation Order

| Priority | Fix | Impact | Effort |
|----------|-----|--------|--------|
| **1** | Add `loading.tsx` skeleton files | Eliminates perceived blank screen | 30 min |
| **2** | Cache `/v1/me` and plan/usage calls | Cuts 1-2 API calls per navigation | 15 min |
| **3** | Verify Render health check + plan | Eliminates cold starts | 5 min |
| **4** | Add `prefetch={true}` to sidebar links | Pre-loads data before click | 5 min |
| **5** | Audit layout.tsx for redundant fetches | Prevents double-fetching | 15 min |

**Total estimated time: ~1 hour for all fixes**

---

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Time to first visual (perceived) | 1-2+ seconds (blank) | **< 100ms** (skeleton) |
| Dashboard load | 3 API calls, uncached | 3 calls, cached 5 min |
| Navigation between pages | Full re-fetch every time | Cached + prefetched |
| Cold start risk | Possible on low traffic | Eliminated with health check |

The skeleton files alone will make the app feel 10x faster even if actual load times don't change. Users perceive speed based on visual feedback, not raw milliseconds.
