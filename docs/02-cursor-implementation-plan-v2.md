# TrendyReports API Performance Fix — Cursor Implementation Plan v2

## Overview

The full Claude Code audit confirmed 5 Critical, 4 High, 5 Medium, and 5 Low issues. This plan fixes all of them in dependency order across 7 phases.

**Total findings: 19 issues across performance, security, and code quality.**

**Do NOT skip phases or reorder. Each phase must be deployed and verified before starting the next.**

---

## Phase 1: Connection Pooling + Middleware Rewrite (Critical: C1, C2, H4, M3)

### What This Fixes
- **C1:** No connection pooling — every `db_conn()` opens a new TCP connection (~200ms each)
- **C2:** Auth middleware opens 3-5 raw `psycopg.connect()` calls per request (~600-1500ms)
- **H4:** Middleware ordering is inverted — rate limiting runs before auth (completely broken)
- **M3:** `set_rls()` uses f-string SQL interpolation (injection risk)

This is the single highest-impact phase. It affects every single request.

### File 1: `apps/api/src/api/db.py` — Complete rewrite

```python
"""
Database connection module with connection pooling.

BEFORE: Every db_conn() call opened a new TCP connection (~200ms each).
AFTER:  Connections come from a warm pool (~0ms acquisition).
"""

from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional
import psycopg
from psycopg import sql
from psycopg_pool import ConnectionPool
from .settings import settings
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION POOL
# Initialized once at first use (lazy singleton), reused for all requests.
# Render Starter PostgreSQL supports ~100 connections.
# We use 2-10 to leave room for worker, migrations, admin tools.
# ============================================================================

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get or create the connection pool (lazy singleton)."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=2,          # Keep 2 warm connections ready
            max_size=10,         # Scale up to 10 under load
            max_idle=300,        # Close idle connections after 5 min
            max_lifetime=1800,   # Recycle every 30 min (prevents stale)
            timeout=10,          # Max 10s wait for available connection
        )
    return _pool


@contextmanager
def db_conn():
    """
    Get a pooled database connection.
    
    Usage is IDENTICAL to before — no route code needs to change:
        with db_conn() as (conn, cur):
            set_rls(cur, account_id)
            cur.execute(...)
    
    But connections now come from a pool (~0ms) instead of
    being created fresh each time (~200ms).
    """
    pool = get_pool()
    with pool.connection() as conn:
        conn.autocommit = False  # Required for SET LOCAL (RLS)
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()


@contextmanager
def db_conn_autocommit():
    """
    Pooled connection with autocommit=True.
    Use for simple reads that don't need RLS transactions
    (like middleware lookups).
    """
    pool = get_pool()
    with pool.connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            yield cur


def set_rls(conn_or_cur, account_id: str, user_id: str | None = None,
            user_role: str | None = None):
    """
    Enforce RLS using Postgres session variables.
    
    FIX (M3): Uses parameterized sql.Literal instead of f-string interpolation
    to prevent SQL injection if account_id is ever malformed.
    """
    if isinstance(conn_or_cur, tuple):
        conn, cur = conn_or_cur
    else:
        cur = conn_or_cur

    cur.execute(
        sql.SQL("SET LOCAL app.current_account_id TO {}").format(sql.Literal(account_id))
    )
    if user_id:
        cur.execute(
            sql.SQL("SET LOCAL app.current_user_id TO {}").format(sql.Literal(user_id))
        )
    if user_role:
        cur.execute(
            sql.SQL("SET LOCAL app.current_user_role TO {}").format(sql.Literal(user_role))
        )


def fetchone_dict(cur) -> Optional[Dict[str, Any]]:
    row = cur.fetchone()
    if row is None:
        return None
    cols = [desc.name for desc in cur.description]
    return dict(zip(cols, row))


def fetchall_dicts(cur) -> Iterable[Dict[str, Any]]:
    cols = [desc.name for desc in cur.description]
    for row in cur.fetchall():
        yield dict(zip(cols, row))
```

**Add dependency:**
```bash
cd apps/api
poetry add psycopg-pool
```

### File 2: `apps/api/src/api/middleware/authn.py` — Rewrite with pooled connections + fix ordering + fail-closed security

This is a full rewrite of the middleware file. Key changes:
- All `psycopg.connect()` calls replaced with `db_conn_autocommit()` from pool
- Remove `import psycopg` (no longer needed directly)
- Blacklist checks fail CLOSED (deny request on DB error) instead of fail-open
- Remove debug logging on every `/reports/` request (L5)
- Rate limit middleware uses Redis cache for account limit (H2)

```python
"""
Authentication and Rate Limiting Middleware — Rewritten.

Changes from original:
- All DB access uses connection pool (was: raw psycopg.connect per call)
- Blacklist checks fail CLOSED on DB error (was: fail open — security hole)
- Rate limit caches account limit in Redis (was: DB query per request)
- Debug logging removed from production paths
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import redis
import time
import hashlib
import logging
from ..settings import settings
from ..auth import verify_jwt, hash_api_key
from ..db import db_conn_autocommit

logger = logging.getLogger(__name__)


# ============================================================================
# Public paths that skip authentication entirely
# ============================================================================

_PUBLIC_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi",
    "/v1/auth/",
    "/dev-files/",
    "/v1/webhooks/stripe",
    "/v1/billing/debug",
    "/v1/email/unsubscribe",
    "/v1/dev/",
    "/v1/leads/capture",
    "/v1/property/public/",
    "/v1/cma/",
    "/v1/r/",
)


def _is_public_path(path: str) -> bool:
    """Check if path is public (no auth required)."""
    if path.startswith(_PUBLIC_PREFIXES):
        return True
    # Special case: /v1/reports/{id}/data is public (used by PDF generation)
    if path.startswith("/v1/reports/") and path.endswith("/data"):
        return True
    # Special case: exact match
    if path == "/v1/leads/capture":
        return True
    return False


class AuthContextMiddleware(BaseHTTPMiddleware):
    """
    Resolves account_id via:
      1) Authorization: Bearer <JWT>
      2) Authorization: Bearer <API-KEY>
      3) X-Demo-Account (temporary fallback)
    Sets request.state.account_id and request.state.user.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        if _is_public_path(path):
            return await call_next(request)

        acct: Optional[str] = None
        claims: Optional[dict] = None

        # ── 1) Try Authorization header (Bearer JWT or API key) ──────────
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()

            # Try JWT first
            claims = verify_jwt(token, settings.JWT_SECRET)
            if claims and claims.get("account_id"):
                # FIX (M2): Blacklist check fails CLOSED — deny on DB error
                if _is_token_blacklisted(token):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Token has been invalidated"},
                    )
                acct = claims["account_id"]
            else:
                # JWT failed — try API key
                key_hash = hash_api_key(token)
                try:
                    with db_conn_autocommit() as cur:
                        cur.execute(
                            "SELECT account_id FROM api_keys "
                            "WHERE key_hash=%s AND is_active=TRUE",
                            (key_hash,),
                        )
                        row = cur.fetchone()
                        if row:
                            acct = row[0]
                except Exception as e:
                    logger.error(f"API key lookup failed: {e}")

        # ── 2) Cookie fallback (mr_token) ────────────────────────────────
        if not acct:
            cookie_token = request.cookies.get("mr_token")
            if cookie_token:
                claims = verify_jwt(cookie_token, settings.JWT_SECRET)
                if claims and claims.get("account_id"):
                    # FIX (M2): Fail closed on blacklist check error
                    if _is_token_blacklisted(cookie_token):
                        return JSONResponse(
                            status_code=401,
                            content={"detail": "Session has expired"},
                        )
                    acct = claims["account_id"]

        # ── 3) Demo header fallback ──────────────────────────────────────
        if not acct:
            demo = request.headers.get("X-Demo-Account")
            if demo:
                acct = demo

        if not acct:
            return JSONResponse(
                status_code=401, content={"detail": "Unauthorized"}
            )

        request.state.account_id = acct

        # ── Fetch user info (single pooled connection) ───────────────────
        user_info = {"account_id": acct, "role": "USER"}

        if claims and claims.get("user_id"):
            try:
                with db_conn_autocommit() as cur:
                    cur.execute(
                        "SELECT id, email, role, is_platform_admin FROM users "
                        "WHERE id=%s::uuid AND account_id=%s::uuid",
                        (claims["user_id"], acct),
                    )
                    user_row = cur.fetchone()
                    if user_row:
                        user_info = {
                            "id": str(user_row[0]),
                            "email": user_row[1],
                            "role": (user_row[2] or "USER").upper(),
                            "is_platform_admin": bool(user_row[3])
                            if user_row[3] is not None
                            else False,
                            "account_id": acct,
                        }
            except Exception as e:
                logger.error(f"User info fetch failed: {e}")

        request.state.user = user_info
        return await call_next(request)


def _is_token_blacklisted(token: str) -> bool:
    """
    Check if a JWT is blacklisted.

    FIX (M2): Fails CLOSED — if the DB check fails, we deny the request.
    This prevents logged-out tokens from being accepted during DB hiccups.
    Returns True (blacklisted / deny) on any error.
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        with db_conn_autocommit() as cur:
            cur.execute(
                "SELECT 1 FROM jwt_blacklist "
                "WHERE token_hash = %s AND expires_at > NOW()",
                (token_hash,),
            )
            return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Blacklist check failed (denying request): {e}")
        return True  # Fail CLOSED — deny on error


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-account rate limiter using Redis.

    FIX (H2): Account rate limit is cached in Redis (5 min TTL)
    instead of querying the database on every request.
    """

    def __init__(self, app):
        super().__init__(app)
        self.r = redis.from_url(settings.REDIS_URL)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/health", "/openapi", "/docs", "/redoc")):
            return await call_next(request)

        acct = getattr(request.state, "account_id", None)
        if not acct:
            return await call_next(request)

        # ── Get rate limit from Redis cache (not DB) ─────────────────────
        limit_key = f"ratelimit_config:{acct}"
        cached_limit = self.r.get(limit_key)

        if cached_limit is not None:
            limit = int(cached_limit)
        else:
            # Cache miss — fetch from DB (pooled), cache for 5 minutes
            limit = 60  # default
            try:
                with db_conn_autocommit() as cur:
                    cur.execute(
                        "SELECT api_rate_limit FROM accounts WHERE id=%s",
                        (acct,),
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        limit = int(row[0])
            except Exception:
                pass  # Use default 60 if DB fails
            self.r.setex(limit_key, 300, str(limit))  # Cache 5 min

        # ── Token bucket check ───────────────────────────────────────────
        now = int(time.time())
        minute = now - (now % 60)
        key = f"ratelimit:{acct}:{minute}"
        count = self.r.incr(key)
        if count == 1:
            self.r.expire(key, 60)

        remaining = max(0, limit - count)
        reset = 60 - (now - minute)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit of {limit} requests/minute exceeded",
                    "retry_after": reset,
                },
                headers=dict(response.headers),
            )
        return response
```

### File 3: `apps/api/src/api/main.py` — Fix middleware registration order + remove dead middleware + add timing

**FIX (H4):** Starlette uses LIFO for `add_middleware()`. Register in reverse execution order so auth runs first.

**FIX (L1):** Remove `RLSContextMiddleware` — it's a no-op. Auth middleware already handles `X-Demo-Account`.

```python
# ============================================================================
# MIDDLEWARE REGISTRATION
# 
# CRITICAL: Starlette add_middleware() uses LIFO (stack).
# Last added = first to execute.
# We want: Timing → Auth → RateLimit → Route
# So register in REVERSE order:
# ============================================================================

# 1. Register RateLimit FIRST (executes LAST, after auth sets account_id)
app.add_middleware(RateLimitMiddleware)

# 2. Register Auth SECOND (executes SECOND, sets account_id)
app.add_middleware(AuthContextMiddleware)

# 3. Register Timing LAST (executes FIRST, wraps everything)
# This is a @app.middleware("http") function, not add_middleware,
# so it automatically wraps the outermost layer.

import time as _time

@app.middleware("http")
async def timing_middleware(request, call_next):
    start = _time.perf_counter()
    response = await call_next(request)
    elapsed = _time.perf_counter() - start
    
    level = logging.WARNING if elapsed > 1.0 else logging.DEBUG
    logging.getLogger("api.timing").log(
        level,
        f"[TIMING] {request.method} {request.url.path} "
        f"→ {response.status_code} in {elapsed:.3f}s"
    )
    response.headers["Server-Timing"] = f"total;dur={elapsed * 1000:.0f}"
    return response

# REMOVED: RLSContextMiddleware (L1 — was a no-op, auth handles X-Demo-Account)
# DO NOT add: app.add_middleware(RLSContextMiddleware)
```

**Also remove** the import of `RLSContextMiddleware` and the `rls.py` file reference. The `rls.py` file itself can stay (harmless) or be deleted.

### Verification

After deploying Phase 1:

```powershell
# Test 1: Health endpoint (baseline — no auth)
Measure-Command { Invoke-WebRequest -Uri "https://reportscompany-api.onrender.com/health" }
# Expected: <300ms

# Test 2: Authenticated endpoint
$headers = @{ "Authorization" = "Bearer YOUR_JWT" }
Measure-Command { Invoke-WebRequest -Uri "https://reportscompany-api.onrender.com/v1/me" -Headers $headers }
# Expected: <400ms (was 900ms)

# Test 3: Verify rate limiting actually works now
# Hit an endpoint 65 times rapidly — should get 429 after 60
for ($i = 0; $i -lt 65; $i++) {
    $r = Invoke-WebRequest -Uri "https://reportscompany-api.onrender.com/v1/me" -Headers $headers -SkipHttpErrorCheck
    if ($r.StatusCode -eq 429) { Write-Host "Rate limited at request $i"; break }
}
```

---

## Phase 2: Cache Stripe Plan Data (Critical: C3, High: H3)

### What This Fixes
- **C3:** `get_plan_catalog()` calls Stripe API live for every plan on every request (~1-2 seconds)
- **H3:** `get_plan_info()` fetches entire catalog (all Stripe calls) to return one plan

### File: `apps/api/src/api/services/plans.py` — Add in-memory cache

```python
"""
Plan Catalog Service — with caching.

BEFORE: Every call fetched all plans from DB, then called stripe.Price.retrieve()
        per plan (4 HTTP roundtrips = 800-2000ms).
AFTER:  Cached in memory for 1 hour. First call pays the cost, subsequent = ~0ms.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
import stripe
import os
import time
import logging

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class StripeBilling(BaseModel):
    amount: int
    currency: str
    interval: str
    interval_count: int
    nickname: Optional[str] = None


class PlanCatalog(BaseModel):
    plan_slug: str
    plan_name: str
    stripe_price_id: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    stripe_billing: Optional[StripeBilling] = None


# ── In-Memory Cache ──────────────────────────────────────────────────────

_plan_cache: Dict[str, PlanCatalog] | None = None
_plan_cache_time: float = 0
_CACHE_TTL_SECONDS = 3600  # 1 hour


def invalidate_plan_cache():
    """
    Call this when plans change. Hook into:
    - Stripe webhook handler (price.updated, product.updated)
    - Admin plan management endpoints
    """
    global _plan_cache, _plan_cache_time
    _plan_cache = None
    _plan_cache_time = 0
    logger.info("Plan cache invalidated")


def get_plan_catalog(cur) -> Dict[str, PlanCatalog]:
    """
    Returns plan catalog, cached in memory for 1 hour.
    
    First call:  DB query + Stripe API × N plans (~1-2 seconds)
    Cached call: Returns dict from memory (~0ms)
    """
    global _plan_cache, _plan_cache_time

    now = time.time()
    if _plan_cache is not None and (now - _plan_cache_time) < _CACHE_TTL_SECONDS:
        return _plan_cache

    # ── Cache miss: fetch from DB + Stripe ───────────────────────────
    try:
        cur.execute("""
            SELECT plan_slug, plan_name, stripe_price_id, description, is_active
            FROM plans WHERE is_active = TRUE ORDER BY plan_slug
        """)
    except Exception:
        cur.execute("""
            SELECT slug AS plan_slug, name AS plan_name, stripe_price_id,
                   description, TRUE AS is_active
            FROM plans ORDER BY slug
        """)

    rows = cur.fetchall()
    catalog: Dict[str, PlanCatalog] = {}

    for row in rows:
        plan_slug, plan_name, stripe_price_id = row[0], row[1], row[2]
        description = row[3]
        is_active = row[4] if len(row) > 4 else True

        stripe_billing = None
        if stripe_price_id and stripe.api_key:
            try:
                price = stripe.Price.retrieve(stripe_price_id)
                recurring = price.get("recurring")
                if recurring and price.get("unit_amount"):
                    stripe_billing = StripeBilling(
                        amount=price["unit_amount"],
                        currency=price["currency"],
                        interval=recurring["interval"],
                        interval_count=recurring.get("interval_count", 1),
                        nickname=price.get("nickname"),
                    )
            except Exception as e:
                logger.warning(f"Stripe price fetch failed for {plan_slug}: {e}")

        catalog[plan_slug] = PlanCatalog(
            plan_slug=plan_slug,
            plan_name=plan_name,
            stripe_price_id=stripe_price_id,
            description=description,
            is_active=is_active,
            stripe_billing=stripe_billing,
        )

    _plan_cache = catalog
    _plan_cache_time = now
    logger.info(f"Plan catalog cached ({len(catalog)} plans)")
    return catalog


def get_plan_info(cur, plan_slug: str) -> Optional[PlanCatalog]:
    """Get a single plan. Uses cached catalog so no extra Stripe calls."""
    catalog = get_plan_catalog(cur)
    return catalog.get(plan_slug)
```

### Verification

```powershell
# Hit plan-usage twice — second call should be dramatically faster
$headers = @{ "Authorization" = "Bearer YOUR_JWT" }
Measure-Command { Invoke-WebRequest -Uri "https://reportscompany-api.onrender.com/v1/account/plan-usage" -Headers $headers }
# First call: may still take 1-2s (Stripe fetch + cache)
Measure-Command { Invoke-WebRequest -Uri "https://reportscompany-api.onrender.com/v1/account/plan-usage" -Headers $headers }
# Second call: should be <300ms (cached)
```

---

## Phase 3: Fix Duplicate and N+1 Queries (Critical: C4, C5, High: H1, Medium: M1)

### What This Fixes
- **C4:** Affiliate overview calls `get_sponsored_accounts()` twice per request
- **C5:** N+1 group membership query (1 per sponsored account × 2 calls = 40+ queries)
- **H1:** Plan-usage calls `resolve_plan_for_account` and `get_monthly_usage` twice
- **M1:** Correlated subquery in schedule_runs count

### File 1: `apps/api/src/api/services/affiliates.py` — Full rewrite

```python
"""
Affiliate Services — Rewritten for performance.

BEFORE: get_sponsored_accounts ran 1 + N queries (N = sponsored account count).
        get_affiliate_overview called get_sponsored_accounts just to count/sum.
        Route called both = everything ran twice.
AFTER:  get_sponsored_accounts runs exactly 2 queries (main + batch groups).
        get_affiliate_overview runs 1 lightweight aggregate query.
        Route calls each once.
"""

from typing import Dict, Any, List


def get_sponsored_accounts(cur, affiliate_account_id: str) -> List[Dict[str, Any]]:
    """
    Get all sponsored accounts with usage metrics and group memberships.
    Uses exactly 2 queries regardless of account count (was 1 + N).
    """
    # Query 1: All sponsored accounts with report stats
    cur.execute("""
        SELECT
            a.id::text AS account_id,
            a.name,
            a.plan_slug,
            a.account_type,
            a.created_at,
            COALESCE(u.report_count, 0) AS reports_this_month,
            u.last_report_at
        FROM accounts a
        LEFT JOIN (
            SELECT 
                account_id,
                COUNT(*) AS report_count,
                MAX(generated_at) AS last_report_at
            FROM report_generations
            WHERE generated_at >= DATE_TRUNC('month', NOW())
              AND status IN ('completed', 'processing')
            GROUP BY account_id
        ) u ON u.account_id = a.id
        WHERE a.sponsor_account_id = %s::uuid
        ORDER BY u.report_count DESC NULLS LAST, a.created_at DESC
    """, (affiliate_account_id,))

    rows = cur.fetchall()
    if not rows:
        return []

    account_ids = [row[0] for row in rows]

    # Query 2: ALL group memberships in ONE batch (was: 1 query per account)
    cur.execute("""
        SELECT
            cgm.member_id::text AS account_id,
            cg.id::text AS group_id,
            cg.name AS group_name
        FROM contact_group_members cgm
        JOIN contact_groups cg ON cgm.group_id = cg.id
        WHERE cgm.member_type = 'sponsored_agent'
          AND cgm.member_id = ANY(%s::uuid[])
          AND cgm.account_id = %s::uuid
    """, (account_ids, affiliate_account_id))

    groups_by_account: Dict[str, list] = {}
    for group_row in cur.fetchall():
        aid = group_row[0]
        if aid not in groups_by_account:
            groups_by_account[aid] = []
        groups_by_account[aid].append({
            "id": group_row[1],
            "name": group_row[2],
        })

    return [
        {
            "account_id": row[0],
            "name": row[1],
            "plan_slug": row[2],
            "account_type": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "reports_this_month": row[5],
            "last_report_at": row[6].isoformat() if row[6] else None,
            "groups": groups_by_account.get(row[0], []),
        }
        for row in rows
    ]


def get_affiliate_overview(cur, affiliate_account_id: str) -> Dict[str, Any]:
    """
    Lightweight aggregate metrics. Does NOT call get_sponsored_accounts().
    Single query, O(1) regardless of account count.
    """
    cur.execute("""
        SELECT
            COUNT(*) AS sponsored_count,
            COALESCE(SUM(u.report_count), 0) AS total_reports_this_month
        FROM accounts a
        LEFT JOIN (
            SELECT account_id, COUNT(*) AS report_count
            FROM report_generations
            WHERE generated_at >= DATE_TRUNC('month', NOW())
              AND status IN ('completed', 'processing')
            GROUP BY account_id
        ) u ON u.account_id = a.id
        WHERE a.sponsor_account_id = %s::uuid
    """, (affiliate_account_id,))

    row = cur.fetchone()
    return {
        "sponsored_count": row[0] if row else 0,
        "total_reports_this_month": row[1] if row else 0,
    }


def verify_affiliate_account(cur, account_id: str) -> bool:
    """Check if account is an industry affiliate."""
    cur.execute(
        "SELECT account_type FROM accounts WHERE id = %s::uuid",
        (account_id,),
    )
    row = cur.fetchone()
    return row[0] == "INDUSTRY_AFFILIATE" if row else False
```

### File 2: `apps/api/src/api/services/usage.py` — Fix correlated subquery

In `get_monthly_usage()`, replace the schedule_runs query (~line 60-72):

```python
# BEFORE (correlated subquery — scans schedules for every run):
cur.execute("""
    SELECT COUNT(*) FROM schedule_runs
    WHERE schedule_id IN (
        SELECT id FROM schedules WHERE account_id = %s
    )
    AND created_at >= %s::date
    AND created_at < (%s::date + INTERVAL '1 day')
    AND status IN ('completed', 'processing')
""", (account_id, period_start, period_end))

# AFTER (JOIN — single pass):
cur.execute("""
    SELECT COUNT(*)
    FROM schedule_runs sr
    JOIN schedules s ON sr.schedule_id = s.id
    WHERE s.account_id = %s
      AND sr.created_at >= %s::date
      AND sr.created_at < (%s::date + INTERVAL '1 day')
      AND sr.status IN ('completed', 'processing')
""", (account_id, period_start, period_end))
```

### File 3: `apps/api/src/api/routes/account.py` — Eliminate duplicate calls in plan-usage

In `get_current_account_plan_usage()`, replace the three separate service calls:

```python
# BEFORE (6-8 queries — resolve + usage + evaluate which repeats both):
plan = resolve_plan_for_account(cur, account_id)        # queries 1-2
usage = get_monthly_usage(cur, account_id)               # queries 3-4
decision, info = evaluate_report_limit(cur, account_id)  # queries 5-8 (repeats!)

# AFTER (3-4 queries — evaluate returns plan and usage in info dict):
decision, info = evaluate_report_limit(cur, account_id)  # queries 1-4 only
plan = info["plan"]
usage = info["usage"]
```

The rest of the function stays the same — it already reads `plan` and `usage` by those names.

### File 4: `apps/api/src/api/routes/affiliates.py` — No code change needed

The overview route already calls `get_affiliate_overview()` and `get_sponsored_accounts()` separately. Now that `get_affiliate_overview()` no longer calls `get_sponsored_accounts()` internally, the duplication is eliminated without touching the route.

### Verification

```powershell
$headers = @{ "Authorization" = "Bearer YOUR_JWT" }

# Affiliate overview (was 3-8 seconds)
Measure-Command { Invoke-WebRequest -Uri "https://reportscompany-api.onrender.com/v1/affiliate/overview" -Headers $headers }
# Expected: <500ms

# Plan usage (was 3-5 seconds)
Measure-Command { Invoke-WebRequest -Uri "https://reportscompany-api.onrender.com/v1/account/plan-usage" -Headers $headers }
# Expected: <300ms
```

---

## Phase 4: Database Indexes

### What This Fixes
- Missing indexes on all high-frequency query patterns
- Ensures EXPLAIN plans show Index Scan, not Seq Scan

### Run in PostgreSQL Console

Connect to Render PostgreSQL and run:

```sql
-- Report generation queries (affiliate overview, usage tracking, report list)
CREATE INDEX IF NOT EXISTS idx_report_gen_account_status_generated
    ON report_generations(account_id, status, generated_at DESC);

-- Sponsored account lookups
CREATE INDEX IF NOT EXISTS idx_accounts_sponsor
    ON accounts(sponsor_account_id)
    WHERE sponsor_account_id IS NOT NULL;

-- Batch group membership lookups (after N+1 fix)
CREATE INDEX IF NOT EXISTS idx_cgm_member_lookup
    ON contact_group_members(member_type, member_id, account_id);

-- Schedule lookups for usage counting
CREATE INDEX IF NOT EXISTS idx_schedules_account
    ON schedules(account_id);

-- JWT blacklist checks (every authenticated request)
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_hash
    ON jwt_blacklist(token_hash);

-- Schedule runs for usage counting  
CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_date
    ON schedule_runs(schedule_id, created_at);

-- API key lookups (auth middleware)
CREATE INDEX IF NOT EXISTS idx_api_keys_hash
    ON api_keys(key_hash)
    WHERE is_active = TRUE;

-- Verify
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

### Verification

```sql
EXPLAIN ANALYZE
SELECT a.id, a.name FROM accounts a
WHERE a.sponsor_account_id = 'YOUR_AFFILIATE_UUID'::uuid;
-- Must show "Index Scan using idx_accounts_sponsor" not "Seq Scan"
```

---

## Phase 5: Sponsored Account Detail — Combine 4 Queries into 1 (Medium: M4)

### What This Fixes
- **M4:** `GET /affiliate/accounts/{id}` runs 4 sequential queries for data that can be fetched in 1

### File: `apps/api/src/api/routes/affiliates.py`

Replace lines ~716-759 (the `get_sponsored_account_detail` handler). Replace the 4 separate queries with:

```python
cur.execute("""
    SELECT
        a.id::text,
        a.name,
        a.plan_slug,
        a.is_active,
        a.created_at,
        (SELECT COUNT(*) FROM report_generations
         WHERE account_id = a.id
           AND generated_at >= date_trunc('month', CURRENT_DATE)
           AND status IN ('completed', 'processing')) AS reports_this_month,
        (SELECT MAX(generated_at) FROM report_generations
         WHERE account_id = a.id) AS last_report_at,
        (SELECT COUNT(*) FROM report_generations
         WHERE account_id = a.id
           AND status IN ('completed', 'processing')) AS total_reports
    FROM accounts a
    WHERE a.id = %s::uuid
      AND a.sponsor_account_id = %s::uuid
""", (sponsored_account_id, account_id))

row = cur.fetchone()
if not row:
    raise HTTPException(status_code=404, detail="Sponsored account not found")

return {
    "account": {
        "account_id": row[0],
        "name": row[1],
        "plan_slug": row[2],
        "is_active": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
    },
    "metrics": {
        "reports_this_month": row[5],
        "total_reports": row[7],
        "last_report_at": row[6].isoformat() if row[6] else None,
    },
}
```

**Note:** The original code queries a `reports` table (lines 737, 746, 756) but other queries use `report_generations`. Verify which table name is correct. The fix above uses `report_generations` to be consistent with the rest of the codebase.

---

## Phase 6: Dead Code Cleanup (Medium: M5, Low: L1, L3, L5)

### What This Fixes
- **M5:** Duplicate `GET/POST /branding` route definitions (Phase 30 vs Phase W2)
- **L1:** `RLSContextMiddleware` is a no-op (already removed from middleware in Phase 1)
- **L3:** `CREATE TABLE IF NOT EXISTS` in request handler (DDL in a route)
- **L5:** Debug logging on every `/reports/` request

### Changes

**`apps/api/src/api/routes/affiliates.py`:**

1. **Remove duplicate branding routes (M5).** Lines ~251-363 (Phase 30 version) and ~502-579 (Phase W2 version) are duplicates. Keep whichever version is more complete and delete the other. If Phase W2 is newer, keep that one and delete Phase 30's.

2. **Remove `CREATE TABLE IF NOT EXISTS` from invite-agent (L3).** Lines ~162-172 create the `signup_tokens` table inside the request handler. Remove this block entirely. Create the table via a migration instead:

```sql
-- Run once in PostgreSQL console or add to migrations:
CREATE TABLE IF NOT EXISTS signup_tokens (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    account_id UUID NOT NULL REFERENCES accounts(id),
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
);
```

**`apps/api/src/api/middleware/rls.py`:**

3. **Delete or leave as-is (L1).** Already removed from middleware registration in Phase 1. File is harmless but can be deleted for clarity.

**`apps/api/src/api/middleware/authn.py`:**

4. **Already fixed in Phase 1.** Debug logging (L5) was removed in the rewrite. If you didn't use the full rewrite, find and remove:
```python
# DELETE these lines (~line 30-31):
if "/reports/" in path:
    logger.info(f"AUTH_DEBUG: path={path}, ...")
```

**`apps/api/src/api/settings.py`:**

5. **Remove JWT secret preview logging (L2).** Find ~line 35-36 and remove or change to:
```python
# BEFORE:
logger.info(f"JWT_SECRET preview: {settings.JWT_SECRET[:10]}...")

# AFTER (log length only, not content):
logger.info(f"JWT_SECRET configured ({len(settings.JWT_SECRET)} chars)")
```

---

## Phase 7: Error Handling Hardening (Medium: M2)

### What This Fixes
- **M2:** Multiple `except Exception: pass` blocks that swallow errors silently

### Changes

Already partially addressed in Phase 1 (blacklist checks now fail closed). Remaining locations:

**`apps/api/src/api/services/usage.py` ~line 76-78:**
```python
# BEFORE:
except Exception:
    pass  # silently returns 0

# AFTER:
except Exception as e:
    logger.warning(f"schedule_runs query failed (table may not exist): {e}")
    # Returns 0 — acceptable fallback for missing table
```

**`apps/api/src/api/services/plans.py` ~line 69-75:**
```python
# BEFORE:
except Exception:
    # Fall back to old column names
    cur.execute("""SELECT slug AS plan_slug ...""")

# AFTER:
except Exception as e:
    logger.warning(f"Plans query failed with new columns, trying legacy: {e}")
    cur.execute("""SELECT slug AS plan_slug ...""")
```

**`apps/api/src/api/routes/affiliates.py` ~line 306, 340, 556-558 (branding queries):**
```python
# BEFORE:
except Exception:
    pass

# AFTER:
except Exception as e:
    logger.warning(f"Branding query failed, trying fallback: {e}")
```

---

## Deployment Checklist

```
Phase 1  →  poetry add psycopg-pool
         →  Replace db.py, authn.py, update main.py middleware order
         →  Deploy to Render
         →  Verify: /v1/me < 400ms, rate limiting works
         
Phase 2  →  Replace plans.py
         →  Deploy
         →  Verify: plan-usage 2nd call < 300ms

Phase 3  →  Replace services/affiliates.py
         →  Edit services/usage.py (JOIN fix)
         →  Edit routes/account.py (eliminate duplicate calls)
         →  Deploy
         →  Verify: affiliate/overview < 500ms

Phase 4  →  Run CREATE INDEX statements in Postgres console
         →  Verify: EXPLAIN ANALYZE shows index scans

Phase 5  →  Edit routes/affiliates.py (combine detail queries)
         →  Deploy
         →  Verify: sponsored account detail < 200ms

Phase 6  →  Remove duplicate branding routes
         →  Remove CREATE TABLE from invite handler
         →  Remove debug logging, JWT secret preview
         →  Deploy

Phase 7  →  Add logging to all silent except blocks
         →  Deploy
```

---

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Middleware overhead | 600-1500ms | <15ms |
| `/v1/affiliate/overview` | 3-8s | <300ms |
| `/v1/account/plan-usage` | 3-5s | <200ms (cached) |
| `/v1/me` | 900ms | <200ms |
| Rate limiting | **Broken** (never enforced) | Working |
| Blacklist security | Fail-open (allows logged-out tokens on DB error) | Fail-closed |
| **Full affiliate page load** | **8-14s** | **<1.5s** |
| **Estimated improvement** | | **20-50x faster** |

---

## All Audit Findings — Status Tracker

| ID | Severity | Issue | Fixed In |
|----|----------|-------|----------|
| C1 | Critical | No connection pooling | Phase 1 |
| C2 | Critical | Middleware raw connections ×3-5 | Phase 1 |
| C3 | Critical | Live Stripe API calls per request | Phase 2 |
| C4 | Critical | Duplicate get_sponsored_accounts() | Phase 3 |
| C5 | Critical | N+1 group membership queries | Phase 3 |
| H1 | High | Duplicate plan/usage calls | Phase 3 |
| H2 | High | Rate limit DB query per request | Phase 1 |
| H3 | High | get_plan_info fetches all plans | Phase 2 |
| H4 | High | Middleware ordering inverted (rate limit broken) | Phase 1 |
| M1 | Medium | Correlated subquery in schedule_runs | Phase 3 |
| M2 | Medium | Fail-open error handling (security) | Phase 1 + 7 |
| M3 | Medium | SQL injection in set_rls f-string | Phase 1 |
| M4 | Medium | 4 queries for 1 sponsored account detail | Phase 5 |
| M5 | Medium | Duplicate branding route definitions | Phase 6 |
| L1 | Low | RLSContextMiddleware is a no-op | Phase 1 |
| L2 | Low | JWT secret logged at startup | Phase 6 |
| L3 | Low | CREATE TABLE in request handler | Phase 6 |
| L4 | Low | get_plan_info fetches entire catalog | Phase 2 |
| L5 | Low | Debug logging on every /reports/ request | Phase 1 |
