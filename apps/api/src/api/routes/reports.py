from fastapi import APIRouter, Depends, HTTPException, Request, Query, status, Response
from pydantic import BaseModel, Field, constr
from typing import List, Optional, Dict, Any
import json
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts
from ..services import evaluate_report_limit, log_limit_decision, LimitDecision

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


class ReportRow(BaseModel):
    id: str
    report_type: str
    status: str
    html_url: Optional[str] = None
    json_url: Optional[str] = None
    csv_url: Optional[str] = None
    pdf_url: Optional[str] = None
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
    account_id: str = Depends(require_account_id)
):
    """
    Create a new report generation request.
    
    Enforces monthly report limits based on account's plan.
    Returns 429 if limit exceeded (for non-overage plans).
    """
    params = {
        "city": payload.city,
        "zips": payload.zips,
        "polygon": payload.polygon,
        "lookback_days": payload.lookback_days,
        "filters": payload.filters or {},
        "additional_params": payload.additional_params or {}
    }

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        
        # ===== PHASE 29B: CHECK USAGE LIMITS =====
        decision, info = evaluate_report_limit(cur, account_id)
        log_limit_decision(account_id, decision, info)
        
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
        
        cur.execute(
            """
            INSERT INTO report_generations
              (account_id, report_type, input_params, status)
            VALUES (%s, %s, %s::jsonb, 'pending')
            RETURNING id::text, status
            """,
            (account_id, payload.report_type, json.dumps(params)),
        )
        row = fetchone_dict(cur)

    # enqueue job
    try:
        from ..worker_client import enqueue_generate_report
        enqueue_generate_report(row["id"], account_id, payload.report_type, params)
    except Exception:
        pass

    return {"report_id": row["id"], "status": row["status"]}


@router.get("/reports/{report_id}", response_model=ReportRow)
def get_report(report_id: str, request: Request, account_id: str = Depends(require_account_id)):
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        # CRITICAL: Always filter by account_id for data isolation
        cur.execute(
            """
            SELECT id::text, report_type, status, html_url, json_url, csv_url, pdf_url,
                   generated_at::text
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
          SELECT id::text, report_type, status, html_url, json_url, csv_url, pdf_url,
                 generated_at::text
          FROM report_generations
          WHERE {' AND '.join(where)}
          ORDER BY generated_at DESC
          LIMIT %s OFFSET %s
        """
        cur.execute(sql, (*params, limit, offset))
        items = list(fetchall_dicts(cur))

    return {"reports": items, "pagination": {"limit": limit, "offset": offset, "count": len(items)}}

