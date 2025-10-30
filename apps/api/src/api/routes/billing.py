from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
import stripe, psycopg
from ..settings import settings
from ..db import db_conn, set_rls, fetchone_dict
from .reports import require_account_id  # temp auth shim

router = APIRouter(prefix="/v1")

# Note: stripe.api_key will be set in each function to ensure settings are loaded
APP_BASE = settings.APP_BASE

def get_price_map():
    """Get price map from settings (evaluated at runtime)"""
    return {
        "starter": settings.STARTER_PRICE_ID,
        "professional": settings.PRO_PRICE_ID,
        "enterprise": settings.ENTERPRISE_PRICE_ID,
    }

class CheckoutBody(BaseModel):
  plan: str  # starter|professional|enterprise

@router.get("/billing/debug")
def debug_config():
    """Debug endpoint to check Stripe config"""
    return {
        "stripe_key_set": bool(settings.STRIPE_SECRET_KEY),
        "starter_price": settings.STARTER_PRICE_ID,
        "pro_price": settings.PRO_PRICE_ID,
        "enterprise_price": settings.ENTERPRISE_PRICE_ID,
        "price_map": get_price_map()
    }

@router.post("/billing/checkout", status_code=status.HTTP_200_OK)
def create_checkout(body: CheckoutBody, request: Request, account_id: str = Depends(require_account_id)):
    # Set Stripe API key at runtime to ensure settings are loaded
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    plan = body.plan.lower()
    price_map = get_price_map()
    price = price_map.get(plan)
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
    # Set Stripe API key at runtime
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
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

