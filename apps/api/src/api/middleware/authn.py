from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import redis, time
from ..settings import settings
from ..auth import verify_jwt, hash_api_key
import psycopg

class AuthContextMiddleware(BaseHTTPMiddleware):
    """
    Resolves account_id via:
      1) Authorization: Bearer <JWT>
      2) Authorization: Bearer <API-KEY> (sha256 matched against api_keys.key_hash)
      3) X-Demo-Account (temporary fallback)
    Sets request.state.account_id if resolved. Otherwise 401.
    """
    async def dispatch(self, request: Request, call_next):
        # Pass through OPTIONS
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip auth for public endpoints
        path = request.url.path
        if path.startswith("/health") or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi") or path.startswith("/v1/auth/") or path.startswith("/dev-files/") or path.startswith("/v1/webhooks/stripe") or path.startswith("/v1/billing/debug") or path.startswith("/v1/email/unsubscribe"):
            return await call_next(request)

        acct: Optional[str] = None

        # 1) JWT
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            # Try JWT first
            claims = verify_jwt(token, settings.JWT_SECRET)
            if claims and claims.get("account_id"):
                acct = claims["account_id"]
            else:
                # Try API key
                key_hash = hash_api_key(token)
                with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                          SELECT account_id FROM api_keys
                          WHERE key_hash=%s AND is_active=TRUE
                          """, (key_hash,))
                        row = cur.fetchone()
                        if row:
                            acct = row[0]

        # 3) Temporary demo header
        if not acct:
            demo = request.headers.get("X-Demo-Account")
            if demo:
                acct = demo

        if not acct:
            raise HTTPException(status_code=401, detail="Unauthorized")

        request.state.account_id = acct
        return await call_next(request)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple per-account limiter using Redis minute buckets.
    Emits X-RateLimit-* headers.
    """
    def __init__(self, app):
        super().__init__(app)
        self.r = redis.from_url(settings.REDIS_URL)

    async def dispatch(self, request: Request, call_next):
        # Skip for /health and /docs
        path = request.url.path
        if path.startswith("/health") or path.startswith("/openapi") or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        acct = getattr(request.state, "account_id", None)
        if not acct:
            return await call_next(request)

        # fetch limit from DB (fallback 60 rpm)
        limit = 60
        with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT api_rate_limit FROM accounts WHERE id=%s", (acct,))
                row = cur.fetchone()
                if row and row[0]:
                    limit = int(row[0])

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
            # Too many; overwrite with 429
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"You have exceeded your rate limit of {limit} requests per minute",
                    "retry_after": reset
                },
                headers=response.headers
            )
        return response


