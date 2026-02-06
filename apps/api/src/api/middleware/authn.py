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
