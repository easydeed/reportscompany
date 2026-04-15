# TrendyReports

> **A production-ready SaaS platform that transforms live MLS data into branded PDF market reports with automated scheduling, AI insights, and email delivery.**

**Status:** Production Ready | **Last Updated:** April 13, 2026

---

## Overview

TrendyReports enables real estate agents and industry affiliates (title companies, lenders, brokerages) to generate professional, photo-rich PDF market reports from live MLS data. The platform features full white-label branding, automated scheduling, AI-powered market commentary, and email delivery.

### Key Value Propositions

1. **Automation** — Set-and-forget scheduled reports delivered via email
2. **White-Label** — Affiliates get full branding control (logos, colors, contact info)
3. **Professional PDFs** — Print-ready market reports from live MLS data (8 market types + 5 property themes)
4. **AI-Powered** — GPT-4o-mini market commentary with sender-aware tone
5. **Multi-Tenant** — Secure data isolation via PostgreSQL Row-Level Security

---

## System Status

| System | Status |
|--------|--------|
| PDF Report Generation (8 market + 5 property themes) | COMPLETE |
| Email Delivery (SendGrid) | COMPLETE |
| AI-Powered Insights (GPT-4o-mini) | COMPLETE |
| Automated Scheduling | COMPLETE |
| White-Label Branding | COMPLETE |
| Admin Console | COMPLETE |
| User Onboarding | COMPLETE |
| Account Settings | COMPLETE |
| Contacts & Groups | COMPLETE |
| Billing (Stripe) | COMPLETE |
| Authentication & RLS | COMPLETE |
| Affiliate Onboarding | COMPLETE |
| Social Media Sharing | COMPLETE |
| Lead Pages | COMPLETE |

---

## Technology Stack

| Layer | Technology | Version | Deployment |
|-------|------------|---------|------------|
| Frontend | Next.js (App Router) | 16.0.7 | Vercel |
| UI | React + Tailwind CSS | 19.2.0 / v4 | Vercel |
| API | FastAPI + Poetry | ^0.115 | Render |
| Worker | Celery + Redis | ^5.4 | Render Background Worker |
| Database | PostgreSQL + RLS | 15 | Render Postgres |
| File Storage | Cloudflare R2 | — | R2 Bucket |
| Email | SendGrid | — | Transactional API |
| Payments | Stripe | — | Checkout + Portal |
| MLS Data | SimplyRETS | — | Production API |
| AI | OpenAI GPT-4o-mini | — | Optional integration |

---

## Repository Structure

```
/
├── apps/
│   ├── web/                    # Next.js 16 frontend (Vercel)
│   │   ├── app/                # App Router pages (50+ routes)
│   │   │   ├── app/            # Authenticated user dashboard
│   │   │   ├── admin/          # Platform admin console
│   │   │   ├── print/          # PDF render endpoints
│   │   │   ├── social/         # Social media image pages
│   │   │   └── api/proxy/      # Backend API proxies
│   │   ├── components/         # 181 React components
│   │   ├── hooks/              # React Query hooks
│   │   ├── lib/                # Utilities, API clients, types
│   │   └── templates/          # HTML PDF/email templates
│   │
│   ├── api/                    # FastAPI backend (Render)
│   │   └── src/api/
│   │       ├── main.py         # App + 28 router mounts
│   │       ├── routes/         # 28 API route modules
│   │       ├── services/       # 15 business logic modules
│   │       ├── middleware/     # Auth, rate limiting
│   │       ├── schemas/        # Pydantic models
│   │       └── config/         # Billing configuration
│   │
│   └── worker/                 # Celery worker (Render)
│       └── src/worker/
│           ├── tasks.py        # Market report generation tasks
│           ├── property_tasks/ # Property report tasks
│           ├── report_builders.py  # 8 report type builders
│           ├── market_builder.py   # Market report HTML renderer
│           ├── property_builder.py # Property report HTML (5 themes)
│           ├── filter_resolver.py  # Market-adaptive filters
│           ├── ai_insights.py      # GPT-4o-mini integration
│           ├── pdf_engine.py       # PDF rendering (Playwright/PDFShift)
│           ├── email/              # Email templates + sending
│           ├── vendors/            # SimplyRETS client
│           ├── utils/              # R2 upload, photo proxy
│           ├── compute/            # Statistical calculations
│           ├── sms/                # Twilio SMS
│           └── templates/          # Jinja2 PDF templates
│
├── db/
│   └── migrations/             # 46 SQL migrations (0001–0046)
│
├── docs/                       # Technical documentation
│   ├── architecture/           # Architecture docs + module docs
│   │   ├── SOURCE_OF_TRUTH.md  # Master architecture document
│   │   └── modules/            # Per-module deep dives
│   ├── plan/                   # Plans & playbooks
│   └── design/                 # HTML design mockups
│
├── packages/
│   └── ui/                     # Shared UI components (109 files)
│
├── libs/
│   └── shared/                 # Shared Python utilities
│
├── scripts/                    # 42 utility/migration/test scripts
├── tests/                      # Root-level Python tests
├── tools/                      # Data export & smoke test tools
├── .cursor/rules/              # AI agent skill files
└── .github/workflows/          # CI/CD (4 workflows)
```

---

## Local Development

### Prerequisites
- Node.js 20+ (see `.nvmrc`: 20.18.1)
- Python 3.11+
- pnpm 9+
- Docker (for Postgres + Redis)

### Setup
```bash
# Install frontend dependencies
pnpm install

# Install backend dependencies
cd apps/api && poetry install
cd apps/worker && poetry install

# Start database + Redis
docker-compose up -d

# Run migrations
python scripts/run_migrations.py

# Start development servers
pnpm dev               # Frontend (localhost:3000)
cd apps/api && poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 10000
cd apps/worker && poetry run celery -A worker.app.celery worker -l info
```

See [LOCAL_SETUP_GUIDE.md](./LOCAL_SETUP_GUIDE.md) for detailed setup instructions.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture/SOURCE_OF_TRUTH.md](./docs/architecture/SOURCE_OF_TRUTH.md) | **Master architecture document** — start here |
| [docs/architecture/INDEX.md](./docs/architecture/INDEX.md) | Quick-reference source tree |
| [docs/architecture/modules/](./docs/architecture/modules/) | Per-module deep dives (13 modules) |
| [docs/plan/MARKET_REPORT_PDF_PLAYBOOK.md](./docs/plan/MARKET_REPORT_PDF_PLAYBOOK.md) | PDF generation playbook |
| [LOCAL_SETUP_GUIDE.md](./LOCAL_SETUP_GUIDE.md) | Local development setup |

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
