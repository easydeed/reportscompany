"""
Lead Pages Public API

Consumer-facing endpoints for the lead capture flow.
NO AUTHENTICATION REQUIRED for these endpoints.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, field_validator
from typing import Optional, List
import json
import re
import logging

from ..db import db_conn, set_rls
from ..services.agent_code import get_agent_by_code, increment_landing_page_visits
from ..services.sitex import lookup_property

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/cma", tags=["lead-pages"])


# =============================================
# SCHEMAS
# =============================================

class AgentLandingPageInfo(BaseModel):
    """Agent info displayed on landing page."""
    name: str
    photo_url: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    headline: str
    subheadline: str
    theme_color: str
    logo_url: Optional[str] = None
    website_url: Optional[str] = None


class PropertySearchRequest(BaseModel):
    """Consumer searching for their property."""
    address: str
    city: Optional[str] = None
    state: Optional[str] = None


class PropertySearchResult(BaseModel):
    """Property from SiteX search."""
    apn: str
    fips: str
    address: str
    city: str
    state: str
    zip: str
    owner_name: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None


class ReportRequestPayload(BaseModel):
    """Consumer requesting their report. Accepts phone OR email."""
    phone: Optional[str] = None
    email: Optional[str] = None
    delivery_method: str = "sms"  # "sms" or "email"
    property_apn: str
    property_fips: str
    property_address: str
    property_city: str
    property_state: str
    property_zip: str
    consent_given: bool = False
    name: Optional[str] = None
    owner_name: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    lot_size: Optional[int] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        digits = re.sub(r'\D', '', v)
        if len(digits) != 10:
            raise ValueError('Phone must be 10 digits')
        return digits


# =============================================
# HELPER FUNCTIONS
# =============================================

def detect_device_type(user_agent: str) -> str:
    """Simple device detection."""
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'


# =============================================
# ENDPOINTS
# =============================================

@router.get("/{agent_code}", response_model=AgentLandingPageInfo)
async def get_landing_page_info(
    agent_code: str,
    request: Request,
):
    """
    Get agent info for rendering the landing page.
    Called when consumer visits: /cma/{agent_code}
    """
    with db_conn() as (conn, cur):
        agent = get_agent_by_code(cur, agent_code)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if not agent.get("landing_page_enabled", True):
            raise HTTPException(status_code=410, detail="This page is currently unavailable")
        
        # Track visit
        increment_landing_page_visits(conn, cur, agent_code)
        
        return AgentLandingPageInfo(
            name=agent.get("full_name", ""),
            photo_url=agent.get("photo_url"),
            company_name=agent.get("company_name"),
            phone=agent.get("phone"),
            email=agent.get("email"),
            license_number=agent.get("license_number"),
            headline=agent.get("landing_page_headline", "What's Your Home Worth?"),
            subheadline=agent.get("landing_page_subheadline", "Get a free, professional property report in seconds."),
            theme_color=agent.get("landing_page_theme_color", "#8B5CF6"),
            logo_url=agent.get("logo_url"),
            website_url=agent.get("website_url"),
        )


@router.post("/{agent_code}/search", response_model=List[PropertySearchResult])
async def search_property(
    agent_code: str,
    payload: PropertySearchRequest,
):
    """
    Search for properties by address.
    Consumer enters their address, we find matching properties.
    """
    with db_conn() as (conn, cur):
        # Validate agent exists
        agent = get_agent_by_code(cur, agent_code)
        if not agent:
            raise HTTPException(status_code=404, detail="Invalid agent code")
        
        if not agent.get("landing_page_enabled", True):
            raise HTTPException(status_code=410, detail="This page is currently unavailable")
    
    # Build city_state_zip for SiteX
    city_state_zip = ""
    if payload.city or payload.state:
        city_state_zip = f"{payload.city or ''}, {payload.state or 'CA'}"
    
    # Search via SiteX
    try:
        property_data = await lookup_property(
            address=payload.address,
            city_state_zip=city_state_zip
        )
        
        if not property_data:
            return []
        
        # Return single result wrapped in list
        return [PropertySearchResult(
            apn=property_data.apn or "",
            fips=property_data.fips or "",
            address=property_data.street or property_data.full_address,
            city=property_data.city or "",
            state=property_data.state or "CA",
            zip=property_data.zip_code or "",
            owner_name=property_data.owner_name,
            bedrooms=property_data.bedrooms,
            bathrooms=property_data.bathrooms,
            sqft=property_data.sqft,
            year_built=property_data.year_built,
        )]
        
    except Exception as e:
        logger.error(f"Property search error: {e}")
        raise HTTPException(status_code=500, detail="Property search failed")


@router.post("/{agent_code}/request")
async def request_report(
    agent_code: str,
    payload: ReportRequestPayload,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Consumer requests their home value report.
    Accepts phone (SMS) or email delivery. Also writes to unified leads table.
    """
    if payload.delivery_method == "sms" and not payload.phone:
        raise HTTPException(status_code=422, detail="Phone number required for SMS delivery")
    if payload.delivery_method == "email" and not payload.email:
        raise HTTPException(status_code=422, detail="Email required for email delivery")

    with db_conn() as (conn, cur):
        agent = get_agent_by_code(cur, agent_code)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Invalid agent code")
        
        if not agent.get("landing_page_enabled", True):
            raise HTTPException(status_code=410, detail="This page is currently unavailable")
        
        agent_id = agent.get("id")
        account_id = agent.get("account_id")
        
        cur.execute(
            "SELECT sms_credits FROM accounts WHERE id = %s",
            (account_id,)
        )
        result = cur.fetchone()
        sms_credits = result[0] if result else 0
        
        ip = request.client.host if request.client else None
        if ip:
            cur.execute(
                """
                SELECT COUNT(*) FROM consumer_reports 
                WHERE ip_address = %s AND created_at > NOW() - INTERVAL '1 hour'
                """,
                (ip,)
            )
            recent_count = cur.fetchone()[0]
            if recent_count >= 5:
                raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        
        user_agent = request.headers.get("user-agent", "")
        device_type = detect_device_type(user_agent)
        
        property_data = {
            "address": payload.property_address,
            "city": payload.property_city,
            "state": payload.property_state,
            "zip": payload.property_zip,
            "apn": payload.property_apn,
            "fips": payload.property_fips,
            "owner_name": payload.owner_name,
            "bedrooms": payload.bedrooms,
            "bathrooms": payload.bathrooms,
            "sqft": payload.sqft,
            "year_built": payload.year_built,
            "lot_size": payload.lot_size,
        }
        property_data = {k: v for k, v in property_data.items() if v is not None}
        
        # Create consumer_report record (tracks the generated PDF/data)
        cur.execute(
            """
            INSERT INTO consumer_reports (
                agent_id, agent_code, consumer_phone, consumer_email,
                delivery_method,
                property_address, property_city, property_state, property_zip,
                property_data,
                consent_given, consent_timestamp,
                ip_address, user_agent, device_type, status
            ) VALUES (
                %s, %s, %s, %s,
                %s,
                %s, %s, %s, %s,
                %s::jsonb,
                %s, NOW(),
                %s, %s, %s, 'pending'
            )
            RETURNING id
            """,
            (
                agent_id,
                agent_code.upper(),
                payload.phone,
                payload.email,
                payload.delivery_method,
                payload.property_address,
                payload.property_city,
                payload.property_state,
                payload.property_zip,
                json.dumps(property_data),
                payload.consent_given,
                ip,
                user_agent[:500] if user_agent else None,
                device_type,
            )
        )
        report_id = cur.fetchone()[0]

        # Also write to unified leads table
        full_address = f"{payload.property_address}, {payload.property_city}, {payload.property_state} {payload.property_zip}"
        cur.execute(
            """
            INSERT INTO leads (
                account_id, name, email, phone, message,
                source, consent_given, status,
                ip_address, user_agent, consumer_report_id
            ) VALUES (
                %s::uuid, %s, %s, %s, %s,
                'cma_page', %s, 'new',
                %s, %s, %s
            )
            """,
            (
                account_id,
                payload.name or payload.owner_name,
                payload.email,
                payload.phone,
                f"CMA report requested for {full_address}",
                payload.consent_given,
                ip,
                user_agent[:500] if user_agent else None,
                str(report_id),
            )
        )

        conn.commit()
        
        try:
            from celery import current_app
            current_app.send_task(
                "process_consumer_report",
                args=[str(report_id)]
            )
            logger.info(f"Queued consumer report processing: {report_id}")
        except Exception as e:
            logger.warning(f"Failed to queue task, will process inline: {e}")
        
        delivery_msg = (
            "You'll receive a text in a few seconds."
            if payload.delivery_method == "sms"
            else "Check your email for your report."
        )
        return {
            "success": True,
            "message": f"Your report is being generated! {delivery_msg}",
            "report_id": str(report_id),
        }


@router.get("/{agent_code}/settings")
async def get_landing_page_settings(agent_code: str):
    """Get landing page settings for the agent."""
    with db_conn() as (conn, cur):
        agent = get_agent_by_code(cur, agent_code)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "agent_code": agent.get("agent_code"),
            "headline": agent.get("landing_page_headline"),
            "subheadline": agent.get("landing_page_subheadline"),
            "theme_color": agent.get("landing_page_theme_color"),
            "enabled": agent.get("landing_page_enabled"),
            "visits": agent.get("landing_page_visits", 0),
        }

