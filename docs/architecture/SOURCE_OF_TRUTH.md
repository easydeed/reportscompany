# TrendyReports — Architecture Source of Truth

> **Version:** 16 (Apr 2026)
> **Updated by:** Documenter agent — full code-verified audit
> **Previous version:** V15 (Feb 2026)

---

## Change Log

| Date | Change |
|------|--------|
| 2026-04 | **Audit:** V16 — full code-verified rewrite. Fixed Next.js version (16.0.7), router count (28), migration count (46), report type key (`closed` not `closed_sales`), RLS middleware status (placeholder, not registered), property tasks module path, services count, component counts. Removed 13 dead doc links from V14. |
| 2026-02 | **Audit:** V15 — architecture docs audit, module docs index added. |
| 2026-01 | **Feature:** V14 — sender-aware AI insights, audience-based listing caps. |

---

## 1. System Overview

TrendyReports is a **multi-tenant SaaS platform** that transforms live MLS data (via SimplyRETS + SiteX) into branded PDF reports and email campaigns for real estate agents and their affiliated title/escrow companies.

**Two primary report families:**

| Family | Description |
|--------|-------------|
| **Market Reports** | Area-level snapshots: New Listings, Closed Sales, Inventory, Price Bands, etc. Delivered via automated schedules (email + optional PDF). 8 report types. |
| **Property Reports** | Subject-property comparables analysis (CMA-style): PDF with cover, AI executive summary, aerial, comparables, market trends, price range chart. Agent-branded with Smart Color System. 5 themes. |

**Target users:**
1. **Individual agents** — create and schedule reports for their client lists
2. **Affiliates** (title companies, lenders) — white-label reports on behalf of sponsored agents

---

## 2. Major Components

### 2.1 Frontend — `apps/web` (Next.js 16.0.7, React 19.2.0, Tailwind CSS v4)

| Sub-system | Path | Description |
|-----------|------|-------------|
| App router pages | `app/` | 50+ routes (public, protected `/app/*`, admin `/app/admin/*`) |
| API proxy | `app/api/proxy/` | Next.js API routes that forward to FastAPI backend |
| UI components | `components/` | 181 component files (Radix UI + shadcn/ui primitives, domain components) |
| Shared lib | `lib/` | Client fetch utilities (`api.ts`, `api-server.ts`), React Query hooks (`hooks/use-api.ts`), type definitions (`wizard-types.ts`, `templates.ts`) |
| Report types | `app/lib/reportTypes.ts` | Single source of truth for frontend report type definitions (8 types) |

**Auth guard:** `middleware.ts` protects all `/app/*` routes via JWT cookie validation.

**Hosting:** Vercel

**Key dependencies:** `next@16.0.7`, `react@19.2.0`, `@tanstack/react-query@^5.90`, `zod@^4.1`, `recharts@^3.3`, `framer-motion@^12.23`, `lucide-react@^0.552`

### 2.2 API Backend — `apps/api` (FastAPI, Python 3.11+)

| Sub-system | Path | Description |
|-----------|------|-------------|
| App bootstrap | `src/api/main.py` | FastAPI app, **28 router mounts**, middleware registration (L38–L118) |
| Routes | `src/api/routes/` | 28 modules covering auth, reports, schedules, billing, property, admin, leads, lead pages |
| Services | `src/api/services/` | 15 business logic modules (SimplyRETS, SiteX, email, branding, billing, plans, usage, etc.) |
| Middleware | `src/api/middleware/` | `AuthContextMiddleware` + `RateLimitMiddleware` (active); `RLSContextMiddleware` (placeholder, **not registered**) |
| Schemas | `src/api/schemas/` | Pydantic data models (`property.py`) |
| Config | `src/api/config/` | `billing.py` — Stripe price mapping |

**Route modules (28, registered in `main.py` L91–L118):**

| Router | Module | Purpose |
|--------|--------|---------|
| `health` | `routes/health.py` | Health check endpoint |
| `auth` | `routes/auth.py` | Login, signup, password reset, email verification, invite accept |
| `apikeys` | `routes/apikeys.py` | API key management |
| `webhooks` | `routes/webhooks.py` | Webhook endpoint registration |
| `devfiles` | `routes/devfiles.py` | Development file access |
| `billing` | `routes/billing.py` | Stripe checkout + portal |
| `stripe_webhook` | `routes/stripe_webhook.py` | Stripe webhook handler |
| `reports` | `routes/reports.py` | Market report CRUD + task enqueueing |
| `report_data` | `routes/report_data.py` | Report data retrieval |
| `account` | `routes/account.py` | Account management |
| `usage` | `routes/usage.py` | Usage tracking and limits |
| `schedules` | `routes/schedules.py` | Schedule CRUD (city, filters, cadence, recipients) |
| `unsubscribe` | `routes/unsubscribe.py` | Email unsubscribe handling |
| `admin` | `routes/admin.py` | Platform admin CRUD |
| `me` | `routes/me.py` | Current user profile |
| `affiliates` | `routes/affiliates.py` | Affiliate management |
| `contacts` | `routes/contacts.py` | Contact CRUD |
| `contact_groups` | `routes/contact_groups.py` | Contact group management |
| `dev_stripe_prices` | `routes/dev_stripe_prices.py` | Dev-only Stripe price listing |
| `upload` | `routes/upload.py` | File upload to R2 |
| `branding_tools` | `routes/branding_tools.py` | Branding asset management |
| `users` | `routes/users.py` | User administration |
| `onboarding` | `routes/onboarding.py` | User onboarding flow |
| `leads` | `routes/leads.py` | Lead capture |
| `property` | `routes/property.py` | Subject search (SiteX), comparables (SimplyRETS fallback ladder), PDF generation |
| `mobile_reports` | `routes/mobile_reports.py` | Mobile-optimized report access |
| `admin_metrics` | `routes/admin_metrics.py` | Platform analytics |
| `lead_pages` | `routes/lead_pages.py` | Lead capture page management |

**Middleware stack (LIFO order in `main.py` L55–88):**
1. Timing middleware (`@app.middleware("http")`) — executes first, logs slow requests (>1s)
2. `AuthContextMiddleware` — JWT/API-key auth, sets `request.state.account_id` + `request.state.user`
3. `RateLimitMiddleware` — Redis token bucket, per-account rate limiting

> **Note:** `RLSContextMiddleware` in `middleware/rls.py` is a **placeholder** (accepts `X-Demo-Account` header). It is explicitly **not registered** in `main.py` (see L70–71). RLS session vars are set via `db.set_rls`, not this middleware.

**Hosting:** Render (web service)

**Key dependencies:** `fastapi@^0.115`, `psycopg@^3.2.1` (with binary), `celery@^5.4`, `stripe@^10.0`, `httpx@^0.27.2`, `boto3@^1.35`, `PyJWT@^2.9`, `bcrypt@^4.2`, `qrcode@^7.4`, `Pillow@^10.0`

### 2.3 Background Worker — `apps/worker` (Celery 5, Python 3.11+)

| Sub-system | Path | Description |
|-----------|------|-------------|
| Celery app | `src/worker/app.py` | App init, Redis broker (SSL-aware), beat schedule (L29–63) |
| Market report tasks | `src/worker/tasks.py` | `generate_report` (L778), `process_consumer_report` (L1382), `ping` (L308), `keep_alive_ping` (L313) |
| Property report tasks | `src/worker/property_tasks/property_report.py` | Property report generation Celery task |
| Market builder | `src/worker/market_builder.py` | `MarketReportBuilder` class — Jinja2 HTML renderer for market reports (L70) |
| Property builder | `src/worker/property_builder.py` | `PropertyReportBuilder` class — Jinja2 HTML renderer for property reports (5 themes, 9 pages, Smart Color System) (L206) |
| Report builders | `src/worker/report_builders.py` | Pure-function builders for all 8 market report types: `build_market_snapshot_result` (L59), `build_new_listings_result` (L336), `build_inventory_result` (L414), `build_closed_result` (L499), `build_price_bands_result` (L575), `build_new_listings_gallery_result` (L704), `build_featured_listings_result` (L830), `build_result_json` (L892) |
| Schedule tick | `src/worker/schedules_tick.py` | Minute-by-minute scheduler: `process_due_schedules()` (L309), `run_forever()` (L437), `compute_next_run()` (L116) |
| Filter resolver | `src/worker/filter_resolver.py` | Market-adaptive filter resolution + elastic widening |
| SimplyRETS vendor | `src/worker/vendors/simplyrets.py` | Synchronous SimplyRETS client with `RateLimiter` (L17), `fetch_properties` (L79) |
| PDF engine | `src/worker/pdf_engine.py` | `render_pdf()` (L218) — delegates to Playwright or PDFShift |
| PDF adapter | `src/worker/pdf_adapter.py` | `generate_pdf()` (L22) — Playwright → PDFShift fallback |
| AI insights | `src/worker/ai_insights.py` | `generate_insight()` (L82) — GPT-4o-mini market commentary, sender-aware tone |
| AI market narrative | `src/worker/ai_market_narrative.py` | `generate_market_pdf_narrative()` (L177) — PDF-specific narrative with Redis caching |
| AI overview | `src/worker/ai_overview.py` | `generate_overview()` (L50) — GPT-4o-mini property executive summary |
| Social engine | `src/worker/social_engine.py` | `render_social_image()` (L36) — 1080×1920 branded images |
| Email send | `src/worker/email/send.py` | `send_schedule_email()` (L36) — SendGrid delivery + unsubscribe tokens |
| Email templates | `src/worker/email/template.py` | `schedule_email_html()` (L1682), `schedule_email_subject()` (L2215) — 2200+ line template engine |
| R2 utilities | `src/worker/utils/r2.py` | `upload_to_r2()` (L29) — Cloudflare R2 upload via boto3 |
| Photo proxy | `src/worker/utils/photo_proxy.py` | MLS photo → R2 proxy for PDF reliability |
| Image proxy | `src/worker/utils/image_proxy.py` | Image proxying utilities |
| Compute modules | `src/worker/compute/` | `calc.py`, `extract.py`, `market_trends.py`, `validate.py` — statistical computation |
| SMS | `src/worker/sms/send.py` | Twilio SMS sending |
| Templates | `src/worker/templates/` | Jinja2 templates: `market/` (1 theme), `property/` (5 themes: bold, classic, elegant, modern, teal) |

**Celery beat schedule (from `app.py` L46–52):**
- `keep-alive-ping` — every 300 seconds (5 minutes)

**Hosting:** Render (background worker)

**Key dependencies:** `celery@^5.4`, `redis@^5.0.8`, `playwright@^1.48`, `httpx@^0.27.2`, `boto3@^1.35.20`, `psycopg@^3.2.1`, `jinja2@^3.1.2`, `twilio@^9.0`

### 2.4 Shared Libraries — `libs/` + `packages/`

| Package | Path | Description |
|---------|------|-------------|
| `shared` (Python) | `libs/shared/` | Shared email template utilities (`src/shared/email/template.py`) |
| `ui` (TypeScript) | `packages/ui/` | 109 files — React components shared across `apps/web`, `reportsbuilder`, `scheduledreports` |

### 2.5 Development Tools — `reportsbuilder/`, `scheduledreports/`, `emailpreview/`

Standalone Next.js preview apps for developing report layouts, schedule builders, and email templates. **Not deployed to production.** Each has its own `package.json`, `next.config.mjs`, and component set.

### 2.6 Database — `db/`

- **46 numbered SQL migrations** (0001_base through 0046_market_report_theme) + 1 seed file
- Row-Level Security (RLS) for multi-tenant data isolation
- Managed via `scripts/run_migrations.py`
- Additional SQL scripts in `db/` root: seed scripts, verification queries, fix scripts

**Hosting:** Render Postgres (PostgreSQL 15)

### 2.7 CI/CD — `.github/workflows/`

| Workflow | File | Triggers |
|----------|------|----------|
| Backend tests | `backend-tests.yml` | PR + push |
| Frontend tests | `frontend-tests.yml` | PR + push |
| E2E tests | `e2e.yml` | PR + push |
| Release check | `release-check.yml` | PR + push |

---

## 3. External Integrations

| Service | Purpose | Auth Method | Used In |
|---------|---------|------------|---------|
| **SimplyRETS** | Live MLS listing data (comparables + market snapshots) | HTTP Basic Auth (key:secret) | `apps/worker/src/worker/vendors/simplyrets.py`, `apps/api/src/api/services/simplyrets.py` |
| **SiteX Pro** | Property assessor data (subject property lookup) | OAuth2 Client Credentials | `apps/api/src/api/services/sitex.py` |
| **PDFShift** | HTML → PDF rendering | HTTP Basic Auth | `apps/worker/src/worker/pdf_engine.py` |
| **Playwright** | Local HTML → PDF rendering (fallback / dev) | N/A (local browser) | `apps/worker/src/worker/pdf_adapter.py` |
| **SendGrid** | Transactional email delivery | API Key | `apps/worker/src/worker/email/send.py` |
| **OpenAI** | GPT-4o-mini market commentary + property executive summary | API Key (Bearer) | `apps/worker/src/worker/ai_insights.py`, `ai_market_narrative.py`, `ai_overview.py` |
| **Stripe** | Subscription billing, webhooks | API Key + Webhook Secret | `apps/api/src/api/routes/billing.py`, `stripe_webhook.py`, `config/billing.py` |
| **Cloudflare R2** | PDF + logo storage, photo proxy | Access Key + Secret (S3-compatible) | `apps/worker/src/worker/utils/r2.py`, `apps/api/src/api/services/upload.py` |
| **Google Maps** | Aerial + street view images for property reports | API Key | `apps/web/` (frontend) |
| **Twilio** | SMS notifications | Account SID + Auth Token | `apps/worker/src/worker/sms/send.py`, `apps/api/src/api/services/twilio_sms.py` |

---

## 4. Core Data Models

### 4.1 Key Database Tables

| Table | Description |
|-------|-------------|
| `accounts` | Multi-tenant account (agent or affiliate). Has `account_type` (REGULAR / INDUSTRY_AFFILIATE), `plan_slug`, `sponsor_account_id`, `stripe_subscription_id`, `billing_status`. |
| `users` | Platform users. Has `is_platform_admin`, `avatar_url`, `email_verified`. Many-to-many with `accounts` via `account_users`. |
| `account_users` | Join table: user ↔ account with roles (OWNER / ADMIN / MEMBER). |
| `plans` | Plan catalog (free, pro, team, affiliate, sponsored_free). Has `plan_slug`, `plan_name`, `stripe_price_id`, limits, `is_active`. |
| `report_generations` | Every market report generated. Has `schedule_id`, `status`, `generated_at`, `payload` (JSONB), `pdf_url`. |
| `schedules` | Automated report schedules. Has `city`, `filters` (JSONB for smart presets), `cadence`, `next_run_at`, `processing_locked_at` (race prevention). |
| `schedule_runs` | Individual execution records. Has `status`, `sent_count`, `failure_reason`. |
| `property_reports` | Property report records. Has `comparables` (JSONB), `selected_pages`, `pdf_url`, `status`, `default_theme_id`. |
| `contacts` | Agent's contact list. Has `email`, `phone`, `contact_group_id`. |
| `contact_groups` | Contact group definitions. |
| `affiliate_branding` | White-label branding per affiliate. Has 4 logo slots (`header_logo_url`, `footer_logo_url`, `email_header_logo_url`, `email_footer_logo_url`), color overrides, rep photo, contact info. |
| `webhook_endpoints` | Registered webhooks per account. |
| `email_suppressions` | Unsubscribed emails (never re-send). |
| `email_log` | Delivery tracking with `status` column. |
| `signup_tokens` | Invite tokens for agent onboarding. |
| `jwt_blacklist` | Revoked tokens (logout). |
| `login_attempts` | Failed login tracking. |
| `password_reset_tokens` | Password reset flow. |
| `sms_logs` | SMS delivery tracking. |
| `lead_pages` | Lead capture page configuration. |

### 4.2 Report Data Payload (`report_generations.payload`)

```json
{
  "city": "Irvine",
  "report_type": "market_snapshot",
  "date_range": {"from": "2026-01-01", "to": "2026-01-31"},
  "filters": {"type": "residential", "maxprice": 560000, "minbeds": 2},
  "filters_label": "2+ beds, under $560,000 (70% of Irvine median)",
  "listings": [],
  "market_stats": {"median_list_price": 800000, "median_close_price": 785000},
  "ai_insights": "The Irvine market...",
  "branding": {"agent_name": "...", "logo_url": "..."}
}
```

### 4.3 Filters Intent (Schedule `filters` JSONB)

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
| **Session JWT** | Signed HS256, stored in `HttpOnly` cookie `mr_token`. 1-hour TTL (7-day for invite accept). Validated in `middleware/authn.py` `AuthContextMiddleware` (L70–166). |
| **API keys** | SHA-256 hashed in DB. Used for programmatic API access. Managed via `routes/apikeys.py`. |
| **Password storage** | bcrypt (`bcrypt@^4.2`) |
| **RLS** | PostgreSQL Row-Level Security on all tenant tables. `SET app.current_account_id` set per request via `db.py`. |
| **Admin gate** | `is_platform_admin` flag on `users`. `deps/admin.py` enforces for all `/admin` routes. |
| **Rate limiting** | Redis-backed per-account token bucket in `middleware/authn.py` `RateLimitMiddleware` (L197–260). Per-minute window. |
| **JWT blacklist** | `jwt_blacklist` table for revoked tokens (logout). Checked in `authn.py` `_is_token_blacklisted()` (L169–188). |
| **Webhook signatures** | HMAC-SHA256 on all outbound webhook payloads. `X-TrendyReports-Signature` header. Implemented in `tasks.py` `_sign()` (L336) and `_deliver_webhooks()` (L340). |
| **Login attempts** | `login_attempts` table tracks failed logins. |
| **Credentials** | Never stored in code; all secrets via environment variables. See `.env.example`. |

---

## 6. Report Types

**Frontend definition:** `apps/web/app/lib/reportTypes.ts`
**Worker builders:** `apps/worker/src/worker/report_builders.py`
**Email templates:** `apps/worker/src/worker/email/template.py`

| Type | Key (slug) | Category | Description |
|------|-----------|----------|-------------|
| Market Snapshot | `market_snapshot` | core | Overview KPIs: count, median price, DOM, price/sqft |
| New Listings | `new_listings` | core | Active listings in date range |
| New Listings Gallery | `new_listings_gallery` | core | Photo-rich 3×3 gallery of newest listings |
| Featured Listings | `featured_listings` | core | Curated 2×2 photo grid of premium listings |
| Closed Sales | `closed` | secondary | Closed transactions in date range |
| Inventory | `inventory` | secondary | Active inventory trend |
| Price Bands | `price_bands` | secondary | Distribution by price segment |
| Open Houses | `open_houses` | secondary | Upcoming open house schedule |

**Property Report Themes (5):**

| Theme | Template Path |
|-------|--------------|
| Bold | `templates/property/bold/` |
| Classic | `templates/property/classic/` |
| Elegant | `templates/property/elegant/` |
| Modern | `templates/property/modern/` |
| Teal | `templates/property/teal/` |

---

## 7. Smart Presets (Market-Adaptive Audience Filters)

| Preset | type | minbeds | minbaths | Price strategy | price_pct |
|--------|------|---------|----------|---------------|-----------|
| First-Time Buyer | SFR | 2 | 2 | `maxprice_pct_of_median_list` | 70 |
| Investor Deals | All | — | — | `maxprice_pct_of_median_close` | 50 |
| Luxury Showcase | SFR | — | — | `minprice_pct_of_median_list` | 150 |
| Condo Watch | Condo | 1 | — | — | — |
| Family Homes | SFR | 4 | 2 | — | — |

Price caps are resolved dynamically at generation time using the market median for the report's city and date range. Implemented in `apps/worker/src/worker/filter_resolver.py`.

**Elastic Widening:** If results < 6 (4 for featured), price percentage is expanded: 70% → 85% → 100% → 120%. Ensures reports never appear empty.

---

## 8. Subscription Plans

| Plan | Slug | Monthly Limit | Price | Stripe |
|------|------|--------------|-------|--------|
| Free | `free` | 5 reports | $0 | No card required |
| Pro | `pro` | 50 reports | $29/mo | `STRIPE_PRICE_PRO_MONTH` |
| Team | `team` | 200 reports | $99/mo | `STRIPE_PRICE_TEAM_MONTH` |
| Affiliate | `affiliate` | 500 reports | Custom | Custom |
| Sponsored Free | `sponsored_free` | 10 reports | $0 (affiliate-sponsored) | No Stripe |

Plan catalog is stored in the `plans` table and cached in memory for 1 hour (`apps/api/src/api/services/plans.py` `get_plan_catalog()` L57). Stripe price mapping in `apps/api/src/api/config/billing.py`.

---

## 9. AI System

### GPT-4o-mini Integration

| Module | File | Purpose |
|--------|------|---------|
| Market insights | `apps/worker/src/worker/ai_insights.py` | Email market commentary, sender-aware tone (L82) |
| PDF narrative | `apps/worker/src/worker/ai_market_narrative.py` | PDF-specific market narrative with Redis caching (L177) |
| Property overview | `apps/worker/src/worker/ai_overview.py` | Property report executive summary (L50) |

### Sender-Aware Tone

| Account Type | Tone | Example Opening |
|--------------|------|-----------------|
| `REGULAR` (Agent) | Personal, warm, "I" voice | "I've been keeping an eye on the market for you..." |
| `INDUSTRY_AFFILIATE` | Professional, "we" voice | "This week's market update from Pacific Coast Title..." |

### Audience-Based Listing Caps

| Audience | Email Cap | PDF Cap |
|----------|-----------|---------|
| All Listings | 24 | 9 |
| First-Time Buyers | 24 | 9 |
| Family Homes | 18 | 9 |
| Condo Watch | 18 | 9 |
| Investors | 12 | 9 |
| Luxury | 8 | 9 |
| Featured Listings | 4 | 4 |

### Configuration

```bash
AI_INSIGHTS_ENABLED=true    # Enable AI insights (default: false)
OPENAI_API_KEY=sk-xxx       # Required if AI enabled
```

Graceful fallback: if AI is disabled or fails, template-based text is used.

---

## 10. Observability & Testing

### Unit / Integration Tests

```bash
# API tests
cd apps/api && poetry run pytest tests/ -v

# Worker tests
cd apps/worker && poetry run pytest -v

# Frontend tests
cd apps/web && pnpm test

# Root-level tests
pytest tests/ -v
```

**Test files:**
- `apps/api/tests/` — `test_accept_invite.py`, `test_affiliate_branding.py`, `test_billing_checkout.py`, `test_me_endpoint.py`, `test_plans_limits.py`, `test_schedules_report_types.py`
- `apps/web/__tests__/` — `AccountSwitcher.test.tsx`, `AffiliatePage.test.tsx`, `NewSchedulePage.test.tsx`, `PlanPage.test.tsx`, `TemplatesMapping.test.ts`
- `tests/` (root) — `test_market_templates.py`, `test_new_metrics.py`, `test_property_templates.py`, `test_simplyrets_query_builder.py`

### CI Workflows

```bash
# Runs automatically on PR + push via GitHub Actions
.github/workflows/backend-tests.yml
.github/workflows/frontend-tests.yml
.github/workflows/e2e.yml
.github/workflows/release-check.yml
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

## 11. Infrastructure Stack

| Component | Technology | Version | Host |
|-----------|-----------|---------|------|
| Frontend | Next.js (App Router) | 16.0.7 | Vercel |
| React | React | 19.2.0 | Vercel |
| CSS | Tailwind CSS | v4 | Vercel |
| API | FastAPI | ^0.115 | Render |
| Worker | Celery | ^5.4 | Render |
| Python | Python | 3.11+ | Render |
| Database | PostgreSQL + RLS | 15 | Render |
| Cache / Queue | Redis | 7 | Render |
| File storage | Cloudflare R2 | — | Cloudflare |
| Package manager | pnpm | 9.12.3 | — |
| Node version | Node.js | 20.18.1 (`.nvmrc`) | — |
| Monorepo | pnpm workspaces | — | — |
| Python deps | Poetry | — | — |
| Container (dev) | Docker Compose | Postgres 15 + Redis 7 | Local |

---

## 12. Environment Variables

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
STRIPE_PRICE_PRO_MONTH=price_...
STRIPE_PRICE_TEAM_MONTH=price_...
R2_ACCOUNT_ID=<id>
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<key>
R2_BUCKET_NAME=market-reports
REDIS_URL=redis://...
```

### Worker (Render)

```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CELERY_RESULT_URL=redis://...
SIMPLYRETS_USERNAME=<user>
SIMPLYRETS_PASSWORD=<pass>
PDFSHIFT_API_KEY=<key>
PRINT_BASE=https://trendyreports.io
PHOTO_PROXY_ENABLED=true
R2_*=<same as API>
AI_INSIGHTS_ENABLED=true
OPENAI_API_KEY=sk-xxx
```

See `.env.example` for the full template.

---

## 13. Architecture Docs Index

| Document | Description |
|----------|-------------|
| [INDEX.md](./INDEX.md) | Quick-reference source tree |
| [WIZARD_AND_API_CALLS.md](./WIZARD_AND_API_CALLS.md) | Wizard flows, sequence diagrams, full API reference |
| [SITE_ARCHITECTURE_TREE.md](./SITE_ARCHITECTURE_TREE.md) | Directory tree + logical component tree |
| [ARCHITECTURE_AUDIT.md](./ARCHITECTURE_AUDIT.md) | Docs inventory, status, and audit trail |
| [backend-core.md](./backend-core.md) | FastAPI app startup, DB, auth, settings |
| [backend-middleware.md](./backend-middleware.md) | Auth + rate-limit middleware |
| [backend-routes.md](./backend-routes.md) | All 28 API routes |
| [backend-services.md](./backend-services.md) | Business logic service modules |
| [frontend-core.md](./frontend-core.md) | Next.js config, middleware, API clients |
| [frontend-pages.md](./frontend-pages.md) | All app-router pages |
| [frontend-components.md](./frontend-components.md) | Component organization |
| [frontend-api-proxy.md](./frontend-api-proxy.md) | Next.js proxy routes |
| [property-type-data-contract.md](./property-type-data-contract.md) | SiteX → SimplyRETS type mapping |
| [performance-audit.md](./performance-audit.md) | Performance findings |
| **Module Docs** (`modules/`) | |
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
| [modules/email-template.md](./modules/email-template.md) | Email template engine |
| [modules/market-reports-audit.md](./modules/market-reports-audit.md) | Market reports audit trail |
| **Plans & Playbooks** (`docs/plan/`) | |
| [MARKET_REPORT_PDF_PLAYBOOK.md](../plan/MARKET_REPORT_PDF_PLAYBOOK.md) | PDF generation playbook |
| [MARKET_REPORT_AGENT_PROMPTS.md](../plan/MARKET_REPORT_AGENT_PROMPTS.md) | AI prompt engineering reference |
| [V0_MARKET_REPORTS_SPEC.md](../plan/V0_MARKET_REPORTS_SPEC.md) | Original market reports specification |
| **Skill Files** (`.cursor/rules/`) | |
| `market-report-templates-skill.md` | AI agent guide: market report PDF templates |
| `branding-color-system-skill.md` | AI agent guide: branding & color system |
| `email-html-design-skill.md` | AI agent guide: email HTML design |
| `admin-panel-design-skill.md` | AI agent guide: admin panel design |

---

## 14. Demo Accounts (Staging)

| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@trendyreports-demo.com | DemoAdmin123! |
| Free Agent | agent-free@trendyreports-demo.com | DemoAgent123! |
| Pro Agent | agent-pro@trendyreports-demo.com | DemoAgent123! |
| Affiliate | affiliate@trendyreports-demo.com | DemoAff123! |
| Sponsored Agent | agent-sponsored@trendyreports-demo.com | DemoAgent123! |

---

_This document is the single source of truth for TrendyReports architecture. Every fact was verified against the codebase on 2026-04-13._
