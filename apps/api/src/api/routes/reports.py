from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Query, status, Response
from pydantic import BaseModel, Field, constr
from typing import Any, Dict, List, Optional
import json
import logging
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts
from ..services import evaluate_report_limit, log_limit_decision, LimitDecision
from ..services.email import send_limit_warning_email, send_limit_reached_email
from ..cache import get_redis
from ..crmls_cities import VALID_CITY_NAMES

_logger = logging.getLogger(__name__)


def _check_and_notify_limit(account_id: str, info: dict):
    """
    After a report is enqueued, check usage % and send one-time
    notifications at 80% and 100% thresholds.
    Uses Redis keys with 30-day TTL for billing-cycle dedup.
    """
    try:
        plan = info.get("plan", {})
        usage = info.get("usage", {})
        limit = plan.get("monthly_report_limit", 0)
        count = usage.get("report_count", 0) + 1  # +1 for the report just enqueued

        if limit <= 0 or limit >= 10000:
            return

        ratio = count / limit
        month_key = usage.get("period_start", "")[:7]  # "YYYY-MM"
        if not month_key:
            return

        r = get_redis()

        with db_conn() as (conn, cur):
            cur.execute("""
                SELECT u.email, u.first_name
                FROM users u
                JOIN account_users au ON au.user_id = u.id
                WHERE au.account_id = %s::uuid AND au.role = 'OWNER'
                LIMIT 1
            """, (account_id,))
            owner = cur.fetchone()
            if not owner or not owner[0]:
                return
            email, first_name = owner

        if ratio >= 1.0:
            cache_key = f"limit_notify:{account_id}:{month_key}:100"
            if not r.get(cache_key):
                send_limit_reached_email(email, first_name, limit)
                r.setex(cache_key, 30 * 86400, "1")
                _logger.info(f"Sent 100%% limit notification to {email} for account {account_id}")

        elif ratio >= 0.8:
            cache_key = f"limit_notify:{account_id}:{month_key}:80"
            if not r.get(cache_key):
                send_limit_warning_email(email, first_name, count, limit)
                r.setex(cache_key, 30 * 86400, "1")
                _logger.info(f"Sent 80%% limit notification to {email} for account {account_id}")

    except Exception as exc:
        _logger.warning(f"Limit notification check failed (non-critical): {exc}")


router = APIRouter(prefix="/v1")

# ====== Schemas ======
class ReportCreate(BaseModel):
    report_type: constr(strip_whitespace=True, min_length=2)
    city: Optional[str] = None
    zips: Optional[List[str]] = None
    polygon: Optional[str] = None
    lookback_days: int = 30
    filters: Optional[Dict[str, Any]] = None
    additional_params: Optional[dict] = None
    theme_id: Optional[str] = None
    accent_color: Optional[str] = None
    send_email: Optional[bool] = None
    recipients: Optional[list] = None


class ReportRow(BaseModel):
    id: str
    report_type: str
    status: str
    city: Optional[str] = None
    html_url: Optional[str] = None
    json_url: Optional[str] = None
    csv_url: Optional[str] = None
    pdf_url: Optional[str] = None
    theme_id: Optional[str] = None
    generated_at: Optional[str] = None


# ====== Helpers ======
def require_account_id(request: Request) -> str:
    """
    Returns the account_id set by AuthContextMiddleware.
    The middleware has already validated authentication, so we just retrieve it.
    """
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account_id


# ====== Routes ======
@router.post("/reports", status_code=status.HTTP_202_ACCEPTED)
def create_report(
    payload: ReportCreate, 
    response: Response,
    request: Request, 
    bg: BackgroundTasks,
    account_id: str = Depends(require_account_id)
):
    """
    Create a new report generation request.
    
    Enforces monthly report limits based on account's plan.
    Returns 429 if limit exceeded (for non-overage plans).
    """
    if payload.city and payload.city not in VALID_CITY_NAMES:
        raise HTTPException(
            status_code=422,
            detail=f"'{payload.city}' is not a recognized CRMLS city. "
                   f"Please select a city from the dropdown.",
        )

    params = {
        "city": payload.city,
        "zips": payload.zips,
        "polygon": payload.polygon,
        "lookback_days": payload.lookback_days,
        "filters": payload.filters or {},
        "additional_params": payload.additional_params or {},
        "send_email": payload.send_email,
        "recipients": payload.recipients,
    }

    limit_info = None
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        
        # ===== PHASE 29B: CHECK USAGE LIMITS =====
        decision, info = evaluate_report_limit(cur, account_id)
        log_limit_decision(account_id, decision, info)
        limit_info = info
        
        # Block if limit reached and no overage allowed
        if decision == LimitDecision.BLOCK:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "limit_reached",
                    "message": info["message"],
                    "usage": info["usage"],
                    "plan": info["plan"],
                }
            )
        
        # Add warning header if approaching/over limit
        if decision == LimitDecision.ALLOW_WITH_WARNING:
            response.headers["X-TrendyReports-Usage-Warning"] = info["message"]
        # ===== END PHASE 29B =====
        
        # Resolve theme defaults from account if not provided
        theme_id = payload.theme_id
        accent_color = payload.accent_color
        if not theme_id:
            cur.execute(
                "SELECT default_theme_id FROM accounts WHERE id = %s::uuid",
                (account_id,),
            )
            acct_row = cur.fetchone()
            theme_id = str(acct_row[0]) if acct_row and acct_row[0] else "1"
        if not accent_color:
            cur.execute(
                "SELECT secondary_color FROM accounts WHERE id = %s::uuid",
                (account_id,),
            )
            acct_row2 = cur.fetchone()
            if acct_row2 and acct_row2[0]:
                accent_color = acct_row2[0]

        cur.execute(
            """
            INSERT INTO report_generations
              (account_id, report_type, input_params, status, theme_id, accent_color)
            VALUES (%s, %s, %s::jsonb, 'pending', %s, %s)
            RETURNING id::text, status
            """,
            (account_id, payload.report_type, json.dumps(params), theme_id, accent_color),
        )
        row = fetchone_dict(cur)

    # enqueue job
    try:
        from ..worker_client import enqueue_generate_report
        enqueue_generate_report(row["id"], account_id, payload.report_type, params)
    except Exception as e:
        # Log the error instead of swallowing it silently
        import logging
        logging.getLogger(__name__).error(f"Failed to enqueue report {row['id']}: {e}")
        # Update report status to failed
        with db_conn() as (conn2, cur2):
            cur2.execute("""
                UPDATE report_generations 
                SET status='failed', error_message=%s 
                WHERE id=%s
            """, (f"Failed to enqueue: {str(e)}", row["id"]))
            conn2.commit()

    # Check plan limits and send notifications in background (non-blocking)
    if limit_info:
        bg.add_task(_check_and_notify_limit, account_id, limit_info)

    return {"report_id": row["id"], "status": row["status"]}


@router.get("/reports/{report_id}", response_model=ReportRow)
def get_report(report_id: str, request: Request, account_id: str = Depends(require_account_id)):
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        # CRITICAL: Always filter by account_id for data isolation
        cur.execute(
            """
            SELECT id::text, report_type, status,
                   input_params->>'city' AS city,
                   html_url, json_url, csv_url, pdf_url,
                   theme_id, generated_at::text
            FROM report_generations
            WHERE id = %s AND account_id = %s
            """,
            (report_id, account_id),
        )
        row = fetchone_dict(cur)
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
        return row


@router.get("/reports")
def list_reports(
    request: Request,
    account_id: str = Depends(require_account_id),
    type: Optional[str] = Query(None, alias="report_type"),
    status_param: Optional[str] = Query(None, alias="status"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # CRITICAL: Always filter by account_id for data isolation
    where = ["account_id = %s"]
    params = [account_id]
    
    if type:
        where.append("report_type = %s")
        params.append(type)
    if status_param:
        where.append("status = %s")
        params.append(status_param)
    if from_date:
        where.append("generated_at >= %s::timestamp")
        params.append(from_date)
    if to_date:
        where.append("generated_at < %s::timestamp")
        params.append(to_date)

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        sql = f"""
          SELECT id::text, report_type, status,
                 input_params->>'city' AS city,
                 html_url, json_url, csv_url, pdf_url,
                 theme_id, generated_at::text
          FROM report_generations
          WHERE {' AND '.join(where)}
          ORDER BY generated_at DESC
          LIMIT %s OFFSET %s
        """
        cur.execute(sql, (*params, limit, offset))
        items = list(fetchall_dicts(cur))

    return {"reports": items, "pagination": {"limit": limit, "offset": offset, "count": len(items)}}

