"""
Affiliate API Routes

Phase 29C: Industry affiliate dashboard and management
Performance: Duplicate routes removed, queries optimized
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, EmailStr
import csv
import io
import re
import secrets
import time
import logging
from typing import Any
from ..db import db_conn
from ..services.affiliates import (
    get_affiliate_overview,
    get_sponsored_accounts,
    verify_affiliate_account
)
from ..services.branding import (
    get_brand_for_account,
    validate_brand_input,
    Brand
)
from ..services.email import send_invite_email
from .reports import require_account_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _create_sponsored_agent(
    cur: Any,
    affiliate_account_id: str,
    email: str,
    name: str,
    default_city: str | None = None,
    phone: str | None = None,
    job_title: str | None = None,
    company_name: str | None = None,
    license_number: str | None = None,
) -> dict:
    """
    Shared helper: create a sponsored REGULAR account + user + invite token.
    Returns dict with account_id, user_id, token, invite_url.
    Caller is responsible for commit and email sending.
    """
    slug = name.lower().replace(' ', '-').replace('.', '').replace(',', '')[:50]
    cur.execute("SELECT id FROM accounts WHERE slug = %s", (slug,))
    if cur.fetchone():
        slug = f"{slug}-{int(time.time())}"[:50]

    cur.execute("""
        INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id)
        VALUES (%s, %s, 'REGULAR', 'sponsored_free', %s::uuid)
        RETURNING id::text
    """, (name, slug, affiliate_account_id))
    new_account_id = cur.fetchone()[0]

    if default_city:
        cur.execute(
            "UPDATE accounts SET default_city = %s WHERE id = %s::uuid",
            (default_city, new_account_id),
        )

    parts = name.strip().split(None, 1)
    first_name = parts[0] if parts else name.strip()
    last_name = parts[1] if len(parts) > 1 else ""

    cur.execute("""
        INSERT INTO users (account_id, email, is_active, email_verified, role,
                           first_name, last_name,
                           phone, job_title, company_name, license_number)
        VALUES (%s::uuid, %s, true, false, 'member',
                %s, %s, %s, %s, %s, %s)
        RETURNING id::text
    """, (new_account_id, email, first_name, last_name,
          phone, job_title, company_name, license_number))
    new_user_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO account_users (account_id, user_id, role)
        VALUES (%s::uuid, %s::uuid, 'OWNER')
    """, (new_account_id, new_user_id))

    token = secrets.token_urlsafe(32)
    cur.execute("""
        INSERT INTO signup_tokens (token, user_id, account_id)
        VALUES (%s, %s::uuid, %s::uuid)
    """, (token, new_user_id, new_account_id))

    return {
        "account_id": new_account_id,
        "user_id": new_user_id,
        "token": token,
        "invite_url": f"https://reportscompany-web.vercel.app/welcome?token={token}",
    }


@router.get("/overview")
def get_overview(request: Request, account_id: str = Depends(require_account_id)):
    """
    Get affiliate dashboard overview.
    
    Phase 29C: Shows sponsored accounts and usage metrics.
    
    Returns 403 if account is not INDUSTRY_AFFILIATE.
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # Get overview metrics (lightweight aggregate — no N+1)
        overview = get_affiliate_overview(cur, account_id)
        
        # Get sponsored accounts list (batch groups — 2 queries total)
        sponsored = get_sponsored_accounts(cur, account_id)
        
        # Get account info
        cur.execute("""
            SELECT id::text, name, account_type, plan_slug
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        
        acc_row = cur.fetchone()
        
        return {
            "account": {
                "account_id": acc_row[0],
                "name": acc_row[1],
                "account_type": acc_row[2],
                "plan_slug": acc_row[3],
            },
            "overview": overview,
            "sponsored_accounts": sponsored,
        }


# Phase 29C.6A: Invite sponsored agents

class InviteAgentRequest(BaseModel):
    name: str
    email: EmailStr
    default_city: str | None = None
    phone: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    license_number: str | None = None


@router.post("/invite-agent")
def invite_agent(
    body: InviteAgentRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    account_id: str = Depends(require_account_id)
):
    """
    Invite a new agent to be sponsored by this affiliate.
    
    Phase 29C: Creates new REGULAR account with sponsored_free plan.
    """
    email = body.email.strip().lower()

    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail="Only industry affiliates can invite agents"
            )

        cur.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email,))
        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists"
            )

        result = _create_sponsored_agent(
            cur, account_id, email, body.name,
            default_city=body.default_city,
            phone=body.phone,
            job_title=body.job_title,
            company_name=body.company_name,
            license_number=body.license_number,
        )

        inviter_name, company_name = _get_inviter_info(cur, account_id, request)
        conn.commit()

        try:
            background_tasks.add_task(
                send_invite_email,
                email, inviter_name, company_name, result["token"]
            )
            logger.info(f"Invite email queued for {email} from {company_name}")
        except Exception as e:
            logger.error(f"Failed to queue invite email for {email}: {e}")

        return {
            "ok": True,
            **result,
            "email_queued": True,
        }


class ResendInviteRequest(BaseModel):
    email: EmailStr


@router.post("/resend-invite")
def resend_invite(
    body: ResendInviteRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    account_id: str = Depends(require_account_id),
):
    """Resend invitation email to a pending sponsored agent (no user recreation)."""
    email = body.email.strip().lower()

    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(status_code=403, detail="Not an affiliate account")

        # Find the user and verify sponsorship in one query
        cur.execute("""
            SELECT u.id::text, u.email_verified, u.password_hash IS NOT NULL AS has_password,
                   a.id::text AS agent_account_id
            FROM users u
            JOIN account_users au ON au.user_id = u.id AND au.role = 'OWNER'
            JOIN accounts a ON a.id = au.account_id
            WHERE LOWER(u.email) = %s
              AND a.sponsor_account_id = %s::uuid
        """, (email, account_id))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Agent not found or not sponsored by your account")

        user_id, email_verified, has_password, agent_account_id = row

        if email_verified and has_password:
            raise HTTPException(status_code=400, detail="This agent has already accepted their invitation")

        # Invalidate old tokens, generate a new one
        cur.execute("""
            UPDATE signup_tokens SET used = TRUE
            WHERE user_id = %s::uuid AND used = FALSE
        """, (user_id,))

        token = secrets.token_urlsafe(32)
        cur.execute("""
            INSERT INTO signup_tokens (token, user_id, account_id, expires_at)
            VALUES (%s, %s::uuid, %s::uuid, NOW() + INTERVAL '7 days')
        """, (token, user_id, agent_account_id))

        conn.commit()

    inviter_name, company_name = _get_inviter_info_simple(cur, account_id, request)

    try:
        background_tasks.add_task(send_invite_email, email, inviter_name, company_name, token)
        logger.info(f"Resend invite email queued for {email}")
    except Exception as e:
        logger.error(f"Failed to queue resend invite for {email}: {e}")

    return {"ok": True, "email_queued": True}


def _get_inviter_info_simple(cur, account_id: str, request: Request) -> tuple[str, str]:
    """Standalone helper that opens its own cursor for use after conn is closed."""
    with db_conn() as (conn2, cur2):
        return _get_inviter_info(cur2, account_id, request)


def _get_inviter_info(cur: Any, account_id: str, request: Request) -> tuple[str, str]:
    """Return (inviter_name, company_name) for invite emails."""
    cur.execute("SELECT name FROM accounts WHERE id = %s::uuid", (account_id,))
    row = cur.fetchone()
    company_name = row[0] if row else "Your Sponsor"
    inviter_name = company_name

    user_id_from_token = getattr(request.state, 'user_id', None)
    if user_id_from_token:
        cur.execute("""
            SELECT COALESCE(first_name || ' ' || last_name, email)
            FROM users WHERE id = %s::uuid
        """, (user_id_from_token,))
        inviter_row = cur.fetchone()
        if inviter_row and inviter_row[0] and inviter_row[0].strip():
            inviter_name = inviter_row[0].strip()

    return inviter_name, company_name


@router.post("/bulk-invite")
async def bulk_invite_agents(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    account_id: str = Depends(require_account_id),
):
    """
    Bulk invite agents from a CSV upload.

    CSV columns: name (required), email (required),
    city, phone, job_title, company_name, license_number (all optional).
    """
    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail="Only industry affiliates can invite agents",
            )

        inviter_name, company_name = _get_inviter_info(cur, account_id, request)

        content = await file.read()
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        reader = csv.DictReader(io.StringIO(text))
        errors: list[dict] = []
        invited = 0
        total_rows = 0
        email_tasks: list[tuple[str, str]] = []

        for idx, row in enumerate(reader, start=2):
            total_rows += 1
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}

            email = row.get("email", "").strip().lower()
            name = row.get("name", "")

            if not email:
                errors.append({"row": idx, "email": "", "reason": "email is required"})
                continue
            if not EMAIL_RE.match(email):
                errors.append({"row": idx, "email": email, "reason": "invalid email format"})
                continue
            if not name:
                errors.append({"row": idx, "email": email, "reason": "name is required"})
                continue

            cur.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email,))
            if cur.fetchone():
                errors.append({"row": idx, "email": email, "reason": "email already registered"})
                continue

            try:
                result = _create_sponsored_agent(
                    cur, account_id, email, name,
                    default_city=row.get("city") or None,
                    phone=row.get("phone") or None,
                    job_title=row.get("job_title") or None,
                    company_name=row.get("company_name") or None,
                    license_number=row.get("license_number") or None,
                )
                email_tasks.append((email, result["token"]))
                invited += 1
            except Exception as e:
                logger.error(f"Failed to create agent for {email}: {e}")
                errors.append({"row": idx, "email": email, "reason": str(e)})

        conn.commit()

    for email_addr, token in email_tasks:
        try:
            background_tasks.add_task(
                send_invite_email, email_addr, inviter_name, company_name, token,
            )
        except Exception as e:
            logger.error(f"Failed to queue invite email for {email_addr}: {e}")

    return {
        "total_rows": total_rows,
        "invited": invited,
        "skipped": len(errors),
        "errors": errors,
    }


# ============================================================================
# AFFILIATE BRANDING ENDPOINTS
# FIX (M5): Removed duplicate Phase 30 / Phase W2 branding routes.
# Kept the most complete version (Phase 30's with all logo fields).
# ============================================================================

class BrandingInput(BaseModel):
    """Input model for branding configuration."""
    brand_display_name: str
    # PDF logos
    logo_url: str | None = None              # PDF header (gradient bg - light/white logo)
    footer_logo_url: str | None = None       # PDF footer (gray bg - dark/colored logo)
    # Email logos
    email_logo_url: str | None = None        # Email header (gradient bg - light/white logo)
    email_footer_logo_url: str | None = None # Email footer (light bg - dark/colored logo)
    # Colors
    primary_color: str | None = None
    accent_color: str | None = None
    # Contact
    rep_photo_url: str | None = None
    contact_line1: str | None = None
    contact_line2: str | None = None
    website_url: str | None = None


@router.get("/branding")
def get_branding(request: Request, account_id: str = Depends(require_account_id)):
    """
    Get affiliate branding configuration.
    
    Returns white-label branding settings for this affiliate.
    Falls back to account name if no branding configured.
    
    Returns 403 if account is not INDUSTRY_AFFILIATE.
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # Try to load branding configuration (with graceful handling for missing columns)
        try:
            cur.execute("""
                SELECT
                    brand_display_name,
                    logo_url,
                    email_logo_url,
                    footer_logo_url,
                    email_footer_logo_url,
                    primary_color,
                    accent_color,
                    rep_photo_url,
                    contact_line1,
                    contact_line2,
                    website_url
                FROM affiliate_branding
                WHERE account_id = %s::uuid
            """, (account_id,))
            row = cur.fetchone()
            
            if row:
                return {
                    "brand_display_name": row[0],
                    "logo_url": row[1],
                    "email_logo_url": row[2],
                    "footer_logo_url": row[3],
                    "email_footer_logo_url": row[4],
                    "primary_color": row[5],
                    "accent_color": row[6],
                    "rep_photo_url": row[7],
                    "contact_line1": row[8],
                    "contact_line2": row[9],
                    "website_url": row[10],
                }
        except Exception as e:
            # Column may not exist yet - try legacy query
            logger.warning(f"Branding query failed, trying fallback: {e}")
            try:
                cur.execute("""
                    SELECT
                        brand_display_name,
                        logo_url,
                        email_logo_url,
                        footer_logo_url,
                        primary_color,
                        accent_color,
                        rep_photo_url,
                        contact_line1,
                        contact_line2,
                        website_url
                    FROM affiliate_branding
                    WHERE account_id = %s::uuid
                """, (account_id,))
                row = cur.fetchone()
                
                if row:
                    return {
                        "brand_display_name": row[0],
                        "logo_url": row[1],
                        "email_logo_url": row[2],
                        "footer_logo_url": row[3],
                        "email_footer_logo_url": None,
                        "primary_color": row[4],
                        "accent_color": row[5],
                        "rep_photo_url": row[6],
                        "contact_line1": row[7],
                        "contact_line2": row[8],
                        "website_url": row[9],
                    }
            except Exception as e2:
                logger.warning(f"Legacy branding query also failed: {e2}")
        
        # No branding configured - return account name as default
        cur.execute("""
            SELECT name FROM accounts WHERE id = %s::uuid
        """, (account_id,))
        
        account_row = cur.fetchone()
        account_name = account_row[0] if account_row else "Unknown"
        
        return {
            "brand_display_name": account_name,
            "logo_url": None,
            "email_logo_url": None,
            "footer_logo_url": None,
            "email_footer_logo_url": None,
            "primary_color": "#7C3AED",
            "accent_color": "#F26B2B",
            "rep_photo_url": None,
            "contact_line1": None,
            "contact_line2": None,
            "website_url": None,
        }


@router.post("/branding")
def save_branding(
    body: BrandingInput,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Save affiliate branding configuration.
    
    Upserts white-label branding settings for this affiliate.
    These settings will be used on all client-facing reports and emails
    for this affiliate and their sponsored agents.
    
    Returns 403 if account is not INDUSTRY_AFFILIATE.
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # Validate input
        is_valid, error_msg = validate_brand_input(body.model_dump())
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_input",
                    "message": error_msg
                }
            )
        
        # Check if this rep belongs to a company (set override flag if so)
        cur.execute("""
            SELECT parent_account_id FROM accounts WHERE id = %s::uuid
        """, (account_id,))
        parent_row = cur.fetchone()
        has_parent = bool(parent_row and parent_row[0])

        # Upsert branding (with all logo fields)
        cur.execute("""
            INSERT INTO affiliate_branding (
                account_id,
                brand_display_name,
                logo_url,
                email_logo_url,
                footer_logo_url,
                email_footer_logo_url,
                primary_color,
                accent_color,
                rep_photo_url,
                contact_line1,
                contact_line2,
                website_url,
                branding_override,
                updated_at
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (account_id)
            DO UPDATE SET
                brand_display_name = EXCLUDED.brand_display_name,
                logo_url = EXCLUDED.logo_url,
                email_logo_url = EXCLUDED.email_logo_url,
                footer_logo_url = EXCLUDED.footer_logo_url,
                email_footer_logo_url = EXCLUDED.email_footer_logo_url,
                primary_color = EXCLUDED.primary_color,
                accent_color = EXCLUDED.accent_color,
                rep_photo_url = EXCLUDED.rep_photo_url,
                contact_line1 = EXCLUDED.contact_line1,
                contact_line2 = EXCLUDED.contact_line2,
                website_url = EXCLUDED.website_url,
                branding_override = CASE WHEN %s THEN TRUE
                                         ELSE affiliate_branding.branding_override END,
                updated_at = NOW()
            RETURNING
                brand_display_name,
                logo_url,
                email_logo_url,
                footer_logo_url,
                email_footer_logo_url,
                primary_color,
                accent_color,
                rep_photo_url,
                contact_line1,
                contact_line2,
                website_url
        """, (
            account_id,
            body.brand_display_name,
            body.logo_url,
            body.email_logo_url,
            getattr(body, 'footer_logo_url', None),
            getattr(body, 'email_footer_logo_url', None),
            body.primary_color,
            body.accent_color,
            body.rep_photo_url,
            body.contact_line1,
            body.contact_line2,
            body.website_url,
            has_parent,
            has_parent,
        ))
        
        row = cur.fetchone()
        conn.commit()
        
        return {
            "ok": True,
            "brand_display_name": row[0],
            "logo_url": row[1],
            "email_logo_url": row[2],
            "footer_logo_url": row[3],
            "email_footer_logo_url": row[4],
            "primary_color": row[5],
            "accent_color": row[6],
            "rep_photo_url": row[7],
            "contact_line1": row[8],
            "contact_line2": row[9],
            "website_url": row[10],
        }


# Phase: Sponsored account management (metrics + suspend)

@router.get("/accounts/{sponsored_account_id}")
def get_sponsored_account_detail(
    sponsored_account_id: str,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Get detailed metrics for a specific sponsored account.
    
    FIX (M4): Combined 4 separate queries into 1 with correlated subqueries.
    
    Returns 403 if:
    - Current account is not INDUSTRY_AFFILIATE
    - sponsored_account_id is not actually sponsored by current account
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # FIX (M4): Single query instead of 4 separate ones
        cur.execute("""
            SELECT
                a.id::text,
                a.name,
                a.plan_slug,
                a.is_active,
                a.created_at,
                (SELECT COUNT(*) FROM report_generations
                 WHERE account_id = a.id
                   AND generated_at >= date_trunc('month', CURRENT_DATE)
                   AND status IN ('completed', 'processing')) AS reports_this_month,
                (SELECT MAX(generated_at) FROM report_generations
                 WHERE account_id = a.id) AS last_report_at,
                (SELECT COUNT(*) FROM report_generations
                 WHERE account_id = a.id
                   AND status IN ('completed', 'processing')) AS total_reports
            FROM accounts a
            WHERE a.id = %s::uuid
              AND a.sponsor_account_id = %s::uuid
        """, (sponsored_account_id, account_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Sponsored account not found or not owned by you"
            )
        
        return {
            "account": {
                "account_id": row[0],
                "name": row[1],
                "plan_slug": row[2],
                "is_active": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            },
            "metrics": {
                "reports_this_month": row[5],
                "total_reports": row[7],
                "last_report_at": row[6].isoformat() if row[6] else None,
            },
        }


@router.post("/accounts/{sponsored_account_id}/deactivate")
def deactivate_sponsored_account(
    sponsored_account_id: str,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Suspend/deactivate a sponsored account.
    
    Sets is_active = FALSE on the account.
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # Verify ownership and update
        cur.execute("""
            UPDATE accounts
            SET is_active = FALSE
            WHERE id = %s::uuid
              AND sponsor_account_id = %s::uuid
            RETURNING id::text, name, is_active
        """, (sponsored_account_id, account_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Sponsored account not found or not owned by you"
            )
        
        conn.commit()
        
        return {
            "ok": True,
            "account_id": row[0],
            "name": row[1],
            "is_active": row[2],
        }


@router.post("/accounts/{sponsored_account_id}/unsponsor")
def unsponsor_account(
    sponsored_account_id: str,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Remove sponsorship from an account.
    
    Sets sponsor_account_id = NULL and optionally downgrades to free plan.
    The account becomes independent.
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # Verify sponsorship and get account details
        cur.execute("""
            SELECT id::text, name, plan_slug
            FROM accounts
            WHERE id = %s::uuid
              AND sponsor_account_id = %s::uuid
        """, (sponsored_account_id, account_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Sponsored account not found or not sponsored by you"
            )
        
        # Remove sponsorship and optionally downgrade to free
        cur.execute("""
            UPDATE accounts
            SET sponsor_account_id = NULL,
                plan_slug = CASE 
                    WHEN plan_slug = 'sponsored_free' THEN 'free'
                    ELSE plan_slug
                END,
                updated_at = NOW()
            WHERE id = %s::uuid
            RETURNING id::text, name, plan_slug, sponsor_account_id
        """, (sponsored_account_id,))
        
        updated_row = cur.fetchone()
        if not updated_row:
            raise HTTPException(
                status_code=500,
                detail="Failed to unsponsor account"
            )
        
        conn.commit()
        
        return {
            "ok": True,
            "account_id": updated_row[0],
            "name": updated_row[1],
            "plan_slug": updated_row[2],
            "sponsor_account_id": updated_row[3],  # Should be None
            "message": "Account is now independent"
        }


@router.post("/accounts/{sponsored_account_id}/reactivate")
def reactivate_sponsored_account(
    sponsored_account_id: str,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Reactivate a suspended account.
    
    Sets is_active = TRUE on the account.
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # Verify ownership and update
        cur.execute("""
            UPDATE accounts
            SET is_active = TRUE
            WHERE id = %s::uuid
              AND sponsor_account_id = %s::uuid
            RETURNING id::text, name, is_active
        """, (sponsored_account_id, account_id))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Sponsored account not found or not owned by you"
            )
        
        conn.commit()
        
        return {
            "ok": True,
            "account_id": row[0],
            "name": row[1],
            "is_active": row[2],
        }
