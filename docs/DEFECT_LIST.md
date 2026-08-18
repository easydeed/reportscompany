# DEFECT LIST — Phase 2A (local verification sweep)

**Date:** 2026-08-18
**Plan:** `EXECUTION_PLAN_REV_A.md` Phase 2A (local only)
**Tickets covered:** T2.1 (test account provisioning), T2.2 (company / title-company portal), T2.4 (registration → onboarding → first-run), T2.6 (authenticated smoke test), T2.7 (migration state)
**Status:** Phase 2A complete (T2.1, T2.2, T2.4, T2.6, T2.7), plus the F5 affiliate-surface audit. All of Phase 2B remains blocked on deployed access.
**Fix status:** D-005/D-007 fixed (PR #24). D-001 and D-016 fixed on `fix/p4-broken-defects`.

## Severity counts

| Severity | Count |
|---|---|
| BROKEN | 7 |
| WRONG | 6 |
| FRAGILE | 6 |
| ROUGH | 2 |
| **Total** | **21** |

Plus 4 items marked BLOCKED-NEEDS-DEPLOYED-ACCESS and 1 UNVERIFIED.

## Test environment

Local, per Rev A §2A. Postgres **16.13** (system package — the Docker daemon is unavailable in this container, so `docker-compose.yml`'s `postgres:15-alpine` could not be used; **version deviation from production**), Redis 7.0.15, API on `127.0.0.1:10000` via uvicorn, venv **Python 3.12** (see D-003), `ENVIRONMENT=development`, `JWT_SECRET=local-test-secret`. Database built from `db/migrations/` (see D-001 for how). Accounts provisioned by `scripts/seed_test_accounts.py` (T2.1).

**Critical context for reading everything below:** the app connects to Postgres as the `postgres` **superuser**, which owns every table, and no migration issues `FORCE ROW LEVEL SECURITY`. Postgres therefore **does not apply RLS policies to the application at all**. Verified directly:

```
psql> SELECT current_user, usesuper;                        -> postgres | t
psql> SELECT relname, relrowsecurity, relforcerowsecurity
      FROM pg_class WHERE relname='report_generations';     -> report_generations | t | f
-- as superuser, with Company A's RLS context set:
BEGIN; SET LOCAL app.current_account_id='<company A>';
SELECT count(*) FROM report_generations WHERE account_id LIKE 'bbbb%';  -> 3   (B's rows visible)
-- identical query as a non-superuser role:
                                                             -> 0   (RLS applies)
```

All tenant isolation observed below is produced by **hand-written SQL predicates**, not by RLS. Every `WHERE account_id = ...` is load-bearing; every omission is a live leak.

---

## BROKEN

### D-005 — Cross-tenant data leak: any title company can read another company's reports and schedules
**Severity:** BROKEN · **Affects:** TITLE_COMPANY (attacker), COMPANY_REP + SPONSORED of every other company (victims)

`GET /v1/company/reports` and `GET /v1/company/schedules` accept a caller-supplied `rep_id` and never verify it belongs to the caller's company.

- `apps/api/src/api/routes/company.py:494-500` — when `rep_id` is supplied, the agent lookup becomes `SELECT id FROM accounts WHERE sponsor_account_id = %s::uuid` with the **raw parameter**. The company-scoped `rep_ids` list fetched at `:485-489` is not consulted for validation.
- `company.py:502` — `all_ids = agent_ids + rep_ids`, and `:512`/`:520` then select `report_generations WHERE account_id = ANY(all_ids)`.
- Identical defect in schedules: `company.py:559-566` (lookup), `:568` (`all_ids`), `:574-589` (select).

**Reproduction (executed, not hypothetical):**
```bash
# Company B has a sponsored agent with a report in "CONFIDENTIAL-B-CITY"
# and a schedule named "B AGENT SECRET SCHEDULE".
curl -H "Authorization: Bearer <COMPANY_A_TOKEN>" \
  "http://127.0.0.1:10000/v1/company/reports?rep_id=<COMPANY_B_REP_ID>"
```
**Expected:** 403, or Company A's own data only.
**Actual:** Company A receives Company B's agent's report —
`{"report_type":"closed","city":"CONFIDENTIAL-B-CITY","account_name":"Test Agent B","user_type":"Agent"}` — and, from the schedules endpoint, `{"name":"B AGENT SECRET SCHEDULE","area":"CONFIDENTIAL-B-CITY","account_name":"Test Agent B"}` including its recipient configuration.

The `rep_id` values needed are UUIDs, but they are not secret: they are returned to every company admin in their own `/v1/company/reps` payload, and a rep that moves between companies keeps its id.

**Why RLS does not save this:** RLS is inert for the app's DB role (see above). Even if it were enforced, `company.py` never calls `set_rls` — so the policies would have no account context to match. This is failure mode (b) from the ticket: the policy exists in the migration and reads correctly, but the route never applies it.

### D-006 — No route in the company portal sets RLS context; enforcing RLS would blank the portal
**Severity:** BROKEN (latent) · **Affects:** all company-portal users

`apps/api/src/api/routes/company.py:13` imports `db_conn, fetchall_dicts, fetchone_dict` — **`set_rls` is not imported**, and none of the 10 handlers call it. The contract in `apps/api/src/api/db.py:48-51` states the required pattern (`with db_conn() as (conn, cur): set_rls(cur, account_id); ...`); 14 other route modules follow it (e.g. `apps/api/src/api/routes/reports.py:152-153`).

Handlers querying RLS-protected tables with no RLS context: `get_overview` (`company.py:78`, queries `report_generations` at `:105,:111,:155,:193,:208,:226,:250`), `list_reps` (`:335` → `:347,:353,:358`), `list_agents` (`:410` → `:422,:426`), `get_company_reports` (`:483` → `:508,:512`), `get_company_schedules` (`:549` → `:573,:582`), `get_metrics` (`:917` → `:936,:945,:960,:981`).

**Consequence:** the moment anyone hardens the DB role (non-superuser) or adds `FORCE ROW LEVEL SECURITY` — the standard fix for D-005's class — `current_setting('app.current_account_id', true)` is NULL, every policy predicate evaluates NULL, and these endpoints return **empty lists and zeros rather than errors**. The company dashboard would silently show a working page with no data. Fix D-005 and D-006 together; fixing either alone leaves the portal wrong.

### D-015 — The API test suite does not run, and has not for some time
**Severity:** BROKEN · **Affects:** all — this is the mechanism, not a symptom

**Read this one first.** Every other defect in this document is a thing that broke. This is the reason nothing caught them. `pytest apps/api/tests/` on `main` does not complete: 3 of 8 test modules fail at import, and 29 of the tests that do collect fail.

```
$ pytest apps/api/tests/ -q          # on main, before any Phase-2 work
ERROR apps/api/tests/test_billing_checkout.py
ERROR apps/api/tests/test_me_endpoint.py
ERROR apps/api/tests/test_schedules_report_types.py
!!!!! Interrupted: 3 errors during collection !!!!!

$ pytest apps/api/tests/ -q --ignore=<those three>
29 failed, 21 passed
```

Collection errors: `ModuleNotFoundError: No module named 'api.app'` and `ImportError: attempted relative import beyond top-level package`. The modules import a package path that does not exist — so these tests cannot ever have passed in their current form against the current tree.

The 29 failures are concentrated in `apps/api/tests/test_plans_limits.py`, whose mocked cursor return shapes no longer match what `apps/api/src/api/services/usage.py` reads.

**Verified pre-existing:** both numbers reproduce on `main` with no Phase-2 changes applied (checked out `main`, ran the suite, same 3 errors / 29 failures). The cross-tenant isolation branch adds 9 passing tests and no new failures.

**Why this is severity BROKEN rather than FRAGILE:** a suite in this state cannot have been run recently by anyone. The consequence is not "tests are untidy" — it is that D-005 (a live cross-tenant data leak) shipped, survived, and was found by hand-driven verification rather than by CI. `.github/workflows/backend-tests.yml` exists and runs on PR and push; either it is not running this suite or its result is not gating anything. Both possibilities are worth checking.

**Bearing on Phase 3 — start here.** The 29 failures sit in `test_plans_limits.py`, and Phase 3's entire subject is reconciling displayed plan limits against enforced plan limits. Those failing assertions encode what the limits were once expected to be; the diff between that and current behaviour is likely a substantial part of Phase 3's answer. Not investigated here — flagged so Phase 3 opens with it.

**Also note:** the new `test_company_tenant_isolation.py` needs a live database and skips without one, so it will not fire in a CI job that has no Postgres service. Wiring one in is what turns that regression guard from present into effective.

### D-016 — `signup_tokens` lives in a second migrations directory that nothing applies, so no invited account can be created
**Severity:** BROKEN · **Affects:** TITLE_COMPANY, COMPANY_REP, SPONSORED, INDUSTRY_AFFILIATE (4 of the 5 personas)

The `signup_tokens` table is created **only** in `apps/api/migrations/phase4_indexes.sql:38`. Neither runner touches that directory: `scripts/migrate.sh:9` globs `db/migrations/*.sql`, and `scripts/run_migrations.py:47` builds its path as `<repo>/db/migrations`. `grep -rl signup_tokens db/migrations/` returns nothing.

Four code paths depend on the table — `services/invite_service.py`, `services/affiliates.py`, `routes/auth.py`, `routes/admin.py` — so on any database built from the repo's documented migration process, the table is absent and those paths fail at runtime.

**Observed, on a database built exactly as the docs prescribe:**

```
POST /v1/company/invite-rep  -> 500
  {"error":"invite_failed","message":"Failed to create rep invitation:
   relation \"signup_tokens\" does not exist ... INSERT INTO signup_tokens ..."}

GET  /v1/affiliate/overview  -> 500
  psycopg.errors.UndefinedTable: relation "signup_tokens" does not exist
  (services/affiliates.py:36 — the "last_invite_sent" subquery)
```

Consequence: **invite-based onboarding is impossible.** Only `REGULAR` self-registration works, and that is the one persona that does not use invites. Every title-company rep, sponsored agent, and affiliate-invited agent is created through this path.

One thing that is right: the failed invite rolls back cleanly — 0 accounts and 0 users created after the 500, so there is no partial-write corruption.

Production presumably has the table because the file was applied by hand at some point; there is no record of when, and nothing detects the divergence. See T2.7 below for the full migration story.

### D-017 — `/v1/property/stats/affiliate` returns 500 on the empty state
**Severity:** BROKEN · **Affects:** INDUSTRY_AFFILIATE

`GET /v1/property/stats/affiliate` declares `response_model=AffiliateStatsResponse` (`apps/api/src/api/routes/property.py:835`) but the handler's return value omits the required `themes` field, so FastAPI raises after the handler succeeds:

```
fastapi.exceptions.ResponseValidationError: 1 validation error:
{'type':'missing','loc':('response','themes'),'msg':'Field required',
 'input': {'period':{...},'summary':{'total_agents':0,...},'aggregate':{},
           'leaderboard':[],'agents':[],'inactive_agents':[]}}
```

Reproduced as an `INDUSTRY_AFFILIATE` with no sponsored agents — i.e. **the state every new affiliate is in on day one**. The data-bearing path may populate `themes`; the empty path does not, and the response model does not allow its absence.

### D-018 — `/v1/dev/stripe-prices` crashes on a type mismatch
**Severity:** WRONG · **Affects:** all (dev/staging surface)

`apps/api/src/api/routes/dev_stripe_prices.py:34` indexes the catalog entries as dicts — `plan["plan_name"]`, `plan["stripe_price_id"]` — but `get_plan_catalog()` returns `PlanCatalog` objects:

```
TypeError: 'PlanCatalog' object is not subscriptable
```

500 for every persona. The route is meant to be dev-only; note it is reachable (not 404'd) whenever `ENVIRONMENT != production`, so it is live on any staging deploy. Relevant to Phase 3: this is the endpoint intended to show which Stripe price IDs the app believes in.

### D-019 — Email verification is not enforced anywhere
**Severity:** WRONG · **Affects:** REGULAR (and any self-registered account)

`POST /v1/auth/register` creates the user with `email_verified = false` (confirmed in the database) and returns `{"ok":true,"email_verified":false}`. Logging in immediately afterwards with the same credentials **succeeds**, and every authenticated surface then works normally — `/v1/onboarding`, `/v1/me`, `/v1/account/plan-usage`, `/v1/reports`, `/v1/schedules`, `/v1/contacts` all returned 200 for the unverified account.

So the verification email is decorative: nothing gates on `users.email_verified`. Whether that is intended is a product decision, but it should be a decision — as written, the flow implies a gate that does not exist, and an address typo produces a working account nobody can reach.

Minor, same endpoint: the docstring for `register` (`apps/api/src/api/routes/auth.py:229-238`) claims it "Returns auth session (JWT + cookie)". It does not — the response carries no token.

### D-001 — A fresh database cannot be built by `scripts/migrate.sh`
**Severity:** BROKEN · **Affects:** all (dev onboarding, CI, disaster recovery)

`bash scripts/migrate.sh` against an empty database aborts at file 11 of 53.

- `db/migrations/0007_phase_29a_plans_and_account_types.sql:11-17` creates `plans(slug, name, monthly_report_limit, ...)`.
- `db/migrations/0011_create_plans_table.sql:5-12` is `CREATE TABLE IF NOT EXISTS plans(plan_slug, plan_name, stripe_price_id, ...)` — a no-op against the existing table — and then `:14` creates an index on `stripe_price_id`, a column that does not exist yet.
- `scripts/migrate.sh:11` runs `psql -v ON_ERROR_STOP=1`, so the run dies. `0012_seed_plans.sql` would fail next (it inserts `plan_slug`).
- `db/migrations/0013_unify_plans_table.sql:6-33` is the guarded reconciliation that adds `stripe_price_id` and renames `slug`→`plan_slug` — i.e. 0011/0012 are ordered before the migration that makes them valid.

**Expected:** all migrations apply in order on a fresh database.
**Actual:** `psql:db/migrations/0011_create_plans_table.sql:14: ERROR: column "stripe_price_id" does not exist`, run aborts, 42 migrations never applied.
**Workaround used for this phase (documented, not committed):** applied 0011/0012 with errors tolerated, then 0013–0052 strictly. Result: 38 tables, 17 RLS policies, plans seeded.

---

## WRONG

### D-007 — The `rep_id` filter does not filter
**Severity:** WRONG · **Affects:** TITLE_COMPANY

Separate from the leak: when `rep_id` **is** a legitimate rep of the caller's company, the response still includes every other rep's rows. `company.py:502` computes `all_ids = agent_ids + rep_ids`, where `rep_ids` is unconditionally *all* the company's reps (`:485-489`). Only the agent set narrows. Same at `:568` for schedules.

**Reproduction:** as Company A with one rep and one agent, `GET /v1/company/reports?rep_id=<A's own rep>` returns the rep's report regardless of which rep is named. The UI's per-rep drill-down (`apps/web/app/app/company/page.tsx:446`, `reports/page.tsx:150`) therefore shows unfiltered data under a filtered heading.

### D-008 — Company agents page builds a filter link from a field the API never returns
**Severity:** WRONG · **Affects:** TITLE_COMPANY

`apps/web/app/app/company/agents/page.tsx:369` and `:392` link to `/app/company/agents?rep=${agent.rep_id}`, but `GET /v1/company/agents` returns no `rep_id` key. Verified response shape: `{agent_id, agent_name, email, rep_name, status, plan, reports_this_month, last_activity, created_at}` (`apps/api/src/api/routes/company.py:456-466`). `agent.rep_id` is `undefined`, so the link resolves to `?rep=undefined` and the page's filter (`agents/page.tsx:129`, `searchParams.get("rep")`) matches nothing.

Note the API also accepts no server-side rep filter for this endpoint — `list_agents(company: dict = Depends(get_company_admin))` (`company.py:406-407`) takes no `rep_id` parameter, unlike reports/schedules. Filtering is entirely client-side.

### D-004 — Plan catalog disagrees with every document, and local seed drifts from production
**Severity:** WRONG · **Affects:** all (billing correctness — hand to Phase 3)

After a full local migration the `plans` table holds: `affiliate`(5000), `free`(3), `pro`(99999), `sponsored_free`(3), `starter`(25), `team`(99999), **`trial`(3)**. `trial` appears in no documentation and was not among the slugs the audit found (`starter`, `solo`). `solo` is **absent locally** because its seed lives in `0012_seed_plans.sql`, which is unrunnable in a fresh build (D-001) — so a rebuilt database and the evolved production database do not have the same plan rows.

---

## FRAGILE

### D-003 — API source requires Python 3.12+ while `pyproject.toml` declares `^3.11`
**Severity:** FRAGILE · **Affects:** all (runtime/deploy)

`apps/api/src/api/services/email.py:729` contains an f-string whose expression part includes a backslash — legal only from Python 3.12. On 3.11 the app fails at **import**:
```
File "apps/api/src/api/services/email.py", line 729
SyntaxError: f-string expression part cannot include a backslash
```
`apps/api/pyproject.toml:5` declares `python = "^3.11"`, and README/LOCAL_SETUP_GUIDE both say "Python 3.11+". Any 3.11 environment cannot start the API at all. Production must already be on 3.12+; the declared floor is wrong.

### D-002 — `scripts/run_migrations.py` silently skips statements and cannot run 0013+
**Severity:** FRAGILE · **Affects:** all (schema drift)

The README-documented runner splits each file on `;` and **drops any resulting chunk whose first line starts with `--`** (`scripts/run_migrations.py:22`) — a statement preceded by a comment is skipped without a warning. The same split shatters `DO $$ ... END $$` blocks (used throughout `0013_unify_plans_table.sql:15-33` and later migrations) at their internal semicolons. Its only tolerated error is "already exists" (`:30`), so it also dies on D-001. A database migrated with this runner can differ from one migrated with `migrate.sh`, with no error either way.

### D-009 — Redis is a hard dependency of every authenticated request, with no failure handling
**Severity:** FRAGILE · **Affects:** all

`RateLimitMiddleware` constructs its own Redis client at import/app-construction time (`apps/api/src/api/middleware/authn.py:203`) and calls `self.r.get(...)` / `.incr(...)` per request (`:216`, `:240`) with no try/except. If Redis is unreachable, **every authenticated request 500s**, including the entire company portal. `/health` is exempt only because it is on the public-path skip list (`:207`), so a health check would report the service up while every real request fails. (This also means D-009 is invisible to any monitor that polls `/health` — see the audit's finding that `/health` probes neither DB nor Redis.)

---

### D-012 — No audit record for company-scoped reads
**Severity:** FRAGILE · **Affects:** TITLE_COMPANY (and any incident response)

Nothing in `apps/api/src/api/routes/company.py` writes an application-level record of who read what. There is no access-log table, and the `rep_id` filter value is not persisted anywhere. Consequence: the question "was D-005 ever exploited, and against whom?" **cannot be answered from the product's own database** — it has to go to the hosting provider's HTTP request logs, filtered to `/v1/company/reports` and `/v1/company/schedules` carrying a `rep_id` parameter, across the whole window since `db/migrations/0048_title_company_hierarchy.sql` shipped. Any tenant-scoped read path that a caller can parameterise should leave a record.

### D-013 — A database or Redis outage is reported to users as an auth failure
**Severity:** FRAGILE · **Affects:** all authenticated users

`_is_token_blacklisted` fails **closed**: any exception returns `True` (`apps/api/src/api/middleware/authn.py:189-190`), so the request is rejected with `401 {"detail":"Token has been invalidated"}`. Failing closed is the correct security posture; the reporting is wrong.

Observed live during this phase — when local Postgres stopped, every authenticated request returned "Token has been invalidated" while the API log showed the real cause: `Blacklist check failed (denying request): couldn't get a connection after 10.00 sec`. To the user this is indistinguishable from being logged out, and it is invisible to monitoring: `/health` is on the middleware's public-path skip list (`authn.py:207`) and probes neither database nor Redis (`apps/api/src/api/routes/health.py:6-8`), so it stays green throughout. Combined with D-009 (Redis unreachable ⇒ 500 on every authenticated request), an infrastructure blip presents to a customer as "the product logged me out / is broken" with no corresponding signal on our side.

### D-020 — `scripts/migrate.sh` cannot be run twice, so no future migration can be applied with it
**Severity:** BROKEN · **Affects:** all (deployment)

`migrate.sh` re-applies **every** file in `db/migrations/` on each invocation — there is no tracking table (see T2.7). A second run against the same database fails, so adding migration `0054` and running the documented runner would abort before reaching it.

Observed on a database freshly built by that same script (run 1: exit 0, 54/54):

```
run 2 -> psql:db/migrations/0007_...sql:20: ERROR: column "slug" of relation "plans" does not exist
        (0011/0013 rename slug -> plan_slug; 0007's COMMENT and its seed INSERT still name the old column)
after guarding 0007:
run 2 -> psql:db/migrations/0008_create_affiliate_branding.sql:35: ERROR:
        relation "idx_affiliate_branding_account_id" already exists   (CREATE INDEX with no IF NOT EXISTS)
```

I guarded 0007 while investigating, hit 0008 next, and **reverted** rather than land a partial fix — a half-fixed re-run is still a broken re-run, and it would read as solved.

Scope for whoever takes it (upper bound, since many are already inside `DO $$` guards): 1 unguarded `CREATE INDEX`, ~17 `ADD COLUMN` and ~9 `ADD CONSTRAINT` statements. The durable fix is a migration-tracking table so files are applied once, rather than making 54 historical files individually re-runnable.

Not the same defect as D-001 (fresh build), which is fixed: a fresh database now builds cleanly end to end.

### D-021 — "Demo Title Company" sponsors agents while not being typed `TITLE_COMPANY`
**Severity:** WRONG · **Affects:** TITLE_COMPANY, SPONSORED · **Source: Jerry's query against the deployed database, not reproduced locally**

An account named "Demo Title Company" sponsors 3 agents but does not carry `account_type = 'TITLE_COMPANY'`. Consistent with `db/seed_demo_accounts_v2.sql:105-120`, which creates that account as `INDUSTRY_AFFILIATE` — the file predates `db/migrations/0048_title_company_hierarchy.sql`, which introduced the type.

The name implies one role and the type grants another: this account gets the affiliate surface, not the company portal, and `apps/api/src/api/deps/company.py:24-31` would refuse it a company admin's endpoints. Anything reasoning about "which title companies exist" by name rather than by `account_type` will disagree with the code.

Related and worth checking in the same pass: `db/migrations/0050_pct_to_title_company.sql:8-13` promotes accounts to `TITLE_COMPANY` by matching `name ILIKE '%pacific coast%'`, i.e. tenancy structure assigned by string match on a display name.

## ROUGH

### D-010 — `office_location` is accepted by the invite API and silently discarded
**Severity:** ROUGH · **Affects:** TITLE_COMPANY

`InviteRepRequest` accepts `office_location` (`apps/api/src/api/routes/company.py:32-39`) but no handler persists it, and `office` is hardcoded to `""` in every response (`:144`, `:392`). The rep table's "Office" column is therefore permanently blank.

### D-011 — `/v1/company/metrics` is fully wired but unreachable from the product
**Severity:** ROUGH · **Affects:** TITLE_COMPANY

The endpoint exists (`company.py:913`), its Next.js proxy exists (`apps/web/app/api/proxy/v1/company/metrics/route.ts`), and no page or hook calls it (no `useCompanyMetrics` in `apps/web/hooks/use-api.ts`). Either dead code (Phase 5 candidate) or an unfinished feature.

---

## T2.6 — Authenticated smoke test (results)

Every parameter-free `GET` in the OpenAPI spec, as each of the five personas: **66 routes × 5 personas = 330 requests**. Route list taken from `/openapi.json` (157 documented paths, 91 GET operations, 66 without path parameters) rather than hand-assembled.

| Status | Count | Reading |
|---|---|---|
| 403 | 192 | Expected — role gating (e.g. every persona but `company-a` is refused the company portal; non-admins refused `/v1/admin/*`) |
| 200 | 105 | Expected |
| 429 | 15 | **Sweep artifact, not a result** — see the caveat below |
| 500 | 13 | Four unique routes, below |
| 422 | 5 | Endpoints requiring query parameters the sweep did not supply |

**Caveat that limits this ticket's coverage:** the rate limiter allows 60 requests/minute per account (`apps/api/src/api/middleware/authn.py:225`) and the sweep issues 66 per persona, so the tail of each persona's run was rate-limited. 15 results are therefore unknown rather than passing, and **S5 ("no route returns 5xx for any account type") is not fully satisfied by this run** — it is satisfied for the 315 requests that produced a real status. A paced re-run would close the gap; the 5xx set below is confirmed by isolated retries, not by the sweep alone.

The four 5xx routes, each retried individually with pacing to rule out rate-limit contamination:

| Route | Personas | Cause | Entry |
|---|---|---|---|
| `/v1/affiliate/overview` | affiliate, rep-a | missing `signup_tokens` table | D-016 |
| `/v1/company/invite-rep` (POST, tested in T2.4) | company-a | missing `signup_tokens` table | D-016 |
| `/v1/property/stats/affiliate` | affiliate | response model missing `themes` | D-017 |
| `/v1/dev/stripe-prices` | all 5 | `PlanCatalog` not subscriptable | D-018 |
| `/v1/billing/portal` | all 5 | **environment, not code** — returns a structured `{"error":"stripe_config_missing","message":"Missing: STRIPE_SECRET_KEY, ..."}` because no Stripe keys are set locally. Worth noting that a known configuration state is reported as `500`; `503` would be the honest status, and it means a Stripe misconfiguration in production would look like a crash. |

## T2.7 — Migration state (results)

**Which directories contain migrations:** two.

1. `db/migrations/` — 52 numbered files (`0001_base.sql` … `0052_simplify_contact_types.sql`) plus `seed_demo_account.sql`.
2. `apps/api/migrations/` — one file, `phase4_indexes.sql`, containing 7 `CREATE INDEX` statements **and the `CREATE TABLE signup_tokens` at line 38**.

**What each runner applies:** both target only the first directory. `scripts/migrate.sh:9` globs `db/migrations/*.sql`; `scripts/run_migrations.py:47` resolves `<repo>/db/migrations`. **Nothing in the repository applies `apps/api/migrations/phase4_indexes.sql`** — no script, no CI step, no documentation. Its own header comment ("was previously CREATE TABLE in request handler") suggests it was extracted from application code and applied by hand.

**Is it applied in production, and how would anyone know?** Unanswerable from here — see BLOCKED below. The detection method is `SELECT to_regclass('public.signup_tokens')`. There is no migration-tracking table anywhere in this project: no `schema_migrations`, no `alembic_version`, nothing recording which files have run. Both runners are idempotent-by-convention (`IF NOT EXISTS`) and re-run everything every time, so "which migrations has this database had?" has no answer beyond inspecting the schema.

**Does a fresh local bring-up produce the same schema as production?** No — demonstrably. A fresh build following the documented process yields a database **without `signup_tokens`**, on which invite-based onboarding fails entirely (D-016) and `/v1/affiliate/overview` 500s. Production must have the table, or the platform's affiliate features could never have worked. That is drift between the repo's migration process and the deployed schema, of unknown extent: `signup_tokens` is the one instance this sweep proves, and the 7 indexes in the same file are equally unapplied locally (index absence degrades performance silently rather than erroring, so their production status is likewise unknown).

Compounding it, D-001 means the documented process does not even complete without manual intervention, and D-002 means the alternative runner silently skips statements. There is currently no reliable way to construct a database that matches production.

## F5 — Affiliate/sponsor surface audited for the D-005 defect class: **no leak found**

Motivation: the deployed database has 17 sponsored accounts across 4 sponsors and **zero** `COMPANY_REP` accounts, so real sponsorship runs through the affiliate path, not the company portal. That path holds actual data and had never been tested for cross-tenant leakage. D-005 was a `sponsor_account_id` lookup with no ownership check; this surface performs the same class of lookup.

**Method (same as T2.2 — tested by request, not inferred).** Two `INDUSTRY_AFFILIATE` accounts, each with a sponsored agent; affiliate B's agent owns rows carrying distinctive markers. Affiliate A then attempted every endpoint that accepts a caller-supplied identifier, targeting B's agent.

| Request as affiliate A, targeting B's sponsored agent | Result |
|---|---|
| `GET /v1/affiliate/accounts/{B_agent}` | 404 "not found or not owned by you" |
| `GET /v1/affiliate/agents/{B_agent}/reports` | 403 "This agent is not in your book" |
| `GET /v1/affiliate/agents/{B_agent}/schedules` | 403 |
| `GET /v1/affiliate/agents/{B_agent}/usage` | 403 |
| `POST /v1/affiliate/accounts/{B_agent}/deactivate` | 404 |
| `POST /v1/affiliate/accounts/{B_agent}/unsponsor` | 404 |
| `POST /v1/affiliate/accounts/{B_agent}/reactivate` | 404 |
| `POST /v1/affiliate/resend-invite` with B's agent email | 404 "not sponsored by your account" |
| A targeting B's **affiliate account** itself (3 endpoints) | 403 / 404 |
| `GET /all-reports`, `/all-schedules` as A | 200, A's own data only |

Zero B-markers appeared in any A response. **The three state-changing endpoints did not mutate B's agent** — after all attempts, `is_active = true` and `sponsor_account_id` intact.

Positive controls pass: affiliate B reads its own agent through every one of those endpoints (200, with its own data). Role gating holds: a `REGULAR` account is refused with `not_affiliate_account`.

**Why this surface is safe where the company portal was not.** Every identifier-taking handler carries the ownership predicate inline — `WHERE id = %s::uuid AND sponsor_account_id = %s::uuid` (`apps/api/src/api/routes/affiliates.py:676-677, 728-729, 777-778, 848-849`) or an explicit pre-check that 403s (`:1080-1084`, `:1117-1121`, `:1161-1165`). The collection endpoints derive their id set from `sponsor_account_id = <caller>` and accept no caller-supplied id at all (`:879`, `:926`). The company portal's defect was structurally different: it accepted an id, looked up agents *by that id*, and then unioned the result with its own set.

One inconsistency, not a leak: `GET /v1/affiliate/all-reports` returns `200 {"reports":[],"total":0}` for a non-affiliate `REGULAR` account, where every sibling endpoint returns `403 not_affiliate_account`. It is safe (the caller sponsors nobody, so the derived set is empty) but the gating is inconsistent.

## Confirmed correct (negative results worth recording)

Tested by request, not inferred:

- **COMPANY_REP is fully excluded from the company portal.** All 7 endpoints return `403 {"detail":"Title Company admin only"}` for a rep token (`get_company_admin`, `apps/api/src/api/deps/company.py:24-31`, which re-checks `account_type` **against the database**, not the JWT claim).
- **Branding cascade is correctly tenant-scoped.** `PATCH /v1/company/branding` as Company A updated A's company and A's rep (`reps_updated: 1`) and left both of Company B's rows byte-identical (`Company B Brand`/`#123456`).
- **Invite collision handling is safe.** `POST /v1/company/invite-rep` with another company's rep email → `409`, no information disclosed beyond email existence. `POST /v1/company/resend-rep-invite` targeting another company's rep → `404 "Rep not found or not under your company."`
- **The four RLS-dependent non-company routes do not leak** under the same superuser connection: `/v1/reports`, `/v1/contacts`, `/v1/schedules` all returned empty for accounts owning no data, i.e. they carry their own `account_id` predicates rather than relying on RLS.
- **All five personas authenticate and receive correct JWT claims** — `account_type`, `is_company_admin`, `is_sponsored`, `parent_account_id` all resolve as designed (T2.1).
- **All 6 company pages render for TITLE_COMPANY and are correctly gated against COMPANY_REP.** Exercised by request against a local Next.js dev server (`NEXT_PUBLIC_API_BASE=http://127.0.0.1:10000`), authenticating with the `mr_token` cookie:

  | Page | TITLE_COMPANY | COMPANY_REP | Unauthenticated |
  |---|---|---|---|
  | `/app/company` | 200 | 307 → `/app` | 307 → `/login` |
  | `/app/company/reps` | 200 | 307 → `/app` | — |
  | `/app/company/agents` | 200 | — | — |
  | `/app/company/reports` | 200 | — | — |
  | `/app/company/schedules` | 200 | — | — |
  | `/app/company/branding` | 200 | 307 → `/app` | — |

  No error boundaries triggered, no 5xx in the server log. (Page data loads client-side via React Query, so the SSR HTML carries no tenant data — the data-layer behaviour is the API testing above.)

---

## UNVERIFIED

- **Rep removal / orphaned agents** (Rev A T2.2 question). No endpoint to remove a rep exists in `company.py`; the deletion path, if any, lives in the admin tree and was not exercised. `accounts.parent_account_id` (`db/migrations/0048_title_company_hierarchy.sql:5`) declares no `ON DELETE` behaviour, so it defaults to `NO ACTION` — deleting a company row with reps attached would be refused by the FK rather than orphaning them, but this was not tested.

## Design brief — RLS enforcement (future ticket)

### D-014 — RLS cannot be enforced until policies model the account hierarchy
**Severity:** FRAGILE · **Affects:** TITLE_COMPANY, COMPANY_REP, SPONSORED

This is the ticket that was originally scoped as "harden the DB role and add `FORCE ROW LEVEL SECURITY`". **Doing only that would blank the company portal.** Written to stand alone; no prior context needed.

**The problem.** Every RLS policy in `db/migrations/` keys on the row's own account: `account_id = current_setting('app.current_account_id', true)::uuid` (e.g. `0001_base.sql:129-132` for `report_generations`, `0006_schedules.sql:101-103` for `schedules`, `0009_create_contacts.sql:25-27` for `contacts`). No policy references `accounts.parent_account_id` or `accounts.sponsor_account_id`.

The company portal exists to read **other accounts' rows** — its reps' rows and its sponsored agents' rows. So correct RLS context plus today's policies still yields nothing.

**Measured, not predicted.** Against the real policies with a non-superuser role (`rls_probe`), context set to Company A:

| Query under enforced RLS, `app.current_account_id = <Company A>` | Rows visible |
|---|---|
| Company A's own `report_generations` rows | 0 |
| Company A's **own rep's** rows | 0 |
| all `report_generations` | 0 |
| same, plus `app.current_user_role = 'ADMIN'` | 5 (every tenant) |

Today RLS is inert — the app connects as the `postgres` superuser, which owns the tables, and no migration issues `FORCE ROW LEVEL SECURITY` (`relforcerowsecurity = f` on every policied table). Tenant isolation currently rests entirely on hand-written SQL predicates.

**The `ADMIN` bypass is disqualified.** `0025_admin_rls_bypass.sql:11-20` adds `OR current_setting('app.current_user_role', true) = 'ADMIN'` to five tables, and `admin.py` uses it (`admin.py:57`). Wiring company admins to it would make the portal work under enforcement **and grant every company admin an unrestricted cross-tenant read at the database layer** — reinstating D-005 one level down, with only the SQL predicates between tenants. Those predicates are exactly what failed in D-005. Do not take this path.

**Three parts, in this order:**

1. **Policy migration (in-repo).** Extend the policies on the tables the portal reads (`report_generations`, `schedules`, `schedule_runs`, and any future ones) so a company can see its subtree — conceptually `account_id = current_account OR account_id IN (SELECT id FROM accounts WHERE parent_account_id = current_account) OR account_id IN (SELECT sa.id FROM accounts sa WHERE sa.sponsor_account_id IN (SELECT id FROM accounts WHERE parent_account_id = current_account))`. Two open questions for whoever takes this: **performance** (that subquery is evaluated per row on `report_generations`; a denormalised `company_account_id` column may be the better design), and **`forbidden.md:11`** — modifying RLS policies requires understanding the isolation impact, so this needs review, not a quick commit.
2. **Role change (outside the repo).** A non-superuser Postgres role on Render with appropriate `GRANT`s, plus `DATABASE_URL` repointed for the API and worker services. Optionally `ALTER TABLE ... FORCE ROW LEVEL SECURITY` so even the owner is subject to policies.
3. **Ordering is load-bearing.** Part 1 must ship and be verified before part 2. Reversed, the portal returns empty lists and zeros — not errors — the moment the role changes.

**Acceptance for the future ticket:** after both parts, the full T2.2 endpoint sweep returns the same data it returns today for both `TITLE_COMPANY` and `COMPANY_REP`, and the cross-tenant regression test (`apps/api/tests/test_company_tenant_isolation.py`) still passes. Any endpoint returning empty means part 1 is incomplete.

**Prerequisite check:** confirm production's policy set matches `db/migrations/` before designing — `SELECT * FROM pg_policies` against production. A second migrations directory exists (`apps/api/migrations/`, see D-002), so the deployed policy set is not guaranteed to match the repo.

**Status:** C1 (predicate validation) and C2 (RLS context in all handlers) shipped on `fix/security-cross-tenant-leak`. C2 is a no-op until this ticket lands; it is a prerequisite for it, not a substitute.

## BLOCKED-NEEDS-DEPLOYED-ACCESS (Phase 2B)

- **Is production's DB role a superuser?** D-005/D-006's real-world severity depends on it. If production also connects as owner/superuser, D-005 is live exactly as reproduced. If production uses a restricted role, D-005 is contained but D-006 means the portal is showing zeros.
- **Production `PDF_ENGINE`, `PDF_API_URL`, `SITEX_BASE_URL`, `RESEND_API_KEY`, `PDFSHIFT_API_KEY` values** (T2.9/T2.10). `SITEX_BASE_URL` defaults to the **UAT** host (`apps/api/src/api/services/sitex.py:39`) — if unset in production, property reports are being built from test data.
- **Scheduled delivery end-to-end** (T2.3). Needs a real send and a readable inbox.
- **Is `apps/api/migrations/phase4_indexes.sql` applied in production?** (T2.7). Run `SELECT to_regclass('public.signup_tokens')` and check for the 7 indexes it declares. If the table is present the file was applied by hand at some point; if the indexes are missing, production is running without them. Nothing in the repo can answer this, and nothing detects the drift.
