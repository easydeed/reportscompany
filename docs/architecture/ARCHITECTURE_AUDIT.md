# TrendyReports — Architecture Docs Audit

> **Audit date:** 2026-04-13 (V2)
> **Conducted by:** Documenter agent — full code-verified audit
> **Previous audit:** 2026-02-25 (V1)

---

## Change Log

| Date | Change |
|------|--------|
| 2026-04 | **V2 Audit:** Verified all docs against codebase. Fixed: router count (26→28), migration count (42→46), Next.js version (15→16.0.7), React 19.2.0, `closed_sales`→`closed`, RLS middleware status, `schedules_tick` runs as standalone process (not Celery beat), `psycopg` not `psycopg2`, `zoneinfo` not `pytz`. Updated 3 module docs (worker-tasks, worker-core, filter-resolver). Updated SOURCE_OF_TRUTH to V16. Updated README.md. |
| 2026-02 | **V1 Audit:** Initial architecture docs audit, 11 module docs created, SOURCE_OF_TRUTH V15. |

---

## A. Existing Architecture Docs Inventory

| File | Location | Status (2026-04) |
|------|----------|-------------------|
| `SOURCE_OF_TRUTH.md` | `docs/architecture/SOURCE_OF_TRUTH.md` | **V16 — current** (updated 2026-04) |
| `INDEX.md` | `docs/architecture/INDEX.md` | needs update (route count) |
| `backend-core.md` | `docs/architecture/backend-core.md` | accurate |
| `backend-middleware.md` | `docs/architecture/backend-middleware.md` | needs update (RLS not registered) |
| `backend-routes.md` | `docs/architecture/backend-routes.md` | needs update (28 routes, not 26) |
| `backend-services.md` | `docs/architecture/backend-services.md` | accurate |
| `frontend-core.md` | `docs/architecture/frontend-core.md` | needs update (Next.js 16) |
| `frontend-pages.md` | `docs/architecture/frontend-pages.md` | accurate |
| `frontend-components.md` | `docs/architecture/frontend-components.md` | accurate |
| `frontend-api-proxy.md` | `docs/architecture/frontend-api-proxy.md` | accurate |
| `property-type-data-contract.md` | `docs/architecture/property-type-data-contract.md` | accurate |
| `performance-audit.md` | `docs/architecture/performance-audit.md` | accurate |
| `WIZARD_AND_API_CALLS.md` | `docs/architecture/WIZARD_AND_API_CALLS.md` | accurate |
| `WIZARD_FLOW_AND_API_CALLS.md` | `docs/architecture/WIZARD_FLOW_AND_API_CALLS.md` | accurate |
| `SITE_ARCHITECTURE_TREE.md` | `docs/architecture/SITE_ARCHITECTURE_TREE.md` | accurate |
| `ARCHITECTURE_AUDIT.md` | `docs/architecture/ARCHITECTURE_AUDIT.md` | **V2 — current** (this file) |

**Module docs (13, all in `docs/architecture/modules/`):**

| File | Status (2026-04) |
|------|-------------------|
| `worker-tasks.md` | **updated** (V2 audit — corrected task signatures, added line numbers) |
| `worker-core.md` | **updated** (V2 audit — corrected app.py, schedules_tick facts) |
| `filter-resolver.md` | **updated** (V2 audit — corrected price_strategy format, added line numbers) |
| `property-builder.md` | accurate |
| `worker-simplyrets-vendor.md` | accurate |
| `simplyrets-api-service.md` | accurate |
| `sitex-api-service.md` | accurate |
| `property-routes-comparables.md` | accurate |
| `admin-metrics-routes.md` | accurate |
| `email-template.md` | accurate |
| `qr-landing-leads-sms.md` | accurate |
| `market-reports-audit.md` | accurate |
| `cli-tools.md` | accurate |
| `test-suite.md` | accurate |

---

## B. Deprecated / Legacy Docs

| File | Location | Status |
|------|----------|--------|
| `SourceOfTruth.md` | Root (`/SourceOfTruth.md`) | **DEPRECATED** — V14 (Jan 2026). Superseded by `docs/architecture/SOURCE_OF_TRUTH.md` (V16). |
| `SourceOfTruth.md` | `docs/architecture/SourceOfTruth.md` | **DEPRECATED** — duplicate of root V14. |
| `MARKET_REPORTS_CODE_DUMP.md` | Root | Legacy code dump reference |

---

## C. Key Discrepancies Found and Fixed (V2 Audit)

| # | Area | Old Value | Correct Value | Fixed In |
|---|------|-----------|---------------|----------|
| 1 | Next.js version | "Next.js 15" | Next.js 16.0.7 (`apps/web/package.json` L56) | SOURCE_OF_TRUTH V16, README |
| 2 | React version | "React 18/19" | React 19.2.0 (`apps/web/package.json` L58) | SOURCE_OF_TRUTH V16 |
| 3 | Tailwind version | Unspecified | Tailwind CSS v4 (`apps/web/package.json` L88) | SOURCE_OF_TRUTH V16 |
| 4 | Router count | "26 router mounts" | 28 (`apps/api/src/api/main.py` L91–118) | SOURCE_OF_TRUTH V16 |
| 5 | Migration count | "42 SQL migrations" | 46 numbered + 1 seed = 47 total | SOURCE_OF_TRUTH V16 |
| 6 | Report type key | `closed_sales` | `closed` (`apps/web/app/lib/reportTypes.ts` L18) | SOURCE_OF_TRUTH V16 |
| 7 | RLS middleware | "Active" | Placeholder, NOT registered in main.py (L70–71) | SOURCE_OF_TRUTH V16 |
| 8 | Property tasks location | In `tasks.py` | In `property_tasks/property_report.py` (`app.py` L65) | worker-tasks.md |
| 9 | `generate_report` signature | `(schedule_id, run_id, ...)` | `(self, run_id, account_id, report_type, params)` (tasks.py L778) | worker-tasks.md |
| 10 | `schedules_tick` execution | "via Celery beat" | Standalone process via `run_forever()` (L437) | worker-core.md |
| 11 | Timezone library | `pytz` | `zoneinfo.ZoneInfo` (stdlib, L21) | worker-core.md |
| 12 | PostgreSQL driver | `psycopg2` | `psycopg` v3 (`pyproject.toml`) | worker-core.md |
| 13 | Celery app name | `"worker"` | `"market_reports"` (app.py L29) | worker-core.md |
| 14 | `price_strategy` format | `{mode, price_pct}` top-level | `{mode, value}` nested dict | filter-resolver.md |
| 15 | Root README doc links | 13 links to non-existent files | Corrected to actual file locations | README.md |
| 16 | README `packages/api-client/` | Listed | Does not exist — removed | README.md |

---

## D. Documentation Inventory Summary

| Category | Count | Location |
|----------|-------|----------|
| Architecture docs | 16 | `docs/architecture/` |
| Module docs | 14 | `docs/architecture/modules/` |
| Plan docs | 4 | `docs/plan/` |
| Design docs | 10 | `docs/design/` |
| Skill files | 4 | `.cursor/rules/` |
| READMEs | 5 | Root + apps + packages |
| Fix docs | 1 | `docs/fix/` |
| Archive docs | 1 | `docs/archive/` |
| **Total documentation files** | **55** | |

---

## E. Remaining Work (for future audits)

| Priority | Task | Status |
|----------|------|--------|
| Medium | Update `backend-routes.md` to reflect 28 routes (not 26) | Pending |
| Medium | Update `backend-middleware.md` to note RLS is placeholder/not registered | Pending |
| Medium | Update `frontend-core.md` to reflect Next.js 16.0.7 | Pending |
| Medium | Update `INDEX.md` with correct counts | Pending |
| Low | Add deprecation notice to root `SourceOfTruth.md` | Pending |
| Low | Add deprecation notice to `docs/architecture/SourceOfTruth.md` | Pending |
| Low | Verify all 4 `.cursor/rules/` skill files against current code | Pending |
| Low | Create `LAUNCH_PLAN.md` (referenced in prompt but doesn't exist) | N/A — not in codebase |
| Low | Create `HELP_CENTER_CONTENT.md` (referenced in prompt but doesn't exist) | N/A — not in codebase |
