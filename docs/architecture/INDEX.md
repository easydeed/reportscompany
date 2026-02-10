# TrendyReports Architecture Reference

> Quick-reference source tree for the full codebase.
> Each link points to a detailed module doc in this folder.

---

## Backend (`apps/api/src/api/`)

| Doc | Covers | Key Files |
|-----|--------|-----------|
| [backend-core.md](./backend-core.md) | App startup, settings, DB layer, auth utilities | `main.py` `settings.py` `db.py` `auth.py` `worker_client.py` |
| [backend-middleware.md](./backend-middleware.md) | Auth, rate-limiting, RLS middleware | `middleware/authn.py` `middleware/rls.py` |
| [backend-routes.md](./backend-routes.md) | All 26 route modules and their endpoints | `routes/*.py` |
| [backend-services.md](./backend-services.md) | Business logic, integrations, SQL | `services/*.py` `config/` `deps/` `schemas/` |

## Frontend (`apps/web/`)

| Doc | Covers | Key Files |
|-----|--------|-----------|
| [frontend-core.md](./frontend-core.md) | Next.js config, middleware, API clients, providers, hooks | `next.config.ts` `middleware.ts` `lib/` `hooks/` |
| [frontend-pages.md](./frontend-pages.md) | All app-router pages (public + protected + admin) | `app/` |
| [frontend-components.md](./frontend-components.md) | All components by domain | `components/` |
| [frontend-api-proxy.md](./frontend-api-proxy.md) | Next.js API routes that proxy to the backend | `app/api/` |

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
      rls.py                     # RLSContextMiddleware (legacy placeholder)
    routes/                      # 26 route modules (see backend-routes.md)
    services/                    # 15 service modules (see backend-services.md)

  web/                           # Next.js 16 frontend
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
      ui/                        # 50+ Radix/shadcn primitives
      report-builder/            # Report creation wizard
      schedule-builder/          # Schedule creation wizard
      property/                  # Property search + comps
      admin/                     # Admin dashboard components
      marketing/                 # Landing page sections
      onboarding/                # Onboarding wizard
      branding/                  # Branding preview + tools
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15 (Render) with RLS |
| Cache / Queue | Redis (rate limits + Celery broker) |
| Task runner | Celery |
| Frontend framework | Next.js 16, React 19 |
| UI library | Radix UI + shadcn/ui, Tailwind CSS v4 |
| State management | TanStack React Query v5 |
| Forms | React Hook Form + Zod |
| Auth | Custom JWT (cookie + Bearer) |
| Payments | Stripe (subscriptions, webhooks) |
| Email | Resend |
| SMS | Twilio |
| MLS data | SimplyRETS, SiteX |
| Maps | Google Maps API |
| Hosting | Render (API + DB), Vercel (frontend) |
