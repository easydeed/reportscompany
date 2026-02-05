# TrendyReports / Market Reports - Master System Overview

> **Purpose**: This document provides Claude with complete context about every module, service, and integration in the TrendyReports platform. Use this as the authoritative reference for understanding how the system works.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [API Service (FastAPI)](#2-api-service-fastapi)
3. [Worker Service (Celery)](#3-worker-service-celery)
4. [Frontend (Next.js)](#4-frontend-nextjs)
5. [Database Schema](#5-database-schema)
6. [PDF Generation System](#6-pdf-generation-system)
7. [Property Report Templates](#7-property-report-templates)
8. [External Integrations](#8-external-integrations)
9. [Authentication & Authorization](#9-authentication--authorization)
10. [Environment Configuration](#10-environment-configuration)
11. [Key Workflows](#11-key-workflows)
12. [Common Patterns & Conventions](#12-common-patterns--conventions)

---

## 1. System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRENDYREPORTS PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │   Frontend   │    │   API        │    │   Worker     │                  │
│   │   (Next.js)  │───▶│   (FastAPI)  │───▶│   (Celery)   │                  │
│   │   Port 3000  │    │   Port 10000 │    │              │                  │
│   └──────────────┘    └──────┬───────┘    └──────┬───────┘                  │
│                              │                    │                          │
│         ┌────────────────────┼────────────────────┼─────────────────┐        │
│         │                    │                    │                 │        │
│         ▼                    ▼                    ▼                 ▼        │
│   ┌──────────┐        ┌──────────┐        ┌──────────┐      ┌──────────┐    │
│   │PostgreSQL│        │  Redis   │        │ R2/S3    │      │ External │    │
│   │   :5432  │        │  :6379   │        │ Storage  │      │   APIs   │    │
│   └──────────┘        └──────────┘        └──────────┘      └──────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Summary

| Service | Framework | Port | Purpose |
|---------|-----------|------|---------|
| **API** | FastAPI (Python 3.11+) | 10000 | REST API, authentication, business logic |
| **Worker** | Celery (Python 3.11+) | N/A | Background jobs, PDF generation, emails |
| **Frontend** | Next.js 16 + React 19 | 3000 | User dashboard, admin console |
| **Database** | PostgreSQL 15 | 5432 | Primary data store with RLS |
| **Cache/Broker** | Redis 7 | 6379 | Task queue, caching, sessions |

### Directory Structure

```
apps/
├── api/                    # FastAPI backend
│   └── src/api/
│       ├── routes/         # API endpoints
│       ├── services/       # Business logic
│       ├── schemas/        # Pydantic models
│       ├── models/         # SQLAlchemy models
│       └── middleware/     # Auth, RLS, CORS
│
├── worker/                 # Celery worker
│   └── src/worker/
│       ├── tasks.py        # Celery task definitions
│       ├── property_builder.py    # Report HTML builder
│       ├── pdf_engine.py   # PDF generation
│       ├── templates/      # Jinja2 templates
│       │   └── property/   # 5 theme templates
│       └── vendors/        # External API clients
│
└── web/                    # Next.js frontend
    └── src/
        ├── app/            # App router pages
        ├── components/     # React components
        └── lib/            # Utilities, API client
```

---

## 2. API Service (FastAPI)

### Location: `apps/api/src/api/`

### Core Components

#### Routes (`routes/`)

| File | Prefix | Description |
|------|--------|-------------|
| `auth.py` | `/v1/auth` | Login, register, password reset, email verification |
| `reports.py` | `/v1/reports` | Market report CRUD, generation triggers |
| `schedules.py` | `/v1/schedules` | Scheduled report management |
| `property.py` | `/v1/property` | Property search, property report CRUD |
| `leads.py` | `/v1/leads` | Lead capture and management |
| `contacts.py` | `/v1/contacts` | Contact and group management |
| `account.py` | `/v1/account` | Account settings, usage tracking |
| `billing.py` | `/v1/billing` | Stripe checkout, webhooks |
| `admin.py` | `/v1/admin` | Admin console endpoints |
| `consumer_report.py` | `/v1/r` | Public mobile report viewer |
| `cma.py` | `/v1/cma` | Agent landing pages |

#### Services (`services/`)

| File | Purpose |
|------|---------|
| `sitex.py` | SiteX Pro API client (property data) |
| `email.py` | Resend email sending |
| `twilio_sms.py` | Twilio SMS sending |
| `stripe_service.py` | Stripe billing operations |

#### Schemas (`schemas/`)

| File | Models |
|------|--------|
| `property.py` | `ComparableProperty`, `PropertyStats`, `ReportStats`, `normalize_comparable()` |
| `report.py` | `ReportCreate`, `ReportResponse`, `ReportFilters` |
| `schedule.py` | `ScheduleCreate`, `ScheduleResponse`, `RecipientTyped` |
| `auth.py` | `LoginRequest`, `TokenResponse`, `UserCreate` |

#### Middleware (`middleware/`)

| Middleware | Purpose |
|------------|---------|
| `AuthContextMiddleware` | Extracts user/account from JWT or API key |
| `RLSContextMiddleware` | Sets PostgreSQL `app.current_account_id` for RLS |
| `RateLimitMiddleware` | Token-bucket rate limiting per API key |
| `CORSMiddleware` | Cross-origin request handling |

### Key API Patterns

```python
# Dependency injection for current user
@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return current_user

# Async database sessions
async with get_db() as db:
    result = await db.execute(select(Report).where(...))

# Background task enqueueing
from worker.tasks import generate_report
generate_report.delay(run_id, account_id, report_type, params)
```

---

## 3. Worker Service (Celery)

### Location: `apps/worker/src/worker/`

### Core Files

| File | Purpose |
|------|---------|
| `tasks.py` | Main Celery task definitions |
| `property_builder.py` | `PropertyReportBuilder` class for HTML generation |
| `pdf_engine.py` | PDF rendering (Playwright or PDFShift) |
| `celery_app.py` | Celery application configuration |

### Celery Tasks

#### `generate_report` (Main Report Generation)
```python
@celery.task(name="generate_report", bind=True, max_retries=3)
def generate_report(self, run_id: str, account_id: str, report_type: str, params: dict):
    """
    Main report generation pipeline:
    1. Fetch data from SimplyRETS/SiteX APIs
    2. Extract and validate data
    3. Compute market metrics
    4. Build report JSON
    5. Render PDF (Playwright or PDFShift)
    6. Upload to R2/S3
    7. Update database with URLs
    """
```

#### `process_consumer_report` (Mobile CMA)
```python
@celery.task(name="process_consumer_report", bind=True, max_retries=3)
def process_consumer_report(self, report_id: str):
    """
    Consumer report (mobile CMA) processing:
    1. Look up property via SiteX
    2. Fetch comparable sales (SimplyRETS)
    3. Calculate value estimate
    4. Send SMS notifications to consumer & agent
    5. Store report data for mobile viewer
    """
```

#### Supporting Tasks
- `ping` - Health check
- `schedules_tick` - Cron-like schedule execution
- `send_email` - Email delivery via Resend
- `send_sms` - SMS delivery via Twilio

### PropertyReportBuilder

```python
# Location: apps/worker/src/worker/property_builder.py

class PropertyReportBuilder:
    """
    Builds HTML property reports using Jinja2 templates.

    Usage:
        builder = PropertyReportBuilder(report_data)
        html = builder.render_html()

    Themes:
        1 = classic (Navy + Sky Blue)
        2 = modern (Coral + Midnight)
        3 = elegant (Burgundy + Gold)
        4 = teal (Teal + Navy) [DEFAULT]
        5 = bold (Navy + Gold)
    """

    def __init__(self, report_data: Dict[str, Any]):
        # Resolve theme (number or name)
        # Set up Jinja2 environment
        # Register custom filters

    def render_html(self) -> str:
        # Build context (property, agent, comparables, stats, images)
        # Select theme template
        # Render and return HTML
```

### Custom Jinja2 Filters

| Filter | Example | Output |
|--------|---------|--------|
| `format_currency` | `{{ 650000 \| format_currency }}` | `$650,000` |
| `format_currency_short` | `{{ 1200000 \| format_currency_short }}` | `$1.2M` |
| `format_number` | `{{ 2500 \| format_number }}` | `2,500` |
| `truncate` | `{{ "Long text" \| truncate(5) }}` | `Lo...` |

---

## 4. Frontend (Next.js)

### Location: `apps/web/`

### Tech Stack
- **Framework**: Next.js 16 with App Router
- **React**: 19.x
- **Styling**: Tailwind CSS
- **State**: React Query / SWR
- **Maps**: @react-google-maps/api

### Key Pages

| Route | Purpose |
|-------|---------|
| `/dashboard` | Main user dashboard |
| `/reports` | Report list and management |
| `/reports/new` | Create new market report |
| `/property-reports` | Property report (CMA) list |
| `/property-reports/new` | Property report wizard |
| `/schedules` | Scheduled reports management |
| `/leads` | Lead management |
| `/contacts` | Contact management |
| `/settings` | Account settings |
| `/admin/*` | Admin console (metrics, accounts, users) |
| `/print/[id]` | Print-optimized report view (for PDF generation) |

### API Client Pattern

```typescript
// apps/web/src/lib/api.ts
const api = {
  reports: {
    list: () => fetch('/api/v1/reports'),
    get: (id: string) => fetch(`/api/v1/reports/${id}`),
    create: (data: ReportCreate) => fetch('/api/v1/reports', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  },
  // ... other resources
};
```

---

## 5. Database Schema

### Core Tables

#### Multi-Tenant Foundation

```sql
-- accounts: Top-level tenant container
accounts (
    id UUID PRIMARY KEY,
    name TEXT,
    slug TEXT UNIQUE,
    status TEXT DEFAULT 'active',
    account_type TEXT DEFAULT 'REGULAR',  -- REGULAR | INDUSTRY_AFFILIATE
    subscription_status TEXT,
    plan_id TEXT REFERENCES plans(slug),
    sponsor_account_id UUID REFERENCES accounts(id),  -- For affiliate relationships
    monthly_report_limit INTEGER,
    sms_credits INTEGER DEFAULT 0,
    branding JSONB,  -- {logo_url, primary_color, ...}
    created_at, updated_at
)

-- users: Individual user accounts
users (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    role TEXT DEFAULT 'user',  -- user | admin
    email_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    agent_code TEXT UNIQUE,  -- For landing pages
    photo_url TEXT,
    license_number TEXT,
    landing_page_headline TEXT,
    landing_page_theme_color TEXT,
    created_at, updated_at
)

-- account_users: Many-to-many with roles
account_users (
    account_id UUID,
    user_id UUID,
    role TEXT,  -- OWNER | MEMBER | AFFILIATE | ADMIN
    PRIMARY KEY (account_id, user_id)
)
```

#### Report Generation

```sql
-- report_generations: Market report jobs
report_generations (
    id UUID PRIMARY KEY,
    account_id UUID,
    user_id UUID,
    report_type TEXT,  -- sold | active | pending | etc.
    input_params JSONB,  -- {city, zips, polygon, filters, ...}
    status TEXT DEFAULT 'pending',  -- pending | processing | completed | failed
    html_url TEXT,
    json_url TEXT,
    csv_url TEXT,
    pdf_url TEXT,
    processing_time_ms INTEGER,
    error_message TEXT,
    billable BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    created_at, updated_at
)

-- property_reports: Property CMA reports
property_reports (
    id UUID PRIMARY KEY,
    account_id UUID,
    user_id UUID,
    report_type TEXT,  -- seller | buyer
    theme INTEGER DEFAULT 4,  -- 1-5
    property_address TEXT,
    property_city TEXT,
    property_state TEXT,
    property_zip TEXT,
    sitex_data JSONB,  -- Full property details from SiteX
    comparables JSONB,  -- Array of comparable properties
    pdf_url TEXT,
    status TEXT DEFAULT 'pending',
    short_code TEXT UNIQUE,  -- For QR codes
    qr_code_url TEXT,
    view_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at, updated_at
)

-- consumer_reports: Mobile-first CMA reports
consumer_reports (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES users(id),
    agent_code TEXT,
    consumer_phone TEXT,
    consumer_email TEXT,
    property_address TEXT,
    property_data JSONB,  -- SiteX response
    comparables JSONB,
    market_stats JSONB,
    value_estimate JSONB,
    status TEXT,  -- pending | ready | failed
    pdf_url TEXT,
    view_count INTEGER DEFAULT 0,
    device_type TEXT,
    created_at, updated_at
)
```

#### Scheduling

```sql
-- schedules: Scheduled report configuration
schedules (
    id UUID PRIMARY KEY,
    account_id UUID,
    name TEXT,
    report_type TEXT,
    city TEXT,
    zip_codes TEXT[],
    lookback_days INTEGER DEFAULT 7,
    cadence TEXT,  -- weekly | monthly
    weekly_dow INTEGER,  -- 0-6 (Sunday-Saturday)
    monthly_dom INTEGER,  -- 1-28
    send_hour INTEGER,
    send_minute INTEGER,
    timezone TEXT,  -- IANA timezone
    recipients JSONB,  -- Array of typed recipients
    filters JSONB,  -- {price_strategy, min_price, max_price, ...}
    include_attachment BOOLEAN DEFAULT true,
    active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    failure_count INTEGER DEFAULT 0,
    created_at, updated_at
)
```

#### Lead Management

```sql
-- leads: Captured leads
leads (
    id UUID PRIMARY KEY,
    account_id UUID,
    property_report_id UUID,
    name TEXT,
    email TEXT,
    phone TEXT,
    source TEXT,  -- qr_scan | direct_link
    status TEXT DEFAULT 'new',  -- new | contacted | converted
    message TEXT,
    consent_given BOOLEAN DEFAULT false,
    created_at, updated_at
)

-- contacts: Contact database
contacts (
    id UUID PRIMARY KEY,
    account_id UUID,
    name TEXT,
    email TEXT,
    phone TEXT,
    type TEXT,  -- client | list | agent | group
    notes TEXT,
    created_at, updated_at
)
```

#### Billing

```sql
-- plans: Subscription plans
plans (
    slug TEXT PRIMARY KEY,  -- free | pro | team | affiliate
    name TEXT,
    monthly_report_limit INTEGER,
    allow_overage BOOLEAN DEFAULT false,
    overage_price_cents INTEGER,
    stripe_price_id TEXT
)

-- usage_tracking: Usage events
usage_tracking (
    id UUID PRIMARY KEY,
    account_id UUID,
    user_id UUID,
    event_type TEXT,  -- report_generated | api_call | etc.
    report_id UUID,
    billable_units INTEGER DEFAULT 1,
    cost_cents INTEGER,
    created_at
)
```

### Row-Level Security (RLS)

```sql
-- Enable RLS on tenant-scoped tables
ALTER TABLE report_generations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their account's data
CREATE POLICY tenant_isolation ON report_generations
    USING (account_id = current_setting('app.current_account_id')::uuid);

-- Set context in API middleware
SET app.current_account_id = '<account-uuid>';
```

---

## 6. PDF Generation System

### Location: `apps/worker/src/worker/pdf_engine.py`

### Dual-Engine Architecture

The system supports two PDF rendering backends:

| Engine | Use Case | Margins | Configuration |
|--------|----------|---------|---------------|
| **Playwright** | Local development | 0.5in all sides (API) | `PDF_ENGINE=playwright` |
| **PDFShift** | Production | 0 (CSS handles) | `PDF_ENGINE=pdfshift` |

### Playwright (Local)

```python
def render_pdf_playwright(run_id, account_id, html_content=None, print_base=None):
    """
    Render PDF using local Chromium via Playwright.

    Settings:
    - format: Letter (8.5" x 11")
    - print_background: True (include colors/images)
    - margin: 0.5in all sides
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        if html_content:
            page.set_content(html_content)
        else:
            page.goto(print_url, wait_until="networkidle")

        page.pdf(
            path=pdf_path,
            format="Letter",
            print_background=True,
            margin={"top": "0.5in", "right": "0.5in",
                    "bottom": "0.5in", "left": "0.5in"}
        )
```

### PDFShift (Production)

```python
def render_pdf_pdfshift(run_id, account_id, html_content=None, print_base=None):
    """
    Render PDF using PDFShift cloud API.

    CRITICAL: Margins set to 0 - CSS templates handle all margins.
    Templates use @page { margin: 0 } and internal padding.
    """
    payload = {
        "source": html_content or print_url,
        "format": "Letter",
        "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
        "use_print": True,  # Use @media print styles
        "remove_blank": True,  # Remove blank trailing pages
        "delay": 5000,  # Wait for images to load
        "wait_for_network": True,
        "lazy_load_images": True,
        "timeout": 100,
    }

    response = httpx.post(PDFSHIFT_API_URL, json=payload, headers={
        "X-API-Key": PDFSHIFT_API_KEY,
        "X-Processor-Version": "142"  # Latest engine
    })
```

### Environment Variables

```bash
PDF_ENGINE=playwright|pdfshift  # Which engine to use
PDFSHIFT_API_KEY=xxx            # PDFShift API key
PDFSHIFT_API_URL=https://api.pdfshift.io/v3/convert/pdf
PDF_DIR=/tmp/mr_reports         # Local PDF output directory
PRINT_BASE=http://localhost:3000  # Base URL for print pages
```

---

## 7. Property Report Templates

### Location: `apps/worker/src/worker/templates/property/`

### Theme Overview

| Theme | ID | Primary Font | Body Font | Primary Color | Accent Color |
|-------|-----|--------------|-----------|---------------|--------------|
| **Classic** | 1 | Merriweather | Source Sans Pro | Navy (#1B365D) | Sky (#4A90A4) |
| **Modern** | 2 | Space Grotesk | DM Sans | Coral (#FF6B5B) | Midnight (#1A1F36) |
| **Elegant** | 3 | Playfair Display | Montserrat | Burgundy (#1a1a1a) | Gold (#C9A962) |
| **Teal** | 4 | Montserrat | Montserrat | Teal (#34d1c3) | Navy (#18235c) |
| **Bold** | 5 | Oswald | Montserrat | Navy (#15216E) | Gold (#D69649) |

### Template Structure (All Themes)

Each theme template is self-contained with 7 pages:

```
1. Cover Page      - Title, address, agent info, branding
2. Contents Page   - Table of contents
3. Aerial Page     - Map/satellite view of property
4. Property Page   - Property details, owner info, tax data
5. Analysis Page   - Area sales analysis, comparison table
6. Comparables     - 4 comparable property cards
7. Range Page      - Price range slider, summary stats
```

### Template Data Contract

```python
# Context passed to all templates
{
    "theme_color": "#34d1c3",  # Custom primary color override

    "property": {
        "street_address": "123 Main St",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90210",
        "full_address": "123 Main St, Los Angeles, CA 90210",
        "owner_name": "John Doe",
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2200,
        "lot_size": 7500,
        "year_built": 1985,
        "assessed_value": 650000,
        "tax_amount": 8500,
        # ... more fields
    },

    "agent": {
        "name": "Jane Agent",
        "title": "Realtor",
        "license": "CA BRE#01234567",
        "phone": "(555) 123-4567",
        "email": "jane@example.com",
        "company_name": "Acme Realty",
        "photo_url": "https://...",
        "logo_url": "https://...",
    },

    "comparables": [
        {
            "address": "456 Oak Ave",
            "sale_price": 725000,
            "sold_date": "01/15/2024",
            "sqft": 2100,
            "bedrooms": 4,
            "bathrooms": 2,
            "price_per_sqft": 345,
            "map_image_url": "https://...",
        },
        # ... up to 6 comparables
    ],

    "stats": {
        "total_comps": 4,
        "avg_sqft": 2050,
        "avg_beds": 3.5,
        "avg_baths": 2.25,
        "price_low": 650000,
        "price_high": 800000,
        "piq": { /* subject property stats */ },
        "low": { /* lowest comp stats */ },
        "medium": { /* median comp stats */ },
        "high": { /* highest comp stats */ },
    },

    "images": {
        "hero": "https://...",  # Cover background
        "aerial_map": "https://maps.googleapis.com/...",
    },
}
```

### CSS Variables (Per Theme)

```css
/* Common across all themes */
:root {
    --page-w: 8.5in;
    --page-h: 11in;
    --pad: 0.5in - 0.6in;  /* Varies by theme */
}

/* Print rules (all themes) */
@page { size: Letter; margin: 0; }
@media print {
    body { background: #fff; }
    .page {
        page-break-after: always;
        page-break-inside: avoid;
    }
}
```

### Known Inconsistencies

| Issue | Impact | Themes Affected |
|-------|--------|-----------------|
| `--pad` varies (0.5-0.6in) | Content positioning differs | All |
| Footer bottom (0.3in vs 0.4in) | Footer position varies | Teal vs others |
| Playwright margins (0.5in) vs PDFShift (0) | Different output between engines | All |

---

## 8. External Integrations

### SimplyRETS (Real Estate Listings)

```python
# Location: apps/worker/src/worker/vendors/simplyrets.py

# Configuration
SIMPLYRETS_BASE_URL = "https://api.simplyrets.com"
SIMPLYRETS_USERNAME = os.getenv("SIMPLYRETS_USERNAME")
SIMPLYRETS_PASSWORD = os.getenv("SIMPLYRETS_PASSWORD")
SIMPLYRETS_RPM = 60  # Rate limit: 60 requests/minute
SIMPLYRETS_BURST = 10  # Burst allowance

# Usage
async def fetch_properties(city, zip_codes, filters):
    """
    Fetch listings from SimplyRETS.
    - Rate limited with token-bucket algorithm
    - Exponential backoff on 429 responses
    - Max 1000 results per query
    """
```

### SiteX Pro (Property Data)

```python
# Location: apps/api/src/api/services/sitex.py

# Configuration
SITEX_BASE_URL = os.getenv("SITEX_BASE_URL")  # UAT or Prod
SITEX_CLIENT_ID = os.getenv("SITEX_CLIENT_ID")
SITEX_CLIENT_SECRET = os.getenv("SITEX_CLIENT_SECRET")
SITEX_FEED_ID = "100001"

# Token management
# - OAuth2 client credentials flow
# - 10-minute TTL, auto-refresh at 9 minutes

# Functions
async def lookup_property(address: str) -> PropertyData:
    """Search property by address."""

async def lookup_property_by_apn(apn: str, fips: str) -> PropertyData:
    """Search property by APN and FIPS code."""
```

### Stripe (Billing)

```python
# Location: apps/api/src/api/routes/billing.py

# Endpoints
POST /v1/billing/checkout       # Create Stripe checkout session
GET  /v1/billing/customer-portal  # Get portal URL
POST /v1/billing/webhook        # Handle Stripe events

# Webhook Events Handled
- checkout.session.completed    # Subscription created
- customer.subscription.updated # Plan changed
- customer.subscription.deleted # Cancelled
- invoice.paid                  # Payment successful
- invoice.payment_failed        # Payment failed
```

### Resend (Email)

```python
# Location: apps/api/src/api/services/email.py

# Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM_ADDRESS = "Market Reports <noreply@marketreports.com>"

# Functions
async def send_email(to, subject, html_body, reply_to=None):
    """Send transactional email via Resend."""
```

### Twilio (SMS)

```python
# Location: apps/worker/src/worker/sms/send.py

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Functions
async def send_sms(to, message):
    """Send SMS via Twilio. Tracks delivery status and costs."""
```

### Cloudflare R2 / AWS S3 (File Storage)

```python
# Location: apps/worker/src/worker/tasks.py

# Configuration
S3_ENDPOINT = os.getenv("S3_ENDPOINT")  # R2 or S3 endpoint
S3_BUCKET = os.getenv("S3_BUCKET", "market-reports")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

# Functions
def upload_to_r2(local_path, s3_key):
    """Upload file to R2/S3 and return public URL."""
```

### Google Maps (Static Maps)

```python
# Location: apps/worker/src/worker/property_builder.py

# Configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Usage in templates
aerial_map_url = (
    f"https://maps.googleapis.com/maps/api/staticmap"
    f"?center={lat},{lng}"
    f"&zoom=15&size=800x600&maptype=roadmap"
    f"&markers=color:0x1e3a5f%7C{lat},{lng}"
    f"&key={GOOGLE_MAPS_API_KEY}"
)
```

---

## 9. Authentication & Authorization

### Authentication Methods

#### 1. JWT Bearer Tokens (Primary)

```python
# Token generation
payload = {
    "account_id": str(account.id),
    "user_id": str(user.id),
    "role": user.role,
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(seconds=JWT_TTL)
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# Token validation (in middleware)
decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
```

#### 2. API Keys (Machine-to-Machine)

```python
# Format: mr_live_ + base64(32 random bytes)
# Storage: SHA256 hash only (never store plaintext)

# Validation
key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
api_key = await db.execute(
    select(ApiKey).where(ApiKey.key_hash == key_hash)
)
```

### Authorization (Role-Based + RLS)

```python
# Roles
OWNER    # Full account access
MEMBER   # Standard user access
AFFILIATE # Affiliate agent access
ADMIN    # System administrator (bypasses RLS)

# Row-Level Security
# Set in middleware for every request:
await db.execute(text(f"SET app.current_account_id = '{account_id}'"))

# RLS policies automatically filter queries:
SELECT * FROM reports;  # Only returns rows where account_id matches
```

### Public Endpoints (No Auth Required)

```python
PUBLIC_PATHS = [
    "/health",
    "/docs", "/redoc", "/openapi.json",
    "/v1/auth/*",
    "/v1/leads/capture",
    "/v1/property/public/*",
    "/v1/r/*",
    "/v1/cma/*",
    "/v1/webhooks/stripe",
]
```

---

## 10. Environment Configuration

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/market_reports

# Redis
REDIS_URL=redis://localhost:6379/0

# API Server
PORT=10000
JWT_SECRET=<strong-random-secret>
ALLOWED_ORIGINS=["http://localhost:3000"]

# Frontend URLs
NEXT_PUBLIC_API_BASE=http://localhost:10000
APP_BASE=http://localhost:3000
PRINT_BASE=http://localhost:3000

# External Services
SIMPLYRETS_USERNAME=xxx
SIMPLYRETS_PASSWORD=xxx
SITEX_BASE_URL=https://api.uat.bkitest.com
SITEX_CLIENT_ID=xxx
SITEX_CLIENT_SECRET=xxx

# PDF Generation
PDF_ENGINE=playwright
PDFSHIFT_API_KEY=xxx

# Storage
S3_ENDPOINT=https://xxx.r2.cloudflarestorage.com
S3_BUCKET=market-reports
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx

# Communications
RESEND_API_KEY=re_xxx
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1xxx

# Billing
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

### Docker Compose Services

```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: market_reports
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

---

## 11. Key Workflows

### Property Report Generation

```
1. User fills out wizard in frontend
   └─ Selects property, comparables, theme

2. Frontend POSTs to /v1/property/reports
   └─ Creates DB record (status=pending)
   └─ Enqueues Celery task

3. Celery worker picks up task
   ├─ Fetches property data (SiteX)
   ├─ Fetches comparables (SimplyRETS)
   ├─ Builds HTML (PropertyReportBuilder)
   ├─ Renders PDF (Playwright/PDFShift)
   ├─ Uploads to R2/S3
   └─ Updates DB (status=completed, pdf_url)

4. Frontend polls for completion
   └─ Displays PDF download link
```

### Scheduled Report Execution

```
1. schedules_tick runs every minute
   └─ Checks for due schedules (based on timezone)

2. For each due schedule:
   ├─ Resolves recipients (contacts, groups, emails)
   ├─ Fetches data (SimplyRETS)
   ├─ Generates report (JSON, PDF)
   ├─ Sends emails with attachments (Resend)
   └─ Updates last_run_at

3. On failure:
   └─ Increments failure_count
   └─ Stores last_failure_reason
```

### Lead Capture

```
1. Consumer scans QR code on property report
   └─ Lands on /v1/property/public/{short_code}

2. Consumer fills out lead form
   └─ POSTs to /v1/leads/capture (public endpoint)

3. System:
   ├─ Creates lead record
   ├─ Sends email to agent
   ├─ Sends SMS to agent (if configured)
   └─ Tracks source (qr_scan | direct_link)
```

---

## 12. Common Patterns & Conventions

### Error Handling

```python
# API errors use HTTPException
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Report not found")
raise HTTPException(status_code=403, detail="Insufficient permissions")
raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### Database Transactions

```python
# Use async context manager
async with get_db() as db:
    report = Report(...)
    db.add(report)
    await db.commit()
    await db.refresh(report)
```

### Celery Task Patterns

```python
# Always use bind=True for self reference
@celery.task(bind=True, max_retries=3)
def my_task(self, arg):
    try:
        # ... work
    except Exception as e:
        self.retry(exc=e, countdown=60)  # Retry in 60s
```

### Jinja2 Template Patterns

```jinja2
{# Safe defaults #}
{{ property.pool | default('None') }}

{# Conditional rendering #}
{% if agent.photo_url %}
<img src="{{ agent.photo_url }}" />
{% endif %}

{# Loops with limits #}
{% for comp in comparables[:4] %}
...
{% endfor %}

{# Custom filters #}
{{ comp.sale_price | format_currency }}
```

### API Response Patterns

```python
# List with pagination
@router.get("/items")
async def list_items(skip: int = 0, limit: int = 20):
    return {"items": items, "total": total, "skip": skip, "limit": limit}

# Single item
@router.get("/items/{id}")
async def get_item(id: str):
    if not item:
        raise HTTPException(404, "Not found")
    return item

# Create with 201/202
@router.post("/items", status_code=201)  # Sync creation
@router.post("/items", status_code=202)  # Async (background job)
```

---

## Quick Reference

### File Locations

| Component | Path |
|-----------|------|
| API routes | `apps/api/src/api/routes/` |
| API services | `apps/api/src/api/services/` |
| Celery tasks | `apps/worker/src/worker/tasks.py` |
| PDF engine | `apps/worker/src/worker/pdf_engine.py` |
| Report builder | `apps/worker/src/worker/property_builder.py` |
| Templates | `apps/worker/src/worker/templates/property/` |
| Frontend pages | `apps/web/src/app/` |

### Theme Quick Reference

| Theme | ID | Template Path |
|-------|-----|---------------|
| Classic | 1 | `property/classic/classic_report.jinja2` |
| Modern | 2 | `property/modern/modern_report.jinja2` |
| Elegant | 3 | `property/elegant/elegant_report.jinja2` |
| Teal | 4 | `property/teal/teal_report.jinja2` |
| Bold | 5 | `property/bold/bold_report.jinja2` |

### Common Commands

```bash
# Start all services
docker-compose up -d

# Run API locally
cd apps/api && uvicorn src.api.main:app --reload --port 10000

# Run worker locally
cd apps/worker && celery -A src.worker.celery_app worker --loglevel=info

# Run frontend locally
cd apps/web && npm run dev
```

---

*Last updated: 2024*