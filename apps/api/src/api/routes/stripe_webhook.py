from fastapi import APIRouter, Request, HTTPException
import os, stripe, psycopg, json
from ..settings import settings

router = APIRouter(prefix="/v1")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/webhooks/stripe")
async def stripe_webhook(req: Request):
    payload = await req.body()
    sig = req.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    et = event["type"]
    data = event["data"]["object"]

    # Persist event (optional)
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO billing_events (account_id, type, payload) VALUES (%s,%s,%s)",
                        (data.get("metadata",{}).get("account_id") if isinstance(data, dict) else None, et, json.loads(payload.decode())))

    # Handle subscription lifecycle
    if et == "customer.subscription.created" or et == "customer.subscription.updated":
        sub = data
        acct_id = (sub.get("metadata") or {}).get("account_id")
        plan_slug = (sub.get("metadata") or {}).get("plan")
        if acct_id:
            with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE accounts
                        SET stripe_subscription_id=%s,
                            plan_slug=%s,
                            billing_status=%s
                        WHERE id=%s
                    """, (sub.get("id"), plan_slug, sub.get("status"), acct_id))

    if et == "customer.subscription.deleted":
        sub = data
        acct_id = (sub.get("metadata") or {}).get("account_id")
        if acct_id:
            with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE accounts
                        SET stripe_subscription_id=NULL,
                            billing_status='canceled'
                        WHERE id=%s
                    """, (acct_id,))

    if et == "invoice.payment_succeeded":
        # Optionally reset counters / mark month start
        pass

    return {"received": True}

