# TrendyReports — Single Source of Truth

_Project Status & Architecture for Investors and Development Teams_

**Last Updated:** December 18, 2025

---

## Executive Summary

**TrendyReports** is a production-ready SaaS platform that transforms live MLS data into photo-rich, branded **PDF reports** and matching **email-ready reports** with automated scheduling and delivery.

### Target Market
- **Individual Real Estate Agents** — Generate professional market reports to share with clients
- **Industry Affiliates** (title companies, lenders, brokerages) — Sponsor agents with white-labeled reports featuring their branding

### Key Value Propositions
1. **Automation** — Set-and-forget scheduled reports delivered via email
2. **White-Label** — Affiliates get full branding control (logos, colors, contact info)
3. **Professional PDFs** — Print-ready market reports from live MLS data
4. **Multi-Tenant** — Secure data isolation via PostgreSQL Row-Level Security

---

## Core System Status

| System | Status | Notes |
|--------|--------|-------|
| **PDF Report Generation** | COMPLETE | 8 report types, R2 photo proxy, PDFShift engine |
| **Email Delivery** | COMPLETE | SendGrid integration, V4.2 PDF-aligned templates |
| **Schedules (Automation)** | COMPLETE | Plan limits, timezone support, auto-pause on failure |
| **Branding (White-Label)** | COMPLETE | File uploads, live preview, sample downloads, test emails |
| **Admin Console** | COMPLETE | Platform admin role, full CRUD for accounts/users/plans |
| **User Onboarding** | COMPLETE | Setup wizard, checklist, empty states |
| **Account Settings** | COMPLETE | Profile, password, email change, avatar upload |
| **Contacts & Groups** | COMPLETE | Full CRUD, CSV import, group targeting |
| **Billing (Stripe)** | COMPLETE | Plans DB, webhooks, subscription management |
| **Authentication & RLS** | COMPLETE | JWT cookies, multi-tenant row-level security |
| **Affiliate Onboarding** | COMPLETE | Admin dashboard, invite system, bulk CSV import |

---

## Architecture Overview

### Infrastructure Stack

| Layer | Technology | Deployment |
|-------|------------|------------|
| **Frontend** | Next.js 15 (App Router) | Vercel |
| **API** | FastAPI + Poetry | Render |
| **Worker** | Celery + Redis | Render Background Worker |
| **Scheduler** | Python (schedules_tick.py) | Render Background Worker |
| **Database** | PostgreSQL 15 + RLS | Render Postgres |
| **File Storage** | Cloudflare R2 | R2 Bucket (PDFs, logos, photos) |
| **Email** | SendGrid | Transactional API |
| **Payments** | Stripe | Checkout + Customer Portal + Webhooks |
| **MLS Data** | SimplyRETS | Production API |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                         Next.js on Vercel                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   /app/*     │  │   /admin/*   │  │  /branding   │  │   /login    │ │
│  │  Dashboard   │  │ Admin Console│  │  White-Label │  │    Auth     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               API LAYER                                  │
│                          FastAPI on Render                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  /v1/auth    │  │ /v1/reports  │  │ /v1/admin/*  │  │ /v1/upload  │ │
│  │  JWT Auth    │  │  Generation  │  │ Admin APIs   │  │  R2 Upload  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐  ┌─────────────┐  ┌─────────────────────────────┐
│    PostgreSQL + RLS   │  │    Redis    │  │     Celery Worker           │
│  ┌─────────────────┐  │  │   Queue     │  │  ┌─────────────────────────┐│
│  │ accounts        │  │  └─────────────┘  │  │ Report Generation Task  ││
│  │ users           │  │                   │  │ ┌─────────────────────┐ ││
│  │ report_gens     │  │                   │  │ │ 1. Fetch MLS Data   │ ││
│  │ schedules       │  │                   │  │ │ 2. Calculate Metrics│ ││
│  │ contacts        │  │                   │  │ │ 3. Proxy Photos→R2  │ ││
│  │ plans           │  │                   │  │ │ 4. Render PDF       │ ││
│  │ affiliate_brand │  │                   │  │ │ 5. Upload to R2     │ ││
│  └─────────────────┘  │                   │  │ │ 6. Send Email       │ ││
└───────────────────────┘                   │  │ └─────────────────────┘ ││
                                            │  └─────────────────────────┘│
                                            └─────────────────────────────┘
                                                          │
                    ┌─────────────────────────────────────┼──────────────┐
                    ▼                                     ▼              ▼
            ┌─────────────┐                      ┌─────────────┐  ┌───────────┐
            │ SimplyRETS  │                      │ Cloudflare  │  │ SendGrid  │
            │  MLS API    │                      │     R2      │  │   Email   │
            └─────────────┘                      │ (PDFs/imgs) │  └───────────┘
                                                 └─────────────┘
```

---

## Data Model (Core Tables)

| Table | Purpose |
|-------|---------|
| `accounts` | Tenant accounts (agents, affiliates) |
| `users` | User credentials and profile |
| `account_users` | Many-to-many user↔account with roles (OWNER/ADMIN/MEMBER) |
| `plans` | Subscription tiers (free, pro, team, affiliate, sponsored_free) |
| `report_generations` | Report jobs with status, result JSON, PDF URL |
| `schedules` | Automated report configurations |
| `contacts` | Email recipients |
| `contact_groups` | Recipient groups for targeting |
| `affiliate_branding` | White-label configuration (logos, colors, contact) |
| `email_logs` | Delivery tracking |
| `signup_tokens` | Invite tokens for agent onboarding |

---

## Feature Deep Dive

### 1. Report Types (8 Total)

| Report | Description | Output |
|--------|-------------|--------|
| **Market Snapshot** | Complete market overview with all key metrics | 1-page PDF |
| **New Listings** | Table of recently listed properties | 1-page PDF |
| **Closed Sales** | Recently sold properties with metrics | 1-page PDF |
| **Inventory** | Current active listings analysis | 1-page PDF |
| **Price Bands** | Market segmented by price ranges | 1-page PDF |
| **New Listings Gallery** | 3×3 photo grid of newest listings | 1-page PDF |
| **Featured Listings** | 2×2 photo grid of premium listings | 1-page PDF |
| **Open Houses** | Upcoming open house events | 1-page PDF |

### 2. White-Label Branding System

Affiliates control all branding elements:

| Element | Description |
|---------|-------------|
| **Header Logo** | Light logo for dark gradient backgrounds |
| **Footer Logo** | Dark logo for white/gray backgrounds |
| **Primary Color** | Main brand color (gradients, buttons) |
| **Accent Color** | Secondary color (highlights, badges) |
| **Rep Photo** | Circular headshot in footer |
| **Contact Info** | Name, title, phone, email, website |

**Brand Resolution:**
- Sponsored agents → Use sponsor's branding
- Direct affiliates → Use own branding
- Regular agents → Use own account branding

### 3. Admin Console

Platform administrators have full control via `/admin`:

| Page | Functionality |
|------|---------------|
| **Dashboard** | KPIs: accounts, users, reports, error rate |
| **Accounts** | Browse/filter all tenant accounts |
| **Users** | Manage users, activate/deactivate, verify emails |
| **Affiliates** | Title company management, agent invites, bulk CSV import |
| **Plans** | Create/edit pricing tiers, adjust limits |
| **Reports** | Monitor all report generations, view errors |
| **Emails** | Email delivery logs |
| **Settings** | System status, integrations |

### 4. Automated Scheduling

| Feature | Description |
|---------|-------------|
| **Frequency** | Daily, Weekly, Biweekly, Monthly, First of Month |
| **Timezone Support** | User-configurable, defaults to America/Los_Angeles |
| **Plan Limits** | Enforced per plan (free: 5 reports/mo, pro: 50, etc.) |
| **Auto-Pause** | Schedules pause after 3 consecutive failures |
| **Email Delivery** | PDF attached + inline metrics in email |

### 5. Authentication & Security

| Feature | Implementation |
|---------|----------------|
| **Token Type** | JWT in HttpOnly cookie (`mr_token`) |
| **Multi-Tenancy** | PostgreSQL Row-Level Security (RLS) |
| **Password** | bcrypt hashed |
| **Session** | 1-hour TTL (login), 7-day TTL (invite accept) |
| **Platform Admin** | `is_platform_admin` flag for `/admin` access |

---

## Subscription Plans

| Plan | Monthly Limit | Price | Use Case |
|------|---------------|-------|----------|
| `free` | 5 reports | $0 | Trial users |
| `pro` | 50 reports | $29/mo | Individual agents |
| `team` | 200 reports | $99/mo | Small teams |
| `affiliate` | 500 reports | Custom | Title companies |
| `sponsored_free` | 10 reports | $0 (sponsored) | Agents under affiliate |

---

## Key Integrations

### SimplyRETS (MLS Data)
- Live property data from participating MLSs
- Queries: Active, Pending, Closed listings
- Photos proxied through R2 for PDF reliability

### Stripe (Payments)
- Checkout Sessions for new subscriptions
- Customer Portal for self-service billing
- Webhooks for subscription state sync

### SendGrid (Email)
- Transactional email delivery
- Dynamic templates with brand variables
- Delivery tracking via webhooks

### Cloudflare R2 (Storage)
- PDF storage with presigned URLs
- Logo/headshot uploads
- MLS photo proxy for PDF generation

---

## Demo Accounts (Staging)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@trendyreports-demo.com | DemoAdmin123! |
| Free Agent | agent-free@trendyreports-demo.com | DemoAgent123! |
| Pro Agent | agent-pro@trendyreports-demo.com | DemoAgent123! |
| Affiliate | affiliate@trendyreports-demo.com | DemoAff123! |
| Sponsored Agent | agent-sponsored@trendyreports-demo.com | DemoAgent123! |

---

## Repository Structure

```
/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── app/
│   │   │   ├── app/            # Authenticated user pages
│   │   │   ├── admin/          # Platform admin console
│   │   │   ├── login/          # Authentication
│   │   │   ├── print/          # PDF render endpoint
│   │   │   └── api/proxy/      # Backend API proxies
│   │   ├── components/         # React components
│   │   ├── lib/                # Utilities
│   │   └── templates/          # HTML PDF templates
│   │
│   ├── api/                    # FastAPI backend
│   │   └── src/api/
│   │       ├── routes/         # API endpoints
│   │       ├── services/       # Business logic
│   │       └── middleware/     # Auth, RLS
│   │
│   └── worker/                 # Celery worker
│       └── src/worker/
│           ├── tasks.py        # Report generation task
│           ├── report_builders.py
│           ├── pdf_engine.py
│           └── email/          # Email templates
│
├── db/
│   ├── migrations/             # SQL migrations (0001-0026+)
│   └── seed_demo_accounts.sql
│
├── docs/                       # Technical documentation
│   ├── ADMIN_CONSOLE.md
│   ├── BRANDING.md
│   ├── PDF_REPORTS.md
│   ├── EMAIL_SYSTEM.md
│   ├── SIMPLYRETS_API.md
│   └── ...
│
└── scripts/                    # Utility scripts
    ├── test_report_flow.py
    └── test_simplyrets.py
```

---

## Environment Variables

### Frontend (Vercel)
```
NEXT_PUBLIC_API_BASE=https://reportscompany.onrender.com
```

### API (Render)
```
DATABASE_URL=postgresql://...
JWT_SECRET=<secret>
SENDGRID_API_KEY=<key>
STRIPE_SECRET_KEY=<key>
STRIPE_WEBHOOK_SECRET=<key>
R2_ACCOUNT_ID=<id>
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<key>
R2_BUCKET_NAME=market-reports
```

### Worker (Render)
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SIMPLYRETS_USERNAME=<user>
SIMPLYRETS_PASSWORD=<pass>
PDFSHIFT_API_KEY=<key>
PRINT_BASE=https://trendyreports.io
PHOTO_PROXY_ENABLED=true
R2_*=<same as API>
```

---

## Business Model

### Revenue Streams

1. **Direct B2C** — Agents subscribe to Pro/Team plans ($29-$99/mo)
2. **B2B2C (Affiliates)** — Title companies pay for affiliate plan, sponsor agents with free access
3. **Overage Fees** — Pay-per-report beyond plan limits (where enabled)

### Unit Economics

| Metric | Value |
|--------|-------|
| CAC Target | <$50 |
| LTV Target | >$500 |
| Gross Margin | ~80% (low COGS: API calls, storage) |

---

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **PostgreSQL RLS** | True multi-tenancy without app-level filtering |
| **JWT in HttpOnly cookie** | XSS protection, seamless SSR auth |
| **R2 Photo Proxy** | MLS photos blocked by PDFShift; proxy ensures reliability |
| **PDFShift** | Cloud PDF rendering without server Chromium |
| **Celery + Redis** | Reliable async job processing with retries |
| **Next.js App Router** | Modern React with server components |

---

## Roadmap (Future Enhancements)

### Near-Term
- [ ] Two-factor authentication (2FA)
- [ ] Mobile-responsive PDF templates
- [ ] Advanced scheduling (custom cron)

### Medium-Term
- [ ] Agent-facing mobile app
- [ ] CRM integrations (Follow Up Boss, kvCORE)
- [ ] Custom template builder

### Long-Term
- [ ] Multi-MLS support beyond SimplyRETS
- [ ] AI-powered market insights
- [ ] International expansion

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [ADMIN_CONSOLE.md](docs/ADMIN_CONSOLE.md) | Platform admin features |
| [BRANDING.md](docs/BRANDING.md) | White-label branding system |
| [PDF_REPORTS.md](docs/PDF_REPORTS.md) | PDF generation pipeline |
| [EMAIL_SYSTEM.md](docs/EMAIL_SYSTEM.md) | Email templates and delivery |
| [SIMPLYRETS_API.md](docs/SIMPLYRETS_API.md) | MLS data integration |
| [AUTH_ARCHITECTURE_V1.md](docs/AUTH_ARCHITECTURE_V1.md) | Authentication system |
| [REPORT_TYPES_MATRIX.md](docs/REPORT_TYPES_MATRIX.md) | All report specifications |
| [TITLE_COMPANY_ONBOARDING.md](docs/TITLE_COMPANY_ONBOARDING.md) | Affiliate onboarding |
| [USER_ONBOARDING.md](docs/USER_ONBOARDING.md) | User setup wizard |
| [ACCOUNT_SETTINGS.md](docs/ACCOUNT_SETTINGS.md) | Profile management |
| [DEMO_ACCOUNTS.md](docs/DEMO_ACCOUNTS.md) | Staging demo logins |

---

_This document is the single source of truth for TrendyReports platform status and architecture._
