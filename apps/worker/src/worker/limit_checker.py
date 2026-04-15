"""
Usage Limit Checker for Worker

Per-product limit enforcement: check market_reports or property_reports limits
before generating scheduled or queued reports.
"""

import os
import psycopg
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_reports")


def _first_not_none(*values, default):
    """Return the first value that is not None, or default.

    Explicit None check so that override = 0 (freeze account) is honoured
    instead of being skipped by a falsy `or` chain.
    """
    for v in values:
        if v is not None:
            return v
    return default


def check_usage_limit(account_id: str, product: str = "market_reports") -> Dict[str, Any]:
    """
    Check if an account can generate a report of the given product type.

    Args:
        account_id: Account UUID string
        product: "market_reports" | "property_reports"

    Returns:
        dict with keys: can_proceed, used, limit, plan_slug, reason
    """
    with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            # Fetch per-product plan limits and account-level overrides
            cur.execute("""
                SELECT
                    p.market_reports_limit,
                    p.schedules_limit,
                    p.property_reports_per_month,
                    a.market_reports_limit_override,
                    a.schedules_limit_override,
                    a.property_reports_limit_override,
                    a.monthly_report_limit_override,
                    p.plan_slug
                FROM accounts a
                LEFT JOIN plans p ON p.plan_slug = a.plan_slug
                WHERE a.id = %s::uuid
            """, (account_id,))
            row = cur.fetchone()

            if not row:
                logger.warning(f"[limit_checker] account {account_id} not found")
                return {"can_proceed": False, "reason": "account_not_found"}

            (mkt_plan_limit, sched_plan_limit, prop_plan_limit,
             mkt_override, sched_override, prop_override,
             legacy_override, plan_slug) = row

            # Resolve effective limit for the requested product.
            # Use _first_not_none so that override = 0 (freeze account) is honoured.
            # Priority: per-product override → legacy single override → plan default → hard floor
            if product == "market_reports":
                effective_limit = _first_not_none(mkt_override, legacy_override, mkt_plan_limit, default=3)
                cur.execute("""
                    SELECT COUNT(*) FROM report_generations
                    WHERE account_id = %s::uuid
                      AND generated_at >= date_trunc('month', NOW())
                      AND status IN ('completed', 'processing')
                """, (account_id,))

            elif product == "property_reports":
                effective_limit = _first_not_none(prop_override, prop_plan_limit, default=1)
                cur.execute("""
                    SELECT COUNT(*) FROM property_reports
                    WHERE account_id = %s::uuid
                      AND created_at >= date_trunc('month', NOW())
                      AND status IN ('complete', 'generating')
                """, (account_id,))

            else:
                logger.warning(f"[limit_checker] unknown product '{product}' — allowing by default")
                return {"can_proceed": True, "reason": "unknown_product"}

            used = cur.fetchone()[0]

    # Unlimited check
    if effective_limit >= 99999:
        return {
            "can_proceed": True,
            "used": used,
            "limit": effective_limit,
            "plan_slug": plan_slug,
            "reason": "ok",
        }

    ratio = used / max(effective_limit, 1)
    can_proceed = ratio < 1.1  # allow up to 110% (matches API evaluate_product_limit)

    return {
        "can_proceed": can_proceed,
        "used": used,
        "limit": effective_limit,
        "plan_slug": plan_slug or "free",
        "reason": "limit_reached" if not can_proceed else "ok",
    }


def log_limit_decision_worker(account_id: str, limit_result: Dict[str, Any]):
    """Log usage limit decision for worker monitoring."""
    logger.info(
        f"[usage] account={account_id} "
        f"plan={limit_result.get('plan_slug', 'unknown')} "
        f"used={limit_result.get('used', 0)} "
        f"limit={limit_result.get('limit', 0)} "
        f"can_proceed={limit_result.get('can_proceed')} "
        f"reason={limit_result.get('reason', 'ok')}"
    )
