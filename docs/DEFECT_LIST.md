# DEFECT LIST — Phase 2A (local verification sweep)

**Date:** 2026-08-18
**Plan:** `EXECUTION_PLAN_REV_A.md` Phase 2A (local only)
**Tickets covered:** T2.1 (test account provisioning), T2.2 (company / title-company portal), T2.4 (registration → onboarding → first-run), T2.6 (authenticated smoke test), T2.7 (migration state), P1/P2/P3 (configuration trace, `chore/p2b-config-trace`), and the production-evidence reconciliation (`chore/defect-reconciliation`)
**Phase status:** Phase 2A complete (T2.1, T2.2, T2.4, T2.6, T2.7), plus the F5 affiliate-surface audit and the P2B configuration trace. **S2 (autonomous delivery) is PROVEN in production** — see the S2 section. The rest of Phase 2B remains blocked on deployed access.

## Status

**Last reconciled:** 2026-09-29, against `main` at `b0c52f9`, at the close of Workstream D.

**HOW DEEP THIS SWEEP WENT, PER ENTRY RATHER THAN PER SWEEP** — §0.6's rule, because "swept, all
36 checked" flattens three different claims into one:

| depth | entries | what was done |
|---|---|---|
| **mechanism reproduced** | 6 | D-086, D-097, D-098, D-027, D-106, D-109 — the named construct executed or read in current code, and the numbers in the entry recomputed |
| **construct located** | 5 | D-050, D-052, D-096, D-075, D-100 — the code the entry describes found and confirmed unchanged, without re-running the original measurement |
| **file references resolved** | all 36 | every `path/to/file.py` an open entry names was checked to still exist. 33 references; **one is stale** (D-011 names `apps/api/migrations/phase4_indexes.sql`, which the 2026-08-18 reconciliation already established was never applied and has since been removed) |
| **not re-verified** | 24 | unchanged since 2026-09-24 and nothing in Workstreams C or D touched them. **"Not re-verified" is not "probably fine"** |

**Two drifts found, both small and both in the same direction — the entry overstating:**

* **D-052** says `_intake/` is 183 files. It is **180**. The claim that nothing references it
  stands; the count does not.
* **D-086** is now *partially* superseded and the entry did not say so. `compute/price_bands.py`
  (D-111) has its own `_median` that returns `None` for an empty list, which is the fix this
  entry asks for — but `report_builders._median` still returns `0.0` and still reaches
  `median_close_price`, `median_list_price` and four other price fields. The defect is live on
  the paths it was filed against and fixed on one new one.

**Nothing was found fixed-but-still-open, and nothing open-but-actually-fixed** — the two
directions the 2026-09-22 sweep caught. The board and the code agree on all 36.


> ## PRODUCTION IS TEST DATA (confirmed by Jerry, 2026-09-17)
>
> **Every account in the production database is test data. There are no real customers yet.**
> Recorded here once rather than on each entry, because it changes the same thing everywhere.
>
> **What it changes:** nothing currently open is a live incident. No disclosure is owed, no
> customer is being harmed today, and there is time to fix a family properly rather than patch its
> symptom.
>
> **What it does not change: severity.** A defect that sends a stranger's report nowhere is BROKEN
> whether or not a stranger has arrived yet — it ships the moment one does, and the fix is the same
> size either way. Severities on this board are properties of the code, not of the customer list.
> The word to use is **latent**, not *"not a real problem"*.
>
> **What it closes:** D-021 (`closed-not-live` — "Demo Title Company" is test data; its account
> type is cosmetic, not a tenancy defect). It also removes the migration and grandfathering
> questions from anything that changes user-facing behaviour, which is why D-019 could be decided
> for free — and, now that it is fixed, shipped without a migration or a grandfathering pass.
>
> Two entries still describe live customer harm in the present tense because they were written
> before this was known — D-031 and D-074. Both are corrected in place.

Every defect carries its own `**Status:**` line. **That line is the source of truth.** Everything in this section is derived from it by parsing the document — do not edit these counts by hand, and do not record a status here that is not also on the entry. A summary that can drift from the entries is how a defect list stops being trusted, and an untrusted list stops being read.

| State | Count | Meaning |
|---|---|---|
| `recorded` | 0 | Observed, not yet triaged |
| `open` | 56 | Real, unfixed |
| `fixed` | 91 | Corrected in code, with the branch or PR named on the entry |
| `closed-not-live` | 4 | Not occurring in production, with the evidence named on the entry |
| **Total** | **151** | D-001 … D-151, contiguous, no duplicates |

**Open by severity:** BROKEN 5 · WRONG 14 · FRAGILE 15 · ROUGH 22. (Sums to 56, the open total.)

> **THIS TABLE WENT STALE AND NOTHING NOTICED — including the sweep that was about exactly that.**
> On 2026-09-23 it read `open 33 · fixed 53 · Total 91`, with a severity line summing to 34 against
> its own stated 33, while the entries below said 30 / 60 / 94. Three successive branches had
> updated it with a `str.replace` against an expected string; after a merge changed that string,
> the replace matched nothing and **silently did nothing** — the same no-op-mutation trap that made
> a regression look green in D-087's harness.
>
> The instruction above ("do not edit these counts by hand, re-derive them") was followed every
> time, and the derivation was correct every time. What failed was *writing the result back*.
>
> **So it is now a test:** `tests/test_defect_list_counts.py` re-derives the counts by parsing and
> fails if this table disagrees. A board whose own summary can drift is the write-only-record
> problem one level down — and the fix is the same one this file keeps arriving at, which is to
> make the property structural instead of somebody's diligence.
>
> **AND THE SECOND READER DISAGREED WITH THE FIRST, on 2026-09-30.** `scripts/derive.py` had its
> own copy of the parse. Adding D-145…D-149, it reported 149 contiguous entries and `fixed = 89`
> while the test reported 146 and `fixed = 86`: three of the new entries carried `**Status:**`
> mid-line, which the test's line-anchored regex requires and the script's did not. The script
> — whose entire job is to stop this table drifting — said the document was fine. `derive.py` now
> imports the test's `parse()`, so there is one reader and it is the one CI runs. Two
> implementations of "how to read this document" is a second answer waiting to be believed.

`fixed` — D-001, D-002, D-015, D-016, D-017, D-018, D-020, D-022 (`fix/p4-broken-defects`); D-005, D-007 (PR #24); D-038, D-039 (PR #29); D-040 (PR #30); D-044 (`fix/m5-responsive`); D-041, D-042 (`fix/frontend-ci`); D-049 (`fix/m4-nav-identity`); D-045 (`chore/disable-e2e-workflow`); D-046, D-048 (`fix/m3-copy-truth`); D-053 (`chore/migration-bootstrap-guard`); D-054 (`chore/collect-root-tests`); D-055 (`fix/insight-moi-guard`); D-059 (`fix/brand-color-validation`); D-058 (`fix/template-escaping`); D-061 (`fix/schedule-run-lifecycle`); D-035 (`0054_growth_plan_report_limit.sql`, applied 2026-09-09); D-066 (`fix/realtor-mark-default`); D-065 (`fix/email-log-commit`); D-063 (`fix/pdf-missing-explicit`); D-062 (`fix/acks-late`); D-064 (`fix/email-log-commit` — loss count zero, confirmed from the mailbox); D-072 (`fix/enqueue-after-commit`); D-067 (`fix/theme-cover-title`); D-071 (`fix/retry-policy-honest`); D-076 (`fix/vendor-query-idioms`); D-080, D-081 (`fix/pagination-by-count`); D-056 (`fix/inventory-moi`); D-060 (`fix/postal-address`); D-031, D-032, D-033, D-069 (`fix/consumer-delivery-truth`); D-070 (`chore/agreed-followups`); D-019 (`fix/d019-verified-sending`); D-037 (`fix/d037-bridge-durability`); D-074 (`fix/d074-close-date-window`); D-057 (`fix/d057-inventory-median-price`); D-087, D-088 (`fix/q-city-contamination`); D-089, D-090 (`fix/root-suite-mode`); D-091, D-092 (`fix/api-suite-drift`); D-095 (`fix/d095-d096-cache-key-and-limiter`); D-085 (`feat/workstream-c-email-rebuild`); D-099 (`fix/d099-readability-helpers`); D-093, D-094, D-009 (`fix/d093-d094-redis-and-free-plan` — D-009 closed as the Phase 2A filing of D-094); D-006 (`00df801`), D-003 (`cd94e27`) — both closed by the 2026-09-22 stale sweep, fixed long before and never recorded. D-107, D-108 (`feat/zero-rendering-and-band-cards`); D-112 (`fix/masthead-contrast-and-neutral-default`); D-113 (`fix/d113-trend-history-never-fetched`); D-111 (`chore/probe-365-window`); D-116, D-117 (`fix/e1-remove-owner-block`); D-118, D-132 (`fix/d118-remove-assessment-row`, completed by `feat/d118-last-sale-from-sitex`); D-133 (`feat/d118-last-sale-from-sitex`); D-138 (`fix/wizard-lookup-contract`); D-139 (`fix/cma-projection-gaps`); D-140 (`refactor/consumer-report-data-shared`); D-141 (`docs/d141-consumer-page-set`); D-120, D-137 (`fix/d137-absent-is-not-a-default`).
`closed-not-live` — D-025, D-026, D-029 (worker logs, 8/17); D-021 (production is test data, Jerry 2026-09-17).

**A status claim with no pointer is not a status, it is an assertion.** `fixed` must name a branch or PR; `closed-not-live` must name the evidence. Anything that cannot be traced reverts to `open`. This is the standard the 2026-08-17 docs audit applied to `SOURCE_OF_TRUTH.md`, and it applies to entries written during this remediation too — four of the claims corrected in this pass were written today.

**How to re-derive:** parse `^### (D-\d{3}) —` for entries and the following `**Status:**` / `**Severity:**` lines. A count computed any other way — including by adding up what changed on each branch — is a hypothesis. The previous version of this table was produced that way and was wrong by three: it dropped D-035, D-036 and D-037 entirely.

Plus 5 items marked BLOCKED-NEEDS-DEPLOYED-ACCESS and 2 UNVERIFIED. Those are open questions, not defects, and are counted separately.

**Which of this remediation's scripts have actually been run:** `docs/SCRIPT_EXECUTION_INVENTORY.md`. **Nothing is now unexecuted.** Getting there found six defects in the two live-database `.sql` proposals — none caught by review or by their text-assertion tests, two of which would have written false data into production. Worth reading before pointing anything at production.

D-001 through D-024 are grouped by severity below. D-025 through D-034 are grouped in the **P2B — Configuration trace** section, D-035 through D-037 in the **Production evidence reconciliation** section, and D-041 through D-054 in the **Phase M — Marketing / UX** section, because each is only readable alongside the trace that produced it.

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
**Status:** `fixed` — `00df801` *"fix(security): set RLS context in all company portal handlers"*

> **STALE SINCE `00df801`, FOUND BY THE 2026-09-22 SWEEP.** Every claim below is now false:
> `set_rls` **is** imported (`company.py:13`), and all six named handlers call it —
> `get_overview` :96, `list_reps` :354, `list_agents` :430, `get_company_reports` :504,
> `get_company_schedules` :587, `get_metrics` :989 — ten call sites across the module.
>
> **Severity left at BROKEN (latent) rather than retconned.** The original triage was right and
> should stay legible.
>
> This is the second entry the sweep closed and the more uncomfortable one: a BROKEN defect was
> fixed and the board never heard about it, so the number at the top of this file has been
> overstating the risk for as long as that commit has been in. **A stale `open` is not a harmless
> bookkeeping error — it is the mirror image of D-009.** One made real risk invisible; this made
> imaginary risk visible, and both corrupt the same count.

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
**Status:** `fixed` — `fix/d019-verified-sending`

`POST /v1/auth/register` creates the user with `email_verified = false` (confirmed in the database) and returns `{"ok":true,"email_verified":false}`. Logging in immediately afterwards with the same credentials **succeeds**, and every authenticated surface then works normally — `/v1/onboarding`, `/v1/me`, `/v1/account/plan-usage`, `/v1/reports`, `/v1/schedules`, `/v1/contacts` all returned 200 for the unverified account.

So the verification email is decorative: nothing gates on `users.email_verified`. Whether that is intended is a product decision, but it should be a decision — as written, the flow implies a gate that does not exist, and an address typo produces a working account nobody can reach.

Minor, same endpoint: the docstring for `register` (`apps/api/src/api/routes/auth.py:229-238`) claims it "Returns auth session (JWT + cookie)". It does not — the response carries no token.

> **DECIDED AND FIXED (Jerry, 2026-09-17): enforce on SENDING, not on login.**
>
> An unverified account logs in, builds and previews as before. It cannot send, and it cannot
> set up something that will send later. That is the narrow rule that matches the harm: gating
> login punishes the typo victim by locking them out of the account they just made, while gating
> sending is what stops the platform putting mail in strangers' inboxes over a return address
> nobody has confirmed. It also keeps the product usable in the minute between signing up and
> clicking the link, which is when most people look around.
>
> **The gate is account-level, not caller-level**, and that is forced rather than chosen.
> `AuthContextMiddleware` resolves `request.state.user` only on the JWT path
> (`authn.py:145`) — API-key callers and the `X-Demo-Account` fallback set `account_id` and no
> user at all. A per-user rule has to invent an answer for those and both answers are wrong:
> deny and API keys stop working, allow and the gate is bypassable by authenticating
> differently. So the question asked is *does this account have any active user with a
> confirmed address*. For a self-registered account the two readings coincide exactly —
> `register` (`auth.py:270-290`) creates a fresh account holding exactly one user.
>
> **`POST /v1/reports` could not be gated at the route.** Build and send are the same endpoint,
> told apart only by `send_email` / `recipients` in the payload, which are handed straight to
> the worker. A `Depends` would have blocked previewing, which is the half the decision
> explicitly preserves. So the condition is the payload — and it is `or` where the worker's own
> ad-hoc send path uses `and` (`tasks.py:1826`), deliberately the looser of the two: a refusal
> that over-refuses costs an unverified account nothing it is entitled to, while matching the
> worker's `and` would mean any future loosening there silently opens a hole here.
>
> **The API gate alone would not have been enforcement.** It refuses to *create* a sending
> schedule; it cannot refuse one that already exists, and the API is not what sends. Sixty
> seconds after a schedule comes due, `process_due_schedules` picks the row up having consulted
> nothing but `active` and `next_run_at`. The check is therefore repeated in
> `schedules_tick.py`, in the same shape as the usage-limit pre-check beside it — skip, record,
> advance `next_run_at`. Not DRY and it cannot be: the API and the worker are separately
> deployed services that do not import each other, which is why `check_usage_limit` already
> exists in one package alongside `get_full_plan_usage` in the other. **The duplication is the
> deployment boundary.** Both sites name each other.
>
> **Every refusal is recorded** — `email_log`, `status = 'blocked_unverified'`, with the reason
> and the action. #61's rule: a send that does not happen leaves something behind saying why,
> or the only difference between "we refused" and "it silently vanished" is a log line nobody
> reads at the time it matters. The status is deliberately outside `admin.py`'s email-count
> allowlist (`sent`, `sending`, `failed`), which that file's comment already explains: a status
> added later can only undercount, never inflate.
>
> **§0.6 rule 3, in the design rather than in the postmortem.** `db_conn()` commits only on a
> clean exit (`db.py:56-61`) and the gate raises on the line after it writes — so a refusal
> recorded on the caller's cursor would be rolled away *by the refusal it documents*. Present
> in the code, absent from the database, discoverable only in production. That is exactly
> D-065's shape. The record therefore goes in a transaction of its own, with its own explicit
> commit.
>
> Gated surfaces: `POST /v1/schedules`; `PATCH /v1/schedules/{id}` when it sets `active: true`
> or changes recipients (a rename or a **pause** stays allowed — stopping a schedule should
> never need verification); `POST /v1/reports` when it names recipients; `POST
> /v1/branding/test-email`; `POST /v1/company/invite-rep` and `/resend-rep-invite`; `POST
> /v1/affiliates/invite-agent`, `/resend-invite` and `/bulk-invite` — checked before the CSV is
> read, so a refused bulk invite has not parsed a row.
>
> **Does a refused schedule advance `next_run_at`? Yes — confirmed by behaviour, not by
> reading.** If it did not, the schedule would stay due and write a `blocked_unverified` row
> every 60 seconds, per schedule, indefinitely — 1,440 a day into the table D-061 through
> D-065 spent five branches making trustworthy. The skip calls `compute_next_run` and commits
> the new value on the same path as the record, before `continue`. Proved in
> `test/ticker-skip-advances` by ticking a blocked schedule twice against a fake that honours
> `next_run_at`, and getting one row. **The test that was supposed to already cover this
> passed against the regression** — it asserted that an `UPDATE` to `schedules` had happened,
> and the lock-clearing `UPDATE` on the same path satisfied that. Fourth instance of §0.6's
> "a test you have not seen fail". Now asserts the column and, separately, the consequence.
>
> Tests: `apps/api/tests/test_verified_sending.py` (13 cases, 10 fail against `main`) and
> `apps/worker/tests/test_ticker_unverified.py` (9 cases). Both behavioural — requests through
> the real app, and the real ticker loop against a fake feed — with the database double
> **raising on any statement past the gate**, so a gate placed after the write would fail them.
> A test that grepped the routes for `block_unverified_send` would not.
>
> **No migration and no grandfathering**, because production is test data (see the board note).
> `email_log.status` is `TEXT` with no `CHECK`, so the new value needs no DDL. The one thing
> that does need checking on real data is whether any existing account would be locked out of
> sending on merge — `scripts/check_unverified_senders.sql`, read only, Jerry's to run. That
> query is itself checked against `sender_verification()` rather than trusted
> (`apps/api/tests/test_sender_query_matches_code.py`, 6 accounts, 0 disagreements, both
> directions), because a diagnostic query that has drifted from its code does not fail — it
> returns the answer everybody is hoping for. Validated on Postgres 16; production is
> documented as 15, so the query prints the server version it actually ran on.
>
> The `register` docstring is left as it was: it is a doc defect on an endpoint this ticket
> does not touch, and folding it in would put an unrelated edit in this diff.

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
**Status:** `fixed` — `cd94e27` *"fix(ci): restore backend CI — Poetry instead of a requirements.txt that never existed, Python 3.12 instead of 3.11"*

> **STALE, found by the 2026-09-22 sweep.** `apps/api/pyproject.toml:10` now declares
> `python = "^3.12"`, matching both the source (which does not compile on 3.11 — see the f-string
> at `services/email.py:729`) and the CI pin. Closed against the commit that did it, which fixed
> this incidentally while restoring the backend workflow and never said so.

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
**Status:** `fixed` — `fix/d093-d094-redis-and-free-plan` (as D-094)

> **THIS IS D-094, FILED IN PHASE 2A AND CORRECTLY DESCRIBED THEN.** The paragraph below names the
> exact lines, the exact symptom and the `/health` blindness — eleven months before D-094 was
> written from the other end, by tripping over it while making the API test suite green.
>
> Closing it here rather than leaving it open beside its duplicate, because two open entries for
> one defect is how a board stops being countable. **The severity was understated**: filed FRAGILE,
> it is BROKEN — every authenticated request 500s — and D-094 carries that. Left at FRAGILE here so
> the original triage is legible rather than retconned.
>
> Worth sitting with: this was **found, written down accurately, and not acted on**, and then
> rediscovered by accident. The board worked as a record and failed as a queue.

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

Observed live during this phase — when local Postgres stopped, every authenticated request returned "Token has been invalidated" while the API log showed the real cause: `Blacklist check failed (denying request): couldn't get a connection after 10.00 sec`. To the user this is indistinguishable from being logged out, and it is invisible to monitoring: `/health` is on the middleware's public-path skip list (`authn.py:207`) and probes neither database nor Redis (`apps/api/src/api/routes/health.py:6-8`), so it stays green throughout. **CORRECTION (2026-09-22): the D-009 half of this is fixed; this entry is not.** Redis being
unreachable no longer 500s anything — the rate limiter degrades and says so (D-094). What remains
is the sentence this entry is actually about: a **database** outage still reaches the user as
`401 "Token has been invalidated"`, because the blacklist check fails closed, which is correct, and
reports itself as a revoked token, which is not. `/health` still probes neither dependency. The
paragraph below was written when both halves were live; read it for the reporting defect, not for
the 500s.

Combined with D-009 (Redis unreachable ⇒ 500 on every authenticated request), an infrastructure blip presented to a customer as "the product logged me out / is broken" with no corresponding signal on our side.

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

Related to D-021, which is the same class of mismatch observed from the other direction.

> **CORRECTED BY THE 2026-09-22 SWEEP — this entry overstated the live risk.** It said *"renaming
> that customer, or onboarding any other company whose name happens to contain those words, changes
> tenancy behaviour."* **That is not true and cannot be.** `0050` is a migration: it ran once, and
> the runner will not run it again. A rename today changes nothing, and a new company whose name
> contains "pacific coast" gets whatever `account_type` it is created with.
>
> What remains true is narrower and worth keeping: the `account_type` values that exist **were
> assigned by a name match**, so their provenance is a string someone typed rather than a decision
> anybody recorded. That is a data-lineage concern, not a live trigger. Kept `open` at FRAGILE on
> that basis; it would be `closed-not-live` if the assignment were ever verified against intent.
>
> Recorded rather than quietly reworded, because the difference between "this will fire again" and
> "this fired once and left residue" is the difference between a defect and a footnote — and the
> original wording would have sent somebody looking for a trigger that does not exist.

### D-024 — `/v1/affiliate/all-reports` is gated differently from every sibling endpoint
**Severity:** ROUGH · **Affects:** REGULAR
**Status:** `open`

Every other affiliate endpoint refuses a non-affiliate caller with `403 {"error":"not_affiliate_account"}` via `verify_affiliate_account`. `GET /v1/affiliate/all-reports` instead returns `200 {"reports":[],"total":0}` (`apps/api/src/api/routes/affiliates.py:879`), because it derives its account set from `sponsor_account_id = <caller>` and a non-affiliate sponsors nobody.

Not a leak — verified during the F5 audit — but the inconsistency means a caller cannot distinguish "you are not an affiliate" from "you are an affiliate with no agents".

### D-021 — "Demo Title Company" sponsors agents while not being typed `TITLE_COMPANY`
**Severity:** WRONG · **Affects:** TITLE_COMPANY, SPONSORED · **Source: Jerry's query against the deployed database, not reproduced locally**
**Status:** `closed-not-live` — **the whole production database is test data (Jerry, 2026-09-17)**

> "Demo Title Company" sponsoring three agents while typed as something other than `TITLE_COMPANY`
> is not a tenancy defect, because there is no tenant. Its account type is cosmetic: clean it up or
> leave it. Closed on the evidence named above rather than on a code change.

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

> **STALE FILE REFERENCE, corrected 2026-09-29.** This entry names
> `apps/api/migrations/phase4_indexes.sql`, which no longer exists. That is consistent rather
> than contradictory: the 2026-08-18 production reconciliation established the file never ran and
> it has since been deleted. The entry's own claim — `/v1/company/metrics` is wired and
> unreachable from the product — is unaffected.

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


> **STILL REPRODUCES, AND IS NOW BETTER CAMOUFLAGED (2026-09-22 sweep).** `branding_tools.py:120`
> reads:
>
> ```python
> PDFSHIFT_API_KEY = os.getenv("PDF_API_KEY", "")
> ```
>
> The local variable has been renamed to match the rest of the codebase while the env var it reads
> has not. Someone grepping for `PDFSHIFT_API_KEY` now finds this line and moves on satisfied. The
> defect is unchanged; only its visibility got worse.

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
**Status:** `fixed` (`fix/consumer-delivery-truth`) — **the four branches that claimed a delivery are now three failures and one send**

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

> **FIXED 2026-09-17, and the survey missed one.** Four branches of this dispatch wrote
> `status='sent'`; exactly one of them had sent something:
>
> | Branch | Attempted? | Was |
> |---|---|---|
> | `RESEND_API_KEY` unset | never attempted | `sent` — **D-031** |
> | provider rejected it | attempted, refused | `sent` — **not filed, found here** |
> | no usable delivery method | could not be attempted | `sent` — **D-032** |
> | genuine success | yes | `sent` — correct |
>
> The second is the most direct instance of this project's shape anywhere in the codebase: the code
> logs *"CMA email delivery failed"* and the **very next statement** records success, with a
> timestamp. Found by re-running the survey after fixing D-031 two branches up — §0.6 rule 4.
>
> All three now call `_record_consumer_delivery_failure`, which writes `failed` **and the specific
> reason**. Not a new status: #56 added `sending` to `email_log` because it needed a state that did
> not exist; here the state exists and the adjacent path already uses it. What was missing was the
> reason, and that belongs on the row rather than in a log line that rotates (D-064).
>
> **A second bug was hiding behind the first.** The failure return read `sms_result`, which is bound
> only inside the SMS branch — so on the email and no-method paths it raised `NameError`, the outer
> handler caught it, and the real reason was replaced with a generic message. And the tail
> overwrote every specific reason with the string `'Delivery failed'`, the one fact everybody
> already had. Both fixed.
>
> **Latent, not live** — production is test data (see the note at the top of this file). The
> paragraph above describing an agent chasing a lead who received nothing is what happens the day a
> real lead arrives, not what has happened.

### D-032 — An unrecognised delivery method is also recorded as sent
**Severity:** WRONG · **Affects:** REGULAR, SPONSORED
**Status:** `fixed` (`fix/consumer-delivery-truth`) — **records `failed` with the method that could not be used**

`tasks.py:2020-2025`, the `else` arm of the same dispatch:

```python
logger.warning(f"No valid delivery method for report {report_id}: method={delivery_method}")
cur.execute("UPDATE consumer_reports SET status = 'sent' WHERE id = %s::uuid", (report_id,))
delivered = True
```

Same failure shape as D-031, different trigger: a report with no usable delivery method — no phone for SMS, no address for email, or an unrecognised `delivery_method` value — is marked `sent` and fires the agent's "new lead" SMS. `status='failed'` exists and is used on the adjacent path (`:2054-2060`); this branch chooses not to use it.

### D-033 — Failure notifications are the one alert that tells an agent their scheduled report broke, and they are skipped silently
**Severity:** FRAGILE · **Affects:** every persona with a schedule · **Conditional on `RESEND_API_KEY` on the worker**
**Status:** `fixed` (`fix/consumer-delivery-truth`) — **the suppression is recorded in `email_log`, not only logged**

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
**Status:** `fixed` (`db/migrations/0054_growth_plan_report_limit.sql`, applied to production 2026-09-09)

> **CLOSED 2026-09-09.** `0054` is applied: Growth is **25/25** in production — both
> `market_reports_limit` and `monthly_report_limit`, so the enforced gate and the legacy column
> agree and marketing's 25 is now the number the code uses. Fixed as a **data** migration, not a
> copy change, per the G1a decision.
>
> **The bootstrap guard worked as designed on its first real use.** `--except` marked 54 files
> applied without executing them, `seed_demo_account.sql` was *recorded rather than run* — the
> sorted-order trap that made a bare `--bootstrap` dangerous — and only `0054` executed. That trap
> is exactly what D-053 was filed for, and this is it functioning in production.
>
> The eleven `skipped_limit` runs on the review's own schedule between January and April were this
> cap firing. They stop now.

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

**How to apply it, exactly.** Production has never been bootstrapped, and a bare `--bootstrap` would mark 0054 applied without running it (D-053). Use the explicit form:

```bash
python scripts/run_migrations.py --status
#   expect: 55 files on disk, 0 applied, 55 pending

python scripts/run_migrations.py --bootstrap --except 0054_growth_plan_report_limit.sql
#   expect: 54 marked as applied without running
#           1 file(s) were deliberately LEFT PENDING ... 0054_growth_plan_report_limit.sql

python scripts/run_migrations.py
#   expect: >>> Running migration: 0054_growth_plan_report_limit.sql
```

`--except` rather than `--through 0053_…`: `--through` splits on sorted order and `seed_demo_account.sql` sorts last, so a 0053 boundary would leave the demo seeder pending too and the normal run would insert a demo account into production. See D-053.

Verified locally against a database seeded from `db/migrations/`: reproduced production's `15 | 15`, ran that exact three-command sequence, and the verification query returned `25 | 25`. Also verified the older path — apply 0054 directly, re-apply, still `25 | 25` (idempotent). **95 `skipped_limit` rows say real users are hitting the 15 today**, so this is the one item in this batch with a live customer cost attached to the delay.

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


> **PARTIALLY ADDRESSED BY D-037, AND THE REMAINING HALF IS THE ONE THIS ENTRY IS ABOUT
> (2026-09-22 sweep).** The bridge now takes work with `BLMOVE` onto a processing list,
> dead-letters what it cannot dispatch, and marks the run `failed` — so a payload that FAILS is no
> longer silent.
>
> A bridge that is **DOWN** is untouched: `rpush` still succeeds, the item waits in the list, and
> the report sits at `pending` with no error and no alert until the bridge returns. Kept open at
> FRAGILE for exactly that. The fix is an alert on queue depth or age, not more durability inside a
> process that is not running.

### D-037 — The bridge pops a job off the queue and then drops it permanently on any unexpected error
**Severity:** WRONG · **Affects:** REGULAR, SPONSORED, INDUSTRY_AFFILIATE, COMPANY_REP (manual reports)
**Status:** `fixed` — `fix/d037-bridge-durability`

`tasks.py:2116` pops with `blpop` — destructive — then parses and dispatches. The catch-all at `:2154-2157` logs and continues:

```python
except Exception as e:
    consecutive_errors += 1
    print(f"❌ Unexpected error in consumer (#{consecutive_errors}): {e}")
    time.sleep(min(5, backoff))
```

The item is already gone from the list. It is not re-queued, not written anywhere, not retried. Any exception between the pop and the `.delay()` — a malformed payload, a missing key, a broker publish failure — **destroys that job permanently**. The `report_generations` row stays `pending` forever and the only trace is one line of stdout.

This is the same user-visible symptom as D-036 (a report stuck at pending) with the opposite recovery property: an outage self-heals when the bridge returns, this does not. Distinguishing them in production means reading bridge logs; there is no state anywhere that separates "queued and waiting" from "silently destroyed".

> **FIXED as a reliable queue, not as a bigger `try`.**
>
> `blpop` removes the item. Wrapping the window in a handler cannot help, because the
> handler's problem is not that it lacks a `try` — it is that by the time it runs, the only
> copy of the job is a local variable, and a `SIGKILL` does not run handlers at all. The take
> itself had to stop being destructive:
>
> ```python
> payload = r.blmove(QUEUE_KEY, PROCESSING_KEY, 5, "LEFT", "RIGHT")
> ```
>
> One atomic step, same blocking wait, and `LEFT`/`RIGHT` preserves FIFO against the
> producer's `rpush` (`api/worker_client.py:15`). The item now survives anything that happens
> next, including the process dying mid-window; `_recover_processing` returns stranded items
> to the head of the queue at startup and after every reconnect, in their original order.
>
> **Three outcomes, because the failure modes are not alike.** A malformed payload is not
> retryable — re-queueing it is a poison-message loop, since it will fail to parse just as
> reliably next time — so it is dead-lettered. A dispatch failure usually *is* transient, so it
> is re-queued with an attempt counter carried in the payload, up to
> `BRIDGE_MAX_DISPATCH_ATTEMPTS` (3); an unbounded retry is the same hot loop in slower motion.
> After that the job is given up on **loudly**: `report_generations` is marked `failed` with
> the reason, and the payload goes to the dead-letter list.
>
> **Marking the row is the part that makes this visible.** Nothing sweeps `report_generations`
> — the stale sweep in `schedules_tick.py` covers `schedule_runs`, which a manual report does
> not have — so a destroyed job's row sat at `pending` forever and `/admin/health:2984`
> counted it as `idle_with_pending`, a number that goes up and never comes down. The
> dead-letter list is the payload archive; the row is the signal.
>
> **The catch-all at the bottom of the loop is still a catch-all**, and that is deliberate. It
> was never the bug. The bug was that it ran after the only copy of the job had already been
> destroyed. It can keep logging and carrying on now that doing so costs nobody a report.
>
> Tests: `apps/worker/tests/test_bridge_durability.py`, 12 cases, **against a real Redis**
> (7.0.15) — the fix is a claim about Redis semantics, and a fake implementing `blmove` would
> implement my belief about it and agree with the code for exactly the reasons the code might
> be wrong. Three regressions applied and seen to fail: reverting to `blpop`, replacing the
> dead-letter with a silent drop, and removing the startup recovery.
>
> **The first attempt at the end-to-end test did not catch `blpop`** — reverting the take left
> all 11 tests green, because the unit tests did their own atomic take in a helper and the
> drain test only observed the loop after it had finished, when a destructive take and a safe
> one look identical. Fifth instance of §0.6's "a test you have not seen fail". The test that
> does catch it parks the loop *inside* the window by blocking `delay`, and asserts the job is
> findable in Redis while it is held.
>
> **This does not touch D-036.** Whether the bridge runs in production at all is still open,
> and a durable queue in a process nobody starts is durable in the same way an unread log is
> informative.
>
> **`BLMOVE` confirmed on production Upstash, 2026-09-21** — `nil` returned after 1.476s on an
> empty list (correct blocking behaviour, not an error), `PING` true. Host tested:
> **`massive-caiman-34610.upstash.io`**. Recorded here so the next person can compare it
> against the bridge service's `REDIS_URL` in Render directly, rather than re-deriving it.
>
> **That confirmation carries one caveat, and it is recorded rather than smoothed over.** The
> check ran from a laptop against whichever `REDIS_URL` a local `.env` yielded, and that file
> contains **more than one** `REDIS_URL` line — so which value won depended on the dotenv
> parser's precedence rather than on anything anyone chose. The bridge in production reads
> Render's environment, not that file. One Upstash host is the likely answer for both, but
> "likely" is what this board exists to replace.
>
> So the bridge now prints the broker host AND the Redis version at startup, credentials
> stripped (`REDIS_URL.split('@')[-1]`, the idiom already used for `DATABASE_URL` at
> `schedules_tick.py:774`). Whatever that line says in Render's log **is** the broker the
> bridge uses — no comparison needed, and no dependence on a file that is not deployed.
>
> The duplicate `.env` line still wants deleting. It is not in this repository (`.gitignore:14`
> excludes `.env`; only `.env.example` is committed, and it has one `REDIS_URL`), so it cannot
> be fixed from here — it is on whichever machine ran the check.

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

**M4-T3 — ANSWERED (G3) and done on `fix/m4-t3-business-address`.** The real registered address replaces the placeholder on both legal pages: `terms/page.tsx` and `privacy/page.tsx`.

**The fake phone the ticket describes is not on any live page.** `git log -S "(415) 555-1234"` over `privacy`, `terms` and `security` returns nothing — it was never there. It lives at `_intake/real-estate-saas/components/footer.tsx:33`, the vendored second app that renders nowhere (D-052); the audit grepped the repository and attributed it to the legal pages. `123 Market Street` is in that file too (`:22`), alongside the live copies. So the placeholder pair the gate describes is really one live defect and one dead-code artefact, and the dead half is covered by issue #42 rather than here.

**No phone line was added.** None was supplied, and per the ticket an omitted phone is neutral where a fake one is disqualifying — so the field is absent rather than filled. The reasoning is recorded at both sites so a future editor does not "complete" the block with a placeholder.

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

### D-052 — `_intake/` is 180 files referenced by nothing
**Severity:** ROUGH · **Affects:** nobody at runtime — dead weight and a re-litigation risk
**Status:** `open`

`_intake/real-estate-saas/` contains 183 tracked files, including its own `components/footer.tsx` and `components/navbar.tsx`. **Nothing in `apps/web` references `_intake/`** — not the app code, not `tsconfig.json`, not `next.config`.

Same class as D-050 (`components/v0/`), and the same specific hazard: it holds another copy of the footer whose Partners/Press/Support mailto entries M4-T1 removed, so an audit sweeping for those strings finds them again and re-opens a closed finding.

Held for PR #27's dead-code removal alongside D-050, on the same reasoning: deleting 183 files is not a side effect of a copy ticket. **#27 is still unmerged**, and it should take D-050 and D-052 in with it.

### D-053 — `--bootstrap` marks never-run migrations as applied: a silent no-op with a green result
**Severity:** BROKEN · **Affects:** any deploy where a migration is authored before bootstrap runs
**Status:** `fixed` — `chore/migration-bootstrap-guard`

`--bootstrap` records files as applied **without executing them**, and it recorded *every* unrecorded file. Any migration in the tree that had never run anywhere would be marked applied and never execute — and nothing re-runs it afterwards, because the loop skips whatever is already recorded.

The result reads as complete success:

```
--status      → Status: 0 applied, 55 pending.
--bootstrap   → marked applied WITHOUT running: 0054_growth_plan_report_limit.sql
                Bootstrap complete: 55 marked as applied without running.
--status      → Status: 55 applied, 0 pending.
normal apply  → All migrations applied. (0 newly applied, 55 already recorded)

starter = 15 | 15          ← the migration's change was never made
schema_migrations claims:  0054_growth_plan_report_limit.sql
```

**Not hypothetical.** The production bootstrap runbook for this repository was written twice with `0054` already in the tree. Reproduced end to end against a database shaped like production (schema present, `starter` at 15, no tracking table); the sequence completed cleanly and left the Growth limit unchanged.

**Fixed** by making the boundary explicit in both runners — `scripts/run_migrations.py` and `scripts/migrate.sh` implement the same contract, so guarding only one would have left the hazard in place:

| Invocation | Behaviour |
|---|---|
| `--bootstrap --through NAME` | records `NAME` and everything sorting before it; the rest stay genuinely pending |
| `--bootstrap --except NAME` (repeatable) | records everything except the named files |
| `--bootstrap` (bare) | still permitted, but now **warns**, lists every file it would mark, and requires confirmation — `--yes`, or an interactive answer. Non-interactive without `--yes` exits 3 having written nothing |

Whatever is left pending is printed under the heading *"WILL EXECUTE on the next normal run"*, and an unknown filename in `--through`/`--except` is a hard error (exit 2) rather than a silent non-match — a typo in `--except` is precisely how a migration you meant to protect gets marked applied anyway.

**A trap the naive version of this guard would have introduced.** `--through` splits on *sorted* order, and not every file here is numbered: `seed_demo_account.sql` sorts after every `NNNN_` migration. So `--bootstrap --through 0053_phase4_indexes_and_signup_tokens.sql` leaves **both** `0054` and the seeder pending, and the next normal run would execute the seeder — inserting a hardcoded "Demo Account" (`912014c3-…`, 1000-report limit) into production. The guard would have swapped one silent hazard for another. It is documented in both runners' headers, asserted in the tests, and printed at runtime; `--except` has no ordering surprise and is the correct invocation for the current production run.

**Regression test:** `tests/test_migration_bootstrap_guard.py`, 19 cases, no database required — the defect lives entirely in *which files get selected*, never in the SQL, so the selection is a pure function and is tested as one. `run_migrations.py` now imports `psycopg` inside `main()` so the module is importable without a driver, which is what lets these run in CI (which has no Postgres service). **Verified load-bearing:** reverting `partition_bootstrap` to the old "mark everything" behaviour fails 10 of the 19, including `test_the_actual_regression`.

### D-054 — four documented test suites have never been collected
**Severity:** FRAGILE · **Affects:** template rendering, market metrics, SimplyRETS query building
**Status:** `fixed` — `chore/collect-root-tests`

`tests/` at the repository root holds `test_market_templates.py`, `test_property_templates.py`, `test_new_metrics.py` and `test_simplyrets_query_builder.py`. `pytest.ini`'s `testpaths` listed only `apps/api/tests apps/worker/tests`, so **none of them has ever been collected** — by CI or by anyone running `pytest` from the repository root.

They are not abandoned scratch files. `docs/architecture/modules/test-suite.md:9,25` documents `tests/test_property_templates.py` as part of the project's test suite and gives `pytest tests/test_property_templates.py -v` as the command; `.cursor/rules/market-report-templates-skill.md:335` describes `tests/test_market_templates.py` as a "Template test suite (57 tests)". The documentation and the runner disagree, and the runner wins silently.

This is the fifth instance of the same class in this document (D-015, D-038, D-039, D-041, D-042): a suite that exists, is believed to run, and does not.

**FIXED — `testpaths` now collects the `tests` directory, and the pipeline is red.**

Baseline at the moment of collection, measured per suite on `main` at `fde163f`:

| Suite | Result |
|---|---|
| `test_market_templates.py` | 1 failed, 56 passed |
| `test_property_templates.py` | 24 failed, 62 passed |
| `test_new_metrics.py` | **36 passed** — fully green |
| `test_simplyrets_query_builder.py` | 15 failed, 13 passed |
| **Four suites combined** | **40 failed, 167 passed (207)** |

Plus the 19 guard tests from D-053, which pass — 226 collected in `tests/` in total.

**The 40 failures are pre-existing and were previously invisible, not new breakage.** They are concentrated in two places: `test_simplyrets_query_builder.py` (query-parameter construction and vendor injection — 15 of 28 failing, the worst ratio in the repository) and `test_property_templates.py` (`None`-value handling across four themes, 24). `test_new_metrics.py` passes completely, which is worth noting: at least one of these suites has been correct and unrun for its whole life.

A detail that settles whether these are scratch files: `.cursor/rules/market-report-templates-skill.md:335` calls `test_market_templates.py` a "Template test suite (57 tests)". It has exactly 57. The documentation was accurate; only the runner ignored it.

**Landed red on the same reasoning as D-038 and D-041** — narrowing `testpaths` to make the pipeline green would restore precisely the condition that hid these, and the note in `pytest.ini` says so, so a future editor does not quietly undo it. Clearing the 40 is separate work; the SimplyRETS query builder is the place to start, since query-parameter defects reach live MLS calls.

**All three pipelines now report honestly rather than not at all** — backend (D-038/D-039), frontend (D-041/D-042), and these.

---

## Delivery Surfaces Phase 1

### D-055 — The email insight paragraph formats a value it has just established is falsy
**Severity:** FRAGILE · **Affects:** `market_snapshot` and `inventory` scheduled emails
**Status:** `fixed` — `fix/insight-moi-guard`

`_get_insight_paragraph()` in `apps/worker/src/worker/email/template.py` built its fallback prose with branches shaped like this:

```python
if moi and moi < 3:    ... f"{moi:.1f} months of inventory"
elif moi and moi > 6:  ... f"{moi:.1f} months of inventory"
else:                  ... f"{moi:.1f} months of inventory"   # moi is falsy HERE
```

The `else` branch is reached **precisely when `moi` is falsy**, and then formats it. On `None` that raises:

```
TypeError: unsupported format string passed to NoneType.__format__
```

Two sites, at what were `:1556` (market_snapshot) and `:1591` (inventory). Found by rendering an email during the B1 investigation, not by reading.

**The blast radius if it fires.** The exception propagates `_get_insight_paragraph` → `schedule_email_html` (`:1930`) → `send_schedule_email` (`email/send.py:205`). The email is never sent, and the Celery task fails. Combined with **D-033** — schedule failure notifications do not fire when `RESEND_API_KEY` is unset — the visible result is *a schedule that silently stops delivering, with nobody notified.* That interaction is why this was chased rather than filed.

**Severity is FRAGILE, not BROKEN, because the reachability trace came back negative.** Every producer that reaches this code supplies the key:

| Path | Producer | Supplies `months_of_inventory`? |
|---|---|---|
| Scheduled + ad-hoc email (`tasks.py:1048` → `:1280`, `:1347`) | `build_result_json` → `build_market_snapshot_result:256` / `build_inventory_result:493` | **Always.** `moi` is `99.9` (`:150`) or `0.0` (`:468`) when there are no closed sales — never `None` |
| Branding-page "Test Email" (`routes/branding_tools.py:877`) | `services/sample_report_data.py` | **Always** — every report type sets it |

Those are the only two production callers of `schedule_email_html`; the rest are `scripts/` generators and tests. So the crash is **not currently reachable**. The guard is still wrong, it costs nothing to fix, and the next producer that omits the key would take delivery down silently.

**Fixed** by computing the inventory clause once against `moi is not None` and omitting it when absent, rather than formatting unconditionally. Where the clause is dropped, the sentence that depended on it changes too — the old copy asserted a "balanced environment" and "well-balanced" market, which were inferences *from* the number and cannot stand without it.

**Regression test:** `apps/worker/tests/test_insight_paragraph_missing_metrics.py`, 44 cases — every report type × five degraded metrics shapes, plus direct exercises of the two branches. It renders through the real `schedule_email_html`, because the defect is a runtime format error invisible to any source-text assertion. **Verified load-bearing: 10 fail against the unfixed module, 44 pass with the fix**, full worker suite 56 pass with no regression.

### D-056 — `months_of_inventory = 0` means two different things, and the email reads it as a third
**Severity:** WRONG · **Affects:** **every** `inventory` email — see the severity confirmation below
**Status:** `fixed` (`fix/inventory-moi`) — **the Closed query exists, the numerator is inventory, and there is no sentinel left**

> **FIXED 2026-09-17.** Three changes, and all three are required; any one on its own still
> produces a wrong number:
>
> 1. **A Closed query exists.** `build_inventory_closed` fetches sales in the rate window, in
>    parallel with the Active query. `closed` was always empty because the query pinned
>    `status=Active`, so MOI was always the `else` branch.
> 2. **The numerator is total inventory.** `build_inventory_active` sends no date window.
>    Adding the Closed query alone would have divided *"listed in the last 30 days and still
>    active"* by a full 90-day sales rate — a wrong number, more convincingly.
>    `market_trends.py:98` already carried the comment that says why.
> 3. **The sentinel is gone.** Below three closings the metric returns `None` and the page says
>    *"Not enough recent sales to estimate"*. There is no 0.0 and no 999.0 anywhere.
>
> **Six implementations, not two.** The survey found two formulas. Re-running it after fixing
> them found four sites, then a fifth in `market_trends.py`, then a sixth in `compute/calc.py` —
> which used a **third** formula, a bare `active/closed` with no monthly rate at all, and its own
> `999.0`. That one is imported by `tasks.py` and never called; it is fixed rather than deleted
> because a function named `snapshot_metrics` in a module named `calc` is the most
> canonical-looking of the six and would have been the next one copied. Deleting it is a
> judgement for someone else.
>
> All six now call `compute/moi.py`. A test searches for the construct — a monthly sales rate
> computed outside that module — rather than for the literals that were wrong.
>
> **What a reader sees.** Every surface that prints the figure now prints
> *"at the last 90 days' sales pace"* beside it, because the window is a choice and a number
> whose basis is not stated cannot be checked (§0.6 rule 6, which was written about this metric).
>
> **The cost question is closed: SimplyRETS is not metered.** Confirmed by Jerry 2026-09-17 — the
> plan is flat, so the second query per inventory generation is free. Recorded here so it is not
> re-litigated: the only remaining cost of the Closed query is latency, and it is fetched in
> parallel so the added wall-clock is `max(0, closed − active)` rather than the sum.

> **Severity confirmed 2026-09-08 — the blast radius is larger than first recorded.**
> This was filed as reachable "on any inventory report over a period with no closings." It is
> reachable on **every inventory report ever sent**. `build_inventory_by_zip`
> (`query_builders.py:275`) pins `"status": "Active"`, so the vendor never returns a Closed
> record; `closed` in `build_inventory_result` is therefore *always* empty and
> `moi = ... if closed else 0.0` *always* takes the `else`. There is no market condition in
> which an inventory report produces a non-zero MOI. The elastic-widening retry
> (`tasks.py:1013`) re-queries through the same `build_params(report_type, ...)`, so it does not
> introduce Closed data either.
>
> Proven by driving the real chain — `build_params('inventory', …)` → `build_inventory_result` →
> `_build_email_payload` → `schedule_email_html` — against a deliberately **hot** market fixture
> (40 Active listings, 5–11 day DOM, nothing balanced about it):
>
> ```
> QUERY ISSUED: {'status': 'Active', 'mindate': '2026-08-09', 'maxdate': '2026-09-08'}
> MOI FROM BUILDER: 0.0   COUNTS: {'Active': 27, 'Pending': 0, 'Closed': 0}
> EMAIL METRICS  moi: 0.0 | total_active: 27 | total_closed: 0
>
> The La Verne market is well-balanced right now with 27 active listings and
> 0.0 months of inventory at a median of varying prices. Homes are averaging
> 8 days on market—neither rushed nor stagnant. Buyers can explore confidently
> without extreme competition, while sellers benefit from consistent demand…
> ```
>
> An 8-day-DOM market described as "neither rushed nor stagnant," "without extreme competition."
> `inventory` is a first-class scheduled report type (`routes/schedules.py:83`), so the question
> "has production rendered this?" reduces to "has any inventory schedule ever sent?" — no market
> condition is required. **That last question needs the read-only production query to close;**
> everything upstream of it is settled in code.
>
> The "at a median of **varying prices**" in the same sentence is a *separate* defect with a
> different root cause — see D-057.

Two builders use **opposite sentinels for the same condition**:

| Builder | No closed sales → | Meaning |
|---|---|---|
| `build_market_snapshot_result` (`report_builders.py:150`) | `moi = 99.9` | "very high — buyer's market indicator" |
| `build_inventory_result` (`report_builders.py:468`) | `moi = 0.0` | same condition, opposite number |

And a third convention: 6 of the 8 report types in `services/sample_report_data.py` ship `months_of_inventory: 0` simply meaning *not modelled*.

The email then reads `0` as neither. `if moi and moi < 3` treats `0` as falsy, so it falls to the `else` branch and renders:

> "The La Verne market is **well-balanced** right now with 42 active listings and **0.0 months of inventory** at a median of $812K."

A market with **zero closed sales**, described as balanced, in a sentence that contradicts its own figure. Not merely reachable — this is the *only* copy an inventory email can produce, for the reason given in the severity confirmation above.

**Deliberately not fixed, and one attempted fix was reverted.** Changing the branch conditions to `moi is not None and moi < 3` routes `0` to the seller's-market branch — *"Inventory is tight … well below the balanced threshold … an excellent time to list"* — which is confidently wrong for a market with no sales, and would fire on 6 of 8 branding-page test emails. The reading cannot be fixed in the email while `0` means three different things upstream. **The sentinel disagreement is the defect**; the email is downstream of it. Fix `report_builders.py` first, then revisit the routing.

The rationale is recorded in the code at the branch conditions so the next reader does not "correct" them into the same trap.

**Production reach, answered 2026-09-09.** **Zero** schedules have `report_type = 'inventory'` —
43 schedules exist, none of them inventory. The report type has run 12 times ad-hoc
(`report_generations`, all with PDFs); **4 of those were emailed**, in January 2026, and the other
8 are PDF-only from May 2026 with no `email_log` row.

So the contradictory copy has reached four real recipients, nine months ago, through one-off
sends — never on a recurring schedule and not since. **The §10 inventory decision is unhurried:
fix it properly rather than fast.** That does not downgrade the severity — the copy is still
wrong on every inventory report and still ships the moment anyone runs one — it changes only the
scheduling.

**Scope note from the same read, which bears on §10 more than this entry does.** Of 43 schedules,
**3 are active**: two `market_snapshot` and one `new_listings_gallery`. That matches exactly the
two report types Cursor found generating in production since July. Eight report types are
specified; two have a live audience. Worth settling before Workstream C and D spread design effort
evenly across all eight.

---

### D-057 — every inventory email quotes a median price of "varying prices"
**Severity:** WRONG · **Affects:** **every** `inventory` email
**Status:** `fixed` — `fix/d057-inventory-median-price`

`_get_insight_paragraph` (`email/template.py:1522`) sources the price from:

```python
median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
...
price_str = _format_price_clean(median_price) if median_price else "varying prices"
```

`build_inventory_result` (`report_builders.py:489-493`) emits exactly three metrics —
`median_dom`, `months_of_inventory`, `new_this_month` — and **neither price key**.
`_build_email_payload` adds counts and aliases `median_dom → avg_dom`, but no price. So
`median_price` is always `None` and every inventory email renders:

> "…at a median of **varying prices**."

A price clause with no price, in a report whose every listing carries a `list_price` the builder
already reads (it sorts and medians on other fields from the same records). Observed in the same
real-pipeline render that confirmed D-056 above.

Distinct from D-056: D-056 is a sentinel disagreement upstream, this is a metric the builder
never computes. They surface in the same sentence, which is why one render exposes both.

**Fix belongs in `build_inventory_result`** — add `median_list_price` (`_median` over
`l["list_price"]` for the active set, the way `build_new_listings_result:386` already does it) —
not in the email. Guessing a price in the template would be inventing a figure.

> **FIXED as prescribed, and the prescription was right — which I nearly talked myself out of.**
>
> Grepping `price_str` in the template finds five sentences, three of which say *"homes **sold**
> at a median of…"*. Read on their own they say the fix should be a CLOSE price, and that the
> entry's prescription would print asking prices as sale prices. They belong to the
> **market_snapshot** branch. The **inventory** branch says *"{n} **active listings** at a median
> of…"* — an asking price, exactly as prescribed. Reading the branch structure rather than the
> grep hits is what separated them.
>
> **Two things the fix had to get right that the entry does not mention.**
>
> *The population.* The sentence pairs the median with `total_active`, which the email payload
> fills from `counts["Active"]` — `len(active)`, the **date-filtered** set the listings table
> shows, not the months-of-supply numerator. The median is over that same set. A median of one
> population beside a count of another is D-056's mistake with different numbers.
>
> *No `median_close_price`, though this report now has the closed listings to compute one.*
> `_get_insight_paragraph` picks the price by precedence — close, else list — and applies it to
> sentences that disagree about which kind they want. Adding a correct close price here would
> silently turn this report's asking sentence into a sale price. Filed as **D-085**, and pinned
> by a test that fails if the metric is ever added.
>
> **`_median` returns `0.0` for an empty list**, so the first version of this fix published a
> median asking price of zero whenever nothing was priced — D-056's sentinel with a new name.
> Found by the test asserting `is None`. Now `None`, and only `None`, means nothing to report.
> The same expression at `:144` has the same sentinel and is **not** changed here: filed as
> **D-086** rather than widened into silently.
>
> Tests: `apps/worker/tests/test_inventory_median_price.py`, 8 cases.

---

### D-058 — brand fields are interpolated into email HTML with no escaping
**Severity:** WRONG · **Affects:** every scheduled email · **Found during:** P1-B (B2/B4)
**Status:** `fixed` (`fix/template-escaping`)

`email/template.py` contains no `html.escape` and no autoescaping anywhere. Every brand value —
`display_name`, `rep_name`, `rep_title`, `rep_phone`, `rep_email`, `contact_line1/2`, `city` — is
f-string-interpolated straight into markup and into attribute values. All of them are
user-editable (`users` columns via the profile page, `affiliate_branding` via branding settings).

Reproduced through `schedule_email_html`, all four confirmed:

| Field set to | Result in the sent email |
|---|---|
| `rep_name` = `Dana <b>Ortiz</b>` | renders as bold markup, not as text |
| `rep_title` = `Broker</p><a href="https://evil.test">Claim your prize</a><p>` | **renders as a live anchor** |
| `display_name` = `Acme" onmouseover="x` | breaks out of the `alt="…"` attribute |
| `rep_email` = `d@e.test" style="display:none` | breaks out of the `mailto:` href and injects an attribute |

**Not browser XSS** — mail clients strip `<script>`, and there is no session to steal. The real
exposure is a live attacker-authored link inside an email that carries *someone else's* brand:
`_resolve_email_brand` (`tasks.py:439-447`) inherits a parent company's branding into a sub-account's
sends while letting the sub-account override `contact_line1/2`. So a rep under a title company can
place markup into mail that reads as coming from the company.

Scoped out of P1-B deliberately — the fix is an escaping pass over ~100 interpolation sites in one
file, which is its own ticket, not a rider on a links fix. One narrowing did land with B2: the
phone `href` now goes through `_tel_uri`, whose output is digits and `+` only, so that particular
attribute is no longer injectable regardless of what is typed into the field.

**Scope, mapped 2026-09-09 on `fix/template-escaping`** — see the entry's full surface map in that
branch's PR. Short version: the injectable channel is not "brand fields", it is *every untrusted
string reaching the module* — brand (14 keys), listing fields from SimplyRETS (11 keys, external
vendor data), and five top-level arguments (`account_name`, `city`, `preset_display_name`,
`filter_description`, plus AI insight text). All confirmed live by render. Two adjacent findings
came out of the same map and are filed separately: the colour crash on
`fix/brand-color-validation`, and the postal-address schema gap with the fix on this branch.

Also unguarded, same class: `website_url`, `logo_url`, `rep_photo_url` and the vendor's
`hero_photo_url` are `str` with no scheme allowlist, so `javascript:` reaches `href` and `src`
verbatim. Inert in a mail client, but the same brand columns feed the PDF renderer, which is a real
browser.

**Fixed at the boundary, not at the sites.** A single sanitisation block at the top of
`schedule_email_html` cleans the ~30 untrusted inputs; everything below it is safe by
construction. Escaping at the ~460 interpolation sites would have meant ~460 correct judgements
about which of two categories each site is in, and ~50 of them insert HTML fragments this module
built — escaping those renders markup as visible text. The boundary makes that failure mode
structurally impossible rather than avoided by care, and the block carries a comment saying so,
because the next reader will see 460 raw interpolations and no engine and reach for per-site
escaping.

Brand keys are classified into three buckets — text (escaped), URL (scheme-allowlisted), colour
(hex-normalised at the read). **An unrecognised key defaults to escaping**, so a text field added
later is protected the day it appears, and a URL field added later renders visibly broken rather
than silently injectable.

**The PDF surfaces did not need escaping, and adding it would have broken them.** Both
`property_builder.py:336` and `market_builder.py:180` already run Jinja with
`autoescape=select_autoescape(['html','xml','jinja2'])`, the templates are `.jinja2` so it is
active, and there are **zero** `|safe` filters anywhere under `templates/`. Verified by rendering
the same payloads through that exact Environment config. Only the email module, which has no
engine, needed HTML escaping.

**What the PDF surfaces did need is the URL allowlist**, and that is the more serious half.
Autoescape does nothing to a scheme — `href="javascript:…"` survives it intact, confirmed by
render — and a PDF is produced by a real browser, so it is a genuine execution context rather than
the inert one an email client provides. `safe_url()` therefore lives in `property_builder.py`
above all three render surfaces and is applied at the PDF context sites
(`market_builder.py:253,311-315`, `property_builder.py:557-558,654-656`) as well as in the email.

A scheme check alone turned out to be insufficient, which a test caught rather than a review:
`https://cdn.example.test/a.jpg" onerror="alert(1)` passes any scheme test and is a live event
handler. `safe_url` truncates at the first character that cannot legally appear in a URI, which is
lossless for real URLs and leaves a usable prefix.

Tests: `apps/worker/tests/test_email_input_sanitization.py`, 41 cases across all three channels;
27 fail against `52e3d76`.

**Near-miss, recorded because the pattern has now happened twice.** The first version of this fix
scheme-allowlisted `unsubscribe_url` along with every other href. The unsubscribe *sentinel*
(`__TRENDYREPORTS_UNSUBSCRIBE_URL__`) is not a URL, so it was stripped; `send.py` would then have
found nothing to substitute per recipient and aborted at its own guard (`send.py:233`) — **every
send, not only a malicious one.** Caught by `test_unsubscribe_token_roundtrip.py`, whose stub
module mirrors `template.py`'s interface.

That is the second time on this project that a correct-looking security fix would have converted
an injection into an **outage**, after D-059 (where passing a non-hex colour through to "let CSS
decide" was the injection, and rejecting it by raising was the outage). Both were caught, both by
running something rather than by reading. The general shape: **a guard that refuses input is a
guard that can refuse legitimate input**, and on this codebase the legitimate-input path is often
a sentinel or an empty-means-unset convention that no type signature records. Check what the
guard rejects, not only what it accepts.

The scope was also completed on `fix/url-boundary-completeness` — see D-061 for why the per-site
URL guard was replaced with a render-boundary sweep.

---

### D-059 — a non-hex brand colour stopped every email on the account
**Severity:** BROKEN · **Affects:** any account whose stored brand colour is not a hex triple
**Status:** `fixed` (`fix/brand-color-validation`)

`schedule_email_html` called `compute_color_roles(accent_color, dark_bg=primary_color)`
unconditionally, before producing any HTML. That reached `_hex_to_rgb` (`property_builder.py:43`),
which does `int(h[i:i+2], 16)` and raised:

```
ValueError: invalid literal for int() with base 16: 'rr'
```

on the value `red`. The exception propagated out of `schedule_email_html` into
`send_schedule_email` and **the email was never sent**.

**Not an edge case — the most likely input.** `red` is what a person types into a field labelled
"Brand Color". The admin affiliate form binds a *free-text* input to the same state as the colour
picker (`apps/web/app/admin/(dashboard)/affiliates/page.tsx:191`) and posts it verbatim.

**Reachable through five write paths, four of them unvalidated.** Only `account.py:74` had the
pattern; `affiliates.py` (`BrandingInput`), `admin.py` (`UpdateAffiliateBrandingRequest`,
`CreateAffiliateRequest`, `CreateCompanyRequest`) and `company.py` (`UpdateBrandingRequest`, which
writes straight into `affiliate_branding`) all took the colours as a bare `str`. The initial scope
said three paths; a sweep for the model definitions found five.

**Interaction with D-055 and D-033.** This is the *second* defect found on the same failure path:
raise inside `schedule_email_html` → propagate through `send_schedule_email` → email never sent,
and with `RESEND_API_KEY` unset (D-033) no failure notification fires. The account silently and
permanently stops delivering from one settings save, and the owner learns of it when a client asks
why the reports stopped. That is a plausible churn mechanism, and the shape recurring twice on one
path is the argument for fixing D-033.

**Fixed in two layers**, because closing the write paths does not help a row that is already bad:

1. `normalize_hex_color()` in `property_builder.py`, used by `_hex_to_rgb` and at the top of
   `compute_color_roles`, so all four call sites (email, market PDF, property PDF) stop raising.
   Both arguments are normalised so `theme_color` agrees with the roles derived from it — coercing
   only the derived values would echo the bad input straight back into a `style` attribute.
2. `email/template.py:1971-1972` normalises the two brand colours at the read, not merely defaults
   them with `or`. These values are interpolated into ~48 `style="…"` attributes as well as being
   parsed as hex, so a permissive guard would have traded the crash for a CSS-injection —
   `red; background: url(https://evil.test/t.gif)` is a tracking pixel and `#fff" onload="…`
   breaks out of the attribute entirely. Both are asserted absent from the output.

Plus the five request models now carry the `account.py` pattern, with a `mode="before"` validator
mapping an emptied field to `None` so clearing a colour still means "unset" rather than 422.

**Answered 2026-09-09: a fix, not an incident.** All 11 rows in `affiliate_branding` hold valid
hex (9 share `#03374f`/`#ff6600`; two accounts diverge). No account has been silently unable to
send. **Latent, and now closed before it fired.**

Two schema corrections came back with that read and are worth carrying: `affiliate_branding` keys
on `account_id` and has **no `id` column**, and `secondary_color` is not on that table — it lives
on `accounts`. `accounts.secondary_color` was therefore checked separately rather than assumed
from the table name: it is written only by `account.py:220-221`, guarded by `BrandingPatch`
(`account.py:75`) which already carried the hex pattern, and by `invite_service.py:110-112`, which
writes the hardcoded literals `#4F46E5`/`#1a1a1a`. Enumerated by grepping every
`UPDATE accounts` / `INSERT INTO accounts` in the repo. **Covered.**

`reports.py`'s per-request `ReportCreate.accent_color` was the one remaining unvalidated path
reaching `compute_color_roles`; it now carries the same pattern
(`fix/url-boundary-completeness`).

The 32 failed `schedule_runs` carry no `ValueError` from `compute_color_roles` — but see **D-061**:
that table cannot record this class of failure at all, so its silence is not evidence.

Tests: `apps/worker/tests/test_brand_color_validation.py`, 53 cases; 41 fail against `52e3d76`.

---

### D-060 — no postal-address column exists anywhere in the schema
**Severity:** WRONG · **Affects:** every commercial email the product sends · **Found during:** P1-B (B5)
**Status:** `fixed` (`fix/postal-address`) — **every send is compliant on merge; the migration adds the per-account override**

> **CLOSED 2026-09-17.** All three things this was gated on arrived: the address (supplied, never
> guessed), somewhere to store per-account overrides (`0055`), and the resolution rule.
>
> **The attribution is the design, and it is why this was not a one-line `or`.** The footer line
> reads `<name> • <address>`, so a naive fallback prints the AFFILIATE'S brand beside
> TRENDYREPORTS' address — an affirmative statement that their business is somewhere it is not.
> That is exactly what the original slot's TODO warned about, arriving through the fallback
> instead of through a guess. So the label travels with the value:
>
> | | |
> |---|---|
> | account set its own | `<their brand> • <their address>` |
> | falling back | `Sent by TrendyReports • <platform address>` |
>
> Both satisfy the statute, which requires the address of the sender **or of the person who
> initiated the message** — and on the fallback path the initiator is TrendyReports, which is what
> the line then says. Neither claims an address for a business that does not have it.
>
> **Compliant before the migration runs, not after.** No account has an override today and nothing
> writes the column yet, so every email takes the fallback path — which needs no schema at all.
> `0055` adds the ability to override, which is the non-urgent half. **Applied to production 2026-09-21** (56 applied / 0 pending; `information_schema` confirms `text`, nullable, no default). Nothing in
> CI or the worker runs migrations.
>
> **Verified by rendering all eight report emails**, twice each — with an override and without —
> checking four things per type: the address is present, the account's own one wins when set, the
> platform address never wears the account's brand, and an override does not print both. The
> naive-`or` regression was applied deliberately and is caught.
>
> **The value was already in the repository.** G3 put `440 Rte. 66, Glendora, CA 91740` on the
> terms and privacy pages on **2026-08-27**, while this entry sat blocked on "the address itself".
> Nothing needed doing for G3, and a test now asserts all three surfaces agree — they are edited by
> different people at different times, and two of them disagreeing is what a title company finds
> during vendor diligence.
>
> **Not built: the settings surface.** Filed as **D-079**. The default alone makes every send
> compliant, which was the urgent half.
>
> **FOLLOW-UP, same day (`fix/postal-conspicuous`): the line was legible only in principle.** It
> inherited the styling of the decoration it sits between — 10px `#9ca3af`, identical to the
> unsubscribe link. Measured against the `#f8f9fa` footer that is a contrast ratio of **2.41:1**;
> WCAG AA asks 4.5:1 for normal text and 3.0:1 even for large text, and 10px is not large text. It
> failed both.
>
> The statute's own wording is *"clearly and conspicuously"*. Present in the HTML and unreadable in
> the client satisfies the letter and not the point — which is this project's recurring shape
> arriving one more time, on the line added to fix an instance of it. Now `#6b7280` (4.59:1, and
> already the wordmark colour in that same block, so not a new colour) at 11px. Still smaller than
> body text; no longer the smallest thing on the page.
>
> The contrast ratio is asserted in the test, with the helper checked against known values so the
> assertion is not circular. Restoring the old styling fails exactly one test.

CAN-SPAM (15 U.S.C. §7704(a)(5)) requires the sender's valid physical postal address in every
commercial email. There is nowhere to put one: no address column on `accounts`, none on
`affiliate_branding`, none anywhere in `db/migrations/`. Verified by grepping every migration for
an address column — the only hits are `property_address` on report tables, which is the *subject*
of a report, not the sender.

B5 was ticketed as "add the postal address to the footer" and landed as a dark slot
(`email/template.py`, `postal_address_html`, PR #49) because the value was gated on a business
decision. The gate is larger than the value:

1. **storage** — a column, a migration, and the resolver reading it into the brand dict.
2. **per-account, not global.** Sends are white-labelled: `_resolve_email_brand` puts an
   affiliate's or a company's identity on the message, so the address of record is *that sender's*.
   A single constant would put the wrong company's address on most mail.
3. **a settings surface** so accounts can enter and maintain their own.

**This reframes open decision 09.** It was recorded as "what is Jerry's address"; the answerable
question first is "where would any address live." The slot stays dark until all three exist —
`brand["postal_address"]` renders the line the moment anything populates it, and both states are
covered by tests.

---

### D-061 — a crash in the email block leaves the schedule run stuck at `queued`
**Severity:** WRONG · **Affects:** sends that raise inside the email block · **Found during:** the D-059 production read
**Status:** `fixed` (`fix/schedule-run-lifecycle`)

*(Filed as "D-061a" in the brief. Numbered plainly because the status parser and the contiguity
check key on `D-\d{3}`; a letter suffix breaks both.)*

`tasks.py` wraps the scheduled-email block in `try:` (1260) … `except Exception as email_error:`
(1308). The handler writes an `email_log` row carrying the error. **It does not touch
`schedule_runs`** — that `UPDATE` sits inside the try body (1289-1302), after the send. A raise
skips it and the run stays `queued`. Confirmed by walking the function's AST:

```
try line 1260 .. except line 1308
  handler writes schedule_runs : False
  handler writes email_log     : True
  TRY BODY writes schedule_runs: True
```

**Severity corrected down from BROKEN.** The first writeup implied crashes generally go
unrecorded. They do not: `tasks.py:1395`, in the *outer* handler, writes
`schedule_runs.status='failed'` keyed on `report_run_id`, so any crash outside the email block is
recorded correctly. Only the email block swallows, because its own handler catches before the
outer one sees anything. That is a narrower defect than first stated.

**A second bug in the same statement, and this one explains the accumulation.** The three writers
do not agree on how they find the row:

| Writer | Keys on |
|---|---|
| `tasks.py:874` (`skipped_limit`) | `report_run_id` ✅ |
| `tasks.py:1395` (`failed`) | `report_run_id` ✅ |
| `tasks.py:1289` (`completed`/`failed_email`) | `schedule_id` + `status='queued'` + `ORDER BY created_at DESC LIMIT 1` ⚠️ |

The third updates *the newest queued row for the schedule*, not the row for the run that is
finishing. So once a row is stranded, no later run ever reclaims it — a subsequent success updates
its own (newer) row and leaves the old one queued forever. **That is the "recovers and re-stalls"
pattern**: the schedule works again, and the stranded rows simply accumulate.

Fix: the `:1289` writer now keys on `report_run_id` like the other two, and the email handler
writes `failed_email` with the error before returning. **Production confirms the accumulation
mechanism was the larger half: 35 of the 57 stranded rows are this defect over work that had
already completed** — 27 with a finished report and a PDF, 8 whose generation failed correctly and
whose run status simply never followed.

---

### D-062 — schedule runs are stranded at `queued` in bursts, with no timeout and no record
**Severity:** BROKEN · **Affects:** 58 scheduled reports across ten months, including a live schedule
**Status:** `fixed` (`fix/acks-late`) — **right fix, wrong stated mechanism; residual gap is D-068**

*(Filed as "D-061b" in the brief.)* 58 rows sit at `status='queued'` in five bursts — 26 in a
single ticker pass on 2026-04-12 spanning 25 seconds, 17 across a week in Nov 2025, 5 each in Dec,
Jan and Feb. Every row joins a real schedule. Zero are inventory, which independently confirms
D-056 has never run on a schedule. **58 scheduled reports the system was told to send and did not.**

**First, a correction to how this data has been read — by both of us.**
`schedule_runs.started_at` is **never written anywhere in the codebase.** It is declared
(`0006_schedules.sql:45`), read by the API (`schedules.py:734`), and used as a predicate
(`tasks.py:1298`) — and never assigned, by the ticker, the worker or the API. Verified by grepping
every `.py`, `.sql`, `.ts` and `.tsx` in the repo.

So `WHERE status='queued' AND started_at IS NULL` selects on status alone; the second clause is
true of every row that has ever existed. **"Enqueued and never picked up" is not established by
this data.** What is established is narrower: 58 rows never advanced past `queued`. That is
consistent with the consumer never draining the queue *and* with several outcomes where the task
ran fine.

**The four ways a row is stranded, and how to tell them apart.** The `schedule_runs` row carries
`report_run_id`, a FK to `report_generations` (`schedules_tick.py:416`), and *that* table does get
a real lifecycle — `processing` at `tasks.py:839`, `completed` at `:1253`, `failed` at `:1389`. One
join separates every hypothesis, with no log retention required:

| `report_generations.status` | What happened |
|---|---|
| `queued` | the worker never consumed the task — the consumer hypothesis |
| `processing` | consumed, then killed mid-flight; no handler ran |
| `completed`, `pdf_url` null | ran fine, but `if schedule_id and pdf_url:` (`:1259`) was false, so the **entire email block was skipped — no email, no error, no trace** |
| `completed`, `pdf_url` set | reached the email block and it raised — D-061 |

```sql
SELECT r.status AS run_status, g.status AS gen_status,
       (g.pdf_url IS NULL) AS no_pdf, COUNT(*), MIN(r.created_at), MAX(r.created_at)
FROM schedule_runs r JOIN report_generations g ON g.id = r.report_run_id
WHERE r.status = 'queued'
GROUP BY 1,2,3 ORDER BY 4 DESC;
```

**The strongest hypothesis from config, not from logs.** `app.py:35-52` sets no
`task_acks_late`, so Celery's default of **`acks_late=False`** applies: a task is acknowledged the
moment a worker *receives* it, before it executes. ~~With the default prefetch multiplier of 4, a
worker holds up to 4×concurrency tasks already acked and not yet run. **A restart — a deploy, an
OOM, a platform recycle — discards every one of them silently: no retry, no error, no record.**
Twenty-six tasks lost in a single 25-second pass is precisely that shape, and it is not
twenty-six independent crashes.~~ `task_time_limit: 300` compounds it: a hard kill at five minutes
leaves no handler to run, stranding `report_generations` at `processing`.

> **CORRECTION, 2026-09-14, by measurement.** The struck sentences are wrong, and the same claim
> was repeated into `schedules_tick.py:496`, `test_delivery_idempotency.py` and PR #61. Celery's
> default acknowledges a message when a pool child **starts executing** it, not when the worker
> receives it. Messages sitting in the prefetch buffer are unacknowledged in **both** modes, and
> Redis hands them back either way. Verified by running a worker against a real broker and killing
> it mid-burst of six tasks: `acks_late` off, **five of six** completed; on, **six of six**. The
> four prefetched ones came back in both runs. The single difference is the task that was
> **running**.
>
> That does not change the fix — it makes it more precise. The stranded rows this entry is about
> are the 18 at `report_generations.status='processing'`, i.e. tasks that were *executing* when
> something killed the worker, which is exactly and only what `acks_late` recovers. It does change
> the reading of "26 in one 25-second pass": that burst cannot be one restart discarding a prefetch
> buffer, because a prefetch buffer is not discarded. The join already said as much — only **3** of
> the 57 were never consumed — so the burst is 26 rows *enqueued* together, not 26 *lost* together.

This is **not** a broker-enqueue failure. `enqueue_report` commits `report_generations` and calls
`send_task` *before* the caller inserts `schedule_runs` (`schedules_tick.py:410-419`), all inside
the per-schedule `try`. A `send_task` raise would leave an orphan `report_generations` row and
**no** `schedule_runs` row at all — so the existence of 58 stranded `schedule_runs` rows is
evidence *against* tasks being lost at enqueue.

**Whatever the cause, the missing safety net is the same and is worth building regardless:** a run
enqueued and not terminal within a window must be marked `failed` with "never picked up".
Indefinite silent `queued` is D-033's shape a third time — D-033 is "the notification does not
fire", D-061 is "the failure is not written down", this is "nothing ever notices". Two further
things belong with it: `started_at` should actually be set when the task begins, so the staleness
sweep has something honest to measure and `started_at IS NULL` stops being a predicate that means
nothing; and `acks_late` should be reconsidered, since a report task is idempotent enough to retry.

**Investigation resolved 2026-09-09 by the `report_generations` join. 57 rows, four causes:**

| `report_generations` | rows | What happened |
|---|---|---|
| `completed` + pdf | **27** | work succeeded; only the status write was lost → **D-061**, not this |
| `processing`, no pdf | **18** | consumed, killed mid-flight, no handler ran → **the real delivery loss** |
| `failed`, no pdf | **8** | generation failed correctly; run status never followed → **D-061** |
| `queued`, no pdf | **3** | never consumed |
| *no generation row* | **1** | dangling `report_run_id` |

**So 35 of 57 were a status-write bug over completed work, and 18 are genuine losses** — 18
reports a schedule said to send that were never made. That reorders the severity: the alarming
number is 18, not 58, and the accumulation is D-061's.

**The dangling row does not weaken the enqueue argument.** `schedule_runs.report_run_id` has **no
foreign key** — `0006_schedules.sql:42` declares it as a bare `UUID` with a comment pointing at
`report_generations.id`. So a dangling value violates nothing, and the likeliest cause is that the
generation row was deleted while the run row survived: `schedule_runs` cascades on `schedules`,
not on `report_generations`. Adding the FK is worth doing; one row does not justify guessing
further.

**THE `acks_late` BLOCKER IS NOW CLEARED** (`fix/delivery-idempotency`, 2026-09-14). A delivery
idempotency guard sits at `_send_and_log_report_email`: a send is refused when `email_log` already
holds a `sent` row for the `report_run_id`, or a `sending` row inside a 10-minute window. The
refusal is recorded as its own `email_log` row (`status='duplicate_suppressed'`) rather than only
logged — a silent refusal would have been the seventh instance of this project's recurring shape.

Scoped to **delivery, not the task**: rendering twice is wasteful and harmless (same R2 key, same
`report_generations` row, and `check_usage_limit` excludes scheduled runs), while sending twice
cannot be taken back. A test asserts the guard did not leak into `generate_report`.

Deliberately does **not** block on `failed` (a retry is exactly what that is for), on `suppressed`
(nothing was delivered), or on a `sending` row older than the window — the last because blocking
forever on debris from a crashed process would mean one crash permanently barred an account's
reports, which is §0.6's guard trap. The check also **fails open**: if it cannot run, the send
proceeds, because withholding a scheduled report on a database hiccup is worse than a rare
duplicate.

**So the remaining question for the 18 is now a decision, not a blocker.** Timeouts were ruled out
by the timing data (p99 41s against a 300s limit), which leaves worker restarts — and `acks_late`
is the fix for exactly that. It can be enabled once someone accepts the trade it carries.

**ENABLED 2026-09-14 (`fix/acks-late`).** `task_acks_late: True` in `app.py`, with the reasoning
and the measurements in the comment beside it rather than only here. Four things were checked by
running Celery 5.6 against a real Redis broker, not by reading its documentation:

| Question | Measured |
|---|---|
| Does it recover lost work? | worker SIGKILLed mid-burst: **5/6** completed with acks eager, **6/6** with acks late |
| Should `worker_prefetch_multiplier` change with it? | **No.** The worker held exactly 4 (= multiplier 4 × concurrency 1) in both modes, and all four came back in both. The batch-on-restart concern is not caused by this setting. Left unset. |
| Does the 300s limit become a redelivery loop? | **No**, because `task_acks_on_failure_or_timeout` defaults to **True**, so a task killed at the limit is still acknowledged. With that default: **1** execution. With it flipped to False: **16 executions in 50 seconds.** |
| Does it cover every way a task dies? | **No.** Kill the pool child alone and the surviving parent acknowledges the message: **0 of 1** completed even with acks late. → **D-068** |

**The loop, if someone ever does flip that setting, would not be caught by the idempotency guard.**
`generate_report` renders *before* it sends, so a task killed at 300s never reaches the send, never
writes an `email_log` row, and `_already_delivered` has nothing to match on. It would spin and
re-render, not duplicate. Two invariants in `apps/worker/tests/test_acks_late.py` guard that line
and the guard's continued existence; neither asserts `task_acks_late is True`, which would only
restate `app.py`.

**Recovery is not immediate.** On a hard kill nothing restores the message; Redis returns it only
after the broker visibility timeout, measured from delivery, and `broker_transport_options` is
unset — kombu's default is 3600s. → **D-070**

The original blocker, retained for the record:

**`acks_late` is now load-bearing rather than speculative, and must not be enabled yet.**
`generate_report` is **not idempotent for email**: `run_report` sets `status='processing'`
unconditionally (`tasks.py:837`) with no check for an already-completed run, so a retry
re-renders and **re-sends**. Given 27 rows already show a completed generation with a PDF, a
retry that regenerates and re-sends is worse than the loss it is meant to prevent. Usage counting
is safe — `check_usage_limit` counts `report_generations` rows and excludes any with a
`schedule_runs` row, and a retry reuses the same row — so the blocker is delivery only. **Enabling
`acks_late` requires an idempotency guard first** (return early when the run is already
`completed`, or check `email_log` for a `sent` row against this `report_run_id`).

**Whether this is a timeout or a restart is answerable from data already stored, not from logs.**
`report_generations.processing_time_ms` is written on every completed run (`tasks.py:1253`). If p99
approaches `task_time_limit` (300 000 ms), these are timeouts — and `acks_late` would then retry
into the same timeout forever, turning 18 losses into an infinite loop:

```sql
SELECT report_type, COUNT(*),
       ROUND(AVG(processing_time_ms))                                            AS avg_ms,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time_ms)          AS p95_ms,
       PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY processing_time_ms)          AS p99_ms,
       MAX(processing_time_ms)                                                   AS max_ms
FROM report_generations
WHERE status = 'completed' AND processing_time_ms IS NOT NULL
GROUP BY report_type ORDER BY p99_ms DESC;
```

**Fixed here — the safety net, which is worth building whichever cause it is:**
`sweep_stale_runs()` runs on every ticker pass and marks any run past
`STALE_RUN_MINUTES` (30, comfortably clear of the 300 s task limit) as `failed`, distinguishing
"never picked up" from "died while running" via `started_at` — which is now **actually written**
(`tasks.py`, persist_status). A sweep is the only thing that can catch this class, because by
definition the process that would have reported it is gone.

~~**Still open:** the cause of the 18. The timing query above and the `acks_late` decision both
remain.~~ The timing query came back (p99 41s), which ruled out timeouts, and the `acks_late`
decision was taken above. Worker logs for 2026-04-12 09:00-09:01 UTC would confirm the cause
directly but are five months back, beyond default retention — so the cause of the 18 is
**inferred from the `report_generations` join plus the timing data**, not observed. Flagged rather
than assumed: the fix addresses the only mechanism left standing, which is not the same as having
watched it happen.

**Backfill proposed, not run:** `scripts/reconcile_stranded_schedule_runs.sql`. It preserves real
timestamps for the 27 (stamping `NOW()` would make ten months of history look like it finished on
one day) and leaves the dangling row untouched. It also flags a trap inside the benign bucket:
`completed` means the *report* completed, not that the email was delivered — any of the 27 with no
`email_log` row is a report that was built and never sent.

---

### D-063 — a falsy `pdf_url` skips the whole email block silently
**Severity:** WRONG · **Affects:** any scheduled run that completes without a PDF
**Status:** `fixed` (`fix/pdf-missing-explicit`) — **guard added; the case was never reachable**

`tasks.py:1259` gates the entire scheduled-email block on `if schedule_id and pdf_url:`. When PDF
generation returns nothing but the run otherwise completes, the block is skipped in its entirety:
no email is sent, no exception is raised, nothing is logged, and — before D-061's fix — the run
stayed at `queued` with no trace anywhere.

**Latent, filed anyway.** It does not appear in the current distribution: all 27 `completed` rows
carry a PDF. But it is reachable by construction, and it is the **fourth instance of this shape**
on this path — D-033 (the notification does not fire), D-061 (the failure is not written down),
D-062 (nothing ever notices), and now this (the work is skipped without anyone deciding to skip
it). The pattern is a success-path-only design: every record of what happened is written by code
that only runs when things go right.

D-061's fix does not close this — the run now reaches a terminal status via the sweep at worst,
but a silently unsent report still reads as a healthy `completed` run. The fix is to make the
missing PDF an explicit outcome: log it, and record the run as `failed` with a reason rather than
falling through a truthiness check.

**Fixed — and the reachability is narrower than this entry first claimed, which is worth stating
plainly rather than letting the fix imply a live bug was closed.**

`pdf_url` is bound in exactly two places inside `generate_report`: `None` at initialisation
(`tasks.py:923`) and the result of `upload_to_r2` at `:1355`. That function
(`utils/r2.py:29`) returns a public URL, a presigned URL, or a local dev stub, and **raises** on
failure — it has **no path that returns `None` or `""`**. So if control reaches the guard,
`pdf_url` is truthy; a failed upload raises instead, lands in the outer handler, and is recorded
as `failed` correctly. **The case is not reachable today.**

Per §0.5 — *do not fix a bug you cannot see* — the honest position is that this is a **latent
trap, not a live defect**. It is guarded anyway because the distance to reachable is one plausible
refactor: *"return None instead of raising so one bad upload doesn't kill the whole run"* is a
change someone makes deliberately, and it would convert this into silent non-delivery the same
day, with nothing in any table to show for it.

The guard now logs at `error` and records the run as `failed` with a reason. **No behavioural C4
differential is claimed** — the tests assert the guard exists and that the normal send path is
still reachable, which is all that can honestly be asserted about an unreachable branch.

---

### D-064 — a missing schedule row skips the send with no email, no error and no record
**Severity:** WRONG · **Affects:** bookkeeping for 20 runs, Dec 2025 – Apr 2026 · **LOSS COUNT: ZERO**
**Status:** `fixed` (`fix/email-log-commit`, D-065) — **all 20 emails arrived; the proof below is refuted by the mailbox**

> ## ANSWERED 2026-09-14 FROM THE MAILBOX. THE LOSS COUNT IS ZERO.
>
> **All 20 were delivered.** Jerry checked `gerardoh@gmail.com`: twenty reports, present. The
> transaction theory in the warning box below is confirmed — the send succeeded and the
> `email_log` write was rolled back. This was never twenty undelivered reports; it was twenty
> runs whose bookkeeping was lost.
>
> **And that refutes the proof by elimination further down this entry, not just its severity.**
> That table concluded `_send_and_log_report_email` was *never called*, on the strength of one
> premise: *"if it had been called, a row would exist."* The emails exist. So it was called, the
> row was written, and the transaction that held it rolled back. The premise was itself an
> inference from a missing row — **the named trap, a fourth time, inside the very entry that
> names it.** The elimination table is left standing below with this correction attached rather
> than deleted, because the reasoning is the artefact worth keeping.
>
> `schedule_row` being falsy at `tasks.py:1290` is therefore **not** established. It remains a
> real hole in the guard — a `print()` and a fall-through — but nothing now says it ever fired.
>
> **Fixed by D-065**, which is what closes the mechanism: an `email_log` row is written and
> committed on its own connection *before* the provider call, so a process that dies between the
> send and the commit now leaves evidence instead of a gap. Nothing further is needed here.
>
> **One thing the answer opened, which is not this defect.** The emails arrived on **different
> dates** from the runs that produced them, and timezone does not explain it: these runs are
> 09:00 and 14:00 UTC, which are 01:00 and 06:00 Pacific on the *same* calendar day. A real gap
> between enqueue and delivery has a mechanism, it is live today, and it is **D-070** — prefetched
> messages stranded in Redis's `unacked` hash until an arbitrary later worker start. The query
> that measures it is on that entry.
>
> **Downgraded from BROKEN, and the title corrected.** Two things changed the reading. The
> schedule has run **21 consecutive Mondays, 2026-04-20 → 2026-09-07, all `completed` + PDF +
> `email_log.status = sent`.** Nothing has failed on this path in five months. And the RLS
> hypothesis this entry originally named — see below — is **dead**. What remains is a real defect
> in the guard, with an unexplained trigger that has not fired since. It returns to BROKEN the day
> it recurs.
>
> ### ⚠️ THE LOSS COUNT IS ZERO — CONFIRMED. This box called it before the mailbox did.
>
> The block runs `autocommit=False` (`tasks.py:1279`) and commits only at `:1308`. The
> `INSERT INTO email_log` runs on **the same cursor, inside that same uncommitted transaction**.
> A process that died between the SendGrid call and the commit loses **the record, not the
> delivery** — the message was already handed to the provider.
>
> So *"20 reports never delivered"* may be *"20 runs whose bookkeeping was rolled back"*, and
> those emails may have arrived normally. It also fits the batch shape better than anything else
> proposed: one restart mid-pass loses every in-flight transaction at once, with no account
> scoping required.
>
> ~~**This is answerable from a mailbox, not a database.**~~ **It was, and it was answered.**
> Every one of the 20 went to `gerardoh@gmail.com` — market-snapshot emails on 2025-12-29,
> 2026-01-05, 2026-02-05 and 2026-04-12, at 09:00 or 14:00 UTC. **All twenty present.** Purely a
> bookkeeping defect, as this box predicted. The test was cheap, decisive, and answerable by
> nothing in the repository — worth remembering the next time a question looks like it needs more
> code reading.
>
> ### THE NAMED TRAP — third instance in this investigation
>
> **A missing row proves a missing WRITE, not a missing ACTION.**
>
> | # | The row that wasn't there | What it was read as | What it actually meant |
> |---|---|---|---|
> | 1 | `schedule_runs.started_at` NULL | "never picked up" | the column is **assigned by nothing** — the predicate matched every row that ever existed and read like a guard |
> | 2 | no `failed` rows in eight months | "nothing has broken" | the failure path **cannot write** to that table (D-061) |
> | 3 | no `email_log` row | "no email was sent" | the write is **inside an uncommitted transaction** and can be rolled back after the send |
> | 4 | no `email_log` row | "the send function was never called" (the elimination table below) | same write, same rollback — **this entry fell into its own trap while documenting it** |
>
> Each time, absence of evidence was read as evidence of absence, and each time the correction came
> from asking *what writes this row, and when* rather than from looking harder at the rows. That
> question is the check; run it before drawing a conclusion from a row that is not there.

20 runs have a **completed generation with a PDF** and **no `email_log` row at all**, in four
batches of exactly five: 2025-12-29, 2026-01-05, 2026-02-05, 2026-04-12. Three of the four start
at 14:00 or 09:00 on the hour; each spans under 20 seconds. Five consecutive schedules in one
ticker pass, four separate times. **The report was built and nobody was sent it.**

This is *not* the 2026-04-12 worker restart (that is D-062, and it produced no PDF). It recurs.

**Proved to one line, by elimination rather than by guessing.** Only one path produces that exact
signature — completed generation, `pdf_url` present, no `email_log` row, no status update:

| Candidate path | Ruled out because |
|---|---|
| `if schedule_id and pdf_url:` false (`tasks.py:1275`) — this is D-063 | `schedule_id` is *always* present: `enqueue_report` puts it in `params` unconditionally (`schedules_tick.py`) and the task reads it from there. `pdf_url` is present in all 20 rows. **The guard passes.** |
| the send returned any status at all | `_send_and_log_report_email` (`tasks.py:598-649`) has **one return, at the end**, and its `INSERT INTO email_log` at `:634` is unconditional — every early return inside `send_schedule_email` (no pdf_url, all recipients suppressed) still comes back through it. If it had been called, a row would exist. |
| anything raised inside the block | `except email_error` (`:1326`) inserts an `email_log` row carrying the traceback. A row would exist. |

⇒ `_send_and_log_report_email` was **never called** and nothing raised ⇒ **`schedule_row` was
falsy at `tasks.py:1290`**, which does nothing but `print()` a warning and fall through. No email,
no exception, no `email_log`, and — before D-061's fix — no status update either.

**And the schedule was not deleted.** `schedule_runs.schedule_id` is
`REFERENCES schedules(id) ON DELETE CASCADE` (`0006_schedules.sql:41`), so deleting a schedule
takes its run rows with it. **These run rows exist, therefore the schedules existed.** The row was
*invisible*, not absent.

**The RLS hypothesis was wrong. Recorded because it was tested and killed, not quietly dropped.**
The account ids **match**, and the same account both succeeded and failed — so visibility was not
gated on `app.current_account_id`. The schedule-state hypothesis is dead too: 12 of the 13
schedules involved were deactivated in **May**, months *after* their failures, and the 13th was
never deactivated at all. Neither explains the batches.

The reasoning below is kept in full because the **elimination to `tasks.py:1290` is still sound**
— it rules out paths by what they would have written, not by what caused them — and it is the map
if this ever returns. Only the mechanism named at the end was wrong:

**The hypothesis was row-level security.** `schedules` has RLS enabled with

```sql
USING (account_id = current_setting('app.current_account_id', true)::uuid
       OR current_setting('app.current_user_role', true) = 'ADMIN')
```

(`0025_admin_rls_bypass.sql:23`), and the block sets that GUC from the task's `account_id`
argument one statement earlier (`tasks.py:1281`). When the setting is absent or does not match,
`current_setting(..., true)` returns NULL, `account_id = NULL` evaluates to NULL rather than true,
and **the row silently disappears from the result set.** No error is raised — that is the whole
danger of RLS as a failure mode.

That fit the batch shape, which is why it was persuasive: visibility would be a function of
`account_id` rather than of the individual schedule, so five consecutive rows would be one
account's schedules in one pass. **The data says otherwise.** The batch shape is real and still
unexplained.

**A correction to what these 20 rows prove — and it is the same mistake as `started_at`.**
"No `email_log` row" does **not** establish "no email was sent". The `INSERT INTO email_log` runs
on the *same cursor, inside the same uncommitted transaction* as everything else in that block
(`autocommit=False` at `tasks.py:1279`, `conn.commit()` only at `:1308`). A process that died
between the SendGrid call and that commit loses **the record**, not the delivery — the email was
already handed to the provider. So a third explanation is live, and with RLS and deletion both
dead it is now the strongest: these are runs whose *bookkeeping* was rolled back, some of which
may have been delivered normally. That also fits the batch shape without needing anything
account-scoped: one worker restart mid-pass loses every in-flight transaction at once.

Settling it does not need code — it needs one of the recipients to say whether those reports
arrived. Worth asking before treating 20 as a delivery-loss count.

**No code change caused the recovery.** `git log` across the whole repository for
2026-03-25 → 2026-05-01 returns **zero commits** — not to `tasks.py`, not to `email/`, not
anywhere. `tasks.py` was untouched between 2026-05-15 and this remediation. Whatever changed
around 2026-04-20 was environmental or data-driven, not a deploy. That is a stop condition, and
the investigation stops here.

**What is still unknown: what breaks the match.** Two reads settle it, and both are one query:

```sql
-- 1. Do the account ids agree? A mismatch proves the RLS hypothesis outright.
SELECT r.id, r.created_at, s.account_id AS schedule_account, g.account_id AS run_account,
       (s.account_id = g.account_id) AS ids_match, s.report_type, s.active
FROM schedule_runs r
JOIN report_generations g ON g.id = r.report_run_id
JOIN schedules s         ON s.id = r.schedule_id
LEFT JOIN email_log e    ON e.report_id = r.report_run_id
WHERE g.status = 'completed' AND g.pdf_url IS NOT NULL AND e.id IS NULL
ORDER BY r.created_at;

-- 2. Do the 20 that failed differ structurally from the 7 that sent?
SELECT (e.id IS NULL) AS never_emailed, s.report_type, g.account_id,
       jsonb_array_length(COALESCE(s.recipients, '[]'::jsonb)) AS recipient_count,
       a.plan_slug, a.account_type, COUNT(*)
FROM schedule_runs r
JOIN report_generations g ON g.id = r.report_run_id
JOIN schedules s         ON s.id = r.schedule_id
JOIN accounts a          ON a.id = g.account_id
LEFT JOIN email_log e    ON e.report_id = r.report_run_id
WHERE g.status = 'completed' AND g.pdf_url IS NOT NULL
GROUP BY 1,2,3,4,5,6 ORDER BY 1 DESC, 7 DESC;
```

**Relationship to D-063.** D-063 stays latent: it is the `pdf_url`-falsy branch of the *same*
`if`, and every one of these 20 rows has a PDF. This is a different silent skip on the very next
line — which makes the count **five** instances of the shape, not four (D-033, D-061, D-062,
D-063, D-064). Every record of what happened is written by code that only runs when things go
right, and every guard that fails does so by falling through.

**Not fixed, and no longer urgent.** Five months clean means chasing a ten-month-old trigger has
low return. The guard itself is still wrong and worth fixing whenever this area is next touched: a
missing schedule row on a run that *has* a `schedule_id` is an error, not a no-op, and must be
recorded and reported rather than `print()`ed. The two queries above stay on the entry as the
first move if it recurs.

---

### D-065 — `email_log` cannot be trusted as a delivery record: its write is rollback-able after the send
**Severity:** WRONG · **Affects:** every scheduled send · **Found during:** D-064
**Status:** `fixed` (`fix/email-log-commit`)

The scheduled-email block opens `psycopg.connect(DATABASE_URL, autocommit=False)`
(`tasks.py:1279`) and commits once, at `:1308`. Everything in between — the schedule lookup, the
recipient resolution, the SendGrid call, and the `INSERT INTO email_log` that records its outcome
(`tasks.py:634`) — shares that one transaction.

**So the record of a send that really happened can be undone by a later failure in the same
transaction, or by the process dying before the commit.** The email is already gone: SendGrid
accepted it over the network, which no database rollback can retract. Only the evidence
disappears.

This is a defect independent of D-064's mystery, and it is the reason that mystery **cannot be
settled from data at all**. A delivery log with this property answers "is there a record?" and
never "was it delivered?" — and those are the same answer only when nothing goes wrong, which is
precisely when nobody is asking.

It also silently weakens two things built on top of it:

- the D-064 backfill's own caution (`scripts/reconcile_stranded_schedule_runs.sql`) that "any of
  the 27 with no `email_log` row is a report built and never sent" — which, given this, is not
  sound either;
- any future "did this account receive their reports?" question, which is the exact question a
  customer complaint produces.

**Fix — either, not both:**

1. **Commit the delivery record separately.** Write `email_log` on its own short-lived connection
   or commit it immediately after the provider returns, before the rest of the block continues.
   The row then survives whatever happens next. This is the option that makes the table mean what
   its name says.
2. **Accept the limitation and say so** — rename or document `email_log` as an attempt log rather
   than a delivery record, and stop treating its absence as evidence.

Option 1 has a cost worth stating plainly: a committed row for a send that a later rollback
"undoes" means the log can now record a send whose surrounding run was abandoned. That is the
correct trade — the email really did go out, so a row saying so is true, and a run that was
abandoned is D-061/D-062's problem to record. **The asymmetry matters: a false absence hides a
delivery that happened; a false presence records one that also happened.** Only one of those
misleads.

**Fixed — option 1, and the ordering is the decision.** A `'sending'` row is written and
**committed before** the provider is called, then updated to `sent`/`suppressed`/`failed`
afterwards. Both writes use their own short-lived autocommit connection, so nothing the caller
does later can roll them back.

Neither ordering is free, and the choice is which way to be wrong:

| ordering | failure mode |
|---|---|
| log **after** the send, commit immediately | loses the record if the process dies between the provider returning and the commit — **fails towards silence**, the same failure with a smaller window |
| log **before** the send, update after ✅ | can leave a row saying `'sending'` for an attempt that never reached the provider — **fails towards "we tried and do not know"** |

A row stuck at `'sending'` is legible and actionable; silence is neither. That is the asymmetry
the entry already argued, now applied.

Three details that made this less trivial than it looks:

- **Cardinality had to stay at one row per attempt.** `admin.py:113` and `:197` do `COUNT(*)` on
  this table, so a second row per send would have silently inflated every email metric in the
  admin dashboard. The row is created then *updated*, and the outer failure handler's INSERT is
  now guarded with `WHERE NOT EXISTS (… report_id = …)` so it only fires when the failure happened
  *before* an attempt row existed.
- **A raise from the provider closes the row out before propagating**, so a known failure is
  recorded as `failed` rather than left at `'sending'`.
- `status` is plain `TEXT` with no CHECK (`0027`), so `'sending'` needed no migration — but
  **`0027`'s `COMMENT ON COLUMN` still lists only sent/suppressed/failed/unknown and is now
  incomplete.** Not worth a migration on its own; worth folding into the next one that touches
  this table.

Tests: `apps/worker/tests/test_email_log_durability.py`, 10 cases, 7 failing against `6075879`.
Three of the ten do not read the source at all — they run a fake connection that models the one
behaviour under test (uncommitted writes are invisible and lost on rollback) and demonstrate the
old shape losing the row and the new shape surviving. Those three pass before and after by
design: they establish the baseline the fix is measured against rather than asserting the fix.

**This is what makes D-064 answerable from data next time** rather than from a mailbox.

---

### D-066 — every property report asserted NAR membership on the agent's behalf
**Severity:** WRONG · **Affects:** every property report by an agent who left their title blank
**Status:** `fixed` (`fix/realtor-mark-default`)

`{{ agent.title | default('Realtor®') }}` — and its Python equivalents — printed **Realtor®** on a
report whenever an agent had not set a job title. REALTOR® is a registered collective membership
mark owned by the National Association of REALTORS® and usable only by its members; roughly a
third of licensed US agents are not members, and nothing in this product asks.

So a licensee who skipped one optional field at signup had a claim of NAR membership printed on a
document they hand to clients, under their own name and photo — **a trademark exposure created by
a default value, not by anything they did.** `Real Estate Agent` is accurate for every licensee
and asserts nothing; a member who wants the mark can type it, which is the only way it should ever
appear.

**Ticketed as one line. It was nine, and the first two greps found neither the important ones nor
the last one:**

| Site | Why the first pass missed it |
|---|---|
| `_base/_macros.jinja2:70` | the one that was ticketed |
| 5 theme contact blocks | found by grepping `Realtor` |
| **`property_builder.py:583`** | **Python, and load-bearing** — it supplies the string *before* the template runs, so the Jinja `default()` is dead code on that path. **A template-only fix would have changed nothing while looking like a fix.** |
| `tasks.py:1797` | the CMA path, written `"Realtor\u00ae"` — invisible to a grep for `Realtor` |
| `bold_report.jinja2:848` | found only when a **test** ran after the fix, because it defaults to `'Licensed Real Estate Agent'` — the right construct, a different string, so a grep keyed on the *symptom* could never see it |

The last row is the lesson, and it is the third time on this project: **grep for the construct, not
for the symptom.** The check that runs after the fix finds what the check before it missed.

**And the `property_builder.py` row is a second, sharper method note.** The ticket specified a
template change. That change was real, it edited the right-looking line, it would have produced a
green diff and a closed ticket — and it would have fixed nothing, because the value is supplied
upstream and the Jinja `default()` on that path is dead code. **A fix that edits the correct line
can still be inert if something earlier supplies the value.** The only thing that distinguishes
the two cases is rendering the result. Render to verify; do not read to verify.

**A separate bug in the same expression, found by render.** Jinja's `default(x)` fires only on
*undefined*. `agent.get("title", …)` returns `None` when the key exists holding a null, and
`{{ None | default('…') }}` renders the literal string **"None"** onto a customer-facing PDF. The
final form is `{{ (agent.title or '') | trim | default('Real Estate Agent', true) }}`:

| input | plain `default(x)` | `default(x, true)` | final form |
|---|---|---|---|
| absent | fallback | fallback | fallback |
| `None` | **"None"** | fallback | fallback |
| `""` | `""` beside a bare ` · ` | fallback | fallback |
| `"   "` | spaces | spaces | fallback |
| `"Broker Associate"` | preserved | preserved | preserved |

Filter order is load-bearing and not cosmetic: `trim` *before* `default` **reintroduces** the
`None` leak, because `None | trim` stringifies to `"None"` first. Confirmed by rendering all three
candidate expressions rather than reasoning about them.

Tests: `apps/worker/tests/test_agent_title_default.py`, 10 cases, 9 failing against `main`.

---

### D-067 — the theme cover blocks leak the literal string "None" onto the PDF cover
**Severity:** WRONG · **Affects:** *(as filed)* any property report where `agent.title` is NULL rather than absent
**Status:** `fixed` (`fix/theme-cover-title`) — **the filed defect is unreachable; two others on the same lines were not**

The same `default()` bug as D-066, in the *other* `agent.title` expression — the theme **cover**
block, one per theme, each with its own copy:

| Template | default |
|---|---|
| `classic_report.jinja2:557` | `'Licensed Real Estate Agent'` |
| `bold_report.jinja2:848` | `'Licensed Real Estate Agent'` |
| `elegant_report.jinja2:251` | `'Luxury Property Specialist'` |
| `modern_report.jinja2:331` | `'Real Estate Specialist'` |
| `teal_report.jinja2:1186` | **none at all** — `{{ agent.title }}` bare |

All five use the plain `default()` form (or nothing), so a NULL title renders **"None"** in large
type on the report cover. Teal is worst: no fallback whatsoever.

**Deliberately not fixed with D-066.** None of these asserts the REALTOR® mark, so this is not the
trademark problem — and the per-theme strings look like intentional design voice rather than
accident. Flattening them all to one value inside a PR whose point was to make a *trademark* call
visible would bury a design decision inside a legal one. **The mechanical part** — switching to
`(agent.title or '') | trim | default(<the theme's own string>, true)`, keeping each theme's copy —
is safe and should just be done. **Teal needs a decision**: it has no fallback, so what a
title-less agent should see there is a design question.

> **RESOLVED 2026-09-14 BY RENDERING IT, AND THE HEADLINE IS WRONG.** The templates do say what is
> written above. It cannot happen. `PropertyReportBuilder._build_agent_context` substitutes the
> title **before** the template runs, using `or` — which catches None — so a NULL title arrives at
> the cover as `'Real Estate Agent'`, and the five per-theme `default()` calls are dead code.
>
> This entry was written by reading five template lines. D-066 nearly shipped an inert fix by
> editing only the template; this nearly filed an impossible bug by reading only the template.
> Same trap, opposite direction. §0.6: **render to verify, do not read to verify.**
>
> **Two defects on those same lines were real, and neither is what was filed:**
>
> - **A whitespace-only title renders a blank line in cover-sized type.** `"   "` is truthy, so it
>   passes the `or` untouched. All five themes. Fixed at the load-bearing site:
>   `property_builder.py` now strips before the fallback.
> - **`classic` and `bold` print a dangling separator.** The line is `{{ title }} • {{ license }}`
>   with the bullet outside any condition, and `license` is `""` for any agent with no licence
>   number on file. Those covers read **"Real Estate Agent • "** with nothing after the bullet —
>   not an edge case but the default state of a new account. Fixed by moving the bullet inside an
>   `{% if %}`.
>
>   That one also **masked** the first: the stray bullet made the whitespace case render non-empty,
>   so a "the cover is not blank" assertion passed on classic and bold for the wrong reason.
>
> **Teal is given no invented value.** It has no fallback string of its own and choosing one is a
> design decision; its slot now renders only when there is something to put in it.
>
> **The same construct was hardened in `market_builder.py:318`**, called out rather than done
> quietly: `branding.get("agent_title", "")` returns None on a NULL column. The market templates
> guard with `{% if agent.title %}`, so nothing ever leaked there, but whitespace rendered a blank
> styled footer line. One line, identical shape, and §0.6 rule 4 says to follow the construct
> rather than the symptom.
>
> **What remains is a decision, filed as D-073:** because the Python default wins, every theme
> prints "Real Estate Agent" and the designed per-theme voice has never once rendered.

---

### D-068 — a task whose pool child is killed is still lost, even with `acks_late` on
**Severity:** WRONG · **Affects:** any task the OOM killer reaps, one per occurrence
**Status:** `open`

`acks_late` recovers a task when the **whole worker** dies. It does not recover one when only the
**pool child** dies and the parent survives — an OOM kill of a single child, which is the common
shape on a memory-limited container, because rendering is the memory-hungry part.

Measured against a real broker, `acks_late` already on, one task, child SIGKILLed while the parent
lived: **1 start, 0 completions.** The parent catches `WorkerLostError`, treats it as a task
failure, and acknowledges the message — because `task_acks_on_failure_or_timeout` defaults to
True, the same default that keeps the 300s limit from looping (D-062). The one setting closes the
hole the other opens.

The remedy is `task_reject_on_worker_lost = True`. With it, the same experiment gives **2 starts,
1 completion** — redelivered and finished.

**Not enabled, because the trade is real and is not this ticket's to take.** A task that reliably
exhausts memory redelivers forever rather than failing once, and the delivery guard would not
contain it: an OOM during rendering dies before the send, so no `email_log` row exists for
`_already_delivered` to match on — the same reason the time-limit loop would be uncatchable. A
memory ceiling on the render, or a redelivery counter, should land first or alongside.

Recorded here rather than left as a footnote on D-062 because it is a different mechanism with a
different fix, and because D-062 now reads as closed — this is the part that is not.

---


> **UNVERIFIED IS NOT UNLIKELY, AND THE 2026-09-22 SWEEP DID NOT CHANGE THAT.** This entry was
> carried on its original evidence because confirming it needs the method D-062 needed: a real
> worker, a real broker, and a `kill -9` at the right moment — **not a code read.**
>
> That distinction is the whole of D-062's lesson. "Celery acknowledges a task on receipt, so a
> restart discards prefetched work" was written into four files and a PR body without once being
> run, and running it took under an hour and showed the claim was wrong. A confident reading of
> this code would carry exactly the same risk in either direction.
>
> So: **this stays open at WRONG on the strength of the original observation, and nobody should
> read "not re-verified" as "probably fine."** The experiment is the citation, and it has not been
> performed. Until it is, the honest statement is that we do not know, and the entry's severity
> reflects what was observed rather than what has been confirmed since.

### D-069 — `process_consumer_report` re-sends the SMS and re-spends the credit if it is redelivered
**Severity:** WRONG · **Affects:** consumer lead reports, on any worker death mid-task
**Status:** `fixed` (`fix/consumer-delivery-truth`) — **a redelivery is refused before any provider is called**

`task_acks_late` is a **worker-wide** setting, so enabling it for D-062 changed the failure mode of
every registered task, not just `generate_report`. Five are registered: `ping`, `keep_alive_ping`,
`generate_property_report`, `generate_report` and `process_consumer_report`. The first three have no
irreversible side effect. `generate_report` is guarded (`fix/delivery-idempotency`).
`process_consumer_report` is not.

It sends an SMS through Twilio and then decrements the account's SMS credits
(`tasks.py`, the `delivery_method == 'sms'` branch), or sends through Resend on the email branch.
It sets `consumer_reports.status='processing'` at the top with **no already-sent check**, so a
redelivered run repeats the whole thing. If the worker dies after the provider call and before the
task returns, the consumer gets a second text and the account pays for it twice.

**Reported, not fixed, and not quietly excluded.** Two one-line remedies exist — `@celery.task(...,
acks_late=False)` on this task alone, which restores today's behaviour for it and nothing else, or
a `status='sent'` check before the provider call, which is the same shape as the delivery guard and
is strictly better. Choosing between them is a product call: today this task silently loses the
lead's report when a worker dies, and the choice is between losing it and occasionally duplicating
it. That is the same trade D-062 took the other way, for a different audience.

---

### D-070 — no broker visibility timeout is configured, so a stranded report lands at an arbitrary later time
**Severity:** WRONG · **Affects:** how late a delayed report arrives — **and this is live today, not a consequence of `acks_late`**
**Status:** `fixed` (`chore/agreed-followups`) — **`visibility_timeout = 900`**

`acks_late` (D-062) makes a lost task recoverable. It does not make it prompt. On a graceful
`SIGTERM` the worker restores its unacknowledged messages immediately, so a normal deploy is fine.
On a **hard** kill nothing restores anything, and Redis returns the message only when the broker's
**visibility timeout** elapses — measured from when the message was *delivered*, not from the
crash.

`app.py` sets no `broker_transport_options`, so that timeout is kombu's default of **3600
seconds**. A daily report recovered this way can land an hour late, which for a morning market
report is late enough to be a different product.

**Not tuned here, because the number cuts both ways.** The visibility timeout is also the lease on
a running task: set it below the longest legitimate render and a second worker picks up work the
first worker is still doing, which is a duplicate execution rather than a slow one. p99 is 41s and
the hard limit is 300s, so anything comfortably above 300s is safe on the timing evidence —
600s would cut worst-case recovery by a factor of six with margin over the limit that already
bounds every task. Left as a decision rather than assumed.

> **UPGRADED 2026-09-14 from FRAGILE to WRONG, and the title corrected.** This was filed as a
> property of the recovery `acks_late` introduces. It is not. **The same mechanism is live right
> now, with `acks_late` off**, and it is the only mechanism found that can put a report in
> someone's inbox on a different day from the run that produced it — which is exactly what Jerry's
> mailbox check turned up for D-064.
>
> **Why it does not need `acks_late`.** Celery acknowledges a message when a pool child *starts*
> executing it, so everything a worker has **prefetched but not started** is unacknowledged in
> both modes — measured, 4 held at the default multiplier with concurrency 1. When that worker
> dies, those messages are not lost and they are not returned promptly. They sit in Redis's
> `unacked` hash, invisible to the queue, until some later worker start restores them — and only
> once the visibility timeout has elapsed **since delivery**.
>
> **Restoration is opportunistic, which is the part that makes it arbitrary.** Four runs against a
> real broker, visibility timeout set to 45s so the window is observable:
>
> | Restart | Result |
> |---|---|
> | ~13s after delivery, timeout 10s | restored, ran |
> | inside the window | not restored — correct, the window had not elapsed |
> | a 40s worker lifetime *spanning* the boundary | **not restored** |
> | a later start, messages 92s old | restored immediately, all ran |
>
> So it is not "returned after the timeout". It is "returned at the first worker start that
> happens to check after the timeout". With the production default of **3600s** and a worker that
> restarts on deploys, the gap between a report being enqueued and being sent is bounded by
> nothing in particular. **Days is possible.**
>
> **A prediction this makes, checkable without a mailbox.** `schedule_runs.created_at` and
> `report_generations` are both written by the ticker at *enqueue* time, while the send happens
> when the task finally runs. So a stranded task leaves a measurable gap:
>
> ```sql
> SELECT r.id, r.created_at AS enqueued_at, g.generated_at, g.status,
>        g.processing_time_ms,
>        g.generated_at - r.created_at AS lag
> FROM schedule_runs r
> JOIN report_generations g ON g.id = r.report_run_id
> WHERE r.created_at >= '2025-12-01'
> ORDER BY lag DESC NULLS LAST
> LIMIT 40;
> ```
>
> A lag of seconds is the normal case. A lag of hours or days, with a *normal*
> `processing_time_ms`, is this defect — the task ran fine, just much later than it was asked to.
> That distinction matters: a long `processing_time_ms` would be a slow render, which is a
> different problem.
>
> **What this means for `acks_late`.** It makes enabling it a **smaller** change than it looked,
> not a riskier one. Redelivery is not a new behaviour being introduced; it is an existing one
> being extended from prefetched messages to the running task. Both are governed by this same
> timeout. **Tuning this is now more valuable than it was when it was filed**, because it bounds a
> delay that is already happening rather than one that might.

**RECOMMENDED VALUE: `visibility_timeout = 900` (15 minutes). Not applied** — this is a number
someone should agree to, and the reasoning is short enough to check.

The timeout is two things at once, which is why 3600s is wrong in both directions:

| As a… | Shorter is | Because |
|---|---|---|
| recovery delay | **better** | it is the floor on how late a stranded report can arrive |
| lease on a running task | **worse** | drop below the longest legitimate run and a second worker picks up work the first is still doing — a duplicate execution, not a slow one |

**The lease side has a hard floor and we know it exactly.** No task can outlive
`task_time_limit = 300s`; the hard kill guarantees it. So any value comfortably above 300s cannot
hand live work to a second worker, whatever the p99 does. 900s is 3× that ceiling — the same kind
of margin `STALE_STARTED_MINUTES = 6` already takes against the same limit, and consistent with it.

**The recovery side is no longer symmetric with it, which is what changed.** Before #61, shortening
this traded delay for duplicate-send risk, and that was a real trade. The idempotency guard now
covers the duplicate side: a redelivery of an already-sent report is refused and recorded rather
than delivered. What the guard cannot reach is a task killed *before* the send — it leaves no
`email_log` row to match on — and that case simply re-renders. Re-rendering is wasteful and
harmless, which is the finding the guard's scoping already rested on.

**Why not 600s, which is what this entry said when it was filed.** 900s is preferred on second look
only because the margin is free: the difference between a 10- and a 15-minute worst-case recovery
does not decide whether a daily report is usable, while the extra headroom is real protection
against the one failure here that cannot be undone. **Below 300s would be a mistake at any point**
— that is not tuning, it is removing the guarantee the time limit provides.

```python
"broker_transport_options": {"visibility_timeout": 900},
```

**APPLIED 2026-09-17 (`chore/agreed-followups`).** Set on the worker's Celery app, which is the
consumer — the ticker's separate Celery instance only produces and never holds an unacknowledged
message, so it does not need the option and has not been given it.

`apps/worker/tests/test_acks_late.py` asserts the *relationship* rather than the value: the
visibility timeout must exceed `task_time_limit`. Each number looks reasonable alone and nothing
else connects them, so that is the assertion worth having. Verified against both ways of breaking
it — lowered below the limit, and removed so kombu's 3600s default returns.

---
### D-071 — `generate_report`'s retry policy is unreachable, except through its own failure handler, where it re-sends
**Severity:** WRONG · **Affects:** every scheduled and on-demand market report
**Status:** `fixed` (`fix/retry-policy-honest`) — **decorator removed, perverse path closed; real retries scoped separately**

`generate_report` is decorated `autoretry_for=(Exception,)`, `retry_backoff=True`,
`retry_backoff_max=600`, `max_retries=3` (`tasks.py:1046-1052`). It reads as a resilient task.

**It never retries.** The body is one `try` covering everything, and its `except Exception`
handler **returns a dict** rather than re-raising (`tasks.py:1697-1755`). Nothing escapes, so
`autoretry_for` has nothing to catch. Every failure this task can have is swallowed and reported
as `{"ok": False}`. Three retries with exponential backoff are configured and have, as far as the
code allows, never once happened.

**Except by one route, and that route re-sends.** The handler is not itself guarded: it opens a
new database connection and runs four `UPDATE`s with no `try` around them
(`tasks.py:1699` onward). If that connection fails — which is *likely* precisely when something
has already gone wrong enough to reach the handler — the exception escapes, `autoretry_for`
catches it, and **the entire task re-runs from the top: re-render, re-upload, re-send.**

So the only reachable retry path is the one where the first attempt may already have emailed the
recipient. Since #61 the duplicate-send guard covers it, which is the second thing that guard
turned out to be for.

**This cannot explain a report arriving on a different day** (three retries, backoff capped at
600s — under half an hour end to end). It is a separate defect, found while checking whether one
could. See D-070 for the mechanism that can.

**Two decisions, not one.** Whether the task should retry at all is a real question — a re-render
is cheap and a re-send is now guarded, so retries are safer than they were. But "it retries" and
"it does not retry" are both defensible, and "it retries only when its own error handler breaks"
is not. Either make failures propagate or drop the decorator; do not leave it describing
behaviour the code prevents.

**THE SHAPE, named.** A retry path that opens only when the error handler itself fails is **a
guard that arms exactly when everything else has already gone wrong.** That is the inverse of the
shape this remediation keeps finding. The recurring one is *silent when it works* — correct
behaviour with no trace. This is *active only when nothing else is*: dormant through every
ordinary failure, and live precisely in the conditions least able to survive it.

**FIXED 2026-09-17 (`fix/retry-policy-honest`), taking the "drop the decorator" branch.** Two
changes:

1. **The handler is guarded**, so the perverse route is closed whatever the decorator says. The
   bookkeeping is lifted into `_record_generation_failure` and called inside a `try`; the failure
   notification is guarded at the call site as well. A guard that discarded its exception silently
   would be the same shape again, so each one logs the bookkeeping error *beside the original*.
2. **The retry configuration is removed**, and the reason it is not simply switched on is written
   where the decorator used to be.

**Why "make failures propagate" is not the one-line half of that choice.** The failure bookkeeping
runs on **every attempt**, and it:

| It does this | Under retries that becomes |
|---|---|
| increments `schedules.consecutive_failures`, **auto-pausing at 3** | four attempts at one transient failure pause the schedule |
| writes terminal status to `report_generations` and `schedule_runs` | a run that failed twice and then succeeded is recorded as **failed** |

Both are false negatives in the exact tables D-061 and D-062 exist to make trustworthy. Real
retries want the bookkeeping to distinguish *"this attempt failed"* from *"the task failed"*, and
that is a behaviour change with its own review. **It is worth doing** — a transient SimplyRETS or
PDFShift blip currently costs that day's report outright — and it is not this ticket.

`apps/worker/tests/test_retry_policy.py` carries the coupling: **if `autoretry_for` goes back on
while `_record_generation_failure` still runs unconditionally, the suite fails** and says why.
Verified against that exact regression, not assumed.

**`generate_property_report` is the control.** Same decorator, and its handler ends with a bare
`raise` and the comment "Re-raise to trigger Celery retry". It does retry. One statement of
difference decided which of two tasks got the resilience it advertised — and the one that missed
out is the one that sends email. A test now checks the whole worker package for that disagreement
rather than these two functions, per §0.6 rule 4.

**One line hardened in passing, same construct as #64:** the lifted bookkeeping interpolated
`account_id` into `SET LOCAL app.current_account_id TO '<id>'`. Now `set_config`. Note it passes
`is_local => false` here, unlike the ticker: this connection is `autocommit`, so scoping the
setting to a transaction that does not exist would silently do nothing.

**A test in this file caught its own author.** It exempted `_send_failure_notification` from the
"nothing in the handler may raise" check as self-guarding, and a companion test written to
*verify* that exemption rather than trust it found the function's first three statements sitting
outside its own `try`. The exemption was deleted and the call site guarded instead — cheaper than
being right about another function's internals, and it removes the coupling rather than
documenting it.

---

### D-072 — the ticker dispatches the Celery task before the transaction that records it commits
**Severity:** WRONG · **Affects:** every schedule, on any ticker interruption
**Status:** `fixed` (`fix/enqueue-after-commit`)

In `schedules_tick.py`, the per-schedule block runs in this order:

1. `enqueue_report(...)` — inserts `report_generations` **and calls Celery `send_task`**
2. `INSERT INTO schedule_runs (...)`
3. `UPDATE schedules SET last_run_at, next_run_at, processing_locked_at = NULL`
4. `conn.commit()`

**The task is dispatched at step 1 and the work is recorded at step 4.** Anything that interrupts
steps 2-4 — a failed insert, a lost connection, the ticker process dying — rolls the transaction
back. The Celery message is already in Redis and is not rolled back with it.

Two consequences, both matching shapes this project has already seen:

- **A report is generated and emailed with no `schedule_runs` row at all.** Which is one of the
  signatures D-064 was filed for, arrived at from the other direction.
- **`next_run_at` is not advanced, so the schedule is still due**, and the next tick 60 seconds
  later enqueues it again. Two reports, two emails, one scheduled send. Since #61 the second is
  refused and recorded rather than delivered — but the refusal is a symptom being caught, not the
  cause being fixed.

D-062 reasoned about this ordering already, as *evidence* that tasks were not being lost at
enqueue: "a `send_task` raise would leave an orphan `report_generations` row and no `schedule_runs`
row at all." That is correct and the conclusion stands. What it did not say is that the same
ordering is a defect in its own right, in the other direction — the dispatch surviving a rollback
is as much a problem as the rollback surviving a dispatch.

**The fix is the ordering, not a guard:** commit the bookkeeping first, dispatch second. That
inverts the failure mode to a run row with no task — which the stale-run sweep already catches and
reports, rather than a duplicate email nobody asked for. Worth doing with D-071, since both are
about this task's boundaries rather than its contents.
### D-073 — the per-theme cover titles were designed, and have never rendered
**Severity:** ROUGH · **Affects:** all five property report themes
**Status:** `open` — **needs a design decision, not a fix**

Each theme's cover carries its own fallback for an agent with no title —
`'Luxury Property Specialist'` (elegant), `'Real Estate Specialist'` (modern),
`'Licensed Real Estate Agent'` (classic and bold) — and teal has none. Distinct copy per theme is
plainly deliberate; it is the same kind of voice difference as the typography.

**None of it has ever appeared on a report.** `property_builder.py` substitutes
`'Real Estate Agent'` before the template is reached, so all five themes print the same words.
Established by rendering the production path rather than reading the templates — see D-067.

Two coherent answers, and they are not interchangeable:

1. **The themes should differ.** Move the fallback out of Python so each theme's string reaches the
   page, and decide what teal says. More work, and it means one agent's report reads differently
   depending on the theme they picked — which may or may not be wanted.
2. **The themes should not differ.** Delete the four dead strings so the templates stop describing
   behaviour that does not exist. Cheap, and it removes a trap for the next reader.

`apps/worker/tests/test_theme_cover_title.py` pins the current state: if the per-theme copy ever
becomes reachable, that test fails and points at this decision instead of letting it land quietly.
**Not decided here** — §0.2, this is a product voice call.

**FIXED 2026-09-15 by the ordering, as described.** `enqueue_report` is split in two:

| | |
|---|---|
| `create_report_generation(cur, …)` | takes the **caller's cursor**, so the generation row lives in the same transaction as `schedule_runs` and the `next_run_at` advance. It dispatches nothing. |
| `dispatch_report(run_id, …)` | hands the task to Celery and touches no database. Called only after `conn.commit()`. |

The split matters as much as the order. The old function committed the generation row **on a
connection of its own**, so it survived the caller's rollback independently of the dispatch — two
separate ways for one tick's work to come apart.

**The residual failure mode is inverted into the one that is already handled.** If the process dies
between the commit and the dispatch, the rows are durable at `'queued'` with no task, and
`sweep_stale_runs` marks that `failed` with "never picked up" — the sweep doing exactly the job it
was built for. A dispatch failure is therefore logged loudly and **not raised**: the run is already
committed, and an exception would misreport it as a tick that did nothing.

**One line hardened while moving it.** The old code interpolated `account_id` into
`SET LOCAL app.current_account_id TO '<id>'` as SQL text. Nothing could be smuggled through a uuid
column today, but the parameterised `set_config(…, true)` form costs nothing and does not rely on
that staying true. Same call the delivery guard uses.

**A test of mine failed this defect's own lesson, and it is worth recording.** The first ordering
assertion was *"some `conn.commit()` precedes the dispatch"*. The ticker loop has another commit
several branches earlier, on the usage-limit skip path — so moving the dispatch back above the real
commit left that test **passing**. §0.6 rule seven, in a test written just after rule seven was
written. It was caught by applying the regression and re-running, not by rereading the assertion,
which is the other half of rule four. The assertion now requires a commit *between* recording the
run and dispatching it.

---

### D-074 — the Market Trends gauge may be printing an inflated months-of-supply figure

**Severity:** WRONG · **Affects:** every property report's Market Trends page — **shipping today**
**Status:** `fixed` — `fix/d074-close-date-window`, and **HALF CONFIRMED** against the production feed; see the verdict below

> **THE VERDICT IS HALF CONFIRMED, AND THE PROBE OVERCLAIMED IT.**
>
> What the production run settles: a future `minclosedate` returned **1 of 500** rows where no
> cutoff returned 500. The parameter filters. The one survivor has `closeDate='<absent>'` — a
> Closed record with no close date, leaking through the feed's own filter, which is a
> null-handling leak and not a failure to filter.
>
> What it does **not** settle, and what the probe claimed anyway: section 2b reported *"a 90-day
> window returned 500 of 500 (a real subset)"*. Both numbers are the probe's own `limit=500`.
> **500 of 500 with both sides capped is indistinguishable from the parameter being ignored** —
> and the script's closing paragraph warns about exactly that reading, two sections below where
> its own logic committed it. Fifth instance of the named trap, in the file that names it.
>
> Fixed in the probe: now that `count=true` is confirmed in production, 2b compares
> `X-Total-Count` for the baseline against the 90-day query instead of capped page counts.
> That is the corroboration, and it has not been run yet.
>
> **The fix ships anyway, because it is safe under either answer.** `market_trends.py` now
> sends `minclosedate` (180 days — the window the client-side split actually reads) AND keeps
> the client-side `close_date` split. If the parameter is honoured the second pass is a no-op;
> if it is not, the second pass is what makes the window true. What stays blocked on the
> corroboration is **dropping the client-side filter** or **switching the denominator to a
> count** — hold both.
>
> `minlistdate` is gone. It was a cutoff on the wrong column: a home listed 300 days ago and
> sold last week is a closed sale by every measure that matters, and 210 days excluded it. The
> loss was not random — long-DOM listings are exactly the ones that take that long — so the
> sales rate came out too LOW and months of supply too HIGH, never the other way.
>
> **The absent `closeDate` is handled, and it was already handled.** The split skips
> `cd is None`, so such a row is counted in neither window and does not crash the comparison.
> Now tested rather than read: `test_market_trends_close_window.py`, 7 cases, three regressions
> applied and seen to fail (restore `minlistdate`; count undated closes as in-window; drop the
> client-side split).
>
> **THE SURVEY IS DONE AND `market_trends.py` WAS THE ONLY ONE.** Grepped for the construct
> — every place a list-date-bounded window feeds a closed-sales or sales-rate figure — not
> for the string. Three other Closed queries exist:
>
> | builder | window sent | what actually bounds it |
> |---|---|---|
> | `build_inventory_closed` | `minclosedate` | the API filter, plus a client-side `close_date` pass |
> | `build_market_snapshot_closed` | `mindate`/`maxdate` — **inert** | the client-side `close_date` filter |
> | `build_closed` | `mindate`/`maxdate` — **inert** | the client-side `close_date` filter |
>
> None of them was bounded by list date. `build_inventory_closed` already carries a comment
> naming D-074 as the mistake it is avoiding. **D-074 is complete**, and this is the evidence
> rather than an assumption that one grep was enough.

`market_trends.py` computes months of supply as `active_count / (closed_in_90_days × 30.437/90)`.
The numerator is right. **The denominator may be missing sales.**

To collect closed sales it fetches with `minlistdate = now − 210 days` and then splits client-side
on `close_date`, under this comment:

> *"the critical rule: minlistdate ≠ closeDate. We fetch a wide window and split client-side so
> both periods use the same fetched dataset."*

The premise is that SimplyRETS has no close-date filter. **It does.** Measured against
`api.simplyrets.com`:

| Query | Rows |
|---|---|
| `status=Closed` | 13 |
| `status=Closed&minclosedate=2000-01-01` | 7 |
| `status=Closed&minclosedate=2030-01-01` | **0** |

A filter that returns nothing for a future date and a subset for a past one is a filter that works.

**The consequence, and it runs one way.** A property listed more than 210 days ago and sold last
month is **excluded** from the closed count. Long-DOM listings are exactly the ones that take more
than seven months to sell, so the exclusion is not random — it removes real, recent sales from the
denominator. A smaller denominator means a smaller monthly sales rate, and MOI is inventory divided
by that rate. **MOI comes out too high, never too low.**

**What that means to the person holding the report.** High months-of-supply reads as a slow market:
`_classify_market_condition` turns it into a "buyer's market" badge and narrative copy about
homes taking longer to sell. A seller deciding how to price is being shown a market slower than
the one they are in. This is the page described as the strongest in the product.

**WHAT WOULD CHANGE THIS, and why it is not filed as confirmed.** Every measurement above is
against the **public demo feed** (`simplyrets:simplyrets`), and this repository already knows the
demo and production feeds differ — `IS_DEMO`, `ALLOW_CITY_SEARCH` and `ALLOW_SORTING` exist for
precisely that reason (§0.6 rule 1: a sample shows what the code *can* do, not what it *does*).
Three outcomes from the production probe:

- **`minclosedate` works in production** → this is live, severity holds, and the fix is a one-line
  swap of the filter plus deleting the client-side split.
- **`minclosedate` is rejected or ignored in production** → the 210-day workaround is the right
  design, and what remains is the *size* of the window. 210 days truncates the tail either way, so
  the question becomes what it should be, not whether to keep it.
- **Long-DOM sales turn out to be rare in the covered markets** → the defect is real and the
  magnitude is small. Worth knowing before spending anything on it.

**Do not fix this before the probe returns.** The workaround is currently load-bearing.

**The probe is `scripts/probe_simplyrets_behaviour.py`** — six read-only GETs, one command, and it
prints the verdict wording for this entry rather than raw rows. It refuses to run against the demo
credentials without `--allow-demo`, because a demo answer pasted into a production discussion is
the mistake this entry exists to avoid.

---

### D-075 — `mindate` / `maxdate` appear to do nothing, and the code half-knew

**Severity:** FRAGILE · **Affects:** most query builders; impact currently absorbed client-side
**Status:** `open` — **CONFIRMED against the production feed 2026-09-21** (verbatim: "mindate is accepted and ignored, silently. The report builders' client-side filtering is load-bearing, not belt-and-braces. Impact is nil today; the trap is for whoever trusts the parameter next.")

> **`maxdate` is the same, and was not named.** The parameter canary survey (see D-084) sent
> `maxdate=<ten years ago>` against Active and got the whole feed back — accepted, ignored,
> no error. Both halves of the window that `build_market_snapshot_closed` and `build_closed`
> send are inert.
>
> Impact is still nil, for the reason this entry already gives: both builders filter
> client-side on `close_date`. But three comments described the parameters as *"filter by
> listDate, NOT closeDate"* — a specific wrong belief rather than a vague one, and the kind
> that gets acted on. Corrected in `query_builders.py` (twice) and `report_builders.py`.

> **Production verdict, as the probe printed it:**
>
> > CONFIRMED — `mindate` is accepted and ignored, silently. The report builders' client-side
> > filtering is load-bearing, not belt-and-braces. Impact is nil today; the trap is for whoever
> > trusts the parameter next.
>
> Stays `open` because nothing has been changed — the client-side filtering that absorbs it is
> correct and still there. What has changed is that "may not filter" is now "does not filter, in
> production", so a future query builder that omits the client-side pass is broken rather than
> merely unlucky.

`mindate=2030-01-01` returned **all 13** closed listings on the demo feed. Not an error, not an
empty set — the parameter was accepted and ignored. `build_inventory_by_zip` and most of
`query_builders.py` pass `mindate`/`maxdate` as their date window.

`build_inventory_result` already compensates:

> *"The SimplyRETS API's mindate/maxdate may not filter Active listings as expected. We must filter
> by list_date client-side."*

So the reports are probably correct today. **"May not" is now "did not, silently"**, which is a
different thing to know.

**Filed even though the impact may be nil,** because a filter that silently does nothing is a trap
for the next person who trusts it — and the next person is whoever adds a query without noticing
that every existing builder quietly re-filters afterwards. The client-side compensation is
invisible from the query builder, which is where someone reasons about what the query returns.

Also a cost: the query fetches rows it is going to discard, so `limit: 1000` is spent on a
superset. That is wasted paging, not a wrong answer.

**Same caveat as D-074:** demo feed. If production honours these parameters, this is a
demo-only quirk and closes as `closed-not-live`. The probe settles it.

**The probe is `scripts/probe_simplyrets_behaviour.py`** — six read-only GETs, one command, and it
prints the verdict wording for this entry rather than raw rows. It refuses to run against the demo
credentials without `--allow-demo`, because a demo answer pasted into a production discussion is
the mistake this entry exists to avoid.

---

### D-076 — a comma-separated multi-value parameter silently returns only the first value

**Severity:** WRONG · **Affects:** the documented vendor idiom; reached today only by two scripts
**Status:** `fixed` (`fix/vendor-query-idioms`) — **CONFIRMED against the production feed 2026-09-21** (verbatim: "the comma form silently drops values (comma returned ['Active'], repeated returned ['Active', 'Closed']). The fix already shipped is correct.")

> **Production verdict, as the probe printed it:**
>
> > CONFIRMED — the comma form silently drops values (comma returned `['Active']`, repeated
> > returned `['Active', 'Closed']`). The fix already shipped is correct.
>
> Not a demo-feed quirk. The shipped fix stands, and this entry needs nothing further.

SimplyRETS takes repeated parameters for multiple values. Given a comma-packed string it answers
**HTTP 200 and discards everything after the first value.** Measured:

| Query | Rows | Statuses returned |
|---|---|---|
| `status=Active` | 42 | Active |
| `status=Closed` | 13 | Closed |
| **`status=Active,Closed`** | **42** | **Active only** |
| `status=Active&status=Closed` | 55 | Active, Closed |
| `status=Active&status=Pending&status=Closed` | 78 | all three |

No error and no warning — just a smaller answer than the one asked for.

**Confirmed end to end through the client this repo actually uses**, not inferred:
`httpx.Request(..., params={"status": "Active,Pending,Closed"})` encodes to
`status=Active%2CPending%2CClosed`, while `params={"status": ["Active","Pending","Closed"]}`
encodes to `status=Active&status=Pending&status=Closed`. The first is the form the live API
answered with one status.

**Why this silence is worse than most.** Anyone asking for several statuses is computing something
*across* them — a ratio, a split, a rate. Lose the second status and the denominator is zero.
`calc.py:snapshot_metrics` does exactly this: it splits rows by status and computes
`moi = active/closed`, returning the sentinel **999.0** when closed is empty. That is **D-056's
failure mode arriving through the transport layer** rather than the query builder.

**Not live.** `vendors/simplyrets.py:build_market_snapshot_params` is the only comma-form caller
and is reached only by `apps/worker/test_pipeline.py` and `test_simplyrets.py`. Production's
`query_builders.py` asks for one status per query throughout.

**Fixed anyway, and this is the reason:** it was the idiom the module *documented*, in
`fetch_properties`'s own docstring, as the worked example of a multi-value parameter. The next
multi-status query would have copied it — and the next multi-status query is the inventory Closed
work this was found while scoping. A test now searches for the construct (a comma-packed value
under a multi-value key) rather than for the literal that was wrong, and separately checks that no
docstring still teaches it.

**This one does not need the production probe.** Repeated parameters are the standard encoding for
multi-value query strings and are what the API answered correctly; the comma form is proven wrong
on at least one feed and proven right on none.

---

### D-077 — the inventory report's "Active" count and its months-of-supply numerator are different populations

**Severity:** ROUGH · **Affects:** the inventory report's headline count and its PDF section copy
**Status:** `open` — **needs a product decision, not a fix**

The listings table shows active listings that came to market inside the lookback window; that is
deliberate and documented (*"Per user request: only show listings that were listed within the
selected date range"*). Months of supply divides **total** inventory by the sales rate, which is
the only correct numerator.

So after `fix/inventory-moi` the report can say **"Active 20"** beside **"8.9 months of supply"**,
and a reader who divides one by the other gets a sales rate that does not exist. Both figures are
right. Together they imply a third that is not.

`metrics.total_active` is published alongside, so nothing has to be inferred — but "published in
the JSON" is not "visible on the page".

**Two coherent answers, and they are not interchangeable:**

1. **`Active` means inventory.** The tile shows total active and the table keeps its window, with
   its own count. Consistent, and it changes a headline number this report has always shown.
2. **`Active` means the table.** Label it as such — "New this period" — and show total inventory
   beside the supply figure. Smaller change, more words on the page.

**A second, older instance of the same mismatch, found while checking this.** `PDF_CONFIG`'s
inventory copy reads *"All {total} active listings in {city}"* where `{total}` is the windowed
subset. That sentence has been describing a fraction of inventory as if it were all of it since
before this ticket. It is the same decision, so it belongs with it.

**Not decided here** — §0.2, this is a product voice call about a headline figure.

---

### D-078 — "not enough recent sales" is also what a too-large market is told

**Severity:** ROUGH · **Affects:** the inventory report in markets above the fetch limit
**Status:** `open` — **filed rather than fixed, per the one-line threshold**

`compute.moi.months_of_supply` returns `None` for two unrelated reasons, and the page renders the
same sentence for both:

| Cause | What the reader sees | What is actually true |
|---|---|---|
| fewer than 3 closings in the window | *"Not enough recent sales to estimate"* | correct |
| the Active fetch hit its 1000-row limit | *"Not enough recent sales to estimate"* | **there were plenty of sales; there was too much inventory to count** |

The second is the opposite situation wearing the first one's words. A busy market — the one most
likely to have both many sales and more than a thousand active listings — is told it has too few
sales. Someone will report that as a bug, and the report will have told them the wrong thing about
why.

**Refusing to publish is still right.** A truncated fetch makes the numerator a floor, which makes
months-of-supply too LOW, which reads as a hotter market and would push a seller to underprice
(D-056's direction, inverted). The number should not be printed. Only the explanation is wrong.

**Not a one-line change, which is why it is filed.** `months_of_supply` returns a bare float-or-
None, so the reason does not survive the return. The shape that fixes it is a sibling — say
`estimate(active, closed, window, truncated) -> {"value", "reason", "formatted"}` — with
`months_of_supply` kept as the thin numeric API for callers that only want the figure. Roughly
25 lines in `compute/moi.py` plus two call sites and two strings of copy. Small, contained, and
more than the threshold the ticket set.

**Worth doing with D-077**, since both are about what the inventory report says rather than what it
computes, and both change page copy.

> **THE THRESHOLD IS 1000, NOT 500 — and the ceiling may not need raising at all.**
>
> The production probe reported 500 rows on the active query and that was read as a page ceiling.
> It is not: **500 was the probe's own `limit` on a single GET.** `fetch_properties` paginates at
> 500 per page up to `INVENTORY_FETCH_LIMIT`, which this session set to 1000. So D-078 fires above
> **1000** active listings, not 500 — still reachable in a large market, and still worth fixing,
> but double the stated figure and not an API property at all.
>
> **And the right fix is not to page further.** `?count=true` returns the exact total in
> `X-Total-Count` in a single `limit=1` request (D-081). Months of supply needs a count, not the
> listings. That removes the ceiling instead of raising it, and costs fewer calls than today.
>
> So this entry's copy fix — distinguishing "not enough sales" from "too much inventory to count" —
> may end up describing a state that can no longer occur. **Take D-081 first and see what is left.**

> **D-081 IS DONE, AND THIS IS NARROWED RATHER THAN CLOSED.** Asked directly — does the truncation
> case still occur? Measured, with the builder, four ways:
>
> | Case | Renders |
> |---|---|
> | 12,000 active, count available | **88.7 months** — the ceiling is gone |
> | 12,000 active, feed returns no header | "Not enough recent sales" — falls back to a row floor |
> | 12,000 active, **the CLOSED fetch truncated** | **"Not enough recent sales"** ← still wrong |
> | 50 active, 2 sales | "Not enough recent sales" — true |
>
> The **numerator** half is gone: a count cannot be truncated. The **denominator** half survives —
> a market with more than 1,000 closed sales in the 90-day window is still told it has too few, and
> that is the same misleading sentence from the opposite input. It cannot be fixed the same way
> until D-074 is corroborated, because switching the denominator to a count means trusting
> `minclosedate` outright.
>
> So this stays open, halved, and **the copy is worth writing** — the remaining branch is reachable,
> not hypothetical. Still bundled with D-077.

---


> **D-087 MADE THIS MORE REACHABLE, NOT LESS (2026-09-22 sweep).** D-081 removed the 1000-row
> ceiling from the months-of-supply numerator, which was most of this defect's trigger. D-087 put
> that ceiling back **for city-based reports**, because the exact count it relied on counts other
> cities. So a large city market can once again hit `active_was_truncated` → `moi is None` →
> `"Not enough recent sales to estimate"` — a sentence about SALES, shown because there were too
> many ACTIVE listings.
>
> That is this entry's exact complaint, restored by a fix that was right for its own reasons. The
> cost of D-087 is named on its own entry; this is where it lands. **It goes away again when the
> probe settles `cities`** — the same verdict D-087 is waiting on.

### D-079 — no settings surface for an account's own postal address

**Severity:** ROUGH · **Affects:** accounts that want their own address on their white-labelled email
**Status:** `open` — **the non-urgent half of D-060**

`affiliate_branding.postal_address` exists (`0055`) and the render path uses it, but nothing writes
it. Every account therefore sends with the platform address, correctly attributed to TrendyReports
— compliant, and not what a white-label customer wants on their own mail.

**Filed rather than built, per the ticket's own threshold.** It is larger than it sounds:

| | |
|---|---|
| `routes/affiliates.py` | ~11 touch points — the request model, two INSERTs, two SELECTs, two response dicts, the UPDATE |
| `settings/branding/page.tsx` | 846 lines, and it does not currently expose **any** contact field — `contact_line1` appears zero times. So this is not "add an input beside the others"; it means deciding where a contact section lives on that page. |

**Two things to settle when it is taken:**

1. **Regular accounts have nowhere to put one.** The column is on `affiliate_branding`, which
   white-label accounts have and regular accounts do not. A regular account that wants its own
   address on its mail needs either a row created for it or a second column on `accounts` — and
   the second option splits the sender's identity across two tables, which is the reason `0055`
   chose `affiliate_branding` in the first place.
2. **A validation question that must not become a guard trap.** An empty save has to mean "use the
   platform address", not "send nothing" — the render path already handles blank and
   whitespace-only, and the API must not 422 an emptied field. Same shape as the colour validator
   in D-059, which nearly shipped that exact regression.

---

### D-080 — `fetch_properties` raises when the result count is an exact multiple of the page size

**Severity:** WRONG · **Affects:** every report, in any market whose matching set lands on a page boundary
**Status:** `fixed` (`fix/pagination-by-count`) — **stops on the feed's own total, not on a page's size**

`fetch_properties` pages with `offset`, and stops when a page comes back **shorter** than it asked
for. When the total is an exact multiple of the page size, no page is ever short: the loop
increments `offset` past the end and asks for one more.

SimplyRETS answers that with **HTTP 400**, not an empty list:

```
{"error":"InvalidArguments","errors":["offset too high"]}
```

`_request_with_retries` re-raises `httpx.HTTPError` for 4xx, so the exception propagates out of the
fetch and fails the whole generation. Not a truncated report — no report.

**Reproduced by replaying the loop's own arithmetic against the live feed** (65 properties, page
size 65):

```
GET limit=65 offset=0    -> 65 rows, 65 == page_size -> continue, offset now 65
GET limit=65 offset=65   -> HTTP 400 "offset too high"
```

**How often.** The page size is 500, so this needs a market with exactly 500, 1000, 1500 … matching
listings. Rare per report, certain across enough of them — and it presents as an unexplained
failure rather than as a wrong number, so it would be chased as a transient.

**The fix is the stop condition, not a try/except.** Stopping on `len(batch) < page_size` is
inferring the end from a page's size; the loop should also stop when it has fetched everything the
API says exists. `X-Total-Count` gives that directly — see D-078. A `try/except` around the extra
request would also work and would be worse: it would treat a real argument error as a normal end
of data.

**Found while investigating the 500-row ceiling** (D-078), not by the survey — the two share a
cause, which is that this module infers pagination state instead of reading it.

---

### D-081 — the active count for months-of-supply is fetched by paging when the API will just say

**Severity:** ROUGH · **Affects:** inventory report latency, and D-078's ceiling
**Status:** `fixed` (`fix/pagination-by-count`) — **numerator CONFIRMED in production 2026-09-21 (`X-Total-Count=70760`); the denominator still waits on D-074**

Months of supply needs a **count** of active inventory, not the listings themselves. The inventory
report currently pages up to `INVENTORY_FETCH_LIMIT = 1000` listings to get it, and refuses to
publish a figure when that limit is hit (D-078).

SimplyRETS returns the exact total in a header, on request:

```
GET /properties?status=Active&cities=…&limit=1&count=true
X-Total-Count: 65
```

One request, `limit=1`, and the true count regardless of size. `X-Total-Count` is listed in the
feed's `Access-Control-Expose-Headers` and is returned **only when `count=true` is passed** —
measured: absent on four other query shapes, present with that parameter.

That removes the ceiling rather than raising it, and it is *fewer* calls than today, not more. The
listings table still needs the listings, but it is served from the date-windowed set it always
was; only the MOI numerator needs a total, and a total is what this returns.

**IMPLEMENTED 2026-09-17.** `count_properties()` does one `limit=1&count=true` request and reads
`X-Total-Count`; the inventory numerator uses it. Measured end to end: a market with 12,000 active
listings and 400 sales in the window now yields **88.7 months**, where it previously said *"not
enough recent sales to estimate"* because the fetch stopped at 1000.

**The denominator deliberately does NOT switch.** It could — `status=Closed&minclosedate=…` with
`count=true` — but that would make the sales rate depend entirely on `minclosedate` being honoured,
and the production probe has confirmed only that the parameter **filters**, not that it filters
correctly at a real date (D-074). The closed listings are still fetched and re-filtered on
`close_date` client-side, which is right under either answer. **Switch it when D-074's 90-day
corroboration lands, and not before.**

**Returns `None`, not `0`, when the feed does not say.** Those are different facts, and a caller
reading "the feed did not say" as "there are none" would compute months of supply from a zero it
invented — D-056's failure with a new cause. When it returns `None` the builder falls back to
counting rows, and the truncation flag still refuses to publish.

### D-082 — seventeen mutating actions in the web app fail with no visible sign

**Severity:** WRONG · **Affects:** every authenticated surface, and D-019's enforcement
**Status:** `open` — two instances fixed in `fix/d019-verified-sending`, the rest unfixed

The shape is one line:

```ts
    } catch (error) {
      console.error("Save error:", error)
    }
```

A handler POSTs, PATCHes or DELETEs, the request is rejected, the failure is thrown or the
`!res.ok` branch is taken, and the **only** thing that happens is a line in a console nobody has
open. The button springs back to its resting state. The user's sole evidence that their action did
not work is the absence of the thing they expected, which for a toggle is indistinguishable from a
slow refresh.

Found by grepping for the construct rather than the symptom (§0.6 rule 5): a `catch` whose entire
body is a `console.*` call, filtered to those wrapping a non-GET request. **17 instances.** The
full list is in the branch's PR; the ones that matter most are the two schedule toggles, because
they are exactly what D-019 now refuses:

- `apps/web/app/app/schedules/[id]/schedule-detail-shell.tsx:11` — did not read the response at
  all. It `await`ed the fetch and then called `router.refresh()` unconditionally, so a **403 was
  processed identically to a 200**.
- `apps/web/components/v0-styling/SchedulesListShell.tsx:31` — checks `res.ok` and does nothing
  on the other branch.
- `apps/web/components/schedule-builder/index.tsx:236` — `if (!res.ok) throw new Error(...)` into
  a catch whose body was `console.error`.

**This is why it is filed rather than left for later.** D-019's third requirement is that the
blocked action explains why and offers a resend. A 403 the UI discards is not enforcement anyone
can act on — it is the same dead end as an unreachable account, arriving one step later. The three
call sites above are fixed on `fix/d019-verified-sending` because that branch's gate makes them
reachable; **the other fourteen are untouched and still silent**, and most of them are admin
surfaces where the same rejection could be a permissions failure, a stale row, or a validation
error.

Not a new observation about any one file — it is a house style, which is why it wants one
deliberate pass (a shared error surface) rather than fourteen separate edits.

### D-085 — the email picks which KIND of price to quote by precedence, not by what the sentence says

**Severity:** FRAGILE · **Affects:** every report type's insight paragraph
**Status:** `fixed` (`feat/workstream-c-email-rebuild`)

> **FIXED, and the entry undercounted it by two functions.** The precedence line
> is in `_get_insight_paragraph`, `_get_quick_take` **and**
> `_get_conversation_starter` — three functions and nine sentences, not one and
> four.
>
> Each site now names its kind through `_median(SOLD|ASKING|EITHER, metrics)`,
> which returns `None` rather than the other kind when the metric it was asked
> for is absent, so the **sentence** changes instead of the number. A wrong
> figure reads as authoritative; a missing one reads as missing.
>
> **Demonstrated before the fix**, with a metrics dict carrying only a list
> price: *"18 homes sold at a median of $825K"* — the asking price, described as
> a sale. After: the clause drops and the paragraph reads *"Great news for
> sellers in La Verne—the market is moving fast."*
>
> `apps/worker/tests/test_insight_price_kind.py` (48 cases) covers every report
> type against all four combinations of the two metrics, including that no
> sentence is left with a seam where a clause was removed — the first version of
> the fix produced *"just hit the market . Current inventory"*.
>
> One pre-existing test was **rewritten rather than deleted**:
> `test_varying_prices_still_appears_when_there_is_genuinely_no_price` asserted
> the literal fallback string, which this fix removes in favour of dropping the
> clause. It is restated against its own stated purpose — *do not invent a
> figure* — and renamed. The argument for why that is a restatement and not a
> removal is written into the test.

`_get_insight_paragraph` (`email/template.py:1717`) resolves one variable:

```python
median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
```

and spends it on sentences that want different things:

| report type | the sentence | the price it needs |
|---|---|---|
| `market_snapshot` | "{n} homes **sold** at a median of {price}" | close |
| `market_snapshot` | "The median **sale** price sits at {price}" | close |
| `inventory` | "{n} **active listings** at a median of {price}" | list |
| `new_listings` | "with a median **asking** price of {price}" | list |

**Every one of them renders correctly today, and none of them is guaranteed to.** The precedence
happens to match because of which metrics each builder emits: `market_snapshot` emits both, so
close wins and its sale sentences are right; `new_listings` and `price_bands` emit only a list
price, so their asking sentences are right. Correct by coincidence, across two files, with nothing
stating the dependency.

Found while fixing D-057: `build_inventory_result` now has closed listings and could compute a
close price. Adding one — an obviously correct metric, in a builder, reviewed on its own terms —
would turn *"active listings at a median of $450,000"* into a figure describing homes that already
sold. Nothing would fail. The email would just quietly start saying something else.

**The fix is to stop making the template guess.** Each sentence should name the metric it means —
`median_close_price` in the sale clauses, `median_list_price` in the asking ones — and fall back to
its own wording when that one is absent, rather than to the other kind of price. Not done here
because it touches shared prose for four report types and D-057's branch is about one builder.

The absence is pinned in the meantime: `test_the_inventory_builder_does_not_emit_a_close_price`
fails with the reason if anyone adds it.

### D-086 — `_median` and `_average` publish `0.0` as a price

**Severity:** ROUGH · **Affects:** market snapshot, price bands, property reports, and anything reading a metric rather than testing it
**Status:** `open`

> **PARTIALLY SUPERSEDED, 2026-09-29 (D-111).** `compute/price_bands.py` has its own `_median`
> that returns `None` for an empty list — the fix this entry asks for, on the one path that is
> new. `report_builders._median` and `_average` still return `0.0` and still reach
> `median_close_price`, `median_list_price`, the tier medians and `avg_ppsf`. **The defect is
> live everywhere it was filed against.** Recorded because a reader finding the correct
> behaviour in the newer module could reasonably conclude the entry was stale.

```python
def _median(vals): return statistics.median(vals) if vals else 0.0
def _average(vals): return (sum(vals) / len(vals)) if vals else 0.0
```

`0.0` is a price. It is a claim that the median asking price in this market is zero, and it is
emitted whenever the input list is empty — which is exactly when there is nothing to claim. Several
call sites go further and write `else 0` explicitly (`:237`, `:799`, `:800`, `:801`).

Impact today is limited because the email template guards on truthiness, so `0.0` renders as
"varying prices" or "typical time" rather than "$0". That is the template being lucky, not the
metric being right: **any surface that formats the number instead of testing it prints `$0`**, and
the PDF templates and the API's report JSON both read these fields.

This is D-056's sentinel, which the months-of-supply work settled — `None` when there is nothing to
estimate from, never a number that looks like an answer — applied to one function and not to its
neighbours. `build_inventory_result`'s `median_list_price` was fixed to `None` in
`fix/d057-inventory-median-price`; **at least eight other published metrics still carry the
sentinel**, including the identical expression at `report_builders.py:144`.

Not fixed alongside D-057 because each one publishes a field other surfaces read, and changing
eight metrics' empty-case type inside a ticket about one email sentence is how a scoped fix becomes
an unreviewed one.

### D-084 — a misspelled SimplyRETS parameter widens the query silently, and nothing notices

**Severity:** FRAGILE · **Affects:** every report that filters — market snapshot, closed, inventory, new listings, price bands, market trends
**Status:** `open` — the probe now detects it; nothing at runtime does

D-075 recorded that `mindate` is accepted and ignored. That is not a property of `mindate`. It is
a property of **every** parameter name SimplyRETS does not recognise.

Found by making the mistake. The D-081 filtered-count check sent `postalcodes` — lowercase — and
reported *"the header IGNORES the filter: BROKEN"*. The feed was fine; the spelling was not:

```
postalCodes=77018  ->  X-Total-Count=5
postalcodes=77018  ->  X-Total-Count=42   (the whole feed)
postalcode=77018   ->  X-Total-Count=42
(no filter)        ->  X-Total-Count=42
```

**A typo does not fail. It widens.** No 4xx, no warning, no unknown-parameter error — the query
simply stops being narrowed. And the consequence scales with what the query feeds: on a listing
page a widened result is visibly wrong; on a `count=true` request it is one number that reads as a
big market. `count_properties` is the months-of-supply numerator, so a misspelled `postalCodes`
there would put the entire MLS over one city's sales rate.

**The survey.** Every filtering parameter this client sends, each with a deliberately misspelled
twin, compared on `X-Total-Count` against an unfiltered baseline — probe section 5. Twelve
parameters; values derived from the feed's own sample so each one must bite. Result on the demo
feed:

| | |
|---|---|
| filters correctly | `postalCodes`, `type`, `subtype`, `minprice`, `maxprice`, `minbeds`, `minbaths`, `cities`, `minclosedate` |
| **filters, but FUZZILY** | `q` — narrows, and to the wrong set (see below, and D-087) |
| **accepted and ignored** | `mindate`, `maxdate` (see D-075) |
| not canaried | `limit`, `offset`, `sort`, `count`, `vendor` — they change the shape of the answer, not which rows are in it |

**All twelve misspellings were ignored**, which is what makes the canary meaningful: the feed is
spelling-strict, so "correct narrows and wrong does not" is a real signal rather than a
coincidence.

> **CORRECTION, 2026-09-22 — `q` was listed as "filters correctly" and does not.** The canary only
> asks *did the result narrow?* `q` narrows, so it passed. It does not ask *did it narrow to the
> right rows*, and `q` is free-text over MLS number, address, city and ZIP:
>
> ```
> cities=Houston  ->  X-Total-Count 12, every row in Houston
> q=Houston       ->  X-Total-Count 13, twelve Houston + one TOMBALL
> ```
>
> A canary that compares a filtered count against an unfiltered one can only distinguish *narrowed*
> from *ignored*. "Narrowed to the correct set" is a third state it is structurally blind to, and
> `q` is the parameter that lives there. The row-level check — do the returned rows actually satisfy
> the filter? — is what separates them, and only `type` (whose returned rows carry their own type
> field) has ever been checked that way. **Any parameter in the "filters correctly" row could in
> principle be in the fuzzy row**; what is established for them is that they narrow.
>
> This matters for the allowlist, which is the whole point of D-084: an allowlist built from this
> table would have declared `q` sound. The allowlist answers "is this name recognised", which is a
> genuinely different question from "does this name do what we think", and it should be described
> as the former when it lands.

**What is NOT fixed.** Nothing at runtime detects a misspelling. The probe catches it when someone
runs the probe. A real guard would be an allowlist in `query_builders.py` — every key it emits
checked against the set of parameters known to work — which is a small change and a real one, and
is not in this branch because the survey had to come first: an allowlist built from a guess at the
vocabulary is worse than none.

**AND THE SURVEY IT IS BUILT FROM MUST BE THE PRODUCTION ONE, NOT THE DEMO RUN ABOVE.** The table
here is from the demo feed, and this very survey has already shown the two feeds disagree about
which parameters work: `cities` narrowed 8 of 42 on demo, while `query_builders.py:_location`
carries a comment saying the demo ignores city params and `q` is the fallback for that reason. One
of those is wrong, and an allowlist measured on the wrong feed encodes the wrong feed — which
would be worse than no allowlist in the specific way this defect is about, because it would look
authoritative.

So D-084 stays open until Jerry's production run lands, and the allowlist is built from those
verdicts. The demo results are the shape of the answer, not the answer.

This is filed FRAGILE rather than WRONG because every name the client currently sends is spelled
correctly. The defect is that nothing would tell you if that stopped being true.

### D-083 — `email_log.status`'s COMMENT documents four of its six values

**Severity:** ROUGH · **Affects:** anyone reading the schema to find out what the column means
**Status:** `open`

`db/migrations/0027_fix_email_log_and_schedule_indexes.sql:16` says:

```sql
COMMENT ON COLUMN email_log.status IS 'Email send status: sent, suppressed, failed, unknown';
```

Since then the code has written `sending` (#56, a state that did not exist and was needed),
`duplicate_suppressed` (#61, a send refused because the report had already gone), and now
`blocked_unverified` (D-019). Six values, four documented, and the two undocumented ones are both
*non-deliveries* — which is the distinction the comment would be consulted for in the first place.

Cosmetic in the sense that nothing reads a COMMENT at runtime, and precisely not cosmetic in the
sense that this column stopped meaning "an email" some time ago and the schema still says it does.
`admin.py:113` already carries that correction as a code comment, which is the wrong place for it
to live alone.

Fixing it is one `COMMENT ON COLUMN` in a new migration. Not folded into D-019's branch because it
would have added a second unapplied migration to the pile Jerry was then holding (0055, since applied), for no
behavioural gain, and a DDL file in a diff invites the assumption that the fix needs it.

### D-087 — the months-of-supply numerator counts listings from other cities

**Severity:** WRONG · **Affects:** the `inventory` report's hero KPI and months of supply, on every
city-based run (ZIP-based runs are unaffected)
**Status:** `fixed` — `fix/q-city-contamination`

`_location` (`query_builders.py`) sends `q=<city>`, SimplyRETS' free-text search over MLS number,
address, city and ZIP. Measured against the demo feed:

```
cities=Houston  ->  X-Total-Count 12, every row in Houston
q=Houston       ->  X-Total-Count 13, twelve Houston + one listing in TOMBALL
Cities=Houston  ->  X-Total-Count 65, the whole feed  (D-084: names are case-sensitive)
```

**The rows were never the problem, and saying otherwise would be the interesting-sounding version
of this defect rather than the true one.** `_filter_by_city` (`report_builders.py:285`) exists
precisely for this, is applied at the top of all eight builders and twice in `market_trends.py`,
and matches on equality rather than substring — so the Tomball row has never reached a listings
table, a median, a DOM or `counts["Active"]`. That defence long predates this entry.

**What it cannot reach is a count.** `count_properties` asks with `count=true` and the feed answers
with `X-Total-Count`: one number covering everything the API matched. There are no rows to filter.
So on a city report:

| figure | source | population |
|---|---|---|
| `counts["Active"]`, the table, every median | fetched rows, city-filtered | the requested city |
| `metrics["total_active"]` (hero KPI) | `X-Total-Count` | the city **plus fuzzy matches** |
| months-of-supply NUMERATOR | `X-Total-Count` | the city **plus fuzzy matches** |

Two populations, one report. **That is D-056 exactly, arriving by a different route** — and worse
than D-056 in one respect: the hero KPI reading 13 above a table of 12 is at least visible, while
the same 13 inside months of supply is not. The error is one-directional (`q` can only match more,
never fewer), so inventory is overstated and months of supply is overstated, which pushes the
market-condition badge toward buyer's-market — the same direction D-074 pushed it.

Size unknown in production and not extrapolated from 13-vs-12: `q` is full-text, so a city whose
name appears in street names, subdivision names or agent remarks matches far more of the feed than
one whose name does not. One city, one feed, one day is not a rate.

> **FIXED, AND NOT BY SWITCHING TO `cities`.** The precise-looking fix is the dangerous one.
> The code's own comment says some accounts may not support `cities`, and D-084 measured what
> SimplyRETS does with a name it does not recognise: accepts it, ignores it, returns the whole feed
> with a 200. On an unsupporting production account the swap turns one stray Tomball listing into
> **every listing in the MLS** — a city report computed over ~70,000 homes, silently. Being wrong by
> one row and being wrong by the entire feed are not the same bet.
>
> So: keep `q`, keep cleaning the rows, and **stop counting**. `count_properties_if_exact`
> (`vendors/simplyrets.py`) returns `None` when the query's location filter is fuzzy, and sends no
> request at all — a call saved, not spent. `None` is not a new code path: it is the existing "the
> feed did not return the header" case, which already falls back to the **city-filtered** row count
> with `active_was_truncated` set if the fetch hit its ceiling.
>
> **The cost is real and stated rather than buried.** D-081 removed the 1000-row ceiling from this
> figure; this puts it back for city-based reports. A city with more than 1000 active listings now
> *declines to state* months of supply instead of stating a contaminated one — D-078's flag doing
> its job. ZIP reports keep the exact count, because `postalCodes` was measured exact.
> `location_is_exact` already lists `cities`, so the day Jerry's probe confirms production honours
> it, the ceiling comes off again with a one-line change in `_location` and nothing else.
>
**XFAILS THIS DEFECT GATES** (§0.6: two-way link, or an xfail is a skip with better manners).
All in `tests/test_simplyrets_query_builder.py`, marked `xfail(strict=True)` with `D-087` named
in the reason. **Strict**, so the day this is fixed they PASS, the unexpected pass FAILS THE BUILD,
and the markers have to come off — which is how this list stops being a lie.

| test |
|---|
| `test_production_uses_cities_param` |
| `test_production_city_value_preserved` |

> ### THIS FIX IS EXPECTED TO BE TEMPORARY, AND THE PROBE IS WHAT ENDS IT
>
> **Do not read the entry above as settled engineering.** Refusing to count is the correct thing to
> do *while the question is open*; it is not the destination. The destination is `cities`, which
> measured exact on the demo feed — an exact count, no ceiling, no contamination, for every city
> report. What stands between here and there is one verdict from
> `scripts/probe_simplyrets_behaviour.py` section 5, whose canary already covers `cities` on the
> production feed.
>
> | probe says `cities` filters on production | then |
> |---|---|
> | **yes** | `_location` returns `{"cities": city}` instead of `{"q": city}`. `location_is_exact` already lists it, so counts come back exact for city reports and the 1000-row ceiling goes away again. One line. This entry becomes history. |
> | **no** | the guard stays, permanently, and the ceiling is the price of not publishing a contaminated numerator. Worth then asking whether a *paged* exact count is affordable for the >1000 case. |
>
> **The probe now gates three things, and this is the third:** the parameter allowlist (D-084),
> D-074's remaining 90-day corroboration, and whether city reports get exact counts back. The cost
> of this fix is the reason its priority went up, not a reason to route around it.
>
> A note for whoever reads this after the probe lands: if the answer is yes, the one-line change is
> **not** the whole job. `_filter_by_city` stays — an exact API filter does not make a client-side
> equality check redundant, it makes it a cheap no-op, and D-074's posture is the precedent. Remove
> it and the next time a location parameter is quietly dropped, nothing catches it.

Tests: `apps/worker/tests/test_city_contamination.py`, 11 cases, four regressions applied and seen
to fail on the right tests — including one on `_filter_by_city` itself, because a fix that replaced
one fuzzy match with another (a substring test would readmit "South Houston") would be no fix.

### D-088 — two of the six documented SimplyRETS property types are silently ignored

**Severity:** FRAGILE · **Affects:** nothing today; any future query that asks for multi-family or
commercial inventory by the documented code
**Status:** `fixed` — `fix/q-city-contamination`

`query_builders.py:_filters` documented the `type` vocabulary as
*"RES=Residential, CND=Condo, MUL=Multi-family, LND=Land, COM=Commercial, RNT=Rental"*. Each value
sent to the demo feed with `count=true`, and the returned rows' own `property.type` inspected:

| sent | count | rows returned | |
|---|---|---|---|
| `residential` / `RES` | 45 | all RES | |
| `condominium` / `CND` | 33 | RES + CND | |
| `land` / `LND` | 6 | all LND | |
| `rental` / `RNT` | 10 | all RNT | |
| `multifamily` | 7 | all MLF | |
| **`MUL`** | **45** | **all RES** | ← ignored |
| `commercial` | 5 | all CRE | |
| **`COM`** | **45** | **all RES** | ← ignored |
| `farm` | 4 | all FRM | |
| `ZZZNONSENSE`, `` (empty) | 45 | all RES | the fallback |

**An unrecognised VALUE does not 400 and is not dropped — it falls back to residential.** So a
query asking for multi-family or commercial by the documented code comes back with houses, at 200,
and every downstream median is a median of the wrong property class. This is D-084's silent-widening
finding one level down: that one is about parameter *names*, this one is about their *values*, and
the failure mode is the same shape — accepted, ignored, no error.

Nothing sends `MUL` or `COM` today (grepped across `apps/`), which is why this is FRAGILE and not
WRONG. The fix is the corrected table, so that the next person writing a commercial report copies a
value that works.

**`RES` is left alone and cannot be adjudicated from outside.** It produces exactly the residential
set — but so does `ZZZNONSENSE`, because the fallback *is* residential. Whether `RES` is recognised
or merely lands on the default is not observable through the API, and the root suite's
`test_resolver_type_is_residential` asserts it is invalid on grounds nothing here can establish.
The docstring now says to prefer the long names, which are unambiguous either way. Values are
case-insensitive (`Residential`, `RESIDENTIAL` both return 45); parameter *names* are not (D-084).

**XFAILS THIS DEFECT GATES** (§0.6: two-way link, or an xfail is a skip with better manners).
All in `tests/test_simplyrets_query_builder.py`, marked `xfail(strict=True)` with `D-088` named
in the reason. **Strict**, so the day this is fixed they PASS, the unexpected pass FAILS THE BUILD,
and the markers have to come off — which is how this list stops being a lie.

| test |
|---|
| `test_default_type_is_not_RES` |
| `test_default_type_is_residential` |
| `test_RES_alias_normalized_to_residential` |
| `test_MUL_alias_normalized_to_multifamily` |
| `test_LND_alias_normalized_to_land` |
| `test_RNT_alias_normalized_to_rental` |
| `test_market_snapshot_query_has_no_RES` |
| `test_resolver_type_is_not_RES` |
| `test_resolver_type_is_residential` |
| `test_no_report_type_produces_RES` |
| `test_valid_types_only` |


### D-089 — the root suite's 40 failures were the suite describing a system that had moved

**Severity:** ROUGH · **Affects:** CI, continuously since 2026-09-03
**Status:** `fixed` — `fix/root-suite-mode`

D-054 added `tests` to `pytest.ini`'s `testpaths` and recorded that 40 of 207 failed,
pre-existing and previously invisible. That was correct and it was left as "the known-red
baseline" for **19 days**, during which every Backend Tests run — on `main` and on every PR,
including ones that were reviewed and merged — reported failure. Checked: the last ten runs
before this entry, all `conclusion: failure`.

**A baseline nobody can act on is not a baseline, it is a disabled check.** That is D-038 and
D-041 exactly, which this repository has now hit three times.

**The triage.** All 40 fail in BOTH credential modes — an earlier claim that they were
mode-dependent was wrong, and is corrected in this entry rather than quietly dropped: it came
from reading a `Mode: DEMO` banner next to a `'RES' != 'residential'` assertion and inferring
causation from adjacency. Flipping `SIMPLYRETS_USERNAME` and confirming the constants changed
produces the identical 40.

| | | |
|---|---|---|
| **23** | the fixture contradicts the real payload contract | fixed |
| **4** | the product moved and the test did not | fixed |
| **13** | the test is right and the product change is gated | `xfail(strict=True)` |

**None of the 40 was a product defect this suite had caught.** Worth saying plainly, because the
case for keeping a red suite is that it might be telling you something, and here it was not.

**The 23.** `test_property_templates.py` hand-wrote the `property` dict and omitted
`assessed_value`, `land_value` and `tax_amount` — keys `_build_property_context()`, the only
construction site, sets unconditionally. Production's own `format_currency` raises
`UndefinedError` on an absent key (it catches `ValueError`/`TypeError`, and `UndefinedError` is
neither), so the templates were being asked to render a shape production cannot produce. The
file also carried copies of three filters under a header reading *"must match production"* which
no longer did (`"-"` vs `"N/A"` for None), and a local Jinja `Environment` differing from the
real one in three settings. Three more asserted `>None<` never appears while the same fixture
set `"pool": "None"` — the literal string.

Rewritten so that **nothing in the file builds a context**: every test goes through
`PropertyReportBuilder(report_data).render_html()`, the call `tasks.py` makes. The hand-written
inputs are now `report_data`, which is the builder's own argument — the thing production also
writes by hand. That is §0.6's new rule, and this file is its evidence.

**The 4.** Two tested `vendors/simplyrets._inject_vendor`, deleted when vendor injection moved
into `_common_params()` — rewritten against a real built query rather than a helper.
`test_agent_name_rendered` asserted against `render_html()` after the agent footer moved into
PDFShift's `footer` param; `render_page_footer_html()` contains the name and `tasks.py:1650`
passes it to `render_pdf`. `test_has_seven_pages[teal]` counted `class="page ` *with a trailing
space* and fell back to `class="page"` only when that returned zero — teal uses both (5 + 2), so
the fallback never fired and it reported 5 of 7. teal has always rendered seven.

**The 13, and why `xfail` rather than a fix or a deletion.** They demand two product changes that
are deliberately gated: `_location` sending `cities` (D-087, waiting on the production probe,
where switching on demo evidence risks returning the entire feed) and the `type` vocabulary
(D-088, which changes every SimplyRETS query the product sends and belongs in its own diff).
`strict=True` is load-bearing: the day either lands these PASS, and a strict xfail that passes
**fails the build**, which is the prompt to remove the marker. A plain skip would go quiet
forever, which is the failure this entry is about.

> **The marker caught its own misuse immediately.** Applied at class level first, it covered two
> tests that were already green; they xpassed, strict turned that into a failure, and the mistake
> surfaced in one run. Moved to the thirteen methods.

**Also fixed: `tests/**` was not in the workflow's `paths` filter**, so editing this suite did not
trigger the job that runs it. Its breakage could only ever surface on somebody else's unrelated
PR. `db/**` added for the same reason.

**CI is still red, and this entry does not claim otherwise** — see D-091.

### D-090 — a NULL database column renders as the word "None" in customer PDFs

**Severity:** WRONG · **Affects:** property reports whose agent or parcel data has NULL columns
**Status:** `fixed` — `fix/root-suite-mode`

`d.get(k, "")` returns the default only when the key is **missing**. When the key exists holding
None — a nullable column, a `LEFT JOIN`, a JSON null — it returns None, and Jinja prints `None`.

Three of five themes rendered, in the agent block of a customer-facing report:

```
☎ None      ✉ None
```

**`_build_agent_context` already carried a comment explaining this exact trap**, above `title`,
which was hardened for D-066/D-067. `phone`, `email`, `name`, `company_name` and
`company_tagline` — the lines immediately below it — were not. §0.6 says to grep for the
**construct** rather than the symptom and re-run the check after the fix; this is what the second
half of that rule costs when it is skipped.

Surveying the construct rather than the two symptoms found a worse instance in
`_build_property_context`: `street`, `city` and `state` are interpolated into `full_address`, so a
NULL there is not a blank on a detail line — it is

```
None, La Verne, CA 91750
```

on the cover of **all five themes**, measured. Plus `owner_name`, `county`, `apn`,
`property_type` and `legal_description`, each written `a.get(k, "") or b.get(k, "")`, where the
last term's None becomes the value of the whole expression — a chain that looks guarded and is not.

**Found by the D-089 rewrite, not by looking for it.** One rewritten case passes optional fields
as explicit `None` rather than omitting them, because that is what a nullable column looks like by
the time it arrives. The old hand-built fixtures omitted keys instead, which is the one shape that
cannot expose this.

**Deliberately not changed: `latitude`/`longitude` stay None-able.** There None is a real value
meaning "no coordinates", and `_build_images_context` branches on it to skip the aerial map. The
defect is not that None exists in the context — it is that None reaches a template that prints it.
A blanket sweep would have broken the aerial page; `test_coordinates_are_still_allowed_to_be_none`
pins that.

Tests: `apps/worker/tests/test_null_columns_render.py`, 31 cases.

### D-091 — `apps/api/tests` is red too, and was never part of the 40

**Severity:** ROUGH · **Affects:** CI
**Status:** `fixed` — `fix/api-suite-drift`

Running the exact CI command (`pytest` from the repo root, Python 3.12, both Poetry projects
installed into one venv) gives **34 failed, 5 errors** in `apps/api/tests` — confirmed pre-existing
by stashing this branch and re-running, identical either way.

These were never in D-054's count, which covered root `tests/` only. **So "the 40" was never the
whole of CI's red**, and fixing them does not turn the pipeline green.

Two causes, both the same family as D-089:

| | |
|---|---|
| `ValueError: not enough values to unpack (expected 15, got 7)` at `services/usage.py:90` | a fake cursor returning a 7-tuple where the code unpacks 15 — a hand-written stand-in that fell behind the query it doubles (23 failures across `test_plans_limits.py` and `test_affiliate_branding.py`) |
| `fixture 'db_session' not found` | 5 errors, a fixture that no longer exists |

**Not fixed in `fix/root-suite-mode`, on purpose.** That branch's ticket is the root suite; folding
in a second suite would double an already large diff and mix two reviews. Filed so it is owned
rather than rediscovered, and because the honest status of this work is *"the root suite is green
and CI is not yet"*.

The unpack mismatch is worth noting for its own sake: it is D-089's lesson in `apps/api`, and the
same remedy applies — a double built from the real query rather than transcribed from it.

> **FIXED, and the triage held: not one of the 39 was a defect this suite had caught.** Six groups,
> all of them the harness failing to REACH the product:
>
> | n | file | signature | what it was |
> |---|---|---|---|
> | 12 | `test_plans_limits` | fake row 7 cols, query selects 15 | the query GAINED per-product limits |
> | 11 | `test_affiliate_branding` | fake row 4 cols, query selects 3 | the query LOST the sponsor column |
> | 6 | `test_accept_invite` | `StopIteration`, 2 rows for 3 `fetchone`s | the route gained a third query |
> | 4 | `test_schedules_report_types` | 401, then 422, then 500 | three seams, peeled one at a time |
> | 4 | `test_billing_checkout` | patched a name the route never imports | the price moved to the plans table |
> | 2 | `test_me_endpoint` | `fixture 'db_session' not found` | a fixture that was never committed |
>
> **The remedy is `apps/api/tests/_query_rows.py`:** `row_for(func, index, **columns)` reads the
> function's own SQL with `inspect.getsource`, extracts the SELECT list, and builds a tuple of that
> width from named columns. A test now says what it means and the ARITY comes from the query, so
> the next column added widens every row automatically and a column removed fails on the NAME, in
> the test, instead of at an unpack inside the production module. It catches arity and order drift
> and nothing else — no types, no column existence, no database — which is exactly what broke here
> and is worth saying so nobody reads more into it.
>
> **Three seams, discovered in order, each hidden behind the last.** `patch('...require_account_id')`
> cannot reach a `Depends` FastAPI captured at import — 401. `app.dependency_overrides` can, and
> still returns 401, because `AuthContextMiddleware` answers before any dependency. The
> `X-Demo-Account` header is the app's own seam and gets through, leaving the real middleware in
> place. Then 422 (the CRMLS city allowlist, added after these tests: "Atlanta" is not a
> California city), then 500 (D-019's verification gate, a query the double predated).
>
> **Seven tests now declare that they need a database** rather than pretending otherwise. The
> schedule and billing routes reach a POOLED connection the fixtures do not patch, so without one
> the request spends ~40s in connection timeouts and 500s. Faking that means faking the data layer
> to assert a URL path, and every query added to the route breaks it again — the treadmill this
> whole ticket is about. They use the `db_session` fixture (added to `conftest.py`, which never had
> it) and skip cleanly. **The coverage they were NAMED for did not need a database at all** and is
> now asserted directly against the schema in `test_every_report_type_is_accepted_by_the_schema`,
> which runs in CI.
>
> **Two assertions turned out to have never been able to pass.**
> `pytest.approx("UPDATE users", abs=50)` is not a flexible match: `approx` on a string falls back
> to equality, so it demanded the SQL be exactly those twelve characters. It had never reported
> that, because the test died earlier on `StopIteration` — fixing the row count is what let it run
> and show itself. §0.6's "a test you have not seen fail", from the other direction.
>
> **CI IS GREEN.** The exact workflow command on Python 3.12, both Poetry projects into one venv:
> **785 passed, 55 skipped, 15 xfailed, 0 failed.**

### D-092 — an unlimited plan was silently capped at 100 reports and blocked at 110

**Severity:** WRONG · **Affects:** any account on a plan whose `monthly_report_limit` is 0
**Status:** `fixed` — `fix/api-suite-drift`

`evaluate_report_limit` treats `limit <= 0` as unlimited and says so
(`usage.py:327`, *"Unlimited plan - no restrictions"*). `resolve_plan_for_account` computed that
limit as:

```python
effective_limit = limit_override if limit_override is not None else (plan_limit or 100)
```

`0 or 100` is `100`. **A plan row meaning "no cap" became a cap of 100**, the unlimited branch could
never fire for a plan-sourced zero, and the account was BLOCKED at 110 reports with a message
quoting a limit nobody had set.

**The file already had the right tool and the right explanation, three lines above.**
`_first_not_none` exists precisely for this, and the comment over `market_limit` says so: explicit
None checks *"so that 0 (freeze-account override) is honoured instead of being skipped by a falsy
`or` chain"*. The same sentence, unapplied one expression later — the D-090 shape exactly, and the
`_median`-returns-0.0 family from D-086 in a third place.

Found by D-091's triage: the test asserting it had been failing inside an unpack error for months,
so the assertion never ran. `default=100` is preserved verbatim — it is a business number, and
changing it is D-093's question, not this fix's.

### D-093 — three numbers each claimed to be the free allowance

**Severity:** ROUGH · **Affects:** accounts with a NULL `plan_slug`
**Status:** `fixed` — `fix/d093-d094-redis-and-free-plan`

`resolve_plan_for_account` sent an account with no `plan_slug` to `plan_slug = "free"` and stopped,
leaving every limit NULL, so it fell through to hard-coded defaults. Four sources disagreed about
what "free" means:

| | |
|---|---|
| `100` | `usage.py`'s `default=` |
| `50` | what `test_plans_limits` asserted |
| `3` | what the `plans` row in **production** says |
| *(absent)* | what `0012_seed_plans.sql` seeds — `solo` and `affiliate`, and no free row at all |

**Fixed by reading the table rather than choosing a number.** The `plans` table is what every
*assigned* plan is read from, and an unassigned account is not a different kind of account — it is
one whose plan nobody wrote down. So it now runs the same query against the same row.

**The test needed no change.** It had always supplied a free-plan row as its second fake answer —
the query the product had simply stopped asking for. Restoring the lookup made an assertion written
in 2025 correct again, which is the clearest evidence available that the removal was the
regression and not the test.

**`0056_seed_free_plan.sql`** adds the missing row so a fresh database matches production. Its
values are not invented: `0051` already assigns `free` its per-product limits (3 / 1 / 1) with an
`UPDATE`, which touches rows that exist and creates none. `monthly_report_limit = 3` matches both
that table and the production row. `ON CONFLICT DO NOTHING`, and no `UPDATE`, so it is inert on
production and cannot overwrite a limit set deliberately there.

**0012 is not edited.** It has been applied, and an applied migration that gains a statement is a
file whose name no longer describes what ran.

### D-094 — a Redis outage took down every authenticated request

**Severity:** BROKEN · **Affects:** the entire API whenever Upstash is unreachable
**Status:** `fixed` — `fix/d093-d094-redis-and-free-plan`

`RateLimitMiddleware.dispatch` called Redis four times — `get`, `setex`, `incr`, `expire` — **with
no exception handling at all**, while the database call sitting between them WAS guarded (*"Use
default 60 if DB fails"*). Degradation had been considered for the database and not for the cache.

With Redis unreachable, `redis.exceptions.ConnectionError` propagated out of the middleware and
every authenticated request returned 500 **before any route ran** — over a component whose entire
job is throttling. Redis is Upstash, a hosted third party, so this is an ordinary event.

> ### THE SAME OUTAGE, REPORTED THREE TIMES, WEARING THREE FACES
>
> **D-009 and D-013 are this defect seen from Phase 2A** — auth failures with `/health` still
> green. That combination looked inexplicable and is now obvious: `/health` is exempted at the top
> of `dispatch` and never touches Redis, so **the one endpoint anybody checks was the one endpoint
> that could not see the problem.** A health check that does not exercise the dependency it shares
> with every other route is a health check for the process, not the service.
>
> Worth reading those two entries with this in hand rather than re-diagnosing them.

**FIXED BY FAILING OPEN — and the middleware above it still fails CLOSED, which is correct.**
The two are different kinds of control and the file is right to answer differently:

| | | |
|---|---|---|
| `_is_token_blacklisted` | **authorisation** | if we cannot check whether a token was revoked, refusing is the only safe answer. Fails CLOSED, and says so |
| `RateLimitMiddleware` | **abuse protection** | if we cannot count requests, refusing converts a Redis outage into a TOTAL OUTAGE — strictly worse than what it protects against. Fails OPEN |

Every Redis call now goes through one `_redis()` helper, so being guarded is a property of the
class rather than of whoever last edited `dispatch` — the previous version had four call sites and
zero guards, which is what happens when each one is somebody's individual responsibility. A test
asserts against the source that no bare `self.r.…` call remains, because the behaviour tests would
all still pass with a fifth unguarded call on a path they do not exercise.

**The cost is stated, not implied: during a Redis outage there is no rate limiting.** With no real
customers that currently costs nothing, and with customers it still costs less than being down.
Every fallback is logged with the defect ID and the operation, and `REDIS_FALLBACK_COUNT` climbs
for as long as the outage lasts, so the loss is visible while it happens rather than inferred
afterwards.

**The response does not claim a count it does not have.** A failed `INCR` means the count is
unknown, and 0 is a count — publishing `X-RateLimit-Remaining: 60` from a store that answered
nothing is D-086 and D-090's mistake in an HTTP header, a fiction a client would throttle itself
against. The header is omitted and `X-RateLimit-Degraded: 1` is set instead.

Tests: `apps/api/tests/test_rate_limiter_degrades.py`, 6 cases, four regressions applied and seen
to fail — including one on the `/health` exemption, pinned so the asymmetry that hid D-009 and
D-013 stays written down where someone debugging an outage will find it.


### D-095 — two identical cache lookups miss each other if the keys were typed in a different order

**Severity:** FRAGILE · **Affects:** anything caching on a payload built at more than one call site
**Status:** `fixed` — `fix/d095-d096-cache-key-and-limiter`

`cache._key` hashes `json.dumps(payload)` with **no `sort_keys=True`**. Python preserves insertion
order, so the same logical payload written two ways produces two different cache keys:

```python
_key("closed_buckets", {"city": "Glendora", "month": "2026-09"})
_key("closed_buckets", {"month": "2026-09", "city": "Glendora"})
# -> different keys.  Measured, not reasoned about.
```

The consequence is a **silent 100% miss rate** between the two call sites — no error, no warning,
just a cache that never hits and a vendor bill that looks like the cache was never there. Same
shape as every other defect on this board that returns a plausible answer instead of an error.

**Harmless today**, which is why it is FRAGILE and not WRONG: the only live cache payload
(`{"type": report_type, "params": params}`, `tasks.py:1311`) is constructed in exactly one place,
so both sides always agree.

**It stops being harmless the moment anything caches from two places**, and the rate-limit analysis
for §7.3 recommends precisely that — caching 12-month bucket counts on *(city, month)* so twelve
report types share thirteen requests instead of making 156. Found while reading the cache for that
analysis rather than by hitting it.

**FIXED: `sort_keys=True` in `_key`.** One argument, applied before the bucket cache lands rather
than after somebody wonders why the bucket cache does nothing — because that is how this defect
would have presented, as an ineffective feature rather than as a bug in the cache.

It **changes every existing key**, so the report cache is cold after deploy. That is safe precisely
because a cache miss has no correctness consequence: the orphans expire on their own TTL and the
next request refills. Worth saying plainly, since "we changed every cache key" sounds like the
expensive part of this and is the cheapest.

`sort_keys` is opt-in and `set()` does not opt in — the stored value's field order is cosmetic, and
sorting it would rewrite every cached blob for no benefit.

Tests: `apps/worker/tests/test_cache_key_stability.py`, 6 cases, including two guards on the fix
itself — distinct payloads must still get distinct keys (a key function returning one value for
everything passes the headline test and destroys the cache), and **list order must stay
significant**, because `sort_keys` sorts mapping keys and must not be "improved" into sorting
sequence values: `["91750", "91711"]` and `["91711", "91750"]` are not interchangeable anywhere
else in the code.


### D-096 — every worker process grants itself the whole vendor rate limit

**Severity:** FRAGILE · **Affects:** every SimplyRETS-backed report, at any concurrency above one
**Status:** `open`

`vendors/simplyrets.py` creates `_limiter = RateLimiter(RPM, BURST)` at **module level**, so under
Celery's prefork pool every worker process holds its own deque and its own 60-requests-per-minute
allowance. No `--concurrency` is set anywhere (confirmed: `schedules_tick.py:683` relies on that
fact for its own reasoning), so the pool is one process per CPU.

The vendor account limit is 60 rpm — the limiter's own docstring cites it. **So with N busy
processes the aggregate offered load is N × 60 against a ceiling of 60, and no limiter can see it,
because each one is counting only its own requests.**

**What happens when the far side refuses.** `_request_with_retries` retries a 429 four times with
backoff 2 → 4 → 8 → 16s, and then makes **one final unguarded attempt** whose `raise_for_status()`
raises. So a sustained 429 does not degrade — it **fails the report**, about 30 seconds later.

**Live today, and independent of anything planned.** This was found while calculating whether
§7.3's 12-month trend line is affordable, and the honest reading is that trend charts *multiply* the
exposure (roughly quadrupling requests per report) rather than creating it. Filing it against the
chart spec would have buried a standing defect inside a design note.

**Not established, and it decides the severity:** whether the vendor's 60 rpm is per account, per
credential, or per source IP. Per account or per credential, this is real as described. Per IP it is
worse — the API service and every worker share one egress. **Nothing in the repository answers
this**, and the limiter's docstring cites "docs" without a link. Filed FRAGILE on the assumption
that it is per account; it is WRONG if that assumption is right and something is already failing at
volume, which has not been checked either.

**Remedies, recorded without choosing one**, because the choice depends on the answer above:

| option | cost | note |
|---|---|---|
| **Shared bucket in Redis** — one window across all processes | a round trip per request | the only option that is correct at any concurrency; Redis is already a hard dependency of the worker |
| **Pin `--concurrency 1`** | throughput | makes the existing limiter true by construction, and 26-schedule bursts already drain roughly serially (`schedules_tick.py:683`), so the practical loss may be small |
| **Divide the allowance** — `RPM // concurrency` per process | none | wrong whenever a process is idle, which is most of the time; wastes most of the budget to avoid a ceiling nobody is near |
| **Leave it and handle 429 properly** | none | the retry path already exists but ends in an unguarded attempt that raises; making that final try retry-aware would turn failures into waits |

> **Also on this entry, because it is the same three lines of code: `burst` is inert.**
> `acquire()` caps at `max(self.rpm, self.burst)`, which is `max(60, 10)` = 60 — the `rpm` value
> always wins, so the "60 rpm **+ burst**" the class docstring describes is an allowance the
> arithmetic cannot reach. Not itself a defect: the effective limit is the stricter of the two, which
> is the safe direction. But `BURST` and `SIMPLYRETS_BURST` are configuration that does nothing, and
> a knob that does nothing is worse than no knob — somebody will turn it.


---

### D-097 — five of the seven brand/text pairs the templates ship fail WCAG AA, and no template derives any of them

**Severity:** WRONG · **Affects:** every PDF, every email and every social card, on five of six themes
**Status:** `open`

The master plan recorded one instance of this: Luxury Estates renders its price in `#0D9488`, which
is **3.74:1** on white. Building the token layer (Workstream A) required measuring the rest, and the
rest is worse.

**Measured, from the values the templates hardcode today:**

| theme | fill | text on the fill | ratio | brand text on white | ratio |
|---|---|---|---|---|---|
| property/teal | `#34D1C3` | `#1a1a1a` | 9.16 ok | `#1abaae` | **2.42 FAIL** |
| property/bold | `#0F1629` | `#ffffff` | 17.99 ok | `#15216E` | 14.24 ok |
| property/classic | `#1B365D` | `#ffffff` | 12.12 ok | `#1B365D` | 12.12 ok |
| property/modern | `#FF6B5B` | `#ffffff` | **2.80 FAIL** | `#d94e3f` | **4.11 FAIL** |
| property/elegant | `#1A1A1A` | `#ffffff` | 17.40 ok | `#1a1a1a` | 17.40 ok |
| market (theme default) | `#0d9488` | `#ffffff` | **3.74 FAIL** | `#0f766e` | 5.47 ok |
| market (base fallback) | `#0d9488` | `#ffffff` | **3.74 FAIL** | `#0d7268` | 5.79 ok |

`#1abaae` at **2.42:1** is the worst value on the board and it is the teal theme's designated
"brand colour on a light surface" — the slot whose entire job is to be readable. The market
surface repeats the Luxury Estates defect in a different slot: white label text on the teal fill,
also 3.74:1, because `--accent-text` defaults to `#ffffff` regardless of what the fill is.

> **THE EMAIL SURFACE IS DONE (`feat/workstream-c-email-rebuild`).** Measured with a walker that
> resolves the real background for every text run in a rendered document:
> **1,167 unreadable runs out of 3,822 → 0**, across seven brands × eight report types.
> `apps/worker/tests/test_email_contrast.py` holds it there. What is left below is the PDF and
> template half, which is Workstream D's migration.
>
> The email measurement found four things this entry did not have:
>
> - **`_build_quick_take` painted one brand colour on another.** Label and panel arrived as two
>   independent arguments with nothing relating them: `#8b5cf6` on `#0d9488` is 1.13:1, and an
>   account that sets ONE colour rather than two got **1.00:1 — invisible text**. The master plan's
>   B3 recorded 1.4:1 from a sample render; that was the same bug with different brand values in it.
> - **The email's own default brand was unfixable.** `#6366f1` sits inside D-098's band (4.47:1), so
>   no choice of label cleared AA — on the default, which is what every unbranded account ships. It
>   also disagreed with `templates.ts` and `social-templates.ts`, both of which default to `#4F46E5`
>   (6.29:1). Changing a **default** does not violate the fill-is-the-affiliate's rule: nobody chose
>   it. Now aligned, and the PDF and the email finally match for an unbranded account.
> - **`§3.1`'s ink target assumes a white card and the design ships near-white ones.** The metric
>   strips are `#f8fafc`, the rows `#f9fafb`, the stat cells `#f1f5f9`. Luxury Estates' ink is
>   4.63:1 on white and **4.43:1** on `#f8fafc` — passing the specification and failing the reader.
>   The email derives against its darkest light surface; whether the cards should simply be white is
>   a design decision and is **[JERRY]**.
> - **The status palette failed its own text.** White on `#16a34a` is 3.30:1 and on `#f59e0b` is
>   2.15:1. Now `#15803d` and `#b45309` (5.02 each), both already used in the PDF templates.

**Why every one of these is a hardcoded literal.** Nothing derives a readable value from the
affiliate's colour, because until now there was nothing to derive it with. `apps/worker/src/worker/
themes.py` (`derive_theme`, Workstream A) now does; **no template consumes it yet**, which is why
this entry is open rather than fixed.

**Scale of the literals, measured rather than estimated.** `scripts/lint_template_colors.py`
reports **111 brand hex literals across 26 of 30 template files** — 92 of them sitting directly in
a brand-role custom property (`--primary-color`, `--color-accent`, `--pct-blue`, or a
`default('#…')` fallback for one). Recorded in `scripts/template_color_baseline.txt` as a ratchet:
CI fails on a new one, and retiring them is the migration that closes this entry.

> **The derivation is done and deliberately not wired.** Substituting the tokens changes what
> ships: 12 of 17 brand-role values move by more than ΔE 2.3 (the just-noticeable threshold), and
> two move by ΔE 93 — `--coral-text` and `--accent-text` go from white to `#14151a`, because white
> on coral is 2.80:1 and white on teal is 3.74:1 and near-black is the readable choice on both.
> Those moves **are the fix**, not a side effect of it, but Workstream A was specified to ship
> invisibly and it cannot. Reported rather than absorbed.

**Two smaller things found in the same measurement, recorded here rather than filed separately:**

- **The bold theme declares two different primaries.** `bold.jinja2:21` defaults `theme_color` to
  `#0F1629`; `bold_report.jinja2:13` defaults the same variable to `#15216E`. Whichever is right,
  the two files disagree about what the theme is when branding is absent.
- **The market surface disagrees with itself about its own fallback.** `_base/base.jinja2:28` has
  `--accent-on-light: #0d7268`; `market.jinja2:12` has `#0f766e`. Both are teal, neither is
  derived, and which one renders depends on whether the theme block is reached.

### The `--*-light` / `--*-on-dark` gap, surveyed before deriving anything

*2026-09-23, at Jerry's instruction: **"survey before deriving… report which before proposing
either."*** Every `var()` reference to one of these tokens was read and classified by the CSS
property it lands in. The answer is cleaner than the question assumed, and it is **one token, not
two**.

**The `-light` family paints nothing that carries text.**

| token | themes | uses | as text | decorative | verdict |
|---|---|---|---|---|---|
| `--accent-light` | market | 6 | 0 | 6 | panel backgrounds, a photo border, a pill border |
| `--color-primary-light` | 5 property themes | 12 | 0 | 12 | chart wraps, cover washes, one gradient stop |
| `--color-accent-light` | 5 property themes | 17 | **3** | 14 | see below — the three are a dark-surface case |
| `--coral-light` | modern | 1 | 0 | 1 | a background |
| `--teal-light` | teal | **0** | — | — | **declared, never referenced** |
| `--navy-light` | classic, bold | **0** | — | — | **declared, never referenced** |
| `--gold-light` | elegant | 11 | 4 | 7 | not brand-derived — elegant's fixed gold, outside this question |

The three text uses of `--color-accent-light` are all in `classic` — `.cover-property-type`,
`.analysis-intro-title`, `.range-stat-label` — and all three sit on a **dark** panel (their
siblings are `rgba(255,255,255,0.8)` on the same surface). So they are not a counterexample; they
are the same case as the row below, wearing the wrong token name.

**Conclusion: `-light` is decorative and needs no brand derivation.** `tint` covers the pale
backgrounds and `primary_dark` the darker washes. Nothing in this family needs a contrast
guarantee, and the token set is not short on its account.

**The `-on-dark` family is text, every time.**

| token | themes | uses | as text | what it paints |
|---|---|---|---|---|
| `--teal-on-dark` | teal | 10 | 10 | cover labels, section headings, stat numbers |
| `--coral-on-dark` | modern | 4 | 4 | cover label, aerial-card headings |
| `--accent-on-dark` | market | 1 | 1 | the header band's highlighted span |
| `--navy-on-dark` | classic, bold | **0** | — | **declared, never referenced** |

**So the gap is one token: a brand value readable on a DARK surface.** `primary_ink` guarantees
≥4.5:1 **on white**; §3.1 has no concept of a dark surface at all, while three property themes and
the market header put brand-coloured text on one. `on_primary` is not it — that is text on a
*brand fill*, not brand text on a dark neutral.

Not proposing a derivation here, per the instruction. What the decision needs to settle: whether
the dark surface is a fixed neutral the token can be derived against (the live
`compute_color_roles` assumes `#18235c`, and the themes' actual darks are `#18235c`, `#0f1a45`,
`#0b0f1a`, `#1a1f36`) or a per-theme value the derivation has to take as an argument. **[JERRY]**

> **ANSWERED 2026-09-23 (Jerry): one fixed dark neutral, not per-theme.** *"§3.2 already fixes
> neutrals for this reason, and five surfaces means five drift paths."*
>
> D-099's work was evidence for that reading: widening `compute_color_roles` to accept several dark
> surfaces was necessary for the market band, and the very first thing it produced was a surface
> pair no colour can satisfy.
>
> **Built** on `feat/workstream-c-consolidation`. `worker.themes` gains a sixth token,
> `primary_on_dark`, derived against `DARK_SURFACE = #0f172a` — the dark neutral these templates
> already use most, chosen so the token converges on the design rather than adding to it, and a
> genuine neutral where the previous default `#18235c` has chroma 68 and is somebody's brand colour
> doing a neutral's job. Locked in the golden file with its achieved ratio, as D-099 established.
>
> **The condition, measured and asserted rather than noted.** Six of the eight dark surfaces these
> templates paint today are lighter than `#0f172a`, so the token does not clear AA on them:
> **3.24:1 on classic's `#1B365D`**, 3.80 on bold's `#15216E`, 3.91 on `#18235c`, 4.47 on
> `#0f1a45`. That is the migration the decision implies — the dark panels become the neutral — and
> until it happens `primary_on_dark` is correct about a surface the page does not yet have. The
> four shortfalls are asserted exactly in `test_the_guarantee_is_against_the_fixed_surface_and_no_other`,
> so the list fails when a panel migrates instead of going quietly stale. **Filed as D-100** so the
> migration is on the board rather than living only in a test assertion.

**Two more AA failures, found by this survey and belonging to this entry:**

| where | value | on | ratio |
|---|---|---|---|
| market `.header-subtitle span` | `#5eead4` | the header gradient's far end, `#0d9488` | **2.53 FAIL** |
| classic `.analysis-intro-title` etc. | `#a89070` | the navy panel, `#1b365d` | **3.98 FAIL** |

The market one is conditional and stated as such: the band is
`linear-gradient(135deg, header-bg 0%, header-bg 50%, primary-color 100%)`, so it measures 9.90:1
against `#18235c` at the left and 2.53:1 where the teal takes over. Whether real text lands past
the midpoint depends on layout and has not been rendered to check — but a token whose contrast
depends on where on the band it falls is not a token that can be verified, which is the defect
regardless of today's layout.

**Ten dead tokens, not three.** The survey read the template SOURCE; rendering all five property
reports and counting `var()` references against the declarations in the output gives the real
number:

| theme | declared and never referenced |
|---|---|
| modern | `--coral-dark`, `--coral-text` |
| teal | `--teal-light`, `--teal-text`, `--soft` |
| classic | `--navy-light`, `--navy-on-dark` |
| bold | `--navy-light`, `--navy-on-dark`, `--gold-light` |

49 variables are live; these 10 are not. They are the only literals that can be retired with
provably zero visual change, since nothing reads them.

> **THIS CORRECTS A CLAIM MADE ON D-099'S PULL REQUEST, AND THE CORRECTION MATTERS.** That PR said
> `modern.theme_color_text` flipping white → `#14151a` was *"the largest visual change this project
> has shipped"* and asked for it to be reviewed before the consolidation. **`--coral-text` is
> declared and referenced nowhere. It renders on no page.** So does `--navy-on-dark`, which carried
> the chroma 33 → 156 improvement on classic and bold — also nowhere.
>
> Rendering the five reports and counting `var()` references is a ten-line check that would have
> caught it before the claim was made. Measuring the derivation is not the same as measuring the
> page, and this board has the rule for it already: §0.6, *no finding derived from a sample render
> counts until it is reproduced through the production path* — applied here in the other direction,
> to a finding derived from a function without checking whether the page consumes it.
>
> **What D-099 actually changes on rendered output, in full:** `modern --coral-on-light`
> (`#f46657` 3.05 → `#c55145` 4.53, 4 uses), `teal --teal-on-light` (`#27a196` 3.32 → `#1f847c`
> 4.52, 4 uses), and on the market report `--accent-on-light` (`#0D9488` 3.74 → `#0b8277` 4.69,
> 5 uses) and `--accent-on-dark` (`#5eead4` 2.53 → `#ffffff` 3.74 worst-case, 1 use). Five values.
> All small labels, contents numbers and comparable prices on light cards — no cover changes at all.


---

### D-098 — `on_primary` cannot reach 4.5:1 against every fill, and the spec asks it to

**Severity:** ROUGH · **Affects:** label text on a brand fill, for roughly 5% of pickable colours
**Status:** `open`

Master plan §3.1 defines `on_primary` as *"whichever of white or `#14151A` scores higher against
primary"*. §4.2 then requires `contrast(on_primary, primary) >= 4.5` for every input. **The first
cannot deliver the second, and the arithmetic says so without needing an experiment.**

Both candidates are fixed. Their contrast against a fill of luminance *L* is `1.05 / (L + 0.05)`
for white and `(L + 0.05) / 0.0576` for `#14151A`. The two curves cross at *L* = 0.196, where each
scores **4.27:1** — so that is the best any binary choice between them can do, for the worst fill.

**Measured:** 1,056 of 20,000 random sRGB colours (**5.3%**) fall under 4.5:1. Worst observed
`#9158f5` at 4.27:1. Two of the six live themes are close to the band but clear it (Demo Title and
Violet at 4.83 and 5.70); nothing shipping is currently affected.

This is a finding about the spec, not a bug in the code. `themes.py` implements §3.1 exactly.

> **THE SPEC WAS WRONG, AND ITS AUTHOR SAYS SO.** Recorded at Jerry's instruction, 2026-09-23:
> *"D-098 is my error — I approved an acceptance criterion §3.1 can't satisfy."* Noted here
> because the natural reading of an unsatisfiable test is that the implementation is behind, and
> the natural response is to change the implementation until the test passes. It is the criterion
> that is behind. Nothing in `themes.py` should be adjusted to close this entry.

**XFAILS THIS DEFECT GATES** (§0.6: two-way link, or an xfail is a skip with better manners).

- `apps/worker/tests/test_themes.py::test_on_primary_clears_aa_against_the_fill_for_5000_random_colours`
- `apps/worker/tests/test_color_roles.py::test_text_on_accent_clears_aa_for_5000_random_brands`

**The second one is the PDF path, and it matters that it exists.** This entry
reads like a fact about `themes.py`; it is a fact about **any** binary choice of
text against a fill that may not be adjusted. `property_builder._text_on_accent`
arrives at the same ceiling independently — measured 278 of 5,000 brands (5.6%)
below 4.5:1, worst 4.27:1, from a different function written years apart. Fixing
`derive_theme` alone would leave half the product short.

Strict, so it breaks the build the day the derivation can satisfy it. The achievable bound is
asserted live alongside it by `test_on_primary_always_reaches_the_achievable_ceiling`, so a change
that makes `on_primary` *worse* still fails today.

**DECIDED, 2026-09-23 (Jerry). `on_primary` may NOT adjust the fill.**

> *"The fill is the affiliate's chosen colour and the one value in the system that's theirs.
> Contrast is satisfied by choosing the text, never by moving the brand. If that makes a pair
> unreachable, that's D-098's ~5% and it degrades to the best available contrast with the bound
> asserted — not to a modified brand."*

This closes the only remedy that would have delivered §4.2's property, so the property stays
unreachable **by design** rather than by omission. That is the point of recording it: a later
reader who finds the strict xfail and reasons "we just need `on_primary` to nudge the fill" is
about to undo a decision, not fix an oversight.

`primary` is now a **constraint**, not merely an output — it is returned exactly as given, and
`test_luxury_estates_is_fixed_specifically` already asserts that for the one theme where the
temptation is strongest. A test naming the rule in general terms is worth adding when this entry
is next touched.

**Remedies still open**, all three of them documentation-shaped rather than code-shaped:

| option | cost | note |
|---|---|---|
| **Accept 4.27 and say so** | the shortfall is undocumented outside this entry | cheapest; the measurement is already here, and the live test asserts the achievable bound |
| **Accept 3:1 for this pair** | none | WCAG AA asks 3:1 for large text and UI components, and `on_primary` mostly carries badge and button labels; needs the type sizes checked, not assumed |
| **Restrict the picker** | affiliates lose ~5% of the colour space | §3.1 explicitly promises the opposite: *"the picker needs no restrictions"*, and the decision above is the same principle — so this is listed for completeness and is probably already ruled out by it |
| ~~Let `on_primary` adjust the fill~~ | — | **REJECTED above.** |


---

### D-099 — the readability helpers target 3.0:1 while their own docstring says 4.5, and hand back unchecked values

**Severity:** WRONG · **Affects:** every property PDF and market PDF; the email until this branch
**Status:** `fixed` (`fix/d099-readability-helpers`)

> **FIXED.** The target is 4.5, the ratio comes from `worker.themes.contrast` — the same instrument
> checked against the master plan's six independent measurements — and neither helper returns a
> value it has not verified. Where a target is genuinely unreachable it returns the best available,
> increments `UNREACHABLE_CONTRAST_COUNT` and logs, which is the D-094 pattern: a degraded path that
> is silent is a path nobody knows they are on.
>
> **Every role on every theme now clears 4.5**, locked with its achieved ratio in
> `apps/worker/tests/golden/color_roles.json` — the number D-099 was about, finally written down.
>
> **What moved.** 7 of the 15 role values on the five property themes shift past ΔE 2.3, and every
> one of the seven goes from failing to passing. The largest is `modern.theme_color_text`: white to
> `#14151a`, ΔE 93, because white on that coral measures 2.80:1. The eight that do not move are the
> eight that already passed — a colour clearing the bar is returned untouched.
>
> **`_ensure_readable_on_dark` no longer trades the brand away to get bright.** It shed 0.02 of
> saturation on *every* step; it now raises HSV value first and spends saturation only once value
> has maxed out. On the three themes where the brand *is* the dark surface that is the difference
> between a colour and a grey: classic `#929fb3` (chroma 33) becomes `#639fff` (chroma 156), both
> clearing 4.5.
>
> **`_text_on_accent` was a threshold, not a comparison** — `white if luminance < 0.35 else dark`.
> The crossover for that pair is at luminance 0.196, so a whole band of mid-tone brands got white
> when near-black wins. That is what put white on the modern coral.
>
> **`dark_bg` may now name several surfaces**, and the result clears the bar against all of them.
> `market_builder` passes both ends of its header band, which is the D-097 finding about a token
> whose contrast depends on where along the gradient it falls.
>
> > **And the first thing that change found: the market band is unsatisfiable as designed.** No
> > single text colour clears 4.5:1 against both `#18235c` and a mid-tone brand — brightening runs
> > to white, which fails on the accent; darkening runs to near-black, which fails on the navy. The
> > helper returns the best worst case (white, 3.74:1 against the accent end, up from the shipped
> > 2.53:1) **and says it fell short**. That is a defect in the band, not in the function, and it is
> > the new guarantee earning its place on its first real call. Recorded on D-097; the remedy is a
> > design decision — narrow the gradient, move the label off the changing part, or accept 3:1.
>
> Nine regressions applied and each seen to fail, including target back to 3.0, `on_light` always
> black, `on_dark` always white, the unreachable report suppressed, the old desaturate-every-step
> brightening, the old luminance threshold, and binding a gradient on its first stop only.

`property_builder._ensure_readable_on_light` and `_ensure_readable_on_dark` exist to make a brand
colour readable. Neither does.

**The threshold is 3.0.** `_ensure_readable_on_dark`'s docstring reads *"Target: WCAG AA (contrast
ratio ≥ 4.5) or at minimum 3.0 for large text."* Its code checks `if ratio >= 3.0` on entry and
`if new_ratio >= 3.0` in the loop. 4.5 appears nowhere in either function. **The docstring states
one threshold and the code enforces another**, which is the same shape as D-083 and D-088 — a
comment that is the only place a contract is written down, disagreeing with the code under it.

**Measured**, through `compute_color_roles(hex, dark_bg=hex)`:

| brand | `theme_color_on_light` | on white | `theme_color_on_dark` | on the fill |
|---|---|---|---|---|
| Demo Title `#DC2626` | `#DC2626` | 4.83 ok | `#ffbaba` | **2.99** |
| Luxury Estates `#0D9488` | `#0D9488` unchanged | **3.74** | `#4effef` | **3.01** |
| Coastal `#0E7490` | `#0E7490` | 5.36 ok | `#50d9ff` | **3.24** |
| Amber `#F59E0B` | `#cc8309` | **3.08** | `#ffdda4` | **1.65** |
| Lime `#84CC16` | `#69a311` | **3.07** | `#e1ffb4` | **1.80** |
| Violet `#7C3AED` | `#7C3AED` | 5.70 ok | `#ccaeff` | **3.00** |

`theme_color_on_dark` **never clears 4.5 on any theme** — it cannot, because it stops at 3.0. The
three that pass on light do so by being readable already; the function changed nothing.

**Two more faults in the same twenty lines:**

- **They return an unchecked value.** After 30 iterations both `return` whatever the loop last
  produced, without re-testing. A caller cannot distinguish "readable" from "gave up", and there is
  no log line either way.
- **`_ensure_readable_on_dark` desaturates as it brightens** (`s -= 0.02` per step). Thirty steps
  removes 0.6 of saturation, so the escape hatch from an unreadable brand colour is to stop it being
  the brand colour.

**And it was called against the wrong background.** `email/template.py` computed
`compute_color_roles(accent_color, dark_bg=primary_color)` and rendered the result on a panel
painted with `accent_color`. Derived against one surface, displayed on another. That call is gone
on this branch; the same pattern should be checked wherever `compute_color_roles` is still used.

**Not fixed here.** `worker.themes.derive_theme` (Workstream A) does this correctly and the email
now uses it; `compute_color_roles` remains live on both PDF paths (`property_builder.py:1247`,
`market_builder.py:25`) and replacing it there moves rendered output, which is D-097's migration
and is reviewed per surface. Filed so the migration has a defect to close rather than a preference
to justify.

> Worth stating plainly: **this is why measuring found what reviewing did not.** The function is
> named `_ensure_readable_on_light`, its docstring cites WCAG AA, and it is called on every render.
> Everything about it reads as a guarantee. Only the number is wrong, and only running it says so.



---

### D-100 — four dark panels are lighter than the fixed dark neutral, so `primary_on_dark` is true about a surface the page does not have

**Severity:** ROUGH · **Affects:** brand-coloured text on a dark panel — teal, bold and classic property reports
**Status:** `open`

Filed as the consequence of a decision, not as a bug in the code it constrains.

Jerry decided (2026-09-23) that the dark surface behind brand text is **one fixed neutral for every
theme**, not a per-theme value: *"§3.2 already fixes neutrals for this reason, and five surfaces
means five drift paths."* `worker.themes.DARK_SURFACE = #0f172a` implements that, and
`primary_on_dark` is guaranteed against it.

**The templates do not paint that neutral.** They paint eight different dark surfaces, four of them
lighter than `#0f172a`, and a value that clears 4.5:1 on a darker surface does not clear it on a
lighter one. Measured with Luxury Estates' token (`#0d9488`):

| surface | where | ratio |
|---|---|---|
| `#0b0f1a` | teal `--ink` | 5.11 ok |
| `#0f1629` | bold `--color-text` / primary | 4.81 ok |
| `#111827` | shared neutral ink | 4.74 ok |
| `#1a1a1a` | elegant `--charcoal` | 4.65 ok |
| `#0f1a45` | teal cover overlay | **4.47** |
| `#18235c` | teal `--navy` | **3.91** |
| `#15216e` | bold `--navy` | **3.80** |
| `#1b365d` | classic `--navy` | **3.24** |

**TWO OF THE FOUR ARE NOT A REPAINT. READ THIS BEFORE ESTIMATING THE ENTRY.**

| surface | what it is | what closing it takes |
|---|---|---|
| `#18235c` teal `--navy` | a flat fill | repaint to `#0f172a` |
| `#15216e` bold `--navy` | a flat fill | repaint to `#0f172a` |
| `#1b365d` classic `--navy` | a flat fill | repaint to `#0f172a` |
| `#0f1a45` teal cover overlay | **not a surface at all** — `rgba(15,26,69,.3)` → `.7` → `.95` over an arbitrary listing photo passed through `brightness(.6)` | a different problem; see below |

**THE FOURTH IS NOT A HARDER VERSION OF THE OTHER THREE. IT IS A DIFFERENT PROBLEM.**

The other three are flat fills with a wrong value: pick the right one and the contrast is decided
forever. The teal cover overlay **has no fixed background to guarantee anything against**. Its
backdrop is a three-stop alpha gradient composited over whichever photo the listing happens to
carry, so the effective colour behind a glyph differs from the top of the panel to the bottom, and
differs again for every property in every report. There is no value to compute a ratio from.

**No choice of text colour can make that surface AA-compliant**, because contrast is a relation
between two colours and one of them is unknown at render time and variable within a single panel.
That is not a decision waiting to be made; it is a category the current design cannot satisfy.

The remedies are correspondingly different in kind — none of them is "pick a neutral":

- a **scrim**: a fixed opaque or near-opaque layer between photo and text, which then IS a surface
  and can be guaranteed against
- a **solid plate** behind the text block only, leaving the photo visible around it
- **move the text off the image** entirely

D-099 reached the same wall from the other side: the market header runs navy → accent and no single
text colour clears 4.5:1 against both ends, which is why `_ensure_readable_on_dark` returns the best
worst case and logs that it fell short. Two surfaces, one conclusion — **a background that varies
cannot be made accessible by choosing a foreground.** Both need a design change. **[JERRY]**

**Three of the four are the repaint.** Those panels become `#0f172a`, and then the token is true
about the rendered page rather than about a surface the design intends. Note what the three worst
are: `#18235c`, `#15216e` and `#1B365D` are **brand navies being used as neutrals** — which is the
exact confusion the fixed-neutral decision exists to end. `#18235c` has chroma 68. A neutral with
chroma 68 is somebody's brand colour doing a neutral's job, and it is why the old
`compute_color_roles` default was wrong in kind and not only in value.

**Why this is not folded into the consolidation.** Repainting a panel is a visible change and the
consolidation is a pure restructure whose acceptance is an empty render diff. Putting them in one
branch would mean a diff that is supposed to be empty and is not, with no way to attribute a row to
either. Separate entry, separate change.

**Already asserted, exactly:**
`apps/worker/tests/test_themes.py::test_the_guarantee_is_against_the_fixed_surface_and_no_other`
pins the four shortfalls by value. It **fails when a panel migrates**, which is the point — the
list is a checklist that breaks rather than a comment that goes stale. Closing this entry means
that test's expected set becoming empty.

> **Why the split above matters for planning.** Read quickly, this entry looks like four lines in
> four templates. Three of them are. The fourth is not a line at all — it is a change to how that
> panel is composed, and the market header band is the same change again on another surface. An
> estimate that treats the entry as uniform will be wrong by the only part that is not a repaint.


---


### D-101 — the "view in browser" link on a market report opened a different build than the PDF

**Severity:** WRONG · **Affects:** every market report — `report_generations.html_url`, surfaced in the app in three places
**Status:** `fixed` — `feat/workstream-d-market-pdfs`, code + migration 0057

One report, two renderings, and a customer could open both.

**The PDF** is built by `MarketReportBuilder` (`tasks.py:1676-1708`), server-side, from
`templates/market/`. It is the only market-report PDF path: all three `render_pdf` call sites in
the worker pass `html_content`, so the `html_content=None` branch that navigates to
`/print/{run_id}` has no caller.

**The link was that URL anyway.** `render_pdf` built `print_url = f"{effective_base}/print/{run_id}"`
unconditionally and returned it whether or not the render had come from it (`pdf_engine.py:83`
and `:163`). Confirmed by reading both renderers end to end: **when `html_content` is passed,
`print_url` is used for nothing inside either function.** It is not in the PDFShift payload, not
navigated to, not logged as the source — it is only returned. The docstring called it *"the
URL/HTML that was rendered"*, which in that case it was not. `tasks.py:1700,1750` wrote it to
`report_generations.html_url`.

**That route renders the legacy build**: `apps/web/app/print/[runId]/page.tsx:141-148` maps each
report type to one of the seven `apps/web/templates/trendy-*.html` files and a builder in
`apps/web/lib/templates.ts`. The differences are not cosmetic:

| | PDF (`MarketReportBuilder`) | that route (`/print/{runId}`) |
|---|---|---|
| table rows per page | 13 on page 1, then 25 — CSS flow | fixed 15 (`ROWS_PER_PAGE = 15`, three call sites) |
| gallery cards per page | 6 then 9 | fixed 6 (`CARDS_PER_PAGE = 6`) |
| branding | themed header, Outfit, AI narrative | none of those — `tasks.py:1592` says the legacy path *"produced unbranded PDFs missing the Outfit font, themed header, and AI narrative"* |
| `open_houses` | its own gallery render | reuses the inventory template (`page.tsx:146`) |

**CORRECTION to this entry as first filed.** It said the link was *"shown in the app and sent to
customers"*. The second half was taken from `apps/worker/ENV_TEMPLATE.md:62`, which describes it
as a *"view in browser"* link *"shown to customers"* — prose, not code. **The email does not carry
it.** `email/send.py:182-216` builds the CTA from `pdf_url`, so the email and its attachment agree.
The exposure is the app UI (`components/report-builder/index.tsx:213`,
`app/app/reports/[id]/page.tsx:292`, `app/app/reports/page.tsx:107`) and the `report.completed`
webhook payload (`tasks.py:1943`). Narrower than filed, and worth correcting rather than leaving a
claim sourced from a doc.

**The fix, both halves.**

1. **`render_pdf` no longer returns a URL that rendered nothing.** The second element of its return
   is now `None` whenever `html_content` was passed, in both engines, with the reason at the
   return and at the call site. `apps/worker/tests/test_pdf_source_url.py` asserts both directions
   — the HTML path returns None *and* the URL path still returns its URL, because a test for the
   first alone also passes against a function that returns None always. Three regressions applied
   and seen to fail: each engine reverted to the old behaviour, and the over-correction.
2. **Migration 0057 clears the rows already written.** The code fix is forward-only; every existing
   row keeps its link and the app keeps showing it. `0057_clear_stale_view_in_browser_links.sql`
   nulls `html_url` where it matches the print path. Nothing is lost that cannot be reconstructed
   from the row's own id — and what would be reconstructed is the wrong document.

**The link is now gone rather than corrected, and that is a product gap, not a fix.** Restoring
"view in browser" means serving the `html_content` that was actually rendered — it is already
self-contained, with images base64-embedded before the PDF call — at a URL. That is separate work
and not filed as a defect, because nothing is currently wrong; something is merely absent.

**ANSWERED 2026-09-24 — `INTERNAL_RENDER_TOKEN` is NOT set** (Jerry, from recollection; asked to
confirm from the Vercel dashboard, and this entry should be updated with which it was).
`apps/api/ENV_TEMPLATE.md:95` says that when it is empty the data route is disabled and
`/print/{runId}` renders *"Report Not Found"*.

**So the realised harm is zero.** Nobody ever saw the legacy build through this path — a customer
clicking "view in browser" got an error page, not a different report. The defect was real and the
exposure was not, and those are worth recording as two separate facts rather than one. It also
means migration 0057 removes an error page rather than a wrong document, and the second thing this
answer might have created — chasing who saw what — does not exist.

**An evidence-class note, because this entry got it wrong once already.** Both halves of this
paragraph and the "sent to customers" claim corrected above come from `ENV_TEMPLATE.md`, which is
prose about runtime behaviour. It was right this time and wrong last time, and neither outcome
makes it evidence. It is the same class as reading a docs page for production's Postgres version
(§0.6, *a description of what code does is a hypothesis*): a documented environment variable is a
statement about a deployment, and only the deployment can confirm it. Hence the ask to check the
dashboard rather than closing on the recollection.

**Do not resolve the route by deleting it.** `docs/DEAD_CODE.md:34` exists because two separate
documents declared `/print/[runId]` removed while it was live. This entry is evidence it is live in
a way neither considered — reachable by a person, not by the renderer.

### D-102 — the three report types documented as one page all render two

**Severity:** ROUGH · **Affects:** `market_snapshot`, `price_bands`, `featured_listings` PDFs
**Status:** `fixed` — `feat/workstream-d-market-pdfs`; page-1 composition decided and built

`market_builder.PDF_CONFIG` splits the eight types into two modes in its own comment:

> SNAPSHOT (**1-page**, curated sample): market_snapshot, price_bands, featured_listings
> CATALOG (multi-page, ALL matching listings): closed, inventory, new_listings, new_listings_gallery, open_houses

Measured through the production path — `MarketReportBuilder` → Letter with PDFShift's reservations
(1.4in top, 1.0in bottom) → Chromium's paginator, `scripts/measure_market_pagination.py`:

| report type | cap | pages | listings per page |
|---|---|---|---|
| `market_snapshot` | 9 | **2** | 3, 6 |
| `price_bands` | 8 | **2** | 4, 4 |
| `featured_listings` | 12 | **2** | 6, 6 |

All three spill. The caps are set as though the first page held the whole sample and it does not:
page 1 carries the hero stat, the section header and the narrative, so it holds roughly a third to
a half of what a continuation page holds.

**The measurement is conservative.** The fixture renders with `photo_url: None` because the
container has no network. Real listings carry photos, which make cards taller, so a real render
cannot be shorter than this one.

**MEASURED 2026-09-24 — page 2 is pure listing spillover, and it is not a few orphans.** Asked
directly: is page 2 a whole section, or a couple of rows that did not fit? Neither. Extracting
page 2's text for each type, it contains **nothing but listing cards** — no heading, no section, no
footer content — and it holds between a half and two thirds of the sample:

| report type | cap | page 1 | page 2 | page 2 contains |
|---|---|---|---|---|
| `market_snapshot` | 9 | 3 | **6** | six listing cards, nothing else |
| `price_bands` | 8 | 4 | **4** | four listing cards, nothing else |
| `featured_listings` | 12 | 6 | **6** | six listing cards, nothing else |

So the config is wrong rather than the pagination: the caps are two to three times what page 1
holds. They were set to the size of a good sample without anyone measuring the page it had to fit
on.

**Page-1 capacity is now a fixed number, which makes the cap a decision someone can actually
make.** Before §7.2's narrative box was fixed, capacity moved with the copy and there was no number
to set a cap against. It is now pinned per type in
`apps/worker/tests/test_narrative_box.py::PAGE_1_CAPACITY` — 3 for `market_snapshot` and
`price_bands`, 6 for `featured_listings`, with a narrative.

**THE DECISION, IN THE TERMS IT SHOULD BE DECIDED IN — [JERRY].** This is not a pagination target
and it is not blocking anything. It is one trade, and both sides are already measured, so it can be
settled without re-deriving any of it:

| | keep the cap | cut the cap to page-1 capacity |
|---|---|---|
| `market_snapshot` | 9 listings, **2 pages** | 3 listings, **1 page** |
| `price_bands` | 8 listings, **2 pages** | 3 listings, **1 page** |
| `featured_listings` | 12 listings, **2 pages** | 6 listings, **1 page** |

**Page count against sample size, and nothing else moves.** Cutting the cap does not change the
layout, the metrics, the narrative or the branding — only how many listings the agent's client
sees. Keeping it does not break anything either; it makes `PDF_CONFIG`'s own "1-page" comment
false, which is what this entry is.

A third answer is available and costs nothing: keep the caps and **correct the comment** to say
these are two-page reports. That closes the defect as filed — a comment disagreeing with the
renderer — and leaves the product exactly as it is.

Whichever is chosen, the capacities are pinned in
`apps/worker/tests/test_market_layout_map.py` (caps) and
`apps/worker/tests/test_narrative_box.py::PAGE_1_CAPACITY` (what page 1 holds), so the two cannot
drift apart again without the suite saying so.

**THE BREAKDOWN, 2026-09-25 — and it sharpens the question rather than answering it.** After §7.1
variant A, `market_snapshot`'s page 1 holds **zero** listings, with all nine on page 2. That is a
count; here is what is actually on the page, measured element by element with margins included:

| page 1 of `market_snapshot` | | |
|---|---|---|
| masthead | 1.39in | 14% |
| hero stat | 1.14in | 12% |
| narrative box | 1.42in | 15% |
| stats bar | 2.42in | 25% |
| section heading + truncation note | 0.78in | 8% |
| **used before a single listing** | **7.15in** | **74%** |
| free | 2.52in | |
| a row of three cards | 2.77in | |

**Page 1 misses its card row by 0.25in.** Not by a page, not by half a page — by a quarter inch out
of nine and two thirds. And **3.56in of page 1, 37%, is two metric blocks presenting FIVE numbers**
(`hero-stat` 1.14in and `stats-bar` 2.42in). *An earlier note here said six; it is five, counted
off the markup.*

**WHAT THE FIVE ARE, AND WHETHER ANY IS SAID TWICE.**

| block | figure | set at |
|---|---|---|
| `hero-stat` | Median Sale Price | 56px |
| `stats-bar` | Avg Days on Market · Months of Inventory (+ pace) · Price per Sq Ft · List-to-Sale Ratio | 14px |

**Nothing is duplicated.** The hero carries a figure the stats bar does not, and no stats row
restates another. So on the face of it the trim is a trade rather than a free saving.

**It is not, and this is the part that decides it: the 0.25in is available entirely from
whitespace.**

| | |
|---|---|
| `stats-bar` own top + bottom margins | **0.50in** |
| the four rows together | 1.90in (0.474in each: 14px of text in 10px/10px padding) |
| the shortfall to recover | **0.25in** |

The stats bar's own margins are twice the shortfall, on a block that already sits between two
others carrying their own spacing. Halving them — 24px to 12px — recovers the quarter inch exactly
and **removes no information at all**. Trimming the hero's 56px figure, or the rows' 10px padding,
are two further sources of the same order.

So the decision is not "which number do we drop". It is "is 24px of margin above and below the
stats bar worth more than three listings on page 1", and it can be taken without touching the cap,
the layout or the sample.

---

**THE TRIM WAS TAKEN, AND IT DID NOT WORK. THE REASON IS THE FINDING.** 2026-09-25.

`.stats-bar`'s margins went 24px to 12px. It recovers exactly what it was measured to recover, and
page 1 still holds zero listings:

| | free on page 1 | a row of three | |
|---|---|---|---|
| before the trim | 2.519in | 2.772in | short by 0.253in |
| after the trim | 2.769in | 2.772in | **short by 0.003in** |

Three thousandths of an inch. The obvious move is to shave 1px off something else, and that is the
move to refuse: **a layout that fits by 0.003in is a coincidence, not a fit.** Before taking it, the
question is what varies — and the answer is that page 1's chrome varies by far more than the
slack being fought over.

**THE MASTHEAD WRAPS ON THE CITY NAME**, measured:

| | masthead | used on page 1 | a row of three |
|---|---|---|---|
| Irvine | 1.21in | 6.90in | short by 0.003in |
| **Rancho Santa Margarita** | **1.51in** | 7.20in | **short by 0.303in** |
| Irvine, long filter label | 1.38in | 7.07in | short by 0.175in |
| with an agent logo | 1.21in | 6.90in | short by 0.003in |

A two-line title costs 0.30in — a hundred times the slack. So a trim sized to make Irvine fit gives
Irvine three listings on page 1 and Rancho Santa Margarita none.

**That is the §7.2 problem again, one block higher up.** §7.2 fixed the narrative box because
page-1 capacity cannot depend on the length of model-generated prose. It equally cannot depend on
the length of a city name, and the masthead is now the variable block. Cities are unbounded; there
is no trim that makes this deterministic.

**So the real options are two, and neither is "trim a bit more":**

1. **Page 1 is a cover.** Masthead, metrics, narrative, and every listing from page 2. Deterministic
   for every city, every affiliate, and what ships today. Costs nothing.
2. **Bound the masthead's height** the way the narrative box was bounded — a fixed title area, with
   long city names set smaller rather than wrapped. Then page 1 holds a row of three for everyone.
   That is a design change to the most prominent element in the document, and it is a real piece of
   work rather than a margin edit.

**The trim is kept**, because 0.50in of margin duplicating separation two neighbours already
provide is worth removing on its own terms, and because option 2 needs that 0.25in as well. It
changes no page count for any of the eight report types today, and this entry says so rather than
claiming a win.

**And the chart stays free**, since page 1 still cannot fit a row: `market_snapshot` is 2 pages with
or without it. That conditional resolves only if option 2 is taken.

---

**THE SURVEY: WHAT ELSE ON PAGE 1 IS UNBOUNDED?** 2026-09-25. Two instances of the same failure —
model prose (§7.2) and now a city name — is enough to ask the general question rather than wait for
a third. **Page-1 capacity is a fiction wherever any input on the page is unbounded**, so every
input was stretched one at a time and every element re-measured.

Enumerated rather than listed from memory: the elements come from walking `.page-content`'s
children, the inputs from the string-valued keys the builder is handed. A block that grows shows up
whether or not anyone predicted it.

| input stretched | grew | by |
|---|---|---|
| **city** | masthead | **+0.300in** |
| **filter label** | masthead | **+0.172in** |
| AI narrative, 40 sentences | — | 0 — capped by §7.2, the cap proving itself |
| months-of-supply pace label | — | 0 — a constant in `moi.py`, not an input |
| median price at $123,456,789 | — | 0 |
| counts at 2,666,664 | — | 0 |
| company / agent name | — | 0 — not on page 1's body at all; running head and footer |

**Each zero has a positive control.** A zero delta means bounded only if the value reached the page,
so every stretched value was also grepped in the rendered HTML. Six of the seven rendered. The
seventh, the company name, does not appear in page 1's body, which is why it cannot affect it.

**The same seven, across all eight report types: identical. Always the masthead, always +0.300 and
+0.172.** Combined, when both are long: masthead 1.394in to **1.866in, +0.472in**.

**SO THE ANSWER IS BETTER THAN EXPECTED: IT IS JUST THOSE TWO, AND THEY ARE THE SAME ELEMENT.**
Option 2 is not bound-the-masthead-and-whatever-else-turns-up. Nothing else turns up. Bounding the
masthead's two text lines — title and subtitle — makes page-1 capacity deterministic for every city,
every filter label and every report type at once, and it is one change to one block.

Everything else on that page is already fixed, numeric, a code constant, or capped. The narrative
box is the precedent and it works: stretched to forty sentences, it moved page 1 by nothing.

---

**BUILT 2026-09-25 — the masthead is bounded, and page 1 is the same height for every city.**

`.masthead-title` and `.masthead-subtitle` are each one line in a box whose height is in **pixels**,
so the title's size can step down without the box moving: 24 → 21 → 18 → 16 → 14, chosen in
`MarketReportBuilder._masthead_title_px` from a measured character ladder. `white-space: nowrap`
stops the wrap; `text-overflow: ellipsis` is the backstop past the smallest step.

| | masthead | page 1 used | verdict |
|---|---|---|---|
| Irvine | 1.21in | 6.846in | **fits by 0.052in** |
| Rancho Santa Margarita | 1.21in | 6.846in | **fits by 0.052in** |
| Rancho Santa Margarita and San Juan Capistrano | 1.21in | 6.846in | **fits by 0.052in** |
| long filter label | 1.21in | 6.846in | **fits by 0.052in** |
| with an agent logo | 1.21in | 6.846in | **fits by 0.052in** |

One number, every case. Before the bound the same table read 0.003in short for Irvine and 0.303in
short for Rancho Santa Margarita.

**The last 0.010in came from `.masthead`'s bottom margin, 18px to 12px**, matching the rhythm
`.stats-bar` now uses. Trimming to fit is sound *here* and was not before: the page is the same
height for every input, so there is no case this makes fit at another's expense. That distinction
is the whole reason the earlier 0.003in trim was refused.

**`market_snapshot` page 1 has its row of three back** — `[3, 6]`, still two pages — and
`PAGE_1_CAPACITY` is re-pinned. These are the first numbers on that page that are properties of the
layout rather than of a fixture.

**The ellipsis backstop was made to fire rather than assumed.** A 98-character title reaches it: the
text measures 665px in a 474px box, the ellipsis shows, and **the box stays 29px** — the property
that matters holds even when the backstop triggers.

**ONE FIDELITY CAVEAT, STATED.** This container has no network, so Google Fonts do not load and
every measurement above is in the fallback stack; production renders Outfit. The ladder is cut ~12%
against that, and — more to the point — **the height does not depend on the ladder being right.** A
step that is slightly too large in Outfit costs an ellipsis, not a wrapped line and not a shifted
page. The determinism survives the uncertainty; only the type size is approximate.

**WHAT IS STILL OPEN HERE.** The caps still exceed what page 1 holds, so all three "1-page"
snapshot types are still two pages — `market_snapshot` `[3, 6]`, `price_bands` `[3, 5]`,
`featured_listings` `[6, 6]`. The trade is unchanged and now cleanly stated, because the capacities
are real: **cut each cap to page-1 capacity for a one-page report with a smaller sample, keep the
caps for two pages, or correct the comment.** Jerry's call.

**AND THE CHART CONDITIONAL RESOLVED, AS PREDICTED.** With page 1 holding three listings again, the
§7.3 trend chart is no longer free on `market_snapshot`: with it, `[0, 9]`; without it, `[3, 6]`.
Both are two pages. So the choice is **three listings on page 1, or the twelve-month price trend** —
not both. On `inventory` the chart remains free: five pages either way.

So there are two different questions hiding in "how many listings should page 1 hold":

1. **Is the metrics block too tall?** Trimming 0.25in — 10% off the stats bar, or 7% across both —
   puts a row of three listings back on page 1 without touching the cap, the layout or the sample.
2. **What should page 1 be?** Masthead, metrics and narrative with every listing on page 2 may be
   the better document: a cover page that reads, then the inventory. That is a deliberate choice,
   and it is available for free today.

**And it is entangled with §7.3's chart.** Measured: the trend chart costs `market_snapshot`
nothing at all right now — 2 pages either way — because it lands in the 2.52in that is going to
waste. Recover the 0.25in and the chart stops being free. **One decision, not three.**

---

---

## CLOSED 2026-09-28 — page 1 carries the trend, listings begin on page 2

**Jerry's decision, with the reasoning recorded so it survives the people who made it.**

The measurement that framed it: page 1 holds **either** a row of three listings **or** the
twelve-month price trend, never both. Both give a two-page report carrying the same nine listings,
so this decides what page 1 **leads with**, not what the report contains.

**Why the chart won.**

- **Nothing is lost.** Same two pages, same nine listings, different first page.
- **It is the only element on that page a client cannot get elsewhere.** Listings are on Zillow,
  Redfin and their own saved search. A twelve-month median for their specific market, computed from
  MLS closings, requires us.
- **It matches the reader.** These reports go on a schedule to an agent's sphere — past clients,
  not active buyers. Those readers want to know what their house is doing, not what is for sale.
- **Page 1 becomes a coherent market summary** — hero stat, narrative, metrics, trend — rather than
  half a summary and half a truncated feed.

**RECORDED AGAINST IT.** Listings are photographs, and photographs draw the eye where a line chart
does not. If the audience were active buyers the listings would be the hook. **If the product's
primary reader ever changes, revisit this rather than inherit it.**

**The final page-1 composition, measured:**

| page 1 | |
|---|---|
| masthead | 1.21in |
| hero stat | 1.14in |
| AI narrative | 1.42in |
| stats bar | 2.17in |
| **trend chart** | **1.87in** |
| listings | none — the section breaks to page 2 |

**Confirmed across the whole title ladder, not just the fixture's city:**

| city | title | pages | page-1 listings |
|---|---|---|---|
| Irvine | 24px | 2 | 0 |
| Tustin | 24px | 2 | 0 |
| San Juan Capistrano | 18px | 2 | 0 |
| Rancho Santa Margarita | 16px | 2 | 0 |
| Rancho Santa Margarita and San Juan Capistrano | 14px | 2 | 0 |
| four cities, 79 characters | 14px | 2 | 0 |

One answer at every step, which is what the masthead bound bought.

**The break is conditional and that is deliberate.** `force-new-page` is applied only when the
chart renders. With no trend data there is nothing to give the page up for, and an unconditional
break would leave 2.8in of white above it. Two deterministic states, both pinned — not a third
variable. The section heading and truncation note sit inside the section that breaks, so they
travel with the listings rather than stranding at the foot of page 1 above nothing.

**Asserted structurally**, because this failure is invisible: if the chart stopped rendering, the
break would go with it and the report would quietly revert to three listings on page 1 — no error,
no visual damage, a different document than the one chosen. Four regressions applied and seen to
fail: the chart silently not rendering, the break removed, the break made unconditional, and
`market_snapshot` losing its series.

**PAGE_1_CAPACITY IS NOW EMITTED RATHER THAN TYPED.** These numbers have been re-pinned three
times, and each time they were read off a terminal and retyped — which is exactly how the defect
board's own summary header went stale: the derivation was right every time and the transcription
was the weak step. `python3 scripts/measure_market_pagination.py --emit-capacity` prints the dict
literal, so re-pinning is a paste. The regeneration stays a deliberate, reviewed act — the diff is
what a reviewer reads — which is the same contract as `golden/themes.json` and
`regen_theme_golden.py`.

**What this entry no longer claims.** It opened as "three report types documented as 1-page render
two". `market_snapshot` is settled above. `price_bands` `[3, 5]` and `featured_listings` `[6, 6]`
are still two pages against a `PDF_CONFIG` comment that says one — a stale comment now rather than
an open question, since the capacities are known and the trade is stated. Correcting that comment
is the remaining work and it is not a decision.


### D-103 — every continuation page pays for a full masthead, and the space reserved for it is larger than the masthead

**Severity:** ROUGH · **Affects:** every market report PDF, worst on the long ones
**Status:** `fixed` — `feat/workstream-d-market-pdfs`, §7.1 variant A

Two separate costs, both measured, both on every page.

**1. The hero repeats at full size.** `page_header.jinja2` is passed to PDFShift's `header` param
with `start_at: 1`, so the same gradient masthead is painted on page 1 and on page 18. Master plan
§7.1 asks for a full masthead on page 1 (~150pt) and a **one-line running head after (~38pt)**.
Measured at Letter width, the masthead renders **1.165in (83.9pt)** — smaller than §7.1 wants on
page 1, and more than double what it wants on every page after.

**2. The reservations are larger than what they hold.** `pdf_engine.render_pdf_pdfshift` reserves
`header.height 1.3in` and `footer.height 0.9in`, and its own comment says those *"MUST match the
actual rendered content height of the templates — too small clips content, too large leaves
whitespace"*. Measured:

| | reserved | renders at | slack |
|---|---|---|---|
| header | 1.300in | **1.165in** | 0.135in |
| footer | 0.900in | **0.781in** | 0.119in |

Plus `margin.top 0.1in` and `margin.bottom 0.1in`. **2.4in of every 11in page (21.8%) is reserved
for 1.946in of paint.**

**A constraint to design around, recorded but NOT verified.** `tasks.py:1679-1683` states that
PDFShift requires `header.start_at` and `footer.start_at` to match when either is greater than 1.
If that is true, §7.1's architecture cannot be built the obvious way — moving the running head to
`start_at: 2` also moves the footer off page 1 — and the masthead has to move into the body for
page 1 instead. **That claim is a code comment, not a measurement**, and it should be checked
against PDFShift before the page architecture is designed around it either way.

> **ANSWERED 2026-09-24 by running the probe. The constraint is real, and it is worse than a
> refusal.** `scripts/probe_pdfshift_start_at.py`, four renders of one four-page document:
>
> | case | `header.start_at` | `footer.start_at` | PDFShift's response | what it actually did |
> |---|---|---|---|---|
> | A control | 1 | 1 | 200 | header 1-4, footer 1-4 — as asked |
> | B matched | 2 | 2 | 200 | header 2-4, footer 2-4 — as asked |
> | **C split** | **2** | **1** | **200** | **header 2-4, footer 2-4 — NOT as asked** |
> | **D split** | **1** | **2** | **200** | **header 2-4, footer 2-4 — NOT as asked** |
>
> **PDFShift accepts differing values and silently applies `max(header, footer)` to both.** Ask for
> the footer from page 1 and the header from page 2 and you get neither: you get both from page 2,
> with a 200 and no warning.
>
> **This is why the probe searched the rendered pages for markers instead of trusting the status
> code.** A probe that checked only whether the request was accepted would have reported the
> constraint as imaginary, and code written on that answer would believe it had a split while
> shipping reports with no footer on page 1. The failure mode the instrument was designed to catch
> is the one that happened. Reading PDFShift's documentation would have produced the same wrong
> answer — the API does not document a coercion it performs silently.
>
> **So §7.1 as written is unbuildable.** A full masthead on page 1, a slim running head after, and
> a footer on every page is `header.start_at=2` with `footer.start_at=1` — case C exactly. See the
> §7.1 correction in the master plan for the architecture that replaces it.

**FIXED 2026-09-24 — §7.1 variant A, which closes both halves of this entry.**

The masthead moved out of PDFShift's `header` slot and into the document body, where it renders
once, at the top of the flow — which in a paged document is what "page 1 only" means — as content
under CSS control. The header slot carries a slim running head instead. **Both `start_at` values
stay at 1**, so nothing is asked to differ and nothing is coerced; the running head therefore
appears on page 1 as well, above the masthead, which §7.1 never excluded.

That also settles the reservations, because the masthead is no longer a height negotiated with a
vendor:

| | before | after |
|---|---|---|
| top | 1.3in reserved / 1.165in painted, + 0.1in margin | **0.44in / 0.417in**, no margin |
| bottom | 0.9in / 0.781in, + 0.1in margin | **0.89in / 0.885in**, no margin |
| reserved per page | 2.4in of 11in (21.8%) | **1.33in (12.1%)** |

Both PDFShift margins are 0 and the breathing room moved inside the header and footer documents —
a CSS `padding-top` applies once at the start of the flow, not after each page break, so
continuation pages would otherwise sit flush against the band.

Measured: `closed` goes 6 pages to **5** and 25 rows a continuation page to **29**; `new_listings`
18 pages to **16**. Page 1 holds slightly less, since it now pays for the masthead as content
rather than every page paying for it as a reservation. `market_snapshot`'s page 1 drops to zero
listings, which is quantisation of a three-card row rather than a fault — the report is still two
pages and every listing is on page 2.

`apps/worker/tests/test_page_architecture.py` guards all four legs structurally, because none of
them shows up in rendered HTML: the `start_at` pair, the header slot carrying the running head and
not the masthead, the masthead being called from the body, and each reservation matching what its
document paints. Five regressions applied and seen to fail. **The `start_at` gate is the one that
earns its keep** — that change fails loudly nowhere, because PDFShift answers 200 and simply drops
page 1's footer.

### D-104 — the market narrative shipped whatever the API returned, including sentences it had cut off

**Severity:** WRONG · **Affects:** the "AI Market Insight" paragraph on page 1 of every market report PDF
**Status:** `fixed` — `feat/workstream-d-market-pdfs`

`generate_market_pdf_narrative` sends `max_tokens: 150` to GPT-4o. When a model reaches that
ceiling the API returns what it had written so far, with `finish_reason: "length"`, and the text
ends mid-sentence. **Nothing in the worker read `finish_reason`** — confirmed by grep, it appeared
nowhere in `apps/worker/src`. The string went back to the builder like any other and rendered under
the heading "AI Market Insight" in a customer's PDF.

**THIS SHIPPED.** The code path has been live in production for as long as the market PDF has had
an AI narrative — every report generated in that time went through a function that returned a
cut-off sentence as readily as a complete one. That is the fact worth carrying, separately from the
fix.

What is NOT established is how often it fired. 150 tokens is roughly 110 words against a prompt
asking for 2-3 sentences, so it takes a verbose answer to reach the ceiling — and **nothing
recorded it either way**, which is most of the point. There is no log line to count, because the
condition was never examined. Estimating a rate from the prompt would be reasoning about a model's
behaviour from its instructions, which is the same class of claim §0.6 warns about; the honest
answer is that the exposure is unmeasured and now cannot be measured retrospectively.

Found while implementing §7.2's narrative cap, not looked for.

**A second way the same thing happened.** Even a complete narrative that is simply long pushed
page 1's table down, because the narrative box grew with its copy. That is the variability §7.2
removes, and with the box now fixed it would instead overflow the box.

**Both are now generation failures rather than layout ones**, which is where they are visible:

- `finish_reason == "length"` → drop the narrative, log at ERROR naming the report and city.
- `len(narrative) > NARRATIVE_MAX_CHARS` (380, measured against the four-line box) → same.

Every layout already renders without a narrative, so the report is complete either way. A half
sentence is not.

**The boundary is tested from both sides.** `test_narrative_guards.py` asserts a cut narrative and
an over-budget one are dropped, *and* that one exactly at the budget is kept — without that, both
guards could be off by one in the strict direction and every ordinary narrative would be silently
discarded, which looks exactly like "the AI is not configured". It also pins that the quote-unwrap
runs before the budget check, since measuring a quoted string two characters long decides the
boundary case.

Six regressions applied and seen to fail, covering both guards, the box height and the budget in
both directions.


---

### D-105 — days on market is read from a path the feed does not use, so every DOM is computed and closed comps are overstated by the escrow period

**Severity:** WRONG · **Affects:** the DOM column and Avg DOM on every market report, and anywhere else `extract.py`'s `days_on_market` reaches
**Status:** `fixed` — `feat/workstream-d-market-pdfs`

Found 2026-09-28 while checking whether `closed`'s DOM column was sound enough to build a
distribution chart on. It is not, and the reason is not the one the register recorded.

**THE PATH IS WRONG.** `compute/extract.py:30` reads

```python
dom = _int(p.get("daysOnMarket"))
```

SimplyRETS puts it at **`p["mls"]["daysOnMarket"]`**. Confirmed against this repo's own fixture:
`tests/fixtures/listing_closed_minimal.json` has no top-level `daysOnMarket` and carries `16` at
`mls.daysOnMarket`, and `tests/test_new_metrics.py:334` reads it from that path and asserts on it.

So the lookup returns `None` for every listing, always, and every DOM in the product comes from
the fallback branch. **This is the same defect as `closeDate`**, which lives at
`row["sales"]["closeDate"]` and whose top-level read returned `None` for every row — recorded in
the master plan's decision-01 note, and evidently not swept for.

**THE COMMENT ABOVE IT DOCUMENTS THE SYMPTOM AS A PROPERTY OF THE FEED.**

```python
# DOM: Use API value if available, otherwise calculate from dates
# SimplyRETS doesn't return daysOnMarket for Closed listings
```

The feed does return it. It does not return it *at the path being read*. A true observation about
the code's behaviour was written down as a fact about the vendor, and then relied on — the
documentation-as-evidence trap, one layer further in than usual, because the documentation is a
code comment written by someone watching the right symptom.

**WHAT THE NUMBER MEANS NOW, AND WHAT IT SHOULD MEAN.** Measured on the fixture above:

| | days |
|---|---|
| feed `daysOnMarket` — list → contract, the industry's DOM | **16** |
| computed `close_date − list_date`, what ships | **42** |
| escrow, contract → close | 26 |
| **overstatement** | **26 days, 162% high** |

`test_new_metrics.py:331` already states the distinction in as many words: *"SimplyRETS
daysOnMarket = days from listing to contract only. It does NOT equal escrow_days +
marketing_days (which spans list→close)."* The test knew; the extractor did not.

**Scope.** Closed rows are wrong as described. Active and pending rows fall back to
`now − list_date`, which is the right notion for a listing that has not sold, so those are
defensible — but they are computed rather than read, so they will also disagree with the feed's
own figure wherever it differs.

**Why this blocks §7.3's DOM distribution chart, which is how it was found.** A histogram over
this column would be a distribution of marketing-plus-escrow presented under a label every agent
reads as marketing. Charting it would make a wrong number look authoritative, which is worse than
not charting it — so the chart waits for the fix rather than shipping alongside it.

**The fix is one line plus a decision.** Read `mls.daysOnMarket` first. Then decide what the
column should show when the feed has no value: list→close is available and honest if labelled as
such, but it is not DOM. Both halves need doing; the read alone changes numbers on live reports.

---

**FIXED 2026-09-28 — path corrected, comment corrected, and the sweep run.**

`extract.py` now reads `mls.daysOnMarket` first, falls back to the top level for deployments that
put it there, and when the feed carries nothing derives **the same quantity** from
`sales.contractDate` rather than a different one. A closed sale with neither reports `None`, which
the table already renders as `-` — D-056's rule: no sentinel, and the caller says so in words.
Active and pending rows keep `now − list_date`, which is the right notion for a listing that has
not sold; only closed rows changed.

On the fixture: **42 → 16**, the feed's own number.

The comment is replaced with what was actually observed. The old one said the vendor does not
return the field; what was observed is that *the lookup returned None*, and it returned None
because it was the wrong key.

**THE SWEEP, ENUMERATED WITH `ast` RATHER THAN BY READING.** Every `<expr>.get("key")` in
`extract.py` — 22 of them — resolved to the path it reads and checked against both captured
fixtures' actual shape:

| | |
|---|---|
| reads checked | 22 |
| **`daysOnMarket` — read top-level, feed has `mls.daysOnMarket`** | **D-105, fixed here** |
| **`bathrooms` — read as `property.bathrooms`, feed has `bathsFull`/`bathsHalf`** | **D-106, filed** |
| `status` — flagged, then verified fine: the expression reads `mls.status` first and the top-level `p.get("status")` is an unreachable fallback | dead code, not a defect |
| the other 19 | read where the feed puts them |

**The sweep's first run examined 10 of its own 22 reads and reported completeness**, because
`(addr or {}).get("city")` unparses as `(addr or {})` and did not match the list of row variables.
Fixed to unwrap the guard, and to print what it skips instead of dropping it. An incomplete sweep
that looks complete is worse than no sweep — §0.6, *enumerate the parts that are there*.

**NOT CONFIRMED AGAINST A LIVE PAYLOAD, AND THAT IS NAMED RATHER THAN GLOSSED.** This container has
no SimplyRETS credentials, so the sweep ran against `tests/fixtures/listing_{closed,active}_minimal.json`
— captured responses, real in shape, but two of them. `tools/dump_market_snapshot.py` needs
`SIMPLYRETS_USERNAME`/`PASSWORD` and would settle it in one call. What the fixtures cannot rule out
is a deployment that DOES populate `property.bathrooms` or a top-level `daysOnMarket`; both reads
are kept as fallbacks for exactly that reason, so the fix is correct either way.

**THE REPO HELD BOTH ANSWERS.** `tests/test_new_metrics.py:334` reads
`closed_listing["mls"]["daysOnMarket"]` and asserts on it — the correct path, in a passing test,
in the same repository as the wrong one. Nothing compared the two files.
`apps/worker/tests/test_extract_field_paths.py` now runs the extractor over the same fixtures those
tests use, so they cannot disagree in silence again.

**Three regressions applied and seen to fail** — the original top-level-only read, `close − list`
substituted again, and the contract-derived branch removed.

**The first attempt at the first one MISSED.** Reverting to the old read left the contract-derived
branch computing 16 on this fixture, the same answer by a different route, so the assertion could
not tell "read it" from "worked it out". A second test now sets the feed's value to a number
neither derivation can produce, which makes the read the only way to obtain it. Two independent
paths agreeing on one input is the same shape as a test reading its expectation from the code
under test: the assertion is true and it is not evidence.

**BLAST RADIUS.** DOM reaches, by grep rather than recollection: `report_builders.py` (24 sites),
`email/template.py` (18), the market macros (10), `compute/market_trends.py` (9),
`property_builder.py` (6), `tasks.py` (5), `market_builder.py` (3), `ai_overview.py` (3),
`ai_market_narrative.py` (3), `ai_insights.py` (2), and five property-report templates. Concretely
the figures that move are the market report's **DOM column** and **Avg DOM**, the stats bar's
**Avg Days on Market**, the property report's **Market Trends** average, and any **AI narrative**
that quotes them — the narrative is generated from these numbers, so past commentary described a
market that was slower than it was.

**Every closed comp's DOM falls by that listing's escrow period** — contract to close, 26 days on
the only real sample available. Reports already sent are not corrected by this; the entry records
that plainly rather than implying a retroactive fix.


---

### D-106 — bathroom counts are read from a key the feed does not have, so every listing ships without one

**Severity:** WRONG · **Affects:** the Bd/Ba column, every listing card's bath chip, the AI overview's property line
**Status:** `open`

Found by the D-105 sweep, not looked for. Same shape, same file, one line apart.

`compute/extract.py:54` reads

```python
baths = _float((pr or {}).get("bathrooms"))
```

SimplyRETS' `property` object carries **`bathsFull`** and **`bathsHalf`**. There is no
`bathrooms` key. Confirmed against both captured fixtures, whose `property` objects hold
`acres, area, bathsFull, bathsHalf, bedrooms, cooling, garageSpaces, heating, lotSizeArea,
lotSizeAreaUnits, pool, stories, subType, subTypeText, type, view, yearBuilt` — and running the
extractor over them returns `bathrooms: None` for both.

**It fails invisibly, which is why it has lasted.** Every consumer guards:

- `macros.jinja2:271` renders the closed table's Bd/Ba as `{{ l.beds }}/{{ l.baths | default('-') }}`, so it prints **`3/-`**
- the listing cards emit the bath chip under `{% if listing.baths %}`, so it simply is not there
- `email/template.py:704` and `ai_overview.py:159` are both `if`-guarded the same way

No error, no blank where a number should be, no log line. A bathroom count is one of the three
figures a reader looks for on a comp, and the reports have never carried it.

**The fix needs a decision, which is why it is filed rather than done in the same commit as
D-105.** `bathsFull` and `bathsHalf` are two integers and the product wants one number. The
convention agents use is `full + half/2` rendered as `2.5`, but "2 full and 1 half" is also
written `2.1` in some MLS markets, and the extractor's own comment says *"Keep as float (e.g., 2.5
baths)"* — which says what it expected and not what the feed provides. Pick the convention
deliberately, then read both keys.

**Do not close this by reading `bathsFull` alone.** A three-bed with two full baths and a powder
room would render `2`, which is wrong in the direction that matters to a seller.

**THE CONVENTION QUESTION, NAMED RATHER THAN LEFT OPEN — [JERRY].** There are two sensible rules
and only two:

| | a home with 2 full baths and a powder room reads | |
|---|---|---|
| **decimal — halves as `.5`** | **`2.5`** | MLS convention; what an agent expects to read, and what the extractor's own comment already assumed ("Keep as float (e.g., 2.5 baths)") |
| explicit — full plus half | `2+1`, or `2F 1H` | unambiguous about which is which, and unfamiliar on a market report |

**Recommended: the decimal.** It is the industry convention, every comparable portal shows it that
way, and the report's Bd/Ba column has room for one number per side and not two. The explicit form
buys precision a reader of a market comp does not need — they are scanning for "is this like my
house", not auditing fixture counts.

The rule to implement once confirmed: `bathsFull + (bathsHalf × 0.5)`, rendered without a trailing
`.0`, and `None` when both keys are absent rather than `0`.

**Awaiting Jerry's confirmation, not blocked on it for the diagnosis** — the read is wrong either
way, and only the rendering rule is in question.


---

### D-107 — the price-band stat cards show the first four bands and never say so

**Severity:** ROUGH · **Affects:** `price_bands` PDFs for any market with more than four bands
**Status:** `fixed` — `feat/zero-rendering-and-band-cards`

`macros.jinja2`, `pricebands_layout`:

```jinja
{% for band in price_bands[:4] %}
```

A market with six price bands renders four cards. Nothing on the page says the other two exist,
and nothing in the code says why four.

**Surfaced by the §7.3 band chart**, which renders every band — so a six-band report now shows four
cards above six bars. The chart's caption names the discrepancy as a stopgap ("the cards above show
the first 4; the chart shows all 6"), which is a caption apologising for a layout rather than a fix.

**IT IS NOT PROTECTING AGAINST ANYTHING, WHICH IS THE POINT.** The obvious defence of a cap is that
more cards would break the row. Measured, with the cap lifted:

| | cards | width each | label lines | row height |
|---|---|---|---|---|
| capped at four | 4 | 79px | 2 | 84.8px |
| all six | 6 | 56px | 3 | 95.2px |

Nothing overflows, nothing truncates, no label is clipped. `.stat-cards` is `display: flex` with
`flex: 1` children — not a four-column grid — so the cards simply divide the row. Six costs
**10.4px of height** and a tighter label. That is an aesthetic cost, not a constraint, and it is
being paid in hidden information instead.

**No recorded intent.** The `[:4]` dates to the repository's squashed base commit, so there is no
commit message, no comment, and nobody to ask. It is as likely to be a slice someone wrote while
the layout had four bands as a decision.

**Two ways to close it, and the first is now the cheaper one:**

1. **Show every band.** Costs 10.4px. The cards and the chart then agree, and the chart's caption
   loses the clause explaining why they do not — which is the better outcome, since that clause
   exists only to describe this defect.
2. **Keep four and say so on the card row** — "4 of 6 bands" — rather than leaving the reader to
   infer it from a chart further down.

**Recommended: the first.** A report that hides two price bands from an agent who is showing it to
a client is worse than a slightly tighter row of cards, and the 10.4px is available — page 1 of
`price_bands` gives up one listing to the chart already and stays at two pages.

Left open rather than taken, because it changes what a shipping report looks like and the
measurement is what the decision needs, not more analysis.


---

**FIXED 2026-09-28 — every band renders, and the measurement was wrong about which case matters.**

`{% for band in price_bands %}`. The caption's apology clause is gone, `BAND_CARDS_SHOWN` with it,
and `test_band_chart.py` now asserts the card labels and the bar labels are the **same list** —
so the two cannot drift apart again without a test saying so.

**A correction to the measurement above, found while re-pinning page-1 capacity.** The six-band
row it measured is not a state production can currently produce. `build_price_bands_result` derives
its bands from **quartiles of the result set** — three `band_defs` when there are four or more
listings, one otherwise — and drops any band with no listings. So the live maximum is **three**,
and `[:4]` was never truncating anything. The slice was dead code, not a live defect.

That does not change the fix — a cap with no recorded intent, protecting nothing, sitting in front
of a chart that shows everything, is worth removing whether or not it fires today, and the caption
it forced was real. It does change the severity of what was fixed, and it is recorded here rather
than left as an overstated win.

It also cost something measurable. At six bands, `price_bands` and `new_listings` each lose one
listing from page 1 (3 → 2 with a narrative), so page-1 capacity is no longer independent of
content for those two layouts. At three bands — every report the product can currently emit —
the re-measured capacity is **identical to the pinned table**, which is why `PAGE_1_CAPACITY` is
unchanged. If the band definitions ever become fixed bands, that pin moves.

**The quartile banding is its own problem** and is filed as **D-111**.

### D-108 — numeric fields are shown with `{% if value %}`, so a legitimate zero renders as nothing

**Severity:** ROUGH · **Affects:** studios (no bed count), same-day sales, any metric that can
honestly be zero, and — found while fixing it — **every DOM statistic the product computes**
**Status:** `fixed` — `feat/zero-rendering-and-band-cards`

Found by applying §0.6's *knowledge transfers by search* rule immediately after filing it: grepping
the market macros for the shape behind the `selectattr` mistake, in its other syntax.

Jinja's `{% if x %}` is falsy for `0`, so every one of these hides the row or chip when the value
is a real zero rather than missing:

| site | zero means | how likely |
|---|---|---|
| `{% if listing.beds %}` — the bd chip, twice | **a studio** | common in condo and urban markets |
| `{% if stats.avg_dom %}` — Avg Days on Market | everything sold the day it listed | rare, and **newly reachable**: D-105 now reads the feed's DOM, and a same-day sale reports 0 |
| `{% if stats.months_of_inventory %}` — Months of Inventory | nothing is for sale | rare, and it is **D-056's own metric** — that defect was a sentinel 0 rendering as a measurement, and `moi.py` returns `None` for "not enough data" precisely so 0 can mean zero |

`price_per_sqft`, `list_to_sale_ratio`, `list_price` and `sqft` use the same shape and cannot
honestly be zero, so they are correct by accident rather than by design.

**The studio case is the one that will actually be seen.** A studio renders `2 ba · 620 sf` with no
bed figure at all — not "0 bd", not "studio", just an absent chip, which reads as missing data on
a listing where the data is present and interesting.

**The fix is `is not none`, not a rewrite** — `{% if listing.beds is not none %}` — plus a decision
on how a zero should read in each case. `0 bd` is technically right and unidiomatic; **"Studio" is
what an agent would write**, and that is a copy choice rather than a template one, which is why
this is filed rather than taken.

**Not urgent, and recorded because the class is the point.** This is the same call as the trend
chart's gap-versus-zero and the band chart's empty band, in a third syntax. The grep that found it
took under a minute and is the practice the §0.6 entry argues for.

---

**THE FULL SWEEP, 2026-09-28.** Every Jinja conditional in every template, matched against numeric
leaf names **derived from real built contexts** rather than from a list of numeric-looking names —
the builders' `stats`, `header` and `listings` contexts were walked and every `int`/`float` leaf
collected, then matched against every bare `{% if ... %}`. Comparisons, `is not none` and boolean
chains are excluded; they are already explicit about what they test.

**40 conditionals, 17 distinct expressions, 3 files** — wider than the two found by hand, and
including the property report, which the original entry did not mention.

| expression | zero means | verdict |
|---|---|---|
| `listing.beds` · `property.bedrooms` | **a studio** | **fix** — common, and the chip vanishes entirely |
| `listing.days_on_market` | **listed and sold the same day** | **fix** — newly reachable: D-105 now reads the feed's value, and the sweep's own baseline notes a DOM of 0 is real |
| `stats.months_of_inventory` | **nothing is for sale** | **fix** — D-056's own metric; `moi.py` returns `None` for "not enough data" precisely so 0 can mean zero |
| `stats.avg_dom` | every sale closed the day it listed | **fix** — rare but the same class, and free to do alongside |
| `header.total_count` · `total_count` | **the query matched nothing** | **fix, differently** — an empty report is an empty-state question, not a hidden field |
| `listing.sqft` · `l.sqft` · `property.sqft` | land, or bad data | **leave** — 0 sqft on a dwelling is wrong data, and land carries `None` rather than 0 |
| `listing.baths` · `property.bathrooms` | no bathroom | **leave** — not a habitable dwelling, and D-106 means it is `None` today regardless |
| `listing.list_price` · `stats.price_per_sqft` · `stats.list_to_sale_ratio` | — | **leave** — unreachable; correct by accident rather than by design |
| `stats.median_close_price` | — | **leave** — this one is a deliberate fallback chain (`{% if close %}…{% elif list %}`), not an absence check |
| `band.count` | an empty price band | **already fixed** — draws "none" |

**Each case needs a rendering, and none of them is "hide the field":**

| | renders as |
|---|---|
| 0 bedrooms | **"Studio"** — what an agent writes; `0 bd` is correct and reads as a data error |
| 0 days on market | `0` — or "New", which is the MLS convention for a same-day listing |
| 0 months of inventory | `0` **with the pace label**, since the label is what makes it a measurement |
| 0 avg DOM | `0` |
| 0 total count | not a field to render — the report should say it matched nothing, which is a separate piece of work |

**The mechanical half is `is not none`;** the copy is the part that needs deciding, which is why
this stays open rather than being taken as a sweep-and-replace.

`scripts/sweep_zero_conditionals.py` re-runs the enumeration, so the list above can be regenerated
rather than re-derived by eye when a template changes.

---

**FIXED 2026-09-28 — and the sweep found a fifth case that is worse than the four it was filed for.**

Jerry approved the four copy decisions (Studio, New, the pace label carrying a zero, and an empty
state for `total_count` 0). Implementing them turned up two things the original write-up missed,
both of which would have made the template fix actively wrong.

**FIRST: THE BUILDER DESTROYED THE DISTINCTION BEFORE THE TEMPLATE COULD RENDER IT.**

```python
"beds": item.get("bedrooms") or item.get("beds", 0),
```

`or` is zero-is-falsy too. A studio (`bedrooms: 0`) and a listing with no bed count both arrived at
the template as `0`. The old `{% if listing.beds %}` then hid both — **which is the only reason the
old code read as correct.** Rendering that 0 as "Studio" without fixing this would have printed
**"Studio" over missing data**: the defect inverted, and shipped as a fix.

Six of these in `market_builder`, replaced with `_first_present(source, *keys)` — first value that
is not None, which is what the `or` chain was trying to say. Two tests pin both directions: a
studio must reach the template as `0`, a missing bed count must reach it as `None`.

**SECOND: NINE STATISTICS WERE AVERAGING A LIST THEIR ZEROS HAD BEEN FILTERED OUT OF.**

```python
avg_dom = _average([l["days_on_market"] for l in closed if l.get("days_on_market")])
```

A same-day sale reports a DOM of 0, `0` is falsy, so **the fastest sales were excluded from the
average of how fast sales happen.** Nine sites across `report_builders.py` and `compute/calc.py` —
`avg_dom`, `median_dom`, and the per-band DOM — every one biased upward, on numbers the page
presents as measurements.

**This was dormant until D-105 fixed the DOM path last week.** The old code computed
`close − list`, which is 0 only for a same-day close; the feed's `daysOnMarket` is 0 for any
listing that went under contract the day it listed. A fix in one file turned on a defect in
another, and nothing connected them. That is the argument for a walk rather than nine edits.

**It is the worst of the four syntaxes because it is silent.** A template that hides a zero shows
a visibly missing chip. An average that drops its zeros just reads a little high, and nothing on
the page says so.

**WHAT NOW RENDERS**

| | before | after |
|---|---|---|
| a studio | nothing where the bed chip goes | **Studio** |
| a listing under contract the day it listed | nothing where DOM goes | **New** |
| 0 months of inventory | the whole row disappears | `0` with its pace label |
| 0 avg DOM | the whole block disappears | `0` |
| a search that matched nothing | "No listings found for this period." | **"No listings matched this search."** plus the city, window and filters, so an empty market and an over-tight filter can be told apart |
| avg DOM over 40 sales, 3 of them same-day | mean of 37 | mean of 40 |

**Whether a report that matched nothing should be SENT is not decided here** — it is a scheduling
question and Claude Design's work does not touch it. Filed as **D-110**.

**THE PROPERTY REPORT IS DELIBERATELY NOT FIXED.** `property_builder.py` collapses None to 0
(`sitex_data.get("bedrooms") or 0`, and `_safe_num(..., 0)`) with the stated intent "numeric fields
default to 0 for safe template arithmetic" — and six themes do arithmetic on them. On that surface
a 0 does **not** mean a studio, so rendering "Studio" there would invent data. The template change
was written, then reverted for exactly that reason. Filed as **D-109**, and the exemption in the
gate carries the reason so the next person does not "fix" it into inventing data.

---

**THE GATE, AND WHY IT IS A WALK.**

`apps/worker/tests/test_zero_conditionals.py`, with the checker in `_zero_conditionals.py`.

The templates are being replaced. Forty corrected conditionals leave with the files that hold them,
and a replacement set can reintroduce every one in silence — so **nothing in the gate names a file,
a line, a CSS class, or a fragment of markup**:

| | |
|---|---|
| which names hold numbers | **derived** — build real contexts from the market *and* property builders, keep every `int`/`float` leaf. 49 names. A field a builder adds is in scope with nobody remembering to add it. |
| which templates | walked from the templates tree |
| how each is read | **Jinja's own parser**, and `ast` for the Python half. §0.6 has four entries about substring false positives in this repo; a parser cannot produce one |
| what counts as handled | **the conditional has an `{% else %}`** — a structural property, not the presence of the word "Studio". A replacement template may render a zero however it likes and the gate stays quiet |
| the exemptions | keyed by **leaf name** (`sqft`), or by full path where the claim holds on one surface and not another (`property.bedrooms`). A new template inherits the exemptions it has earned and none that it has not |

**Four syntaxes, because this defect has appeared in all four here:**

```
{% if x %}…{% endif %}              hides the field
{{ x if x else '-' }}               same thing, as an expression
{{ bands | selectattr('count') }}   drops the zero rows       (twice — §0.6)
[r["dom"] for r in rows
          if r.get("dom")]          drops them from the STATISTIC
```

**The exemption list cannot rot, and cannot be padded.** A second test fails on any `EXEMPT` entry
no template or module relies on any more — so it cannot outlive what it excused, and cannot be
pre-loaded with a name to clear a defect that has not been filed yet. Three entries written on the
first pass were deleted by it.

**Seen to fail.** Six regressions applied to real files, each observed red: the `beds` conditional
reverted to bare, one `or` chain restored in the builder, the `avg_dom` fallback restored, the
empty state reverted to the generic copy, one DOM filter reverted, and an `EXEMPT` entry padded
with an unused name. Three more run inside the gate against scratch templates, one per syntax.
Two negative tests pin the other direction — an else-covered conditional and an `{% elif %}`
fallback chain must **not** be reported; the first version of the walk failed two correct chains
because it judged the elif on its own empty `else_` rather than the chain's.

`scripts/sweep_zero_conditionals.py` prints the same walk with its workings, sharing one
implementation with the gate. Two front ends, one rule — a script and a gate with separate copies
would disagree, and the one that disagreed quietly would be the gate.

**Result: 44 sites, 0 unexempt, across templates and Python.** Suite 921 passed.

---


### D-109 — the property report collapses a missing number to 0, so the report cannot tell "no data" from "zero"

**Severity:** ROUGH · **Affects:** every property report; bedrooms, bathrooms, sqft, lot size, year built
**Status:** `open`

Found 2026-09-28 while fixing D-108, by writing the same fix for the property report and then
**reverting it**.

`property_builder.py:659`:

```python
# Property details (numeric fields default to 0 for safe template arithmetic)
"bedrooms": sitex_data.get("bedrooms") or 0,
"bathrooms": sitex_data.get("bathrooms") or 0,
"sqft": sitex_data.get("sqft") or 0,
"lot_size": sitex_data.get("lot_size") or 0,
"year_built": sitex_data.get("year_built") or 0,
```

and again at `:870` for comps, and again through `_safe_num(..., 0)` at `:1134` and `:1150`.

**The comment states the intent and the intent is defensible** — six themes do arithmetic on these
(`_macros.jinja2:467`: `property.bedrooms | default(0, true) | float`), and a None would raise
mid-render. The cost is that every "no data" is indistinguishable from a real zero by the time a
template sees it, in a report whose whole subject is one specific property.

**Why this is filed rather than fixed.** D-108's market-side fix renders a 0 bed count as
**"Studio"**. Applying the same copy here would print "Studio" on **every property the county has
no bedroom count for**, which is the D-108 defect inverted and shipped as a fix. The template
change was written, rendered, and reverted for that reason. The gate's exemption for
`property.bedrooms` names this entry, so the next person to run the sweep is told why the bare
conditional is allowed to stand rather than finding it unexplained and "fixing" it.

**The fix is the builder, not the template, and it is not one line.** Preserving None means
auditing every arithmetic site across six themes and giving each a None-safe form — which is a
larger and more testable piece of work than it looks, and belongs with whatever replaces the
property templates rather than in front of it.

**Year built is the clearest symptom:** a property with no year on record renders as a `0` under
the label "Year Built", or vanishes, depending on the theme.

---


### D-110 — a report that matched nothing is still sent, and nobody has decided whether it should be

**Severity:** ROUGH · **Affects:** every scheduled market report whose search returns zero listings
**Status:** `open` — a product decision, not a code fault

Split out of D-108 on 2026-09-28. **D-108 fixed what such a report LOOKS like; it deliberately did
not change whether it goes out.**

The report now renders an explicit empty state — "No listings matched this search", with the city,
the window and the filter label, so a genuinely empty market and an over-tight filter can be told
apart. That is strictly better than the old "No listings found for this period.", and it is the
right behaviour *given the report is being produced at all*.

**What is undecided:** a weekly schedule on a filter that matches nothing sends an empty report
every week, indefinitely. Three defensible answers:

| | |
|---|---|
| **send it** | the agent learns their filter is too tight, and silence is indistinguishable from a broken schedule — this is what happens today |
| **skip it, log it** | no empty mail; the agent finds out only if they look |
| **send it once, then hold** | the first one informs, the rest are noise. Needs state per schedule |

**Why it is not answered here.** It is a scheduling behaviour with an owner and a support cost,
Claude Design's template work does not touch it, and getting it wrong in either direction is
visible to customers. Recorded so the empty-state work does not read as having settled it.

---


### D-111 — "price bands" are quartiles of the current result set, so the bands move every run and cannot be compared

**Severity:** WRONG · **Affects:** the `price_bands` report, and the band cards on `new_listings`
**Status:** `fixed` — `chore/probe-365-window`

Found 2026-09-28 while confirming D-107's measurement against what production can actually emit.

`build_price_bands_result` (`report_builders.py:718`) does not use price bands. It uses quartiles:

```python
p50 = sorted_prices[n // 2]
p75 = sorted_prices[(3 * n) // 4]
band_defs = [
    (f"Under {fmt(p50)}", 0, p50),
    (f"{fmt(p50)} – {fmt(p75)}", p50, p75),
    (f"{fmt(p75)}+", p75, max_price + 1),
]
```

**Three consequences, in increasing order of how much they matter:**

1. **There are at most three bands, ever** — three when there are four or more listings, one
   otherwise. The `[:4]` slice D-107 removed had therefore never truncated anything. Recorded on
   that entry as a correction rather than left as an overstated fix.

2. **Empty bands are dropped** (`if band_listings:`), so a band with no listings never reaches the
   template. The band chart's "none" row and the cards' zero handling are both correct and both
   currently unreachable. They stay: the rendering should not depend on a filter three call frames
   away, and this entry is what would make them reachable.

3. **The bands are redefined on every run, from that run's own results — which is the defect.**
   A report titled "Price Bands" whose bands are the current median and 75th percentile shows
   roughly 50% / 25% / 25% *by construction*, whatever the market does. Two consecutive weeks are
   not comparable: the label moves, the boundary moves, and the counts barely move at all because
   they are quartiles. An agent reading "Under $920K: 31 listings" one week and "Under $955K: 29"
   the next cannot tell whether inventory shifted or the divider did.

**The distribution chart makes this worse, not better** (§7.3, shipped). Three bars at roughly
2:1:1 look like a finding. They are an artefact of the banding.

**The fix is fixed bands** — $200K or $250K steps across the market's range, or a per-market
configured set — which is what "price bands" means to an agent and what makes two runs comparable.
Needs a decision on the step and on how many bands is too many for the row, and the row measurement
is already on D-107.

**Also in this function, same family as D-108:**
`hottest = min(bands, key=lambda b: b["avg_dom"] if b["avg_dom"] > 0 else 999)`. A band whose sales
all went under contract the day they listed scores **999** and can never be the hottest band. The
zero-is-falsy pattern in a ranking, using a sentinel rather than a filter — which is why the D-108
gate does not catch it, and why it is written down here.

---

**MEASURED 2026-09-29, and it is worse than "the bands move".**

Bootstrap: draw two independent weekly samples from one **unchanging** market and compare the
bands each run would produce. 400 pairs per market shape.

| market | p50 boundary moves between consecutive runs | p75 moves | distinct first-band labels over 800 runs |
|---|---|---|---|
| Irvine-like, 60 sales/wk | median **$105,500** (p90 $269,000) | median $141,000 | **33** |
| smaller, 25 sales/wk | median $55,000 | median $61,000 | 219 |
| thin, 10 sales/wk | median $130,000 | median $121,000 | 363 |

**And the counts, over those same runs, are `[30, 15, 15]` every single time.** They have to be:
they are 50% / 25% / 25% of 60 by construction.

So the report has it exactly inverted. **The part that carries information is constant by
construction; the part that is constant in reality is what moves on the page.** An agent reading
"Under $1.2M: 30" one week and "Under $984K: 30" the next is being shown a $216,000 swing in a
market where nothing happened, next to three counts that cannot change.

**THE RECOMMENDATION: ROUND BOUNDARIES ON A 1-2-5 LADDER, WITH THE EXTENT TAKEN FROM THE
TWELVE-MONTH HISTORY RATHER THAN FROM THIS WEEK'S RESULTS.**

Pick the step from `[25K, 50K, 100K, 200K, 250K, 500K, 1M, 2M]` nearest `range / 6`, lay the
boundaries on multiples of it from zero, and take the range from the same twelve months of
closings `compute/monthly_trend.py` already fetches for the trend chart.

Measured on the same bootstrap:

| market | distinct edge sets over 400 runs of an unchanging market | consecutive runs identical |
|---|---|---|
| Irvine-like | **1** | 399/399 |
| smaller | 2 | 329/399 |
| thin | **1** | 399/399 |

versus 33 / 219 / 363 distinct labels for quartiles. And the counts now vary —
`(15, 10, 5, 9, 8, 5, 6, 2)` — because the boundaries stopped absorbing the variation.

**Why this rather than the two obvious alternatives.**

| | |
|---|---|
| **fixed global bands** (say $250K everywhere) | comparable across markets as well as across runs, which sounds strictly better and is not: a $250K step gives one band in a $350K market and twelve in a $3M one. The report would be unusable at both ends to buy a comparison the product never makes — it shows one market over time, not two markets side by side |
| **per-market bands persisted in the database** | the textbook answer, and it needs a schema change, a decision about when to recompute, and a migration. It buys stability this already has: **1 distinct edge set in 400 runs** is not meaningfully less stable than a stored constant, and it fails safe — a market that genuinely moves a step gets new bands rather than stale ones |
| **snapping, extent from this week's sample** | the intermediate version, measured because it is the cheaper thing to build: 2 / 5 / **18** distinct edge sets. The step is stable (chosen identically in 382 of 400 runs) but a ten-sale week's min and max swing enough to add or drop a band at the ends. Anchoring the extent to the history is what fixes it, and the history is already being fetched |

**Three things this does not settle**, to be decided when it is built rather than assumed now:

1. **Six bands is a guess.** The row measurement on D-107 says six cards fit at 56px. The chart
   has more room than the cards do, so the number may want to differ between them — and if it
   does, the cards and the chart disagree again, which is what D-107 just closed.
2. **What happens with no history.** A market with under twelve months of closings has no extent
   to anchor to. Falling back to this week's sample reintroduces the drift, silently; saying so
   on the page is the alternative, and it is the same gap-versus-zero call as the trend chart's.
3. **Empty bands become reachable for the first time.** `if band_listings:` currently drops them,
   which is why the chart's "none" row and D-107's all-cards change have never been exercised.
   Fixed bands produce empty bands routinely. That is the intended behaviour and it means the
   two unreachable code paths become live in the same change — they need a test that renders
   them, not just a sweep that finds them.

**Also still open in this function** (unchanged by the above):
`hottest = min(bands, key=lambda b: b["avg_dom"] if b["avg_dom"] > 0 else 999)` — a band whose
sales all went under contract the day they listed scores 999 and can never be the hottest band.

---

**FIXED 2026-09-29 — round bands on a 1-2-5 ladder, sized from twelve months.**

`compute/price_bands.py`. The extent comes from `closed_history`, which D-113 made real earlier
the same day; `price_bands` joins `HISTORY_REPORT_TYPES` to pay for the same fetch, deliberately
NOT `TREND_REPORT_TYPES` — it wants the rows to size boundaries, not to draw a line.

**Re-bootstrapped against the shipped implementation, not the prototype:**

| market | distinct edge sets / 120 runs of an unchanging market | distinct count vectors |
|---|---|---|
| Irvine-like, 60/wk | **1** (was 33 labels) | 120 of 120 |
| smaller, 25/wk | **1** (was 219) | ~118 |
| thin, 10/wk | **1** (was 363) | ~115 |

Better than the 1/2/1 the recommendation predicted, and the counts now vary on essentially every
run — the boundaries stopped absorbing the variation.

**The three questions that went with the build:**

| | |
|---|---|
| how many bands | **six** — see below, it took three goes |
| under twelve months of history | falls back to this period's results **and says so on the page** — the caption carries "may shift between reports". Bands that will move look identical to bands that will not, and the whole point is that two runs can be compared |
| empty bands become routine | kept, not dropped. The chart's "none" row and the cards' zero rendering were both written while unreachable and are now exercised by a test that renders one |

**And the `999` sentinel is gone.** Bands with no sales have `avg_dom: None` and are excluded from
the ranking because they have no speed — not because their speed is zero. A band whose sales all
went under contract the day they listed can now be the hottest.

**TWO BUGS THE TESTS FOUND IN MY OWN CODE BEFORE IT SHIPPED.**

`format_price` used one decimal place, so a **$1,250,000 boundary rendered as "$1.2M"** — and
$250K is one of the commonest rungs, so above a million the label routinely named a boundary the
band did not have. A reader placing a $1,240,000 listing into "$1.2M – $1.5M" would put it in the
wrong band. Now two decimals with trailing zeros stripped, plus a property test that round-trips
every multiple of every rung through its own label.

And `MAX_BANDS` was enforced only by walking up the ladder, which stops at $2M — so a
$50K–$90M range fell through to the top rung and produced **46 bands**. The count is bounded by
construction now.

**PAGE_1_CAPACITY MOVED, AND THE REASON IS D-113'S LESSON ONE FILE LATER.**
`price_bands` 4/3 → **3/2**, `new_listings` 4/3 → **3/2** (via 2/1, before `MAX_BANDS` came
down to six and gave a listing back). Not because the layout changed: the
measuring script set `price_bands` to a **two-entry literal it supplied to itself**, while
production emits six to eight, so the pinned numbers described a card row the product does not
render. The fixture builds its bands with the real `build_bands` now. Caught only because D-113
had just been written up.

**HOW MANY BANDS TOOK THREE GOES, AND THE LAST ONE WAS LOOKING AT IT.**

1. The first draft said **eight**, citing D-107's measurement — which was of **six** cards
   (56px each, row 95.2px, nothing clipped) and does not support eight.
2. So eight was measured: 53px per card, row 95px, **zero labels clipped**. That reads like a
   pass. It is a clipping answer to a legibility question.
3. Then it was **rendered and looked at**. At 53px, after `.stat-card`'s 12px side padding, a
   label has about **29px of content width** — less than one price. The en-dash became a line of
   its own in four of the eight cards (`$500K` / `–` / `$750K`) and the wrap ran to two or three
   lines unpredictably, so the row read as a rendering fault rather than as dense. A
   non-breaking space after the dash did not fix it and was removed: the width is the problem,
   not the break opportunity.

**`MAX_BANDS = 6`. D-107's measured number was right all along**, and two of the three attempts
to improve on it were measurements that answered a question nobody had asked.

The cost is resolution — a $600K–$2.4M market now gets a $500K step and four bands rather than a
$250K step and eight, because the ladder has no rung between them. Four legible bands beat eight
unreadable ones, and if the resolution ever matters more the fix is to widen the **ladder**, not
to raise the cap.

**`price_bands` page 1 holds two listings with a narrative, and that is decided rather than
open** (Jerry, 2026-09-29): this is a distribution report, the cards and the chart **are** the
content, and the listings are supporting detail. Unlike `market_snapshot` (D-102) nothing is
competing for that space, so there is no trade to make.

**Four regressions seen to fail:** the extent taken from this period's results instead of the
history · empty bands dropped again · the `999` sentinel restored · quartile boundaries restored,
which is the defect itself.


---


### D-112 — the market masthead paints every label in hardcoded white on a band that is often light

**Severity:** WRONG · **Affects:** page 1 of every market report, every table header, and the
default palette of every account that has not chosen an accent
**Status:** `fixed` — `fix/masthead-contrast-and-neutral-default`

Found 2026-09-29 by the first contrast measurement these documents have ever had
(`docs/CONTRAST_AUDIT_PDF_2026-09-29.md`). **560 failing text runs, the largest single finding in
a corpus of 1,387.**

```css
.masthead {
  background: linear-gradient(135deg, var(--header-bg) 0%, var(--header-bg) 50%,
                                      var(--primary-color) 100%);
  color: #ffffff;
}
.masthead-subtitle { color: rgba(255,255,255,0.7); }
```

**The variable names say the opposite of what they hold.** `market.jinja2` set `--header-bg` from
the affiliate's **primary** and `--primary-color` from their **accent**, so the band ran
*brand → brand → accent* with every label hardcoded white or 70% white.

| brand | white title (needs 3:1) | 70% white subtitle (needs 4.5:1) |
|---|---|---|
| lime `#84cc16` | **1.98** | **1.61** |
| amber `#f59e0b` | **2.15** | **1.71** |
| demo_title `#dc2626` | 4.83 | **2.99** |
| luxury_estates `#0d9488` | 3.74 | **2.60** |
| coastal `#0e7490` | 5.36 | **3.47** |
| violet `#7c3aed` | 5.70 | **3.58** |

**The subtitle and metric label failed for every brand at every stop.** There was no configuration
in which they passed.

`--header-bg` is also `.data-table thead th`'s background, so every table header in the product
was white text on the raw brand colour for the same reason.

---

**WHY THE BAND AND NOT THE TEXT.** The obvious fix is a better text colour. Measured, it cannot
work: **for three of the six audited brands no single colour clears 4.5:1 on both ends** — white
fails on amber and lime, near-black fails on coastal and violet. A band whose two ends are that
far apart in luminance cannot carry any one text colour, so the band is the defect.

`darken_until_readable(surface, text, alpha)` darkens each stop until the text on it is readable
and **stops at the first step that works**, so a brand already dark enough is returned untouched
rather than dulled to a safe constant.

**Guaranteed for the TRANSLUCENT subtitle, not for opaque white**, which is the harder case and
the one that was failing everywhere. The opaque title is then safe by construction, and the muted
subtitle survives as a design element instead of being flattened to the same white as the title.
`MASTHEAD_SUBTITLE_ALPHA` is pinned in the builder and asserted against the stylesheet, so the two
halves of one decision cannot drift — the §7.2 narrative-box contract in a second place.

| | before | after |
|---|---|---|
| title | 1.98 – 5.70 | **7.41 – 7.57** |
| subtitle / metric label | 1.61 – 3.58 | **4.53** |
| `--accent-on-dark` (the highlight) | 3.74 for two brands | **4.53 – 4.63** |
| market runs below threshold | **734** | **66** |
| worst ratio on the market surface | 1.08:1 | 2.66:1 |

The 66 that remain are the six status and tier badge colours — semantic chips on a 10% tint of
themselves, brand-independent, one decision, and deliberately not taken here.

---

**THE PERMANENT UNREAD WARNING IS GONE.** `_report_unreachable` printed

```
[CONTRAST] on_dark: cannot reach 4.5:1 for #0d9488 on #1B365D/#0d9488;
           best achievable 3.74:1. Returning it anyway
```

**on every single render.** The derivation worked, knew its own limit, and reported it to a log
nobody reads — the shape this project keeps finding. `compute_color_roles` is now fed the
guaranteed band instead of the raw colours, and **the log does not appear once across 90 renders**.
It is asserted rather than observed: `UNREACHABLE_CONTRAST_COUNT` must not move, so the degraded
path becoming normal again is a test failure.

---

**THE DEFAULT ACCENT WAS AN AFFILIATE'S BRAND.** `DEFAULT_ACCENT = "#0d9488"` is Luxury Estates'
teal, so every account that had not picked an accent shipped someone else's identity — and a third
of the masthead's failures were **brand-independent** because the band always ended in that teal.

Now `#4F46E5`, which is not a new colour: it is `DEFAULT_PRIMARY_COLOR` in `templates.ts` and
`social-templates.ts`, and the email moved to it for the same reason in D-098 — *a default is not
the affiliate's colour; nobody chose it, and it is ours to set.* The market PDF was the last
surface still defaulting to something else, so an unbranded account's PDF and its email did not
match. Now they do.

**And the same defect was one layer further down.** Thirteen template-level fallbacks
(`default('#0d9488')`, `#a6e4de`, `#5eead4`, `#0f766e`) were shades of that same teal, reachable
through any render path that omits the context value. Changing only the Python would have left it
live. All thirteen replaced and annotated `lint-allow-hex` rather than baselined, because a
platform default **is** a brand literal and the annotation exists for exactly that. Colour-lint
baseline 111 → 98.

---

**PULLED IN BECAUSE THIS CHANGE MOVED THEM.** `.stat-block-accent` paints accent-coloured text on
a 35% tint of the same accent, and the footer's initials circle painted the raw *primary* on a
tint of the *accent*. Both were already failing; changing the default moved one of them the wrong
way (`stat-block-label` 2.08 → 1.54). A fix that makes something worse is not finished, so both
now use `ink_on(colour, background)` — the existing readability helper applied to the **tint**
rather than to white, which is a different and easier background than `theme_color_on_light`
assumes.

---

**SEEN TO FAIL — five regressions, each observed red.** The band returning the raw colours · the
guarantee weakened to opaque white · darkening to a constant instead of stopping when satisfied ·
`DEFAULT_ACCENT` restored to the teal · the stylesheet's subtitle opacity dropped below what the
band guarantees.

**The fifth one did not fail on its first attempt.** `rgba(255,255,255,0.7)` appears four times in
the stylesheet and the edit hit `.report-header`'s copy, not `.masthead-subtitle`'s — the test
passed, correctly, on a masthead that had not changed. §0.6's substring rule in a fifth costume:
the string was right, the *site* was not, and a regression applied to the wrong site proves
nothing.

**The ratchet caught its own fix.** Regenerating the contrast board was refused until the
staleness test was satisfied: **190 entries no longer fail**, 0 added, 410 → 220.


---


---


### D-113 — the twelve-month trend chart never renders, because nothing fetches the history it reads

**Severity:** WRONG · **Affects:** §7.3's trend chart on `market_snapshot` and `inventory`, and
D-102's page-1 decision for `market_snapshot`
**Status:** `fixed` — `fix/d113-trend-history-never-fetched`

Found 2026-09-29 while starting D-111, whose recommended fix was to take its price-band extent
from "the twelve-month history `monthly_trend.py` already fetches". **It does not. Nothing does.**

`MarketReportBuilder._build_monthly_trend` reads one key:

```python
history = self.report_data.get("closed_history")
if not history:
    return None, None, None
```

`closed_history` appears in exactly three places in the repository:

| | |
|---|---|
| `market_builder.py:342` | reads it |
| `apps/worker/tests/test_monthly_trend.py:132, 351` | a test sets it |
| `scripts/measure_market_pagination.py:227` | my own measurement script sets it |

**No builder returns it and `tasks.py` never adds it.** `builder_data` is the report-type
builder's `result` plus `report_type`, `theme_id`, `accent_color`, `branding` and `ai_insights`
— and none of the eight builders emits a year of closed rows. So the guard returns
`(None, None, None)` on **every production render**, and the chart has never appeared in a
customer's report.

**WHAT IS UNREACHABLE.** `TREND_SERIES`, `median_series`, `count_series`, `_build_monthly_trend`'s
whole body past the guard, the `monthly_trend_chart` macro, `monthly_trend_note`, and
`MIN_CLOSED_FOR_MEDIAN`. All tested, all correct, none of it reached.

**And D-102 with it.** The decision that `market_snapshot`'s page 1 carries the twelve-month price
trend rather than a row of three listings is unrealised: with no trend, the layout falls back and
page 1 shows the three listings. `PAGE_1_CAPACITY`'s `with_trend` rows describe a state production
never enters. **The behaviour was decided, built, measured, pinned, and is not running.**

**Why nothing caught it.** Every test of the trend supplies `closed_history` itself, which is the
right thing for a unit test and means the suite proves the chart draws correctly from data it is
handed and says nothing about whether it is ever handed any. `measure_market_pagination.py` sets
it too, so the pagination measurements — including the `with_trend` capacities — were taken in a
state production does not reach. §0.6's *a test that supplies its own input cannot tell you the
input arrives*, which this list did not have and now does.

**THE FIX IS A FETCH, AND IT HAS A PRICE THIS PROJECT HAS ALREADY REASONED ABOUT.**
`compute/monthly_trend.py`'s own header says the series needs "one `minclosedate = today - 365`
query", and `closed_history_truncated` exists because that query can return more rows than a page.
So the work is: issue that fetch in the market path, pass the rows through as `closed_history`,
set the truncation flag honestly, and decide what a truncated year does — which the compute layer
already refuses to average, correctly.

**It is filed rather than taken because it changes the fetch path**, which has a vendor cost and a
pagination decision attached, and because it should be measured against a live feed rather than a
fixture — the same trip as D-105/D-106's confirmation.

**WHAT IT DOES TO D-111.** The recommendation recorded there rests on this history existing. It
does not, so the choice is now:

| | |
|---|---|
| **fix D-113 first, then D-111 as recommended** | 1 / 2 / 1 distinct edge sets. Needs the fetch change |
| **D-111 with the extent from the current result set** | 2 / 5 / **18** — still far better than quartiles' 33 / 219 / 363, and it needs nothing new. The thin-market case is the one that regresses |

Both beat what ships. Recorded here rather than chosen, because the first is a fetch-path change
and that is not a decision to make inside a banding fix.

---

**FIXED 2026-09-29 — the fetch, the refusal, and the gate's marker off.**

`build_closed_history(params)` asks for `status=Closed` with **`minclosedate = today − 365`** —
not `mindate`, which D-075 measured doing nothing at all, and the series buckets by `close_date`
so the filter has to be the one the feed applies to that field. `tasks.py` issues it for the two
report types in `TREND_REPORT_TYPES` and no others: it is a second vendor request, and six
reports that cannot use the answer should not buy it.

Cost is what `compute/monthly_trend.py`'s header priced: **one query, two requests at
`page_max = 500`**, against decision 01's 13 for a count series.

**No report filters on the history query.** The trend is the *market's* twelve months. A chart
captioned "median sale price" that silently showed only 3-bed homes under $1.5M is a different
statistic wearing the same label, and a test asserts each filter key stays out.

**Truncation refuses rather than draws.** `closed_history_truncated` is set when the fetch returns
`>= TREND_HISTORY_FETCH_LIMIT` rows, and `median_series` / `count_series` already refuse on it —
D-078's rule, the same contract `closed_was_truncated` carries for months of supply. Both halves
existed; what was missing was anything setting the flag. Asserted end to end, because **a fetch
setting a flag nothing reads is the shape of this defect all over again.**

**A failed fetch is non-fatal** and degrades to exactly what shipped for three weeks: no chart. A
market report without a trend is a complete report; one that failed to send because its chart
could not be drawn is not.

**`TREND_REPORT_TYPES` is DERIVED from `TREND_SERIES`, not a second literal** — the first draft of
that line was a second literal. The caller deciding whether to buy the data and the builder
deciding whether to draw it must read one list; two copies fail quietly in both directions.

**The contract gate's `xfail(strict=True)` came off**, which is what strict was for. Reverting the
producer was applied as a regression and the gate caught it — the first time it has been seen to
fail on the real defect rather than a planted one.

**PAGE_1_CAPACITY re-measured: identical.** That is the good outcome and it does not make the
earlier run evidence. It was a correct prediction, confirmed late.

**A CORRECTION TO THIS ENTRY'S OWN RISK STATEMENT, 2026-09-29.** PR #105 listed as its first
uncertainty that if `minclosedate` were ignored "the chart draws from an unfiltered year and
nothing here would notice". **That is wrong, and measuring it was a five-line check that should
have preceded writing it down.** `median_series` and `count_series` both iterate
`_window(today, 12)` and look up each month, so rows outside the window are never read — fed five
years of closings they return a series identical to the one from twelve months.

The exposure is the row cap instead: an ignored cutoff makes the fetch ask for the whole closed
history, hit `TREND_HISTORY_FETCH_LIMIT`, set the truncation flag and refuse. **"No chart on the
biggest markets", not "a wrong chart."** Still worth confirming — a chart that silently never
appears is precisely how this defect survived three weeks — but it is fail-safe, and the
overstatement travelled into the probe's comments and a message to the vendor trip before it was
caught.

**And the client-side re-filter that would have followed from it is NOT worth adding.** The
symmetry with `moi.py` is superficial: `moi` *counts* rows to derive a rate, so one extra row is
one extra sale and the re-filter is load-bearing; the trend *looks up* months, so an extra row
outside the window is never read. Filtering client-side cannot help with the one real failure
either, because truncation happens at fetch time — filtering rows that already came back does not
restore the ones that did not.

---

**AND A CORRECTION TO D-102, WHICH IS THE PART WORTH CARRYING.**

D-102's decision — that `market_snapshot`'s page 1 carries the twelve-month trend rather than a
row of three listings — **was taken on measurements from a state production could not enter.**
The numbers were real, the script produced them honestly, and the script supplied
`closed_history` to itself. Nothing in the chain was dishonest and the conclusion was still
reached on evidence that was not describing the product.

The decision holds now that the data flows, and the re-measurement says so. But "the measurement
was right" is a different claim from "the measurement was of the thing we were deciding about",
and only the second one was ever in doubt. Recorded because the next decision taken on a
fixture-fed measurement will look exactly as sound as this one did.


## BLOCKED-NEEDS-DEPLOYED-ACCESS (Phase 2B)

- **Can any existing schedule make `compute_next_run` raise?** Deliberately NOT filed as a
  defect, because nothing establishes it is reachable. If it is, the consequence is a
  permanent loop: the ticker's skip paths — the D-019 verification skip and the usage-limit
  skip — call `compute_next_run` before advancing `next_run_at`, and a raise sends the
  per-schedule handler into `conn.rollback()`, discarding the advance. The schedule is due
  again 60 seconds later, forever, logging a traceback and never sending. The auto-pause that
  would normally catch a repeatedly-failing schedule cannot help: it lives in the Celery task's
  failure handler (`tasks.py:1985`), and this failure happens in the ticker, before any task
  exists, so `consecutive_failures` is never incremented.
  **Why it is a query and not a code read.** The tempting answer is "the API validates cadence
  on create". That covers rows written after the validator existed; `schedules` dates to
  migration 0006 and `timezone` to 0015 (November 2025), and much of this codebase's validation
  is weeks old. The `CHECK (cadence IN ('weekly','monthly'))` has the same hole — `ADD
  CONSTRAINT ... NOT VALID` enforces new rows and skips old ones, and leaves no trace in the
  table definition — which is why the query reads `pg_constraint.convalidated` rather than
  trusting the schema. See §0.6, *a validator on the write path proves what gets written from
  now on, not what is already there*.
  **The query:** `scripts/check_schedule_cadence_validity.sql` (read only, four SELECTs). Nine
  raising cases, each measured against the function rather than reasoned about, and the
  predicate cross-checked against `compute_next_run` row by row on a scratch Postgres — 19
  cases, 0 disagreements, both directions. `apps/worker/tests/test_cadence_hazard_query.py`
  reads the CASE expression out of the `.sql` file so the query and the code cannot drift; both
  regressions (weakening the predicate, editing only the second copy) were applied and seen to
  fail.
  **Zero rows in sections 1 and 2** → close as unreachable, with the query as the evidence.
  **Any rows** → file it, and the fix is both sides: a guard in the ticker that marks the
  schedule failed rather than spinning, and cleanup of the rows.
---

## Workstream E, measured before it was started (2026-09-29)

Every E ticket in the master plan §08 was written from a review of six property PDFs. Those six
came from `scripts/generate_all_property_pdfs.py`, a QA script that **bypasses
`PropertyReportBuilder` entirely** — it owns a copy of the Jinja filters and a 200-line
`SAMPLE_CONTEXT` literal, and renders the same five templates with data production never
produces. So the reviewed documents are the product's templates fed a fixture, not the product.

Before fixing anything, all five themes were re-rendered through the path
`property_tasks/property_report.py` actually takes — `fetch_report_with_joins`-shaped
`report_data` → `PropertyReportBuilder(...).render_html()` — in two variants (`bare`: no
Google Maps key, default 7-page set, no agent photo; `full`: key present, photo set, all nine
pages), then screenshotted in Chromium at Letter width and looked at.

**Eleven of the twenty-two reproduce. Seven do not — they are properties of the QA script's
literal, not of the product.** The rest resolve differently than filed. The entries below are
the eleven, plus what the measurement found that no E ticket names.

**The seven that do not reproduce, with what was actually hardcoded:**

| E | filed as | what production does |
|---|---|---|
| **E4** | the aerial page is a stock photo of a different country, with a pin dropped on it | `SAMPLE_CONTEXT["images"]["aerial_map"]` is an Unsplash URL. `_build_images_context` emits a Google Static Maps roadmap for the subject's lat/lng, or `None`. **Zero Unsplash references in any of the ten production renders.** The real defect underneath is D-121 |
| **E5** | "Medium" is the *median* $610,750, not a comp — a chimera beside real rows | `SAMPLE_CONTEXT["stats"]["medium"]` is hand-written. `_build_stats_context` takes `sorted_by_price[len//2]` and `extract_comp_stats` reads every field off that one comp. Measured: medium = 1889 Bonita, $631,500 / 940 sf / 1953 / 7,446 lot / 0.58 mi — one real listing, coherent |
| **E7** | Group A's rows sorted independently; the 698 sf comp priced at $470,000 | same cause. All three of low/medium/high are internally coherent in every production render |
| **E9** | Market Trends six months stale — "JAN 2026 – MAR 2026", "Generated Mar 3, 2026" | `SAMPLE_CONTEXT["market_trends"]["generated_date"]` is the literal `"Mar 3, 2026"`. `compute/market_trends.py` sets `generated_date` to `now.strftime("%B %Y")` and `period_label` to `"Last 90 Days"`, both at fetch time |
| **E10** | a date row of four dates above a five-column table, the first reading as the subject's | no such row exists in any theme. The four dates are the chart's x-axis labels, under the bars |
| **E11** | `teal.pdf`'s contents renders as a skewed 3D card, one entry of seven, page number `0033` | teal's contents page renders correctly: six rows, dotted leaders, clean numerals. `teal.pdf` was an older artefact of a different generator run. D-121 is what is actually wrong with that page |
| **E12** | teal cover prints `123 Main St, Los Angeles, CA 90012`; the wordmark strikes the phone number | `SAMPLE_CONTEXT["agent"]["address"]`. Production's `_build_agent_context` composes the address from `company_address`/`city`/`state`/`zip` and yields `""` when they are unset, which is the whole of it today. No overlap in the rendered cover: the `TR` mark sits bottom-right, the phone bottom-left |

**And one that resolves inverted.** **E13** says teal's Area Sales summary row is dark navy on a
dark navy band. Measured, teal's `Sale Price` row passes. The row *is* unreadable — in
**classic** (`#ffffff` on `#4a90a4`, **3.61:1**) and **modern** (`#ffffff` on `#ff6b5b`,
**2.80:1**), both below the 4.5:1 they need. Filed under D-129.

This is D-113's lesson on a second surface, and the reason the measurement came first: *a
document that was rendered by something other than the production path is evidence about that
something.* Added to §0.6 of the master plan.

---

### D-114 — the missing-photo placeholder is an unlabelled grey box, on all six gallery sizes

**Severity:** BROKEN · **Affects:** every email gallery — `featured_listings`, `open_houses`,
`new_listings`, `price_bands`, and the three card sizes each uses · **Found during:** Workstream B
(register item **B5**), re-verified 2026-09-29
**Status:** `open`

On the register since the v1 audit and never given a defect entry, which is the read-path failure
D-009 was: an item marked **STILL OPEN** inside a planning document is not on the board, and the
board is what gets worked from.

`email/template.py:671`, `_GALLERY_SIZES`. Each of the six entries is a pair — the `<img>` and the
placeholder that stands in when `hero_photo_url` is absent. All six placeholders are the same
shape:

```python
'<div style="width: 100%; height: 160px; background: #f5f5f4; border: 1px solid #e5e7eb;"></div>'
```

A blank grey rectangle at the size of the photo, with no text, no glyph and no alt. A reader sees
a listing card with a hole in it and cannot tell whether the photo failed to load or the listing
has none. The register's fix — hatched fill, camera glyph, "Photo pending" — is unimplemented.

**Why it looks fixed and is not.** The C consolidation put `B5` in a comment directly above
`_GALLERY_SIZES`, explaining why the six placeholders are centralised. The comment says the
opposite of closure — *"current behaviour preserved, because this is a restructure"* — but a
register number written beside code reads as a fix to anyone skimming. The master plan §05 records
this risk explicitly; this entry is the board half of that record.

**Same family as D-122**, which is this defect on the property PDFs: an absent image handled by
painting a shape the size of the image and saying nothing.

---

### D-115 — price-band bars are normalised to the largest band while the labels beside them show share of total

**Severity:** WRONG · **Affects:** the `price_bands` email · **Found during:** Workstream B
(register item **B6**), re-verified 2026-09-29
**Status:** `open`

The second register item with no board entry. `email/template.py:1053`, `_band_rows`:

```python
max_count = max(counts) or 1
...
bar_pct = max(int((count_val / max_count) * 100), 2)
```

`bar_pct` is the band's count as a fraction of the **largest band**. `pct` is `pct_str`, taken
straight from `trend_stats`, which is the band's share of the **total**. The two are rendered on
the same row, so the widest band always fills the track while its label reads whatever its real
share is — the register's example is Move-Up at 43% beside a bar drawn to 100%.

Both numbers are correct in isolation. Neither is wrong; the pairing is. A reader takes the bar as
the picture of the number printed next to it, and it is a picture of a different number.

**What the C consolidation did and did not do.** It moved both calculations into this one function
so they cannot live in two files any more — which removes the *drift* risk and leaves the
*disagreement* in place, deliberately, because a restructure whose acceptance is an empty render
diff cannot also change what renders. The docstring says so. The defect is untouched.

**The fix is one line** (`bar_pct` from `pct_str`'s value rather than from `max_count`) and one
decision: whether a 4%-of-total band should be drawn as a 4% sliver or whether the chart wants a
second, explicitly-labelled "relative to largest" reading. The 2% floor already in the code exists
so a one-listing band does not vanish, and survives either choice.

---

### D-116 — the property report prints the owner's legal name to whoever requested it

**Severity:** BROKEN · **Affects:** all five property themes, both report types, and the consumer
lead-capture path in particular · **Found during:** Workstream E measurement (E1)
**Status:** `fixed` — `fix/e1-remove-owner-block`

Reproduced in all five production renders. The property page is headed **"Prospective Property"**
and its first field is **`Primary Owner: HERNANDEZ GERARDO J`**, read from
`report_data["owner_name"]` (SiteX assessor roll) via `_build_property_context`. Teal, bold,
classic and modern print `secondary_owner` beside it; teal's aerial page adds body copy reading
*"the neighborhood in which your prospective property is located."*

**Why the delivery path is the severity.** `lead_pages.py` → the consumer CMA task generates this
document for a stranger who typed their address into a landing page. What arrives is an automated
PDF that opens by naming the occupant from the assessor roll, addresses them as a *prospective*
buyer of their own home, and was not requested by name. The data is public record; leading with it
in an unsolicited automated document is not the same act as looking it up.

**Not a rendering bug.** `owner_name` is fetched, stored on `property_reports`, joined, built into
the context and printed. Removing the block is a product decision about what a CMA is for —
recorded here so the decision is made rather than inherited. The recipient knows who they are.

---

**FIXED 2026-09-29.** Jerry confirmed: remove the owner block; keep APN, county, legal
description, tax and assessment; rename the section; fix teal's copy.

| | before | after |
|---|---|---|
| page heading | *Prospective Property* | **Property Information** |
| section heading | *Owner Information* / *Owner & Legal Information* / *OWNER & ADDRESS* | **Parcel & Legal Information** / **PARCEL & ADDRESS** |
| rows removed | Primary Owner, Secondary Owner, Mailing Address | — |
| teal aerial copy | *"your prospective property"* | *"your property"* |
| modern section icon | a person glyph | a folder glyph |

Renaming the page to **Property Information** is what the contents page has always called it, so
this also closes one of D-121's four label mismatches.

**`mailing_address` went too, and that is a judgement beyond the instruction.** It is in neither
Jerry's remove list nor his keep list. For an absentee owner it is not a fact about the property,
it is where that person lives — the same disclosure E1 is about, and leaving it would have
defeated the fix on exactly the reports where it matters most. It defaulted to `full_address`
when absent, so an owner-occupier loses nothing. Putting it back is one row per template.

**The context keys are deliberately still built.** `_build_property_context` still emits all
three; they come from real columns other surfaces read. D-090's framing applies — the defect is
not that the value exists, it is that it reaches a template that prints it — so the gate sits at
the template boundary and walks every file under `templates/property/`, which a sixth theme
inherits on the day it is added.

**Checked rather than assumed:** `ai_overview._build_prompt` names every field it sends to the
model and none of the three is among them, so the executive summary cannot reintroduce the name.

**The fix's own footgun, found by rendering and now gated.** Removing the owner rows left bold's,
classic's and elegant's first block holding a single row, so parcel fields were moved into it —
and the block beside it already carried them. The first render printed **APN, County and Legal
Description twice on one page**. Nothing in the suite would have caught that;
`test_no_field_is_printed_twice_on_the_property_page` now does. §0.6, *render to verify*.

`apps/worker/tests/test_no_owner_identity_in_property_report.py`. Four regressions applied and
each seen to fail: reinstating an owner row, restoring the "prospective property" copy,
re-duplicating APN, and deleting the property page outright (the trap where removal passes an
absence test).

---

### D-117 — the comparables query applies no date filter at all, under copy that promises the last 12 months

**Severity:** BROKEN · **Affects:** every property report; every theme's Area Sales Analysis
heading and body copy · **Found during:** Workstream E measurement (E2)
**Status:** `fixed` — `fix/e1-remove-owner-block`

`apps/api/src/api/routes/property.py`, `_build_params` inside `get_comparables`. The params
assembled for SimplyRETS are `status`, `type`, `limit`, `postalCodes`, `cities`,
`minarea`/`maxarea`, `minbeds`/`maxbeds`, `minbaths`/`maxbaths`, `subtype`. **There is no
`minclosedate`, no `mindate`, and no post-filter on `close_date` anywhere in the six-level
fallback ladder.** Whatever the feed returns for a closed listing in that postal code is a comp,
at any age.

Meanwhile every theme prints a window:

| theme | the claim |
|---|---|
| teal | `SALES IN THE PAST 12 MONTHS` as the Area Sales Analysis subtitle |
| modern | a `LAST 12 MONTHS` pill on the chart card |
| bold, classic, elegant | *"comparable homes sold within the last 12 months"* in the section body |

`PropertyReportBuilder.fetch_comparables()` cannot correct it — it returns the stored list or
`None` and never queries.

**What the reviewed PDFs did and did not prove.** Their comps dated 5/10/23, 3/15/23, 4/25/22 and
4/8/22 are `SAMPLE_CONTEXT` literals, so they are not evidence of a live date window. The absent
filter is, and it is worse than a wrong window: there is no window. D-113's rule — *the render
proves the consumer, the query proves the producer* — cuts both ways here, and the query is where
the answer was.

**Two fixes, and they are different tickets.** Adding `minclosedate` narrows the result set in
thin markets, where the ladder already struggles to reach `FALLBACK_MIN = 5`; making the copy
honest costs nothing and can ship first. Which one is right depends on whether a four-year-old
comp is better than no comp, and that is a valuation question, not an engineering one. **[JERRY]**

---

**FIXED 2026-09-29.** Jerry: **six months**, `minclosedate`, and correct the copy.

`routes/property.COMP_CLOSE_WINDOW_DAYS = 180`, sent as
`minclosedate = today − 180` on **every level of the six-level fallback ladder** — a later level
widens the search and must not widen the window with it — and re-filtered client-side by
`_closed_within_window`. `minclosedate`, never `mindate`: D-075 measured `mindate` being accepted
and doing nothing, silently. The client-side pass is not belt and braces; `minclosedate` has only
been measured against the public demo feed and the production probe has not come back, so the
vendor filter is an optimisation and the local one is the guarantee. Same reasoning as
`compute.moi.closed_in_window` and `build_closed_history`.

**A SECOND DEFECT, FOUND WHILE FIXING THE FIRST, AND IT CHANGES WHAT "CORRECT THE COPY" MEANS.**

`ComparablesRequest.status` defaults to `"Active"`, and the wizard defaults to it too
(`property-wizard.tsx:53`, with a toggle to `Closed`). So a property report may carry **homes
that are currently for sale and have not sold at all** — under a heading reading *SALES IN THE
PAST 12 MONTHS* and a paragraph beginning *"comparable homes sold within the last 12 months"*.

Changing 12 to 6 fixes the window and makes this worse: it states a wrong thing more precisely.
So the copy is now derived from what the comps actually are, by
`PropertyReportBuilder._comps_window()`, using the same active/closed distinction
`_build_comparables_context` already applies per comp:

| comps | heading | body |
|---|---|---|
| all closed | *Sales in the past 6 months* | *"…sold within the last 6 months…"* |
| all active | *Comparable homes currently for sale* | *"…currently listed… what sellers are asking rather than what buyers have paid."* |
| mixed | *Recent sales and current listings* | *"…mixes sale prices with asking prices."* |
| none | *No comparable properties found* | what to widen |

The page describes its contents instead of asserting a window somebody hoped for. This is beyond
the literal instruction and is flagged as such; the alternative was to print "sold in the last 6
months" over active listings.

**And `minclosedate` is therefore sent only when the query is closed sales alone.** Not on
`Active` — an active listing has no close date, so the filter either empties the result or is
ignored, and neither is a filter. Not on `Active,Closed` either: SimplyRETS applies the parameter
to the whole response, so it would silently drop the active half of a deliberately mixed search.
The wizard never sends `All`, but the endpoint accepts it, and *unreachable from our UI* is not a
reason to send a parameter that would be wrong if it arrived.

**Two deployments, one number.** API and worker are deployed separately, so the constant cannot
be shared; `PropertyReportBuilder.COMP_CLOSE_WINDOW_DAYS` mirrors it and
`test_the_api_and_the_worker_agree_on_the_window` asserts they match. A query window and a
printed window drifting apart *is* D-117, so the agreement is asserted rather than hoped for.

**Tests.** `apps/api/tests/test_comp_close_window.py` drives the real endpoint with
`simplyrets_fetch_properties` replaced by a spy, because `_build_params` is a closure with
nothing importable to call and testing an extracted copy would prove the copy (§0.6). Plus a
structural gate: no live template may hardcode a month count in window copy.
Six regressions applied and each seen to fail — `mindate` for `minclosedate`, dropping the
client-side pass, sending the window on an Active query, the two constants disagreeing, a
hardcoded "12 MONTHS" back in a template, and calling active listings sales.

**Not fixed, and Jerry asked for a recommendation rather than an assumption** — what the report
does when six months returns fewer than three comps. See the note under D-132.

---

### D-118 — the subject property's "Sale Price" is its Prop 13 tax assessment

**Severity:** WRONG · **Affects:** the Area Sales Analysis table in all five themes, and the
price-per-sqft derived from it · **Found during:** Workstream E measurement (E3)
**Status:** `fixed` — `fix/d118-remove-assessment-row` (the assessment is out; what fills
the row is D-134, and it stays empty until then)

`property_builder.py:_build_stats_context`:

```python
# Use assessed_value as fallback for estimated_value since SiteX may not provide it
est_value = sitex_data.get("estimated_value") or sitex_data.get("assessed_value") or 0
piq = { ..., "price": _safe_num(est_value, 0),
        "price_per_sqft": _safe_num(self._calc_price_per_sqft(est_value, sitex_data.get("sqft")), 0) }
```

Rendered, with the measurement's SiteX payload (`assessed_value: 428248`, `sqft: 786`):

```
Sale Price     $428,248    $470,000    $631,500    $635,000
Price/Sq.Ft.   $544        $610        $671        $696
```

The first column is the subject. **$428,248 is the county's assessed value** — a Prop 13 figure
that tracks the 1949 house's last reassessment, not what it would sell for — printed in a row
whose other three cells are real closed sale prices, under a header that says `Sale Price` in
every theme. The seller reading this sees their home valued 9% below the cheapest comp. `$544`
per square foot is the same error divided by area.

**`estimated_value` is never populated.** No writer anywhere in the repository sets it on
`sitex_data`, so the `or` chain always falls through to the assessment. The comment describes the
fallback as occasional; it is the only path.

**Three ways out, and the choice is Jerry's:** leave the cell empty and label the row honestly for
the subject; print the assessment under its own label (`Assessed`, which the property page
already does correctly one page earlier); or compute an estimate from the comps, which is what a
CMA is and is a product feature rather than a bug fix. **[JERRY]**

---

**JERRY'S ANSWER, 2026-09-29 — and it is two things, not one.**

> The subject's sale-price row shows the **last actual sale price**, not an assessment. Separately,
> an **estimated value** is derived by us from the comparable range — a different figure with a
> different label, not a substitute for this one. If the feed carries a last sale, read it; if it
> doesn't, show nothing rather than a substitute. Never the assessment in an unlabelled price row.
> Investigate whether the data exists at all before designing around it.

**INVESTIGATION — the answer is "one of the two sources is unknowable from here, and that is
itself the finding".**

**SiteX: cannot be answered from the repository, and the two possible answers lead to different
tickets.**

| | |
|---|---|
| `SiteXClient._parse_response` | extracts address, owner, legal, tax and characteristics. Reads **no** sale-history field |
| `PropertyData` | has no slot for one, so a field present in the payload would be dropped at the boundary regardless |
| captured payloads | **none.** Every `.json`, `.py` and `.md` in the repository was searched for `PropertyProfile`; the only hit is the parser itself |

So *"SiteX does not give us last-sale data"* and *"SiteX gives it to us and we throw it away"* are
indistinguishable from inside the code. The first is a vendor/feed-id question; the second is a
twenty-line parsing ticket. **One real lookup separates them**, and `raw_response` is already
retained on every lookup, so nothing new has to be built to find out.

`scripts/probe_sitex_sale_history.py` — one address lookup, read only, prints every key under
`Feed.PropertyProfile` and opens any section whose name suggests sale, transfer, deed or
transaction history. It does **not** print owner names or mailing addresses at any depth, and it
truncates every value, because the output is meant to be pasted into a ticket and D-116 is about
exactly that data leaving the system. The redaction is tested
(`apps/api/tests/test_sitex_probe_redaction.py`, with the weakening applied and seen to fail),
not trusted. Matched on substrings rather than a fixed key list, because the exact spelling is
the thing being discovered.

**SimplyRETS: the field exists; the coverage does not follow from that.** `closePrice` and
`closeDate` are already proven fields on closed listings (D-074, D-105). A subject that has been
MLS-listed and closed can be found. But the MLS knows only MLS history — **a home sold FSBO,
off-market, at auction, or transferred within a family is invisible to it, and so is one that has
never been listed.** So a hit proves the field and says nothing about how often a real subject
will have one. Probe section 3b reports the field and states that limitation in its verdict
rather than letting a "CONFIRMED" read as coverage.

**A THIRD READ-WITH-NO-WRITER, FOUND WHILE LOOKING.** `estimated_value` is written by nothing —
that is this entry. `routes/mobile_reports.py:187-188` reads `last_sale_date` and
`last_sale_price` off the stored `property_data` JSON, and **nothing writes either one**:
`tasks.py:2277` builds that blob from four address fields plus whatever the lead-capture form
left there. Three fields, one family, and it is D-009's family — see **D-133**.

**WHAT IS NOT BUILT, DELIBERATELY.** Jerry asked for the investigation before the design, and the
design depends on the probe. The estimated-value half needs a stated method that survives a
seller asking how it was calculated, which is its own ticket and its own decision — recorded as
**D-134** rather than started.

**REMOVED 2026-09-30, on Jerry's instruction, without waiting for the probe.**

> A wrong number is worse than an empty one, and if the probe says SiteX has no sale data the row
> stays empty regardless. Don't hold a correct removal on a replacement that may not arrive.

`est_value = sitex_data.get("estimated_value")` — no fallback. `piq.price` and
`piq.price_per_sqft` are `None` when it is absent, **not `0`**: zero is a price, and
`format_currency(0)` renders `$0`. `format_currency(None)` renders `N/A`, which is what an
unknown sale price is. Rendered, all five themes:

```
Sale Price     N/A     $470,000   $631,500   $635,000
Price/Sq.Ft.   N/A     $610       $671       $696
```

The assessment survives on the property page under `Assessed Value`, inside `Tax & Assessment`,
which is where it was always correct. A test asserts both directions: gone from the analysis
table, still present in the report.

**And the row's LABEL lied the same way the subtitle did.** Over active comps `_extract_price`
returns `list_price`, so a row headed *Sale Price* was showing asking prices. It now comes from
`comps_window.price_row` — *Sale Price* / *List Price* / *Price* — and the per-comp cards from
`comp.price_label`, beside the `sold_date_label` that already made the same distinction.

Four regressions applied and seen to fail: restoring the fallback, `0` instead of `None`,
severing the row from `estimated_value` altogether (so a later producer fix would look broken),
and calling asking prices sale prices.

---

**RESOLVED 2026-09-30 — the probe came back and SiteX had it all along.**

`Feed.PropertyProfile.SaleLoanInfo`, exact keys from production:

```
TransferDate    20151223      (a YYYYMMDD int, not a date string)
SalesPrice      369000
PricePerSQFT    469.0
DocumentNumber  15-1611995
```

**The subject sold for $369,000 in December 2015, and that figure has been sitting in
`raw_response` on every property report ever generated, unread**, while the page printed the
assessment. A twenty-line parsing ticket, as hoped.

**It closes the $369,000 mystery.** That number appeared in Group A of the six reviewed PDFs and
nobody could account for it — the Workstream E measurement listed it among the QA script's
invented literals. It was not invented. It is the real last sale price, reaching the page by a
path the current parser stopped taking. **Group A was not wrong; it was reading something
production stopped reading.** One more turn of §0.6's rule about artefacts: a figure you cannot
account for is a question, not a verdict.

**What was built.**

| | |
|---|---|
| `PropertyData` | `last_sale_price`, `last_sale_date`, `last_sale_price_per_sqft`, `last_sale_document` |
| `_parse_response` | reads `SaleLoanInfo`; `SellerName`, `LenderName` and `TitleCompany` deliberately not parsed — person and counterparty names, out for D-116's reason |
| `_sitex_date` | `20151223` → `"2015-12-23"`. **`0` → `None`, not 1970** |
| `_build_stats_context` | the row shows the recorded sale; `estimated_value` still ranks first, for D-134 |
| `price_display` | `$369,000 · Dec 2015` |
| the wizard, lead capture, the consumer task | all three carry the fields, or the two paths disagree — D-135's `land_value`/`$0` split recreated |
| `mobile_reports` | the same two fields, plus `tax_assessed_value or assessed_value` |

**The date carries because the figure alone would repeat the assessment's harm.** A 2015 sale
printed bare sits 25% below four recent comps and reads as a current valuation. True number,
wrong question answered — which is what the assessment was.

**SiteX's `PricePerSQFT` is used, not derived.** Theirs is computed against the sqft recorded
with the sale, which differs from `PropertyCharacteristics` after an addition, and a row that
disagrees with itself is worse than one slightly stale. An `estimated_value` we compute gets a
derived ratio instead, because SiteX's belongs to SiteX's price.

**Two of five regressions were NOT caught, and both were my tests.**

* Deriving the ratio instead of using SiteX's left the suite green, because the fixture's
  `369000 / 786` rounds to `469` — SiteX's own figure. The assertion could not tell which was
  used. A case where they diverge now exists and fails.
* Removing `_sitex_date`'s range check left the suite green too, and **that one is correct**:
  measured, `date()` already rejects `0`, `-20151223`, `201512`, `2015`, `99999999`,
  `10000000` and `2015122300`, because floor division sends each to an impossible year, month or
  day. The guard is documentation, not mechanism, and the comment now says so — a guard whose
  removal changes nothing is otherwise assumed load-bearing by whoever finds it.

The three that were caught: parsing `SellerName` into the model, dropping the date from the
cell, and letting a computed estimate inherit SiteX's ratio and date.

---

**PROBE RETURNED 2026-09-30, AND ITS VERDICT ON THIS ENTRY IS HALF WRONG — SPLIT.**

`closePrice` on **0 of 20** closed listings. `closeDate` on **0 of 20**. The probe's own wording
was *"cannot be built on a field this sparse without a fallback"*, and that conflates two
different questions. Corrected in the script so a re-run says the right thing:

| | |
|---|---|
| **the subject's last-sale row** | **unaffected, and shipped.** It does not come from SimplyRETS. SiteX answers it from `SaleLoanInfo`, cleanly, and this result changes nothing about it |
| **any comp-level sale price** | **no source exists.** The feed does not carry the fields. That is not sparseness to engineer around — it is the absence of a producer, and no fallback can invent one |

The second half matters beyond this entry: a comp's `price` on the analysis table and the
comparables cards is `listPrice` wherever `closePrice` is absent, which is **every closed comp
on this feed**. So a "Sale Price" column over closed comps is showing list prices. D-118's own
`comps_window.price_row` work labels active comps correctly; **it cannot label a closed comp
whose price is secretly a list price**, because nothing distinguishes them. Filed as **D-144**.

---

### D-119 — the Area Sales Analysis table shows three comps; the chart beside it shows four

**Severity:** WRONG · **Affects:** the Area Sales Analysis page in all five themes ·
**Found during:** Workstream E measurement (E6)
**Status:** `open`

`_build_stats_context` reduces the comparables to exactly three named slots:

```python
low_comp  = sorted_by_price[0]
high_comp = sorted_by_price[-1]
med_idx   = len(sorted_by_price) // 2
med_comp  = sorted_by_price[med_idx]
```

With the four comps in the measurement (470,000 · 590,000 · 631,500 · 635,000) that is index 0,
index 3 and index 2. **Index 1 — 1848 1st St at $590,000 — is in no column.** It appears in the
chart directly above the table, in the Sales Comparables page's four cards, and in the Range of
Sales averages. It is absent from the analysis, in all five themes, with nothing on the page
saying three of four are shown.

Generalising: for *n* comps the table shows at most 3 and silently drops *n−3*. It also collapses
when *n* is small — at *n* = 2, `low` is index 0, `med_idx` is 1 and `high` is index 1, so the
same listing fills two columns; at *n* = 1 all three columns are the same listing; at *n* = 0
`extract_comp_stats({})` returns a full row of zeros and the table renders `0 0 0 0` throughout.
None of these states is guarded.

**"Medium" is not a median.** `len // 2` on a price-sorted list of four is the third-cheapest, so
the column labelled Medium sat at $631,500 against a true median of $610,750. The value is a real
listing, which is the right choice and is what makes the label wrong. (E5 filed the opposite —
that Medium is a computed median and therefore no property at all. That is the QA fixture's
behaviour, not the builder's.)

---

### D-120 — `pools` is computed from a truthy string, so a house with no pool has one, one page after saying it doesn't

**Severity:** WRONG · **Affects:** the teal Area Sales Analysis table; the `pools` and `stories`
context keys in all five themes · **Found during:** Workstream E measurement (E8)
**Status:** `fixed` — `fix/d137-absent-is-not-a-default`, together with D-137. **The
mechanism as first filed was unreachable; see the correction at the end.**

```python
"pools": 1 if sitex_data.get("pool") else 0,
```

SiteX reports an absent pool as the **string** `"None"`, which is truthy, so the subject's `pools`
is `1`. `_build_property_context` handles the same field correctly — `"pool": sitex_data.get("pool") or "No"` — and prints it verbatim. Rendered, teal, one page apart:

```
page 03   Pool/Spa:   None
page 04   Pools       1     0     0     0
```

Two statements about one house, both from the same source field, contradicting each other inside
one document.

**The same row is a second defect.** `"stories": _safe_num(comp.get("stories"), 0)` renders
`Stories  0  0  0  0` — SiteX does not return `stories` and neither does the comps payload, so a
missing value is printed as the number zero for every column. This is D-090's family on a surface
D-090 did not cover: *absent* rendered as *measured to be none*. A house with zero storeys is not
a thing, so the row is self-evidently data-absent to a careful reader and quietly wrong to
everyone else.

Only teal renders these two rows (see D-124), so only teal shows the contradiction — but both
values are in the context for all five themes and any theme that adds the row inherits it.

---

**CORRECTION, 2026-09-30 — the mechanism as filed is UNREACHABLE, and I filed it.**

The generalised contract gate (D-135) settled it: **`sitex_data` never carries `pool`.** Neither
producer writes it —

| producer | keys | has `pool`? |
|---|---|---|
| `services/sitex.PropertyData.model_dump()` | 28 | **no** |
| the wizard's `sitex_data` payload (`step-generate.tsx:104`) | 25 | **no** |

So `1 if sitex_data.get("pool") else 0` always takes the `else`, `pools` is always `0`, and the
truthy-`"None"` bug cannot fire in production. The `"None"` in the evidence came from **my own
test fixture**, which invented a `pool` key SiteX does not return.

This is the failure this workstream was opened to avoid, committed by the person auditing for
it. §0.6 says *a document rendered by something other than the production path is evidence about
that something* — and **a fixture is that something too.** The Workstream E measurement replaced
the QA generator's invented context with a production-*shaped* one and never checked that every
key in it was one production can actually produce. Shaped like production is not the same as
producible by production.

**What is actually wrong, and it is worse than the bug it replaces.** With no data behind them,
the defaults assert facts:

```python
"pool":       sitex_data.get("pool") or "No",             # every report: "Pool/Spa: No"
"tax_status": sitex_data.get("tax_status") or "Current",  # every report: "Tax Status: Current"
```

`No` and `Current` are not placeholders. They are claims about a specific person's property,
printed with the same weight as the APN. A dash says *we don't know*; these say *we checked*.
The pool claim reaches a seller who may well have one; the tax claim asserts a stranger's
property taxes are paid. **Refiled as D-137**, which is the live defect. This entry stays open
only for `stories`, whose missing-as-zero is real and unaffected.

---

### D-121 — the contents page is hardcoded, and lists two pages the report does not contain

**Severity:** BROKEN · **Affects:** the contents page of all five property themes, in the default
production page set · **Found during:** Workstream E measurement (E15, E17, and a third thing
neither names)
**Status:** `open`

The default page set, set in `PropertyReportBuilder.__init__` when `selected_pages` is empty, is
seven pages:

```python
["cover", "contents", "aerial", "property", "analysis", "comparables", "range"]
```

`overview` and `market_trends` are **not** in it. Both pages are conditional on data that the
default path does not request. But the contents page in every theme is a literal block of seven
`<div class="contents-item">` rows with literal page numbers and no reference to `page_set`:

```html
<div class="contents-item"><div class="contents-num">05</div><div class="contents-text">Market Trends</div><div class="contents-dots"></div><div class="contents-page">07</div></div>
```

`grep -c "if " ` over the contents block of each theme returns **0** for all five. Teal guards one
row (`{% if "overview" in _pages and overview_text %}`) and nothing else.

**Three separate failures, all on this one page.**

1. **It advertises absent pages.** Every default production report's contents lists *Market
   Trends* at page 07; four of the five also list *Executive Summary* at page 02. Neither page is
   in the document. A reader turning to page 7 finds Sales Comparables.
2. **The numbers are decorative.** The printed footers of teal's bare render run `03, 04, 05 …`
   against contents entries claiming `04, 05, 06 …`. Every entry is off, by a margin that depends
   on which optional pages happened to be dropped, and the literals skip `03` even when nothing is
   dropped.
3. **The labels are not the page titles.** Measured against each theme's own `page-header-title`:

   | contents says | the page says |
   |---|---|
   | Aerial Property View / Aerial Snapshot | **Aerial View** |
   | ~~Property Information~~ | ~~**Prospective Property**~~ — closed by D-116's rename |
   | Estimated Value Range | **Range of Sales** |
   | Comparable Sales *(elegant)* | **Sales Comparables** |

E15 read the symptom as "the aerial page carries no number". It does carry one — see D-129, it is
painted white on white. E11 read teal's contents as structurally broken; it renders correctly and
is wrong in content instead.

**The fix is structural or it will rot.** A contents page derived from `page_set` with numbers
counted at render time removes all three at once; patching the literals leaves the next
`selected_pages` value to break them again.

---

### D-122 — no theme handles a missing agent photo, and the theme that has one renders its alt text

**Severity:** BROKEN · **Affects:** the cover of all five property themes, and the executive
summary page · **Found during:** Workstream E measurement (E14)
**Status:** `open`

With `agent.photo_url` unset — the state for any user who has not uploaded an avatar, and the
`bare` variant of the measurement — every theme paints the frame and nothing in it:

| theme | what renders |
|---|---|
| bold | a solid navy square |
| classic | nothing; the name shifts left into the gap |
| elegant | an empty gold-ruled circle |
| modern | a grey rounded square |
| teal | a grey circle with a teal ring |

Five themes, five different empty shapes, no label on any of them. `_build_agent_context` passes
`photo_url` through and no template has a fallback branch.

**And the populated case is worse.** In the `full` variant, with `photo_url` set to a URL that
does not resolve, elegant's executive summary renders the browser's broken-image glyph **with the
alt text `Zoe Noelle` wrapping out of the circle**. PDFShift renders from its own servers, so a
photo behind any referrer or IP restriction reaches the customer exactly like this;
`embed_images_as_base64` is best-effort and returns the original URL when the fetch fails.

Same family as **D-114** (B5) on the email side: an absent image handled by painting a shape the
size of the image and saying nothing. One labelled placeholder — initials, or a person glyph with
the agent's name beside it — serves both surfaces, and the property report has the harder case
because the frame shapes differ per theme.

---

### D-123 — the production property report contains no photographs of anything

**Severity:** WRONG · **Affects:** all five property themes · **Found during:** Workstream E
measurement (E20, which named two themes)
**Status:** `open`

Counted directly in the rendered HTML: `<img>` tags per document.

| variant | bold | classic | elegant | modern | teal |
|---|---|---|---|---|---|
| **bare** (no Maps key) | **0** | **0** | **0** | **0** | **0** |
| **full** (Maps key set) | 2 | 2 | 3 | 2 | 2 |

The two or three in `full` are the Street View hero, the Static Maps aerial and the brand logo.
**Comp photos are zero in every theme in both variants**, because `_build_comparables_context`
resolves a comp's image from `image_url` / `photo_url` / `photos[0]`, and the comps the API's
`get_comparables` route stores carry none of the three — its projection is address, price, beds,
baths, sqft, `closeDate`, geo and distance. The `map_image_url` fallback needs the same Maps key.

So a Sales Comparables page that is built entirely around four photo cards renders four grey
rectangles, and a report whose Aerial View page exists to show an aerial view shows an empty
placeholder under copy asserting *"This is an aerial view of the neighborhood in which your
prospective property is located."*

E20 filed this as a theme-parity gap — *"Classic renders no imagery at all"* while others do. The
parity differences in the reviewed set came from which Unsplash URLs `SAMPLE_CONTEXT` happened to
supply to which template. **On the production path no theme has an advantage, because no theme has
a photograph.** Whether `GOOGLE_MAPS_API_KEY` is set in the worker's environment is not readable
from the repository and is the first thing to check.

---

### D-124 — the analysis table's field set changes with the theme, so the theme choice changes the analysis

**Severity:** FRAGILE · **Affects:** the Area Sales Analysis table, all five themes ·
**Found during:** Workstream E measurement (E16)
**Status:** `open`

Rendered from one identical context, the table's rows:

| row | bold | classic | elegant | modern | teal |
|---|---|---|---|---|---|
| Distance | ✓ | ✓ | ✓ | ✓ | ✓ |
| Living Area | ✓ | ✓ | ✓ | ✓ | ✓ |
| Price/Sq.Ft. | ✓ | ✓ | ✓ | ✓ | ✓ |
| Year Built | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lot Size | ✓ | ✓ | ✓ | **✗** | ✓ |
| Bedrooms | ✓ | ✓ | ✓ | ✓ | ✓ |
| Bathrooms | ✓ | ✓ | ✓ | **✗** | ✓ |
| Stories | ✗ | ✗ | ✗ | ✗ | **✓** |
| Pools | ✗ | ✗ | ✗ | ✗ | **✓** |
| Sale Price | ✓ | ✓ | ✓ | ✓ | ✓ |

Every value is in `stats` for every theme; each template picks its own subset by hand. An agent
switching from Classic to Modern for visual reasons silently removes lot size and bathrooms from
the comparison their client receives, and switching to Teal adds two rows that are always `0`
and `1/0/0/0` (D-120).

FRAGILE rather than WRONG because no single render is incorrect — the property is that the
document's content is a function of its skin, which no part of the system states or checks. The
durable fix is one shared table partial driven by a field list; the cheap one is a test that
renders all five and asserts the row sets match.

---

### D-125 — integers render with a decimal point throughout the analysis table

**Severity:** ROUGH · **Affects:** the Area Sales Analysis table in all five themes; the property
page's Bathrooms field · **Found during:** Workstream E measurement (E19)
**Status:** `open`

`_safe_num` returns `float(val)` and the templates interpolate it raw. Every numeric cell that is
not currency-formatted therefore carries `.0`:

```
Living Area   786.0    770.0    940.0    912.0
Year Built    1949.0   1910.0   1953.0   1952.0
Bedrooms      2.0      3.0      2.0      3.0
Bathrooms     1.0      1.0      1.0      1.0
```

`1949.0` as a year and `2.0` as a bedroom count read as machine output in a document a seller is
meant to take seriously. Lot Size escapes because it goes through `format_number`; Price/Sq.Ft.
escapes because it goes through `format_currency`.

The property page has the same thing in one place — `Bathrooms: 1.0` — and there it matters more,
because `1.5` and `2.5` are real values, so the fix cannot simply be `int()`. A filter that drops
a trailing `.0` and keeps a genuine half is the shape of it; `compute/price_bands.format_price`
already does exactly this for currency and is the precedent.

E19 recorded this as unevenly applied — *"Group A formats correctly"*. Group A is the QA script,
whose own `format_number` differs from production's. **On the production path all five themes are
affected identically.**

---

### D-126 — four of the five sales charts have no values and no axis

**Severity:** ROUGH · **Affects:** the Area Sales Analysis chart in bold, classic, elegant and
modern · **Found during:** Workstream E measurement (E22)
**Status:** `open`

Rendered, the same four comps in each theme:

* **teal** — each bar labelled with its price (`$632k`, `$635k`, `$470k`, `$590k`) above and its
  month below.
* **bold, classic, elegant, modern** — month labels only. No value on any bar, no y-axis, no
  gridline labels, no scale anywhere on the card.

Four bars of differing heights with no quantity attached is decoration. A reader can see that one
comp sold for less than another and cannot tell whether the gap is $20,000 or $200,000 — and the
prices are in the table directly underneath, so the chart adds nothing it does not also obscure.
The bars are not zero-anchored either, which exaggerates the differences that are visible.

E22 named elegant and said `teal_report` gets it right and should be the standard. Measured, that
holds and the scope is three themes wider. Teal's labels are `.bar .val` at `top:-24px`, dark navy
on the card, and they are legible (the contrast auditor reports them at 1.00:1 against the bar's
gradient — a false positive, see D-130).

---

### D-127 — teal labels the subject column `PIQ`

**Severity:** ROUGH · **Affects:** the teal Area Sales Analysis table · **Found during:**
Workstream E measurement (E18)
**Status:** `open`

Teal's table heads its first column **`PIQ`**. Bold, classic, elegant and modern all say
`Subject`. "Property in question" is appraisal shorthand; the document's reader is a homeowner who
has never seen it. It also sits directly above the row that prints the tax assessment as a sale
price (D-118), so the one column a seller most needs to understand is the one labelled in jargon.

One word, one template. Recorded separately from D-124 because that entry is about which rows
exist and this is about what a heading says.

---

### D-128 — the executive summary is two sentences on an otherwise empty page

**Severity:** ROUGH · **Affects:** the `overview` page, in the themes that carry it ·
**Found during:** Workstream E measurement (E21)
**Status:** `open`

Measured in the `full` variant, elegant: the page holds a label, a title, a two-line paragraph and
the agent's contact line, and then **roughly 78% of the page is empty**. `ai_overview.generate_overview`'s output is a short paragraph and the page is a full Letter sheet
with no other content block.

Not in the default page set, so it reaches a customer only when `selected_pages` includes
`overview` — which makes it lower priority than it looks in the E register, and does not make it
acceptable when it does render. Either the page earns its sheet (the key figures alongside the
prose, which is what the space is for) or the summary moves onto the cover or the property page.
A blank two-thirds reads as a printing failure.

---

### D-129 — 229 text runs on the property PDFs fail WCAG contrast, and the page number on the aerial page is invisible in four themes

**Severity:** BROKEN · **Affects:** all five property themes · **Found during:** Workstream E
measurement, first contrast measurement this surface has had
**Status:** `open`

Measured by pixel, over the ten production renders (five themes × two variants), 2,344 text runs:

| variant | runs | below 4.5:1 | below WCAG threshold | worst |
|---|---|---|---|---|
| bare | 1,047 | — | **69** | 1.00:1 |
| full | 1,297 | — | **160** | 1.00:1 |
| **total** | **2,344** | **250** | **229** | **1.00:1** |

| theme | runs | failing |
|---|---|---|
| bold | 450 | 41 |
| classic | 448 | 39 |
| elegant | 450 | **16** |
| modern | 426 | **91** |
| teal | 570 | 42 |

229 failing runs in **48 distinct (selector, colour, background) combinations**. WCAG's large-text
allowance is applied, not ignored.

**Invisible, not merely low — verified by cropping the rendered page and looking:**

| ratio | what | where |
|---|---|---|
| **1.00:1** | `div.num` — the page number `03` on the Aerial View page, `#ffffff` on `#ffffff` | bold, classic |
| **1.00:1** | `div.brand` — the footer line `Classic Collection • TrendyReports` | classic |
| **1.07:1** | `div.num` — the same page number | teal |
| **1.11:1** | `div.num` — the same page number | elegant |
| **1.31:1** | `div.brand` — `Elegant Collection` | elegant |

**This is E15's real mechanism.** E15 filed the aerial page as carrying *no* number. It carries
one, in white, on white, in four of the five themes — which is why the sixth footer exists in the
markup and nothing is visible on the page.

**The largest visible groups:**

| ratio | needs | runs | what |
|---|---|---|---|
| 1.90:1 | 3.0 | 10 | teal `h2.section-title` — **every page heading in the theme**, `#34d1c3` on white |
| 2.52:1 | 4.5 | 26 | bold `div.contents-page` and `div.brand`, `#d69649` on white |
| 2.34–2.56:1 | 4.5 | 29 | modern's entire muted-text role, `#94a3b8` on white and `#f1f5f9` |
| 2.80:1 | 4.5 | 18 | modern `td` in the Sale Price summary row and `div.comp-card-price`, white on `#ff6b5b` |
| 3.61:1 | 4.5 | 22 | classic `div.page-header-label` and the Sale Price row, `#4a90a4` both directions |
| 2.25–3.30:1 | 4.5 | 26 | the market-trends gauge zone labels (`Seller's`, `Balanced`, `Buyer's`), all four themes that have the page |

**On the 653 figure.** The 2026-09-29 market audit reported 653 failing runs on the property
surface. That was a different corpus — 30 documents, five themes × six brand colours, rendered
from `measure_pdf_contrast.py`'s own minimal fixture with no market-trends or overview page — and
measured by the DOM walker, which over-reports here (D-130). **229 is the production-path,
pixel-verified number for ten documents.** Neither supersedes the other; they count different
things, and the brand sweep is still owed on this surface.

**Why modern is four times worse than elegant.** Modern's palette leans on `#94a3b8` for every
secondary string and `#ff6b5b` as a fill behind white text. Both are single token definitions.
Elegant's 16 are almost all on the market-trends page it shares with the others. This is the
market surface's D-112 shape again: a small number of role definitions, not a long tail.

---

### D-130 — the contrast auditor over-reports on absolutely-positioned and `pointer-events:none` text

**Severity:** FRAGILE · **Affects:** `scripts/measure_pdf_contrast.py` and the
`apps/worker/tests/test_pdf_contrast.py` ratchet it feeds · **Found during:** Workstream E
measurement, cross-checking the property numbers before filing them
**Status:** `open`

Both the auditor and a pixel-truth pass were run over the same ten renders. On the 1,965 runs both
identified:

| | |
|---|---|
| auditor reports failing, pixel says passing | **22** |
| pixel reports failing, auditor says passing | **0** |

**As a gate it is sound — it never goes falsely green.** Its counts are inflated by roughly 10% on
this surface and five selectors in its output are not defects.

**Two mechanisms, both verified by cropping the render:**

1. **The ancestor-fill loop, on a child that escapes its parent's box.** `backdropsFor` expands
   the `elementsFromPoint` chain with DOM ancestors sitting between consecutive hits — added
   because `elementsFromPoint` skips `thead`/`tbody`/`tr`. Teal's `.bar .val` is
   `position:absolute; top:-24px`, so it paints *above* its bar. The hit chain is
   `[span.val, div.chart, …]`, the loop walks up from `span.val` and finds `.bar` on the way to
   `div.chart`, and attributes the label to the bar's navy gradient: `#18235c on #18235c`,
   **1.00:1**. Cropped, the label is dark navy on white and plainly legible. 12 runs
   (`span.val`, `.bar label`), plus 6 more of the same shape on teal's cover
   (`div.cover-label`, `h1`).

2. **`pointer-events:none` makes an element invisible to hit-testing.** Bold's
   `.mt-gauge-marker` sets it, so `elementsFromPoint` never returns `span.mt-gauge-val` and
   `idx === -1`. The `slice(idx)` guard that deliberately keeps an element's *own* background
   never fires, and `.mt-gauge-val { background: var(--navy) }` is never seen:
   `#ffffff on #ffffff`, **1.00:1**. Cropped, it is white on a navy pill. 4 runs.

**This is the fourth time this resolver has produced a confident wrong reading**, after the
ancestor walk, the `slice(idx+1)` exclusion and the `thead`/`tbody`/`tr` skip — and mechanism 1 is
a *regression introduced by* the fix for the third. Each fix was correct for the case it was
written against and wrong for a case it did not have.

**The fix is to stop hit-testing.** Rendering the page a second time with
`*{color:transparent;-webkit-text-fill-color:transparent}` and sampling the pixel at each text
rect gives the backdrop directly, whatever painted it — no chain, no ancestors, no assumptions
about paint order. It found every failure the walker found and 22 fewer that were not there. It
costs one extra screenshot per document. Its own caveat, stated rather than hidden: blanking text
also blanks anything deriving from `currentColor`, which nothing in these templates does today.

A secondary finding from the same pass: **206 of 2,344 runs straddle two different backdrops**
across their own width. Both tools pick one. Neither is wrong about the pixel it sampled and
neither reports that the run has two.


---

### D-131 — five unreachable copies of the property templates, carrying copy that has now drifted

**Severity:** FRAGILE · **Affects:** nothing that renders — which is the problem ·
**Found during:** D-117's copy fix
**Status:** `open`

`templates/property/<theme>/` holds two files per theme: `<theme>_report.jinja2`, which
`THEME_TEMPLATES` maps to, and `<theme>.jinja2`, which **nothing references**. Checked by
grepping every `.py` and `.jinja2` in the repository for each name: zero hits, no `include`, no
`extends`, no loader path.

They are not stubs. Each is a near-complete copy of the live template, and each carries the same
sentence D-117 was about:

> *The above statistics represent average property details for comparable homes sold within the
> last 12 months…*

Fixing the five live templates left five dead ones still claiming twelve months over a query that
now uses six. Nobody sees it, and that is exactly the hazard: the next person searching for that
sentence finds ten hits, changes some subset, and cannot tell which mattered. D-052's family —
code referenced by nothing — with the added edge that this copy *looks* current.

The structural gate in `test_property_production_render.py` deliberately checks only the five
live templates, because failing on dead files would pressure the next person into editing them
rather than deleting them. `test_no_owner_identity_in_property_report.py` walks all ten, because
that rule is about disclosure and a file that might one day be wired up should not carry an
owner block.

**Delete them, or wire them up and delete the others.** Not both, and not neither.

---

### D-132 — six months of comps has no floor, and the ladder cannot widen time

**Severity:** WRONG · **Affects:** property reports in thin markets; the consumer lead-capture
path most of all · **Found during:** D-117, which created the condition
**Status:** `fixed` — `fix/d118-remove-assessment-row`

Jerry asked what the report does when six months returns too few comps. It currently does nothing
special, and the answer matters more after D-117 than before it.

**What the ladder already absorbs, measured.** The window filter runs *before* the
`len(filtered) >= FALLBACK_MIN` check, so a result thinned by the window escalates the ladder
exactly as one thinned by the sqft filter does. Given twenty listings all outside the window,
**all six levels run** and the response is empty rather than stale
(`test_the_ladder_widens_in_response_to_the_window`).

**What it cannot absorb.** The six levels widen sqft tolerance, bed range, subtype and radius —
radius by 3× at L5. **Not one of them widens time.** So in a market where nothing comparable has
closed in 180 days, the ladder exhausts itself and returns whatever it has, which may be zero.
Before D-117 that market returned four-year-old sales; now it returns none. Both are wrong, and
the new failure is the more visible one.

**Where it lands.** D-119 records what the analysis table does with too few comps: at *n* = 2 the
Low and Medium columns hold the same listing; at *n* = 1 all three do; at *n* = 0
`extract_comp_stats({})` fills the table with zeros. None of those states is guarded, so a thin
market does not produce a thin report — it produces a confident-looking one that is wrong.

**RECOMMENDATION — a seventh ladder level that widens the window to twelve months, and a page
that says which window it used.**

| | |
|---|---|
| **why not "show fewer and say so"** | It is honest, and it makes D-119's degenerate table the common path in thin markets. A CMA whose comparison table shows one listing twice is not a thinner product, it is a broken one. Worth doing *as well*, not *instead* |
| **why not "refuse to generate"** | Worst outcome on the funnel this report reaches. A stranger who typed their address gets nothing, and the agent is not in the loop to notice |
| **why widening works here** | `comps_window` already derives the page's copy from the comps rather than from a constant — that is why it was built that way. A twelve-month fallback can state *"Sales in the past 12 months"* truthfully with **no new copy decision and no new template change**. The machinery is in place |
| **why it matches the ladder** | Every other level widens an axis, records which level was used, and reports it. Time is the one axis the ladder was never given, and there is no principled reason for the exception |

**The months-of-supply parallel Jerry drew, stated precisely.** `describe_moi` does not widen its
window when data is thin; it returns a "no estimate" shape and the page says so. That precedent
supports the *honesty* half — say which window produced these comps — and does not by itself
support widening. The difference is that a market report without months-of-supply still has seven
other metrics, and a CMA without comparables has nothing. So: widen, but only after six months
has genuinely failed, and never silently.

**Concretely, if accepted:** `COMP_FALLBACK_WINDOW_DAYS = 365` as an L6 level entered only when
L5 returns fewer than three; `search_params` in the response already carries
`fallback_level_used`, so the wizard can show the agent which window ran; the page's heading
follows from `comps_window` with no further change.

---

**ACCEPTED AND BUILT, 2026-09-30.**

`COMP_FALLBACK_WINDOW_DAYS = 365`, `COMP_MIN_FOR_ANALYSIS = 3`. The ladder gains a seventh
element — a per-level `window_days` — and `L6:window-12mo` last.

**It is a last resort, not a rung.** The level is skipped entirely unless the best result so far
is under three, so no report carries a year-old comp while a six-month one exists. Being last
also matters on its own: a twelve-month query earlier in the ladder would win on count and mask
a perfectly good six-month result. Both are tested, and the ordering test failed when the level
was moved up.

**The client-side pass widens with it.** `_closed_within_window(filtered, window)` — the
level's own window, not the constant. D-117 established that the vendor filter is never trusted;
leaving the local pass at 180 would have made L6 fetch a year and discard it, which is a
failure mode that looks exactly like the feed ignoring the parameter.

**Grade D with its own reason.** L6 was falling into the same `else` as L5 and reporting *Thin
market*. It now reports *Widened to 12 months — under 3 sales in 6*, because the reason differs
in kind: not that the search went wider in space, but that it went back in time.

**THE PAGE STATES THE WINDOW THAT COVERS ITS COMPS, AND IT IS DERIVED, NOT PLUMBED.**
`PropertyReportBuilder._window_months` reads the oldest `close_date` among the comps and rounds
up to the ladder's own buckets — 6, then 12, then the real figure for anything older. The
alternative was carrying the window from the API response through the wizard, the create
payload, the `property_reports` row and into `report_data`: four hops, each able to drop it, for
a number the data already implies. Deriving it also survives a report being regenerated later or
its comps edited by hand, where a stored window goes stale. Without this the page would say six
months over a twelve-month search — **D-117 again, one level up.**

**A test bug this surfaced, worth recording.** The spy in `test_comp_close_window.py` returned a
fixed list for every ladder level, so no level could ever be seen to gain anything, and the
grading test passed for the wrong reason — the ladder correctly declined to credit L6 for a tie.
The spy now takes a callable and models a feed where a listing appears only if the query's window
reaches it. A mock that cannot distinguish the levels cannot test a ladder.

Five regressions applied and seen to fail: L6 not last, L6 unconditional, the client-side pass
left at six months, the page stating the constant instead of the comps, and absolute dates back
in the fixture.

---

### D-133 — `last_sale_date` and `last_sale_price` are read in one place and written in none

**Severity:** WRONG · **Affects:** the mobile report detail endpoint ·
**Found during:** D-118's investigation
**Status:** `fixed` — `feat/d118-last-sale-from-sitex`

`routes/mobile_reports.py:187-188` builds its `PropertyData` response with:

```python
last_sale_date=property_data.get("last_sale_date"),
last_sale_price=property_data.get("last_sale_price"),
```

`property_data` is the JSON column on `consumer_reports`. The only writer is `tasks.py:2277`,
which builds it from `address`, `city`, `state`, `zip` plus whatever the lead-capture form left
there, and `setdefault`s the same four. **Neither key is ever set**, by that writer or any other
— searched across every `.py`, `.sql`, `.ts` and `.tsx` in the repository.

So the mobile endpoint has always returned `null` for both, and any client rendering a "last
sold for X in Y" line has always rendered it empty.

**Third instance of one family, and the family is D-009's.** `estimated_value` (D-118),
`last_sale_date` and `last_sale_price` are all consumed by code that assumes a producer nobody
wrote. D-118's fallback is the worst version — reading a field nothing writes and *substituting*
the tax assessment — because the substitution makes the absence invisible.

**The general form, for §0.6:** a read of an optional field is indistinguishable from a read of a
field that does not exist. `dict.get()` returns `None` for both, and a `or` fallback turns both
into a plausible value. The check is not "does the code handle a missing value" — it is **"what
writes this, and when"**.

**Do not fix by populating it.** Whether a last-sale figure can be sourced at all is D-118's open
question. This entry exists so that when it is answered, the mobile endpoint is not forgotten —
it is the second consumer, and only the PDF was being looked at.

---

**FIXED 2026-09-30, in the same branch as D-118, which is the point of the paragraph above.**
SiteX carries the sale; the parser now reads it; `lead_pages` and `tasks.py` write both keys into
`property_data`, and the endpoint returns them. `tax_assessed_value` reads both spellings, with
the producer's (`assessed_value`) second so a future rename cannot silently win.

**The D-135 baseline caught the fix before this entry was written** — it failed with *"no longer
orphaned"* on all three, which is the direction a ratchet usually lacks. The mobile surface's
baseline is now empty.

---

### D-134 — the estimated value has no method, and "analysing the comparable ranges" is not one

**Severity:** ROUGH · **Affects:** the subject's value figure on every property report ·
**Found during:** D-118's answer
**Status:** `open` — **[JERRY]**, scope before build

Jerry, 2026-09-29, alongside D-118's last-sale row:

> An **estimated** value is derived by us from the comparable range — a different figure with a
> different label, and clearly ours rather than a recorded fact. Scope it and report before
> building; whatever the method is has to survive a seller asking how it was calculated.

Nothing like this exists today. `stats.price_low` / `price_high` are the min and max of the
comps, `avg_price_per_sqft` is the mean of per-comp ratios, and no code combines them into an
estimate for the subject.

**Why this is filed rather than started.** The method is the deliverable, not the arithmetic. A
seller asking "how did you get this number" must get an answer that is true, short, and the same
every time — which rules out anything tuned per report. It interacts with at least four open
entries: **D-119** (the analysis table drops all but three comps, so "the comparable range" and
"what the page shows" are already different sets), **D-132** (in a thin market the range may rest
on one or two sales), **D-125** (the subject's sqft is a float from SiteX and may be absent), and
**D-118** itself, since an estimate sitting beside a last-sale row needs the two to be visibly
different kinds of number.

**Minimum the ticket must state before any code:** which comps feed it (all returned, or the
three the table shows), whether it is a point or a range, whether it adjusts for the subject's
size, what it does when the inputs are too thin, and the exact sentence printed under it.
Recorded now so the figure is not invented by whoever gets to the template first.

---

### D-135 — the contract gate, generalised: nineteen reads with no producer on one surface

**Severity:** WRONG · **Affects:** the property page's Property Details and Tax blocks in all
five themes; the mobile report endpoint · **Found during:** extending D-113's gate on Jerry's
instruction
**Status:** `open` — the gate is built and baselined; the gaps it found are not fixed

D-113's contract test asked one question — *does everything `market_builder` reads off
`report_data` have a producer?* — and it was scoped to that one (reader, holder, producer)
triple because that is where the first instance was found. Two more turned up within the week,
both outside its reach: `estimated_value` (D-118) and `last_sale_*` (D-133).

Jerry, 2026-09-30: *extend it, and report what it catches — if there's a fourth, that changes
this from a recurring defect to a structural property.*

**It is a fourth and eighteen more.**

| surface | reads | orphans |
|---|---|---|
| `market_builder` ← `report_data` | 17 | **0** |
| `property_builder` ← `sitex_data` | 41 | **19** |
| `mobile_reports` ← `property_data` | 17 | **3** |

**The `sitex_data` nineteen**, measured against the only two things that can produce that blob —
`services/sitex.PropertyData.model_dump()` (28 keys, read off the model rather than guessed from
the route) and the wizard's payload at `step-generate.tsx:104` (25 keys):

```
pool  zoning  garage  fireplace  stories  census_tract  housing_tract  lot_number
page_grid  partial_bath  percent_improved  tax_status  tax_rate_area  total_rooms
num_units  use_code  mailing_address  notes  estimated_value
```

Every one is read by `_build_property_context` or `_build_stats_context`. None is produced by
either path. So the Property Details block renders `Zoning: -`, `Garage: -`, `Fireplace: -`,
`Census Tract: -` on every real report — and two of them do something worse than a dash, which
is **D-137**.

**One of them is produced by neither path but differs between them**, which is its own finding:
`land_value` and `improvement_value` are in SiteX's 28 and *not* in the wizard's 25, so the same
property renders `$337,378` when the worker looked it up and **`$0`** when the wizard supplied
the data. `tax_year` renders `2024` or `-`. Same house, two reports, different numbers,
depending only on which code path created it.

**The `mobile_reports` three** are D-133's two plus `tax_assessed_value` — and that third is a
different species: not *nobody writes it* but *the writer calls it something else*
(`tasks.py` writes `assessed_value`). A near-miss is the one a reader's eye skips over, so the
gate has a test asserting it is reported rather than matched.

**How the gate works, and two things it had to get right.**

*Alias chains.* `comp.get("distance_miles") or comp.get("distance")` is one requirement with two
spellings. Counting them separately reported every alias in the codebase, and a gate whose
output is mostly noise gets skimmed — which is how a real finding gets missed. An `or` chain of
`.get()`s on one holder is now a single group, satisfied if any member is produced.

*Naming every producer.* The first run reported `apn` and `property_type` as orphans on the
mobile surface. Both are written, at `lead_pages.py:302,312`, which was missing from the
producer list. **A gate with an incomplete producer set invents gaps**, and an invented gap
costs the same trust as a missed one.

**Baselined, not xfailed.** A strict xfail per surface says "these are broken" and hides a new
orphan appearing beside them. The baseline is asserted exactly and fails in both directions: a
new gap fails, and a *fixed* gap fails too, because a stale baseline protects nothing. Both
directions were applied and seen to fail, along with a planted D-118-shaped orphan and the
removal of the alias grouping.

**The answer to Jerry's question is yes.** Three instances made it a recurring defect; nineteen
on one surface makes it a property of how this context is assembled — a builder written against
a data source nobody diffed it with.

---

### D-136 — two context builders invent demographics, and nothing renders them yet

**Severity:** FRAGILE · **Affects:** nothing today · **Found during:** D-135's gate
**Status:** `open`

`_build_neighborhood_context` reads `sitex_data["neighborhood"]` and
`_build_area_analysis_context` reads `sitex_data["area_analysis"]`. Neither key exists in either
producer (D-135), so both always take their defaults — and the defaults are **invented figures**:

```python
"female_ratio": neighborhood.get("female_ratio", "51.5"),
"male_ratio":   neighborhood.get("male_ratio",   "48.5"),
"avg_beds":     neighborhood.get("avg_beds",     "3"),
"area_min_radius": area.get("area_min_radius", "0.1 mi"),
```

**Checked before filing, because the severity turns on it:** no live template references
`neighborhood.*` or `area_analysis.*`. Both contexts are built on every render and consumed by
nothing, so **no report has ever printed a fabricated demographic.** This is FRAGILE, not WRONG,
and saying so precisely is the D-113 discipline — an unreachable state is not a live defect.

It is filed because the gun is loaded. The contexts are in `render_html`'s dict under plausible
names, and the first person to put a "Neighborhood" page in a theme wires up
`51.5% female / 48.5% male` for a census tract nobody looked at. Delete both builders, or
source them.

---

### D-137 — the property page asserts "Pool/Spa: No" and "Tax Status: Current" with no data behind either

**Severity:** WRONG · **Affects:** the property page in all five themes, every report ·
**Found during:** D-135's gate, while correcting D-120
**Status:** `fixed` — `fix/d137-absent-is-not-a-default`

```python
"pool":       sitex_data.get("pool") or "No",
"tax_status": sitex_data.get("tax_status") or "Current",
```

Neither key is produced by SiteX's model or the wizard's payload (D-135), so the `or` is not a
fallback — it is the only path, and **every property report ever generated has stated that the
home has no pool and that its taxes are current.**

These are not the same as the eighteen fields that render `-`. A dash says *we don't know*.
`No` and `Current` say *we checked*, in the same type and the same table as the APN and the legal
description, which are real. A seller with a pool sees their report deny it. A stranger who
typed their address into a landing page gets a document asserting their tax standing.

Same `or`-chain family as D-118 — and D-118 is the precedent for the severity, because there the
fallback rendering a *plausible number* is what made the absence invisible. Here it renders a
plausible *fact*.

---

**FIXED 2026-09-30.** Jerry took this before D-121: the readership went from zero to every
consumer report in one merge (D-141), and on that path there is no agent to catch it.

**One convention, one spelling:** `ABSENT = "-"`, matching what `zoning`, `garage` and
`fireplace` already printed, so an unknown field looks the same wherever it appears.

**TWO LAYERS, AND FIXING ONE WOULD HAVE LEFT THE OTHER.** The templates carried their own
assertions — `{{ property.tax_status | default('Current') }}`,
`{{ stats.piq.stories | default('0') }}`, `{{ 'Yes' if comp.pool else 'No' }}`. The construct
lives in Python *and* in Jinja, so both were swept and both are gated. §0.6's *grep for the
construct*, across a language boundary.

**The whole family, found by scanning rather than by memory** — and the first scan was too
narrow. `X.get(k) or "<str>"` missed `X.get(k, "<str>")`, which is where
`comp.get("pool", "No")` was hiding: **every comp card on every report read "Pool: No"**, on a
field no producer writes.

| site | was | now |
|---|---|---|
| `property.pool` | `or "No"` | `or ABSENT` |
| `property.tax_status` | `or "Current"` | `or ABSENT` |
| comp card pool | `comp.get("pool", "No") == "Yes"` | `_tri_state_bool` |
| `stats.*.pools` | `1 if …get("pool") else 0` | `ABSENT` when absent |
| `stats.*.stories` | `_safe_num(…, 0)` | `ABSENT` when absent |
| teal `comp.price_label` fallback | `default('Sale Price')` | `default('Price')` |

**`_tri_state_bool` is the distinction the bug collapsed, and it cuts both ways.** Absent → None.
But **SiteX spells "no pool" as the literal string `"None"`, which is a genuine negative and
stays False.** D-120 got that backwards — it read the string as truthy and reported a pool. A
regression that turns a real negative into an absence is applied and seen to fail, because
over-correcting here would be the same defect wearing the other hat.

**AND THE REPRODUCTION TOOL WAS LYING.** `scripts/render_property_production.py` invented
`zoning`, `pool`, `garage`, `fireplace`, `census_tract`, `total_rooms`, `use_code`, `tax_status`,
`percent_improved`, `secondary_owner` and `mailing_address` — none of which SiteX returns
(D-135). So the fix looked unapplied in its output, because the fixture was still feeding it
`pool: "None"`. **§0.6's rule about fixtures was written from this script's output and then not
applied to this script.** It now asserts its own keys against `PropertyData.model_fields`, and
that assertion is a regression seen to fail.

Rendered on a fixture production can actually produce, the property page now reads
`Pool/Spa: -`, `Tax Status: -`, `Zoning: -`, `Garage: -`, `Census Tract: -` — **the first time
anyone has seen what this page really looks like** — with real figures in Assessed Value, Land
Value, Tax Year, APN, County and Legal.

**Gated:** `apps/worker/tests/test_absent_is_not_a_default.py`, scoped by *holder* rather than by
allow-listing everything else, so its output is entirely findings. A default on a brand colour or
an agent's job title is about us and is not this rule's business; a default on `sitex_data`,
`comp`, `property` or `stats` is a claim about somebody's house and needs a recorded reason or it
fails. Five regressions applied and each seen to fail, including the template layer alone and the
over-correction.

**D-120 closes with it.** Its `stories` half is fixed by the same change, and its correction note
stands: the mechanism first filed was unreachable, and the real defect was worse.

**Found on the way, not fixed:** four themes fall back to `(000) 000-0000`,
`agent@example.com` and `info@example.com` for agent contact details. Placeholder contact data in
client-facing output is B2's family, not this entry's — **filed as D-143**.

---

### D-138 — the consumer lead page's search silently dropped the last-sale fields the day they were added

**Severity:** WRONG · **Affects:** every consumer CMA — the path that reaches a stranger ·
**Found during:** closing D-118's own stated flag
**Status:** `fixed` — `fix/wizard-lookup-contract`

D-118 added three fields to `PropertyData` and taught two wizards to read them. `tsc` passed. The
agent wizard worked. **The consumer wizard did not**, and nothing said so.

`/v1/cma/{agent_code}/search` does not return `PropertyData`. It returns `PropertySearchResult`,
a **hand-copied projection** in `lead_pages.py` that lists fourteen fields by name — and had
none of the three. So:

```
SiteX returns it  →  PropertyData carries it  →  PropertySearchResult drops it
                  →  the wizard reads undefined  →  /request receives nothing
                  →  the report's price row says N/A
```

No exception, no log line, no type error. The frontend declares the fields optional, which is
correct — a property that has never transferred has no sale — so `undefined` is indistinguishable
from *this house has never sold*.

**It is the project's signature failure, on code written the same day the rule about it was
written down.** D-113: a producer silently stopping short of a consumer. D-133: a read nobody
writes. D-135: nineteen of them. This one is a producer that *was* wired, through a projection
nobody thought of as a producer.

**And it landed on the consumer path specifically** — the one that reaches someone who typed
their address into a landing page and has no agent to notice the report is thinner than it should
be. The agent path worked, which is exactly how it would have survived review.

**THIRD TIME THE CONSUMER PATH HAS CARRIED A DEFECT THE AGENT PATH DID NOT** — D-116 (owner
identity), this, and D-139. After three it is a property of the path rather than a coincidence,
and the property is in its construction: **the agent path hands `PropertyData` almost straight
through, while the consumer path retypes the shape three times** — a hand-copied projection, a
request payload, and a dict literal in the worker. Every retyping is a place to forget a field,
none of them errors when it does, and the path has no agent in the loop to notice the report
came out thin. Any future work on this funnel should assume it drops things until measured.

**Fixed:** `PropertySearchResult` gains the three fields and `lot_size`, which was missing for the
same reason and which `ReportRequestPayload` had been accepting from nobody.

**Gated, at the boundary that actually broke.**
`apps/api/tests/test_property_lookup_contract.py` asserts, in both languages:

| | |
|---|---|
| the fields survive `PropertySearchResponse` | the agent path |
| `PropertySearchResult` carries them | the path that broke |
| `ReportRequestPayload` accepts everything the search can return | the next hop, same failure one step later |
| the `.tsx` spells them identically | **a rename typechecks and sends `undefined`** |
| the consumer wizard *sends* them, not just reads them | reading is not forwarding |
| the hand-copied projection carries no name | D-116, at the one place the shape is retyped |

Five regressions applied and each seen to fail, including the original bug and a camelCase
rename in the `.tsx`.

**A second finding, filed here rather than separately: `last_sale_document` was parsed and
displayed nowhere.** It was added on the reasoning that a recorder's document number is the only
field letting a figure be checked against the county record. Nothing displayed it and nothing
asked for it. **A parsed field with no consumer is D-135's mirror** — the same debt as a read with
no producer, accruing the same way, by looking deliberate. Removed. The probe recorded the key
name, `raw_response` still holds the value, and it is one line to add back on the day something
wants it. `test_every_last_sale_field_on_the_model_reaches_a_consumer` now fails in **both**
directions for this family.

---

### D-139 — nine more fields missing from every consumer report, in three separate places

**Severity:** WRONG · **Affects:** every CMA delivered through the landing-page funnel ·
**Found during:** Jerry's follow-up to D-138 — *"you fixed the one you tripped over; the gate you
just built can answer the general question in one run"*
**Status:** `fixed` — `fix/cma-projection-gaps`

It could, and the answer is nine.

D-138 fixed three fields. `lot_size` had been missing the same way for longer, which said the
projection had been dropping things for a while and nothing noticed. Rendering both paths'
property pages from one fully-populated SiteX lookup and diffing them:

| field | agent report | consumer report |
|---|---|---|
| `county` | LOS ANGELES | *(blank)* |
| `apn` | 8381-021-001 | *(blank)* |
| `legal_description` | LOT 44 TR#6654 | *(blank)* |
| `property_type` | Single Family Residential | *(blank)* |
| `assessed_value` | $428,248 | **$0** |
| `land_value` | $337,378 | **$0** |
| `improvement_value` | $90,870 | **$0** |
| `tax_amount` | $5,198 | **$0** |
| `tax_year` | 2024 | – |

**The consumer report's entire Parcel & Legal block rendered blank and its entire Tax &
Assessment block rendered `$0`** — and `$0` is a number, not a gap, so it reads as an assessed
value of nothing rather than as data we do not have. On every consumer report ever generated.

**THREE SEPARATE PLACES DROP FIELDS ON ONE PATH, and only the third costs nothing.**

1. **`PropertySearchResult`** — the hand-copied projection. D-138's culprit, and it was missing
   the whole parcel and tax family too.
2. **`ReportRequestPayload`** — the next hop. A field the search returns and the request rejects
   is dropped one step later and looks identical from the report.
3. **`tasks.py`'s consumer branch** — builds its own `report_data` and its own `sitex_data`
   literal. `apn`, `county`, `legal_description` and `property_type` were **already stored on
   `consumer_reports.property_data`** and simply never forwarded. This one was free to fix and
   hid the longest, because every model in the chain agreed.

`"assessed_value": 0` was a hardcoded literal in that third place.

**Gated at two levels, deliberately.**

* `test_property_lookup_contract.py` diffs `PropertyData` against the projection, with a
  `CONSUMER_EXCLUDED` list that names a reason per field and a staleness test. Cheap; catches a
  field added to the model and forgotten.
* `apps/worker/tests/test_consumer_and_agent_reports_agree.py` builds both `report_data` dicts
  the way the two producers build them, runs the **real builder**, and requires the property
  contexts to match. This is what answers the general question permanently: it measures what a
  reader sees, so it survives a rename, a new block, or a **fourth** place that drops things —
  which the model diff cannot, and which is exactly how place 3 stayed hidden.

**A guard that caught its own fixture.** `test_every_field_that_should_travel_is_populated`
failed on its first run: six fields were blank in the fixture, so the parity test would have
compared two absences and passed. Five of the six are deliberate (identity, plumbing), and the
test now names them. §0.6's coincidence rule, one day old, catching the author of the rule.

**Not carried, each for a stated reason:** `owner_name` and `secondary_owner` (D-116 — and the
consumer path is the one that made that urgent), `fips` (a re-query key, never rendered),
`full_address` (derived), `unit_number`/`unit_type` (not reachable from the consumer address
search), `source`/`confidence`/`raw_response` (plumbing). Widening this path is exactly when an
owner name gets added back by reflex, so both gates assert its absence.

Four regressions applied and each seen to fail: a field dropped from the projection, the worker
ceasing to forward a stored field, the hardcoded `0` returning, and an owner name reappearing.

**EXISTING CONSUMER REPORTS ARE NOT BACKFILLED, and probably should not be.** The nine fields
were never *stored* on the old rows — `lead_pages` did not accept them, so
`consumer_reports.property_data` has no record of them. Regenerating an old report therefore
recovers nothing; it re-renders the same thin data. Filling them in would mean re-running SiteX
for historical rows, which is a paid lookup per row against addresses whose reports have already
been delivered, to improve a document nobody is going to read again. Recorded as a decision
rather than an omission: **new reports are correct from this change forward, old ones stay as
they were sent.**

---

### D-140 — the gate for D-139's worst site mirrored the code instead of importing it

**Severity:** FRAGILE · **Affects:** `test_consumer_and_agent_reports_agree.py`, and therefore
everything it was written to protect · **Found during:** D-139, flagged in its own PR
**Status:** `fixed` — `refactor/consumer-report-data-shared`

D-139's third and worst site was a `report_data` **dict literal** ~350 lines inside a Celery
task: fields already stored on `consumer_reports.property_data` and never forwarded. The gate
written to catch it could not import a literal, so it **restated** it.

A gate that goes quiet when somebody edits the thing it guards is worse than no gate, **because
it reports green.** D-139's own regression run only failed because both copies were changed by
hand — which is not a property a gate can rely on.

**Extracted:** `worker/consumer_report_data.build_consumer_report_data`. The task calls it; the
gate imports it. A field dropped from the one definition now fails the gate by construction.

**The DB access was not woven through the literal**, which is why this stayed the size of one
ticket. Every input was a local the task already held — `property_data` fetched above, the brand
row unpacked above, the comparables computed above. Nothing had to move; the function is pure and
its arguments are keyword-only, so a mis-ordering is impossible.

**Fifteen flat parameters, deliberately.** Grouping them into `brand` and `agent` dicts at the
call site would read better and would hand the caller two more shapes to assemble by hand —
which is the defect this path has now produced three times.

**PROVEN EQUIVALENT, not assumed.** The pre-refactor literal was extracted from
`git show HEAD:…tasks.py` into a callable and run against the new function on **300 randomised
inputs** — every key distinct per trial so two fields cannot agree by coincidence, and every
third trial dropping random keys to exercise each `.get` default. 300/300 identical.

**AND THE EXTRACTION IMMEDIATELY FOUND A HOLE IN THE GATE.** With the consumer side coming from
the real builder, four fields diverged: `property_address`, `property_city`, `property_state`,
`property_zip`. They are top-level columns on `property_reports`, not part of `sitex_data`, and
the *agent* fixture had never supplied them. The mirrored consumer fixture had not either, so
**the parity test had been comparing two blanks and passing.**

That is the coincidence rule again, and the fixture guard written for it missed this because it
checked `LOOKUP` — the *source* — and these four never travel through `LOOKUP` at all.
`test_neither_path_s_property_page_is_blank_where_they_agree` now asserts non-emptiness on the
rendered context, which is one level below where the first guard was looking.

**A second thing the refactor broke, and it should have.** `test_agent_title_default` asserted
`"Real Estate Agent"` appears in **`tasks.py`**, by filename. Moving the default to another
module changed nothing about the default and failed the test. A guard pinned to a file path
fails on a move and passes on a deletion elsewhere; it now searches every module under
`src/worker/` for the default and asserts one supplies it. §0.6's accidental-selector rule with
a filename as the selector — and `docs/TEST_DURABILITY.md`'s point exactly.

Four regressions applied and each seen to fail, the first being the one that was impossible
before: **dropping a field from the production builder alone**, with no edit to the test.

---

### D-141 — the consumer CMA has no Area Sales Analysis, and nothing decided that

**Severity:** WRONG · **Affects:** every CMA delivered through the landing-page funnel ·
**Found during:** D-140's extraction, which put the page set somewhere it could be read ·
**Status:** `fixed` — `docs/d141-consumer-page-set`

`CONSUMER_PAGES` is not the agent default. It drops `contents` and **`analysis`**, and adds
`market_trends` and `overview`.

---

**1 · Was it decided, or did it accrete?**

**It accreted.** `git log -S` on every distinguishing string — `"selected_pages"`,
`market_trends", "overview` — in `tasks.py` returns exactly two commits: D-140's extraction
yesterday, and **`4bcb3d2`**. That is commit **182 of 182**, the squashed base, dated 2026-05-18,
and its message is entirely about *"show 1 row of cards on Market Snapshot page 1"* — nine
paragraphs about `.force-new-page` and gallery rows, with no mention of the consumer CMA or its
pages.

Same method and same answer as the `[:4]` slice: **traces to the squashed base with no recorded
intent.** Nobody chose this; it arrived.

---

**2 · What the consumer report actually lacks.** Both paths rendered from one identical SiteX
lookup and four identical comps:

| | agent | consumer |
|---|---|---|
| `<section>` elements | **7** | **5** |
| rendered page titles | Property Information · **Area Sales Analysis** · Sales Comparables · Range of Sales | Property Information · Sales Comparables · Range of Sales |
| the comps comparison table | ✓ | **✗** |
| the sales chart | ✓ | **✗** |
| **the last-sale figure ($369,000 · Dec 2015)** | ✓ | **✗** |

**Nothing else carries it.** Sales Comparables shows four cards — four *other* houses' prices.
Range of Sales shows `$470k – $635k` and four averages. **Neither ever places the subject
property against the comps.** The Subject column, the price-per-sqft comparison and the sale
price row all live on the page that is missing, so a homeowner who asked what their house is
worth receives a document showing four neighbours' sale prices and a band, and nothing that says
*and here is yours*.

It also means **D-118's fix does not reach this path at all.** The last-sale figure was wired
through the projection, the payload, the row and the builder (D-138, D-139, D-140) — and then
lands on a page the consumer report does not print.

*A false positive worth recording:* grepping the HTML for `"AREA SALES ANALYSIS"` returns a hit
on the consumer render. It is inside a `<style>` block — a CSS selector name, not content. The
`<section>` count and the rendered `section-title` list are the honest measures. §0.6's substring
rule, caught during this investigation rather than after it.

---

**3 · Are `market_trends` and `overview` better for that reader?**

**They are both conditional, and the page they replaced is not.** Measured:

| supplied | sections | pages |
|---|---|---|
| nothing | **5** | Property Information · Sales Comparables · Range of Sales |
| `market_trends_data` | 6 | + Market Trends |
| both | 7 | + Property Overview |

`market_trends` needs a live SimplyRETS fetch and `overview` needs an OpenAI key; `render_html`
silently drops either when its data does not arrive. So the consumer report traded **one page
that always renders** for **two that may not** — and in an environment without both services it
is a five-page document.

On the merits the two additions are defensible for that reader: a market gauge and a plain-English
summary suit a homeowner better than a specification table. **But they are additions, and the
analysis page was not theirs to displace.** Nothing about including them required excluding it.

---

**VERDICT: a defect, and the fifth way the consumer path is thinner than the agent one** —
after D-116 (owner identity), D-138 (last-sale fields), D-139 (nine parcel and tax fields) and
D-140 (the gate that could not see any of it).

**Recommendation, not built:** add `analysis` back to `CONSUMER_PAGES`, keeping `market_trends`
and `overview`. It is a one-line change to a now-shared constant and it restores the table the
document exists to provide. Two things to weigh first: whether `contents` should return as well
(it is unguarded and mis-numbered — D-121 — so adding it before that is fixed would ship a
contents page listing pages this set does not contain), and that the consumer report would then
be eight pages rather than five.

*Incidentally visible in the render:* the consumer report's footers read `04` then `07` on
consecutive pages. That is D-121's hardcoded numbering, wrong here for the same reason it is
wrong everywhere, and more obviously so on a path whose page set differs.

---

**FIXED 2026-09-30.** Jerry: add `analysis` back, keep `market_trends` and `overview`, leave
`contents` out until D-121.

```python
CONSUMER_PAGES = ["cover", "aerial", "property", "analysis",
                  "comparables", "range", "market_trends", "overview"]
```

**Verified by the thing that matters, not by the page appearing.** Three PRs of plumbing
(D-138, D-139, D-140) landed or did not land on this one line, and *the page renders* is not
*the figure is on it*. Rendered:

```
Sale Price   $369,000 · Dec 2015   $470,000   $631,500   $635,000
```

— in the consumer report, in the analysis table, in the price row, identical to the agent's. A
test asserts the value in the row in the table, and a second asserts the two paths render the
**same** table cell for cell, because a consumer table built from a thinner context would pass
the first and still differ.

**PAGE COUNT: five → eight.** What a stranger receives changes materially. Precisely: **six**
pages when neither external service answers, seven with market trends, **eight** with both. The
consumer report was four-to-six before. `analysis` is the only one of the three that renders
unconditionally.

**`contents` STAYS OUT UNTIL D-121 IS FIXED — AND THEN COMES BACK HERE.** Its block is
hardcoded and unguarded, so adding it now ships a contents page listing pages this set does not
contain, numbered wrongly. **When D-121 lands, add `contents` to `CONSUMER_PAGES`.** The
reminder is on this entry, in the constant's own comment, and in
`test_contents_stays_out_until_d121`.

**The silent-conditional trade is filed separately as D-142**, because "the page is absent" and
"the page failed" being indistinguishable is a defect in its own right, not a footnote to this
one.

**Two of my own tests were passing by coincidence, again.** Both fixtures had `comparables=[]`,
so the analysis table's comp columns were `$0` on both sides and
`test_both_paths_render_the_same_analysis_table` would have compared two rows of zeros. And the
page-count test asserted on `builder.page_set`, which `render_html` never updates — it prunes a
local copy — so it reported eight pages for a six-page document, **measuring the intent instead
of the output, which is the error this whole defect is made of.** Both fixed; counted from the
render now.

Four regressions applied and each seen to fail: removing `analysis` again, adding `contents`
early, the last-sale figure ceasing to reach this path, and a page dropped from the set.

---

### D-142 — a page that fails to load and a page that was never asked for look identical

**Severity:** FRAGILE · **Affects:** the consumer CMA's `market_trends` and `overview` pages;
the agent report's too where selected · **Found during:** D-141
**Status:** `open`

`render_html` builds `market_trends` from a live SimplyRETS fetch and `overview` from an OpenAI
call. When either returns nothing it removes the page from the set and logs at `info`:

```python
if market_trends_data is None and "market_trends" in page_set:
    page_set = [p for p in page_set if p != "market_trends"]
    logger.info("market_trends: page REMOVED from page_set (no data returned)")
```

The document then renders one page shorter, with nothing in it saying so. **A report missing its
market-trends page because SimplyRETS was down is byte-for-byte the same document as one whose
page set never included it.** Measured on the consumer path: six sections with neither service,
seven with trends, eight with both.

**Why this is its own entry.** The removal is the right *behaviour* — a half-rendered gauge is
worse than no gauge, and D-108 settled that a report should say what it could not find rather
than print zeros. What is missing is the saying. There is no signal at any level:

| who | what they see |
|---|---|
| the recipient | a shorter document, no explanation |
| the agent | nothing — no flag on the report row |
| us | one `info` line per render, in a log nobody reads per-report |

**It is the D-113 family with the arrow reversed.** There, a consumer read a key no producer
wrote. Here a producer fails and the consumer silently narrows. Both are invisible from both
ends; both were found only by counting what came out.

**What it would take.** The page set that was *requested* and the set that *rendered* are both
in hand at the end of `render_html` — the difference is computable in one line. Somewhere to put
it is the open question: a `pages_dropped` column on the report row (visible to the agent, and
to us in aggregate), a line in the document itself, or both. The aggregate is the more valuable
half: **"market trends failed on 40% of consumer reports last week" is a number nobody can
currently produce.**

Not fixed here. D-141 restored the page this defect was hiding behind; this is the general case.

---

### D-143 — the property report falls back to a placeholder phone number and email

**Severity:** ROUGH · **Affects:** the agent contact block, four themes ·
**Found during:** D-137's scan, which reported them and then excluded them as out of scope
**Status:** `open`

```jinja
{{ agent.phone | default('(000) 000-0000') }}
{{ agent.email | default('agent@example.com') }}
{{ agent.email | default('info@example.com') }}
```

An agent with no phone number on file gets `(000) 000-0000` printed on a client-facing document,
and `agent@example.com` beside it. Unlike D-137's defaults these are not *wrong claims about the
property* — they are placeholders reaching a customer, which is **B2's family** (`Footer Logo`
rendering as literal text).

Out of D-137's scope on purpose: that entry is about a default that asserts a fact, and its gate
is scoped to property holders so its output stays entirely findings. This is a different rule —
*no placeholder may render* — and it wants its own sweep across both surfaces, which is B2's.

`agent.phone` and `agent.email` are produced by `fetch_report_with_joins` from the `users` row,
so the fallback fires only when the column is empty. How often that is, is unmeasured.

---

### D-144 — a closed comp's "sale price" is its list price — and the reason filed here was wrong

**Severity:** WRONG · **Affects:** the comparables cards and the analysis table, every property
report · **Found during:** the 2026-09-30 probe, splitting D-118's verdict
**Status:** `fixed` — `feat/d144-size-the-close-price-gap`. **The symptom was real. The cause
recorded below was not, and the sizing that was asked for before any fix is what caught it.**

> **CORRECTION, 2026-09-30, before anything was relabelled.** The ticket said to size this with
> a count against a real market first, because "if no closed listing on this feed carries a sale
> price, the comps table can never show sale prices and that's a product fact, not a bug." The
> count came back the other way. `tmp/market_snapshot_downey.json` — a real capture of a real
> market, 134 listings, 31 of them Closed — reports a **median close price of $810,000** across
> those 31, and computes escrow days for **31 of 31**, which needs `closeDate` and `contractDate`
> on every one. The feed carries the sale price. **Our code reads it from a path the feed does
> not use** — see **D-145**. The probe's "0 of 20" measured our own reach.
>
> So the decision the ticket set up — relabel the column *List Price*, or show the list price and
> state the distinction — **does not arise.** Neither option was taken and the column keeps its
> name, because the number under it is now the sale price. That is the recommendation: the
> cheapest correct change to a mislabelled column was to stop mislabelling the data.
>
> Three of the five closed rows in the capture sold for something **other** than their asking
> price ($1,059,000 → $1,100,000; $1,199,000 → $1,140,000). This was never only a labelling
> problem; it was a different number.

The probe measured `closePrice` present on **0 of 20** closed listings and `closeDate` on
**0 of 20**. `_extract_price` falls back to `listPrice`, so on this feed **every closed comp's
price is what the seller asked, printed in a column headed *Sale Price*.**

**This is not D-117's problem and the D-118 work does not cover it.** `comps_window.price_row`
distinguishes a set of *active* comps from a set of *closed* ones and labels the column
accordingly — correct, and no help here, because these comps **are** closed. Their status says
Closed, their date says Closed, and their price is a list price with nothing marking it as one.
A label derived from status cannot catch a value that disagrees with its own status.

**Three things it could be, and they need settling in this order:**

1. **A vendor/feed question.** `closePrice` is a standard RESO field. 0/20 may mean this feed
   does not license it, or that the probe's 20 rows came from a source that does not populate
   it. **Twenty rows from one query is not the whole feed** — the next credential trip should
   count it across statuses and postcodes before anyone concludes it is absent everywhere.
2. **If it is genuinely absent:** the honest rendering is to label the column *List Price* for
   closed comps too, and say so — the same move D-118 made for the subject's row, for the same
   reason.
3. **Only then:** whether a CMA built on asking prices rather than sale prices is a CMA. That
   is Jerry's, not engineering's.

**The three questions above, answered.** (1) is settled: the field is present, and the 0/20 was
a reading error. (2) does not arise. (3) does not arise — the CMA is built on sale prices, as it
was always meant to be.

**What the original entry got right, and why it still counted.** "A label derived from status
cannot catch a value that disagrees with its own status" was correct and is the reason this was
filed at all. Had the ticket said *relabel it* rather than *size it first*, the column would now
read "List Price" over a column of sale prices — a second wrong label, shipped on the strength
of a number nobody checked the provenance of.

---

### D-145 — `closePrice` and `closeDate` are read at the top level, where the feed never puts them

**Severity:** BROKEN · **Affects:** every comparable in every property report, both deployments;
and the six-month comp window, which was a no-op · **Found during:** sizing D-144
**Status:** `fixed` — `feat/d144-size-the-close-price-gap`

A SimplyRETS row nests the sale under `sales`: `row["sales"]["closePrice"]`,
`row["sales"]["closeDate"]`, `row["sales"]["contractDate"]`. Five production reads went to the
top level or to `mls`, so all five saw `None`:

| site | field | what it did |
|---|---|---|
| `apps/api/routes/property.py:797` | `closePrice` | fell through to `listPrice` — the agent comps table |
| `apps/api/routes/property.py:799,811` | `closePrice`, `closeDate` | `close_price` and `close_date` always null |
| `apps/worker/tasks.py:2383,2385,2397` | both | the same three, consumer path |
| `apps/api/services/simplyrets.py:181,182,192` | both | the same three again |
| `apps/api/schemas/property.py:214,226` | both | `sale_price` fell to `listPrice`, `sold_date` fell to **`listDate`** |

**The window filter is the serious one.** `_closed_within_window` read
`(lst["mls"] or {})["closeDate"] or lst["closeDate"]` — two paths the feed does not use — and
keeps a listing with no close date **on purpose**, because an Active listing has not closed. So
every closed listing looked date-less, every one was kept, and the filter was a no-op. Its own
docstring says *"THE CLIENT-SIDE PASS IS NOT BELT AND BRACES, IT IS THE ACTUAL GUARANTEE."* The
guarantee was void from the day it was written, and D-117's derived subtitle has been promising
a six-month window that nothing in our code enforced. Only `minclosedate` did — the vendor
parameter the client-side pass exists precisely in order not to depend on.

**THE TESTS AGREED WITH THE CODE AND BOTH DISAGREED WITH THE FEED.** Every fixture in
`test_comp_close_window.py` was built as `{"mls": {"closeDate": …}}`, and one test,
`test_the_close_date_is_read_from_both_shapes_the_feed_uses`, asserted that a top-level
`closeDate` and an `mls.closeDate` must *both* be honoured — reasoning by analogy from D-105,
where `daysOnMarket` really does live under `mls`. Neither path exists on a closed row. That
test has been inverted: a date at either invented path now means a listing whose close date we
did not find, and the fixtures are checked against
`tests/fixtures/listing_closed_minimal.json`, which is captured rather than written.

This is §0.6's coincidence class in its purest form — **two wrong paths agreeing is not a
test**. `compute/extract.py` has read `sales.closePrice` correctly since it was written, so the
repo held both the right path and the wrong one, and the wrong one was in the four files that
build what a reader sees.

> **THE NESTED-PATH FAMILY IS NOW AT FOUR, AND THE FOURTH WAS FOUND BY THE INSTRUMENT REPEATING
> THE ERROR IT WAS WRITTEN TO DETECT.**
>
> | | field | read as | lives at |
> |---|---|---|---|
> | 1 | `closeDate` | top level | `sales.closeDate` |
> | 2 | `daysOnMarket` (D-105) | top level | `mls.daysOnMarket` |
> | 3 | `bathrooms` (D-106) | `property.bathrooms` | `bathsFull` / `bathsHalf` |
> | 4 | `closePrice` (D-145) | top level | `sales.closePrice` |
>
> The probe exists to catch exactly this, and section 3b counted
> `r["closePrice"]` — the same top-level guess the production code makes. So the probe's answer
> **confirmed the code's mistake instead of catching it**, and "0 of 20" read as a fact about
> the feed. An instrument that shares the assumption it is testing returns agreement, not
> evidence. 3b now counts every location separately and prints where each field was found.
>
> `scripts/sweep_extract_field_paths.py` is the general answer to this family, and it is only as
> good as the payloads it checks against — two bundled fixtures, where a key absent from both is
> *unproven* rather than wrong. Its `--capture` argument is what turns that into a real sample,
> and the reason it had never been used is **D-150**: the only capture on disk is a snapshot
> with its rows stripped. Both halves are now ready and neither has met production.

**The guard.** `apps/api/tests/test_close_price_field_path.py` walks the AST of all four files
and fails on any read of `closePrice`/`closeDate`/`contractDate` off anything that is not the
`sales` object. Source-level and not behavioural because two of the four build their dict inline
inside a 350-line route with nothing importable to call — the same wall D-140 hit. Three of the
nine tests in that file were each seen to fail against a reverted line.

**Also removed: `sold_date` falling back to `listDate`.** A comp that has not sold has no sold
date, and `""` is the honest answer. Same rule as D-137, one field over.

**Noted, not filed.** `normalize_comparable` / `normalize_comparables` in
`apps/api/schemas/property.py` are exported and have **no production caller** — D-135's family.
Fixed here rather than deleted because deleting an exported helper is a separate decision.

**WHAT THE NOW-REAL WINDOW COSTS — measured 2026-09-30, `feat/measure-the-window-cost`.**

The open question on merge was that the filter had never actually filtered, so nobody knew what
enforcing it would drop. Three parts, and only the third is unanswered.

1. **On `status=Closed` — the only closed path the wizard reaches — the window was never off.**
   `minclosedate` is sent on every closed ladder level, and D-074 confirmed in production that
   it filters correctly: **60,874 closings in 90 days against 962,517 unfiltered.** The vendor
   was enforcing the window server-side the whole time. What was void was the **backstop**, not
   the window. The expected client-side drop on this path is near zero, and a large one would
   mean the vendor filter is not what D-074 measured.

2. **On `status=All`, the fix is not a backstop — it is the whole mechanism.** `minclosedate`
   is sent only when the resolved status is `Closed` (property.py:642), correctly, since the
   vendor applies it to the whole response and would drop the active half. But
   `_closed_within_window` runs on **every** level regardless of status (property.py:742). So
   an `All` search has no vendor window at all, and until this week it had no client one either.
   That path now drops out-of-window sales for the first time. Not reachable from the wizard
   (property-wizard.tsx:53 sends Active or Closed); reachable from the endpoint. Asserted in
   `test_an_all_status_search_has_no_vendor_window_so_the_client_pass_is_the_only_one`.

3. **The per-subject comp count cannot be measured from anything on disk** — see **D-150**. The
   Downey capture bounds it from above only: **31 closings in 30 days, all carrying
   `sales.closeDate`**, so roughly 186 city-wide inside six months against a floor of
   `COMP_MIN_FOR_ANALYSIS = 3`. That is a ceiling, not the answer — one address's comps are what
   survives radius, sqft band, beds and subtype.

**PART 3 ANSWERS ITSELF FROM THIS DEPLOY, AND THAT IS THE BETTER MEASUREMENT.** property.py:743
logs `"Comps %s: close-date window dropped %d of %d client-side (minclosedate was sent: %s)"`
whenever the count changes. **That line has never fired in the life of the repository**, because
the count never changed — the filter dropped nothing, always. From this deploy it is the real
number, per request, per ladder level, across every market and subject that actually gets a
report.

**So do not construct a thin market to test against.** A synthetic population answers the
question I would have designed it to answer; real traffic answers the one that exists. **Check
the log after a week**, and read it as: a near-zero drop on `status=Closed` confirms D-074's
finding that the vendor filter is exact, and anything larger means it is not. A raw capture of
a genuinely thin market (D-150's `--raw-out`) is still worth having, but as a second opinion
rather than the primary source it would have been.

**And D-132's seventh level had never run against a real window.** Every ladder test predating
this was written while the filter was a no-op, so L6 was only ever exercised by the sqft, bed
and subtype filters — not by time, which is the only reason L6 exists. Four tests now cover it,
three of which fail against the pre-fix read: a vendor that honours `minclosedate` and returns
more at twelve months than at six; a vendor that **ignores** it, where the client pass is what
escalates the ladder and L6's wider window is what legitimately readmits the sales; the
converse, that nothing older leaks when six months suffices; and the `All` path above.

One of those four was written wrong first and the failure was worth more than the test: three
in-window comps clears `COMP_MIN_FOR_ANALYSIS` (3) but not `FALLBACK_MIN` (5), so the ladder
runs all six space-widening levels and skips only the time-widening one. Two thresholds, easy to
misremember as one.

---

### D-146 — the two deployments disagreed on whether a closed comp shows its sale price or its asking price

**Severity:** WRONG · **Affects:** agent reports vs consumer reports on the same address
· **Found during:** sizing D-144
**Status:** `fixed` — `feat/d144-size-the-close-price-gap`

```
apps/api/routes/property.py:797   "price": listing.get("listPrice") or listing.get("closePrice")   # agent: LIST first
apps/worker/tasks.py:2383         "price": listing.get("closePrice") or listing.get("listPrice")   # consumer: CLOSE first
```

Opposite precedence, in two hand-copied literals, under a comment in the worker that says
*"Normalize into EXACT same dict format as the working API endpoint."* The sixth agent/consumer
divergence, and the first where the **consumer** side was the correct one.

**It was invisible, and D-145 is why.** While `closePrice` read as `None` on both paths, the two
expressions returned the same value for every input in existence. A divergence that cannot be
observed is still a divergence — it was one field-path fix away from becoming two different
numbers on two reports for the same house. Unified on close-price-first, which is correct for a
closed comp: what it sold for, not what it asked.

Covered by `test_a_closed_comp_reports_what_it_sold_for`, which drives the real route with a
listing that sold for **more** than its asking price, so a fallback shows up as a wrong number
rather than as a coincidence — and by `test_an_active_comp_still_reports_its_asking_price`, so
the fix cannot pass by always reading `sales`.

---

### D-147 — `apps/api` did not parse on the Python version the release gate pins

**Severity:** BROKEN · **Affects:** the entire API test suite, and any 3.11 deployment
· **Found during:** trying to run the comps tests
**Status:** `fixed` — `feat/d144-size-the-close-price-gap`

`services/email.py` had `\u2019` inside the *expression* part of an f-string. That is a
`SyntaxError` before Python 3.12 and legal from 3.12 on. `api/main.py` imports
`routes/reports.py` imports `services/email.py`, so **`from api.main import app` raised
`SyntaxError` and every test module that imports the app was uncollectable.**

`backend-tests.yml` runs on **3.12** and was green. `release-check.yml` pins **3.11** — and is
`workflow_dispatch` only, so nobody had ever run it. The gate that would have caught this is the
one that never runs, and the gate that runs cannot see it.

`apps/api/tests/test_sources_parse.py` compiles every file under `apps/api/src`,
`apps/worker/src`, `scripts` and `tools` on whichever interpreter is executing. It takes
milliseconds, holds no opinion about which Python version is right, and fails on the one whose
opinion matters at that moment. Seen to fail against the reverted line.

> **CORRECTION, 2026-09-30 — this was already known, and the entry above overstated the
> discovery.** `backend-tests.yml` carries a comment naming `services/email.py:729` and the
> exact PEP 701 rule, and pins 3.12 *because of it*. It also records that there is no
> `requirements.txt` and that the old install step failed before running a test. So the syntax
> error was documented and worked around; what nobody had done was fix the source. The fix
> stands and the compile guard is new, but "found by trying to run the comps tests" describes
> how **I** met it, not when the project did. `backend-tests.yml`'s comment has been updated,
> since its stated reason for the 3.12 pin no longer holds — the pin stays, because CI should
> run what production runs.
>
> **Sizing, as asked: what would `release-check.yml` have caught? Nothing. It would have caught
> itself.** The GitHub Actions API reports **0 runs, ever**. Both of its blockers are in its own
> configuration, not in the code it would test:
>
> 1. `pip install -r requirements.txt` — **that file has never existed in this repository.**
>    `apps/api` and `apps/worker` are Poetry projects. It dies at the install step.
> 2. Had that been fixed, on 3.11 it would have died at `from api.main import app` — on the
>    error above, which `backend-tests.yml` had already routed around.
>
> Its value to date is zero and its cost is not: it duplicates `backend-tests.yml`'s job with a
> manifest that does not exist and an interpreter production does not use, while appearing in
> the workflow list as a release gate. **Recommendation: delete it.** A `workflow_dispatch`
> alias for `backend-tests.yml` would be the alternative if a manual pre-release button is
> wanted. Not done here — removing a workflow that says "Release Check" is a call to make
> deliberately, not as a side effect of a comps fix.
>
> **Done, 2026-09-30: see D-151.**

---

### D-148 — two welcome emails printed the literal text `{company}`

**Severity:** WRONG · **Affects:** every title rep who accepted an invite · **Found during:**
fixing D-147, in the same three lines
**Status:** `fixed` — `feat/d144-size-the-close-price-gap`

`send_rep_welcome_email` builds its body as an f-string whose `{_step_row(...)}` calls take plain
string literals as arguments. A `{company}` inside one of those literals is not in the outer
f-string's expression scope — it is ordinary text. So the email told reps their agents' reports
would carry "**{company}**'s branding", twice.

Found because the illegal escape sequence that caused D-147 was on the same three lines; reading
them to fix the syntax is what surfaced the braces. `send_company_admin_welcome_email` has the
same shape and was checked — its step rows carry no placeholder.

`test_welcome_email_interpolates.py` asserts on the **rendered HTML**, not the source, because
the defect is that a brace reached the reader. Both branches are tested: a company name set, and
the `"your company"` fallback — a placeholder defect that only shows with a value set is half
tested. Seen to fail against the reverted line.

---

### D-149 — the close-to-list ratio reads 135.2% on a real market

**Severity:** WRONG · **Affects:** market reports and the AI narrative, which quotes the figure
in a sentence · **Found during:** reading the Downey capture for D-144's sizing
**Status:** `open`

`tmp/market_snapshot_downey.json` reports `close_to_list_ratio: 135.2` over 31 closed listings.
A market where homes sell for 35% over asking is not what that number is describing.

The computation is an **unweighted mean of per-listing ratios** — `avg(close/list*100)` — and it
is the same shape in the product, not only in the capture tool:
`compute/extract.py:117` → `compute/calc.py:39`, and again at `report_builders.py:170,697`. So
this figure ships.

**What is known and what is not.** The five closed rows in the capture's sample average ≈99.8%,
so the outlier is among the other 26 and the capture does not carry them. The cause is therefore
**not established** — an unweighted mean has no defence against one bad row, and a plausible bad
row is visible in the same sample: a listing at `list_price: 3200`, `close_price: 3200`, which
is a **rent**, counted as a closed sale. That would also be polluting `median_close_price` and
`avg_ppsf`.

**Needs, in order:** (1) a capture that keeps every closed row rather than five, so the outlier
can be named; (2) a decision on whether a mean or a median is the right statistic here; (3)
whether lease listings belong in a sale-price aggregate at all. Not fixed, because (1) has to
come before anyone chooses between (2) and (3) — the same discipline that turned D-144 around.

---

### D-150 — the capture tool cannot answer the questions captures are taken for

**Severity:** FRAGILE · **Affects:** every investigation that needs real feed rows, and
therefore every credential trip · **Found during:** trying to measure D-145's window cost
**Status:** `fixed` — `feat/measure-the-window-cost`

`tools/dump_market_snapshot.py` writes aggregates plus `listings_sample`: **five closed rows and
five active ones**, already normalised to our own key names, with `list_date`, `close_date`,
`contract_date` and `modified` **stripped from each**. That is the right shape for reading a
market at a glance and the wrong shape for every question a capture has actually been taken for
since:

| question | why the capture could not answer it |
|---|---|
| Does a closed listing carry a sale price, and where? (D-144/D-145) | the rows carrying `sales.closePrice` are not in the file — it had to be inferred from `median_close_price` |
| What does the six-month comp window cost? (D-132) | needs close dates on every closed row; the sampler removes exactly those |
| `sweep_extract_field_paths.py --capture` | wants the feed's own key names; `listings_sample` has been normalised |

**Every one of those was asked of the Downey capture and none could be answered from it.** The
cost is a credential trip each time, which is the scarcest thing in this remediation.

**Three changes, all to instruments, none to product code:**

* `--raw-out` writes every row exactly as the feed sent it, minus `privateRemarks`,
  `showingContactName` and `showingInstructions` — the same three
  `tmp/samples/*.sanitized.json` redact. Nothing else is reshaped, because a dump that quietly
  normalises is how a capture ends up unable to answer its own question. `.gitignore` takes
  `tmp/*_raw.json`: these are whole credentialed rows, unlike the aggregates already tracked.
* `sweep_extract_field_paths.py` now **refuses** a market snapshot and prints the two commands
  that fix it. Accepting one would have been worse than refusing: every path would have read as
  absent and none of it true — the same false negative that made the probe report 0/20.
* `scripts/measure_window_cost.py` runs the real `_closed_within_window` — imported, not
  reimplemented — over a raw capture at both windows, and in snapshot mode says plainly which
  part of the question it cannot reach rather than estimating it.

**One trip now serves all three.** Nothing here has been run against production; the tools are
ready and the numbers are not in yet.

---

### D-151 — a workflow named "Release Check" that has never run and could not run

**Severity:** FRAGILE · **Affects:** anyone reading the Actions tab, and `SOURCE_OF_TRUTH.md`,
which listed it as firing on every PR · **Found during:** sizing D-147
**Status:** `fixed` — `chore/delete-release-check`

`.github/workflows/release-check.yml` is deleted. The sizing D-147 asked for — *what would this
gate have caught?* — has one answer: **itself, and nothing else.**

| | |
|---|---|
| runs, ever (GitHub Actions API) | **0** |
| trigger | `workflow_dispatch` only, despite the docs |
| first blocker | `pip install -r requirements.txt` — **that file has never existed here.** `apps/api` and `apps/worker` are Poetry projects |
| second blocker | on 3.11, `from api.main import app` raised `SyntaxError` (D-147) |
| third problem | its `e2e-tests` job duplicates `e2e.yml`, which **D-045 deliberately disabled** after 783 consecutive failures |

Both of the first two are in the workflow's own configuration, not in the code it would test. It
could not have reached an assertion on any commit in this repository's history. The third is
worse than dead weight: running it by hand would have resurrected, through a side door, a job
that was switched off on purpose.

**Deleted rather than repaired.** Repairing it would produce a second copy of
`backend-tests.yml` — which already installs via Poetry, pins the interpreter production runs,
and runs the same suites. If a manual pre-release button is wanted later it should be written
against what CI actually does, not recovered from this.

**Checked before deleting:** `main` is not a protected branch, so no required status check can
name it; nothing in the repository references it but the two docs corrected here.

**`SOURCE_OF_TRUTH.md` said it ran on "PR + push".** It never did. The same table said `e2e.yml`
runs on PR + push, and that has been manual-only since D-045 — both rows are corrected. **A
docs table that grants a workflow triggers it does not have is how a gate that does nothing
reads as coverage,** which is the whole of this entry: the cost was never the wasted minutes, it
was the four-row table that made someone believe four things were being checked.

---

## PROBE RETURNED — 2026-09-30, production credentials, read only

Jerry ran `scripts/probe_simplyrets_behaviour.py` against the production feed. **Verbatim, as
the probe reported them.**

| | verdict |
|---|---|
| **D-074** | **CONFIRMED.** `minclosedate` filters correctly at a real date: **60,874 in 90 days against 962,517 unfiltered.** The 210-day workaround goes |
| **D-075** | `mindate` accepted and ignored. Confirms the shipped choice of `minclosedate` everywhere |
| **D-076** | multi-value `status` — see the probe output; the repeated-parameter form shipped is correct either way |
| **D-081** | **CONFIRMED.** `count=true` works and respects filters: **125 for `postalCodes=92503` against 70,519 feed-wide.** Months-of-supply is one cheap request |
| **D-113** | **CONFIRMED at the window the chart uses: 244,158 closings in 365 days** |
| **decision 01** | **13 requests, monotone, differences cleanly. §7.3 is affordable** |

> **D-118's 3b result was wrong, and the table above is left as the probe reported it.** The row
> is not in the table because 3b's verdict was recorded on the entry rather than here, but it
> belongs with the rest of the trip: the probe counted `closePrice` at `r["closePrice"]` and
> reported **0 of 20**. The feed writes it at `r["sales"]["closePrice"]`. The subject half of
> that verdict stands — SiteX answers the subject's last sale and nothing here changes it. The
> comps half was the opposite of true. Section 3b now counts **every** location separately and
> prints where each field was found, and "absent" means absent from all of them. See **D-145**.
>
> A probe that looks in one place and reports a count is indistinguishable from a probe that
> looks in the right place and finds nothing — and those two results lead to opposite product
> decisions. This one did: D-144 was filed on it.

**The canary worked on 7 of 12 — and what it found is worse than a gap.** Every misspelling
returned the **whole feed, silently**, including lowercase `postalcodes`. A mistyped filter does
not error; it widens the query to everything, and the result reads as a big market rather than
as a bug. That is D-084, confirmed, and it is the reason the canary section exists.

**Two of the twelve failed for a bug in the probe, not the feed.** `cities=San Diego` and
`q=San Diego` raised `InvalidURL` on the unencoded space — **and those two are precisely the
parameters D-087's city-contamination fix depends on.** So the trip spent its credentials and
returned "untestable" for the only question that would have moved D-087. Fixed: `_encode`
percent-encodes each value (commas preserved, since SimplyRETS takes comma-separated lists), and
both now reach the feed. `minclosedate` timed out and is re-queued.

**`--only` added so the re-run costs one section.** Asking for the whole probe again would spend
a credential handover on five questions already answered. Verdicts for sections that did not run
now print **SKIPPED**, not INCONCLUSIVE — those mean different things, and a re-run that reports
five inconclusive results looks like five failures.

> **One command for Jerry:**
> ```
> SIMPLYRETS_USERNAME=... SIMPLYRETS_PASSWORD=... \
>   python3 scripts/probe_simplyrets_behaviour.py --only 5
> ```
> Read only. ~26 requests. It answers whether `cities` and `q` filter in production — and if
> `cities` does, city reports get exact counts back and the 1000-row ceiling lifts (D-087).

**A dependency `--only` exposed, found by running it rather than reading it.** Section 5's
canaries compare against the unfiltered baseline that section 1 fetched, so `--only 5` raised
`UnboundLocalError`. The baseline is now fetched outside the section gates. A section-skipping
flag that has not been run is a flag that does not work.

**The Downey capture is the real-payload fixture.** 301 listings, avg DOM 36.4, MOI 2.4 — used
for the D-105 and D-106 confirmations instead of asking for another trip.
`scripts/sweep_extract_field_paths.py` now takes `--capture` and adds **every row** in it to the
sample, because a field present on some listings and absent from others is exactly what two
bundled fixtures cannot show. Its hardcoded `/home/user/reportscompany` is gone — it derives the
repo root from its own location, so it runs on Jerry's machine, which is the entire point of a
script somebody else is meant to run.

## ONE CREDENTIAL TRIP SETTLES THREE THINGS

All read-only, all needing the same `SIMPLYRETS_USERNAME` / `SIMPLYRETS_PASSWORD`, and they are
listed together because running them separately costs three handovers for one set of credentials.
**`git pull` first** — two of the three only exist as of 2026-09-29.

| # | what | how |
|---|---|---|
| 1 | the behaviour probe — parameter canaries, `count=true`, and the D-074/075/076/081/084 verdicts | `python3 scripts/probe_simplyrets_behaviour.py` |
| 2 | a live payload, to confirm D-105's DOM path and D-106's bathrooms against real data rather than two captured fixtures | `python3 tools/dump_market_snapshot.py`, then `python3 scripts/sweep_extract_field_paths.py` against it |
| 3 | **`minclosedate` at 365 days**, which the twelve-month trend chart now depends on | section **2c** of the same probe — no extra run |

**Item 3 is new.** D-074 confirmed the parameter *filters*; section 2b confirmed it filters *at a
real date*, 90 days out. The trend chart (D-113) asks for **365**, and a feed that honours the
cutoff only so far back would answer 2b correctly and still over-read. Section 2c asks for one
extra count and settles it in the same pass.

**What an ignored cutoff would actually cost — measured, after a first version of this paragraph
said something stronger and wrong.** It claimed the chart would "draw a twelve-month line from an
arbitrary span". It would not. `median_series` iterates `_window(today, 12)` and *looks up* each
month, so rows outside the last twelve calendar months land in buckets nobody reads: fed five
years of closings it returns a series **identical** to the one from twelve months, for both the
median and the count variants. Measured, not reasoned.

The real exposure is the row cap. An ignored cutoff makes the fetch ask for the feed's entire
closed history, which hits `TREND_HISTORY_FETCH_LIMIT` in any busy market, sets the truncation
flag, and makes the series refuse (D-078). **The failure is "no chart in exactly the largest
markets", not "a misleading line"** — fail-safe, and still worth settling, because a chart that
quietly never appears is how D-113 went unnoticed for three weeks in the first place.

**Paste the whole probe output back.** The wording of each verdict is what distinguishes
"confirmed" from "confirmed the wrong thing", and section 2b exists because the first run came
back ambiguous in a way a summary would have hidden.

- **A live SimplyRETS payload, on the same trip as the production probe.** D-105 and D-106 were
  both diagnosed against `tests/fixtures/listing_*.json` — captured responses, real in shape, and
  two of them. `tools/dump_market_snapshot.py` fetches a live page with `SIMPLYRETS_USERNAME` /
  `SIMPLYRETS_PASSWORD` and `scripts/sweep_extract_field_paths.py` re-runs the whole field sweep
  against whatever it returns. **Same credentials as the probe, so it is one trip rather than
  two.** This project has been caught three times by a fixture that did not match production
  (D-084's filter behaviour, the `closeDate` path, and now these), and both fixes retain the old
  read as a fallback precisely because the fixtures cannot rule out a deployment that populates
  it. What the live payload settles: whether any other field is read at a path this particular
  feed does not use.

- **Is production's DB role a superuser?** D-005/D-006's real-world severity depends on it. If production also connects as owner/superuser, D-005 is live exactly as reproduced. If production uses a restricted role, D-005 is contained but D-006 means the portal is showing zeros.
- **Production env values** (T2.9/T2.10). Partially answered by the P2B trace above for the API service; the worker and Vercel sets are still outstanding — see "What I still need" above for exactly which variables settle which defect.
- **Scheduled delivery end-to-end** (T2.3). Needs a real send and a readable inbox.
- **Does a deployed E2E environment exist?** (D-045). `e2e.yml` is disabled until someone can confirm a host these tests can run against *and* that all five `E2E_*` repository secrets are populated. Not a defect — a fact about the deployment that cannot be read from the repository. If the answer is no, the workflow should be deleted rather than re-enabled.
- ~~**Is `apps/api/migrations/phase4_indexes.sql` applied in production?**~~ **ANSWERED (2026-08-18): no, and neither is `0042`.** `signup_tokens` exists but 5 of the 7 indexes do not, and the 2 that do are each declared by an *other*, applied migration. The file never ran; the table arrived by the route its own header describes — created inline by an old request handler. See **Production evidence reconciliation** for the proof, the confirming query, and the corrected bootstrap order.
