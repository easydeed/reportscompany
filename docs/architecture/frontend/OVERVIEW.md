# Frontend Service

> `apps/web/` -- Next.js 16 application (React 19)

## Architecture

- **Framework:** Next.js 16 with App Router
- **React:** 19.2.0 with React Compiler enabled
- **UI Library:** Radix UI + shadcn/ui (57 components in `components/ui/`)
- **Styling:** Tailwind CSS v4
- **State Management:** TanStack React Query v5 (5min stale time, 10min GC, no window focus refetch, 1 retry)
- **Forms:** React Hook Form + Zod validation
- **Auth:** JWT via `mr_token` cookie, checked in Next.js middleware
- **API Pattern:** Client-side calls route through `/api/proxy/v1/*` to avoid CORS
- **Hosting:** Vercel

## API Communication

### Client-Side (React components)
```
Component -> lib/api.ts -> /api/proxy/v1/endpoint -> FastAPI backend
```
The `apiFetch()` function in `lib/api.ts` routes all browser requests through Next.js proxy routes. It includes:
- Automatic retry (3 attempts with 250ms/500ms/750ms backoff) for transient network errors
- `credentials: 'include'` to send cookies
- `cache: 'no-store'` on all requests

### Server-Side (Server Components / API routes)
```
Server Component -> lib/api-server.ts -> FastAPI backend directly
```
The `createServerApi()` function reads the `mr_token` cookie from incoming request and passes it as a Cookie header. Features:
- 10-second timeout with AbortController
- Pre-configured cache durations (USER_PROFILE: 5min, PLAN_USAGE: 2min, CONTACTS: 1min)
- Parallel fetch helper `fetchApiParallel()`

## Route Protection

`middleware.ts` runs on every `/app/*` request:
- Reads `mr_token` cookie
- Decodes JWT claims (without full verification, uses `atob()`)
- No token or decode failure -> redirect to `/login` (clears cookie)
- Expired token (`exp` claim check) -> redirect to `/login` (clears cookie)
- `/app/admin/*` -> checks `role` claim for `ADMIN`
  - Non-admin with `ADMIN_CLOAK_404=1` env -> rewrite to `/404`
  - Non-admin otherwise -> redirect to `/app`

## Query Provider

`components/providers/query-provider.tsx` wraps the app with TanStack Query defaults:
- `staleTime`: 5 minutes
- `gcTime`: 10 minutes
- `refetchOnWindowFocus`: false
- `retry`: 1

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `@tanstack/react-query` | Server state management |
| `@radix-ui/*` | Accessible UI primitives |
| `react-hook-form` + `zod` | Form handling + validation |
| `recharts` | Data visualization |
| `framer-motion` | Animations |
| `lucide-react` | Icon library |
| `date-fns` | Date formatting |
| `sonner` | Toast notifications |

## Directory Structure

```
apps/web/
  app/                    # Next.js App Router pages
    app/                  # Protected routes (/app/*)
    admin/                # Legacy admin (separate auth)
    api/proxy/v1/         # API proxy routes
    r/[id]/               # Public report viewer
    p/[code]/             # Property landing page
    print/[runId]/        # Print-optimized report
    social/[runId]/       # Social media image
  components/
    ui/                   # 57 shadcn/ui primitives
    report-builder/       # Market report wizard
    schedule-builder/     # Schedule wizard
    property/             # Property report components
    onboarding/           # Setup wizard + checklist
    admin/                # Admin-specific components
    dashboard/            # Dashboard content
    marketing/            # Landing page components
  hooks/                  # Custom React hooks
  lib/                    # Utilities, API clients, types
  middleware.ts           # Auth middleware
```
