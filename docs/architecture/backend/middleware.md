# Middleware

> Authentication, rate limiting, and RLS context middleware
> File: `apps/api/src/api/middleware/authn.py` and `rls.py`

## Middleware Stack (Starlette LIFO)

Middleware is added via `app.add_middleware()` in `main.py`. Starlette executes middleware in LIFO (last-in, first-out) order. The add order is:

1. `CORSMiddleware` (added first, executes last on request)
2. `RLSContextMiddleware` (legacy placeholder)
3. `RateLimitMiddleware`
4. `AuthContextMiddleware` (added last, executes first on request)

Actual request execution order: Auth -> RateLimit -> RLS -> CORS -> Route handler.

**Known bug:** Due to LIFO ordering, `RateLimitMiddleware` runs *after* `AuthContextMiddleware`. This means `request.state.account_id` is already set when rate limiting checks run, which is the intended behavior. However, the ordering of middleware add calls in `main.py` may be confusing to read -- the order of `add_middleware()` is the *reverse* of execution order.

## AuthContextMiddleware

> File: `apps/api/src/api/middleware/authn.py`, lines 13-164

### Auth Resolution Flow

```
1. Skip if OPTIONS request
2. Skip if public path (see list below)
3. Try Authorization: Bearer header
   a. Try JWT decode (verify_jwt)
      - If valid: check jwt_blacklist table (raw psycopg.connect, line 68)
      - If blacklisted: return 401
      - If valid + not blacklisted: use claims.account_id
   b. If JWT fails: try API key
      - Hash token with hash_api_key()
      - Query api_keys table (raw psycopg.connect, line 88)
      - If match: use account_id from api_keys row
4. Cookie fallback: read mr_token cookie
   a. verify_jwt on cookie value
   b. Blacklist check (raw psycopg.connect, line 108)
   c. Use claims.account_id
5. X-Demo-Account header (temporary dev fallback)
6. If no account resolved: return 401 JSONResponse
7. Set request.state.account_id
8. Fetch user info from users table (raw psycopg.connect, line 147)
9. Set request.state.user
```

### Public Paths (no auth required)

- `/health`, `/docs`, `/redoc`, `/openapi`
- `/v1/auth/*` (login, register, etc.)
- `/dev-files/*`
- `/v1/webhooks/stripe`
- `/v1/billing/debug`
- `/v1/email/unsubscribe`
- `/v1/dev/*`
- `/v1/leads/capture` (public lead form)
- `/v1/property/public/*` (public property landing pages)
- `/v1/cma/*` (consumer CMA landing pages)
- `/v1/r/*` (mobile report viewer)
- `/v1/reports/{id}/data` (PDF generation source)

### Raw psycopg.connect() Calls

The middleware opens raw connections outside the `db_conn()` helper, bypassing RLS:

| Line | Purpose |
|------|---------|
| 68 | JWT blacklist check (Bearer token) |
| 88 | API key lookup (key_hash match) |
| 108 | JWT blacklist check (cookie token) |
| 147 | Fetch user info (id, email, role, is_platform_admin) |

All use `psycopg.connect(settings.DATABASE_URL, autocommit=True)`.

### request.state Fields Set

| Field | Type | Description |
|-------|------|-------------|
| `request.state.account_id` | `str` | UUID of the resolved account |
| `request.state.user` | `dict` | `{id, email, role, is_platform_admin, account_id}` |

## RateLimitMiddleware

> File: `apps/api/src/api/middleware/authn.py`, lines 166-221

### Rate Limit Flow

```
1. Skip for /health, /docs, /openapi, /redoc
2. Get account_id from request.state (set by AuthContextMiddleware)
3. If no account_id: pass through (public routes)
4. Fetch per-account limit from accounts.api_rate_limit (raw psycopg.connect, line 187)
   - Default: 60 requests/minute
5. Redis minute bucket: key = ratelimit:{account_id}:{minute}
   - INCR key, EXPIRE 60s on first hit
6. Calculate remaining = max(0, limit - count)
7. Set response headers:
   - X-RateLimit-Limit
   - X-RateLimit-Remaining
   - X-RateLimit-Reset
8. If count > limit: return 429 JSONResponse
```

### Raw psycopg.connect() Call

| Line | Purpose |
|------|---------|
| 187 | Fetch `accounts.api_rate_limit` for the account |

### Known Issue

The rate limit check queries the database on every request to get the per-account limit. This could be cached in Redis for better performance.

## RLSContextMiddleware (Legacy)

> File: `apps/api/src/api/middleware/rls.py`, lines 6-19

This is a legacy placeholder. It only reads the `X-Demo-Account` header and sets `request.state.account_id`. The actual auth logic has been moved to `AuthContextMiddleware`. This middleware still runs in the stack but is effectively a no-op for authenticated requests since `AuthContextMiddleware` already sets `request.state.account_id`.

### Fields Set

| Field | Type | Description |
|-------|------|-------------|
| `request.state.account_id` | `str` | Only if X-Demo-Account header is present |
