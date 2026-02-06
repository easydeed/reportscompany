# Backend Cleanup & Hardening — Cursor Implementation Prompt

## Context

We recently reactivated TrendyReports and made several rapid patches to fix critical issues. Now we need to tighten everything up before onboarding our first paying customer. This prompt covers three tiers of work — do them in order.

**Architecture Reference:**
- `apps/api/` — FastAPI backend (hosted on Render)
- `apps/worker/` — Celery worker (hosted on Render)
- `apps/web/` — Next.js 16 frontend (hosted on Vercel)
- Database: PostgreSQL on Render
- Cache/Broker: Redis on Render
- Storage: Cloudflare R2

---

## TIER 1: Harden Recent Patches (Do First)

### 1A. Keep-Alive Mechanism (Eliminate Cold Starts)

**Problem:** Our FastAPI service on Render's Starter plan spins down after inactivity. Cold starts cause 10-15 second delays, which cascade into 22+ second page loads because our Next.js Server Components call `/v1/me` on every navigation.

**Solution:** Add a periodic keep-alive ping using our existing Celery Beat schedule. Do NOT add external cron services or new dependencies.

**File:** `apps/worker/src/worker/celery_app.py` (or wherever Celery Beat schedule is configured)

Add a beat schedule entry that runs every 5 minutes:

```python
# In the Celery Beat schedule configuration
'keep-alive-ping': {
    'task': 'keep_alive_ping',
    'schedule': 300.0,  # Every 5 minutes
},
```

**File:** `apps/worker/src/worker/tasks.py`

Add the task:

```python
@celery.task(name="keep_alive_ping")
def keep_alive_ping():
    """
    Ping the API health endpoint to prevent Render cold starts.
    Runs every 5 minutes via Celery Beat.
    """
    import httpx
    import os
    
    api_base = os.getenv("API_BASE_URL") or os.getenv("NEXT_PUBLIC_API_BASE") or "http://localhost:10000"
    
    try:
        response = httpx.get(f"{api_base}/health", timeout=10.0)
        logger.info(f"Keep-alive ping: {response.status_code}")
    except Exception as e:
        logger.warning(f"Keep-alive ping failed: {e}")
```

**Important:** 
- The worker itself is already running (it processes Celery tasks), so it won't cold start
- We're using the worker to keep the API warm — the worker pings the API
- Use the internal Render service URL if available (faster than going through the public URL)
- Check if there's already an `API_BASE_URL` or similar env var — use whatever already exists
- If the health endpoint is at a different path (e.g., `/health`, `/healthz`, `/`), use whatever already exists

### 1B. Validate Template Rebuild Wiring

**Problem:** We recently replaced the old standalone template files with a new inheritance-based system. Need to verify everything is correctly wired.

**Files to check:**
- `apps/worker/src/worker/property_builder.py` (or `property_report_builder.py`)
- `apps/worker/src/worker/templates/property/`

**Verify these things:**

1. **Theme mapping is correct** — the builder should map theme IDs to the NEW paths:
```python
# CORRECT mapping (new system):
THEME_TEMPLATES = {
    1: "classic/classic.jinja2",    # NOT "classic_report.jinja2"
    2: "modern/modern.jinja2",      # NOT "modern_report.jinja2"  
    3: "elegant/elegant.jinja2",    # NOT "elegant_report.jinja2"
    4: "teal/teal.jinja2",          # NOT "teal_report.jinja2"
    5: "bold/bold.jinja2",          # NOT "bold_report.jinja2"
}
```
   - **CRITICAL:** Theme 1=Classic, 2=Modern, 3=Elegant, 4=Teal (default), 5=Bold. Do NOT shuffle these.

2. **Jinja2 FileSystemLoader points at the right directory:**
```python
template_dir = Path(__file__).parent / "templates" / "property"
env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=False,
)
```
   - The loader root must be `templates/property/` so that `{% extends '_base/base.jinja2' %}` resolves to `templates/property/_base/base.jinja2`

3. **Custom filters are registered:**
```python
env.filters['format_currency'] = format_currency      # 650000 → "$650,000"
env.filters['format_currency_short'] = format_currency_short  # 1200000 → "$1.2M"
env.filters['format_number'] = format_number            # 2500 → "2,500"
env.filters['truncate'] = truncate_filter               # or whatever the truncate function is named
```

4. **Old template files are deleted** — if any of these still exist, delete them:
   - `templates/property/bold_report.jinja2`
   - `templates/property/classic_report.jinja2`
   - `templates/property/elegant_report.jinja2`
   - `templates/property/modern_report.jinja2`
   - `templates/property/teal_report.jinja2`

5. **New template files exist:**
   - `templates/property/_base/base.jinja2`
   - `templates/property/_base/_macros.jinja2`
   - `templates/property/bold/bold.jinja2`
   - `templates/property/classic/classic.jinja2`
   - `templates/property/elegant/elegant.jinja2`
   - `templates/property/modern/modern.jinja2`
   - `templates/property/teal/teal.jinja2`

### 1C. Validate PDF Engine Configuration

**File:** `apps/worker/src/worker/pdf_engine.py`

**Verify Playwright settings:**
```python
# Playwright margins MUST be 0 — CSS handles margins internally
margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
# Format must be Letter
format="Letter"
# Must include background colors/images
print_background=True
```

**Verify PDFShift settings (do NOT change these, just verify they exist):**
```python
payload = {
    "format": "Letter",
    "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
    "use_print": True,
    "remove_blank": True,
    "delay": 5000,
    "wait_for_network": True,
    "lazy_load_images": True,
    "timeout": 100,
}
# Header must include processor version
headers = {
    "X-Processor-Version": "142"
}
```

---

## TIER 2: Navigation Performance (Do Second)

### 2A. Client-Side Caching with React Query

**Problem:** Every page navigation triggers a full Server Component re-render, which makes fresh API calls. Moving from Market Reports to Affiliate Dashboard takes ~4 seconds because `/v1/me`, `/v1/account/plan-usage`, and page-specific endpoints all get called fresh.

**Solution:** Implement React Query (TanStack Query) for client-side data caching. First visit = API call + cache. Subsequent visits = instant from cache.

**Step 1: Install React Query**

```bash
cd apps/web
npm install @tanstack/react-query
```

**Step 2: Create a QueryClientProvider wrapper**

**File:** `apps/web/src/components/providers/query-provider.tsx`

```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // Cache data for 5 minutes before considering it stale
        staleTime: 5 * 60 * 1000,
        // Keep unused cache for 10 minutes
        gcTime: 10 * 60 * 1000,
        // Don't refetch on window focus (reduces unnecessary API calls)
        refetchOnWindowFocus: false,
        // Retry failed requests once
        retry: 1,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

**Step 3: Wrap the app layout**

**File:** `apps/web/src/app/app/layout.tsx`

Add the `QueryProvider` to the layout. It should wrap the main content area (inside the auth check, outside the sidebar/content).

```tsx
import { QueryProvider } from '@/components/providers/query-provider'

// In the layout component, wrap children:
<QueryProvider>
  {children}
</QueryProvider>
```

**Step 4: Create shared query hooks**

**File:** `apps/web/src/lib/hooks/use-user.ts`

```tsx
'use client'

import { useQuery } from '@tanstack/react-query'

async function fetchUser() {
  const res = await fetch('/api/proxy/v1/me', {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to fetch user')
  return res.json()
}

export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: fetchUser,
    staleTime: 10 * 60 * 1000, // User data rarely changes — cache 10 min
  })
}
```

**File:** `apps/web/src/lib/hooks/use-plan-usage.ts`

```tsx
'use client'

import { useQuery } from '@tanstack/react-query'

async function fetchPlanUsage() {
  const res = await fetch('/api/proxy/v1/account/plan-usage', {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to fetch plan usage')
  return res.json()
}

export function usePlanUsage() {
  return useQuery({
    queryKey: ['plan-usage'],
    queryFn: fetchPlanUsage,
    staleTime: 5 * 60 * 1000,
  })
}
```

**Step 5: Convert key pages from Server Components to Client Components where it makes sense**

The goal is NOT to convert everything — only the data-fetching parts of pages that users navigate between frequently. The layout shell, sidebar, and static content should remain Server Components.

**Pattern to follow:**

For pages like `/app` (dashboard), `/app/reports`, `/app/schedules`, etc.:

1. Keep the page.tsx as a Server Component for the shell/layout
2. Extract the data-dependent content into a Client Component that uses the React Query hooks
3. The Client Component reads from cache on subsequent visits

```tsx
// apps/web/src/app/app/page.tsx (Server Component — just the shell)
import { DashboardContent } from '@/components/dashboard/dashboard-content'

export default function DashboardPage() {
  return <DashboardContent />
}

// apps/web/src/components/dashboard/dashboard-content.tsx (Client Component)
'use client'

import { useUser } from '@/lib/hooks/use-user'
import { usePlanUsage } from '@/lib/hooks/use-plan-usage'

export function DashboardContent() {
  const { data: user, isLoading: userLoading } = useUser()
  const { data: planUsage, isLoading: planLoading } = usePlanUsage()

  if (userLoading || planLoading) {
    return <DashboardSkeleton />  // Show loading skeleton
  }

  return (
    // ... existing dashboard content using user and planUsage data
  )
}
```

**Important considerations:**
- The sidebar already has user data (name, avatar, account type). If it currently fetches this server-side, consider having it also use the `useUser()` hook so it shares the same cache.
- Don't convert the wizards (report builder, schedule builder, property report wizard) — they already work well and don't have navigation performance issues.
- Focus on: Dashboard, Reports list, Schedules list, Leads list, Contacts list, Settings pages, Affiliate dashboard.
- Keep loading skeletons/spinners consistent with the existing UI patterns.

### 2B. Prefetch on Hover (Optional Enhancement)

Once React Query is in place, you can add prefetching when users hover over sidebar links:

```tsx
// In the sidebar nav component
import { useQueryClient } from '@tanstack/react-query'

const queryClient = useQueryClient()

function handleHover(route: string) {
  // Prefetch the data for the hovered route
  if (route === '/app') {
    queryClient.prefetchQuery({ queryKey: ['user'], queryFn: fetchUser })
  }
  // ... etc for other routes
}
```

This makes navigation feel truly instant. Implement this AFTER the basic caching is working.

---

## TIER 3: Backend Hygiene (Do Third)

### 3A. Audit Comparables Data Flow

**Problem:** The comparables section in property reports was previously showing Google Maps embeds instead of property data cards. Need to verify this is fixed.

**Files:**
- `apps/worker/src/worker/property_builder.py` — where comparables context is built
- `apps/worker/src/worker/templates/property/_base/base.jinja2` — comparables page structure
- `apps/worker/src/worker/templates/property/_base/_macros.jinja2` — comp card macro

**What to check:**

1. In the builder, verify that `comparables` is a list of dicts with these keys:
```python
{
    "address": "123 Oak Ave",
    "sale_price": 725000,        # Must be a number, not a string
    "sold_date": "01/15/2024",
    "sqft": 2100,
    "bedrooms": 4,
    "bathrooms": 2,
    "year_built": 1992,
    "price_per_sqft": 345,       # Calculated: sale_price / sqft
    "distance_miles": 0.3,
    "lot_size": 7800,
    "pool": True,
    "map_image_url": "https://maps.googleapis.com/...",  # Small satellite image of THIS comp
}
```

2. Verify the template renders comp CARDS (not map embeds). The comp card should show:
   - Property address
   - Sale price (formatted)
   - Beds/baths/sqft
   - Year built
   - Price per sqft
   - A small map thumbnail (NOT a full Google Maps embed)

3. The comp card layout should be a 2x2 grid showing up to 4 comps per page. Check the `{% for comp in comparables[:4] %}` loop in the base template.

### 3B. Verify Image URLs Are Populated

**Problem:** Property reports need visual richness — hero images, aerial maps, agent photos, comp map thumbnails. If any of these are missing, the report looks bare.

**Files:**
- `apps/worker/src/worker/property_builder.py` — where the `images` dict is built
- `apps/api/src/api/routes/property.py` — where property data is fetched

**Verify the context includes:**

```python
"images": {
    "hero": "https://...",        # Cover page background (property photo from MLS)
    "aerial_map": "https://maps.googleapis.com/maps/api/staticmap?..."  # Aerial view
}
```

For the aerial map, verify the Google Maps Static API URL is built correctly:
```python
aerial_map_url = (
    f"https://maps.googleapis.com/maps/api/staticmap"
    f"?center={lat},{lng}"
    f"&zoom=15&size=800x600&maptype=satellite"  # or 'roadmap'
    f"&markers=color:0x1e3a5f%7C{lat},{lng}"
    f"&key={GOOGLE_MAPS_API_KEY}"
)
```

- If `lat`/`lng` aren't available from the property data, the aerial page should gracefully degrade (show a placeholder or skip)
- If `hero` image isn't available from MLS photos, the cover page should still look good with just the color/gradient background
- Each comp should have its own `map_image_url` — a small satellite thumbnail centered on that comp's location

**Verify agent data includes:**
```python
"agent": {
    "photo_url": "https://...",   # Agent headshot (from user profile)
    "logo_url": "https://...",    # Company logo (from branding settings)
}
```

- If `photo_url` is None, templates should show initials or a placeholder
- If `logo_url` is None, templates should show company name as text

### 3C. Clean Up Middleware Timeout Patches

**Problem:** We added emergency 5-second timeouts in two places to prevent page hangs. With the keep-alive in place (Tier 1A), these become less critical but should remain as safety nets. However, they should be cleaned up.

**File:** `apps/web/src/middleware.ts`

**Verify:**
- There's an `AbortController` with a 5-second timeout on the admin role check (`/v1/me`)
- On timeout, it should allow the request through (fail open) rather than blocking the user
- Error logging exists so we can monitor if timeouts still occur

```typescript
// Pattern should look like:
const controller = new AbortController()
const timeoutId = setTimeout(() => controller.abort(), 5000)

try {
  const response = await fetch(`${API_BASE}/v1/me`, {
    headers: { Cookie: `mr_token=${token}` },
    signal: controller.signal,
  })
  clearTimeout(timeoutId)
  // ... check admin role
} catch (error) {
  clearTimeout(timeoutId)
  // On timeout/error: allow through (don't block)
  console.error('Middleware timeout:', error)
  return NextResponse.next()
}
```

**File:** `apps/web/src/app/app/layout.tsx`

**Same pattern** — verify the `/v1/me` call in the layout has timeout protection and fails gracefully (renders the layout without user data rather than hanging).

### 3D. API Error Handling Audit

Do a quick scan of these API route files and verify they have proper error handling:

**Files:**
- `apps/api/src/api/routes/property.py`
- `apps/api/src/api/routes/reports.py`
- `apps/api/src/api/routes/schedules.py`

**Check for:**
1. All external API calls (SimplyRETS, SiteX, Google Maps) have timeouts set:
```python
# Should have explicit timeouts
response = await httpx.get(url, timeout=10.0)
# or
async with httpx.AsyncClient(timeout=10.0) as client:
```

2. Failed external calls return meaningful errors, not 500s:
```python
try:
    data = await fetch_from_simplyrets(params)
except httpx.TimeoutException:
    raise HTTPException(504, "MLS data provider timeout — please retry")
except httpx.HTTPError as e:
    raise HTTPException(502, f"MLS data provider error: {str(e)}")
```

3. Celery task failures are logged and don't silently swallow errors:
```python
@celery.task(bind=True, max_retries=3)
def generate_report(self, run_id, ...):
    try:
        # ... work
    except Exception as e:
        # Update DB status to 'failed' with error message
        update_report_status(run_id, status='failed', error_message=str(e))
        # Then retry
        self.retry(exc=e, countdown=60)
```

---

## Summary Checklist

After completing all three tiers, verify:

- [ ] Celery Beat has keep-alive task running every 5 minutes
- [ ] Keep-alive task pings API `/health` endpoint
- [ ] Template mapping: 1=Classic, 2=Modern, 3=Elegant, 4=Teal, 5=Bold
- [ ] Jinja2 loader root is `templates/property/`
- [ ] Old standalone template files deleted
- [ ] Playwright margins set to 0
- [ ] PDFShift config unchanged (delay 5000, wait_for_network, processor 142)
- [ ] React Query installed and QueryProvider wrapping app
- [ ] `useUser()` and `usePlanUsage()` hooks created
- [ ] Key list pages converted to use cached client-side data
- [ ] Comparables render as property cards (not Google Maps embeds)
- [ ] Hero image, aerial map, agent photo, comp thumbnails all populate
- [ ] Middleware timeout patches in place with fail-open behavior
- [ ] External API calls have explicit timeouts
- [ ] Celery tasks update DB status to 'failed' on errors

---

## Important Notes

- **Do NOT touch the template files themselves** (`_base/base.jinja2`, `_macros.jinja2`, theme files) — they're a coordinated design system.
- **Do NOT change PDFShift configuration** — only verify it.
- **Do NOT convert the wizards to use React Query** — they already work well. Focus on list pages and dashboard.
- **Keep the middleware timeouts** even after keep-alive is working — they're safety nets.
- **Use existing env vars** wherever possible — don't add new ones unless absolutely necessary.
