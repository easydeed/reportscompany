# Backend Core

> `apps/api/src/api/` -- App startup, configuration, database, auth utilities

---

## main.py -- App Initialization

**Purpose:** Creates the FastAPI app, registers middleware, includes all routers.

**Middleware registration order** (Starlette executes bottom-to-top):
```
Line 54: AuthContextMiddleware    -- added first, runs LAST
Line 55: RateLimitMiddleware      -- added second, runs SECOND
Line 58: RLSContextMiddleware     -- added third, runs FIRST
```

**Known issue:** Execution order is inverted. `RateLimitMiddleware` runs before `AuthContextMiddleware` sets `account_id`, so rate limiting is effectively a no-op. See performance audit [H4].

**Routers included:** 26 total -- health, auth, apikeys, webhooks, devfiles, billing, stripe_webhook, reports, report_data, account, usage, schedules, unsubscribe, admin, me, affiliates, contacts, contact_groups, dev_stripe_prices, upload, branding_tools, users, onboarding, leads, property, mobile_reports, admin_metrics, lead_pages.

---

## settings.py -- Configuration

**Class:** `Settings(BaseSettings)` using pydantic-settings.

| Setting | Default | Notes |
|---------|---------|-------|
| `DATABASE_URL` | `postgresql://...localhost:5432/market_reports` | Overridden by env var on Render |
| `REDIS_URL` | `redis://localhost:6379/0` | Used by Celery + rate limiter |
| `JWT_SECRET` | `dev-secret` | Must be overridden in production |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS whitelist |
| `STRIPE_SECRET_KEY` | `""` | Stripe API key |
| `STARTER_PRICE_ID` / `PRO_PRICE_ID` / `ENTERPRISE_PRICE_ID` | `""` | Stripe price IDs |
| `APP_BASE` | `http://localhost:3000` | Frontend URL for links |
| `STRIPE_WEBHOOK_SECRET` | `""` | Webhook signature verification |
| `RESEND_API_KEY` | `""` | Email provider |
| `EMAIL_FROM_ADDRESS` / `EMAIL_REPLY_TO` | Default values | Email sender config |

**Known issue:** JWT secret preview (first 10 chars) logged at startup. See audit [L2].

---

## db.py -- Database Layer

### `db_conn()` context manager (line 8-15)
```python
@contextmanager
def db_conn():
    with psycopg.connect(settings.DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()
```

**Usage pattern in routes:**
```python
with db_conn() as (conn, cur):
    set_rls(cur, account_id)
    cur.execute("SELECT ...")
```

**Known issue:** Opens a new TCP connection every call. No connection pooling. See audit [C1].

### `set_rls(conn_or_cur, account_id, user_id?, user_role?)` (line 18-44)
Sets PostgreSQL session variables for Row-Level Security:
- `app.current_account_id`
- `app.current_user_id` (optional)
- `app.current_user_role` (optional)

Accepts either a cursor or `(conn, cur)` tuple for backwards compatibility.

**Known issue:** Uses f-string interpolation for SQL values. See audit [M3].

### `fetchone_dict(cur)` / `fetchall_dicts(cur)` (line 48-59)
Convert cursor results to dictionaries using column names from `cur.description`.

---

## auth.py -- Authentication Utilities

**Functions available** (imported by middleware and routes):
- `verify_jwt(token, secret)` -- Decode and validate JWT, returns claims dict or None
- `hash_api_key(key)` -- SHA-256 hash for API key lookup
- Password hashing utilities

---

## worker_client.py -- Task Queue

Enqueues Celery tasks for background report generation via Redis broker.

**Key function:** `enqueue_generate_report(report_id, account_id, report_type, params)`

---

## config/billing.py -- Stripe Mapping

Maps plan slugs to Stripe Price IDs. Provides billing helper functions.

## deps/admin.py -- Admin Dependency

FastAPI dependency that verifies `is_platform_admin` status on the current user. Used to protect admin-only routes.

## schemas/property.py -- Property Models

Pydantic models for normalizing property data from different MLS sources (SimplyRETS, SiteX).
