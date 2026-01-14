"""
Admin Console API Routes
Provides system-wide metrics, schedules, reports, and email logs for platform operators.
Requires ADMIN role.
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import secrets
import logging
from ..db import db_conn, set_rls
from ..deps.admin import get_admin_user
from ..services import get_monthly_usage, resolve_plan_for_account, evaluate_report_limit
from ..services.email import send_invite_email, send_welcome_email
from ..services.property_stats import get_platform_stats, refresh_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


# ==================== Metrics ====================

@router.get("/metrics")
def get_admin_metrics(_admin: dict = Depends(get_admin_user)):
    """
    Get system-wide metrics for the admin dashboard.

    Returns:
        - reports_24h: Number of reports generated in last 24 hours
        - reports_7d: Number of reports generated in last 7 days
        - reports_failed_7d: Number of failed reports in last 7 days
        - error_rate_7d: Failure percentage in last 7 days
        - avg_processing_ms_7d: Average processing time in milliseconds (last 7 days)
        - schedules_active: Number of active schedules
        - emails_24h: Number of emails sent in last 24 hours
        - total_accounts: Total number of accounts
        - total_users: Total number of users
        - total_affiliates: Total number of affiliate accounts
        - queue_depth: Current queue depth (optional, returns 0 if not available)
    """

    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Reports in last 24h
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE generated_at >= NOW() - INTERVAL '24 hours'
        """)
        reports_24h = cur.fetchone()[0] or 0

        # Reports in last 7d (total and failed)
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'processing') as processing,
                COUNT(*) FILTER (WHERE status = 'pending') as pending
            FROM report_generations
            WHERE generated_at >= NOW() - INTERVAL '7 days'
        """)
        row = cur.fetchone()
        reports_7d = row[0] or 0
        reports_failed_7d = row[1] or 0
        reports_completed_7d = row[2] or 0
        reports_processing = row[3] or 0
        reports_pending = row[4] or 0

        # Calculate error rate
        error_rate_7d = 0.0
        if reports_7d > 0:
            error_rate_7d = round((reports_failed_7d / reports_7d) * 100, 2)

        # Avg processing time in last 7d (for completed reports)
        cur.execute("""
            SELECT AVG(processing_time_ms)
            FROM report_generations
            WHERE status = 'completed'
            AND processing_time_ms IS NOT NULL
            AND generated_at >= NOW() - INTERVAL '7 days'
        """)
        avg_ms = cur.fetchone()[0]
        avg_processing_ms_7d = int(avg_ms) if avg_ms else 0

        # Active schedules
        cur.execute("""
            SELECT COUNT(*) FROM schedules
            WHERE active = TRUE
        """)
        schedules_active = cur.fetchone()[0] or 0

        # Total schedules
        cur.execute("SELECT COUNT(*) FROM schedules")
        schedules_total = cur.fetchone()[0] or 0

        # Emails in last 24h
        cur.execute("""
            SELECT COUNT(*) FROM email_log
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        emails_24h = cur.fetchone()[0] or 0

        # Total accounts
        cur.execute("SELECT COUNT(*) FROM accounts")
        total_accounts = cur.fetchone()[0] or 0

        # Total users
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0] or 0

        # Total affiliates
        cur.execute("SELECT COUNT(*) FROM accounts WHERE account_type = 'INDUSTRY_AFFILIATE'")
        total_affiliates = cur.fetchone()[0] or 0

        # Active users (placeholder - no last_login_at column yet)
        # TODO: Add last_login_at column to users table to track this
        active_users_30d = 0

        # Queue depth (placeholder - would require Redis inspection)
        queue_depth = 0

        return {
            "reports_24h": reports_24h,
            "reports_7d": reports_7d,
            "reports_failed_7d": reports_failed_7d,
            "reports_completed_7d": reports_completed_7d,
            "reports_processing": reports_processing,
            "reports_pending": reports_pending,
            "error_rate_7d": error_rate_7d,
            "avg_processing_ms_7d": avg_processing_ms_7d,
            "schedules_active": schedules_active,
            "schedules_total": schedules_total,
            "emails_24h": emails_24h,
            "total_accounts": total_accounts,
            "total_users": total_users,
            "total_affiliates": total_affiliates,
            "active_users_30d": active_users_30d,
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
    
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Reports by day
        cur.execute("""
            SELECT 
                DATE(generated_at) as day,
                COUNT(*) as count
            FROM report_generations
            WHERE generated_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(generated_at)
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
    
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
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
            r.input_params,
            r.result_json,
            r.pdf_url,
            r.error,
            r.generated_at,
            r.processing_time_ms
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
    
    query += " ORDER BY r.generated_at DESC LIMIT %s"
    params.append(limit)
    
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        cur.execute(query, params)
        
        reports = []
        for row in cur.fetchall():
            reports.append({
                "id": str(row[0]),
                "account_id": str(row[1]),
                "account_name": row[2],
                "report_type": row[3],
                "status": row[4],
                "params": row[5],  # input_params column
                "has_result": bool(row[6]),
                "pdf_url": row[7],
                "error": row[8],
                "generated_at": row[9].isoformat() if row[9] else None,
                "duration_ms": int(row[10]) if row[10] else None,
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
    
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
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
    
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
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


# ==================== Plan & Usage (Phase 29B) ====================

@router.get("/accounts/{account_id}/plan-usage")
def get_account_plan_usage(
    account_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """
    Get detailed plan and usage information for a specific account.
    
    Phase 29B: Admin-only endpoint for debugging plan limits and usage.
    
    Args:
        account_id: Account UUID
    
    Returns:
        - account_id: Account UUID
        - account_type: REGULAR or INDUSTRY_AFFILIATE
        - plan: Plan details (name, slug, limit, overage settings)
        - usage: Current month usage (report count, schedule run count)
        - decision: Current limit decision (ALLOW, ALLOW_WITH_WARNING, BLOCK)
        - info: Additional decision info (ratio, message, etc.)
    """
    
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Get basic account info
        cur.execute("""
            SELECT 
                id::text,
                name,
                slug,
                account_type,
                plan_slug,
                monthly_report_limit_override,
                sponsor_account_id::text,
                created_at
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        
        account_row = cur.fetchone()
        if not account_row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        account_info = {
            "id": account_row[0],
            "name": account_row[1],
            "slug": account_row[2],
            "account_type": account_row[3],
            "plan_slug": account_row[4],
            "monthly_report_limit_override": account_row[5],
            "sponsor_account_id": account_row[6],
            "created_at": account_row[7].isoformat() if account_row[7] else None,
        }
        
        # Get plan details
        plan = resolve_plan_for_account(cur, account_id)
        
        # Get current usage
        usage = get_monthly_usage(cur, account_id)
        
        # Evaluate current limit decision
        decision, info = evaluate_report_limit(cur, account_id)
        
        return {
            "account": account_info,
            "plan": plan,
            "usage": usage,
            "decision": decision.value,
            "info": {
                "ratio": info.get("ratio", 0),
                "message": info.get("message", ""),
                "can_proceed": info.get("can_proceed", True),
                "overage_count": info.get("overage_count", 0),
            }
        }


# ==================== Affiliates (Title Companies) ====================

@router.get("/affiliates")
def list_affiliates(
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    _admin: dict = Depends(get_admin_user)
):
    """
    List all affiliate (title company) accounts.

    Args:
        search: Search by company name
        limit: Maximum number of results

    Returns:
        Array of affiliate accounts with agent counts and metrics
    """
    query = """
        SELECT
            a.id::text,
            a.name,
            a.slug,
            a.plan_slug,
            a.is_active,
            a.created_at,
            ab.logo_url,
            ab.primary_color,
            ab.brand_display_name,
            (SELECT COUNT(*) FROM accounts sa WHERE sa.sponsor_account_id = a.id) as agent_count,
            (SELECT COUNT(*) FROM report_generations rg
             JOIN accounts sa ON rg.account_id = sa.id
             WHERE sa.sponsor_account_id = a.id
             AND rg.generated_at >= date_trunc('month', CURRENT_DATE)) as reports_this_month
        FROM accounts a
        LEFT JOIN affiliate_branding ab ON ab.account_id = a.id
        WHERE a.account_type = 'INDUSTRY_AFFILIATE'
    """
    params = []

    if search:
        query += " AND (a.name ILIKE %s OR a.slug ILIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])

    query += " ORDER BY a.created_at DESC LIMIT %s"
    params.append(limit)

    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        cur.execute(query, params)

        affiliates = []
        for row in cur.fetchall():
            affiliates.append({
                "account_id": row[0],
                "name": row[1],
                "slug": row[2],
                "plan_slug": row[3],
                "is_active": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "logo_url": row[6],
                "primary_color": row[7],
                "brand_display_name": row[8],
                "agent_count": row[9] or 0,
                "reports_this_month": row[10] or 0,
            })

        return {"affiliates": affiliates, "count": len(affiliates)}


@router.get("/affiliates/{affiliate_id}")
def get_affiliate_detail(
    affiliate_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """
    Get detailed information about a specific affiliate.

    Returns affiliate info, branding, and list of sponsored agents.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Get affiliate info
        cur.execute("""
            SELECT
                a.id::text,
                a.name,
                a.slug,
                a.account_type,
                a.plan_slug,
                a.is_active,
                a.created_at,
                ab.brand_display_name,
                ab.logo_url,
                ab.primary_color,
                ab.accent_color,
                ab.rep_photo_url,
                ab.contact_line1,
                ab.contact_line2,
                ab.website_url
            FROM accounts a
            LEFT JOIN affiliate_branding ab ON ab.account_id = a.id
            WHERE a.id = %s::uuid AND a.account_type = 'INDUSTRY_AFFILIATE'
        """, (affiliate_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Affiliate not found")

        affiliate = {
            "account_id": row[0],
            "name": row[1],
            "slug": row[2],
            "account_type": row[3],
            "plan_slug": row[4],
            "is_active": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "branding": {
                "brand_display_name": row[7],
                "logo_url": row[8],
                "primary_color": row[9],
                "accent_color": row[10],
                "rep_photo_url": row[11],
                "contact_line1": row[12],
                "contact_line2": row[13],
                "website_url": row[14],
            }
        }

        # Get admin user for this affiliate
        cur.execute("""
            SELECT u.id::text, u.email, u.first_name, u.last_name, u.is_active, u.created_at
            FROM users u
            JOIN account_users au ON au.user_id = u.id
            WHERE au.account_id = %s::uuid AND au.role = 'OWNER'
            LIMIT 1
        """, (affiliate_id,))

        admin_row = cur.fetchone()
        if admin_row:
            affiliate["admin_user"] = {
                "user_id": admin_row[0],
                "email": admin_row[1],
                "first_name": admin_row[2],
                "last_name": admin_row[3],
                "is_active": admin_row[4],
                "created_at": admin_row[5].isoformat() if admin_row[5] else None,
            }

        # Get sponsored agents
        cur.execute("""
            SELECT
                a.id::text,
                a.name,
                a.slug,
                a.plan_slug,
                a.is_active,
                a.created_at,
                u.email,
                u.first_name,
                u.last_name,
                u.avatar_url,
                (SELECT COUNT(*) FROM report_generations rg
                 WHERE rg.account_id = a.id
                 AND rg.generated_at >= date_trunc('month', CURRENT_DATE)) as reports_this_month,
                (SELECT MAX(rg.generated_at) FROM report_generations rg WHERE rg.account_id = a.id) as last_report_at
            FROM accounts a
            LEFT JOIN users u ON u.account_id = a.id
            WHERE a.sponsor_account_id = %s::uuid
            ORDER BY a.created_at DESC
        """, (affiliate_id,))

        agents = []
        for agent_row in cur.fetchall():
            agents.append({
                "account_id": agent_row[0],
                "name": agent_row[1],
                "slug": agent_row[2],
                "plan_slug": agent_row[3],
                "is_active": agent_row[4],
                "created_at": agent_row[5].isoformat() if agent_row[5] else None,
                "email": agent_row[6],
                "first_name": agent_row[7],
                "last_name": agent_row[8],
                "avatar_url": agent_row[9],
                "reports_this_month": agent_row[10] or 0,
                "last_report_at": agent_row[11].isoformat() if agent_row[11] else None,
            })

        affiliate["agents"] = agents
        affiliate["agent_count"] = len(agents)

        # Get metrics
        cur.execute("""
            SELECT COUNT(*) FROM report_generations rg
            JOIN accounts sa ON rg.account_id = sa.id
            WHERE sa.sponsor_account_id = %s::uuid
            AND rg.generated_at >= date_trunc('month', CURRENT_DATE)
        """, (affiliate_id,))
        affiliate["reports_this_month"] = cur.fetchone()[0] or 0

        return affiliate


class CreateAffiliateRequest(BaseModel):
    """Request body for creating a new affiliate."""
    company_name: str
    admin_email: EmailStr
    admin_first_name: Optional[str] = None
    admin_last_name: Optional[str] = None
    plan_slug: str = "affiliate"
    # Branding (optional)
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    website_url: Optional[str] = None


@router.post("/affiliates")
def create_affiliate(
    body: CreateAffiliateRequest,
    background_tasks: BackgroundTasks,
    _admin: dict = Depends(get_admin_user)
):
    """
    Create a new affiliate (title company) account.

    Creates:
    1. Account with INDUSTRY_AFFILIATE type
    2. Admin user for the affiliate
    3. Branding record (if branding provided)
    4. Sends welcome email

    Returns the new affiliate details.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (body.admin_email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # Generate slug
        slug = body.company_name.lower().replace(' ', '-').replace('.', '').replace(',', '')[:50]

        # Ensure slug is unique
        cur.execute("SELECT id FROM accounts WHERE slug = %s", (slug,))
        if cur.fetchone():
            import time
            slug = f"{slug}-{int(time.time())}"[:50]

        # Create account
        cur.execute("""
            INSERT INTO accounts (name, slug, account_type, plan_slug, is_active)
            VALUES (%s, %s, 'INDUSTRY_AFFILIATE', %s, true)
            RETURNING id::text
        """, (body.company_name, slug, body.plan_slug))
        account_id = cur.fetchone()[0]

        # Generate temporary password and hash it
        temp_password = secrets.token_urlsafe(12)

        # Create admin user (no password - will use invite flow)
        cur.execute("""
            INSERT INTO users (account_id, email, first_name, last_name, is_active, email_verified, role)
            VALUES (%s::uuid, %s, %s, %s, true, false, 'member')
            RETURNING id::text
        """, (account_id, body.admin_email, body.admin_first_name, body.admin_last_name))
        user_id = cur.fetchone()[0]

        # Create account_users entry (OWNER)
        cur.execute("""
            INSERT INTO account_users (account_id, user_id, role)
            VALUES (%s::uuid, %s::uuid, 'OWNER')
        """, (account_id, user_id))

        # Create branding record if any branding provided
        if body.logo_url or body.primary_color:
            cur.execute("""
                INSERT INTO affiliate_branding (
                    account_id, brand_display_name, logo_url, primary_color, accent_color, website_url
                ) VALUES (%s::uuid, %s, %s, %s, %s, %s)
            """, (
                account_id, body.company_name, body.logo_url,
                body.primary_color or '#7C3AED', body.accent_color, body.website_url
            ))

        # Generate invite token for password setup
        token = secrets.token_urlsafe(32)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS signup_tokens (
                id SERIAL PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                user_id UUID NOT NULL REFERENCES users(id),
                account_id UUID NOT NULL REFERENCES accounts(id),
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
            )
        """)

        cur.execute("""
            INSERT INTO signup_tokens (token, user_id, account_id)
            VALUES (%s, %s::uuid, %s::uuid)
        """, (token, user_id, account_id))

        conn.commit()

        # Send welcome/invite email
        try:
            background_tasks.add_task(
                send_invite_email,
                body.admin_email,
                "TrendyReports Admin",
                body.company_name,
                token
            )
            logger.info(f"Affiliate welcome email queued for {body.admin_email}")
        except Exception as e:
            logger.error(f"Failed to queue affiliate welcome email: {e}")

        return {
            "ok": True,
            "account_id": account_id,
            "user_id": user_id,
            "name": body.company_name,
            "slug": slug,
            "admin_email": body.admin_email,
            "invite_url": f"https://reportscompany-web.vercel.app/welcome?token={token}",
        }


class InviteAgentAdminRequest(BaseModel):
    """Request body for inviting an agent from admin."""
    affiliate_id: str
    agent_name: str
    agent_email: EmailStr


@router.post("/affiliates/{affiliate_id}/invite-agent")
def admin_invite_agent(
    affiliate_id: str,
    body: InviteAgentAdminRequest,
    background_tasks: BackgroundTasks,
    _admin: dict = Depends(get_admin_user)
):
    """
    Invite a new agent to be sponsored by an affiliate (admin action).

    Similar to the affiliate's own invite, but done by admin.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Verify affiliate exists
        cur.execute("""
            SELECT name FROM accounts
            WHERE id = %s::uuid AND account_type = 'INDUSTRY_AFFILIATE'
        """, (affiliate_id,))
        affiliate_row = cur.fetchone()
        if not affiliate_row:
            raise HTTPException(status_code=404, detail="Affiliate not found")

        company_name = affiliate_row[0]

        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (body.agent_email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")

        # Generate slug
        slug = body.agent_name.lower().replace(' ', '-').replace('.', '').replace(',', '')[:50]

        cur.execute("SELECT id FROM accounts WHERE slug = %s", (slug,))
        if cur.fetchone():
            import time
            slug = f"{slug}-{int(time.time())}"[:50]

        # Create agent account
        cur.execute("""
            INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id)
            VALUES (%s, %s, 'REGULAR', 'sponsored_free', %s::uuid)
            RETURNING id::text
        """, (body.agent_name, slug, affiliate_id))
        new_account_id = cur.fetchone()[0]

        # Create user
        cur.execute("""
            INSERT INTO users (account_id, email, is_active, email_verified, role)
            VALUES (%s::uuid, %s, true, false, 'member')
            RETURNING id::text
        """, (new_account_id, body.agent_email))
        new_user_id = cur.fetchone()[0]

        # Create account_users entry
        cur.execute("""
            INSERT INTO account_users (account_id, user_id, role)
            VALUES (%s::uuid, %s::uuid, 'OWNER')
        """, (new_account_id, new_user_id))

        # Generate invite token
        token = secrets.token_urlsafe(32)

        cur.execute("""
            INSERT INTO signup_tokens (token, user_id, account_id)
            VALUES (%s, %s::uuid, %s::uuid)
        """, (token, new_user_id, new_account_id))

        conn.commit()

        # Send invite email
        try:
            background_tasks.add_task(
                send_invite_email,
                body.agent_email,
                "TrendyReports Admin",
                company_name,
                token
            )
            logger.info(f"Agent invite email queued for {body.agent_email}")
        except Exception as e:
            logger.error(f"Failed to queue agent invite email: {e}")

        return {
            "ok": True,
            "account_id": new_account_id,
            "user_id": new_user_id,
            "name": body.agent_name,
            "email": body.agent_email,
            "affiliate_id": affiliate_id,
            "affiliate_name": company_name,
            "invite_url": f"https://reportscompany-web.vercel.app/welcome?token={token}",
        }


@router.patch("/affiliates/{affiliate_id}")
def update_affiliate(
    affiliate_id: str,
    is_active: Optional[bool] = None,
    plan_slug: Optional[str] = None,
    _admin: dict = Depends(get_admin_user)
):
    """
    Update an affiliate's status or plan.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        updates = []
        params = []

        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if plan_slug is not None:
            updates.append("plan_slug = %s")
            params.append(plan_slug)

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        params.append(affiliate_id)

        cur.execute(f"""
            UPDATE accounts
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = %s::uuid AND account_type = 'INDUSTRY_AFFILIATE'
            RETURNING id::text, name, is_active, plan_slug
        """, params)

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Affiliate not found")

        conn.commit()

        return {
            "ok": True,
            "account_id": row[0],
            "name": row[1],
            "is_active": row[2],
            "plan_slug": row[3],
        }


# ==================== Accounts ====================

@router.get("/accounts")
def list_accounts(
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    plan_slug: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(get_admin_user)
):
    """
    List all accounts with filters.

    Args:
        search: Search by name or slug
        account_type: Filter by type (REGULAR, INDUSTRY_AFFILIATE)
        plan_slug: Filter by plan
        is_active: Filter by active status
        limit: Maximum results
        offset: Pagination offset

    Returns:
        Array of accounts with usage metrics
    """
    query = """
        SELECT
            a.id::text,
            a.name,
            a.slug,
            a.account_type,
            a.plan_slug,
            a.is_active,
            a.sponsor_account_id::text,
            sa.name as sponsor_name,
            a.created_at,
            (SELECT COUNT(*) FROM users u WHERE u.account_id = a.id) as user_count,
            (SELECT COUNT(*) FROM report_generations rg
             WHERE rg.account_id = a.id
             AND rg.generated_at >= date_trunc('month', CURRENT_DATE)) as reports_this_month
        FROM accounts a
        LEFT JOIN accounts sa ON sa.id = a.sponsor_account_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (a.name ILIKE %s OR a.slug ILIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])

    if account_type:
        query += " AND a.account_type = %s"
        params.append(account_type)

    if plan_slug:
        query += " AND a.plan_slug = %s"
        params.append(plan_slug)

    if is_active is not None:
        query += " AND a.is_active = %s"
        params.append(is_active)

    # Get total count
    count_query = query.replace(
        "SELECT \n            a.id::text,",
        "SELECT COUNT(*) FROM (SELECT a.id"
    ).split("FROM accounts a")[0] + "FROM accounts a" + query.split("FROM accounts a")[1]

    query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        cur.execute(query, params)

        accounts = []
        for row in cur.fetchall():
            accounts.append({
                "account_id": row[0],
                "name": row[1],
                "slug": row[2],
                "account_type": row[3],
                "plan_slug": row[4],
                "is_active": row[5],
                "sponsor_account_id": row[6],
                "sponsor_name": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "user_count": row[9] or 0,
                "reports_this_month": row[10] or 0,
            })

        # Get total
        cur.execute("SELECT COUNT(*) FROM accounts")
        total = cur.fetchone()[0]

        return {
            "accounts": accounts,
            "count": len(accounts),
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.patch("/accounts/{account_id}")
def update_account(
    account_id: str,
    is_active: Optional[bool] = None,
    plan_slug: Optional[str] = None,
    monthly_report_limit_override: Optional[int] = None,
    _admin: dict = Depends(get_admin_user)
):
    """
    Update an account's status, plan, or limits.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        updates = []
        params = []

        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if plan_slug is not None:
            updates.append("plan_slug = %s")
            params.append(plan_slug)

        if monthly_report_limit_override is not None:
            updates.append("monthly_report_limit_override = %s")
            params.append(monthly_report_limit_override if monthly_report_limit_override > 0 else None)

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        params.append(account_id)

        cur.execute(f"""
            UPDATE accounts
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = %s::uuid
            RETURNING id::text, name, account_type, is_active, plan_slug, monthly_report_limit_override
        """, params)

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")

        conn.commit()

        return {
            "ok": True,
            "account_id": row[0],
            "name": row[1],
            "account_type": row[2],
            "is_active": row[3],
            "plan_slug": row[4],
            "monthly_report_limit_override": row[5],
        }


# ==================== Users ====================

@router.get("/users")
def list_users(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(get_admin_user)
):
    """
    List all users with filters.

    Args:
        search: Search by email, first name, or last name
        is_active: Filter by active status
        role: Filter by role
        limit: Maximum results
        offset: Pagination offset

    Returns:
        Array of users with account info
    """
    query = """
        SELECT
            u.id::text,
            u.email,
            u.first_name,
            u.last_name,
            u.is_active,
            u.email_verified,
            u.created_at,
            a.id::text as account_id,
            a.name as account_name,
            a.account_type,
            au.role,
            u.is_platform_admin
        FROM users u
        LEFT JOIN accounts a ON a.id = u.account_id
        LEFT JOIN account_users au ON au.user_id = u.id AND au.account_id = a.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (u.email ILIKE %s OR u.first_name ILIKE %s OR u.last_name ILIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    if is_active is not None:
        query += " AND u.is_active = %s"
        params.append(is_active)

    if role:
        query += " AND au.role = %s"
        params.append(role)

    query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        cur.execute(query, params)

        users = []
        for row in cur.fetchall():
            users.append({
                "user_id": row[0],
                "email": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "is_active": row[4],
                "email_verified": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "account_id": row[7],
                "account_name": row[8],
                "account_type": row[9],
                "role": row[10],  # Tenant role from account_users
                "is_platform_admin": bool(row[11]) if row[11] is not None else False,
            })

        # Get total
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]

        return {
            "users": users,
            "count": len(users),
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """
    Get detailed information about a specific user.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        cur.execute("""
            SELECT
                u.id::text,
                u.email,
                u.first_name,
                u.last_name,
                u.company_name,
                u.phone,
                u.avatar_url,
                u.is_active,
                u.email_verified,
                u.created_at,
                a.id::text as account_id,
                a.name as account_name,
                a.account_type,
                a.plan_slug,
                au.role
            FROM users u
            LEFT JOIN accounts a ON a.id = u.account_id
            LEFT JOIN account_users au ON au.user_id = u.id AND au.account_id = a.id
            WHERE u.id = %s::uuid
        """, (user_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        user = {
            "user_id": row[0],
            "email": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "company_name": row[4],
            "phone": row[5],
            "avatar_url": row[6],
            "is_active": row[7],
            "email_verified": row[8],
            "created_at": row[9].isoformat() if row[9] else None,
            "account": {
                "account_id": row[10],
                "name": row[11],
                "account_type": row[12],
                "plan_slug": row[13],
            },
            "role": row[14],
        }

        # Get user's report count
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE account_id = (SELECT account_id FROM users WHERE id = %s::uuid)
        """, (user_id,))
        user["total_reports"] = cur.fetchone()[0] or 0

        return user


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    is_active: Optional[bool] = None,
    email_verified: Optional[bool] = None,
    is_platform_admin: Optional[bool] = None,
    _admin: dict = Depends(get_admin_user)
):
    """
    Update a user's status.
    
    Args:
        user_id: User UUID
        is_active: Activate/deactivate user
        email_verified: Mark email as verified
        is_platform_admin: Grant/revoke platform admin access (DANGEROUS)
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        updates = []
        params = []

        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if email_verified is not None:
            updates.append("email_verified = %s")
            params.append(email_verified)
        
        if is_platform_admin is not None:
            updates.append("is_platform_admin = %s")
            params.append(is_platform_admin)
            logger.warning(f"Platform admin {'granted to' if is_platform_admin else 'revoked from'} user {user_id} by admin {_admin.get('email')}")

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        params.append(user_id)

        cur.execute(f"""
            UPDATE users
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = %s::uuid
            RETURNING id::text, email, is_active, email_verified, is_platform_admin
        """, params)

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        conn.commit()

        return {
            "ok": True,
            "user_id": row[0],
            "email": row[1],
            "is_active": row[2],
            "email_verified": row[3],
            "is_platform_admin": row[4],
        }


class BulkAgentImportRequest(BaseModel):
    """Request body for bulk agent import."""
    affiliate_id: str
    agents: List[Dict[str, Any]]  # List of {email, first_name, last_name, name}


class BulkAgentResult(BaseModel):
    """Result for a single agent in bulk import."""
    email: str
    success: bool
    account_id: Optional[str] = None
    user_id: Optional[str] = None
    error: Optional[str] = None


@router.post("/affiliates/{affiliate_id}/bulk-import")
def bulk_import_agents(
    affiliate_id: str,
    body: BulkAgentImportRequest,
    background_tasks: BackgroundTasks,
    _admin: dict = Depends(get_admin_user)
):
    """
    Bulk import agents for an affiliate from CSV data.

    Creates accounts and users for each agent, sends invite emails.
    Used for full-service title company onboarding where admin does everything.

    Args:
        affiliate_id: The affiliate account ID to sponsor these agents
        body: Contains list of agents with email, first_name, last_name, name

    Returns:
        Summary of results with success/failure for each agent
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Verify affiliate exists
        cur.execute("""
            SELECT name FROM accounts
            WHERE id = %s::uuid AND account_type = 'INDUSTRY_AFFILIATE'
        """, (affiliate_id,))
        affiliate_row = cur.fetchone()
        if not affiliate_row:
            raise HTTPException(status_code=404, detail="Affiliate not found")

        company_name = affiliate_row[0]

        results = []
        success_count = 0
        error_count = 0

        for agent_data in body.agents:
            email = agent_data.get("email", "").strip().lower()
            first_name = agent_data.get("first_name", "").strip() or None
            last_name = agent_data.get("last_name", "").strip() or None
            name = agent_data.get("name", "").strip()

            # Generate name if not provided
            if not name:
                if first_name and last_name:
                    name = f"{first_name} {last_name}"
                elif first_name:
                    name = first_name
                elif email:
                    name = email.split("@")[0].replace(".", " ").title()
                else:
                    results.append({
                        "email": email or "unknown",
                        "success": False,
                        "error": "No email provided"
                    })
                    error_count += 1
                    continue

            if not email:
                results.append({
                    "email": "unknown",
                    "success": False,
                    "error": "No email provided"
                })
                error_count += 1
                continue

            try:
                # Check if email already exists
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    results.append({
                        "email": email,
                        "success": False,
                        "error": "Email already exists"
                    })
                    error_count += 1
                    continue

                # Generate slug
                slug = name.lower().replace(' ', '-').replace('.', '').replace(',', '')[:50]

                cur.execute("SELECT id FROM accounts WHERE slug = %s", (slug,))
                if cur.fetchone():
                    import time
                    slug = f"{slug}-{int(time.time())}"[:50]

                # Create agent account
                cur.execute("""
                    INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id)
                    VALUES (%s, %s, 'REGULAR', 'sponsored_free', %s::uuid)
                    RETURNING id::text
                """, (name, slug, affiliate_id))
                new_account_id = cur.fetchone()[0]

                # Create user
                cur.execute("""
                    INSERT INTO users (account_id, email, first_name, last_name, is_active, email_verified, role)
                    VALUES (%s::uuid, %s, %s, %s, true, false, 'member')
                    RETURNING id::text
                """, (new_account_id, email, first_name, last_name))
                new_user_id = cur.fetchone()[0]

                # Create account_users entry
                cur.execute("""
                    INSERT INTO account_users (account_id, user_id, role)
                    VALUES (%s::uuid, %s::uuid, 'OWNER')
                """, (new_account_id, new_user_id))

                # Generate invite token
                token = secrets.token_urlsafe(32)

                cur.execute("""
                    INSERT INTO signup_tokens (token, user_id, account_id)
                    VALUES (%s, %s::uuid, %s::uuid)
                """, (token, new_user_id, new_account_id))

                # Queue invite email
                try:
                    background_tasks.add_task(
                        send_invite_email,
                        email,
                        "TrendyReports Admin",
                        company_name,
                        token
                    )
                except Exception as e:
                    logger.error(f"Failed to queue invite email for {email}: {e}")

                results.append({
                    "email": email,
                    "success": True,
                    "account_id": new_account_id,
                    "user_id": new_user_id,
                })
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to create agent {email}: {e}")
                results.append({
                    "email": email,
                    "success": False,
                    "error": str(e)
                })
                error_count += 1

        conn.commit()

        return {
            "ok": True,
            "affiliate_id": affiliate_id,
            "affiliate_name": company_name,
            "total": len(body.agents),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
        }


class UpdateAgentHeadshotRequest(BaseModel):
    """Request to update an agent's headshot."""
    headshot_url: str


@router.patch("/agents/{account_id}/headshot")
def update_agent_headshot(
    account_id: str,
    body: UpdateAgentHeadshotRequest,
    _admin: dict = Depends(get_admin_user)
):
    """
    Update an agent's headshot from admin.

    Used for full-service onboarding where admin uploads headshots for agents.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Verify account exists and is a regular account (agent)
        cur.execute("""
            SELECT a.id, u.id as user_id
            FROM accounts a
            JOIN users u ON u.account_id = a.id
            WHERE a.id = %s::uuid AND a.account_type = 'REGULAR'
            LIMIT 1
        """, (account_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agent account not found")

        user_id = row[1]

        # Update user's avatar
        cur.execute("""
            UPDATE users
            SET avatar_url = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id::text, email, avatar_url
        """, (body.headshot_url, user_id))

        updated = cur.fetchone()
        conn.commit()

        return {
            "ok": True,
            "account_id": account_id,
            "user_id": str(updated[0]),
            "email": updated[1],
            "headshot_url": updated[2],
        }


class ResendInviteRequest(BaseModel):
    """Request to resend an invite email."""
    pass


@router.post("/users/{user_id}/resend-invite")
def resend_user_invite(
    user_id: str,
    background_tasks: BackgroundTasks,
    _admin: dict = Depends(get_admin_user)
):
    """
    Resend invite email to a user who hasn't set up their password yet.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Get user info
        cur.execute("""
            SELECT u.email, u.email_verified, a.name as account_name, a.sponsor_account_id
            FROM users u
            JOIN accounts a ON a.id = u.account_id
            WHERE u.id = %s::uuid
        """, (user_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        email, email_verified, account_name, sponsor_id = row

        if email_verified:
            raise HTTPException(status_code=400, detail="User already verified")

        # Get sponsor name if sponsored
        company_name = account_name
        if sponsor_id:
            cur.execute("SELECT name FROM accounts WHERE id = %s", (sponsor_id,))
            sponsor_row = cur.fetchone()
            if sponsor_row:
                company_name = sponsor_row[0]

        # Generate new token
        token = secrets.token_urlsafe(32)

        # Delete old tokens and create new one
        cur.execute("""
            DELETE FROM signup_tokens WHERE user_id = %s::uuid
        """, (user_id,))

        cur.execute("""
            SELECT account_id FROM users WHERE id = %s::uuid
        """, (user_id,))
        account_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO signup_tokens (token, user_id, account_id)
            VALUES (%s, %s::uuid, %s)
        """, (token, user_id, account_id))

        conn.commit()

        # Send invite email
        try:
            background_tasks.add_task(
                send_invite_email,
                email,
                "TrendyReports Admin",
                company_name,
                token
            )
            logger.info(f"Resent invite email to {email}")
        except Exception as e:
            logger.error(f"Failed to resend invite: {e}")
            raise HTTPException(status_code=500, detail="Failed to send email")

        return {
            "ok": True,
            "email": email,
            "invite_url": f"https://reportscompany-web.vercel.app/welcome?token={token}",
        }


# ==================== Plans Management ====================

@router.get("/plans")
def list_plans(_admin: dict = Depends(get_admin_user)):
    """
    List all subscription plans with their limits and pricing.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        cur.execute("""
            SELECT
                plan_slug,
                plan_name,
                monthly_report_limit,
                allow_overage,
                overage_price_cents,
                stripe_price_id,
                description,
                is_active,
                created_at,
                updated_at,
                (SELECT COUNT(*) FROM accounts WHERE plan_slug = plans.plan_slug) as account_count
            FROM plans
            ORDER BY monthly_report_limit ASC
        """)

        plans = []
        for row in cur.fetchall():
            plans.append({
                "plan_slug": row[0],
                "plan_name": row[1],
                "monthly_report_limit": row[2],
                "allow_overage": row[3],
                "overage_price_cents": row[4],
                "stripe_price_id": row[5],
                "description": row[6],
                "is_active": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "updated_at": row[9].isoformat() if row[9] else None,
                "account_count": row[10] or 0,
            })

        return {"plans": plans, "count": len(plans)}


class UpdatePlanRequest(BaseModel):
    """Request body for updating a plan."""
    plan_name: Optional[str] = None
    monthly_report_limit: Optional[int] = None
    allow_overage: Optional[bool] = None
    overage_price_cents: Optional[int] = None
    stripe_price_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.patch("/plans/{plan_slug}")
def update_plan(
    plan_slug: str,
    body: UpdatePlanRequest,
    _admin: dict = Depends(get_admin_user)
):
    """
    Update a plan's settings.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        updates = []
        params = []

        if body.plan_name is not None:
            updates.append("plan_name = %s")
            params.append(body.plan_name)

        if body.monthly_report_limit is not None:
            updates.append("monthly_report_limit = %s")
            params.append(body.monthly_report_limit)

        if body.allow_overage is not None:
            updates.append("allow_overage = %s")
            params.append(body.allow_overage)

        if body.overage_price_cents is not None:
            updates.append("overage_price_cents = %s")
            params.append(body.overage_price_cents)

        if body.stripe_price_id is not None:
            updates.append("stripe_price_id = %s")
            params.append(body.stripe_price_id if body.stripe_price_id else None)

        if body.description is not None:
            updates.append("description = %s")
            params.append(body.description if body.description else None)

        if body.is_active is not None:
            updates.append("is_active = %s")
            params.append(body.is_active)

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        updates.append("updated_at = NOW()")
        params.append(plan_slug)

        cur.execute(f"""
            UPDATE plans
            SET {', '.join(updates)}
            WHERE plan_slug = %s
            RETURNING plan_slug, plan_name, monthly_report_limit, allow_overage, overage_price_cents, is_active
        """, params)

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plan not found")

        conn.commit()

        return {
            "ok": True,
            "plan_slug": row[0],
            "plan_name": row[1],
            "monthly_report_limit": row[2],
            "allow_overage": row[3],
            "overage_price_cents": row[4],
            "is_active": row[5],
        }


class CreatePlanRequest(BaseModel):
    """Request body for creating a new plan."""
    plan_slug: str
    plan_name: str
    monthly_report_limit: int
    allow_overage: bool = False
    overage_price_cents: int = 0
    stripe_price_id: Optional[str] = None
    description: Optional[str] = None


@router.post("/plans")
def create_plan(
    body: CreatePlanRequest,
    _admin: dict = Depends(get_admin_user)
):
    """
    Create a new subscription plan.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Check if slug already exists
        cur.execute("SELECT id FROM plans WHERE plan_slug = %s", (body.plan_slug,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Plan slug already exists")

        cur.execute("""
            INSERT INTO plans (
                plan_slug, plan_name, monthly_report_limit,
                allow_overage, overage_price_cents, stripe_price_id, description
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING plan_slug, plan_name, monthly_report_limit
        """, (
            body.plan_slug,
            body.plan_name,
            body.monthly_report_limit,
            body.allow_overage,
            body.overage_price_cents,
            body.stripe_price_id,
            body.description,
        ))

        row = cur.fetchone()
        conn.commit()

        return {
            "ok": True,
            "plan_slug": row[0],
            "plan_name": row[1],
            "monthly_report_limit": row[2],
        }


# ==================== Manual Actions ====================

class TriggerReportRequest(BaseModel):
    """Request body for manually triggering a report."""
    report_type: str
    city: Optional[str] = None
    zip_codes: Optional[List[str]] = None
    recipients: Optional[List[str]] = None


@router.post("/accounts/{account_id}/trigger-report")
def trigger_report_for_account(
    account_id: str,
    body: TriggerReportRequest,
    _admin: dict = Depends(get_admin_user)
):
    """
    Manually trigger a report generation for any account.
    
    This bypasses normal limits and schedules, useful for:
    - Testing reports for a customer
    - Regenerating failed reports
    - Customer support requests
    
    Args:
        account_id: Target account UUID
        body: Report parameters
    
    Returns:
        Report generation ID and status
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Verify account exists
        cur.execute("SELECT id, name FROM accounts WHERE id = %s::uuid", (account_id,))
        account_row = cur.fetchone()
        if not account_row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        account_name = account_row[1]
        
        # Create report generation record
        import uuid
        run_id = str(uuid.uuid4())
        
        input_params = {
            "report_type": body.report_type,
            "city": body.city,
            "zip_codes": body.zip_codes or [],
            "triggered_by_admin": _admin.get("email"),
        }
        
        cur.execute("""
            INSERT INTO report_generations (
                id, account_id, report_type, status, input_params, generated_at
            ) VALUES (
                %s::uuid, %s::uuid, %s, 'pending', %s, NOW()
            )
            RETURNING id::text
        """, (run_id, account_id, body.report_type, str(input_params).replace("'", '"')))
        
        conn.commit()
        
        logger.info(f"Admin {_admin.get('email')} triggered {body.report_type} report for account {account_name}")
        
        # Note: The actual report generation would be enqueued here
        # For now we just create the record - the worker will pick it up
        # or we can call enqueue_generate_report if available
        
        return {
            "ok": True,
            "run_id": run_id,
            "account_id": account_id,
            "account_name": account_name,
            "report_type": body.report_type,
            "status": "pending",
            "message": "Report generation queued. Check /admin/reports for status.",
        }


@router.post("/users/{user_id}/force-password-reset")
def force_password_reset(
    user_id: str,
    background_tasks: BackgroundTasks,
    _admin: dict = Depends(get_admin_user)
):
    """
    Force send a password reset email to any user.
    
    Useful for:
    - Users who can't access their email
    - Locked out accounts
    - Security concerns
    
    Args:
        user_id: Target user UUID
    
    Returns:
        Success message
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Get user info
        cur.execute("SELECT email, first_name FROM users WHERE id = %s::uuid", (user_id,))
        user_row = cur.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        
        email, first_name = user_row
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        
        # Delete any existing tokens
        cur.execute("DELETE FROM password_reset_tokens WHERE user_id = %s::uuid", (user_id,))
        
        # Create new token
        cur.execute("""
            INSERT INTO password_reset_tokens (user_id, token, expires_at)
            VALUES (%s::uuid, %s, NOW() + INTERVAL '24 hours')
        """, (user_id, token))
        
        conn.commit()
        
        # Send reset email
        from ..services.email import send_password_reset_email
        try:
            background_tasks.add_task(send_password_reset_email, email, token, first_name)
            logger.info(f"Admin {_admin.get('email')} force sent password reset to {email}")
        except Exception as e:
            logger.error(f"Failed to queue password reset email: {e}")
            raise HTTPException(status_code=500, detail="Failed to send email")
        
        return {
            "ok": True,
            "user_id": user_id,
            "email": email,
            "message": "Password reset email sent. Token expires in 24 hours.",
            "reset_url": f"https://reportscompany-web.vercel.app/reset-password?token={token}",
        }


# ==================== System Health ====================

@router.get("/system/health")
def get_system_health(_admin: dict = Depends(get_admin_user)):
    """
    Get system health status including database, Redis, and worker status.
    
    Returns:
        - database: Connection status and basic stats
        - redis: Connection status (if available)
        - worker: Recent task stats
        - system: General system info
    """
    import os
    from datetime import datetime
    
    health = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "worker": {"status": "unknown"},
        "system": {},
    }
    
    # Database health
    try:
        with db_conn() as (conn, cur):
            set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
            
            # Test query
            cur.execute("SELECT 1")
            health["database"]["status"] = "healthy"
            
            # Get DB size
            cur.execute("""
                SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb
            """)
            health["database"]["size_mb"] = round(cur.fetchone()[0], 2)
            
            # Get table counts
            cur.execute("SELECT COUNT(*) FROM users")
            health["database"]["users"] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM accounts")
            health["database"]["accounts"] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM report_generations WHERE generated_at >= NOW() - INTERVAL '24 hours'")
            health["database"]["reports_24h"] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM schedules WHERE active = true")
            health["database"]["active_schedules"] = cur.fetchone()[0]
            
            # Recent failures
            cur.execute("""
                SELECT COUNT(*) FROM report_generations 
                WHERE status = 'failed' 
                AND generated_at >= NOW() - INTERVAL '1 hour'
            """)
            health["database"]["recent_failures"] = cur.fetchone()[0]
            
    except Exception as e:
        health["database"]["status"] = "unhealthy"
        health["database"]["error"] = str(e)
    
    # Redis health (try to connect)
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        health["redis"]["status"] = "healthy"
        
        # Get queue depth
        try:
            queue_len = r.llen("celery")
            health["redis"]["queue_depth"] = queue_len
        except:
            health["redis"]["queue_depth"] = 0
            
    except ImportError:
        health["redis"]["status"] = "not_available"
        health["redis"]["message"] = "Redis client not installed"
    except Exception as e:
        health["redis"]["status"] = "unhealthy"
        health["redis"]["error"] = str(e)
    
    # Worker status (check recent activity)
    try:
        with db_conn() as (conn, cur):
            set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
            
            # Check for recent completed reports (indicates worker is processing)
            cur.execute("""
                SELECT COUNT(*) FROM report_generations
                WHERE status = 'completed'
                AND generated_at >= NOW() - INTERVAL '10 minutes'
            """)
            recent_completed = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM report_generations
                WHERE status = 'processing'
            """)
            currently_processing = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM report_generations
                WHERE status = 'pending'
            """)
            pending = cur.fetchone()[0]
            
            health["worker"]["recent_completed_10m"] = recent_completed
            health["worker"]["currently_processing"] = currently_processing
            health["worker"]["pending"] = pending
            
            if recent_completed > 0 or currently_processing > 0:
                health["worker"]["status"] = "active"
            elif pending > 0:
                health["worker"]["status"] = "idle_with_pending"
            else:
                health["worker"]["status"] = "idle"
                
    except Exception as e:
        health["worker"]["status"] = "unknown"
        health["worker"]["error"] = str(e)
    
    # System info
    health["system"]["environment"] = os.getenv("ENVIRONMENT", "production")
    health["system"]["api_base"] = os.getenv("NEXT_PUBLIC_API_BASE", "unknown")
    
    return health


# ==================== System Stats ====================

@router.get("/stats/revenue")
def get_revenue_stats(_admin: dict = Depends(get_admin_user)):
    """
    Get revenue and billing statistics.
    """
    with db_conn() as (conn, cur):
        # Set admin role for RLS bypass
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")

        # Accounts by plan
        cur.execute("""
            SELECT plan_slug, COUNT(*) as count
            FROM accounts
            GROUP BY plan_slug
            ORDER BY count DESC
        """)
        accounts_by_plan = [
            {"plan": row[0], "count": row[1]}
            for row in cur.fetchall()
        ]

        # Reports by status this month
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM report_generations
            WHERE generated_at >= date_trunc('month', CURRENT_DATE)
            GROUP BY status
        """)
        reports_by_status = [
            {"status": row[0], "count": row[1]}
            for row in cur.fetchall()
        ]

        # Growth metrics (new accounts per month, last 6 months)
        cur.execute("""
            SELECT
                date_trunc('month', created_at) as month,
                COUNT(*) as new_accounts
            FROM accounts
            WHERE created_at >= NOW() - INTERVAL '6 months'
            GROUP BY date_trunc('month', created_at)
            ORDER BY month DESC
        """)
        growth = [
            {"month": row[0].strftime("%Y-%m"), "new_accounts": row[1]}
            for row in cur.fetchall()
        ]

        return {
            "accounts_by_plan": accounts_by_plan,
            "reports_by_status": reports_by_status,
            "growth": growth,
        }


# ==================== Property Reports Admin ====================

@router.get("/property-reports")
def list_admin_property_reports(
    status: Optional[str] = None,
    account: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    _admin: dict = Depends(get_admin_user)
):
    """
    List all property reports across all accounts.
    
    Args:
        status: Filter by status (draft, processing, complete, failed)
        account: Filter by account name (partial match)
        from_date: Filter by created date (YYYY-MM-DD)
        to_date: Filter by created date (YYYY-MM-DD)
        limit: Maximum number of results
    
    Returns:
        Array of property reports with account and user info
    """
    query = """
        SELECT 
            pr.id::text,
            pr.account_id::text,
            a.name as account_name,
            u.email as user_email,
            pr.report_type,
            pr.status,
            pr.property_address,
            pr.property_city,
            pr.property_state,
            pr.short_code,
            pr.pdf_url,
            pr.view_count,
            pr.created_at
        FROM property_reports pr
        JOIN accounts a ON pr.account_id = a.id
        LEFT JOIN users u ON pr.user_id = u.id
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND pr.status = %s"
        params.append(status)
    
    if account:
        query += " AND a.name ILIKE %s"
        params.append(f"%{account}%")
    
    if from_date:
        query += " AND pr.created_at >= %s"
        params.append(from_date)
    
    if to_date:
        query += " AND pr.created_at <= %s"
        params.append(to_date)
    
    query += " ORDER BY pr.created_at DESC LIMIT %s"
    params.append(limit)
    
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        cur.execute(query, params)
        
        reports = []
        for row in cur.fetchall():
            reports.append({
                "id": row[0],
                "account_id": row[1],
                "account_name": row[2],
                "user_email": row[3],
                "report_type": row[4],
                "status": row[5],
                "property_address": row[6],
                "property_city": row[7],
                "property_state": row[8],
                "short_code": row[9],
                "pdf_url": row[10],
                "view_count": row[11],
                "created_at": row[12].isoformat() if row[12] else None,
            })
        
        return {"reports": reports, "count": len(reports)}


@router.get("/property-reports/{report_id}")
def get_admin_property_report(
    report_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """
    Get detailed property report information including associated leads.
    """
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            SELECT 
                pr.id::text,
                pr.account_id::text,
                a.name as account_name,
                pr.user_id::text,
                u.email as user_email,
                COALESCE(u.first_name || ' ' || u.last_name, u.email) as user_name,
                pr.report_type,
                pr.status,
                pr.theme,
                pr.accent_color,
                pr.language,
                pr.property_address,
                pr.property_city,
                pr.property_state,
                pr.property_zip,
                pr.property_county,
                pr.apn,
                pr.owner_name,
                pr.legal_description,
                pr.property_type,
                pr.sitex_data,
                pr.comparables,
                pr.short_code,
                pr.qr_code_url,
                pr.pdf_url,
                pr.view_count,
                pr.unique_visitors,
                pr.last_viewed_at,
                pr.is_active,
                pr.expires_at,
                pr.max_leads,
                pr.access_code,
                pr.created_at,
                pr.updated_at
            FROM property_reports pr
            JOIN accounts a ON pr.account_id = a.id
            LEFT JOIN users u ON pr.user_id = u.id
            WHERE pr.id = %s::uuid
        """, (report_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Property report not found")
        
        report = {
            "id": row[0],
            "account_id": row[1],
            "account_name": row[2],
            "user_id": row[3],
            "user_email": row[4],
            "user_name": row[5],
            "report_type": row[6],
            "status": row[7],
            "theme": row[8],
            "accent_color": row[9],
            "language": row[10],
            "property_address": row[11],
            "property_city": row[12],
            "property_state": row[13],
            "property_zip": row[14],
            "property_county": row[15],
            "apn": row[16],
            "owner_name": row[17],
            "legal_description": row[18],
            "property_type": row[19],
            "sitex_data": row[20],
            "comparables": row[21],
            "short_code": row[22],
            "qr_code_url": row[23],
            "pdf_url": row[24],
            "view_count": row[25],
            "unique_visitors": row[26],
            "last_viewed_at": row[27].isoformat() if row[27] else None,
            "is_active": row[28],
            "expires_at": row[29].isoformat() if row[29] else None,
            "max_leads": row[30],
            "access_code": row[31],
            "created_at": row[32].isoformat() if row[32] else None,
            "updated_at": row[33].isoformat() if row[33] else None,
        }
        
        # Get associated leads
        cur.execute("""
            SELECT 
                id::text,
                name,
                email,
                phone,
                status,
                source,
                created_at
            FROM leads
            WHERE property_report_id = %s::uuid
            ORDER BY created_at DESC
        """, (report_id,))
        
        leads = []
        for lead_row in cur.fetchall():
            leads.append({
                "id": lead_row[0],
                "name": lead_row[1],
                "email": lead_row[2],
                "phone": lead_row[3],
                "status": lead_row[4],
                "source": lead_row[5],
                "created_at": lead_row[6].isoformat() if lead_row[6] else None,
            })
        
        report["leads"] = leads
        return report


@router.delete("/property-reports/{report_id}")
def delete_admin_property_report(
    report_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """Delete a property report (admin action)."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            DELETE FROM property_reports
            WHERE id = %s::uuid
            RETURNING id::text
        """, (report_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Property report not found")
        
        conn.commit()
        logger.info(f"Admin {_admin.get('email')} deleted property report {report_id}")
        
        return {"ok": True, "deleted_id": row[0]}


@router.post("/property-reports/{report_id}/retry")
def retry_property_report(
    report_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """Re-queue a failed property report for PDF generation."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Check report exists and is failed
        cur.execute("""
            SELECT status FROM property_reports
            WHERE id = %s::uuid
        """, (report_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Property report not found")
        
        # Update status to processing
        cur.execute("""
            UPDATE property_reports
            SET status = 'processing', updated_at = NOW()
            WHERE id = %s::uuid
        """, (report_id,))
        
        conn.commit()
        
        # Queue the task
        try:
            from celery import current_app
            current_app.send_task("generate_property_report", args=[report_id])
            logger.info(f"Admin {_admin.get('email')} retried property report {report_id}")
        except Exception as e:
            logger.error(f"Failed to queue property report task: {e}")
        
        return {"ok": True, "report_id": report_id, "status": "processing"}


@router.get("/stats/property-reports")
def get_property_report_stats(_admin: dict = Depends(get_admin_user)):
    """Get property report statistics."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at >= date_trunc('month', CURRENT_DATE)) as this_month,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE status = 'processing') as processing
            FROM property_reports
        """)
        
        row = cur.fetchone()
        return {
            "total": row[0] or 0,
            "this_month": row[1] or 0,
            "failed": row[2] or 0,
            "processing": row[3] or 0,
        }


# ==================== Leads Admin ====================

@router.get("/leads")
def list_admin_leads(
    status: Optional[str] = None,
    account: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    _admin: dict = Depends(get_admin_user)
):
    """
    List all leads across all accounts.
    """
    query = """
        SELECT 
            l.id::text,
            l.account_id::text,
            a.name as account_name,
            l.property_report_id::text,
            pr.property_address,
            l.name,
            l.email,
            l.phone,
            l.message,
            l.source,
            l.status,
            l.consent_given,
            l.sms_sent_at,
            l.email_sent_at,
            l.created_at
        FROM leads l
        JOIN accounts a ON l.account_id = a.id
        LEFT JOIN property_reports pr ON l.property_report_id = pr.id
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND l.status = %s"
        params.append(status)
    
    if account:
        query += " AND a.name ILIKE %s"
        params.append(f"%{account}%")
    
    if from_date:
        query += " AND l.created_at >= %s"
        params.append(from_date)
    
    if to_date:
        query += " AND l.created_at <= %s"
        params.append(to_date)
    
    query += " ORDER BY l.created_at DESC LIMIT %s"
    params.append(limit)
    
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        cur.execute(query, params)
        
        leads = []
        for row in cur.fetchall():
            leads.append({
                "id": row[0],
                "account_id": row[1],
                "account_name": row[2],
                "property_report_id": row[3],
                "property_address": row[4],
                "name": row[5],
                "email": row[6],
                "phone": row[7],
                "message": row[8],
                "source": row[9],
                "status": row[10],
                "consent_given": row[11],
                "sms_sent_at": row[12].isoformat() if row[12] else None,
                "email_sent_at": row[13].isoformat() if row[13] else None,
                "created_at": row[14].isoformat() if row[14] else None,
            })
        
        return {"leads": leads, "count": len(leads)}


@router.get("/leads/export")
def export_admin_leads(_admin: dict = Depends(get_admin_user)):
    """Export all leads as CSV."""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            SELECT 
                l.id::text,
                a.name as account_name,
                pr.property_address,
                l.name,
                l.email,
                l.phone,
                l.message,
                l.source,
                l.status,
                l.consent_given,
                l.created_at
            FROM leads l
            JOIN accounts a ON l.account_id = a.id
            LEFT JOIN property_reports pr ON l.property_report_id = pr.id
            ORDER BY l.created_at DESC
        """)
        
        rows = cur.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Account", "Property", "Name", "Email", "Phone",
        "Message", "Source", "Status", "Consent", "Created"
    ])
    
    for row in rows:
        writer.writerow([
            row[0], row[1], row[2] or "", row[3], row[4], row[5] or "",
            row[6] or "", row[7], row[8], row[9],
            row[10].isoformat() if row[10] else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads-export.csv"}
    )


@router.delete("/leads/{lead_id}")
def delete_admin_lead(
    lead_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """Delete a lead (admin action)."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            DELETE FROM leads
            WHERE id = %s::uuid
            RETURNING id::text
        """, (lead_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        conn.commit()
        logger.info(f"Admin {_admin.get('email')} deleted lead {lead_id}")
        
        return {"ok": True, "deleted_id": row[0]}


@router.get("/stats/leads")
def get_lead_stats(_admin: dict = Depends(get_admin_user)):
    """Get lead statistics."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as new_this_week,
                COUNT(*) FILTER (WHERE status = 'contacted') as contacted,
                COUNT(*) FILTER (WHERE status = 'converted') as converted
            FROM leads
        """)
        
        row = cur.fetchone()
        total = row[0] or 0
        converted = row[3] or 0
        conversion_rate = (converted / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "new_this_week": row[1] or 0,
            "contacted": row[2] or 0,
            "converted": converted,
            "conversion_rate": round(conversion_rate, 1),
        }


# ==================== SMS Admin ====================

@router.get("/sms/credits")
def get_sms_credits(_admin: dict = Depends(get_admin_user)):
    """Get SMS credit balances for all accounts."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            SELECT 
                a.id::text,
                a.name,
                a.sms_credits,
                COALESCE(p.sms_credits_per_month, 0) as sms_credits_per_month,
                COALESCE(p.lead_capture_enabled, false) as lead_capture_enabled
            FROM accounts a
            LEFT JOIN plans p ON a.plan_slug = p.plan_slug
            WHERE a.sms_credits > 0 OR p.lead_capture_enabled = true
            ORDER BY a.sms_credits DESC
        """)
        
        accounts = []
        for row in cur.fetchall():
            accounts.append({
                "account_id": row[0],
                "account_name": row[1],
                "sms_credits": row[2] or 0,
                "sms_credits_per_month": row[3],
                "lead_capture_enabled": row[4],
            })
        
        return {"accounts": accounts, "count": len(accounts)}


class AdjustCreditsRequest(BaseModel):
    """Request body for adjusting SMS credits."""
    account_id: str
    adjustment: int


@router.post("/sms/credits")
def adjust_sms_credits(
    body: AdjustCreditsRequest,
    _admin: dict = Depends(get_admin_user)
):
    """Adjust SMS credits for an account."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            UPDATE accounts
            SET sms_credits = GREATEST(0, sms_credits + %s), updated_at = NOW()
            WHERE id = %s::uuid
            RETURNING id::text, name, sms_credits
        """, (body.adjustment, body.account_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        conn.commit()
        logger.info(f"Admin {_admin.get('email')} adjusted SMS credits for {row[1]} by {body.adjustment}")
        
        return {
            "ok": True,
            "account_id": row[0],
            "account_name": row[1],
            "new_balance": row[2],
        }


@router.get("/sms/logs")
def get_sms_logs(
    limit: int = Query(50, ge=1, le=500),
    _admin: dict = Depends(get_admin_user)
):
    """Get SMS delivery logs."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Check if sms_logs table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sms_logs'
            )
        """)
        
        if not cur.fetchone()[0]:
            return {"logs": [], "count": 0}
        
        cur.execute("""
            SELECT 
                sl.id::text,
                sl.account_id::text,
                a.name as account_name,
                sl.to_phone,
                sl.from_phone,
                sl.message,
                sl.status,
                sl.error,
                sl.created_at
            FROM sms_logs sl
            JOIN accounts a ON sl.account_id = a.id
            ORDER BY sl.created_at DESC
            LIMIT %s
        """, (limit,))
        
        logs = []
        for row in cur.fetchall():
            logs.append({
                "id": row[0],
                "account_id": row[1],
                "account_name": row[2],
                "to_phone": row[3],
                "from_phone": row[4],
                "message": row[5],
                "status": row[6],
                "error": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
            })
        
        return {"logs": logs, "count": len(logs)}


# ==================== Blocked IPs ====================


class BlockIPRequest(BaseModel):
    """Request to block an IP address"""
    ip_address: str
    reason: Optional[str] = None
    expires_at: Optional[str] = None


@router.get("/blocked-ips")
def get_blocked_ips(
    include_expired: bool = Query(False),
    _admin: dict = Depends(get_admin_user)
):
    """Get all blocked IP addresses."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Base query
        if include_expired:
            where_clause = "1=1"
        else:
            where_clause = "(bi.expires_at IS NULL OR bi.expires_at > NOW())"
        
        cur.execute(f"""
            SELECT 
                bi.id::text,
                bi.ip_address,
                bi.reason,
                u.email as blocked_by_email,
                bi.created_at,
                bi.expires_at
            FROM blocked_ips bi
            LEFT JOIN users u ON bi.blocked_by = u.id
            WHERE {where_clause}
            ORDER BY bi.created_at DESC
        """)
        
        blocked_ips = []
        for row in cur.fetchall():
            blocked_ips.append({
                "id": row[0],
                "ip_address": row[1],
                "reason": row[2],
                "blocked_by_email": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "expires_at": row[5].isoformat() if row[5] else None,
            })
        
        return {"blocked_ips": blocked_ips, "count": len(blocked_ips)}


@router.post("/blocked-ips")
def block_ip(
    payload: BlockIPRequest,
    _admin: dict = Depends(get_admin_user)
):
    """Block an IP address."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Check if IP already blocked
        cur.execute("""
            SELECT id FROM blocked_ips 
            WHERE ip_address = %s
            AND (expires_at IS NULL OR expires_at > NOW())
        """, (payload.ip_address,))
        
        if cur.fetchone():
            raise HTTPException(
                status_code=409,
                detail="IP address is already blocked"
            )
        
        # Insert new block
        cur.execute("""
            INSERT INTO blocked_ips (ip_address, reason, blocked_by, expires_at)
            VALUES (%s, %s, %s::uuid, %s::timestamptz)
            RETURNING id::text, created_at
        """, (
            payload.ip_address,
            payload.reason,
            _admin.get("user_id"),
            payload.expires_at,
        ))
        
        row = cur.fetchone()
        conn.commit()
        
        logger.info(f"IP {payload.ip_address} blocked by admin {_admin.get('email')}")
        
        return {
            "ok": True,
            "id": row[0],
            "ip_address": payload.ip_address,
            "created_at": row[1].isoformat() if row[1] else None,
        }


@router.delete("/blocked-ips/{block_id}")
def unblock_ip(
    block_id: str,
    _admin: dict = Depends(get_admin_user)
):
    """Remove an IP from the block list."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            DELETE FROM blocked_ips
            WHERE id = %s::uuid
            RETURNING ip_address
        """, (block_id,))
        
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Block record not found")
        
        conn.commit()
        
        logger.info(f"IP {row[0]} unblocked by admin {_admin.get('email')}")
        
        return {"ok": True, "ip_address": row[0]}


@router.post("/blocked-ips/cleanup")
def cleanup_expired_blocks(
    _admin: dict = Depends(get_admin_user)
):
    """Remove expired IP blocks and old rate limit records."""
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Delete expired blocked IPs
        cur.execute("""
            DELETE FROM blocked_ips
            WHERE expires_at IS NOT NULL AND expires_at < NOW()
            RETURNING id
        """)
        expired_blocks = len(cur.fetchall())
        
        # Delete old rate limit records (older than 24 hours)
        cur.execute("""
            DELETE FROM lead_rate_limits
            WHERE submitted_at < NOW() - INTERVAL '24 hours'
            RETURNING id
        """)
        old_rate_limits = len(cur.fetchall())
        
        conn.commit()
        
        logger.info(f"Cleanup: removed {expired_blocks} expired blocks, {old_rate_limits} old rate limits")
        
        return {
            "ok": True,
            "expired_blocks_removed": expired_blocks,
            "rate_limits_removed": old_rate_limits,
        }


# ==================== Property Report Statistics ====================


class PlatformPropertyStatsResponse(BaseModel):
    """Platform-wide property report statistics"""
    period: dict
    summary: dict
    engagement: dict
    leads: dict
    by_account_type: dict
    themes: dict
    top_affiliates: List[dict]
    top_agents: List[dict]
    daily_trend: List[dict]
    all_time: dict


@router.get("/property-reports/stats", response_model=PlatformPropertyStatsResponse)
def get_admin_property_stats(
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get platform-wide property report statistics.
    
    Returns:
    - Total reports, completion rates, failure rates
    - Breakdown by account type (regular, sponsored, affiliate)
    - Theme popularity
    - Top affiliates by volume
    - Top agents by volume
    - Lead metrics and conversion rates
    - Daily activity trend
    """
    # Parse dates
    from_dt = datetime.fromisoformat(from_date.replace('Z', '')) if from_date else None
    to_dt = datetime.fromisoformat(to_date.replace('Z', '')) if to_date else None
    
    stats = get_platform_stats(from_dt, to_dt)
    return stats


@router.get("/property-reports")
def list_all_property_reports(
    status: Optional[str] = Query(None, description="Filter by status"),
    account_type: Optional[str] = Query(None, description="Filter by account type: regular, sponsored, affiliate"),
    theme: Optional[int] = Query(None, ge=1, le=5, description="Filter by theme"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(get_admin_user)
):
    """
    List all property reports across the platform.
    
    Supports filtering by status, account type, and theme.
    """
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        # Build query with filters
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("pr.status = %s")
            params.append(status)
        
        if theme:
            where_clauses.append("pr.theme = %s")
            params.append(theme)
        
        if account_type:
            if account_type == "sponsored":
                where_clauses.append("a.sponsor_account_id IS NOT NULL")
            elif account_type == "affiliate":
                where_clauses.append("a.account_type = 'INDUSTRY_AFFILIATE'")
            elif account_type == "regular":
                where_clauses.append("a.account_type = 'REGULAR' AND a.sponsor_account_id IS NULL")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        cur.execute(f"""
            SELECT COUNT(*) FROM property_reports pr
            JOIN accounts a ON a.id = pr.account_id
            WHERE {where_sql}
        """, params)
        total = cur.fetchone()[0]
        
        # Get reports
        cur.execute(f"""
            SELECT 
                pr.id::text,
                pr.account_id::text,
                a.name AS account_name,
                CASE 
                    WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 'affiliate'
                    WHEN a.sponsor_account_id IS NOT NULL THEN 'sponsored'
                    ELSE 'regular'
                END AS account_type,
                pr.property_address,
                pr.property_city,
                pr.property_state,
                pr.report_type,
                pr.theme,
                pr.status,
                pr.view_count,
                pr.unique_visitors,
                pr.short_code,
                pr.is_active,
                pr.created_at,
                (SELECT COUNT(*) FROM leads l WHERE l.property_report_id = pr.id) AS lead_count
            FROM property_reports pr
            JOIN accounts a ON a.id = pr.account_id
            WHERE {where_sql}
            ORDER BY pr.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        
        reports = []
        for row in cur.fetchall():
            reports.append({
                "id": row[0],
                "account_id": row[1],
                "account_name": row[2],
                "account_type": row[3],
                "address": row[4],
                "city": row[5],
                "state": row[6],
                "report_type": row[7],
                "theme": row[8],
                "status": row[9],
                "views": row[10],
                "unique_visitors": row[11],
                "short_code": row[12],
                "is_active": row[13],
                "created_at": row[14].isoformat() if row[14] else None,
                "leads": row[15]
            })
        
        return {
            "reports": reports,
            "total": total,
            "limit": limit,
            "offset": offset
        }


@router.get("/property-reports/top-affiliates")
def get_top_affiliates(
    limit: int = Query(10, ge=1, le=50),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get top affiliates ranked by property report activity.
    """
    from_dt = datetime.fromisoformat(from_date.replace('Z', '')) if from_date else datetime.utcnow() - timedelta(days=30)
    to_dt = datetime.fromisoformat(to_date.replace('Z', '')) if to_date else datetime.utcnow()
    
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        cur.execute("""
            SELECT
                aff.id::text AS affiliate_id,
                aff.name AS affiliate_name,
                COUNT(DISTINCT a.id) AS total_agents,
                COUNT(DISTINCT CASE WHEN pr.created_at >= %s THEN a.id END) AS active_agents,
                COUNT(pr.id) AS report_count,
                COALESCE(SUM(pr.view_count), 0) AS total_views,
                COALESCE(SUM(pr.unique_visitors), 0) AS unique_visitors,
                COUNT(l.id) AS total_leads,
                MAX(pr.created_at) AS last_activity
            FROM accounts aff
            JOIN accounts a ON a.sponsor_account_id = aff.id
            LEFT JOIN property_reports pr ON pr.account_id = a.id 
                AND pr.created_at >= %s AND pr.created_at < %s
            LEFT JOIN leads l ON l.account_id = a.id 
                AND l.created_at >= %s AND l.created_at < %s
            WHERE aff.account_type = 'INDUSTRY_AFFILIATE'
            GROUP BY aff.id, aff.name
            ORDER BY COUNT(pr.id) DESC
            LIMIT %s
        """, (from_dt, from_dt, to_dt, from_dt, to_dt, limit))
        
        affiliates = []
        for row in cur.fetchall():
            affiliates.append({
                "id": row[0],
                "name": row[1],
                "total_agents": row[2],
                "active_agents": row[3],
                "reports": row[4],
                "views": row[5],
                "unique_visitors": row[6],
                "leads": row[7],
                "last_activity": row[8].isoformat() if row[8] else None
            })
        
        return {"affiliates": affiliates}


@router.get("/property-reports/top-agents")
def get_top_agents(
    limit: int = Query(10, ge=1, le=50),
    account_type: Optional[str] = Query(None, description="Filter: regular, sponsored, all"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    _admin: dict = Depends(get_admin_user)
):
    """
    Get top agents ranked by property report activity.
    """
    from_dt = datetime.fromisoformat(from_date.replace('Z', '')) if from_date else datetime.utcnow() - timedelta(days=30)
    to_dt = datetime.fromisoformat(to_date.replace('Z', '')) if to_date else datetime.utcnow()
    
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        
        type_filter = ""
        if account_type == "sponsored":
            type_filter = "AND a.sponsor_account_id IS NOT NULL"
        elif account_type == "regular":
            type_filter = "AND a.sponsor_account_id IS NULL"
        
        cur.execute(f"""
            SELECT
                a.id::text AS account_id,
                a.name AS agent_name,
                u.email,
                CASE WHEN a.sponsor_account_id IS NOT NULL THEN 'sponsored' ELSE 'regular' END AS account_type,
                sponsor.name AS sponsor_name,
                COUNT(pr.id) AS report_count,
                COALESCE(SUM(pr.view_count), 0) AS total_views,
                COALESCE(SUM(pr.unique_visitors), 0) AS unique_visitors,
                COUNT(l.id) AS total_leads,
                CASE WHEN COALESCE(SUM(pr.unique_visitors), 0) > 0 
                    THEN ROUND((COUNT(l.id)::DECIMAL / SUM(pr.unique_visitors)) * 100, 2)
                    ELSE 0 
                END AS conversion_rate,
                MAX(pr.created_at) AS last_activity
            FROM accounts a
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            LEFT JOIN accounts sponsor ON sponsor.id = a.sponsor_account_id
            LEFT JOIN property_reports pr ON pr.account_id = a.id 
                AND pr.created_at >= %s AND pr.created_at < %s
            LEFT JOIN leads l ON l.account_id = a.id 
                AND l.created_at >= %s AND l.created_at < %s
            WHERE a.account_type = 'REGULAR' {type_filter}
            GROUP BY a.id, a.name, u.email, sponsor.name
            HAVING COUNT(pr.id) > 0
            ORDER BY COUNT(pr.id) DESC
            LIMIT %s
        """, (from_dt, to_dt, from_dt, to_dt, limit))
        
        agents = []
        for row in cur.fetchall():
            agents.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "type": row[3],
                "sponsor": row[4],
                "reports": row[5],
                "views": row[6],
                "unique_visitors": row[7],
                "leads": row[8],
                "conversion_rate": float(row[9]) if row[9] else 0,
                "last_activity": row[10].isoformat() if row[10] else None
            })
        
        return {"agents": agents}


@router.post("/property-reports/refresh-stats")
def refresh_property_stats(
    account_id: Optional[str] = Query(None, description="Specific account to refresh, or all if omitted"),
    _admin: dict = Depends(get_admin_user)
):
    """
    Manually trigger a refresh of property report statistics.
    
    Use sparingly - stats are automatically refreshed on changes.
    """
    result = refresh_stats(account_id)
    logger.info(f"Property stats refreshed by admin {_admin.get('email')}: {result}")
    return result