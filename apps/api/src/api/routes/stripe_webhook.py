"""
Phase 29D: Stripe Webhook Handler

Syncs Stripe subscription events back to accounts.plan_slug.
Allows existing plan/limit system to work seamlessly with Stripe.
"""

from fastapi import APIRouter, Request, HTTPException
import os
import psycopg
import logging
from ..settings import settings
from ..config.billing import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET
)
from ..services.plan_lookup import get_plan_slug_for_stripe_price
from ..services.billing_state import update_account_billing_state

router = APIRouter(prefix="/v1")

logger = logging.getLogger(__name__)

# Lazy import stripe
try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None
    logger.warning("Stripe SDK not installed")


@router.post("/webhooks/stripe")
async def stripe_webhook(req: Request):
    """
    Handle Stripe webhook events.
    
    Phase 29D: Updates accounts.plan_slug based on subscription changes.
    
    Events handled:
    - customer.subscription.created: Set plan_slug from price_id
    - customer.subscription.updated: Update plan_slug if price changed
    - customer.subscription.deleted: Downgrade to 'free'
    
    Returns:
        {"received": True} for all events (even unhandled ones)
    
    Raises:
        400: Invalid webhook signature
    """
    if not stripe or not STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook called but Stripe not configured")
        return {"received": True, "error": "Stripe not configured"}
    
    payload = await req.body()
    sig = req.headers.get("stripe-signature")
    
    # Validate webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_type = event["type"]
    data = event["data"]["object"]
    
    logger.info(f"Received Stripe event: {event_type}, ID: {event.get('id')}")
    
    # Handle subscription created/updated
    if event_type in ["customer.subscription.created", "customer.subscription.updated"]:
        subscription = data
        account_id = subscription.get("metadata", {}).get("account_id")
        
        if not account_id:
            logger.warning(f"Subscription {subscription.get('id')} missing account_id metadata")
            return {"received": True}
        
        # Get price_id from first line item
        items = subscription.get("items", {}).get("data", [])
        if not items:
            logger.warning(f"Subscription {subscription.get('id')} has no line items")
            return {"received": True}
        
        price_id = items[0].get("price", {}).get("id")
        if not price_id:
            logger.warning(f"Subscription {subscription.get('id')} missing price_id")
            return {"received": True}
        
        # Map price_id → plan_slug (PASS 1: DB lookup)
        try:
            with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    plan_slug = get_plan_slug_for_stripe_price(cur, price_id)
                    if not plan_slug:
                        logger.warning(f"Stripe webhook: no plan found for price_id={price_id}")
                        return {"received": True}
                    
                    # Update plan_slug
                    cur.execute("""
                        UPDATE accounts
                        SET plan_slug = %s
                        WHERE id = %s::uuid
                    """, (plan_slug, account_id))
                    
                    if cur.rowcount > 0:
                        logger.info(f"✅ Updated account {account_id} to plan '{plan_slug}' (price: {price_id})")
                    else:
                        logger.warning(f"Account {account_id} not found for subscription update")
                    
                    # Update subscription state (PASS 2)
                    update_account_billing_state(cur, account_id=account_id, subscription=subscription)
        
        except Exception as e:
            logger.error(f"Failed to update account {account_id}: {e}")
            # Still return 200 to prevent Stripe retries
    
    # Handle subscription deleted/canceled
    elif event_type == "customer.subscription.deleted":
        subscription = data
        account_id = subscription.get("metadata", {}).get("account_id")
        
        if not account_id:
            logger.warning(f"Deleted subscription {subscription.get('id')} missing account_id metadata")
            return {"received": True}
        
        # Downgrade to free and clear subscription state
        try:
            with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    # Downgrade plan
                    cur.execute("""
                        UPDATE accounts
                        SET plan_slug = 'free'
                        WHERE id = %s::uuid
                    """, (account_id,))
                    
                    if cur.rowcount > 0:
                        logger.info(f"✅ Downgraded account {account_id} to 'free' (subscription canceled)")
                    else:
                        logger.warning(f"Account {account_id} not found for subscription cancellation")
                    
                    # Clear subscription state (PASS 2)
                    update_account_billing_state(cur, account_id=account_id, subscription=None)
        
        except Exception as e:
            logger.error(f"Failed to downgrade account {account_id}: {e}")
    
    # Log other events but don't process
    else:
        logger.info(f"Received unhandled event type: {event_type}")
    
    return {"received": True}












