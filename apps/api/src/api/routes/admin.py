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

    with db_conn() as conn:
        cur = conn.cursor()

        # Reports in last 24h
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE created_at >= NOW() - INTERVAL '24 hours'
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
            WHERE created_at >= NOW() - INTERVAL '7 days'
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

        # Active users (logged in last 30 days)
        cur.execute("""
            SELECT COUNT(*) FROM users
            WHERE last_login_at >= NOW() - INTERVAL '30 days'
        """)
        active_users_30d = cur.fetchone()[0] or 0

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
    
    with db_conn() as conn:
        cur = conn.cursor()
        
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
             AND rg.created_at >= date_trunc('month', CURRENT_DATE)) as reports_this_month
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

    with db_conn() as conn:
        cur = conn.cursor()
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
    with db_conn() as conn:
        cur = conn.cursor()

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
                 AND rg.created_at >= date_trunc('month', CURRENT_DATE)) as reports_this_month,
                (SELECT MAX(rg.created_at) FROM report_generations rg WHERE rg.account_id = a.id) as last_report_at
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
            AND rg.created_at >= date_trunc('month', CURRENT_DATE)
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
    with db_conn() as conn:
        cur = conn.cursor()

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
    with db_conn() as conn:
        cur = conn.cursor()

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
    with db_conn() as conn:
        cur = conn.cursor()

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
             AND rg.created_at >= date_trunc('month', CURRENT_DATE)) as reports_this_month
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

    with db_conn() as conn:
        cur = conn.cursor()
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
    with db_conn() as conn:
        cur = conn.cursor()

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
            u.last_login_at,
            a.id::text as account_id,
            a.name as account_name,
            a.account_type,
            au.role
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

    with db_conn() as conn:
        cur = conn.cursor()
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
                "last_login_at": row[7].isoformat() if row[7] else None,
                "account_id": row[8],
                "account_name": row[9],
                "account_type": row[10],
                "role": row[11],
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
    with db_conn() as conn:
        cur = conn.cursor()

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
                u.last_login_at,
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
            "last_login_at": row[10].isoformat() if row[10] else None,
            "account": {
                "account_id": row[11],
                "name": row[12],
                "account_type": row[13],
                "plan_slug": row[14],
            },
            "role": row[15],
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
    _admin: dict = Depends(get_admin_user)
):
    """
    Update a user's status.
    """
    with db_conn() as conn:
        cur = conn.cursor()

        updates = []
        params = []

        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if email_verified is not None:
            updates.append("email_verified = %s")
            params.append(email_verified)

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        params.append(user_id)

        cur.execute(f"""
            UPDATE users
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = %s::uuid
            RETURNING id::text, email, is_active, email_verified
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
    with db_conn() as conn:
        cur = conn.cursor()

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
    with db_conn() as conn:
        cur = conn.cursor()

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
    with db_conn() as conn:
        cur = conn.cursor()

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
    with db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
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
                "id": row[0],
                "plan_slug": row[1],
                "plan_name": row[2],
                "monthly_report_limit": row[3],
                "allow_overage": row[4],
                "overage_price_cents": row[5],
                "stripe_price_id": row[6],
                "description": row[7],
                "is_active": row[8],
                "created_at": row[9].isoformat() if row[9] else None,
                "updated_at": row[10].isoformat() if row[10] else None,
                "account_count": row[11] or 0,
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
    with db_conn() as conn:
        cur = conn.cursor()

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
            RETURNING id, plan_slug, plan_name, monthly_report_limit, allow_overage, overage_price_cents, is_active
        """, params)

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plan not found")

        conn.commit()

        return {
            "ok": True,
            "id": row[0],
            "plan_slug": row[1],
            "plan_name": row[2],
            "monthly_report_limit": row[3],
            "allow_overage": row[4],
            "overage_price_cents": row[5],
            "is_active": row[6],
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
    with db_conn() as conn:
        cur = conn.cursor()

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
            RETURNING id, plan_slug, plan_name, monthly_report_limit
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
            "id": row[0],
            "plan_slug": row[1],
            "plan_name": row[2],
            "monthly_report_limit": row[3],
        }


# ==================== System Stats ====================

@router.get("/stats/revenue")
def get_revenue_stats(_admin: dict = Depends(get_admin_user)):
    """
    Get revenue and billing statistics.
    """
    with db_conn() as conn:
        cur = conn.cursor()

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
            WHERE created_at >= date_trunc('month', CURRENT_DATE)
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

