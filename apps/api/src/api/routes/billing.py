"""
Phase 29D: Stripe Billing Routes

Handles subscription checkout and customer portal access.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Literal
from ..db import db_conn, set_rls
from .reports import require_account_id
from ..config.billing import (
    STRIPE_SECRET_KEY,
    validate_stripe_config
)
from ..services.plan_lookup import get_plan_by_slug

router = APIRouter(prefix="/v1/billing", tags=["billing"])

WEB_BASE = os.getenv("WEB_BASE", "https://reportscompany-web.vercel.app")

# Lazy import stripe to avoid import errors if not installed
try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None


class CheckoutRequest(BaseModel):
    """Request to create a Stripe Checkout Session."""
    plan_slug: str  # Any plan_slug with stripe_price_id set


class CheckoutResponse(BaseModel):
    """Response containing Stripe Checkout Session URL."""
    url: str


class PortalResponse(BaseModel):
    """Response containing Stripe Customer Portal URL."""
    url: str


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout_session(
    body: CheckoutRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Create a Stripe Checkout Session for plan upgrade.
    
    Phase 29D: Allows REGULAR users to upgrade from free → pro/team.
    
    Flow:
    1. Validate user account is eligible (REGULAR, not sponsored)
    2. Get or create Stripe customer
    3. Create checkout session with selected plan
    4. Return checkout URL for frontend redirect
    
    Returns:
        CheckoutResponse with Stripe checkout URL
    
    Raises:
        400: Invalid plan, account is sponsored, or missing Stripe config
        500: Stripe API error
    """
    # Validate Stripe config
    is_valid, missing = validate_stripe_config()
    if not is_valid:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "stripe_config_missing",
                "message": f"Stripe is not configured. Missing: {', '.join(missing)}"
            }
        )
    
    if not stripe:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "stripe_not_installed",
                "message": "Stripe SDK not installed"
            }
        )
    
    with db_conn() as (conn, cur):
        # Get plan from database (PASS 1: Single source of truth)
        plan = get_plan_by_slug(cur, body.plan_slug)
        if not plan:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "plan_not_found",
                    "message": f"Plan '{body.plan_slug}' does not exist or is inactive"
                }
            )
        
        price_id = plan.get("stripe_price_id")
        if not price_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "plan_not_configured",
                    "message": f"Plan '{body.plan_slug}' is not configured for Stripe checkout"
                }
            )
        set_rls(cur, account_id)
        
        # Load account details
        cur.execute("""
            SELECT 
                id::text,
                name,
                account_type,
                plan_slug,
                sponsor_account_id::text,
                stripe_customer_id
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        
        acc_row = cur.fetchone()
        if not acc_row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        acc_id, acc_name, acc_type, current_plan, sponsor_id, stripe_customer_id = acc_row
        
        # Validate account can upgrade
        if acc_type != 'REGULAR':
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_account_type",
                    "message": f"Only REGULAR accounts can upgrade via Stripe. Your account type: {acc_type}"
                }
            )
        
        if sponsor_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "sponsored_account",
                    "message": "Sponsored accounts cannot self-upgrade. Contact your affiliate for plan changes."
                }
            )
        
        # Get user email for Stripe customer
        cur.execute("""
            SELECT email
            FROM users
            WHERE account_id = %s::uuid
            LIMIT 1
        """, (account_id,))
        
        user_row = cur.fetchone()
        if not user_row:
            raise HTTPException(
                status_code=400,
                detail="No user found for this account"
            )
        
        user_email = user_row[0]
        
        # Ensure Stripe customer exists
        if not stripe_customer_id:
            try:
                # Create Stripe customer
                customer = stripe.Customer.create(
                    email=user_email,
                    metadata={
                        "account_id": acc_id,
                        "account_name": acc_name,
                    }
                )
                stripe_customer_id = customer.id
                
                # Save customer ID
                cur.execute("""
                    UPDATE accounts
                    SET stripe_customer_id = %s
                    WHERE id = %s::uuid
                """, (stripe_customer_id, account_id))
                
                conn.commit()
                
            except stripe.error.StripeError as e:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "stripe_customer_creation_failed",
                        "message": str(e)
                    }
                )
        
        # Create Checkout Session
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                customer=stripe_customer_id,
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                success_url=f"{WEB_BASE}/account/plan?checkout=success",
                cancel_url=f"{WEB_BASE}/account/plan?checkout=cancel",
                metadata={
                    "account_id": acc_id,
                    "plan_slug": body.plan_slug,
                },
                subscription_data={
                    "metadata": {
                        "account_id": acc_id,
                        "plan_slug": body.plan_slug,
                    }
                }
            )
            
            return {"url": session.url}
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "checkout_session_failed",
                    "message": str(e)
                }
            )


@router.get("/portal", response_model=PortalResponse)
def create_portal_session(
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Create a Stripe Customer Portal Session.
    
    Phase 29D: Allows users with active subscriptions to manage billing.
    
    Flow:
    1. Verify account has Stripe customer ID
    2. Create portal session
    3. Return portal URL for frontend redirect
    
    Returns:
        PortalResponse with Stripe portal URL
    
    Raises:
        400: No Stripe customer for this account
        500: Stripe API error or missing config
    """
    # Validate Stripe config
    is_valid, missing = validate_stripe_config()
    if not is_valid:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "stripe_config_missing",
                "message": f"Stripe is not configured. Missing: {', '.join(missing)}"
            }
        )
    
    if not stripe:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "stripe_not_installed",
                "message": "Stripe SDK not installed"
            }
        )
    
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        
        # Load stripe_customer_id
        cur.execute("""
            SELECT stripe_customer_id
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        
        acc_row = cur.fetchone()
        if not acc_row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        stripe_customer_id = acc_row[0]
        
        if not stripe_customer_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "no_stripe_customer",
                    "message": "No Stripe customer associated with this account. You must complete checkout first."
                }
            )
        
        # Create portal session
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=stripe_customer_id,
                return_url=f"{WEB_BASE}/account/plan",
            )
            
            return {"url": portal_session.url}
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "portal_session_failed",
                    "message": str(e)
                }
            )
