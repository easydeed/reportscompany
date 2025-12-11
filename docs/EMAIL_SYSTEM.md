# TrendyReports Email System

> Complete technical documentation for the email infrastructure, templates, and delivery pipeline.

**Last Updated:** December 11, 2024

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Email Data Model](#2-email-data-model)
3. [Provider Integration (SendGrid)](#3-provider-integration-sendgrid)
4. [Scheduled Report Emails](#4-scheduled-report-emails)
5. [Branding Test Emails](#5-branding-test-emails)
6. [Email Templates](#6-email-templates)
7. [White-Label Branding](#7-white-label-branding)
8. [Unsubscribe & Suppression](#8-unsubscribe--suppression)
9. [Environment Variables](#9-environment-variables)
10. [Email Flow Diagrams](#10-email-flow-diagrams)
11. [Troubleshooting](#11-troubleshooting)
12. [Database Schema Changes](#12-database-schema-changes)
13. [Future Enhancements](#13-future-enhancements)

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
| Email Template | `apps/worker/src/worker/email/template.py` | HTML generation for scheduled emails |
| Email Orchestrator | `apps/worker/src/worker/email/send.py` | Suppression filtering, template rendering |
| Branding Test | `apps/api/src/api/routes/branding_tools.py` | Test email endpoint |
| Unsubscribe API | `apps/api/src/api/routes/unsubscribe.py` | Handle unsubscribe requests |

---

## 2. Email Data Model

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
   c. Build sample email HTML with branding
   d. Send via SendGrid (directly, not via worker)
   e. Return success/failure
```

### 5.4 Test Email Content

The test email includes:
- Branded header (logo, colors, brand name)
- Sample metrics (hardcoded Beverly Hills data)
- Sample metric table
- Branded footer with contact info
- "[Test]" prefix in subject line

---

## 6. Email Templates

### 6.1 Template Version History

| Version | Date | Changes |
|---------|------|---------|
| V3 | Dec 11, 2024 | Professional styling, Market Snapshot breakdowns |
| V2 | Nov 25, 2024 | Gradient headers, dark mode, responsive |
| V1 | Nov 2024 | Initial template |

### 6.2 Scheduled Report Template (V3)

**File:** `apps/worker/src/worker/email/template.py`

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
) -> str:
```

**V3 Features:**

| Feature | Description |
|---------|-------------|
| **Professional Typography** | Georgia serif for headings, system sans-serif for body |
| **Muted Color Palette** | Refined tones (#64748b, #94a3b8) for sophistication |
| **Email Logo Support** | Separate `email_logo_url` for light logos on gradient headers |
| **Property Type Breakdown** | SFR, Condo, Townhome counts (Market Snapshot) |
| **Price Tier Distribution** | Entry, Move-Up, Luxury with counts and ranges |
| **Extra Stats Row** | Months of Inventory, Close-to-List Ratio |

**Template Structure:**

```html
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
  
  <!-- Gradient Header -->
  <table style="background: linear-gradient(135deg, {primary_color}, {accent_color});">
    <!-- Logo (email_logo_url or logo_url) -->
    <img src="{email_logo_url}" />
    <!-- Report label badge -->
    <span>{report_type}</span>
    <!-- Tagline in Georgia serif -->
    <h1 style="font-family: Georgia, serif;">{tagline}</h1>
    <p>{area} • Last {lookback_days} days</p>
  </table>
  
  <!-- 3-Column Metrics (Georgia serif numbers) -->
  <table>
    <tr>
      <td style="font-family: Georgia, serif; font-size: 30px;">{metric1_value}</td>
      <td style="font-family: Georgia, serif; font-size: 30px;">{metric2_value}</td>
      <td style="font-family: Georgia, serif; font-size: 30px;">{metric3_value}</td>
    </tr>
  </table>
  
  <!-- Extra Stats Row (Market Snapshot & Closed Sales) -->
  <table style="background: #f8fafc;">
    <td>{moi} Months of Inventory | {ctl}% Close-to-List</td>
  </table>
  
  <!-- Property Type Breakdown (Market Snapshot) -->
  <table style="background: #f8fafc;">
    <td>🏠 {sfr} Single Family • 🏢 {condo} Condos • 🏘️ {townhome} Townhomes</td>
  </table>
  
  <!-- Price Tier Distribution (Market Snapshot) -->
  <table>
    <tr>
      <td style="border-left: 3px solid #059669;">{entry_count} Entry Level</td>
      <td style="border-left: 3px solid {primary_color};">{moveup_count} Move-Up</td>
      <td style="border-left: 3px solid {accent_color};">{luxury_count} Luxury</td>
    </tr>
  </table>
  
  <!-- CTA Button (solid color, subtle shadow) -->
  <a href="{pdf_url}" style="background: {primary_color}; font-family: Georgia, serif;">
    View Full Report →
  </a>
  
  <!-- Agent Footer with circular photo -->
  <table>
    <tr>
      <td><img src="{rep_photo_url}" style="border-radius: 50%;" /></td>
      <td>
        <p>{contact_line1}</p>
        <p>{contact_line2}</p>
        <a href="{website_url}">{website_url}</a>
      </td>
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

### 6.4 Test Email Template

**File:** `apps/api/src/api/routes/branding_tools.py`

The test email sent from the branding page mirrors the V3 scheduled report template with sample data:

| Section | Sample Values |
|---------|---------------|
| Main Metrics | 127 Active, $4.2M Median, 42 days DOM |
| Extra Stats | 2.8 MOI, 98.5% CTL |
| Property Types | 89 SFR, 28 Condos, 10 Townhomes |
| Price Tiers | 45 Entry, 52 Move-Up, 30 Luxury |

---

## 7. White-Label Branding

### 7.1 Brand Resolution

**File:** `apps/api/src/api/services/branding.py`

```python
def get_branding_for_account(cur, account_id: str) -> dict:
    """
    Resolve branding for an account.
    
    Logic:
    1. If account is INDUSTRY_AFFILIATE → use their affiliate_branding
    2. If account has sponsor_account_id → use sponsor's branding
    3. Otherwise → return TrendyReports default branding
    """
```

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

### 7.3 How Branding Appears in Emails

| Element | Branding Field | Notes |
|---------|----------------|-------|
| Header background | `primary_color` → `accent_color` | 135° gradient |
| Logo in header | `email_logo_url` or `logo_url` | Light version preferred |
| Brand name | `brand_display_name` | |
| CTA button | `primary_color` | Subtle shadow |
| Metric values | `primary_color`, `accent_color` | Georgia serif |
| Footer photo | `rep_photo_url` | Circular, border |
| Footer contact | `contact_line1`, `contact_line2` | |
| Footer link | `website_url` | |

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
| `apps/worker/src/worker/email/template.py` | HTML template generation |
| `apps/worker/src/worker/email/send.py` | Email orchestration |
| `apps/worker/src/worker/tasks.py` | Celery task with email hook |
| `apps/api/src/api/routes/branding_tools.py` | Test email endpoint |
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

