# Docs Audit — 2026-08-17

**Scope:** every file under `docs/`, plus the root-level doc set (`README.md`, `LOCAL_SETUP_GUIDE.md`, `SourceOfTruth.md`, `MARKET_REPORTS_CODE_DUMP.md`) and `.cursor/rules/` / `.claude/skills/` agent docs.
**Method:** every claim verified against code at HEAD `f854ed6` (2026-06-24). Docs were not reconciled against each other.
**Headline:** every file in `docs/` was last touched in a single commit, `29c408f` (2026-05-14) — the repo's initial import. The code has moved through 40+ commits since (onboarding guided flow, company/title-company hierarchy, per-product limits, contact-type collapse, Open Houses disablement, marketing scrub). **No doc reflects any change made after 2026-05-14.** Of 50 files in `docs/`, 6 earn KEEP.

---

## 1. Verdict Table

Last commit for **every** file below: `2026-05-14 29c408f` (single import commit; per-file dates carry no information). "Refs" = files that mention the doc by name, excluding other docs' self-referential webs.

### docs/architecture/

| Path | Lines | Verdict | Justification |
|---|---|---|---|
| `ARCHITECTURE_AUDIT.md` | 121 | **DELETE** | A 2026-04 audit whose "corrected" values are now themselves wrong (says 28 routers/46 migrations; actual 29/52) and which certifies as "accurate" nine docs this audit falsified. Superseded by this report. |
| `INDEX.md` | 190 | **REWRITE** | Linked from README; navigation value is real, but counts are wrong ("26 routes" →29, "~60 proxy" →127, "75 ui" →58) and it omits `company/`, `get-started/`, `market_trends.py`. |
| `SITE_ARCHITECTURE_TREE.md` | 346 | **DELETE** | Redundant with INDEX.md and wrong everywhere INDEX is wrong plus more: "42 migrations" (→52), "60+ packages/ui components" (→37), lists RLSContext as registered middleware (removed, `main.py:72`), lists a `POST /generate` route that doesn't exist, lists 11 of 14 module docs, `schedules_tick.py` twice. |
| `SOURCE_OF_TRUTH.md` | 554 | **REWRITE** | The canonical doc and the best of the three variants, but 20 falsified claims (see §2.1) including its route/migration/service counts, the §8 plans table, two nonexistent DB tables, and a fictional `/health` response. Structure is worth keeping; numbers are not. |
| `SourceOfTruth.md` | 596 | **DELETE** | Stale V14 (Jan 2026), byte-identical to the deprecated root copy **minus the deprecation banner** — the most dangerous file in the repo: an unmarked obsolete source-of-truth sitting next to the real one, with a case-collision filename hazard on macOS/Windows. |
| `WIZARD_AND_API_CALLS.md` | 456 | **REWRITE** | Its entire SiteX section is wrong (fabricated base URL/endpoints/params/exception name — see §2.3); property wizard has 4 steps, not 5; documents a `POST /reports/{id}/generate` route that doesn't exist. The comparables-ladder and caching sections are worth salvaging. Absorb the correct SiteX section from `WIZARD_FLOW_AND_API_CALLS.md`. |
| `WIZARD_FLOW_AND_API_CALLS.md` | 289 | **MERGE INTO `WIZARD_AND_API_CALLS.md`** | Competing duplicate. Its SiteX section is the correct one (`sitex.py:39,46,50`), but its market-wizard section documents the dead `v0-report-builder` component (zero importers) instead of the live UnifiedReportWizard. Take SiteX + env-var table, delete the rest. |
| `backend-core.md` | 179 | **REWRITE** | Mostly verified (pool params `db.py:32-38`, `set_rls`, LIFO order), but "26 routers" is wrong and its claim that `RateLimitMiddleware` consumes `cache.py` is false — `cache.py` has **zero** consumers (`authn.py:203` uses its own redis client). |
| `backend-middleware.md` | 99 | **KEEP** | Every hard claim verified (fail-closed blacklist `authn.py:189-190`, skip paths `:207`, 60/min `:225`, header names `:248-250`). One wording fix needed: "rls.py — REMOVED" — the file exists; only its registration was removed. |
| `backend-routes.md` | 103 | **REWRITE** | "All 26 modules" →29; omits `company.py` (mounted `main.py:120`); all three line refs to `reports.py` wrong (e.g. `POST /reports` "L45-119" → actual `reports.py:119`); `account.py` documented twice. |
| `backend-services.md` | 169 | **REWRITE** | Every `usage.py` line ref wrong (e.g. `get_monthly_usage` "L20-85" → `usage.py:266`); omits 4 of 19 services (`brand_resolver`, `invite_service`, `sample_report_data`, `schedule_utils`); its "known issue" contradicts backend-routes.md which says the issue was fixed. |
| `frontend-api-proxy.md` | 159 | **DELETE** | Documents ~50 of 127 proxy routes with 10 dead paths (see §2.4) and misses entire families (company ×9, admin/metrics ×8, affiliates, r/[id]). The proxy is a mechanical 1:1 mirror of the backend; a hand-maintained route list will always be stale. Replace with one paragraph on the proxy convention in the frontend doc. |
| `frontend-components.md` | 264 | **KEEP** | All ~50 file paths resolve; claims verified. Two blemishes for a follow-up edit: "50+" ui primitives (actual 58) and silence about the dead `v0-report-builder/` directory (6 files, zero importers). |
| `frontend-core.md` | 129 | **REWRITE** | Nearly every React Query number is wrong: `useUser` staleTime 5min→10min (`use-user.ts:36`), fetch path `/v1/me`→`/api/proxy/v1/users/me` (`:22`), provider staleTime 5min→2min, `refetchOnWindowFocus` false→true, `retry` 1→2 (`query-provider.tsx:13,19,23`); documented `User` shape has fields that don't exist. |
| `frontend-pages.md` | 128 | **REWRITE** | Lists ~52 of 98 pages; 3 dead paths (`/help`, `/branding-preview/*`); omits the entire company portal (6 pages), the second top-level `/admin` tree (14 pages), and `get-started`. |
| `performance-audit.md` | 118 | **DELETE** | Documents pre-fix state with no FIXED markers. Every spot-checked finding is resolved (pooling: `db.py:32-38`; N+1: batch query `affiliates.py:60-68`; "duplicate /branding routes": only one GET `:371` / one POST `:501` exist; indexes: deployed in 0042). **Zero claims in this doc are currently true.** Worst kind of doc: reads as an open bug list. |
| `property-type-data-contract.md` | 270 | **REWRITE** | Cited by live code (`property.py:64,533`), so the subject matters — but §4's "authoritative mapping" has every subtype in the wrong case (doc lowercase vs actual CamelCase, which the code says "MUST match" at `property.py:113`), wrong `type` values for condo/mobile, a post-filter table missing `Detached`/`Attached`/`MobileHome`, a fabricated "Multi-Family" key, and a `NormalizedPropertyType` enum that exists nowhere (zero grep hits). |

### docs/architecture/modules/

| Path | Lines | Verdict | Justification |
|---|---|---|---|
| `admin-metrics-routes.md` | 132 | **REWRITE** | Documents a fictional module: 6-of-7 endpoints, a `require_platform_admin` dependency that doesn't exist (actual `get_admin_user`, `deps/admin.py:5`), a `/conversion` path that is actually `/conversion-funnel` (`admin_metrics.py:416`), and return shapes sharing zero fields with the real `OverviewStats` (`admin_metrics.py:38-66`). |
| `cli-tools.md` | 266 | **REWRITE** | Scripts exist; interfaces are wrong: `--report-types` flag doesn't exist (`qa_deliver_reports.py:211-226`), "8 configurations" →12 (`:37`), `--email/--password` → `--login-email/--login-password`, and it names env vars `SIMPLYRETS_API_KEY/SECRET` that exist nowhere in the repo (real: `SIMPLYRETS_USERNAME/PASSWORD`). |
| `email-template.md` | 139 | **REWRITE** | `schedule_email_html` signature invented (actual: 18 params, `template.py:1804-1823`); 4 of 8 `LAYOUT_MAP` entries wrong (`template.py:1106-1115`); "no hardcoded brand colors" falsified (`:204,270,343,646`); "dark mode CSS removed" falsified (`:2230`). |
| `filter-resolver.md` | 184 | **KEEP** | Every line ref and signature verified exactly (`compute_market_stats` L29, `resolve_filters` L65, `build_filters_label` L152, `elastic_widen_filters` L198). The one accurate module doc. |
| `market-reports-audit.md` | 265 | **DELETE** | Dated point-in-time audit whose headline issues are fixed: "recipients hardcoded to `[]`" — falsified (`unified-wizard/index.tsx:278-280,331`); "open_houses has no template" — falsified (`print/[runId]/page.tsx:128`); cites a `STORY_TO_REPORT_TYPE` symbol that doesn't exist. Reads as an open bug list for bugs that no longer exist. |
| `property-builder.md` | 222 | **REWRITE** | `__init__(theme, selected_pages)` → actual `__init__(report_data)` (`property_builder.py:264`); documented `render()` entry point doesn't exist (actual `render_html()`, `:1038`); "default 9 pages" → actual 7 (`:292`). Color-system section verified. |
| `property-routes-comparables.md` | 200 | **REWRITE** | Two routes that don't exist (`PUT /reports/{id}`, `POST /reports/{id}/generate`); omits 6 real routes; request/response schemas don't match `ComparablesRequest`/`ComparablesResponse` (`property.py:227-242,760-769`); duplex/triplex map to `multifamily` not `residential` (`:90-95`); beds tolerance off by one at every ladder level (`:574-576`). |
| `qr-landing-leads-sms.md` | 384 | **KEEP** | Broadly verified: QR service internals, all 5 lead endpoints, honeypot, rate limits, migrations 0034/0035/0039 all check out. Two blemishes: worker SMS uses the Twilio SDK not raw httpx (`sms/send.py:17`), and one undocumented endpoint (`lead_pages.py:406`). |
| `simplyrets-api-service.md` | 107 | **REWRITE** | Signatures fictional: `build_comparables_params(subject, options)` → actual 11 flat kwargs (`simplyrets.py:90-102`); claims `PropertyData` normalization that doesn't happen (`:74-77` returns raw JSON); claims `HTTPException` raises that are actually bare `Exception` (`:64-70`); names env vars that exist nowhere. |
| `sitex-api-service.md` | 135 | **REWRITE** | Wrong API host, wrong token path, wrong search path (actual `api.uat.bkitest.com`, `/ls/apigwy/oauth2/v1/token`, `/realestatedata/search` — `sitex.py:39,46,50`); wrong exception name; methods attributed to the wrong class; a `normalize_sitex` function that doesn't exist; wrong cache-key scheme (`:567-572`). |
| `test-suite.md` | 166 | **REWRITE** | The quoted `pytest.ini` is wrong on every line — actual `testpaths = apps/api/tests apps/worker/tests`, not root `tests/`; quoted `playwright.config.ts` baseURL wrong (actual `E2E_BASE_URL \|\| vercel.app`, `playwright.config.ts:5`); omits 3 of 4 root test files. |
| `worker-core.md` | 244 | **REWRITE** | The documented `cache.py` API is fictional (`cache.set(key, value)` → actual `set(namespace, payload, data)` `cache.py:33`; no `delete()` exists; no `Cache` class); `check_report_limit() → bool` doesn't exist (actual `check_usage_limit() → Dict`, `limit_checker.py:30`). schedules_tick/app.py sections verified modulo line drift. |
| `worker-simplyrets-vendor.md` | 138 | **DELETE** | Documents code that was never written: `Link: rel=next` pagination, `X-Total-Count`, four `SimplyRETS*Error` exception classes, a `paginate` param, a `filters`-dict API, `requests`+`threading.local` — none exist in the 131-line module (`vendors/simplyrets.py` uses httpx, offset paging, deque). Rewriting from scratch is cheaper than fixing; the module is small enough to read directly. |
| `worker-tasks.md` | 202 | **REWRITE** | Content sound — every documented symbol exists and pipeline descriptions hold — but every line number is stale by 45-60 lines (`generate_report` "L778" → `tasks.py:823`; `process_consumer_report` "L1382" → `:1442`) and it names a `generate_property_report_task` that is actually `generate_property_report` (`property_report.py:421`). |

### docs/archive/, docs/design/, docs/fix/, docs/plan/

| Path | Lines | Verdict | Justification |
|---|---|---|---|
| `archive/SELLER_REPORT_INTEGRATION.md` | 680 | **DELETE** | Describes an architecture that never shipped: no `seller_report.jinja2`/`seller_base.jinja2`/`bases/theme_N` anywhere, WeasyPrint never adopted (zero hits), no `POST /reports/seller/generate`, page sets are 7 not 21/9 (`property_builder.py:292`). Note: its stale naming leaked into live code comments (`property_builder.py:210`, `property_report.py:9,16` reference the nonexistent `seller_report.jinja2`) — fix those separately. |
| `archive/cursor_documentation_and_commit_review.md` | 75,067 | **DELETE** | A raw exported Cursor chat transcript (Jan 2026). 96% of the audited line count, referenced by nothing, work long shipped. |
| `archive/real-estate-report-html.zip` | bin | **DELETE** | Binary zip referenced only by the transcript above. |
| `design/index.html` | 81 | **KEEP** | Gallery index for the four layout references below. (Its grep "refs" are false positives on the generic name `index.html`.) |
| `design/analytics-layout.html` | 618 | **KEEP** | Named "definitive visual reference" by `.cursor/rules/market-report-templates-skill.md:341`. |
| `design/closed-inventory-layout.html` | 624 | **KEEP** | Same — active skill reference. |
| `design/gallery-layout.html` | 576 | **KEEP** | Same — active skill reference. |
| `design/market-narrative-layout.html` | 526 | **KEEP** | Same — active skill reference. |
| `design/theme-gallery-bold.html` | 131 | **DELETE** | Referenced by nothing. |
| `design/theme-gallery-classic.html` | 130 | **DELETE** | Referenced by nothing. |
| `design/theme-gallery-elegant.html` | 132 | **DELETE** | Referenced by nothing. |
| `design/theme-gallery-modern.html` | 132 | **DELETE** | Referenced by nothing. |
| `design/theme-gallery-teal.html` | 131 | **DELETE** | Referenced by nothing. |
| `fix/CURSOR_FIX_SCHEDULE_RECIPIENTS.md` | 167 | **DELETE** | One-shot fix prompt, fully SHIPPED (all 4 steps in code: `step-deliver.tsx:14,158-162`; `index.tsx:191-192,331-336`). Every "BEFORE" snippet it quotes no longer exists. Referenced by nothing. |
| `plan/GOPHER-001-REPORT.md` | 285 | **DELETE** | One-shot pre-build investigation; all three recommendations shipped (`template_filters.py`; market `_base` fork; `tasks.py:1093-1120`). Referenced by nothing except the playbook (also dying). |
| `plan/MARKET_REPORT_AGENT_PROMPTS.md` | 430 | **DELETE** | Agent-role prompts for a completed project; superseded by `.claude/skills/multi-agent-workflow/SKILL.md`. Cites a wrong migration number (says 0044, actual `0046_market_report_theme.sql`) and a script that doesn't exist. |
| `plan/MARKET_REPORT_PDF_PLAYBOOK.md` | 536 | **DELETE** | The work SHIPPED (P1-P2 verified ticket-by-ticket). Actively harmful as future intent: P3-T1 ("remove schedule mode") is now wrong-by-design — the unified wizard is shared by 3 routes; its acceptance criterion for the legacy fallback contradicts shipped behavior (`tasks.py:1095-1099` — fallback deliberately removed). Only live content: the P4-T3 legacy-cleanup list — move to an issue, not a doc. |
| `plan/V0_MARKET_REPORTS_SPEC.md` | 156 | **DELETE** | Shipped verbatim — the 8-type→4-layout mapping is now code (`market_builder.py:56-66`). The code is the spec now. Its run instructions point at a script and output dir that don't exist. |
| `plan/sample/new-listings-gallery.html` | 691 | **DELETE** | One-shot design input; only one CSS class survives into production templates (`macros.jinja2:445`). Silently drifting "reference." |

### Root-level docs

| Path | Lines | Verdict | Justification |
|---|---|---|---|
| `README.md` | 186 | **REWRITE** | Referenced entry point, but 7 falsified counts/claims (§2.5), including a `pnpm dev` that starts nothing. |
| `LOCAL_SETUP_GUIDE.md` | 389 | **REWRITE** | A setup guide is needed and its infra half is accurate, but it's frozen at Nov 2025: the walkthrough city (Houston) is rejected by CRMLS validation, a dead env var, "13+ tables" (actual 47), and it ends by pointing at "Phase 24B" work that shipped long ago. |
| `SourceOfTruth.md` | 600 | **DELETE** | V14, correctly banner-deprecated in favor of `docs/architecture/SOURCE_OF_TRUTH.md`. The banner is the only thing keeping it honest; the file serves no purpose. |
| `MARKET_REPORTS_CODE_DUMP.md` | 3,046 | **DELETE** | 108KB verbatim source-code paste "Generated: March 12 2026" for a one-shot debugging session. No staleness warning, nothing regenerates it, and every embedded file has since changed. |

### .cursor/rules/ and agent docs (audited per Phase 2.4; not in the kill list — separate decision)

| Path | Verdict | Justification |
|---|---|---|
| `.cursor/rules/db-schema.md` | **KEEP** | Highest-fidelity doc in the repo: 5 tables spot-checked column-by-column against migrations — all real, including post-rename `plans` columns and the gotchas table. Its 4 false claims are all in the non-schema PDF preamble (see §2.6). |
| `.cursor/rules/skills/references/pdf-pipeline.md` | **REWRITE** | Engine-selection story is wrong: selection is by `PDF_ENGINE` env (default **playwright**, `pdf_engine.py:30`), not PDFShift-key presence with fallback; missing key raises (`:159-160`). Also claims `/print/{runId}` removed (it isn't) and a `render_pdf(html)` adapter API that doesn't exist. |
| `.cursor/rules/skills/references/architecture.md` | **REWRITE** | "26 route modules" (→29), "latest migration 0051" (→0052). |
| `.cursor/rules/skills/references/conventions.md` | **REWRITE** | Repeats the fictional `pdf_adapter.render_pdf()` (actual `generate_pdf(url,...)`, `pdf_adapter.py:22`). |
| `.cursor/rules/skills/references/forbidden.md` | **KEEP** | UNVERIFIED in depth — path checks passed; content claims not exhaustively audited. |
| `.cursor/rules/*-skill.md` (4 design skills) | **KEEP** | Template paths and referenced routes all resolve. Fix: each file's line 3 tells the reader to install it under a filename without the `-skill` suffix, which doesn't exist. |
| `.cursor/rules/skills/README.md` + 5 `trendyreports-*/SKILL.md` | **KEEP** | All cross-links resolve; placeholder paths are labeled as such. |
| `.cursorrules.md` | **REWRITE** | Committed as `.cursorrules.md`, so Cursor never auto-loads it (its own line 2 says it belongs at `.cursorrules`); links `GOPHER-001_REPORT.md` (underscore — dead; actual hyphen). |
| `.claude/skills/multi-agent-workflow/SKILL.md` | **KEEP** | Current (added 2026-06-24, `d48a619`); one trivial dead prose ref (`tests/render`). |

---

## 2. Falsified Claims Log

Every claim below was disproved against code at HEAD `f854ed6`. Doc line → disproving code.

### 2.1 `docs/architecture/SOURCE_OF_TRUTH.md` (the canonical doc)

1. **L58, L65** "28 router mounts" / "Route modules (28)" — actual **29**: `main.py:92-120`; the table omits `company` (`main.py:120`, `routes/company.py`, prefix `/v1/company`).
2. **L157** "46 numbered SQL migrations (0001 through 0046)" — actual **52**: `db/migrations/0052_simplify_contact_types.sql` is the highest (`ls db/migrations | grep -cE '^[0-9]{4}_'` = 52). Six shipped migrations undocumented: 0047 plan downgrade, 0048 title-company hierarchy, 0049 branding override, 0050 pct-to-title-company, 0051 per-product limits, 0052 contact types.
3. **L44** "181 component files" — actual 177 `.tsx` / 191 total (`find apps/web/components -name '*.tsx' | wc -l`). No counting method yields 181.
4. **L60** "15 business logic modules" in services — actual **19** (`ls apps/api/src/api/services/`). Unlisted: `brand_resolver`, `agent_code`, `qr_service`, `billing_state`, `plan_lookup`, `invite_service`, `property_stats`, `sample_report_data`, `schedule_utils`, `accounts`.
5. **L209** table `webhook_endpoints` — **does not exist**. Zero hits repo-wide. The actual table is `webhooks` (`db/migrations/0002_webhooks.sql`).
6. **L217** table `lead_pages` — **does not exist** in any migration. `routes/lead_pages.py` reads/writes `consumer_reports` and `leads`.
7. **L212** table `signup_tokens` — not created by anything in `db/migrations/`; it exists only in a second, undocumented migrations directory: `apps/api/migrations/phase4_indexes.sql:38`.
8. **L314-320** §8 plan table (Free 5 / Pro 50 / Team 200 / Affiliate 500 / Sponsored 10) — falsified by `db/migrations/0051_per_product_limits.sql:11-19`: `market_reports_limit` is free=**3**, sponsored_free=**3**, pro=**99999**, team=**99999**, affiliate=**5000**; plus slugs `starter` and `solo` exist and are unlisted. UI renames Starter/Pro → "Growth"/"Growth Plus" (commit `9b095ff`). Prices $29/$99: UNVERIFIED — could not confirm anywhere in the repo.
9. **L421** `GET /health → {"status": "ok", "db": "ok", "redis": "ok"}` — actual `{"ok": True, "service": settings.APP_NAME}`; no DB or Redis probe exists (`routes/health.py:6-8`).
10. **L263, L494** "See `.env.example` for the full template" — `.env.example` is 26 lines and contains **none** of `SENDGRID_API_KEY`, `SIMPLYRETS_*`, `PDFSHIFT_API_KEY`, `OPENAI_API_KEY`, `R2_*`, `TWILIO_*`, `STRIPE_PRICE_*`; instead it names `RESEND_API_KEY`/`POSTMARK_API_KEY`/`S3_*`, none of which any code reads. **Security flag:** it also contains live-looking SiteX UAT client credentials (`.env.example:23-25`) committed to git.
11. **L27, §6** "8 report types" — 8 slugs exist in `reportTypes.ts:32-74`, but `open_houses` is disabled in the wizard (commits `26f1e7b`, `3164cbb`); user-facing count is 7.
12. **L114** `generate_report` "(L778)" → `tasks.py:823`; `process_consumer_report` "(L1382)" → `tasks.py:1442`; `ping`/`keep_alive_ping` off by 2.
13. **L116** `MarketReportBuilder` "(L70)" → `market_builder.py:156`.
14. **L118** all seven `report_builders.py` line refs drifted (e.g. `build_result_json` "L892" → `:980`), and the list omits `build_open_houses_result` (`report_builders.py:911`) while claiming to cover "all 8" with 7 builders.
15. **L122** `render_pdf` "(L218)" → `pdf_engine.py:308`. **L125** `generate_market_pdf_narrative` "(L177)" → `ai_market_narrative.py:257`. **L129** `schedule_email_html` "(L1682)" → `template.py:1804`; `schedule_email_subject` "(L2215)" → `:2358`.
16. **L254/259/260** authn.py line ranges all drifted: `AuthContextMiddleware` → `authn.py:63`, `RateLimitMiddleware` → `:193`, `_is_token_blacklisted` → `:171`.
17. **L119** `run_forever` "(L437)" → `schedules_tick.py:459`.

Verified true (credit where due): 8 report slugs incl. `closed`; middleware LIFO stack and the RLS-not-registered note (`main.py:65-72`); beat schedule; all dependency versions; packages/ui = 109; all 25 integration module paths; all listed test files; 4 CI workflows; demo account emails (`db/seed_demo_accounts_v2.sql`; passwords UNVERIFIED); `get_plan_catalog` L57; admin metrics path; **zero dead links in the §13 docs index**.

### 2.2 Cross-doc count contradictions (no two docs agree; none is right)

| Fact | Doc claims | Actual |
|---|---|---|
| Router count | 26 (`backend-core.md:23`, `backend-routes.md:3`, `INDEX.md:16,83`, `SITE_ARCHITECTURE_TREE.md:29,341`, `references/architecture.md:26`) · 28 (`ARCHITECTURE_AUDIT.md:77`, `README.md:80-81`, `SOURCE_OF_TRUTH.md:58`) | **29** (`main.py:92-120`) |
| Migrations | 42 (`SITE_ARCHITECTURE_TREE.md:146`) · 46 (`SOURCE_OF_TRUTH.md:157`, `README.md:105`) · 47 (`ARCHITECTURE_AUDIT.md:78`) · "latest 0051" (`references/architecture.md:89`) | **52 numbered + 1 seed** |
| Service modules | 15 (`SOURCE_OF_TRUTH.md:60`, `README.md:82`, `SITE_ARCHITECTURE_TREE.md:342`) | **19** |
| Proxy routes | ~60 (`INDEX.md:133`, `SITE_ARCHITECTURE_TREE.md:86`) | **127** |
| ui/ primitives | 50+ (`frontend-components.md:258`) · 75 (`INDEX.md:135`, `TREE.md:88`) | **58** |
| packages/ui components | 60+ (`TREE.md:138`) | **37** |
| Property wizard steps | 5 (`WIZARD_AND_API_CALLS.md:11-17`) · 4 (`WIZARD_FLOW:13`, `frontend-components.md:126`) | **4** (`components/property-wizard/`) |
| `/app/reports/new` component | ReportBuilderWizard (`WIZARD_FLOW:160`) · UnifiedReportWizard (`frontend-components.md:31`) | **UnifiedReportWizard** (`app/app/reports/new/page.tsx:6`); `v0-report-builder/` has zero importers |
| module docs count | 13 (`ARCHITECTURE_AUDIT.md:39`, `README.md:168`) · 14 (its own table) | **14** |

### 2.3 Fabricated API documentation (worst category — describes code that never existed)

- **SiteX API** (`WIZARD_AND_API_CALLS.md:188-246`, `sitex-api-service.md:54-88`): base `https://api.sitexpro.com` → actual `https://api.uat.bkitest.com` (`sitex.py:39`); token `POST /oauth/token` → `/ls/apigwy/oauth2/v1/token` (`:46`); search `GET /v2/property/search` → `/realestatedata/search` (`:50`); params `address/city/state/zip` → `addr/lastLine/feedId/options` (`:351`); `MultiMatchError` → `SiteXMultiMatchError` (`:206`); `normalize_sitex` — no such function.
- **`POST /v1/property/reports/{id}/generate`** (`WIZARD_AND_API_CALLS.md:64-65`, `property-routes-comparables.md:25`, `SITE_ARCHITECTURE_TREE.md:291`, `cli-tools.md:118-124`): route does not exist; enqueue is inline in `POST /reports` (`property.py:1181`).
- **`SimplyRETS*Error` exception hierarchy, `Link: rel=next` pagination, `X-Total-Count`, `paginate=` param** (`worker-simplyrets-vendor.md:14,21,66,92-113`): none exist; actual is offset paging with `MAX_RESULTS` guard (`vendors/simplyrets.py:79-104`).
- **`SIMPLYRETS_API_KEY` / `SIMPLYRETS_API_SECRET`** (`cli-tools.md:85,217-218`, `simplyrets-api-service.md:60,88`): exist nowhere; actual `SIMPLYRETS_USERNAME`/`SIMPLYRETS_PASSWORD` (`services/simplyrets.py:20-21`, `vendors/simplyrets.py:8-9`).
- **`NormalizedPropertyType` enum** (`property-type-data-contract.md:236-249`): zero grep hits repo-wide.
- **`cache.py` key/value API with `delete()` and a `Cache` class** (`worker-core.md:163-189`): actual is namespace/payload functions, no delete, no class (`worker/cache.py:28,33`).
- **`require_platform_admin` dependency** (`admin-metrics-routes.md:3,82,95`): actual `get_admin_user` (`deps/admin.py:5`).
- **`PropertyReportBuilder.render()` / `pdf_adapter.render_pdf(html)`** (`property-builder.md:60`, `db-schema.md:16`, `pdf-pipeline.md:25,33`, `conventions.md:94`): actual `render_html()` (`property_builder.py:1038`) and `generate_pdf(url, ...)` (`pdf_adapter.py:22`).

### 2.4 Dead paths referenced by docs (file/route absent on disk)

- `apps/web/app/help/page.tsx` (`frontend-pages.md:21`) — actual location `app/app/help/`.
- `apps/web/app/branding-preview/**` (`frontend-pages.md:39-40`) — no such directory.
- 10 proxy routes in `frontend-api-proxy.md:55,68,82,99,106,107,129,136,146,147` (e.g. `v1/accounts/[id]`, `v1/billing/customer-portal`, `v1/onboarding/status`) — none exist at those paths.
- `scripts/gen_market_all_themes.py` + `output/market_themes/` (`MARKET_REPORT_PDF_PLAYBOOK.md:63,237,241-244,302,352`; `MARKET_REPORT_AGENT_PROMPTS.md:172,223,352`; `V0_MARKET_REPORTS_SPEC.md:152-156`; `references/pdf-pipeline.md:77`) — actual `scripts/gen_market_reports.py` → `output/market_reports/` (`gen_market_reports.py:15-17`; note that output dir is also currently absent on disk).
- `docs/architecture/modules/{frontend-components,frontend-pages,backend-routes}.md` (`MARKET_REPORT_PDF_PLAYBOOK.md:488-490`) — exist only at `docs/architecture/` level, not under `modules/`.
- `docs/plan/GOPHER-001_REPORT.md` — underscore typo in `.cursorrules.md:17` and `MARKET_REPORT_PDF_PLAYBOOK.md:509`; actual file uses a hyphen.
- `seller_report.jinja2`, `seller_base.jinja2`, `bases/theme_{1..5}_*.jinja2`, `templates/reports/seller/`, `weasyprint`, `test_seller_report.py` (`SELLER_REPORT_INTEGRATION.md:10-51,370,535,620,646,676`) — none ever existed in this repo; the naming also leaked into live code comments (`property_builder.py:210`, `property_tasks/property_report.py:9,16`).
- Migration `0044_market_report_theme.sql` (`MARKET_REPORT_AGENT_PROMPTS.md:171`) — `0044` is `0044_cma_funnel_redesign.sql`; theme migration is `0046`.

### 2.5 `README.md` and `LOCAL_SETUP_GUIDE.md`

- `README.md:153` `pnpm dev # Frontend (localhost:3000)` — root `package.json:16` maps `dev` to `scripts/dev.sh`, a stub that starts nothing (echoes "will run in Section 2/3"); `dev:api`/`dev:worker` are `echo` placeholders (`package.json:14-15`). Working command: `cd apps/web && pnpm dev`.
- `README.md:105` "46 SQL migrations" → 53 files; `:81-82` "28 routes / 15 services" → 29/19; `:73` "181 React components" → 177/191; `:120` "42 scripts" → 47; `:168` "13 modules" → 14.
- `LOCAL_SETUP_GUIDE.md:219` Houston walkthrough — `apps/api/src/api/crmls_cities.py` contains zero Houston (CRMLS SoCal-only); the walkthrough cannot succeed as written.
- `LOCAL_SETUP_GUIDE.md:169` `NEXT_PUBLIC_DEMO_ACCOUNT_ID` — zero references under `apps/web/`; dead env var.
- `LOCAL_SETUP_GUIDE.md:84-101` migration output ending at 0006 and "13+ tables" — 53 migration files run; 47 tables.
- `LOCAL_SETUP_GUIDE.md:384` "Continue with Phase 24B (API routes for schedules)" — shipped long ago (`routes/schedules.py`, migrations 0006/0015/0016/0027/0033).

### 2.6 `.cursor/rules` content claims

- "PDFShift-key presence selects the engine, Playwright fallback" (`pdf-pipeline.md:51-53`, `db-schema.md:33-37`) — selection is `PDF_ENGINE` env, default `playwright` (`pdf_engine.py:30,350`); missing key with `PDF_ENGINE=pdfshift` **raises** (`:159-160`). A third selector (`PDF_API_URL`, `pdf_adapter.py:17-18,37`) is documented nowhere.
- "legacy `/print/{runId}` has been removed" (`db-schema.md:68`, `pdf-pipeline.md:110`) — the route exists (`apps/web/app/print/[runId]/page.tsx`) and the worker still builds URLs against it (`tasks.py:1069,1096`, `PRINT_BASE` at `:249`).
- `backend-core.md:131` "cache.py consumed by RateLimitMiddleware" — the middleware constructs its own redis client (`authn.py:203,217-218,236`); `cache.py` has zero consumers.

### 2.7 Docs describing already-fixed states as current

- `performance-audit.md` — all 5 spot-checked findings resolved; every `file:line` now points at unrelated code (details in verdict table).
- `market-reports-audit.md` Issues 1 & 7 — recipients bug fixed (`unified-wizard/index.tsx:278-280,331,191-192`); open_houses template exists (`print/[runId]/page.tsx:128`).
- `backend-services.md:37` claims a query-duplication bug that `backend-routes.md:63-64` says is fixed — the routes doc is right per `affiliates.py:60-68` batching.

---

## 3. Coverage Gaps

Subsystems with **no documentation anywhere**:

1. **Company / title-company portal** — `routes/company.py` (mounted `main.py:120`), 9 proxy routes, 6 pages under `app/app/company/`, migrations `0048_title_company_hierarchy.sql`–`0050_pct_to_title_company.sql`. Shipped after the docs froze; invisible to every doc.
2. **Onboarding system** — `routes/onboarding.py`, `onboarding_progress` table, the guided `/app/get-started` flow (commits `8afb7c0`, `9e4b58c`), delivery-based completion metrics. Nothing documents it.
3. **The second top-level `/admin` app tree** — 14 pages under `apps/web/app/admin/` (separate from `/app/admin`), plus 18 direct `/api/v1` routes. No doc mentions it exists.
4. **Per-product limits / billing state** — `billing_state.py`, `plan_lookup.py`, migration 0051's `market_reports_limit`/`schedules_limit`/`property_reports_per_month` model, plan downgrade columns (0047). The only doc describing plans (§8 of SOURCE_OF_TRUTH) is wrong.
5. **The second migrations directory** — `apps/api/migrations/phase4_indexes.sql` creates `signup_tokens` outside `db/migrations/`; no doc (or migration runner doc) acknowledges it.
6. **`mobile_reports` route** — one line in the SOURCE_OF_TRUTH router table; nothing else.
7. **e2e suite** — `e2e/*.spec.ts` + `playwright.config.ts` get one wrong paragraph in `test-suite.md`.
8. **`report_builders.py` / `market_builder.py`** as a module doc — the largest worker surface has no dedicated module doc (only SOURCE_OF_TRUTH one-liners); the playbook references module docs for it that were never written.
9. **Dead code inventory** — `v0-report-builder/` (zero importers), `apps/web/lib/templates.ts` + 7 `trendy-*.html` legacy templates + `/print/[runId]` (the "P4-T3 cleanup" the playbook deferred). No doc tracks what is intentionally dead vs. live.

---

## 4. Proposed Final Doc Set

Minimum set to fully describe the platform to a zero-context agent. Counts should be generated (script), never hand-written.

| File | Scope (one line) |
|---|---|
| `README.md` (rewrite) | What the product is, monorepo map, working dev commands, links to the three docs below. |
| `docs/SETUP.md` (rewrite of LOCAL_SETUP_GUIDE) | Docker/DB/Redis bring-up, migrations (both directories), env vars that actually exist, a walkthrough with a CRMLS city. |
| `docs/architecture/SOURCE_OF_TRUTH.md` (V17 rewrite) | System map: apps, 29 routers, 52+ migrations, integrations, data model, auth, plans-as-shipped, report types (7 live + 1 disabled), hosting. |
| `docs/architecture/INDEX.md` (rewrite) | Source-tree navigation only — no counts, no claims that can drift. |
| `docs/architecture/backend.md` (merge core+middleware+routes+services) | FastAPI bootstrap, middleware stack, router inventory incl. `company`, service layer incl. all 19 modules, proxy convention paragraph. |
| `docs/architecture/frontend.md` (merge core+pages+components) | Next.js config, both admin trees, company portal, page inventory, component org, dead-code notes (`v0-report-builder`, legacy print path). |
| `docs/architecture/worker.md` (merge worker-core+worker-tasks+builders) | Celery app, schedules tick, generate_report/process_consumer_report pipelines, market/property builders, PDF engine selection (`PDF_ENGINE`), email templates. |
| `docs/architecture/wizards-and-apis.md` (merge the two WIZARD docs) | Both wizards (4-step property, unified market), correct SiteX/SimplyRETS endpoints, comparables ladder, caching. |
| `docs/architecture/property-type-data-contract.md` (rewrite) | SiteX→SimplyRETS type mapping with CamelCase values — kept because live code cites it (`property.py:64,533`). |
| `docs/architecture/modules/filter-resolver.md` (keep as-is) | Market-adaptive filters + elastic widening. |
| `docs/architecture/modules/qr-landing-leads-sms.md` (keep, 2 fixes) | QR / lead pages / SMS funnel. |
| `.cursor/rules/db-schema.md` (keep; fix preamble; re-dump on schema change) | Authoritative table/column reference. |
| `docs/design/` 4 layout HTMLs + index (keep) | Visual reference for market-report PDF layouts (cited by the templates skill). |

Everything else in `docs/` dies. New-subsystem docs (company portal, onboarding) belong as sections of `backend.md`/`frontend.md` until they stabilize, not as new files.

---

## 5. Kill List

Ready to run from repo root. **Not executed — Phase 0 respected; nothing in this audit modified or deleted any existing file.**

```bash
# Stale/duplicate sources of truth
git rm SourceOfTruth.md
git rm docs/architecture/SourceOfTruth.md

# Self-invalidated audits
git rm docs/architecture/ARCHITECTURE_AUDIT.md
git rm docs/architecture/performance-audit.md
git rm docs/architecture/modules/market-reports-audit.md

# Redundant / always-stale inventories
git rm docs/architecture/SITE_ARCHITECTURE_TREE.md
git rm docs/architecture/frontend-api-proxy.md

# Module doc describing never-written code
git rm docs/architecture/modules/worker-simplyrets-vendor.md

# Shipped plans and one-shot artifacts
git rm docs/plan/GOPHER-001-REPORT.md
git rm docs/plan/MARKET_REPORT_AGENT_PROMPTS.md
git rm docs/plan/MARKET_REPORT_PDF_PLAYBOOK.md
git rm docs/plan/V0_MARKET_REPORTS_SPEC.md
git rm docs/plan/sample/new-listings-gallery.html
git rm docs/fix/CURSOR_FIX_SCHEDULE_RECIPIENTS.md

# Archive: transcript, dead integration guide, binary
git rm docs/archive/cursor_documentation_and_commit_review.md
git rm docs/archive/SELLER_REPORT_INTEGRATION.md
git rm docs/archive/real-estate-report-html.zip

# Unreferenced design galleries
git rm docs/design/theme-gallery-bold.html
git rm docs/design/theme-gallery-classic.html
git rm docs/design/theme-gallery-elegant.html
git rm docs/design/theme-gallery-modern.html
git rm docs/design/theme-gallery-teal.html

# One-shot code dump (root)
git rm MARKET_REPORTS_CODE_DUMP.md

# After merging its SiteX section into WIZARD_AND_API_CALLS.md:
git rm docs/architecture/WIZARD_FLOW_AND_API_CALLS.md
```

24 files (+1 post-merge), removing ~85,000 lines of which ~75,000 are one chat transcript.

**Follow-ups outside this audit's scope (report only, not done):**
- Fix stale code comments referencing `seller_report.jinja2` (`apps/worker/src/worker/property_builder.py:210`, `apps/worker/src/worker/property_tasks/property_report.py:9,16`).
- Rotate/remove the SiteX UAT credentials committed in `.env.example:23-25`.
- Rename `.cursorrules.md` → `.cursorrules` (or wire it into Cursor properly) if it's meant to load.
- Decide the fate of dead frontend code the docs revealed: `apps/web/components/v0-report-builder/` (zero importers), legacy `lib/templates.ts` + `trendy-*.html` + `/print/[runId]` (playbook P4-T3).
