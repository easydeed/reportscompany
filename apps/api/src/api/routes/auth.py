from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
import psycopg
from ..settings import settings
from ..auth import sign_jwt, check_password, hash_password

router = APIRouter(prefix="/v1")

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/auth/login", response_model=LoginOut)
def login(body: LoginIn):
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
              SELECT id::text, account_id::text, password_hash FROM users WHERE email=%s AND is_active=TRUE
            """, (body.email,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            user_id, account_id, pw_hash = row
            if not pw_hash or not check_password(body.password, pw_hash):
                raise HTTPException(status_code=401, detail="Invalid credentials")

    token = sign_jwt({"sub": user_id, "account_id": account_id, "scopes": ["reports:read","reports:write"]}, settings.JWT_SECRET, ttl_seconds=3600)
    return {"access_token": token}

# Optional seed endpoint for dev (remove/guard in prod)
class SeedIn(BaseModel):
    account_id: str
    email: EmailStr
    password: str
    name: str = "Demo User"

@router.post("/auth/seed-dev", status_code=status.HTTP_201_CREATED)
def seed_dev(body: SeedIn):
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (account_id, email, password_hash, role) VALUES (%s,%s,%s,'owner') ON CONFLICT (email) DO NOTHING",
                        (body.account_id, body.email, hash_password(body.password)))
    return {"ok": True}













