# Performance Audit

> Full API performance audit -- response times 3-8s, target <500ms

---

## CRITICAL (1-5+ second delays per request)

### [C1] No connection pooling
- **Files:** `db.py:11`
- **Impact:** `psycopg.connect()` opens new TCP+TLS connection per call. 100-300ms each on Render.
- **Fix:** Replace with `psycopg_pool.ConnectionPool`. `db_conn()` becomes `pool.connection()`.

### [C2] Middleware opens 3-5 raw connections per request
- **Files:** `middleware/authn.py:68, 88, 108, 147, 187`
- **Impact:** JWT blacklist + API key + user info + rate limit = 3-5 separate `psycopg.connect()` calls = 300-1500ms.
- **Fix:** All middleware DB access through shared pool. Single connection per request.

### [C3] Live Stripe API calls on every page load
- **Files:** `services/plans.py:91-103`
- **Impact:** `stripe.Price.retrieve()` per plan. 4 plans x 200-500ms = 800-2000ms. Called by `/v1/account/plan-usage`.
- **Fix:** Cache in Redis (1-24hr TTL). Stripe prices change rarely.

### [C4] Duplicate `get_sponsored_accounts()` calls
- **Files:** `routes/affiliates.py:51-54`, `services/affiliates.py:94`
- **Impact:** Overview endpoint calls it once via `get_affiliate_overview()`, then again directly. Everything runs 2x.
- **Fix:** Call once, derive overview metrics locally.

### [C5] N+1 query in `get_sponsored_accounts()`
- **Files:** `services/affiliates.py:59-68`
- **Impact:** Per-account group membership query. 20 accounts = 20 extra queries. Combined with C4 = 40.
- **Fix:** Batch query with `WHERE member_id = ANY(%s)`.

---

## HIGH (500ms-2s delays)

### [H1] Redundant sub-function calls in plan-usage endpoint
- **Files:** `routes/account.py:376-382`, `services/usage.py:182-183`
- **Impact:** `resolve_plan_for_account()` and `get_monthly_usage()` each called 2x.
- **Fix:** Call `evaluate_report_limit()` once, extract plan/usage from result.

### [H2] Rate limit DB query on every request
- **Files:** `middleware/authn.py:187-192`
- **Impact:** Raw connection to fetch `api_rate_limit` every request. 100-300ms.
- **Fix:** Cache in Redis (5min TTL) or embed in JWT claims.

### [H3] `get_plan_info()` triggers all Stripe calls for one plan
- **Files:** `services/plans.py:122-128`
- **Impact:** Fetches entire catalog to return one plan.
- **Fix:** Fixed by C3 caching.

### [H4] Middleware ordering inverted
- **Files:** `main.py:54-58`
- **Impact:** Starlette LIFO = RateLimitMiddleware runs before auth. Rate limiting disabled.
- **Fix:** Reverse registration order.

---

## MEDIUM (100-500ms delays)

### [M1] Correlated subquery in schedule runs
- **Files:** `services/usage.py:63-72`
- **Fix:** Rewrite as JOIN.

### [M2] Error swallowing / fail-open security
- **Files:** `middleware/authn.py:77-78, 117-118`, `services/usage.py:76-78`, `routes/affiliates.py:306,340,556`
- **Fix:** Log exceptions. Fail closed on security checks.

### [M3] SQL injection risk in `set_rls()`
- **Files:** `db.py:38, 42, 44`
- **Fix:** Use `sql.Literal()` parameterization.

### [M4] 4 separate queries in sponsored account detail
- **Files:** `routes/affiliates.py:716-759`
- **Fix:** Combine into single query with subqueries.

### [M5] Duplicate route definitions
- **Files:** `routes/affiliates.py:251-363, 502-579`
- **Fix:** Remove duplicate GET/POST `/branding` routes.

---

## LOW (code quality)

### [L1] RLSContextMiddleware is redundant
### [L2] JWT secret preview logged at startup
### [L3] CREATE TABLE in request handler
### [L4] get_plan_info fetches all plans for one
### [L5] Debug logging on every /reports/ request

---

## Missing Database Indexes

| Table | Column(s) | Why |
|-------|-----------|-----|
| `report_generations` | `(account_id, generated_at)` | Monthly usage count |
| `accounts` | `sponsor_account_id` | Sponsored accounts lookup |
| `contact_group_members` | `(member_type, member_id, account_id)` | Group membership |
| `jwt_blacklist` | `token_hash` | Auth blacklist check |
| `schedule_runs` | `(schedule_id, created_at)` | Schedule usage count |
| `api_keys` | `key_hash` | API key auth |

---

## Impact Summary

| Source | Before | After Fix |
|--------|--------|-----------|
| Connection pool | 100-300ms/conn | ~0-5ms |
| Middleware connections (x3-5) | 300-1500ms | ~5-15ms |
| Stripe API (x4) | 800-2000ms | ~1-5ms |
| Duplicate sponsored calls | 200-500ms | 0ms |
| N+1 group queries (x20-40) | 400-1000ms | ~10-30ms |
| Duplicate plan/usage calls | 40-200ms | 0ms |
| Rate limit DB query | 100-300ms | ~1-5ms |
| **Total** | **~2-5.2s** | **~30-100ms** |
