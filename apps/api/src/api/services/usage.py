"""
Usage Tracking & Plan Limit Enforcement

Per-product limit model:
  - market_reports   → report_generations table
  - schedules        → schedules table (active count)
  - property_reports → property_reports table
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


# ─── DISPLAY NAMES ────────────────────────────────────────────────────────────

_PLAN_DISPLAY_NAMES = {
    "free": "Free",
    "sponsored_free": "Trial",
    "trial": "Trial",
    "starter": "Starter",
    "solo": "Starter",
    "pro": "Pro",
    "team": "Pro",
    "affiliate": "Affiliate",
}


# ─── CORE: RESOLVE PLAN ───────────────────────────────────────────────────────

def resolve_plan_for_account(cur, account_id: str) -> Dict[str, Any]:
    """
    Resolve effective limits for all three product types.

    Handles deferred downgrades inline.  Returns both the new per-product
    limit keys AND the legacy ``monthly_report_limit`` key for backward
    compatibility.
    """
    cur.execute("""
        SELECT
            a.plan_slug,
            a.monthly_report_limit_override,
            a.account_type,
            p.plan_name,
            p.monthly_report_limit          AS plan_limit,
            p.allow_overage,
            p.overage_price_cents,
            a.plan_downgrade_at,
            a.plan_downgrade_to,
            p.market_reports_limit,
            p.schedules_limit,
            p.property_reports_per_month,
            a.market_reports_limit_override,
            a.schedules_limit_override,
            a.property_reports_limit_override
        FROM accounts a
        LEFT JOIN plans p ON a.plan_slug = p.plan_slug
        WHERE a.id = %s::uuid
    """, (account_id,))

    row = cur.fetchone()
    if not row:
        raise ValueError(f"Account {account_id} not found")

    (plan_slug, limit_override, account_type,
     plan_name, plan_limit, allow_overage, overage_price_cents,
     downgrade_at, downgrade_to,
     mkt_plan_limit, sched_plan_limit, prop_plan_limit,
     mkt_override, sched_override, prop_override) = row

    # ── Deferred downgrade ────────────────────────────────────────────────────
    if downgrade_at and downgrade_to:
        now = datetime.utcnow()
        downgrade_dt = downgrade_at.replace(tzinfo=None) if downgrade_at.tzinfo else downgrade_at
        if now >= downgrade_dt:
            logger.info(
                f"Executing deferred downgrade for account {account_id}: "
                f"{plan_slug} -> {downgrade_to}"
            )
            cur.execute("""
                UPDATE accounts
                SET plan_slug         = %s,
                    plan_downgrade_at  = NULL,
                    plan_downgrade_to  = NULL,
                    billing_status     = 'canceled'
                WHERE id = %s
            """, (downgrade_to, account_id))
            plan_slug = downgrade_to
            cur.execute("""
                SELECT plan_name, monthly_report_limit, allow_overage, overage_price_cents,
                       market_reports_limit, schedules_limit, property_reports_per_month
                FROM plans WHERE plan_slug = %s
            """, (plan_slug,))
            new_plan = cur.fetchone()
            if new_plan:
                plan_name, plan_limit, allow_overage, overage_price_cents = new_plan[:4]
                mkt_plan_limit, sched_plan_limit, prop_plan_limit = new_plan[4:]

    # ── Default if no plan assigned ───────────────────────────────────────────
    if not plan_slug:
        plan_slug = "free"

    # ── Effective limits ──────────────────────────────────────────────────────
    # Per-product override → legacy single override → plan default → hard floor
    market_limit    = mkt_override  or limit_override or mkt_plan_limit  or 3
    schedules_limit = sched_override or sched_plan_limit or 1
    property_limit  = prop_override  or prop_plan_limit  or 1

    # Legacy single limit (backward compat for evaluate_report_limit)
    effective_limit = limit_override if limit_override is not None else (plan_limit or 100)
    has_override    = limit_override is not None

    display_name = _PLAN_DISPLAY_NAMES.get(plan_slug, plan_name) or "Free"

    return {
        # ── legacy keys ──────────────────────────────────────────────────────
        "plan_slug":             plan_slug or "free",
        "plan_name":             display_name,
        "monthly_report_limit":  effective_limit,
        "allow_overage":         allow_overage or False,
        "overage_price_cents":   overage_price_cents or 0,
        "has_override":          has_override,
        "account_type":          account_type or "REGULAR",
        # ── per-product limits ───────────────────────────────────────────────
        "market_reports_limit":  market_limit,
        "schedules_limit":       schedules_limit,
        "property_reports_limit": property_limit,
    }


# ─── USAGE COUNTS ─────────────────────────────────────────────────────────────

def get_usage_counts(cur, account_id: str) -> Dict[str, Any]:
    """Count usage for all three product types."""
    # Market reports this month
    cur.execute("""
        SELECT COUNT(*) FROM report_generations
        WHERE account_id = %s::uuid
          AND generated_at >= date_trunc('month', NOW())
          AND status IN ('completed', 'processing')
    """, (account_id,))
    market_used = cur.fetchone()[0]

    # Active schedules
    cur.execute("""
        SELECT COUNT(*) FROM schedules
        WHERE account_id = %s::uuid AND active = TRUE
    """, (account_id,))
    schedules_active = cur.fetchone()[0]

    # Property reports this month
    property_used = 0
    try:
        cur.execute("""
            SELECT COUNT(*) FROM property_reports
            WHERE account_id = %s::uuid
              AND created_at >= date_trunc('month', NOW())
              AND status IN ('complete', 'generating')
        """, (account_id,))
        property_used = cur.fetchone()[0]
    except Exception as e:
        logger.warning(f"property_reports count failed (table may not exist): {e}")

    return {
        "market_reports_used":  market_used,
        "schedules_active":     schedules_active,
        "property_reports_used": property_used,
    }


# ─── SINGLE-PRODUCT EVALUATOR ─────────────────────────────────────────────────

def evaluate_product_limit(used: int, limit: int) -> Dict[str, Any]:
    """Evaluate a single product's limit status."""
    if limit >= 99999:
        return {"used": used, "limit": limit, "status": "ok", "can_proceed": True}

    ratio = used / max(limit, 1)
    if ratio < 0.8:
        status = "ok"
    elif ratio < 1.0:
        status = "warning"
    elif ratio < 1.1:
        status = "at_limit"
    else:
        status = "exceeded"

    return {
        "used":        used,
        "limit":       limit,
        "status":      status,
        "can_proceed": status != "exceeded",
    }


# ─── FULL PLAN USAGE ──────────────────────────────────────────────────────────

def get_full_plan_usage(cur, account_id: str) -> Dict[str, Any]:
    """Complete three-product plan usage response for the frontend."""
    plan  = resolve_plan_for_account(cur, account_id)
    usage = get_usage_counts(cur, account_id)

    return {
        "plan": {
            "plan_slug":              plan["plan_slug"],
            "plan_name":              plan["plan_name"],
            "market_reports_limit":   plan["market_reports_limit"],
            "schedules_limit":        plan["schedules_limit"],
            "property_reports_limit": plan["property_reports_limit"],
        },
        "usage": usage,
        "limits": {
            "market_reports": evaluate_product_limit(
                usage["market_reports_used"],   plan["market_reports_limit"]),
            "schedules": evaluate_product_limit(
                usage["schedules_active"],      plan["schedules_limit"]),
            "property_reports": evaluate_product_limit(
                usage["property_reports_used"], plan["property_reports_limit"]),
        },
    }


# ─── LEGACY: get_monthly_usage ────────────────────────────────────────────────

def get_monthly_usage(cur, account_id: str, now: datetime | None = None) -> Dict[str, Any]:
    """
    Get usage statistics for the current calendar month.
    Kept for backward compatibility — new code should call get_usage_counts().
    """
    if now is None:
        now = datetime.utcnow()

    year  = now.year
    month = now.month
    period_start = date(year, month, 1)
    _, last_day  = calendar.monthrange(year, month)
    period_end   = date(year, month, last_day)

    cur.execute("""
        SELECT COUNT(*) FROM report_generations
        WHERE account_id = %s
          AND generated_at >= %s::date
          AND generated_at < (%s::date + INTERVAL '1 day')
          AND status IN ('completed', 'processing')
    """, (account_id, period_start, period_end))
    report_count = (cur.fetchone() or [0])[0]

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
        schedule_run_count = (cur.fetchone() or [0])[0]
    except Exception as e:
        logger.warning(f"schedule_runs query failed (table may not exist): {e}")

    return {
        "report_count":       report_count,
        "schedule_run_count": schedule_run_count,
        "period_start":       period_start.isoformat(),
        "period_end":         period_end.isoformat(),
    }


# ─── LEGACY: evaluate_report_limit ────────────────────────────────────────────

def evaluate_report_limit(
    cur, account_id: str, now: datetime | None = None
) -> Tuple[LimitDecision, Dict[str, Any]]:
    """
    Evaluate whether an account can generate another market report.
    Kept for backward compatibility — routes should migrate to get_full_plan_usage().
    """
    usage = get_monthly_usage(cur, account_id, now)
    plan  = resolve_plan_for_account(cur, account_id)

    limit = plan["monthly_report_limit"]
    count = usage["report_count"]

    if limit <= 0 or limit >= 10000:
        return LimitDecision.ALLOW, {
            "usage": usage, "plan": plan,
            "ratio": 0.0,
            "message": "Unlimited plan - no restrictions",
            "can_proceed": True,
        }

    ratio = count / limit if limit > 0 else 0.0

    if ratio < 0.8:
        decision     = LimitDecision.ALLOW
        message      = f"Usage: {count}/{limit} reports ({int(ratio * 100)}%)"
        can_proceed  = True
    elif ratio < 1.1:
        decision    = LimitDecision.ALLOW_WITH_WARNING
        can_proceed = True
        if ratio >= 1.0:
            if plan["allow_overage"]:
                overage = count - limit
                message = (
                    f"\u26a0\ufe0f Over limit by {overage} reports. "
                    f"Overage billing applies (${plan['overage_price_cents'] / 100:.2f}/report)."
                )
            else:
                message = (
                    f"\u26a0\ufe0f At {int(ratio * 100)}% of monthly limit "
                    f"({count}/{limit}). Consider upgrading your plan."
                )
        else:
            message = f"\u26a0\ufe0f Approaching limit: {count}/{limit} reports ({int(ratio * 100)}%)"
    else:
        if plan["allow_overage"]:
            decision    = LimitDecision.ALLOW_WITH_WARNING
            can_proceed = True
            overage     = count - limit
            message     = (
                f"\u26a0\ufe0f Significantly over limit ({count}/{limit}). "
                f"Overage charges: ${overage * plan['overage_price_cents'] / 100:.2f}"
            )
        else:
            decision    = LimitDecision.BLOCK
            can_proceed = False
            message     = (
                f"\U0001f6ab Monthly report limit reached ({count}/{limit}). "
                f"Upgrade your plan to generate more reports."
            )

    return decision, {
        "usage":        usage,
        "plan":         plan,
        "ratio":        ratio,
        "message":      message,
        "can_proceed":  can_proceed,
        "overage_count": max(0, count - limit) if limit > 0 else 0,
    }


# ─── LOGGING HELPER ───────────────────────────────────────────────────────────

def log_limit_decision(account_id: str, decision: LimitDecision, info: Dict[str, Any]):
    """Log usage limit decision for monitoring and debugging."""
    plan  = info.get("plan", {})
    usage = info.get("usage", {})
    logger.info(
        f"[usage] account={account_id} "
        f"plan={plan.get('plan_slug', 'unknown')} "
        f"decision={decision.value} "
        f"usage={usage.get('report_count', 0)} "
        f"limit={plan.get('monthly_report_limit', 0)} "
        f"ratio={info.get('ratio', 0):.2f}"
    )
