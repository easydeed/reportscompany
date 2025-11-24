"""
Plan Lookup Service - PASS 1

Database-backed plan lookups to replace env-based price maps.
Single source of truth: plans table with stripe_price_id.
"""

from typing import Optional
from ..db import fetchone_dict


def get_plan_by_slug(cur, plan_slug: str) -> Optional[dict]:
    """
    Get plan details from database by plan_slug.
    
    Args:
        cur: Database cursor
        plan_slug: Plan identifier (e.g., 'solo', 'affiliate', 'free')
    
    Returns:
        Plan dict with keys: plan_slug, plan_name, stripe_price_id, etc.
        None if not found or inactive.
    """
    cur.execute("""
        SELECT 
            plan_slug,
            plan_name,
            monthly_report_limit,
            allow_overage,
            overage_price_cents,
            stripe_price_id,
            description,
            is_active
        FROM plans
        WHERE plan_slug = %s AND is_active = true
    """, (plan_slug,))
    
    return fetchone_dict(cur)


def get_plan_slug_for_stripe_price(cur, price_id: str) -> Optional[str]:
    """
    Map Stripe Price ID back to plan_slug.
    
    Used by webhooks to determine which plan a subscription corresponds to.
    
    Args:
        cur: Database cursor
        price_id: Stripe Price ID (e.g., 'price_...')
    
    Returns:
        plan_slug or None if price_id not found in any active plan
    """
    cur.execute("""
        SELECT plan_slug
        FROM plans
        WHERE stripe_price_id = %s AND is_active = true
    """, (price_id,))
    
    row = cur.fetchone()
    return row[0] if row else None

