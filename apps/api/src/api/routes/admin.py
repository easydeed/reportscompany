"""
Admin Console API Routes
Provides system-wide metrics, schedules, reports, and email logs for platform operators.
Requires ADMIN role.
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from ..db import db_conn
from ..deps.admin import get_admin_user

router = APIRouter(prefix="/v1/admin", tags=["admin"])


# ==================== Metrics ====================

@router.get("/metrics")
def get_admin_metrics(_admin: dict = Depends(get_admin_user)):
    """
    Get system-wide metrics for the admin dashboard.
    
    Returns:
        - reports_24h: Number of reports generated in last 24 hours
        - reports_7d: Number of reports generated in last 7 days
        - avg_processing_ms_7d: Average processing time in milliseconds (last 7 days)
        - schedules_active: Number of active schedules
        - emails_24h: Number of emails sent in last 24 hours
        - queue_depth: Current queue depth (optional, returns 0 if not available)
    """
    
    with db_conn() as conn:
        cur = conn.cursor()
        
        # Reports in last 24h
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        reports_24h = cur.fetchone()[0] or 0
        
        # Reports in last 7d
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        reports_7d = cur.fetchone()[0] or 0
        
        # Avg processing time in last 7d (for completed reports)
        cur.execute("""
            SELECT AVG(EXTRACT(EPOCH FROM (finished_at - started_at)) * 1000)
            FROM report_generations
            WHERE status = 'completed'
            AND finished_at IS NOT NULL
            AND started_at IS NOT NULL
            AND created_at >= NOW() - INTERVAL '7 days'
        """)
        avg_ms = cur.fetchone()[0]
        avg_processing_ms_7d = int(avg_ms) if avg_ms else 0
        
        # Active schedules
        cur.execute("""
            SELECT COUNT(*) FROM schedules
            WHERE active = TRUE
        """)
        schedules_active = cur.fetchone()[0] or 0
        
        # Emails in last 24h
        cur.execute("""
            SELECT COUNT(*) FROM email_log
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        emails_24h = cur.fetchone()[0] or 0
        
        # Queue depth (placeholder - would require Redis inspection)
        queue_depth = 0
        
        return {
            "reports_24h": reports_24h,
            "reports_7d": reports_7d,
            "avg_processing_ms_7d": avg_processing_ms_7d,
            "schedules_active": schedules_active,
            "emails_24h": emails_24h,
            "queue_depth": queue_depth
        }


@router.get("/metrics/timeseries")
def get_admin_timeseries(
    days: int = Query(30, ge=1, le=90),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get timeseries data for charts (reports and emails per day).
    
    Args:
        days: Number of days to retrieve (1-90, default 30)
    
    Returns:
        - reports_by_day: Array of {date, count}
        - emails_by_day: Array of {date, count}
    """
    
    with db_conn() as conn:
        cur = conn.cursor()
        
        # Reports by day
        cur.execute("""
            SELECT 
                DATE(created_at) as day,
                COUNT(*) as count
            FROM report_generations
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        """, (days,))
        reports_by_day = [
            {"date": str(row[0]), "count": row[1]}
            for row in cur.fetchall()
        ]
        
        # Emails by day
        cur.execute("""
            SELECT 
                DATE(created_at) as day,
                COUNT(*) as count
            FROM email_log
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        """, (days,))
        emails_by_day = [
            {"date": str(row[0]), "count": row[1]}
            for row in cur.fetchall()
        ]
        
        return {
            "reports_by_day": reports_by_day,
            "emails_by_day": emails_by_day
        }


# ==================== Schedules ====================

@router.get("/schedules")
def list_admin_schedules(
    search: Optional[str] = None,
    active: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    _admin: dict = Depends(get_admin_user)
):
    """
    List all schedules across all accounts with search and filter capabilities.
    
    Args:
        search: Search by schedule name or account name
        active: Filter by active status
        limit: Maximum number of results
    
    Returns:
        Array of schedules with account information
    """
    
    query = """
        SELECT 
            s.id,
            s.account_id,
            a.name as account_name,
            s.name,
            s.report_type,
            s.city,
            s.zip_codes,
            s.cadence,
            s.weekly_dow,
            s.monthly_dom,
            s.send_hour,
            s.send_minute,
            s.recipients,
            s.active,
            s.next_run_at,
            s.last_run_at,
            s.created_at
        FROM schedules s
        JOIN accounts a ON s.account_id = a.id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (s.name ILIKE %s OR a.name ILIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    if active is not None:
        query += " AND s.active = %s"
        params.append(active)
    
    query += " ORDER BY s.created_at DESC LIMIT %s"
    params.append(limit)
    
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        
        schedules = []
        for row in cur.fetchall():
            schedules.append({
                "id": str(row[0]),
                "account_id": str(row[1]),
                "account_name": row[2],
                "name": row[3],
                "report_type": row[4],
                "city": row[5],
                "zip_codes": row[6],
                "cadence": row[7],
                "weekly_dow": row[8],
                "monthly_dom": row[9],
                "send_hour": row[10],
                "send_minute": row[11],
                "recipients": row[12],
                "active": row[13],
                "next_run_at": row[14].isoformat() if row[14] else None,
                "last_run_at": row[15].isoformat() if row[15] else None,
                "created_at": row[16].isoformat() if row[16] else None
            })
        
        return {"schedules": schedules, "count": len(schedules)}


# ==================== Reports ====================

@router.get("/reports")
def list_admin_reports(
    status: Optional[str] = None,
    report_type: Optional[str] = None,
    limit: int = Query(200, ge=1, le=1000),
    _admin: dict = Depends(get_admin_user)
):
    """
    List recent report generations across all accounts.
    
    Args:
        status: Filter by status (pending, processing, completed, failed)
        report_type: Filter by report type
        limit: Maximum number of results
    
    Returns:
        Array of reports with account and timing information
    """
    
    query = """
        SELECT 
            r.id,
            r.account_id,
            a.name as account_name,
            r.report_type,
            r.status,
            r.params,
            r.result_json,
            r.pdf_url,
            r.error,
            r.started_at,
            r.finished_at,
            r.created_at,
            EXTRACT(EPOCH FROM (r.finished_at - r.started_at)) * 1000 as duration_ms
        FROM report_generations r
        JOIN accounts a ON r.account_id = a.id
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND r.status = %s"
        params.append(status)
    
    if report_type:
        query += " AND r.report_type = %s"
        params.append(report_type)
    
    query += " ORDER BY r.created_at DESC LIMIT %s"
    params.append(limit)
    
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        
        reports = []
        for row in cur.fetchall():
            reports.append({
                "id": str(row[0]),
                "account_id": str(row[1]),
                "account_name": row[2],
                "report_type": row[3],
                "status": row[4],
                "params": row[5],
                "has_result": bool(row[6]),
                "pdf_url": row[7],
                "error": row[8],
                "started_at": row[9].isoformat() if row[9] else None,
                "finished_at": row[10].isoformat() if row[10] else None,
                "created_at": row[11].isoformat() if row[11] else None,
                "duration_ms": int(row[12]) if row[12] else None
            })
        
        return {"reports": reports, "count": len(reports)}


# ==================== Emails ====================

@router.get("/emails")
def list_admin_emails(
    limit: int = Query(200, ge=1, le=1000),
    _admin: dict = Depends(get_admin_user)
):
    """
    List recent email sends across all accounts.
    
    Args:
        limit: Maximum number of results
    
    Returns:
        Array of email logs with delivery information
    """
    
    query = """
        SELECT 
            e.id,
            e.account_id,
            a.name as account_name,
            e.schedule_id,
            e.report_id,
            e.provider,
            e.to_emails,
            e.subject,
            e.response_code,
            e.error,
            e.created_at
        FROM email_log e
        JOIN accounts a ON e.account_id = a.id
        ORDER BY e.created_at DESC
        LIMIT %s
    """
    
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, (limit,))
        
        emails = []
        for row in cur.fetchall():
            emails.append({
                "id": str(row[0]),
                "account_id": str(row[1]),
                "account_name": row[2],
                "schedule_id": str(row[3]) if row[3] else None,
                "report_id": str(row[4]) if row[4] else None,
                "provider": row[5],
                "to_emails": row[6],
                "to_count": len(row[6]) if row[6] else 0,
                "subject": row[7],
                "response_code": row[8],
                "error": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "status": "success" if row[8] and row[8] < 300 else "failed"
            })
        
        return {"emails": emails, "count": len(emails)}


# ==================== Schedule Actions ====================

@router.patch("/schedules/{schedule_id}")
def update_admin_schedule(
    schedule_id: str,
    active: bool,
    _admin: dict = Depends(get_admin_user)
):
    """
    Update schedule status (pause/resume) from admin console.
    
    Args:
        schedule_id: Schedule UUID
        active: Whether the schedule should be active
    
    Returns:
        Success message
    """
    
    with db_conn() as conn:
        cur = conn.cursor()
        
        # Update schedule
        cur.execute("""
            UPDATE schedules
            SET active = %s, next_run_at = NULL
            WHERE id = %s::uuid
            RETURNING id
        """, (active, schedule_id))
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        conn.commit()
        
        return {
            "message": f"Schedule {'activated' if active else 'paused'}",
            "schedule_id": schedule_id,
            "active": active
        }

