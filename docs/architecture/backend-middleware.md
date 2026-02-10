# Backend Middleware

> `apps/api/src/api/middleware/` -- Runs on every request before route handlers

---

## authn.py -- Authentication + Rate Limiting

This file contains two middleware classes.

### AuthContextMiddleware (line 13-164)

**Purpose:** Resolves `account_id` and `user` info, sets them on `request.state`.

**Auth flow (in order):**

1. **Skip public paths** (lines 33-53): Health, docs, auth, webhooks, dev, public reports, lead pages, etc.

2. **Bearer token (JWT)** (lines 60-81):
   - Decode JWT via `verify_jwt()`
   - If valid, check blacklist: `SELECT 1 FROM jwt_blacklist WHERE token_hash = %s` (line 68-76) -- **raw psycopg.connect()**
   - Set `acct = claims["account_id"]`

3. **Bearer token (API key)** (lines 82-97):
   - If JWT fails, hash the token and look up: `SELECT account_id FROM api_keys WHERE key_hash=%s` (line 88-94) -- **raw psycopg.connect()**

4. **Cookie fallback (mr_token)** (lines 100-123):
   - Decode JWT from `mr_token` cookie
   - Check blacklist again (line 108-118) -- **raw psycopg.connect()**

5. **Demo header fallback** (lines 126-129):
   - `X-Demo-Account` header sets account_id directly

6. **Fetch user info** (lines 141-163):
   - If JWT auth, query: `SELECT id, email, role, is_platform_admin FROM users` (line 147-153) -- **raw psycopg.connect()**
   - Sets `request.state.user` dict with `id`, `email`, `role`, `is_platform_admin`, `account_id`

**Sets on request.state:**
- `request.state.account_id` -- string UUID
- `request.state.user` -- dict with id, email, role, is_platform_admin, account_id

**Known issues:**
- 3-4 raw `psycopg.connect()` calls per request (no pooling). See audit [C2].
- Blacklist check fails open (silent except). See audit [M2].

---

### RateLimitMiddleware (line 166-221)

**Purpose:** Per-account rate limiting using Redis minute buckets.

**Flow:**
1. Skip health/docs paths
2. Get `account_id` from `request.state` (set by auth middleware)
3. Fetch `api_rate_limit` from accounts table (line 187-192) -- **raw psycopg.connect()**
4. Increment Redis key `ratelimit:{acct}:{minute}`
5. Set `X-RateLimit-*` headers on response
6. Return 429 if over limit

**Default limit:** 60 requests per minute.

**Known issues:**
- Opens a raw DB connection on every request for rate limit lookup. See audit [H2].
- Due to middleware ordering bug [H4], this middleware runs BEFORE auth sets `account_id`, so it skips rate limiting entirely (line 182-183 gets `None`).

---

## rls.py -- RLS Context (Legacy)

### RLSContextMiddleware (line 6-19)

**Purpose:** Placeholder that sets `request.state.account_id` from `X-Demo-Account` header.

**Known issue:** Redundant with AuthContextMiddleware which does the same thing at line 127-129. This middleware adds an extra ASGI layer for no benefit. See audit [L1].
