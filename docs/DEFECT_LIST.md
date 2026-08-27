# DEFECT LIST — Phase 2A (local verification sweep)

**Date:** 2026-08-18
**Plan:** `EXECUTION_PLAN_REV_A.md` Phase 2A (local only)
**Tickets covered:** T2.1 (test account provisioning), T2.2 (company / title-company portal), T2.4 (registration → onboarding → first-run), T2.6 (authenticated smoke test), T2.7 (migration state), P1/P2/P3 (configuration trace, `chore/p2b-config-trace`), and the production-evidence reconciliation (`chore/defect-reconciliation`)
**Phase status:** Phase 2A complete (T2.1, T2.2, T2.4, T2.6, T2.7), plus the F5 affiliate-surface audit and the P2B configuration trace. **S2 (autonomous delivery) is PROVEN in production** — see the S2 section. The rest of Phase 2B remains blocked on deployed access.

## Status

**Last reconciled:** 2026-08-27, against `fix/m3-copy-truth`, cut from `main` at `524ce99` (PRs #33–#38 all merged).

Every defect carries its own `**Status:**` line. **That line is the source of truth.** Everything in this section is derived from it by parsing the document — do not edit these counts by hand, and do not record a status here that is not also on the entry. A summary that can drift from the entries is how a defect list stops being trusted, and an untrusted list stops being read.

| State | Count | Meaning |
|---|---|---|
| `recorded` | 0 | Observed, not yet triaged |
| `open` | 29 | Real, unfixed |
| `fixed` | 20 | Corrected in code, with the branch or PR named on the entry |
| `closed-not-live` | 3 | Not occurring in production, with the evidence named on the entry |
| **Total** | **52** | D-001 … D-052, contiguous, no duplicates |

**Open by severity:** BROKEN 3 · WRONG 10 · FRAGILE 10 · ROUGH 6. (Sums to 29, the open total.)

`fixed` — D-001, D-002, D-015, D-016, D-017, D-018, D-020, D-022 (`fix/p4-broken-defects`); D-005, D-007 (PR #24); D-038, D-039 (PR #29); D-040 (PR #30); D-044 (`fix/m5-responsive`); D-041, D-042 (`fix/frontend-ci`); D-049 (`fix/m4-nav-identity`); D-045 (`chore/disable-e2e-workflow`); D-046, D-048 (`fix/m3-copy-truth`).
`closed-not-live` — D-025, D-026, D-029 (worker logs, 8/17).

**A status claim with no pointer is not a status, it is an assertion.** `fixed` must name a branch or PR; `closed-not-live` must name the evidence. Anything that cannot be traced reverts to `open`. This is the standard the 2026-08-17 docs audit applied to `SOURCE_OF_TRUTH.md`, and it applies to entries written during this remediation too — four of the claims corrected in this pass were written today.

**How to re-derive:** parse `^### (D-\d{3}) —` for entries and the following `**Status:**` / `**Severity:**` lines. A count computed any other way — including by adding up what changed on each branch — is a hypothesis. The previous version of this table was produced that way and was wrong by three: it dropped D-035, D-036 and D-037 entirely.

Plus 4 items marked BLOCKED-NEEDS-DEPLOYED-ACCESS and 2 UNVERIFIED. Those are open questions, not defects, and are counted separately.

D-001 through D-024 are grouped by severity below. D-025 through D-034 are grouped in the **P2B — Configuration trace** section, D-035 through D-037 in the **Production evidence reconciliation** section, and D-041 through D-052 in the **Phase M — Marketing / UX** section, because each is only readable alongside the trace that produced it.

**Reading note on the P2B entries:** six were written as conditional on environment values I did not have. Production logs have since settled three of them (two BROKEN, one WRONG — all closed, with evidence). The remaining conditionals are listed at the end of the reconciliation section.

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
**Status:** `fixed` — PR #24

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
**Status:** `open`

`apps/api/src/api/routes/company.py:13` imports `db_conn, fetchall_dicts, fetchone_dict` — **`set_rls` is not imported**, and none of the 10 handlers call it. The contract in `apps/api/src/api/db.py:48-51` states the required pattern (`with db_conn() as (conn, cur): set_rls(cur, account_id); ...`); 14 other route modules follow it (e.g. `apps/api/src/api/routes/reports.py:152-153`).

Handlers querying RLS-protected tables with no RLS context: `get_overview` (`company.py:78`, queries `report_generations` at `:105,:111,:155,:193,:208,:226,:250`), `list_reps` (`:335` → `:347,:353,:358`), `list_agents` (`:410` → `:422,:426`), `get_company_reports` (`:483` → `:508,:512`), `get_company_schedules` (`:549` → `:573,:582`), `get_metrics` (`:917` → `:936,:945,:960,:981`).

**Consequence:** the moment anyone hardens the DB role (non-superuser) or adds `FORCE ROW LEVEL SECURITY` — the standard fix for D-005's class — `current_setting('app.current_account_id', true)` is NULL, every policy predicate evaluates NULL, and these endpoints return **empty lists and zeros rather than errors**. The company dashboard would silently show a working page with no data. Fix D-005 and D-006 together; fixing either alone leaves the portal wrong.

### D-015 — The API test suite does not run, and has not for some time
**Severity:** BROKEN · **Affects:** all — this is the mechanism, not a symptom
**Status:** `fixed` — `fix/p4-broken-defects`

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

The failures are **not** concentrated in one file, as this entry originally stated. Measured after the collection errors were fixed, they are spread across `test_plans_limits.py` (12), `test_affiliate_branding.py` (11) and `test_accept_invite.py` (6) — mocked cursor return shapes that no longer match what the services read. Phase 3 should start with `test_plans_limits.py`, but it is 12 assertions, not 29.

**Verified pre-existing:** both numbers reproduce on `main` with no Phase-2 changes applied (checked out `main`, ran the suite, same 3 errors / 29 failures). The cross-tenant isolation branch adds 9 passing tests and no new failures.

**Why this is severity BROKEN rather than FRAGILE:** a suite in this state cannot have been run recently by anyone. The consequence is not "tests are untidy" — it is that D-005 (a live cross-tenant data leak) shipped, survived, and was found by hand-driven verification rather than by CI. `.github/workflows/backend-tests.yml` exists and runs on PR and push; either it is not running this suite or its result is not gating anything. Both possibilities are worth checking.

**Bearing on Phase 3 — start here.** The 29 failures sit in `test_plans_limits.py`, and Phase 3's entire subject is reconciling displayed plan limits against enforced plan limits. Those failing assertions encode what the limits were once expected to be; the diff between that and current behaviour is likely a substantial part of Phase 3's answer. Not investigated here — flagged so Phase 3 opens with it.

**Also note:** the new `test_company_tenant_isolation.py` needs a live database and skips without one, so it will not fire in a CI job that has no Postgres service. Wiring one in is what turns that regression guard from present into effective.

### D-016 — `signup_tokens` lives in a second migrations directory that nothing applies, so no invited account can be created
**Severity:** BROKEN · **Affects:** TITLE_COMPANY, COMPANY_REP, SPONSORED, INDUSTRY_AFFILIATE (4 of the 5 personas)
**Status:** `fixed` — `fix/p4-broken-defects`

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

**Confirmed by Jerry against the live database: `signup_tokens` exists there.** So the deployed environment is unaffected — D-016 is scoped to databases built from this repository — but the table exists while being created solely by a file no runner has ever applied. That is the third independent indicator that the deployed schema was assembled partly by hand, after 0012's impossible seed rows (D-022) and 0011's abandoned column shape (D-001). The repository and the database have never been in a verified relationship; F7's tracking table is what ends that. See T2.7 below.

### D-017 — `/v1/property/stats/affiliate` returns 500 on the empty state
**Severity:** BROKEN · **Affects:** INDUSTRY_AFFILIATE
**Status:** `fixed` — `fix/p4-broken-defects`

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
**Status:** `fixed` — `fix/p4-broken-defects`

`apps/api/src/api/routes/dev_stripe_prices.py:34` indexes the catalog entries as dicts — `plan["plan_name"]`, `plan["stripe_price_id"]` — but `get_plan_catalog()` returns `PlanCatalog` objects:

```
TypeError: 'PlanCatalog' object is not subscriptable
```

500 for every persona. The route is meant to be dev-only; note it is reachable (not 404'd) whenever `ENVIRONMENT != production`, so it is live on any staging deploy. Relevant to Phase 3: this is the endpoint intended to show which Stripe price IDs the app believes in.

### D-019 — Email verification is not enforced anywhere
**Severity:** WRONG · **Affects:** REGULAR (and any self-registered account)
**Status:** `open`

`POST /v1/auth/register` creates the user with `email_verified = false` (confirmed in the database) and returns `{"ok":true,"email_verified":false}`. Logging in immediately afterwards with the same credentials **succeeds**, and every authenticated surface then works normally — `/v1/onboarding`, `/v1/me`, `/v1/account/plan-usage`, `/v1/reports`, `/v1/schedules`, `/v1/contacts` all returned 200 for the unverified account.

So the verification email is decorative: nothing gates on `users.email_verified`. Whether that is intended is a product decision, but it should be a decision — as written, the flow implies a gate that does not exist, and an address typo produces a working account nobody can reach.

Minor, same endpoint: the docstring for `register` (`apps/api/src/api/routes/auth.py:229-238`) claims it "Returns auth session (JWT + cookie)". It does not — the response carries no token.

### D-001 — A fresh database cannot be built by `scripts/migrate.sh`
**Severity:** BROKEN · **Affects:** all (dev onboarding, CI, disaster recovery)
**Status:** `fixed` — `fix/p4-broken-defects`

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
**Status:** `fixed` — PR #24

Separate from the leak: when `rep_id` **is** a legitimate rep of the caller's company, the response still includes every other rep's rows. `company.py:502` computes `all_ids = agent_ids + rep_ids`, where `rep_ids` is unconditionally *all* the company's reps (`:485-489`). Only the agent set narrows. Same at `:568` for schedules.

**Reproduction:** as Company A with one rep and one agent, `GET /v1/company/reports?rep_id=<A's own rep>` returns the rep's report regardless of which rep is named. The UI's per-rep drill-down (`apps/web/app/app/company/page.tsx:446`, `reports/page.tsx:150`) therefore shows unfiltered data under a filtered heading.

### D-008 — Company agents page builds a filter link from a field the API never returns
**Severity:** WRONG · **Affects:** TITLE_COMPANY
**Status:** `open`

`apps/web/app/app/company/agents/page.tsx:369` and `:392` link to `/app/company/agents?rep=${agent.rep_id}`, but `GET /v1/company/agents` returns no `rep_id` key. Verified response shape: `{agent_id, agent_name, email, rep_name, status, plan, reports_this_month, last_activity, created_at}` (`apps/api/src/api/routes/company.py:456-466`). `agent.rep_id` is `undefined`, so the link resolves to `?rep=undefined` and the page's filter (`agents/page.tsx:129`, `searchParams.get("rep")`) matches nothing.

Note the API also accepts no server-side rep filter for this endpoint — `list_agents(company: dict = Depends(get_company_admin))` (`company.py:406-407`) takes no `rep_id` parameter, unlike reports/schedules. Filtering is entirely client-side.

### D-004 — Plan catalog disagrees with every document, and local seed drifts from production
**Severity:** WRONG · **Affects:** all (billing correctness — hand to Phase 3)
**Status:** `open`

After a full local migration the `plans` table holds: `affiliate`(5000), `free`(3), `pro`(99999), `sponsored_free`(3), `starter`(25), `team`(99999), **`trial`(3)**. `trial` appears in no documentation and was not among the slugs the audit found (`starter`, `solo`). `solo` is **absent locally** because its seed lives in `0012_seed_plans.sql`, which is unrunnable in a fresh build (D-001) — so a rebuilt database and the evolved production database do not have the same plan rows.

---

## FRAGILE

### D-003 — API source requires Python 3.12+ while `pyproject.toml` declares `^3.11`
**Severity:** FRAGILE · **Affects:** all (runtime/deploy)
**Status:** `open`

`apps/api/src/api/services/email.py:729` contains an f-string whose expression part includes a backslash — legal only from Python 3.12. On 3.11 the app fails at **import**:
```
File "apps/api/src/api/services/email.py", line 729
SyntaxError: f-string expression part cannot include a backslash
```
`apps/api/pyproject.toml:5` declares `python = "^3.11"`, and README/LOCAL_SETUP_GUIDE both say "Python 3.11+". Any 3.11 environment cannot start the API at all. Production must already be on 3.12+; the declared floor is wrong.

### D-002 — `scripts/run_migrations.py` silently skips statements and cannot run 0013+
**Severity:** FRAGILE · **Affects:** all (schema drift)
**Status:** `fixed` — `fix/p4-broken-defects`

The README-documented runner splits each file on `;` and **drops any resulting chunk whose first line starts with `--`** (`scripts/run_migrations.py:22`) — a statement preceded by a comment is skipped without a warning. The same split shatters `DO $$ ... END $$` blocks (used throughout `0013_unify_plans_table.sql:15-33` and later migrations) at their internal semicolons. Its only tolerated error is "already exists" (`:30`), so it also dies on D-001. A database migrated with this runner can differ from one migrated with `migrate.sh`, with no error either way.

### D-009 — Redis is a hard dependency of every authenticated request, with no failure handling
**Severity:** FRAGILE · **Affects:** all
**Status:** `open`

`RateLimitMiddleware` constructs its own Redis client at import/app-construction time (`apps/api/src/api/middleware/authn.py:203`) and calls `self.r.get(...)` / `.incr(...)` per request (`:216`, `:240`) with no try/except. If Redis is unreachable, **every authenticated request 500s**, including the entire company portal. `/health` is exempt only because it is on the public-path skip list (`:207`), so a health check would report the service up while every real request fails. (This also means D-009 is invisible to any monitor that polls `/health` — see the audit's finding that `/health` probes neither DB nor Redis.)

---

### D-012 — No audit record for company-scoped reads
**Severity:** FRAGILE · **Affects:** TITLE_COMPANY (and any incident response)
**Status:** `open`

Nothing in `apps/api/src/api/routes/company.py` writes an application-level record of who read what. There is no access-log table, and the `rep_id` filter value is not persisted anywhere. Consequence: the question "was D-005 ever exploited, and against whom?" **cannot be answered from the product's own database** — it has to go to the hosting provider's HTTP request logs, filtered to `/v1/company/reports` and `/v1/company/schedules` carrying a `rep_id` parameter, across the whole window since `db/migrations/0048_title_company_hierarchy.sql` shipped. Any tenant-scoped read path that a caller can parameterise should leave a record.

### D-013 — A database or Redis outage is reported to users as an auth failure
**Severity:** FRAGILE · **Affects:** all authenticated users
**Status:** `open`

`_is_token_blacklisted` fails **closed**: any exception returns `True` (`apps/api/src/api/middleware/authn.py:189-190`), so the request is rejected with `401 {"detail":"Token has been invalidated"}`. Failing closed is the correct security posture; the reporting is wrong.

Observed live during this phase — when local Postgres stopped, every authenticated request returned "Token has been invalidated" while the API log showed the real cause: `Blacklist check failed (denying request): couldn't get a connection after 10.00 sec`. To the user this is indistinguishable from being logged out, and it is invisible to monitoring: `/health` is on the middleware's public-path skip list (`authn.py:207`) and probes neither database nor Redis (`apps/api/src/api/routes/health.py:6-8`), so it stays green throughout. Combined with D-009 (Redis unreachable ⇒ 500 on every authenticated request), an infrastructure blip presents to a customer as "the product logged me out / is broken" with no corresponding signal on our side.

### D-020 — `scripts/migrate.sh` cannot be run twice, so no future migration can be applied with it
**Severity:** BROKEN · **Affects:** all (deployment)
**Status:** `fixed` — `fix/p4-broken-defects`

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

### D-022 — `0012_seed_plans.sql` could never have succeeded on a fresh build
**Severity:** WRONG · **Affects:** all (schema provenance)
**Status:** `fixed` — `fix/p4-broken-defects`

`db/migrations/0007_phase_29a_plans_and_account_types.sql:11-17` creates `plans` with `monthly_report_limit INT NOT NULL` and no default. `0012_seed_plans.sql:5` then inserted `(plan_slug, plan_name, stripe_price_id, description)` — omitting that column. On any database where 0007 created the table, the insert fails:

```
ERROR: null value in column "monthly_report_limit" of relation "plans" violates not-null constraint
DETAIL: Failing row contains (solo, Solo Agent, null, f, 0, price_1SO4sD..., ...)
```

**So the `solo` and `affiliate` rows in the deployed database did not get there via this migration.** Combined with D-016 (`signup_tokens` only ever existed in an unapplied second directory), that is a second independent indication that the production schema was assembled partly by hand rather than by the documented runner.

Fixed on `fix/p4-broken-defects`: 0012 now supplies the column, with the values 0051 assigns to those slugs, and remains inert where the rows already exist.

### D-023 — Tenancy structure is assigned by a display-name string match
**Severity:** FRAGILE · **Affects:** TITLE_COMPANY, INDUSTRY_AFFILIATE
**Status:** `open`

`db/migrations/0050_pct_to_title_company.sql:8-13` promotes accounts to `TITLE_COMPANY` by matching `name ILIKE '%pacific coast%' OR slug ILIKE '%pacific-coast%'`. An account's type — which decides whether it gets the company portal or the affiliate surface, and which `apps/api/src/api/deps/company.py:24-31` enforces on every company endpoint — is therefore a consequence of how someone typed a display name.

Renaming that customer, or onboarding any other company whose name happens to contain those words, changes tenancy behaviour. Related to D-021, which is the same class of mismatch observed from the other direction.

### D-024 — `/v1/affiliate/all-reports` is gated differently from every sibling endpoint
**Severity:** ROUGH · **Affects:** REGULAR
**Status:** `open`

Every other affiliate endpoint refuses a non-affiliate caller with `403 {"error":"not_affiliate_account"}` via `verify_affiliate_account`. `GET /v1/affiliate/all-reports` instead returns `200 {"reports":[],"total":0}` (`apps/api/src/api/routes/affiliates.py:879`), because it derives its account set from `sponsor_account_id = <caller>` and a non-affiliate sponsors nobody.

Not a leak — verified during the F5 audit — but the inconsistency means a caller cannot distinguish "you are not an affiliate" from "you are an affiliate with no agents".

### D-021 — "Demo Title Company" sponsors agents while not being typed `TITLE_COMPANY`
**Severity:** WRONG · **Affects:** TITLE_COMPANY, SPONSORED · **Source: Jerry's query against the deployed database, not reproduced locally**
**Status:** `open`

An account named "Demo Title Company" sponsors 3 agents but does not carry `account_type = 'TITLE_COMPANY'`. Consistent with `db/seed_demo_accounts_v2.sql:105-120`, which creates that account as `INDUSTRY_AFFILIATE` — the file predates `db/migrations/0048_title_company_hierarchy.sql`, which introduced the type.

The name implies one role and the type grants another: this account gets the affiliate surface, not the company portal, and `apps/api/src/api/deps/company.py:24-31` would refuse it a company admin's endpoints. Anything reasoning about "which title companies exist" by name rather than by `account_type` will disagree with the code.

Related and worth checking in the same pass: `db/migrations/0050_pct_to_title_company.sql:8-13` promotes accounts to `TITLE_COMPANY` by matching `name ILIKE '%pacific coast%'`, i.e. tenancy structure assigned by string match on a display name.

## ROUGH

### D-010 — `office_location` is accepted by the invite API and silently discarded
**Severity:** ROUGH · **Affects:** TITLE_COMPANY
**Status:** `open`

`InviteRepRequest` accepts `office_location` (`apps/api/src/api/routes/company.py:32-39`) but no handler persists it, and `office` is hardcoded to `""` in every response (`:144`, `:392`). The rep table's "Office" column is therefore permanently blank.

### D-011 — `/v1/company/metrics` is fully wired but unreachable from the product
**Severity:** ROUGH · **Affects:** TITLE_COMPANY
**Status:** `open`

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

## F4 — Paced smoke re-run (S5 settled)

The T2.6 sweep sent 66 requests per persona against a 60/minute limiter, so its tail was rate-limited and 15 of 330 results were artifacts. Re-run at ~1.1s per request: **330 requests, 0 rate-limited, every result real.**

| Status | T2.6 (unpaced) | F4 (paced, after F3 fixes) |
|---|---|---|
| 403 (expected role gating) | 192 | 192 |
| 200 | 105 | 126 |
| 429 (artifact) | 15 | **0** |
| 500 | 13 | **7** |
| 422 (missing query params) | 5 | 5 |

Unique 5xx routes fell from 4 to 2: `/v1/dev/stripe-prices` (D-018) and `/v1/property/stats/affiliate` (D-017) are fixed and no longer appear.

The two that remain:

- **`/v1/affiliate/overview`** (affiliate, rep-a) — D-016 on a database built before 0053 existed. Applying 0053 to it turned both into **200**. Not a separate defect; it is the same missing-`signup_tokens` failure, and it confirms the fix end to end on a second database.
- **`/v1/billing/portal`** (all five personas) — **environment, not code**: `{"error":"stripe_config_missing","message":"Missing: STRIPE_SECRET_KEY, ..."}`. It is a deliberate, well-formed error handed back with the wrong status; `503` would be honest, and as written a Stripe misconfiguration in production is indistinguishable from a crash.

**S5 verdict:** with the two D-016/D-017/D-018 fixes applied and Stripe unconfigured locally, **no route returns a 5xx for any account type except `/v1/billing/portal`, whose 500 is a configuration state rather than a fault.** That is as close to S5 as this environment can establish; confirming it fully requires a deployment with Stripe keys present (Phase 2B).

## T2.7 — Migration state (results)

**Which directories contain migrations:** two.

1. `db/migrations/` — 52 numbered files (`0001_base.sql` … `0052_simplify_contact_types.sql`) plus `seed_demo_account.sql`.
2. `apps/api/migrations/` — one file, `phase4_indexes.sql`, containing 7 `CREATE INDEX` statements **and the `CREATE TABLE signup_tokens` at line 38**.

**What each runner applies:** both target only the first directory. `scripts/migrate.sh:9` globs `db/migrations/*.sql`; `scripts/run_migrations.py:47` resolves `<repo>/db/migrations`. **Nothing in the repository applies `apps/api/migrations/phase4_indexes.sql`** — no script, no CI step, no documentation. Its own header comment ("was previously CREATE TABLE in request handler") suggests it was extracted from application code and applied by hand.

**Is it applied in production, and how would anyone know?** Unanswerable from here at the time of writing; **answered 2026-08-18 — it is not, and neither is `0042_add_performance_indexes.sql`.** See the **Production evidence reconciliation** section, which also corrects the `--bootstrap` ordering this sweep originally implied. The detection method used was `SELECT to_regclass('public.signup_tokens')` plus a `pg_indexes` probe. There is no migration-tracking table anywhere in this project: no `schema_migrations`, no `alembic_version`, nothing recording which files have run. Both runners are idempotent-by-convention (`IF NOT EXISTS`) and re-run everything every time, so "which migrations has this database had?" has no answer beyond inspecting the schema.

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
- **`https://api.bkiconnect.com` as the SiteX production gateway** (P2). The string appears nowhere in this repository. It is a vendor fact; the code cannot confirm or refute it, and I did not probe a third-party production API to find out. See the P2 section for what the code *does* settle.

## Design brief — RLS enforcement (future ticket)

### D-014 — RLS cannot be enforced until policies model the account hierarchy
**Severity:** FRAGILE · **Affects:** TITLE_COMPANY, COMPANY_REP, SPONSORED
**Status:** `open`

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

**Prerequisite work:** C1 (predicate validation) and C2 (RLS context in all handlers) shipped on `fix/security-cross-tenant-leak`. C2 is a no-op until this ticket lands; it is a prerequisite for it, not a substitute.

## P2B — Configuration trace (P1/P2/P3)

**Branch:** `chore/p2b-config-trace` · **Date:** 2026-08-18 · **Method:** static trace only. No deployed access; no request was made to any production service. Every claim below cites the code that produces it.

**The configuration I was given** (Jerry, API service only): `DATABASE_URL` set, `SENDGRID_API_KEY` set, `PDF_ENGINE=playwright`, `SITEX_BASE_URL=https://api.bkiconnect.com`, `PDFSHIFT_API_KEY` set. **Worker and Vercel env sets were not provided.** What that costs is stated per ticket.

### P1 — Which engine renders a production report

**Short answer: the value you gave me is on the wrong service and cannot affect a single report PDF.**

Report PDFs are rendered in the **worker**, not the API. There are exactly three callers of `render_pdf`, all in worker code: `apps/worker/src/worker/tasks.py:1203` (market reports), `tasks.py:1795` (consumer/CMA reports), `apps/worker/src/worker/property_tasks/property_report.py:474` (property reports). Each reads `PDF_ENGINE` from `apps/worker/src/worker/pdf_engine.py:30`, which is the **worker process's** environment. `PDF_ENGINE` on the API service is read by nothing (`grep` for `PDF_ENGINE` across `apps/api/`: no match). So the production engine is **UNVERIFIED — could not confirm**; it is whatever the worker service has, which I was not given.

**Does `PDF_API_URL` override `PDF_ENGINE`? No.** `PDF_API_URL` and `PDF_API_KEY` are read only by `apps/worker/src/worker/pdf_adapter.py:18-19`, and that module has **zero importers** — `grep -rn "pdf_adapter" --include=*.py` returns one hit, a comment at `apps/api/src/api/routes/branding_tools.py:372`. `pdf_adapter.generate_pdf` (`:22`) and `get_pdf_engine_info` (`:176`) are called from nowhere. The whole `PDF_ENGINE=api` / `PDF_API_URL` / `PDF_API_KEY` selector is unreachable code. Nothing it does can override anything.

The two selectors are also **incompatible**, which is what makes D-025 possible: `pdf_adapter.py:17` expects `PDF_ENGINE` ∈ {`playwright`, `api`}; the live `pdf_engine.py:30,342-359` expects {`playwright`, `pdfshift`} and raises on anything else.

`PDF_ENGINE` is read at **module import** (`pdf_engine.py:30`), so a change to it does not take effect until the worker process restarts.

### D-025 — The worker's own env template tells you to set a value that makes every PDF render fail
**Severity:** BROKEN · **Affects:** every persona that generates any report · **CLOSED 2026-08-18 — NOT LIVE**
**Status:** `closed-not-live` — worker logs, 8/17 — `PDF Engine: pdfshift` (`pdf_engine.py:340`); the deployed worker is not configured from its own template

> **Resolution.** Worker logs show `📄 PDF Engine: pdfshift` three times on 8/17 (`pdf_engine.py:340`). The deployed worker is **not** configured from its own template, so `pdf_engine.py:359` never fires. The trap in `apps/worker/ENV_TEMPLATE.md:33` is real and still in the repo — anyone provisioning a new worker from that file walks into it — but nothing is broken in production today. Closed as not-live; the template line remains a documentation defect and is on the fix list below.

`apps/worker/ENV_TEMPLATE.md:33` instructs the deployer to set `PDF_ENGINE=api` on the worker service. The code that actually renders (`pdf_engine.py:342-359`) accepts only `playwright` or `pdfshift`, and `:359` raises `ValueError: Invalid PDF_ENGINE: api. Must be 'playwright' or 'pdfshift'` for anything else. If the worker was configured from its own template, **every** report PDF — market, consumer, property — fails at the render step with an unhandled `ValueError`.

The same template block (`:34-35`) tells you to set `PDF_API_URL` and `PDF_API_KEY`, which nothing reads (see P1 above). `apps/api/ENV_TEMPLATE.md:34` repeats `PDF_API_KEY` for the API — that one **is** read, and is wrong in a different way (D-028).

**To settle it:** read `PDF_ENGINE` off the worker service. Three outcomes: unset or `playwright` → Playwright renders (see D-026); `pdfshift` → PDFShift renders and output is correct; `api` → nothing has rendered since that value was set, and D-025 is BROKEN in production right now.

### D-026 — Under `PDF_ENGINE=playwright` every market report silently loses its branded header and footer
**Severity:** BROKEN · **Affects:** REGULAR, SPONSORED, INDUSTRY_AFFILIATE, COMPANY_REP — every market report · **CLOSED 2026-08-18 — NOT LIVE**
**Status:** `closed-not-live` — worker logs, 8/17 — `PDF Engine: pdfshift` (`pdf_engine.py:340`); PDFShift is the branch that honours header/footer

> **Resolution.** The worker runs `pdfshift`, which is the branch that *honours* `header_html`/`footer_html` (`pdf_engine.py:203-222`). Branded headers and footers are rendering in production. The silent-discard code path in `render_pdf_playwright` (`:79`) still exists and is still undefended — this defect becomes live the moment anyone sets `PDF_ENGINE=playwright`, which is exactly what `.env.example:87` defaults to and what is currently set on the API service. Closed as not-live; keep the entry, because the failure is silent and the trigger is a one-word env change.

The market report path **always** builds the repeating hero header and agent footer and always passes them: `tasks.py:1186-1187` (`builder.render_page_header_html()` / `render_page_footer_html()`), base64-inlined at `:1200-1201`, passed at `:1207-1208`.

`render_pdf_playwright` **discards them**. `pdf_engine.py:79` is literally `_ = (header_html, footer_html, header_start_at, footer_start_at)`, and the docstring at `:58-66` says so: *"accepted for API parity with PDFShift; currently IGNORED by Playwright — flagged for follow-up ticket."* No warning is logged. No error is raised. A PDF is produced and uploaded, just without the agent's photo, name, phone, email, company name or logo on any page.

The layout is worse than "header missing". The page geometry was tuned around PDFShift's additive margin model — `pdf_engine.py:176-186` reserves `header.height: 1.3in` plus `margin.top: 0.1in`, with the comment *"PDFShift treats margin.top and header.height as ADDITIVE"*. Playwright is called with all four margins at `0` (`:111-116`) and no header slot, so body content renders into space the CSS expects to be reserved.

For a white-label branding product, this is not a cosmetic difference: it is the total, silent loss of the branding on every page of every market report. Graded BROKEN on that basis.

Consumer (`tasks.py:1795`) and property (`property_report.py:474`) reports pass no header/footer, so they are unaffected by this specific defect.

### D-027 — `pdf_adapter.py` is dead code that documents a third, non-existent engine selector
**Severity:** WRONG · **Affects:** anyone reading the config
**Status:** `open`

Zero importers (proof in P1 above). It nonetheless defines `PDF_ENGINE` with a **different value set** than the live selector (`pdf_adapter.py:17` vs `pdf_engine.py:30`), and both `.env.example:91-92` and `apps/worker/ENV_TEMPLATE.md:34-35` advertise its variables as live configuration. `docs/architecture/SOURCE_OF_TRUTH.md:129,188` describes it as a "Playwright → PDFShift fallback", which is a mechanism that exists in neither module.

This is a Phase 5 deletion candidate under the prove-death standard in `docs/DEAD_CODE.md` — it passes all three tests (no importers, no route reference, no runtime string construction). It was not on the Phase 5 candidate list and was not removed on that branch. `apps/worker/src/worker/social_engine.py` has the same status (zero importers; `render_social_image` called from nowhere) and should be assessed in the same ticket.

### D-028 — The branding sample-PDF and sample-JPG endpoints read a different key name than the one that is set
**Severity:** BROKEN · **Affects:** every persona using the branding preview · **Conditional on `PDF_API_KEY` on the API service**
**Status:** `open`

`apps/api/src/api/routes/branding_tools.py:119` reads `os.getenv("PDF_API_KEY", "")`. You told me the API service has **`PDFSHIFT_API_KEY`** set. Those are different variables; nothing maps one to the other. Every other PDFShift call site in the codebase uses `PDFSHIFT_API_KEY` (`pdf_engine.py:31`, `social_engine.py:28`) — `branding_tools.py` is the lone outlier.

If `PDF_API_KEY` is unset, both endpoints fail closed with a 503 before doing any work: `:335-339` (`POST /v1/branding/sample-pdf`) and `:428-432` (`POST /v1/branding/sample-jpg`), both returning *"PDF generation service not configured. Please contact support."* Both are mounted (`apps/api/src/api/main.py:29,112`) and both are reachable from the UI through `apps/web/app/api/proxy/v1/branding/sample-pdf` and `.../sample-jpg`.

**To settle it:** check whether `PDF_API_KEY` is also set on the API service. If it is, this is latent, not live — but two names for one secret is still the defect.

### D-029 — `PRINT_BASE` on the worker is persisted as the user-visible "view in browser" link, and defaults to localhost
**Severity:** WRONG · **Affects:** every persona · **CLOSED 2026-08-18 — NOT LIVE**
**Status:** `closed-not-live` — worker logs, 8/17 — `print_base: https://reportscompany-web.vercel.app` (`pdf_engine.py:340`); `PRINT_BASE` is set

> **Resolution.** Worker logs show `print_base: https://reportscompany-web.vercel.app` (`pdf_engine.py:340`). `PRINT_BASE` is set, so no report row has been stamped with a localhost link. The mechanism described below is confirmed correct and is *not* closed as wrong — it is closed as not-currently-failing.
>
> **Two residuals worth a decision, neither a defect:** (1) the link handed to customers carries the `reportscompany-web.vercel.app` hostname rather than the branded `www.trendyreports.io`, and those links are **persisted**, so changing `PRINT_BASE` later will not retroactively fix rows already written. (2) The `/print/[runId]` route is now confirmed as a live customer-facing destination, which means the Vercel side of it (`NEXT_PUBLIC_API_BASE`, `INTERNAL_RENDER_TOKEN` — `page.tsx:36-39,49-55`) has to be right or those links render "Report Not Found". That is still unverified.

`render_pdf` returns `(pdf_path, print_url)` where `print_url` is `f"{effective_base}/print/{run_id}"` (`pdf_engine.py:82-83`). The market path captures that second value as `html_url` (`tasks.py:1203`) and **writes it to the database** (`:1253-1255`, `UPDATE ... SET status='completed', html_url=%s ...`) and into the completion webhook payload (`:1376`).

That column is user-facing. `apps/api/src/api/routes/reports.py:98,246,292` returns it, and the web app renders it as a link: `apps/web/app/app/reports/page.tsx:107-110` and `apps/web/app/app/reports/[id]/page.tsx:292-294`.

`PRINT_BASE` defaults to `http://localhost:3000` (`pdf_engine.py:33`, and `tasks.py:249` for `DEV_BASE`, which is passed as `print_base=` at `:1211`). If it is unset on the worker, every report row is stamped with a `http://localhost:3000/print/<id>` link that is then shown to the customer. Nothing validates it and nothing fails.

This also **upgrades the `/print/[runId]` finding in `docs/DEAD_CODE.md`**: that document records the route as reachable-but-unexercised because all three `render_pdf` callers pass `html_content=`. That is still true of *rendering*, but the URL is not merely constructed and dropped — it is persisted and published to users as a link. `/print/[runId]` is a live user-facing destination, not a latent fallback. Correction recorded here rather than edited into the Phase 5 branch, which is open as PR #27.

### P2 — Is `https://api.bkiconnect.com` the production SiteX host?

**UNVERIFIED — could not confirm.** The string `bkiconnect` appears **zero times** in this repository (`grep -rn "bkiconnect"` across all tracked files: no match). Nothing in the code, the docs, the env templates, or git history names a production SiteX host. This is a vendor fact that only ICE/SiteX or your onboarding paperwork can settle; I will not assert it from the code, and I did not probe a third-party production API to find out.

What I **can** confirm, and it is the part that matters mechanically:

1. **The host is used only as a prefix, so swapping it is safe in itself.** `SiteXConfig.base_url` (`apps/api/src/api/services/sitex.py:39`) is concatenated with two host-relative paths and nothing else: `/ls/apigwy/oauth2/v1/token` (`:46`) and `/realestatedata/search` (`:50`). No path, header, or payload is conditioned on the host value. If the production gateway exposes the same two paths, the swap works; if it does not, you get a 404 from the token call, surfaced as `SiteXAuthError` (`:181-183`).
2. **You set it on the right service.** SiteX is called only from the API (`apps/api/src/api/services/sitex.py`, used by `routes/property.py`, `routes/lead_pages.py`, `routes/admin.py`). The worker never calls SiteX — every `sitex` hit in worker code reads the already-persisted `sitex_data` column (`property_tasks/property_report.py:228,262,292`, `property_builder.py:362-399`). No `SITEX_*` variable is needed on the worker.
3. **Misconfiguration fails loudly, not silently.** `SiteXClient.initialize` calls `config.validate()` (`:249`) and raises `SiteXError("Invalid SiteX configuration")` if any of base URL / client id / client secret / feed id is blank. Unlike the PDF and email paths, this one does not pretend to succeed.
4. **The client is a process-lifetime singleton** (`get_sitex_client`, `:601-605`), so the value is read once per API process — a change needs a restart, not just a redeploy of config.

### D-030 — The UAT host is the default, so any unset environment silently queries test data
**Severity:** FRAGILE · **Affects:** REGULAR, SPONSORED (property reports)
**Status:** `open`

`sitex.py:39` defaults `SITEX_BASE_URL` to `https://api.uat.bkitest.com`. There is no environment check, no startup log of which host is in use beyond one `logger.info` at `:255`, and no marker on the resulting data. An unset variable does not fail — it returns plausible-looking test property data that is then persisted into `property_reports.sitex_data` and rendered into a customer's PDF. A production default should not point at a vendor's test gateway.

**Two things you still need to check, which the base URL alone does not cover:**

- `SITEX_CLIENT_ID`, `SITEX_CLIENT_SECRET` and `SITEX_FEED_ID` were not in the config you sent. `SITEX_FEED_ID` defaults to `100001` (`sitex.py:42`), which the module docstring gives as the example feed. A production host with UAT credentials or a UAT feed id fails at the token call (`:181-183`) — or worse, succeeds against the wrong feed.
- **Any property report generated while `SITEX_BASE_URL` was unset has UAT data frozen into `property_reports.sitex_data`.** Changing the variable does not correct rows already written. Worth a `SELECT count(*) FROM property_reports WHERE sitex_data IS NOT NULL AND created_at < '<the date you set the variable>'`.

### P3 — `RESEND_API_KEY`: the code path, and what happens when it is absent

**Confirmed. There are two call sites and they behave differently. One is a warning; the other writes a false record into the database.**

Both read `os.environ.get("RESEND_API_KEY", "")` in the **worker**: `tasks.py:668` and `tasks.py:1894`. `apps/api/src/api/settings.py:36` declares `RESEND_API_KEY: str = ""` with the comment `# Deprecated — kept for backwards compat, unused` — that comment is true **of the API** and false of the product: the worker is where email for these two flows is actually sent, and both flows use Resend, not SendGrid. An operator reading `settings.py` would reasonably delete the variable.

Note that the two providers are split by flow, not by environment: scheduled/ad-hoc **report delivery** goes through SendGrid (`_send_and_log_report_email`, `tasks.py:598-649`, `provider='sendgrid'` at `:641`), and only failure notifications and consumer-report delivery use Resend. `SENDGRID_API_KEY` being set does not cover the Resend paths.

### D-031 — A consumer report is recorded as delivered when no email was sent
**Severity:** BROKEN · **Affects:** REGULAR, SPONSORED (lead capture / consumer CMA delivery) · **Conditional on `RESEND_API_KEY` on the worker**
**Status:** `open`

`process_consumer_report` (`tasks.py:1441`), email delivery branch, `:1894-1901`:

```python
resend_key = os.environ.get("RESEND_API_KEY", "")
if not resend_key:
    logger.warning("RESEND_API_KEY not set — marking as sent without email")
    cur.execute("""
        UPDATE consumer_reports
        SET status = 'sent', consumer_email_sent_at = NOW()
        WHERE id = %s::uuid
    """, (report_id,))
    delivered = True
```

The consequence, plainly: **the consumer never receives their report, and the system records that they did.** `status='sent'` and a non-null `consumer_email_sent_at` timestamp are written for an email that was never attempted. No row is written to `email_log` — this path does not log at all, unlike the SendGrid path (`:637-644`) — so there is no record anywhere that contradicts the `sent` status.

It then gets worse. `delivered = True` falls through to `:2027-2052`, which SMSes the **agent** that they have a new lead, with the consumer's phone and email. The agent is told a lead converted and was served a report. They follow up on a report the lead never saw.

This is not recoverable after the fact by fixing the key: you cannot tell, from the database, which `sent` rows were real. The only distinguishing evidence is the `logger.warning` in the worker logs.

### D-032 — An unrecognised delivery method is also recorded as sent
**Severity:** WRONG · **Affects:** REGULAR, SPONSORED
**Status:** `open`

`tasks.py:2020-2025`, the `else` arm of the same dispatch:

```python
logger.warning(f"No valid delivery method for report {report_id}: method={delivery_method}")
cur.execute("UPDATE consumer_reports SET status = 'sent' WHERE id = %s::uuid", (report_id,))
delivered = True
```

Same failure shape as D-031, different trigger: a report with no usable delivery method — no phone for SMS, no address for email, or an unrecognised `delivery_method` value — is marked `sent` and fires the agent's "new lead" SMS. `status='failed'` exists and is used on the adjacent path (`:2054-2060`); this branch chooses not to use it.

### D-033 — Failure notifications are the one alert that tells an agent their scheduled report broke, and they are skipped silently
**Severity:** FRAGILE · **Affects:** every persona with a schedule · **Conditional on `RESEND_API_KEY` on the worker**
**Status:** `open`

`_send_failure_notification` (`tasks.py:654`), at `:668-671`:

```python
resend_key = os.environ.get("RESEND_API_KEY", "")
if not resend_key:
    logger.warning("RESEND_API_KEY not set — skipping failure notification")
    return
```

Returning early here is the correct shape — unlike D-031, it does not lie. The severity is in what is lost: this is the only mechanism that tells an account owner a scheduled report failed. Without it, a schedule can fail silently every week and the customer's first signal is a recipient asking where the report went. Combined with the "Deprecated … unused" comment at `settings.py:36`, an operator has an explicit invitation to remove the variable that keeps this alive.

### D-034 — Five environment variables name the same web app, with three different defaults, and two of them ship broken links when unset
**Severity:** FRAGILE · **Affects:** every persona
**Status:** `open`

| Variable | Read at | Default | What breaks if unset |
|---|---|---|---|
| `PRINT_BASE` | `pdf_engine.py:33`, `social_engine.py:29`, `tasks.py:249` | `http://localhost:3000` | Report "view in browser" links (D-029) — **confirmed set in production**, so this row is settled |
| `WEB_BASE` | `apps/worker/src/worker/email/send.py:13` | `http://localhost:3000` | **Unsubscribe links in every outbound email** (`send.py:138`) |
| `WEB_BASE` | `apps/api/src/api/routes/billing.py:21` | `https://reportscompany-web.vercel.app` | Stripe checkout return URLs (`:206-207,303`) land on the wrong domain |
| `APP_BASE` | `apps/api/src/api/settings.py:23` | `https://www.trendyreports.io` | Invite links (`invite_service.py:160`, `admin.py:2488`) |
| `APP_BASE` | `tasks.py:713` | `https://reportscompany-web.vercel.app` | Failure-notification links |
| `FRONTEND_URL` | `tasks.py:1497` | `https://www.trendyreports.io` | Consumer report links |

The same name (`WEB_BASE`, `APP_BASE`) resolves to a different default in two different services, so setting it correctly on one does not imply the other. The `send.py:13` case is the one to fix first: if `WEB_BASE` is unset on the worker, every marketing email you send carries an unsubscribe link pointing at `http://localhost:3000`, which is a deliverability and compliance problem, not a cosmetic one.

### What I still need, and what it would settle

| Needed | Settles |
|---|---|
| ~~Worker: `PDF_ENGINE`~~ | **ANSWERED** — `pdfshift`. Closed D-025 and D-026. |
| ~~Worker: `PRINT_BASE`~~ | **ANSWERED** — `https://reportscompany-web.vercel.app`. Closed D-029. |
| ~~Worker: `PDFSHIFT_API_KEY`~~ | **ANSWERED by inference** — the engine is `pdfshift` and PDFs are being produced; `pdf_engine.py:159-160` would raise on every render if the key were absent. Confirm cheaply by grepping the same worker logs for `✅ PDF generated` alongside the three `PDF Engine: pdfshift` lines. |
| Worker: `WEB_BASE`, `APP_BASE`, `FRONTEND_URL` | D-034. `WEB_BASE` is the urgent one — unset means every outbound email carries a `localhost:3000` unsubscribe link (`email/send.py:13,138`). |
| Worker: `RESEND_API_KEY` | D-031, D-033 — whether the false-`sent` path is live |
| API service: `PDF_API_KEY` | D-028 |
| API service: `SITEX_CLIENT_ID`, `SITEX_CLIENT_SECRET`, `SITEX_FEED_ID` | Whether the production host has production credentials (P2) |
| Vercel: `NEXT_PUBLIC_API_BASE`, `INTERNAL_RENDER_TOKEN` | Whether `/print/[runId]` — now confirmed a link we hand to customers (D-029) — actually renders. `page.tsx:36-39` returns null without the first; `:49-55` warns and 401s without the second. |
| Vendor confirmation that `api.bkiconnect.com` is the SiteX production gateway | P2 |

---

## Production evidence reconciliation

**Branch:** `chore/defect-reconciliation` · **Date:** 2026-08-18 · **Evidence source:** Jerry, from Cursor with deployed access. My part is reconciliation only — I checked each reported fact against the code and recorded what it settles, what it changes, and where it points somewhere different than first read.

### S2 — Autonomous delivery: **PROVEN in production**

769 `schedule_runs`, 585 completed, with the ticker → database → worker → `email_log` chain verified end to end. Scheduled reports generate and deliver themselves in production without a human.

This is the first of the seven "Definition of Stable" items proven against production rather than a local harness, and it retires the largest open question in Rev A. It also matches the code path exactly: `apps/worker/src/worker/schedules_tick.py:300-301` dispatches with `celery.send_task("generate_report", ...)` **directly to Celery**, so scheduled delivery never touches the Redis bridge and is not exposed to D-036 or D-037 below.

**The 184 non-completed runs, resolved 2026-08-18** (queried by Cursor — do not re-run):

| status | count | reading |
|---|---|---|
| `completed` | 585 | delivered |
| `skipped_limit` | 95 | the plan cap firing on real users — **not a failure**, see D-035 |
| `queued` | 57 | in flight or abandoned ticks |
| `failed` | 32 | actual failures |
| **total** | **769** | |

**The real failure rate is 32/769 = 4.2%, not the 24% this section originally implied.** That earlier figure was `769 − 585` treated as if every non-completed row were a failure, which is exactly the inference this document keeps warning against — a number derived by subtraction rather than read from the source. Corrected here rather than left standing.

The 95 `skipped_limit` rows are the more interesting half. They are not delivery breaking; they are **D-035's cap firing on paying customers** — `starter` accounts hitting a 15-report ceiling while being sold 25. Autonomous delivery is working; the plan configuration is what is turning reports away.

32 genuine failures across 769 runs is worth a Phase 3 look at *why*, but it is a tail, not a systemic problem, and S2 stands as proven.

### Migration state in production — the bootstrap warning is confirmed, and it reaches further than 0053

Two facts reported: `schema_migrations` does not exist, nothing auto-applies migrations on startup, and of 0053's seven indexes only `idx_accounts_sponsor` and `idx_api_keys_hash` exist.

**Those two are not evidence that 0053 partly applied. They are evidence that it never ran at all** — and that 0042 never ran either. Each index in 0053 is declared by other migrations too, and the pattern is decisive:

| Index | Declared in | In production |
|---|---|---|
| `idx_api_keys_hash` | `0001_base.sql:113`, `0042:37`, `0053:41` | **present** |
| `idx_accounts_sponsor` | `0042:16`, `0048_title_company_hierarchy.sql:17`, `0053:20` | **present** |
| `idx_jwt_blacklist_hash` | `0042:27`, `0053:33` — **and nowhere else** | **absent** |
| `idx_report_gen_account_status_generated` | `0053:16` only | absent |
| `idx_cgm_member_lookup` | `0053:25` only | absent |
| `idx_schedules_account` | `0053:29` only | absent |
| `idx_schedule_runs_schedule_date` | `0053:37` only | absent |

Both surviving indexes are also declared by a migration **other than** 0042 or 0053 — `0001` and `0048`, which evidently did apply. The one index declared *only* by 0042 and 0053 is missing. So neither 0042 nor 0053 has ever been applied to production, and the two that exist arrived by another route entirely.

**That means a numbered migration in the main `db/migrations/` directory was skipped, with applied migrations on both sides of it.** Every previous drift indicator (D-001, D-016, D-022) pointed at the *second* directory or at hand-assembly. This one is different in kind: the sequence in the primary directory is not contiguous in production. `0048` ran, `0042` did not.

**Confirming query** — all four are declared only by 0042, so if they are absent, 0042 is confirmed unapplied:

```sql
SELECT indexname FROM pg_indexes WHERE schemaname='public' AND indexname IN
  ('idx_cgm_member','idx_property_reports_account_created',
   'idx_report_generations_account_generated','idx_schedule_runs_schedule_created');
```

**What production is missing, in order of what it costs:** `idx_jwt_blacklist_hash` is consulted on **every authenticated request** (`middleware/authn.py`); `idx_schedule_runs_schedule_date` backs usage counting over a table with 769 rows and growing; `idx_report_gen_account_status_generated` backs the affiliate overview and report list. The two that exist are the two that matter least. Missing indexes degrade silently rather than erroring, which is why nothing surfaced this.

#### The corrected deployment order

`--bootstrap` records every unrecorded file as applied **without executing it**. Run against production as it stands, it would permanently assert that 0042 and 0053 had been applied. Those five indexes would then never be created by any future run, and the tracking table — the thing built specifically to end this class of uncertainty — would be lying from its first row. The warning raised when F7 shipped is now confirmed with evidence, and it inverts the order:

1. **Audit first, bootstrap last.** Run the confirming query above. The index probe catches 0042 and 0053 because indexes are easy to probe; other migrations may be unapplied in ways nothing detects. The bootstrap is only as trustworthy as this audit, and that limit should be stated when it runs.
2. **Apply the genuinely-unapplied files by hand.** Both candidates are pure `IF NOT EXISTS`, so both are safe to run against live data. **Apply 0053 only, not both** — see the duplication note below.
3. **Then `--bootstrap`,** which now records something true.
4. **Then normal runs** apply only genuinely new migrations.

#### Two defects in 0053 itself, found while reconciling this

Both are mine, from Phase 4, and neither was caught because 0053 was written against a local database where none of the objects existed:

- **0042 and 0053 declare the same indexes under different names.** `idx_schedule_runs_schedule_date (schedule_id, created_at)` is definitionally identical to 0042's `idx_schedule_runs_schedule_created (schedule_id, created_at)`; `idx_cgm_member_lookup (member_type, member_id, account_id)` supersedes 0042's `idx_cgm_member (member_type, member_id)`; `idx_report_gen_account_status_generated` overlaps `idx_report_generations_account_generated`. Applying both files creates three redundant index pairs that cost write throughput and disk for nothing. Apply one.
- **0053's `idx_api_keys_hash` can never be created.** `0001:113` already creates that name without a predicate; `0053:41` declares it `WHERE is_active = TRUE`. `CREATE INDEX IF NOT EXISTS` matches on **name, not definition**, so 0053's partial version is silently skipped wherever 0001 has run — which is everywhere. Production's index is 0001's unpartial one, and 0053 claims a partial index it will never produce. Harmless in effect, dishonest in the file.

### D-035 — `starter` is enforced at 15 while marketing sells 25, and the cap is firing on real users
**Severity:** WRONG · **Affects:** REGULAR (every paying agent on `starter`) · **Extends D-004**
**Status:** `open`

Reported production `plans`: `free`=3, `starter`("Growth")=15, `pro`("Growth Plus")=99999, `solo`("Solo Agent")=25, `trial`=3, `team`, `affiliate`=5000, `sponsored_free`=3. Marketing sells Growth at 25/month.

**The 15 is not what gates market report creation.** `POST /v1/reports` calls `get_full_plan_usage` (`routes/reports.py:156`), which reads `plan["market_reports_limit"]` (`services/usage.py:248,255`) — the **per-product** column added by `0051_per_product_limits.sql:5`. The reported 15 is `plans.monthly_report_limit`, the **legacy** column, read only by `evaluate_report_limit` (`usage.py:324`), which `usage.py:319` itself labels backward-compatibility and which the market-report gate no longer calls.

**ANSWERED 2026-08-18 — queried against production by Cursor. Do not re-run this.**

```
plan_slug | plan_name | market_reports_limit | monthly_report_limit
starter   | Growth    | 15                   | 15
```

`market_reports_limit = 15`. **Not NULL, and not the floor-of-3 case** — 0051 did reach production and set the column, so the third branch below is ruled out. The gate at `routes/reports.py:156` → `usage.py:248` reads 15 and enforces 15.

So the answer is the middle row: **enforced at 15, sold at 25.** Marketing oversells by 10 reports a month, and the defect is WRONG rather than BROKEN — customers get fewer reports than advertised, not the catastrophic 3.

**It is not theoretical: the cap is firing.** `schedule_runs` carries **95 rows with status `skipped_limit`** — real users hitting a ceiling set 10 below what they were sold. That figure also resolves the S2 question above; see that section.

The three outcomes were enumerated before the query, and are kept because the reasoning that produced the floor-of-3 branch is what made the query worth running — `_first_not_none` genuinely does fall through to 3 rather than to `monthly_report_limit`, and that remains true for any plan whose `market_reports_limit` is NULL:

| If `starter.market_reports_limit` is… | Enforced limit | How |
|---|---|---|
| `25` (0051 applied — `:14` and `:56-60` both set it) | **25** | Would match marketing. **Ruled out — the column is 15.** |
| **`15`** | **15** | ← **This is production.** Matches the legacy column and the internal docs. Marketing oversells by 10. |
| `NULL` (0051 never applied) | **3** | `_first_not_none(mkt_override, limit_override, mkt_plan_limit, default=3)` (`usage.py:131`) does **not** fall back to `monthly_report_limit` — it falls through to the hard floor of **3**. **Ruled out — the column is populated.** Still live for any plan whose column is NULL. |

**The fix is a value, not code.** Decide whether Growth is a 15-report plan or a 25-report plan, then set `market_reports_limit` and `monthly_report_limit` to match the marketing copy — or change the copy. Both columns, because the legacy one still feeds `evaluate_report_limit`.

**ANSWERED (G1a): Growth is 25, and the DATA changes, not the copy.**

**Fix written, not yet applied — `db/migrations/0054_growth_plan_report_limit.sql` on `fix/m3-copy-truth`.** It sets both columns to 25 for `plan_slug='starter'`, leaves `plan_name` alone (production has renamed it "Growth"; overwriting that from a stale repository value inside a limits migration would be a silent regression), and is idempotent.

**Status stays `open` deliberately.** This defect is a value in the production database, and writing a migration does not change one. It closes when Jerry applies 0054 and the verification query in its header returns `25 | 25`. Marking it `fixed` on the strength of an unapplied migration would be exactly the kind of unbacked status claim the header of this document forbids.

Verified locally against a database seeded from `db/migrations/`: reproduced production's `15 | 15`, applied 0054, got `25 | 25`, re-applied and got `25 | 25` again. **95 `skipped_limit` rows say real users are hitting the 15 today**, so this is the one item in this batch with a live customer cost attached to the delay.

**Independent of the limit question, the naming is wrong three ways at once.** For `plan_slug='starter'`: the database says `plan_name='Growth'`; the API overrides it and returns **"Starter"** (`_PLAN_DISPLAY_NAMES` at `usage.py:32` wins over the DB value at `usage.py:139`); and every piece of user-facing copy says **"Growth"** (`apps/web/components/stripe-billing-actions.tsx:98`, `components/marketing/faq.tsx:35`, `.cursor/rules/skills/references/architecture.md:70-71`). A customer on Growth sees "Growth" on the marketing site and "Starter" in their own account page. The same collision exists for `pro`/`team` → "Pro" vs "Growth Plus".

**`solo` is the trap.** It carries 25 — the number marketing sells — has no UI presence, and `_PLAN_DISPLAY_NAMES` maps it to "Starter" as well (`usage.py:33`). Anyone reconciling "which row holds the 25 we advertise?" will find `solo` and be tempted to point `starter` customers at it. `solo` is a legacy slug seeded by `0012_seed_plans.sql:11`; the live plan is `starter`. Fix the column, not the slug.

**Also worth knowing:** `usage.py:327` treats any limit `>= 10000` as unlimited. `pro` at 99999 is therefore unlimited by sentinel, and `affiliate` at 5000 is genuinely capped. Raising affiliate to 10000 would silently make it unlimited.

### D-036 — A bridge outage strands manual market reports at `pending` with no error, no retry and no alert
**Severity:** FRAGILE · **Affects:** REGULAR, SPONSORED, INDUSTRY_AFFILIATE, COMPANY_REP (manual reports); admin (retry)
**Status:** `open`

The consumer bridge is a separate Render service running `run_redis_consumer_forever` (`apps/worker/src/worker/tasks.py:2087-2158`): `blpop` off a Redis list, then `generate_report.delay(...)`.

**What routes through it, verified:** `POST /v1/reports` (`routes/reports.py:215` → `worker_client.py:12-20`, `r.rpush`) and admin retry (`routes/admin.py:422`). **What bypasses it, verified:** scheduled reports (`schedules_tick.py:300-301`, `celery.send_task`), property reports (`worker_client.py:23-29`, `send_task`), and consumer CMA reports (`routes/lead_pages.py:387`, `send_task`). Jerry's characterisation is exactly right.

**What an outage costs.** `enqueue_generate_report` is `r.rpush` onto a Redis **list**. That succeeds whether or not the bridge is alive. So during a bridge outage:

- `POST /v1/reports` returns success and writes `status='pending'`. The user's report sits at "pending" indefinitely.
- Nothing errors. The failure handler at `reports.py:214-225` only fires if the **rpush itself** fails — i.e. if Redis is unreachable. A dead bridge is invisible to it.
- No timeout, no retry, no alert. Celery's `autoretry_for` (`tasks.py:815-822`) never engages, because the task was never published.
- **The jobs are not lost.** `blpop` is destructive but the list persists; when the bridge returns it drains the backlog and every stranded report generates at once. An outage is a delay, not data loss — provided Redis retained the list and the bridge actually restarts.

So the cost of the two transient package-download 502s today was: nothing, if no manual report was submitted in the window; a delayed report, if one was. Deploy failures leave the *old* process running, so the bridge was never actually down — which is the one piece of good news in it running stale code.

**The staleness is low-risk but not zero, and one question decides it.** The bridge has run commit `6d1e100d` since 2026-05-21 and has not picked up any Phase 4 or Phase 5 merge. That is fine *if* its start command is the consumer loop only, because the loop's entire contract is four dict keys (`run_id`, `account_id`, `report_type`, `params` — `tasks.py:2124`) and the actual report generation happens in the **worker** service on current code. **But if that service's start command also runs `celery -A worker.app.celery worker`, then three-month-old task code is executing today's jobs**, and every fix merged since May is absent from whatever it picks up. Confirm the start command before trusting the deploy failures as harmless.

### D-037 — The bridge pops a job off the queue and then drops it permanently on any unexpected error
**Severity:** WRONG · **Affects:** REGULAR, SPONSORED, INDUSTRY_AFFILIATE, COMPANY_REP (manual reports)
**Status:** `open`

`tasks.py:2116` pops with `blpop` — destructive — then parses and dispatches. The catch-all at `:2154-2157` logs and continues:

```python
except Exception as e:
    consecutive_errors += 1
    print(f"❌ Unexpected error in consumer (#{consecutive_errors}): {e}")
    time.sleep(min(5, backoff))
```

The item is already gone from the list. It is not re-queued, not written anywhere, not retried. Any exception between the pop and the `.delay()` — a malformed payload, a missing key, a broker publish failure — **destroys that job permanently**. The `report_generations` row stays `pending` forever and the only trace is one line of stdout.

This is the same user-visible symptom as D-036 (a report stuck at pending) with the opposite recovery property: an outage self-heals when the bridge returns, this does not. Distinguishing them in production means reading bridge logs; there is no state anywhere that separates "queued and waiting" from "silently destroyed".

### Still open after this reconciliation

| Item | Needs |
|---|---|
| D-028 | Is `PDF_API_KEY` set on the API service? (`PDFSHIFT_API_KEY` is, and `branding_tools.py:119` reads the other name.) |
| D-030 | `SITEX_CLIENT_ID` / `SITEX_CLIENT_SECRET` / `SITEX_FEED_ID` on the API; plus vendor confirmation of `api.bkiconnect.com` |
| D-031, D-032, D-033 | `RESEND_API_KEY` on the **worker** — the false-`sent` path. Still the highest-value unknown left: it writes incorrect data rather than failing. |
| D-034 | `WEB_BASE`, `APP_BASE`, `FRONTEND_URL` on the worker. `WEB_BASE` first — unset means a `localhost:3000` unsubscribe link in every outbound email. |
| ~~D-035~~ | **ANSWERED** — `market_reports_limit = 15`. Enforced 15, sold 25. Floor-of-3 ruled out. |
| D-036 | The bridge service's start command |
| ~~S2~~ | **ANSWERED** — 585 completed / 95 `skipped_limit` / 57 queued / 32 failed. Real failure rate 4.2%. |
| Migration audit | The four-index confirming query, before any `--bootstrap` |
## Why none of this was caught: two independent mechanisms

**Branch:** `fix/ci-restoration` · **Date:** 2026-08-18

D-015 recorded that the API test suite does not run. That is one mechanism. There is a second, upstream of it, and together they explain how a class of defect accumulated invisibly for months.

| | Mechanism | Effect |
|---|---|---|
| **1** | **The suite was broken** (D-015). Three modules imported a package path that does not exist; 29 more tests carried stale expectations. | Even a green pipeline would have told you nothing. |
| **2** | **CI never reached the suite** (D-038, below). `.github/workflows/backend-tests.yml:16` ran `pip install -r requirements.txt` against a file that does not exist in this repository and never has. | The job failed at the install step, before a single test was collected. |

These are independent. Fixing either alone leaves the other in place. D-015 was fixed in Phase 4; mechanism 2 survived it untouched, which is why nothing changed.

**And they are not the whole chain — a third condition pinned it shut.** Even with a working `requirements.txt`, the workflow pinned Python 3.11, on which the API suite *cannot collect* (D-003/D-039). Verified on one tree, in one sitting:

```
Python 3.11:  Interrupted: 3 errors during collection   (SyntaxError, services/email.py:729)
Python 3.12:  34 failed, 22 passed, 9 skipped, 5 errors  (collects and runs)
```

So the missing requirements file and the Python pin had to be fixed **together**; either alone still leaves CI red without running anything. That is why they landed in one branch.

### D-038 — `requirements.txt` does not exist, so backend CI has never run a test
**Severity:** BROKEN · **Affects:** all — this is a mechanism, not a symptom
**Status:** `fixed` — PR #29

`.github/workflows/backend-tests.yml:16` ran `pip install -r requirements.txt`. No such file exists at the repository root or anywhere else; `git log -- requirements.txt` returns nothing, so it was never committed and later removed — it was never there. Every run of the Backend Tests workflow failed at that step.

`apps/api` and `apps/worker` are Poetry projects, each with a `pyproject.toml` and a `poetry.lock` (lock-version 2.1). The Render services build with `pip install poetry && poetry install --no-root`. The `requirements.txt` reference was a fiction the workflow inherited; nothing in the repository ever produced or consumed that file.

**First run that could execute, on merged `main` at `3751a5c`: 34 failed, 34 passed, 9 skipped, 5 errors.** That is the real number, not a projection — it matches the post-Phase-4 baseline, confirming the 34 failures are pre-existing and were simply never visible. Clearing them is D-015's tail and belongs to Phase 3.

**Fixed on this branch** by switching the workflow to Poetry, installing both projects into one shared virtualenv, and running `pytest` once from the repository root. One environment is required rather than convenient: `pytest.ini` declares a single session spanning both packages, and `apps/worker/tests/test_unsubscribe_token_roundtrip.py` imports from both — the worker signs the unsubscribe token and the API verifies it, so testing that contract needs both dependency sets present together.

`pytest` and `pytest-asyncio` were added to the worker's dev dependencies, which previously declared only `ruff` despite CI running `pytest apps/worker/tests`.

### D-039 — `pyproject.toml` declares `^3.11` while the source requires 3.12+
**Severity:** WRONG · **Affects:** all — CI, local setup, and anyone trusting the declaration · **Supersedes the diagnosis in D-003**
**Status:** `fixed` — PR #29

All three `pyproject.toml` files (`apps/api`, `apps/worker`, `libs/shared`) declared `python = "^3.11"`. The API source does not compile on 3.11: `apps/api/src/api/services/email.py` interpolates strings containing `\u` escapes inside f-string **expression** parts, which PEP 701 permits only from 3.12. `py_compile` on 3.11 gives `SyntaxError: f-string expression part cannot include a backslash` at `services/email.py:729`.

This is not confined to one module. `apps/api/src/api/main.py:14` imports `routes/auth.py`, which imports `services/email.py` at `:11` — so **the API application cannot start at all on Python 3.11.** `routes/admin.py:18`, `routes/reports.py:8`, `routes/company.py:15` and `routes/affiliates.py:27` import it too.

**What the deployed runtime must be, and how we know.** The API service is live and serving in production. Since importing the app compiles `services/email.py`, and that file is a syntax error on 3.11, the deployed Python is necessarily **3.12 or newer**. That is an inference from the service being up, not a reading of Render's configuration — no deploy configuration exists in this repository (no `render.yaml`, no Dockerfile, no `runtime.txt`, no `.python-version`), so the version is set in the Render dashboard and cannot be confirmed from here. **Worth confirming directly, because the alternative would be far worse:** if Render were somehow on 3.11, the API could not be running, so the inference is strong — but it is still an inference. That it *has* to be an inference is its own defect: see D-040.

**Fixed on this branch** by raising the constraint to `^3.12` in all three `pyproject.toml` files, regenerating both lock files, and pinning CI to 3.12 — i.e. by matching the declaration to what the code actually requires and what production demonstrably runs, rather than by rewriting the f-strings to suit a version nothing uses.

The alternative fix — replacing the `’` / `—` escapes in `services/email.py` with the literal characters, which removes the backslashes and restores 3.11 compatibility — is available and small, and would be the right call if anything actually needed to run on 3.11. Nothing does.

### D-040 — The deployed Python version is not pinned anywhere in the repository
**Severity:** FRAGILE · **Affects:** all — every service, every deploy
**Status:** `fixed` — PR #30

D-039's conclusion that production runs Python 3.12+ is **inferred from the API service being up**, not read from any configuration. It cannot be read from configuration, because none exists. Checked, all absent:

```
render.yaml   ABSENT      runtime.txt      ABSENT      Procfile   ABSENT
render.yml    ABSENT      .python-version  ABSENT      app.json   ABSENT
Dockerfile    ABSENT      .tool-versions   ABSENT
```

Every deploy setting — Python version, build command, start command, environment variables — lives only in the Render dashboard. Nothing in version control records what any service actually runs, and nothing detects drift between services.

**Why that is more than untidy.** The Python version is now load-bearing in a way it was not before: the API source is a syntax error below 3.12 (D-039). If Render's default image moves, or a service is recreated from scratch, or someone sets a version on one service and not another, **the API stops booting** — and the repository contains nothing that would have warned them, nothing to diff against, and nothing to restore from. The three sibling services (`reportscompany-consumer-bridge`, `markets-report-ticker`, worker) import the same packages and are equally exposed; whether they are on the same interpreter is unknown.

This is the same shape as the env-var drift class: configuration that exists only in a dashboard, described nowhere, verified by nothing. It is why the deploy timestamps, the `PDF_ENGINE` value, and the worker's `RESEND_API_KEY` all had to be asked for rather than looked up.

**Two fixes, both small, neither done here** (this branch fixes CI, not deployment):

1. **Pin the version in the repo** — a `.python-version` file, or `runtime.txt`, or an explicit `PYTHON_VERSION` in Render, committed alongside a note of which services it applies to. `pyproject.toml`'s `^3.12` now declares the requirement, but Render does not read it.
2. **Adopt `render.yaml` (Render Blueprints)** so build commands, start commands, and non-secret configuration are version-controlled and reviewable. Larger change, and the honest one.

**Confirm the current value first.** Read the Python version off each of the four services in the Render dashboard before pinning anything, so the pin matches what is running rather than freezing a guess.

### What this does NOT do

**CI will now run, and it will be red.** Making the pipeline execute does not make it pass. On 3.12 the suite reports **34 failed, 22 passed, 9 skipped, 5 errors** — matching the post-Phase-4 baseline recorded above, which is the point: these are pre-existing, previously invisible failures, not regressions introduced here. Clearing them is D-015's remaining tail (`test_plans_limits.py`, `test_affiliate_branding.py`, `test_accept_invite.py`) and belongs to Phase 3.

The choice of whether to land a running-but-red pipeline or to scope CI to a passing subset first is Jerry's; this branch implements the honest version, on the grounds that a red pipeline that reports real failures is strictly better than a green-or-erroring one that reports nothing.

**Note on severity counts:** the table at the top of this document is not updated here. `chore/p2b-config-trace` and `chore/defect-reconciliation` both rewrite it and are unmerged; editing it on a third branch would guarantee a conflict. Reconcile the counts once those land.

---

## Phase M — Marketing / UX (`fix/m5-responsive`)

### The frontend CI has the same two-mechanism shape as the backend CI did

D-038 and D-039 were landed together because either one alone still left backend CI red without running anything. The **Frontend Tests** workflow has the identical structure, and it was found the same way: not by reading the workflow, but by trying to run the suite locally during M5 and watching it fail.

Two independent mechanisms, each sufficient on its own to hide every frontend test:

| # | Mechanism | Where it stops |
|---|---|---|
| D-041 | `pnpm` is never installed on the runner | Before dependency install — the job never reaches jest |
| D-042 | `ts-node` is not a dependency, so `jest.config.ts` cannot be parsed | At jest startup — no test file is ever collected |

Fixing either alone leaves the suite still not running. **They must land together or neither helps** — the same framing recorded for D-038/D-039, arrived at independently on the frontend.

### D-041 — The Frontend Tests workflow never installs `pnpm`, so it has failed every run
**Severity:** BROKEN · **Affects:** all — this is a mechanism, not a symptom
**Status:** `fixed` — `fix/frontend-ci`

`.github/workflows/frontend-tests.yml` uses `actions/setup-node@v4` and then runs `pnpm install`. `setup-node` does not provide `pnpm`, and the workflow has no `pnpm/action-setup` step and never enables corepack. The job dies at the install step.

**This is read from CI, not inferred.** Run `33099064110` (`main`, 2026-08-27, job `98611593553`):

```
Run pnpm install
/home/runner/work/_temp/….sh: line 1: pnpm: command not found
##[error]Process completed with exit code 127.
```

Exit 127 is "command not found" — the job fails before any dependency is installed and long before jest starts.

**Scale.** The workflow reports **481 runs**. Every run I sampled failed: the 30 most recent (2026-06-08 → 2026-08-27) and the 30 oldest the API will return (2026-03-04 → 2026-03-13). I did not enumerate all 481, so the precise claim is *every sampled run across the full available date range failed*, not "all 481" — but the failing step is environmental, not code-dependent, so nothing in between could have passed while both ends failed.

The six suites under `apps/web/__tests__/` — including `app-layout.test.tsx`, which exists specifically to pin the route-matching matrix that `isBuilderRoute()` depends on — have therefore never been enforced by CI.

**Fixed on `fix/frontend-ci`** by adding `pnpm/action-setup@v4` before `actions/setup-node@v4`.

**Deliberately no `version:` on the action.** `action-setup` then reads `packageManager` from the root `package.json` (`pnpm@9.12.3`) — the same field Vercel reads to choose the pnpm version for a build. Pinning a version in the workflow would have created a second declaration that could drift from the one production uses; this way, bumping `packageManager` moves CI and Vercel together.

Two supporting changes in the same file, both for the same reason — CI should build the way the frontend actually builds:

- **`node-version-file: .nvmrc` instead of `node-version: "20"`.** `.nvmrc` pins `20.18.1` and is what local development and Vercel both read. The literal `"20"` floated to whatever 20.x the runner shipped, so CI and production could differ by a patch release with nothing recording it.
- **Ordering:** `pnpm/action-setup` must run *before* `setup-node`, because `cache: pnpm` shells out to pnpm to locate the store and fails if pnpm is not yet on PATH.

### D-042 — `ts-node` is missing, so jest cannot parse its own config
**Severity:** BROKEN · **Affects:** all — this is a mechanism, not a symptom
**Status:** `fixed` — `fix/frontend-ci`

`apps/web/jest.config.ts` is a TypeScript config file. Jest requires `ts-node` to read one. `apps/web/package.json` declares `jest`, `jest-environment-jsdom`, `ts-jest`, `@types/jest` and `@testing-library/jest-dom` — but **not `ts-node`**. Observed directly, running the project's own `test` script locally with dependencies installed:

```
Error: Jest: Failed to parse the TypeScript config file .../apps/web/jest.config.ts
  Error: Jest: 'ts-node' is required for the TypeScript configuration files. Make sure it is installed
```

`ts-jest` is not a substitute — it transforms test files, it does not load the config. This failure is downstream of D-041: CI has never reached it, so it has never been reported by CI. It surfaces the moment D-041 is fixed, which is why fixing D-041 alone would produce a workflow that still runs zero tests.

**Fixed on `fix/frontend-ci`** by adding `ts-node@^10.9.2` to `apps/web` devDependencies and regenerating `pnpm-lock.yaml`.

The alternative — renaming the config to `jest.config.js` so no TypeScript loader is needed — removes a dependency rather than adding one and was the more attractive option in the abstract. It was **not** taken: `jest.config.ts` is what the repository already has, `next/jest` and the `Config` type import are written for it, and inventing a third convention for how this project configures jest is the failure mode being corrected here, not a fix for it.

The lockfile diff is `ts-node` plus its small dependency tree (`arg`, `create-require`, `diff`, `v8-compile-cache-lib`, `yn`, `@cspotcode/source-map-support`, `@tsconfig/*`), and re-keying of jest's peer-resolution entries — jest declares `ts-node` as an *optional peer dependency*, so its resolution key gains a `(ts-node@10.9.2…)` suffix. **No existing package version changed**; verified by reading every removed line of the diff.

Resolution is via pnpm's store (`node_modules/.pnpm/ts-node@10.9.2_…`), confirmed with `require.resolve`. During M5 this was satisfied by a symlink to a global copy, which proved the diagnosis but is not a fix — nothing in the repository would have reproduced it.

**What the suite actually reports once it can run.** Measured on this branch by satisfying `ts-node` locally (a symlink to a global copy — nothing committed, `package.json` untouched):

```
Test Suites: 4 failed, 3 passed, 7 total
Tests:      13 failed, 38 passed, 51 total
```

Failing suites: `AccountSwitcher`, `NewSchedulePage`, `PlanPage`, `TemplatesMapping`. `NewSchedulePage` fails inside `useQueryClient` — a missing `QueryClientProvider` in the test harness, i.e. a test-setup defect rather than a product one. These are pre-existing and previously invisible, exactly as the backend's 34 failures were.

**The pipeline now runs, and it is red.** Running the exact command CI runs, on `fix/frontend-ci`, after `pnpm install --frozen-lockfile`:

```
$ pnpm --filter web test
Test Suites: 4 failed, 3 passed, 7 total
Tests:      13 failed, 41 passed, 54 total
Exit status 1
```

(41 rather than 38 because D-044's three regression tests are now on `main`.) Landing it red is deliberate and is Jerry's call, recorded: scoping CI to a passing subset would recreate the exact condition that hid these since March. Clearing the 13 is separate work; the `NewSchedulePage` harness defect is the cheapest of them.

**Run jest from `apps/web`, not the repo root.** From the root there is no jest config, so `rootDir` becomes the repository and jest collects `e2e/*.spec.ts` — Playwright specs, which fail immediately with `Cannot use import statement outside a module`. This is not a defect: `pnpm --filter web test` runs in `apps/web`, which is correct. It is recorded only because the root-level run produces an alarming "11 suites failed, 0 tests" that looks like a catastrophe and is purely an artifact of the wrong working directory.

### D-045 — `e2e.yml` carries the identical `pnpm` defect and has also never run
**Severity:** BROKEN · **Affects:** every E2E run since the workflow was written
**Status:** `fixed` — `chore/disable-e2e-workflow`

`.github/workflows/e2e.yml` had the same shape as `frontend-tests.yml` did — `actions/setup-node@v4`, then `pnpm install`, with nothing that installs pnpm. It reported **783 runs, and every one sampled failed**, including the two triggered by merging PRs #33 and #34.

**Disabled rather than repaired, on Jerry's decision.** The `push: branches: [main]` trigger is removed and only `workflow_dispatch` remains, so nothing fires on its own. The reasoning is the one this document keeps arriving at from different directions: *a permanently red check that nobody can act on is precisely what let D-041 hide for six months.* Making this workflow fail more eloquently — reaching Playwright and then failing to reach an unknown host — would have restored the noise without restoring the signal.

**The pnpm defect is fixed in the same commit anyway**, using the setup now verified green in `frontend-tests.yml`. Not to make it run, but so that whoever re-enables it is not made to rediscover D-041 from scratch: re-enabling is now uncommenting two lines rather than a fresh debugging session. Leaving a known-broken install step inside a file being edited for this exact class of defect would have been the half-applied shape recorded in D-048.

**What must be confirmed before re-enabling** is written into the file itself rather than left here, because the file is what someone will read:

1. A deployed environment exists that these tests can run against, reachable from a GitHub-hosted runner.
2. All five secrets are populated — `E2E_BASE_URL`, `E2E_REGULAR_EMAIL/PASSWORD`, `E2E_AFFILIATE_EMAIL/PASSWORD`.

Point 2 has a trap worth naming: **an unset GitHub secret expands to an empty string rather than erroring**, so a missing `E2E_BASE_URL` does not announce itself — the run fails somewhere inside Playwright, looking like a test problem. The header says so explicitly, and says to delete the file rather than re-enable it if the environment does not exist.

Whether that environment exists is not a defect and has moved to BLOCKED-NEEDS-DEPLOYED-ACCESS.

It never gated anything: `e2e.yml` triggered only on `push` to `main` and `workflow_dispatch`, so unlike `frontend-tests.yml` it never blocked a pull request.

### D-043 — The onboarding checklist card is clipped by up to 85px and the clipped content is unreachable
**Severity:** ROUGH · **Affects:** REGULAR (agent) accounts on `/app`
**Status:** `open`

Found while measuring M5, and **not** the M5 defect — it never reaches document level, so it produces no horizontal page scroll and did not appear in the `scrollWidth > clientWidth` sweep. It was caught only by the separate reachability check.

The "Welcome! Let's get you set up" card sits in the one-third column of a `grid grid-cols-1 lg:grid-cols-3`. Its `CardHeader` row has an intrinsic width of **312px**, while the column is narrower, and the Card itself is `overflow-x: hidden` — so the excess is **clipped and cannot be scrolled to**. Measured on `/app` as `regular@test-tenant.example.com`:

| Viewport | Column width | Header intrinsic | Clipped |
|---|---|---|---|
| 1024 | 227px | 312px | **85px** |
| 1142 | 266px | 312px | **46px** |
| 1280 | 310px | 312px | **2px** |
| 1600 | — | 312px | none |

**Confirmed pre-existing.** The identical three failures were measured with the M5 fix stashed, so this is not a regression introduced by `min-w-0`. It is width-dependent but not shell-related: the fix for D-044 does not touch it, because the clipping happens inside a grid cell that was already the correct size.

**Not fixed here** — it is a content-layout change to the onboarding checklist, outside a branch scoped to the app shell.

### D-044 — `SidebarInset` has no `min-w-0`, so the whole app shell cannot shrink below its content width
**Severity:** WRONG · **Affects:** COMPANY_REP and TITLE_COMPANY at any viewport below ~1280px
**Status:** `fixed` — `fix/m5-responsive`

This is Chrome finding #17, reproduced and root-caused.

`SidebarInset` (`apps/web/components/ui/sidebar.tsx:309`) renders the `<main>` that holds the entire authenticated UI, as a flex child of the shell's row container, with `flex w-full flex-1 flex-col`. A flex item's default `min-width: auto` refuses to shrink it below its content's intrinsic width, and `flex-1` does not override that. The element therefore stayed pinned at its content width at every viewport:

```
COMPANY_REP /app @1142 : document 1268/1142  inset width 1012  → CLIPPED
COMPANY_REP /app @1024 : document 1268/1024  inset width 1012  → CLIPPED
```

The inset is **1012px wide at both viewports** — it is not responding to the viewport at all. 256px sidebar + 1012px inset = the 1268px the document scrolls to. The topbar's account menu sits at the right edge of that inset, which is why it lands off-screen, matching the original report.

It also defeats every `overflow-x-auto` wrapper nested inside: on `/app/company/reps` the reps table's own scroll container could not absorb the table, because the table's intrinsic width propagated straight through the inset instead.

**Measured, not read.** Local stack (Postgres + Redis + API on :10000 + Next on :3000, 54 migrations, 9 seeded accounts). Routes were discovered from each account's own rendered sidebar rather than hardcoded, then loaded at each width and probed twice with a settle gap, keeping the worse sample.

| | Before | After |
|---|---|---|
| REGULAR (11 routes × 3 widths) | 33/33 clean | 33/33 clean |
| TITLE_COMPANY (8 × 3) | 22/24 clean — `/app/company/reps` clipped at 1024 and 1142 | 24/24 clean |
| COMPANY_REP (12 × 3) | 32/36 clean — `/app` and `/app/affiliate` clipped at 1024 and 1142 | 36/36 clean |
| **Total** | **87/93** | **93/93** |

**Fixed** by adding `min-w-0` to `SidebarInset`. Four of the sidebar's other flex children (`SidebarGroup`, `SidebarMenu`, `SidebarMenuSub`, `SidebarMenuSubButton`) already carry it; the inset was the one that was missed.

**Two checks a `scrollWidth` sweep cannot make** were run separately, because `min-w-0` can convert "overflows the viewport" into "clipped and unreachable":

1. The topbar account menu is inside the viewport **and opens on click** at all three widths for all three account types — 18/18.
2. Nothing wider than its parent lacks a scrollable ancestor. 15/18 pass; the 3 failures are D-043 and were verified byte-identical with the fix stashed.

Also verified with the sidebar **collapsed** as well as expanded (12/12 clean), since the fix changes how the inset shares space with the sidebar.

**Single probe was not enough.** An earlier single-sample run reported COMPANY_REP `/app` @1142 as clean — the exact width the finding names — because content width moves as async data lands. The two-sample worst-case probe catches it consistently. A measurement claiming *absence* has to err toward sensitivity.

**REGULAR had to be un-blocked before it could be measured at all.** A freshly seeded agent account is redirected off `/app` to the `/app/get-started` wizard, which is a builder route and renders no sidebar — so the first sweep measured the wizard for REGULAR and reported it clean, satisfying "three account types" on paper only. The redirect is gated on `sessionStorage` (`dashboard-onboarding.tsx:31-36`), so the harness seeds `guided_onboarding_skipped`, putting the browser in the state a real user reaches by clicking "Skip for now" without mutating the database. The sweep now refuses to run for any account whose sidebar discovery returns fewer than two routes, so this cannot silently recur.

**Regression test:** `apps/web/__tests__/SidebarInset.test.tsx`, 3 cases. jsdom does no layout — `scrollWidth` is always 0 there — so it cannot reproduce the defect; it asserts the rendered className instead, including under the exact class list `app-layout.tsx` passes and under a conflicting `w-*` class, so tailwind-merge is exercised rather than the source text being grepped. **Verified load-bearing:** all 3 fail with the fix stashed and pass with it applied. The suite is otherwise unchanged — 13 failed / 38 passed before, 13 failed / 41 passed after, same four failing suites (see D-042). When written, this test could not protect anything, because CI never ran it; `fix/frontend-ci` (D-041, D-042) closed that gap immediately afterwards.

### D-046 — "Priority Generation" is sold on the $29 tier and does not exist
**Severity:** WRONG · **Affects:** every Growth Plus subscriber
**Status:** `fixed` — `fix/m3-copy-truth`

`apps/web/components/marketing/pricing.tsx:50` lists **Priority Generation** as a Growth Plus ($29/mo) feature, repeated in-app at `apps/web/app/app/settings/billing/page.tsx:99`. **No implementation exists anywhere in the repository.** A Growth Plus account's report is enqueued and processed identically to a Free account's.

Verified directly, not inferred:

| Where priority would have to live | What is actually there |
|---|---|
| Market-report queue | `r.rpush(QUEUE_KEY, …)` (`apps/api/src/api/worker_client.py:15`) / `r.blpop(QUEUE_KEY, …)` (`apps/worker/src/worker/tasks.py:2116`) — a Redis list. Right-push/left-pop is strict FIFO: no score, no ZSET, no plan lookup on either side. `account_id` is in the payload and is never used for ordering. |
| Celery routing | `task_routes` contains exactly one entry, `{"ping": {"queue": "celery"}}` (`apps/worker/src/worker/app.py:41-43`). No `task_queue_max_priority`, no `task_default_priority`. |
| Enqueue calls | Every `send_task` / `.delay()` site passes no `priority` and no queue but the default. |
| Database | `grep -rniE "priority" db/migrations/*.sql` returns **nothing**. The `plans` table has no priority column. |
| Schedule dispatch | Ordered `BY COALESCE(next_run_at, '1970-01-01') ASC` (`schedules_tick.py:336-347`). Plan is consulted only to *skip* over-limit accounts, never to reorder. |

**This is why M3-T5 was not executed as written.** That ticket says to "derive real definitions from the code rather than inventing marketing language — these are implemented features," and to add explanatory tooltips. For this bullet there is nothing to derive: writing a tooltip would be inventing exactly the marketing language the ticket forbids, and would state the false claim more confidently than the bare bullet does.

The correct fix is to delete the bullet, but that changes what a paid tier offers and is a product decision, not a copy fix — and the tier structure was G1-gated. Escalated rather than actioned at the time.

**ANSWERED (G1c): delete it from every tier.** Removed from `components/marketing/pricing.tsx` (Growth Plus) and `app/app/settings/billing/page.tsx` (the in-app plan card), with the evidence above recorded at both sites so it cannot be restored as copy without someone first building the feature. A repo-wide grep for "Priority Generation" now returns only those two comments.

Nothing was built to back the claim, and nothing should be: this closes as a copy correction. If prioritised generation is ever wanted as a product, it starts from an empty queue design — there is no partial implementation to finish.

### D-047 — "AI Market Insights" is sold as a paid differentiator but is not plan-gated
**Severity:** WRONG · **Affects:** pricing accuracy on every tier, in both directions
**Status:** `open`

`pricing.tsx:34,49` lists **AI Market Insights** on Growth and Growth Plus but not Free. The feature is real — `generate_insight()` at `apps/worker/src/worker/ai_insights.py:82-179` calls `gpt-4o-mini` and returns a 4–5 sentence market paragraph that is rendered into scheduled-report emails (`email/template.py:1475-1516`, `:1930-1940`). But **there is no plan check on it anywhere.**

The proof is structural rather than a grep result: `generate_insight()`'s signature (`ai_insights.py:82-92`) takes `report_type`, `area`, `metrics`, `lookback_days`, `filter_description`, `sender_type`, `total_found`, `total_shown`, `audience_name` — **no `account_id`, no plan, no account object**. Neither does `schedule_email_html()` (`template.py:1804-1822`). The function cannot consult a plan because it is never told which account it is generating for.

The only gate is process-wide:

```python
AI_INSIGHTS_ENABLED = os.getenv("AI_INSIGHTS_ENABLED", "false").lower() == "true"   # ai_insights.py:21
if not AI_INSIGHTS_ENABLED:                                                          # ai_insights.py:110
    return None
```

So the claim is wrong whichever way the worker is configured: with it **on**, Free accounts get the paid feature; with it **off**, Growth Plus subscribers pay for something nobody receives. There is no configuration in which the pricing page is accurate.

**Which it is in production is unknown** — the worker's environment variables have still not been provided (see BLOCKED-NEEDS-DEPLOYED-ACCESS). Worth knowing, because the two failure modes have opposite commercial consequences.

**A fifth instance of env-var drift, and the first that is a value conflict rather than a name mismatch:** `.env.example:97` ships `AI_INSIGHTS_ENABLED=false`, while `apps/worker/ENV_TEMPLATE.md:131` documents `AI_INSIGHTS_ENABLED=true`. The four instances in `docs/ENV_VAR_AUDIT.md` were all names that did not match a runtime read; this is two documents disagreeing about the value of a flag that decides whether a paid feature functions.

**Related, and also ungated:** two further OpenAI features have no plan check *and* no enable flag — they run whenever `OPENAI_API_KEY` is set. The PDF market narrative (`ai_market_narrative.py`, invoked `tasks.py:1165-1177`) and the property-report executive summary (`ai_overview.py:71-118`, invoked `property_builder.py:1127-1141`). Neither is mentioned on the pricing page at all.

**Also confirmed, and clean:** **CMA Lead Page** is implemented (`routes/lead_pages.py`, `services/agent_code.py`, `app/cma/[code]/`), is available to every tier, and the pricing page correctly lists it on all three. One vestigial flag exists — `plans.lead_capture_enabled` (`db/migrations/0034_property_reports.sql:186`) — which the CMA funnel never reads, and which the one endpoint that does read it explicitly ignores: `routes/leads.py:329-330` logs "not enabled … but accepting lead anyway" and proceeds.

### D-048 — `/about` contradicts `/login` on user count and still carries the uptime claim removed in June
**Severity:** WRONG · **Affects:** anyone who reaches `/about` by URL
**Status:** `fixed` — `fix/m3-copy-truth`

Found by sweeping for the M3-T4 claims rather than editing only the page the ticket named. `apps/web/app/about/page.tsx:50-68` renders four figures, and `:45-46` the matching prose:

| `/about` | `/login` |
|---|---|
| "1,200+ Active Users", and "we help over 1,200 real estate professionals" | "Trusted by 2,000+ agents" |
| "50K+ **Reports Generated**" | "50K+ **Emails sent monthly**" (removed in M3-T4) |
| "99.9% Uptime" | "Reliable / Uptime" — and 99.9% was deleted here in June |
| "3hrs Saved Weekly/User" | — |

Two distinct problems. **The site contradicts itself on how many customers it has**, 1,200+ against 2,000+, with no way for a reader to tell which is true. And the same "50K+" is attached to two different metrics on two pages.

**The uptime figure is a half-applied fix.** Commit `725802a` (2026-06-09) changed the login tile from `99.9% / Uptime SLA` to `Reliable / Uptime` and deleted `/status` for "fabricated uptime numbers and incident history, no real monitoring" — but left `/about` untouched. That commit's own message also asserts it "Kept real stats (2,000+ agents, 50K+ emails)" while citing no source for either.

`/about` is unlinked from all navigation and absent from `app/sitemap.ts`, but the route exists and is publicly reachable by URL.

**Was not edited at the time, deliberately** — three of the four figures are social proof, which was gated on G2, and removing only the uptime cell would have left the 1,200-versus-2,000 contradiction standing.

**ANSWERED (G2): delete every unsourced number sitewide, in one pass.** Done on `fix/m3-copy-truth`:

| Where | Removed |
|---|---|
| `/about` | the entire four-figure stats card — `1,200+ Active Users`, `50K+ Reports Generated`, `3hrs Saved Weekly/User`, `99.9% Uptime` — plus the prose "we help over 1,200 real estate professionals" and "Join 1,200+ real estate professionals" |
| `/login` | `Trusted by 2,000+ agents` |
| `/register` | the whole social-proof block: `4.9/5 from 500+ agents`, the five-star row, and the avatar strip ending `+495` |
| `packages/ui` | `99.9% / Uptime` and the `SOC 2 / Ready` badge |

Two of these were removed as a *block* rather than edited as a caption, because trimming the text would have left the claim standing in the graphic: `/register`'s `+495` encodes the same unsourced 500 a second time, and `/about`'s figures exist only as a card.

`/about`'s two-column grid collapses to one column. Its CTA also read "Start Your Free Trial" and pointed at `/login` — now "Start free", pointing at `/register` (G1b).

**Kept:** "7 / Report types" on `/login`. 8 report slugs exist, `open_houses` is disabled in the wizard, so 7 is what a user can actually count.

The `packages/ui` copy was corrected even though the file is dead (D-050) — a dead file is precisely where a retired claim survives to be rediscovered. Its `SOC 2 / Ready` badge is the one commit `725802a` recorded as knowingly left behind "pending a separate decision on that package", while that same commit rewrote `/security` to state plainly that TrendyReports is **not** SOC 2 certified. That decision is now made.

**One more instance, dead rather than live:** `packages/ui/src/components/marketing-home.tsx:588-589` also carries `99.9% / Uptime`, plus the SOC 2 badge `725802a` explicitly deferred. `packages/ui` is imported by nothing in `apps/` — it meets the Phase 5 death standard and its copy should be deleted with the package rather than corrected.

### D-049 — Footer navigation entries were mailto links, one of them to a page that does not exist
**Severity:** ROUGH · **Affects:** every visitor to a secondary page
**Status:** `fixed` — `fix/m4-nav-identity`

Chrome findings #7 and #8. A nav entry that opens a blank email client is a dead end dressed as a destination — the reader clicks expecting a page and gets an empty compose window with no context.

**In the live footer** (`components/site-footer.tsx`), two entries:

- **"For Title Companies"** → `mailto:sales@trendyreports.io`, sitting in the Product column between two real page links. `apps/web/app/for-title-companies/` **does not exist**, so there was no page to link to even in principle. Removed. The page is M6, gated on G4; restore the entry when the route exists — a missing link is better than a dead end.
- **"Contact Us"** → `mailto:support@trendyreports.io`, styled as a nav link. Replaced with a single labelled contact line that shows the actual address, so the reader can see where it goes, copy it, or use whatever client they actually use. FAQ stays a link because `#faq` is a real section.

**In the dead footer** (`components/footer.tsx`), the "Company" column was **Partners, Press and Support — three nav entries, all mailto**. That is the "site with no company behind it" shape finding #7 describes. Per the ticket, deleting the headings is the fix rather than building Partners/Press pages; here the whole file went, because it renders nowhere.

**`components/footer.tsx` and `components/navbar.tsx` deleted.** Both meet the Phase 5 death standard, confirmed rather than assumed: their exported symbols `Footer` and `Navbar` have **zero references anywhere** in `app/`, `components/` or `lib/` — searched by symbol as well as by import path, so relative imports could not hide one. M2 replaced them with `site-nav.tsx` / `site-footer.tsx`. Verified with a full `next build` (exit 0), not just `tsc`. Deleted here rather than left for a future audit to re-litigate.

**Every remaining nav and footer entry was verified to resolve** — the eight anchors across both components all have matching section IDs on the landing page (`how-it-works.tsx:385`, `report-types.tsx:101`, `lead-capture.tsx:41`, `contact-management.tsx:123`, `pricing.tsx:59`, `faq.tsx:51`). This matters because M2 made these anchors root-relative, which fixed *where* they point without establishing that anything is *there*; a bare `#fragment` that resolves to nothing fails just as silently as one on the wrong route.

**M4-T3 not done — G3 unanswered.** `/privacy:186` and `/terms:192` still carry "123 Market Street, San Francisco, CA 94103" and "(415) 555-1234", on the exact pages a title company reads during vendor diligence. Per the ticket, no substitute placeholder is to be shipped, and an omitted phone is neutral where a fake one is disqualifying.

### D-050 — `components/v0/` is six files with no importers
**Severity:** ROUGH · **Affects:** nobody at runtime — this is dead weight and a re-litigation risk
**Status:** `open`

`apps/web/components/v0/` contains `Navbar.tsx`, `code-tabs.tsx`, `dashboard-overview.tsx`, `new-report-wizard.tsx`, `segmented-control.tsx`, `tag-input.tsx`. **All six have zero importers.**

`v0/Navbar.tsx:16` carries `{ label: "Partners", href: "#partners" }` — the same Partners entry M4-T1 removed, and `#partners` matches no section anywhere. So a future audit sweeping for "Partners" will find it again and re-open a closed finding.

Recorded rather than deleted because this is a different path from PR #27's `v0-report-builder/` and belongs with that dead-code removal, not inside a navigation ticket. **PR #27 is still unmerged** — this should go in with it.

### D-051 — `plans.monthly_report_limit` and `plans.market_reports_limit` disagree on four plans
**Severity:** WRONG · **Affects:** admin limit checks and the account API, on `free`, `sponsored_free`, `pro`, `team`
**Status:** `open`

Found while writing migration 0054 (G1a), which updates both columns for `starter` precisely so they cannot diverge. Checking whether the others were already divergent showed that **four of eight are**:

| plan_slug | `monthly_report_limit` (legacy) | `market_reports_limit` (live) |
|---|---|---|
| `free` | **5** | 3 |
| `sponsored_free` | **10** | 3 |
| `pro` | **300** | 99999 (unlimited) |
| `team` | **1000** | 99999 (unlimited) |
| `affiliate`, `solo`, `starter`, `trial` | — | agree |

The two columns are **not derived from one another**. In `apps/api/src/api/services/usage.py`, `market_reports_limit` → `market_limit` (`:131`) → `evaluate_product_limit` / `get_full_plan_usage` (`:248-255`), which is the live enforcement path for report creation; `monthly_report_limit` → `effective_limit` (`:135`) → `evaluate_report_limit` (`:324`).

**Why this has not caused visible breakage:** the live path uses the correct column, and `evaluate_report_limit` has exactly one remaining caller, `routes/admin.py:621`. It is imported into `routes/reports.py:7` but never called there — the live route uses `get_full_plan_usage` at `:156`.

**Where it does surface:** that one admin path, and `monthly_report_limit` is returned verbatim in the account API responses (`routes/account.py:180,299`). So an admin or API consumer reading a `pro` account sees a limit of **300** for a plan the product sells and enforces as unlimited, and a `free` account reads **5** against an enforced 3.

**Also worth noting:** `:135` reads `plan_limit or 100`. A NULL legacy column does not fail closed — it silently grants **100**.

**Measured locally, against a database built from `db/migrations/`.** Production values for `monthly_report_limit` are unknown; the production evidence supplied so far covers `market_reports_limit` only. **Confirm before fixing** — the production `plans` table has demonstrably been hand-edited (see 0054's header), so it may diverge differently.

The fix is one statement extending 0054's shape to the other rows, deliberately not included: the instruction scoped that migration to `starter`, and silently rewriting limits on four more plans inside a ticket about the Growth tier is the kind of unrequested data change that should be its own reviewed decision.

### D-052 — `_intake/` is 183 files referenced by nothing
**Severity:** ROUGH · **Affects:** nobody at runtime — dead weight and a re-litigation risk
**Status:** `open`

`_intake/real-estate-saas/` contains 183 tracked files, including its own `components/footer.tsx` and `components/navbar.tsx`. **Nothing in `apps/web` references `_intake/`** — not the app code, not `tsconfig.json`, not `next.config`.

Same class as D-050 (`components/v0/`), and the same specific hazard: it holds another copy of the footer whose Partners/Press/Support mailto entries M4-T1 removed, so an audit sweeping for those strings finds them again and re-opens a closed finding.

Held for PR #27's dead-code removal alongside D-050, on the same reasoning: deleting 183 files is not a side effect of a copy ticket. **#27 is still unmerged**, and it should take D-050 and D-052 in with it.

---

## BLOCKED-NEEDS-DEPLOYED-ACCESS (Phase 2B)

- **Is production's DB role a superuser?** D-005/D-006's real-world severity depends on it. If production also connects as owner/superuser, D-005 is live exactly as reproduced. If production uses a restricted role, D-005 is contained but D-006 means the portal is showing zeros.
- **Production env values** (T2.9/T2.10). Partially answered by the P2B trace above for the API service; the worker and Vercel sets are still outstanding — see "What I still need" above for exactly which variables settle which defect.
- **Scheduled delivery end-to-end** (T2.3). Needs a real send and a readable inbox.
- **Does a deployed E2E environment exist?** (D-045). `e2e.yml` is disabled until someone can confirm a host these tests can run against *and* that all five `E2E_*` repository secrets are populated. Not a defect — a fact about the deployment that cannot be read from the repository. If the answer is no, the workflow should be deleted rather than re-enabled.
- ~~**Is `apps/api/migrations/phase4_indexes.sql` applied in production?**~~ **ANSWERED (2026-08-18): no, and neither is `0042`.** `signup_tokens` exists but 5 of the 7 indexes do not, and the 2 that do are each declared by an *other*, applied migration. The file never ran; the table arrived by the route its own header describes — created inline by an old request handler. See **Production evidence reconciliation** for the proof, the confirming query, and the corrected bootstrap order.
