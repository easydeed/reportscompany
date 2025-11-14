import os, time, hashlib, hmac, base64
from typing import Optional, Tuple
import jwt, bcrypt

JWT_ALG = "HS256"

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def sign_jwt(payload: dict, secret: str, ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    payload = {**payload, "iat": now, "exp": now + ttl_seconds}
    return jwt.encode(payload, secret, algorithm=JWT_ALG)

def verify_jwt(token: str, secret: str) -> Optional[dict]:
    import logging
    logger = logging.getLogger(__name__)
    try:
        return jwt.decode(token, secret, algorithms=[JWT_ALG])
    except Exception as e:
        logger.error(f"🔥 JWT verification exception: {type(e).__name__}: {str(e)}")
        return None

def new_api_key(prefix: str = "mr_live_") -> Tuple[str, str, str]:
    """
    Returns (api_key, key_prefix, key_hash). Store only key_hash in DB.
    """
    raw = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    api_key = f"{prefix}{raw}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_prefix = api_key[:10]
    return api_key, key_prefix, key_hash

def hash_api_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()













