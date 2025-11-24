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
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    subscription_status: Optional[str] = None
    monthly_report_limit: Optional[int] = None
    api_rate_limit: Optional[int] = None
    plan_slug: Optional[str] = None
    billing_status: Optional[str] = None
    stripe_customer_id: Optional[str] = None

class BrandingPatch(BaseModel):
    logo_url: Optional[str] = Field(None, description="Public URL to a logo")
    primary_color: Optional[constr(pattern=r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')] = None
    secondary_color: Optional[constr(pattern=r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')] = None
    disclaimer: Optional[str] = None  # store in future column if needed

@router.get("/account", response_model=AccountOut)
def get_account(request: Request, account_id: str = Depends(require_account_id)):
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute("""
            SELECT id::text, name, slug, logo_url, primary_color, secondary_color,
                   subscription_status, monthly_report_limit, api_rate_limit,
                   plan_slug, billing_status, stripe_customer_id
            FROM accounts
            WHERE id = %s
        """, (account_id,))
        row = fetchone_dict(cur)
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        return row

@router.patch("/account/branding", response_model=AccountOut, status_code=status.HTTP_200_OK)
def patch_branding(payload: BrandingPatch, request: Request, account_id: str = Depends(require_account_id)):
    sets = []
    params = []
    if payload.logo_url is not None:
        sets.append("logo_url = %s"); params.append(payload.logo_url)
    if payload.primary_color is not None:
        sets.append("primary_color = %s"); params.append(payload.primary_color)
    if payload.secondary_color is not None:
        sets.append("secondary_color = %s"); params.append(payload.secondary_color)
    # NOTE: disclaimer column not in base schema; capture later when added.

    if not sets:
        raise HTTPException(status_code=400, detail="No branding fields provided.")

    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute(f"UPDATE accounts SET {', '.join(sets)}, updated_at = NOW() WHERE id = %s RETURNING id::text",
                    (*params, account_id))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Account not found")

        cur.execute("""
            SELECT id::text, name, slug, logo_url, primary_color, secondary_color,
                   subscription_status, monthly_report_limit, api_rate_limit,
                   plan_slug, billing_status, stripe_customer_id
            FROM accounts WHERE id = %s
        """, (account_id,))
        row = fetchone_dict(cur)
        return row


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
        
        # Get plan details
        plan = resolve_plan_for_account(cur, account_id)
        
        # Get usage
        usage = get_monthly_usage(cur, account_id)
        
        # Evaluate limit
        decision, info = evaluate_report_limit(cur, account_id)
        
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

