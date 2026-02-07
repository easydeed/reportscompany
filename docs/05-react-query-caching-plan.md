# TrendyReports Frontend Caching — React Query Implementation Plan

## The Problem

Every page navigation under `/app/*` triggers fresh API calls through the proxy chain:

```
Browser → Vercel (/api/proxy/v1/...) → Render API → PostgreSQL → back
```

Even though the API is now fast (~200ms), the double network hop (browser→Vercel→Render) adds ~400-800ms per request. Pages that make 2-3 parallel fetches wait ~1-2 seconds on every navigation — even when the user is returning to a page they just visited 5 seconds ago.

**Current behavior:** Click "Reports" → 1-2s load → Click "Schedules" → 1-2s load → Click "Reports" again → 1-2s load (re-fetches everything)

**Target behavior:** Click "Reports" → 1-2s load → Click "Schedules" → 1-2s load → Click "Reports" again → **instant** (cached) → data quietly refreshes in background

## Why React Query

Your pages are already `'use client'` components that fetch via `useEffect` + `fetch()`. React Query replaces the manual `useEffect` + `useState` + `setLoading` + `setError` pattern with a single `useQuery()` hook that adds:

- **Caching:** Data persists across navigations. Returning to a page is instant.
- **Stale-while-revalidate:** Shows cached data immediately, refreshes in background.
- **Deduplication:** Multiple components requesting the same data = 1 fetch.
- **Automatic refetch:** Refetches on window focus, reconnect, or custom intervals.
- **Built-in loading/error states:** Replaces your manual `loading`/`error` useState.

No architecture change needed — your pages stay as client components, your proxy routes stay, your API stays. This is purely additive.

---

## Phase 1: Install and Configure React Query

### 1a. Install

```bash
cd apps/web
npm install @tanstack/react-query
```

### 1b. Create the Query Client Provider

**Create: `apps/web/src/lib/query-provider.tsx`**

```tsx
"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Show cached data immediately, refetch in background after 2 min
            staleTime: 2 * 60 * 1000,       // Data is "fresh" for 2 minutes
            gcTime: 10 * 60 * 1000,          // Keep unused cache for 10 minutes
            refetchOnWindowFocus: true,       // Refresh when user tabs back
            refetchOnReconnect: true,         // Refresh on network recovery
            retry: 2,                         // Retry failed requests twice
            retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 5000),
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

**Key settings explained:**

| Setting | Value | Why |
|---------|-------|-----|
| `staleTime: 2min` | Data is considered fresh for 2 minutes | Navigating between pages within 2 min = instant, no refetch |
| `gcTime: 10min` | Cached data lives for 10 minutes | Even if unused, cache persists for back-navigation |
| `refetchOnWindowFocus` | `true` | User tabs away for a meeting, tabs back = fresh data |
| `retry: 2` | 2 retries on failure | Handles transient proxy/network errors |

### 1c. Wire into the App Layout

**Edit: `apps/web/src/app/app-layout.tsx`** (the client layout component)

Wrap the existing content with `QueryProvider`:

```tsx
import { QueryProvider } from "@/lib/query-provider"

export default function AppLayoutClient({ 
  children, 
  isAdmin, 
  isAffiliate, 
  accountType 
}: { 
  children: React.ReactNode
  isAdmin: boolean
  isAffiliate: boolean
  accountType: string
}) {
  return (
    <QueryProvider>
      {/* ... existing sidebar + main content layout ... */}
      {children}
    </QueryProvider>
  )
}
```

**Important:** The `QueryProvider` goes inside `AppLayoutClient` (the client component), NOT in the server layout. This keeps the provider in the client tree where it belongs.

### Verification

After Phase 1, nothing changes visually. Pages still work exactly as before. You're just adding the plumbing. Verify the app loads without errors.

---

## Phase 2: Create Shared API Hooks

**Create: `apps/web/src/hooks/use-api.ts`**

This replaces the manual `useEffect` + `useState` pattern across all pages:

```ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

// ============================================================================
// Core fetch function (reuses your existing proxy pattern)
// ============================================================================

async function apiFetchRQ(path: string, init?: RequestInit) {
  const res = await fetch(`/api/proxy${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    credentials: "include",
  })

  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`API ${res.status}: ${text}`)
  }

  return res.json()
}

// ============================================================================
// Query Key Factory
// Organized key structure prevents cache collisions and enables targeted
// invalidation (e.g., invalidate all "reports" queries at once).
// ============================================================================

export const queryKeys = {
  // User / Account
  me: ["me"] as const,
  planUsage: ["plan-usage"] as const,
  onboarding: ["onboarding"] as const,
  branding: ["branding"] as const,

  // Reports
  reports: {
    all: ["reports"] as const,
    list: (filters?: Record<string, string>) =>
      ["reports", "list", filters ?? {}] as const,
    detail: (id: string) => ["reports", "detail", id] as const,
  },

  // Property Reports
  propertyReports: {
    all: ["property-reports"] as const,
    list: () => ["property-reports", "list"] as const,
    detail: (id: string) => ["property-reports", "detail", id] as const,
  },

  // Schedules
  schedules: {
    all: ["schedules"] as const,
    list: () => ["schedules", "list"] as const,
    detail: (id: string) => ["schedules", "detail", id] as const,
  },

  // Contacts
  contacts: {
    all: ["contacts"] as const,
    list: () => ["contacts", "list"] as const,
    groups: () => ["contacts", "groups"] as const,
  },

  // Leads
  leads: {
    all: ["leads"] as const,
    list: (filters?: Record<string, string>) =>
      ["leads", "list", filters ?? {}] as const,
    stats: () => ["leads", "stats"] as const,
  },

  // Affiliate
  affiliate: {
    overview: ["affiliate", "overview"] as const,
    accounts: ["affiliate", "accounts"] as const,
    detail: (id: string) => ["affiliate", "detail", id] as const,
  },
} as const

// ============================================================================
// Hooks — Each replaces a useEffect + useState + setLoading + setError block
// ============================================================================

/** Current user profile */
export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => apiFetchRQ("/v1/me"),
    staleTime: 5 * 60 * 1000, // Profile rarely changes — 5 min
  })
}

/** Plan usage (shown on dashboard + sidebar) */
export function usePlanUsage() {
  return useQuery({
    queryKey: queryKeys.planUsage,
    queryFn: () => apiFetchRQ("/v1/account/plan-usage"),
    staleTime: 2 * 60 * 1000,
  })
}

/** Onboarding status */
export function useOnboarding() {
  return useQuery({
    queryKey: queryKeys.onboarding,
    queryFn: () => apiFetchRQ("/v1/onboarding"),
    staleTime: 5 * 60 * 1000,
  })
}

/** Market reports list */
export function useReports() {
  return useQuery({
    queryKey: queryKeys.reports.list(),
    queryFn: () => apiFetchRQ("/v1/reports"),
  })
}

/** Property reports list */
export function usePropertyReports() {
  return useQuery({
    queryKey: queryKeys.propertyReports.list(),
    queryFn: () => apiFetchRQ("/v1/property/reports?limit=100"),
  })
}

/** Schedules list */
export function useSchedules() {
  return useQuery({
    queryKey: queryKeys.schedules.list(),
    queryFn: () => apiFetchRQ("/v1/schedules"),
  })
}

/** Contacts list */
export function useContacts() {
  return useQuery({
    queryKey: queryKeys.contacts.list(),
    queryFn: () => apiFetchRQ("/v1/contacts"),
  })
}

/** Contact groups */
export function useContactGroups() {
  return useQuery({
    queryKey: queryKeys.contacts.groups(),
    queryFn: () => apiFetchRQ("/v1/contact-groups"),
  })
}

/** Leads with optional filters */
export function useLeads(filters?: Record<string, string>) {
  const params = filters
    ? "?" + new URLSearchParams(filters).toString()
    : ""
  return useQuery({
    queryKey: queryKeys.leads.list(filters),
    queryFn: () => apiFetchRQ(`/v1/leads${params}`),
  })
}

/** Lead stats */
export function useLeadStats() {
  return useQuery({
    queryKey: queryKeys.leads.stats(),
    queryFn: () => apiFetchRQ("/v1/leads/stats"),
  })
}

/** Affiliate overview */
export function useAffiliateOverview() {
  return useQuery({
    queryKey: queryKeys.affiliate.overview,
    queryFn: () => apiFetchRQ("/v1/affiliate/overview"),
  })
}

/** Branding settings */
export function useBranding() {
  return useQuery({
    queryKey: queryKeys.branding,
    queryFn: () => apiFetchRQ("/v1/account/branding"),
    staleTime: 5 * 60 * 1000,
  })
}

// ============================================================================
// Cache Invalidation Helper
// Use after mutations (create report, delete schedule, etc.)
// ============================================================================

export function useInvalidate() {
  const qc = useQueryClient()
  return {
    /** Invalidate all queries matching a key prefix */
    invalidate: (...key: readonly unknown[]) => qc.invalidateQueries({ queryKey: key }),
    /** Invalidate specific common groups */
    reports: () => qc.invalidateQueries({ queryKey: queryKeys.reports.all }),
    propertyReports: () => qc.invalidateQueries({ queryKey: queryKeys.propertyReports.all }),
    schedules: () => qc.invalidateQueries({ queryKey: queryKeys.schedules.all }),
    contacts: () => qc.invalidateQueries({ queryKey: queryKeys.contacts.all }),
    leads: () => qc.invalidateQueries({ queryKey: queryKeys.leads.all }),
    planUsage: () => qc.invalidateQueries({ queryKey: queryKeys.planUsage }),
  }
}
```

### Verification

Import one hook in any page to confirm it compiles. No page changes yet.

---

## Phase 3: Migrate Pages (One at a Time)

Each migration follows the same pattern: replace `useEffect` + `useState` + `fetch` with `useQuery`. The page's JSX stays identical.

### Migration Template

**Before (current pattern):**
```tsx
export default function SomePage() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch('/api/proxy/v1/something', {
          credentials: 'include',
          cache: 'no-store',
        })
        if (!res.ok) { setError(true); return }
        const json = await res.json()
        setData(json.items || [])
      } catch { setError(true) }
      finally { setLoading(false) }
    }
    fetchData()
  }, [])

  if (loading) return <Skeleton />
  if (error) return <ErrorBanner />
  return <Content data={data} />
}
```

**After (React Query):**
```tsx
import { useSomething } from "@/hooks/use-api"

export default function SomePage() {
  const { data, isLoading, error } = useSomething()

  if (isLoading) return <Skeleton />
  if (error) return <ErrorBanner />
  return <Content data={data?.items || []} />
}
```

**That's it.** The JSX doesn't change. The skeleton doesn't change. The error handling doesn't change. You're just replacing the data-fetching plumbing.

### 3a. Reports Page (`/app/reports/page.tsx`)

```tsx
'use client'

import { useReports } from "@/hooks/use-api"
// ... all existing imports stay ...

export default function ReportsPage() {
  const { data, isLoading, error } = useReports()
  const reports: Report[] = data?.reports || []

  // Everything below is identical to current code,
  // just replace:
  //   loading     → isLoading
  //   error       → !!error
  //   reports     → reports (from above)
  // Remove: useState for reports/loading/error
  // Remove: the entire useEffect block

  return (
    <div className="space-y-5">
      {/* ... identical JSX ... */}
    </div>
  )
}
```

### 3b. Schedules Page (`/app/schedules/page.tsx`)

```tsx
'use client'

import { useSchedules } from "@/hooks/use-api"

export default function SchedulesPage() {
  const { data, isLoading } = useSchedules()
  const schedules = Array.isArray(data)
    ? data
    : Array.isArray(data?.schedules)
    ? data.schedules
    : []

  if (isLoading) return <SchedulesSkeleton />
  return <SchedulesListShell schedules={schedules} />
}
```

### 3c. Property Reports Page (`/app/property/page.tsx`)

```tsx
'use client'

import { usePropertyReports, useInvalidate } from "@/hooks/use-api"

export default function PropertyReportsPage() {
  const { data, isLoading, error } = usePropertyReports()
  const invalidate = useInvalidate()

  const allReports: PropertyReport[] = data?.reports || []
  const [statusFilter, setStatusFilter] = useState("all")

  // Stats computed from cached data (no second API call)
  const stats = useMemo(() => {
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    return {
      total: allReports.length,
      thisMonth: allReports.filter(r => new Date(r.created_at) >= startOfMonth).length,
      processing: allReports.filter(r => r.status === "processing").length,
      complete: allReports.filter(r => r.status === "complete").length,
    }
  }, [allReports])

  // Client-side filter (no API call)
  const reports = statusFilter !== "all"
    ? allReports.filter(r => r.status === statusFilter)
    : allReports

  async function deleteReport(id: string) {
    await apiFetch(`/v1/property/reports/${id}`, { method: "DELETE" })
    invalidate.propertyReports()  // Refreshes the list from cache
  }

  // ... rest of JSX identical ...
}
```

### 3d. Affiliate Dashboard (`/app/affiliate/page.tsx`)

```tsx
'use client'

import { useAffiliateOverview, usePlanUsage, useOnboarding } from "@/hooks/use-api"

export default function AffiliateDashboardPage() {
  const { data: affiliateData, isLoading: affLoading, error: affError } = useAffiliateOverview()
  const { data: planUsage } = usePlanUsage()
  const { data: onboardingData } = useOnboarding()

  const loading = affLoading
  const error = affError
    ? affiliateData === undefined ? "load_failed" : null
    : null

  // Check for 403 (not affiliate) — useAffiliateOverview will throw
  // Handle in error state

  if (loading) return <AffiliateSkeleton />
  if (error) return <ErrorState />

  // ... rest of JSX identical, just read from the hook data ...
}
```

### 3e. Dashboard Page (`/app/page.tsx` → `DashboardContent`)

The dashboard page already renders `<DashboardContent />`. Inside that client component, replace its `useEffect` fetches with:

```tsx
import { useMe, usePlanUsage, useOnboarding } from "@/hooks/use-api"

function DashboardContent() {
  const { data: user } = useMe()
  const { data: planUsage } = usePlanUsage()
  const { data: onboarding } = useOnboarding()

  // ... existing rendering logic ...
}
```

### Migration Order

Migrate one page at a time, deploy, verify, then move to the next:

```
1. Reports page        (simplest — single fetch)
2. Schedules page      (simple — single fetch)
3. Property reports    (medium — has delete mutation)
4. Affiliate dashboard (medium — 3 parallel fetches)
5. Dashboard           (medium — DashboardContent component)
6. Leads page          (has filters)
7. Contacts/People     (has tabs)
```

---

## Phase 4: Invalidate Cache After Mutations

When the user creates, updates, or deletes something, the cached list needs to refresh. Use `useInvalidate()` after mutations:

```tsx
import { useInvalidate } from "@/hooks/use-api"

// In report builder, after successful generation:
const invalidate = useInvalidate()

async function onReportGenerated() {
  invalidate.reports()        // Refetches report list in background
  invalidate.planUsage()      // Usage count changed
}

// In schedule builder, after create/update:
async function onScheduleSaved() {
  invalidate.schedules()
}

// After deleting a property report:
async function onDelete(id: string) {
  await apiFetch(`/v1/property/reports/${id}`, { method: "DELETE" })
  invalidate.propertyReports()
}

// After updating branding:
async function onBrandingSaved() {
  invalidate.invalidate("branding")
}
```

**Where to add invalidation calls:**

| Action | Invalidate |
|--------|-----------|
| Create market report | `reports`, `planUsage` |
| Create property report | `propertyReports`, `planUsage` |
| Create/update schedule | `schedules` |
| Delete report | `reports` or `propertyReports` |
| Delete schedule | `schedules` |
| Update contacts | `contacts` |
| Update branding | `branding` |
| Complete onboarding step | `onboarding` |

---

## Phase 5 (Optional): Prefetch on Hover

For the ultimate snappy feel — prefetch data when the user hovers over a sidebar link:

```tsx
import { useQueryClient } from "@tanstack/react-query"
import { queryKeys } from "@/hooks/use-api"

function SidebarLink({ href, label, queryKey, fetchFn }) {
  const qc = useQueryClient()

  return (
    <Link
      href={href}
      prefetch={false}  // Keep Next.js prefetch off
      onMouseEnter={() => {
        // Prefetch data when user hovers (before they click)
        qc.prefetchQuery({
          queryKey,
          queryFn: fetchFn,
          staleTime: 2 * 60 * 1000,
        })
      }}
    >
      {label}
    </Link>
  )
}
```

This means by the time the user clicks, the data is already in cache. Navigation feels instant even on first visit.

---

## What NOT to Change

1. **The proxy routes** — Keep `/api/proxy/v1/...`. They solve CORS and you can't call Render directly from the browser.
2. **The `/app/layout.tsx` server component** — It only decodes the JWT (no API calls). Leave it as-is.
3. **The `api-server.ts` file** — Used by any remaining server components. Keep for backwards compatibility.
4. **Wizard pages** (report builder, schedule builder, property report wizard) — These are multi-step forms with their own state. Don't add React Query to wizard internals. Only use it for the initial data load if the wizard needs to pre-fetch contacts, templates, etc.
5. **`export const dynamic = 'force-dynamic'`** — Keep this on the server layout. It ensures the JWT cookie is always read fresh.

---

## Expected Results

| Scenario | Before | After |
|----------|--------|-------|
| First page load (cold) | ~2s | ~1-1.5s (same, but skeleton shows instantly) |
| Navigate to visited page | ~2s | **Instant** (<100ms, cached) |
| Navigate to new page | ~2s | ~1-1.5s (same, first fetch) |
| Tab away and come back | ~2s full reload | Instant show + background refresh |
| After creating a report | Navigate away + back = stale | Invalidation triggers fresh fetch |
| Hover prefetch (Phase 5) | N/A | Even first visits feel instant |

**The big win:** Returning to any previously visited page goes from ~2 seconds to instant. For a user clicking between Reports → Schedules → Dashboard → Reports, this eliminates 6+ seconds of cumulative wait time per session.

---

## Stale Time Recommendations by Endpoint

| Endpoint | `staleTime` | Rationale |
|----------|-------------|-----------|
| `/v1/me` | 5 min | Profile changes rarely |
| `/v1/account/plan-usage` | 2 min | Changes on report generation |
| `/v1/onboarding` | 5 min | Changes on step completion |
| `/v1/reports` | 2 min (default) | New reports appear after generation |
| `/v1/schedules` | 2 min (default) | Changes on create/edit/delete |
| `/v1/property/reports` | 2 min (default) | Changes on create/delete |
| `/v1/contacts` | 2 min (default) | Changes on add/import/delete |
| `/v1/leads` | 2 min (default) | New leads arrive from public pages |
| `/v1/affiliate/overview` | 2 min (default) | Sponsored account activity |
| `/v1/account/branding` | 5 min | Changes rarely |

---

## Files Changed Summary

| File | Action | Phase |
|------|--------|-------|
| `package.json` | Add `@tanstack/react-query` | 1 |
| `src/lib/query-provider.tsx` | **New** — QueryClient provider | 1 |
| `src/app/app-layout.tsx` | Wrap children with `<QueryProvider>` | 1 |
| `src/hooks/use-api.ts` | **New** — All query hooks + invalidation | 2 |
| `src/app/app/reports/page.tsx` | Replace useEffect with useReports() | 3 |
| `src/app/app/schedules/page.tsx` | Replace useEffect with useSchedules() | 3 |
| `src/app/app/property/page.tsx` | Replace useEffect with usePropertyReports() | 3 |
| `src/app/app/affiliate/page.tsx` | Replace useEffect with 3 hooks | 3 |
| `src/components/dashboard/dashboard-content.tsx` | Replace useEffect with hooks | 3 |
| Various wizard/builder files | Add invalidation calls after mutations | 4 |
