# TrendyReports Lead Pages - Complete Cursor Implementation Package

## Overview

**Lead Pages** is a consumer-initiated lead generation system. Agents share a unique URL/QR code, consumers request their own home value report, and both parties receive SMS notifications.

---

## THE FLOW (This Is The Source of Truth)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              THE LEAD PAGES FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     1. AGENT SETUP (One Time)                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • Agent creates TrendyReports account                               │   │
│  │  • System auto-generates unique code: "ZOE2024"                      │   │
│  │  • Agent's /app/leads page shows:                                    │   │
│  │    - Their unique URL: trendyreports.io/cma/ZOE2024                 │   │
│  │    - Downloadable QR code (encodes the URL)                         │   │
│  │    - Stats: visits, reports, leads                                   │   │
│  │  • Agent shares URL/QR everywhere (cards, signs, social, etc.)      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    2. CONSUMER VISITS URL                            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • Consumer scans QR or clicks link                                  │   │
│  │  • Arrives at: trendyreports.io/cma/ZOE2024                         │   │
│  │  • Sees agent-branded landing page:                                  │   │
│  │    - Agent's photo, name, company (pulled from ZOE2024's profile)   │   │
│  │    - Headline: "Get Your Free Home Value Report"                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   3. CONSUMER COMPLETES WIZARD                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  Step 1: Enter phone number         "(555) 123-4567"                │   │
│  │  Step 2: Enter property address     "123 Main St, Los Angeles"      │   │
│  │  Step 3: Confirm property           "Yes, this is my property"      │   │
│  │  Step 4: Submit                     [Get My Free Report]            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                 4. SYSTEM PROCESSES (2-3 seconds)                    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  ✓ Lead record created (linked to agent via "ZOE2024")              │   │
│  │  ✓ Property data fetched from SiteX                                 │   │
│  │  ✓ Comparables auto-selected (8 best matches)                       │   │
│  │  ✓ Value estimate calculated                                        │   │
│  │  ✓ JSON stored (NO PDF yet - mobile-first!)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    5. SMS NOTIFICATIONS SENT                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  📱 TO CONSUMER:                                                     │   │
│  │  "Your home value report is ready!                                   │   │
│  │   View here: trendyreports.io/r/abc123"                             │   │
│  │                                                                      │   │
│  │  📱 TO AGENT (ZOE2024):                                             │   │
│  │  "🏠 New Lead!                                                       │   │
│  │   Phone: (555) 123-4567                                              │   │
│  │   Property: 123 Main St, Los Angeles CA                              │   │
│  │   View: trendyreports.io/app/leads"                                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │               6. CONSUMER VIEWS MOBILE REPORT                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • Consumer taps link in SMS                                         │   │
│  │  • Opens: trendyreports.io/r/abc123                                 │   │
│  │  • Sees beautiful 5-tab mobile report:                               │   │
│  │    [Overview] [Details] [Comps] [Market] [Agent]                    │   │
│  │  • Agent tab has tap-to-call, tap-to-text buttons                   │   │
│  │  • Optional: "Download PDF" button (generates on-demand)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  7. AGENT TRACKS IN DASHBOARD                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • Agent visits /app/leads                                           │   │
│  │  • Sees all leads with engagement metrics:                           │   │
│  │    - Views, time spent, tabs viewed                                  │   │
│  │    - Contact clicked (call/text/email)                               │   │
│  │    - PDF downloaded                                                  │   │
│  │  • Hot lead indicators: 🔥 multiple views, comp tab, contact click  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## KEY PRINCIPLE: Mobile-First, PDF On-Demand

```
OLD WAY (Wasteful):
Request → Generate PDF (10 sec) → Send SMS → User ignores PDF on phone

NEW WAY (Smart):
Request → Store JSON (instant) → Send SMS → Beautiful mobile view → PDF only if clicked
```

**Why?**
- 90% of users view on mobile
- PDFs are painful on phones
- Saves server resources
- Faster time-to-SMS (2 sec vs 10+ sec)

---

## URL STRUCTURE

| URL Pattern | Purpose | Auth Required |
|-------------|---------|---------------|
| `/cma/{agent_code}` | Consumer landing page wizard | No |
| `/r/{report_id}` | Mobile report viewer | No |
| `/r/{report_id}/pdf` | On-demand PDF generation | No |
| `/app/leads` | Agent's leads dashboard | Yes |
| `/admin/lead-pages` | Admin metrics dashboard | Yes (admin) |

---

# PART 1: DATABASE SCHEMA

## File: `apps/api/migrations/0037_lead_pages.sql`

```sql
-- =============================================
-- 1. ADD AGENT CODE TO USERS TABLE
-- =============================================

-- Unique identifier for each agent (e.g., "ZOE2024", "ABC123")
ALTER TABLE users ADD COLUMN IF NOT EXISTS agent_code VARCHAR(10) UNIQUE;

-- Landing page customization
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_headline VARCHAR(255) 
    DEFAULT 'Get Your Free Home Value Report';
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_subheadline TEXT 
    DEFAULT 'Find out what your home is worth in today''s market.';
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_theme_color VARCHAR(7) 
    DEFAULT '#8B5CF6';
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_enabled BOOLEAN DEFAULT true;

-- Stats
ALTER TABLE users ADD COLUMN IF NOT EXISTS landing_page_visits INTEGER DEFAULT 0;

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_agent_code ON users(agent_code) WHERE agent_code IS NOT NULL;


-- =============================================
-- 2. CONSUMER REPORTS TABLE (Lead + Report Data)
-- =============================================

CREATE TABLE IF NOT EXISTS consumer_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to agent (via their unique code)
    agent_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    agent_code VARCHAR(10) NOT NULL,  -- Denormalized for fast lookups
    
    -- Consumer info (THE LEAD)
    consumer_phone VARCHAR(20) NOT NULL,
    consumer_email VARCHAR(255),
    consent_given BOOLEAN DEFAULT false,
    consent_timestamp TIMESTAMPTZ,
    
    -- Property info
    property_address TEXT NOT NULL,
    property_city VARCHAR(100),
    property_state VARCHAR(2),
    property_zip VARCHAR(10),
    property_owner VARCHAR(255),
    
    -- Report data (JSON - powers mobile view)
    property_data JSONB NOT NULL DEFAULT '{}',   -- Full SiteX response
    comparables JSONB NOT NULL DEFAULT '[]',     -- Auto-selected comps
    value_estimate JSONB DEFAULT '{}',           -- Low/mid/high range
    market_stats JSONB DEFAULT '{}',             -- Area statistics
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',        -- pending, ready, failed
    error_message TEXT,
    
    -- PDF (only generated on-demand)
    pdf_url TEXT,                                -- NULL until user requests
    pdf_generated_at TIMESTAMPTZ,
    pdf_download_count INTEGER DEFAULT 0,
    
    -- SMS tracking
    consumer_sms_sent_at TIMESTAMPTZ,
    consumer_sms_sid VARCHAR(50),
    agent_sms_sent_at TIMESTAMPTZ,
    agent_sms_sid VARCHAR(50),
    
    -- Engagement metrics (for agent dashboard)
    view_count INTEGER DEFAULT 0,
    unique_views INTEGER DEFAULT 0,
    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,
    tabs_viewed JSONB DEFAULT '[]',              -- Which tabs consumer viewed
    time_on_page_seconds INTEGER DEFAULT 0,
    agent_contact_clicked BOOLEAN DEFAULT false,
    agent_contact_type VARCHAR(20),              -- 'call', 'text', 'email'
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),                     -- 'mobile', 'tablet', 'desktop'
    referrer TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_consumer_reports_agent_id ON consumer_reports(agent_id);
CREATE INDEX idx_consumer_reports_agent_code ON consumer_reports(agent_code);
CREATE INDEX idx_consumer_reports_status ON consumer_reports(status);
CREATE INDEX idx_consumer_reports_created ON consumer_reports(created_at DESC);
CREATE INDEX idx_consumer_reports_phone ON consumer_reports(consumer_phone);


-- =============================================
-- 3. ANALYTICS TABLE (Detailed Event Tracking)
-- =============================================

CREATE TABLE IF NOT EXISTS report_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES consumer_reports(id) ON DELETE CASCADE,
    
    -- Event info
    event_type VARCHAR(50) NOT NULL,  -- 'view', 'tab_change', 'agent_click', 'pdf_request', 'share'
    event_data JSONB DEFAULT '{}',    -- Additional details
    
    -- Session
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
-- 4. SMS CREDITS & LOGS
-- =============================================

-- Add SMS credits to accounts (if not exists)
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS sms_credits INTEGER DEFAULT 0;

-- SMS log table
CREATE TABLE IF NOT EXISTS sms_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    consumer_report_id UUID REFERENCES consumer_reports(id),
    
    direction VARCHAR(10) DEFAULT 'outbound',
    recipient_type VARCHAR(20) NOT NULL,         -- 'consumer', 'agent'
    to_phone VARCHAR(20) NOT NULL,
    from_phone VARCHAR(20) NOT NULL,
    message_body TEXT NOT NULL,
    
    twilio_sid VARCHAR(50),
    status VARCHAR(20) DEFAULT 'queued',         -- queued, sent, delivered, failed
    error_code VARCHAR(10),
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sms_logs_account ON sms_logs(account_id);
CREATE INDEX idx_sms_logs_report ON sms_logs(consumer_report_id);


-- =============================================
-- 5. ADMIN VIEWS (For Metrics Dashboard)
-- =============================================

-- Daily metrics
CREATE OR REPLACE VIEW admin_daily_metrics AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as reports_requested,
    COUNT(*) FILTER (WHERE status = 'ready') as reports_ready,
    COUNT(*) FILTER (WHERE status = 'failed') as reports_failed,
    COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdfs_generated,
    COUNT(*) FILTER (WHERE agent_contact_clicked = true) as agent_contacts,
    SUM(view_count) as total_views,
    ROUND(AVG(view_count), 1) as avg_views_per_report,
    ROUND(AVG(time_on_page_seconds), 1) as avg_time_seconds,
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
    u.agent_code,
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
WHERE u.agent_code IS NOT NULL
GROUP BY u.id, u.full_name, u.email, u.agent_code, a.name
ORDER BY total_reports DESC;
```

---

# PART 2: AGENT CODE GENERATION

## File: `apps/api/src/api/services/agent_code.py`

```python
"""
Agent Code Generation Service

Generates unique 6-character codes for agents.
Format: Alphanumeric, uppercase, no confusing characters (0, O, I, L)
"""

import random
import string

# Characters that are easy to read (no 0/O, I/L confusion)
ALLOWED_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def generate_agent_code(length: int = 6) -> str:
    """Generate a random agent code."""
    return ''.join(random.choices(ALLOWED_CHARS, k=length))


async def create_unique_agent_code(db, user_id: str, max_attempts: int = 10) -> str:
    """
    Generate a unique agent code and save to user record.
    Retries if code already exists.
    """
    for _ in range(max_attempts):
        code = generate_agent_code()
        
        # Check if code exists
        existing = await db.fetchval(
            "SELECT 1 FROM users WHERE agent_code = $1",
            code
        )
        
        if not existing:
            # Save to user
            await db.execute(
                "UPDATE users SET agent_code = $1 WHERE id = $2",
                code,
                user_id
            )
            return code
    
    raise ValueError("Could not generate unique agent code after max attempts")


async def get_or_create_agent_code(db, user_id: str) -> str:
    """Get existing code or create new one."""
    existing = await db.fetchval(
        "SELECT agent_code FROM users WHERE id = $1",
        user_id
    )
    
    if existing:
        return existing
    
    return await create_unique_agent_code(db, user_id)
```

## Add to User Registration Flow

```python
# In your user registration/creation endpoint, add:

from ..services.agent_code import create_unique_agent_code

# After creating user:
agent_code = await create_unique_agent_code(db, user_id)
```

---

# PART 3: PUBLIC API ENDPOINTS

## File: `apps/api/src/api/routes/lead_pages.py`

```python
"""
Lead Pages Public API

Consumer-facing endpoints for the lead capture flow.
NO AUTHENTICATION REQUIRED for these endpoints.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel, validator
from typing import Optional, List
from uuid import UUID
import json
import re

router = APIRouter(prefix="/v1/cma", tags=["lead-pages"])


# =============================================
# SCHEMAS
# =============================================

class AgentLandingPageInfo(BaseModel):
    """Agent info displayed on landing page."""
    name: str
    photo_url: Optional[str]
    company_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    license_number: Optional[str]
    headline: str
    subheadline: str
    theme_color: str


class PropertySearchRequest(BaseModel):
    """Consumer searching for their property."""
    address: str
    city: Optional[str]
    state: Optional[str]


class PropertySearchResult(BaseModel):
    """Property from SiteX search."""
    apn: str
    address: str
    city: str
    state: str
    zip: str
    owner_name: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    sqft: Optional[int]
    year_built: Optional[int]


class ReportRequestPayload(BaseModel):
    """Consumer requesting their report."""
    phone: str
    property_apn: str
    property_address: str
    property_city: str
    property_state: str
    property_zip: str
    consent_given: bool = False
    
    @validator('phone')
    def validate_phone(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) != 10:
            raise ValueError('Phone must be 10 digits')
        return digits


# =============================================
# ENDPOINTS
# =============================================

@router.get("/{agent_code}", response_model=AgentLandingPageInfo)
async def get_landing_page_info(
    agent_code: str,
    request: Request,
    db = Depends(get_db)
):
    """
    Get agent info for rendering the landing page.
    Called when consumer visits: /cma/{agent_code}
    """
    agent = await db.fetchrow(
        """
        SELECT 
            u.full_name as name,
            u.photo_url,
            u.company_name,
            u.phone,
            u.email,
            u.license_number,
            u.landing_page_headline as headline,
            u.landing_page_subheadline as subheadline,
            u.landing_page_theme_color as theme_color,
            u.landing_page_enabled
        FROM users u
        WHERE u.agent_code = $1
        """,
        agent_code.upper()
    )
    
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    if not agent["landing_page_enabled"]:
        raise HTTPException(410, "This page is currently unavailable")
    
    # Track visit
    await db.execute(
        "UPDATE users SET landing_page_visits = landing_page_visits + 1 WHERE agent_code = $1",
        agent_code.upper()
    )
    
    return AgentLandingPageInfo(
        name=agent["name"],
        photo_url=agent["photo_url"],
        company_name=agent["company_name"],
        phone=agent["phone"],
        email=agent["email"],
        license_number=agent["license_number"],
        headline=agent["headline"] or "Get Your Free Home Value Report",
        subheadline=agent["subheadline"] or "Find out what your home is worth in today's market.",
        theme_color=agent["theme_color"] or "#8B5CF6"
    )


@router.post("/{agent_code}/search", response_model=List[PropertySearchResult])
async def search_property(
    agent_code: str,
    payload: PropertySearchRequest,
    db = Depends(get_db)
):
    """
    Search for properties by address.
    Consumer enters their address, we find matching properties.
    """
    # Validate agent exists
    agent = await db.fetchval(
        "SELECT id FROM users WHERE agent_code = $1 AND landing_page_enabled = true",
        agent_code.upper()
    )
    if not agent:
        raise HTTPException(404, "Invalid agent code")
    
    # Search via SiteX
    from ..services.sitex import search_properties
    
    results = await search_properties(
        address=payload.address,
        city=payload.city,
        state=payload.state or "CA"
    )
    
    return [PropertySearchResult(**r) for r in results[:10]]


@router.post("/{agent_code}/request")
async def request_report(
    agent_code: str,
    payload: ReportRequestPayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Consumer requests their home value report.
    This is the main submission endpoint.
    """
    # Get agent
    agent = await db.fetchrow(
        """
        SELECT u.id, u.phone as agent_phone, u.full_name,
               a.id as account_id, a.sms_credits
        FROM users u
        JOIN accounts a ON u.account_id = a.id
        WHERE u.agent_code = $1 AND u.landing_page_enabled = true
        """,
        agent_code.upper()
    )
    
    if not agent:
        raise HTTPException(404, "Invalid agent code")
    
    # Rate limit check (5 per hour per IP)
    ip = request.client.host if request.client else None
    if ip:
        recent_count = await db.fetchval(
            """
            SELECT COUNT(*) FROM consumer_reports 
            WHERE ip_address = $1 AND created_at > NOW() - INTERVAL '1 hour'
            """,
            ip
        )
        if recent_count >= 5:
            raise HTTPException(429, "Too many requests. Please try again later.")
    
    # Create report record
    report_id = await db.fetchval(
        """
        INSERT INTO consumer_reports (
            agent_id, agent_code, consumer_phone,
            property_address, property_city, property_state, property_zip,
            consent_given, consent_timestamp,
            ip_address, user_agent, device_type, status
        ) VALUES (
            $1, $2, $3,
            $4, $5, $6, $7,
            $8, NOW(),
            $9, $10, $11, 'pending'
        )
        RETURNING id
        """,
        agent["id"],
        agent_code.upper(),
        payload.phone,
        payload.property_address,
        payload.property_city,
        payload.property_state,
        payload.property_zip,
        payload.consent_given,
        ip,
        request.headers.get("user-agent"),
        detect_device_type(request.headers.get("user-agent", ""))
    )
    
    # Queue processing task
    from ..tasks import process_consumer_report
    process_consumer_report.delay(str(report_id))
    
    return {
        "success": True,
        "message": "Your report is being generated! You'll receive a text in a few seconds.",
        "report_id": str(report_id)
    }


def detect_device_type(user_agent: str) -> str:
    """Simple device detection."""
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'
```

---

# PART 4: MOBILE REPORT VIEWER API

## File: `apps/api/src/api/routes/mobile_report.py`

```python
"""
Mobile Report Viewer API

Public endpoints for viewing reports.
NO AUTHENTICATION REQUIRED.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import json

router = APIRouter(prefix="/v1/r", tags=["mobile-report"])


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
    latitude: Optional[float]
    longitude: Optional[float]


class Comparable(BaseModel):
    address: str
    city: str
    sold_price: int
    sold_date: str
    days_ago: int
    bedrooms: int
    bathrooms: float
    sqft: int
    price_per_sqft: int
    distance_miles: float
    photo_url: Optional[str]


class ValueEstimate(BaseModel):
    low: int
    mid: int
    high: int
    confidence: str


class MarketStats(BaseModel):
    median_price: Optional[int]
    avg_price_per_sqft: Optional[int]
    avg_days_on_market: Optional[int]
    total_sold_last_6mo: Optional[int]


class AgentInfo(BaseModel):
    name: str
    phone: Optional[str]
    email: Optional[str]
    photo_url: Optional[str]
    company_name: Optional[str]
    license_number: Optional[str]


class MobileReportData(BaseModel):
    id: str
    property: PropertyData
    comparables: List[Comparable]
    value_estimate: ValueEstimate
    market_stats: MarketStats
    agent: AgentInfo
    has_pdf: bool


class AnalyticsEvent(BaseModel):
    event_type: str
    event_data: Optional[dict] = {}
    session_id: Optional[str]


# =============================================
# ENDPOINTS
# =============================================

@router.get("/{report_id}/data", response_model=MobileReportData)
async def get_report_data(
    report_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Get report data for mobile viewer.
    Called when consumer opens: /r/{report_id}
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
            u.license_number
        FROM consumer_reports cr
        JOIN users u ON cr.agent_id = u.id
        WHERE cr.id = $1 AND cr.status = 'ready'
        """,
        str(report_id)
    )
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Track view
    background_tasks.add_task(
        track_report_view,
        db,
        str(report_id),
        request.client.host if request.client else None,
        request.headers.get("user-agent")
    )
    
    # Parse JSON fields
    property_data = report["property_data"] if isinstance(report["property_data"], dict) else json.loads(report["property_data"])
    comparables = report["comparables"] if isinstance(report["comparables"], list) else json.loads(report["comparables"])
    value_estimate = report["value_estimate"] if isinstance(report["value_estimate"], dict) else json.loads(report["value_estimate"] or '{}')
    market_stats = report["market_stats"] if isinstance(report["market_stats"], dict) else json.loads(report["market_stats"] or '{}')
    
    return MobileReportData(
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
            license_number=report["license_number"]
        ),
        has_pdf=report["pdf_url"] is not None
    )


@router.post("/{report_id}/pdf")
async def generate_pdf_on_demand(
    report_id: UUID,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Generate PDF when consumer clicks "Download PDF".
    PDF is only created on-demand, not upfront.
    """
    report = await db.fetchrow(
        "SELECT id, pdf_url FROM consumer_reports WHERE id = $1",
        str(report_id)
    )
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Return existing PDF if already generated
    if report["pdf_url"]:
        await db.execute(
            "UPDATE consumer_reports SET pdf_download_count = pdf_download_count + 1 WHERE id = $1",
            str(report_id)
        )
        return {"status": "ready", "pdf_url": report["pdf_url"]}
    
    # Queue PDF generation
    from ..tasks import generate_pdf_on_demand_task
    task = generate_pdf_on_demand_task.delay(str(report_id))
    
    return {
        "status": "generating",
        "task_id": task.id,
        "message": "Your PDF is being generated. This takes about 5 seconds."
    }


@router.get("/{report_id}/pdf/status")
async def check_pdf_status(
    report_id: UUID,
    db = Depends(get_db)
):
    """Poll for PDF generation status."""
    report = await db.fetchrow(
        "SELECT pdf_url FROM consumer_reports WHERE id = $1",
        str(report_id)
    )
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    if report["pdf_url"]:
        return {"status": "ready", "pdf_url": report["pdf_url"]}
    
    return {"status": "generating"}


@router.post("/{report_id}/analytics")
async def track_analytics(
    report_id: UUID,
    event: AnalyticsEvent,
    request: Request,
    db = Depends(get_db)
):
    """
    Track user interactions.
    Called from mobile report viewer.
    """
    # Insert analytics event
    await db.execute(
        """
        INSERT INTO report_analytics (report_id, event_type, event_data, session_id, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        str(report_id),
        event.event_type,
        json.dumps(event.event_data or {}),
        event.session_id,
        request.client.host if request.client else None,
        request.headers.get("user-agent")
    )
    
    # Update report record for quick stats
    if event.event_type == "agent_click":
        await db.execute(
            """
            UPDATE consumer_reports SET 
                agent_contact_clicked = true,
                agent_contact_type = $2
            WHERE id = $1
            """,
            str(report_id),
            event.event_data.get("contact_type")
        )
    elif event.event_type == "tab_change":
        await db.execute(
            """
            UPDATE consumer_reports SET 
                tabs_viewed = tabs_viewed || $2::jsonb
            WHERE id = $1 AND NOT tabs_viewed ? $3
            """,
            str(report_id),
            json.dumps([event.event_data.get("tab")]),
            event.event_data.get("tab")
        )
    
    return {"success": True}


async def track_report_view(db, report_id: str, ip: str, user_agent: str):
    """Track page view."""
    device = detect_device_type(user_agent or "")
    
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
        device
    )
    
    await db.execute(
        """
        INSERT INTO report_analytics (report_id, event_type, ip_address, user_agent, device_type)
        VALUES ($1, 'view', $2, $3, $4)
        """,
        report_id,
        ip,
        user_agent,
        device
    )


def detect_device_type(user_agent: str) -> str:
    ua = user_agent.lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    return 'desktop'
```

---

# PART 5: CELERY TASKS

## File: `apps/worker/src/worker/tasks/consumer_report.py`

```python
"""
Consumer Report Processing Tasks

1. process_consumer_report - Fast JSON processing, sends SMS
2. generate_pdf_on_demand_task - PDF generation when requested
"""

from celery import shared_task
import json
from datetime import datetime

from ..services.sitex import get_property_data
from ..services.simplyrets import get_comparables
from ..services.twilio_sms import send_sms
from ..services.pdf_engine import generate_property_report_pdf
from ..services.r2 import upload_to_r2
from ..db import get_db
from ..config import settings


@shared_task(
    name="process_consumer_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def process_consumer_report(self, report_id: str):
    """
    Process consumer report request.
    
    This is FAST - no PDF generation!
    1. Fetch property data
    2. Auto-select comparables
    3. Calculate value estimate
    4. Store as JSON
    5. Send SMS to consumer + agent
    """
    with get_db() as db:
        # Get report with agent info
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
            property_data = get_property_data(
                address=report["property_address"],
                city=report["property_city"],
                state=report["property_state"]
            )
            
            # 2. Get and auto-select comparables
            raw_comps = get_comparables(
                lat=property_data.get("latitude"),
                lng=property_data.get("longitude"),
                sqft=property_data.get("sqft"),
                bedrooms=property_data.get("bedrooms"),
                max_results=20
            )
            comparables = auto_select_comparables(property_data, raw_comps)
            
            # 3. Calculate value estimate
            value_estimate = calculate_value_estimate(property_data, comparables)
            
            # 4. Calculate market stats
            market_stats = calculate_market_stats(comparables)
            
            # 5. Store everything as JSON (NO PDF!)
            db.execute(
                """
                UPDATE consumer_reports SET
                    status = 'ready',
                    property_data = $2,
                    property_owner = $3,
                    comparables = $4,
                    value_estimate = $5,
                    market_stats = $6,
                    updated_at = NOW()
                WHERE id = $1
                """,
                report_id,
                json.dumps(property_data),
                property_data.get("owner_name"),
                json.dumps(comparables),
                json.dumps(value_estimate),
                json.dumps(market_stats)
            )
            
            # 6. Send SMS to CONSUMER
            mobile_url = f"{settings.APP_URL}/r/{report_id}"
            consumer_msg = f"Your home value report is ready! View it here: {mobile_url}"
            
            consumer_sms = send_sms(
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
                consumer_sms.get("sid")
            )
            
            # Log SMS
            db.execute(
                """
                INSERT INTO sms_logs (account_id, consumer_report_id, recipient_type, to_phone, from_phone, message_body, twilio_sid, status)
                VALUES ($1, $2, 'consumer', $3, $4, $5, $6, 'sent')
                """,
                report["account_id"],
                report_id,
                report["consumer_phone"],
                settings.TWILIO_PHONE_NUMBER,
                consumer_msg,
                consumer_sms.get("sid")
            )
            
            # 7. Send SMS to AGENT (if credits available)
            if report["sms_credits"] and report["sms_credits"] > 0:
                agent_msg = (
                    f"🏠 New Lead!\n"
                    f"Phone: {report['consumer_phone']}\n"
                    f"Property: {report['property_address']}, {report['property_city']} {report['property_state']}\n"
                    f"View: {settings.APP_URL}/app/leads"
                )
                
                agent_sms = send_sms(
                    to=f"+1{report['agent_phone']}",
                    message=agent_msg
                )
                
                db.execute(
                    """
                    UPDATE consumer_reports SET 
                        agent_sms_sent_at = NOW(),
                        agent_sms_sid = $2
                    WHERE id = $1
                    """,
                    report_id,
                    agent_sms.get("sid")
                )
                
                # Log SMS
                db.execute(
                    """
                    INSERT INTO sms_logs (account_id, consumer_report_id, recipient_type, to_phone, from_phone, message_body, twilio_sid, status)
                    VALUES ($1, $2, 'agent', $3, $4, $5, $6, 'sent')
                    """,
                    report["account_id"],
                    report_id,
                    report["agent_phone"],
                    settings.TWILIO_PHONE_NUMBER,
                    agent_msg,
                    agent_sms.get("sid")
                )
                
                # Decrement SMS credits
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
def generate_pdf_on_demand_task(self, report_id: str):
    """
    Generate PDF on-demand when consumer clicks "Download PDF".
    Only called when explicitly requested.
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
        
        # Already generated?
        if report["pdf_url"]:
            return {"pdf_url": report["pdf_url"]}
        
        # Parse JSON
        property_data = json.loads(report["property_data"]) if isinstance(report["property_data"], str) else report["property_data"]
        comparables = json.loads(report["comparables"]) if isinstance(report["comparables"], str) else report["comparables"]
        value_estimate = json.loads(report["value_estimate"]) if isinstance(report["value_estimate"], str) else report["value_estimate"]
        
        # Build context for PDF template
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
                pdf_download_count = 1
            WHERE id = $1
            """,
            report_id,
            pdf_url
        )
        
        return {"pdf_url": pdf_url}


# =============================================
# HELPER FUNCTIONS
# =============================================

def auto_select_comparables(subject: dict, comps: list, max_count: int = 8) -> list:
    """
    Auto-select best comparables.
    Criteria: distance, sqft, beds, baths, recency
    """
    subject_sqft = subject.get("sqft") or 0
    subject_beds = subject.get("bedrooms") or 0
    subject_baths = subject.get("bathrooms") or 0
    
    scored = []
    
    for comp in comps:
        score = 0
        
        # Distance (must be within 2 miles)
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
        
        # Square footage (±20%)
        comp_sqft = comp.get("sqft") or 0
        if subject_sqft and comp_sqft:
            diff = abs(comp_sqft - subject_sqft) / subject_sqft
            if diff <= 0.1:
                score += 25
            elif diff <= 0.2:
                score += 15
            elif diff <= 0.3:
                score += 5
        
        # Bedrooms (±1)
        comp_beds = comp.get("bedrooms") or 0
        bed_diff = abs(comp_beds - subject_beds)
        if bed_diff == 0:
            score += 15
        elif bed_diff == 1:
            score += 10
        
        # Bathrooms (±1)
        comp_baths = comp.get("bathrooms") or 0
        bath_diff = abs(comp_baths - subject_baths)
        if bath_diff <= 0.5:
            score += 15
        elif bath_diff <= 1:
            score += 10
        
        # Recency
        days_ago = comp.get("days_ago", 365)
        if days_ago <= 30:
            score += 15
        elif days_ago <= 90:
            score += 12
        elif days_ago <= 180:
            score += 8
        
        scored.append((score, comp))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [comp for _, comp in scored[:max_count]]


def calculate_value_estimate(subject: dict, comps: list) -> dict:
    """Calculate value range from comparables."""
    if not comps:
        return {"low": 0, "mid": 0, "high": 0, "confidence": "low"}
    
    subject_sqft = subject.get("sqft") or 1500
    
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
    
    return {"low": low, "mid": mid, "high": high, "confidence": confidence}


def calculate_market_stats(comps: list) -> dict:
    """Calculate market statistics."""
    if not comps:
        return {}
    
    prices = [c["sold_price"] for c in comps]
    ppsf = [c["sold_price"] / c["sqft"] for c in comps if c.get("sqft")]
    days = [c.get("days_on_market", 0) for c in comps if c.get("days_on_market")]
    
    return {
        "median_price": int(sorted(prices)[len(prices) // 2]) if prices else None,
        "avg_price_per_sqft": int(sum(ppsf) / len(ppsf)) if ppsf else None,
        "avg_days_on_market": int(sum(days) / len(days)) if days else None,
        "total_sold_last_6mo": len(comps)
    }
```

---

# PART 6: FRONTEND - CONSUMER LANDING PAGE

## File: `apps/web/app/cma/[code]/page.tsx`

```tsx
import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ConsumerLandingWizard } from '@/components/lead-pages/ConsumerLandingWizard';

interface PageProps {
  params: { code: string };
}

async function getAgentInfo(code: string) {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/cma/${code}`,
    { cache: 'no-store' }
  );
  if (!res.ok) return null;
  return res.json();
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const agent = await getAgentInfo(params.code);
  if (!agent) return { title: 'Page Not Found' };
  
  return {
    title: `${agent.headline} | ${agent.name}`,
    description: agent.subheadline,
  };
}

export default async function ConsumerLandingPage({ params }: PageProps) {
  const agent = await getAgentInfo(params.code);
  
  if (!agent) {
    notFound();
  }
  
  return (
    <div 
      className="min-h-screen"
      style={{ 
        background: `linear-gradient(135deg, ${agent.theme_color}10, white, ${agent.theme_color}05)` 
      }}
    >
      {/* Agent Header */}
      <div className="pt-8 pb-4 px-4 text-center">
        {agent.photo_url ? (
          <img
            src={agent.photo_url}
            alt={agent.name}
            className="w-20 h-20 rounded-full mx-auto mb-3 border-4 border-white shadow-lg object-cover"
          />
        ) : (
          <div 
            className="w-20 h-20 rounded-full mx-auto mb-3 border-4 border-white shadow-lg flex items-center justify-center text-white text-2xl font-bold"
            style={{ backgroundColor: agent.theme_color }}
          >
            {agent.name.charAt(0)}
          </div>
        )}
        <h2 className="text-lg font-semibold text-gray-900">{agent.name}</h2>
        {agent.company_name && (
          <p className="text-gray-600 text-sm">{agent.company_name}</p>
        )}
        {agent.license_number && (
          <p className="text-gray-500 text-xs">DRE# {agent.license_number}</p>
        )}
      </div>
      
      {/* Main Card */}
      <div className="max-w-md mx-auto px-4 pb-8">
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <h1 
            className="text-2xl font-bold text-center mb-2"
            style={{ color: agent.theme_color }}
          >
            {agent.headline}
          </h1>
          <p className="text-gray-600 text-center mb-6 text-sm">
            {agent.subheadline}
          </p>
          
          <ConsumerLandingWizard 
            agentCode={params.code}
            themeColor={agent.theme_color}
            agentName={agent.name}
          />
        </div>
        
        {/* Trust Badges */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            ✓ 100% Free  ✓ No Obligation  ✓ Results in Seconds
          </p>
        </div>
      </div>
      
      {/* Footer */}
      <div className="text-center pb-6">
        <p className="text-xs text-gray-400">
          Powered by <span className="font-medium">TrendyReports</span>
        </p>
      </div>
    </div>
  );
}
```

## File: `apps/web/components/lead-pages/ConsumerLandingWizard.tsx`

```tsx
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Phone, MapPin, Home, Check, Loader2, 
  ChevronRight, Search
} from 'lucide-react';

interface Props {
  agentCode: string;
  themeColor: string;
  agentName: string;
}

type Step = 'phone' | 'address' | 'confirm' | 'processing' | 'success';

interface Property {
  apn: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  owner_name?: string;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
  year_built?: number;
}

export function ConsumerLandingWizard({ agentCode, themeColor, agentName }: Props) {
  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Format phone as user types
  const formatPhone = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 10);
    if (digits.length >= 6) {
      return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
    } else if (digits.length >= 3) {
      return `(${digits.slice(0,3)}) ${digits.slice(3)}`;
    }
    return digits;
  };

  // Step 1: Phone validation
  const handlePhoneSubmit = () => {
    const digits = phone.replace(/\D/g, '');
    if (digits.length !== 10) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }
    setError('');
    setStep('address');
  };

  // Step 2: Address search
  const handleAddressSearch = async () => {
    if (!address.trim()) {
      setError('Please enter your property address');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch(`/api/v1/cma/${agentCode}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      });
      
      if (!res.ok) throw new Error('Search failed');
      
      const data = await res.json();
      setProperties(data);
      
      if (data.length === 0) {
        setError('No properties found. Please check the address and try again.');
      } else if (data.length === 1) {
        // Auto-select if only one result
        setSelectedProperty(data[0]);
        setStep('confirm');
      }
    } catch (err) {
      setError('Could not search. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Select property from list
  const handleSelectProperty = (property: Property) => {
    setSelectedProperty(property);
    setStep('confirm');
  };

  // Step 3: Submit request
  const handleSubmit = async () => {
    if (!consent) {
      setError('Please agree to the terms to continue');
      return;
    }
    
    setStep('processing');
    setError('');
    
    try {
      const res = await fetch(`/api/v1/cma/${agentCode}/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone.replace(/\D/g, ''),
          property_apn: selectedProperty!.apn,
          property_address: selectedProperty!.address,
          property_city: selectedProperty!.city,
          property_state: selectedProperty!.state,
          property_zip: selectedProperty!.zip,
          consent_given: consent
        })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Request failed');
      }
      
      // Wait a moment for dramatic effect, then show success
      setTimeout(() => setStep('success'), 1500);
      
    } catch (err: any) {
      setStep('confirm');
      setError(err.message || 'Something went wrong. Please try again.');
    }
  };

  // Render current step
  return (
    <div className="min-h-[300px]">
      <AnimatePresence mode="wait">
        {/* STEP 1: Phone */}
        {step === 'phone' && (
          <motion.div
            key="phone"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <StepIndicator current={1} total={3} color={themeColor} />
            
            <div className="flex items-center gap-2 mb-4">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <Phone className="w-4 h-4" style={{ color: themeColor }} />
              </div>
              <span className="font-medium text-gray-700">Your Phone Number</span>
            </div>
            
            <Input
              type="tel"
              placeholder="(555) 555-5555"
              value={phone}
              onChange={(e) => setPhone(formatPhone(e.target.value))}
              className="text-lg text-center h-12"
              autoFocus
            />
            
            <p className="text-xs text-gray-500 text-center">
              We'll text your report to this number
            </p>
            
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            
            <Button 
              onClick={handlePhoneSubmit}
              className="w-full h-12 text-base"
              style={{ backgroundColor: themeColor }}
            >
              Continue <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </motion.div>
        )}

        {/* STEP 2: Address */}
        {step === 'address' && (
          <motion.div
            key="address"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <StepIndicator current={2} total={3} color={themeColor} />
            
            <div className="flex items-center gap-2 mb-4">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <MapPin className="w-4 h-4" style={{ color: themeColor }} />
              </div>
              <span className="font-medium text-gray-700">Your Property Address</span>
            </div>
            
            <div className="relative">
              <Input
                type="text"
                placeholder="Enter your address..."
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddressSearch()}
                className="text-base h-12 pr-12"
                autoFocus
              />
              <button
                onClick={handleAddressSearch}
                disabled={loading}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-gray-100"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                ) : (
                  <Search className="w-5 h-5 text-gray-400" />
                )}
              </button>
            </div>
            
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            
            {/* Property Results */}
            {properties.length > 1 && (
              <div className="space-y-2 mt-4">
                <p className="text-sm text-gray-600 font-medium">Select your property:</p>
                {properties.map((prop, i) => (
                  <button
                    key={i}
                    onClick={() => handleSelectProperty(prop)}
                    className="w-full p-3 text-left border rounded-xl hover:border-gray-400 hover:bg-gray-50 transition"
                  >
                    <p className="font-medium text-gray-900">{prop.address}</p>
                    <p className="text-sm text-gray-500">
                      {prop.city}, {prop.state} {prop.zip}
                      {prop.owner_name && ` • ${prop.owner_name}`}
                    </p>
                  </button>
                ))}
              </div>
            )}
            
            <button 
              onClick={() => { setStep('phone'); setProperties([]); }}
              className="text-sm text-gray-500 hover:text-gray-700 w-full text-center py-2"
            >
              ← Back
            </button>
          </motion.div>
        )}

        {/* STEP 3: Confirm */}
        {step === 'confirm' && selectedProperty && (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <StepIndicator current={3} total={3} color={themeColor} />
            
            <div className="flex items-center gap-2 mb-4">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <Home className="w-4 h-4" style={{ color: themeColor }} />
              </div>
              <span className="font-medium text-gray-700">Confirm Your Property</span>
            </div>
            
            {/* Property Card */}
            <div className="bg-gray-50 p-4 rounded-xl border">
              <p className="font-semibold text-gray-900">{selectedProperty.address}</p>
              <p className="text-gray-600 text-sm">
                {selectedProperty.city}, {selectedProperty.state} {selectedProperty.zip}
              </p>
              {selectedProperty.owner_name && (
                <p className="text-gray-500 text-sm mt-1">
                  Owner: {selectedProperty.owner_name}
                </p>
              )}
              {(selectedProperty.bedrooms || selectedProperty.sqft) && (
                <div className="flex gap-3 mt-2 text-sm text-gray-600">
                  {selectedProperty.bedrooms && <span>{selectedProperty.bedrooms} bed</span>}
                  {selectedProperty.bathrooms && <span>{selectedProperty.bathrooms} bath</span>}
                  {selectedProperty.sqft && <span>{selectedProperty.sqft.toLocaleString()} sqft</span>}
                </div>
              )}
            </div>
            
            {/* Consent */}
            <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
              <Checkbox
                checked={consent}
                onCheckedChange={(v) => setConsent(v as boolean)}
                id="consent"
                className="mt-0.5"
              />
              <label htmlFor="consent" className="text-sm text-gray-600 leading-tight">
                I agree to receive my home value report via text and to be contacted by {agentName} about my property.
              </label>
            </div>
            
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            
            <Button 
              onClick={handleSubmit}
              disabled={!consent}
              className="w-full h-12 text-base"
              style={{ backgroundColor: themeColor }}
            >
              Get My Free Report
            </Button>
            
            <button 
              onClick={() => { setStep('address'); setSelectedProperty(null); }}
              className="text-sm text-gray-500 hover:text-gray-700 w-full text-center py-2"
            >
              ← Change address
            </button>
          </motion.div>
        )}

        {/* PROCESSING */}
        {step === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-12 text-center"
          >
            <div 
              className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
              style={{ backgroundColor: `${themeColor}20` }}
            >
              <Loader2 
                className="w-8 h-8 animate-spin" 
                style={{ color: themeColor }} 
              />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Generating Your Report...
            </h3>
            <p className="text-gray-600 text-sm">
              Analyzing property data and finding comparables
            </p>
          </motion.div>
        )}

        {/* SUCCESS */}
        {step === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-8 text-center"
          >
            <div 
              className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
              style={{ backgroundColor: `${themeColor}20` }}
            >
              <Check 
                className="w-8 h-8" 
                style={{ color: themeColor }} 
              />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Your Report is on the Way!
            </h3>
            <p className="text-gray-600 mb-4">
              Check your phone for a text message with your personalized home value report.
            </p>
            <div className="bg-gray-50 rounded-xl p-4 text-sm">
              <p className="text-gray-500">Sent to:</p>
              <p className="font-medium text-gray-900">{phone}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


// Step indicator component
function StepIndicator({ current, total, color }: { current: number; total: number; color: string }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 rounded-full transition-all ${
            i + 1 <= current ? 'w-8' : 'w-4'
          }`}
          style={{ 
            backgroundColor: i + 1 <= current ? color : '#E5E7EB'
          }}
        />
      ))}
    </div>
  );
}
```

---

# PART 7: FRONTEND - MOBILE REPORT VIEWER

## File: `apps/web/app/r/[id]/page.tsx`

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
  
  const price = report.value_estimate?.mid;
  const priceStr = price ? `$${price.toLocaleString()}` : '';
  
  return {
    title: `Home Value Report | ${report.property.address}`,
    description: `Estimated value: ${priceStr}. ${report.property.bedrooms} bed, ${report.property.bathrooms} bath, ${report.property.sqft?.toLocaleString()} sqft.`,
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

## File: `apps/web/components/mobile-report/MobileReportViewer.tsx`

This is a large component - create it with these features:

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

// Full component implementation with:
// - 5 tabs: Overview, Details, Comps, Market, Agent
// - Swipeable comp cards
// - Tap-to-call/text/email on Agent tab
// - On-demand PDF download
// - Analytics tracking for all interactions
// - Responsive mobile-first design

// See previous CURSOR_MOBILE_REPORT_VIEWER_PACKAGE.md for full implementation
// The MobileReportViewer component is ~500 lines

export function MobileReportViewer({ report, reportId }: Props) {
  // Implementation from Part 5 of previous package
  // ...
}
```

**NOTE:** The full MobileReportViewer implementation is in the previous package. Copy it from there - it includes all 5 tabs with full functionality.

---

# PART 8: AGENT DASHBOARD - LEADS PAGE

## File: `apps/web/app/app/leads/page.tsx`

```tsx
'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Copy, ExternalLink, QrCode, Download,
  Phone, Eye, Clock, FileText, TrendingUp,
  Search, Filter
} from 'lucide-react';
import { toast } from 'sonner';

export default function AgentLeadsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [settingsRes, leadsRes] = await Promise.all([
        fetch('/api/v1/me/lead-page').then(r => r.json()),
        fetch('/api/v1/me/leads').then(r => r.json())
      ]);
      setSettings(settingsRes);
      setLeads(leadsRes.leads || []);
    } catch (err) {
      console.error('Failed to fetch data', err);
    } finally {
      setLoading(false);
    }
  };

  const copyUrl = () => {
    navigator.clipboard.writeText(settings?.url);
    toast.success('URL copied to clipboard!');
  };

  const downloadQR = async (format: 'png' | 'svg') => {
    // Download QR code
    const link = document.createElement('a');
    link.href = settings?.qr_code_url;
    link.download = `my-lead-page-qr.${format}`;
    link.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Lead Pages</h1>
        <p className="text-gray-600">Share your link to capture leads automatically</p>
      </div>

      {/* Your Lead Page Card */}
      <Card className="p-6">
        <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-violet-600" />
          Your Lead Page
        </h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          {/* URL Section */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Your Shareable URL
            </label>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-100 px-4 py-3 rounded-lg font-mono text-sm truncate">
                {settings?.url}
              </div>
              <Button variant="outline" size="icon" onClick={copyUrl}>
                <Copy className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="icon" asChild>
                <a href={settings?.url} target="_blank">
                  <ExternalLink className="w-4 h-4" />
                </a>
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Share this link on business cards, social media, email signatures, yard signs, etc.
            </p>
          </div>

          {/* QR Code Section */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Your QR Code
            </label>
            <div className="flex items-center gap-4">
              <div className="bg-white border rounded-xl p-3">
                <img 
                  src={settings?.qr_code_url} 
                  alt="QR Code"
                  className="w-24 h-24"
                />
              </div>
              <div className="space-y-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => downloadQR('png')}
                  className="w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download PNG
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => downloadQR('svg')}
                  className="w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download SVG
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t">
          <StatBox 
            label="Page Visits" 
            value={settings?.landing_page_visits || 0} 
            icon={<Eye className="w-4 h-4" />}
          />
          <StatBox 
            label="Reports Sent" 
            value={leads.length} 
            icon={<FileText className="w-4 h-4" />}
          />
          <StatBox 
            label="Contacts" 
            value={leads.filter(l => l.agent_contact_clicked).length}
            icon={<Phone className="w-4 h-4" />}
            highlight
          />
          <StatBox 
            label="Contact Rate" 
            value={`${leads.length ? Math.round(leads.filter(l => l.agent_contact_clicked).length / leads.length * 100) : 0}%`}
            icon={<TrendingUp className="w-4 h-4" />}
          />
        </div>
      </Card>

      {/* Leads List */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg">Your Leads</h2>
          <div className="flex items-center gap-2">
            <Button 
              variant={filter === 'all' ? 'default' : 'outline'} 
              size="sm"
              onClick={() => setFilter('all')}
            >
              All
            </Button>
            <Button 
              variant={filter === 'hot' ? 'default' : 'outline'} 
              size="sm"
              onClick={() => setFilter('hot')}
            >
              🔥 Hot
            </Button>
            <Button 
              variant={filter === 'contacted' ? 'default' : 'outline'} 
              size="sm"
              onClick={() => setFilter('contacted')}
            >
              Contacted
            </Button>
          </div>
        </div>

        {leads.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No leads yet. Share your URL to start capturing leads!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {leads
              .filter(lead => {
                if (filter === 'hot') return lead.view_count > 1 || lead.agent_contact_clicked;
                if (filter === 'contacted') return lead.agent_contact_clicked;
                return true;
              })
              .map((lead, i) => (
                <LeadRow key={i} lead={lead} />
              ))
            }
          </div>
        )}
      </Card>
    </div>
  );
}


function StatBox({ label, value, icon, highlight }: { 
  label: string; 
  value: string | number; 
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className={`text-center p-4 rounded-xl ${highlight ? 'bg-violet-50' : 'bg-gray-50'}`}>
      <div className={`flex justify-center mb-2 ${highlight ? 'text-violet-600' : 'text-gray-500'}`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}


function LeadRow({ lead }: { lead: any }) {
  const isHot = lead.view_count > 1 || lead.agent_contact_clicked;
  
  return (
    <div className={`p-4 rounded-xl border ${isHot ? 'border-orange-200 bg-orange-50' : 'bg-gray-50'}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-gray-900 truncate">
              {lead.property_address}
            </p>
            {isHot && <span className="text-orange-500">🔥</span>}
          </div>
          <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <Phone className="w-3 h-3" />
              {lead.consumer_phone}
            </span>
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              {lead.view_count} views
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(lead.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {lead.agent_contact_clicked && (
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
              Contacted
            </span>
          )}
          {lead.pdf_url && (
            <span className="px-2 py-1 bg-violet-100 text-violet-700 text-xs rounded-full">
              PDF
            </span>
          )}
          <a 
            href={`tel:${lead.consumer_phone}`}
            className="p-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700"
          >
            <Phone className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
```

---

# PART 9: ADMIN DASHBOARD

## File: `apps/web/app/admin/lead-pages/page.tsx`

See the admin dashboard implementation from the previous package - includes:

- Overview stats cards
- Daily trend chart
- Device breakdown pie chart
- Conversion funnel visualization
- Agent leaderboard table
- Recent activity feed

---

# PART 10: IMPLEMENTATION CHECKLIST

## Phase 1: Database & Auth (Day 1)
- [ ] Run migration `0037_lead_pages.sql`
- [ ] Add agent code generation to user registration
- [ ] Create `agent_code.py` service

## Phase 2: Public API (Day 2)
- [ ] Create `lead_pages.py` routes
- [ ] Create `mobile_report.py` routes
- [ ] Test endpoints with Postman/curl

## Phase 3: Consumer Landing Page (Day 3)
- [ ] Create `/cma/[code]/page.tsx`
- [ ] Create `ConsumerLandingWizard.tsx`
- [ ] Test full consumer flow

## Phase 4: Celery Tasks (Day 4)
- [ ] Create `process_consumer_report` task
- [ ] Create `generate_pdf_on_demand_task`
- [ ] Set up Twilio SMS
- [ ] Test SMS delivery

## Phase 5: Mobile Report Viewer (Day 5)
- [ ] Create `/r/[id]/page.tsx`
- [ ] Create `MobileReportViewer.tsx` with all 5 tabs
- [ ] Test on mobile devices
- [ ] Test PDF on-demand

## Phase 6: Agent Dashboard (Day 6)
- [ ] Create `/app/leads/page.tsx`
- [ ] Add QR code generation
- [ ] Add leads list with engagement metrics
- [ ] Add navigation link

## Phase 7: Admin Dashboard (Day 7)
- [ ] Create admin metrics API endpoints
- [ ] Create `/admin/lead-pages/page.tsx`
- [ ] Add charts and visualizations

## Phase 8: Polish & Test (Day 8)
- [ ] End-to-end testing
- [ ] Mobile responsive testing
- [ ] Rate limiting verification
- [ ] Error handling
- [ ] Analytics verification

---

# ENVIRONMENT VARIABLES

```bash
# Twilio SMS
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# App URLs
APP_URL=https://trendyreports.io
NEXT_PUBLIC_API_URL=https://api.trendyreports.io

# Existing vars (already configured)
# DATABASE_URL, R2_*, SITEX_*, etc.
```

---

# SUMMARY

This package implements the complete Lead Pages feature:

1. **Agent gets unique code** on account creation
2. **Agent shares URL/QR** from their dashboard
3. **Consumer visits URL** and sees agent-branded landing page
4. **Consumer completes wizard** (phone → address → confirm)
5. **System processes instantly** (JSON, no PDF)
6. **SMS sent to consumer** with mobile report link
7. **SMS sent to agent** with lead notification
8. **Consumer views mobile report** with 5 interactive tabs
9. **Consumer can download PDF** on-demand if desired
10. **Agent tracks leads** in dashboard with engagement metrics
11. **Admin monitors** overall system performance

**Key Innovation:** Mobile-first, PDF on-demand = faster delivery, better UX, lower costs.
