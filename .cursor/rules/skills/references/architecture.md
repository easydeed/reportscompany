# TrendyReports — System Architecture (Read First)

> ⚠️ **PARTIALLY FALSIFIED.** Audited 2026-08-17 against HEAD `f854ed6`; known-false
> claims are catalogued in [`docs/DOCS_AUDIT_2026-08-17.md`](../../../../docs/DOCS_AUDIT_2026-08-17.md).
> **All counts and line numbers in this file are unreliable — verify against code.**
> Behavioural descriptions are more trustworthy than inventories, but neither is
> guaranteed. Do not cite this document as evidence.

## What TrendyReports Is

Multi-tenant SaaS platform that generates branded real estate market reports and property reports from live CRMLS data (Southern California). Serves real estate agents, title companies, and title reps.

## Tech Stack

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | Next.js 16 (App Router), React 19, Tailwind v4, shadcn/ui | Vercel |
| API | FastAPI, Python 3.11+ | Render |
| Worker | Celery 5, Python 3.11+ | Render |
| Database | PostgreSQL 15 + Row-Level Security | Render |
| Cache/Queue | Redis | Render |
| File Storage | Cloudflare R2 | Cloudflare |
| Package manager (frontend) | pnpm 9.12.3 | — |
| Package manager (backend) | Poetry / pip | — |

## Directory Structure

```
reportscompany/
├── apps/
│   ├── api/src/api/          # FastAPI app
│   │   ├── routes/           # 26 route modules
│   │   ├── services/         # Business logic
│   │   ├── middleware/       # Auth, RLS, rate limit
│   │   └── schemas/          # Pydantic models
│   ├── worker/src/worker/    # Celery worker
│   │   ├── tasks.py          # Celery tasks
│   │   ├── market_builder.py # Market report HTML renderer
│   │   ├── property_builder.py # Property report HTML renderer
│   │   ├── pdf_adapter.py    # PDFShift integration
│   │   ├── email/            # Email template builders
│   │   └── templates/        # Jinja2 templates
│   └── web/                  # Next.js frontend
│       ├── app/              # App router pages
│       ├── components/       # React components
│       ├── hooks/            # React Query hooks
│       └── lib/              # Utilities
├── db/migrations/            # SQL migrations
├── scripts/                  # CLI tools, QA scripts
└── .cursor/rules/            # Agent rules and skills
```

## 5-Tier Role Hierarchy

```
Platform Admin (is_platform_admin=true) → /app/admin
  └── Title Company Admin (TITLE_COMPANY) → /app/company
       └── Title Rep (INDUSTRY_AFFILIATE, parent_account_id, plan=affiliate) → /app/affiliate
            └── Sponsored/Trial Agent (REGULAR, sponsor_account_id, plan=sponsored_free) → /app
  └── Regular Agent (REGULAR, no sponsor) → /app
```

## Subscription Plans

| Slug (DB) | Display Name | Price | Limits (market/sched/prop) |
|-----------|--------------|-------|----------------------------|
| `free` | Free | $0 | 3 / 1 / 1 |
| `sponsored_free` | Sponsored Free | $0 | 3 / 1 / 1 |
| `trial` | Trial | $0 | 3 / 1 / 1 |
| `starter` | **Growth** | **$19** | 15 / 3 / 3 |
| `pro` | **Growth Plus** | **$29** | unlimited / unlimited / 10 |
| `affiliate` | Affiliate | $99 | 5000 / unlimited / 100 |

**IMPORTANT:** DB slugs ('starter', 'pro') do NOT match display names ('Growth', 'Growth Plus'). Code references use slugs; UI shows display names.

## External Integrations

| Service | Purpose | Env Vars |
|---------|---------|----------|
| SimplyRETS | MLS data | SIMPLYRETS_USERNAME, SIMPLYRETS_PASSWORD |
| SiteX Pro | Property assessor data | SITEX_CLIENT_ID, SITEX_CLIENT_SECRET |
| PDFShift | HTML → PDF | PDFSHIFT_API_KEY |
| SendGrid | Email delivery | SENDGRID_API_KEY |
| OpenAI | AI narratives (GPT-4o) | OPENAI_API_KEY |
| Stripe | Subscription billing | STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET |
| Cloudflare R2 | PDF + logo storage | R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_PUBLIC_URL |
| Google Maps | Aerial + street view | GOOGLE_MAPS_API_KEY |
| Twilio | SMS notifications | TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER |

## Environment

- API base (prod): `https://reportscompany-api.onrender.com`
- Frontend: `https://www.trendyreports.io`
- DB: `mr-staging-db` on Render
- Latest migration: 0051 (per-product pricing)
