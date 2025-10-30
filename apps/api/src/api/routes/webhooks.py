from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl, Field
import os, base64, secrets, psycopg
from ..db import db_conn, set_rls, fetchall_dicts, fetchone_dict
from .reports import require_account_id  # temp shim

router = APIRouter(prefix="/v1")

class WebhookCreateIn(BaseModel):
  url: HttpUrl
  events: list[str] = Field(default_factory=lambda: ["report.completed","report.failed"])

class WebhookOut(BaseModel):
  id: str
  url: str
  events: list[str]
  is_active: bool
  created_at: str

@router.post("/account/webhooks", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_webhook(body: WebhookCreateIn, request: Request, account_id: str = Depends(require_account_id)):
  secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
  with db_conn() as (conn, cur):
    set_rls(cur, account_id)
    cur.execute("""
      INSERT INTO webhooks (account_id, url, events, secret, is_active)
      VALUES (%s,%s,%s,%s,TRUE) RETURNING id::text, url, events, is_active, created_at::text
    """, (account_id, str(body.url), body.events, secret))
    row = fetchone_dict(cur)
  # Return secret once
  return {"webhook": row, "secret": secret}

@router.get("/account/webhooks", response_model=list[WebhookOut])
def list_webhooks(request: Request, account_id: str = Depends(require_account_id)):
  with db_conn() as (conn, cur):
    set_rls(cur, account_id)
    cur.execute("SELECT id::text, url, events, is_active, created_at::text FROM webhooks WHERE is_active=TRUE ORDER BY created_at DESC")
    return list(fetchall_dicts(cur))

@router.delete("/account/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(webhook_id: str, request: Request, account_id: str = Depends(require_account_id)):
  with db_conn() as (conn, cur):
    set_rls(cur, account_id)
    cur.execute("UPDATE webhooks SET is_active=FALSE WHERE id=%s", (webhook_id,))
  return

