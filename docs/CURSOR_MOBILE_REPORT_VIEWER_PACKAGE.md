# Cursor Implementation Package: Mobile Report Viewer

## Overview

Replace PDF-first approach with mobile-first web experience. PDF generated only on demand.

**Key Principle:** Fast to SMS, beautiful on mobile, PDF only when requested.

```
OLD: Request → Generate PDF (10s) → SMS → User ignores PDF
NEW: Request → Store JSON (instant) → SMS → Mobile view → PDF if clicked
```

---

## Part 1: Database Schema

### File: `apps/api/migrations/0037_mobile_reports.sql`

```sql
-- =============================================
-- CONSUMER REPORTS TABLE (Updated)
-- =============================================

CREATE TABLE IF NOT EXISTS consumer_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent link
    agent_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    agent_code VARCHAR(10) NOT NULL,
    
    -- Consumer info (the lead)
    consumer_phone VARCHAR(20) NOT NULL,
    consumer_email VARCHAR(255),
    consent_given BOOLEAN DEFAULT false,
    consent_timestamp TIMESTAMPTZ,
    
    -- Property data (JSON - powers mobile view)
    property_address TEXT NOT NULL,
    property_city VARCHAR(100),
    property_state VARCHAR(2),
    property_zip VARCHAR(10),
    property_data JSONB NOT NULL DEFAULT '{}',      -- Full SiteX response
    comparables JSONB NOT NULL DEFAULT '[]',        -- Auto-selected comps
    market_stats JSONB DEFAULT '{}',                -- Area statistics
    value_estimate JSONB DEFAULT '{}',              -- Low/mid/high range
    
    -- Report status
    status VARCHAR(20) DEFAULT 'pending',           -- pending, ready, failed
    error_message TEXT,
    
    -- PDF (only generated on demand)
    pdf_url TEXT,                                   -- NULL until requested
    pdf_generated_at TIMESTAMPTZ,                   -- When PDF was created
    pdf_requested_count INTEGER DEFAULT 0,          -- How many times downloaded
    
    -- SMS tracking
    consumer_sms_sent_at TIMESTAMPTZ,
    consumer_sms_sid VARCHAR(50),
    agent_sms_sent_at TIMESTAMPTZ,
    agent_sms_sid VARCHAR(50),
    
    -- Engagement metrics
    view_count INTEGER DEFAULT 0,                   -- Mobile page views
    unique_views INTEGER DEFAULT 0,                 -- Unique visitors
    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,
    tabs_viewed JSONB DEFAULT '[]',                 -- Which tabs user viewed
    time_on_page INTEGER DEFAULT 0,                 -- Seconds spent
    agent_contact_clicked BOOLEAN DEFAULT false,    -- Did they tap call/text?
    agent_contact_type VARCHAR(20),                 -- 'call', 'text', 'email'
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),                        -- 'mobile', 'tablet', 'desktop'
    referrer TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_consumer_reports_agent ON consumer_reports(agent_id);
CREATE INDEX idx_consumer_reports_code ON consumer_reports(agent_code);
CREATE INDEX idx_consumer_reports_status ON consumer_reports(status);
CREATE INDEX idx_consumer_reports_created ON consumer_reports(created_at DESC);

-- =============================================
-- REPORT ANALYTICS TABLE (Detailed tracking)
-- =============================================

CREATE TABLE report_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES consumer_reports(id) ON DELETE CASCADE,
    
    -- Event tracking
    event_type VARCHAR(50) NOT NULL,    -- 'view', 'tab_change', 'pdf_request', 'agent_click', 'share'
    event_data JSONB DEFAULT '{}',       -- Additional event details
    
    -- Session info
    session_id VARCHAR(100),
    
    -- Device/location
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_report_analytics_report ON report_analytics(report_id);
CREATE INDEX idx_report_analytics_type ON report_analytics(event_type);
CREATE INDEX idx_report_analytics_created ON report_analytics(created_at DESC);

-- =============================================
-- ADMIN METRICS VIEWS
-- =============================================

-- Daily metrics summary
CREATE OR REPLACE VIEW admin_daily_metrics AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as reports_requested,
    COUNT(*) FILTER (WHERE status = 'ready') as reports_ready,
    COUNT(*) FILTER (WHERE status = 'failed') as reports_failed,
    COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdfs_generated,
    COUNT(*) FILTER (WHERE agent_contact_clicked = true) as agent_contacts,
    SUM(view_count) as total_views,
    AVG(view_count) as avg_views_per_report,
    AVG(time_on_page) as avg_time_seconds,
    COUNT(DISTINCT agent_id) as unique_agents
FROM consumer_reports
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Agent leaderboard
CREATE OR REPLACE VIEW admin_agent_leaderboard AS
SELECT 
    u.id as agent_id,
    u.full_name as agent_name,
    u.email as agent_email,
    a.name as account_name,
    COUNT(cr.id) as total_reports,
    COUNT(cr.id) FILTER (WHERE cr.created_at > NOW() - INTERVAL '30 days') as reports_30d,
    SUM(cr.view_count) as total_views,
    COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true) as contacts,
    ROUND(
        COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true)::numeric / 
        NULLIF(COUNT(cr.id), 0) * 100, 1
    ) as contact_rate_pct,
    COUNT(cr.id) FILTER (WHERE cr.pdf_url IS NOT NULL) as pdfs_downloaded
FROM users u
JOIN accounts a ON u.account_id = a.id
LEFT JOIN consumer_reports cr ON cr.agent_id = u.id
WHERE u.ref_code IS NOT NULL
GROUP BY u.id, u.full_name, u.email, a.name
ORDER BY total_reports DESC;

-- Hourly distribution (for load planning)
CREATE OR REPLACE VIEW admin_hourly_distribution AS
SELECT 
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as report_count,
    COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdf_count
FROM consumer_reports
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;
```

---

## Part 2: API Endpoints

### File: `apps/api/src/api/routes/mobile_reports.py`

```python
"""
Mobile Report Viewer API Routes

Public endpoints for consumer report viewing.
No authentication required for viewing, tracks analytics.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import json

router = APIRouter(prefix="/v1/r", tags=["mobile-reports"])


# =============================================
# SCHEMAS
# =============================================

class PropertyData(BaseModel):
    address: str
    city: str
    state: str
    zip: str
    owner_name: Optional[str]
    apn: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    sqft: Optional[int]
    lot_size: Optional[int]
    year_built: Optional[int]
    property_type: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    tax_assessed_value: Optional[int]
    last_sale_date: Optional[str]
    last_sale_price: Optional[int]


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
    lot_size: Optional[int]
    year_built: Optional[int]
    price_per_sqft: int
    distance_miles: float
    photo_url: Optional[str]


class ValueEstimate(BaseModel):
    low: int
    mid: int
    high: int
    confidence: str  # 'high', 'medium', 'low'


class MarketStats(BaseModel):
    median_price: Optional[int]
    avg_price_per_sqft: Optional[int]
    avg_days_on_market: Optional[int]
    total_sold_last_6mo: Optional[int]
    price_trend_pct: Optional[float]  # e.g., +5.2 or -3.1


class AgentInfo(BaseModel):
    name: str
    phone: Optional[str]
    email: Optional[str]
    photo_url: Optional[str]
    company_name: Optional[str]
    license_number: Optional[str]
    website: Optional[str]


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
    session_id: Optional[str]


# =============================================
# PUBLIC ENDPOINTS
# =============================================

@router.get("/{report_id}")
async def get_mobile_report_page(
    report_id: UUID,
    request: Request,
    db = Depends(get_db)
):
    """
    Server-side rendered mobile report page.
    This returns the full Next.js page - see frontend section.
    """
    # This endpoint is handled by Next.js SSR
    # See: apps/web/app/r/[id]/page.tsx
    pass


@router.get("/{report_id}/data", response_model=MobileReportResponse)
async def get_report_data(
    report_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Get report data as JSON for client-side rendering.
    Tracks view analytics.
    """
    report = await db.fetchrow(
        """
        SELECT 
            cr.*,
            u.full_name as agent_name,
            u.phone as agent_phone,
            u.email as agent_email,
            u.photo_url as agent_photo,
            u.company_name,
            u.license_number,
            u.website
        FROM consumer_reports cr
        JOIN users u ON cr.agent_id = u.id
        WHERE cr.id = $1 AND cr.status = 'ready'
        """,
        str(report_id)
    )
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Track view in background
    background_tasks.add_task(
        track_view,
        db,
        str(report_id),
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
        detect_device_type(request.headers.get("user-agent", ""))
    )
    
    # Parse JSON fields
    property_data = json.loads(report["property_data"]) if isinstance(report["property_data"], str) else report["property_data"]
    comparables = json.loads(report["comparables"]) if isinstance(report["comparables"], str) else report["comparables"]
    value_estimate = json.loads(report["value_estimate"]) if isinstance(report["value_estimate"], str) else report["value_estimate"]
    market_stats = json.loads(report["market_stats"]) if isinstance(report["market_stats"], str) else report["market_stats"]
    
    return MobileReportResponse(
        id=str(report["id"]),
        property=PropertyData(**property_data),
        comparables=[Comparable(**c) for c in comparables],
        value_estimate=ValueEstimate(**value_estimate) if value_estimate else ValueEstimate(low=0, mid=0, high=0, confidence='low'),
        market_stats=MarketStats(**market_stats) if market_stats else MarketStats(),
        agent=AgentInfo(
            name=report["agent_name"],
            phone=report["agent_phone"],
            email=report["agent_email"],
            photo_url=report["agent_photo"],
            company_name=report["company_name"],
            license_number=report["license_number"],
            website=report["website"]
        ),
        has_pdf=report["pdf_url"] is not None,
        created_at=report["created_at"]
    )


@router.post("/{report_id}/pdf")
async def generate_pdf_on_demand(
    report_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Generate PDF on demand when user clicks download.
    Returns existing PDF URL if already generated.
    """
    report = await db.fetchrow(
        "SELECT id, pdf_url, property_data, comparables, agent_id FROM consumer_reports WHERE id = $1",
        str(report_id)
    )
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Return existing PDF if available
    if report["pdf_url"]:
        # Increment download count
        await db.execute(
            "UPDATE consumer_reports SET pdf_requested_count = pdf_requested_count + 1 WHERE id = $1",
            str(report_id)
        )
        return {"pdf_url": report["pdf_url"], "status": "ready"}
    
    # Queue PDF generation
    from ..tasks import generate_pdf_task
    task = generate_pdf_task.delay(str(report_id))
    
    # Track analytics
    background_tasks.add_task(
        track_event,
        db,
        str(report_id),
        "pdf_request",
        {},
        request.client.host if request.client else None,
        request.headers.get("user-agent")
    )
    
    return {
        "status": "generating",
        "task_id": task.id,
        "message": "PDF is being generated. This may take a few seconds."
    }


@router.get("/{report_id}/pdf/status")
async def check_pdf_status(
    report_id: UUID,
    db = Depends(get_db)
):
    """
    Check if PDF has been generated (for polling).
    """
    report = await db.fetchrow(
        "SELECT pdf_url FROM consumer_reports WHERE id = $1",
        str(report_id)
    )
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    if report["pdf_url"]:
        return {"status": "ready", "pdf_url": report["pdf_url"]}
    else:
        return {"status": "generating"}


@router.post("/{report_id}/analytics")
async def track_analytics(
    report_id: UUID,
    event: AnalyticsEvent,
    request: Request,
    db = Depends(get_db)
):
    """
    Track user interactions (tab changes, agent clicks, etc.)
    """
    # Validate report exists
    exists = await db.fetchval(
        "SELECT 1 FROM consumer_reports WHERE id = $1",
        str(report_id)
    )
    if not exists:
        raise HTTPException(404, "Report not found")
    
    # Track event
    await track_event(
        db,
        str(report_id),
        event.event_type,
        event.event_data or {},
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
        event.session_id
    )
    
    # Update report record for quick stats
    if event.event_type == "agent_click":
        await db.execute(
            """
            UPDATE consumer_reports 
            SET agent_contact_clicked = true, 
                agent_contact_type = $2
            WHERE id = $1
            """,
            str(report_id),
            event.event_data.get("contact_type")
        )
    elif event.event_type == "tab_change":
        await db.execute(
            """
            UPDATE consumer_reports 
            SET tabs_viewed = tabs_viewed || $2::jsonb
            WHERE id = $1
            """,
            str(report_id),
            json.dumps([event.event_data.get("tab")])
        )
    
    return {"success": True}


# =============================================
# HELPER FUNCTIONS
# =============================================

async def track_view(db, report_id: str, ip: str, user_agent: str, device_type: str):
    """Track page view and update counters."""
    await db.execute(
        """
        UPDATE consumer_reports SET
            view_count = view_count + 1,
            first_viewed_at = COALESCE(first_viewed_at, NOW()),
            last_viewed_at = NOW(),
            device_type = COALESCE(device_type, $2)
        WHERE id = $1
        """,
        report_id,
        device_type
    )
    
    await db.execute(
        """
        INSERT INTO report_analytics (report_id, event_type, ip_address, user_agent, device_type)
        VALUES ($1, 'view', $2, $3, $4)
        """,
        report_id,
        ip,
        user_agent,
        device_type
    )


async def track_event(db, report_id: str, event_type: str, event_data: dict, 
                      ip: str = None, user_agent: str = None, session_id: str = None):
    """Track analytics event."""
    await db.execute(
        """
        INSERT INTO report_analytics (report_id, event_type, event_data, ip_address, user_agent, session_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        report_id,
        event_type,
        json.dumps(event_data),
        ip,
        user_agent,
        session_id
    )


def detect_device_type(user_agent: str) -> str:
    """Simple device detection from user agent."""
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'
```

---

## Part 3: Admin API Endpoints

### File: `apps/api/src/api/routes/admin_metrics.py`

```python
"""
Admin Metrics API Routes

Dashboard metrics for monitoring Lead Pages performance.
Requires admin authentication.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/v1/admin/metrics", tags=["admin-metrics"])


# =============================================
# SCHEMAS
# =============================================

class DailyMetric(BaseModel):
    date: str
    reports_requested: int
    reports_ready: int
    reports_failed: int
    pdfs_generated: int
    agent_contacts: int
    total_views: int
    avg_views_per_report: float
    avg_time_seconds: float
    unique_agents: int


class OverviewStats(BaseModel):
    # Totals
    total_reports: int
    total_views: int
    total_pdfs: int
    total_contacts: int
    
    # Rates
    pdf_rate_pct: float        # % of reports that got PDF
    contact_rate_pct: float    # % of reports that led to contact
    
    # Today
    reports_today: int
    views_today: int
    contacts_today: int
    
    # This week
    reports_this_week: int
    
    # This month
    reports_this_month: int
    
    # Trends (vs last period)
    reports_trend_pct: float   # +/- % vs previous period
    contacts_trend_pct: float


class AgentLeaderboard(BaseModel):
    agent_id: str
    agent_name: str
    agent_email: str
    account_name: str
    total_reports: int
    reports_30d: int
    total_views: int
    contacts: int
    contact_rate_pct: float
    pdfs_downloaded: int


class HourlyDistribution(BaseModel):
    hour: int
    report_count: int
    pdf_count: int


class DeviceBreakdown(BaseModel):
    device_type: str
    count: int
    percentage: float


class RecentReport(BaseModel):
    id: str
    agent_name: str
    property_address: str
    status: str
    view_count: int
    agent_contacted: bool
    has_pdf: bool
    created_at: datetime


# =============================================
# ENDPOINTS
# =============================================

@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Get high-level dashboard metrics.
    """
    # Totals
    totals = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as total_reports,
            SUM(view_count) as total_views,
            COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as total_pdfs,
            COUNT(*) FILTER (WHERE agent_contact_clicked = true) as total_contacts
        FROM consumer_reports
        """
    )
    
    # Today
    today = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as reports_today,
            SUM(view_count) as views_today,
            COUNT(*) FILTER (WHERE agent_contact_clicked = true) as contacts_today
        FROM consumer_reports
        WHERE DATE(created_at) = CURRENT_DATE
        """
    )
    
    # This week
    week = await db.fetchval(
        """
        SELECT COUNT(*) FROM consumer_reports
        WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
        """
    )
    
    # This month
    month = await db.fetchval(
        """
        SELECT COUNT(*) FROM consumer_reports
        WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
        """
    )
    
    # Previous month for trend
    prev_month = await db.fetchval(
        """
        SELECT COUNT(*) FROM consumer_reports
        WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
        AND created_at < DATE_TRUNC('month', CURRENT_DATE)
        """
    )
    
    total = totals["total_reports"] or 0
    
    return OverviewStats(
        total_reports=total,
        total_views=totals["total_views"] or 0,
        total_pdfs=totals["total_pdfs"] or 0,
        total_contacts=totals["total_contacts"] or 0,
        pdf_rate_pct=round((totals["total_pdfs"] or 0) / max(total, 1) * 100, 1),
        contact_rate_pct=round((totals["total_contacts"] or 0) / max(total, 1) * 100, 1),
        reports_today=today["reports_today"] or 0,
        views_today=today["views_today"] or 0,
        contacts_today=today["contacts_today"] or 0,
        reports_this_week=week or 0,
        reports_this_month=month or 0,
        reports_trend_pct=round(((month or 0) - (prev_month or 0)) / max(prev_month or 1, 1) * 100, 1)
            if prev_month else 0,
        contacts_trend_pct=0  # TODO: Calculate
    )


@router.get("/daily", response_model=List[DailyMetric])
async def get_daily_metrics(
    days: int = Query(30, ge=7, le=90),
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Get daily metrics for charting.
    """
    rows = await db.fetch(
        """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as reports_requested,
            COUNT(*) FILTER (WHERE status = 'ready') as reports_ready,
            COUNT(*) FILTER (WHERE status = 'failed') as reports_failed,
            COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdfs_generated,
            COUNT(*) FILTER (WHERE agent_contact_clicked = true) as agent_contacts,
            COALESCE(SUM(view_count), 0) as total_views,
            COALESCE(AVG(view_count), 0) as avg_views_per_report,
            COALESCE(AVG(time_on_page), 0) as avg_time_seconds,
            COUNT(DISTINCT agent_id) as unique_agents
        FROM consumer_reports
        WHERE created_at >= CURRENT_DATE - $1::integer
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """,
        days
    )
    
    return [DailyMetric(
        date=str(r["date"]),
        reports_requested=r["reports_requested"],
        reports_ready=r["reports_ready"],
        reports_failed=r["reports_failed"],
        pdfs_generated=r["pdfs_generated"],
        agent_contacts=r["agent_contacts"],
        total_views=r["total_views"],
        avg_views_per_report=round(r["avg_views_per_report"], 1),
        avg_time_seconds=round(r["avg_time_seconds"], 1),
        unique_agents=r["unique_agents"]
    ) for r in rows]


@router.get("/agents", response_model=List[AgentLeaderboard])
async def get_agent_leaderboard(
    limit: int = Query(20, ge=10, le=100),
    sort_by: str = Query("total_reports", regex="^(total_reports|contacts|contact_rate_pct)$"),
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Get agent leaderboard by report volume or contact rate.
    """
    rows = await db.fetch(
        f"""
        SELECT 
            u.id as agent_id,
            u.full_name as agent_name,
            u.email as agent_email,
            a.name as account_name,
            COUNT(cr.id) as total_reports,
            COUNT(cr.id) FILTER (WHERE cr.created_at > NOW() - INTERVAL '30 days') as reports_30d,
            COALESCE(SUM(cr.view_count), 0) as total_views,
            COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true) as contacts,
            ROUND(
                COUNT(cr.id) FILTER (WHERE cr.agent_contact_clicked = true)::numeric / 
                NULLIF(COUNT(cr.id), 0) * 100, 1
            ) as contact_rate_pct,
            COUNT(cr.id) FILTER (WHERE cr.pdf_url IS NOT NULL) as pdfs_downloaded
        FROM users u
        JOIN accounts a ON u.account_id = a.id
        LEFT JOIN consumer_reports cr ON cr.agent_id = u.id
        WHERE u.ref_code IS NOT NULL
        GROUP BY u.id, u.full_name, u.email, a.name
        HAVING COUNT(cr.id) > 0
        ORDER BY {sort_by} DESC
        LIMIT $1
        """,
        limit
    )
    
    return [AgentLeaderboard(**dict(r)) for r in rows]


@router.get("/hourly", response_model=List[HourlyDistribution])
async def get_hourly_distribution(
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Get hourly report distribution (last 30 days).
    Useful for understanding peak load times.
    """
    rows = await db.fetch(
        """
        SELECT 
            EXTRACT(HOUR FROM created_at)::integer as hour,
            COUNT(*) as report_count,
            COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdf_count
        FROM consumer_reports
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY EXTRACT(HOUR FROM created_at)
        ORDER BY hour
        """
    )
    
    return [HourlyDistribution(**dict(r)) for r in rows]


@router.get("/devices", response_model=List[DeviceBreakdown])
async def get_device_breakdown(
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Get device type breakdown.
    """
    total = await db.fetchval(
        "SELECT COUNT(*) FROM consumer_reports WHERE device_type IS NOT NULL"
    )
    
    rows = await db.fetch(
        """
        SELECT 
            COALESCE(device_type, 'unknown') as device_type,
            COUNT(*) as count
        FROM consumer_reports
        GROUP BY device_type
        ORDER BY count DESC
        """
    )
    
    return [DeviceBreakdown(
        device_type=r["device_type"],
        count=r["count"],
        percentage=round(r["count"] / max(total, 1) * 100, 1)
    ) for r in rows]


@router.get("/recent", response_model=List[RecentReport])
async def get_recent_reports(
    limit: int = Query(20, ge=10, le=100),
    status: Optional[str] = Query(None, regex="^(pending|ready|failed)$"),
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Get recent reports for activity feed.
    """
    rows = await db.fetch(
        """
        SELECT 
            cr.id,
            u.full_name as agent_name,
            cr.property_address,
            cr.status,
            cr.view_count,
            cr.agent_contact_clicked as agent_contacted,
            (cr.pdf_url IS NOT NULL) as has_pdf,
            cr.created_at
        FROM consumer_reports cr
        JOIN users u ON cr.agent_id = u.id
        WHERE ($2::text IS NULL OR cr.status = $2)
        ORDER BY cr.created_at DESC
        LIMIT $1
        """,
        limit,
        status
    )
    
    return [RecentReport(**dict(r)) for r in rows]


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    days: int = Query(30, ge=7, le=90),
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Get conversion funnel metrics.
    """
    data = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as total_requests,
            COUNT(*) FILTER (WHERE status = 'ready') as reports_generated,
            COUNT(*) FILTER (WHERE view_count > 0) as reports_viewed,
            COUNT(*) FILTER (WHERE view_count > 1) as reports_viewed_multiple,
            COUNT(*) FILTER (WHERE agent_contact_clicked = true) as agent_contacted,
            COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdf_downloaded
        FROM consumer_reports
        WHERE created_at >= CURRENT_DATE - $1::integer
        """,
        days
    )
    
    total = data["total_requests"] or 1
    
    return {
        "period_days": days,
        "funnel": [
            {"stage": "Reports Requested", "count": data["total_requests"], "pct": 100},
            {"stage": "Reports Generated", "count": data["reports_generated"], 
             "pct": round(data["reports_generated"] / total * 100, 1)},
            {"stage": "Reports Viewed", "count": data["reports_viewed"],
             "pct": round(data["reports_viewed"] / total * 100, 1)},
            {"stage": "Multiple Views", "count": data["reports_viewed_multiple"],
             "pct": round(data["reports_viewed_multiple"] / total * 100, 1)},
            {"stage": "Agent Contacted", "count": data["agent_contacted"],
             "pct": round(data["agent_contacted"] / total * 100, 1)},
            {"stage": "PDF Downloaded", "count": data["pdf_downloaded"],
             "pct": round(data["pdf_downloaded"] / total * 100, 1)},
        ]
    }
```

---

## Part 4: Celery Tasks (Updated)

### File: `apps/worker/src/worker/tasks/consumer_report.py`

```python
"""
Consumer Report Tasks

Fast report generation (JSON only) + on-demand PDF.
"""

from celery import shared_task
import json

from ..services.sitex import get_property_data
from ..services.simplyrets import get_comparables
from ..services.twilio_sms import send_sms
from ..services.pdf_engine import generate_property_report_pdf
from ..services.r2 import upload_to_r2
from ..db import get_db


@shared_task(
    name="process_consumer_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def process_consumer_report(self, report_id: str):
    """
    Process consumer report request - FAST (no PDF).
    
    1. Fetch property data
    2. Auto-select comparables
    3. Calculate value estimate
    4. Store JSON data
    5. Send SMS notifications
    """
    with get_db() as db:
        # Get report record with agent info
        report = db.fetchrow(
            """
            SELECT cr.*, 
                   u.full_name as agent_name, 
                   u.phone as agent_phone,
                   a.id as account_id,
                   a.sms_credits
            FROM consumer_reports cr
            JOIN users u ON cr.agent_id = u.id
            JOIN accounts a ON u.account_id = a.id
            WHERE cr.id = $1
            """,
            report_id
        )
        
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        try:
            # 1. Fetch property data from SiteX
            property_data = get_property_data(report["property_address"])
            
            # 2. Auto-select comparables
            raw_comps = get_comparables(
                lat=property_data.get("latitude"),
                lng=property_data.get("longitude"),
                sqft=property_data.get("sqft"),
                bedrooms=property_data.get("bedrooms"),
                bathrooms=property_data.get("bathrooms"),
                max_results=20
            )
            comparables = auto_select_comparables(property_data, raw_comps)
            
            # 3. Calculate value estimate
            value_estimate = calculate_value_estimate(property_data, comparables)
            
            # 4. Get market stats
            market_stats = calculate_market_stats(comparables)
            
            # 5. Store everything as JSON
            db.execute(
                """
                UPDATE consumer_reports SET
                    status = 'ready',
                    property_data = $2,
                    comparables = $3,
                    value_estimate = $4,
                    market_stats = $5,
                    updated_at = NOW()
                WHERE id = $1
                """,
                report_id,
                json.dumps(property_data),
                json.dumps(comparables),
                json.dumps(value_estimate),
                json.dumps(market_stats)
            )
            
            # 6. Send SMS to consumer (instant!)
            mobile_url = f"{settings.APP_URL}/r/{report_id}"
            consumer_msg = f"Your home value report is ready! View it here: {mobile_url}"
            
            sms_result = send_sms(
                to=f"+1{report['consumer_phone']}",
                message=consumer_msg
            )
            
            db.execute(
                """
                UPDATE consumer_reports SET 
                    consumer_sms_sent_at = NOW(),
                    consumer_sms_sid = $2
                WHERE id = $1
                """,
                report_id,
                sms_result.get("sid")
            )
            
            # 7. Send SMS to agent (if credits available)
            if report["sms_credits"] and report["sms_credits"] > 0:
                agent_msg = (
                    f"🏠 New Lead!\n"
                    f"Phone: {report['consumer_phone']}\n"
                    f"Property: {report['property_address']}\n"
                    f"View: {settings.APP_URL}/app/leads"
                )
                
                agent_sms = send_sms(
                    to=f"+1{report['agent_phone']}",
                    message=agent_msg
                )
                
                db.execute(
                    """
                    UPDATE consumer_reports SET agent_sms_sent_at = NOW(), agent_sms_sid = $2
                    WHERE id = $1
                    """,
                    report_id,
                    agent_sms.get("sid")
                )
                
                # Decrement credits
                db.execute(
                    "UPDATE accounts SET sms_credits = sms_credits - 1 WHERE id = $1",
                    report["account_id"]
                )
            
            return {"success": True, "report_id": report_id}
            
        except Exception as e:
            db.execute(
                "UPDATE consumer_reports SET status = 'failed', error_message = $2 WHERE id = $1",
                report_id,
                str(e)
            )
            raise


@shared_task(
    name="generate_pdf_on_demand",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2
)
def generate_pdf_task(self, report_id: str):
    """
    Generate PDF on demand when user clicks download.
    Only called when user explicitly requests PDF.
    """
    with get_db() as db:
        report = db.fetchrow(
            """
            SELECT cr.*, 
                   u.full_name as agent_name,
                   u.phone as agent_phone,
                   u.email as agent_email,
                   u.photo_url as agent_photo,
                   u.company_name,
                   u.license_number
            FROM consumer_reports cr
            JOIN users u ON cr.agent_id = u.id
            WHERE cr.id = $1
            """,
            report_id
        )
        
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Skip if already generated
        if report["pdf_url"]:
            return {"pdf_url": report["pdf_url"]}
        
        # Parse stored JSON
        property_data = json.loads(report["property_data"]) if isinstance(report["property_data"], str) else report["property_data"]
        comparables = json.loads(report["comparables"]) if isinstance(report["comparables"], str) else report["comparables"]
        value_estimate = json.loads(report["value_estimate"]) if isinstance(report["value_estimate"], str) else report["value_estimate"]
        
        # Build context
        context = {
            "property": property_data,
            "comparables": comparables,
            "value_estimate": value_estimate,
            "agent": {
                "name": report["agent_name"],
                "phone": report["agent_phone"],
                "email": report["agent_email"],
                "photo_url": report["agent_photo"],
                "company_name": report["company_name"],
                "license_number": report["license_number"],
            }
        }
        
        # Generate PDF
        pdf_bytes = generate_property_report_pdf(context, theme="teal")
        
        # Upload to R2
        filename = f"consumer-reports/{report_id}.pdf"
        pdf_url = upload_to_r2(pdf_bytes, filename, "application/pdf")
        
        # Update record
        db.execute(
            """
            UPDATE consumer_reports SET 
                pdf_url = $2, 
                pdf_generated_at = NOW(),
                pdf_requested_count = 1
            WHERE id = $1
            """,
            report_id,
            pdf_url
        )
        
        return {"pdf_url": pdf_url}


def auto_select_comparables(subject: dict, comps: list, max_count: int = 8) -> list:
    """
    Auto-select best comparables using Modern Agent criteria:
    - Within 2 mile radius
    - Building area ±20%
    - Bedrooms ±1
    - Bathrooms ±1
    - Sold within 12 months
    """
    subject_sqft = subject.get("sqft") or 0
    subject_beds = subject.get("bedrooms") or 0
    subject_baths = subject.get("bathrooms") or 0
    
    scored = []
    
    for comp in comps:
        score = 0
        
        # Distance scoring (max 30 pts)
        distance = comp.get("distance_miles", 10)
        if distance > 2:
            continue
        if distance <= 0.25:
            score += 30
        elif distance <= 0.5:
            score += 25
        elif distance <= 1:
            score += 20
        else:
            score += 10
        
        # Sqft scoring (max 25 pts)
        comp_sqft = comp.get("sqft") or 0
        if subject_sqft and comp_sqft:
            diff = abs(comp_sqft - subject_sqft) / subject_sqft
            if diff <= 0.1:
                score += 25
            elif diff <= 0.2:
                score += 15
            elif diff <= 0.3:
                score += 5
        
        # Bedroom scoring (max 15 pts)
        comp_beds = comp.get("bedrooms") or 0
        bed_diff = abs(comp_beds - subject_beds)
        if bed_diff == 0:
            score += 15
        elif bed_diff == 1:
            score += 10
        elif bed_diff == 2:
            score += 5
        
        # Bathroom scoring (max 15 pts)
        comp_baths = comp.get("bathrooms") or 0
        bath_diff = abs(comp_baths - subject_baths)
        if bath_diff <= 0.5:
            score += 15
        elif bath_diff <= 1:
            score += 10
        elif bath_diff <= 1.5:
            score += 5
        
        # Recency scoring (max 15 pts)
        days_ago = comp.get("days_ago", 365)
        if days_ago <= 30:
            score += 15
        elif days_ago <= 90:
            score += 12
        elif days_ago <= 180:
            score += 8
        elif days_ago <= 365:
            score += 4
        
        scored.append((score, comp))
    
    # Sort by score, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    return [comp for _, comp in scored[:max_count]]


def calculate_value_estimate(subject: dict, comps: list) -> dict:
    """Calculate property value range from comparables."""
    if not comps:
        return {"low": 0, "mid": 0, "high": 0, "confidence": "low"}
    
    subject_sqft = subject.get("sqft") or 1500
    
    # Get price per sqft from comps
    ppsf_values = [c["sold_price"] / c["sqft"] for c in comps if c.get("sqft")]
    
    if not ppsf_values:
        return {"low": 0, "mid": 0, "high": 0, "confidence": "low"}
    
    avg_ppsf = sum(ppsf_values) / len(ppsf_values)
    min_ppsf = min(ppsf_values)
    max_ppsf = max(ppsf_values)
    
    mid = int(avg_ppsf * subject_sqft)
    low = int(min_ppsf * subject_sqft)
    high = int(max_ppsf * subject_sqft)
    
    # Confidence based on comp count and variance
    variance = (max_ppsf - min_ppsf) / avg_ppsf if avg_ppsf else 1
    if len(comps) >= 6 and variance < 0.2:
        confidence = "high"
    elif len(comps) >= 4 and variance < 0.3:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "low": low,
        "mid": mid,
        "high": high,
        "confidence": confidence
    }


def calculate_market_stats(comps: list) -> dict:
    """Calculate market statistics from comparables."""
    if not comps:
        return {}
    
    prices = [c["sold_price"] for c in comps]
    ppsf = [c["sold_price"] / c["sqft"] for c in comps if c.get("sqft")]
    days = [c.get("days_on_market", 0) for c in comps if c.get("days_on_market")]
    
    return {
        "median_price": int(sorted(prices)[len(prices) // 2]) if prices else None,
        "avg_price_per_sqft": int(sum(ppsf) / len(ppsf)) if ppsf else None,
        "avg_days_on_market": int(sum(days) / len(days)) if days else None,
        "total_sold_last_6mo": len(comps),
        "price_trend_pct": None  # TODO: Calculate from historical data
    }
```

---

## Part 5: Frontend - Mobile Report Viewer

### File: `apps/web/app/r/[id]/page.tsx`

```tsx
import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { MobileReportViewer } from '@/components/mobile-report/MobileReportViewer';

interface PageProps {
  params: { id: string };
}

async function getReportData(id: string) {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/r/${id}/data`,
    { cache: 'no-store' }
  );
  if (!res.ok) return null;
  return res.json();
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const report = await getReportData(params.id);
  if (!report) return { title: 'Report Not Found' };
  
  return {
    title: `Home Value Report | ${report.property.address}`,
    description: `Estimated value: $${report.value_estimate.low.toLocaleString()} - $${report.value_estimate.high.toLocaleString()}`,
    openGraph: {
      title: `Home Value Report | ${report.property.address}`,
      description: `Estimated value: $${report.value_estimate.low.toLocaleString()} - $${report.value_estimate.high.toLocaleString()}`,
    },
  };
}

export default async function MobileReportPage({ params }: PageProps) {
  const report = await getReportData(params.id);
  
  if (!report) {
    notFound();
  }
  
  return <MobileReportViewer report={report} reportId={params.id} />;
}
```

### File: `apps/web/components/mobile-report/MobileReportViewer.tsx`

```tsx
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, Building2, TrendingUp, BarChart3, User,
  Phone, MessageSquare, Mail, Download, Share2,
  ChevronLeft, ChevronRight, MapPin, Calendar,
  Bed, Bath, Square, Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ReportData {
  id: string;
  property: {
    address: string;
    city: string;
    state: string;
    zip: string;
    owner_name?: string;
    bedrooms?: number;
    bathrooms?: number;
    sqft?: number;
    lot_size?: number;
    year_built?: number;
    latitude?: number;
    longitude?: number;
  };
  comparables: Array<{
    address: string;
    city: string;
    sold_price: number;
    sold_date: string;
    days_ago: number;
    bedrooms: number;
    bathrooms: number;
    sqft: number;
    price_per_sqft: number;
    distance_miles: number;
    photo_url?: string;
  }>;
  value_estimate: {
    low: number;
    mid: number;
    high: number;
    confidence: string;
  };
  market_stats: {
    median_price?: number;
    avg_price_per_sqft?: number;
    avg_days_on_market?: number;
    total_sold_last_6mo?: number;
  };
  agent: {
    name: string;
    phone?: string;
    email?: string;
    photo_url?: string;
    company_name?: string;
    license_number?: string;
  };
  has_pdf: boolean;
}

interface Props {
  report: ReportData;
  reportId: string;
}

type TabId = 'overview' | 'details' | 'comps' | 'market' | 'agent';

const tabs: { id: TabId; label: string; icon: any }[] = [
  { id: 'overview', label: 'Overview', icon: Home },
  { id: 'details', label: 'Details', icon: Building2 },
  { id: 'comps', label: 'Comps', icon: TrendingUp },
  { id: 'market', label: 'Market', icon: BarChart3 },
  { id: 'agent', label: 'Agent', icon: User },
];

export function MobileReportViewer({ report, reportId }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [compIndex, setCompIndex] = useState(0);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));

  // Track tab views
  useEffect(() => {
    fetch(`/api/v1/r/${reportId}/analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'tab_change',
        event_data: { tab: activeTab },
        session_id: sessionId,
      }),
    });
  }, [activeTab, reportId, sessionId]);

  const trackAgentClick = (type: string) => {
    fetch(`/api/v1/r/${reportId}/analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'agent_click',
        event_data: { contact_type: type },
        session_id: sessionId,
      }),
    });
  };

  const handleDownloadPdf = async () => {
    setPdfLoading(true);
    try {
      const res = await fetch(`/api/v1/r/${reportId}/pdf`, { method: 'POST' });
      const data = await res.json();
      
      if (data.status === 'ready') {
        setPdfUrl(data.pdf_url);
        window.open(data.pdf_url, '_blank');
      } else {
        // Poll for completion
        const checkPdf = async () => {
          const check = await fetch(`/api/v1/r/${reportId}/pdf/status`);
          const status = await check.json();
          if (status.status === 'ready') {
            setPdfUrl(status.pdf_url);
            setPdfLoading(false);
            window.open(status.pdf_url, '_blank');
          } else {
            setTimeout(checkPdf, 1000);
          }
        };
        checkPdf();
      }
    } catch (err) {
      console.error('PDF generation failed', err);
      setPdfLoading(false);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: `Home Value Report - ${report.property.address}`,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  const formatPrice = (n: number) => `$${n.toLocaleString()}`;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex-1 min-w-0">
          <h1 className="font-semibold text-gray-900 truncate">
            {report.property.address}
          </h1>
          <p className="text-sm text-gray-500">
            {report.property.city}, {report.property.state}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={handleShare}>
          <Share2 className="w-5 h-5" />
        </Button>
      </header>

      {/* Tab Content */}
      <main className="flex-1 overflow-y-auto pb-20">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && (
              <OverviewTab report={report} formatPrice={formatPrice} />
            )}
            {activeTab === 'details' && (
              <DetailsTab report={report} />
            )}
            {activeTab === 'comps' && (
              <CompsTab 
                report={report} 
                compIndex={compIndex}
                setCompIndex={setCompIndex}
                formatPrice={formatPrice}
              />
            )}
            {activeTab === 'market' && (
              <MarketTab report={report} formatPrice={formatPrice} />
            )}
            {activeTab === 'agent' && (
              <AgentTab 
                report={report}
                onContactClick={trackAgentClick}
                onDownloadPdf={handleDownloadPdf}
                pdfLoading={pdfLoading}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Tab Bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t px-2 py-2 flex justify-around z-50">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-col items-center px-3 py-1 rounded-lg transition-colors ${
                isActive 
                  ? 'text-violet-600 bg-violet-50' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs mt-0.5">{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}


// =============================================
// TAB COMPONENTS
// =============================================

function OverviewTab({ report, formatPrice }: { report: ReportData; formatPrice: (n: number) => string }) {
  return (
    <div className="p-4 space-y-4">
      {/* Hero Card */}
      <div className="bg-gradient-to-br from-violet-600 to-purple-700 rounded-2xl p-6 text-white">
        <p className="text-violet-200 text-sm mb-1">Estimated Value Range</p>
        <p className="text-3xl font-bold mb-2">
          {formatPrice(report.value_estimate.low)} - {formatPrice(report.value_estimate.high)}
        </p>
        <p className="text-violet-200 text-sm">
          Most likely: {formatPrice(report.value_estimate.mid)}
        </p>
        <div className="mt-4 flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
            report.value_estimate.confidence === 'high' 
              ? 'bg-green-500/20 text-green-100'
              : report.value_estimate.confidence === 'medium'
              ? 'bg-yellow-500/20 text-yellow-100'
              : 'bg-red-500/20 text-red-100'
          }`}>
            {report.value_estimate.confidence} confidence
          </span>
          <span className="text-violet-200 text-xs">
            Based on {report.comparables.length} comparable sales
          </span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard 
          icon={<Bed className="w-5 h-5" />}
          label="Beds"
          value={report.property.bedrooms || '--'}
        />
        <StatCard 
          icon={<Bath className="w-5 h-5" />}
          label="Baths"
          value={report.property.bathrooms || '--'}
        />
        <StatCard 
          icon={<Square className="w-5 h-5" />}
          label="Sqft"
          value={report.property.sqft?.toLocaleString() || '--'}
        />
      </div>

      {/* Address Card */}
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0">
            <MapPin className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{report.property.address}</p>
            <p className="text-gray-600">
              {report.property.city}, {report.property.state} {report.property.zip}
            </p>
            {report.property.owner_name && (
              <p className="text-sm text-gray-500 mt-1">
                Owner: {report.property.owner_name}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Agent Preview */}
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-3">
          {report.agent.photo_url ? (
            <img 
              src={report.agent.photo_url} 
              alt={report.agent.name}
              className="w-12 h-12 rounded-full object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="w-6 h-6 text-gray-500" />
            </div>
          )}
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{report.agent.name}</p>
            <p className="text-sm text-gray-600">{report.agent.company_name}</p>
          </div>
          {report.agent.phone && (
            <a 
              href={`tel:${report.agent.phone}`}
              className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center"
            >
              <Phone className="w-5 h-5 text-violet-600" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}


function DetailsTab({ report }: { report: ReportData }) {
  const details = [
    { label: 'Address', value: report.property.address },
    { label: 'City', value: report.property.city },
    { label: 'State', value: report.property.state },
    { label: 'ZIP', value: report.property.zip },
    { label: 'Owner', value: report.property.owner_name || '--' },
    { label: 'Bedrooms', value: report.property.bedrooms || '--' },
    { label: 'Bathrooms', value: report.property.bathrooms || '--' },
    { label: 'Square Feet', value: report.property.sqft?.toLocaleString() || '--' },
    { label: 'Lot Size', value: report.property.lot_size ? `${report.property.lot_size.toLocaleString()} sqft` : '--' },
    { label: 'Year Built', value: report.property.year_built || '--' },
  ];

  return (
    <div className="p-4">
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h2 className="font-semibold text-gray-900">Property Details</h2>
        </div>
        <div className="divide-y">
          {details.map((item, i) => (
            <div key={i} className="px-4 py-3 flex justify-between">
              <span className="text-gray-600">{item.label}</span>
              <span className="font-medium text-gray-900">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


function CompsTab({ 
  report, 
  compIndex, 
  setCompIndex,
  formatPrice 
}: { 
  report: ReportData; 
  compIndex: number;
  setCompIndex: (n: number) => void;
  formatPrice: (n: number) => string;
}) {
  const comp = report.comparables[compIndex];
  
  if (!report.comparables.length) {
    return (
      <div className="p-4 text-center text-gray-500">
        No comparable sales found
      </div>
    );
  }

  return (
    <div className="p-4">
      {/* Navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setCompIndex(Math.max(0, compIndex - 1))}
          disabled={compIndex === 0}
          className="p-2 rounded-full bg-white shadow disabled:opacity-30"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <span className="text-sm text-gray-600">
          {compIndex + 1} of {report.comparables.length} Comparables
        </span>
        <button
          onClick={() => setCompIndex(Math.min(report.comparables.length - 1, compIndex + 1))}
          disabled={compIndex === report.comparables.length - 1}
          className="p-2 rounded-full bg-white shadow disabled:opacity-30"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Comp Card */}
      <motion.div
        key={compIndex}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-white rounded-2xl shadow-sm overflow-hidden"
      >
        {/* Photo */}
        <div className="h-48 bg-gradient-to-br from-gray-200 to-gray-300 relative">
          {comp.photo_url ? (
            <img 
              src={comp.photo_url} 
              alt={comp.address}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <Home className="w-12 h-12 text-gray-400" />
            </div>
          )}
          <div className="absolute top-3 right-3 px-2 py-1 bg-black/70 rounded text-white text-sm font-medium">
            {formatPrice(comp.sold_price)}
          </div>
        </div>

        {/* Details */}
        <div className="p-4">
          <p className="font-semibold text-gray-900">{comp.address}</p>
          <p className="text-gray-600 text-sm mb-3">{comp.city}, {report.property.state}</p>
          
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.bedrooms}</p>
              <p className="text-xs text-gray-500">Beds</p>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.bathrooms}</p>
              <p className="text-xs text-gray-500">Baths</p>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.sqft.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Sqft</p>
            </div>
          </div>

          <div className="flex justify-between text-sm">
            <span className="text-gray-600">
              <Calendar className="w-4 h-4 inline mr-1" />
              Sold {comp.days_ago} days ago
            </span>
            <span className="text-gray-600">
              <MapPin className="w-4 h-4 inline mr-1" />
              {comp.distance_miles.toFixed(1)} mi away
            </span>
          </div>

          <div className="mt-3 pt-3 border-t">
            <p className="text-center text-violet-600 font-semibold">
              ${comp.price_per_sqft}/sqft
            </p>
          </div>
        </div>
      </motion.div>

      {/* Dots */}
      <div className="flex justify-center gap-1.5 mt-4">
        {report.comparables.map((_, i) => (
          <button
            key={i}
            onClick={() => setCompIndex(i)}
            className={`w-2 h-2 rounded-full transition-colors ${
              i === compIndex ? 'bg-violet-600' : 'bg-gray-300'
            }`}
          />
        ))}
      </div>
    </div>
  );
}


function MarketTab({ report, formatPrice }: { report: ReportData; formatPrice: (n: number) => string }) {
  const stats = report.market_stats;

  return (
    <div className="p-4 space-y-4">
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <h2 className="font-semibold text-gray-900 mb-4">Market Statistics</h2>
        
        <div className="space-y-4">
          <MarketStatRow 
            label="Median Sale Price"
            value={stats.median_price ? formatPrice(stats.median_price) : '--'}
          />
          <MarketStatRow 
            label="Avg. Price per Sqft"
            value={stats.avg_price_per_sqft ? `$${stats.avg_price_per_sqft}` : '--'}
          />
          <MarketStatRow 
            label="Avg. Days on Market"
            value={stats.avg_days_on_market ? `${stats.avg_days_on_market} days` : '--'}
          />
          <MarketStatRow 
            label="Homes Sold (6 mo)"
            value={stats.total_sold_last_6mo?.toString() || '--'}
          />
        </div>
      </div>

      <div className="bg-violet-50 rounded-xl p-4">
        <p className="text-sm text-violet-800">
          Based on {report.comparables.length} comparable sales within 2 miles 
          of your property in the last 12 months.
        </p>
      </div>
    </div>
  );
}


function AgentTab({ 
  report, 
  onContactClick,
  onDownloadPdf,
  pdfLoading
}: { 
  report: ReportData;
  onContactClick: (type: string) => void;
  onDownloadPdf: () => void;
  pdfLoading: boolean;
}) {
  return (
    <div className="p-4 space-y-4">
      {/* Agent Card */}
      <div className="bg-white rounded-xl p-6 shadow-sm text-center">
        {report.agent.photo_url ? (
          <img 
            src={report.agent.photo_url} 
            alt={report.agent.name}
            className="w-24 h-24 rounded-full mx-auto mb-4 object-cover border-4 border-violet-100"
          />
        ) : (
          <div className="w-24 h-24 rounded-full mx-auto mb-4 bg-violet-100 flex items-center justify-center">
            <User className="w-12 h-12 text-violet-400" />
          </div>
        )}
        
        <h2 className="text-xl font-semibold text-gray-900">{report.agent.name}</h2>
        {report.agent.company_name && (
          <p className="text-gray-600">{report.agent.company_name}</p>
        )}
        {report.agent.license_number && (
          <p className="text-sm text-gray-500">DRE# {report.agent.license_number}</p>
        )}
      </div>

      {/* Contact Buttons */}
      <div className="space-y-3">
        {report.agent.phone && (
          <a
            href={`tel:${report.agent.phone}`}
            onClick={() => onContactClick('call')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-violet-600 text-white rounded-xl font-semibold hover:bg-violet-700 transition"
          >
            <Phone className="w-5 h-5" />
            Call {report.agent.name.split(' ')[0]}
          </a>
        )}
        
        {report.agent.phone && (
          <a
            href={`sms:${report.agent.phone}`}
            onClick={() => onContactClick('text')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border-2 border-violet-600 text-violet-600 rounded-xl font-semibold hover:bg-violet-50 transition"
          >
            <MessageSquare className="w-5 h-5" />
            Send Text
          </a>
        )}
        
        {report.agent.email && (
          <a
            href={`mailto:${report.agent.email}`}
            onClick={() => onContactClick('email')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition"
          >
            <Mail className="w-5 h-5" />
            Send Email
          </a>
        )}
      </div>

      {/* Download PDF */}
      <div className="pt-4 border-t">
        <button
          onClick={onDownloadPdf}
          disabled={pdfLoading}
          className="flex items-center justify-center gap-2 w-full py-3 text-gray-600 hover:text-gray-900 transition"
        >
          {pdfLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Download className="w-5 h-5" />
          )}
          {pdfLoading ? 'Generating PDF...' : 'Download Full PDF Report'}
        </button>
      </div>
    </div>
  );
}


// =============================================
// HELPER COMPONENTS
// =============================================

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl p-3 shadow-sm text-center">
      <div className="text-violet-600 mb-1 flex justify-center">{icon}</div>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

function MarketStatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-600">{label}</span>
      <span className="font-semibold text-gray-900">{value}</span>
    </div>
  );
}
```

---

## Part 6: Admin Dashboard Page

### File: `apps/web/app/admin/lead-pages/page.tsx`

```tsx
'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart3, TrendingUp, Users, FileText, Phone,
  Download, Eye, RefreshCw
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Funnel, FunnelChart, LabelList
} from 'recharts';

export default function AdminLeadPagesMetrics() {
  const [overview, setOverview] = useState<any>(null);
  const [daily, setDaily] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [funnel, setFunnel] = useState<any>(null);
  const [recent, setRecent] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const [ov, dy, ag, dv, fn, rc] = await Promise.all([
        fetch('/api/v1/admin/metrics/overview').then(r => r.json()),
        fetch('/api/v1/admin/metrics/daily?days=30').then(r => r.json()),
        fetch('/api/v1/admin/metrics/agents?limit=10').then(r => r.json()),
        fetch('/api/v1/admin/metrics/devices').then(r => r.json()),
        fetch('/api/v1/admin/metrics/conversion-funnel').then(r => r.json()),
        fetch('/api/v1/admin/metrics/recent?limit=10').then(r => r.json()),
      ]);
      setOverview(ov);
      setDaily(dy.reverse());
      setAgents(ag);
      setDevices(dv);
      setFunnel(fn);
      setRecent(rc);
    } catch (err) {
      console.error('Failed to fetch metrics', err);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#8B5CF6', '#EC4899', '#F59E0B', '#10B981'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-600" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lead Pages Analytics</h1>
          <p className="text-gray-600">Consumer report performance metrics</p>
        </div>
        <Button onClick={fetchMetrics} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          icon={<FileText className="w-5 h-5" />}
          label="Total Reports"
          value={overview?.total_reports?.toLocaleString() || '0'}
          subtext={`${overview?.reports_today || 0} today`}
        />
        <MetricCard
          icon={<Eye className="w-5 h-5" />}
          label="Total Views"
          value={overview?.total_views?.toLocaleString() || '0'}
          subtext={`${overview?.views_today || 0} today`}
        />
        <MetricCard
          icon={<Phone className="w-5 h-5" />}
          label="Agent Contacts"
          value={overview?.total_contacts?.toLocaleString() || '0'}
          subtext={`${overview?.contact_rate_pct || 0}% rate`}
          highlight
        />
        <MetricCard
          icon={<Download className="w-5 h-5" />}
          label="PDFs Generated"
          value={overview?.total_pdfs?.toLocaleString() || '0'}
          subtext={`${overview?.pdf_rate_pct || 0}% of reports`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Daily Trend */}
        <Card className="p-4">
          <h3 className="font-semibold mb-4">Reports & Contacts (30 Days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="reports_requested" 
                  stroke="#8B5CF6" 
                  strokeWidth={2}
                  name="Reports"
                />
                <Line 
                  type="monotone" 
                  dataKey="agent_contacts" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  name="Contacts"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Device Breakdown */}
        <Card className="p-4">
          <h3 className="font-semibold mb-4">Device Breakdown</h3>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={devices}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  dataKey="count"
                  nameKey="device_type"
                  label={({ device_type, percentage }) => `${device_type} ${percentage}%`}
                >
                  {devices.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Conversion Funnel */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Conversion Funnel (30 Days)</h3>
        <div className="grid grid-cols-6 gap-2">
          {funnel?.funnel?.map((step: any, i: number) => (
            <div 
              key={i}
              className="text-center p-3 rounded-lg"
              style={{ 
                backgroundColor: `rgba(139, 92, 246, ${0.1 + (step.pct / 100) * 0.3})` 
              }}
            >
              <p className="text-2xl font-bold text-violet-700">{step.count}</p>
              <p className="text-xs text-gray-600 mt-1">{step.stage}</p>
              <p className="text-xs text-violet-600 font-medium">{step.pct}%</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Agent Leaderboard */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Top Agents by Reports</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="pb-2">Agent</th>
                <th className="pb-2">Account</th>
                <th className="pb-2 text-right">Reports</th>
                <th className="pb-2 text-right">Views</th>
                <th className="pb-2 text-right">Contacts</th>
                <th className="pb-2 text-right">Rate</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-3">
                    <p className="font-medium">{agent.agent_name}</p>
                    <p className="text-sm text-gray-500">{agent.agent_email}</p>
                  </td>
                  <td className="py-3 text-gray-600">{agent.account_name}</td>
                  <td className="py-3 text-right font-medium">{agent.total_reports}</td>
                  <td className="py-3 text-right">{agent.total_views}</td>
                  <td className="py-3 text-right">{agent.contacts}</td>
                  <td className="py-3 text-right">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      agent.contact_rate_pct >= 10 
                        ? 'bg-green-100 text-green-700'
                        : agent.contact_rate_pct >= 5
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {agent.contact_rate_pct}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Recent Reports</h3>
        <div className="space-y-2">
          {recent.map((report, i) => (
            <div 
              key={i}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{report.property_address}</p>
                <p className="text-sm text-gray-500">{report.agent_name}</p>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-0.5 rounded text-xs ${
                  report.status === 'ready' 
                    ? 'bg-green-100 text-green-700'
                    : report.status === 'failed'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {report.status}
                </span>
                <span className="text-gray-500">{report.view_count} views</span>
                {report.agent_contacted && (
                  <Phone className="w-4 h-4 text-green-600" />
                )}
                {report.has_pdf && (
                  <Download className="w-4 h-4 text-violet-600" />
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}


function MetricCard({ 
  icon, 
  label, 
  value, 
  subtext,
  highlight 
}: { 
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext?: string;
  highlight?: boolean;
}) {
  return (
    <Card className={`p-4 ${highlight ? 'ring-2 ring-violet-200 bg-violet-50' : ''}`}>
      <div className="flex items-center gap-2 text-gray-600 mb-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {subtext && (
        <p className="text-sm text-gray-500 mt-1">{subtext}</p>
      )}
    </Card>
  );
}
```

---

## Part 7: Navigation Updates

### Add to sidebar navigation

```tsx
// In apps/web/components/layouts/app-layout.tsx or similar

// Add to admin navigation items:
{
  name: 'Lead Pages',
  href: '/admin/lead-pages',
  icon: TrendingUp,
}

// Add to agent navigation items:
{
  name: 'My Lead Page',
  href: '/app/lead-page',
  icon: Share2,
}
```

---

## Implementation Checklist

### Day 1: Database & Core API
- [ ] Run migration 0037_mobile_reports.sql
- [ ] Create mobile_reports.py routes
- [ ] Create admin_metrics.py routes
- [ ] Update consumer report task (no PDF)

### Day 2: Mobile Report Viewer
- [ ] Create /r/[id]/page.tsx
- [ ] Create MobileReportViewer component
- [ ] All 5 tabs working
- [ ] Analytics tracking

### Day 3: On-Demand PDF
- [ ] Create PDF generation task
- [ ] Add /pdf endpoint
- [ ] Add polling for status
- [ ] Test PDF download flow

### Day 4: Admin Dashboard
- [ ] Create /admin/lead-pages/page.tsx
- [ ] Overview stats cards
- [ ] Daily trend chart
- [ ] Device breakdown pie
- [ ] Conversion funnel
- [ ] Agent leaderboard
- [ ] Recent activity feed

### Day 5: Polish & Test
- [ ] Mobile responsive testing
- [ ] Analytics verification
- [ ] SMS delivery testing
- [ ] Load testing
- [ ] Navigation links

---

## Key Metrics Tracked

| Metric | Purpose |
|--------|---------|
| Reports Requested | Total demand |
| Reports Ready | Success rate |
| Reports Failed | Error monitoring |
| Views | Engagement |
| PDF Downloads | Demand for PDF (expect ~10%) |
| Agent Contacts | **Primary conversion metric** |
| Contact Rate % | Quality of experience |
| Device Type | Mobile-first validation |
| Tabs Viewed | Content engagement |
| Time on Page | Quality of experience |

---

## Environment Variables

```bash
# No new vars needed - uses existing:
# - TWILIO_* for SMS
# - R2_* for PDF storage
# - DATABASE_URL
# - SITEX_* for property data
```
