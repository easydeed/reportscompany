from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional
import redis, time, hashlib
import logging
from ..settings import settings
from ..auth import verify_jwt, hash_api_key
import psycopg

logger = logging.getLogger(__name__)

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
        
        # Debug: Log path for reports endpoints
        if "/reports/" in path:
            logger.info(f"AUTH_DEBUG: path={path}, starts_with_reports={path.startswith('/v1/reports/')}, ends_with_data={path.endswith('/data')}")
        
        is_public = (
            path.startswith("/health") or 
            path.startswith("/docs") or 
            path.startswith("/redoc") or 
            path.startswith("/openapi") or 
            path.startswith("/v1/auth/") or 
            path.startswith("/dev-files/") or 
            path.startswith("/v1/webhooks/stripe") or 
            path.startswith("/v1/billing/debug") or 
            path.startswith("/v1/email/unsubscribe") or 
            path.startswith("/v1/dev/") or
            path == "/v1/leads/capture" or  # Public lead capture endpoint
            path.startswith("/v1/property/public/") or  # Public property report landing pages
            path.startswith("/v1/cma/") or  # Public consumer landing pages (Lead Pages)
            path.startswith("/v1/r/") or  # Public mobile report viewer
            (path.startswith("/v1/reports/") and path.endswith("/data"))  # Allow /v1/reports/{id}/data for PDF generation
        )
        
        if is_public:
            logger.info(f"AUTH_DEBUG: Allowing public access to {path}")
            return await call_next(request)

        acct: Optional[str] = None
        claims = None  # Track JWT claims for later use

        # 1) Try Authorization header first (Bearer token or API key)
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            # Try JWT first
            claims = verify_jwt(token, settings.JWT_SECRET)
            if claims and claims.get("account_id"):
                # Check if token is blacklisted (logged out)
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                try:
                    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT 1 FROM jwt_blacklist 
                                WHERE token_hash = %s AND expires_at > NOW()
                            """, (token_hash,))
                            if cur.fetchone():
                                logger.info(f"Blocked blacklisted token for {path}")
                                return JSONResponse(status_code=401, content={"detail": "Token has been invalidated"})
                except Exception as e:
                    logger.warning(f"Failed to check token blacklist: {e}")
                
                acct = claims["account_id"]
                logger.info(f"Auth via Authorization header (JWT) for {path}")
            else:
                # JWT decode failed, try API key
                if not claims:
                    logger.info(f"JWT verification failed for Authorization header on {path}, trying API key")
                
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
                            logger.info(f"Auth via Authorization header (API key) for {path}")

        # 2) Cookie fallback (mr_token)
        if not acct:
            cookie_token = request.cookies.get("mr_token")
            if cookie_token:
                claims = verify_jwt(cookie_token, settings.JWT_SECRET)
                if claims and claims.get("account_id"):
                    # Check if token is blacklisted
                    token_hash = hashlib.sha256(cookie_token.encode()).hexdigest()
                    try:
                        with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    SELECT 1 FROM jwt_blacklist 
                                    WHERE token_hash = %s AND expires_at > NOW()
                                """, (token_hash,))
                                if cur.fetchone():
                                    logger.info(f"Blocked blacklisted cookie token for {path}")
                                    return JSONResponse(status_code=401, content={"detail": "Session has expired"})
                    except Exception as e:
                        logger.warning(f"Failed to check token blacklist: {e}")
                    
                    acct = claims["account_id"]
                    logger.info(f"Auth via mr_token cookie for {path}")
                else:
                    logger.warning("JWT verification failed", extra={"path": path})

        # 3) Temporary demo header
        if not acct:
            demo = request.headers.get("X-Demo-Account")
            if demo:
                acct = demo

        if not acct:
            # IMPORTANT:
            # This middleware is implemented via Starlette's BaseHTTPMiddleware.
            # Raising HTTPException here can bypass FastAPI's exception handlers
            # (especially under newer Python/Starlette exception-group handling),
            # resulting in a 500 instead of a 401 response.
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        request.state.account_id = acct
        
        # Fetch user information including role (for admin endpoints)
        # If JWT, get user_id from claims; if API key, fetch first admin user for account
        user_info = {"account_id": acct, "role": "USER"}  # default
        
        if claims and claims.get("user_id"):
            # JWT authentication - fetch user's role and platform admin status
            with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, email, role, is_platform_admin FROM users
                        WHERE id=%s::uuid AND account_id=%s::uuid
                    """, (claims["user_id"], acct))
                    user_row = cur.fetchone()
                    if user_row:
                        user_info = {
                            "id": str(user_row[0]),
                            "email": user_row[1],
                            "role": (user_row[2] or "USER").upper(),  # Normalize to uppercase
                            "is_platform_admin": bool(user_row[3]) if user_row[3] is not None else False,
                            "account_id": acct
                        }
        
        request.state.user = user_info
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


