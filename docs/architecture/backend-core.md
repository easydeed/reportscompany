# Backend Core

> `apps/api/src/api/` — App startup, configuration, database, auth utilities

---

## main.py — App Initialization

**Purpose:** Creates the FastAPI app, registers middleware, includes all routers.

**Middleware registration order** (Starlette executes LIFO — last added = first executed):

```
app.add_middleware(RateLimitMiddleware)      # Added first → executes LAST  (after auth)
app.add_middleware(AuthContextMiddleware)    # Added second → executes FIRST (sets account_id)
# RLSContextMiddleware: REMOVED (was redundant with AuthContextMiddleware)
```

**Phase 1 fix:** Middleware order was inverted in the original implementation, causing `RateLimitMiddleware` to run before `account_id` was set, making rate limiting a no-op. Order is now correct.

**Phase 1.4 — Pool shutdown:** `@app.on_event("shutdown")` handler calls `get_pool().close()` to release all connections cleanly when the Uvicorn worker stops. Prevents "connection already closed" log noise during deployments.

**Routers included:** 26 total — health, auth, apikeys, webhooks, devfiles, billing, stripe_webhook, reports, report_data, account, usage, schedules, unsubscribe, admin, me, affiliates, contacts, contact_groups, dev_stripe_prices, upload, branding_tools, users, onboarding, leads, property, mobile_reports, admin_metrics, lead_pages.

---

## settings.py — Configuration

**Class:** `Settings(BaseSettings)` using pydantic-settings.

| Setting | Default | Notes |
|---------|---------|-------|
| `DATABASE_URL` | `postgresql://...localhost:5432/market_reports` | Overridden by env var on Render |
| `REDIS_URL` | `redis://localhost:6379/0` | Used by Celery + rate limiter + cache.py |
| `JWT_SECRET` | `dev-secret` | Must be overridden in production |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS whitelist |
| `STRIPE_SECRET_KEY` | `""` | Stripe API key |
| `STARTER_PRICE_ID` / `PRO_PRICE_ID` / `ENTERPRISE_PRICE_ID` | `""` | Stripe price IDs |
| `APP_BASE` | `http://localhost:3000` | Frontend URL for links |
| `STRIPE_WEBHOOK_SECRET` | `""` | Webhook signature verification |
| `RESEND_API_KEY` | `""` | Email provider |
| `EMAIL_FROM_ADDRESS` / `EMAIL_REPLY_TO` | Default values | Email sender config |

**Phase 6 fix:** JWT secret is no longer logged at startup. Module now logs `"JWT_SECRET configured (N chars)"` — length only, never the value.

---

## db.py — Database Layer

### Connection Pool (Phase 1)

**Before:** `db_conn()` opened a new TCP+TLS connection each call (~200ms per call; 3–4 calls per request = 600–1200ms pure overhead).

**After:** Connections come from a `psycopg_pool.ConnectionPool` initialized once at first use.

```python
_pool = ConnectionPool(
    conninfo=settings.DATABASE_URL,
    min_size=2,       # 2 warm connections always ready
    max_size=10,      # scale to 10 under load
    max_idle=300,     # close idle after 5 min
    max_lifetime=1800 # recycle connections every 30 min
    timeout=10,       # wait max 10s for a connection
)
```

**Estimated impact:** 60–80% reduction in API response times.

### `db_conn()` — Standard Pooled Context Manager

```python
with db_conn() as (conn, cur):
    set_rls(cur, account_id)
    cur.execute("SELECT ...")
```

- Caller interface is **identical** to the old implementation — no route code changed.
- Returns connection to pool automatically on exit.
- Commits on success; rolls back on exception.

### `db_conn_autocommit()` — Pooled, No Transaction

Used for lightweight middleware lookups (blacklist check, API key lookup, user info) where `SET LOCAL` RLS is not needed.

```python
with db_conn_autocommit() as cur:
    cur.execute("SELECT 1 FROM jwt_blacklist WHERE ...")
```

### `set_rls(conn_or_cur, account_id, user_id?, user_role?)` (Phase 6 — SQL injection fix)

Sets PostgreSQL session variables for Row-Level Security.

**Before:** Used f-string interpolation — SQL injection risk if `account_id` was ever malformed.

**After:** Uses `psycopg.sql.Literal` for safe parameterization:

```python
cur.execute(
    sql.SQL("SET LOCAL app.current_account_id TO {}").format(sql.Literal(account_id))
)
```

Accepts either a cursor or `(conn, cur)` tuple for backwards compatibility.

### `fetchone_dict(cur)` / `fetchall_dicts(cur)`

Convert cursor results to dictionaries using column names from `cur.description`.

---

## cache.py — Redis Cache Utility (Phase 2, NEW)

> `apps/api/src/api/cache.py`

**Purpose:** Shared thin Redis wrapper for the API layer. Centralizes connection management, JSON (de)serialization, and silent failure handling.

```python
from api.cache import cache_get, cache_set, cache_delete

val = cache_get("plan_catalog:v1")      # None on miss or Redis failure
cache_set("plan_catalog:v1", obj, 3600) # silently ignored if Redis down
cache_delete("plan_catalog:v1")
```

**Fail-safe design:** All three functions catch all `Exception`s and log at `DEBUG` level. A Redis outage never surfaces as an API error — it just means every request goes to the DB.

**Current consumers:**
| Consumer | Key | TTL |
|----------|-----|-----|
| `middleware/authn.py` `RateLimitMiddleware` | `ratelimit_config:{account_id}` | 5 min |
| `services/plans.py` `get_plan_catalog()` | in-memory (process-local) | 1 hour |

> Note: `plans.py` uses an in-process TTL dict (not Redis) because plan data rarely changes and is small enough to hold in memory per worker. The `cache.py` utility is available for future use requiring shared cross-worker caching.

---

## auth.py — Authentication Utilities

**Functions available** (imported by middleware and routes):
- `verify_jwt(token, secret)` — Decode and validate JWT, returns claims dict or None
- `hash_api_key(key)` — SHA-256 hash for API key lookup
- Password hashing utilities

---

## worker_client.py — Task Queue

Enqueues Celery tasks for background report generation via Redis broker.

**Key function:** `enqueue_generate_report(report_id, account_id, report_type, params)`

---

## config/billing.py — Stripe Mapping

Maps plan slugs to Stripe Price IDs. Provides billing helper functions.

## deps/admin.py — Admin Dependency

FastAPI dependency that verifies `is_platform_admin` status on the current user. Used to protect admin-only routes.

## schemas/property.py — Property Models

Pydantic models for normalizing property data from different MLS sources (SimplyRETS, SiteX).

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02 | **Phase 6:** `set_rls()` SQL injection fix — uses `sql.Literal` instead of f-string. `settings.py` no longer logs JWT secret value (logs length only). |
| 2026-02 | **Phase 2:** Added `cache.py` — shared Redis utility with `cache_get` / `cache_set` / `cache_delete`. |
| 2026-02 | **Phase 1:** `db.py` replaced with `psycopg_pool.ConnectionPool`. Added `db_conn_autocommit()`. Added pool shutdown hook to `main.py`. |
| 2026-02 | **Phase 3:** Fixed LIFO middleware order (`AuthContextMiddleware` now runs before `RateLimitMiddleware`). Removed redundant `RLSContextMiddleware`. |
| 2026-01 | Initial documentation |
