import json, hashlib, os
from datetime import datetime, date
from .redis_utils import create_redis_connection

R = create_redis_connection(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def safe_json_dumps(obj, sort_keys: bool = False):
    """
    JSON serialization with datetime handling.
    Converts datetime/date objects to ISO format strings.

    `sort_keys` exists for `_key` below — see D-095. It is False by default
    because the stored VALUE's field order is cosmetic, and changing it would
    rewrite every cached blob for no benefit.
    """
    def default_handler(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, default=default_handler, sort_keys=sort_keys)

def _key(namespace: str, payload: dict) -> str:
    """
    A cache key that depends on what the payload MEANS, not on the order its
    keys were typed in (D-095).

    Without `sort_keys`, Python's insertion-ordered dicts made these two
    different keys:

        {"city": "Glendora", "month": "2026-09"}
        {"month": "2026-09", "city": "Glendora"}

    — a silent 100% miss between two call sites. No error, no warning, a cache
    that never hits and a vendor bill that looks like it was never there.

    It was harmless while the only payload was built in one place
    (`tasks.py:1311`). The §7.3 rate-limit analysis recommends caching 12-month
    bucket counts on `(city, month)` from several call sites, which is precisely
    the shape that trips it, so this is fixed BEFORE that lands rather than
    after somebody wonders why the cache does nothing.

    THIS CHANGES EVERY EXISTING KEY. Deliberate and harmless: the old entries
    are orphaned, expire on their own TTL, and the first request after deploy
    refills a cold cache. There is no correctness consequence to a cache miss —
    that is the property that makes the change safe to make at all.
    """
    raw = safe_json_dumps(payload, sort_keys=True)
    return f"mr:{namespace}:{hashlib.md5(raw.encode()).hexdigest()}"

def get(namespace: str, payload: dict):
    k = _key(namespace, payload)
    v = R.get(k)
    return json.loads(v) if v else None

def set(namespace: str, payload: dict, data: dict, ttl_s=3600):
    k = _key(namespace, payload)
    R.setex(k, ttl_s, safe_json_dumps(data))  # Use safe version for datetime handling





