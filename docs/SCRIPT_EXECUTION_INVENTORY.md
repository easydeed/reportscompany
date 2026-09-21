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
| `scripts/deactivate_live_schedules.sql` | **yes — since 2026-09-21** | Scratch Postgres 16.13, through `psql`, seeded to 43 schedules (3 active), 1,067 `schedule_runs` rows and a paused schedule held as a control. **Its data handling was already correct**; what was wrong was the part around the write — see below. `apps/worker/tests/test_deactivate_schedules.py`, 8 cases. Still NOT applied to production. **Now requires `-v expected_active=<n>`.** |
| `scripts/reconcile_stranded_schedule_runs.sql` | **yes — since 2026-09-21** | Scratch Postgres 16.13, through `psql`, seeded to its own documented distribution (27/8/18/3/1) plus a live mid-flight run as a control. It parses and all seven statements execute. **Running it found three defects** — see below. `apps/worker/tests/test_reconcile_backfill.py`, 8 cases, keeps it that way. Still NOT applied to production, which remains correct. |
| 14 scripts in `648c56a` (`check_*.py`, `run_migration_*.py`, `seed_*.py`, `test_affiliates.py`) | **NO, not since the change** | Nothing. The change was mechanical — removing a hardcoded production `DATABASE_URL` default from each — but it removes a default, so any of them invoked without `DATABASE_URL` set now behaves differently than it did. None was re-run afterwards. |

## What running the backfill found

`reconcile_stranded_schedule_runs.sql` was the one gap worth closing, and
closing it was not a formality. Three defects, none of which reading it had
found, and none of which its text-assertion test could see:

1. **Section 3's `schedule_runs` UPDATE had no age guard.** A run created
   seconds earlier, generation legitimately `processing`, was marked
   `failed — consumed then killed mid-flight; report never produced`. A
   backfill that can fabricate a failure for work still in progress. 22 rows
   updated where 21 were stranded.

2. **Section 3's `report_generations` UPDATE was guarded on `g.generated_at`,
   which is NULL for exactly the rows it needed to reach.** A generation that
   was never consumed has no timestamp — the API's INSERT writes status and
   nothing else — and `NULL < ...` is NULL, not true. The three never-picked-up
   rows were silently skipped and left at `queued` forever. 18 rows updated
   where 21 were stranded.

3. **The VERIFY said "should return zero rows" and could not.** Section 4
   deliberately leaves the dangling row, and the verify counted it. A correct
   run reported failure.

1 and 2 are opposite errors from one missing idea: the population belongs to
the RUN's age, which always exists, not the generation's timestamp, which may
be NULL or may be recent. Together they produced four rows whose
`schedule_runs` said `failed` while their `report_generations` still said
`processing` or `queued` — the exact inconsistency the file exists to remove,
created by the file.

All three are fixed, and all three regressions were applied and seen to fail.

One more thing surfaced, in the test rather than the file: the first version of
the harness split the SQL on `;` and broke on a semicolon **inside a quoted
literal**. The fix was to stop re-implementing SQL lexing and invoke `psql`
instead — which is how the file will actually be run, so the test now exercises
the real path including `\echo` and `ON_ERROR_STOP`.

## What running the deactivate proposal found

Different from the backfill, and worth separating: **the data handling was
already right.** On a seeded world it changed exactly the three intended rows,
preserved `next_run_at` on each, left the control schedule byte-identical
(hashed before and after), and retained all 1,067 runs. `UPDATE` does not
cascade; the history survived exactly as the header promises.

What was wrong was everything around the write.

1. **"Look before you write" could not be followed.** The SELECT and the UPDATE
   sat in one transaction in one file. Run as a file — the only way anyone runs
   it — psql does both in one pass, and the operator reads the list of what they
   were about to change *after* it has already changed. An instruction that
   cannot be followed is not a safeguard.

2. **"This must return the same count as before" had no before.** The file never
   captured a baseline, so the number it printed was unverifiable against
   anything.

3. **"Expect 3 rows (43 schedules exist, 3 are active)" was a snapshot of
   2026-09-09 with nothing enforcing it.** Confirmed by adding a fourth active
   schedule and re-running: silently deactivated, no mention in the output.

All three are now one mechanism. `expected_active` is a **required** psql
variable — omit it and psql fails on the uninterpolated `:expected_active`
before reaching the UPDATE; get it wrong and the scope guard aborts and says by
how much. Both post-write checks are assertions instead of printed numbers.

**The history assertion has teeth, not just tidiness.** Slipping a `DELETE` in
place of the `UPDATE`, as a test:

```
old structure → committed. 1,067 schedule_runs destroyed, and it printed
                "schedule_runs_retained" as part of a successful-looking run.
new file      → ERROR: STOP - schedule_runs went from 1067 to 0
                transaction rolled back. All 1,067 survive.
```

Implementation note, measured rather than assumed: psql does **not** interpolate
`:variables` inside dollar-quoted blocks, so a `DO $$ ... :expected_active ... $$`
guard is a syntax error. The guard is plain SQL, and the abort is a cast of a
non-numeric string to `INT` — Postgres has no `ASSERT` outside plpgsql, and the
string becomes the error message.

## What that leaves

**One file has never been executed against anything: `0055`**, which waits on
Jerry and is a two-line `ADD COLUMN`. Every `.sql` proposal in this repository
has now been run somewhere.

Between them the two proposals carried six defects, none of which their reviews
or their text-assertion tests had found, and two of which would have written
false data into production. Neither file was careless; both were read carefully
by the person who wrote them. That is the point.

The probe has been run against the repository version at last (2026-09-21), and
four of its five verdicts are settled. One overclaims — see D-074.

The 14 credential-sweep scripts are the weakest link by count. The edit was one
line each and almost certainly harmless, but "almost certainly harmless × 14,
never re-run" is how a repository accumulates scripts that do not work.

## The rule this is an instance of

From §0.6: *a diagnostic query that drifts does not fail — it reassures.* The
same is true one step earlier. **A script that has never run does not announce
itself either.** It reads correctly, reviews cleanly, and fails the first time
somebody depends on it — which, for the files in this table, is the moment
somebody points them at production.
