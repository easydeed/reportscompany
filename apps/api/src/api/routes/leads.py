"""
Leads API - Lead capture and management for property reports.

Endpoints:
- POST /v1/leads/capture (PUBLIC) - Capture lead from QR scan or direct link
- GET /v1/leads - List leads for account
- GET /v1/leads/{id} - Get single lead
- PATCH /v1/leads/{id} - Update lead status
- DELETE /v1/leads/{id} - Delete lead
- GET /v1/leads/export/csv - Export leads as CSV
"""

import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from ..db import db_conn, fetchall_dicts, fetchone_dict, set_rls
from ..services.twilio_sms import (
    format_phone_e164,
    is_configured as twilio_is_configured,
    send_lead_notification_sms,
    TwilioSMSError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")

# Rate limiting: max submissions per IP per hour
RATE_LIMIT_MAX_SUBMISSIONS = 5
RATE_LIMIT_WINDOW_HOURS = 1


# ============================================================================
# Schemas
# ============================================================================


class LeadCaptureInput(BaseModel):
    """Public lead capture input from QR scan or direct link."""
    short_code: str = Field(..., min_length=4, max_length=20, description="Property report short code")
    name: str = Field(..., min_length=1, max_length=200, description="Lead's name")
    email: EmailStr = Field(..., description="Lead's email address")
    phone: Optional[str] = Field(None, max_length=50, description="Lead's phone number")
    message: Optional[str] = Field(None, max_length=2000, description="Optional message")
    consent_given: bool = Field(default=False, description="Whether lead consented to contact")
    source: Literal["qr_scan", "direct_link"] = Field(default="direct_link", description="How lead found the report")
    access_code: Optional[str] = Field(None, max_length=50, description="Access code for protected landing pages")
    website: Optional[str] = Field(None, description="Honeypot field - should be empty")


class LeadCaptureResponse(BaseModel):
    """Response for successful lead capture."""
    success: bool
    message: str


class LeadUpdate(BaseModel):
    """Lead update fields."""
    status: Optional[Literal["new", "contacted", "converted"]] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Lead response model."""
    id: str
    account_id: str
    property_report_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    source: str
    consent_given: bool
    sms_sent_at: Optional[str] = None
    email_sent_at: Optional[str] = None
    status: str
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str
    updated_at: str
    property_address: Optional[str] = None  # Joined from property_reports


# ============================================================================
# Helper Functions
# ============================================================================


def require_account_id(request: Request) -> str:
    """Extract and validate account_id from request state."""
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account_id


def get_client_ip(request: Request) -> str:
    """
    Extract real client IP from request headers.
    Handles proxied requests (X-Forwarded-For, X-Real-IP, CF-Connecting-IP).
    """
    # Cloudflare
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip.strip()
    
    # Standard proxy headers
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs; the first is the client
        return x_forwarded_for.split(",")[0].strip()
    
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


# ============================================================================
# Anti-Spam Helper Functions
# ============================================================================


def check_ip_blocked(cur, ip_address: str) -> bool:
    """Check if IP is on the block list (considering expiry)."""
    cur.execute("""
        SELECT 1 FROM blocked_ips
        WHERE ip_address = %s
        AND (expires_at IS NULL OR expires_at > NOW())
        LIMIT 1
    """, (ip_address,))
    return cur.fetchone() is not None


def check_rate_limit(cur, ip_address: str, hours: int = RATE_LIMIT_WINDOW_HOURS) -> int:
    """Count recent submissions from this IP. Returns count."""
    cur.execute("""
        SELECT COUNT(*) FROM lead_rate_limits
        WHERE ip_address = %s
        AND submitted_at > NOW() - INTERVAL '%s hours'
    """, (ip_address, hours))
    return cur.fetchone()[0]


def record_rate_limit(cur, ip_address: str, report_id: str):
    """Record a submission for rate limiting."""
    cur.execute("""
        INSERT INTO lead_rate_limits (ip_address, property_report_id)
        VALUES (%s, %s::uuid)
    """, (ip_address, report_id))


def check_duplicate_email(cur, email: str, report_id: str) -> bool:
    """Check if this email has already submitted to this report."""
    cur.execute("""
        SELECT 1 FROM leads
        WHERE email = %s
        AND property_report_id = %s::uuid
        LIMIT 1
    """, (email, report_id))
    return cur.fetchone() is not None


def count_leads_for_report(cur, report_id: str) -> int:
    """Count total leads for a property report."""
    cur.execute("""
        SELECT COUNT(*) FROM leads
        WHERE property_report_id = %s::uuid
    """, (report_id,))
    return cur.fetchone()[0]


def update_landing_page_analytics(cur, report_id: str, ip_address: str):
    """Update view count, unique visitors, and last viewed timestamp."""
    # Check if this IP has viewed before
    cur.execute("""
        SELECT 1 FROM lead_rate_limits
        WHERE ip_address = %s AND property_report_id = %s::uuid
        LIMIT 1
    """, (ip_address, report_id))
    is_new_visitor = cur.fetchone() is None
    
    if is_new_visitor:
        cur.execute("""
            UPDATE property_reports
            SET view_count = view_count + 1,
                unique_visitors = unique_visitors + 1,
                last_viewed_at = NOW()
            WHERE id = %s::uuid
        """, (report_id,))
    else:
        cur.execute("""
            UPDATE property_reports
            SET view_count = view_count + 1,
                last_viewed_at = NOW()
            WHERE id = %s::uuid
        """, (report_id,))


# ============================================================================
# PUBLIC Endpoint - Lead Capture
# ============================================================================


@router.post("/leads/capture", response_model=LeadCaptureResponse)
async def capture_lead(payload: LeadCaptureInput, request: Request):
    """
    PUBLIC endpoint - Capture a lead from QR scan or direct link.
    
    No authentication required. This is called by the public property report page.
    
    Anti-spam checks (in order):
    1. Honeypot check (website field should be empty)
    2. Find property_report by short_code
    3. is_active check
    4. expires_at check
    5. max_leads check
    6. access_code check
    7. IP block list check
    8. Rate limit check (5 per hour per IP)
    9. Duplicate email check (silent success)
    10. Store lead + send SMS notification
    """
    # Get client IP for rate limiting and blocking
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")[:500]  # Limit length
    
    # SUCCESS response for bots/invalid - don't reveal anything
    silent_success = LeadCaptureResponse(
        success=True,
        message="Thank you! We'll be in touch soon."
    )
    
    # 1. Honeypot check - "website" field should always be empty
    if payload.website:
        logger.warning(f"Honeypot triggered from IP {client_ip}")
        return silent_success  # Silently ignore bot submissions
    
    with db_conn() as (conn, cur):
        # 2. Find property report by short_code (no RLS - public endpoint)
        cur.execute("""
            SELECT 
                pr.id,
                pr.account_id,
                pr.user_id,
                pr.property_address,
                pr.property_city,
                pr.property_state,
                pr.is_active,
                pr.expires_at,
                pr.max_leads,
                pr.access_code,
                a.sms_credits,
                p.lead_capture_enabled
            FROM property_reports pr
            JOIN accounts a ON pr.account_id = a.id
            LEFT JOIN plans p ON a.plan_slug = p.plan_slug
            WHERE pr.short_code = %s
        """, (payload.short_code,))
        
        report_row = cur.fetchone()
        
        if not report_row:
            raise HTTPException(status_code=404, detail="Property report not found")
        
        (
            report_id,
            account_id,
            user_id,
            property_address,
            property_city,
            property_state,
            is_active,
            expires_at,
            max_leads,
            access_code,
            sms_credits,
            lead_capture_enabled,
        ) = report_row
        
        # 3. Check if landing page is active
        if not is_active:
            raise HTTPException(status_code=410, detail="This page is no longer available")
        
        # 4. Check expiration
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="This page has expired")
        
        # 5. Check max leads
        if max_leads:
            current_leads = count_leads_for_report(cur, str(report_id))
            if current_leads >= max_leads:
                raise HTTPException(status_code=410, detail="This page is no longer accepting submissions")
        
        # 6. Check access code (if set)
        if access_code:
            if payload.access_code != access_code:
                raise HTTPException(status_code=403, detail="Invalid access code")
        
        # 7. Check IP block list
        if check_ip_blocked(cur, client_ip):
            logger.warning(f"Blocked IP attempted submission: {client_ip}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 8. Rate limit check (5 per hour per IP)
        recent_submissions = check_rate_limit(cur, client_ip, RATE_LIMIT_WINDOW_HOURS)
        if recent_submissions >= RATE_LIMIT_MAX_SUBMISSIONS:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {recent_submissions} submissions")
            raise HTTPException(status_code=429, detail="Too many submissions. Please try again later.")
        
        # 9. Duplicate email check (silent success - don't reveal existing leads)
        if check_duplicate_email(cur, payload.email, str(report_id)):
            logger.info(f"Duplicate email submission: {payload.email[:3]}*** to report {report_id}")
            return silent_success
        
        # 10. All checks passed - check plan and create lead
        if not lead_capture_enabled:
            logger.warning(f"Lead capture not enabled for account {account_id}, but accepting lead anyway")
        
        # Record rate limit entry
        record_rate_limit(cur, client_ip, str(report_id))
        
        # Store the lead
        cur.execute("""
            INSERT INTO leads (
                account_id,
                property_report_id,
                name,
                email,
                phone,
                message,
                source,
                consent_given,
                status,
                ip_address,
                user_agent
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'new', %s, %s)
            RETURNING id::text
        """, (
            account_id,
            report_id,
            payload.name,
            payload.email,
            payload.phone,
            payload.message,
            payload.source,
            payload.consent_given,
            client_ip,
            user_agent,
        ))
        
        lead_id = cur.fetchone()[0]
        logger.info(f"Lead {lead_id} captured for property report {report_id} from IP {client_ip}")
        
        # Update landing page analytics
        update_landing_page_analytics(cur, str(report_id), client_ip)
        
        # Send SMS notification if credits available
        sms_sent = False
        if sms_credits and sms_credits > 0 and twilio_is_configured():
            # Get agent's phone number
            cur.execute("""
                SELECT phone FROM users WHERE id = %s
            """, (user_id,))
            
            user_row = cur.fetchone()
            agent_phone = user_row[0] if user_row else None
            
            if agent_phone:
                formatted_phone = format_phone_e164(agent_phone)
                
                if formatted_phone:
                    try:
                        full_address = f"{property_address}, {property_city}, {property_state}"
                        
                        await send_lead_notification_sms(
                            to_phone=formatted_phone,
                            lead_name=payload.name,
                            property_address=full_address,
                            lead_phone=payload.phone,
                            lead_email=payload.email,
                        )
                        
                        # Decrement SMS credits
                        cur.execute("""
                            UPDATE accounts
                            SET sms_credits = sms_credits - 1
                            WHERE id = %s AND sms_credits > 0
                        """, (account_id,))
                        
                        # Update lead with SMS sent timestamp
                        cur.execute("""
                            UPDATE leads
                            SET sms_sent_at = NOW()
                            WHERE id = %s::uuid
                        """, (lead_id,))
                        
                        sms_sent = True
                        logger.info(f"SMS notification sent for lead {lead_id}")
                        
                    except TwilioSMSError as e:
                        logger.error(f"Failed to send SMS for lead {lead_id}: {e}")
                else:
                    logger.warning(f"Agent phone number invalid format: {agent_phone[:4]}***")
            else:
                logger.warning(f"No phone number found for user {user_id}")
        
        conn.commit()
    
    return LeadCaptureResponse(
        success=True,
        message="Thank you! We'll be in touch soon."
    )


# ============================================================================
# Authenticated Endpoints
# ============================================================================


@router.get("/leads")
def list_leads(
    request: Request,
    status: Optional[Literal["new", "contacted", "converted"]] = None,
    property_report_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List leads for current account.
    
    Supports filtering by status and property_report_id.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Build query with optional filters
        where_clauses = ["l.account_id = %s::uuid"]
        params = [account_id]
        
        if status:
            where_clauses.append("l.status = %s")
            params.append(status)
        
        if property_report_id:
            where_clauses.append("l.property_report_id = %s::uuid")
            params.append(property_report_id)
        
        where_sql = " AND ".join(where_clauses)
        
        # Get total count
        cur.execute(f"""
            SELECT COUNT(*) FROM leads l
            WHERE {where_sql}
        """, params)
        total = cur.fetchone()[0]
        
        # Get leads with property info
        params.extend([limit, offset])
        cur.execute(f"""
            SELECT 
                l.id::text,
                l.account_id::text,
                l.property_report_id::text,
                l.name,
                l.email,
                l.phone,
                l.message,
                l.source,
                l.consent_given,
                l.sms_sent_at::text,
                l.email_sent_at::text,
                l.status,
                l.notes,
                l.ip_address,
                l.created_at::text,
                l.updated_at::text,
                pr.property_address,
                pr.property_city,
                pr.property_state
            FROM leads l
            LEFT JOIN property_reports pr ON l.property_report_id = pr.id
            WHERE {where_sql}
            ORDER BY l.created_at DESC
            LIMIT %s OFFSET %s
        """, params)
        
        leads = []
        for row in cur.fetchall():
            property_address = None
            if row[16]:  # property_address exists
                property_address = f"{row[16]}, {row[17] or ''}, {row[18] or ''}".strip(", ")
            
            leads.append({
                "id": row[0],
                "account_id": row[1],
                "property_report_id": row[2],
                "name": row[3],
                "email": row[4],
                "phone": row[5],
                "message": row[6],
                "source": row[7],
                "consent_given": row[8],
                "sms_sent_at": row[9],
                "email_sent_at": row[10],
                "status": row[11],
                "notes": row[12],
                "ip_address": row[13],
                "created_at": row[14],
                "updated_at": row[15],
                "property_address": property_address,
            })
    
    return {
        "leads": leads,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/leads/export/csv")
def export_leads_csv(
    request: Request,
    status: Optional[Literal["new", "contacted", "converted"]] = None,
):
    """
    Export all leads as CSV download.
    """
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Build query
        where_clauses = ["l.account_id = %s::uuid"]
        params = [account_id]
        
        if status:
            where_clauses.append("l.status = %s")
            params.append(status)
        
        where_sql = " AND ".join(where_clauses)
        
        cur.execute(f"""
            SELECT 
                l.id::text,
                l.name,
                l.email,
                l.phone,
                l.message,
                l.source,
                l.consent_given,
                l.status,
                l.created_at::text,
                pr.property_address,
                pr.property_city,
                pr.property_state,
                pr.property_zip
            FROM leads l
            LEFT JOIN property_reports pr ON l.property_report_id = pr.id
            WHERE {where_sql}
            ORDER BY l.created_at DESC
        """, params)
        
        rows = cur.fetchall()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "ID",
        "Name",
        "Email",
        "Phone",
        "Message",
        "Source",
        "Consent Given",
        "Status",
        "Created At",
        "Property Address",
        "Property City",
        "Property State",
        "Property ZIP",
    ])
    
    # Data rows
    for row in rows:
        writer.writerow([
            row[0],
            row[1] or "",
            row[2] or "",
            row[3] or "",
            row[4] or "",
            row[5] or "",
            "Yes" if row[6] else "No",
            row[7] or "",
            row[8] or "",
            row[9] or "",
            row[10] or "",
            row[11] or "",
            row[12] or "",
        ])
    
    output.seek(0)
    
    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"leads_export_{timestamp}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/leads/{lead_id}")
def get_lead(lead_id: str, request: Request):
    """Get a single lead by ID."""
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        cur.execute("""
            SELECT 
                l.id::text,
                l.account_id::text,
                l.property_report_id::text,
                l.name,
                l.email,
                l.phone,
                l.message,
                l.source,
                l.consent_given,
                l.sms_sent_at::text,
                l.email_sent_at::text,
                l.status,
                l.notes,
                l.ip_address,
                l.created_at::text,
                l.updated_at::text,
                pr.property_address,
                pr.property_city,
                pr.property_state
            FROM leads l
            LEFT JOIN property_reports pr ON l.property_report_id = pr.id
            WHERE l.id = %s::uuid AND l.account_id = %s::uuid
        """, (lead_id, account_id))
        
        row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    property_address = None
    if row[16]:
        property_address = f"{row[16]}, {row[17] or ''}, {row[18] or ''}".strip(", ")
    
    return {
        "id": row[0],
        "account_id": row[1],
        "property_report_id": row[2],
        "name": row[3],
        "email": row[4],
        "phone": row[5],
        "message": row[6],
        "source": row[7],
        "consent_given": row[8],
        "sms_sent_at": row[9],
        "email_sent_at": row[10],
        "status": row[11],
        "notes": row[12],
        "ip_address": row[13],
        "created_at": row[14],
        "updated_at": row[15],
        "property_address": property_address,
    }


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: str, updates: LeadUpdate, request: Request):
    """Update a lead's status or notes."""
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Build dynamic UPDATE
        fields = []
        values = []
        
        if updates.status is not None:
            fields.append("status = %s")
            values.append(updates.status)
        
        if updates.notes is not None:
            fields.append("notes = %s")
            values.append(updates.notes)
        
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        fields.append("updated_at = NOW()")
        values.extend([lead_id, account_id])
        
        cur.execute(f"""
            UPDATE leads
            SET {', '.join(fields)}
            WHERE id = %s::uuid AND account_id = %s::uuid
            RETURNING 
                id::text,
                account_id::text,
                property_report_id::text,
                name,
                email,
                phone,
                message,
                source,
                consent_given,
                sms_sent_at::text,
                email_sent_at::text,
                status,
                notes,
                ip_address,
                created_at::text,
                updated_at::text
        """, values)
        
        row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        "id": row[0],
        "account_id": row[1],
        "property_report_id": row[2],
        "name": row[3],
        "email": row[4],
        "phone": row[5],
        "message": row[6],
        "source": row[7],
        "consent_given": row[8],
        "sms_sent_at": row[9],
        "email_sent_at": row[10],
        "status": row[11],
        "notes": row[12],
        "ip_address": row[13],
        "created_at": row[14],
        "updated_at": row[15],
    }


@router.delete("/leads/{lead_id}")
def delete_lead(lead_id: str, request: Request):
    """Delete a lead."""
    account_id = require_account_id(request)
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        cur.execute("""
            DELETE FROM leads
            WHERE id = %s::uuid AND account_id = %s::uuid
            RETURNING id
        """, (lead_id, account_id))
        
        deleted = cur.fetchone()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"ok": True, "deleted_id": lead_id}

