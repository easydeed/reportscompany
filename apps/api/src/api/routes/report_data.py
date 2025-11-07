from fastapi import APIRouter, Depends, HTTPException, Request
from ..db import db_conn, set_rls, fetchone_dict
from .reports import require_account_id

router = APIRouter(prefix="/v1")

@router.get("/reports/{run_id}/data")
def report_data(run_id: str, request: Request, account_id: str = Depends(require_account_id)):
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute("SELECT result_json FROM report_generations WHERE id=%s", (run_id,))
        row = fetchone_dict(cur)
        if not row or not row.get("result_json"):
            raise HTTPException(status_code=404, detail="No data for report")
        return row["result_json"]





