# Cursor: Wire Stripe Caching + Rate Limit Redis Cache

> **Date:** February 26, 2026
> **Scope:** 2 files to verify/fix, 1 file for reference
> **Risk:** LOW — these are additive caching layers with silent fallthrough
> **Branch:** `enhance/wire-stripe-ratelimit-cache`

---

## Context

We recently created `apps/api/src/api/cache.py` — a shared Redis cache utility with `cache_get()`, `cache_set()`, and `cache_delete()` that silently handles Redis failures. Two consumers were planned but may not be wired yet:

1. **`services/plans.py`** — `get_plan_catalog()` calls `stripe.Price.retrieve()` for every plan on every page load that touches plan-usage. 4 plans × 200-500ms each = 800-2000ms of pure Stripe overhead. This needs caching.

2. **`middleware/authn.py`** — `RateLimitMiddleware` fetches the per-account rate limit from the DB on every request. This needs Redis caching with a 5-minute TTL.

---

## Task 1: Verify and Fix `services/plans.py`

### Step 1 — Read the current file

```
READ apps/api/src/api/services/plans.py
```

Look for:
- Is there ALREADY an in-memory cache (`_plan_cache`, `_plan_cache_time`, `_CACHE_TTL_SECONDS`)?
- Does `get_plan_catalog(cur)` check a cache before calling Stripe?
- Is `invalidate_plan_cache()` defined?

### Step 2 — If caching is NOT present, add it

If `get_plan_catalog` still calls `stripe.Price.retrieve()` on every invocation without any cache check, add in-memory caching. The approach is in-memory (not Redis) because:
- The plan catalog is the same for all accounts
- It changes extremely rarely (monthly at most)
- In-memory is faster than Redis for a single shared object

**Wrap the existing function — do NOT rewrite its internals:**

```python
import time
import logging

logger = logging.getLogger(__name__)

# ── In-Memory Plan Cache ─────────────────────────────────────────────
_plan_cache = None
_plan_cache_time: float = 0
_CACHE_TTL_SECONDS = 3600  # 1 hour


def invalidate_plan_cache():
    """Call after plan/price changes (Stripe webhook, admin action)."""
    global _plan_cache, _plan_cache_time
    _plan_cache = None
    _plan_cache_time = 0
    logger.info("Plan catalog cache invalidated")


def get_plan_catalog(cur):
    """
    Returns the full plan catalog dict.
    
    Cached in-memory for 1 hour. First call pays the Stripe API cost
    (~1-2 seconds for 4 plans). All subsequent calls within the TTL
    return instantly from memory.
    """
    global _plan_cache, _plan_cache_time

    now = time.time()
    if _plan_cache is not None and (now - _plan_cache_time) < _CACHE_TTL_SECONDS:
        return _plan_cache

    # ── Cache miss: run the original logic ────────────────────────────
    # (Keep ALL existing DB query + Stripe API logic here, unchanged)
    
    # ... existing code that queries DB and calls stripe.Price.retrieve() ...
    
    result = { ... }  # whatever the function currently builds and returns

    # ── Store in cache ────────────────────────────────────────────────
    _plan_cache = result
    _plan_cache_time = now
    logger.info("Plan catalog cached (%d plans)", len(result))

    return result
```

**CRITICAL RULES:**
- Do NOT change the function signature: `get_plan_catalog(cur) -> dict`
- Do NOT change the return structure — callers depend on the exact dict shape
- Do NOT change `get_plan_info(cur, plan_slug)` — it calls `get_plan_catalog()` and benefits from the cache automatically
- The `cur` parameter is still needed for the DB query on cache miss — don't remove it

### Step 3 — Wire cache invalidation into Stripe webhook

```
READ apps/api/src/api/routes/stripe_webhook.py
```

Find the webhook handler(s) that process `price.updated` or `product.updated` events. Add a call to `invalidate_plan_cache()`:

```python
from api.services.plans import invalidate_plan_cache

# Inside the webhook handler, after processing price/product events:
if event_type in ("price.updated", "price.created", "price.deleted",
                   "product.updated", "product.created", "product.deleted"):
    invalidate_plan_cache()
```

If there's no explicit handler for price/product events (only subscription events), that's fine — the 1-hour TTL handles staleness. But if the file DOES handle these events, add the invalidation call.

### Step 4 — Verify

```bash
# Start API
cd apps/api && uvicorn src.api.main:app --reload --port 10000

# First call — should take 1-2 seconds (Stripe API calls)
time curl -s http://localhost:10000/v1/account/plan-usage \
  -H "Authorization: Bearer $TOKEN" > /dev/null

# Second call — should take <100ms (cached)
time curl -s http://localhost:10000/v1/account/plan-usage \
  -H "Authorization: Bearer $TOKEN" > /dev/null
```

---

## Task 2: Verify and Fix Rate Limit Redis Cache in Middleware

### Step 1 — Read the current middleware

```
READ apps/api/src/api/middleware/authn.py
```

Look at the `RateLimitMiddleware` class. Specifically find:
- How does it get the per-account rate limit?
- Does it use Redis caching for the limit config, or does it hit the DB every time?
- Does it already use `db_conn()` (pooled) or raw `psycopg.connect()`?

### Step 2 — If the rate limit config is NOT cached in Redis, add it

The rate limit middleware needs TWO Redis interactions:
1. **Rate limit CONFIG** (what's the account's limit?) — cached in Redis with 5-min TTL
2. **Rate limit COUNTER** (how many requests this minute?) — this is likely already in Redis

If the CONFIG lookup still hits the DB on every request, replace it with:

```python
from api.cache import cache_get, cache_set
# OR, if the middleware already has its own Redis client:
# Use self.r (the Redis client already on the class)

# Inside the dispatch method, replace the DB lookup for rate limit:

# BEFORE (what it might look like):
#   with db_conn() as (conn, cur):
#       cur.execute("SELECT api_rate_limit FROM accounts WHERE id=%s", (acct,))
#       row = cur.fetchone()
#       limit = row[0] if row else 60

# AFTER (with Redis cache):
limit_cache_key = f"ratelimit_config:{acct}"

# Try cache first
cached_limit = None
try:
    cached_limit = self.r.get(limit_cache_key)  # or cache_get(limit_cache_key)
except Exception:
    pass

if cached_limit is not None:
    limit = int(cached_limit)
else:
    # Cache miss — fetch from DB, then cache for 5 minutes
    limit = 60  # default
    try:
        with db_conn() as (conn, cur):
            cur.execute(
                "SELECT api_rate_limit FROM accounts WHERE id=%s",
                (acct,),
            )
            row = cur.fetchone()
            if row and row[0]:
                limit = int(row[0])
    except Exception:
        pass  # Use default 60 if DB fails
    
    try:
        self.r.setex(limit_cache_key, 300, str(limit))  # Cache 5 min
    except Exception:
        pass  # Redis write failure is non-critical
```

**CRITICAL RULES:**
- Keep the Redis counter logic (the `ratelimit:{acct}:{minute}` key) completely unchanged
- Only cache the CONFIG lookup (the `SELECT api_rate_limit` query)
- If the middleware already has `self.r` (a Redis client), use it. Don't create a second Redis connection.
- If it doesn't have a Redis client, initialize one in `__init__`:
  ```python
  def __init__(self, app):
      super().__init__(app)
      self.r = redis.from_url(settings.REDIS_URL, decode_responses=True)
  ```
- All Redis operations must be wrapped in try/except — a Redis failure should never crash the middleware

### Step 3 — Check if the middleware already does this

It's possible this was already implemented in a prior enhancement round. Read the file and check. If the rate limit CONFIG is already cached in Redis (look for `ratelimit_config:` key pattern or `cache_get` usage), then this task is already done — move on.

### Step 4 — Verify

```bash
# Start API with Redis running
cd apps/api && uvicorn src.api.main:app --reload --port 10000

# Hit an endpoint — check Redis for the cached config
redis-cli GET "ratelimit_config:<your-account-id>"
# Should return a number (e.g., "60") after the first request

# Verify rate limiting works
for i in $(seq 1 65); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    http://localhost:10000/v1/me \
    -H "Authorization: Bearer $TOKEN")
  if [ "$STATUS" = "429" ]; then
    echo "Rate limited at request $i"
    break
  fi
done
```

---

## Task 3: Verify `cache.py` Exists and Is Correct

### Step 1 — Read it

```
READ apps/api/src/api/cache.py
```

Confirm it has:
- `get_redis()` — lazy Redis client initialization
- `cache_get(key)` — returns parsed JSON or None
- `cache_set(key, value, ttl_seconds)` — stores JSON with TTL
- `cache_delete(key)` — removes a key
- Silent failure handling (try/except around all Redis operations)

If any of these are missing, add them. The utility should be a thin wrapper that never throws.

---

## Summary — What Success Looks Like

| Endpoint | Before | After |
|----------|--------|-------|
| `GET /v1/account/plan-usage` (first call) | ~2-3 seconds | ~2-3 seconds (cache warming) |
| `GET /v1/account/plan-usage` (cached) | ~2-3 seconds | **<100ms** |
| Any authenticated request (rate limit overhead) | +100-300ms | **+0-5ms** |
| Dashboard page load (plan-usage + rate limit) | ~3-5 seconds | **<200ms** |

---

## Files to Touch

| File | Action | Change |
|------|--------|--------|
| `apps/api/src/api/services/plans.py` | Verify/modify | Add in-memory cache around `get_plan_catalog()` if not present |
| `apps/api/src/api/routes/stripe_webhook.py` | Verify/modify | Add `invalidate_plan_cache()` call on price events if applicable |
| `apps/api/src/api/middleware/authn.py` | Verify/modify | Add Redis cache for rate limit config if not present |
| `apps/api/src/api/cache.py` | Verify only | Confirm it exists and has the right API |

---

## DO NOT Touch

- `apps/api/src/api/db.py` — already has pooling
- `apps/api/src/api/main.py` — middleware order already fixed
- `apps/api/src/api/routes/account.py` — plan-usage dedup already done
- `apps/api/src/api/services/affiliates.py` — N+1 already fixed
- Any worker files
- Any frontend files
- Any test files
