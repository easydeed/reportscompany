# TrendyReports — Project Overview

**A comprehensive real estate market reporting SaaS platform**

---

## Report Types

TrendyReports offers **8 distinct market report types** plus **property-specific reports** to cover all real estate marketing needs:

### Market Reports

| Report Type | Description | Use Case |
|-------------|-------------|----------|
| **Market Snapshot** | Complete overview of current market conditions including active, pending, and closed listings | Monthly market updates for clients |
| **New Listings** | Recently listed properties in a specific area | Weekly prospecting and buyer alerts |
| **Inventory Report** | Available properties and market supply analysis | Market trend analysis |
| **Closed Sales** | Recently sold properties with price trends | Comparative market analysis |
| **Price Bands** | Market segmentation by price ranges | Buyer/seller price positioning |
| **Open Houses** | Upcoming open house schedule | Weekend marketing |
| **New Listings Gallery** | Photo-rich gallery of new listings | Visual marketing for social media |
| **Featured Listings** | Curated showcase of featured properties | Agent listing promotions |

### Property Reports (Seller Reports)

Individual property reports with **5 design templates**:

| Template | Style |
|----------|-------|
| **Bold** | High-contrast, impactful design |
| **Classic** | Traditional, timeless layout |
| **Elegant** | Sophisticated, refined aesthetic |
| **Modern** | Clean, contemporary look |
| **Teal** | Vibrant, professional style |

### Report Filtering Options

- **Area Selection**: City, ZIP codes, or custom polygon
- **Property Types**: Residential, Condo, Multi-Family, Land, Commercial
- **Lookback Period**: 7, 14, 30, 60, or 90 days
- **Price Range**: Min/max price filtering
- **Beds/Baths**: Minimum bedroom and bathroom requirements

---

## External Integrations

### Data & Content

| Integration | Purpose | Authentication |
|-------------|---------|----------------|
| **SimplyRETS** | Live MLS property data (listings, photos, details) | HTTP Basic Auth |
| **OpenAI GPT-4o-mini** | AI-generated market insights for email content | API Key |
| **Google Places** | Address autocomplete for lead capture forms | API Key |

### Communications

| Integration | Purpose | Features |
|-------------|---------|----------|
| **Resend** | Transactional email delivery | HTML templates, delivery tracking |
| **Twilio** | SMS notifications for lead capture | Consumer reports, agent alerts |

### Payments & Billing

| Integration | Purpose | Features |
|-------------|---------|----------|
| **Stripe** | Subscription billing and payments | Checkout, Portal, Webhooks |

### Storage & Generation

| Integration | Purpose | Details |
|-------------|---------|---------|
| **Cloudflare R2** | File storage (PDFs, images) | S3-compatible, presigned URLs |
| **PDFShift** | PDF generation (production) | HTML-to-PDF API |
| **Playwright** | PDF generation (local dev) | Chromium-based rendering |
| **QRCode** | QR code generation for mobile reports | Styled with rounded modules |

---

## Technology Stack

### Frontend (apps/web)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0.7 | React framework with App Router |
| **React** | 19.2.0 | UI library |
| **TypeScript** | 5.9.3 | Type safety |
| **Tailwind CSS** | 4.x | Utility-first styling |
| **shadcn/ui** | Latest | Component library (Radix-based) |
| **Framer Motion** | 12.x | Animations |
| **Recharts** | 3.x | Data visualization |
| **Zod** | 4.x | Schema validation |
| **React Hook Form** | 7.x | Form management |

### Backend API (apps/api)

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.115.0 | API framework |
| **Python** | 3.11+ | Runtime |
| **Poetry** | Latest | Dependency management |
| **Pydantic** | 2.x | Data validation |
| **psycopg** | 3.2.1 | PostgreSQL driver |
| **PyJWT** | 2.9.0 | JWT authentication |
| **boto3** | 1.35.0 | AWS/R2 S3 client |
| **httpx** | 0.27.2 | HTTP client |
| **bcrypt** | 4.2.0 | Password hashing |

### Background Worker (apps/worker)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Celery** | 5.4.0 | Task queue |
| **Redis** | 5.0.8 | Message broker & rate limiting |
| **Jinja2** | 3.1.2 | HTML templating |
| **Playwright** | 1.48.0 | PDF rendering (local) |
| **Twilio** | 9.0.0 | SMS delivery |

### Infrastructure

| Component | Service | Purpose |
|-----------|---------|---------|
| **Frontend Hosting** | Vercel | Next.js deployment |
| **API Hosting** | Render | FastAPI service |
| **Worker Hosting** | Render | Background worker |
| **Database** | Render PostgreSQL | Data persistence + RLS |
| **Cache/Queue** | Redis (Render) | Celery broker & rate limiting |
| **File Storage** | Cloudflare R2 | PDFs, images, assets |

---

## Key Features

### Multi-Tenant Architecture
- PostgreSQL Row-Level Security (RLS) for data isolation
- Account-based access control
- Affiliate/sponsor relationships

### White-Label Branding
- Custom logos, colors, and contact information
- Branded email templates
- Agent photo integration

### Automated Scheduling
- Recurring report generation (daily, weekly, monthly)
- Timezone-aware with DST handling
- Email delivery to contacts and groups

### Lead Capture System
- Consumer landing pages with address autocomplete
- SMS delivery of home value reports
- Agent notification system

### Admin Console
- User management
- SMS credit tracking
- Report generation monitoring
- Billing management

---

## Deployment Overview

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Vercel    │      │   Render    │      │   Render    │
│  (Next.js)  │─────▶│  (FastAPI)  │─────▶│  (Worker)   │
└─────────────┘      └─────────────┘      └─────────────┘
                            │                    │
                            ▼                    ▼
                     ┌─────────────┐      ┌─────────────┐
                     │  PostgreSQL │      │    Redis    │
                     │   (Render)  │      │  (Render)   │
                     └─────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │ Cloudflare  │
                     │     R2      │
                     └─────────────┘
```

---

## Environment Variables Summary

### Required for Production

```env
# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# Authentication
JWT_SECRET=<secure-random-string>

# MLS Data
SIMPLYRETS_API_KEY=<key>
SIMPLYRETS_API_SECRET=<secret>

# Email
RESEND_API_KEY=<key>

# Storage
R2_ACCOUNT_ID=<id>
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
R2_BUCKET_NAME=market-reports

# PDF Generation
PDF_ENGINE=api
PDF_API_URL=https://api.pdfshift.io/v3/convert/pdf
PDF_API_KEY=<key>

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# SMS (Optional)
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_PHONE_NUMBER=+1...

# AI Insights (Optional)
OPENAI_API_KEY=<key>
AI_INSIGHTS_ENABLED=true

# Frontend
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=<key>
```

---

*Document generated: February 2026*
