# Mobile Report Viewer Documentation

## Overview

The Mobile Report Viewer is a consumer-facing feature that delivers property value reports via SMS with a mobile-first web experience. Unlike traditional PDF-first approaches, this system prioritizes instant delivery and mobile engagement, generating PDFs only on demand.

### Key Principle

```
OLD: Request → Generate PDF (10s) → SMS → User ignores PDF
NEW: Request → Store JSON (instant) → SMS → Mobile view → PDF if clicked
```

### Benefits

| Metric | Before | After |
|--------|--------|-------|
| Time to SMS | ~15 seconds | < 2 seconds |
| Mobile engagement | ~5% | ~40%+ |
| PDF generation cost | Every report | ~10% of reports |
| Agent contact rate | ~2% | ~8-15% |

---

## Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONSUMER REPORT FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. AGENT INITIATES                                                          │
│     ┌──────────────┐                                                         │
│     │ Agent Portal │ → Property Address + Consumer Phone                     │
│     └──────────────┘                                                         │
│            │                                                                 │
│            ▼                                                                 │
│  2. DATA COLLECTION (Celery Worker)                                          │
│     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│     │    SiteX     │ →   │  SimplyRETS  │ →   │   Calculate  │              │
│     │ Property Data│     │  Comparables │     │ Value Range  │              │
│     └──────────────┘     └──────────────┘     └──────────────┘              │
│            │                                                                 │
│            ▼                                                                 │
│  3. STORAGE (PostgreSQL)                                                     │
│     ┌──────────────────────────────────────────────────────┐                │
│     │ consumer_reports table (JSON fields)                  │                │
│     │ - property_data, comparables, value_estimate          │                │
│     │ - market_stats, engagement metrics                    │                │
│     └──────────────────────────────────────────────────────┘                │
│            │                                                                 │
│            ▼                                                                 │
│  4. NOTIFICATIONS (Twilio)                                                   │
│     ┌──────────────┐     ┌──────────────┐                                   │
│     │ Consumer SMS │     │  Agent SMS   │                                   │
│     │ "View Report"│     │ "New Lead!"  │                                   │
│     └──────────────┘     └──────────────┘                                   │
│            │                                                                 │
│            ▼                                                                 │
│  5. MOBILE VIEWER (Next.js)                                                  │
│     ┌──────────────────────────────────────────────────────┐                │
│     │ /r/{report_id}                                        │                │
│     │ ┌─────────┬─────────┬─────────┬─────────┬─────────┐  │                │
│     │ │Overview │ Details │  Comps  │ Market  │  Agent  │  │                │
│     │ └─────────┴─────────┴─────────┴─────────┴─────────┘  │                │
│     └──────────────────────────────────────────────────────┘                │
│            │                                                                 │
│            ▼                                                                 │
│  6. ON-DEMAND PDF (Optional)                                                 │
│     ┌──────────────┐                                                         │
│     │   PDFShift   │ → R2 Storage → Download Link                           │
│     └──────────────┘                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14 | Mobile Report Viewer, Admin Dashboard |
| API | FastAPI | Report data, analytics, PDF generation |
| Worker | Celery | Background processing, PDF generation |
| Database | PostgreSQL | Report storage, analytics |
| SMS | Twilio | Consumer and agent notifications |
| PDF | PDFShift | On-demand PDF generation |
| Storage | Cloudflare R2 | PDF file storage |
| Property Data | SiteX Pro | Property details, ownership |
| Comparables | SimplyRETS | MLS comparable sales |

---

## Database Schema

### Migration: `0038_mobile_reports.sql`

#### consumer_reports Table

```sql
CREATE TABLE consumer_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent Relationship
    agent_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    agent_code VARCHAR(10) NOT NULL,
    
    -- Consumer Information (Lead)
    consumer_phone VARCHAR(20) NOT NULL,
    consumer_email VARCHAR(255),
    consent_given BOOLEAN DEFAULT false,
    consent_timestamp TIMESTAMPTZ,
    
    -- Property Data (JSON - Powers Mobile View)
    property_address TEXT NOT NULL,
    property_city VARCHAR(100),
    property_state VARCHAR(2),
    property_zip VARCHAR(10),
    property_data JSONB NOT NULL DEFAULT '{}',
    comparables JSONB NOT NULL DEFAULT '[]',
    market_stats JSONB DEFAULT '{}',
    value_estimate JSONB DEFAULT '{}',
    
    -- Report Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, ready, failed
    error_message TEXT,
    
    -- PDF (On-Demand Only)
    pdf_url TEXT,
    pdf_generated_at TIMESTAMPTZ,
    pdf_requested_count INTEGER DEFAULT 0,
    
    -- SMS Tracking
    consumer_sms_sent_at TIMESTAMPTZ,
    consumer_sms_sid VARCHAR(50),
    agent_sms_sent_at TIMESTAMPTZ,
    agent_sms_sid VARCHAR(50),
    
    -- Engagement Metrics
    view_count INTEGER DEFAULT 0,
    unique_views INTEGER DEFAULT 0,
    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,
    tabs_viewed JSONB DEFAULT '[]',
    time_on_page INTEGER DEFAULT 0,
    agent_contact_clicked BOOLEAN DEFAULT false,
    agent_contact_type VARCHAR(20),  -- 'call', 'text', 'email'
    
    -- Device/Session Metadata
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),  -- 'mobile', 'tablet', 'desktop'
    referrer TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### JSON Field Structures

**property_data:**
```json
{
  "address": "123 Main St",
  "city": "Los Angeles",
  "state": "CA",
  "zip": "90210",
  "owner_name": "John Smith",
  "apn": "1234-567-890",
  "bedrooms": 4,
  "bathrooms": 3.5,
  "sqft": 2500,
  "lot_size": 8500,
  "year_built": 1985,
  "property_type": "Single Family",
  "latitude": 34.0522,
  "longitude": -118.2437,
  "tax_assessed_value": 850000,
  "last_sale_date": "2019-05-15",
  "last_sale_price": 725000
}
```

**comparables:**
```json
[
  {
    "address": "456 Oak Ave",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90210",
    "sold_price": 875000,
    "sold_date": "2024-01-15",
    "days_ago": 45,
    "bedrooms": 4,
    "bathrooms": 3,
    "sqft": 2400,
    "lot_size": 7500,
    "year_built": 1990,
    "price_per_sqft": 365,
    "distance_miles": 0.3,
    "photo_url": "https://..."
  }
]
```

**value_estimate:**
```json
{
  "low": 825000,
  "mid": 875000,
  "high": 925000,
  "confidence": "high"  // high, medium, low
}
```

**market_stats:**
```json
{
  "median_price": 850000,
  "avg_price_per_sqft": 375,
  "avg_days_on_market": 28,
  "total_sold_last_6mo": 45,
  "price_trend_pct": 5.2
}
```

#### report_analytics Table

```sql
CREATE TABLE report_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES consumer_reports(id) ON DELETE CASCADE,
    
    -- Event Tracking
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    
    -- Session Info
    session_id VARCHAR(100),
    
    -- Device/Location
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Event Types:**
| Event Type | Description | Event Data |
|------------|-------------|------------|
| `view` | Page view | `{}` |
| `tab_change` | User switched tabs | `{"tab": "comps"}` |
| `agent_click` | Contact button clicked | `{"contact_type": "call"}` |
| `pdf_request` | PDF download requested | `{}` |
| `share` | Share button used | `{}` |

#### Admin Views

```sql
-- Daily Metrics Summary
CREATE VIEW admin_daily_metrics AS
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

-- Agent Leaderboard
CREATE VIEW admin_agent_leaderboard AS
SELECT 
    u.id as agent_id,
    CONCAT(u.first_name, ' ', u.last_name) as agent_name,
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
GROUP BY u.id, u.first_name, u.last_name, u.email, a.name
ORDER BY total_reports DESC;

-- Hourly Distribution
CREATE VIEW admin_hourly_distribution AS
SELECT 
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as report_count,
    COUNT(*) FILTER (WHERE pdf_url IS NOT NULL) as pdf_count
FROM consumer_reports
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;
```

#### Indexes

```sql
CREATE INDEX idx_consumer_reports_agent ON consumer_reports(agent_id);
CREATE INDEX idx_consumer_reports_code ON consumer_reports(agent_code);
CREATE INDEX idx_consumer_reports_status ON consumer_reports(status);
CREATE INDEX idx_consumer_reports_created ON consumer_reports(created_at DESC);

CREATE INDEX idx_report_analytics_report ON report_analytics(report_id);
CREATE INDEX idx_report_analytics_type ON report_analytics(event_type);
CREATE INDEX idx_report_analytics_created ON report_analytics(created_at DESC);
```

---

## API Endpoints

### Public Endpoints (No Authentication Required)

These endpoints are public because consumers access reports via SMS links without logging in.

#### GET /v1/r/{report_id}/data

Retrieves report data for the mobile viewer.

**Response:**
```json
{
  "id": "uuid",
  "property": {
    "address": "123 Main St",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90210",
    "owner_name": "John Smith",
    "bedrooms": 4,
    "bathrooms": 3.5,
    "sqft": 2500,
    "lot_size": 8500,
    "year_built": 1985,
    "latitude": 34.0522,
    "longitude": -118.2437
  },
  "comparables": [...],
  "value_estimate": {
    "low": 825000,
    "mid": 875000,
    "high": 925000,
    "confidence": "high"
  },
  "market_stats": {
    "median_price": 850000,
    "avg_price_per_sqft": 375,
    "avg_days_on_market": 28,
    "total_sold_last_6mo": 45
  },
  "agent": {
    "name": "Jane Agent",
    "phone": "+15551234567",
    "email": "jane@realty.com",
    "photo_url": "https://...",
    "company_name": "ABC Realty",
    "license_number": "DRE01234567"
  },
  "has_pdf": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Side Effects:**
- Increments `view_count` on the report
- Sets `first_viewed_at` if first view
- Updates `last_viewed_at`
- Records device type
- Creates `view` event in report_analytics

#### POST /v1/r/{report_id}/analytics

Tracks user interactions on the mobile viewer.

**Request Body:**
```json
{
  "event_type": "tab_change",
  "event_data": {"tab": "comps"},
  "session_id": "abc123"
}
```

**Event Types:**
- `tab_change` - User switched tabs
- `agent_click` - Contact button clicked (includes `contact_type`)
- `share` - Share button used
- `pdf_request` - PDF download initiated

**Response:**
```json
{
  "success": true
}
```

#### POST /v1/r/{report_id}/pdf

Requests PDF generation (on-demand).

**Response (PDF exists):**
```json
{
  "status": "ready",
  "pdf_url": "https://r2.../consumer-reports/uuid.pdf"
}
```

**Response (PDF generating):**
```json
{
  "status": "generating",
  "message": "PDF is being generated. This may take a few seconds."
}
```

#### GET /v1/r/{report_id}/pdf/status

Polls for PDF generation status.

**Response:**
```json
{
  "status": "ready",  // or "generating"
  "pdf_url": "https://..."  // only if ready
}
```

---

### Admin Endpoints (Authentication Required)

All admin endpoints require platform admin authentication.

#### GET /v1/admin/metrics/overview

High-level dashboard KPIs.

**Response:**
```json
{
  "total_reports": 1250,
  "total_views": 4580,
  "total_pdfs": 125,
  "total_contacts": 98,
  "pdf_rate_pct": 10.0,
  "contact_rate_pct": 7.8,
  "reports_today": 15,
  "views_today": 42,
  "contacts_today": 3,
  "reports_this_week": 85,
  "reports_this_month": 320,
  "reports_trend_pct": 12.5,
  "contacts_trend_pct": 8.2
}
```

#### GET /v1/admin/metrics/daily

Daily metrics for charting.

**Query Parameters:**
- `days` (int, default: 30, range: 7-90)

**Response:**
```json
[
  {
    "date": "2024-01-15",
    "reports_requested": 45,
    "reports_ready": 43,
    "reports_failed": 2,
    "pdfs_generated": 5,
    "agent_contacts": 4,
    "total_views": 128,
    "avg_views_per_report": 2.8,
    "avg_time_seconds": 45.2,
    "unique_agents": 12
  }
]
```

#### GET /v1/admin/metrics/agents

Agent leaderboard.

**Query Parameters:**
- `limit` (int, default: 20, range: 10-100)
- `sort_by` (string: `total_reports`, `contacts`, `contact_rate_pct`)

**Response:**
```json
[
  {
    "agent_id": "uuid",
    "agent_name": "Jane Agent",
    "agent_email": "jane@realty.com",
    "account_name": "ABC Realty",
    "total_reports": 85,
    "reports_30d": 25,
    "total_views": 312,
    "contacts": 12,
    "contact_rate_pct": 14.1,
    "pdfs_downloaded": 8
  }
]
```

#### GET /v1/admin/metrics/devices

Device type breakdown.

**Response:**
```json
[
  {"device_type": "mobile", "count": 850, "percentage": 68.0},
  {"device_type": "desktop", "count": 320, "percentage": 25.6},
  {"device_type": "tablet", "count": 80, "percentage": 6.4}
]
```

#### GET /v1/admin/metrics/hourly

Hourly distribution for load planning.

**Response:**
```json
[
  {"hour": 0, "report_count": 12, "pdf_count": 1},
  {"hour": 1, "report_count": 8, "pdf_count": 0},
  ...
  {"hour": 23, "report_count": 15, "pdf_count": 2}
]
```

#### GET /v1/admin/metrics/conversion-funnel

Conversion funnel metrics.

**Query Parameters:**
- `days` (int, default: 30, range: 7-90)

**Response:**
```json
{
  "period_days": 30,
  "funnel": [
    {"stage": "Reports Requested", "count": 500, "pct": 100.0},
    {"stage": "Reports Generated", "count": 485, "pct": 97.0},
    {"stage": "Reports Viewed", "count": 420, "pct": 84.0},
    {"stage": "Multiple Views", "count": 180, "pct": 36.0},
    {"stage": "Agent Contacted", "count": 45, "pct": 9.0},
    {"stage": "PDF Downloaded", "count": 52, "pct": 10.4}
  ]
}
```

#### GET /v1/admin/metrics/recent

Recent activity feed.

**Query Parameters:**
- `limit` (int, default: 20, range: 10-100)
- `status` (optional: `pending`, `ready`, `failed`)

**Response:**
```json
[
  {
    "id": "uuid",
    "agent_name": "Jane Agent",
    "property_address": "123 Main St",
    "status": "ready",
    "view_count": 3,
    "agent_contacted": true,
    "has_pdf": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

## Frontend Components

### Mobile Report Viewer

**Path:** `/r/[id]`

**File:** `apps/web/app/r/[id]/page.tsx`

**Component:** `apps/web/components/mobile-report/MobileReportViewer.tsx`

#### Tab Structure

| Tab | Icon | Description |
|-----|------|-------------|
| Overview | Home | Value estimate hero card, quick stats, address, agent preview |
| Details | Building2 | Full property details table |
| Comps | TrendingUp | Comparable sales carousel with photos |
| Market | BarChart3 | Market statistics summary |
| Agent | User | Agent profile, contact buttons, PDF download |

#### Features

1. **Responsive Design**: Mobile-first with full tablet/desktop support
2. **Tab Navigation**: Fixed bottom navigation bar
3. **Animated Transitions**: Smooth tab switching with Framer Motion
4. **Comparables Carousel**: Swipeable cards with pagination dots
5. **Contact Actions**: One-tap call, text, email buttons
6. **PDF On-Demand**: Generate and download PDF from Agent tab
7. **Share Functionality**: Native share API or clipboard fallback
8. **Analytics Tracking**: All interactions tracked automatically

#### Analytics Events Tracked

```typescript
// Tab changes
{event_type: 'tab_change', event_data: {tab: 'comps'}}

// Agent contact
{event_type: 'agent_click', event_data: {contact_type: 'call'}}

// PDF request
{event_type: 'pdf_request', event_data: {}}

// Share
{event_type: 'share', event_data: {}}
```

---

### Admin Dashboard

**Path:** `/admin/lead-pages`

**File:** `apps/web/app/admin/(dashboard)/lead-pages/page.tsx`

#### Dashboard Sections

1. **Overview Cards**
   - Total Reports
   - Total Views
   - Agent Contacts (highlighted)
   - PDFs Generated

2. **Charts**
   - Reports & Contacts (30 Days) - Line chart
   - Device Breakdown - Pie chart

3. **Conversion Funnel**
   - 6-stage visual funnel with percentages

4. **Agent Leaderboard**
   - Sortable table with contact rate badges

5. **Recent Activity**
   - Real-time feed of latest reports

---

## File Structure

```
apps/
├── api/
│   └── src/api/
│       └── routes/
│           ├── mobile_reports.py      # Public report endpoints
│           └── admin_metrics.py       # Admin dashboard endpoints
│
├── web/
│   ├── app/
│   │   ├── r/
│   │   │   └── [id]/
│   │   │       └── page.tsx           # Mobile viewer page
│   │   │
│   │   ├── admin/
│   │   │   └── (dashboard)/
│   │   │       └── lead-pages/
│   │   │           └── page.tsx       # Admin dashboard
│   │   │
│   │   └── api/
│   │       └── proxy/
│   │           └── v1/
│   │               ├── r/
│   │               │   └── [id]/
│   │               │       ├── data/
│   │               │       │   └── route.ts
│   │               │       ├── analytics/
│   │               │       │   └── route.ts
│   │               │       └── pdf/
│   │               │           └── route.ts
│   │               │
│   │               └── admin/
│   │                   └── metrics/
│   │                       ├── overview/
│   │                       │   └── route.ts
│   │                       ├── daily/
│   │                       │   └── route.ts
│   │                       ├── agents/
│   │                       │   └── route.ts
│   │                       ├── devices/
│   │                       │   └── route.ts
│   │                       ├── conversion-funnel/
│   │                       │   └── route.ts
│   │                       └── recent/
│   │                           └── route.ts
│   │
│   └── components/
│       └── mobile-report/
│           └── MobileReportViewer.tsx
│
└── worker/
    └── src/worker/
        └── tasks/
            └── consumer_report.py     # Report processing task

db/
└── migrations/
    └── 0038_mobile_reports.sql

docs/
└── MOBILE_REPORT_VIEWER.md            # This document
```

---

## Metrics & KPIs

### Primary Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Contact Rate** | % of reports where agent was contacted | > 8% |
| **View Rate** | % of SMS recipients who viewed report | > 60% |
| **PDF Rate** | % of viewers who downloaded PDF | ~10% |
| **Mobile Rate** | % of views from mobile devices | > 65% |

### Secondary Metrics

| Metric | Definition | Purpose |
|--------|------------|---------|
| Time to SMS | Seconds from request to SMS sent | Performance |
| Avg Views/Report | Average page views per report | Engagement |
| Avg Time on Page | Seconds spent viewing report | Quality |
| Tabs Viewed | Which sections users explore | Content optimization |
| Multiple Views | Reports viewed more than once | Interest indicator |

### Conversion Funnel

```
Reports Requested     ████████████████████████████████  100%
        ↓
Reports Generated     ██████████████████████████████░░   97%
        ↓
Reports Viewed        ████████████████████████░░░░░░░░   84%
        ↓
Multiple Views        ████████████░░░░░░░░░░░░░░░░░░░░   36%
        ↓
Agent Contacted       ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    9%
        ↓
PDF Downloaded        ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   10%
```

---

## Security Considerations

### Public Endpoints

1. **No PII in URLs**: Report IDs are UUIDs, not sequential
2. **Rate Limiting**: Applied to prevent abuse
3. **No Auth Required**: By design - consumers access via SMS
4. **IP Logging**: For abuse detection

### Admin Endpoints

1. **Platform Admin Only**: `is_platform_admin = true` required
2. **Cookie Authentication**: `mr_token` cookie validated
3. **No Direct DB Access**: All queries through API

### Data Privacy

1. **Consumer Phone**: Stored for SMS delivery, not exposed in API
2. **Property Data**: Public record data, no sensitive PII
3. **Analytics**: IP addresses stored for fraud detection
4. **Retention**: Consider 90-day retention policy for analytics

---

## Error Handling

### Report Not Found

```json
{
  "detail": "Report not found"
}
```
HTTP 404 - Report ID invalid or status not 'ready'

### PDF Generation Failed

```json
{
  "detail": "PDF generation failed"
}
```
HTTP 500 - Worker failed to generate PDF

### Rate Limited

```json
{
  "detail": "Rate limit exceeded"
}
```
HTTP 429 - Too many requests

---

## Future Enhancements

### Planned Features

1. **Report Scheduling**: Auto-generate reports on schedule
2. **A/B Testing**: Test different mobile viewer layouts
3. **Push Notifications**: Follow-up reminders
4. **Agent Response Time**: Track how fast agents respond
5. **Geographic Heatmaps**: Visualize report locations
6. **Custom Branding**: White-label mobile viewer

### Performance Optimizations

1. **CDN Caching**: Cache report data at edge
2. **Image Optimization**: Compress comparable photos
3. **Lazy Loading**: Load comparables on demand
4. **Service Worker**: Offline support for viewed reports

---

## Troubleshooting

### Report Shows "Not Found"

1. Check report status is 'ready' in database
2. Verify report_id UUID format
3. Check if report was deleted

### PDF Not Generating

1. Check PDFShift API key is valid
2. Verify R2 credentials are configured
3. Check worker logs for errors

### Analytics Not Recording

1. Verify API proxy routes are working
2. Check browser console for errors
3. Ensure report_id is valid

### Admin Dashboard Empty

1. Verify user has `is_platform_admin = true`
2. Check authentication cookie
3. Verify database views exist

---

## Related Documentation

- [Property Reports Documentation](./PROPERTY_REPORTS_DOCUMENTATION.md)
- [Admin Console Documentation](./ADMIN_CONSOLE.md)
- [SimplyRETS API](./SIMPLYRETS_API.md)
- [Report Types Matrix](./REPORT_TYPES_MATRIX.md)

