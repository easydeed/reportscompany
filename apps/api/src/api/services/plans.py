"""
Plan Catalog Service - PASS 3

Provides a single source of truth for plan information by reading from the plans table
and enriching with real-time Stripe pricing data.

✅ PASS 3 COMPLETE: This service already exists and is used by /v1/account/plan-usage
to return stripe_billing info (amount, currency, interval, nickname) from Stripe API.

Usage:
    catalog = get_plan_catalog(cur)
    pro_plan = catalog.get('pro')
    if pro_plan:
        amount = pro_plan.stripe_billing.amount  # cents
        price_display = f"${amount / 100:.2f}/{pro_plan.stripe_billing.interval}"
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
import stripe
import os

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class StripeBilling(BaseModel):
    """Stripe billing information for a plan."""
    amount: int  # Price in cents
    currency: str  # e.g., 'usd'
    interval: str  # 'month', 'year'
    interval_count: int  # Usually 1
    nickname: Optional[str] = None  # e.g., 'Pro – $29/mo'


class PlanCatalog(BaseModel):
    """Plan catalog entry with optional Stripe billing."""
    plan_slug: str
    plan_name: str
    stripe_price_id: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    stripe_billing: Optional[StripeBilling] = None


def get_plan_catalog(cur) -> Dict[str, PlanCatalog]:
    """
    Returns a dict keyed by plan_slug with enriched plan information.
    
    Each entry is a PlanCatalog object that includes:
    - plan_slug: Internal identifier (e.g., 'pro')
    - plan_name: Display name (e.g., 'Pro')
    - stripe_price_id: Stripe Price ID (e.g., 'price_...')
    - description: Plan description
    - is_active: Whether plan is available
    - stripe_billing: StripeBilling object with amount, currency, interval, etc.
    
    For free plans or plans without Stripe prices, stripe_billing will be None.
    The function is resilient: if Stripe API fails, returns plan info without pricing.
    """
    # Try new column names first, fall back to old names for backwards compatibility
    try:
        cur.execute("""
            SELECT plan_slug, plan_name, stripe_price_id, description, is_active
            FROM plans
            WHERE is_active = TRUE
            ORDER BY plan_slug
        """)
    except Exception:
        # Fall back to old column names
        cur.execute("""
            SELECT slug AS plan_slug, name AS plan_name, stripe_price_id, description, TRUE AS is_active
            FROM plans
            ORDER BY slug
        """)
    
    rows = cur.fetchall()
    
    catalog: Dict[str, PlanCatalog] = {}
    
    for row in rows:
        plan_slug = row[0]
        plan_name = row[1]
        stripe_price_id = row[2]
        description = row[3]
        is_active = row[4] if len(row) > 4 else True
        
        stripe_billing = None
        
        # Fetch Stripe pricing if price_id exists
        if stripe_price_id and stripe.api_key:
            try:
                price = stripe.Price.retrieve(stripe_price_id)
                recurring = price.get("recurring")
                
                if recurring and price.get("unit_amount"):
                    stripe_billing = StripeBilling(
                        amount=price["unit_amount"],
                        currency=price["currency"],
                        interval=recurring["interval"],
                        interval_count=recurring.get("interval_count", 1),
                        nickname=price.get("nickname")
                    )
            except stripe.error.StripeError as e:
                # Log but don't crash - app continues with plan_name only
                print(f"Warning: Failed to fetch Stripe price for {plan_slug} ({stripe_price_id}): {e}")
            except Exception as e:
                print(f"Warning: Unexpected error fetching Stripe price for {plan_slug}: {e}")
        
        catalog[plan_slug] = PlanCatalog(
            plan_slug=plan_slug,
            plan_name=plan_name,
            stripe_price_id=stripe_price_id,
            description=description,
            is_active=is_active,
            stripe_billing=stripe_billing
        )
    
    return catalog


def get_plan_info(cur, plan_slug: str) -> Optional[PlanCatalog]:
    """
    Convenience function to get a single plan's info.
    Returns None if plan doesn't exist.
    """
    catalog = get_plan_catalog(cur)
    return catalog.get(plan_slug)

