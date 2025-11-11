import json, hashlib, os
from datetime import datetime, date
import redis

R = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def safe_json_dumps(obj):
    """
    JSON serialization with datetime handling.
    Converts datetime/date objects to ISO format strings.
    """
    def default_handler(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    
    return json.dumps(obj, default=default_handler)

def _key(namespace: str, payload: dict) -> str:
    raw = safe_json_dumps(payload)  # Use safe version for datetime handling
    return f"mr:{namespace}:{hashlib.md5(raw.encode()).hexdigest()}"

def get(namespace: str, payload: dict):
    k = _key(namespace, payload)
    v = R.get(k)
    return json.loads(v) if v else None

def set(namespace: str, payload: dict, data: dict, ttl_s=3600):
    k = _key(namespace, payload)
    R.setex(k, ttl_s, safe_json_dumps(data))  # Use safe version for datetime handling





