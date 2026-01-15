"""
Mobile Report Viewer API Routes

Public endpoints for consumer report viewing.
No authentication required for viewing, tracks analytics.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import json
import logging

from ..db import db_conn, fetchone_dict, fetchall_dicts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/r", tags=["mobile-reports"])


# =============================================
# SCHEMAS
# =============================================

class PropertyData(BaseModel):
    address: str
    city: str
    state: str
    zip: str
    owner_name: Optional[str] = None
    apn: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tax_assessed_value: Optional[int] = None
    last_sale_date: Optional[str] = None
    last_sale_price: Optional[int] = None


class Comparable(BaseModel):
    address: str
    city: str
    state: str
    zip: str
    sold_price: int
    sold_date: str
    days_ago: int
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    price_per_sqft: int
    distance_miles: float
    photo_url: Optional[str] = None


class ValueEstimate(BaseModel):
    low: int
    mid: int
    high: int
    confidence: str  # 'high', 'medium', 'low'


class MarketStats(BaseModel):
    median_price: Optional[int] = None
    avg_price_per_sqft: Optional[int] = None
    avg_days_on_market: Optional[int] = None
    total_sold_last_6mo: Optional[int] = None
    price_trend_pct: Optional[float] = None  # e.g., +5.2 or -3.1


class AgentInfo(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    company_name: Optional[str] = None
    license_number: Optional[str] = None
    website: Optional[str] = None


class MobileReportResponse(BaseModel):
    id: str
    property: PropertyData
    comparables: List[Comparable]
    value_estimate: ValueEstimate
    market_stats: MarketStats
    agent: AgentInfo
    has_pdf: bool
    created_at: datetime


class AnalyticsEvent(BaseModel):
    event_type: str  # 'tab_change', 'agent_click', 'share', 'pdf_request'
    event_data: Optional[dict] = {}
    session_id: Optional[str] = None


# =============================================
# PUBLIC ENDPOINTS
# =============================================

@router.get("/{report_id}/data", response_model=MobileReportResponse)
async def get_report_data(
    report_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Get report data as JSON for client-side rendering.
    Tracks view analytics.
    """
    with db_conn() as (conn, cur):
        cur.execute(
            """
            SELECT 
                cr.*,
                CONCAT(u.first_name, ' ', u.last_name) as agent_name,
                u.phone as agent_phone,
                u.email as agent_email,
                u.avatar_url as agent_photo,
                u.company_name
            FROM consumer_reports cr
            JOIN users u ON cr.agent_id = u.id
            WHERE cr.id = %s AND cr.status IN ('ready', 'sent')
            """,
            (str(report_id),)
        )
        report = fetchone_dict(cur)
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Track view in background
    background_tasks.add_task(
        track_view,
        str(report_id),
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
        detect_device_type(request.headers.get("user-agent", ""))
    )
    
    # Parse JSON fields
    property_data = report.get("property_data") or {}
    if isinstance(property_data, str):
        property_data = json.loads(property_data)
    
    comparables = report.get("comparables") or []
    if isinstance(comparables, str):
        comparables = json.loads(comparables)
    
    value_estimate = report.get("value_estimate") or {}
    if isinstance(value_estimate, str):
        value_estimate = json.loads(value_estimate)
    
    market_stats = report.get("market_stats") or {}
    if isinstance(market_stats, str):
        market_stats = json.loads(market_stats)
    
    # Build property data with fallbacks
    prop = PropertyData(
        address=property_data.get("address") or report.get("property_address", ""),
        city=property_data.get("city") or report.get("property_city", ""),
        state=property_data.get("state") or report.get("property_state", ""),
        zip=property_data.get("zip") or report.get("property_zip", ""),
        owner_name=property_data.get("owner_name"),
        apn=property_data.get("apn"),
        bedrooms=property_data.get("bedrooms"),
        bathrooms=property_data.get("bathrooms"),
        sqft=property_data.get("sqft"),
        lot_size=property_data.get("lot_size"),
        year_built=property_data.get("year_built"),
        property_type=property_data.get("property_type"),
        latitude=property_data.get("latitude"),
        longitude=property_data.get("longitude"),
        tax_assessed_value=property_data.get("tax_assessed_value"),
        last_sale_date=property_data.get("last_sale_date"),
        last_sale_price=property_data.get("last_sale_price")
    )
    
    # Build comparables list
    comp_list = []
    for c in comparables:
        try:
            comp_list.append(Comparable(
                address=c.get("address", ""),
                city=c.get("city", ""),
                state=c.get("state", ""),
                zip=c.get("zip", ""),
                sold_price=c.get("sold_price") or c.get("soldPrice") or 0,
                sold_date=c.get("sold_date") or c.get("soldDate") or "",
                days_ago=c.get("days_ago") or c.get("daysAgo") or 0,
                bedrooms=c.get("bedrooms") or 0,
                bathrooms=c.get("bathrooms") or 0,
                sqft=c.get("sqft") or 0,
                lot_size=c.get("lot_size") or c.get("lotSize"),
                year_built=c.get("year_built") or c.get("yearBuilt"),
                price_per_sqft=c.get("price_per_sqft") or c.get("pricePerSqft") or 0,
                distance_miles=c.get("distance_miles") or c.get("distanceMiles") or 0,
                photo_url=c.get("photo_url") or c.get("photoUrl")
            ))
        except Exception as e:
            logger.warning(f"Error parsing comparable: {e}")
            continue
    
    # Build value estimate
    val_est = ValueEstimate(
        low=value_estimate.get("low") or 0,
        mid=value_estimate.get("mid") or 0,
        high=value_estimate.get("high") or 0,
        confidence=value_estimate.get("confidence") or "low"
    )
    
    # Build market stats
    mkt_stats = MarketStats(
        median_price=market_stats.get("median_price"),
        avg_price_per_sqft=market_stats.get("avg_price_per_sqft"),
        avg_days_on_market=market_stats.get("avg_days_on_market"),
        total_sold_last_6mo=market_stats.get("total_sold_last_6mo"),
        price_trend_pct=market_stats.get("price_trend_pct")
    )
    
    # Build agent info
    agent = AgentInfo(
        name=report.get("agent_name") or "",
        phone=report.get("agent_phone"),
        email=report.get("agent_email"),
        photo_url=report.get("agent_photo"),
        company_name=report.get("company_name")
    )
    
    return MobileReportResponse(
        id=str(report["id"]),
        property=prop,
        comparables=comp_list,
        value_estimate=val_est,
        market_stats=mkt_stats,
        agent=agent,
        has_pdf=report.get("pdf_url") is not None,
        created_at=report["created_at"]
    )


@router.post("/{report_id}/pdf")
async def generate_pdf_on_demand(
    report_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Generate PDF on demand when user clicks download.
    Returns existing PDF URL if already generated.
    """
    with db_conn() as (conn, cur):
        cur.execute(
            "SELECT id, pdf_url, property_data, comparables, agent_id FROM consumer_reports WHERE id = %s",
            (str(report_id),)
        )
        report = fetchone_dict(cur)
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Return existing PDF if available
    if report.get("pdf_url"):
        with db_conn() as (conn, cur):
            cur.execute(
                "UPDATE consumer_reports SET pdf_requested_count = pdf_requested_count + 1 WHERE id = %s",
                (str(report_id),)
            )
            conn.commit()
        return {"pdf_url": report["pdf_url"], "status": "ready"}
    
    # Queue PDF generation (Celery task)
    # For now, we'll return a "generating" status
    # The actual PDF generation will be handled by the worker
    background_tasks.add_task(
        track_event,
        str(report_id),
        "pdf_request",
        {},
        request.client.host if request.client else None,
        request.headers.get("user-agent")
    )
    
    return {
        "status": "generating",
        "message": "PDF is being generated. This may take a few seconds."
    }


@router.get("/{report_id}/pdf/status")
async def check_pdf_status(report_id: UUID):
    """
    Check if PDF has been generated (for polling).
    """
    with db_conn() as (conn, cur):
        cur.execute(
            "SELECT pdf_url FROM consumer_reports WHERE id = %s",
            (str(report_id),)
        )
        report = fetchone_dict(cur)
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    if report.get("pdf_url"):
        return {"status": "ready", "pdf_url": report["pdf_url"]}
    else:
        return {"status": "generating"}


@router.post("/{report_id}/analytics")
async def track_analytics(
    report_id: UUID,
    event: AnalyticsEvent,
    request: Request
):
    """
    Track user interactions (tab changes, agent clicks, etc.)
    """
    with db_conn() as (conn, cur):
        # Validate report exists
        cur.execute(
            "SELECT 1 FROM consumer_reports WHERE id = %s",
            (str(report_id),)
        )
        if not cur.fetchone():
            raise HTTPException(404, "Report not found")
    
    # Track event
    await track_event(
        str(report_id),
        event.event_type,
        event.event_data or {},
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
        event.session_id
    )
    
    # Update report record for quick stats
    with db_conn() as (conn, cur):
        if event.event_type == "agent_click":
            cur.execute(
                """
                UPDATE consumer_reports 
                SET agent_contact_clicked = true, 
                    agent_contact_type = %s
                WHERE id = %s
                """,
                (event.event_data.get("contact_type"), str(report_id))
            )
            conn.commit()
        elif event.event_type == "tab_change":
            cur.execute(
                """
                UPDATE consumer_reports 
                SET tabs_viewed = tabs_viewed || %s::jsonb
                WHERE id = %s
                """,
                (json.dumps([event.event_data.get("tab")]), str(report_id))
            )
            conn.commit()
    
    return {"success": True}


# =============================================
# HELPER FUNCTIONS
# =============================================

async def track_view(report_id: str, ip: str, user_agent: str, device_type: str):
    """Track page view and update counters."""
    try:
        with db_conn() as (conn, cur):
            cur.execute(
                """
                UPDATE consumer_reports SET
                    view_count = view_count + 1,
                    first_viewed_at = COALESCE(first_viewed_at, NOW()),
                    last_viewed_at = NOW(),
                    device_type = COALESCE(device_type, %s)
                WHERE id = %s
                """,
                (device_type, report_id)
            )
            conn.commit()
            
            cur.execute(
                """
                INSERT INTO report_analytics (report_id, event_type, ip_address, user_agent, device_type)
                VALUES (%s, 'view', %s, %s, %s)
                """,
                (report_id, ip, user_agent, device_type)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to track view: {e}")


async def track_event(report_id: str, event_type: str, event_data: dict, 
                      ip: str = None, user_agent: str = None, session_id: str = None):
    """Track analytics event."""
    try:
        with db_conn() as (conn, cur):
            cur.execute(
                """
                INSERT INTO report_analytics (report_id, event_type, event_data, ip_address, user_agent, session_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (report_id, event_type, json.dumps(event_data), ip, user_agent, session_id)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to track event: {e}")


def detect_device_type(user_agent: str) -> str:
    """Simple device detection from user agent."""
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'

