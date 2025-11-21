"""
Plan Catalog Service

Provides a single source of truth for plan information by reading from the plans table
and enriching with real-time Stripe pricing data.

Usage:
    catalog = get_plan_catalog(cur)
    pro_plan = catalog.get('pro')
    if pro_plan:
        amount = pro_plan['amount']  # cents
        price_display = f"${amount / 100:.2f}/{pro_plan['interval']}"
"""

from typing import Dict, Any, Optional
import stripe
import os

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def get_plan_catalog(cur) -> Dict[str, Dict[str, Any]]:
    """
    Returns a dict keyed by plan_slug with enriched plan information.
    
    Each entry includes:
    - plan_slug: Internal identifier (e.g., 'pro')
    - plan_name: Display name (e.g., 'Pro')
    - stripe_price_id: Stripe Price ID (e.g., 'price_...')
    - amount: Price in cents (e.g., 2900)
    - currency: Currency code (e.g., 'usd')
    - interval: Billing interval (e.g., 'month')
    - interval_count: Number of intervals (e.g., 1)
    - nickname: Stripe price nickname (e.g., 'Pro – $29/mo')
    
    For free plans or plans without Stripe prices, amount/currency/interval will be None.
    The function is resilient: if Stripe API fails, returns plan info without pricing.
    """
    cur.execute("""
        SELECT plan_slug, plan_name, stripe_price_id, description
        FROM plans
        ORDER BY plan_slug
    """)
    rows = cur.fetchall()
    
    catalog: Dict[str, Dict[str, Any]] = {}
    
    for row in rows:
        slug = row[0]
        entry: Dict[str, Any] = {
            "plan_slug": slug,
            "plan_name": row[1],
            "stripe_price_id": row[2],
            "description": row[3],
            "amount": None,
            "currency": None,
            "interval": None,
            "interval_count": None,
            "nickname": None,
        }
        
        price_id = row[2]
        if price_id and stripe.api_key:
            try:
                price = stripe.Price.retrieve(price_id)
                entry["amount"] = price.get("unit_amount")
                entry["currency"] = price.get("currency")
                
                recurring = price.get("recurring")
                if recurring:
                    entry["interval"] = recurring.get("interval")
                    entry["interval_count"] = recurring.get("interval_count")
                
                entry["nickname"] = price.get("nickname")
            except stripe.error.StripeError as e:
                # Log but don't crash - app continues with plan_name only
                print(f"Warning: Failed to fetch Stripe price for {slug} ({price_id}): {e}")
            except Exception as e:
                print(f"Warning: Unexpected error fetching Stripe price for {slug}: {e}")
        
        catalog[slug] = entry
    
    return catalog


def get_plan_info(cur, plan_slug: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get a single plan's info.
    Returns None if plan doesn't exist.
    """
    catalog = get_plan_catalog(cur)
    return catalog.get(plan_slug)

