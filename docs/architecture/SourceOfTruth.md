# TrendyReports — Single Source of Truth

_Project Status & Architecture for Investors and Development Teams_

**Last Updated:** January 9, 2026
**Version:** V14 (Sender-Aware AI Insights)

---

## Executive Summary

**TrendyReports** is a production-ready SaaS platform that transforms live MLS data into photo-rich, branded **PDF reports** and matching **email-ready reports** with automated scheduling, delivery, and **AI-powered market insights**.

### Target Market
- **Individual Real Estate Agents** — Generate professional market reports to share with clients
- **Industry Affiliates** (title companies, lenders, brokerages) — Sponsor agents with white-labeled reports featuring their branding

### Key Value Propositions
1. **Automation** — Set-and-forget scheduled reports delivered via email
2. **White-Label** — Affiliates get full branding control (logos, colors, contact info)
3. **Professional PDFs** — Print-ready market reports from live MLS data
4. **AI-Powered Insights** — GPT-4o-mini generated market commentary with sender-aware tone
5. **Smart Presets** — Market-adaptive filters that work in any price range
6. **Multi-Tenant** — Secure data isolation via PostgreSQL Row-Level Security

---

## Current Version: V14 Highlights

| Feature | Description |
|---------|-------------|
| **Sender-Aware AI Insights** | AI adapts tone based on sender: agents get personal "I" voice, affiliates get professional "we" voice |
| **Audience-Based Listing Caps** | Different caps per audience (Luxury=8, First-Time=24, etc.) |
| **"Showing X of Y" Display** | Gallery emails show curation context (e.g., "8 of 104 listings") |
| **Market-Adaptive Filters** | Presets use percentage of median (works in $300K and $3M markets) |
| **Elastic Widening** | Auto-expands filters if results <6, ensuring reports never appear empty |

---

## Core System Status

| System | Status | Notes |
|--------|--------|-------|
| **PDF Report Generation** | COMPLETE | 8 report types, R2 photo proxy, PDFShift engine |
| **Email Delivery** | COMPLETE | SendGrid integration, V14 templates with AI insights |
| **AI-Powered Insights** | COMPLETE | GPT-4o-mini, sender-aware prompts, graceful fallback |
| **Smart Presets** | COMPLETE | Market-adaptive pricing, elastic widening |
| **Schedules (Automation)** | COMPLETE | Plan limits, timezone support, race-condition safe |
| **Branding (White-Label)** | COMPLETE | 4 logo slots, live preview, sample downloads, test emails |
| **Admin Console** | COMPLETE | Platform admin role, full CRUD, schedule management |
| **User Onboarding** | COMPLETE | Setup wizard, checklist, empty states |
| **Account Settings** | COMPLETE | Profile, password, email change, avatar upload |
| **Contacts & Groups** | COMPLETE | Full CRUD, CSV import, group targeting |
| **Billing (Stripe)** | COMPLETE | Plans DB, webhooks, subscription management |
| **Authentication & RLS** | COMPLETE | JWT cookies, multi-tenant row-level security |
| **Affiliate Onboarding** | COMPLETE | Admin dashboard, invite system, bulk CSV import |
| **Social Media Sharing** | COMPLETE | 1080x1920 branded images for Stories/Reels |

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
| **AI Insights** | OpenAI GPT-4o-mini | Optional integration |

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
│  │ report_gens     │  │                   │  │ │ 1. Resolve Filters  │ ││
│  │ schedules       │  │                   │  │ │ 2. Fetch MLS Data   │ ││
│  │ contacts        │  │                   │  │ │ 3. Calculate Metrics│ ││
│  │ plans           │  │                   │  │ │ 4. Proxy Photos→R2  │ ││
│  │ affiliate_brand │  │                   │  │ │ 5. Generate AI Text │ ││
│  └─────────────────┘  │                   │  │ │ 6. Render PDF       │ ││
└───────────────────────┘                   │  │ │ 7. Send Email       │ ││
                                            │  │ └─────────────────────┘ ││
                                            │  └─────────────────────────┘│
                                            └─────────────────────────────┘
                                                          │
                    ┌─────────────────────────────────────┼──────────────┐
                    ▼                    ▼                ▼              ▼
            ┌─────────────┐      ┌─────────────┐  ┌───────────┐  ┌───────────┐
            │ SimplyRETS  │      │ Cloudflare  │  │ SendGrid  │  │  OpenAI   │
            │  MLS API    │      │     R2      │  │   Email   │  │ GPT-4o-m  │
            └─────────────┘      │ (PDFs/imgs) │  └───────────┘  └───────────┘
                                 └─────────────┘
```

---

## AI-Powered Insights System (V13-V14)

### Overview

TrendyReports includes optional GPT-4o-mini integration for generating contextual market insight paragraphs in emails.

### Sender-Aware Tone (V14)

| Account Type | Tone | Example Opening |
|--------------|------|-----------------|
| **REGULAR** (Agent) | Personal, warm, "I" voice | "I've been keeping an eye on the market for you..." |
| **INDUSTRY_AFFILIATE** | Professional, "we" voice | "This week's market update from Pacific Coast Title..." |

### Insight Structure (4-5 sentences, 80-120 words)

1. **Hook** — Lead with most exciting finding
2. **Data** — Reference 2-3 specific numbers
3. **Context** — What it means for buyer/seller
4. **Highlight** — Something interesting about listings
5. **Invitation** — Encourage reaching out

### Audience-Based Listing Caps (V14)

| Audience | Email Cap | PDF Cap | Rationale |
|----------|-----------|---------|-----------|
| All Listings | 24 | 9 | Comprehensive view |
| First-Time Buyers | 24 | 9 | Need lots of options |
| Family Homes | 18 | 9 | Moderate selection |
| Condo Watch | 18 | 9 | Moderate selection |
| Investors | 12 | 9 | Focused on deals |
| Luxury | 8 | 9 | Curated, exclusive |
| Featured Listings | 4 | 4 | Always premium |

### Configuration

```bash
# Worker environment variables
AI_INSIGHTS_ENABLED=true    # Enable AI insights (default: false)
OPENAI_API_KEY=sk-xxx       # Required if AI enabled
```

### Graceful Fallback

If AI is disabled or fails, the system uses warm, engaging template text that still sounds personable.

---

## Smart Presets & Market-Adaptive Filters

### Overview

Smart Presets allow users to select audience-based report configurations that automatically adapt to any market's price range.

### Built-in Presets

| Preset | Report Type | Filters | Price Strategy |
|--------|-------------|---------|----------------|
| **First-Time Buyer** | `new_listings_gallery` | 2+ beds, 2+ baths, SFR | ≤70% of median |
| **Investor Deals** | `new_listings` | All types | ≤50% of median |
| **Luxury Showcase** | `featured_listings` | SFR | ≥150% of median |
| **Condo Watch** | `new_listings_gallery` | 1+ beds, Condo | No price filter |
| **Family Homes** | `new_listings` | 4+ beds, 2+ baths, SFR | No price filter |

### How Market-Adaptive Pricing Works

```
1. User selects "First-Time Buyer" for Irvine
   → price_strategy: { mode: "maxprice_pct_of_median_list", value: 0.70 }

2. Worker fetches baseline listings (90 days, same subtype)
   → Computes median_list_price = $2,400,000

3. Resolves filters
   → maxprice = $2,400,000 × 0.70 = $1,680,000

4. Queries SimplyRETS with resolved maxprice
   → Returns homes under $1.68M

5. PDF header shows "First-Time Buyer — Irvine"
```

### Elastic Widening (Zero Results Safety Net)

If preset returns <6 results (4 for featured):

1. **Expand price**: 70% → 85% → 100% → 120%
2. **Note in report**: "Expanded to match local market conditions"

This ensures users never see empty reports.

### Key Files

| File | Purpose |
|------|---------|
| `packages/ui/src/components/schedules/types.ts` | `PriceStrategy`, `SMART_PRESETS` definitions |
| `apps/worker/src/worker/filter_resolver.py` | `resolve_filters()`, `compute_market_stats()` |
| `apps/api/src/api/routes/schedules.py` | `ReportFilters` Pydantic model |

---

## Data Model (Core Tables)

| Table | Purpose |
|-------|---------|
| `accounts` | Tenant accounts (agents, affiliates) with `account_type` |
| `users` | User credentials, profile, `is_platform_admin`, `avatar_url` |
| `account_users` | Many-to-many user↔account with roles (OWNER/ADMIN/MEMBER) |
| `plans` | Subscription tiers (free, pro, team, affiliate, sponsored_free) |
| `report_generations` | Report jobs with status, result JSON, PDF URL |
| `schedules` | Automated report configs with `filters` JSONB column |
| `contacts` | Email recipients |
| `contact_groups` | Recipient groups for targeting |
| `affiliate_branding` | White-label configuration (4 logos, colors, contact) |
| `email_log` | Delivery tracking with `status` column |
| `signup_tokens` | Invite tokens for agent onboarding |
| `email_suppressions` | Unsubscribed/bounced emails per account |

### Recent Schema Additions

| Column | Table | Purpose |
|--------|-------|---------|
| `filters` (JSONB) | `schedules` | Smart preset filter storage |
| `processing_locked_at` | `schedules` | Race condition prevention |
| `status` | `email_log` | Send status tracking |
| `account_type` | `accounts` | REGULAR vs INDUSTRY_AFFILIATE |

---

## Feature Deep Dive

### 1. Report Types (8 Total)

| Report | Description | Output | AI Insight |
|--------|-------------|--------|------------|
| **Market Snapshot** | Complete market overview | 1-page PDF | ✅ |
| **New Listings** | Table of recently listed properties | 1-page PDF | ✅ |
| **Closed Sales** | Recently sold properties with metrics | 1-page PDF | ✅ |
| **Inventory** | Current active listings analysis | 1-page PDF | ✅ |
| **Price Bands** | Market segmented by price ranges | 1-page PDF | ✅ |
| **New Listings Gallery** | 3×3 photo grid of newest listings | 1-page PDF | ✅ |
| **Featured Listings** | 2×2 photo grid of premium listings | 1-page PDF | ✅ |
| **Open Houses** | Upcoming open house events | 1-page PDF | ✅ |

### 2. White-Label Branding System

| Element | Description |
|---------|-------------|
| **PDF Header Logo** | Light logo for dark gradient backgrounds |
| **PDF Footer Logo** | Dark logo for white/gray backgrounds |
| **Email Header Logo** | Light logo for email header gradient |
| **Email Footer Logo** | Dark logo for white email footer |
| **Primary Color** | Main brand color (gradients, buttons) |
| **Accent Color** | Secondary color (gradient end, accents) |
| **Rep Photo** | Circular headshot in footer |
| **Contact Info** | Name, title, phone, email, website |

**Brand Resolution:**
- Sponsored agents → Use sponsor's branding
- Direct affiliates → Use own branding
- Regular agents → Use own account branding + profile avatar

### 3. Admin Console

Platform administrators have full control via `/admin`:

| Page | Functionality |
|------|---------------|
| **Dashboard** | KPIs: accounts, users, reports, error rate |
| **Accounts** | Browse/filter all tenant accounts |
| **Users** | Manage users, activate/deactivate, verify emails |
| **Affiliates** | Title company management, bulk CSV import |
| **Schedules** | All automated schedules (pause/resume) |
| **Plans** | Create/edit pricing tiers, adjust limits |
| **Reports** | Monitor all report generations, view errors |
| **Emails** | Email delivery logs with status |
| **Settings** | System status, integrations |

### 4. Automated Scheduling

| Feature | Description |
|---------|-------------|
| **Frequency** | Daily, Weekly, Biweekly, Monthly, First of Month |
| **Timezone Support** | User-configurable, defaults to America/Los_Angeles |
| **Plan Limits** | Enforced per plan (free: 5/mo, pro: 50, etc.) |
| **Auto-Pause** | Schedules pause after 3 consecutive failures |
| **Smart Presets** | Market-adaptive filters with elastic widening |
| **Race-Safe** | Atomic locking prevents duplicate processing |

### 5. Email System (V14)

| Feature | Description |
|---------|-------------|
| **Sender-Aware AI** | Tone adapts to agent vs affiliate |
| **Audience Caps** | 8-24 listings based on preset type |
| **"X of Y" Display** | Shows curation context in galleries |
| **Photo Galleries** | 3×3 and 2×2 grids for gallery reports |
| **Filter Descriptions** | Shows applied criteria in styled box |
| **Adaptive Layouts** | 3-col, 2-col, or vertical based on count |

### 6. Authentication & Security

| Feature | Implementation |
|---------|----------------|
| **Token Type** | JWT in HttpOnly cookie (`mr_token`) |
| **Multi-Tenancy** | PostgreSQL Row-Level Security (RLS) |
| **Password** | bcrypt hashed |
| **Session** | 1-hour TTL (login), 7-day TTL (invite accept) |
| **Platform Admin** | `is_platform_admin` flag for `/admin` access |
| **Schedule Locks** | `processing_locked_at` for race prevention |

### 7. Social Media Sharing

| Feature | Description |
|---------|-------------|
| **Format** | 1080×1920 JPEG (9:16 Stories format) |
| **Platforms** | Instagram, TikTok, LinkedIn, Facebook Stories |
| **Branding** | Full white-label (logo, colors, headshot) |
| **Report Types** | All 8 report types supported |

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
- **Critical**: Always use `type=RES` to exclude rentals

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

### OpenAI (AI Insights)
- GPT-4o-mini for market commentary
- Sender-aware system prompts
- Graceful fallback if unavailable

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
│   │   │   ├── social/         # Social media image pages
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
│           ├── filter_resolver.py  # Market-adaptive filters
│           ├── ai_insights.py      # GPT-4o-mini integration
│           ├── pdf_engine.py
│           ├── utils/
│           │   └── photo_proxy.py  # R2 photo proxying
│           └── email/          # Email templates
│
├── packages/
│   └── ui/                     # Shared UI components
│       └── src/components/
│           └── schedules/
│               └── types.ts    # SMART_PRESETS definitions
│
├── db/
│   ├── migrations/             # SQL migrations (0001-0033+)
│   └── seed_demo_accounts.sql
│
├── docs/                       # Technical documentation
│   ├── ADMIN_CONSOLE.md
│   ├── BRANDING.md
│   ├── PDF_REPORTS.md
│   ├── EMAIL_SYSTEM.md
│   ├── REPORT_TYPES_MATRIX.md
│   ├── SCHEDULES.md
│   ├── SIMPLYRETS_API.md
│   ├── SOCIAL_MEDIA_SHARING.md
│   └── ...
│
└── scripts/                    # Utility scripts
    ├── test_report_flow.py
    ├── test_simplyrets.py
    └── test_all_reports.py
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

# AI Insights (optional)
AI_INSIGHTS_ENABLED=true
OPENAI_API_KEY=sk-xxx
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
| **GPT-4o-mini** | Cost-effective AI (~$0.001-0.002/email) with quality output |
| **Atomic Schedule Locks** | `FOR UPDATE SKIP LOCKED` prevents race conditions |
| **Market-Adaptive Filters** | Percentage of median works in any price market |

---

## Roadmap (Future Enhancements)

### Near-Term
- [ ] Two-factor authentication (2FA)
- [ ] Mobile-responsive PDF templates
- [ ] Video export for Reels/TikTok

### Medium-Term
- [ ] Agent-facing mobile app
- [ ] CRM integrations (Follow Up Boss, kvCORE)
- [ ] Custom template builder

### Long-Term
- [ ] Multi-MLS support beyond SimplyRETS
- [ ] Advanced AI features (trend prediction, market alerts)
- [ ] International expansion

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [ADMIN_CONSOLE.md](docs/ADMIN_CONSOLE.md) | Platform admin features |
| [BRANDING.md](docs/BRANDING.md) | White-label branding system |
| [PDF_REPORTS.md](docs/PDF_REPORTS.md) | PDF generation pipeline |
| [EMAIL_SYSTEM.md](docs/EMAIL_SYSTEM.md) | Email templates, AI insights, delivery |
| [SIMPLYRETS_API.md](docs/SIMPLYRETS_API.md) | MLS data integration |
| [REPORT_TYPES_MATRIX.md](docs/REPORT_TYPES_MATRIX.md) | All report specifications |
| [SCHEDULES.md](docs/SCHEDULES.md) | Scheduling system with smart presets |
| [AUTH_ARCHITECTURE_V1.md](docs/AUTH_ARCHITECTURE_V1.md) | Authentication system |
| [TITLE_COMPANY_ONBOARDING.md](docs/TITLE_COMPANY_ONBOARDING.md) | Affiliate onboarding |
| [USER_ONBOARDING.md](docs/USER_ONBOARDING.md) | User setup wizard |
| [ACCOUNT_SETTINGS.md](docs/ACCOUNT_SETTINGS.md) | Profile management |
| [SOCIAL_MEDIA_SHARING.md](docs/SOCIAL_MEDIA_SHARING.md) | Social media image generation |
| [CHANGELOG.md](docs/CHANGELOG.md) | Version history |

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| V14 | Jan 2026 | Sender-aware AI, audience-based caps, "X of Y" display |
| V13 | Jan 2026 | AI insights for all report types, gallery fix |
| V12 | Jan 2026 | Gallery metrics fix, AI insights introduction |
| V11 | Jan 2026 | Filter description blurbs, closed sales optimization |
| V10 | Jan 2026 | Professional corporate email redesign |
| V8 | Jan 2026 | Adaptive gallery layouts |
| V6 | Dec 2025 | Unified email template architecture |
| V5 | Dec 2025 | Photo galleries in emails |
| V4 | Dec 2025 | PDF-aligned email layouts |
| V2.5 | Dec 2025 | R2 photo proxy for reliable PDF images |
| V1.0 | Dec 2025 | Initial production release |

---

_This document is the single source of truth for TrendyReports platform status and architecture._
