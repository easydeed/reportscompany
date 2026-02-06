# Convert All /app/* Pages to Client-Side Data Fetching

## The Problem

Every page under `/app/*` currently uses Server Components that fetch data from our external API during SSR. Vercel waits 8-12 seconds for the Render API to respond before sending ANY HTML to the browser. The user stares at a blank white screen the entire time.

This is an architectural problem. Server Components are great when your data source is fast (same-region database, edge cache, etc). Ours is a separate Render service that takes seconds to respond. We need to decouple page rendering from API response time.

## The Fix

Convert every `/app/*` page to this pattern:

1. **Thin Server Component** (the page.tsx file) — renders the page shell instantly, no API calls
2. **Client Component** — fetches data after mount, shows skeleton loaders while waiting
3. **Progressive loading** — data fills in as it arrives, page is interactive immediately

## Architecture Pattern

### BEFORE (current — slow)

```tsx
// app/app/affiliate/page.tsx — SERVER COMPONENT
export default async function AffiliatePage() {
  const api = await createServerApi()
  const overview = await api.get('/v1/affiliate/overview')  // ← BLOCKS for 10s
  const accounts = await api.get('/v1/affiliate/accounts')  // ← BLOCKS for 10s
  
  return <AffiliateContent data={overview} accounts={accounts} />
}
```

The page.tsx is an async Server Component. Vercel executes it server-side, waits for ALL API calls to complete, then sends the rendered HTML. If the API takes 10 seconds, the page takes 10 seconds.

### AFTER (new — fast)

```tsx
// app/app/affiliate/page.tsx — THIN SERVER COMPONENT (no API calls)
import { AffiliateDashboard } from './affiliate-dashboard'

export default function AffiliatePage() {
  // NO async, NO API calls, NO await
  // This renders instantly on Vercel and sends HTML to browser
  return <AffiliateDashboard />
}
```

```tsx
// app/app/affiliate/affiliate-dashboard.tsx — CLIENT COMPONENT
'use client'

import { useEffect, useState } from 'react'
import { AffiliateSkeleton } from './affiliate-skeleton'

export function AffiliateDashboard() {
  const [overview, setOverview] = useState(null)
  const [accounts, setAccounts] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [overviewRes, accountsRes] = await Promise.all([
          fetch('/api/proxy/v1/affiliate/overview'),
          fetch('/api/proxy/v1/affiliate/accounts'),
        ])
        
        const overviewData = await overviewRes.json()
        const accountsData = await accountsRes.json()
        
        setOverview(overviewData)
        setAccounts(accountsData)
      } catch (error) {
        console.error('Failed to load affiliate data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  if (loading) return <AffiliateSkeleton />

  return (
    <div>
      {/* Render actual content with overview and accounts data */}
    </div>
  )
}
```

```tsx
// app/app/affiliate/affiliate-skeleton.tsx
export function AffiliateSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Metric cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-28 bg-muted rounded-xl" />
        ))}
      </div>
      {/* Table skeleton */}
      <div className="bg-muted rounded-xl h-64" />
    </div>
  )
}
```

## Pages to Convert

Apply this pattern to EVERY page under `/app/`. Here are the pages and their API calls:

### Priority 1 — Most used pages

**`/app/affiliate/page.tsx`** (affiliate dashboard)
- API calls: `GET /v1/affiliate/overview`, `GET /v1/affiliate/accounts`
- Skeleton: 3 metric cards + accounts table

**`/app/page.tsx`** (main dashboard)
- API calls: `GET /v1/usage`, `GET /v1/account/plan-usage`, `GET /v1/onboarding`
- Skeleton: 4 metric cards + onboarding checklist + plan usage bar

**`/app/reports/page.tsx`** (report list)
- API calls: `GET /v1/reports`
- Skeleton: table rows

**`/app/property/page.tsx`** (property reports list)
- API calls: `GET /v1/property/reports`
- Skeleton: table/card grid

**`/app/schedules/page.tsx`** (schedules list)
- API calls: `GET /v1/schedules`
- Skeleton: table rows

### Priority 2 — Secondary pages

**`/app/leads/page.tsx`** (leads list)
- API calls: `GET /v1/leads`, `GET /v1/leads/stats`
- Skeleton: stats cards + table

**`/app/people/page.tsx`** (contacts)
- API calls: `GET /v1/contacts`, `GET /v1/contact-groups`
- Skeleton: tabs + table

**`/app/settings/profile/page.tsx`**
- API calls: `GET /v1/users/me`
- Skeleton: form fields

**`/app/settings/billing/page.tsx`**
- API calls: `GET /v1/account/plan-usage`
- Skeleton: plan card + usage bar

**`/app/settings/branding/page.tsx`**
- API calls: `GET /v1/account/branding`
- Skeleton: color pickers + logo upload areas

### Priority 3 — Admin pages

**`/app/admin/page.tsx`** and all `/app/admin/*` pages
- Same pattern: thin server wrapper + client component + skeleton

## Implementation Rules

### 1. Page files (page.tsx) must be synchronous

```tsx
// ✅ CORRECT — no async, no await, renders instantly
export default function SomePage() {
  return <SomeClientComponent />
}

// ❌ WRONG — blocks on API
export default async function SomePage() {
  const data = await fetchSomething()
  return <SomeClientComponent data={data} />
}
```

The ONLY exception is if the page needs to read cookies/headers for a redirect (e.g., affiliate redirect). In that case, do the redirect logic only — no data fetching:

```tsx
// ✅ OK — server logic for redirect only, no data fetching
import { cookies } from 'next/headers'
import { jwtDecode } from 'jwt-decode'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value
  
  if (token) {
    const decoded = jwtDecode(token)
    if (decoded.account_type === 'INDUSTRY_AFFILIATE') {
      redirect('/app/affiliate')
    }
  }
  
  return <DashboardContent />
}
```

### 2. Client components handle ALL data fetching

```tsx
'use client'

import { useEffect, useState } from 'react'

export function PageContent() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/proxy/v1/some-endpoint')
        if (!res.ok) throw new Error(`API error: ${res.status}`)
        const json = await res.json()
        setData(json)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <PageSkeleton />
  if (error) return <ErrorState message={error} />
  return <ActualContent data={data} />
}
```

### 3. Use Promise.all for parallel fetches

If a page makes multiple API calls, fire them all at once:

```tsx
const [res1, res2, res3] = await Promise.all([
  fetch('/api/proxy/v1/endpoint-1'),
  fetch('/api/proxy/v1/endpoint-2'),
  fetch('/api/proxy/v1/endpoint-3'),
])
```

### 4. Skeleton components should match the actual layout

Don't use a generic spinner. The skeleton should mirror the real layout so there's no layout shift when data loads:

```tsx
// If the real page has 4 metric cards in a grid:
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
  {[1, 2, 3, 4].map((i) => (
    <div key={i} className="rounded-xl border bg-card p-6 animate-pulse">
      <div className="h-4 w-24 bg-muted rounded mb-2" />
      <div className="h-8 w-16 bg-muted rounded" />
    </div>
  ))}
</div>

// If the real page has a table:
<div className="rounded-xl border bg-card">
  <div className="p-4 border-b">
    <div className="h-5 w-32 bg-muted rounded animate-pulse" />
  </div>
  {[1, 2, 3, 4, 5].map((i) => (
    <div key={i} className="p-4 border-b last:border-0 animate-pulse">
      <div className="h-4 w-full bg-muted rounded" />
    </div>
  ))}
</div>
```

### 5. Handle the existing component structure

Many pages probably pass server-fetched data as props to child components. You need to restructure:

**Before:**
```
page.tsx (server, fetches data) → ContentComponent (receives data as props)
```

**After:**
```
page.tsx (server, NO fetch, renders client wrapper) → ClientWrapper (fetches data, shows skeleton) → ContentComponent (receives data as props, unchanged)
```

The actual content components might not need to change at all — you're just moving WHERE the data comes from (server fetch → client fetch) and adding a loading state wrapper around them.

### 6. API proxy routes

Client-side fetches should go through Next.js API proxy routes (not directly to Render) to include the auth cookie:

```
Browser → /api/proxy/v1/affiliate/overview → Render API
```

Check if proxy routes already exist at `app/api/proxy/` or similar. If they use a catch-all route like `app/api/proxy/[...path]/route.ts`, client-side fetches to `/api/proxy/v1/*` should already work. If not, you'll need to set up the proxy.

### 7. Don't break the layout

The `/app/layout.tsx` file renders the sidebar and header. If it currently fetches user data for the sidebar (user name, avatar, nav items), that ALSO needs to be converted:

- Layout renders the shell (sidebar structure, logo, nav links) synchronously
- A client component inside the layout fetches user info and fills it in
- The sidebar shows a small skeleton for the user's name/avatar while loading

Check if this was already fixed (JWT decode in layout instead of API call). If not, apply the same pattern.

## File Naming Convention

For each page, create these files in the same directory:

```
app/app/affiliate/
  page.tsx                    ← thin server wrapper (exists, modify)
  affiliate-dashboard.tsx     ← new client component
  affiliate-skeleton.tsx      ← new skeleton component

app/app/reports/
  page.tsx                    ← thin server wrapper (modify)
  reports-content.tsx         ← new client component  
  reports-skeleton.tsx        ← new skeleton component

app/app/
  page.tsx                    ← thin server wrapper (modify)
  dashboard-content.tsx       ← new client component
  dashboard-skeleton.tsx      ← new skeleton component
```

## Expected Result

```
BEFORE:
  Navigate to /app/affiliate → 10 second white screen → content appears all at once

AFTER:  
  Navigate to /app/affiliate → instant sidebar + header + skeleton cards → 
  data fills in after API responds → smooth, professional experience
```

Even if the API still takes 10 seconds, the user sees a professional loading state immediately. No more staring at a blank screen.

## Checklist

- [ ] `/app/page.tsx` (dashboard) — converted
- [ ] `/app/affiliate/page.tsx` — converted
- [ ] `/app/reports/page.tsx` — converted
- [ ] `/app/property/page.tsx` — converted
- [ ] `/app/schedules/page.tsx` — converted
- [ ] `/app/leads/page.tsx` — converted
- [ ] `/app/people/page.tsx` — converted
- [ ] `/app/settings/profile/page.tsx` — converted
- [ ] `/app/settings/billing/page.tsx` — converted
- [ ] `/app/settings/branding/page.tsx` — converted
- [ ] `/app/admin/page.tsx` — converted
- [ ] Layout sidebar user info — converted (if not already)
- [ ] All skeletons match actual page layouts
- [ ] No async page.tsx files remain in /app/* (except for redirect-only logic)
- [ ] All client fetches use /api/proxy/ routes
- [ ] Error states handled (show retry button or error message)
- [ ] No layout shift when data loads (skeleton matches real layout)
