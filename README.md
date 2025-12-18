# TrendyReports

> **A production-ready SaaS platform that transforms live MLS data into branded PDF market reports with automated scheduling and email delivery.**

**Status:** Production Ready | **Last Updated:** December 18, 2025

---

## Overview

TrendyReports enables real estate agents and industry affiliates (title companies, lenders, brokerages) to generate professional, photo-rich PDF market reports from live MLS data. The platform features full white-label branding, automated scheduling, and email delivery.

### Key Value Propositions

1. **Automation** — Set-and-forget scheduled reports delivered via email
2. **White-Label** — Affiliates get full branding control (logos, colors, contact info)
3. **Professional PDFs** — Print-ready market reports from live MLS data
4. **Multi-Tenant** — Secure data isolation via PostgreSQL Row-Level Security

---

## System Status

| System | Status |
|--------|--------|
| PDF Report Generation (8 types) | COMPLETE |
| Email Delivery (SendGrid) | COMPLETE |
| Automated Scheduling | COMPLETE |
| White-Label Branding | COMPLETE |
| Admin Console | COMPLETE |
| User Onboarding | COMPLETE |
| Account Settings | COMPLETE |
| Contacts & Groups | COMPLETE |
| Billing (Stripe) | COMPLETE |
| Authentication & RLS | COMPLETE |
| Affiliate Onboarding | COMPLETE |

---

## Technology Stack

| Layer | Technology | Deployment |
|-------|------------|------------|
| Frontend | Next.js 15 (App Router) | Vercel |
| API | FastAPI + Poetry | Render |
| Worker | Celery + Redis | Render Background Worker |
| Database | PostgreSQL 15 + RLS | Render Postgres |
| File Storage | Cloudflare R2 | R2 Bucket |
| Email | SendGrid | Transactional API |
| Payments | Stripe | Checkout + Portal |
| MLS Data | SimplyRETS | Production API |

---

## Repository Structure

```
/
├── apps/
│   ├── web/                    # Next.js frontend (Vercel)
│   │   ├── app/                # App Router pages
│   │   │   ├── app/            # User dashboard
│   │   │   ├── admin/          # Platform admin console
│   │   │   └── print/          # PDF render endpoints
│   │   ├── components/         # React components
│   │   └── lib/                # Utilities
│   │
│   ├── api/                    # FastAPI backend (Render)
│   │   └── src/api/
│   │       ├── routes/         # API endpoints
│   │       ├── services/       # Business logic
│   │       └── middleware/     # Auth, RLS
│   │
│   └── worker/                 # Celery worker (Render)
│       └── src/worker/
│           ├── tasks.py        # Report generation
│           └── email/          # Email templates
│
├── db/
│   └── migrations/             # SQL migrations
│
├── docs/                       # Technical documentation
│   ├── ADMIN_CONSOLE.md
│   ├── BRANDING.md
│   ├── PDF_REPORTS.md
│   ├── EMAIL_SYSTEM.md
│   └── ...
│
├── packages/
│   ├── api-client/             # OpenAPI → TypeScript client
│   └── ui/                     # Shared UI components
│
└── scripts/                    # Utility scripts
```

---

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15
- Redis 7

### Setup
```bash
# Install dependencies
pnpm install           # Frontend
poetry install         # Backend

# Start services
docker-compose up -d   # Postgres + Redis

# Run migrations
cd apps/api && poetry run alembic upgrade head

# Start development servers
pnpm dev               # Frontend (localhost:3000)
poetry run uvicorn     # API (localhost:8000)
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [SourceOfTruth.md](./SourceOfTruth.md) | **Complete platform overview for investors** |
| [docs/ADMIN_CONSOLE.md](./docs/ADMIN_CONSOLE.md) | Platform admin features |
| [docs/BRANDING.md](./docs/BRANDING.md) | White-label branding system |
| [docs/PDF_REPORTS.md](./docs/PDF_REPORTS.md) | PDF generation pipeline |
| [docs/EMAIL_SYSTEM.md](./docs/EMAIL_SYSTEM.md) | Email templates and delivery |
| [docs/AUTH_ARCHITECTURE_V1.md](./docs/AUTH_ARCHITECTURE_V1.md) | Authentication system |
| [docs/DEMO_ACCOUNTS.md](./docs/DEMO_ACCOUNTS.md) | Staging demo logins |

---

## Demo Access (Staging)

| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@trendyreports-demo.com | DemoAdmin123! |
| Pro Agent | agent-pro@trendyreports-demo.com | DemoAgent123! |
| Affiliate | affiliate@trendyreports-demo.com | DemoAff123! |

---

## License

Proprietary — All rights reserved.
