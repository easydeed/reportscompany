"""
Affiliate API Routes

Phase 29C: Industry affiliate dashboard and management
Performance: Duplicate routes removed, queries optimized
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, EmailStr, constr, field_validator
import csv
import io
import re
import logging
from typing import Any
from ..db import db_conn
from ..verification import block_unverified_send
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
from ..services.brand_resolver import resolve_brand
from ..services.email import send_role_invite_email
from ..services.invite_service import (
    create_invited_user,
    find_user_for_resend,
    get_inviter_context,
    regenerate_invite_token,
)
from .reports import require_account_id
from ..services.timefmt import utc_iso

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

#: Bulk invite limits. Each row is an account created and an email sent in this
#: affiliate's name, and the upload had no ceiling: a file of any size went
#: straight to the loop. 100 rows covers a whole office; more is refused before
#: a single row is read into the database.
BULK_INVITE_MAX_ROWS = 100
BULK_INVITE_MAX_BYTES = 256 * 1024


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

            # D-019. An invite is an email to a stranger, sent in this
            # affiliate's name.
            block_unverified_send(
                cur, account_id,
                action="invite an agent",
                to_emails=[body.email] if body.email else None,
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

            # D-019. Same as invite-agent: this puts mail in someone's inbox.
            block_unverified_send(
                cur, account_id,
                action="resend an agent invite",
                to_emails=[body.email] if body.email else None,
            )

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

        # D-019, and this is the one where it matters most: a CSV is an
        # arbitrary number of strangers in one request. Checked before the file
        # is read, so a refused bulk invite has not parsed a single row.
        block_unverified_send(cur, account_id, action="bulk-invite agents")

        inviter_name, company_name = _get_inviter_info(cur, account_id, request)

        content = await file.read(BULK_INVITE_MAX_BYTES + 1)
        if len(content) > BULK_INVITE_MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"The file is over {BULK_INVITE_MAX_BYTES // 1024} KB. Split it and upload in parts.",
            )
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        rows = list(csv.DictReader(io.StringIO(text)))
        if len(rows) > BULK_INVITE_MAX_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"{len(rows)} rows; the limit is {BULK_INVITE_MAX_ROWS} per upload. Nobody was invited.",
            )

        errors: list[dict] = []
        invited = 0
        total_rows = 0
        email_tasks: list[tuple[str, str]] = []
        seen: dict[str, int] = {}

        for idx, row in enumerate(rows, start=2):
            total_rows += 1
            row = {(k or "").strip().lower(): (v.strip() if v else "") for k, v in row.items()}

            email = row.get("email", "").strip().lower()
            name = row.get("name", "")

            if not email:
                errors.append({"row": idx, "email": "", "reason": "email is required"})
                continue
            if not EMAIL_RE.match(email):
                errors.append({"row": idx, "email": email, "reason": "invalid email format"})
                continue
            if email in seen:
                errors.append({"row": idx, "email": email, "reason": f"duplicate of row {seen[email]}"})
                continue
            seen[email] = idx
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

# Hex colour pattern, identical to routes/account.py:74. These columns are read
# by compute_color_roles(), which parses them as hex; an unvalidated value used
# to raise ValueError out of schedule_email_html() and stop every send on the
# account (D-060). Kept as a literal in each module rather than shared, matching
# how account.py already declares it.
HEX_COLOR = r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$'


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
    primary_color: constr(pattern=HEX_COLOR) | None = None
    accent_color: constr(pattern=HEX_COLOR) | None = None
    # Contact
    rep_photo_url: str | None = None
    contact_line1: str | None = None
    contact_line2: str | None = None
    website_url: str | None = None

    # An emptied colour field means "unset", not "invalid". The admin affiliate
    # form binds a free-text input to the same state as the colour picker
    # (apps/web/app/admin/(dashboard)/affiliates/page.tsx:191) and posts it
    # verbatim, so clearing it would otherwise 422 where it used to store "".
    @field_validator("primary_color", "accent_color", mode="before")
    @classmethod
    def _blank_color_is_unset(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


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

        # Centralized brand resolution (handles title-rep → parent inheritance)
        resolved = resolve_brand(cur, account_id)
        resolved_fields = {
            "resolved_logo_url": resolved["logo_url"],
            "resolved_primary_color": resolved["primary_color"],
            "resolved_accent_color": resolved["accent_color"],
            "resolved_display_name": resolved["display_name"],
            "brand_source": resolved["source"],
            "brand_source_account_id": resolved["source_account_id"],
        }

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
                    **resolved_fields,
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
                        **resolved_fields,
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
            **resolved_fields,
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
    Suspend a sponsored agent — what "Deactivate" and "Cancel Invitation" say.

    D-273: this used to set `accounts.is_active` and nothing else, and nothing
    reads that flag — login, accept-invite, the session check and the schedule
    sender all read `users.is_active`. So the agent kept signing in, kept
    sending, kept showing "active", and a cancelled invite still worked.

    Now, for the agent's account only (the ownership predicate is unchanged):
      * its users are deactivated — sign-in refused, an existing session
        refused by the auth middleware, scheduled sends skipped
        (`schedules_tick.account_can_send`);
      * its unused invite tokens are spent, so a cancelled invite link stops
        working (a reactivated invitee gets a new one from Resend);
      * `accounts.is_active` is still set, for the admin views that read it.
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

        # Only reached for an account the caller sponsors (the UPDATE above).
        cur.execute("UPDATE users SET is_active = FALSE WHERE account_id = %s::uuid", (row[0],))
        cur.execute(
            "UPDATE signup_tokens SET used = TRUE WHERE account_id = %s::uuid AND used = FALSE",
            (row[0],),
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
    Reactivate a suspended agent: the account and its users (D-273).
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

        # The reverse of deactivate (D-273). A spent invite token stays spent;
        # an invitee who never joined gets a fresh link from Resend.
        cur.execute("UPDATE users SET is_active = TRUE WHERE account_id = %s::uuid", (row[0],))

        conn.commit()
        
        return {
            "ok": True,
            "account_id": row[0],
            "name": row[1],
            "is_active": row[2],
        }


# ── Aggregate endpoints (rep views ALL agents' data) ─────────────────────────

@router.get("/all-reports")
def get_all_agent_reports(
    limit: int = 50,
    offset: int = 0,
    account_id: str = Depends(require_account_id),
):
    """Return reports from ALL sponsored agents plus the rep's own."""
    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT id FROM accounts WHERE sponsor_account_id = %s::uuid
        """, (account_id,))
        # cur returns UUID objects; account_id from the JWT is a str.
        # psycopg cannot dump a list with mixed UUID + str types into
        # ANY(%s), so coerce every id to str up front.
        agent_ids = [str(row[0]) for row in cur.fetchall()]
        all_ids = agent_ids + [str(account_id)]

        cur.execute("""
            SELECT COUNT(*) FROM report_generations WHERE account_id = ANY(%s)
        """, (all_ids,))
        total = cur.fetchone()[0]

        cur.execute("""
            SELECT rg.id::text, rg.report_type, rg.status, rg.generated_at,
                   COALESCE(rg.input_params->>'city', rg.cities[1], 'Unknown') AS city,
                   rg.pdf_url,
                   u.first_name || ' ' || COALESCE(u.last_name, '') AS user_name,
                   a.id::text AS agent_account_id,
                   CASE WHEN rg.account_id = %s::uuid THEN 'You' ELSE 'Agent' END AS source
            FROM report_generations rg
            JOIN accounts a ON a.id = rg.account_id
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            WHERE rg.account_id = ANY(%s)
            ORDER BY rg.generated_at DESC
            LIMIT %s OFFSET %s
        """, (account_id, all_ids, limit, offset))
        reports = [
            {
                "id": r[0], "report_type": r[1], "status": r[2],
                "generated_at": utc_iso(r[3]),
                "city": r[4], "pdf_url": r[5],
                "user_name": (r[6] or "").strip(),
                "agent_account_id": r[7], "source": r[8],
            }
            for r in cur.fetchall()
        ]

        return {"reports": reports, "total": total}


@router.get("/all-schedules")
def get_all_agent_schedules(account_id: str = Depends(require_account_id)):
    """Return schedules from ALL sponsored agents plus the rep's own."""
    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT id FROM accounts WHERE sponsor_account_id = %s::uuid
        """, (account_id,))
        # See get_all_agent_reports — must coerce UUIDs to str to match
        # the JWT-derived account_id, otherwise psycopg refuses the mixed
        # list when binding ANY(%s).
        agent_ids = [str(row[0]) for row in cur.fetchall()]
        all_ids = agent_ids + [str(account_id)]

        cur.execute("""
            SELECT s.id::text, s.name, s.report_type,
                   COALESCE(s.city, 'Unknown') AS area,
                   s.cadence, s.send_hour, s.send_minute, s.timezone,
                   s.active, s.last_run_at, s.next_run_at,
                   u.first_name || ' ' || COALESCE(u.last_name, '') AS user_name,
                   a.id::text AS agent_account_id,
                   (SELECT COUNT(*) FROM schedule_runs sr WHERE sr.schedule_id = s.id) AS total_runs,
                   CASE WHEN s.account_id = %s::uuid THEN 'You' ELSE 'Agent' END AS source,
                   s.weekly_dow, s.monthly_dom
            FROM schedules s
            JOIN accounts a ON a.id = s.account_id
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            WHERE s.account_id = ANY(%s)
            ORDER BY s.created_at DESC
        """, (account_id, all_ids))
        schedules = [
            {
                "id": r[0], "name": r[1], "report_type": r[2],
                "area": r[3], "cadence": r[4],
                "send_hour": r[5], "send_minute": r[6], "timezone": r[7],
                "active": r[8],
                "last_run_at": r[9].isoformat() if r[9] else None,
                "next_run_at": r[10].isoformat() if r[10] else None,
                "user_name": (r[11] or "").strip(),
                "agent_account_id": r[12], "total_runs": r[13],
                "source": r[14],
                "weekly_dow": r[15], "monthly_dom": r[16],
            }
            for r in cur.fetchall()
        ]

        return {"schedules": schedules, "total": len(schedules)}


# ── Agent visibility endpoints (rep views agent data) ────────────────────────

#: Where a lead came from, as the rep's pages say it. `qr_scan` and
#: `direct_link` both mean the agent's property-report page: its lead form
#: sends `qr_scan` whichever way the visitor arrived (D-325), so the two are
#: one place, not two. `cma_page` is the agent's home-value page
#: (`lead_pages.py`). Anything else is said as "other", never guessed.
LEAD_CAME_FROM = {"qr_scan": "property_page", "direct_link": "property_page", "cma_page": "home_value_page"}


@router.get("/agents/{agent_account_id}")
def get_book_agent(agent_account_id: str, account_id: str = Depends(require_account_id)):
    """One agent in the rep's book: who they are, where they stand, how many
    reports and homeowner leads. No lead's name, email, phone, message or
    address — the lead belongs to the agent."""
    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(403, detail="Not an affiliate account")
        # In the caller's book, or nothing: the id is bounded here, in the route.
        cur.execute("SELECT 1 FROM accounts WHERE id = %s::uuid AND sponsor_account_id = %s::uuid",
                    (agent_account_id, account_id))
        if not cur.fetchone():
            raise HTTPException(403, detail="This agent is not in your book")
        cur.execute("""
            SELECT a.id::text, a.name, a.created_at,
                   TRIM(COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, '')),
                   u.email, u.is_active, u.email_verified, u.password_hash IS NOT NULL,
                   (SELECT MAX(rg.generated_at) FROM report_generations rg
                     WHERE rg.account_id = a.id AND rg.status IN ('completed', 'processing')),
                   (SELECT COUNT(*) FROM leads l WHERE l.account_id = a.id
                     AND l.created_at >= date_trunc('month', NOW())),
                   (SELECT COUNT(*) FROM leads l WHERE l.account_id = a.id
                     AND l.created_at >= date_trunc('month', NOW() - INTERVAL '1 month')
                     AND l.created_at <  date_trunc('month', NOW())),
                   (SELECT COUNT(*) FROM leads l WHERE l.account_id = a.id)
              FROM accounts a
              LEFT JOIN LATERAL (
                  SELECT u2.first_name, u2.last_name, u2.email, u2.is_active,
                         u2.email_verified, u2.password_hash
                    FROM account_users au JOIN users u2 ON u2.id = au.user_id
                   WHERE au.account_id = a.id AND au.role = 'OWNER' LIMIT 1
              ) u ON true
             WHERE a.id = %s::uuid
        """, (agent_account_id,))
        r = cur.fetchone()
        from ..services.usage import get_full_plan_usage
        usage = get_full_plan_usage(cur, agent_account_id)

    if r[5] is False:
        status = "deactivated"
    elif r[6] and r[7]:
        status = "active"
    else:
        status = "pending"
    return {
        "agent": {
            "id": r[0],
            "name": r[3] or r[1] or r[4] or "",
            "email": r[4] or "",
            "status": status,
            "joined_at": r[2].isoformat() if r[2] else None,
            "last_report_at": utc_iso(r[8]),
            "plan_slug": usage["plan"]["plan_slug"],
            "plan_name": usage["plan"]["plan_name"],
            "market_reports_used": usage["usage"]["market_reports_used"],
            "market_reports_limit": usage["plan"]["market_reports_limit"],
        },
        "leads": {"this_month": r[9], "last_month": r[10], "total": r[11]},
    }


@router.get("/leads")
def get_book_leads(agent: str | None = None, account_id: str = Depends(require_account_id)):
    """Homeowner leads the agents in the rep's book have brought in: a count
    per agent and a feed, newest first. A READ of rows the agents' own pages
    wrote (`leads.py`, `lead_pages.py`); nothing is captured here. Each row
    says whose lead it is, where it came from and when — never who the lead
    is: the lead belongs to the agent."""
    with db_conn() as (conn, cur):
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(403, detail="Not an affiliate account")
        if agent:
            cur.execute("SELECT 1 FROM accounts WHERE id = %s::uuid AND sponsor_account_id = %s::uuid",
                        (agent, account_id))
            if not cur.fetchone():
                raise HTTPException(403, detail="This agent is not in your book")
        cur.execute("""
            SELECT a.id::text,
                   COALESCE(NULLIF(TRIM(COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, '')), ''), a.name),
                   COUNT(l.id) FILTER (WHERE l.created_at >= date_trunc('month', NOW())),
                   COUNT(l.id) FILTER (WHERE l.created_at >= date_trunc('month', NOW() - INTERVAL '1 month')
                                         AND l.created_at <  date_trunc('month', NOW())),
                   COUNT(l.id)
              FROM accounts a
              LEFT JOIN leads l ON l.account_id = a.id
              LEFT JOIN LATERAL (
                  SELECT u2.first_name, u2.last_name FROM account_users au JOIN users u2 ON u2.id = au.user_id
                   WHERE au.account_id = a.id AND au.role = 'OWNER' LIMIT 1
              ) u ON true
             WHERE a.sponsor_account_id = %s::uuid
             GROUP BY a.id, a.name, u.first_name, u.last_name
             ORDER BY 3 DESC, 5 DESC, 2
        """, (account_id,))
        agents = [{"agent_account_id": r[0], "agent_name": r[1], "this_month": r[2],
                   "last_month": r[3], "total": r[4]} for r in cur.fetchall()]
        names = {a["agent_account_id"]: a["agent_name"] for a in agents}
        ids = [agent] if agent else list(names)
        rows = []
        if ids:
            cur.execute("""
                SELECT l.id::text, l.account_id::text, l.source, l.created_at
                  FROM leads l
                 WHERE l.account_id = ANY(%s::uuid[])
                 ORDER BY l.created_at DESC
                 LIMIT 100
            """, (ids,))
            rows = cur.fetchall()
    return {
        "this_month": sum(a["this_month"] for a in agents),
        "last_month": sum(a["last_month"] for a in agents),
        "agents": agents,
        "leads": [
            {"id": r[0], "agent_account_id": r[1], "agent_name": names.get(r[1], ""),
             "came_from": LEAD_CAME_FROM.get(r[2], "other"), "created_at": utc_iso(r[3])}
            for r in rows
        ],
    }

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
                "generated_at": utc_iso(r[3]),
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
                   s.recipients, s.weekly_dow, s.monthly_dom
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
                "weekly_dow": r[14], "monthly_dom": r[15],
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
