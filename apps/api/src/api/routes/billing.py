from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
import os, stripe, psycopg
from ..settings import settings
from ..db import db_conn, set_rls, fetchone_dict
from .reports import require_account_id  # temp auth shim

router = APIRouter(prefix="/v1")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
APP_BASE = os.getenv("APP_BASE", "http://localhost:3000")

PRICE_MAP = {
  "starter": os.getenv("STARTER_PRICE_ID"),
  "professional": os.getenv("PRO_PRICE_ID"),
  "enterprise": os.getenv("ENTERPRISE_PRICE_ID"),
}

class CheckoutBody(BaseModel):
  plan: str  # starter|professional|enterprise

@router.post("/billing/checkout", status_code=status.HTTP_200_OK)
def create_checkout(body: CheckoutBody, request: Request, account_id: str = Depends(require_account_id)):
    plan = body.plan.lower()
    price = PRICE_MAP.get(plan)
    if not price:
        raise HTTPException(status_code=400, detail="Unknown plan")

    # Ensure account has stripe_customer_id
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute("SELECT name, email FROM (SELECT a.name, u.email FROM accounts a LEFT JOIN users u ON u.account_id=a.id WHERE a.id=%s LIMIT 1) t", (account_id,))
        row = fetchone_dict(cur) or {"name": "Market Reports Customer", "email": None}

    # load account stripe IDs
    customer_id = None
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stripe_customer_id FROM accounts WHERE id=%s", (account_id,))
            r = cur.fetchone()
            customer_id = r[0] if r and r[0] else None

    if not customer_id:
        customer = stripe.Customer.create(name=row.get("name") or "Market Reports Customer", metadata={"account_id": account_id})
        customer_id = customer["id"]
        with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE accounts SET stripe_customer_id=%s WHERE id=%s", (customer_id, account_id))

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price, "quantity": 1}],
        success_url=f"{APP_BASE}/app/billing?status=success",
        cancel_url=f"{APP_BASE}/app/billing?status=cancel",
        allow_promotion_codes=True,
        automatic_tax={"enabled": False},
        metadata={"account_id": account_id, "plan": plan},
    )
    return {"url": session["url"]}

@router.get("/billing/portal")
def billing_portal(request: Request, account_id: str = Depends(require_account_id)):
    # find customer
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stripe_customer_id FROM accounts WHERE id=%s", (account_id,))
            r = cur.fetchone()
            if not r or not r[0]:
                raise HTTPException(status_code=400, detail="No Stripe customer for account")
            customer_id = r[0]

    portal = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{APP_BASE}/app/billing"
    )
    return {"url": portal["url"]}

