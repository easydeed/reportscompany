# TrendyReports Technical Documentation

> Complete technical documentation for the TrendyReports SaaS platform.

---

## Overview

TrendyReports is a white-label market report generation platform for real estate professionals. The platform provides automated PDF reports, email delivery, and white-label branding for agents and title companies (affiliates).

---

## Documentation Index

### Core Features

| Document | Description |
|----------|-------------|
| [EMAIL_SYSTEM.md](./EMAIL_SYSTEM.md) | Email infrastructure, templates, and delivery pipeline |
| [PDF_REPORTS.md](./PDF_REPORTS.md) | PDF generation, templates, and white-label branding |
| [SCHEDULES.md](./SCHEDULES.md) | Automated report scheduling system |
| [REPORT_TYPES_MATRIX.md](./REPORT_TYPES_MATRIX.md) | Report types, parameters, and output specifications |

### User Management

| Document | Description |
|----------|-------------|
| [USER_ONBOARDING.md](./USER_ONBOARDING.md) | New user onboarding flow and setup wizard |
| [ACCOUNT_SETTINGS.md](./ACCOUNT_SETTINGS.md) | User profile and security settings |
| [AUTH_ARCHITECTURE_V1.md](./AUTH_ARCHITECTURE_V1.md) | Authentication, JWT tokens, and session management |

### Business Features

| Document | Description |
|----------|-------------|
| [BRANDING.md](./BRANDING.md) | White-label branding system for logos, colors, and contact info |
| [TITLE_COMPANY_ONBOARDING.md](./TITLE_COMPANY_ONBOARDING.md) | Affiliate (title company) setup and agent sponsorship |
| [SOCIAL_MEDIA_SHARING.md](./SOCIAL_MEDIA_SHARING.md) | Social media image generation for stories/reels |

### Administration

| Document | Description |
|----------|-------------|
| [ADMIN_CONSOLE.md](./ADMIN_CONSOLE.md) | Platform admin dashboard and system management |

### Integrations

| Document | Description |
|----------|-------------|
| [SIMPLYRETS_API.md](./SIMPLYRETS_API.md) | MLS data integration via SimplyRETS API |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TrendyReports                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Next.js    │────▶│   FastAPI    │────▶│   Worker     │     │
│  │   Frontend   │     │   Backend    │     │   (Celery)   │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│         │                    │                    │              │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Vercel     │     │   Render     │     │   Render     │     │
│  │   (Hosting)  │     │   (API)      │     │   (Workers)  │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │  PostgreSQL  │     │    Redis     │     │ Cloudflare   │     │
│  │  (Database)  │     │   (Queue)    │     │  R2 (Files)  │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Technologies

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS |
| Backend API | FastAPI, Python 3.11 |
| Worker | Celery, Python |
| Database | PostgreSQL with Row-Level Security (RLS) |
| Queue | Redis |
| File Storage | Cloudflare R2 |
| Email | SendGrid |
| PDF Generation | PDFShift / Playwright |
| MLS Data | SimplyRETS API |
| Hosting | Vercel (Web), Render (API, Workers) |

---

## Environment Configuration

All services require environment variables for:
- Database connection (`DATABASE_URL`)
- Redis connection (`REDIS_URL`)
- JWT secret (`JWT_SECRET`)
- SendGrid API key (`SENDGRID_API_KEY`)
- Cloudflare R2 credentials (`R2_*`)
- SimplyRETS credentials (`SIMPLYRETS_*`)

See individual service documentation for complete environment variable requirements.

---

## Getting Started

1. Review the [Architecture Overview](#architecture-overview) above
2. Set up environment variables per service requirements
3. Run database migrations from `db/migrations/`
4. Deploy services to respective platforms

For detailed setup instructions, see individual documentation files.

---

*This documentation represents the complete technical specification for TrendyReports.*

