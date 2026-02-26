"""
Redis Cache Utility — Phase 2

Shared thin wrapper around Redis for the API service.

- Lazy-initializes a single redis.Redis client (reused across requests)
- All cache operations are SILENT on Redis failure — never break requests
- Uses the same REDIS_URL env var as Celery

Usage:
    from api.cache import cache_get, cache_set, cache_delete

    val = cache_get("my:key")           # None if missing or Redis down
    cache_set("my:key", obj, ttl=3600)  # silently ignored if Redis down
    cache_delete("my:key")
"""

import json
import logging
from typing import Any, Optional

import redis as _redis

from .settings import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[_redis.Redis] = None


def get_redis() -> _redis.Redis:
    """Lazy-initialize a shared Redis client (connection-per-command pool)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = _redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve a value from the cache.
    Returns None on cache miss OR Redis failure (fail-safe).
    """
    try:
        raw = get_redis().get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception as exc:
        logger.debug("cache_get miss (Redis error): %s — %s", key, exc)
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    """
    Store a JSON-serializable value with a TTL.
    Silently no-ops on Redis failure — callers need not handle errors.
    """
    try:
        get_redis().setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("cache_set failed: %s — %s", key, exc)


def cache_delete(key: str) -> None:
    """Invalidate a single cache key. Silently ignores Redis failures."""
    try:
        get_redis().delete(key)
    except Exception as exc:
        logger.debug("cache_delete failed: %s — %s", key, exc)
