# TrendyReports - Property Reports Feature

## Complete Documentation

**Version:** 1.0  
**Date:** January 9, 2026  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Services](#services)
6. [Frontend Pages](#frontend-pages)
7. [Environment Variables](#environment-variables)
8. [User Flows](#user-flows)
9. [Admin Features](#admin-features)
10. [Security & Anti-Spam](#security--anti-spam)
11. [Deployment Checklist](#deployment-checklist)
12. [Troubleshooting](#troubleshooting)

---

## Overview

Property Reports extends TrendyReports with single-property CMA-style reports for real estate agents. This feature was integrated from Modern Agent (MyListingPitch) into the existing TrendyReports platform.

### Key Features

- **Property Lookup**: SiteX Pro API integration for property data (owner, APN, legal description, tax info)
- **PDF Reports**: Automated generation with customizable themes
- **QR Code Lead Capture**: Scannable QR codes link to landing pages for lead generation
- **SMS Notifications**: Instant alerts when leads are captured
- **Landing Page Controls**: Expiration, max leads, password protection

### Why Integrated vs Standalone

| Factor | Integrated | Standalone |
|--------|------------|------------|
| Development time | 2-3 weeks | 8+ weeks |
| Infrastructure reuse | 70-80% | 0% |
| Auth/billing | Existing | Build new |
| Deployment | Single codebase | New deployment |
| Cross-sell | Built-in | Separate |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  Next.js (apps/web)                                             │
├─────────────────────────────────────────────────────────────────┤
│  /app/property/new          → Report Creation Wizard (4 steps)  │
│  /app/property              → Reports List                      │
│  /app/property/[id]         → Report Detail                     │
│  /app/property/[id]/settings→ Landing Page Controls             │
│  /app/leads                 → Leads Management                  │
│  /p/[code]                  → Public Landing Page               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           API                                   │
│  FastAPI (apps/api)                                             │
├─────────────────────────────────────────────────────────────────┤
│  /v1/property/*             → Property & Report endpoints       │
│  /v1/leads/*                → Lead management                   │
│  /v1/admin/*                → Admin endpoints                   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│     SiteX       │ │    SimplyRETS   │ │     Twilio      │
│  Property Data  │ │   Comparables   │ │      SMS        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         WORKER                                  │
│  Celery (apps/worker)                                           │
├─────────────────────────────────────────────────────────────────┤
│  generate_property_report   → PDF generation task               │
│  PropertyReportBuilder      → Jinja2 template rendering         │
│  PDFShift                   → HTML to PDF conversion            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        STORAGE                                  │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL                 → Reports, Leads, SMS Logs          │
│  Cloudflare R2              → PDFs, QR Codes                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Migration 0034: Property Reports

```sql
-- Main tables
property_reports          -- Property report records
leads                     -- Captured leads
blocked_ips               -- IP blocklist for spam prevention
lead_rate_limits          -- Rate limiting tracking

-- Extended tables
accounts.sms_credits      -- SMS credit balance
plans.property_reports_per_month
plans.sms_credits_per_month
plans.lead_capture_enabled
```

### Migration 0035: SMS Logs

```sql
sms_logs                  -- SMS message history
```

### property_reports Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| account_id | UUID | FK to accounts |
| user_id | UUID | FK to users |
| report_type | VARCHAR | 'seller', 'buyer' |
| theme | INTEGER | 1-5 |
| accent_color | VARCHAR | Hex color (#2563eb) |
| property_address | VARCHAR | Full address |
| property_city | VARCHAR | City |
| property_state | VARCHAR | State |
| property_zip | VARCHAR | ZIP code |
| property_county | VARCHAR | County |
| apn | VARCHAR | Assessor's Parcel Number |
| owner_name | VARCHAR | Property owner |
| legal_description | TEXT | Legal description |
| sitex_data | JSONB | Cached SiteX response |
| comparables | JSONB | Selected comparables |
| pdf_url | VARCHAR | R2 URL to PDF |
| status | VARCHAR | draft/processing/complete/failed |
| error_message | TEXT | Error details if failed |
| short_code | VARCHAR | Unique code for QR/landing page |
| qr_code_url | VARCHAR | R2 URL to QR image |
| view_count | INTEGER | Landing page views |
| unique_visitors | INTEGER | Unique visitors |
| is_active | BOOLEAN | Landing page enabled |
| expires_at | TIMESTAMPTZ | Auto-disable date |
| max_leads | INTEGER | Lead cap |
| access_code | VARCHAR | Password protection |
| created_at | TIMESTAMPTZ | Created timestamp |
| updated_at | TIMESTAMPTZ | Updated timestamp |

### leads Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| account_id | UUID | FK to accounts |
| property_report_id | UUID | FK to property_reports |
| name | VARCHAR | Lead name |
| email | VARCHAR | Lead email |
| phone | VARCHAR | Lead phone |
| message | TEXT | Optional message |
| source | VARCHAR | qr_scan, direct_link |
| consent_given | BOOLEAN | GDPR consent |
| status | VARCHAR | new/contacted/qualified/converted |
| notes | TEXT | Agent notes |
| ip_address | VARCHAR | Submission IP |
| user_agent | TEXT | Browser info |
| sms_sent_at | TIMESTAMPTZ | When SMS was sent |
| created_at | TIMESTAMPTZ | Created timestamp |

### sms_logs Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| account_id | UUID | FK to accounts |
| lead_id | UUID | FK to leads |
| to_phone | VARCHAR | Recipient |
| from_phone | VARCHAR | Twilio number |
| message | TEXT | Message content |
| status | VARCHAR | sent/delivered/failed |
| twilio_sid | VARCHAR | Twilio message ID |
| error_message | TEXT | Error if failed |
| created_at | TIMESTAMPTZ | Sent timestamp |

---

## API Endpoints

### Property Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /v1/property/search | Yes | Search property by address |
| POST | /v1/property/search-by-apn | Yes | Search by FIPS + APN |
| POST | /v1/property/comparables | Yes | Get comparable properties |
| POST | /v1/property/reports | Yes | Create new report |
| GET | /v1/property/reports | Yes | List user's reports |
| GET | /v1/property/reports/{id} | Yes | Get report details |
| DELETE | /v1/property/reports/{id} | Yes | Delete report |
| GET | /v1/property/reports/{id}/settings | Yes | Get landing page settings |
| PATCH | /v1/property/reports/{id}/settings | Yes | Update settings |
| POST | /v1/property/reports/{id}/regenerate-qr | Yes | New QR code |
| GET | /v1/property/public/{short_code} | No | Public landing page data |

### Lead Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /v1/leads/capture | No | Submit lead (public) |
| GET | /v1/leads | Yes | List leads |
| GET | /v1/leads/{id} | Yes | Get lead details |
| PATCH | /v1/leads/{id} | Yes | Update status/notes |
| DELETE | /v1/leads/{id} | Yes | Delete lead |
| GET | /v1/leads/export/csv | Yes | Export CSV |

### Admin Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /v1/admin/property-reports | Admin | List all reports |
| GET | /v1/admin/property-reports/{id} | Admin | Report details |
| DELETE | /v1/admin/property-reports/{id} | Admin | Delete report |
| POST | /v1/admin/property-reports/{id}/retry | Admin | Retry PDF |
| GET | /v1/admin/leads | Admin | List all leads |
| GET | /v1/admin/leads/export | Admin | Export all CSV |
| GET | /v1/admin/sms/credits | Admin | Credit balances |
| POST | /v1/admin/sms/credits | Admin | Adjust credits |
| GET | /v1/admin/sms/logs | Admin | SMS history |
| GET | /v1/admin/blocked-ips | Admin | Blocked IPs |
| POST | /v1/admin/blocked-ips | Admin | Block IP |
| DELETE | /v1/admin/blocked-ips/{id} | Admin | Unblock IP |

---

## Services

### SiteX Service

**File:** `apps/api/src/api/services/sitex.py`

Property data lookup via ICE SiteX Pro API.

```python
# Usage
from api.services.sitex import lookup_property, lookup_property_by_apn

# By address
result = await lookup_property("714 Vine St", "Anaheim, CA 92805")

# By APN (more precise)
result = await lookup_property_by_apn("06059", "035-202-10")
```

**Features:**
- OAuth2 token management (auto-refresh)
- In-memory caching (24-hour TTL)
- Multi-match handling
- Correct field mappings (owner, legal description, county)

**Response Fields:**
- full_address, street, city, state, zip_code, county
- apn, fips, owner_name, secondary_owner
- legal_description, property_type
- bedrooms, bathrooms, sqft, lot_size, year_built
- assessed_value, tax_amount, land_value, improvement_value

### QR Code Service

**File:** `apps/api/src/api/services/qr_service.py`

```python
from api.services.qr_service import generate_qr_code, generate_short_code

# Generate QR code
qr_url = await generate_qr_code(
    url="https://trendy.com/p/abc123",
    color="#2563eb",
    report_id="uuid-here"
)

# Generate short code
code = generate_short_code(length=8)  # e.g., "x7k2m9p4"
```

**Features:**
- Styled QR codes (rounded modules)
- Custom colors
- R2 upload
- Fallback to external service

### Twilio SMS Service

**File:** `apps/api/src/api/services/twilio_sms.py`

```python
from api.services.twilio_sms import send_lead_notification_sms

result = await send_lead_notification_sms(
    to_phone="+14155551234",
    lead_name="John Smith",
    property_address="123 Main St, Anytown, CA"
)
```

**Features:**
- E.164 phone formatting
- Lead notification templates
- Uses httpx (no SDK dependency)

### Property Report Builder

**File:** `apps/worker/src/worker/property_builder.py`

Jinja2-based HTML generation for PDF conversion.

**Templates:**
- `seller_base.jinja2` - Base HTML with theme CSS
- `seller_cover.jinja2` - Cover page
- `seller_property_details.jinja2` - Property details

---

## Frontend Pages

### Agent/User Pages

| Path | Component | Description |
|------|-----------|-------------|
| /app/property | page.tsx | Reports list with stats |
| /app/property/new | page.tsx | 4-step creation wizard |
| /app/property/[id] | page.tsx | Report detail view |
| /app/property/[id]/settings | page.tsx | Landing page controls |
| /app/leads | page.tsx | Leads management |
| /p/[code] | page.tsx | Public landing page |

### Admin Pages

| Path | Component | Description |
|------|-----------|-------------|
| /admin/property-reports | page.tsx | All reports (cross-account) |
| /admin/property-reports/[id] | page.tsx | Report detail + raw data |
| /admin/leads | page.tsx | All leads (cross-account) |
| /admin/sms | page.tsx | SMS credits + logs |
| /admin/blocked-ips | page.tsx | IP blocklist management |

### Report Creation Wizard

**Step 1: Find Property**
- Address input with search
- Displays: owner, beds/baths, sqft, year built
- SiteX API lookup

**Step 2: Select Comparables**
- Two-column picker (available ↔ selected)
- 4-8 comparables required
- Shows: address, price, beds/baths, distance
- Optional map modal

**Step 3: Choose Theme**
- 5 preset themes
- Accent color picker
- Live preview

**Step 4: Review & Generate**
- Summary of selections
- Generate button
- Progress indicator
- Auto-redirect on completion

---

## Environment Variables

### Required for API + Worker

```bash
# SiteX Pro API
SITEX_BASE_URL=https://api.bkiconnect.com  # Production
# SITEX_BASE_URL=https://api.uat.bkitest.com  # UAT
SITEX_CLIENT_ID=your_client_id
SITEX_CLIENT_SECRET=your_client_secret
SITEX_FEED_ID=100001

# Twilio SMS
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890
```

### Where to Configure

| Service | Location |
|---------|----------|
| API | Render → API service → Environment |
| Worker | Render → Worker service → Environment |
| Local | .env file in project root |

---

## User Flows

### Creating a Property Report

```
1. Agent clicks "Create Report" → /app/property/new
2. Enters address → SiteX lookup → Property data displayed
3. Clicks "Continue" → Comparables fetched from SimplyRETS
4. Selects 4-8 comparables → Clicks "Continue"
5. Chooses theme + accent color → Clicks "Continue"
6. Reviews summary → Clicks "Generate Report"
7. API creates record (status=draft)
8. QR code generated and uploaded
9. Celery task queued
10. Frontend polls for completion
11. Worker generates PDF via Jinja2 + PDFShift
12. PDF uploaded to R2
13. Status updated to "complete"
14. Agent redirected to report detail page
```

### Lead Capture Flow

```
1. Prospect scans QR code on report/flyer
2. Opens landing page /p/{short_code}
3. Sees property info + agent info
4. Fills out lead form (name, email, phone)
5. Checks consent checkbox
6. Submits form

Backend checks:
- Honeypot field (bot detection)
- Landing page active?
- Not expired?
- Under max_leads?
- Access code correct?
- IP not blocked?
- Rate limit OK? (5/hour/IP)
- Duplicate email?

If all pass:
7. Lead saved to database
8. View count incremented
9. SMS sent to agent (if credits available)
10. SMS logged
11. Credits decremented
12. Success response to prospect
```

---

## Admin Features

### Property Reports Management

- View all reports across accounts
- Filter by status, account, date
- Retry failed PDF generation
- Delete reports
- View raw SiteX data
- Toggle landing page active/inactive

### Leads Management

- View all leads across accounts
- Export all as CSV
- Filter by status, account, date
- Delete leads

### SMS Management

- View account credit balances
- Add/subtract credits manually
- View SMS send history
- Filter by status (sent/failed)
- Debug failed messages

### IP Blocking

- View blocked IPs
- Add IP with reason + optional expiry
- Remove blocks
- Cleanup expired blocks

---

## Security & Anti-Spam

### Landing Page Controls

| Control | Description |
|---------|-------------|
| is_active | Kill switch for landing page |
| expires_at | Auto-disable after date |
| max_leads | Cap leads per report |
| access_code | Password protection |

### Lead Capture Protection

| Layer | Description |
|-------|-------------|
| Honeypot | Hidden field catches bots |
| Rate Limiting | 5 submissions per hour per IP |
| IP Blocking | Admin can block abusive IPs |
| Duplicate Check | Same email can't submit twice |
| Active Check | Inactive pages return 410 |
| Expiry Check | Expired pages return 410 |
| Max Leads Check | Over-limit pages return 410 |

### Implementation

```python
# Lead capture flow (simplified)
async def capture_lead(request):
    # 1. Honeypot check (silent fail)
    if request.website:  # hidden field
        return {"success": True}  # Fake success
    
    # 2. Get report
    report = await get_report_by_short_code(request.short_code)
    
    # 3. Active check
    if not report.is_active:
        raise HTTPException(410, "Page not available")
    
    # 4. Expiry check
    if report.expires_at and report.expires_at < now():
        raise HTTPException(410, "Page expired")
    
    # 5. Max leads check
    if report.max_leads and lead_count >= report.max_leads:
        raise HTTPException(410, "No longer accepting submissions")
    
    # 6. Access code check
    if report.access_code and request.access_code != report.access_code:
        raise HTTPException(403, "Invalid access code")
    
    # 7. IP block check
    if await is_ip_blocked(client_ip):
        raise HTTPException(403, "Access denied")
    
    # 8. Rate limit check
    if await get_recent_submissions(client_ip) >= 5:
        raise HTTPException(429, "Too many submissions")
    
    # 9. Duplicate check (silent success)
    if await email_exists_for_report(request.email, report.id):
        return {"success": True}
    
    # 10. Create lead
    lead = await create_lead(...)
    
    # 11. Send SMS if credits available
    if account.sms_credits > 0 and user.phone:
        await send_notification(...)
        await decrement_credits(account)
    
    return {"success": True}
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Environment variables set (API + Worker)
- [ ] Database migrations applied (0034, 0035)
- [ ] SiteX credentials tested
- [ ] Twilio credentials tested
- [ ] R2 bucket accessible

### Deployment Steps

1. **Deploy API**
   ```bash
   # Render auto-deploys on push, or manual deploy
   ```

2. **Deploy Worker**
   ```bash
   # Ensure worker restarts to pick up new tasks
   ```

3. **Run Migrations**
   ```bash
   # Should auto-run, or manually:
   python db/migrations/run_migrations.py
   ```

4. **Verify Deployment**
   ```bash
   # Test health
   curl https://api.trendy.com/health
   
   # Test SiteX
   curl -X POST https://api.trendy.com/v1/property/search \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"address": "714 Vine St", "city_state_zip": "Anaheim, CA 92805"}'
   ```

### Post-Deployment

- [ ] Create test property report
- [ ] Verify PDF generates
- [ ] Test QR code scanning
- [ ] Submit test lead
- [ ] Verify SMS received
- [ ] Check admin pages work

---

## Troubleshooting

### SiteX Issues

**Problem:** Empty owner_name or address fields

**Solution:** Check field mappings in `sitex.py`. SiteX feeds vary - some use nested objects (OwnerInformation), others use flat fields (PrimaryOwnerName).

**Problem:** 401 Unauthorized

**Solution:** Token expired or credentials wrong. Check SITEX_CLIENT_ID and SITEX_CLIENT_SECRET.

### PDF Generation Issues

**Problem:** Status stuck on "processing"

**Solution:** 
1. Check Celery worker logs
2. Verify worker has SITEX_* env vars
3. Check PDFShift API status
4. Try retry via admin panel

**Problem:** PDF missing content

**Solution:** Check Jinja2 templates in `apps/worker/src/worker/templates/property/`

### SMS Issues

**Problem:** SMS not sending

**Solution:**
1. Check account has sms_credits > 0
2. Verify agent has phone number in profile
3. Check Twilio credentials
4. Review sms_logs for error messages

**Problem:** SMS shows "failed" status

**Solution:** Check error_message in sms_logs. Common issues:
- Invalid phone format
- Twilio account suspended
- Number blocked by carrier

### Lead Capture Issues

**Problem:** Getting 429 Too Many Requests

**Solution:** Rate limit hit. Wait 1 hour or have admin clear lead_rate_limits table.

**Problem:** Getting 410 Gone

**Solution:** Landing page is inactive, expired, or over max_leads. Check report settings.

---

## API Response Examples

### Property Search Response

```json
{
  "success": true,
  "data": {
    "full_address": "714 N VINE ST, ANAHEIM, CA 92805",
    "street": "714 N VINE ST",
    "city": "ANAHEIM",
    "state": "CA",
    "zip_code": "92805",
    "county": "ORANGE",
    "apn": "035-202-10",
    "fips": "06059",
    "owner_name": "CUENCA, JESUS; CUENCAS LIVING TRUST",
    "legal_description": "N TR 1618 BLK LOT 17",
    "bedrooms": 3,
    "bathrooms": 1.0,
    "sqft": 1112,
    "lot_size": 6113,
    "year_built": 1954,
    "assessed_value": 516112,
    "source": "sitex"
  }
}
```

### Create Report Response

```json
{
  "success": true,
  "report": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "draft",
    "short_code": "x7k2m9p4",
    "qr_code_url": "https://r2.trendy.com/qr-codes/550e8400.png",
    "landing_page_url": "https://trendy.com/p/x7k2m9p4"
  }
}
```

### Lead Capture Response

```json
{
  "success": true,
  "message": "Thank you! The agent will be in touch soon."
}
```

---

## Support

For issues or questions:
- Check this documentation first
- Review Troubleshooting section
- Check application logs in Render dashboard
- Contact Jerry for escalation

---

*Documentation generated January 9, 2026*
