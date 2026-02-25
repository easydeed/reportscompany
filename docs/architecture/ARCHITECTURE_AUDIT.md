# TrendyReports — Architecture Docs Audit

> **Audit date:** 2026-02-25
> **Conducted by:** Architecture docs audit (AI-assisted)
> **Branch:** `claude/kind-noyce`

---

## A. Existing Architecture Docs Inventory

| File | Location | Description |
|------|----------|-------------|
| `INDEX.md` | `docs/architecture/INDEX.md` | Quick-reference source tree, tech stack table |
| `backend-core.md` | `docs/architecture/backend-core.md` | App startup, DB, auth, settings |
| `backend-middleware.md` | `docs/architecture/backend-middleware.md` | Auth context + RLS middleware |
| `backend-routes.md` | `docs/architecture/backend-routes.md` | All 26 API route modules |
| `backend-services.md` | `docs/architecture/backend-services.md` | Business logic services (with performance notes) |
| `frontend-core.md` | `docs/architecture/frontend-core.md` | Next.js config, middleware, API clients, hooks |
| `frontend-pages.md` | `docs/architecture/frontend-pages.md` | All app-router pages (public + protected + admin) |
| `frontend-components.md` | `docs/architecture/frontend-components.md` | Component organization by domain |
| `frontend-api-proxy.md` | `docs/architecture/frontend-api-proxy.md` | ~60 Next.js proxy routes |
| `property-type-data-contract.md` | `docs/architecture/property-type-data-contract.md` | SiteX UseCode → SimplyRETS type/subtype mapping |
| `performance-audit.md` | `docs/architecture/performance-audit.md` | Performance findings by severity |
| `SourceOfTruth.md` (root) | `SourceOfTruth.md` | V14 executive platform overview |

**Total existing architecture docs:** 12

---

## B. Actual Modules Discovered in Repo

### B.1 `apps/api/src/api/` (Backend)

| Module path | Description |
|-------------|-------------|
| `main.py` | FastAPI app bootstrap, 26 router mounts |
| `settings.py` | Pydantic env settings |
| `db.py` | PostgreSQL connection, RLS helpers |
| `auth.py` | JWT sign/verify, bcrypt, API key hashing |
| `worker_client.py` | Celery task enqueue |
| `config/billing.py` | Stripe price ID mapping |
| `deps/admin.py` | Admin-only FastAPI dependency |
| `schemas/property.py` | PropertyData, ComparableData Pydantic models |
| `middleware/authn.py` | AuthContextMiddleware, RateLimitMiddleware |
| `middleware/rls.py` | RLSContextMiddleware |
| `routes/auth.py` | Login, signup, password reset, email verify, invite |
| `routes/property.py` | **Subject search + comparables (fallback ladder L0–L5)** |
| `routes/reports.py` | Market report CRUD + task enqueueing |
| `routes/schedules.py` | Schedule CRUD |
| `routes/billing.py` | Stripe checkout / portal |
| `routes/stripe_webhook.py` | Stripe subscription events |
| `routes/admin.py` | Platform admin |
| `routes/admin_metrics.py` | **Platform analytics (overview, daily, agents, conversion, devices, recent)** |
| `routes/me.py` | Current user profile, leads, lead-pages |
| `routes/users.py` | Multi-user account management |
| `routes/affiliates.py` | Affiliate program |
| `routes/contacts.py` | Contact CRUD, CSV import |
| `routes/contact_groups.py` | Contact group CRUD |
| `routes/leads.py` | Lead CRUD, CSV export |
| `routes/lead_pages.py` | Lead capture page management |
| `routes/mobile_reports.py` | Mobile-optimized report viewer |
| `routes/health.py` | Liveness check |
| `routes/account.py` | Account settings, plan usage |
| `routes/usage.py` | API usage tracking |
| `routes/apikeys.py` | API key CRUD |
| `routes/branding_tools.py` | White-label branding assets |
| `routes/upload.py` | File upload handler |
| `routes/onboarding.py` | Onboarding workflow |
| `routes/webhooks.py` | Generic webhook management |
| `routes/unsubscribe.py` | Email unsubscribe |
| `routes/devfiles.py` | Dev-only test utilities |
| `routes/dev_stripe_prices.py` | Dev-only Stripe config |
| `services/simplyrets.py` | **API-layer SimplyRETS client (fetch_properties, normalize)** |
| `services/sitex.py` | **SiteX Pro OAuth2 client (address + APN search)** |
| `services/usage.py` | Plan limit enforcement |
| `services/plans.py` | Plan catalog |
| `services/affiliates.py` | Affiliate account management |
| `services/accounts.py` | Multi-account support |
| `services/email.py` | Email via Resend |
| `services/branding.py` | White-label brand resolution |
| `services/property_stats.py` | Property report statistics |
| `services/qr_service.py` | QR code generation |
| `services/twilio_sms.py` | SMS via Twilio |
| `services/upload.py` | File upload processing |
| `services/agent_code.py` | Promotional code management |
| `services/billing_state.py` | Billing state management |
| `services/plan_lookup.py` | Plan detail resolution |

### B.2 `apps/worker/src/worker/` (Background Worker)

| Module path | Description |
|-------------|-------------|
| `app.py` | Celery app init, beat schedule |
| `tasks.py` | **generate_report, generate_property_report_task, keep_alive_ping, webhook delivery** |
| `schedules_tick.py` | Every-minute tick executor |
| `property_builder.py` | **Jinja2 HTML renderer — 5 themes, 7 pages** |
| `filter_resolver.py` | **Market-adaptive filter resolution + elastic widening** |
| `vendors/simplyrets.py` | **Synchronous SimplyRETS client with rate limiter + pagination** |
| `ai_insights.py` | GPT-4o-mini market commentary |
| `pdf_engine.py` | PDF generation coordinator |
| `pdf_adapter.py` | PDFShift API integration |
| `limit_checker.py` | Worker-context plan enforcement |
| `cache.py` | Redis caching layer |
| `query_builders.py` | SQL query builders |
| `filter_resolver.py` | Market-adaptive filters |
| `social_engine.py` | Social media image generation |
| `redis_utils.py` | Redis utilities |
| `compute/calc.py` | Statistical calculations (median, percentiles) |
| `compute/extract.py` | Data extraction from MLS responses |
| `compute/validate.py` | Data validation |
| `email/send.py` | Email dispatch |
| `email/template.py` | Email template rendering |
| `email/providers/sendgrid.py` | SendGrid provider |
| `templates/property/classic/` | Classic theme Jinja2 templates |
| `templates/property/modern/` | Modern theme Jinja2 templates |
| `templates/property/elegant/` | Elegant theme Jinja2 templates |
| `templates/property/teal/` | Teal theme Jinja2 templates (default) |
| `templates/property/bold/` | Bold theme Jinja2 templates |

### B.3 `tools/` / `scripts/`

| Module path | Description |
|-------------|-------------|
| `qa_deliver_reports.py` (root) | **End-to-end QA report delivery tool** |
| `scripts/test_simplyrets.py` | **SimplyRETS API smoke test** |
| `scripts/test_sitex.py` | **SiteX API smoke test** |
| `scripts/test_property_report_flow.py` | **Property report flow integration test** |
| `scripts/test_all_reports.py` | All 8 market report types test |
| `scripts/test_report_flow.py` | Single market report flow |
| `scripts/test_affiliates.py` | Affiliate flow tests |
| `scripts/generate_all_property_pdfs.py` | **Batch PDF generation (all 5 themes)** |
| `scripts/generate_theme_previews.py` | **Theme preview PNG generation** |
| `scripts/seed_demo_accounts.py` | Demo account seeding |
| `scripts/run_migrations.py` | Migration runner |
| `scripts/grant_admin_role.py` | Admin role assignment |
| `scripts/check_db_tables.py` | DB schema inspection |
| `scripts/upload_seller_assets_to_r2.py` | R2 asset upload |

### B.4 `tests/` (Automated)

| File | Description |
|------|-------------|
| `tests/test_property_templates.py` | **pytest: 5 themes × 6 test classes for Jinja2 rendering** |

### B.5 `e2e/` (End-to-End)

| File | Description |
|------|-------------|
| `e2e/auth.spec.ts` | Playwright: auth flows |
| `e2e/affiliate.spec.ts` | Playwright: affiliate management |
| `e2e/plan.spec.ts` | Playwright: plan management |
| `e2e/stripe.spec.ts` | Playwright: Stripe webhook handling |

### B.6 `templates/` (Jinja2 Email Templates)

5 themes × 2 templates each = 10 `.jinja2` files in `apps/worker/src/worker/templates/property/`

---

## C. Mapping Table: Doc → Module → Status

| Doc file | Module path(s) | Status |
|----------|---------------|--------|
| `backend-core.md` | `main.py`, `settings.py`, `db.py`, `auth.py`, `worker_client.py`, `config/billing.py`, `deps/admin.py`, `schemas/property.py` | **accurate** |
| `backend-middleware.md` | `middleware/authn.py`, `middleware/rls.py` | **accurate** |
| `backend-routes.md` | `routes/*.py` (26 modules) | **outdated** — missing `property.py` fallback ladder + `admin_metrics.py` new endpoints |
| `backend-services.md` | `services/*.py` | **outdated** — `simplyrets.py` and `sitex.py` listed only in summary table, no detail |
| `frontend-core.md` | `next.config.ts`, `middleware.ts`, `lib/`, `hooks/` | **accurate** |
| `frontend-pages.md` | `app/` (all pages) | **accurate** |
| `frontend-components.md` | `components/` | **accurate** |
| `frontend-api-proxy.md` | `app/api/proxy/` | **accurate** |
| `property-type-data-contract.md` | `routes/property.py` (type mapping) | **accurate** |
| `performance-audit.md` | Cross-cutting | **accurate** (not module-specific) |
| `INDEX.md` | All modules | **outdated** — missing worker modules, new modules |
| `SourceOfTruth.md` (root) | Platform overview | **outdated** — V14 (Jan 2026); property report system significantly expanded since |
| _(missing)_ | `services/simplyrets.py` | **missing** → created `modules/simplyrets-api-service.md` |
| _(missing)_ | `services/sitex.py` | **missing** → created `modules/sitex-api-service.md` |
| _(missing)_ | `routes/property.py` (comparables) | **missing** → created `modules/property-routes-comparables.md` |
| _(missing)_ | `vendors/simplyrets.py` | **missing** → created `modules/worker-simplyrets-vendor.md` |
| _(missing)_ | `tasks.py` | **missing** → created `modules/worker-tasks.md` |
| _(missing)_ | `property_builder.py` | **missing** → created `modules/property-builder.md` |
| _(missing)_ | `filter_resolver.py` | **missing** → created `modules/filter-resolver.md` |
| _(missing)_ | `app.py`, `schedules_tick.py`, `limit_checker.py`, `cache.py` | **missing** → created `modules/worker-core.md` |
| _(missing)_ | `routes/admin_metrics.py` | **missing** → created `modules/admin-metrics-routes.md` |
| _(missing)_ | `qa_deliver_reports.py`, `scripts/test_*.py` | **missing** → created `modules/cli-tools.md` |
| _(missing)_ | `tests/test_property_templates.py`, `e2e/` | **missing** → created `modules/test-suite.md` |

---

## D. Action List of Changes Applied

### New Files Created

| File | Deliverable |
|------|------------|
| `docs/architecture/modules/simplyrets-api-service.md` | Module B: new module doc |
| `docs/architecture/modules/sitex-api-service.md` | Module B: new module doc |
| `docs/architecture/modules/property-routes-comparables.md` | Module B: new module doc (fallback ladder) |
| `docs/architecture/modules/worker-simplyrets-vendor.md` | Module B: new module doc |
| `docs/architecture/modules/worker-tasks.md` | Module B: new module doc |
| `docs/architecture/modules/property-builder.md` | Module B: new module doc |
| `docs/architecture/modules/filter-resolver.md` | Module B: new module doc |
| `docs/architecture/modules/worker-core.md` | Module B: new module doc |
| `docs/architecture/modules/admin-metrics-routes.md` | Module B: new module doc |
| `docs/architecture/modules/cli-tools.md` | Module B: new module doc |
| `docs/architecture/modules/test-suite.md` | Module B: new module doc |
| `docs/architecture/WIZARD_AND_API_CALLS.md` | Deliverable C |
| `docs/architecture/SOURCE_OF_TRUTH.md` | Deliverable D (V15) |
| `docs/architecture/SITE_ARCHITECTURE_TREE.md` | Deliverable E |
| `docs/architecture/ARCHITECTURE_AUDIT.md` | Deliverable A (this file) |

### Files Updated

| File | Change |
|------|--------|
| `docs/architecture/INDEX.md` | Added worker section, new module docs links, updated source tree |
| `docs/architecture/backend-services.md` | Added detailed SimplyRETS + SiteX service documentation |

---

## E. Final Summary

| Metric | Count |
|--------|-------|
| **Existing architecture docs** | 12 |
| **New module docs created** | 11 |
| **Main docs created** | 4 (WIZARD_AND_API_CALLS, SOURCE_OF_TRUTH, SITE_ARCHITECTURE_TREE, ARCHITECTURE_AUDIT) |
| **Existing docs updated** | 2 (INDEX.md, backend-services.md) |
| **Total new/updated files** | 17 |
| **Modules status: accurate** | 7 |
| **Modules status: outdated → updated** | 3 (backend-routes.md detail, backend-services.md, INDEX.md) |
| **Modules status: missing → documented** | 11 |
| **Modules still unknown** | 0 |

### Recently Added / Changed Modules (Post V14)

The following modules were added or significantly changed since the SourceOfTruth V14 (Jan 2026):

| Module | Change | Doc |
|--------|--------|-----|
| `routes/property.py` | 6-level fallback ladder added; sqft_tolerance + radius pills; post-filter at every level; best-results tracking | [modules/property-routes-comparables.md](./modules/property-routes-comparables.md) |
| `services/simplyrets.py` | Full API-layer client with `build_comparables_params` + `normalize_listing` | [modules/simplyrets-api-service.md](./modules/simplyrets-api-service.md) |
| `services/sitex.py` | OAuth2 token management + 24h in-memory cache | [modules/sitex-api-service.md](./modules/sitex-api-service.md) |
| `vendors/simplyrets.py` | RateLimiter class + pagination | [modules/worker-simplyrets-vendor.md](./modules/worker-simplyrets-vendor.md) |
| `property_builder.py` | Pages 5-7 transplanted from original V0 HTML; 5 themes | [modules/property-builder.md](./modules/property-builder.md) |
| `filter_resolver.py` | Elastic widening (4-step), build_filters_label | [modules/filter-resolver.md](./modules/filter-resolver.md) |
| `tasks.py` | `generate_property_report_task` fully wired; HMAC webhook delivery | [modules/worker-tasks.md](./modules/worker-tasks.md) |
| `routes/admin_metrics.py` | Conversion funnel + devices endpoints added | [modules/admin-metrics-routes.md](./modules/admin-metrics-routes.md) |
| `tests/test_property_templates.py` | 5 themes × 6 test classes with full/minimal contexts | [modules/test-suite.md](./modules/test-suite.md) |
| `qa_deliver_reports.py` | 8-config QA delivery automation | [modules/cli-tools.md](./modules/cli-tools.md) |
| `scripts/test_simplyrets.py` | SimplyRETS type/subtype discovery script | [modules/cli-tools.md](./modules/cli-tools.md) |
| `scripts/test_sitex.py` | SiteX smoke test | [modules/cli-tools.md](./modules/cli-tools.md) |
