# TrendyReports Email System

> Complete technical documentation for the email infrastructure, templates, and delivery pipeline.

**Last Updated:** January 5, 2026 (V10 Professional Redesign)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Unified Template Architecture](#2-unified-template-architecture)
3. [Email Data Model](#3-email-data-model)
4. [Provider Integration (SendGrid)](#4-provider-integration-sendgrid)
5. [Scheduled Report Emails](#5-scheduled-report-emails)
6. [Branding Test Emails](#6-branding-test-emails)
7. [Email Templates](#7-email-templates)
8. [White-Label Branding](#8-white-label-branding)
9. [Unsubscribe & Suppression](#9-unsubscribe--suppression)
10. [Environment Variables](#10-environment-variables)
11. [Email Flow Diagrams](#11-email-flow-diagrams)
12. [Troubleshooting](#12-troubleshooting)
13. [Database Schema Changes](#13-database-schema-changes)
14. [Future Enhancements](#14-future-enhancements)

---

## 1. Architecture Overview

TrendyReports sends emails through two distinct pathways:

### Email Pathways

| Pathway | Trigger | Service | Purpose |
|---------|---------|---------|---------|
| **Scheduled Reports** | Ticker finds due schedule | Worker (Celery) | Automated market report delivery |
| **Branding Test** | User clicks "Send Test Email" | API (FastAPI) | Preview branding in inbox |

### Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        Email System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Ticker     │────▶│    Worker    │────▶│   SendGrid   │     │
│  │ (schedules)  │     │   (Celery)   │     │    (API)     │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                              │                    │              │
│                              ▼                    ▼              │
│                       ┌──────────────┐     ┌──────────────┐     │
│                       │  email_log   │     │   Recipient  │     │
│                       │   (Postgres) │     │    Inbox     │     │
│                       └──────────────┘     └──────────────┘     │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │  Branding    │────▶│     API      │────▶│   SendGrid   │     │
│  │    Page      │     │   (FastAPI)  │     │    (API)     │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| SendGrid Provider | `apps/worker/src/worker/email/providers/sendgrid.py` | Low-level email sending |
| **Email Template (V5)** | `apps/worker/src/worker/email/template.py` | **Unified** HTML generation for ALL emails (includes photo galleries) |
| Email Orchestrator | `apps/worker/src/worker/email/send.py` | Suppression filtering, template rendering, listings passthrough |
| Branding Test | `apps/api/src/api/routes/branding_tools.py` | Test email endpoint (uses unified template with sample listings) |
| Unsubscribe API | `apps/api/src/api/routes/unsubscribe.py` | Handle unsubscribe requests |

> 📦 **V6 Architecture:** A single template file (`template.py`) serves both scheduled reports and test emails. The unified template is the **single source of truth** for all email styling.

---

## 2. Unified Template Architecture

### 2.1 The Problem (Pre-V6)

Previously, test emails and production emails could diverge:
- **Production:** Worker used `apps/worker/src/worker/email/template.py`
- **Test emails:** API tried to import from worker path, with a fallback inline template

This caused styling inconsistencies when:
1. The API couldn't access the worker's template path (separate deployments)
2. The fallback template was outdated

### 2.2 The Solution (V6)

**Single Source of Truth:** `libs/shared/src/shared/email/template.py`

```
┌─────────────────────────────────────────────────────────────────┐
│                   Unified Email Template                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   libs/shared/src/shared/email/template.py                      │
│   ▲                                                             │
│   │ (copied during development)                                 │
│   │                                                             │
│   ├──────────────────────────────────────────────────┐          │
│   │                                                  │          │
│   ▼                                                  ▼          │
│   apps/worker/src/worker/email/template.py    [API imports]     │
│   (Worker uses directly)                       (via fallback)   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Import Strategy (API)

The API uses a multi-fallback import strategy:

```python
# branding_tools.py - Import Strategy

# Option 1: Try shared package (ideal for local dev)
try:
    from shared.email import schedule_email_html
    UNIFIED_TEMPLATE_AVAILABLE = True
except ImportError:
    pass

# Option 2: Try worker path (works when repo deployed together)
if not UNIFIED_TEMPLATE_AVAILABLE:
    try:
        worker_template_path = "../../../../worker/src/worker/email/template.py"
        # Dynamic import...
    except Exception:
        pass

# Option 3: Use fallback template (last resort)
if not UNIFIED_TEMPLATE_AVAILABLE:
    # _build_fallback_test_email() - simplified but styled correctly
```

### 2.4 Keeping Templates in Sync

When updating email templates:

1. **Edit the source of truth:** `libs/shared/src/shared/email/template.py`
2. **Copy to worker:** `apps/worker/src/worker/email/template.py`
3. **Update fallback:** Update `_build_fallback_test_email()` in `branding_tools.py` if needed

**Sync command:**
```bash
cp libs/shared/src/shared/email/template.py apps/worker/src/worker/email/template.py
```

### 2.5 Template Version History

| Version | Date | Changes |
|---------|------|---------|
| V3 | Dec 2024 | Professional styling, VML fallback for Outlook |
| V3.1 | Dec 2024 | Monochromatic color scheme, unified metrics colors |
| V4 | Dec 2025 | PDF-aligned layout, 4-metric hero row, insight paragraph |
| V4.2 | Dec 2025 | All major report types aligned with PDF structure |
| V5 | Dec 2025 | Photo gallery grids for gallery reports, listings tables |
| V6 | Dec 2025 | Unified template architecture, warm stone palette, font-weight 900 |
| V6.1 | Dec 2025 | Gallery reports - consistent headers, inverted section divs |
| V8 | Jan 2026 | Adaptive gallery layouts (3-col, 2-col, vertical list based on count) |
| V10 | Jan 2026 | Corporate/Professional redesign - removed emojis, casual callouts; neutral colors (#1c1917) for all data values; clean bordered metric rows; single CTA button |
| **V11** | Jan 2026 | **Filter Description Blurb** - styled box after hero showing report criteria (e.g., "2+ beds, Condos, under $1.2M"); **Closed Sales Optimization** - listings table moved higher to avoid Gmail clipping |

### 2.6 V11 Filter Description & Closed Sales Optimization (Current)

**January 6, 2026 Update**

V11 introduces two key UX enhancements:

#### A. Filter Description Blurb

For preset reports (First-Time Buyer, Luxury, Condo Watch, etc.), a styled blurb now appears **immediately after the hero section** explaining the applied filters:

```
┌─────────────────────────────────────────────────────────────┐
│  Report Criteria: 2+ beds, 2+ baths, SFR, under $1,680,000  │
│                   (70% of Irvine median)                     │
└─────────────────────────────────────────────────────────────┘
```

**Styling:**
- Light gradient background (primary_color at 8% opacity)
- Left border accent (3px solid primary_color)
- "Report Criteria:" label in bold primary color
- Filter details in neutral text

**Implementation:**
- New `filter_description` parameter in `schedule_email_html()`
- Generated from `build_filters_label()` in `filter_resolver.py`
- Passed through result → email payload → template

#### B. Closed Sales Table Priority

Previously, the Closed Sales email showed: Hero → Core Indicators → Property Types → Price Tiers → **Listings Table**

This caused Gmail to clip the email (~102KB limit), requiring users to click "View entire message" 3 times to see the listings.

**V11 Fix:** For closed sales, the listings table now appears **immediately after the hero metrics**:

```
Hero Metrics → Listings Table (top 10) → Quick Take → CTA
```

Property Types and Price Tiers are skipped for Closed Sales since the **listings table is the primary content**.

### 2.7 V10 Professional Styling

**Design Philosophy:** Corporate and professional aesthetic that showcases maturity and credibility.

**Key Changes from V9:**

| Element | V9 (Casual) | V10 (Professional) |
|---------|-------------|-------------------|
| Quick Take | Yellow box with emojis (🔥, 📊) | Subtle italic insight line |
| Conversation Starter | Green callout box | **Removed** |
| Headline metric | 56px, brand colored | 48px, neutral dark (#1c1917) |
| Key Stats Bar | Gradient with white text | Light gray bg (#fafaf9), bordered cells |
| Data values | Brand primary color | Neutral dark (#1c1917) |
| Font weights | 900 (extra bold) | 700 (bold) |
| CTA Buttons | Dual buttons with emojis | Single "View Full Report" button |
| Preheaders | Emoji prefixes | Clean text only |

**Color Usage (V10):**

| Element | Color |
|---------|-------|
| Header gradient | `primary_color` → `accent_color` (unchanged) |
| All data values | Neutral dark `#1c1917` |
| Labels | Stone gray `#78716c` |
| Card backgrounds | `#fafaf9` (light gray) |
| Borders | `#e7e5e4` (stone-200) |
| CTA button | `primary_color` (brand) |

### 2.7 V6 Styling Updates (Legacy)

**Color Scheme (Mature Stone Palette):**

| Element | Color | CSS Variable |
|---------|-------|--------------|
| Body background | `#f5f5f4` | stone-100 |
| Card background | `#fafaf9` / `#ffffff` | stone-50 / white |
| Borders | `#e7e5e4` | stone-200 |
| Secondary text | `#78716c` | stone-500 |
| Body text | `#44403c` | stone-700 |
| Dark text | `#1c1917` | stone-900 |

**Typography:**
- Metric values: `font-weight: 900` (black)
- Insight text: `font-weight: 400` (no italic)
- Labels: `font-weight: 600`

**Header Design (V6):**
- Beautiful gradient from `primary_color` to `accent_color` (135°)
- White logo on gradient background (`email_logo_url`)

```
┌────────────────────────────────────────┐
│   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │ ← Gradient (primary → accent)
│           BRAND NAME                   │
│           Report Type                  │
└────────────────────────────────────────┘
```

### 2.7 V6.1 Gallery Reports Styling

**Header Consistency:**
- Gallery report headers now show the report label, not a tagline
- `New Listings Gallery` (not "The Newest Properties")
- `Featured Listings` (not "Premium Properties")

**Section Div Styling (Inverted):**

Both gallery reports (`new_listings_gallery`, `featured_listings`) now use inverted section header styling:

| Element | Before (V5) | After (V6.1) |
|---------|-------------|--------------|
| Background | Orange gradient | White (`#ffffff`) |
| Border | None | 2px solid `accent_color` |
| Text color | White | `accent_color` |
| Count color | White | `accent_color` |

**Visual:**
```
BEFORE (V5):                      AFTER (V6.1):
┌────────────────────────┐        ┌────────────────────────┐
│ ▓▓▓▓ 9 NEW LISTINGS ▓▓▓│        │   9 NEW LISTINGS      │
│ (orange bg, white text)│        │ (white bg, orange     │
└────────────────────────┘        │  border & text)       │
                                  └────────────────────────┘
```

This creates a cleaner, more elegant look that complements the header gradient without competing with it.

---

## 3. Email Data Model

All email-related tables are RLS-protected by `account_id`.

### 2.1 `email_log`

Records every email send attempt for audit and debugging.

```sql
CREATE TABLE email_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    schedule_id UUID REFERENCES schedules(id),
    report_id UUID,  -- Links to report_generations.id
    provider TEXT NOT NULL,  -- 'sendgrid'
    to_emails TEXT[] NOT NULL,
    subject TEXT,
    response_code INT,  -- 202 = success, 4xx/5xx = error
    status TEXT,  -- 'sent', 'failed', 'suppressed'
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Usage:**
- Worker logs every email attempt after calling SendGrid
- Includes both successful (202) and failed sends
- Links to `schedule_id` and `report_id` for traceability

### 2.2 `email_suppressions`

Stores unsubscribed or bounced email addresses per account.

```sql
CREATE TABLE email_suppressions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    email TEXT NOT NULL,
    reason TEXT NOT NULL,  -- 'unsubscribe', 'bounce', 'complaint'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(account_id, email)
);
```

**Usage:**
- Checked before every email send
- Populated via unsubscribe endpoint or webhook events
- Per-account isolation (same email can be suppressed for one account but not another)

### 2.3 `schedules` (Email-Related Fields)

```sql
-- Key fields for email delivery
recipients TEXT[],              -- Array of email addresses
include_attachment BOOLEAN,     -- v1: always FALSE (link-only)
active BOOLEAN,                 -- Must be TRUE to send emails
next_run_at TIMESTAMPTZ,        -- When ticker should process
last_run_at TIMESTAMPTZ         -- Last successful run
```

### 2.4 `schedule_runs`

Tracks individual schedule executions:

```sql
CREATE TABLE schedule_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES schedules(id),
    report_run_id UUID,  -- Links to report_generations.id
    status TEXT NOT NULL,  -- 'queued', 'processing', 'completed', 'failed', 'failed_email'
    error TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 3. Provider Integration (SendGrid)

### 3.1 SendGrid Client

**File:** `apps/worker/src/worker/email/providers/sendgrid.py`

```python
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DEFAULT_FROM_NAME = os.getenv("DEFAULT_FROM_NAME", "Market Reports")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "reports@example.com")

def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_name: str = None,
    from_email: str = None,
) -> Tuple[int, str]:
    """
    Send an email using SendGrid v3 API.
    
    Returns:
        Tuple of (status_code, response_text)
        - 202 = Email accepted for delivery
        - 4xx/5xx = Error
    """
```

### 3.2 Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 202 | Accepted | Email queued for delivery |
| 400 | Bad Request | Check payload format |
| 401 | Unauthorized | Invalid API key |
| 403 | Forbidden | Sender not verified |
| 429 | Rate Limited | Retry with backoff |
| 500+ | Server Error | Retry later |

### 3.3 SendGrid Configuration

Required SendGrid setup:
1. **API Key**: Create in SendGrid dashboard with "Mail Send" permission
2. **Sender Verification**: Verify `reports@trendyreports.io` as sender
3. **Domain Authentication**: Configure SPF/DKIM for `trendyreports.io`

---

## 4. Scheduled Report Emails

### 4.1 Flow Overview

```
1. Ticker (every 60s)
   └─▶ Find due schedules (active=TRUE, next_run_at <= NOW())
       └─▶ Enqueue job to Redis
           └─▶ Insert schedule_runs row (status='queued')

2. Worker (Celery consumer)
   └─▶ Pick up job from queue
       └─▶ Generate report (SimplyRETS → metrics → PDF)
           └─▶ Get branding for account
               └─▶ Build email HTML
                   └─▶ Filter suppressed recipients
                       └─▶ Send via SendGrid
                           └─▶ Log to email_log
                               └─▶ Update schedule_runs (status='completed')
```

### 4.2 Code Path

**Ticker:** `apps/worker/src/worker/schedules_tick.py`
```python
# Finds due schedules and enqueues
def tick():
    with db_conn() as conn:
        due_schedules = find_due_schedules(conn)
        for schedule in due_schedules:
            enqueue_job(schedule)
            insert_schedule_run(schedule.id, status='queued')
            update_next_run_at(schedule)
```

**Worker Task:** `apps/worker/src/worker/tasks.py`
```python
@celery.task(name="generate_report")
def generate_report(run_id, account_id, report_type, params):
    # ... generate report and PDF ...
    
    schedule_id = params.get("schedule_id")
    if schedule_id:
        # This is a scheduled run - send email
        brand = get_brand_for_account(db, account_id)
        send_schedule_email(
            account_id=account_id,
            recipients=schedule.recipients,
            payload={
                "report_type": report_type,
                "city": params.get("city"),
                "metrics": result_json.get("metrics"),
                "pdf_url": pdf_url,
            },
            brand=brand,
            db_conn=conn,
        )
```

### 4.3 Email Orchestrator

**File:** `apps/worker/src/worker/email/send.py`

```python
def send_schedule_email(
    account_id: str,
    recipients: List[str],
    payload: Dict,
    account_name: Optional[str] = None,
    db_conn=None,
    brand: Optional[Dict] = None,
) -> Tuple[int, str]:
    """
    1. Filter suppressed recipients
    2. Generate unsubscribe tokens
    3. Build email HTML with branding
    4. Send via SendGrid
    5. Return status
    """
```

---

## 5. Branding Test Emails

### 5.1 Purpose

Allows affiliates to preview how their branding appears in emails before any scheduled reports are sent.

### 5.2 Endpoint

**File:** `apps/api/src/api/routes/branding_tools.py`

```
POST /v1/branding/test-email
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "report_type": "market_snapshot"
}
```

**Response (Success):**
```json
{
  "ok": true,
  "message": "Test email sent to user@example.com",
  "report_type": "market_snapshot"
}
```

### 5.3 Flow

```
1. User enters email on /app/branding
2. Frontend calls POST /api/proxy/v1/branding/test-email
3. API proxy forwards to backend
4. Backend:
   a. Verify affiliate account
   b. Get branding from affiliate_branding
   c. Import schedule_email_html from worker template (V3.1 unified)
   d. Generate HTML using same template as production
   e. Inject "[Test]" banner at top
   f. Send via SendGrid (directly, not via worker)
   g. Return success/failure
```

### 5.4 Test Email Content

The test email uses the **same template function** as production scheduled emails (V3.1 unified architecture):

- Branded header with gradient (`primary_color` → `accent_color`)
- Sample metrics (hardcoded Beverly Hills data)
- All metrics styled identically to production emails
- Branded footer with contact info
- "[Test]" prefix in subject line
- Yellow test banner at top of email body

> 💡 **V3.1 Change:** Test emails now **exactly match** production emails because they use the same `schedule_email_html()` function from `apps/worker/src/worker/email/template.py`.

---

## 6. Email Templates

### 6.1 Template Version History

| Version | Date | Changes |
|---------|------|---------|
| **V11** | Jan 6, 2026 | **Filter Description Blurb** + Closed Sales table optimization (see §2.6) |
| V10 | Jan 5, 2026 | Corporate/Professional redesign - Removed emojis, casual callouts; neutral colors for data; clean bordered metric rows |
| V8 | Jan 5, 2026 | Adaptive gallery layouts based on listing count |
| V5 | Dec 22, 2025 | Gallery Photo Grids - Email templates now include photo galleries |
| V4.2 | Dec 15, 2025 | All reports PDF-aligned - new_listings, closed, inventory, price_bands now have V4 layout |
| V4.1 | Dec 11, 2025 | Modern styling - system fonts, colored dots for property types |
| V4 | Dec 11, 2025 | PDF-aligned redesign - Market Snapshot email mirrors PDF structure |
| V3.1 | Dec 11, 2025 | Monochromatic refinement - unified colors, template consolidation |
| V3 | Dec 11, 2024 | Professional styling, Market Snapshot breakdowns |
| V2 | Nov 25, 2024 | Gradient headers, dark mode, responsive |
| V1 | Nov 2024 | Initial template |

### 6.1.0 V5 Gallery Photo Grids (Current - December 22, 2025)

**🎉 BREAKTHROUGH:** Gallery report emails now display **photo grids identical to PDF reports**.

Previously, gallery emails (`new_listings_gallery`, `featured_listings`) showed only 3 stat cards—a "teaser" design. Now they include the **actual property photos and listing details**, making emails a true preview of the PDF content.

| Report Type | Grid Layout | Content |
|-------------|-------------|---------|
| `new_listings_gallery` | **3×3 grid** (9 properties) | Photo, address, city/zip, price, beds/baths/sqft |
| `featured_listings` | **2×2 grid** (4 properties) | Photo, address, city/zip, price, beds/baths/sqft |

**V5 Email Structure for Gallery Reports:**

```
┌─────────────────────────────────────────────────────────────┐
│  Header: New Listings Gallery – Redondo Beach               │
│  Subline: Period: Last 30 days • Source: Live MLS Data      │
├─────────────────────────────────────────────────────────────┤
│  SECTION LABEL: Photo Gallery                               │
├─────────────────────────────────────────────────────────────┤
│  3-COLUMN METRICS (Count, Median Price, DOM)                │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────── PHOTO GALLERY GRID ────────────┐            │
│  │  ┌──────┐ ┌──────┐ ┌──────┐               │            │
│  │  │ 📷   │ │ 📷   │ │ 📷   │               │            │
│  │  │ Addr │ │ Addr │ │ Addr │               │            │
│  │  │$1.8M │ │$1.45M│ │$1.3M │               │            │
│  │  └──────┘ └──────┘ └──────┘               │            │
│  │  (... up to 9 properties in 3 rows ...)   │            │
│  └────────────────────────────────────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  [View Full Report →]                                       │
│  Rep Footer                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Details:**

| Component | File | Description |
|-----------|------|-------------|
| `_build_gallery_grid_html()` | `template.py` | Generates email-safe table-based photo grid |
| `_build_listings_table_html()` | `template.py` | Generates email-safe listings table (Address, Beds, Baths, Price) |
| `listings` parameter | `schedule_email_html()` | Accepts listings array from report builder |
| Email payload | `tasks.py` | Passes `result.get("listings")` for gallery reports, `result.get("listings_sample")` for inventory |
| Email orchestrator | `send.py` | Forwards `listings` to template function |
| Test email data | `branding_tools.py` | Sample listings with Unsplash photos (gallery) or address data (inventory) |

**Photo Sources:**

| Environment | Photo Source |
|-------------|--------------|
| **Production** | R2-proxied MLS photos (from `result_json.listings[].hero_photo_url`) |
| **Test emails** | Unsplash placeholder photos (beautiful house images) |

**Key Code Change:**

```python
# schedule_email_html() now accepts listings parameter
def schedule_email_html(
    ...,
    listings: Optional[List[Dict]] = None,  # NEW in V5
) -> str:

# Gallery grid is rendered for gallery reports
if report_type in ("new_listings_gallery", "featured_listings") and listings:
    gallery_html = _build_gallery_grid_html(listings, report_type, primary_color)

# Listings table is rendered for inventory
if config.get("has_listings_table", False) and listings:
    listings_table_html = _build_listings_table_html(listings, report_type, primary_color)
```

**Benefits:**
- ✅ Email recipients see the same content as the PDF
- ✅ Photos load reliably (R2-proxied in production)
- ✅ Test emails accurately preview production output
- ✅ Table-based layout ensures email client compatibility

---

### 6.1.1 Email-to-PDF Alignment Matrix (V5)

This matrix shows how each email template aligns with its corresponding PDF:

| Report Type | PDF Main Content | Email Main Content | Alignment Strategy |
|-------------|------------------|--------------------|--------------------|
| `market_snapshot` | 4 hero metrics, Core Indicators, Property Types table, Price Tiers table | ✅ 4-metric hero row, Core Indicators section, Property Types breakdown, Price Tier cards | **Full alignment** - Email mirrors PDF structure |
| `new_listings` | 4 hero metrics + full listing table | ✅ 4-metric hero row + insight paragraph | **Summary** - Table omitted, stats highlighted |
| `inventory` | 4 hero metrics + full listing table | ✅ 4-metric hero row + insight + **listings table (top 10)** | **Full (V5)** - Includes listing table |
| `closed` | 4 hero metrics + full listing table | ✅ 4-metric hero row + insight paragraph | **Summary** - Table omitted, stats highlighted |
| `price_bands` | 4 hero metrics + visual price band bars + hottest/slowest summary | ✅ 4-metric hero row + price bands rows | **Full alignment** - Price bands shown with counts |
| `open_houses` | Stats + open house schedule list | 3-metric cards (legacy V3) | **Basic** - Summary only |
| `new_listings_gallery` | 3×3 photo grid with property cards | ✅ **V6.1:** 3×3 photo grid, inverted section header | **Full alignment** - Photos match PDF |
| `featured_listings` | 2×2 photo grid with property cards | ✅ **V6.1:** 2×2 photo grid, inverted section header | **Full alignment** - Photos match PDF |

#### Alignment Philosophy

**Full Alignment Reports (V4/V5):**
- `market_snapshot`, `price_bands`, `new_listings_gallery`, `featured_listings`
- Email content mirrors PDF structure exactly
- Users see the same data in both formats

**Summary Reports (V4):**
- `new_listings`, `closed`
- Full listing tables would be impractical in email (hundreds of rows)
- Email shows key summary metrics + insight paragraph
- "View Full Report" button links to complete PDF

**Enhanced Summary Reports (V5):**
- `inventory`
- Now includes **top 10 listings table** (Address, Beds, Baths, Price)
- Provides actionable listing data directly in email

**Legacy Reports (V3):**
- `open_houses`
- Basic 3-metric layout
- Future enhancement: add open house schedule preview

#### What's Shown in Each Email Type

**Market Snapshot (V4 - Full Alignment):**
```
┌─────────────────────────────────────────────────────────────┐
│  INSIGHT: "This snapshot provides key indicators for..."    │
├─────────────────────────────────────────────────────────────┤
│  4-METRIC HERO: Median Price | Closed | DOM | MOI           │
├─────────────────────────────────────────────────────────────┤
│  CORE INDICATORS: New Listings | Pending | Sale-to-List     │
├─────────────────────────────────────────────────────────────┤
│  PROPERTY TYPES: ● 89 SFR  ● 28 Condos  ● 10 Townhomes     │
├─────────────────────────────────────────────────────────────┤
│  PRICE TIERS: [Entry 28] [Move-Up 34] [Luxury 27]          │
└─────────────────────────────────────────────────────────────┘
```

**Table Reports (V4 - Summary):**
```
┌─────────────────────────────────────────────────────────────┐
│  INSIGHT: "47 new listings have entered the market..."      │
├─────────────────────────────────────────────────────────────┤
│  4-METRIC HERO: Total | Median Price | DOM | $/SqFt         │
├─────────────────────────────────────────────────────────────┤
│  [View Full Report →]  (contains the detailed table)        │
└─────────────────────────────────────────────────────────────┘
```

**Inventory Report (V5 - With Listings Table):**
```
┌─────────────────────────────────────────────────────────────┐
│  INSIGHT: "156 active listings in Glendale..."              │
├─────────────────────────────────────────────────────────────┤
│  4-METRIC HERO: Active | New This Month | DOM | MOI         │
├─────────────────────────────────────────────────────────────┤
│  ACTIVE LISTINGS (Top 10)                                   │
│  ┌───────────────────────────┬──────┬──────┬──────────┐    │
│  │ Address                   │ Beds │ Baths│ Price    │    │
│  ├───────────────────────────┼──────┼──────┼──────────┤    │
│  │ 1245 N Central Ave        │  4   │  3   │ $1.30M   │    │
│  │ 823 E Glenoaks Blvd       │  3   │  2   │ $1.15M   │    │
│  │ 456 W Dryden St           │  5   │  4   │ $1.58M   │    │
│  │ ... (up to 10 rows)                                │    │
│  └───────────────────────────┴──────┴──────┴──────────┘    │
├─────────────────────────────────────────────────────────────┤
│  [View Full Report →]                                       │
└─────────────────────────────────────────────────────────────┘
```

**Gallery Reports (V5 - Full Alignment):**
```
┌─────────────────────────────────────────────────────────────┐
│  3-METRIC CARDS: Count | Median Price | DOM                 │
├─────────────────────────────────────────────────────────────┤
│  PHOTO GALLERY GRID                                         │
│  ┌──────┐ ┌──────┐ ┌──────┐                                │
│  │ 📷   │ │ 📷   │ │ 📷   │   (3×3 for gallery)           │
│  │ $1.8M│ │ $1.4M│ │ $1.3M│   (2×2 for featured)          │
│  └──────┘ └──────┘ └──────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### 6.1.1 V4.2 PDF-Aligned Design (Current - All Reports)

V4.2 extends the PDF-aligned design to **all major report types**:

| Report Type | 4-Metric Hero Row | Insight Paragraph |
|-------------|:-----------------:|:-----------------:|
| `market_snapshot` | ✅ Median Price, Closed, DOM, MOI | ✅ Market condition summary |
| `new_listings` | ✅ Total, Median Price, DOM, $/SqFt | ✅ New listings overview |
| `closed` | ✅ Total, Median Price, DOM, CTL% | ✅ Sales activity summary |
| `inventory` | ✅ Active, New, DOM, MOI | ✅ Inventory condition |
| `price_bands` | ✅ Total, Median, DOM, Range | ✅ Price segmentation intro |

Each email now features:
- **PDF-style title**: `{Report Type} – {Area}` format
- **Subline**: `Period: Last X days • Source: Live MLS Data`
- **4-metric hero row**: Report-specific key metrics
- **Insight paragraph**: 1-2 sentence contextual summary

### 6.1.2 V4 Market Snapshot Specifics

V4 redesigns the Market Snapshot email to **feel like the cover page of the PDF**:

| Component | V3 (Old) | V4 (New) |
|-----------|----------|----------|
| **Header Title** | Generic tagline "Your Complete Market Overview" | "Market Snapshot – [Area]" |
| **Header Subline** | "[Area] • Last X Days" | "Period: Last X days • Source: Live MLS Data" |
| **Hero Metrics** | 3 cards (Active, Median, DOM) | **4 cards** (Median Sale Price, Closed Sales, DOM, MOI) |
| **Core Indicators** | N/A | **NEW: 3 cards** (New Listings, Pending, Sale-to-List) |
| **Insight Paragraph** | N/A | **NEW:** 1-2 sentence market summary |
| **Segmentation** | Single-line text | Structured Property Type + Price Tier sections |

**V4 Structure Matches PDF:**

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Market Snapshot – Beverly Hills                    │
│  Subline: Period: Last 30 days • Source: Live MLS Data      │
│  Brand Pill: [Pacific Coast Title]                          │
├─────────────────────────────────────────────────────────────┤
│  INSIGHT PARAGRAPH                                          │
│  "This snapshot provides key market indicators for..."      │
├─────────────────────────────────────────────────────────────┤
│  HERO ROW (4 metrics - same as PDF header)                  │
│  ┌────────┬────────┬────────┬────────┐                      │
│  │ $4.2M  │   42   │   42   │  2.8   │                      │
│  │ Median │ Closed │  DOM   │  MOI   │                      │
│  └────────┴────────┴────────┴────────┘                      │
├─────────────────────────────────────────────────────────────┤
│  CORE INDICATORS (3 cards - same as PDF)                    │
│  ┌──────────┬──────────┬──────────┐                         │
│  │    23    │    18    │  98.5%   │                         │
│  │ New List │ Pending  │   CTL    │                         │
│  └──────────┴──────────┴──────────┘                         │
├─────────────────────────────────────────────────────────────┤
│  SEGMENTATION PREVIEW                                       │
│  Property Types: 🏠 89 SFR • 🏢 28 Condos • 🏘️ 10 Townhomes │
│  Price Tiers: [Entry] 45 | [Move-Up] 52 | [Luxury] 30       │
├─────────────────────────────────────────────────────────────┤
│  [View Full Report →]                                       │
│  Rep Footer                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Rationale:** The V3 email felt like a "teaser" with random numbers. V4 creates a **condensed cover page** that mirrors the PDF's section structure, making the email feel like part of the same product.

### 6.1.2 V4.1 Modern Styling Refinements

V4.1 updates visual elements for a cleaner, more modern look:

| Element | V4 | V4.1 |
|---------|-----|------|
| **Typography** | Georgia serif | System font stack (`-apple-system, BlinkMacSystemFont, Segoe UI...`) |
| **Property Types** | Emoji icons (🏠🏢🏘️) | Colored dots (●) with blue/purple/pink/amber |
| **Price Tiers** | Left border accent | Top border + diamond icons (◇ Entry, ◈ Move-Up, ◆ Luxury) |
| **Text alignment** | Left-aligned in cards | Centered in price tier cards |

### 6.1.3 V3.1 Monochromatic Design (Preserved in V4/V4.1)

V3.1 color philosophy is preserved:

| Color Usage | Where |
|-------------|-------|
| `primary_color` | All data values (hero metrics, indicators, tier counts) |
| `accent_color` | Header gradient only |
| Neutral gray | Labels, supporting text |

### 6.2 Scheduled Report Template (V5)

**File:** `apps/worker/src/worker/email/template.py`

> ⚠️ **Single Source of Truth**: This template is used by BOTH scheduled emails (worker) AND test emails (API). See [Template Unification](#64-unified-template-architecture).

```python
def schedule_email_html(
    account_name: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    metrics: Dict,
    pdf_url: str,
    unsubscribe_url: str,
    brand: Optional[Brand] = None,
    listings: Optional[List[Dict]] = None,  # V5: Photo gallery for gallery reports
    preset_display_name: Optional[str] = None,  # V6: Custom preset name (e.g., "First-Time Buyer")
    filter_description: Optional[str] = None,  # V11: Human-readable filter summary
) -> str:
```

**V3.1 Features:**

| Feature | Description |
|---------|-------------|
| **Monochromatic Metrics** | All 3 metric values use `primary_color` only |
| **Neutral Extra Stats** | Values use dark gray (`#1e293b`) instead of colors |
| **Unified Price Tiers** | `primary_color` with opacity variations (40%, 70%, 100%) |
| **Professional Typography** | Georgia serif for headings, system sans-serif for body |
| **Email Logo Support** | Separate `email_logo_url` for light logos on gradient headers |
| **Property Type Breakdown** | SFR, Condo, Townhome counts (Market Snapshot) |

**Template Structure (V3.1):**

```html
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
  
  <!-- Gradient Header (only place accent_color is used) -->
  <table style="background: linear-gradient(135deg, {primary_color}, {accent_color});">
    <img src="{email_logo_url}" />
    <span>{report_type}</span>
    <h1 style="font-family: Georgia, serif;">{tagline}</h1>
    <p>{area} • Last {lookback_days} days</p>
  </table>
  
  <!-- 3-Column Metrics (ALL use primary_color) -->
  <table>
    <tr>
      <td style="color: {primary_color};">{metric1_value}</td>
      <td style="color: {primary_color};">{metric2_value}</td>
      <td style="color: {primary_color};">{metric3_value}</td>
    </tr>
  </table>
  
  <!-- Extra Stats Row (NEUTRAL gray values) -->
  <table style="background: #f8fafc;">
    <td>
      <strong style="color: #1e293b;">{moi}</strong> Months of Inventory |
      <strong style="color: #1e293b;">{ctl}%</strong> Close-to-List
    </td>
  </table>
  
  <!-- Property Type Breakdown -->
  <table style="background: #f8fafc;">
    <td>🏠 {sfr} Single Family • 🏢 {condo} Condos • 🏘️ {townhome} Townhomes</td>
  </table>
  
  <!-- Price Tier Distribution (primary_color with opacity) -->
  <table>
    <tr>
      <td style="border-left: 3px solid {primary_color}66;">{entry_count} Entry Level</td>
      <td style="border-left: 3px solid {primary_color}B3;">{moveup_count} Move-Up</td>
      <td style="border-left: 3px solid {primary_color};">{luxury_count} Luxury</td>
    </tr>
  </table>
  
  <!-- CTA Button -->
  <a href="{pdf_url}" style="background: {primary_color};">View Full Report →</a>
  
  <!-- Agent Footer -->
  <table>
    <tr>
      <td><img src="{rep_photo_url}" style="border-radius: 50%;" /></td>
      <td>{contact_line1}<br/>{contact_line2}</td>
    </tr>
  </table>
  
  <!-- Unsubscribe -->
  <a href="{unsubscribe_url}">Unsubscribe</a>
</body>
</html>
```

### 6.3 Subject Line Generation

```python
def schedule_email_subject(
    report_type: str,
    city: Optional[str] = None,
    zip_codes: Optional[List[str]] = None
) -> str:
    """
    Generate email subject line.
    
    Examples:
    - "📊 Your Market Snapshot for Beverly Hills is Ready!"
    - "📊 Your New Listings for 90210, 90211 is Ready!"
    - "📊 Your Closed Sales for Your Area is Ready!"
    """
```

### 6.4 Unified Template Architecture

**V3.1 introduces template unification** - test emails and production emails now use the **same template function**.

#### Before V3.1 (❌ Dual Maintenance)
```
apps/worker/src/worker/email/template.py    ← Production scheduled emails
apps/api/src/api/routes/branding_tools.py   ← Test emails (separate 300+ line template)
```

Every template change required updating **two files** - error-prone and time-consuming.

#### After V3.1 (✅ Single Source of Truth)
```
apps/worker/src/worker/email/template.py    ← THE template (used by both)
apps/api/src/api/routes/branding_tools.py   ← Imports and calls the same function
```

**How it works:**

```python
# branding_tools.py imports the worker template
from worker.email.template import schedule_email_html

# Then calls it with sample data for testing
email_html = schedule_email_html(
    account_name=brand_name,
    report_type=body.report_type,
    city="Beverly Hills",          # Sample city
    metrics=sample_metrics,        # Hardcoded sample data
    pdf_url="#",                   # Placeholder
    unsubscribe_url="#",           # Placeholder
    brand=brand_dict,
)
```

**Sample Data for Test Emails (V5 - Report-Specific with Gallery Photos):**

Each report type uses its own sample data and sample city. **V5 adds sample listings with Unsplash photos for gallery reports.**

| Report Type | Sample City | Unique Data |
|-------------|-------------|-------------|
| `market_snapshot` | Beverly Hills | Property types, price tiers, core indicators |
| `new_listings` | Pasadena | 47 new listings, $892/sqft |
| `inventory` | Glendale | 156 active, 34 new this month |
| `closed` | Burbank | 38 sold, $158.7M volume |
| `price_bands` | Santa Monica | 4 price bands ($450K-$8.5M) |
| `open_houses` | Manhattan Beach | 24 open houses (15 Sat, 18 Sun) |
| `new_listings_gallery` | Redondo Beach | **9 sample listings with Unsplash photos** (3×3 grid) |
| `featured_listings` | Malibu | **4 luxury listings with Unsplash photos** (2×2 grid) |

**V5 Sample Listings Structure:**

Gallery report test emails now include a `sample_listings` array with realistic property data:

```python
# Example: new_listings_gallery sample data
sample_listings_data["new_listings_gallery"] = [
    {
        "hero_photo_url": "https://images.unsplash.com/photo-1600596542815...",
        "street_address": "2847 Pacific Coast Hwy",
        "city": "Redondo Beach",
        "zip_code": "90277",
        "list_price": 1875000,
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2650
    },
    # ... 8 more listings for 3×3 grid
]
```

**Benefits:**
- ✅ Change template once, both pathways update
- ✅ Test emails **exactly match** production emails
- ✅ No risk of template drift
- ✅ Reduced maintenance burden

---

## 7. White-Label Branding

### 7.1 Brand Resolution (December 2025 - Option A)

**File:** `apps/api/src/api/services/branding.py`

```python
def get_brand_for_account(cur, account_id: str) -> Brand:
    """
    Resolve branding for an account.
    
    Logic:
    1. If account is REGULAR with sponsor_account_id → use sponsor's affiliate_branding
    2. If account is INDUSTRY_AFFILIATE → use their affiliate_branding
    3. If account is un-sponsored REGULAR → use accounts table + users.avatar_url
    4. Otherwise → return TrendyReports default branding
    """
```

**Option A Implementation:**

For un-sponsored regular users, the system automatically uses:
- Branding fields from the `accounts` table (logos, colors, contact info)
- User's `avatar_url` from the `users` table as their headshot

This means regular agents set their headshot once (during onboarding or Account Settings) and it automatically appears on their reports and emails.

### 7.2 Branding Data Structure

```python
{
    "brand_display_name": "Pacific Coast Title Company",
    "logo_url": "https://r2.../branding/logo.png",
    "email_logo_url": "https://r2.../branding/logo-light.png",  # Optional: light version for email headers
    "primary_color": "#0061bd",
    "accent_color": "#f26b2b",
    "rep_photo_url": "https://r2.../branding/headshot.png",
    "contact_line1": "John Smith • Senior Rep",
    "contact_line2": "(555) 123-4567 • john@company.com",
    "website_url": "https://www.company.com"
}
```

### 7.3 How Branding Appears in Emails (V3.1)

| Element | Branding Field | Notes |
|---------|----------------|-------|
| Header gradient | `primary_color` → `accent_color` | 135° gradient (**only use of accent**) |
| Logo in header | `email_logo_url` or `logo_url` | Light version preferred |
| Brand name | `brand_display_name` | |
| CTA button | `primary_color` | Solid background |
| **All 3 metric values** | `primary_color` | Georgia serif (unified V3.1) |
| **Price tier borders** | `primary_color` with opacity | 40%, 70%, 100% for hierarchy |
| **Extra stats values** | Neutral (`#1e293b`) | Not branded (V3.1) |
| Footer photo | `rep_photo_url` | Circular, border |
| Footer contact | `contact_line1`, `contact_line2` | |
| Footer link | `website_url` | |

#### V3.1 Color Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│  accent_color: ONLY in header gradient                      │
│  primary_color: All data elements (metrics, tiers, CTA)     │
│  Neutral gray: Supporting text (extra stats, labels)        │
└─────────────────────────────────────────────────────────────┘
```

This creates a **cohesive, professional appearance** regardless of brand colors.

---

## 8. Unsubscribe & Suppression

### 8.1 Unsubscribe Flow

```
1. Recipient clicks unsubscribe link in email
   URL: /api/v1/email/unsubscribe?token={token}&email={email}

2. Token is HMAC-SHA256 of "{account_id}:{email}" with EMAIL_UNSUB_SECRET

3. API verifies token:
   - Decode and extract account_id, email
   - Verify HMAC signature
   - If valid, insert into email_suppressions

4. Recipient sees confirmation page
```

### 8.2 Token Generation

**Worker side:** `apps/worker/src/worker/email/send.py`
```python
def generate_unsubscribe_token(account_id: str, email: str) -> str:
    message = f"{account_id}:{email}".encode()
    signature = hmac.new(
        EMAIL_UNSUB_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature
```

### 8.3 Suppression Checking

Before sending any scheduled email:

```python
# Query suppressed emails for this account
cur.execute("""
    SELECT email
    FROM email_suppressions
    WHERE account_id = %s
      AND email = ANY(%s)
""", (account_id, recipients))

suppressed = [row[0] for row in cur.fetchall()]
filtered_recipients = [r for r in recipients if r not in suppressed]

if not filtered_recipients:
    # All recipients suppressed - skip email
    return (200, "All recipients suppressed")
```

---

## 9. Environment Variables

### 9.1 Worker Services

Required on all worker services (`worker-service`, `consumer-bridge`, `ticker`):

```bash
# SendGrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=reports@trendyreports.io
DEFAULT_FROM_NAME=TrendyReports

# Unsubscribe
EMAIL_UNSUB_SECRET=your_32_char_secret_here
WEB_BASE=https://www.trendyreports.io
```

### 9.2 API Service

Required on the API service for branding test emails:

```bash
# SendGrid (for test emails only)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=reports@trendyreports.io
DEFAULT_FROM_NAME=TrendyReports

# Unsubscribe verification (must match worker's EMAIL_UNSUB_SECRET)
EMAIL_UNSUB_SECRET=same_as_worker_EMAIL_UNSUB_SECRET
WEB_BASE=https://www.trendyreports.io
```

### 9.3 Variable Reference

| Variable | Service | Description |
|----------|---------|-------------|
| `SENDGRID_API_KEY` | Worker, API | SendGrid API key with Mail Send permission |
| `DEFAULT_FROM_EMAIL` | Worker, API | Verified sender email address |
| `DEFAULT_FROM_NAME` | Worker, API | Default sender name |
| `EMAIL_UNSUB_SECRET` | Worker, API | HMAC secret for unsubscribe tokens (must match on both) |
| `WEB_BASE` | Worker, API | Base URL for unsubscribe links |

---

## 10. Email Flow Diagrams

### 10.1 Scheduled Email Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SCHEDULED EMAIL FLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐              │
│  │ Ticker  │───▶│  Redis  │───▶│ Worker  │───▶│ SimplyRETS│            │
│  │ (60s)   │    │ Queue   │    │ (Celery)│    │   API    │             │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘              │
│       │                             │              │                     │
│       ▼                             ▼              ▼                     │
│  ┌─────────┐                  ┌─────────┐    ┌─────────┐               │
│  │schedule_│                  │ Report  │───▶│  PDF    │               │
│  │  runs   │                  │ Builder │    │ (R2)    │               │
│  │(queued) │                  └─────────┘    └─────────┘               │
│  └─────────┘                        │              │                    │
│                                     ▼              │                    │
│                               ┌─────────┐         │                    │
│                               │Branding │◀────────┘                    │
│                               │ Service │                              │
│                               └─────────┘                              │
│                                     │                                   │
│                                     ▼                                   │
│  ┌─────────┐                  ┌─────────┐                              │
│  │  email  │◀────────────────│ SendGrid│                              │
│  │   log   │                  │   API   │                              │
│  └─────────┘                  └─────────┘                              │
│                                     │                                   │
│                                     ▼                                   │
│                               ┌─────────┐                              │
│                               │Recipient│                              │
│                               │  Inbox  │                              │
│                               └─────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Unsubscribe Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      UNSUBSCRIBE FLOW                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐              │
│  │ Email   │───▶│  Click  │───▶│   API   │───▶│ Verify  │              │
│  │ Footer  │    │  Link   │    │Endpoint │    │  HMAC   │              │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘              │
│                                                      │                   │
│                                                      ▼                   │
│                                                ┌─────────┐              │
│                                                │  email  │              │
│                                                │suppress │              │
│                                                │  ions   │              │
│                                                └─────────┘              │
│                                                      │                   │
│                                                      ▼                   │
│                                                ┌─────────┐              │
│                                                │ Confirm │              │
│                                                │  Page   │              │
│                                                └─────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Troubleshooting

### 11.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Emails not sending | `SENDGRID_API_KEY` not set | Add to Render environment |
| 401 from SendGrid | Invalid API key | Regenerate key in SendGrid |
| 403 from SendGrid | Sender not verified | Verify sender in SendGrid |
| No branding in email | `affiliate_branding` table missing | Run migration 0008 |
| Unsubscribe not working | `UNSUBSCRIBE_SECRET` mismatch | Ensure same on API and Worker |
| All recipients suppressed | Users unsubscribed | Check `email_suppressions` table |

### 11.2 Checking Email Logs

```sql
-- Recent email sends
SELECT 
    created_at,
    to_emails,
    subject,
    response_code,
    status,
    error
FROM email_log
WHERE account_id = 'your-account-id'
ORDER BY created_at DESC
LIMIT 20;

-- Check suppressions
SELECT email, reason, created_at
FROM email_suppressions
WHERE account_id = 'your-account-id';
```

### 11.3 Testing Email Locally

```bash
# Set environment
export SENDGRID_API_KEY=SG.your_key
export DEFAULT_FROM_EMAIL=reports@trendyreports.io

# Run worker
cd apps/worker
poetry run python -c "
from worker.email.providers.sendgrid import send_email
status, msg = send_email(
    to_emails=['test@example.com'],
    subject='Test Email',
    html_content='<h1>Test</h1>'
)
print(f'Status: {status}, Message: {msg}')
"
```

---

## 12. Database Schema Changes

### 12.1 Email Logo URL (Migration 0019)

**File:** `db/migrations/0019_add_email_logo_url.sql`

```sql
ALTER TABLE affiliate_branding
ADD COLUMN email_logo_url TEXT;
```

**Purpose:** Support a separate light-colored logo for email headers where the gradient background may clash with dark logos.

**Usage:**
- If `email_logo_url` is set → Use in email header
- If `email_logo_url` is null → Fall back to `logo_url`

**Defensive Code:** API queries handle the case where this column doesn't exist (rolling deployment compatibility).

### 12.2 affiliate_branding Table Schema

```sql
CREATE TABLE affiliate_branding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    affiliate_account_id TEXT NOT NULL UNIQUE REFERENCES accounts(id),
    brand_display_name TEXT NOT NULL,
    logo_url TEXT,
    email_logo_url TEXT,           -- Added in migration 0019
    primary_color TEXT NOT NULL DEFAULT '#0ea5e9',
    accent_color TEXT NOT NULL DEFAULT '#2563eb',
    rep_photo_url TEXT,
    contact_line1 TEXT,
    contact_line2 TEXT,
    website_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 13. Future Enhancements

### 13.1 Planned Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **Email Events Webhook** | Track delivered/opened/clicked/bounced via SendGrid webhooks | High |
| **Auto-pause on Bounces** | Disable schedules with high bounce rates | Medium |
| **People-based Recipients** | Select recipients from `/app/people` instead of raw emails | High |
| **Attachment Support** | Option to attach PDF instead of link-only | Low |
| **Template Variants** | Different templates for different report types | Medium |
| **A/B Testing** | Test subject lines and layouts | Low |

### 13.2 Email Events Table (Planned)

```sql
CREATE TABLE email_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_log_id UUID REFERENCES email_log(id),
    event_type TEXT NOT NULL,  -- 'delivered', 'opened', 'clicked', 'bounced', 'spam'
    recipient TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 13.3 Webhook Handler (Planned)

```python
@router.post("/v1/webhooks/sendgrid")
async def handle_sendgrid_webhook(events: List[SendGridEvent]):
    for event in events:
        # Log event
        insert_email_event(event)
        
        # Handle bounces
        if event.type == "bounce":
            insert_suppression(
                account_id=event.account_id,
                email=event.email,
                reason="bounce"
            )
```

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `apps/worker/src/worker/email/providers/sendgrid.py` | SendGrid API client |
| `apps/worker/src/worker/email/template.py` | **Unified HTML template** (used by both scheduled & test emails) |
| `apps/worker/src/worker/email/send.py` | Email orchestration |
| `apps/worker/src/worker/tasks.py` | Celery task with email hook |
| `apps/api/src/api/routes/branding_tools.py` | Test email endpoint (imports from template.py) |
| `apps/api/src/api/routes/unsubscribe.py` | Unsubscribe endpoint |

### Key Tables

| Table | Purpose |
|-------|---------|
| `email_log` | Audit trail of all sends |
| `email_suppressions` | Unsubscribed/bounced emails |
| `schedules` | Schedule config including recipients |
| `schedule_runs` | Individual run tracking |
| `affiliate_branding` | White-label branding data |

### Key Environment Variables

| Variable | Where |
|----------|-------|
| `SENDGRID_API_KEY` | Worker + API |
| `DEFAULT_FROM_EMAIL` | Worker + API |
| `EMAIL_UNSUB_SECRET` | Worker + API |
| `WEB_BASE` | Worker + API |

---

*This document is the single source of truth for TrendyReports email system implementation.*

