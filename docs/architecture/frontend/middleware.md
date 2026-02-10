# Next.js Middleware

> `apps/web/middleware.ts`

## Overview

Runs on every request matching `/app/:path*`. Handles authentication and authorization at the edge (no API calls).

## Route Matching

```typescript
export const config = {
  matcher: ["/app/:path*"],
}
```

Only protects routes under `/app/`. Public routes (`/`, `/login`, `/r/[id]`, `/p/[code]`, etc.) are not affected.

## Authentication Flow

```
Request to /app/*
  |
  +--> Read `mr_token` cookie
        |
        +--> No cookie? --> Redirect to /login
        |
        +--> Decode JWT payload (atob, no verification)
        |     |
        |     +--> Decode failed? --> Redirect to /login + clear cookie
        |     |
        |     +--> Check `exp` claim
        |           |
        |           +--> Expired? --> Redirect to /login + clear cookie
        |           |
        |           +--> Valid? --> Check admin routes
        |                 |
        |                 +--> Path starts with /app/admin?
        |                       |
        |                       +--> role !== ADMIN?
        |                       |     |
        |                       |     +--> ADMIN_CLOAK_404=1? --> Rewrite to /404
        |                       |     |
        |                       |     +--> Otherwise --> Redirect to /app
        |                       |
        |                       +--> role === ADMIN? --> Allow
        |
        +--> All checks pass --> NextResponse.next()
```

## JWT Decoding

Uses a manual decoder (no external library) compatible with Edge Runtime:

```typescript
function decodeJwtPayload(token: string): Record<string, any> | null {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
  const json = atob(base64)
  return JSON.parse(json)
}
```

Does NOT verify the signature. The backend is responsible for full JWT validation on API calls.

## JWT Claims Used

| Claim | Purpose |
|-------|---------|
| `exp` | Expiration timestamp (seconds since epoch) |
| `role` | User role (`USER` or `ADMIN`) |
| `account_type` | Account type (used by dashboard page, not middleware) |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ADMIN_CLOAK_404` | When `"1"`, non-admin access to `/app/admin/*` shows 404 instead of redirect |

## Security Notes

- JWT is decoded but not verified in middleware (performance tradeoff for Edge Runtime)
- Full JWT verification happens on every backend API call
- Cookie is cleared on decode failure or expiry to prevent loops
- Admin cloaking prevents discovery of admin routes by non-admin users

## Key File

- `apps/web/middleware.ts` (77 lines)
