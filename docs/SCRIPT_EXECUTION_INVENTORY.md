# Which of this remediation's scripts have actually been run

**Date:** 2026-09-21 · **Branch:** `chore/bridge-broker-identity`

Two scripts in a row turned out to have shipped on the strength of being written
and read. `check_unverified_senders.sql` went out in #75 never having been
executed against anything (found in #78, when a question about which Postgres
version it was validated on could not be answered); `check_schedule_cadence_validity.sql`
was validated only because #77 happened to build a scratch database for it.

That is a pattern worth checking once rather than discovering a third time —
especially now, because Jerry is holding a queue of these to run against
production.

**"Not run against production" is correct and deliberate for several of these.
"Not run against anything" is the thing this table is looking for.**

## The table

Scope: every file under `scripts/` and `db/` added or substantively changed
since the remediation began (`5fb9cd5`).

| File | Executed? | Against what |
|---|---|---|
| `db/schema_migrations.sql` | **yes** | Local Postgres 16.13. Applied by both runners before anything else; exercised by the full `migrate.sh` run recorded under D-001. |
| `db/migrations/0011_create_plans_table.sql` (mod) | **yes** | Local Postgres 16.13. `077db9b`: `DROP DATABASE`, `CREATE DATABASE`, `bash scripts/migrate.sh` → exit 0, **53 of 53 applied**. |
| `db/migrations/0012_seed_plans.sql` (mod) | **yes** | Same run as 0011. |
| `db/migrations/0053_phase4_indexes_and_signup_tokens.sql` | **yes** | A local database built without it; applying it turned two failing endpoints into 200 (DEFECT_LIST:503). Confirms the D-016 fix end to end on a second database. |
| `db/migrations/0054_growth_plan_report_limit.sql` | **yes — in production** | Applied by Jerry, 2026-09-09. The only file here applied to the real database. |
| `db/migrations/0055_affiliate_branding_postal_address.sql` | **NO** | Nothing. Written for D-060, never executed anywhere. Still pending with Jerry. |
| `scripts/migrate.sh` (mod) | **yes** | Local Postgres 16.13, as above. Note: the *shell script itself* has no test; the `--bootstrap` selection logic that `tests/test_migration_bootstrap_guard.py` covers lives in `run_migrations.py`, which is a different runner. |
| `scripts/run_migrations.py` (mod) | **partly** | `tests/test_migration_bootstrap_guard.py` imports and calls the real `partition_bootstrap` and `parse_args` — 19 cases, verified load-bearing (reverting the fix fails 10 of 19). Its *SQL-applying* path has not been run. |
| `scripts/check_unverified_senders.sql` | **yes** | Scratch Postgres 16.13, six shaped accounts, cross-checked against `sender_verification()` — 6 accounts, 0 disagreements, both directions (`apps/api/tests/test_sender_query_matches_code.py`). **Shipped in #75 unrun; validated retrospectively in #78.** |
| `scripts/check_schedule_cadence_validity.sql` | **yes** | Scratch Postgres 16.13, 19 cases, cross-checked against `compute_next_run` — 0 disagreements (`apps/worker/tests/test_cadence_hazard_query.py`, which reads the CASE out of the `.sql`). |
| `scripts/probe_simplyrets_behaviour.py` | **yes, but not this version** | Jerry ran it against the production SimplyRETS feed — **twice, both times the pre-#73 six-GET build**. The merged nine-GET version, with the corrected verdict logic, section 2b and the `count=true` check, has never run. That is the one D-074 and #74's MOI numerator are waiting on. |
| `scripts/deactivate_live_schedules.sql` | **NO** | Nothing. Written on D-062's branch; by design a proposal for a live database. Four statements, one of them an `UPDATE`. |
| `scripts/reconcile_stranded_schedule_runs.sql` | **NO** | Nothing. Header says "NOT APPLIED … a proposal for review", which is right about production. `apps/worker/tests/test_schedule_run_lifecycle.py` reads it as **text** and asserts on substrings; it never executes it. Seven statements. |
| 14 scripts in `648c56a` (`check_*.py`, `run_migration_*.py`, `seed_*.py`, `test_affiliates.py`) | **NO, not since the change** | Nothing. The change was mechanical — removing a hardcoded production `DATABASE_URL` default from each — but it removes a default, so any of them invoked without `DATABASE_URL` set now behaves differently than it did. None was re-run afterwards. |

## What that leaves

Three files have **never been executed against anything**, and all three are
deliberate: `0055` waits on Jerry, and the two `.sql` proposals are written for
a live database on purpose. The inventory does not change that — it changes
whether anyone running them believes they have been tried.

The one worth acting on is `probe_simplyrets_behaviour.py`: it has been run, but
not the version in the repository, and the difference between the two builds is
exactly the two checks that are still open.

The 14 credential-sweep scripts are the weakest link by count. The edit was one
line each and almost certainly harmless, but "almost certainly harmless × 14,
never re-run" is how a repository accumulates scripts that do not work.

## The rule this is an instance of

From §0.6: *a diagnostic query that drifts does not fail — it reassures.* The
same is true one step earlier. **A script that has never run does not announce
itself either.** It reads correctly, reviews cleanly, and fails the first time
somebody depends on it — which, for the files in this table, is the moment
somebody points them at production.
