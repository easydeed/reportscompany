# Backend API Service

> `apps/api/src/api/` -- FastAPI application serving the REST API

## Architecture

- **Framework:** FastAPI (Python 3.11+, sync handlers)
- **Database:** PostgreSQL 15 with psycopg3 (sync), Row-Level Security
- **Cache/Queue:** Redis (rate limits + Celery broker)
- **Auth:** JWT (HS256) via cookies + Bearer tokens + API keys
- **Multi-tenancy:** RLS enforced via `SET LOCAL app.current_account_id`
- **Hosting:** Render (Starter plan)

## Request Lifecycle

```
Request
  -> CORSMiddleware
  -> RLSContextMiddleware (legacy, sets X-Demo-Account)
  -> RateLimitMiddleware (Redis counter, DB lookup for limit)
  -> AuthContextMiddleware (JWT/API key -> account_id + user)
  -> Route handler
    -> db_conn() opens connection
    -> set_rls(cur, account_id) sets session vars
    -> Business logic (services)
    -> Response
```

Note: Due to Starlette LIFO ordering, actual execution is bottom-to-top of `add_middleware()` calls.

## File Organization

| Directory | Purpose |
|-----------|---------|
| `routes/` | 26 route modules with endpoint definitions |
| `services/` | 16 service modules with business logic + SQL |
| `middleware/` | Auth, rate limiting, RLS |
| `schemas/` | Pydantic models for request/response validation |
| `config/` | Stripe billing configuration |
| `deps/` | FastAPI dependency injection |

## Key Patterns

1. **Connection pattern:** `with db_conn() as (conn, cur): set_rls(cur, account_id); ...`
2. **Auth dependency:** `account_id: str = Depends(require_account_id)` on protected routes
3. **Admin dependency:** `user = Depends(get_admin_user)` on admin routes
4. **Task enqueue:** `enqueue_generate_report()` -> Redis queue -> Worker picks up
5. **Property task:** `enqueue_property_report()` -> Celery direct

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET` | JWT signing secret |
| `ALLOWED_ORIGINS` | CORS whitelist |
| `STRIPE_SECRET_KEY` | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | Webhook signature verification |
| `RESEND_API_KEY` | Email provider API key |
| `APP_BASE` | Frontend URL for generated links |
