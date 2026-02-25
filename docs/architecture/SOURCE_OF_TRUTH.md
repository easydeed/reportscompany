# TrendyReports — Architecture Source of Truth

> **Version:** 15 (Feb 2026)
> **Updated by:** Architecture docs audit (Feb 2026)
> **Previous version:** `SourceOfTruth.md` (V14, root-level, Jan 2026)

---

## 1. System Overview

TrendyReports is a **multi-tenant SaaS platform** that transforms live MLS data (via SimplyRETS + SiteX) into branded PDF reports and email campaigns for real estate agents and their affiliated title/escrow companies.

**Two primary report families:**

| Family | Description |
|--------|-------------|
| **Market Reports** | Area-level snapshots: New Listings, Closed Sales, Inventory, Price Bands, etc. Delivered via automated schedules (email + optional PDF). |
| **Property Reports** | Subject-property comparables analysis (CMA-style): PDF with cover, aerial, comparables, price range chart. Agent-branded. |

**Target users:**
1. **Individual agents** — create and schedule reports for their client lists
2. **Affiliates** (title companies, lenders) — white-label reports on behalf of sponsored agents

---

## 2. Major Components

### 2.1 Frontend — `apps/web` (Next.js 16, React 19)

| Sub-system | Path | Description |
|-----------|------|-------------|
| App router pages | `app/` | 50+ routes (public, protected `/app/*`, admin `/app/admin/*`) |
| API proxy | `app/api/proxy/` | ~60 Next.js API routes that forward to FastAPI backend |
| UI components | `components/` | 162 components (Radix UI + shadcn/ui primitives, domain components) |
| Shared lib | `lib/` | Client fetch utilities, React Query hooks, type definitions |

**Auth guard:** `middleware.ts` protects all `/app/*` routes via JWT cookie validation.

**Hosting:** Vercel

### 2.2 API Backend — `apps/api` (FastAPI, Python 3.11+)

| Sub-system | Path | Description |
|-----------|------|-------------|
| App bootstrap | `src/api/main.py` | FastAPI app, 26 router mounts, middleware registration |
| Routes | `src/api/routes/` | 26 modules covering auth, reports, schedules, billing, property, admin |
| Services | `src/api/services/` | 15+ business logic modules (SimplyRETS, SiteX, email, branding, billing, etc.) |
| Middleware | `src/api/middleware/` | Auth context, rate limiting, RLS context |
| Schemas | `src/api/schemas/` | Pydantic data models |

**Key route groups:**
- `auth.py` — Login, signup, password reset, email verification, invite accept
- `property.py` — Subject search (SiteX), comparables (SimplyRETS fallback ladder), PDF generation
- `reports.py` — Market report CRUD + task enqueueing
- `schedules.py` — Schedule CRUD (city, filters, cadence, recipients)
- `billing.py` + `stripe_webhook.py` — Stripe subscriptions
- `admin.py` + `admin_metrics.py` — Platform admin, analytics

**Hosting:** Render (background service)

### 2.3 Background Worker — `apps/worker` (Celery, Python 3.11+)

| Sub-system | Path | Description |
|-----------|------|-------------|
| Celery app | `src/worker/app.py` | App init, beat schedule |
| Tasks | `src/worker/tasks.py` | `generate_report`, `generate_property_report_task`, `keep_alive_ping` |
| Schedule tick | `src/worker/schedules_tick.py` | Every-minute tick that fires due schedules |
| Property builder | `src/worker/property_builder.py` | Jinja2 HTML renderer for property reports (5 themes) |
| Filter resolver | `src/worker/filter_resolver.py` | Market-adaptive filter resolution + elastic widening |
| SimplyRETS vendor | `src/worker/vendors/simplyrets.py` | Synchronous SimplyRETS client with rate limiter + pagination |
| PDF adapter | `src/worker/pdf_adapter.py` | PDFShift API integration |
| AI insights | `src/worker/ai_insights.py` | GPT-4o-mini market commentary |
| Email templates | `src/worker/templates/property/` | 5 email theme templates (Jinja2) |

**Hosting:** Render (background worker)

### 2.4 Shared Libraries — `libs/` + `packages/`

| Package | Path | Description |
|---------|------|-------------|
| `shared` (Python) | `libs/shared/` | Shared email template utilities |
| `ui` (TypeScript) | `packages/ui/` | 60+ React components shared across `apps/web`, `reportsbuilder`, `scheduledreports` |

### 2.5 Development Tools — `reportsbuilder/`, `scheduledreports/`, `emailpreview/`

Standalone Next.js preview apps for developing report layouts, schedule builders, and email templates. **Not deployed to production.**

### 2.6 Database — `db/`

- 42 SQL migration files (PostgreSQL 15)
- Row-Level Security (RLS) for multi-tenant data isolation
- Managed via `scripts/run_migrations.py`

**Hosting:** Render Postgres

---

## 3. External Integrations

| Service | Purpose | Auth Method |
|---------|---------|------------|
| **SimplyRETS** | Live MLS listing data (comparables + market snapshots) | HTTP Basic Auth (key:secret) |
| **SiteX Pro** | Property assessor data (subject property lookup) | OAuth2 Client Credentials |
| **PDFShift** | HTML → PDF rendering | HTTP Basic Auth |
| **SendGrid** | Transactional email delivery | API Key |
| **OpenAI** | GPT-4o-mini market commentary | API Key (Bearer) |
| **Stripe** | Subscription billing, webhooks | API Key + Webhook Secret |
| **Cloudflare R2** | PDF + logo storage, photo proxy | Access Key + Secret |
| **Google Maps** | Aerial + street view images for property reports | API Key |
| **Twilio** | SMS notifications (optional) | Account SID + Auth Token |
| **Resend** | Transactional email (alternative path) | API Key |

---

## 4. Core Data Models

### 4.1 Key Database Tables

| Table | Description |
|-------|-------------|
| `accounts` | Multi-tenant account (agent or affiliate). Has `account_type`, `plan_slug`, `sponsor_account_id`. |
| `users` | Platform users. Many-to-many with `accounts` via `account_users`. Has `is_platform_admin`. |
| `plans` | Plan catalog (free, pro, team, affiliate, sponsored_free). Limits + Stripe price IDs. |
| `report_generations` | Every market report generated. Has `schedule_id`, `status`, `generated_at`. |
| `schedules` | Automated report schedules. Has `city`, `filters_intent` (JSON), `cadence`, `next_run_at`. |
| `schedule_runs` | Individual execution records. Has `status`, `sent_count`, `failure_reason`. |
| `property_reports` | Property report records. Has `comparables` (JSONB), `selected_pages`, `pdf_url`, `status`. |
| `contacts` | Agent's contact list. Has `email`, `phone`, `contact_group_id`. |
| `contact_groups` | Contact group definitions. |
| `affiliate_branding` | White-label branding per affiliate. Has 4 logo slots, color overrides. |
| `webhook_endpoints` | Registered webhooks per account. |
| `email_suppressions` | Unsubscribed emails (never re-send). |

### 4.2 Report Data Payload (`report_generations`)

The `payload` JSONB column stores the full context used to generate each report:

```json
{
  "city": "Irvine",
  "report_type": "market_snapshot",
  "date_range": {"from": "2026-01-01", "to": "2026-01-31"},
  "filters": {"type": "residential", "maxprice": 560000, "minbeds": 2},
  "filters_label": "2+ beds, under $560,000 (70% of Irvine median)",
  "listings": [...],
  "market_stats": {"median_list_price": 800000, "median_close_price": 785000},
  "ai_insights": "The Irvine market...",
  "branding": {"agent_name": "...", "logo_url": "..."}
}
```

### 4.3 Market Snapshot Payload

```json
{
  "total_listings": 42,
  "median_price": 785000,
  "avg_days_on_market": 18,
  "price_per_sqft": 520,
  "active_count": 28,
  "closed_count": 14,
  "price_change_pct": -2.3
}
```

### 4.4 Comparables Payload (`property_reports`)

```json
{
  "comparables": [
    {
      "address": "123 Main St, La Verne, CA",
      "price": 750000,
      "sqft": 1850,
      "beds": 3,
      "baths": 2.0,
      "status": "Closed",
      "lat": 34.1003,
      "lng": -117.7678,
      "distance_miles": 0.4,
      "photo_url": "https://...",
      "days_on_market": 12,
      "price_per_sqft": 405,
      "subtype": "SingleFamilyResidence"
    }
  ],
  "confidence": "A",
  "ladder_level_used": 0
}
```

### 4.5 Filters Intent (Schedule)

```json
{
  "type": "residential",
  "subtype": "singlefamilyresidence",
  "minbeds": 2,
  "minbaths": 2,
  "price_strategy": "maxprice_pct_of_median_list",
  "price_pct": 70
}
```

---

## 5. Authentication & Security

| Mechanism | Details |
|-----------|---------|
| **Session JWT** | Signed HS256, stored in `HttpOnly` cookie `mr_token`. 1-hour TTL (7-day for invite accept). |
| **API keys** | SHA-256 hashed in DB. Used for programmatic API access. |
| **Password storage** | bcrypt |
| **RLS** | PostgreSQL Row-Level Security on all tenant tables. `SET app.current_account_id` per request. |
| **Admin gate** | `is_platform_admin` flag on `users`. `deps/admin.py` enforces for all `/admin` routes. |
| **Rate limiting** | Redis-backed per-IP rate limiter in `middleware/authn.py`. |
| **JWT blacklist** | `jwt_blacklist` table for revoked tokens (logout). |
| **Webhook signatures** | HMAC-SHA256 on all outbound webhook payloads. `X-TrendyReports-Signature` header. |
| **Credentials** | Never stored in code; all secrets via environment variables. See `.env.example`. |

---

## 6. Report Types

| Type | Key | Description |
|------|-----|-------------|
| Market Snapshot | `market_snapshot` | Overview KPIs: count, median price, DOM, price/sqft |
| New Listings | `new_listings` | Active listings in date range |
| Closed Sales | `closed_sales` | Closed transactions in date range |
| Inventory | `inventory` | Active inventory trend |
| Price Bands | `price_bands` | Distribution by price segment |
| New Listings Gallery | `new_listings_gallery` | Photo-rich gallery of new listings |
| Featured Listings | `featured_listings` | Curated highlights |
| Open Houses | `open_houses` | Upcoming open house schedule |

---

## 7. Smart Presets (Market-Adaptive Audience Filters)

| Preset | type | minbeds | minbaths | Price strategy | price_pct |
|--------|------|---------|----------|---------------|-----------|
| First-Time Buyer | SFR | 2 | 2 | `maxprice_pct_of_median_list` | 70 |
| Investor Deals | All | — | — | `maxprice_pct_of_median_close` | 50 |
| Luxury Showcase | SFR | — | — | `minprice_pct_of_median_list` | 150 |
| Condo Watch | Condo | 1 | — | — | — |
| Family Homes | SFR | 4 | 2 | — | — |

Price caps are resolved dynamically at generation time using the market median for the report's city and date range.

---

## 8. Subscription Plans

| Plan | Monthly limit | Overage | Stripe |
|------|--------------|---------|--------|
| `free` | 5 reports | No | No card |
| `pro` | 50 reports | No | $29/mo |
| `team` | 200 reports | No | $99/mo |
| `affiliate` | 500 reports | Custom | Custom |
| `sponsored_free` | 10 reports | No | $0 (affiliate-sponsored) |

---

## 9. Observability & Testing Entry Points

### Unit / Integration Tests
```bash
pytest tests/test_property_templates.py -v
```

### E2E Tests
```bash
npx playwright test
```

### API Smoke Tests
```bash
python scripts/test_simplyrets.py
python scripts/test_sitex.py
python scripts/test_property_report_flow.py
python scripts/test_all_reports.py
```

### QA Delivery
```bash
python qa_deliver_reports.py \
  --base-url https://reportscompany.onrender.com \
  --token $JWT_TOKEN \
  --deliver-to qa@example.com \
  --city Irvine
```

### Health Check
```
GET /health → {"status": "ok", "db": "ok", "redis": "ok"}
```

### Admin Metrics
```
GET /v1/admin/metrics/overview (requires is_platform_admin=true)
```

---

## 10. Infrastructure Stack

| Component | Technology | Host |
|-----------|-----------|------|
| Frontend | Next.js 16, React 19, Tailwind CSS v4 | Vercel |
| API | FastAPI, Python 3.11+, Poetry | Render |
| Worker | Celery 5, Python 3.11+ | Render |
| Database | PostgreSQL 15 + RLS | Render |
| Cache / Queue | Redis | Render |
| File storage | Cloudflare R2 | Cloudflare |
| Package manager | pnpm 9.12.3 | — |
| Node version | 20.x (`.nvmrc`) | — |

---

## 11. Architecture Docs Index

| Document | Description |
|----------|-------------|
| [INDEX.md](./INDEX.md) | Quick-reference source tree |
| [WIZARD_AND_API_CALLS.md](./WIZARD_AND_API_CALLS.md) | Wizard flows, sequence diagrams, full API reference |
| [SITE_ARCHITECTURE_TREE.md](./SITE_ARCHITECTURE_TREE.md) | Directory tree + logical component tree |
| [ARCHITECTURE_AUDIT.md](./ARCHITECTURE_AUDIT.md) | Docs inventory, status, and audit trail |
| [backend-core.md](./backend-core.md) | FastAPI app startup, DB, auth, settings |
| [backend-middleware.md](./backend-middleware.md) | Auth, rate-limit, RLS middleware |
| [backend-routes.md](./backend-routes.md) | All 26 API routes |
| [backend-services.md](./backend-services.md) | Business logic service modules |
| [frontend-core.md](./frontend-core.md) | Next.js config, middleware, API clients |
| [frontend-pages.md](./frontend-pages.md) | All app-router pages |
| [frontend-components.md](./frontend-components.md) | Component organization |
| [frontend-api-proxy.md](./frontend-api-proxy.md) | Next.js proxy routes |
| [property-type-data-contract.md](./property-type-data-contract.md) | SiteX → SimplyRETS type mapping |
| [performance-audit.md](./performance-audit.md) | Performance findings |
| **modules/** | Detailed module docs (new) |
| [modules/simplyrets-api-service.md](./modules/simplyrets-api-service.md) | API-layer SimplyRETS client |
| [modules/sitex-api-service.md](./modules/sitex-api-service.md) | SiteX Pro API client |
| [modules/property-routes-comparables.md](./modules/property-routes-comparables.md) | Comparables route + fallback ladder |
| [modules/worker-simplyrets-vendor.md](./modules/worker-simplyrets-vendor.md) | Worker-layer SimplyRETS client |
| [modules/worker-tasks.md](./modules/worker-tasks.md) | Celery task definitions |
| [modules/property-builder.md](./modules/property-builder.md) | Property report HTML renderer |
| [modules/filter-resolver.md](./modules/filter-resolver.md) | Market-adaptive filter resolution |
| [modules/worker-core.md](./modules/worker-core.md) | Celery app, schedule tick, cache |
| [modules/admin-metrics-routes.md](./modules/admin-metrics-routes.md) | Admin analytics endpoints |
| [modules/cli-tools.md](./modules/cli-tools.md) | CLI / QA tools reference |
| [modules/test-suite.md](./modules/test-suite.md) | Automated test suite |
