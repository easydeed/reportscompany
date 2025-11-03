from fastapi import APIRouter, Depends, Request, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts
from .reports import require_account_id  # temporary auth

router = APIRouter(prefix="/v1")

def iso_date(s: Optional[str], default: Optional[datetime] = None) -> datetime:
    if s:
        return datetime.fromisoformat(s.replace('Z',''))
    return default or datetime.utcnow()

@router.get("/usage")
def get_usage(
    request: Request,
    account_id: str = Depends(require_account_id),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    group_by: str = Query("day", pattern="^(day|week|month)$")
):
    # defaults: last 30 days
    end = iso_date(to_date, datetime.utcnow())
    start = iso_date(from_date, end - timedelta(days=30))

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)

        # Summary: total reports in period
        cur.execute("""
          SELECT
            COUNT(*) AS total_reports,
            COUNT(*) FILTER (WHERE billable IS TRUE) AS billable_reports
          FROM report_generations
          WHERE generated_at >= %s AND generated_at < %s
        """, (start, end))
        summary = fetchone_dict(cur) or {"total_reports":0,"billable_reports":0}

        # By type
        cur.execute("""
          SELECT report_type, COUNT(*) AS c
          FROM report_generations
          WHERE generated_at >= %s AND generated_at < %s
          GROUP BY report_type
          ORDER BY c DESC
        """, (start, end))
        by_type = list(fetchall_dicts(cur))

        # Timeline (by day/week/month)
        bucket = {
          "day":   "DATE_TRUNC('day', generated_at)",
          "week":  "DATE_TRUNC('week', generated_at)",
          "month": "DATE_TRUNC('month', generated_at)",
        }[group_by]
        cur.execute(f"""
          SELECT {bucket} AS bucket, COUNT(*) AS c
          FROM report_generations
          WHERE generated_at >= %s AND generated_at < %s
          GROUP BY 1
          ORDER BY 1
        """, (start, end))
        timeline_rows = list(fetchall_dicts(cur))
        timeline = [
          {"date": (r["bucket"].isoformat() if hasattr(r["bucket"], "isoformat") else str(r["bucket"])), "reports": r["c"]}
          for r in timeline_rows
        ]

        # Account limits for UI
        cur.execute("""
          SELECT monthly_report_limit, api_rate_limit
          FROM accounts WHERE id = %s
        """, (account_id,))
        limits = fetchone_dict(cur) or {"monthly_report_limit": None, "api_rate_limit": None}

    return {
        "period": {"from": start.isoformat(), "to": end.isoformat(), "group_by": group_by},
        "summary": summary,
        "by_type": by_type,
        "timeline": timeline,
        "limits": limits
    }







