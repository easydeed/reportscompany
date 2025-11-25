# TrendyReports Email System

> Complete technical documentation for the email infrastructure, templates, and delivery pipeline.

**Last Updated:** November 2025

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Email Data Model](#2-email-data-model)
3. [SendGrid Integration](#3-sendgrid-integration)
4. [Scheduled Report Emails](#4-scheduled-report-emails)
5. [Branding Test Emails](#5-branding-test-emails)
6. [White-Label Branding](#6-white-label-branding)
7. [Email Templates](#7-email-templates)
8. [Unsubscribe System](#8-unsubscribe-system)
9. [Environment Variables](#9-environment-variables)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Architecture Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TrendyReports Email System                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SCHEDULED REPORTS                         BRANDING TEST EMAILS             │
│  ─────────────────                         ────────────────────             │
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌────────┐  ┌─────────┐    ┌────────┐       │
│  │ Ticker  │───▶│ Celery  │───▶│ Worker │  │   API   │───▶│SendGrid│       │
│  │(60s loop)│   │  Queue  │    │        │  │         │    │        │       │
│  └─────────┘    └─────────┘    │        │  └─────────┘    └────────┘       │
│                                │        │                                   │
│                                │   ▼    │                                   │
│                           ┌────┴────────┴────┐                              │
│                           │    SendGrid      │                              │
│                           │   (v3 API)       │                              │
│                           └────────┬─────────┘                              │
│                                    │                                        │
│                                    ▼                                        │
│                           ┌─────────────────┐                               │
│                           │   Recipient     │                               │
│                           │    Inbox        │                               │
│                           └─────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Email Role | Description |
|---------|------------|-------------|
| **Ticker** (`markets-report-ticker`) | Triggers | Finds due schedules every 60s, enqueues jobs |
| **Worker** (`reportscompany-worker-service`) | Sends scheduled emails | Generates reports, renders templates, sends via SendGrid |
| **Consumer** (`reportscompany-consumer-bridge`) | Processes queue | Reads Redis queue, dispatches to Celery |
| **API** (`reportscompany-api`) | Sends test emails | Handles branding preview test emails |

### Technology Stack

- **Email Provider:** SendGrid (v3 API)
- **Queue:** Redis (Upstash) + Celery
- **Templates:** Python string templates with inline CSS
- **Storage:** PostgreSQL (email_log, email_suppressions)

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
    report_id UUID REFERENCES report_generations(id),
    provider TEXT NOT NULL,              -- 'sendgrid'
    to_emails TEXT[] NOT NULL,           -- Array of recipients
    subject TEXT,
    response_code INT,                   -- 202 = success, 4xx/5xx = error
    status TEXT,                         -- 'sent', 'failed', 'suppressed'
    error TEXT,                          -- Error message if failed
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Fields:**
- `provider`: Always `'sendgrid'` currently
- `response_code`: `202` means SendGrid accepted the email
- `status`: `'sent'`, `'failed'`, or `'suppressed'` (all recipients blocked)

### 2.2 `email_suppressions`

Stores unsubscribed or bounced email addresses per account.

```sql
CREATE TABLE email_suppressions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    email TEXT NOT NULL,
    reason TEXT NOT NULL,                -- 'unsubscribe', 'bounce', 'complaint'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, email)
);
```

**Behavior:**
- Before sending, worker queries this table
- Suppressed emails are filtered out
- If ALL recipients are suppressed, no email is sent

### 2.3 `schedules` (Email-Related Fields)

```sql
-- Relevant email fields in schedules table
recipients TEXT[],           -- Array of email addresses
include_attachment BOOLEAN,  -- Future: attach PDF vs link-only
active BOOLEAN,              -- Must be true for emails to send
```

### 2.4 `schedule_runs`

Tracks each execution of a schedule.

```sql
CREATE TABLE schedule_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES schedules(id),
    report_run_id UUID REFERENCES report_generations(id),
    status TEXT NOT NULL,    -- 'queued', 'processing', 'completed', 'failed', 'failed_email'
    error TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Status Values:**
- `queued`: Ticker created the run, waiting for worker
- `processing`: Worker is generating the report
- `completed`: Report generated AND email sent successfully
- `failed`: Report generation failed
- `failed_email`: Report generated but email failed

---

## 3. SendGrid Integration

### 3.1 Provider Client

**Location:** `apps/worker/src/worker/email/providers/sendgrid.py`

```python
import httpx

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_name: str = None,
    from_email: str = None,
) -> Tuple[int, str]:
    """
    Send email via SendGrid v3 API.
    
    Returns:
        (status_code, response_text)
        - 202: Email accepted by SendGrid
        - 4xx/5xx: Error occurred
    """
    payload = {
        "personalizations": [{
            "to": [{"email": email} for email in to_emails],
            "subject": subject,
        }],
        "from": {
            "email": from_email or DEFAULT_FROM_EMAIL,
            "name": from_name or DEFAULT_FROM_NAME,
        },
        "content": [{
            "type": "text/html",
            "value": html_content,
        }],
    }
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    
    response = httpx.post(SENDGRID_API_URL, json=payload, headers=headers)
    return (response.status_code, response.text)
```

### 3.2 Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| `202` | Accepted | Email queued for delivery |
| `400` | Bad Request | Check payload format |
| `401` | Unauthorized | Invalid API key |
| `403` | Forbidden | Sender not verified |
| `429` | Rate Limited | Slow down requests |
| `500` | Server Error | Retry later |

### 3.3 Sender Verification

SendGrid requires sender email verification:
- Verify `reports@trendyreports.io` in SendGrid dashboard
- Or use a verified domain with SPF/DKIM/DMARC

---

## 4. Scheduled Report Emails

### 4.1 Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Scheduled Report Email Flow                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. TICKER (every 60s)                                                   │
│     │                                                                    │
│     ├─▶ Query: SELECT * FROM schedules                                   │
│     │          WHERE active = true AND next_run_at <= NOW()              │
│     │                                                                    │
│     ├─▶ For each due schedule:                                           │
│     │   • Insert schedule_runs row (status='queued')                     │
│     │   • Enqueue job to Redis with schedule_id in params                │
│     │   • Calculate and update next_run_at                               │
│     │                                                                    │
│  2. CONSUMER                                                             │
│     │                                                                    │
│     ├─▶ Read job from Redis queue                                        │
│     ├─▶ Call Celery task: generate_report.delay(...)                     │
│     │                                                                    │
│  3. WORKER (generate_report task)                                        │
│     │                                                                    │
│     ├─▶ Fetch MLS data from SimplyRETS                                   │
│     ├─▶ Build result_json with metrics                                   │
│     ├─▶ Generate PDF via PDFShift                                        │
│     ├─▶ Upload PDF to R2                                                 │
│     │                                                                    │
│     ├─▶ IF schedule_id in params:                                        │
│     │   │                                                                │
│     │   ├─▶ Load schedule recipients                                     │
│     │   ├─▶ Get brand via get_brand_for_account()                        │
│     │   ├─▶ Filter against email_suppressions                            │
│     │   ├─▶ Render HTML template with brand + metrics                    │
│     │   ├─▶ Send via SendGrid                                            │
│     │   ├─▶ Log to email_log                                             │
│     │   └─▶ Update schedule_runs status                                  │
│     │                                                                    │
│  4. RECIPIENT receives branded email with PDF link                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Email Send Orchestrator

**Location:** `apps/worker/src/worker/email/send.py`

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
    Send scheduled report email with:
    - Suppression filtering
    - White-label branding
    - Unsubscribe link generation
    """
    # 1. Filter suppressed recipients
    if db_conn:
        suppressed = query_suppressions(db_conn, account_id, recipients)
        recipients = [r for r in recipients if r not in suppressed]
        
        if not recipients:
            return (200, "All recipients suppressed")
    
    # 2. Generate unsubscribe token
    unsub_token = generate_unsubscribe_token(account_id, recipients[0])
    unsubscribe_url = f"{WEB_BASE}/api/v1/email/unsubscribe?token={unsub_token}"
    
    # 3. Render HTML with brand
    html = schedule_email_html(
        account_name=account_name,
        report_type=payload["report_type"],
        metrics=payload["metrics"],
        pdf_url=payload["pdf_url"],
        unsubscribe_url=unsubscribe_url,
        brand=brand,  # White-label branding
    )
    
    # 4. Send via provider
    return send_email(recipients, subject, html)
```

### 4.3 Worker Integration

**Location:** `apps/worker/src/worker/tasks.py` (inside `generate_report`)

```python
# After successful report generation...
if schedule_id:
    # Load schedule and recipients
    schedule = load_schedule(cur, schedule_id)
    recipients = schedule["recipients"]
    
    # Get branding for this account
    brand = get_brand_for_account(cur, account_id)
    
    # Build email payload
    payload = {
        "report_type": report_type,
        "city": city,
        "zip_codes": zip_codes,
        "lookback_days": lookback_days,
        "metrics": result_json.get("metrics", {}),
        "pdf_url": pdf_url,
    }
    
    # Send email
    status_code, response_text = send_schedule_email(
        account_id=account_id,
        recipients=recipients,
        payload=payload,
        account_name=account_name,
        db_conn=conn,
        brand=brand,
    )
    
    # Log to email_log
    cur.execute("""
        INSERT INTO email_log (account_id, schedule_id, report_id, provider,
                               to_emails, subject, response_code, status, error)
        VALUES (%s, %s, %s, 'sendgrid', %s, %s, %s, %s, %s)
    """, (...))
```

---

## 5. Branding Test Emails

### 5.1 Purpose

The branding test email feature allows affiliates to:
- Preview how their branded emails will look
- Verify logo, colors, and contact info appear correctly
- Send a sample to themselves before going live

### 5.2 API Endpoint

**Location:** `apps/api/src/api/routes/branding_tools.py`

```
POST /v1/branding/test-email
```

**Request Body:**
```json
{
    "email": "affiliate@example.com",
    "report_type": "market_snapshot"
}
```

**Response (Success):**
```json
{
    "ok": true,
    "message": "Test email sent to affiliate@example.com",
    "report_type": "market_snapshot"
}
```

### 5.3 Implementation

```python
@router.post("/test-email")
async def send_test_email(
    body: TestEmailRequest,
    account_id: str = Depends(require_account_id)
):
    # 1. Verify SendGrid is configured
    if not SENDGRID_API_KEY:
        raise HTTPException(503, "Email service not configured")
    
    # 2. Get affiliate branding
    with db_conn() as (conn, cur):
        verify_affiliate_account(cur, account_id)
        branding = get_branding_for_account(cur, account_id)
    
    # 3. Build sample email HTML with branding
    email_html = build_test_email_html(branding, body.report_type)
    
    # 4. Send via SendGrid
    response = await httpx.post(
        SENDGRID_API_URL,
        json={
            "personalizations": [{"to": [{"email": body.email}]}],
            "from": {"email": DEFAULT_FROM_EMAIL, "name": branding["brand_display_name"]},
            "content": [{"type": "text/html", "value": email_html}],
        },
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"}
    )
    
    return {"ok": True, "message": f"Test email sent to {body.email}"}
```

### 5.4 Frontend Integration

**Proxy Route:** `apps/web/app/api/proxy/v1/branding/test-email/route.ts`

```typescript
export async function POST(request: NextRequest) {
    const token = cookies().get("mr_token")?.value;
    const body = await request.json();
    
    const response = await fetch(`${API_BASE}/v1/branding/test-email`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Cookie: `mr_token=${token}`,
        },
        body: JSON.stringify(body),
    });
    
    return NextResponse.json(await response.json());
}
```

---

## 6. White-Label Branding

### 6.1 Branding Resolution Logic

**Location:** `apps/api/src/api/services/branding.py`

```python
def get_branding_for_account(cur, account_id: str) -> Dict:
    """
    Resolve branding for an account:
    
    1. If INDUSTRY_AFFILIATE → use their affiliate_branding
    2. If REGULAR with sponsor → use sponsor's affiliate_branding
    3. Otherwise → TrendyReports default branding
    """
    # Get account info
    cur.execute("""
        SELECT account_type, sponsor_account_id
        FROM accounts WHERE id = %s
    """, (account_id,))
    account = cur.fetchone()
    
    if account["account_type"] == "INDUSTRY_AFFILIATE":
        # Use this account's branding
        return get_affiliate_branding(cur, account_id)
    
    if account["sponsor_account_id"]:
        # Use sponsor's branding (agent sponsored by affiliate)
        return get_affiliate_branding(cur, account["sponsor_account_id"])
    
    # Default TrendyReports branding
    return DEFAULT_BRAND
```

### 6.2 Brand Data Structure

```python
{
    "brand_display_name": "Pacific Coast Title Company",
    "logo_url": "https://r2.example.com/branding/logo.png",
    "primary_color": "#0061BD",
    "accent_color": "#F26B2B",
    "rep_photo_url": "https://r2.example.com/branding/headshot.png",
    "contact_line1": "Jane Smith • Senior Title Rep",
    "contact_line2": "(555) 123-4567 • jane@pctitle.com",
    "website_url": "https://www.pctitle.com"
}
```

### 6.3 Branding in Emails

The brand object is passed to email templates and used for:

| Element | Brand Field | Usage |
|---------|-------------|-------|
| Header Logo | `logo_url` | `<img src="{logo_url}">` |
| Header Background | `primary_color` | `background: linear-gradient(..., {primary_color}, {accent_color})` |
| Brand Name | `brand_display_name` | Header text, footer signature |
| CTA Button | `accent_color` | Button background color |
| Footer Photo | `rep_photo_url` | Representative headshot |
| Contact Info | `contact_line1`, `contact_line2` | Footer contact block |
| Website Link | `website_url` | Clickable link in footer |

---

## 7. Email Templates

### 7.1 Template Location

**Location:** `apps/worker/src/worker/email/template.py`

### 7.2 Scheduled Report Email Structure

```html
<!DOCTYPE html>
<html>
<body style="background-color: #f9fafb; font-family: Arial, sans-serif;">
    <table width="600" align="center">
        
        <!-- HEADER (Branded) -->
        <tr>
            <td style="background: linear-gradient(135deg, {primary_color}, {accent_color}); 
                       padding: 40px; text-align: center; border-radius: 8px 8px 0 0;">
                <!-- Logo (if present) -->
                <img src="{logo_url}" alt="{brand_name}" style="height: 50px;">
                
                <!-- Report Title -->
                <h1 style="color: white;">📊 Your {report_type} Report</h1>
                <p style="color: #e0e7ff;">{area} • Last {lookback_days} days</p>
                <p style="color: white; font-weight: 500;">{brand_name}</p>
            </td>
        </tr>
        
        <!-- GREETING -->
        <tr>
            <td style="padding: 30px 40px;">
                <p>Hi {account_name},</p>
                <p>Your scheduled <strong>{report_type}</strong> report is ready!</p>
            </td>
        </tr>
        
        <!-- KEY METRICS -->
        <tr>
            <td style="padding: 0 40px;">
                <table style="background: #f3f4f6; border-radius: 8px; width: 100%;">
                    <tr>
                        <td>Active Listings</td>
                        <td style="text-align: right; font-weight: bold;">{metrics.active}</td>
                    </tr>
                    <tr>
                        <td>Median Price</td>
                        <td style="text-align: right; font-weight: bold;">${metrics.median_price}</td>
                    </tr>
                    <tr>
                        <td>Days on Market</td>
                        <td style="text-align: right; font-weight: bold;">{metrics.avg_dom}</td>
                    </tr>
                </table>
            </td>
        </tr>
        
        <!-- CTA BUTTON -->
        <tr>
            <td style="padding: 30px 40px; text-align: center;">
                <a href="{pdf_url}" style="display: inline-block; padding: 16px 40px;
                   background: linear-gradient(135deg, {primary_color}, {accent_color});
                   color: white; text-decoration: none; border-radius: 8px;">
                    📄 View Full Report (PDF)
                </a>
                <p style="color: #6b7280; font-size: 14px;">Link expires in 7 days</p>
            </td>
        </tr>
        
        <!-- FOOTER (Branded) -->
        <tr>
            <td style="padding: 30px 40px; background: #f9fafb; border-top: 1px solid #e5e7eb;">
                <table>
                    <tr>
                        <!-- Rep Photo (if present) -->
                        <td style="width: 60px; vertical-align: top;">
                            <img src="{rep_photo_url}" style="width: 50px; height: 50px; 
                                 border-radius: 50%; border: 2px solid {primary_color};">
                        </td>
                        <!-- Contact Info -->
                        <td>
                            <p style="font-weight: 600;">{brand_name}</p>
                            <p style="color: #6b7280;">{contact_line1}</p>
                            <p style="color: #6b7280;">{contact_line2}</p>
                            <a href="{website_url}" style="color: {primary_color};">{website_url}</a>
                        </td>
                    </tr>
                </table>
                
                <!-- Unsubscribe -->
                <p style="text-align: center; font-size: 12px; color: #9ca3af;">
                    <a href="{unsubscribe_url}" style="color: #6b7280;">Unsubscribe</a>
                </p>
            </td>
        </tr>
        
    </table>
</body>
</html>
```

### 7.3 Template Functions

```python
def schedule_email_subject(report_type: str, city: str, zip_codes: list) -> str:
    """Generate email subject line."""
    type_display = report_type.replace("_", " ").title()
    area = city or f"ZIP {', '.join(zip_codes[:2])}"
    return f"📊 Your {type_display} Report – {area}"

def schedule_email_html(
    account_name: str,
    report_type: str,
    city: str,
    zip_codes: list,
    lookback_days: int,
    metrics: Dict,
    pdf_url: str,
    unsubscribe_url: str,
    brand: Optional[Dict] = None,
) -> str:
    """Render full HTML email with branding."""
    # Extract brand values with defaults
    brand_name = brand.get("brand_display_name", "TrendyReports") if brand else "TrendyReports"
    primary_color = brand.get("primary_color", "#667eea") if brand else "#667eea"
    # ... etc
    
    return f"""<!DOCTYPE html>..."""
```

---

## 8. Unsubscribe System

### 8.1 Token Generation

Unsubscribe links use HMAC-SHA256 tokens to prevent tampering:

```python
import hmac
import hashlib

def generate_unsubscribe_token(account_id: str, email: str) -> str:
    """
    Generate secure unsubscribe token.
    Token = HMAC-SHA256(secret, "account_id:email")
    """
    message = f"{account_id}:{email}".encode()
    signature = hmac.new(
        EMAIL_UNSUB_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature
```

### 8.2 Unsubscribe Endpoint

**Location:** `apps/api/src/api/routes/email.py`

```
POST /v1/email/unsubscribe/{token}?email={email}
```

**Flow:**
1. Extract `token` and `email` from request
2. Regenerate expected token using `EMAIL_UNSUB_SECRET`
3. Compare tokens (timing-safe comparison)
4. If valid, insert into `email_suppressions`
5. Return success/error response

```python
@router.post("/unsubscribe/{token}")
async def unsubscribe(token: str, email: str):
    # Decode and verify token
    # (token contains account_id:email signed with HMAC)
    
    # Insert suppression
    cur.execute("""
        INSERT INTO email_suppressions (account_id, email, reason)
        VALUES (%s, %s, 'unsubscribe')
        ON CONFLICT (account_id, email) DO NOTHING
    """, (account_id, email))
    
    return {"ok": True, "message": "Successfully unsubscribed"}
```

### 8.3 Unsubscribe Link Format

```
https://www.trendyreports.io/api/v1/email/unsubscribe?token={hmac_token}&email={recipient_email}
```

### 8.4 Suppression Checking

Before sending any scheduled email:

```python
# In send_schedule_email()
cur.execute("""
    SELECT email FROM email_suppressions
    WHERE account_id = %s AND email = ANY(%s)
""", (account_id, recipients))

suppressed = [row[0] for row in cur.fetchall()]
filtered_recipients = [r for r in recipients if r not in suppressed]

if not filtered_recipients:
    # All recipients suppressed - don't send
    return (200, "All recipients suppressed")
```

---

## 9. Environment Variables

### 9.1 Worker Services

Required on: `reportscompany-worker-service`, `reportscompany-consumer-bridge`, `markets-report-ticker`

```bash
# SendGrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=reports@trendyreports.io
DEFAULT_FROM_NAME=TrendyReports

# Unsubscribe
EMAIL_UNSUB_SECRET=your_32_char_minimum_secret_here
WEB_BASE=https://www.trendyreports.io
```

### 9.2 API Service

Required on: `reportscompany-api`

```bash
# SendGrid (for branding test emails)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=reports@trendyreports.io
DEFAULT_FROM_NAME=TrendyReports

# Unsubscribe (must match worker)
UNSUBSCRIBE_SECRET=your_32_char_minimum_secret_here
WEB_BASE=https://www.trendyreports.io
```

### 9.3 Variable Descriptions

| Variable | Description | Example |
|----------|-------------|---------|
| `SENDGRID_API_KEY` | SendGrid API key (starts with `SG.`) | `SG.abc123...` |
| `DEFAULT_FROM_EMAIL` | Sender email (must be verified in SendGrid) | `reports@trendyreports.io` |
| `DEFAULT_FROM_NAME` | Default sender name | `TrendyReports` |
| `EMAIL_UNSUB_SECRET` | HMAC secret for unsubscribe tokens | 32+ char random string |
| `WEB_BASE` | Base URL for unsubscribe links | `https://www.trendyreports.io` |

---

## 10. Troubleshooting

### 10.1 Common Issues

#### Email Not Sending

**Symptoms:** Schedule runs complete but no email received

**Check:**
1. `SENDGRID_API_KEY` is set correctly
2. Sender email is verified in SendGrid
3. Check `email_log` table for errors:
   ```sql
   SELECT * FROM email_log 
   WHERE schedule_id = 'xxx' 
   ORDER BY created_at DESC LIMIT 5;
   ```
4. Check if recipient is suppressed:
   ```sql
   SELECT * FROM email_suppressions 
   WHERE email = 'recipient@example.com';
   ```

#### 401 Unauthorized from SendGrid

**Cause:** Invalid or expired API key

**Fix:** 
1. Verify API key in SendGrid dashboard
2. Update `SENDGRID_API_KEY` in Render environment
3. Redeploy service

#### 403 Forbidden from SendGrid

**Cause:** Sender email not verified

**Fix:**
1. Go to SendGrid → Settings → Sender Authentication
2. Verify `DEFAULT_FROM_EMAIL` domain or single sender
3. Wait for DNS propagation if using domain authentication

#### Emails Going to Spam

**Causes:**
- Missing SPF/DKIM/DMARC records
- Poor sender reputation
- Spammy content

**Fix:**
1. Set up domain authentication in SendGrid
2. Add SPF, DKIM, DMARC DNS records
3. Warm up sending volume gradually

### 10.2 Debugging Queries

```sql
-- Recent email sends
SELECT id, to_emails, response_code, status, error, created_at
FROM email_log
ORDER BY created_at DESC
LIMIT 20;

-- Failed emails
SELECT * FROM email_log
WHERE response_code NOT IN (200, 202)
ORDER BY created_at DESC;

-- Suppression list for an account
SELECT email, reason, created_at
FROM email_suppressions
WHERE account_id = 'xxx';

-- Schedule run history
SELECT sr.*, s.name as schedule_name
FROM schedule_runs sr
JOIN schedules s ON sr.schedule_id = s.id
WHERE s.account_id = 'xxx'
ORDER BY sr.created_at DESC;
```

### 10.3 Testing Email Flow

1. **Create test schedule:**
   - Set yourself as recipient
   - Use short interval for testing
   - Verify email arrives

2. **Test unsubscribe:**
   - Click unsubscribe link in email
   - Verify `email_suppressions` entry created
   - Trigger another schedule run
   - Verify no email sent (check `email_log` for "suppressed")

3. **Test branding:**
   - Go to `/app/branding` as affiliate
   - Use "Send Test Email" feature
   - Verify branding appears correctly

---

## Appendix: File Locations

| Component | Path |
|-----------|------|
| SendGrid Provider | `apps/worker/src/worker/email/providers/sendgrid.py` |
| Email Orchestrator | `apps/worker/src/worker/email/send.py` |
| Email Templates | `apps/worker/src/worker/email/template.py` |
| Worker Tasks | `apps/worker/src/worker/tasks.py` |
| Branding Tools API | `apps/api/src/api/routes/branding_tools.py` |
| Unsubscribe API | `apps/api/src/api/routes/email.py` |
| Branding Service | `apps/api/src/api/services/branding.py` |
| Test Email Proxy | `apps/web/app/api/proxy/v1/branding/test-email/route.ts` |

---

*End of Email System Documentation*

