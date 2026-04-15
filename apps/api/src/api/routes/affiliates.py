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
from ..services.email import send_role_invite_email
from ..services.invite_service import (
    create_invited_user,
    find_user_for_resend,
    get_inviter_context,
    regenerate_invite_token,
)
from .reports import require_account_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _inviter_user_id(request: Request) -> str | None:
    u = getattr(request.state, "user", None) or {}
    return u.get("id")


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
        
        # Get account info (include parent company context for tier-aware UI)
        cur.execute("""
            SELECT a.id::text, a.name, a.account_type, a.plan_slug,
                   a.parent_account_id::text,
                   pa.name AS parent_company_name
            FROM accounts a
            LEFT JOIN accounts pa ON pa.id = a.parent_account_id
            WHERE a.id = %s::uuid
        """, (account_id,))
        
        acc_row = cur.fetchone()
        
        return {
            "account": {
                "account_id": acc_row[0],
                "name": acc_row[1],
                "account_type": acc_row[2],
                "plan_slug": acc_row[3],
                "parent_account_id": acc_row[4],
                "parent_company_name": acc_row[5],
            },
            "overview": overview,
            "metrics": overview.get("metrics", {}),
            "sponsored_accounts": sponsored,
        }


# Phase 29C.6A: Invite sponsored agents

class InviteAgentRequest(BaseModel):
    name: str
    email: EmailStr
    default_city: str | None = None  # accepted for API compatibility; not persisted
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
    try:
        with db_conn() as (conn, cur):
            if not verify_affiliate_account(cur, account_id):
                raise HTTPException(
                    status_code=403,
                    detail="Only industry affiliates can invite agents"
                )

            parts = body.name.strip().split(None, 1)
            first_name = parts[0] if parts else body.name.strip()
            last_name = parts[1] if len(parts) > 1 else ""

            result = create_invited_user(
                cur,
                role="sponsored_agent",
                email=body.email,
                first_name=first_name,
                last_name=last_name,
                phone=body.phone,
                job_title=body.job_title,
                company_name=body.company_name,
                license_number=body.license_number,
                account_name=body.name.strip(),
                sponsor_account_id=account_id,
            )
            ctx = get_inviter_context(
                cur, account_id=account_id, inviter_user_id=_inviter_user_id(request)
            )
            conn.commit()

        background_tasks.add_task(
            send_role_invite_email,
            result["email"],
            ctx["inviter_name"],
            ctx["company_name"],
            result["token"],
            invitee_first_name=first_name,
            role="sponsored_agent",
        )
        logger.info(f"Invite email queued for {result['email']}")
        return {"ok": True, **result, "email_queued": True}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invite agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "invite_failed", "message": str(e)},
        )


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
    try:
        with db_conn() as (conn, cur):
            if not verify_affiliate_account(cur, account_id):
                raise HTTPException(status_code=403, detail="Not an affiliate account")

            user = find_user_for_resend(
                cur, email=body.email, sponsor_account_id=account_id
            )
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="Agent not found or not sponsored by your account",
                )
            if user["already_accepted"]:
                raise HTTPException(
                    status_code=400,
                    detail="This agent has already accepted their invitation",
                )

            token = regenerate_invite_token(
                cur, user_id=user["user_id"], account_id=user["account_id"]
            )
            ctx = get_inviter_context(
                cur, account_id=account_id, inviter_user_id=_inviter_user_id(request)
            )
            conn.commit()

        background_tasks.add_task(
            send_role_invite_email,
            user["email"],
            ctx["inviter_name"],
            ctx["company_name"],
            token,
            invitee_first_name=(user.get("first_name") or "").strip(),
            role="sponsored_agent",
        )
        logger.info(f"Resend invite email queued for {user['email']}")
        return {"ok": True, "email_queued": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resend invite: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "resend_failed", "message": str(e)},
        )


def _get_inviter_info(cur: Any, account_id: str, request: Request) -> tuple[str, str]:
    """Return (inviter_name, company_name) for bulk invite (uses shared context)."""
    ctx = get_inviter_context(cur, account_id=account_id, inviter_user_id=_inviter_user_id(request))
    return ctx["inviter_name"], ctx["company_name"]


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

            try:
                parts = name.strip().split(None, 1)
                fn = parts[0] if parts else name.strip()
                ln = parts[1] if len(parts) > 1 else ""
                result = create_invited_user(
                    cur,
                    role="sponsored_agent",
                    email=email,
                    first_name=fn,
                    last_name=ln,
                    phone=row.get("phone") or None,
                    job_title=row.get("job_title") or None,
                    company_name=row.get("company_name") or None,
                    license_number=row.get("license_number") or None,
                    account_name=name,
                    sponsor_account_id=account_id,
                )
                email_tasks.append(
                    (result["email"], result["token"], fn)
                )
                invited += 1
            except ValueError as e:
                errors.append({"row": idx, "email": email, "reason": str(e)})
            except Exception as e:
                logger.error(f"Failed to create agent for {email}: {e}")
                errors.append({"row": idx, "email": email, "reason": str(e)})

        conn.commit()

    for email_addr, token, fn in email_tasks:
        try:
            background_tasks.add_task(
                send_role_invite_email,
                email_addr,
                inviter_name,
                company_name,
                token,
                invitee_first_name=fn,
                role="sponsored_agent",
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


# ── Agent visibility endpoints (rep views agent data) ────────────────────────

@router.get("/agents/{agent_account_id}/reports")
def get_agent_reports(agent_account_id: str, account_id: str = Depends(require_account_id)):
    """Return report history for a specific sponsored agent."""
    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(403, detail="Not an affiliate account")

        cur.execute("""
            SELECT 1 FROM accounts
            WHERE id = %s::uuid AND sponsor_account_id = %s::uuid
        """, (agent_account_id, account_id))
        if not cur.fetchone():
            raise HTTPException(403, detail="This agent is not in your book")

        cur.execute("""
            SELECT rg.id::text, rg.report_type, rg.status, rg.generated_at,
                   COALESCE(rg.input_params->>'city', rg.cities[1], 'Unknown') AS city,
                   rg.pdf_url,
                   CASE WHEN sr.id IS NOT NULL THEN true ELSE false END AS is_scheduled
            FROM report_generations rg
            LEFT JOIN schedule_runs sr ON sr.report_run_id = rg.id
            WHERE rg.account_id = %s::uuid
            ORDER BY rg.generated_at DESC
            LIMIT 50
        """, (agent_account_id,))
        reports = [
            {
                "id": r[0], "report_type": r[1], "status": r[2],
                "generated_at": r[3].isoformat() if r[3] else None,
                "city": r[4], "pdf_url": r[5], "is_scheduled": r[6],
            }
            for r in cur.fetchall()
        ]

        return {"reports": reports, "total": len(reports)}


@router.get("/agents/{agent_account_id}/schedules")
def get_agent_schedules(agent_account_id: str, account_id: str = Depends(require_account_id)):
    """Return schedules for a specific sponsored agent."""
    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(403, detail="Not an affiliate account")

        cur.execute("""
            SELECT 1 FROM accounts
            WHERE id = %s::uuid AND sponsor_account_id = %s::uuid
        """, (agent_account_id, account_id))
        if not cur.fetchone():
            raise HTTPException(403, detail="This agent is not in your book")

        cur.execute("""
            SELECT s.id::text, s.name, s.report_type,
                   COALESCE(s.city, s.zip_codes[1], 'Unknown') AS area,
                   s.cadence, s.send_hour, s.send_minute, s.timezone,
                   s.active, s.last_run_at, s.next_run_at,
                   s.created_at,
                   (SELECT COUNT(*) FROM schedule_runs sr WHERE sr.schedule_id = s.id) AS total_runs,
                   s.recipients
            FROM schedules s
            WHERE s.account_id = %s::uuid
            ORDER BY s.created_at DESC
        """, (agent_account_id,))
        schedules = [
            {
                "id": r[0], "name": r[1], "report_type": r[2],
                "area": r[3], "cadence": r[4],
                "send_hour": r[5], "send_minute": r[6], "timezone": r[7],
                "active": r[8],
                "last_run_at": r[9].isoformat() if r[9] else None,
                "next_run_at": r[10].isoformat() if r[10] else None,
                "created_at": r[11].isoformat() if r[11] else None,
                "total_runs": r[12],
                "recipient_count": len(r[13]) if r[13] else 0,
            }
            for r in cur.fetchall()
        ]

        return {"schedules": schedules, "total": len(schedules)}


@router.get("/agents/{agent_account_id}/usage")
def get_agent_usage(agent_account_id: str, account_id: str = Depends(require_account_id)):
    """Return per-product usage summary for a specific sponsored agent."""
    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(403, detail="Not an affiliate account")

        cur.execute("""
            SELECT 1 FROM accounts
            WHERE id = %s::uuid AND sponsor_account_id = %s::uuid
        """, (agent_account_id, account_id))
        if not cur.fetchone():
            raise HTTPException(403, detail="This agent is not in your book")

        from ..services.usage import get_full_plan_usage
        return get_full_plan_usage(cur, agent_account_id)
