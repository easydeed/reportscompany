from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import BaseModel, Field, constr
from typing import List, Optional
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts

router = APIRouter(prefix="/v1")

# ====== Schemas ======
class ReportCreate(BaseModel):
    type: constr(strip_whitespace=True, min_length=2) = Field(..., alias="report_type")
    cities: Optional[List[str]] = None
    zipCodes: Optional[List[str]] = None
    lookback_days: int = 30
    property_type: Optional[str] = None
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
    # TEMP auth: header X-Demo-Account (we'll replace with JWT later)
    if request.url.path.endswith("/health"):
        return "00000000-0000-0000-0000-000000000000"
    account_id = request.headers.get("X-Demo-Account")
    if not account_id:
        raise HTTPException(status_code=401, detail="Missing X-Demo-Account header (temporary auth).")
    return account_id


# ====== Routes ======
@router.post("/reports", status_code=status.HTTP_202_ACCEPTED)
def create_report(payload: ReportCreate, request: Request, account_id: str = Depends(require_account_id)):
    # normalize inputs
    cities = payload.cities or []
    if payload.zipCodes and not cities:
        # allow zip codes to be passed but store as cities[] for now
        cities = payload.zipCodes

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute(
            """
            INSERT INTO report_generations
              (account_id, report_type, cities, lookback_days, property_type, additional_params, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id::text, status
            """,
            (account_id, payload.type, cities or None, payload.lookback_days, payload.property_type, payload.additional_params),
        )
        row = fetchone_dict(cur)

    # enqueue Celery job
    # NOTE: we import lazily to avoid importing Celery at app import time
    try:
        from ..worker_client import enqueue_generate_report
        enqueue_generate_report(row["id"], account_id)
    except Exception as e:
        # If enqueue fails, we still return 202; worker can be retried later
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

