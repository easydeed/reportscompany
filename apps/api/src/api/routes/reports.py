from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import BaseModel, Field, constr
from typing import List, Optional, Dict, Any
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts

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
def create_report(payload: ReportCreate, request: Request, account_id: str = Depends(require_account_id)):
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
        cur.execute(
            """
            INSERT INTO report_generations
              (account_id, report_type, input_params, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id::text, status
            """,
            (account_id, payload.report_type, params),
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
        cur.execute(
            """
            SELECT id::text, report_type, status, html_url, json_url, csv_url, pdf_url,
                   generated_at::text
            FROM report_generations
            WHERE id = %s
            """,
            (report_id,),
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
    where = ["1=1"]
    params = []
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

