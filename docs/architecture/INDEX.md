# TrendyReports Architecture Reference

> Quick-reference source tree for the full codebase.
> Each link points to a detailed module doc in this folder.
>
> **See also:** [SOURCE_OF_TRUTH.md](./SOURCE_OF_TRUTH.md) · [WIZARD_AND_API_CALLS.md](./WIZARD_AND_API_CALLS.md) · [SITE_ARCHITECTURE_TREE.md](./SITE_ARCHITECTURE_TREE.md) · [ARCHITECTURE_AUDIT.md](./ARCHITECTURE_AUDIT.md)

---

## Backend (`apps/api/src/api/`)

| Doc | Covers | Key Files |
|-----|--------|-----------|
| [backend-core.md](./backend-core.md) | App startup, settings, DB layer, auth utilities | `main.py` `settings.py` `db.py` `auth.py` `worker_client.py` |
| [backend-middleware.md](./backend-middleware.md) | Auth, rate-limiting, RLS middleware | `middleware/authn.py` `middleware/rls.py` |
| [backend-routes.md](./backend-routes.md) | All 26 route modules and their endpoints | `routes/*.py` |
| [backend-services.md](./backend-services.md) | Business logic, integrations, SQL | `services/*.py` `config/` `deps/` `schemas/` |

### Key API Module Docs (Detailed)

| Doc | Covers | Key Files |
|-----|--------|-----------|
| [modules/simplyrets-api-service.md](./modules/simplyrets-api-service.md) | API-layer SimplyRETS client | `services/simplyrets.py` |
| [modules/sitex-api-service.md](./modules/sitex-api-service.md) | SiteX Pro OAuth2 client (subject property) | `services/sitex.py` |
| [modules/property-routes-comparables.md](./modules/property-routes-comparables.md) | Property search + comparables fallback ladder (L0–L5) | `routes/property.py` |
| [modules/admin-metrics-routes.md](./modules/admin-metrics-routes.md) | Platform analytics endpoints | `routes/admin_metrics.py` |
| [property-type-data-contract.md](./property-type-data-contract.md) | SiteX UseCode → SimplyRETS type/subtype mapping | `schemas/property.py` |

## Worker (`apps/worker/src/worker/`)

| Doc | Covers | Key Files |
|-----|--------|-----------|
| [modules/worker-core.md](./modules/worker-core.md) | Celery app, schedule tick, Redis cache, limit checker | `app.py` `schedules_tick.py` `cache.py` `limit_checker.py` |
| [modules/worker-tasks.md](./modules/worker-tasks.md) | Celery task definitions (market + property report pipelines) | `tasks.py` |
| [modules/property-builder.md](./modules/property-builder.md) | Jinja2 HTML renderer for property reports (5 themes, 7 pages) | `property_builder.py` `templates/property/` |
| [modules/filter-resolver.md](./modules/filter-resolver.md) | Market-adaptive filter resolution + elastic widening | `filter_resolver.py` |
| [modules/worker-simplyrets-vendor.md](./modules/worker-simplyrets-vendor.md) | Synchronous SimplyRETS client with rate limiter + pagination | `vendors/simplyrets.py` |

## Frontend (`apps/web/`)

| Doc | Covers | Key Files |
|-----|--------|-----------|
| [frontend-core.md](./frontend-core.md) | Next.js config, middleware, API clients, providers, hooks | `next.config.ts` `middleware.ts` `lib/` `hooks/` |
| [frontend-pages.md](./frontend-pages.md) | All app-router pages (public + protected + admin) | `app/` |
| [frontend-components.md](./frontend-components.md) | All components by domain | `components/` |
| [frontend-api-proxy.md](./frontend-api-proxy.md) | Next.js API routes that proxy to the backend | `app/api/` |

## Tests & CLI Tools

| Doc | Covers | Key Files |
|-----|--------|-----------|
| [modules/test-suite.md](./modules/test-suite.md) | pytest templates tests + Playwright E2E | `tests/` `e2e/` `pytest.ini` |
| [modules/cli-tools.md](./modules/cli-tools.md) | QA delivery + smoke test scripts | `qa_deliver_reports.py` `scripts/test_*.py` |

## Cross-Cutting

| Doc | Covers |
|-----|--------|
| [performance-audit.md](./performance-audit.md) | Full performance audit with findings by severity |

---

## Source Tree (abridged)

```
apps/
  api/src/api/                   # FastAPI backend
    main.py                      # App init, middleware registration, router includes
    settings.py                  # Pydantic env settings (DB, Redis, Stripe, JWT)
    db.py                        # Connection helper, RLS setter, dict helpers
    auth.py                      # JWT sign/verify, password hash, API key hash
    worker_client.py             # Celery/Redis task enqueue
    config/
      billing.py                 # Stripe price-ID mapping
    deps/
      admin.py                   # FastAPI dependency: require platform admin
    schemas/
      property.py                # Pydantic models for property data
    middleware/
      authn.py                   # AuthContextMiddleware + RateLimitMiddleware
      rls.py                     # RLSContextMiddleware
    routes/                      # 26 route modules (see backend-routes.md)
      property.py                # ← comparables fallback ladder L0-L5 [updated]
      admin_metrics.py           # ← platform analytics [new]
    services/                    # 15+ service modules (see backend-services.md)
      simplyrets.py              # ← API-layer SimplyRETS client [new]
      sitex.py                   # ← SiteX Pro client [new]

  worker/src/worker/             # Celery background worker
    app.py                       # Celery init + beat schedule
    tasks.py                     # generate_report, generate_property_report_task
    schedules_tick.py            # Every-minute schedule executor
    property_builder.py          # ← Jinja2 HTML renderer, 5 themes [new]
    filter_resolver.py           # ← Market-adaptive filters + elastic widen [new]
    limit_checker.py             # Worker-context plan enforcement
    cache.py                     # Redis caching layer
    vendors/
      simplyrets.py              # ← Sync SimplyRETS client, rate limiter [new]
    compute/
      calc.py                    # Statistical calculations
      extract.py                 # Data extraction
      validate.py                # Data validation
    templates/property/          # 5 themes × 2 Jinja2 templates each
      classic/ modern/ elegant/ teal/ bold/

  web/                           # Next.js 16 frontend (Vercel)
    middleware.ts                # JWT auth guard for /app/* routes
    next.config.ts               # React Compiler, Turbopack
    lib/
      api.ts                     # Client-side fetch (goes through /api/proxy)
      api-server.ts              # Server-side fetch (direct to backend)
      utils.ts                   # cn(), helpers
      hooks/
        use-user.ts              # React Query user hook
        use-plan-usage.ts        # Plan usage hook
    app/
      app/                       # Protected routes (auth required)
        admin/                   # Platform admin pages
        affiliate/               # Affiliate dashboard
        property/                # Property reports
        reports/                 # Report management
        schedules/               # Schedule management
        people/                  # Contacts
        leads/                   # Lead management
        settings/                # User settings
        billing/                 # Billing page
        branding/                # Branding editor
      api/proxy/                 # ~60 proxy routes to backend
    components/
      ui/                        # 75 Radix/shadcn primitives
      report-builder/            # Market report creation wizard
      schedule-builder/          # Schedule creation wizard
      property/                  # Property search + comps picker
      property-wizard/           # Property report wizard steps
      admin/                     # Admin dashboard components
      marketing/                 # Landing page sections
      onboarding/                # Onboarding wizard
      branding/                  # Branding preview + tools

tests/
  test_property_templates.py     # pytest: 5 themes × 6 test classes [new]

e2e/
  auth.spec.ts                   # Playwright: auth flows
  affiliate.spec.ts              # Playwright: affiliate flows
  plan.spec.ts                   # Playwright: plan management
  stripe.spec.ts                 # Playwright: Stripe webhooks

scripts/                         # Dev/QA scripts (not production)
  test_simplyrets.py             # ← SimplyRETS smoke test [new]
  test_sitex.py                  # ← SiteX smoke test [new]
  test_property_report_flow.py   # ← Property flow integration test [new]
  generate_all_property_pdfs.py  # Batch PDF generation
  generate_theme_previews.py     # Theme preview PNGs

qa_deliver_reports.py            # ← End-to-end QA delivery tool [new]
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15 (Render) with RLS |
| Cache / Queue | Redis (rate limits + Celery broker) |
| Task runner | Celery |
| PDF generation | PDFShift API |
| AI insights | OpenAI GPT-4o-mini |
| MLS data | SimplyRETS (market + comps) + SiteX Pro (subject property) |
| Frontend framework | Next.js 16, React 19 |
| UI library | Radix UI + shadcn/ui, Tailwind CSS v4 |
| State management | TanStack React Query v5 |
| Forms | React Hook Form + Zod |
| Auth | Custom JWT (HttpOnly cookie + Bearer) |
| Payments | Stripe (subscriptions, webhooks) |
| Email | SendGrid (worker), Resend (API layer) |
| SMS | Twilio |
| Maps | Google Maps Static API |
| File storage | Cloudflare R2 |
| Hosting | Render (API + Worker + DB), Vercel (frontend) |
