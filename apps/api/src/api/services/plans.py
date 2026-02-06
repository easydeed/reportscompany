"""
Plan Catalog Service — with caching.

BEFORE: Every call fetched all plans from DB, then called stripe.Price.retrieve()
        per plan (4 HTTP roundtrips = 800-2000ms).
AFTER:  Cached in memory for 1 hour. First call pays the cost, subsequent = ~0ms.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
import stripe
import os
import time
import logging

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class StripeBilling(BaseModel):
    amount: int
    currency: str
    interval: str
    interval_count: int
    nickname: Optional[str] = None


class PlanCatalog(BaseModel):
    plan_slug: str
    plan_name: str
    stripe_price_id: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    stripe_billing: Optional[StripeBilling] = None


# ── In-Memory Cache ──────────────────────────────────────────────────────

_plan_cache: Dict[str, PlanCatalog] | None = None
_plan_cache_time: float = 0
_CACHE_TTL_SECONDS = 3600  # 1 hour


def invalidate_plan_cache():
    """
    Call this when plans change. Hook into:
    - Stripe webhook handler (price.updated, product.updated)
    - Admin plan management endpoints
    """
    global _plan_cache, _plan_cache_time
    _plan_cache = None
    _plan_cache_time = 0
    logger.info("Plan cache invalidated")


def get_plan_catalog(cur) -> Dict[str, PlanCatalog]:
    """
    Returns plan catalog, cached in memory for 1 hour.
    
    First call:  DB query + Stripe API × N plans (~1-2 seconds)
    Cached call: Returns dict from memory (~0ms)
    """
    global _plan_cache, _plan_cache_time

    now = time.time()
    if _plan_cache is not None and (now - _plan_cache_time) < _CACHE_TTL_SECONDS:
        return _plan_cache

    # ── Cache miss: fetch from DB + Stripe ───────────────────────────
    try:
        cur.execute("""
            SELECT plan_slug, plan_name, stripe_price_id, description, is_active
            FROM plans WHERE is_active = TRUE ORDER BY plan_slug
        """)
    except Exception as e:
        logger.warning(f"Plans query failed with new columns, trying legacy: {e}")
        cur.execute("""
            SELECT slug AS plan_slug, name AS plan_name, stripe_price_id,
                   description, TRUE AS is_active
            FROM plans ORDER BY slug
        """)

    rows = cur.fetchall()
    catalog: Dict[str, PlanCatalog] = {}

    for row in rows:
        plan_slug, plan_name, stripe_price_id = row[0], row[1], row[2]
        description = row[3]
        is_active = row[4] if len(row) > 4 else True

        stripe_billing = None
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
                        nickname=price.get("nickname"),
                    )
            except Exception as e:
                logger.warning(f"Stripe price fetch failed for {plan_slug}: {e}")

        catalog[plan_slug] = PlanCatalog(
            plan_slug=plan_slug,
            plan_name=plan_name,
            stripe_price_id=stripe_price_id,
            description=description,
            is_active=is_active,
            stripe_billing=stripe_billing,
        )

    _plan_cache = catalog
    _plan_cache_time = now
    logger.info(f"Plan catalog cached ({len(catalog)} plans)")
    return catalog


def get_plan_info(cur, plan_slug: str) -> Optional[PlanCatalog]:
    """Get a single plan. Uses cached catalog so no extra Stripe calls."""
    catalog = get_plan_catalog(cur)
    return catalog.get(plan_slug)
