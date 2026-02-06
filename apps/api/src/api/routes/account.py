from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, constr
from typing import Optional
from ..db import db_conn, set_rls, fetchone_dict
from .reports import require_account_id  # reuse temporary shim
from ..services.accounts import (
    get_user_accounts,
    verify_user_account_access,
    get_account_info
)
from ..services.usage import (
    get_monthly_usage,
    resolve_plan_for_account,
    evaluate_report_limit
)
from ..services.plans import get_plan_catalog

router = APIRouter(prefix="/v1")

class AccountOut(BaseModel):
    id: str
    name: str
    slug: str
    # Logo fields
    logo_url: Optional[str] = None
    footer_logo_url: Optional[str] = None
    email_logo_url: Optional[str] = None
    email_footer_logo_url: Optional[str] = None
    # Colors
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    # Contact info - derived from user profile (single source of truth)
    rep_photo_url: Optional[str] = None
    contact_line1: Optional[str] = None
    contact_line2: Optional[str] = None
    website_url: Optional[str] = None
    # Plan/subscription
    subscription_status: Optional[str] = None
    monthly_report_limit: Optional[int] = None
    api_rate_limit: Optional[int] = None
    plan_slug: Optional[str] = None
    billing_status: Optional[str] = None
    stripe_customer_id: Optional[str] = None

class BrandingPatch(BaseModel):
    """
    Branding fields that can be updated.
    
    Note: Contact info (rep_photo_url, contact_line1, contact_line2) is now 
    derived from user profile. Update profile at /v1/users/me instead.
    """
    # Logo fields
    logo_url: Optional[str] = Field(None, description="Header logo URL for PDFs")
    footer_logo_url: Optional[str] = Field(None, description="Footer logo URL for PDFs")
    email_logo_url: Optional[str] = Field(None, description="Header logo URL for emails")
    email_footer_logo_url: Optional[str] = Field(None, description="Footer logo URL for emails")
    # Colors
    primary_color: Optional[constr(pattern=r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')] = None
    secondary_color: Optional[constr(pattern=r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')] = None


def build_contact_lines(first_name: str, last_name: str, job_title: str, 
                        phone: str, email: str) -> tuple[str, str]:
    """Build contact_line1 and contact_line2 from profile fields."""
    # Line 1: Name • Title (e.g., "Jerry Mendoza • Real Estate Agent")
    name = f"{first_name or ''} {last_name or ''}".strip()
    if name and job_title:
        contact_line1 = f"{name} • {job_title}"
    else:
        contact_line1 = name or job_title or ""
    
    # Line 2: Phone • Email (e.g., "(626) 555-1234 • jerry@example.com")
    phone_formatted = phone or ""
    if phone_formatted and len(phone_formatted) == 10:
        phone_formatted = f"({phone_formatted[:3]}) {phone_formatted[3:6]}-{phone_formatted[6:]}"
    
    if phone_formatted and email:
        contact_line2 = f"{phone_formatted} • {email}"
    else:
        contact_line2 = phone_formatted or email or ""
    
    return contact_line1, contact_line2

@router.get("/account", response_model=AccountOut)
def get_account(request: Request, account_id: str = Depends(require_account_id)):
    """
    Get account details with branding.
    
    Contact info (rep_photo_url, contact_line1, contact_line2) is derived from
    the current user's profile - profile is the single source of truth.
    """
    user = getattr(request.state, "user", None)
    user_id = user.get("id") if user else None
    
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        
        # Get account data
        cur.execute("""
            SELECT id::text, name, slug, 
                   logo_url, footer_logo_url, email_logo_url, email_footer_logo_url,
                   primary_color, secondary_color,
                   subscription_status, monthly_report_limit, api_rate_limit,
                   plan_slug, billing_status, stripe_customer_id
            FROM accounts
            WHERE id = %s
        """, (account_id,))
        acc_row = cur.fetchone()
        if not acc_row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get user profile for contact info (single source of truth)
        rep_photo_url = None
        contact_line1 = ""
        contact_line2 = ""
        website_url = ""
        
        if user_id:
            cur.execute("""
                SELECT avatar_url, first_name, last_name, job_title, 
                       phone, email, website
                FROM users
                WHERE id = %s::uuid AND is_active = TRUE
            """, (user_id,))
            user_row = cur.fetchone()
            if user_row:
                rep_photo_url = user_row[0]
                contact_line1, contact_line2 = build_contact_lines(
                    first_name=user_row[1],
                    last_name=user_row[2],
                    job_title=user_row[3],
                    phone=user_row[4],
                    email=user_row[5]
                )
                website_url = user_row[6]
        
        return AccountOut(
            id=acc_row[0],
            name=acc_row[1],
            slug=acc_row[2],
            logo_url=acc_row[3],
            footer_logo_url=acc_row[4],
            email_logo_url=acc_row[5],
            email_footer_logo_url=acc_row[6],
            primary_color=acc_row[7],
            secondary_color=acc_row[8],
            rep_photo_url=rep_photo_url,
            contact_line1=contact_line1,
            contact_line2=contact_line2,
            website_url=website_url,
            subscription_status=acc_row[9],
            monthly_report_limit=acc_row[10],
            api_rate_limit=acc_row[11],
            plan_slug=acc_row[12],
            billing_status=acc_row[13],
            stripe_customer_id=acc_row[14]
        )

@router.patch("/account/branding", response_model=AccountOut, status_code=status.HTTP_200_OK)
def patch_branding(payload: BrandingPatch, request: Request, account_id: str = Depends(require_account_id)):
    """
    Update account branding (logos and colors only).
    
    Note: Contact info is derived from user profile. To update contact info,
    use PATCH /v1/users/me to update your profile instead.
    """
    user = getattr(request.state, "user", None)
    user_id = user.get("id") if user else None
    
    sets = []
    params = []
    
    # Logo fields
    if payload.logo_url is not None:
        sets.append("logo_url = %s"); params.append(payload.logo_url)
    if payload.footer_logo_url is not None:
        sets.append("footer_logo_url = %s"); params.append(payload.footer_logo_url)
    if payload.email_logo_url is not None:
        sets.append("email_logo_url = %s"); params.append(payload.email_logo_url)
    if payload.email_footer_logo_url is not None:
        sets.append("email_footer_logo_url = %s"); params.append(payload.email_footer_logo_url)
    
    # Color fields
    if payload.primary_color is not None:
        sets.append("primary_color = %s"); params.append(payload.primary_color)
    if payload.secondary_color is not None:
        sets.append("secondary_color = %s"); params.append(payload.secondary_color)

    if not sets:
        raise HTTPException(status_code=400, detail="No branding fields provided.")

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute(f"UPDATE accounts SET {', '.join(sets)}, updated_at = NOW() WHERE id = %s RETURNING id::text",
                    (*params, account_id))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Account not found")

        # Get updated account data
        cur.execute("""
            SELECT id::text, name, slug, 
                   logo_url, footer_logo_url, email_logo_url, email_footer_logo_url,
                   primary_color, secondary_color,
                   subscription_status, monthly_report_limit, api_rate_limit,
                   plan_slug, billing_status, stripe_customer_id
            FROM accounts WHERE id = %s
        """, (account_id,))
        acc_row = cur.fetchone()
        
        # Get user profile for contact info (single source of truth)
        rep_photo_url = None
        contact_line1 = ""
        contact_line2 = ""
        website_url = ""
        
        if user_id:
            cur.execute("""
                SELECT avatar_url, first_name, last_name, job_title, 
                       phone, email, website
                FROM users
                WHERE id = %s::uuid AND is_active = TRUE
            """, (user_id,))
            user_row = cur.fetchone()
            if user_row:
                rep_photo_url = user_row[0]
                contact_line1, contact_line2 = build_contact_lines(
                    first_name=user_row[1],
                    last_name=user_row[2],
                    job_title=user_row[3],
                    phone=user_row[4],
                    email=user_row[5]
                )
                website_url = user_row[6]
        
        return AccountOut(
            id=acc_row[0],
            name=acc_row[1],
            slug=acc_row[2],
            logo_url=acc_row[3],
            footer_logo_url=acc_row[4],
            email_logo_url=acc_row[5],
            email_footer_logo_url=acc_row[6],
            primary_color=acc_row[7],
            secondary_color=acc_row[8],
            rep_photo_url=rep_photo_url,
            contact_line1=contact_line1,
            contact_line2=contact_line2,
            website_url=website_url,
            subscription_status=acc_row[9],
            monthly_report_limit=acc_row[10],
            api_rate_limit=acc_row[11],
            plan_slug=acc_row[12],
            billing_status=acc_row[13],
            stripe_customer_id=acc_row[14]
        )


# Phase 29C: Multi-account support

@router.get("/account/accounts")
def list_user_accounts(request: Request, account_id: str = Depends(require_account_id)):
    """
    Phase 29C: List all accounts the current user belongs to.
    
    Returns list of accounts with user's role in each.
    """
    # Get current user from request.state (set by AuthContextMiddleware)
    user = getattr(request.state, "user", None)
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="User ID not found in session")
    
    user_id = user["id"]
    
    with db_conn() as (conn, cur):
        accounts = get_user_accounts(cur, user_id)
        return {"accounts": accounts, "count": len(accounts)}


@router.post("/account/use")
def switch_account(
    body: dict,
    response: Response,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Phase 29C: Switch current account context.
    
    Body: { "account_id": "uuid" }
    
    Sets mr_account_id cookie to chosen account.
    """
    new_account_id = body.get("account_id")
    if not new_account_id:
        raise HTTPException(status_code=400, detail="account_id required")
    
    user = getattr(request.state, "user", None)
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="User ID not found in session")
    
    user_id = user["id"]
    
    with db_conn() as (conn, cur):
        # Verify user has access to this account
        if not verify_user_account_access(cur, user_id, new_account_id):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this account"
            )
        
        # Get account info
        account = get_account_info(cur, new_account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
    
    # Set cookie for account context
    response.set_cookie(
        key="mr_account_id",
        value=new_account_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    return {
        "ok": True,
        "current_account_id": new_account_id,
        "account_type": account["account_type"],
        "plan_slug": account["plan_slug"]
    }


# Phase 29E: Plan & Usage endpoint for current user

@router.get("/account/plan-usage")
def get_current_account_plan_usage(request: Request, account_id: str = Depends(require_account_id)):
    """
    Get plan and usage information for the current account.
    
    Phase 29E: User-facing version of admin endpoint.
    Shows plan details, current usage, and limit status.
    """
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        
        # Get account info
        cur.execute("""
            SELECT 
                id::text,
                name,
                account_type,
                plan_slug,
                monthly_report_limit_override,
                sponsor_account_id::text,
                billing_status
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        
        acc_row = cur.fetchone()
        if not acc_row:
            raise HTTPException(status_code=404, detail="Account not found")
        
        account_info = {
            "id": acc_row[0],
            "name": acc_row[1],
            "account_type": acc_row[2],
            "plan_slug": acc_row[3],
            "monthly_report_limit_override": acc_row[4],
            "sponsor_account_id": acc_row[5],
            "billing_status": acc_row[6],  # PASS 2: Expose billing_status
        }
        
        # FIX (H1): evaluate_report_limit already calls resolve_plan + get_monthly_usage
        # internally. We read plan and usage from its returned info dict
        # instead of calling them separately (was 6-8 queries, now 3-4).
        decision, info = evaluate_report_limit(cur, account_id)
        plan = info["plan"]
        usage = info["usage"]
        
        # Get Stripe billing info from plan catalog
        catalog = get_plan_catalog(cur)
        plan_entry = catalog.get(account_info["plan_slug"])
        
        stripe_billing = None
        if plan_entry and plan_entry.stripe_billing:
            # Convert Pydantic model to dict for API response
            stripe_billing = {
                "stripe_price_id": plan_entry.stripe_price_id,
                "amount": plan_entry.stripe_billing.amount,              # cents
                "currency": plan_entry.stripe_billing.currency,          # 'usd'
                "interval": plan_entry.stripe_billing.interval,          # 'month'
                "interval_count": plan_entry.stripe_billing.interval_count,  # 1
                "nickname": plan_entry.stripe_billing.nickname,          # 'Pro – $29/mo'
            }
        
        return {
            "account": account_info,
            "plan": plan,
            "usage": usage,
            "decision": decision.value,
            "info": info,
            "stripe_billing": stripe_billing,  # can be null for free plans
        }

