# TrendyReports Architecture

> Last updated: 2025-02-10
> This is the single source of truth for the TrendyReports platform.
> TrendyReports is a **3-service architecture**: API (FastAPI) + Worker (Celery) + Frontend (Next.js 16)

---

## Quick Reference

### Where to Find Things

| I need to... | Look in... |
|--------------|------------|
| Add a new API endpoint | `apps/api/src/api/routes/` |
| Modify database schema | `db/migrations/` (add new .sql file) |
| Add a Celery background task | `apps/worker/src/worker/tasks.py` |
| Change PDF generation | `apps/worker/src/worker/pdf_engine.py` |
| Modify property report templates | `apps/worker/src/worker/templates/property/` |
| Build market report JSON | `apps/worker/src/worker/report_builders.py` |
| Add a frontend page | `apps/web/app/` |
| Modify the report builder wizard | `apps/web/components/report-builder/` |
| Modify the property wizard | `apps/web/components/property/` |
| Modify the schedule builder | `apps/web/components/schedule-builder/` |
| Update email templates | `apps/worker/src/worker/email/template.py` |
| Change route protection | `apps/web/middleware.ts` |
| Modify RLS policies | `db/migrations/` (new migration) + `apps/api/src/api/db.py` |
| Update API client (browser) | `apps/web/lib/api.ts` |
| Update API client (server) | `apps/web/lib/api-server.ts` |
| Modify Stripe billing | `apps/api/src/api/routes/billing.py` + `config/billing.py` |
| Change MLS data fetching | `apps/worker/src/worker/vendors/simplyrets.py` |
| Update SiteX property data | `apps/api/src/api/services/sitex.py` |
| Add AI insights | `apps/worker/src/worker/ai_insights.py` |

### Status Codes

| Entity | Statuses |
|--------|----------|
| Report Generation | `pending` -> `processing` -> `completed` / `failed` |
| Property Report | `pending` -> `processing` -> `completed` / `failed` |
| Consumer Report | `pending` -> `ready` / `failed` |
| Schedule | `active` / `paused` (via `active` boolean) |
| Lead | `new` -> `contacted` -> `converted` |

### User Roles & Account Types

| Role | Scope | Access |
|------|-------|--------|
| `OWNER` | Account | Full account management |
| `MEMBER` | Account | Standard user access |
| `AFFILIATE` | Account | Affiliate agent access |
| `is_platform_admin` | Platform | System-wide admin, bypasses RLS |

| Account Type | Dashboard | Features |
|--------------|-----------|----------|
| `REGULAR` | `/app` | Reports, schedules, property, leads, contacts |
| `INDUSTRY_AFFILIATE` | `/app/affiliate` | Sponsored agents, aggregate analytics |

### Multi-Tenant Architecture

- **PostgreSQL RLS** enforces data isolation at the database level
- Every request sets `app.current_account_id` via middleware
- All tenant-scoped tables have RLS policies filtering by `account_id`
- Admin role bypasses RLS for system-wide operations

---

## Documentation Index

### Core Reference
- [File Tree](./FILE-TREE.md) -- Complete annotated file tree for all 3 services
- [Glossary](./GLOSSARY.md) -- Report types, themes, presets, plans, terms
- [Performance Audit](./performance-audit.md) -- API performance findings by severity

### Backend (API Service)
- [Overview](./backend/OVERVIEW.md) -- Architecture, request lifecycle, env vars
- [Models & Database](./backend/models.md) -- All tables, columns, relationships
- [Middleware](./backend/middleware.md) -- Auth, RLS, rate limiting, CORS
- Routes:
  - [Auth](./backend/routes-auth.md) -- Login, register, password reset, verify email
  - [Reports](./backend/routes-reports.md) -- Market report CRUD + limit enforcement
  - [Property](./backend/routes-property.md) -- Property search, CMA reports
  - [Schedules](./backend/routes-schedules.md) -- Schedule CRUD, pause/resume
  - [Contacts](./backend/routes-contacts.md) -- Contact + group CRUD, import
  - [Leads](./backend/routes-leads.md) -- Lead capture, management, export
  - [Account](./backend/routes-account.md) -- Settings, branding, plan-usage
  - [Billing](./backend/routes-billing.md) -- Stripe checkout, portal, webhooks
  - [Admin](./backend/routes-admin.md) -- Metrics, accounts, users, affiliates
  - [Consumer](./backend/routes-consumer.md) -- Public mobile reports, CMA pages
- Services:
  - [SiteX](./backend/services-sitex.md) -- Property data (OAuth2)
  - [Email](./backend/services-email.md) -- Resend transactional email
  - [SMS](./backend/services-sms.md) -- Twilio SMS
  - [Stripe](./backend/services-stripe.md) -- Plan catalog, billing state

### Worker Service
- [Overview](./worker/OVERVIEW.md) -- Architecture, deployment, env vars
- [Celery Tasks](./worker/tasks.md) -- generate_report, process_consumer_report, property_report
- [PDF Engine](./worker/pdf-engine.md) -- Dual backend: Playwright + PDFShift
- [Property Report Builder](./worker/property-builder.md) -- Jinja2 templates, 5 themes
- [Templates](./worker/templates.md) -- Template inheritance, data contract, CSS
- [Market Report Builder](./worker/market-report-builder.md) -- 8 report type JSON builders
- [SimplyRETS Vendor](./worker/vendors-simplyrets.md) -- MLS data, rate limiting
- [R2 Storage Vendor](./worker/vendors-storage.md) -- PDF/image upload, presigned URLs

### Frontend
- [Overview](./frontend/OVERVIEW.md) -- Architecture, API communication, route protection
- Pages:
  - [Dashboard](./frontend/pages-dashboard.md) -- Dashboard + onboarding
  - [Reports](./frontend/pages-reports.md) -- Report list + builder wizard
  - [Property](./frontend/pages-property.md) -- Property report pages
  - [Schedules](./frontend/pages-schedules.md) -- Schedule management
  - [Contacts](./frontend/pages-contacts.md) -- Contacts + groups
  - [Leads](./frontend/pages-leads.md) -- Lead management
  - [Settings](./frontend/pages-settings.md) -- Profile, security, billing, branding
  - [Admin](./frontend/pages-admin.md) -- Admin console
  - [Affiliate](./frontend/pages-affiliate.md) -- Affiliate dashboard
  - [Public](./frontend/pages-public.md) -- /r/*, /p/*, /cma/*, /print/*, /social/*
- Components:
  - [Report Builder](./frontend/components-report-builder.md) -- Market report wizard
  - [Property Wizard](./frontend/components-property-wizard.md) -- Property report wizard
  - [Schedule Builder](./frontend/components-schedule-builder.md) -- Schedule wizard
  - [UI Components](./frontend/components-ui.md) -- shadcn/ui + custom components
- [Hooks](./frontend/hooks.md) -- Custom React hooks
- [API Client](./frontend/lib-api.md) -- Client + server API functions
- [Utils](./frontend/lib-utils.md) -- Utility functions + templates
- [Middleware](./frontend/middleware.md) -- Next.js route protection

### Integrations
- [Overview](./integrations/OVERVIEW.md) -- All external services summary
- [SimplyRETS](./integrations/simplyrets.md) -- MLS listing data
- [SiteX Pro](./integrations/sitex.md) -- Property details + comparables
- [Stripe](./integrations/stripe.md) -- Subscriptions + billing
- [Resend](./integrations/resend.md) -- Transactional email
- [Twilio](./integrations/twilio.md) -- SMS notifications
- [Cloudflare R2](./integrations/cloudflare-r2.md) -- File storage
- [PDFShift](./integrations/pdfshift.md) -- Cloud PDF rendering
- [Google Maps](./integrations/google-maps.md) -- Places + static maps
- [OpenAI](./integrations/openai.md) -- AI market insights

### Database
- [Schema](./database/SCHEMA.md) -- Complete schema with relationships
- [RLS Policies](./database/rls-policies.md) -- Row-Level Security setup
- [Migrations](./database/migrations.md) -- Migration patterns + commands

### Flows (End-to-End Pipelines)
- [Market Report Generation](./flows/market-report-generation.md) -- User -> API -> Worker -> PDF -> Email
- [Property Report Generation](./flows/property-report-generation.md) -- Search -> Comps -> Jinja2 -> PDF -> QR
- [Scheduled Report Execution](./flows/scheduled-report-execution.md) -- Ticker -> Celery -> Generate -> Email
- [Lead Capture](./flows/lead-capture-flow.md) -- QR -> Form -> SMS -> Agent notification
- [Consumer CMA](./flows/consumer-cma-flow.md) -- Landing -> Search -> SMS delivery
- [Billing](./flows/billing-flow.md) -- Stripe checkout -> Webhook -> Plan activation
- [Authentication](./flows/auth-flow.md) -- Register -> Verify -> Login -> JWT -> RLS

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15 (Render) with Row-Level Security |
| Cache / Queue | Redis (rate limits + Celery broker) |
| Task runner | Celery 5.4 |
| PDF rendering | Playwright (local) + PDFShift (production) |
| Frontend framework | Next.js 16, React 19 |
| UI library | Radix UI + shadcn/ui, Tailwind CSS v4 |
| State management | TanStack React Query v5 |
| Forms | React Hook Form + Zod |
| Auth | Custom JWT (cookie + Bearer + API keys) |
| Payments | Stripe (subscriptions, webhooks) |
| Email (transactional) | Resend (API service) |
| Email (reports) | SendGrid (Worker service) |
| SMS | Twilio |
| MLS data | SimplyRETS (Worker) + SiteX Pro (API) |
| Maps | Google Maps API (Places + Static Maps) |
| AI insights | OpenAI GPT-4o-mini (optional) |
| File storage | Cloudflare R2 (S3-compatible) |
| Hosting | Render (API + Worker + DB), Vercel (frontend) |
