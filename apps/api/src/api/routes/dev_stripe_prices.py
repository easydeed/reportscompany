"""
Development endpoint to list Stripe prices.
Public endpoint for verifying Stripe integration.
"""

from fastapi import APIRouter, HTTPException, Request
from ..db import db_conn
from ..services.plans import get_plan_catalog
import os

router = APIRouter(prefix="/v1/dev")


@router.get("/stripe-prices")
def list_stripe_prices(request: Request):
    """
    List all Stripe prices from the plan catalog.
    
    Public endpoint - no authentication required.
    Useful for debugging and verifying Stripe integration.
    Returns the enriched plan catalog with Stripe pricing data.
    """
    # Mark this endpoint as public for auth middleware
    request.state.skip_auth = True
    
    with db_conn() as (conn, cur):
        catalog = get_plan_catalog(cur)
        
        # Format for readability
        result = []
        for slug, plan in catalog.items():
            entry = {
                "plan_slug": slug,
                "plan_name": plan["plan_name"],
                "stripe_price_id": plan["stripe_price_id"],
                "description": plan.get("description"),
            }
            
            if plan["amount"]:
                entry["pricing"] = {
                    "amount": plan["amount"],
                    "amount_display": f"${plan['amount'] / 100:.2f}",
                    "currency": plan["currency"],
                    "interval": plan["interval"],
                    "interval_count": plan["interval_count"],
                    "nickname": plan["nickname"],
                }
            else:
                entry["pricing"] = None
            
            result.append(entry)
        
        return {
            "plans": result,
            "count": len(result),
            "stripe_api_key_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        }

