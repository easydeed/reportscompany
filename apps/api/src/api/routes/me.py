from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging
import os

from ..db import db_conn, set_rls

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1")

APP_URL = os.getenv("APP_URL", "https://trendyreports.io")

@router.get("/me")
def me(request: Request):
    """
    Get current user information including role, account type, and platform admin status.
    Returns: { account_id, user_id, email, role, account_type, is_platform_admin }
    """
    # Auth middleware already set account_id and user info
    account_id = getattr(request.state, "account_id", None)
    user_info = getattr(request.state, "user", None)
    
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Fetch account_type from accounts table
    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT account_type
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        account_row = cur.fetchone()
        account_type = account_row[0] if account_row else "REGULAR"
    
    # If auth middleware set user info (JWT authentication), use it
    if user_info and user_info.get("id"):
        return {
            "account_id": account_id,
            "user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "role": user_info.get("role", "USER"),
            "account_type": account_type,
            "is_platform_admin": user_info.get("is_platform_admin", False)
        }
    
    # Fallback: look up first user in account (API key authentication)
    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT id::text AS user_id, email, role, is_platform_admin 
            FROM users 
            WHERE account_id=%s::uuid 
            ORDER BY created_at ASC 
            LIMIT 1
        """, (account_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found for account")
        
        return {
            "account_id": account_id,
            "user_id": row[0],
            "email": row[1],
            "role": (row[2] or "USER").upper(),
            "account_type": account_type,
            "is_platform_admin": bool(row[3]) if row[3] is not None else False
        }


# ============================================================================
# Lead Pages - Agent Dashboard Endpoints
# ============================================================================

class LeadPageSettingsUpdate(BaseModel):
    """Update lead page settings"""
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    theme_color: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("/me/lead-page")
def get_lead_page_settings(request: Request):
    """
    Get current user's lead page settings including URL and QR code.
    """
    account_id = getattr(request.state, "account_id", None)
    user_info = getattr(request.state, "user", None)
    
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_id = user_info.get("id") if user_info else None
    
    with db_conn() as (conn, cur):
        # Get user ID from account if not in user_info
        if not user_id:
            cur.execute(
                "SELECT id FROM users WHERE account_id = %s::uuid ORDER BY created_at ASC LIMIT 1",
                (account_id,)
            )
            row = cur.fetchone()
            if row:
                user_id = str(row[0])
        
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get lead page settings
        cur.execute("""
            SELECT 
                agent_code,
                CONCAT(first_name, ' ', last_name) as full_name,
                COALESCE(photo_url, avatar_url) as photo_url,
                company_name,
                phone,
                email,
                license_number,
                landing_page_headline,
                landing_page_subheadline,
                landing_page_theme_color,
                landing_page_enabled,
                landing_page_visits
            FROM users
            WHERE id = %s::uuid
        """, (user_id,))
        
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        agent_code = row[0]
        
        # Generate URL and QR code
        url = f"{APP_URL}/cma/{agent_code}" if agent_code else None
        qr_code_url = None
        
        if url:
            # Use external QR service for simplicity
            import urllib.parse
            encoded_url = urllib.parse.quote(url, safe='')
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_url}"
        
        return {
            "agent_code": agent_code,
            "url": url,
            "qr_code_url": qr_code_url,
            "full_name": row[1],
            "photo_url": row[2],
            "company_name": row[3],
            "phone": row[4],
            "email": row[5],
            "license_number": row[6],
            "headline": row[7] or "Get Your Free Home Value Report",
            "subheadline": row[8] or "Find out what your home is worth in today's market.",
            "theme_color": row[9] or "#8B5CF6",
            "enabled": row[10] if row[10] is not None else True,
            "visits": row[11] or 0,
        }


@router.patch("/me/lead-page")
def update_lead_page_settings(updates: LeadPageSettingsUpdate, request: Request):
    """
    Update current user's lead page settings.
    """
    account_id = getattr(request.state, "account_id", None)
    user_info = getattr(request.state, "user", None)
    
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_id = user_info.get("id") if user_info else None
    
    with db_conn() as (conn, cur):
        if not user_id:
            cur.execute(
                "SELECT id FROM users WHERE account_id = %s::uuid ORDER BY created_at ASC LIMIT 1",
                (account_id,)
            )
            row = cur.fetchone()
            if row:
                user_id = str(row[0])
        
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build dynamic UPDATE
        fields = []
        values = []
        
        if updates.headline is not None:
            fields.append("landing_page_headline = %s")
            values.append(updates.headline[:255])  # Limit length
        
        if updates.subheadline is not None:
            fields.append("landing_page_subheadline = %s")
            values.append(updates.subheadline[:1000])
        
        if updates.theme_color is not None:
            # Validate hex color
            color = updates.theme_color
            if not color.startswith("#") or len(color) != 7:
                raise HTTPException(status_code=400, detail="Invalid color format. Use #RRGGBB")
            fields.append("landing_page_theme_color = %s")
            values.append(color)
        
        if updates.enabled is not None:
            fields.append("landing_page_enabled = %s")
            values.append(updates.enabled)
        
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(user_id)
        
        cur.execute(f"""
            UPDATE users
            SET {', '.join(fields)}
            WHERE id = %s::uuid
        """, values)
        conn.commit()
    
    return get_lead_page_settings(request)


@router.get("/me/leads")
def get_my_consumer_leads(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Get leads from consumer reports (Lead Pages feature).
    These are leads captured through the agent's public landing page.
    """
    account_id = getattr(request.state, "account_id", None)
    user_info = getattr(request.state, "user", None)
    
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_id = user_info.get("id") if user_info else None
    
    with db_conn() as (conn, cur):
        if not user_id:
            cur.execute(
                "SELECT id FROM users WHERE account_id = %s::uuid ORDER BY created_at ASC LIMIT 1",
                (account_id,)
            )
            row = cur.fetchone()
            if row:
                user_id = str(row[0])
        
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get total count
        cur.execute("""
            SELECT COUNT(*) FROM consumer_reports
            WHERE agent_id = %s::uuid
        """, (user_id,))
        total = cur.fetchone()[0]
        
        # Get leads
        cur.execute("""
            SELECT 
                id::text,
                consumer_phone,
                consumer_email,
                property_address,
                property_city,
                property_state,
                property_zip,
                status,
                view_count,
                agent_contact_clicked,
                agent_contact_type,
                pdf_url,
                created_at::text,
                updated_at::text
            FROM consumer_reports
            WHERE agent_id = %s::uuid
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, limit, offset))
        
        leads = []
        for row in cur.fetchall():
            leads.append({
                "id": row[0],
                "consumer_phone": row[1],
                "consumer_email": row[2],
                "property_address": row[3],
                "property_city": row[4],
                "property_state": row[5],
                "property_zip": row[6],
                "status": row[7],
                "view_count": row[8],
                "agent_contact_clicked": row[9],
                "agent_contact_type": row[10],
                "pdf_downloaded": row[11] is not None,
                "created_at": row[12],
                "updated_at": row[13],
            })
    
    return {
        "leads": leads,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
