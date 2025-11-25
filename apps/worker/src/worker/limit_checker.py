"""
Usage Limit Checker for Worker

Phase 29B: Check usage limits before generating scheduled reports.
Imports the same logic from API services for consistency.
"""

import psycopg
from enum import Enum
from datetime import datetime, date
import calendar
from typing import Dict, Any, Tuple


class LimitDecision(str, Enum):
    """Decision about whether to allow report generation"""
    ALLOW = "ALLOW"
    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    BLOCK = "BLOCK"


def check_usage_limit(cur, account_id: str) -> Tuple[str, Dict[str, Any]]:
    """
    Check if account can generate another report (worker-side wrapper).
    
    Returns same logic as API services.evaluate_report_limit but worker-friendly.
    
    Args:
        cur: Database cursor
        account_id: Account UUID string
    
    Returns:
        (decision_str, info_dict)
        decision_str: 'ALLOW', 'ALLOW_WITH_WARNING', or 'BLOCK'
        info_dict: usage, plan, ratio, message, etc.
    """
    # Get current month boundaries
    now = datetime.utcnow()
    year = now.year
    month = now.month
    period_start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    period_end = date(year, month, last_day)
    
    # Count reports this month
    cur.execute("""
        SELECT COUNT(*) as report_count
        FROM report_generations
        WHERE account_id = %s::uuid
          AND generated_at >= %s::date
          AND generated_at < (%s::date + INTERVAL '1 day')
          AND status IN ('completed', 'processing')
    """, (account_id, period_start, period_end))
    
    report_count = cur.fetchone()[0] or 0
    
    # Get plan info
    cur.execute("""
        SELECT 
            a.plan_slug,
            a.monthly_report_limit_override,
            a.account_type,
            p.name as plan_name,
            p.monthly_report_limit as plan_limit,
            p.allow_overage,
            p.overage_price_cents
        FROM accounts a
        LEFT JOIN plans p ON a.plan_slug = p.plan_slug
        WHERE a.id = %s::uuid
    """, (account_id,))
    
    plan_row = cur.fetchone()
    if not plan_row:
        # Account not found - allow (shouldn't happen)
        return ("ALLOW", {})
    
    plan_slug, limit_override, account_type, plan_name, plan_limit, allow_overage, overage_price_cents = plan_row
    
    # Resolve effective limit
    effective_limit = limit_override if limit_override is not None else (plan_limit or 100)
    
    # Handle unlimited
    if effective_limit <= 0 or effective_limit >= 10000:
        return ("ALLOW", {
            "usage": {"report_count": report_count},
            "plan": {"plan_slug": plan_slug, "monthly_report_limit": effective_limit},
            "message": "Unlimited plan",
        })
    
    # Calculate ratio
    ratio = report_count / effective_limit if effective_limit > 0 else 0.0
    
    # Decision logic
    if ratio < 0.8:
        decision = "ALLOW"
        message = f"Usage: {report_count}/{effective_limit} reports ({int(ratio * 100)}%)"
        
    elif ratio < 1.1:
        decision = "ALLOW_WITH_WARNING"
        if ratio >= 1.0:
            if allow_overage:
                overage_count = report_count - effective_limit
                message = f"⚠️ Over limit by {overage_count} reports. Overage billing applies."
            else:
                message = f"⚠️ At {int(ratio * 100)}% of monthly limit ({report_count}/{effective_limit})."
        else:
            message = f"⚠️ Approaching limit: {report_count}/{effective_limit} reports"
            
    else:
        # Over 110%
        if allow_overage:
            decision = "ALLOW_WITH_WARNING"
            overage_count = report_count - effective_limit
            message = f"⚠️ Significantly over limit ({report_count}/{effective_limit}). Overage charges apply."
        else:
            decision = "BLOCK"
            message = f"🚫 Monthly report limit reached ({report_count}/{effective_limit})."
    
    info = {
        "usage": {
            "report_count": report_count,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        },
        "plan": {
            "plan_slug": plan_slug or 'free',
            "plan_name": plan_name or 'Free',
            "monthly_report_limit": effective_limit,
            "allow_overage": allow_overage or False,
        },
        "ratio": ratio,
        "message": message,
    }
    
    return (decision, info)


def log_limit_decision_worker(account_id: str, decision: str, info: Dict[str, Any]):
    """Log limit decision for worker (same format as API)"""
    plan = info.get("plan", {})
    usage = info.get("usage", {})
    
    print(
        f"[usage] account={account_id} "
        f"plan={plan.get('plan_slug', 'unknown')} "
        f"decision={decision} "
        f"usage={usage.get('report_count', 0)} "
        f"limit={plan.get('monthly_report_limit', 0)} "
        f"ratio={info.get('ratio', 0):.2f}"
    )

