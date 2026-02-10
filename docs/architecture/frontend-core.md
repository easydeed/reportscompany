# Frontend Core

> `apps/web/` -- Next.js 16 application core: config, middleware, API clients, hooks, providers

---

## next.config.ts -- Next.js Configuration

- React Compiler enabled
- Experimental external dir support
- Turbopack root config

---

## middleware.ts -- Auth Guard

Runs on every request matching `/app/*` routes.

**Logic:**
- Reads `mr_token` cookie
- Decodes JWT (without full verification -- just parsing claims)
- If no token or expired: redirects to `/login`
- For `/app/admin/*` paths: checks `role` claim for admin access
- Sets headers for downstream use

---

## lib/api.ts -- Client-Side API Client

Used by React components for data fetching.

**How it works:** All client-side API calls route through `/api/proxy/...` Next.js API routes to avoid CORS. The proxy forwards the request to the FastAPI backend with the auth cookie attached.

**Typical usage:**
```typescript
const data = await api('/v1/reports', { method: 'GET' })
```

---

## lib/api-server.ts -- Server-Side API Client

Used by Next.js Server Components and API routes.

**How it works:** Makes direct HTTP requests to the backend API URL (bypasses the proxy). Authenticates by reading the `mr_token` cookie from the incoming request.

---

## lib/get-api-base.ts -- API Base URL

Returns the backend API base URL. Uses environment variable `NEXT_PUBLIC_API_URL` or falls back to localhost.

---

## lib/utils.ts -- Utilities

- `cn()` -- Tailwind class merging via `clsx` + `tailwind-merge`
- Other shared helpers

---

## lib/hooks/use-user.ts -- User Hook

React Query hook for fetching the current authenticated user.

```typescript
const { data: user, isLoading } = useUser()
// user: { id, email, role, account_type, account_id, is_platform_admin }
```

- Fetches from `/v1/me`
- Cached by React Query (5min stale time)
- Returns user object with role, account_type, is_platform_admin

---

## lib/hooks/use-plan-usage.ts -- Plan Usage Hook

React Query hook for fetching plan usage data.

```typescript
const { data: planUsage } = usePlanUsage()
// planUsage: { usage, plan, limit_decision, catalog }
```

- Fetches from `/v1/account/plan-usage`
- Used by dashboard and settings pages
- This is the endpoint with the Stripe performance issue [C3]

---

## hooks/useGooglePlaces.ts -- Google Places

Hook for Google Places autocomplete integration. Used by property search and report builder area selection.

---

## hooks/use-toast.ts -- Toast Notifications

Hook for triggering toast notifications (uses Sonner under the hood).

---

## components/providers/query-provider.tsx -- React Query Provider

Wraps the app with `QueryClientProvider`. Configuration:
- `staleTime: 5 * 60 * 1000` (5 minutes)
- `refetchOnWindowFocus: false`
- `retry: 1`

---

## app/app-layout.tsx -- App Layout Client

Client component that wraps all `/app/*` routes. Provides:
- `QueryProvider` (React Query)
- App shell / sidebar layout via `AppLayoutClient`

---

## Data & Templates

| File | Purpose |
|------|---------|
| `lib/templates.ts` | Report template definitions (type, name, description) |
| `lib/social-templates.ts` | Social media post templates |
| `lib/sample-report-data.ts` | Sample data for report previews |
| `lib/property-report-assets.ts` | Property report asset references |
| `lib/wizard-types.ts` | TypeScript types for wizard flows |
