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

