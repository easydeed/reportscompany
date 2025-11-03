import json, hashlib, os
import redis

R = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def _key(namespace: str, payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True)
    return f"mr:{namespace}:{hashlib.md5(raw.encode()).hexdigest()}"

def get(namespace: str, payload: dict):
    k = _key(namespace, payload)
    v = R.get(k)
    return json.loads(v) if v else None

def set(namespace: str, payload: dict, data: dict, ttl_s=3600):
    k = _key(namespace, payload)
    R.setex(k, ttl_s, json.dumps(data))




