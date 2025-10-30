from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, constr
from typing import Optional
from ..db import db_conn, set_rls, fetchone_dict
from .reports import require_account_id  # reuse temporary shim

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
                   subscription_status, monthly_report_limit, api_rate_limit
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
                   subscription_status, monthly_report_limit, api_rate_limit
            FROM accounts WHERE id = %s
        """, (account_id,))
        row = fetchone_dict(cur)
        return row

