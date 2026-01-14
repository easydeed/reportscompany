# TrendyReports - Property Reports Feature

## Complete Documentation

**Version:** 2.0  
**Date:** January 13, 2026  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Services](#services)
6. [PDF Generation System](#pdf-generation-system)
7. [Frontend Pages](#frontend-pages)
8. [Environment Variables](#environment-variables)
9. [User Flows](#user-flows)
10. [Admin Features](#admin-features)
11. [Security & Anti-Spam](#security--anti-spam)
12. [Deployment Checklist](#deployment-checklist)
13. [Troubleshooting](#troubleshooting)

---

## Overview

Property Reports extends TrendyReports with single-property CMA-style reports for real estate agents. This feature provides comprehensive seller/buyer reports with comparables analysis and lead capture capabilities.

### Key Features

- **Property Lookup**: SiteX Pro API integration for property data (owner, APN, legal description, tax info)
- **Comparables**: SimplyRETS integration for comparable property selection
- **PDF Reports**: Automated generation with 5 customizable themes via PDFShift
- **QR Code Lead Capture**: Scannable QR codes link to landing pages for lead generation
- **SMS Notifications**: Instant alerts when leads are captured
- **Landing Page Controls**: Expiration, max leads, password protection

### Available Themes

| Theme ID | Name | Description | Pages |
|----------|------|-------------|-------|
| 1 | Classic | Traditional professional layout | 20 |
| 2 | Modern | Clean contemporary design | 21 |
| 3 | Elegant | Sophisticated premium feel | 18 |
| 4 | **Teal** | Montserrat font, teal/navy scheme | 7 |
| 5 | Bold | High-impact visual design | 8 |

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
│  Cloudflare R2              → PDFs, QR Codes, Static Assets     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Migrations

| Migration | Description |
|-----------|-------------|
| 0034 | Property reports tables, leads, blocked IPs, rate limits |
| 0035 | SMS logs table |
| 0036 | `selected_pages` JSONB column on property_reports |

### property_reports Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| account_id | UUID | FK to accounts |
| user_id | UUID | FK to users |
| report_type | VARCHAR | 'seller', 'buyer' |
| theme | INTEGER | 1-5 |
| accent_color | VARCHAR | Hex color (#2563eb) |
| property_address | VARCHAR | Street address only |
| property_city | VARCHAR | City |
| property_state | VARCHAR | State |
| property_zip | VARCHAR | ZIP code |
| property_county | VARCHAR | County |
| apn | VARCHAR | Assessor's Parcel Number |
| owner_name | VARCHAR | Property owner |
| legal_description | TEXT | Legal description |
| sitex_data | JSONB | Cached SiteX response |
| comparables | JSONB | **Full comparable objects** (not just IDs) |
| selected_pages | JSONB | Array of page IDs to include |
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

### Comparables Data Structure

The `comparables` column stores **full comparable objects**, not just MLS IDs:

```json
[
  {
    "id": "231377504",
    "address": "1889 BONITA AVE, LA VERNE, CA",
    "lat": 34.1234,
    "lng": -117.7654,
    "photo_url": "https://...",
    "price": 631500,
    "close_price": 631500,
    "bedrooms": 2,
    "bathrooms": 1,
    "sqft": 940,
    "year_built": 1952,
    "distance_miles": 0.5,
    "days_on_market": 14
  }
]
```

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

### Create Report Payload

```json
{
  "report_type": "seller",
  "theme": 4,
  "accent_color": "#34d1c3",
  "property_address": "1358 5TH ST",
  "property_city": "LA VERNE",
  "property_state": "CA",
  "property_zip": "91750",
  "apn": "8381-021-001",
  "owner_name": "HERNANDEZ GERARDO J",
  "comparables": [
    {
      "id": "231377504",
      "address": "1889 BONITA AVE, LA VERNE, CA",
      "lat": 34.1234,
      "lng": -117.7654,
      "photo_url": "https://...",
      "price": 631500,
      "bedrooms": 2,
      "bathrooms": 1,
      "sqft": 940,
      "year_built": 1952,
      "distance_miles": 0.5
    }
  ],
  "selected_pages": ["cover", "contents", "aerial", "property", "area_sales", "comparables", "range"],
  "sitex_data": { }
}
```

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
from api.services.sitex import lookup_property, lookup_property_by_apn

# By address
result = await lookup_property("714 Vine St", "Anaheim, CA 92805")

# By APN (more precise)
result = await lookup_property_by_apn("06059", "035-202-10")
```

**Response Fields:**
- full_address, street, city, state, zip_code, county
- apn, fips, owner_name, secondary_owner
- legal_description, property_type
- bedrooms, bathrooms, sqft, lot_size, year_built
- assessed_value, tax_amount, land_value, improvement_value
- latitude, longitude

### QR Code Service

**File:** `apps/api/src/api/services/qr_service.py`

```python
from api.services.qr_service import generate_qr_code, generate_short_code

qr_url = await generate_qr_code(
    url="https://trendy.com/p/abc123",
    color="#2563eb",
    report_id="uuid-here"
)

code = generate_short_code(length=8)  # e.g., "x7k2m9p4"
```

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

---

## PDF Generation System

### Overview

Property Reports use a **Jinja2 → HTML → PDFShift → PDF** pipeline.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Report Data    │ ──▶ │ PropertyReport  │ ──▶ │    PDFShift     │
│  (from DB)      │     │    Builder      │     │    API          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                              ▼                        ▼
                        ┌───────────┐           ┌───────────┐
                        │   HTML    │           │    PDF    │
                        │ (Jinja2)  │           │   (R2)    │
                        └───────────┘           └───────────┘
```

### PropertyReportBuilder

**File:** `apps/worker/src/worker/property_builder.py`

The builder transforms raw report data into structured contexts for Jinja2 templates.

#### Custom Jinja2 Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `format_currency` | Full currency format | 428248 → $428,248 |
| `format_currency_short` | Short format | 470000 → $470k, 1200000 → $1.2M |
| `format_number` | Number with commas | 6155 → 6,155 |

#### Context Builders

| Method | Returns | Description |
|--------|---------|-------------|
| `_build_property_context()` | dict | Property details from sitex_data |
| `_build_agent_context()` | dict | Agent info with formatted license/address |
| `_build_comparables_context()` | list | Normalized comparable data with map URLs |
| `_build_stats_context()` | dict | Aggregated stats (PIQ, low, medium, high) |
| `_build_images_context()` | dict | Hero image and aerial map URLs |

### Template Data Structure

The Teal theme template (and future themes) expects this data structure:

```python
{
    # Property Information
    "property": {
        "street_address": "1358 5TH ST",
        "city": "LA VERNE",
        "state": "CA",
        "zip_code": "91750",
        "full_address": "1358 5TH ST, LA VERNE, CA 91750",
        "owner_name": "HERNANDEZ GERARDO J",
        "secondary_owner": "MENDOZA YESSICA S",
        "mailing_address": "1358 5TH ST, LA VERNE, CA 91750",
        "apn": "8381-021-001",
        "county": "LOS ANGELES",
        "census_tract": "4089.00",
        "housing_tract": "6654",
        "lot_number": "44",
        "page_grid": "E2",
        "legal_description": "LOT:44 TR#:6654 TRACT NO 6654 LOT 44",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 786,
        "lot_size": 6155,
        "year_built": 1949,
        "garage": "-",
        "fireplace": "-",
        "pool": False,
        "zoning": "LVPR4.5D*",
        "property_type": "Single Family Residential",
        "use_code": "Single Family Residential",
        "assessed_value": 428248,
        "tax_amount": 5198,
        "land_value": 337378,
        "improvement_value": 90870,
        "tax_status": "Current",
        "tax_rate_area": "5-283%",
        "tax_year": 2024,
        "latitude": 34.1234,
        "longitude": -117.7654,
    },
    
    # Agent Information
    "agent": {
        "name": "ZOE NOELLE",
        "title": "Realtor",
        "license": "CA BRE#0123456789",
        "phone": "2133097286",
        "email": "info@modernagent.io",
        "address": "985 Success Ave, Success, CA 91252",
        "photo_url": "https://example.com/agent.jpg",
        "company_name": "Flare",
    },
    
    # Comparables (up to 4 for Teal theme)
    "comparables": [
        {
            "address": "1889 BONITA AVE LA VERNE",
            "sale_price": 631500,
            "sold_date": "5/10/2023",
            "distance_miles": 0.5,
            "sqft": 940,
            "price_per_sqft": 671,
            "bedrooms": 2,
            "bathrooms": 1,
            "year_built": 1952,
            "lot_size": 5246,
            "pool": False,
            "map_image_url": "https://maps.googleapis.com/...",
        },
        # ... up to 3 more
    ],
    
    # Aggregated Statistics
    "stats": {
        "total_comps": 4,
        "avg_sqft": 830,
        "avg_beds": 2,
        "avg_baths": 1,
        "price_low": 470000,
        "price_high": 635000,
        
        # Area Sales Analysis (PIQ = Property In Question)
        "piq": {
            "distance": 0,
            "sqft": 786,
            "price_per_sqft": 469,
            "year_built": 1949,
            "lot_size": 6155,
            "bedrooms": 2,
            "bathrooms": 1,
            "stories": 0,
            "pools": 0,
            "price": 369000,
        },
        "low": { ... },
        "medium": { ... },
        "high": { ... },
    },
    
    # Image URLs
    "images": {
        "hero": "https://example.com/hero-house.jpg",
        "aerial_map": "https://maps.googleapis.com/...",
    },
}
```

### Templates

**Location:** `apps/worker/src/worker/templates/property/`

| Theme | Template File | Pages |
|-------|---------------|-------|
| 4 (Teal) | `teal_report.jinja2` | 7 (self-contained) |

#### Teal Theme Pages

1. **Cover** - Property address, agent signature
2. **Contents** - Table of contents
3. **Aerial View** - Google Static Map
4. **Property Info** - 3 sections of property details
5. **Area Sales Analysis** - Bar chart + PIQ/Low/Med/High table
6. **Sales Comparables** - 2x2 grid of comp cards with maps
7. **Range of Sales** - Summary stats with price slider

### Google Static Maps

The builder generates Google Static Maps URLs for:
- Aerial view of subject property
- Individual maps for each comparable

```python
def _get_static_map_url(
    self, 
    lat: float, 
    lng: float, 
    zoom: int = 15, 
    size: str = "800x600"
) -> str:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lng}"
        f"&zoom={zoom}"
        f"&size={size}"
        f"&maptype=roadmap"
        f"&markers=color:0x1e3a5f%7C{lat},{lng}"
        f"&key={api_key}"
    )
```

### Data Flow: Frontend → API → Worker

1. **Frontend** sends full comparable objects (not just IDs)
2. **API** stores comparables as JSONB in `property_reports.comparables`
3. **Worker** reads comparables and normalizes field names:

| Frontend Field | Worker Handles As |
|----------------|-------------------|
| `lat` | `latitude` or `lat` |
| `lng` | `longitude` or `lng` |
| `photo_url` | `image_url` or `photo_url` |
| `distance_miles` | `distance` or `distance_miles` |
| `price` | `price` or `close_price` |

---

## Frontend Pages

### Agent/User Pages

| Path | Description |
|------|-------------|
| /app/property | Reports list with stats |
| /app/property/new | 4-step creation wizard |
| /app/property/[id] | Report detail view |
| /app/property/[id]/settings | Landing page controls |
| /app/leads | Leads management |
| /p/[code] | Public landing page |

### Admin Pages

| Path | Description |
|------|-------------|
| /admin/property-reports | All reports (cross-account) |
| /admin/property-reports/[id] | Report detail + raw data |
| /admin/leads | All leads (cross-account) |
| /admin/sms | SMS credits + logs |
| /admin/blocked-ips | IP blocklist management |

### Report Creation Wizard

**File:** `apps/web/app/app/property/new/page.tsx`

The wizard uses dynamic import with `ssr: false` for client-side rendering.

#### Step 1: Find Property
- Google Places Autocomplete for address input
- "Search" button triggers SiteX lookup
- Displays: owner, beds/baths, sqft, year built, APN, county

#### Step 2: Select Comparables
- Auto-loads comparables based on property location
- Two-column picker (available ↔ selected)
- 4-8 comparables required
- Shows: address, price, beds/baths, distance, photo
- Map modal for geographic view

#### Step 3: Choose Theme
- 5 theme cards with preview images
- Accent color picker (12 preset colors)
- Page selection toggles
- "Preview" modal shows all pages in theme

#### Step 4: Review & Generate
- Summary of all selections
- Property details display
- Generate button
- Progress indicator with stages
- Auto-redirect on completion

### Key Frontend Files

| File | Purpose |
|------|---------|
| `apps/web/app/app/property/new/page.tsx` | Wizard orchestration, API submission |
| `apps/web/lib/wizard-types.ts` | TypeScript types, themes, pages config |
| `apps/web/components/property/ComparablesPicker.tsx` | Step 2 comparable selection |
| `apps/web/components/property/ComparablesMapModal.tsx` | Map view of comparables |
| `apps/web/components/property/ThemeSelector.tsx` | Step 3 theme/page selection |
| `apps/web/lib/property-report-assets.ts` | R2 asset URLs manifest |

---

## Environment Variables

### Required for API + Worker

```bash
# SiteX Pro API
SITEX_BASE_URL=https://api.bkiconnect.com
SITEX_CLIENT_ID=your_client_id
SITEX_CLIENT_SECRET=your_client_secret
SITEX_FEED_ID=100001

# Twilio SMS
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890

# Google Maps (for static maps in PDFs)
GOOGLE_MAPS_API_KEY=AIzaSy...

# PDFShift
PDFSHIFT_API_KEY=sk_...
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
2. Enters address via Google Places → Clicks "Search"
3. SiteX lookup → Property data displayed
4. Clicks "Continue" → Comparables auto-loaded from SimplyRETS
5. Selects 4-8 comparables → Clicks "Continue"
6. Chooses theme + accent color + pages → Clicks "Continue"
7. Reviews summary → Clicks "Generate Report"
8. API creates record (status=draft)
9. QR code generated and uploaded
10. Celery task queued
11. Frontend polls for completion
12. Worker:
    a. Builds template contexts
    b. Renders Jinja2 template to HTML
    c. Sends to PDFShift for conversion
    d. Uploads PDF to R2
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

---

## Deployment Checklist

### Pre-Deployment

- [ ] Environment variables set (API + Worker)
- [ ] Database migrations applied (0034, 0035, 0036)
- [ ] SiteX credentials tested
- [ ] Twilio credentials tested
- [ ] Google Maps API key set
- [ ] PDFShift API key set
- [ ] R2 bucket accessible

### Post-Deployment

- [ ] Create test property report
- [ ] Verify PDF generates with correct template
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
1. Check Celery worker logs on Render
2. Verify worker has all required env vars
3. Check PDFShift API status
4. Try retry via admin panel

**Problem:** PDF missing content / empty pages

**Solution:** 
1. Check template exists in `apps/worker/src/worker/templates/property/`
2. Verify data structure matches template expectations
3. Check Jinja2 filters are registered

**Problem:** Comparables not rendering

**Solution:**
1. Verify `comparables` column contains full objects (not just IDs)
2. Check field name normalization in `_build_comparables_context()`
3. Frontend sends: `lat`, `lng`, `photo_url`, `distance_miles`
4. Worker handles: `latitude`/`lat`, `longitude`/`lng`, `image_url`/`photo_url`, `distance`/`distance_miles`

**Problem:** Maps not showing

**Solution:**
1. Verify GOOGLE_MAPS_API_KEY is set in Worker environment
2. Check API key has Static Maps API enabled
3. Verify lat/lng coordinates are present in data

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
    "latitude": 33.8369,
    "longitude": -117.9111,
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

*Documentation updated January 13, 2026*
