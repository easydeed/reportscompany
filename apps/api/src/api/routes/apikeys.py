from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel
import psycopg
from ..settings import settings
from ..auth import new_api_key
from .reports import require_account_id  # temporary; will be replaced by real auth check

router = APIRouter(prefix="/v1")

class APIKeyOut(BaseModel):
    id: str
    key_prefix: str
    name: str | None = None
    is_active: bool

class APIKeyCreateIn(BaseModel):
    name: str | None = None
    scopes: list[str] | None = None
    rate_limit: int | None = None

@router.post("/api-keys", response_model=dict)
def create_key(body: APIKeyCreateIn, request: Request, account_id: str = Depends(require_account_id)):
    api_key, prefix, key_hash = new_api_key()
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
              INSERT INTO api_keys (account_id, key_prefix, key_hash, name, scopes, rate_limit, is_active)
              VALUES (%s,%s,%s,%s,%s,%s,TRUE)
              RETURNING id::text
            """, (account_id, prefix, key_hash, body.name, body.scopes, body.rate_limit))
            key_id = cur.fetchone()[0]
    # Return the full key once
    return {"id": key_id, "api_key": api_key, "key_prefix": prefix}

@router.get("/api-keys", response_model=list[APIKeyOut])
def list_keys(request: Request, account_id: str = Depends(require_account_id)):
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id::text, key_prefix, name, is_active FROM api_keys WHERE account_id=%s ORDER BY created_at DESC", (account_id,))
            rows = cur.fetchall()
    return [{"id": r[0], "key_prefix": r[1], "name": r[2], "is_active": r[3]} for r in rows]

@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(key_id: str, request: Request, account_id: str = Depends(require_account_id)):
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE api_keys SET is_active=FALSE WHERE id=%s AND account_id=%s", (key_id, account_id))
    return







