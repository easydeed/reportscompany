# API Client Libraries

## Client-Side: `lib/api.ts`

### `apiFetch(path, init?)`

Main client-side fetch utility. All React components use this for API calls.

**Routing Logic:**
- In browser: prefixes path with `/api/proxy` (e.g., `/v1/reports` -> `/api/proxy/v1/reports`)
- On server: uses `API_BASE` env var directly (e.g., `https://reportscompany.onrender.com/v1/reports`)

**Features:**
- Sets `Content-Type: application/json`
- `credentials: 'include'` (sends cookies)
- `cache: 'no-store'`
- Auto-retry: 3 attempts for transient errors (`fetch failed`, `ECONNREFUSED`)
- Backoff: 250ms, 500ms, 750ms between retries
- Parses response as JSON automatically
- Throws on non-OK responses with status + body text

**Environment:**
- `NEXT_PUBLIC_API_BASE` - Backend API URL (used for server-side calls)

## Server-Side: `lib/api-server.ts`

### `createServerApi()`

Creates an authenticated API client for server components. Reads `mr_token` cookie automatically.

```typescript
const api = await createServerApi()
const { data, error, status } = await api.get<User>('/v1/me')
```

**Methods:** `get()`, `post()`, `patch()`, `delete()`

**Features:**
- 10-second timeout via AbortController
- Cookie forwarding (reads `mr_token`, sends as `Cookie` header)
- Optional caching with `revalidate` seconds and `tags` for on-demand revalidation
- Structured error responses: `{ data: T | null, error: string | null, status: number }`

### `fetchApi<T>(path, cache?)`

Simple helper for quick GETs. Returns `data` or `null`.

### `fetchApiParallel<T>(requests)`

Parallel fetch helper. Accepts array of paths or `{ path, cache }` objects.

### `CACHE_DURATIONS`

Pre-configured cache settings:
- `USER_PROFILE`: 5 min, tags: `['user-profile']`
- `ACCOUNT`: 5 min, tags: `['account']`
- `PLAN_USAGE`: 2 min, tags: `['plan-usage', 'usage']`
- `CONTACTS`: 1 min, tags: `['contacts']`

## API Base URL: `lib/get-api-base.ts`

### `getApiBase()`

Returns a safe API base URL. Handles:
- Missing env var -> defaults to `https://reportscompany.onrender.com`
- Missing scheme (e.g., `reportscompany.onrender.com`) -> prepends `https://`
- Trailing slashes -> removed

## Proxy Routes

All client-side API calls go through Next.js API routes at `app/api/proxy/v1/`. These are thin proxies that:
1. Read the `mr_token` cookie from the incoming request
2. Forward it to the backend API
3. Return the backend response

Proxy route files mirror the backend API structure. Examples:
- `app/api/proxy/v1/reports/route.ts` -> `GET /v1/reports`, `POST /v1/reports`
- `app/api/proxy/v1/me/route.ts` -> `GET /v1/me`
- `app/api/proxy/v1/admin/accounts/route.ts` -> `GET /v1/admin/accounts`

## Key Files

- `apps/web/lib/api.ts` - Client-side fetch
- `apps/web/lib/api-server.ts` - Server-side fetch
- `apps/web/lib/get-api-base.ts` - URL resolution
- `apps/web/app/api/proxy/v1/` - All proxy route handlers
