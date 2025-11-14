"""
Phase 29D: Stripe Billing Configuration

Maps internal plan_slug values to Stripe Price IDs.
Allows toggling plan_slug based on Stripe subscription events.
"""

import os
from typing import Optional

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Map plan_slug → Stripe Price ID
# These env vars should be set on Render with your actual Stripe Price IDs
STRIPE_PRICE_MAP = {
    "pro": os.getenv("STRIPE_PRICE_PRO_MONTH"),
    "team": os.getenv("STRIPE_PRICE_TEAM_MONTH"),
    # Note: 'free', 'sponsored_free', and 'affiliate' are not Stripe products
    # They are managed internally without payment
}

# Reverse map: Stripe Price ID → plan_slug
# Built automatically from STRIPE_PRICE_MAP
STRIPE_PRICE_REVERSE_MAP = {
    price_id: plan_slug
    for plan_slug, price_id in STRIPE_PRICE_MAP.items()
    if price_id is not None
}


def get_stripe_price_for_plan(plan_slug: str) -> Optional[str]:
    """
    Get Stripe Price ID for a given plan_slug.
    
    Args:
        plan_slug: One of 'pro', 'team', etc.
    
    Returns:
        Stripe Price ID (e.g., 'price_...') or None if not configured
    """
    return STRIPE_PRICE_MAP.get(plan_slug)


def get_plan_for_stripe_price(price_id: str) -> Optional[str]:
    """
    Get plan_slug from Stripe Price ID.
    
    Used by webhooks to map Stripe subscription updates back to our plans.
    
    Args:
        price_id: Stripe Price ID (e.g., 'price_...')
    
    Returns:
        plan_slug (e.g., 'pro', 'team') or None if not recognized
    """
    return STRIPE_PRICE_REVERSE_MAP.get(price_id)


def validate_stripe_config() -> tuple[bool, list[str]]:
    """
    Validate that required Stripe configuration is present.
    
    Returns:
        (is_valid, list_of_missing_vars)
    """
    missing = []
    
    if not STRIPE_SECRET_KEY:
        missing.append("STRIPE_SECRET_KEY")
    
    if not STRIPE_WEBHOOK_SECRET:
        missing.append("STRIPE_WEBHOOK_SECRET")
    
    if not STRIPE_PRICE_MAP.get("pro"):
        missing.append("STRIPE_PRICE_PRO_MONTH")
    
    if not STRIPE_PRICE_MAP.get("team"):
        missing.append("STRIPE_PRICE_TEAM_MONTH")
    
    return (len(missing) == 0, missing)


# Stripe SDK initialization
try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
except ImportError:
    stripe = None
    print("⚠️  Warning: 'stripe' package not installed. Run: pip install stripe")



