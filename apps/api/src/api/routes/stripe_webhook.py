"""Verified Stripe events: acknowledge only a durable terminal disposition."""
import logging

from fastapi import APIRouter, HTTPException, Request

from ..config.billing import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from ..services.billing_envelope import expected_live_mode, normalize_verified_event
from ..services.billing_events import process_receipt, store_receipt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1")
try:
    import stripe
except ImportError:
    stripe = None


@router.post("/webhooks/stripe")
async def stripe_webhook(req: Request):
    mode = expected_live_mode(STRIPE_SECRET_KEY)
    if stripe is None or not STRIPE_WEBHOOK_SECRET or mode is None:
        raise HTTPException(status_code=503, detail="Billing webhook unavailable")
    try:
        event = stripe.Webhook.construct_event(
            await req.body(), req.headers.get("stripe-signature"), STRIPE_WEBHOOK_SECRET)
        envelope = normalize_verified_event(event, expected_live=mode)
    except (TypeError, ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid billing event") from None
    try:
        store_receipt(envelope)  # Commits independently before account processing.
        process_receipt(envelope['event_id'], envelope['livemode'])
    except Exception:
        # Never log provider payloads, DB exception text, signatures or contacts.
        logger.warning("Billing receipt or processing failed; provider retry required")
        raise HTTPException(status_code=503, detail="Billing event not processed") from None
    return {"received": True}
