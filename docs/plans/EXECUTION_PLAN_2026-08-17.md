# TrendyReports — Remediation Execution Plan

**Date:** 2026-08-17
**Status:** Historical for Phases 0–6. **Current only for §0 Rules of Engagement**, which still governs every later plan.
**Inputs:** `DOCS_AUDIT_2026-08-17.md` (code-verified at HEAD `f854ed6`), Chrome UX audit (17 findings)
**Executor:** Claude Code
**Owner:** Jerry

---

## 0. Rules of Engagement

Read this section fully before touching anything. Violating these is a failure condition,
not a style preference.

### 0.1 Branch hygiene

- **One branch per phase.** Never mix phases. Never mix categories (docs deletion and
  code fixes do not share a branch).
- Branch from `main`, freshly pulled, every time:
  ```bash
  git checkout main && git pull --ff-only && git checkout -b <branch>
  ```
- Branch names are fixed by this document. Do not invent your own.
- **Every branch must be independently revertable.** If Phase 3 has to be rolled back,
  Phase 1 and Phase 2 must survive untouched. No cross-phase dependencies in the diff.
- Commit per ticket, not per phase. Conventional commits:
  ```
  <type>(<scope>): <imperative summary>

  Ticket: T3.5
  Evidence: apps/web/components/marketing/hero.tsx:44
  ```
  Types: `fix`, `feat`, `chore`, `docs`, `test`, `refactor`.
- Never `git push --force` to a branch that exists on origin.
- Never commit directly to `main`.
- Open a PR at the end of each phase. Do not merge it yourself. Jerry merges.
- If a ticket turns out to be wrong or impossible, **stop and report**. Do not improvise
  a substitute.

### 0.2 Scope discipline

- **Fix only what the ticket says.** If you notice something else broken, add it to a
  running `FINDINGS.md` on the branch and keep moving. No opportunistic refactors.
- No dependency upgrades. No formatting-only changes. No "while I was in here."
- Do not touch anything in `.cursor/rules/skills/references/forbidden.md`.
- If a ticket requires a business decision (a price, a real address, a claim about
  customers), it is marked **[JERRY]**. Stop at that ticket and ask. Do not guess and do
  not use a placeholder.

### 0.3 Token efficiency

The audit already did the investigation. Do not repeat it.

- **The audit report is the spec.** Treat its `file:line` citations as accurate at
  `f854ed6` and verify only that the line still says what the audit claims — do not
  re-derive findings from scratch.
- Do one grep pass per phase, up front, for every pattern that phase needs. Write results
  to a scratch file. Do not grep the same pattern twice.
- Do not open a file that is not in the ticket's file list unless you state why first.
- Batch all edits to the same file into one pass.
- Do not run the full test suite per ticket. Run it once per branch, before the PR.
- Do not read `docs/archive/cursor_documentation_and_commit_review.md`. It is 75,000
  lines and it is on the kill list. Delete it unread.

### 0.4 Self-review gate — after EVERY ticket

Before moving to the next ticket, review your own diff as an adversary. Load
`.cursor/rules/skills/trendyreports-reviewer/SKILL.md` and apply it. Output this block
verbatim, filled in:

```
TICKET: <id>
DIFF REVIEWED: <files touched, +N/-N lines>

CHECKED:
- [ ] Change matches the ticket exactly — no more, no less
- [ ] Nothing on the forbidden list touched
- [ ] No secrets, keys, tokens introduced
- [ ] No debug code, console.log, print, commented-out blocks left
- [ ] Imports clean
- [ ] For frontend: loading/error/empty states intact; tier-conditional renders intact
- [ ] For backend: params bound; RLS context set; response shapes backward-compatible
- [ ] Nothing else in the repo now references what I changed or deleted

EVIDENCE: <file:line for each claim above that needs one>

VERDICT: SHIP | FIX | BLOCK

WHAT I DID NOT DO: <explicit list — anything noticed and deliberately left alone>

UNCERTAIN ABOUT: <anything you could not verify. Say so. Do not fabricate confidence.>
```

Rules for the verdict:
- **FIX** means you found a problem in your own work. Fix it, then re-review. Do not
  advance on a FIX.
- **BLOCK** means the ticket cannot be completed correctly as written. Stop the phase and
  report to Jerry.
- A verdict of SHIP with an empty "UNCERTAIN ABOUT" on a non-trivial ticket is a red flag.
  If you genuinely have no uncertainty, say why.

### 0.5 Honesty requirements

- If you cannot reproduce a finding from the audit, say so. Do not fix a bug you cannot
  see.
- If a "fix" is cosmetic and does not actually address the finding, say so.
- If you suspect the local checkout differs from production, flag it as uncertain rather
  than assuming.
- Never claim a test passed that you did not run.

### 0.6 Verification requirements

*Added 2026-09-10 from the Delivery Surfaces remediation. Every rule here was written
after making the mistake it forbids.*

**And several were written after making it again, in the fix.** The rule-seven test that missed
its own regression was written one file from rule seven. The postal-address line added to close a
CAN-SPAM omission was itself unreadable — 2.41:1, failing the standard — so the shape landed on the
line whose only purpose was to be conspicuous. Three separate tests have now matched their own
comments explaining the defect they were searching for, because a fix that documents the bug in
place puts the symptom string in the region the test searches; the fix is to assert against the
code rather than the file. **Treat each of these as evidence the rule is live rather than
historical: the pattern that produced the defect is the one you are working in while you remove
it.**

- **No finding derived from a sample render counts until it is reproduced through the
  production path.** Three instances in this project — the property report aerial, the
  email placeholder links, and the inventory report's months-of-supply figure — where a
  reviewed artefact did not reflect what production emits. A sample can show what the
  code *can* produce; only production shows what it *does*.

- **A number in a tool's output is a property of the tool until you check.** The probe printed
  `500 rows` for the active query and that was read as SimplyRETS' page ceiling. It was the
  probe's own `limit=500`. The conclusion that followed — "D-078 fires on every city with 500+
  active listings" — was wrong in the threshold (it is 1000, ours) and wrong in kind (it is not an
  API property at all). **Fourth instance of the missing-row trap and the first from the reviewing
  side rather than the implementing one**, which is the useful part: the trap is not a property of
  who is writing the code. Before treating a measurement as a fact about the system, ask which
  layer produced the number. The probe now says so in its own output.

- **A validator on the write path proves what gets written from now on, not what is already
  there.** Same family as the missing-row rule below, and the same error one level up: reading
  a property of the code as a property of the data. "The API validates cadence on create, so no
  schedule can be in that state" covers every row written after the validator existed and says
  nothing about the ones written before it — and this project's tables predate most of its
  validation, `schedules` by ten months. The database-level version has the same hole with a
  sharper edge: `ADD CONSTRAINT ... NOT VALID` installs a CHECK that enforces new rows and
  skips existing ones, and a constraint dropped and re-added leaves no mark on the table
  definition, so reading the schema cannot tell you either. **The only thing that answers "is
  any row like this" is a query for rows like this**, plus `pg_constraint.convalidated` to know
  whether the constraint was ever checked against what was already stored.

- **Ask what writes this row, and when, before reasoning about what its absence proves.**
  Three instances where a missing row was read as a missing action:
  `schedule_runs.started_at` (assigned by nothing, so a predicate on it matched every row
  and read like a guard); the failed-runs table (structurally cannot record a crash that
  happens before the send); and `email_log` (written inside a transaction that could roll
  back after the email had already gone). **In each case the answer came from the writer,
  not from the data.** A missing row proves a missing *write*. It does not prove a missing
  *action*.

- **Render to verify; do not read to verify.** A fix that edits the correct-looking line
  can still be inert if the value is supplied upstream. The REALTOR® ticket specified a
  template change that would have produced a green diff, a closed ticket, and no change in
  behaviour, because `property_builder.py` supplies the string before the template runs
  and the Jinja `default()` on that path is dead code.
  **This applies to third-party behaviour too, and that is the version that cost most.**
  "Celery acknowledges a task on receipt, so a restart discards prefetched work" was
  written into D-062, `schedules_tick.py`, `test_delivery_idempotency.py` and a PR body
  without once being run. Running it — a worker, a real broker, `kill -9` mid-burst — took
  under an hour and showed the claim is wrong: prefetched messages are unacknowledged in
  both modes and come back either way; what the default loses is the task that is
  *executing*. The conclusion survived, which is the dangerous part. **A claim repeated
  across four files is not corroborated by being repeated.** Where the behaviour belongs
  to a library, the experiment is the citation.
  **It also runs in reverse, and that version wastes a whole ticket.** D-067 was filed off
  five template lines that use Jinja's plain `default()` — "a NULL title renders the string
  None on the cover". Rendering it showed the leak is impossible: `property_builder.py`
  substitutes the title first, so all five fallbacks are dead code. Same file, same
  reasoning error as D-066, opposite sign: one nearly shipped an inert fix, the other
  nearly fixed an impossible bug. **Render before filing, not only before fixing** — and
  render through the path production uses, because that is where the substitution was.
  Rendering it also turned up the two defects that *were* live on those lines and that
  reading them had missed.

- **Grep for the construct, not for the symptom, and re-run the check after the fix.**
  Three instances where the post-fix check found what the pre-fix survey missed: the third
  unguarded map pin, `CreateCompanyRequest`, and `bold_report.jinja2:848` — the last found
  only because a test ran after the change, since it used the right construct with a
  different string.

- **A check that reports damage after committing it is decoration. A guard refuses to
  commit.** `deactivate_live_schedules.sql` ended with `SELECT COUNT(*) AS
  schedule_runs_retained` — a number printed after the transaction's work was done, with
  nothing to compare it against and no power to stop anything. Substituting a `DELETE` for
  its `UPDATE`, as a test: the old file **committed**, destroyed all 1,067 runs, and printed
  that count as part of a successful-looking run. The same file with the count turned into an
  assertion against a captured baseline aborts and rolls back, and every row survives. The
  test is whether the check can *fail the operation* — if the worst it can do is appear in
  output nobody diffs, it is documentation with a query attached. Same family as the two
  rules above: an instruction that cannot be followed (`"Look before you write"` above a
  SELECT with the UPDATE directly beneath it, in one file, run in one pass) and an expectation
  with no baseline are both checks that cannot fail.

- **A guard that refuses input is a guard that can refuse legitimate input.** Check what
  it rejects, not only what it accepts. Twice a correct-looking security fix would have
  converted an injection into an outage: rejecting a non-hex colour by raising, and
  scheme-allowlisting the unsubscribe URL — which would have stripped a sentinel that is
  not a URL and aborted *every* send.

- **A statistic describing a comparison is not a prediction of an operation.**
  `git diff --stat` between `chore/commit-planning-docs` and `main` showed ~3,200
  deletions — every test file from this remediation, the reconcile script, 847 lines of
  the defect list — and the branch sat unmerged for six turns because that read as
  "merging this wipes six weeks of work". The actual three-way merge was **six additions
  and zero deletions**: the branch predated the files it appeared to delete and never
  touched them. **Test the operation; do not read the summary.**
  (`git merge --no-commit` then `git diff --cached --diff-filter=D` answers this in
  seconds.) Same shape as `started_at` above — a value that means one thing, read as
  evidence of another.

- **A selector that is unique by accident retargets silently when it stops being unique.**
  `handlers[0]` picked one of *two* exception handlers sharing a name and passed only
  because `ast.walk` happened to reach the intended one first; restructuring an unrelated
  `if` changed the nesting and the test began asserting against the other handler while
  still looking like it tested the first. The general form covers `[0]`, `next(...)`,
  `.first()` without an `ORDER BY`, `grep | head -1`, and any CSS or XPath selector:
  **if the thing you are naming could ever have a sibling, name it by a property and
  assert the match is unique.** An audit of this remediation's own tests found five more
  live instances — four taking `[0]` of a list that happens to hold one element today —
  each of which would have gone on passing while checking the wrong thing. A test that
  can quietly point somewhere else is worse than no test, because it reports success
  either way.
  **And the way you check a selector is to make it wrong and confirm it fails.** Not
  rereading the assertion — applying the regression it claims to catch, and running it.
  D-072's first ordering test asserted *"some `conn.commit()` precedes the dispatch"*; the
  ticker loop has an unrelated commit on the usage-limit skip path, so moving the dispatch
  back above the real commit left the test **passing**. That was written by someone who
  had just written this rule, one file away, and rereading it would not have found it. The
  fix — requiring a commit *between* the two calls — was obvious the moment the regression
  was applied and invisible before. **A test you have not seen fail is a test you have not
  seen.**
  **Fifth instance, and the one that names the general shape: a test can be end-to-end and
  still not observe the thing it claims to.** D-037's bridge test ran the real consumer loop,
  against a real Redis, and drained a real queue — and reverting the fix's atomic `blmove`
  back to the destructive `blpop` left all eleven tests GREEN. Two reasons, both worth
  recognising elsewhere: the unit tests performed the atomic take themselves in a helper, so
  they were exercising Redis rather than the bridge; and the end-to-end test only observed the
  loop *after* it finished, where a destructive take and a safe one produce identical state.
  **The defect lives in a window, so the test has to be inside the window** — the fix was to
  block `delay` and assert the job is findable in Redis while the loop is holding it.
  Generally: when what you are testing is what happens during a failure, arrange to be
  observing during it, not after.

  **Fourth instance, same shape, in D-019's ticker gate.** `test_the_skip_advances_next_run_at`
  asserted that an `UPDATE` to `schedules` had happened. Deleting the `compute_next_run` call
  and the `next_run_at = %s` assignment leaves the lock-clearing
  `UPDATE schedules SET processing_locked_at = NULL` on the same path — so the regression the
  test is *named after* left it green, while the thing it was guarding (a refusal row written
  every 60 seconds, forever, into the table five branches had just made trustworthy) went
  unguarded. The correction, again, is to assert the **content** of the write and then, in a
  separate test, its **consequence**: the schedule is no longer in the due set on the next
  tick. "A write happened" and "the write works" are different claims and only the second one
  answers the question anybody actually has.
  **The same failure, one layer out: a diagnostic query that drifts does not fail — it
  reassures.** `check_schedule_cadence_validity.sql` asks whether any stored schedule can make
  `compute_next_run` raise. Let its predicate fall behind the function and it returns zero
  rows, which is indistinguishable from the answer everyone is hoping for, so nobody questions
  it. A test is at least expected to be able to fail; a query is read as a report. Anything
  that encodes a claim about code somewhere the code cannot see it — a diagnostic query, a
  runbook, a dashboard threshold, an alert rule — needs to be executed against the code it
  describes, in both directions. Ours reads its `CASE` expression out of the `.sql` file and
  runs it against the function case by case, including the healthy cases: a predicate that
  flags everything never misses a hazard and tells you nothing.

- **`str()` of a query object gives you a repr, not the query.** A test double for a database
  cursor matched statements with `str(query).startswith("SET LOCAL")`. `psycopg`'s `sql.Composed`
  stringifies to `Composed([SQL('SET LOCAL app.current_account_id TO '), Literal('…')])`, so the
  prefix never matched, RLS scoping fell through to the "unexpected statement" branch, and **ten
  tests failed in a way that read as the feature not working.** Twenty minutes went into the code
  under test, which was fine. The general form is wider than psycopg: any double that pattern-
  matches on a stringified input is asserting against a `__repr__` it did not write and may not
  own. **Print what your double actually received before believing what it tells you about the
  code** — and when a whole suite fails at once, suspect the harness before the change, because a
  real regression rarely breaks everything and a broken fixture always does.

- **A fixture should be built by the production builder, not hand-copied from it.** Twenty-three
  of the root suite's forty failures are one mistake repeated: `tests/test_property_templates.py`
  hand-writes the `property` dict the templates receive, and omits keys that
  `_build_property_context()` — a single dict literal, the only construction site — sets
  unconditionally. The templates then raise `UndefinedError` on a shape production never produces.
  The same file duplicates `format_currency`, `format_currency_short` and `format_number` under a
  header reading *"Custom Filters (must match production)"*, and they no longer do: the copies
  return `"-"` where `template_filters.py` returns `"N/A"`. **A copy annotated "must match" is a
  copy that has already been noticed to be at risk and left unprotected anyway.** A fixture that
  the production builder produces cannot drift from it; one that a human transcribes drifts the
  first time either side changes, and — this is the part that costs — **it drifts silently in both
  directions**, so the suite reports failures the product does not have and misses failures it
  does. Where a builder cannot be called in a test, derive the fixture from its output once and
  assert the derivation, rather than retyping the result.

- **A regression that did not take effect looks exactly like a test that is too weak.** Four
  regressions were applied to D-087's suite; the fourth — replacing `_filter_by_city`'s equality
  test with a substring test — came back **green**, which reads as "this test does not cover that".
  The mutation had applied to the file. It had not reached the interpreter.

  **The mechanism, reproduced in isolation rather than inferred from the symptom.** A `.pyc`
  records the source's mtime **truncated to whole seconds** and its size, and reuses itself when
  both still match. `if listing_city == city_lower:` and `if city_lower in listing_city:` are the
  same length, and the write landed in the same second as the restore before it — so the header
  matched and the old bytecode ran. Instrumented: `pyc mtime=1790091276 size=35`,
  `src mtime=1790091276 size=35`, header match `True`, source on disk reading `return a in b`, and
  the process printing the result of `==`. **Same-size edits inside one second are exactly what a
  scripted regression harness produces**, so this is the normal case for the tool, not a
  coincidence. (The first attempt to reproduce it *failed* — `os.utime` was passed float times,
  which round, which bumps the mtime, which invalidates the cache and hides the effect. Restoring
  the timestamp with `ns=` reproduces it every time. A failed reproduction is not a disproof; it is
  a reproduction with a bug in it.)

  **Remedies, each measured against that reproduction rather than assumed:**

  | | result |
  |---|---|
  | **delete the `.pyc`** (`rm -rf __pycache__`, or unlink the one file) | **works, every time — use this** |
  | `touch`/`os.utime` the source forward | **0 of 12** when the touch lands in the same second; works only if it happens to cross a boundary. Unreliable exactly when the harness is fast, which is always |
  | `-B` / `PYTHONDONTWRITEBYTECODE` | **no effect.** They stop Python *writing* bytecode; they do not stop it *reading* what is already there |
  | `--check-hash-based-pycs always` | **no effect.** Runtime-written `.pyc`s are timestamp-based; the flag governs hash-based ones |

  Note the second and third rows: both are the obvious-sounding fix, and neither works. `-B` was in
  the command that finally showed the regression failing, which made it look like part of the
  remedy; the purge in the same command was doing all of the work. **A fix that was present when
  the symptom cleared is not thereby the fix.**

  Two habits close this off: `assert mutated != original` before running anything, which separately
  catches a `str.replace` that matched nothing, and delete bytecode between runs. And the general
  form, which is why it belongs here: **a negative result from a verification tool is a claim about
  the tool until the tool is shown to have run.** Same class as "a number in a tool's output is a
  property of the tool" — one rule up, one layer down.

- **A check that cannot be fixed yet belongs in `xfail(strict=True)` with its defect named — not
  in a permanently red build, and never in a `skip`.** Unfixable red is not honesty, it is the
  mechanism that hid D-038 and D-041: a check nobody can act on trains everyone to ignore the
  check, and the next *real* failure lands inside the noise unseen. The root suite proved it at
  scale — 40 failures left as "the known-red baseline" for 19 days, during which every Backend
  Tests run on `main` and on every reviewed PR reported failure and nobody looked.

  `xfail(strict=True)` keeps the assertion executing, keeps a NEW failure in the same file
  visible, and **breaks the build the day the product catches up** — because a strict xfail that
  passes is an error, which forces the marker off. A plain `skip` does none of that; it stops
  running and goes quiet forever.

  **The condition, without which this is just a skip with better manners: the link goes both
  ways.** Every `xfail` reason names its defect ID, and that defect's entry lists the tests it
  gates. One direction alone rots — a reason pointing at a defect nobody cross-references is an
  excuse, and a defect that does not name its xfails cannot tell you what to delete when it is
  fixed. Generate the list from the source rather than typing it (`@_Dxxx_GATED` → the `def` on
  the next line), and assert the link in a test, for the same reason every other rule here is a
  test: a documented invariant that nothing checks is a comment.

  **Mark methods, not classes.** Applied at class level the first time, the marker covered two
  tests that were already passing; they xpassed, strict turned that into a failure, and the
  mistake surfaced in one run. That is the mechanism working — but it works only if `strict` is
  on, which is the other half of why `strict` is not optional here.

- **A mutation that matches nothing succeeds. Assert that the edit landed, not that you made it.**
  Three instances now, in three different tools, and each cost something:

  | | what was edited | what happened |
  |---|---|---|
  | D-087's harness | a regression mutation, same length as the original | file changed, interpreter read a stale `.pyc` — the regression came back **green** and read as "this test is too weak" |
  | the D-091 sweep | `str.replace` on a test file | the anchor had drifted; the replace matched nothing, the script printed its success line, and pytest ran against **unmodified** code |
  | the board header | `str.replace` on the summary table | a merge changed the expected string across three branches running; every replace matched nothing and the table silently said `33/53/91` against entries saying `30/60/94` |

  **The common shape is that "replace" and "matched nothing" are indistinguishable from the
  outside.** `str.replace` returns a string either way. `sed` exits 0 either way. A patch that
  applies to zero hunks still writes a file. And in every case the *reasoning* was right — the
  derivation was correct, the mutation was the correct mutation, the anchor was the correct anchor
  *when it was written*.

  Three habits, cheap and in order of value:
  1. **`assert mutated != original`** before doing anything with the result. One line; catches all
     three cases above.
  2. **Check the observable consequence, not the call.** After a mutation, assert the new text is
     present — and after a regression run, assert it produced the failure you expected. A
     regression that does not fail is information about the *harness* until proven otherwise.
  3. **Where the thing being kept in sync is derivable, make it a test rather than a habit.**
     `tests/test_defect_list_counts.py` exists because the board's summary drifted from its own
     entries while every individual derivation was correct. The failure was never the arithmetic;
     it was the write-back, and only a test notices a write-back that did not happen.

- **A defect list needs a read path, not just a write path — a record is not a queue.** D-009 named
  the exact lines, the exact symptom and the `/health` blindness, in Phase 2A, accurately. It was
  then rediscovered eleven months later by tripping over it in unrelated work, and filed again as
  D-094. Everything in this project has been about making failures visible; **this failure was
  visible, correctly written down, and nothing consumed the record.**

  The sweep that followed found two more, in the other direction: D-006 (BROKEN) and D-003 had both
  been *fixed* — one by a security commit, one incidentally while restoring CI — and left `open`.
  So the count at the top of the board was simultaneously hiding a live BROKEN defect and inventing
  two that no longer existed. **Both directions corrupt the same number**, and neither announces
  itself, because an entry nobody re-reads cannot contradict anything.

  The remedy is not better filing. Filing was not the failure. **Concretely: before any branch that
  touches a file, grep the board for that file — an entry naming it is either the work or a
  duplicate of it; and re-run the stale sweep whenever the open count is about to be quoted as a
  status.** Both are cheap and neither depends on anybody remembering an entry exists. The first
  catches D-009's direction (about to rediscover something already known), the second catches
  D-006's (about to report risk that was fixed months ago).

  The general form, which is why it sits in §0.6 rather than in a process doc: **a document that
  records findings and is only ever appended to is write-only, and a write-only record of problems
  reads as diligence while functioning as a drain.** Anything that accumulates claims about the
  system — this board, a findings file, a backlog, a runbook's "known issues" — needs a defined
  moment when something reads it back and checks it, or it decays into an archive that everyone
  cites and nobody consults.

  **Report the depth PER ENTRY, not per sweep.** "Swept, all 30 checked" implies a uniform rigour
  that a sweep never has. The first one here reproduced the mechanism for fifteen entries,
  confirmed four more by appearance only, and did not verify one at all — and those are three
  different claims that a single sentence flattens into one. Mark each entry with how it was
  checked, because the next person's decision about whether to trust it depends on that and not on
  the total.

  The distinction that matters most is the last one: **"not re-verified" must never be allowed to
  read as "probably fine."** D-068 needs a measured Celery experiment, the way D-062 did — a real
  worker, a real broker, a `kill -9` — and a confident code read would carry the same risk in
  either direction. An unverified entry is an open question, and the sweep's job is to say which
  entries are questions rather than to make the list look uniformly examined.

- **A detector's silence means nothing until you have seen it speak. Run every new check against
  input you know is bad, before you run it against the code you hope is good.**

  *Added 2026-09-23 from Workstream A.* The acceptance criterion was "no brand hex literal in any
  template, enforced by lint over the template directory". The obvious order is to write the rule,
  fix the templates, and watch it go green. That order can never distinguish a rule that passes
  from a rule that matches nothing — and this project has already shipped the second kind twice:
  the `str.replace` that silently no-opped after a merge moved its anchor, and the regression
  harness whose mutation was undone by the next mutation before pytest ever saw it.

  So the rule was run against `main` first, on thirty untouched template files. It reported **111
  findings in 26 of them**, which is the result that makes every later green run mean something. A
  zero there would have been the bug.

  The same calibration belongs in the test suite, not just in the session that wrote the rule,
  because a regex can die later: **a positive control and a negative control, side by side.** One
  fixture that must produce findings, one that must produce none. A checker with only the negative
  control is indistinguishable from a checker that has stopped working, and it fails silently in
  the direction that looks like success.

  This generalises past lints. It applies to a validator, a guard clause, a monitoring alert, a
  schema check, a permission test — anything whose normal output is *nothing*. **Absence of a
  finding is evidence only from an instrument you have watched find something.**

- **A revert during recovery is a second change, not a way back. Commit the working state before
  attempting recovery from a bad edit.**

  *Added 2026-09-23 from Workstream C.* A span replacement silently swallowed two functions that sat
  between the one being replaced and the next named one, which surfaced as `NameError` across
  twenty-one tests. The reflex — `git checkout -- <file>` — fixed the NameError and **discarded two
  migrations that had already passed their gate**, because they had not been committed yet.

  `checkout` does not undo the last edit. It returns the file to the last COMMIT, which may be
  several verified steps back. In a session that makes many small verified changes, that distance
  is invisible at the moment you need it most: you are already dealing with one failure, and the
  command that looks like an undo is a larger change than the one you are undoing.

  Concretely: **commit each step that passes its gate**, and when an edit goes wrong prefer a
  targeted inverse edit over a file-level revert. If a revert is genuinely the right move, first
  establish what it will take with you.

- **A behavioural test suite cannot verify a behaviour-preserving migration. Structural claims need
  structural assertions.**

  *Added 2026-09-23, same incident, and it is the more general half.* After that revert the
  repository held two orphaned template files that nothing rendered — and **the whole suite was
  green**, correctly. The inline markup those templates were meant to replace had come back with the
  revert, so behaviour was genuinely unchanged. The green was accurate about behaviour and silent
  about structure.

  That silence is not a gap in the tests; it is what the tests are for. A restructure's entire
  premise is that output does not change, which means **every output-shaped assertion is guaranteed
  to pass whether or not the restructure happened.** The render diff, the contrast audit, the golden
  files — all of them would report success on a migration that had been entirely undone.

  So a migration needs a gate of a different kind, asserting the SHAPE of the code rather than the
  content of its output: that every extracted file has a caller, that no path still does the thing
  the extraction was meant to remove, that the counts agree. Behavioural and structural gates answer
  different questions and neither substitutes for the other — which is worth knowing before writing
  the third behavioural test in a row and feeling covered.

  **The gate was then proved against the byte-exact state, and the first attempt to reproduce that
  state was unfaithful in a way that inverted the result.** Reconstructing "the migration was lost"
  by hand — putting the markup back inline while leaving the seam function in place, still calling
  the block — produced no orphan at all. The render diff fired and the structural gate stayed
  silent, which is the exact opposite of the real incident. Only checking out the actual commit
  reproduced it: render diff 32 passed, contrast audit 77 passed, structural gate failing and naming
  all four lost blocks.

  This is the same family as the stale `.pyc` that made a regression look green and the `str.replace`
  that matched nothing: **a regression which does not reproduce the fault says nothing about the
  guard aimed at it**, and it is worse than no evidence because it reads as evidence. Where a real
  failure has already happened, reproduce it from the recorded state — a commit, a captured payload,
  a saved file — rather than from a description of it. Reconstruction from memory tests the
  reconstruction.

- **A description of what code does is a hypothesis. Derive it by running the code, not by reading
  it — and this holds even when the reading is careful, unhurried, and done by the person who just
  wrote the code.**

  *Added 2026-09-24 from Workstream C.* The consolidation ended with a declarative map,
  `REPORT_BLOCKS`, naming which blocks each of the eight report types renders. It was written first
  by reading the eight builder functions — slowly, with the file open, by the author of the
  refactor that had just moved every one of those blocks. **Seven of the eight entries were wrong.**
  Rewritten from an instrumented render — a hook on `render_block` recording every call during a
  real render of each type — all eight were right, and the difference was checked into a test that
  now compares the declaration against the recorded sequence on every run.

  The errors were not about the hard parts. The one worth naming, because it is now recorded in the
  map itself: `open_houses` does not render `read:insight` like the other seven — it has no insight
  text, so the Quick Take panel stands in, and `read:panel` appears in its place and in a different
  position. That is invisible from the builder, which calls the same helper the other types call;
  it is decided by the data. The rest have the same shape in general: almost none of the twenty-odd
  `render_block` calls sit at a layout function's own level. They sit one or two frames down inside
  small helpers — `_build_hero_stat`, `_build_gallery_card_compact`, `_build_section_label` — whose
  names describe a thing on the page rather than the block that draws it, and several of them are
  called from loops, so one name in the map stands for one call or for six depending on the data.
  The corrected map was not produced by diagnosing the wrong one entry by entry. It was produced by
  discarding it and reading the trace.

  This is the same rule as the detector's silence, turned the other way round. That one says a
  check reporting nothing is not evidence until you have watched it report something. This one says
  **a claim about behaviour is not evidence until you have watched the behaviour** — and the two
  cover the two halves of the same mistake, which is treating your model of the system as an
  observation of it. Reading tells you what the code was meant to do; that is a genuinely useful
  thing and it is not the same question.

  Practically: any artefact that asserts what the code does — a map, a table of call sites, a
  sequence diagram, a docstring listing side effects, a migration checklist — should be produced
  from an instrument where one can be built at all, and where it cannot, should say on its face
  that it was written from reading. And when such an artefact is produced by instrument, wire the
  instrument into the suite: the same drift that made seven entries wrong on the day they were
  written will make them wrong again six months after they were right.

- **A test that reads its expected value from the thing under test cannot fail. Write the
  expectation down, in the test, as a second copy someone has to change on purpose.**

  *Added 2026-09-24 from Workstream D.* A test checked that each report type renders no more
  listings than its configured cap. It read the cap from `PDF_CONFIG[t]["cap"]`, sized its input at
  `cap + 25`, and asserted the render produced exactly `cap`. Every part of that is reasonable and
  the whole is inert: changing a cap changes the expectation and the input together, so the
  assertion holds at any value. Changing `closed` from 200 to 150 was applied deliberately and
  **the suite stayed green.** It was found only because the regression was run.

  This is close to *a detector's silence*, and it is worth separating from it. That rule is about a
  check whose instrument may have stopped working — a regex that matches nothing, a fixture that
  stopped reaching the code. The remedy is to watch it find something. **This one is about a check
  that is working exactly as written and asserts nothing**, because its two sides are the same
  value read twice. Running it against bad input is the only thing that tells them apart, which is
  the third time this month that step has been the whole of the evidence.

  The tell is syntactic and easy to look for: **the expected value and the actual value trace back
  to the same expression.** `assert render(cfg.cap) == cfg.cap`. `assert f(DEFAULT) == DEFAULT`.
  `assert len(items) == len(source)` where `items` came from `source`. A golden file compared
  against a regeneration of itself. A round-trip that serialises with the same function it
  deserialises with. Each of those passes forever and reads like coverage.

  The fix is a pinned literal, and the cost is the point: `RENDERED_LISTING_CAP = {"closed": 200,
  …}` means a cap change fails the suite until someone writes the new number down in a second
  place. That is not duplication to be factored out — **it is the assertion**. Where the value is
  genuinely derived and a literal would be absurd, derive it by a different route than the code
  under test does, and say in the test why the two routes are independent.

---

## Phase 0 — Security & Tooling

**Branch:** `chore/p0-security-tooling`
**Blocking:** yes — nothing else starts until this merges
**Estimated size:** small

### T0.1 — Establish ground truth on repo state

Report only. No changes.

```bash
git log -1 --format="%H %ai %s"
git status -sb
git rev-list --count origin/main..HEAD
git rev-list --count HEAD..origin/main
git log --oneline -15
```

Report: current HEAD SHA and date, whether the working tree is clean, whether local is
ahead of or behind origin, and the date of the most recent commit on `origin/main`.

**Why:** the audit ran at `f854ed6` dated 2026-06-24. Today is 2026-08-17. Either that is
a stale checkout or nothing has shipped in eight weeks. Every downstream ticket assumes
the audit's `file:line` citations are current. If HEAD has moved, say so before
proceeding — a chunk of this plan may need re-verification.

**Acceptance:** a five-line report. If `origin/main` is ahead of the audited SHA, **STOP**
and report before starting T0.2.

### T0.2 — Purge committed credentials from `.env.example`

**File:** `.env.example`

The audit found live-looking SiteX UAT client credentials at `.env.example:23-25`.

1. Replace the credential values with obvious placeholders (`your-sitex-client-id-here`).
2. While in this file: it is also wrong in the other direction — it names
   `RESEND_API_KEY`, `POSTMARK_API_KEY`, `S3_*`, which no code reads, and omits
   `SENDGRID_API_KEY`, `SIMPLYRETS_USERNAME`, `SIMPLYRETS_PASSWORD`, `PDFSHIFT_API_KEY`,
   `OPENAI_API_KEY`, `R2_*`, `TWILIO_*`, `STRIPE_PRICE_*`, `PDF_ENGINE`, `PDF_API_URL`.
   Rebuild the file from the env vars actually read by the codebase:
   ```bash
   grep -rhoE '(os\.environ(\.get)?\(|getenv\(|settings\.)[A-Z_]{3,}' apps/ libs/ scripts/ \
     | grep -oE '[A-Z][A-Z0-9_]{2,}' | sort -u
   ```
   Cross-check against `apps/api/src/api/settings.py` (or equivalent) for the canonical list.
3. Check whether the credentials appear elsewhere:
   ```bash
   git grep -n "<credential-fragment>" -- . || echo "clean in working tree"
   ```

**Do NOT** attempt history rewriting (`filter-repo`, BFG). Report whether the credentials
exist in git history and leave the decision to Jerry.

**[JERRY]** The credentials must be rotated at SiteX regardless of what this ticket does.
Removing them from the file does not un-leak them.

**Acceptance:** `.env.example` contains zero real secret values and lists exactly the env
vars the code reads. A one-line report on history exposure.

### T0.3 — Make Cursor actually load its rules

**Files:** `.cursorrules.md` → `.cursorrules`

The rules file has been committed under a filename Cursor never auto-loads. Its own line 2
says it belongs at `.cursorrules`.

1. `git mv .cursorrules.md .cursorrules`
2. Fix the dead link inside it: `GOPHER-001_REPORT.md` (underscore) → the file uses a
   hyphen. **Note:** `docs/plan/GOPHER-001-REPORT.md` is on the Phase 1 kill list — remove
   the reference entirely rather than repointing it.
3. Grep for anything referencing the old filename:
   ```bash
   git grep -n "cursorrules.md"
   ```

**Acceptance:** `.cursorrules` exists at repo root, contains no dead links, and nothing in
the repo references `.cursorrules.md`.

### T0.4 — Fix stale code comments referencing files that never existed

**Files:** `apps/worker/src/worker/property_builder.py:210`,
`apps/worker/src/worker/property_tasks/property_report.py:9,16`

These reference `seller_report.jinja2`, which has never existed in this repo. It leaked in
from `docs/archive/SELLER_REPORT_INTEGRATION.md` (an architecture that never shipped).
Update the comments to name the actual template. Comment-only change — no logic.

**Acceptance:** `git grep -n "seller_report" apps/` returns nothing, or only genuine hits
you can justify.

**→ PR: `chore/p0-security-tooling`. Merge before Phase 1.**

---

## Phase 1 — Docs Purge

**Branch:** `chore/p1-docs-purge`
**Depends on:** Phase 0 merged
**Nature:** deletions and link repair only. **Zero code changes. Zero doc rewrites.**
**Estimated size:** large diff, low risk

Rewriting docs is Phase 6 and is deferred. This phase only removes what is actively
lying and makes the survivors honest about their own uncertainty.

### T1.1 — Execute the kill list

Run the kill list exactly as written in `DOCS_AUDIT_2026-08-17.md` §5 — 24 files.
Do not add to it. Do not subtract from it. Do not open the files first (several are large;
one is 75,000 lines).

Hold back one item: `docs/architecture/WIZARD_FLOW_AND_API_CALLS.md` is deleted in T1.3,
after its correct SiteX section is salvaged.

**Acceptance:** 23 files deleted in one commit. `git status` shows deletions only.

### T1.2 — Repair every inbound reference to a deleted file

This is the part that goes wrong if rushed. Deleting a doc that six other docs link to
just moves the rot.

For each deleted filename:
```bash
git grep -n "<filename>" -- '*.md' '*.py' '*.ts' '*.tsx' '*.json' | grep -v node_modules
```

For each hit: remove the link, or repoint it to a surviving doc if an obvious equivalent
exists. Do not leave a bare filename in prose where a link used to be.

Known inbound references to expect: `README.md`, `docs/architecture/INDEX.md`,
`docs/architecture/SOURCE_OF_TRUTH.md` §13 index, `.cursorrules`.

**Acceptance:** for every deleted file, `git grep -n "<filename>"` returns zero hits.
Show the verification output for all 23.

### T1.3 — Salvage SiteX, then delete the duplicate wizard doc

**Files:** `docs/architecture/WIZARD_FLOW_AND_API_CALLS.md` (source),
`docs/architecture/WIZARD_AND_API_CALLS.md` (target)

`WIZARD_AND_API_CALLS.md` has a fabricated SiteX section (wrong host, wrong token path,
wrong search path, wrong params, wrong exception name). `WIZARD_FLOW_AND_API_CALLS.md` has
the correct one.

1. Copy the SiteX section and the env-var table from the source into the target,
   replacing the target's fabricated section.
2. Verify the copied section against `apps/api/src/api/services/sitex.py:39,46,50` before
   committing. The salvaged section is only correct if the code still agrees.
3. Delete the source file.
4. Fix the target's other two hard errors while you are in it: property wizard has **4**
   steps, not 5; remove the documented `POST /reports/{id}/generate` route, which does not
   exist.

**Acceptance:** one wizard doc remains. Its SiteX section matches `sitex.py`. Cite the
lines you verified against.

### T1.4 — Commit the audit itself as the current record

Copy `DOCS_AUDIT_2026-08-17.md` to `docs/DOCS_AUDIT_2026-08-17.md` and commit it.

Until Phase 6 lands, this report is the single most accurate description of the system in
existence. It should be in the repo, and it should be the first thing a new agent reads.

**Acceptance:** file committed; `README.md` links to it (link added in T1.5).

### T1.5 — Staleness banners on every surviving doc

Every doc the audit marked **REWRITE** stays for now — but it must stop presenting itself
as trustworthy. Insert this banner immediately after the H1 of each surviving REWRITE doc:

```markdown
> ⚠️ **PARTIALLY FALSIFIED.** Audited 2026-08-17 against HEAD `f854ed6`; known-false
> claims are catalogued in [`docs/DOCS_AUDIT_2026-08-17.md`](../DOCS_AUDIT_2026-08-17.md).
> **All counts and line numbers in this file are unreliable — verify against code.**
> Behavioural descriptions are more trustworthy than inventories, but neither is
> guaranteed. Do not cite this document as evidence.
```

Apply to (from the audit's verdict table): `INDEX.md`, `SOURCE_OF_TRUTH.md`,
`WIZARD_AND_API_CALLS.md`, `backend-core.md`, `backend-routes.md`, `backend-services.md`,
`frontend-core.md`, `frontend-pages.md`, `property-type-data-contract.md`, and every
`modules/*.md` marked REWRITE, plus `README.md`, `LOCAL_SETUP_GUIDE.md`, and the
`.cursor/rules/skills/references/*.md` marked REWRITE.

Also add to `README.md`: a line directing readers to the audit as the current source of
truth for what is and is not accurate.

**Why this and not a rewrite:** an agent that knows a doc is unreliable spends one grep
verifying a claim. An agent that trusts a wrong doc spends a whole context window building
on it. The banner captures most of the value of a rewrite for 2% of the effort, and it
buys the time to defer Phase 6 past the sales motion.

**Acceptance:** every surviving REWRITE doc carries the banner. No KEEP doc carries it.

**→ PR: `chore/p1-docs-purge`.**

---

## Phase 2 — Billing Truth Chain

**Branch:** `fix/p2-plan-limits-truth` (investigation happens on this branch, no commits
until after the [JERRY] gate)
**Depends on:** Phase 0 merged. Independent of Phase 1.
**Estimated size:** unknown until T2.1 completes — that is the point of T2.1

The marketing page and the database disagree about what customers are buying. Chrome saw
Growth $19 = 25 reports/month; migration `0051_per_product_limits.sql:11-19` sets
`pro` = 99999. The audit could not find the prices `$19`/`$29` anywhere in the repo.
This is a correctness problem wearing a copy problem's clothes, and every Phase 3 pricing
fix depends on the answer.

### T2.1 — Map the full chain. Investigation only. No code changes.

Produce this table, one row per plan that exists anywhere in the system:

| Display name (UI) | Slug (DB) | Price shown | Stripe price ID | `market_reports_limit` | `schedules_limit` | `property_reports_per_month` | Enforced at (`file:line`) |
|---|---|---|---|---|---|---|---|

Sources to check, in this order:
1. `db/migrations/0051_per_product_limits.sql` and `db/migrations/0047_*` — the limit values
2. The `plans` table definition and any seed data
3. `apps/api/src/api/services/plan_lookup.py`, `billing_state.py`, `usage.py`
4. Every enforcement call site: `grep -rn "check_usage_limit\|market_reports_limit\|schedules_limit" apps/`
5. Frontend pricing components — where do the `$19` / `$29` / "25/mo" / "Unlimited"
   strings actually live? Are they hardcoded in TSX, or read from the API?
6. `grep -rn "STRIPE_PRICE" apps/ .env.example` — which price IDs exist, and do they map
   to slugs?

Answer these explicitly:
- **Which slug does the UI's "Growth" map to?** (`starter`? `pro`? Something else?)
- **What are `starter` and `solo`?** The audit found both slugs exist and no doc lists them.
- Are the displayed limits read from the DB, or hardcoded in the frontend?
- Is there **any** code path that enforces a 25-report cap? If not, the pricing page is
  advertising a restriction that does not exist.
- Is there **any** trial-expiry mechanism — a `trial_ends_at`, a scheduled downgrade, a
  cron? The Chrome audit found "14-day free trial" copy alongside a permanent $0 tier.
  The audit found no trial mechanism. Confirm or refute.

**Acceptance:** the completed table plus answers to all five questions, each with
`file:line` evidence. Where the answer is "no such code exists," say so and show the grep
that proves it.

### T2.2 — **[JERRY] DECISION GATE. STOP HERE.**

Present T2.1's findings and ask:
1. Is Free permanent, or is it a trial? (The code appears to say permanent — no expiry
   mechanism found. Confirm before Phase 3 rewrites the copy.)
2. What are the intended limits per tier, in plain numbers?
3. Which side is wrong — the pricing page, or the database?

Do not proceed to T2.3 without answers. Do not guess. Do not pick "whatever the code
currently does" as a default — the code may be the bug.

### T2.3 — Reconcile

Written after T2.2. Fix whichever side Jerry says is wrong. Whatever the answer, the
outcome must satisfy: **the number shown on the pricing page is the number the system
enforces**, and there is exactly one place in the codebase where that number lives.

If the frontend hardcodes limits, this ticket includes making it read from the plan
catalog API.

**Acceptance:** a test or a script that asserts displayed limit == enforced limit for
every plan. Not optional — this is the class of bug that silently returns.

**→ PR: `fix/p2-plan-limits-truth`.**

---

## Phase 3 — Marketing Trust Fixes

**Branch:** `fix/p3-marketing-truth`
**Depends on:** Phase 2 T2.2 answered (T3.1 and T3.2 need the decision)
**Estimated size:** medium, many small files

Ordered by damage. Everything here is a reason a real estate agent decides you are not
serious.

### T3.1 — Resolve free-tier vs. trial across all surfaces

**Findings:** Chrome #1 (BLOCKER)
**Files:** landing hero, pricing section, `/register` copy, `/terms` §4

Per T2.2's answer, make all four surfaces say the same thing. If Free is permanent: remove
every instance of "14-day free trial" and rewrite Terms §4, which currently says the
opposite of the pricing table. If it is a trial: delete the $0 tier.

```bash
grep -rn "14-day\|free trial\|14 day" apps/web/ | grep -v node_modules
```

**Acceptance:** grep for "trial" across `apps/web/` returns only intentional, consistent
usage. Terms §4 agrees with the pricing table. Quote both in the review block.

### T3.2 — Fix the "Unlimited" claim on `/register`

**Findings:** Chrome #2
**Files:** `apps/web/app/register/page.tsx`

Benefit list promises "Unlimited market reports from live MLS data" on a page whose
pricing caps Free at 3/mo. Scope the claim to the tier that actually delivers it, or drop
the qualifier.

### T3.3 — One social proof number, or none

**Findings:** Chrome #3, #4
**Files:** `/register` ("4.9/5 from 500+ agents"), `/login` ("TRUSTED BY 2,000+ AGENTS")

Two adjacent funnel pages give different headcounts, neither sourced. Worse: the avatar
initials on `/register` (SJ, MC, LP, DR, AW) are the exact initials of the fake demo
contacts on the homepage — the social proof is the seed data.

**[JERRY]** What is the real number, if any? If there is not a verifiable one, the correct
fix is removal, not a smaller invented number. Ask, then execute.

**Acceptance:** one figure sitewide or zero. Avatar initials no longer match any seed
contact. `grep -rn "500+\|2,000+\|4.9/5" apps/web/` returns only what survives.

### T3.4 — Single fixture file for all demo data

**Findings:** Chrome #5, #13
**Files:** all marketing components rendering mock reports/contacts/metrics

The homepage prices Irvine at both **$485,000** (hero: 1,247 active / 28 DOM) and **$1.2M**
("Live Preview": 847 active / 24 DOM). Demo dates read January and March 2026; today is
August.

1. Create one fixture module — e.g. `apps/web/lib/demo-data.ts` — as the single source for
   every mock number, city, and date on the marketing site.
2. Every marketing component imports from it. No inline mock values anywhere.
3. Dates generate relative to `now` (e.g. "last month"), never hardcoded.
4. All cities remain SoCal/CRMLS-valid. The Chrome audit confirmed Austin was already
   scrubbed — do not reintroduce non-CRMLS cities.

**Why a fixture and not a find-replace:** the numbers diverged because they live in five
places. Fixing the values without fixing the structure guarantees they diverge again.

**Acceptance:** `grep -rn "485,000\|1.2M\|1,247\|847" apps/web/components/` returns hits
only inside the fixture file. Every Irvine figure sitewide is internally consistent.

### T3.5 — Fictional brokerages for fictional agents

**Findings:** Chrome #12
**Files:** the T3.4 fixture

"Sarah Johnson" is credited to "Compass Real Estate" in one card and "Compass Realty" in
another — an invented person attached to a real brokerage, named two ways. That is
trademark exposure, and any agent recognizes Compass instantly.

Replace all real brokerage names with clearly fictional ones (Harbor Point Realty,
Cypress & Vine Properties). Verify the replacements are not real firms:
```bash
grep -rn "Compass\|Coldwell\|Century 21\|Keller Williams\|RE/MAX\|Sotheby\|eXp\|Douglas Elliman" apps/web/ | grep -v node_modules
```

**Acceptance:** zero real brokerage names in marketing surfaces. Fixture is the only home
for the fictional ones.

### T3.6 — Real company identity on legal pages

**Findings:** Chrome #6
**Files:** `/privacy`, `/terms`, `/security`

Address reads "123 Market Street, San Francisco, CA 94103"; phone "(415) 555-1234". Both
are placeholders, on the exact pages a title company reads during vendor diligence.

**[JERRY]** Provide the real registered business address. If there is no business phone,
omit the phone field entirely — an omitted phone is neutral, a fake one is disqualifying.

Do not ship a substitute placeholder. If Jerry has not answered, leave this ticket open and
note it in the PR.

### T3.7 — Shared layout across marketing and legal pages

**Findings:** Chrome #9, #10
**Files:** `/privacy`, `/terms`, `/security`, marketing layout

Legal pages use a completely different header, nav, footer, and tagline than the landing
page (landing: How It Works / Reports / Lead Capture / Contacts / Pricing / Log in; legal:
Product / Pricing / Contact / Sign in). It reads as a different company's site, and there
is no route back to the landing page's sections.

Extract the marketing header/footer into a shared layout component and apply it to all
three legal pages. Also fix the duplicated brand in `<title>` ("Privacy Policy |
TrendyReports | TrendyReports") — the template appends the suffix twice.

**Acceptance:** one header component, one footer component, used by landing and legal
routes. All three legal page titles render the brand once.

### T3.8 — Kill the mailto-as-navigation pattern

**Findings:** Chrome #8
**Files:** footer components

"Partners," "Press," and "Support" are nav links that open a blank email client. A Company
section where every link is a mailto reads as a site with no company behind it.

Reduce the footer to links that resolve to real pages. Move support to a single labelled
contact line rather than three nav entries. (Do not build Partners/Press pages — deleting
the headings is the correct fix.)

`/for-title-companies` is excluded here — it is Phase 4.

### T3.9 — Branded 404

**Findings:** Chrome #16
**Files:** `apps/web/app/not-found.tsx`

Current 404 inherits the homepage title and offers no nav, no search, no link home — a
terminal dead end reachable from the footer. Add the shared header from T3.7, a plain
message, and a primary CTA back to the landing page.

### T3.10 — Login page stat tile

**Findings:** Chrome #11
**Files:** `apps/web/app/login/page.tsx`

Reads "Reliable / Uptime" where a number belongs, sitting between "7 / Report types" and
"50K+ / Emails sent." Either publish a real uptime figure or drop the tile.

Note: the "7 / Report types" figure is **correct** — 8 slugs exist, `open_houses` is
disabled in the wizard, user-facing is 7. Leave it alone. Verify "50K+ emails sent" is
real; if it is not, remove it under the same rule as T3.3.

### T3.11 — Explain the paid-tier differentiators

**Findings:** Chrome #14
**Files:** pricing component

"AI Market Insights," "Priority Generation," and "CMA Lead Page" appear as tier
differentiators with no definition, no tooltip, no anchor. Two of the three upgrade
reasons therefore do not land. Add tooltips or short inline descriptions.

### T3.12 — Drop the "with email" qualifier

**Findings:** Chrome #15
**Files:** `/register`, `/login`

"Register with email" / "Sign in with email" implies alternatives that do not exist. Drop
the qualifier until SSO ships.

**→ PR: `fix/p3-marketing-truth`. Run the full frontend build and test suite before opening.**

---

## Phase 4 — Title Companies Page

**Branch:** `feat/p4-title-companies`
**Depends on:** Phase 3 T3.7 merged (needs the shared layout)
**Estimated size:** medium

**Findings:** Chrome #7

`/for-title-companies` 404s. The footer links to it. The on-page CTA is a mailto. An entire
named revenue channel — one of your three — has no page, and the only path a title company
has to reach you is a blank email client with no context.

### T4.1 — **[JERRY] Content gate. Ask before building.**

This page cannot be written from the codebase. Required before any implementation:
1. What does a title company actually buy — sponsored agent seats, white-label branding,
   co-branded reports? Which of these ships today?
2. Pricing model for this channel, or "contact us"?
3. What is the conversion action — demo request form, calendar link, phone?
4. Is there a real title company relationship to reference? (The Chrome audit found the
   `/app` session authenticated as **Pacific Coast Title Company, TITLE REP role** — is
   that a demo fixture or a live account?)

Do not write placeholder marketing copy. Placeholder copy on this page is worse than the
404, because a 404 does not make a claim.

### T4.2 — Build the route

Once T4.1 is answered: build `/for-title-companies` using the shared layout from T3.7,
with a real conversion action (form or booking link) rather than a mailto. Repoint the
footer link and the on-page CTA.

**Acceptance:** the route renders, the footer link resolves, no mailto remains as the
primary CTA for this segment.

**→ PR: `feat/p4-title-companies`.**

---

## Phase 5 — Funnel Verification

**Branch:** `test/p5-funnel-verification`
**Depends on:** Phase 3 merged
**Estimated size:** medium

The Chrome audit could not test routes 3–6: registration submit, email verification,
onboarding, and `/app` first-run. The docs audit independently found onboarding to be
coverage gap #2 — **no documentation anywhere**, shipped after the docs froze.

So the single path every paying customer must walk is simultaneously untested by the UX
audit and undocumented in the repo. That is the highest-risk surface in this plan.

### T5.1 — Make the funnel testable

Write a seed/teardown script that provisions a throwaway account at a known state
(pre-verification, post-verification, mid-onboarding) for each of the five account types:
`REGULAR`, `INDUSTRY_AFFILIATE`, `TITLE_COMPANY`, `COMPANY_REP`, `SPONSORED`.

**Acceptance:** one command creates a testable account per type; one command removes them.

### T5.2 — Walk and document the flow

For each account type, walk registration → verification → onboarding → first `/app` load.
Record, per step: what the user sees, what is required, what breaks, what is confusing,
what has no empty state.

Output `docs/architecture/onboarding.md` — behavioural description only, **no counts, no
line numbers** (see Phase 6 rationale). This closes the audit's coverage gap #2 with a doc
built from observed behaviour rather than from reading code.

**Acceptance:** the doc exists; every claim in it came from an observed run.

### T5.3 — E2E spec for the critical path

Add a Playwright spec covering register → verify → onboarding complete → dashboard, for
`REGULAR` at minimum. Note that `test-suite.md` is wrong about the Playwright config —
verify against `playwright.config.ts` directly.

### T5.4 — Responsive fix below 1280px

**Findings:** Chrome #17

At 1142px the dashboard clips horizontally; the "Bulk Import" button and the user menu are
cut off. Any laptop at ~1280px or any split window loses controls. Audit the `/app` shell
at 1024 / 1142 / 1280 and fix.

Note: Chrome observed this on an authenticated Title Rep session, so it is not evidence
about other tiers. Check at least Agent and Title Rep.

**→ PR: `test/p5-funnel-verification`.**

---

## Phase 6 — Docs Rebuild (DEFERRED)

**Do not start this phase without explicit instruction from Jerry.**

The audit proposes a consolidated 13-file doc set. It is the right target. It is also a
week of work whose only customer is a coding agent, and Phase 1's staleness banners capture
most of the safety benefit at a fraction of the cost.

Recorded here so it is not lost:

1. **Ban the rot before rewriting.** Two-thirds of the audit's falsified claims are counts
   or line numbers, and every single cross-doc contradiction in §2.2 is a count. Rewriting
   without changing the rules regenerates the same problem in six months. New standard:
   - No counts in prose. Ever.
   - No line numbers. Cite `file.py::symbol_name` — symbols survive refactors; line 823
     does not.
   - Anything countable is emitted by `make docs-stats` at read time, never typed by hand.
   - Docs describe **contracts and behaviour**, not inventory.
2. Build `scripts/docs_stats.py` first, before writing a single doc.
3. Then merge into the audit's §4 target set.
4. Write new-subsystem docs (company portal, onboarding, per-product limits, the second
   `/admin` tree, the second migrations directory at `apps/api/migrations/`) as sections
   of `backend.md` / `frontend.md`, not as new files.

**Sequencing note:** this phase runs after the sales motion is underway, not before.

---

## Definition of Done

The remediation is complete when all of the following are true:

- [ ] SiteX credentials rotated at the vendor and absent from the working tree
- [ ] `.cursorrules` loads; every agent doc it references exists
- [ ] Every file on the kill list is gone; zero dead references remain
- [ ] Every surviving REWRITE doc carries a staleness banner
- [ ] The number on the pricing page is the number the system enforces, asserted by a test
- [ ] Free-vs-trial says the same thing on the hero, pricing table, `/register`, and Terms
- [ ] Every demo number on the marketing site comes from one fixture file
- [ ] Zero real brokerage names attached to fictional people
- [ ] Real business address on the legal pages
- [ ] `/for-title-companies` resolves to a real page with a real conversion action
- [ ] Registration → verification → onboarding → dashboard is documented and E2E-tested
- [ ] `/app` does not clip at 1142px

**Explicitly out of scope:** the docs rebuild (Phase 6), dead-code removal
(`v0-report-builder/`, `lib/templates.ts`, legacy `trendy-*.html`, `/print/[runId]`), git
history rewriting, and every "worth revisiting" note either audit filed. Those go to
`FINDINGS.md` and stay there.

---

## Phase Summary

| Phase | Branch | Depends on | Gate |
|---|---|---|---|
| 0 | `chore/p0-security-tooling` | — | Blocks everything |
| 1 | `chore/p1-docs-purge` | P0 | — |
| 2 | `fix/p2-plan-limits-truth` | P0 | **[JERRY]** at T2.2 |
| 3 | `fix/p3-marketing-truth` | P2 T2.2 | **[JERRY]** at T3.3, T3.6 |
| 4 | `feat/p4-title-companies` | P3 T3.7 | **[JERRY]** at T4.1 |
| 5 | `test/p5-funnel-verification` | P3 | — |
| 6 | deferred | — | Do not start |

Phases 1 and 2 can run in parallel after Phase 0 merges. Everything else is sequential.
