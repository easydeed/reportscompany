"""
Usage Tracking & Plan Limit Enforcement

Phase 29B: Calculate monthly usage and enforce plan limits
Performance fix: Correlated subquery replaced with JOIN (M1)
"""

from datetime import datetime, date
from typing import Dict, Any, Tuple
from enum import Enum
import calendar
import logging

logger = logging.getLogger(__name__)


class LimitDecision(str, Enum):
    """Decision about whether to allow report generation"""
    ALLOW = "ALLOW"
    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    BLOCK = "BLOCK"


def get_monthly_usage(cur, account_id: str, now: datetime | None = None) -> Dict[str, Any]:
    """
    Get usage statistics for the current calendar month.
    
    Args:
        cur: Database cursor
        account_id: Account UUID
        now: Override current time (for testing)
    
    Returns:
        {
            "report_count": int,
            "schedule_run_count": int,
            "period_start": str (ISO date),
            "period_end": str (ISO date)
        }
    """
    if now is None:
        now = datetime.utcnow()
    
    # Current calendar month boundaries
    year = now.year
    month = now.month
    period_start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    period_end = date(year, month, last_day)
    
    # Count report_generations for this month
    cur.execute("""
        SELECT COUNT(*) as report_count
        FROM report_generations
        WHERE account_id = %s
          AND generated_at >= %s::date
          AND generated_at < (%s::date + INTERVAL '1 day')
          AND status IN ('completed', 'processing')
    """, (account_id, period_start, period_end))
    
    report_row = cur.fetchone()
    report_count = report_row[0] if report_row else 0
    
    # FIX (M1): Count schedule_runs using JOIN instead of correlated subquery
    schedule_run_count = 0
    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM schedule_runs sr
            JOIN schedules s ON sr.schedule_id = s.id
            WHERE s.account_id = %s
              AND sr.created_at >= %s::date
              AND sr.created_at < (%s::date + INTERVAL '1 day')
              AND sr.status IN ('completed', 'processing')
        """, (account_id, period_start, period_end))
        
        schedule_row = cur.fetchone()
        schedule_run_count = schedule_row[0] if schedule_row else 0
    except Exception as e:
        # schedule_runs table might not exist yet
        logger.warning(f"schedule_runs query failed (table may not exist): {e}")
    
    return {
        "report_count": report_count,
        "schedule_run_count": schedule_run_count,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }


def resolve_plan_for_account(cur, account_id: str) -> Dict[str, Any]:
    """
    Resolve the effective plan for an account, including any overrides.
    
    Args:
        cur: Database cursor
        account_id: Account UUID
    
    Returns:
        {
            "plan_slug": str,
            "plan_name": str,
            "monthly_report_limit": int,
            "allow_overage": bool,
            "overage_price_cents": int,
            "has_override": bool
        }
    """
    # Get account info
    cur.execute("""
        SELECT 
            a.plan_slug,
            a.monthly_report_limit_override,
            a.account_type,
            p.plan_name,
            p.monthly_report_limit as plan_limit,
            p.allow_overage,
            p.overage_price_cents
        FROM accounts a
        LEFT JOIN plans p ON a.plan_slug = p.plan_slug
        WHERE a.id = %s
    """, (account_id,))
    
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Account {account_id} not found")
    
    (plan_slug, limit_override, account_type, 
     plan_name, plan_limit, allow_overage, overage_price_cents) = row
    
    # If no plan assigned, default to free
    if not plan_slug:
        plan_slug = 'free'
        cur.execute("""
            SELECT name, monthly_report_limit, allow_overage, overage_price_cents
            FROM plans WHERE slug = 'free'
        """)
        free_row = cur.fetchone()
        if free_row:
            plan_name, plan_limit, allow_overage, overage_price_cents = free_row
    
    # Apply override if present
    effective_limit = limit_override if limit_override is not None else (plan_limit or 100)
    has_override = limit_override is not None
    
    return {
        "plan_slug": plan_slug or 'free',
        "plan_name": plan_name or 'Free',
        "monthly_report_limit": effective_limit,
        "allow_overage": allow_overage or False,
        "overage_price_cents": overage_price_cents or 0,
        "has_override": has_override,
        "account_type": account_type or 'REGULAR',
    }


def evaluate_report_limit(cur, account_id: str, now: datetime | None = None) -> Tuple[LimitDecision, Dict[str, Any]]:
    """
    Central function to evaluate whether an account can generate another report.
    
    Logic:
    - Unlimited (limit <= 0): ALLOW
    - Under 80%: ALLOW
    - 80-110%: ALLOW_WITH_WARNING
    - Over 110% and no overage allowed: BLOCK
    - Over 110% with overage allowed: ALLOW_WITH_WARNING (will bill)
    
    Args:
        cur: Database cursor
        account_id: Account UUID
        now: Override current time (for testing)
    
    Returns:
        (decision, info_dict)
        
        info_dict contains:
        {
            "usage": {...},
            "plan": {...},
            "ratio": float,
            "message": str,
            "can_proceed": bool
        }
    """
    usage = get_monthly_usage(cur, account_id, now)
    plan = resolve_plan_for_account(cur, account_id)
    
    limit = plan["monthly_report_limit"]
    count = usage["report_count"]
    
    # Handle unlimited plans (limit <= 0 or very high)
    if limit <= 0 or limit >= 10000:
        return LimitDecision.ALLOW, {
            "usage": usage,
            "plan": plan,
            "ratio": 0.0,
            "message": "Unlimited plan - no restrictions",
            "can_proceed": True,
        }
    
    # Calculate usage ratio
    ratio = count / limit if limit > 0 else 0.0
    
    # Decision logic
    if ratio < 0.8:
        # Under 80%: green light
        decision = LimitDecision.ALLOW
        message = f"Usage: {count}/{limit} reports ({int(ratio * 100)}%)"
        can_proceed = True
        
    elif ratio < 1.1:
        # 80-110%: warn but allow
        decision = LimitDecision.ALLOW_WITH_WARNING
        if ratio >= 1.0:
            if plan["allow_overage"]:
                overage_count = count - limit
                message = f"⚠️ Over limit by {overage_count} reports. Overage billing applies (${plan['overage_price_cents'] / 100:.2f}/report)."
            else:
                message = f"⚠️ At {int(ratio * 100)}% of monthly limit ({count}/{limit}). Consider upgrading your plan."
        else:
            message = f"⚠️ Approaching limit: {count}/{limit} reports ({int(ratio * 100)}%)"
        can_proceed = True
        
    else:
        # Over 110%
        if plan["allow_overage"]:
            # Allow with billing
            decision = LimitDecision.ALLOW_WITH_WARNING
            overage_count = count - limit
            message = f"⚠️ Significantly over limit ({count}/{limit}). Overage charges: ${overage_count * plan['overage_price_cents'] / 100:.2f}"
            can_proceed = True
        else:
            # Block
            decision = LimitDecision.BLOCK
            message = f"🚫 Monthly report limit reached ({count}/{limit}). Upgrade your plan to generate more reports."
            can_proceed = False
    
    return decision, {
        "usage": usage,
        "plan": plan,
        "ratio": ratio,
        "message": message,
        "can_proceed": can_proceed,
        "overage_count": max(0, count - limit) if limit > 0 else 0,
    }


def log_limit_decision(account_id: str, decision: LimitDecision, info: Dict[str, Any]):
    """
    Log usage limit decision for monitoring and debugging.
    """
    plan = info.get("plan", {})
    usage = info.get("usage", {})
    
    logger.info(
        f"[usage] account={account_id} "
        f"plan={plan.get('plan_slug', 'unknown')} "
        f"decision={decision.value} "
        f"usage={usage.get('report_count', 0)} "
        f"limit={plan.get('monthly_report_limit', 0)} "
        f"ratio={info.get('ratio', 0):.2f}"
    )
