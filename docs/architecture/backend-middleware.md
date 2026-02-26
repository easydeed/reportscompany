# Backend Middleware

> `apps/api/src/api/middleware/` — Runs on every request before route handlers

---

## authn.py — Authentication + Rate Limiting

This file contains two middleware classes.

### AuthContextMiddleware

**Purpose:** Resolves `account_id` and `user` info from the incoming request, sets them on `request.state`.

**Auth flow (in order):**

1. **Skip public paths** — Health, docs, auth, webhooks, dev, public reports, lead pages, etc.

2. **Bearer token (JWT):**
   - Decode JWT via `verify_jwt()`
   - If valid, check blacklist via `_is_token_blacklisted()` (uses pooled `db_conn_autocommit()`)
   - Set `acct = claims["account_id"]`

3. **Bearer token (API key):**
   - If JWT fails, hash the token and look up in `api_keys` via pooled `db_conn_autocommit()`

4. **Cookie fallback (`mr_token`):**
   - Decode JWT from cookie, check blacklist again

5. **Demo header fallback:**
   - `X-Demo-Account` header sets `account_id` directly (development only)

6. **Fetch user info:**
   - Single pooled query: `SELECT id, email, role, is_platform_admin FROM users`
   - Sets `request.state.user` dict

**Sets on `request.state`:**
- `request.state.account_id` — string UUID
- `request.state.user` — dict with `id`, `email`, `role`, `is_platform_admin`, `account_id`

**Phase 1 fix:** All 3–4 per-request `psycopg.connect()` calls replaced with `db_conn_autocommit()` (pool). Estimated 600–1200ms saved per authenticated request.

---

### `_is_token_blacklisted(token)` — Internal Helper

Checks `jwt_blacklist` table using a pooled connection.

**Phase 6 fix — Fail CLOSED:**

**Before:** A DB error on the blacklist check silently passed (fail-open). A logged-out token could be accepted during any transient DB error.

**After:** On any `Exception`, the function logs the error and returns `True` (blacklisted) — denying the request. Logged-out tokens are never accepted if the DB can't be checked.

```python
except Exception as e:
    logger.error(f"Blacklist check failed (denying request): {e}")
    return True  # Fail CLOSED — deny on error
```

---

### RateLimitMiddleware

**Purpose:** Per-account rate limiting using Redis minute buckets.

**Flow:**
1. Skip health/docs paths
2. Get `account_id` from `request.state` (set by `AuthContextMiddleware`, which now runs first)
3. Look up `api_rate_limit` — **from Redis cache** (5-min TTL); falls back to DB on miss
4. Increment Redis key `ratelimit:{acct}:{minute}`
5. Set `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` response headers
6. Return 429 if over limit

**Default limit:** 60 requests per minute.

**Phase 1 fix:** Rate limit DB lookup uses pooled `db_conn_autocommit()` instead of raw `psycopg.connect()`.

**Phase 2 fix:** Rate limit value cached in Redis for 5 minutes per account. On cache hit, zero DB queries are made for rate limiting.

**Phase 3 fix:** Middleware LIFO order corrected — `AuthContextMiddleware` now runs before `RateLimitMiddleware`, so `account_id` is always set when rate limiting executes. Rate limiting is now active.

---

## rls.py — RLS Context (REMOVED)

`RLSContextMiddleware` was removed in Phase 3. It set `request.state.account_id` from the `X-Demo-Account` header, but `AuthContextMiddleware` already handles this at its demo header fallback step. Removing it eliminates one unnecessary ASGI wrapper per request.

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02 | **Phase 6:** `_is_token_blacklisted()` now fails CLOSED on DB error (returns `True` = denied). Added structured error logging. |
| 2026-02 | **Phase 2:** `RateLimitMiddleware` caches per-account rate limit in Redis (5-min TTL); no DB query on cache hit. |
| 2026-02 | **Phase 1:** All `psycopg.connect()` calls replaced with `db_conn_autocommit()` (pool). |
| 2026-02 | **Phase 3:** LIFO middleware order fixed. `RLSContextMiddleware` removed. Rate limiting now functional. |
| 2026-01 | Initial documentation |
