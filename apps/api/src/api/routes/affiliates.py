"""
Affiliate API Routes

Phase 29C: Industry affiliate dashboard and management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
import secrets
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
from .reports import require_account_id

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])


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
        
        # Get overview metrics
        overview = get_affiliate_overview(cur, account_id)
        
        # Get sponsored accounts list
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


@router.post("/invite-agent")
def invite_agent(
    body: InviteAgentRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Invite a new agent to be sponsored by this affiliate.
    
    Phase 29C: Creates new REGULAR account with sponsored_free plan.
    
    Body:
        name: Agent/company name
        email: Agent email
        default_city: Optional default city for reports
    
    Returns:
        account_id: New sponsored account ID
        user_id: New user ID
        token: Invite token for welcome link
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail="Only industry affiliates can invite agents"
            )
        
        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (body.email,))
        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists"
            )
        
        # Create new account
        slug = body.name.lower().replace(' ', '-').replace('.', '').replace(',', '')[:50]
        
        # Ensure slug is unique
        cur.execute("SELECT id FROM accounts WHERE slug = %s", (slug,))
        if cur.fetchone():
            # Add timestamp to make unique
            import time
            slug = f"{slug}-{int(time.time())}"[:50]
        
        cur.execute("""
            INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id)
            VALUES (%s, %s, 'REGULAR', 'sponsored_free', %s::uuid)
            RETURNING id::text
        """, (
            body.name,
            slug,
            account_id
        ))
        new_account_id = cur.fetchone()[0]
        
        # Create new user
        cur.execute("""
            INSERT INTO users (account_id, email, is_active, email_verified, role)
            VALUES (%s::uuid, %s, true, false, 'member')
            RETURNING id::text
        """, (new_account_id, body.email))
        new_user_id = cur.fetchone()[0]
        
        # Create account_users entry (OWNER)
        cur.execute("""
            INSERT INTO account_users (account_id, user_id, role)
            VALUES (%s::uuid, %s::uuid, 'OWNER')
        """, (new_account_id, new_user_id))
        
        # Generate invite token
        token = secrets.token_urlsafe(32)
        
        # Create signup_tokens table if it doesn't exist
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
        """, (token, new_user_id, new_account_id))
        
        conn.commit()
        
        # TODO: Send invitation email (Phase 29C - optional enhancement)
        # For now, just return the token
        
        return {
            "ok": True,
            "account_id": new_account_id,
            "user_id": new_user_id,
            "token": token,
            "invite_url": f"https://reportscompany-web.vercel.app/welcome?token={token}"
        }


# ============================================================================
# PHASE 30: AFFILIATE BRANDING ENDPOINTS
# ============================================================================

class BrandingInput(BaseModel):
    """Input model for branding configuration."""
    brand_display_name: str
    logo_url: str | None = None
    primary_color: str | None = None
    accent_color: str | None = None
    rep_photo_url: str | None = None
    contact_line1: str | None = None
    contact_line2: str | None = None
    website_url: str | None = None


@router.get("/branding")
def get_branding(request: Request, account_id: str = Depends(require_account_id)):
    """
    Get affiliate branding configuration.
    
    Phase 30: Returns white-label branding settings for this affiliate.
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
        
        # Try to load branding configuration
        cur.execute("""
            SELECT
                brand_display_name,
                logo_url,
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
            # Return configured branding
            return {
                "brand_display_name": row[0],
                "logo_url": row[1],
                "primary_color": row[2],
                "accent_color": row[3],
                "rep_photo_url": row[4],
                "contact_line1": row[5],
                "contact_line2": row[6],
                "website_url": row[7],
            }
        
        # No branding configured - return account name as default
        cur.execute("""
            SELECT name FROM accounts WHERE id = %s::uuid
        """, (account_id,))
        
        account_row = cur.fetchone()
        account_name = account_row[0] if account_row else "Unknown"
        
        return {
            "brand_display_name": account_name,
            "logo_url": None,
            "primary_color": "#7C3AED",  # Default Trendy violet
            "accent_color": "#F26B2B",   # Default Trendy coral
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
    
    Phase 30: Upserts white-label branding settings for this affiliate.
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
        
        # Upsert branding
        cur.execute("""
            INSERT INTO affiliate_branding (
                account_id,
                brand_display_name,
                logo_url,
                primary_color,
                accent_color,
                rep_photo_url,
                contact_line1,
                contact_line2,
                website_url,
                updated_at
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (account_id)
            DO UPDATE SET
                brand_display_name = EXCLUDED.brand_display_name,
                logo_url = EXCLUDED.logo_url,
                primary_color = EXCLUDED.primary_color,
                accent_color = EXCLUDED.accent_color,
                rep_photo_url = EXCLUDED.rep_photo_url,
                contact_line1 = EXCLUDED.contact_line1,
                contact_line2 = EXCLUDED.contact_line2,
                website_url = EXCLUDED.website_url,
                updated_at = NOW()
            RETURNING
                brand_display_name,
                logo_url,
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
            body.primary_color,
            body.accent_color,
            body.rep_photo_url,
            body.contact_line1,
            body.contact_line2,
            body.website_url
        ))
        
        row = cur.fetchone()
        conn.commit()
        
        return {
            "ok": True,
            "brand_display_name": row[0],
            "logo_url": row[1],
            "primary_color": row[2],
            "accent_color": row[3],
            "rep_photo_url": row[4],
            "contact_line1": row[5],
            "contact_line2": row[6],
            "website_url": row[7],
        }


# Phase W2: Affiliate Branding API

class BrandingRequest(BaseModel):
    brand_display_name: str
    logo_url: str | None = None
    primary_color: str | None = None
    accent_color: str | None = None
    rep_photo_url: str | None = None
    contact_line1: str | None = None
    contact_line2: str | None = None
    website_url: str | None = None


@router.get("/branding")
def get_branding(request: Request, account_id: str = Depends(require_account_id)):
    """
    Get branding configuration for current affiliate account.
    
    Phase W2: Returns affiliate's white-label branding settings.
    
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
        
        # Query affiliate_branding table
        cur.execute("""
            SELECT 
                brand_display_name,
                logo_url,
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
            # Return existing branding
            return {
                "brand_display_name": row[0],
                "logo_url": row[1],
                "primary_color": row[2],
                "accent_color": row[3],
                "rep_photo_url": row[4],
                "contact_line1": row[5],
                "contact_line2": row[6],
                "website_url": row[7],
            }
        else:
            # No branding row yet, use account name as default
            cur.execute("""
                SELECT name FROM accounts WHERE id = %s::uuid
            """, (account_id,))
            acc_row = cur.fetchone()
            account_name = acc_row[0] if acc_row else "My Company"
            
            return {
                "brand_display_name": account_name,
                "logo_url": None,
                "primary_color": None,
                "accent_color": None,
                "rep_photo_url": None,
                "contact_line1": None,
                "contact_line2": None,
                "website_url": None,
            }


@router.post("/branding")
def save_branding(
    body: BrandingRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Save branding configuration for current affiliate account.
    
    Phase W2: Upserts affiliate's white-label branding settings.
    
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
            raise HTTPException(status_code=400, detail={"error": "validation_error", "message": error_msg})
        
        # Upsert branding
        cur.execute("""
            INSERT INTO affiliate_branding (
                account_id,
                brand_display_name,
                logo_url,
                primary_color,
                accent_color,
                rep_photo_url,
                contact_line1,
                contact_line2,
                website_url,
                updated_at
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (account_id)
            DO UPDATE SET
                brand_display_name = EXCLUDED.brand_display_name,
                logo_url = EXCLUDED.logo_url,
                primary_color = EXCLUDED.primary_color,
                accent_color = EXCLUDED.accent_color,
                rep_photo_url = EXCLUDED.rep_photo_url,
                contact_line1 = EXCLUDED.contact_line1,
                contact_line2 = EXCLUDED.contact_line2,
                website_url = EXCLUDED.website_url,
                updated_at = NOW()
            RETURNING 
                brand_display_name,
                logo_url,
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
            body.primary_color,
            body.accent_color,
            body.rep_photo_url,
            body.contact_line1,
            body.contact_line2,
            body.website_url
        ))
        
        row = cur.fetchone()
        conn.commit()
        
        return {
            "brand_display_name": row[0],
            "logo_url": row[1],
            "primary_color": row[2],
            "accent_color": row[3],
            "rep_photo_url": row[4],
            "contact_line1": row[5],
            "contact_line2": row[6],
            "website_url": row[7],
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
        
        # Verify the sponsored account belongs to this affiliate
        cur.execute("""
            SELECT 
                a.id::text,
                a.name,
                a.plan_slug,
                a.is_active,
                a.created_at
            FROM accounts a
            WHERE a.id = %s::uuid
              AND a.sponsor_account_id = %s::uuid
        """, (sponsored_account_id, account_id))
        
        acc_row = cur.fetchone()
        if not acc_row:
            raise HTTPException(
                status_code=404,
                detail="Sponsored account not found or not owned by you"
            )
        
        # Get usage metrics for this month
        cur.execute("""
            SELECT COUNT(*) 
            FROM reports
            WHERE account_id = %s::uuid
              AND created_at >= date_trunc('month', CURRENT_DATE)
        """, (sponsored_account_id,))
        reports_this_month = cur.fetchone()[0]
        
        # Get last report date
        cur.execute("""
            SELECT MAX(created_at)
            FROM reports
            WHERE account_id = %s::uuid
        """, (sponsored_account_id,))
        last_report_row = cur.fetchone()
        last_report_at = last_report_row[0].isoformat() if last_report_row and last_report_row[0] else None
        
        # Get total reports all time
        cur.execute("""
            SELECT COUNT(*)
            FROM reports
            WHERE account_id = %s::uuid
        """, (sponsored_account_id,))
        total_reports = cur.fetchone()[0]
        
        return {
            "account": {
                "account_id": acc_row[0],
                "name": acc_row[1],
                "plan_slug": acc_row[2],
                "is_active": acc_row[3],
                "created_at": acc_row[4].isoformat() if acc_row[4] else None,
            },
            "metrics": {
                "reports_this_month": reports_this_month,
                "total_reports": total_reports,
                "last_report_at": last_report_at,
            }
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
    Future: worker can respect this flag and skip sending schedules.
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

