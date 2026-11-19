import os, time, hashlib, hmac, base64
from typing import Optional, Tuple
import jwt, bcrypt

JWT_ALG = "HS256"

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def _password_version(password_hash: str, secret: str) -> str:
    # A token must never contain the database password verifier itself.
    return hmac.new(secret.encode(), b"password-version\0" + password_hash.encode(),
                    hashlib.sha256).hexdigest()


def session_password_matches(claims, password_hash, changed_epoch, secret):
    if not password_hash:
        return False
    if "pwd_version" in claims:
        return hmac.compare_digest(claims["pwd_version"], _password_version(password_hash, secret))
    # Pre-rollout JWTs have only a whole-second issue time. During the second
    # of a password change, only a versioned replacement can establish order.
    return changed_epoch is None or claims.get("iat", 0) > changed_epoch


def sign_jwt(payload: dict, secret: str, ttl_seconds: int = 3600, *, password_hash: Optional[str] = None) -> str:
    now = int(time.time())
    payload = {**payload, "iat": now, "exp": now + ttl_seconds}
    if password_hash is not None:
        payload["pwd_version"] = _password_version(password_hash, secret)
    return jwt.encode(payload, secret, algorithm=JWT_ALG)

def verify_jwt(token: str, secret: str) -> Optional[dict]:
    try:
        return jwt.decode(token, secret, algorithms=[JWT_ALG])
    except Exception:
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













