"""
Admin Metrics API Routes

Dashboard metrics for monitoring Lead Pages performance.
Requires admin authentication.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..db import db_conn, fetchone_dict, fetchall_dicts
from .admin import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin/metrics", tags=["admin-metrics"])


# =============================================
# SCHEMAS
# =============================================

class DailyMetric(BaseModel):
    date: str
    reports_requested: int
    reports_ready: int
    reports_failed: int
    pdfs_generated: int
    agent_contacts: int
    total_views: int
    avg_views_per_report: float
    avg_time_seconds: float
    unique_agents: int


class OverviewStats(BaseModel):
    # Totals
    total_reports: int
    total_views: int
    total_pdfs: int
    total_contacts: int
    
    # Rates
    pdf_rate_pct: float        # % of reports that got PDF
    contact_rate_pct: float    # % of reports that led to contact
    
    # Today
    reports_today: int
    views_today: int
    contacts_today: int
    
    # This week
    reports_this_week: int
    
    # This month
    reports_this_month: int
    
    # Trends (vs last period)
    reports_trend_pct: float   # +/- % vs previous period
    contacts_trend_pct: float


class AgentLeaderboard(BaseModel):
    agent_id: str
    agent_name: str
    agent_email: str
    account_name: str
    total_reports: int
    reports_30d: int
    total_views: int
    contacts: int
    contact_rate_pct: Optional[float]
    pdfs_downloaded: int


class HourlyDistribution(BaseModel):
    hour: int
    report_count: int
    pdf_count: int


class DeviceBreakdown(BaseModel):
    device_type: str
    count: int
    percentage: float


class RecentReport(BaseModel):
    id: str
    agent_name: str
    property_address: str
    status: str
    view_count: int
    agent_contacted: bool
    has_pdf: bool
    created_at: datetime


# =============================================
# ENDPOINTS
# =============================================

@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(_admin: dict = Depends(get_admin_user)):
    """
    Get high-level dashboard metrics.
    """
    with db_conn() as (conn, cur):
        # Totals
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_reports,
                COALESCE(SUM(view_count), 0) as total_views,
                COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as total_pdfs,
                COUNT(*) FILTER (WHERE agent_contact_clicked = true) as total_contacts
            FROM consumer_reports
            """
        )
        totals = fetchone_dict(cur)
        
        # Today
        cur.execute(
            """
            SELECT 
                COUNT(*) as reports_today,
                COALESCE(SUM(view_count), 0) as views_today,
                COUNT(*) FILTER (WHERE agent_contact_clicked = true) as contacts_today
            FROM consumer_reports
            WHERE DATE(created_at) = CURRENT_DATE
            """
        )
        today = fetchone_dict(cur)
        
        # This week
        cur.execute(
            """
            SELECT COUNT(*) as week_count FROM consumer_reports
            WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
            """
        )
        week = fetchone_dict(cur)
        
        # This month
        cur.execute(
            """
            SELECT COUNT(*) as month_count FROM consumer_reports
            WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
            """
        )
        month = fetchone_dict(cur)
        
        # Previous month for trend
        cur.execute(
            """
            SELECT COUNT(*) as prev_month_count FROM consumer_reports
            WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
            AND created_at < DATE_TRUNC('month', CURRENT_DATE)
            """
        )
        prev_month = fetchone_dict(cur)
    
    total = totals.get("total_reports") or 0
    prev_month_count = prev_month.get("prev_month_count") or 0
    month_count = month.get("month_count") or 0
    
    return OverviewStats(
        total_reports=total,
        total_views=int(totals.get("total_views") or 0),
        total_pdfs=totals.get("total_pdfs") or 0,
        total_contacts=totals.get("total_contacts") or 0,
        pdf_rate_pct=round((totals.get("total_pdfs") or 0) / max(total, 1) * 100, 1),
        contact_rate_pct=round((totals.get("total_contacts") or 0) / max(total, 1) * 100, 1),
        reports_today=today.get("reports_today") or 0,
        views_today=int(today.get("views_today") or 0),
        contacts_today=today.get("contacts_today") or 0,
        reports_this_week=week.get("week_count") or 0,
        reports_this_month=month_count,
        reports_trend_pct=round((month_count - prev_month_count) / max(prev_month_count, 1) * 100, 1) if prev_month_count else 0,
        contacts_trend_pct=0  # TODO: Calculate
    )


@router.get("/daily", response_model=List[DailyMetric])
async def get_daily_metrics(
    days: int = Query(30, ge=7, le=90),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get daily metrics for charting.
    """
    with db_conn() as (conn, cur):
        cur.execute(
            """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as reports_requested,
                COUNT(*) FILTER (WHERE status = 'ready') as reports_ready,
                COUNT(*) FILTER (WHERE status = 'failed') as reports_failed,
                COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdfs_generated,
                COUNT(*) FILTER (WHERE agent_contact_clicked = true) as agent_contacts,
                COALESCE(SUM(view_count), 0) as total_views,
                COALESCE(AVG(view_count), 0) as avg_views_per_report,
                COALESCE(AVG(time_on_page), 0) as avg_time_seconds,
                COUNT(DISTINCT agent_id) as unique_agents
            FROM consumer_reports
            WHERE created_at >= CURRENT_DATE - %s
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,
            (days,)
        )
        rows = fetchall_dicts(cur)
    
    return [DailyMetric(
        date=str(r["date"]),
        reports_requested=r["reports_requested"],
        reports_ready=r["reports_ready"],
        reports_failed=r["reports_failed"],
        pdfs_generated=r["pdfs_generated"],
        agent_contacts=r["agent_contacts"],
        total_views=int(r["total_views"]),
        avg_views_per_report=round(float(r["avg_views_per_report"]), 1),
        avg_time_seconds=round(float(r["avg_time_seconds"]), 1),
        unique_agents=r["unique_agents"]
    ) for r in rows]


@router.get("/agents", response_model=List[AgentLeaderboard])
async def get_agent_leaderboard(
    limit: int = Query(20, ge=10, le=100),
    sort_by: str = Query("total_reports"),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get agent leaderboard by report volume or contact rate.
    """
    # Validate sort_by
    valid_sorts = ["total_reports", "contacts", "contact_rate_pct"]
    if sort_by not in valid_sorts:
        sort_by = "total_reports"
    
    with db_conn() as (conn, cur):
        cur.execute(
            f"""
            SELECT 
                u.id as agent_id,
                CONCAT(u.first_name, ' ', u.last_name) as agent_name,
                u.email as agent_email,
                a.name as account_name,
                COUNT(cr.id) as total_reports,
                COUNT(cr.id) FILTER (WHERE cr.created_at > NOW() - INTERVAL '30 days') as reports_30d,
                COALESCE(SUM(cr.view_count), 0) as total_views,
                COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true) as contacts,
                ROUND(
                    COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true)::numeric / 
                    NULLIF(COUNT(cr.id), 0) * 100, 1
                ) as contact_rate_pct,
                COUNT(cr.id) FILTER (WHERE cr.pdf_url IS NOT NULL) as pdfs_downloaded
            FROM users u
            JOIN accounts a ON u.account_id = a.id
            LEFT JOIN consumer_reports cr ON cr.agent_id = u.id
            GROUP BY u.id, u.first_name, u.last_name, u.email, a.name
            HAVING COUNT(cr.id) > 0
            ORDER BY {sort_by} DESC
            LIMIT %s
            """,
            (limit,)
        )
        rows = fetchall_dicts(cur)
    
    return [AgentLeaderboard(
        agent_id=str(r["agent_id"]),
        agent_name=r["agent_name"] or "",
        agent_email=r["agent_email"] or "",
        account_name=r["account_name"] or "",
        total_reports=r["total_reports"],
        reports_30d=r["reports_30d"],
        total_views=int(r["total_views"]),
        contacts=r["contacts"],
        contact_rate_pct=float(r["contact_rate_pct"]) if r["contact_rate_pct"] else 0,
        pdfs_downloaded=r["pdfs_downloaded"]
    ) for r in rows]


@router.get("/hourly", response_model=List[HourlyDistribution])
async def get_hourly_distribution(_admin: dict = Depends(get_admin_user)):
    """
    Get hourly report distribution (last 30 days).
    Useful for understanding peak load times.
    """
    with db_conn() as (conn, cur):
        cur.execute(
            """
            SELECT 
                EXTRACT(HOUR FROM created_at)::integer as hour,
                COUNT(*) as report_count,
                COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdf_count
            FROM consumer_reports
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
            """
        )
        rows = fetchall_dicts(cur)
    
    return [HourlyDistribution(
        hour=r["hour"],
        report_count=r["report_count"],
        pdf_count=r["pdf_count"]
    ) for r in rows]


@router.get("/devices", response_model=List[DeviceBreakdown])
async def get_device_breakdown(_admin: dict = Depends(get_admin_user)):
    """
    Get device type breakdown.
    """
    with db_conn() as (conn, cur):
        cur.execute(
            "SELECT COUNT(*) as total FROM consumer_reports WHERE device_type IS NOT NULL"
        )
        total_row = fetchone_dict(cur)
        total = total_row.get("total") or 0
        
        cur.execute(
            """
            SELECT 
                COALESCE(device_type, 'unknown') as device_type,
                COUNT(*) as count
            FROM consumer_reports
            GROUP BY device_type
            ORDER BY count DESC
            """
        )
        rows = fetchall_dicts(cur)
    
    return [DeviceBreakdown(
        device_type=r["device_type"] or "unknown",
        count=r["count"],
        percentage=round(r["count"] / max(total, 1) * 100, 1)
    ) for r in rows]


@router.get("/recent", response_model=List[RecentReport])
async def get_recent_reports(
    limit: int = Query(20, ge=10, le=100),
    status: Optional[str] = Query(None),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get recent reports for activity feed.
    """
    # Validate status
    valid_statuses = ["pending", "ready", "failed"]
    if status and status not in valid_statuses:
        status = None
    
    with db_conn() as (conn, cur):
        if status:
            cur.execute(
                """
                SELECT 
                    cr.id,
                    CONCAT(u.first_name, ' ', u.last_name) as agent_name,
                    cr.property_address,
                    cr.status,
                    cr.view_count,
                    cr.agent_contact_clicked as agent_contacted,
                    (cr.pdf_url IS NOT NULL) as has_pdf,
                    cr.created_at
                FROM consumer_reports cr
                JOIN users u ON cr.agent_id = u.id
                WHERE cr.status = %s
                ORDER BY cr.created_at DESC
                LIMIT %s
                """,
                (status, limit)
            )
        else:
            cur.execute(
                """
                SELECT 
                    cr.id,
                    CONCAT(u.first_name, ' ', u.last_name) as agent_name,
                    cr.property_address,
                    cr.status,
                    cr.view_count,
                    cr.agent_contact_clicked as agent_contacted,
                    (cr.pdf_url IS NOT NULL) as has_pdf,
                    cr.created_at
                FROM consumer_reports cr
                JOIN users u ON cr.agent_id = u.id
                ORDER BY cr.created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
        rows = fetchall_dicts(cur)
    
    return [RecentReport(
        id=str(r["id"]),
        agent_name=r["agent_name"] or "",
        property_address=r["property_address"] or "",
        status=r["status"],
        view_count=r["view_count"] or 0,
        agent_contacted=r["agent_contacted"] or False,
        has_pdf=r["has_pdf"] or False,
        created_at=r["created_at"]
    ) for r in rows]


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    days: int = Query(30, ge=7, le=90),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get conversion funnel metrics.
    """
    with db_conn() as (conn, cur):
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_requests,
                COUNT(*) FILTER (WHERE status = 'ready') as reports_generated,
                COUNT(*) FILTER (WHERE view_count > 0) as reports_viewed,
                COUNT(*) FILTER (WHERE view_count > 1) as reports_viewed_multiple,
                COUNT(*) FILTER (WHERE agent_contact_clicked = true) as agent_contacted,
                COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdf_downloaded
            FROM consumer_reports
            WHERE created_at >= CURRENT_DATE - %s
            """,
            (days,)
        )
        data = fetchone_dict(cur)
    
    total = data.get("total_requests") or 1
    
    return {
        "period_days": days,
        "funnel": [
            {"stage": "Reports Requested", "count": data["total_requests"], "pct": 100},
            {"stage": "Reports Generated", "count": data["reports_generated"], 
             "pct": round(data["reports_generated"] / total * 100, 1)},
            {"stage": "Reports Viewed", "count": data["reports_viewed"],
             "pct": round(data["reports_viewed"] / total * 100, 1)},
            {"stage": "Multiple Views", "count": data["reports_viewed_multiple"],
             "pct": round(data["reports_viewed_multiple"] / total * 100, 1)},
            {"stage": "Agent Contacted", "count": data["agent_contacted"],
             "pct": round(data["agent_contacted"] / total * 100, 1)},
            {"stage": "PDF Downloaded", "count": data["pdf_downloaded"],
             "pct": round(data["pdf_downloaded"] / total * 100, 1)},
        ]
    }

