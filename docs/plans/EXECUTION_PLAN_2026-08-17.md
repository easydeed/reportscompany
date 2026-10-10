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

  **AND A SUBSTRING IS NOT A CONSTRUCT.** *Added 2026-09-25, from three false positives in a
  single session, all the same shape — a token matched inside a longer token:*

  | the check | what it hit instead |
  |---|---|
  | `"height:" in rule` | `line-height:`, which every text rule has |
  | `"more-listings-note" not in html` | the `.more-listings-note` CSS rule in the stylesheet |
  | `"masthead" not in header_template` | the comment explaining why the masthead is not in it |

  Every one of them failed *safe* — the assertion fired and the build went red — so each cost
  minutes rather than shipping. That is luck about which direction the mistake ran, not a
  property of the method: the same match written as a positive assertion (`assert "height:" in
  rule`) passes forever on `line-height:` and guards nothing at all.

  **Match the thing, not text that contains the thing.** A CSS declaration is `(?:^|[;{])\s*prop
  \s*:`, not `prop:`. Markup is `class="name"` or an attribute, not the bare class name, which
  also occurs in the stylesheet and in prose. A Python symbol is a `def`/`class`/import or an AST
  node, not an identifier that is also a substring of six others. A config key is the parsed
  value, not a line that mentions it.

  The tell is that the needle would still match if the surrounding characters were anything at
  all. When a real parser is available — an AST, a CSS parser, an HTML parser, the config
  loader — use it; text search is the fallback, and its needle has to carry its own boundaries.

  **AND THE HONEST PART: THIS RULE HAS NOW BEEN BROKEN FOUR TIMES BY THE PERSON WHO FILED IT, AND
  CAUGHT FOUR TIMES BY A REGRESSION RATHER THAN BY RECALL.** A fourth instance landed three days
  after the rule was written — `force-new-page`, matched in the stylesheet instead of the markup —
  in a test written by someone who had the rule in mind that week.

  Read as a scorecard that looks like a dead rule. It is not, and the distinction matters for
  anyone deciding whether to keep it: **this class is not preventable prospectively.** At the
  moment of writing `"height:" in rule` or `"force-new-page" not in html`, the needle IS the
  intent — the mistake is invisible from inside the sentence that expresses it, in the same way
  `minimum - 1` is the natural way to say "below the minimum". Every one of the four was obvious
  within seconds of seeing it fail and invisible while being written.

  So the rule's job is not to stop the hand. It is to make the failure legible when the regression
  produces it — to turn "why is this test red" into "ah, the substring" in one step instead of ten
  — and the thing that actually catches it is **running the check against input you know is bad**.
  A rule that can only be applied in hindsight is an argument for the regression discipline, not
  evidence against itself. Keep both; expect the fifth.

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

  *Recurred the same day, in tests written after this rule was filed.* The §7.3 trend chart gates a
  minimum sample per month, and its tests built fixtures of `MIN_CLOSED_FOR_MEDIAN - 1` and
  `MIN_CLOSED_FOR_MEDIAN` closings. Lowering the threshold from 3 to 1 moved both fixtures with it;
  the suite stayed green and the regression was MISSED. Knowing the rule did not prevent writing
  the shape, because the shape is what expressing the intent naturally produces — "a month below
  the minimum" is most directly written as `minimum - 1`. **Treat the rule as something to check
  for after writing a test, not only as something to remember while writing one**: after each new
  gate, look at where its expected value came from, and if the answer is "the code", change it or
  run the regression that proves otherwise.

- **When you measure a thing made of parts, enumerate the parts that are there. Do not write down
  the list you expect and measure that.**

  *Added 2026-09-25 from Workstream D.* A page-1 budget was needed: what occupies the first page of
  a market report, and what each piece costs in vertical space. The measurement walked a
  hand-written list of selectors — masthead, metric tiles, narrative, heading, note — and reported
  4.73in used with 4.94in free. **The list had missed `.stats-bar`, the tallest block on the
  page.** The real figures are 7.15in used and 2.52in free, which is the difference between "page 1
  has room to spare" and "page 1 misses its next row by a quarter of an inch".

  It was caught, and it was caught by luck rather than by a check: the wrong numbers said 4.94in
  free against a 2.69in card, which should have fitted, while the paginator had already reported
  zero cards on that page. The contradiction was visible only because both numbers happened to be
  in front of me at once. Had the missing block been shorter, the sum would have been merely wrong.

  **The fix is the method, not more care.** Walk the container's children in document order and
  report every one of them, including the ones you did not predict; let anything unrecognised
  appear as an unnamed row rather than vanish. A selector list encodes a belief about what is on the
  page. The DOM is the page. This is the same shape as writing the block map by reading the
  builders, and as reading `ENV_TEMPLATE.md` for a runtime fact: **an inventory assembled from
  memory is a hypothesis wearing the costume of a measurement**, and it is worse than an obviously
  partial one, because it looks complete.

  Where enumeration is genuinely impossible, make the total falsifiable instead: measure the parts
  AND the whole independently and assert they agree. A sum that must equal a separately measured
  container catches a missing part by itself, without depending on a second number happening to
  contradict it.

- **A distinction you drew in one place does not propagate to the next place by having been
  written down. When you make a semantic call, grep for the shape and check every other site.**

  *Added 2026-09-28 from Workstream D.* The trend chart draws a careful line between two kinds of
  absence: a month with no closings is a **gap** in a median series, because the median of nothing
  is not a quantity, and a **real zero** in a count series, because "no homes sold" is a fact about
  the month. That distinction was reasoned about, written into the module docstring, asserted in
  two tests, and described in a commit message.

  Days later the band chart was written with `bands | selectattr('count')`, which silently drops a
  band with zero listings — the same mistake, one macro down the same file, by the same hand, with
  the rule still on screen. "Nothing is for sale above $1.6M" is a fact about the market and one of
  the more useful things on that page.

  **This is the fifth or sixth instance of the pattern**, not the first: the caps read from the
  config they were testing, `minimum - 1`, the substring matches, the hand-written element list,
  the sweep that examined 10 of its 22 reads. Each time the general lesson had already been
  written down, and each time it was rediscovered locally rather than applied.

  **Why writing it down does not work, and what does.** A rule is recalled when something cues it,
  and the cue for "is this absence a gap or a zero?" is *thinking about absence* — which is exactly
  what you are not doing while writing a filter that reads as "the bands that have counts". The
  knowledge is indexed under the concept and the mistake occurs under the syntax.

  So index it under the syntax. **When a semantic call is made about absence, ordering, rounding,
  or units, grep for the construct that encodes it** — `selectattr`, `if x:` on a numeric,
  `or` as a default, `filter(None, …)` — across the module and its siblings, and check each hit
  against the same question. Minutes, and it transfers the decision to every site at once instead
  of waiting for each to be rediscovered.

  The corollary for review: a commit that establishes a distinction should say where else the shape
  appears and that those were checked, in the same way a commit that fixes a defect names the
  regression. "Fixed here" invites the next instance; "checked the other four" closes them.

  *Run against itself the same day.* Grepping the market macros for the shape took under a minute
  and found the same call in a third syntax — Jinja's `{% if x %}` is falsy for `0`, so
  `{% if listing.beds %}` hides the bed count on a **studio**, and `{% if stats.avg_dom %}` hides
  Avg DOM at zero, which D-105 has just made reachable. Filed as **D-108**. Two `selectattr` sites
  existed and both were already correct; the defect had moved syntax, which is exactly what
  searching for the concept rather than the string is for.

  *Run against itself again, 2026-09-28, and this time the rule was right and the search was not.*
  The paragraph above names four constructs — `selectattr`, `if x:` on a numeric, `or` as a
  default, `filter(None, …)`. The sweep that closed D-108 covered the **Jinja** ones and stopped
  at the language boundary, and the write-up said "every conditional in every template" and meant
  it. Finishing the fix found the other two waiting in Python: six `a.get(k) or b.get(k, 0)`
  chains in the builder, which collapsed a real 0 and a missing value into the same 0 — so the
  template fix, applied alone, would have rendered **"Studio" over missing data** — and nine
  comprehension filters, `[l["days_on_market"] for l in closed if l.get("days_on_market")]`,
  each excluding same-day sales from the average of how fast sales happen.

  **So the addendum is about scope, not about the rule: a construct search is bounded by the
  language you happen to be reading when the thought occurs.** The concept crosses languages in a
  way that no single grep does, and the sweep that names its own completeness ("every conditional
  in every template") is the one that has already fixed its boundary at the wrong place. State the
  boundary out loud — *templates only, Python not yet searched* — because an unstated boundary
  reads as none.

  **And the second half, which nothing in §0.6 said yet: fixing a defect can turn one on
  elsewhere.** The nine DOM filters had been harmless for as long as the extractor computed
  `close − list`, which is 0 only for a same-day close. D-105 changed the read to the feed's own
  `daysOnMarket`, which is 0 for anything that goes under contract on its listing day — and nine
  correct-looking statistics started dropping their fastest observations, in a different file,
  with nothing linking the two changes. **A fix's blast radius includes every place that was
  correct only because the value it mishandles never occurred.** Grepping for the *value that
  became reachable*, not only for the code that was edited, is what would have caught it — and is
  now what the D-108 gate does automatically, in both languages, for every numeric the builders
  emit.

- **A TEST THAT SUPPLIES ITS OWN INPUT PROVES THE CONSUMER AND SAYS NOTHING ABOUT THE PRODUCER.** A category, not an instance — every fixture-fed test in this repository has this shape, and each one is silent about the same half. Found 2026-09-29:
  §7.3's twelve-month trend chart has never rendered in a customer's report. It reads
  `report_data["closed_history"]`, and **nothing on the production path writes that key** — no
  builder emits it and `tasks.py` never adds it, so the guard returns None on every render
  (D-113). The feature was designed, built, tested, measured, pinned into `PAGE_1_CAPACITY`, and
  argued over in D-102's page-1 decision, and it does not run.

  **Every test of it supplies `closed_history` itself**, which is correct for a unit test: it
  proves the chart draws properly from data it is handed. It says nothing about whether it is
  ever handed any, and neither did anything else. Even the pagination measurements were taken in
  a state production does not reach, because the measuring script sets the key too.

  The shape is invisible from both ends. **A reader with a graceful fallback looks careful; a
  missing producer looks like nothing at all.** Neither side announces itself, and no
  value-level test can see the gap because the gap is that no value ever arrives.

  So the check is structural and compares the two sets rather than testing either:
  `test_render_context_contract.py` parses every `report_data.get("k")` the builder makes and
  every key the producing modules write, and fails on a read with no writer. It rediscovered
  D-113's two keys on its first run and found no others. **Marked `xfail(strict=True)` rather
  than deleted**, so the known failure cannot become a permanent one: fixing D-113 turns it XPASS
  and fails until the marker goes.

  **The category, stated so it applies past this key.** Unit tests are supposed to supply their
  inputs; that is what makes them unit tests, and none of them is wrong. What is missing is that
  *nothing else* was checking the other side, so the suite's coverage of the feature and the
  suite's coverage of the pipeline looked like the same thing. **Wherever a consumer degrades
  quietly on a missing input, the assertion that the input arrives has to live outside the tests
  of that consumer** — they are precisely the ones that cannot make it.

  Three symptoms to search for, because the shape is recognisable before it bites:

  - a reader with a `if not x: return <empty>` guard and no caller-side test;
  - a fixture or measuring script that sets a key the production path does not;
  - a decision taken on a measurement whose inputs the measurer provided. **D-102 was one.**
    Its numbers were real and its conclusion holds, and it was still reached on evidence that
    was not describing the product. "The measurement was right" and "the measurement was of the
    thing being decided" are different claims, and only the second was ever in doubt.

  The remedy is the contract gate: assert that something *writes* what something else *reads*,
  by parsing both sides. It generalises past this one key and past this one pair of modules, and
  it is cheap — the whole check is one AST walk over each side.

- **SUPERFICIAL SYMMETRY: two call sites that read the same data, with what looks like the same
  guard need, until you check what each DOES with a row.** Named 2026-09-29 after nearly adding
  a defensive filter that could not have helped.

  `compute/moi.py` re-filters its closed rows on `close_date` client-side even though the query
  already asked the vendor to, and says so in its docstring: the parameter's behaviour is not
  fully confirmed, so the number is right under either answer. When the trend chart started
  reading the same rows from the same fetch, copying that filter looked obviously correct — same
  data, same vendor uncertainty, same defensive posture, and the argument for it was made twice
  before anyone checked.

  **It would have done nothing.** `moi` **counts** rows to derive a sales rate, so one extra row
  is one extra sale and the filter is load-bearing. The trend **looks up** twelve month-buckets
  by key, so a row outside the window is never read — measured: five years of closings produce a
  series identical to one year's. And it could not have helped with the real failure either,
  because that is truncation at fetch time: filtering the rows that came back does not restore
  the ones that did not.

  The tell is that the shared thing was the INPUT and the differing thing was the OPERATION. Two
  consumers of one dataset inherit each other's guards only where they consume it the same way,
  and "reads the same rows" is not that. **Ask what a wrong extra row would do to each caller's
  output** — if the answers differ, the guards are not transferable, however alike the callers
  look.

  The same shape sits behind three entries above: the `selectattr` that dropped zeros mattered
  where the zeros were counted and not where they were looked up; `is not none` on a chip and on
  a divisor are different decisions; and a fixed accent readable on a theme's navy is not
  readable on an affiliate's brand. **Same value, different consumer, different obligation.**

- **A gate that mirrors the code instead of importing it reports green while guarding
  nothing.** *Added 2026-09-30, from D-140.* The parity test for D-139's worst site restated
  `tasks.py`'s `report_data` literal, because the literal lived inside a Celery task with
  nothing importable. Editing the task without editing the test would have left the gate
  passing. D-139's own regression run only failed because both copies were changed by hand,
  which is not a property a gate can rely on.

  **If the thing under guard cannot be imported, that is the finding** — extract it, and check
  first whether the extraction is actually hard. Here the DB access surrounded the literal
  rather than running through it, so every input was already a local and the function came out
  pure. The ticket was small because the shape was; assuming otherwise is how a mirror gets
  written instead.

  Prove a refactor equivalent rather than asserting it: the pre-change literal came out of
  `git show HEAD:…` into a callable and ran against the new function on 300 randomised inputs,
  every value distinct so no two fields could agree by coincidence.

  **Expect the extraction to find something.** Feeding the gate the real producer immediately
  exposed four fields both fixtures had left blank, which the parity test had been comparing
  as equal — and a sibling test pinned to `tasks.py` **by filename**, which a legitimate move
  broke while changing nothing about the value it guards.

- **A shape retyped by hand is a place that drops fields, and it never says so.** *Added
  2026-09-30, from D-138 and D-139.* The consumer CMA path restates `PropertyData` three times —
  a projection model, a request payload, and a dict literal in the worker. Each is a list of
  field names somebody wrote out. Nine fields were missing across them: the whole parcel block
  blank, the whole tax block rendering `$0`. No exception, no log, no type error, on every
  consumer report ever generated.

  **The tell is that the copy typechecks.** A projection that omits a field is valid code and a
  valid response; the consumer reads `undefined`, which is indistinguishable from the field
  legitimately having no value. Optionality is correct there — a house that never sold has no
  sale price — and that correctness is what makes the omission invisible.

  So: **when a shape is retyped, diff it against its source in a test**, with an explicit
  exclusion list carrying a reason per field and a staleness check on the list. And where the
  retyping is a literal rather than a model — the case a field diff cannot see — **diff the
  rendered output of the two paths instead.** That is the only thing that caught the third
  place, where every model in the chain agreed and the worker simply did not forward what the
  row already held.

  Corollary worth stating separately, because it is now three for three: **the path with more
  retypings is the one carrying the defects.** D-116, D-138 and D-139 all broke the consumer
  funnel while the agent funnel worked — which is also why each survived review.

- **Two computations agreeing on one input is not a test.** *Added 2026-09-30.* D-118's row
  had to use SiteX's own `PricePerSQFT` rather than deriving one, because theirs is computed
  against the sqft recorded with the sale. The test asserted `piq.price_per_sqft == 469.0` —
  and `369000 / 786` also rounds to `469`. Replacing the vendor value with a derived one left
  the suite **green**: the assertion could not tell apart the two sources it existed to
  distinguish.

  The remedy is a case where the two **must** diverge, and it generalises well past ratios.
  Any test of *which* of two paths produced a value needs an input on which they disagree:
  a cache versus its source, a fallback versus its primary, a client-side filter versus the
  vendor's, a rounded figure versus an exact one. **Pick the fixture so that the wrong answer
  is a different number**, or the test only proves both paths can reach the right one.

  Sibling of the applied-regression rule. Applying the regression is what exposed this —
  the test passed with the defect installed, which is the only way to learn that an assertion
  cannot discriminate.

- **A parsed field with no consumer is the mirror of a read with no producer.** *Added
  2026-09-30, from D-138.* `last_sale_document` was parsed for one commit because the probe
  returned it and it looked useful. Nothing displayed it and nothing had asked. It is the same
  debt as D-135's nineteen reads, accruing the same way — by looking deliberate — and the same
  question answers both: **what consumes this, and when.** Delete it; the key name is recorded
  in the probe and the value is still in `raw_response`, so it costs one line to restore on the
  day something wants it.

- **A value you cannot account for is a question, not a verdict.**
  *Added 2026-09-30.* The Workstream E measurement found `$369,000` as the subject's sale price
  in Group A of the six reviewed PDFs, could not reconcile it with anything the code produces,
  and filed it among the QA script's invented literals. It was not invented. It is the real
  last recorded sale, `SaleLoanInfo.SalesPrice`, which SiteX has returned on every lookup since
  the integration was written and `_parse_response` never read. **Group A was not wrong — it was
  reading something production stopped reading.**

  The measurement was right to distrust the artefact and wrong to conclude from that distrust.
  "I cannot account for this" and "this is fabricated" are different findings, and the first
  one's correct next step is to go looking. Here the cost of not looking was three weeks of a
  Prop 13 assessment printed where a real sale price was available the whole time.

  Applies to any unexplained value in a render, a log or a fixture: **write it down as an open
  question with the number in it.** A number nobody can source is the most likely place a
  producer has quietly stopped running — which is D-113, and D-133, and this.

- **A fixture shaped like production is not the same as one production can produce.**
  *Added 2026-09-30.* The Workstream E measurement replaced a QA script's invented context with
  a production-*shaped* `report_data` and rendered through the real builder — which was the
  right move and caught seven false tickets. It then filed **D-120** on a `sitex_data["pool"]`
  value of `"None"`. No producer writes `pool` at all: neither
  `services/sitex.PropertyData.model_dump()` (28 keys) nor the wizard's payload (25). The
  `"None"` was invented by the fixture, and the entry described a state production cannot enter
  — filed by the person auditing for exactly that, two days after writing the rule about it.

  The rule above says a document rendered by something other than the production path is
  evidence about that something. **A fixture is that something too.** Shaping it correctly
  proves the consumer handles that shape; it says nothing about whether the shape occurs.

  The check is cheap and is now a test (D-135): **diff the keys the consumer reads against the
  keys the producer can emit.** On that one surface it found nineteen reads with no producer,
  and two of them assert facts rather than render dashes (D-137). Do it before writing the
  fixture, not after — a fixture is a claim about the producer, and an unchecked claim is how
  both D-113 and D-120 happened.

- **A read of an optional field is indistinguishable from a read of a field nothing writes.**
  *Added 2026-09-29, from D-118's investigation.* `dict.get(k)` returns `None` for "absent this
  time" and for "absent always", and an `or` fallback turns both into a plausible value. Three
  instances found in one afternoon, all on the property surface:
  `sitex_data["estimated_value"]` (written by nothing, so its `or assessed_value` fallback is
  the only path and the subject's *Sale Price* is a Prop 13 assessment — D-118), and
  `last_sale_date` / `last_sale_price`, read by the mobile endpoint and set by no writer
  anywhere (D-133).

  The worst version is the one with a fallback, because the fallback makes the absence
  invisible. A bare `None` renders as a gap somebody eventually asks about; `or assessed_value`
  renders as a number nobody questions.

  This is the same shape as D-113 — `closed_history` read by the builder and emitted by no
  producer — and as D-009. The check is not *does the code handle a missing value*. It is
  **what writes this, and when.** Grep for assignment before reasoning about the read, and if
  the answer is "nothing", the ticket is about the producer no matter how the consumer looks.

- **A document rendered by something other than the production path is evidence about that
  something.** *Added 2026-09-29, from the Workstream E measurement.* The E register's 22
  tickets were written from a careful review of six property PDFs. The PDFs came from
  `scripts/generate_all_property_pdfs.py`, a QA script that does not call
  `PropertyReportBuilder` at all — it carries its own copy of the Jinja filters and a 200-line
  `SAMPLE_CONTEXT` literal. Re-rendering the same five templates through the production path
  found **seven of the twenty-two do not reproduce**: the stock aerial photograph of another
  country, the placeholder street address, the six-month-stale trend date, the "Medium" column
  that is a computed median, the independently sorted rows, the phantom date row, and the
  skewed contents card were all properties of that literal or of an older artefact. An eighth
  reproduced inverted — the unreadable summary row is in two *other* themes than the one filed.

  This is not a criticism of the review, which described what it was shown accurately. It is
  about what a render licenses you to conclude. **The question to ask of any artefact before
  reasoning from it is: what code produced this, and is it the code that runs?** A screenshot,
  a sample PDF, a preview page and a fixture-driven QA render all look like the product and
  each one differs from it somewhere.

  It also cuts the other way, and that half is the more useful. Three E tickets that *were*
  real could not have been confirmed from any render: **the comp query applies no date filter**
  (D-117) is invisible in a document whose comp dates were hardcoded, and was settled by reading
  `_build_params`; **`estimated_value` is never populated anywhere** (D-118) turns a fallback
  into the only path; **the contents page is a literal block with no `page_set` guard** (D-121)
  is a property of the template, not of one output. Pair this with D-113's rule — *a test that
  supplies its own input proves the consumer and says nothing about the producer.* **Renders
  prove consumers. Producers are proved by reading the code that builds the input.**

  The corollary is a cheap habit: when a review produces a ticket list from artefacts, the first
  ticket is to reproduce the artefacts, and the tool that does it is worth committing —
  `scripts/render_property_production.py` exists so the next person re-checks in one command
  instead of trusting this one.

- **A guard asserting A ⇒ B is half a guard whenever B ⇒ A is also a claim you want to hold.**
  *Added 2026-10-01, after finding the same hole twice in one week, both times by accident
  during regression testing rather than by recall.*

  A check that compares a description against a reality has **two** failure modes, and one
  assertion covers one of them:

  | | the check catches | the check is silent on |
  |---|---|---|
  | docs table vs CI workflows (D-152) | a filter path the row omits | **a path the row claims that the filter does not carry** |
  | field-path sweep vs payload (D-106) | a key read at the wrong path | **a key read at no path that exists** |

  In both cases the silent direction is the one that *overclaims* — the document or the code
  asserting coverage that is not there — which is the direction that costs, because nobody
  goes looking for a capability they have been told they have.

  **Record how both were found, because it is the honest part.** The CI one: a stray
  `git checkout` during regression testing reverted a `tools/**` addition while the docs row
  still advertised it, and all seven tests stayed green. **The one-directional version would
  have shipped**, and would have read as a guard for as long as anybody looked at it. The
  sweep one: `bathrooms` exists at no path in any payload, so the verdict was
  *"not in fixtures"* — the tool declining to judge — which did not fail the run and did not
  appear in the count, so *"0 unacknowledged misreads"* was true and silent about the one
  defect it was taken to clear.

  This is the same family as **"a check that reports damage after committing it is
  decoration"** above, one step subtler: the check *can* fail, it simply cannot fail in the
  direction you were not thinking about when you wrote it. And it is the same family as the
  substring rule in its honesty: **not preventable prospectively.** At the moment of writing
  `assert every_filter_path_is_in_the_row`, that sentence IS the intent; the converse is not
  absent from the code so much as absent from the thought.

  So the habit is mechanical rather than attentive. **When a test compares two representations
  of one thing, write down both set differences before writing either assertion** — `A - B`
  and `B - A` — and say out loud what each one means. If only one of them has a meaning, say
  so in the test and move on. If both do, both are assertions. The tell is any comparison
  whose natural English is "X matches Y": *matches* is symmetric and the code almost never is.

- **A DERIVED SET IS ONLY AS COMPLETE AS THE INPUT IT WAS DERIVED FROM — so derive it from more
  than one.** *Added 2026-10-01, from a coverage regression caused by a correctness fix, which
  is a category that is normally invisible.*

  Deriving beats listing: `_zero_conditionals.numeric_leaf_names()` says so in its own
  docstring — *"a hand-written set of numeric-looking names is the mistake this repo keeps
  re-finding, and it goes stale the moment a builder adds a field."* That is right, and it is
  not the whole story. It derived the property half from **one** input, `PropertyReportBuilder({})`,
  on the stated premise that *"its builder fills every numeric with a default, so an empty
  input still names them all."*

  D-119 falsified that premise **on purpose and correctly**: a Low/Medium/High column with no
  listing behind it must render `-` rather than `$0`. So on an empty input `stats.low.price`
  became a string, `price` dropped out of the derived set, and two real comprehension findings
  in `tasks.py` stopped being reported. **Nothing failed. The audit simply covered less.**

  **The tell is that narrower coverage is always green.** A gate that stops looking at
  something does not go red; it goes quiet, and quiet is what everyone is hoping for. This is
  the same shape as the ratchet that absorbs an invisible pairing by regeneration (E15) and the
  sweep whose third verdict did not fail the build (D-106) — a measurement that reports less
  reads exactly like a system with less wrong with it.

  It surfaced only because `test_the_exemption_list_does_not_outlive_what_it_excused` noticed
  the now-unused `price` exemption — **the other direction of the rule above, on a case nobody
  constructed.** Without that second assertion the narrowing would have shipped.

  So: when a set is derived from a sample, the sample is part of the guard and needs the same
  scrutiny as the assertion. Derive from an empty input *and* a populated one; where the shapes
  differ meaningfully, from one of each. And when a change alters what a builder produces for
  a given input, ask what else reads that builder for its own purposes — the consumer will not
  tell you, because it will keep passing.

  **SECOND INSTANCE, THREE DAYS LATER, BY THE PERSON WHO WROTE THIS DOWN.** D-153 needed a
  colour tolerance for the contrast baseline. The gap between "same backdrop sampled twice"
  and "genuinely different backdrop" was derived from the **ten single-brand property
  renders** — 21 groups spread 1–37, 7 spread 131–614, nothing between — and **48** was
  recommended from that gap. The gate's corpus is **ninety documents across six brand
  colours**, and two of those brands are 41 apart. At 48, fourteen of 178 baseline entries
  collapse, *including every two-brand pair* — the gate losing precisely the distinction six
  brands are rendered to make. The right number, derived from the corpus the constant is
  applied to, is 12.

  Both instances are the same sentence with a different noun: a set derived from ten documents
  and used on ninety; a set derived from an empty context and used on a populated one. **The
  tell was available both times and both times I did not look for it** — the question "what is
  in the input this will be used against that is not in the input I derived from" is one
  sentence and answers it.

  Two instances in three days is the argument for the rule being mechanical rather than
  remembered: **write down what the derivation input contains and what the application input
  contains, side by side, before trusting the number.** Where they differ, the number is
  unproven.

- **THE CLOCK IS AN INPUT. A TEST THAT TAKES ONE FROM ITS FIXTURE AND ANOTHER FROM THE
  ENVIRONMENT IS TESTING NEITHER.** *Added 2026-10-01.* D-158. `test_monthly_trend.py` set
  `TODAY = date(2026, 9, 24)` and built twelve months of fixture rows back from it. Its pure
  tests passed that date in as `today=`, so those were deterministic. Its **render** tests went
  through `MarketReportBuilder`, which calls `median_series(history)` with no `today=` and
  therefore buckets against `date.today()`. Two clocks, one file.

  It was green on 30 September and red on 1 October with nothing merged in between that touches
  the chart. The oldest fixture month fell out of the trailing twelve the builder computes,
  eight rows stopped being counted, and the suite failed. **Nothing was wrong with the
  product.** The test had been counting on the calendar not moving, and it held for exactly as
  long as the fixture's window happened to contain the day the suite ran.

  The general form is the ambient-input one: the clock, the locale, the timezone, the working
  directory, the environment variable the fixture does not set. Each is read from the
  environment by the code under test and written down by hand in the fixture, and a test that
  does both is asserting that those two happen to agree today. **Either inject it into the code
  under test or take it from the environment in the fixture — one clock, not two.** Freezing it
  is the better answer only when the code already accepts an injected one; adding that
  parameter *for a test* is product surface bought with a test's convenience.

- **A TEST THAT WRITES ITS EXPECTED VALUE DOWN BY HAND CANNOT SAY WHY IT FAILED.** *Added
  2026-10-01.* The mirror image of the older rule, and the second half of D-158. "A test that
  reads its expected value from the thing under test cannot fail" — so write it down. But the
  assertion in D-158 was `assert "96 sales" in html`, where 96 is 12 × 8, a property of the
  **fixture**. When it broke it reported *the note is wrong*, which was the opposite of what
  happened: the note was right and eight sales had gone missing before it reached the note.
  Half an hour went into the wrong half of the pipeline.

  The distinction is not "literal versus derived" — it is **which side you derive from.**
  Derive the expectation from the INPUT and it both survives a fixture change and names the
  real failure (`f"{len(rows):,} sales"` says *rows were dropped*). Derive it from the CODE
  UNDER TEST and it cannot fail. Writing it down by hand is the third option and it is only
  right for things that are genuinely constants of the decision — a threshold somebody chose,
  the shape of the fixture itself — not for arithmetic over the input.

- **A FINDING IS NOT NEW UNTIL YOU HAVE LOOKED FOR IT IN THE RECORD.** *Added 2026-10-01.*
  D-160. Scoping D-159's template gate meant deciding whether to cover the property templates
  nothing renders. That decision rediscovered them, and I wrote the rediscovery up as a new
  defect — with a line count, a table and an argument — against a board that had carried
  **D-131, "five unreachable copies of the property templates"**, for a day. One grep of
  `DEFECT_LIST.md` for `template` would have answered it.

  The failure is specific and it is not forgetfulness: **the board is a write path in practice
  and a read path only in principle.** Every entry in it was written by somebody who had just
  investigated something; almost none were read by somebody about to. A document whose whole
  argument is "so the next person does not rediscover this" has to be searched *by the person
  rediscovering it*, and the moment to search is the moment the finding feels new — which is
  exactly the moment it feels unnecessary.

  A duplicate costs more than it looks. The two entries drift, the counts carry the same
  unfixed thing twice, and the one that gets closed is the one with less in it. The remedy is
  one line before filing: **grep the board for the noun**, and read what comes back. Where the
  new finding is a superset — D-160 had two files and a gate D-131 did not — fold it into the
  existing entry and leave the new number as a pointer, because a number referenced from a
  commit must not vanish.

  *And its corollary, found in the same hour.* The summary table gained a fifth status and the
  three assertions guarding it all passed, because each one names the status it checks. The
  rows summed to 159 against a stated 160 and nothing said so. **A guard that enumerates the
  cases it knows about cannot see a new case** — the rows are derived from the entries now, and
  must sum to the total.

- **MOVING FORMATTING TOWARD THE DATA NARROWS EVERY AUDIT THAT READS THE DATA'S TYPE.**
  *Added 2026-10-01.* D-125. Formatting seven numeric context fields in the builder instead of
  in five templates is one change instead of 145, and it is the obviously better engineering
  until you notice what else reads those fields. `numeric_leaf_names()` derives the set of
  numeric fields by walking the built contexts; `1949` is a number and `"1949"` is not, so
  `year_built`, `bedrooms`, `bathrooms`, `sqft`, `distance`, `lot_size` and `stories` left the
  set and the zero-conditional audit stopped covering them. Nothing failed. The audit got
  quieter.

  **This is distinct from the derived-set rule, which is about the INPUT a set is derived
  from.** Here the input was right and the *type* changed underneath it. A formatter looks
  local — it changes how one value prints — and is not local at all when something downstream
  dispatches on `isinstance`. Before moving a conversion toward the data, ask what reads the
  data by type: audits, serialisers, comparisons, JSON dumps, `or 0` chains.

  **Presentation belongs in the template, and the reason is not taste.** It is that the
  context is the thing other code reasons about, and every conversion applied there is a
  conversion those readers have to know about.

  *And the evidence that the rule alone is not enough:* this was caught by the derived-set
  guard written after D-119 — a guard that fails when a name it expects stops appearing. That
  is now the **second** time a guard left by a previous defect has caught the same defect
  recurring in the work that fixed a later one. The guards are doing more work than the rules,
  which is the argument for writing a guard every time rather than a rule every time.

- **A RESTORE THAT TARGETS AN UNTRACKED FILE SUCCEEDS AND DOES NOTHING.** *Added 2026-10-05.*
  Twice this session, both times during regression testing, both times leaving the mutation in
  place for the suite to measure as real.

  `git checkout -- <path>` and `git restore <path>` restore from the index. A file git is not
  tracking has nothing in the index, so the command exits 0, prints nothing, and changes
  nothing. The first instance reverted a whole tracked file and took a *new function* out with
  it — `format_measure` vanished and 36 test files failed to import, which at least announced
  itself. The second was silent: an edit planted in a brand-new correction document stayed
  planted, and the only reason it surfaced is that the gate written minutes earlier asserted
  on that document's contents.

  **This is the no-op mutation trap again** — the same shape as the `str.replace` that matched
  nothing and silently updated no counts, and the same shape as `elementsFromPoint` returning
  `-1`. A command that cannot distinguish "did the thing" from "had nothing to do" is a command
  whose success tells you nothing.

  The habit: **restore from a copy you made, not from git**, when the file might be new —
  `cp` the original aside before mutating and `cp` it back, and have the regression's own
  verification run afterwards rather than trusting the restore. `git status --porcelain` after
  a restore costs nothing and shows `??` for exactly the files the restore could not touch.

- **A LIST OF NAMES IN A TEST IS A COPY OF THE REGISTRY, AND IT GOES STALE SILENTLY OR LOUDLY,
  NEVER USEFULLY.** *Added 2026-10-05, from the theme cut — five instances in one change.*

  Five tests named their subjects in a literal: `parametrize("theme", ["classic", "bold"])` twice,
  `for theme in ("classic", "bold")`, `THEME_DARK_BG = {five entries}`, and
  `assert set(THEMES) == {five names}`. Cutting two themes made three of them raise `KeyError`
  (loud, and the message said "classic is missing" rather than "this list is a copy") and one
  pass while covering less. **A literal list of the things under test cannot distinguish "this
  one went away" from "this one was never supposed to be here".**

  Replaced with the property each list was standing for, found by parsing: *themes whose cover
  line references `agent.license`*, *themes whose brand sits on a dark surface*, *the themes the
  registry declares*. Each now moves with the registry, and each is paired with a guard that the
  derived set is **non-empty** — because a derived set that comes back empty makes every test
  over it pass.

  **And deriving the set found a case the literal had been hiding.** The dark-brand list had been
  `("classic", "bold")`; derived, it includes **elegant**, whose brand is `#1A1A1A` — a pure
  neutral. The assertion was `chroma_of(on_dark) > 100`, unmeetable for an achromatic brand by
  construction, so the literal list was not an abbreviation of the property, it was *excluding a
  counterexample to the assertion*. The guard now states the actual property — saturation may be
  spent, but only once value is at 1.0 — which is strictly stronger and applies to all three.

- **A FLOOR SIZED TO THE CORPUS IS A FLOOR THAT GETS LOWERED TO WHATEVER JUST RAN.**
  *Added 2026-10-05. Two instances, same change.*

  Two "the measurement actually ran" guards were written as corpus totals: `assert len(measured)
  > 900` over five themes, and `> 8000` over ninety documents. Both are the right *kind* of guard
  — zero findings and zero runs look identical from outside, which is the defect they exist for —
  and both failed the moment the corpus legitimately got smaller.

  **The failure is not the false alarm; it is what a false alarm invites.** The obvious response
  to "only 576 text runs measured, expected > 900" is to change 900 to 500, and the next person
  cannot tell a lowered floor from a measured one. Expressed per unit — `MIN_RUNS_PER_THEME * len(THEMES)`,
  `MIN_RUNS_PER_DOCUMENT * len(docs)` — the guard moves with the corpus and the constant stays a
  measurement. **Write the floor as a rate, and record the date and the measured value beside it.**

- **A SELECTOR NAMED AFTER ONE INSTANCE DESCRIBES THAT INSTANCE, NOT THE CONSTRUCT.**
  *Added 2026-10-05. The locator form of "a substring is not a construct", and the fourth
  instance of that rule's family.*

  `test_the_total_comps_badge_is_that_same_number` ran on teal alone, and said so:
  *"Teal is the only theme that prints it."* **That was never true.** Every theme prints the
  Total Comps badge; teal was the only one whose label carried `class="lbl"`, and the test's
  regex matched the class. The docstring had turned a property of the *selector* into a stated
  fact about the *product*, and it had been read and passed over at least twice.

  It surfaced only because the cut deleted teal and the test failed with `found []` — which reads
  as "the badge is gone from the product" and is really "the selector described one theme's
  markup". **When a test runs on one member of a set, the docstring must say whether that is
  because the others lack the behaviour or because the locator only fits one of them** — and the
  way to know which is to point it at a second member before believing the first.

- **BEFORE REMOVING A VALUE FROM AN ENUMERATED SET, ENUMERATE WHAT DEFAULTS TO IT.** *Added
  2026-10-06, from the theme cut. The removal counterpart of the missing-row rule, and the same
  error with the sign flipped: reading a property of the data as a property of the system.*

  **A value's reachability is what is STORED union what is DEFAULTED TO, and a query over the
  table sees only the first half.** The theme cut was planned from the stored counts — 41 accounts
  on teal, none on classic, migrate the 41 — and teal had **five** routes, of which the migration
  covered one. `report_data.get("theme", 4)`, the `else` arm for anything unrecognised,
  `THEME_TEMPLATES.get(name, …["teal"])` at render time, and `DEFAULT_THEME_ID = 4` on the
  consumer lead-capture path. Four of the five are invisible to
  `SELECT … WHERE default_theme_id = 4`.

  Deleting the template while any of them still named it would have left a live path asking the
  renderer for a file that is not there — and the route that would have hit it first is the one a
  **stranger** sees. The migration is correct; what it cannot say is what it does not cover, and
  nothing about reading it suggests the question.

  **Found by rendering, not by reading** — resolving a theme for every input a caller can supply
  (`None`, `0`, `1`, `4`, `"4"`, `"teal"`, `True`, `99`, `"nonsense"`) and reading the answers.
  That is the render-to-verify rule applied to a *removal* rather than to a fix, which is a case
  it had not been applied to before. See **D-166**.

  The structural half: a fallback should name a value the registry *declares*, so that a registry
  which disagrees with itself fails at import rather than one report at a time — and a gate should
  parse every fallback and refuse one naming a value the set does not have.

- **A DEFERRED DECISION NEEDS A RATCHET, NOT A DOCUMENT.** *Added 2026-10-06.*

  "Decide later, it is cheap" is a measurement with an expiry date on it. The theme rename was
  scoped at **16 files and 82 occurrences**, deferred until Design's three templates land — and the
  thing that would invalidate that is not a change of mind, it is **new call sites accruing quietly
  while the templates land**, so the decision gets taken in three weeks against a number measured
  today.

  A scoping document cannot hold that line; it is prose, and prose does not fail. The count is now
  a ratchet with both halves — it may shrink freely, it may grow only by editing the constant, and
  a *shrink* also fails, because a ratchet nobody tightens stops constraining anything. Plus a
  guard on the one thing that would change the answer's kind rather than its size: a live template
  gaining a CSS custom property named after its own theme, which is what made teal expensive and
  which Design's rewrite is the moment it could come back. All three seen to fire.

  **The general form: when you defer a decision on the strength of a measurement, gate the
  measurement.** Otherwise the deferral quietly converts a fact into a memory.

- **A GATE THAT REIMPLEMENTS WHAT IT GUARDS IS GREEN WHATEVER THE PRODUCT DOES.** *Added
  2026-10-06. Second instance, and this one had been green for months.*

  `compute/market_trends.py` imports three metric functions from `worker.report_builders`. None of
  them exists there. The import raises every time, a bare `except (ImportError, Exception)` logs it
  at `info`, and three market metric groups have been `None` since they were written —
  **`tests/test_new_metrics.py` defines its own working copies of two of them, at lines 22 and 47,
  and tests those.** The tests pass. They test code nothing imports. D-167.

  D-140 was the same shape one layer out: a gate that MIRRORED a dict literal because the literal
  lived inside a Celery task and there was nothing to import. That one was caught because a
  regression failed. This one was caught by trying to USE the functions, two years of green behind
  it.

  **Import what you are testing, or the test is a second implementation with a passing grade.** If
  it cannot be imported, that is the finding — extract it until it can be. And a bare
  `except Exception` over an import is not a degraded mode: a missing producer is a defect, and
  `info` is not where anyone looks for one.

- **A PER-ITEM GATE BECOMES A PER-ARCHITECTURE GATE THE MOMENT TWO ITEMS STOP BEING ALIKE.**
  *Added 2026-10-06, from wiring one of three themes onto a shared template.*

  Twelve test files parametrised over themes and read `THEME_TEMPLATES[theme]` as the file for that
  theme. Moving ONE theme onto a shared page architecture broke that in two different ways, and the
  first was loud in the worst place: `test_theme_cover_title` failed at **collection** with
  "expected exactly one cover title line, found 0", which took the whole worker suite down and hid
  every other result until it was fixed.

  The shapes, all of them from the same cause:

  | the gate assumed | what the shared architecture does |
  |---|---|
  | a theme is one file | a theme is an entry file plus the shared one |
  | the page's markup is in the theme's file | it is in the shared file |
  | every theme has nine pages | this one has six |
  | this surface exists on every theme | the contents page, the analysis table and the Total Comps badge exist on none of them |
  | `class="page"` | `class="sheet sheet-<page>"` |

  **Resolved by one shared resolver, `_template_chain`, that parses each theme's includes rather
  than holding a list of which themes are on which architecture** — a list would be a fourth copy
  of the thing D-163 was about. Everything else derives from it: `SHARED_THEMES`,
  `SELF_CONTAINED_THEMES`, and each gate asking which it is looking at.

  **The cost is real and it is paid once.** 55 failures on the first full run after the template
  landed, every one of them a gate correctly reporting that the document changed. Four were defects
  in the new build; the rest were re-points. Theme two and three pay none of it.

  **And re-pointing is not relaxing.** Every property whose surface disappeared was re-asserted on
  the surface that replaced it — "the contents agrees with the document" became "the footers run
  1..N and N is the number of sheets rendered"; "the analysis note states the comp count" became
  "Each sale · N and the comps header agree with the set"; "the chart draws as many bars as the
  table counts" became "there is exactly one bar per comp", which is stronger. A gate narrowed to
  fewer themes without a replacement is coverage quietly withdrawn.

- **A FIXTURE THAT SUPPLIES THE VALUE UNDER TEST CANNOT FAIL.** *Added 2026-10-06. Found by a
  regression run, not by reading the test.*

  `test_the_six_page_set_is_a_maximum_not_a_guarantee` asserts that the consumer path renders five
  pages without market data and six with it. Its fixture set `selected_pages` itself — so when
  `consumer_report_data.py` was reverted to its own stale copy of the nine-page list, **the test
  stayed green.** The gate was passing against the exact defect it was written for.

  The same run found a second one: reverting the cover's bathroom formatter to the integer one left
  "1.5" elsewhere in the document, so a gate asserting "1.5 is somewhere in the output" passed
  while the largest number on page one was wrong. Fixed by asserting **per surface**, not per
  document.

  **Both were invisible to reading and obvious to a regression.** This is why every gate gets one:
  eleven were applied to this change and two came back SILENT, which is a two-in-eleven rate of
  gates that would have reported green on their own subject.

- **A BASELINE CANNOT DESCRIBE A DOCUMENT THAT NO LONGER EXISTS, AND "NEVER REGENERATE" IS A RULE
  ABOUT CASUALNESS, NOT ABOUT REPLACEMENT.** *Added 2026-10-06, as a policy correction from Jerry.*

  The contrast ratchet keys on `(family, selector, foreground, background)`. A redesign changes the
  selector **and** the background, so a replaced surface produces N new keys and N orphans with
  **zero overlap**, and both directions of the check fire on all of them. The output reads as 2N
  regressions. It is one fact: the file is comparing two different documents.

  "Nothing re-baselined" is right when a surface is being *fixed* — bold's 13 new pairings were all
  template defects and all 13 were fixed, with 37 orphans deleted by key and every surviving line
  byte-identical. It is wrong as a standing rule when a surface is being *replaced*, because then
  the baseline has no subject left.

  **The policy: regenerate per surface as each lands, and the diff is the review artefact.** Scoped
  to the family that was rebuilt, with every other line untouched, so the diff still carries the
  claim that nothing else moved. A surface that was not replaced is still a ratchet.

  **The general shape, which is not about contrast.** A baseline is a comparison to a prior state,
  so it has a precondition nobody writes down: *that there is still a prior state to compare to.*
  Every ratchet in this project needs the question asked before its output is read — is this
  reporting a regression, or reporting that its subject was replaced? The two look identical and
  lead to opposite actions.

- **THE SCOPE OF A REACHABILITY CHECK IS PART OF ITS CLAIM, AND THE SECOND TIME IS AS EASY TO GET
  WRONG AS THE FIRST.** *Added 2026-10-06. D-131, and then D-131's own correction.*

  D-131 classified a dead property-template tree correctly and produced the sentence **"everything
  in `_base/` render nowhere"** — unqualified, copied into nine places including the handover Design
  received. There are two `_base/` directories; `templates/market/_base/base.jinja2` is extended by
  `market/market.jinja2` and is the whole of every market report. Acting on "delete the `_base/`
  tree" would have deleted it. **The method was not wrong. The sentence omitted its own scope**, and
  a classification that omits its scope reads as a classification of everything.

  Then the derivation written to fix it **made the same mistake in the other direction.** Following
  only Jinja `extends`/`include`/`import`/`from`, it reported the market running head and footer —
  217 lines — as dead. They are reached from Python: `env.get_template("_base/page_header.jinja2")`.
  A template can be a root with nothing in Jinja referencing it. That near-miss was one commit from
  being filed as a new defect.

  **So derive both ends.** Roots from the code that renders (every `get_template` literal, parsed
  with Python's own parser), edges from the templates, and the answer reported **per surface** —
  because the same template name resolves to different files under different loaders. And the gate
  that keeps it honest asserts the positive: `market/_base/` **is live**, by name. A gate that only
  ever says "this is dead" cannot catch a live file being called dead, which is the failure that
  mattered here.

  The one document that got it right, `00-SHARED.md`, did so structurally rather than by care: its
  table has **one row per surface**, so there was nowhere to write an unqualified `_base/`.

- **A GATE ON A DOCUMENT MUST ASSERT ITS CLAIMS, NOT ITS TEXT — AND THE GATES WHOSE SUBJECT IS
  STALENESS ARE THE ONES THAT GET THIS WRONG.** *Added 2026-10-07. Two instances in one day, both
  in gates written to stop a document going stale.*

  Two documents now leave this building for Design, and both are gated because three bounds have
  arrived from them derived from a sample and stated as a property. Both gates were written against
  the **words** rather than against what the words say, and both let a real change through:

  * `test_the_overlap_is_what_the_document_says` matched the heading string `"Only two of the six
    brands are shared"`. **Reordering the document broke it** — the lead was moved from the
    correction to the finding, every number unchanged, and the gate failed. A gate that fails on a
    rewrite teaches you to stop rewriting.
  * `test_the_document_quotes_the_pinned_capacity` checked `str(rows) in text`. Moving a measured
    capacity from 15 to **17 passed**, because the document contains `D-173` and `"17" in "D-173"`.
    Substring-is-not-a-construct, instance fourteen, inside a staleness gate — which is the irony
    that makes it worth a rule.

  **The fix is the same in both directions: put the claim in a form the document and the gate can
  both parse, then compare the parsed values.** §5 of the capacity document is now a fenced
  ```capacity block of `kind.state = rows` lines, and the assertion is dict equality against
  `PAGE_1_CAPACITY` — which catches a figure that moved, a figure that was dropped, and a figure
  that was added, none of which a substring scan can distinguish from prose. The brand audit asserts
  each hex **by value** and the lead's own count, not the sentence that carries them.

  The general form: **a document's prose is for the reader and its data is for the gate, and they
  have to be different regions of the file.** A gate reaching into prose is either brittle about
  wording or blind about values, and there is no setting of it that is neither.

- **BEFORE BUILDING A TOOL, GREP FOR ONE.** *Added 2026-10-07. Cost: one file overwritten.*

  §0.6 already says a defect list needs a read path, because D-009 was a record nothing consumed.
  **This is the same shape about the repository rather than the board**, and it is a separate rule
  because the remedy is different: a board needs a reader, and a repo needs you to look.

  A generalised regression harness was written to fix three hand-run misfires. `scripts/regress.py`
  had existed since **PR #103** — the same idea for `themes.py`, with eleven recorded mutations and
  **already carrying the two checks that mattered**: an anchor-count check (`if n != 1: MUTATION DID
  NOT APPLY`) and an unchanged-on-disk assert. Two thirds of the remedy was in the repository for a
  hundred PRs. It was overwritten without being read, and the only thing that caught the collision
  was `git status` printing `M` where `??` was expected.

  What the predecessor lacked was real — a bytecode clear, a verified restore, and an exit code
  rather than printing `*** NOTHING CAUGHT IT ***` and exiting 0 — so the new tool was worth
  writing. **Reading the old one first would have produced the same tool and a better one**, because
  its eleven mutations are knowledge that had to be ported back in afterwards.

  **The harness built that day does not and cannot catch this.** It guards mutations; it has nothing
  to say about the decision to create a file. There is no gate for "did you look", which is exactly
  why it is written down here instead: *the habit is the remedy, and `git status` is not it.* A file
  that reports `M` when you expect `??` has already been overwritten — the check has to come before
  the write, not after.

  Operationally: `grep -rl` the concept, not the filename. "regression harness" would not have found
  `regress.py`; `grep -rn "MUTATION DID NOT APPLY"` or a look in `scripts/` would have.

- **A PREDICTION AND A MEASUREMENT CANNOT SHARE A GATE.** *Added 2026-10-08.*

  `docs/MARKET_CAPACITY_VS_DESIGN_2026-10-07.md` §2a forecast what Design's row counts would cost
  per kind, against our capacity at the time. Its gate recomputed the "ours" column from
  `PAGE_1_CAPACITY` — correct for a document that must stay current, and **it broke the moment the
  first kind was built**, because the pin moved to the built figure and the forecast did not.

  The tempting fix is to update the forecast. That destroys the only thing it was for: §2a is worth
  reading *because* it can be compared with what happened, and a forecast edited to match the result
  predicts nothing. The same edit would also have hidden the interesting part — both built kinds
  landed on **5 pages** where the formula said **6**, so the forecast was wrong in a direction worth
  knowing.

  **So the two were split, and the split is the rule.** A forecast records **the inputs it was taken
  with** and its gate checks that its arithmetic is internally consistent against *those*; a
  measurement section carries the built figures and its gate checks them against the live pin. One
  is checkable forever, the other is checkable now, and neither can be made to do the other's job.

  The general form: **a gate enforces either currency or fidelity to a past state, and a document
  that holds both needs one gate per region.** The giveaway is a gate that starts failing because
  something it describes *succeeded* — which is what happened here, and which reads as a broken test
  rather than as a category error.

- **A GATE ON A PRODUCER IS NOT A GATE ON THE DOCUMENT.** *Added 2026-10-08, from D-181.*

  §0.6 already says *a gate on a document must assert its claims, not its text*. This is that rule
  one level further out, and it needed its own line because the failure mode is the opposite of
  loud: the gate does not get weaker, it gets **pointed at the wrong object**, and then it is as
  strong as ever about something nobody reads.

  D-111's price-band rebuild puts a disclosure on the page — *"bands may shift between reports"* —
  whenever the boundaries came from this period's results instead of from twelve months of closings.
  It is the sentence that makes the fallback honest. Its gate was:

      note = builder._band_chart_note()
      assert "may shift between reports" in note

  `_band_chart_note`'s only consumer was a macro reached only from `pricebands_layout`, whose only
  report type was `price_bands` — and `price_bands` left the macro dispatch when it joined the `_v2`
  seam. **One kind moving made a four-link chain dead from the far end.** The method kept returning
  the string, the assertion kept passing, and the document stopped carrying it.

  **A producer with no consumer still produces.** This is the repository's *read-with-no-producer*
  family (nine instances) pointed the other way, and it is harder to see: a consumer reading a key
  nothing writes at least renders something empty, while a producer writing a value nothing reads
  renders nothing at all and looks like a page that never had the line.

  Operationally: when a claim has to appear in an artefact, **assert it on the artefact**. Keep the
  producer assertion if it is cheap — it localises a failure — but it is never the one that matters.
  And when a seam moves a kind, surface or path off one code path onto another, the question is not
  only "does the new path work" but **"what did the old path produce that nobody else produces"**.

- **AN ASSERTION SCOPED TO ONE INSTANCE, NAMED AS IF SCOPED TO THE CLASS.** *Added 2026-10-10.*

  §0.6 already says a gate on a document must assert its claims, not its text, and that a gate on a
  producer is not a gate on the document. This is the third face of it: the gate is pointed at the
  right object, asserts the right thing, and **covers one member of a set whose name it borrows.**

  `TestPrintCSS::test_has_page_size_rule` reads as *"the market templates set a page size"*. Its
  fixture sets one `report_type`, so it meant *"`new_listings_gallery` does"*. **Four `_v2` kinds
  shipped with no `@page` rule for three days and it was unobserved** — the test could not see them,
  and it failed only when the one kind it did see moved, which is the last moment it could have.

  The tell is in the **fixture, not the assertion**: a single-instance fixture under a class-scoped
  name. `full_data` with one `report_type`, a partial render standing for a page, one theme standing
  for six. The assertion reads as coverage and is a sample of one.

  **This is also the direction D-107 failed in**, a day earlier and in a document rather than a test:
  the entry's claim was class-scoped (*"the price-band stat cards show the first four bands"*) and
  its fix was instance-scoped (one macro of two). Same mismatch, and nothing noticed for ten days.

  Two remedies, and which one depends on whether the members differ:

  * **They do not differ** → parametrise over the set. `ALL_REPORT_TYPES`, every theme, every kind.
  * **They do differ** → pin the expectation per member and make an unrecorded member an error, the
    way `HAS_AT_PAGE_RULE` now records that the legacy page has an `@page` rule and the `_v2` page
    deliberately has none.

  What is NOT a remedy is renaming the test to match its scope. `test_new_listings_gallery_has_a_
  page_size_rule` would be honest and would still leave seven kinds unasserted. **The name should
  carry the scope, and the scope should be the class.**

  *Checked and absent:* a test asserting exactly one `<table` in a document that has two, passing
  because its fixture was a partial render, is **not in this repository** — there is no such
  assertion and no `test_html` fixture. Recorded so it is not re-filed; the real instance is the
  `@page` one above.

- **A POSITIVE CONTROL DRAWN FROM THE SET BEING MIGRATED IS CONSUMED BY THE MIGRATION.**
  *Added 2026-10-08.*

  §0.6 already requires a positive control: a checker whose normal output is "match" is
  indistinguishable from one that has stopped matching anything. The trap is **where the control
  comes from.** Four tests named a report type as "the kind that has NOT moved", and each stopped
  being a control the moment that kind moved:

  | test | named | consumed when |
  |---|---|---|
  | `test_the_dispatch_fallback_is_reachable_only_by_an_unknown_layout` | `closed`, then `inventory` | twice |
  | `test_a_kind_without_a_band_spec_raises_rather_than_rendering_empty` | `inventory` | 2026-10-08 |
  | `test_a_v2_render_does_not_pay_for_a_narrative_it_discards` | `inventory` | 2026-10-08 |
  | `test_the_comparison_is_against_the_no_narrative_column` | `inventory` | 2026-10-08 |

  **None of them failed in a way that said "your control is gone."** Three failed with the control's
  own assertion inverted, which reads as the feature breaking; one would have passed while proving
  nothing, because a kind inside the seam satisfies "calls no layout macro" trivially. One of them
  even carried the comment *"`inventory`, not `closed`: closed renders the `_v2` page now"* — the
  same substitution, one kind earlier, by someone who had just watched it happen.

  **The remedy is to compute the control and assert the remainder is non-empty.**
  `sorted(set(ALL_REPORT_TYPES) - V2_KINDS)` with an assertion that it is not empty, so when the
  last member moves the test says *"there is no kind left to act as the control; these tests are no
  longer proving what they say"* instead of quietly passing.

  And when the control genuinely has no replacement, **say that rather than patch it.** The 15/11
  page-1 swing existed only on the two kinds whose layout put a narrative box above a long table,
  and both moved — so "one kind still shows the swing" became "no kind's capacity depends on prose
  length", asserted over all eight. A weaker-looking assertion over the whole set beats a strong one
  over a sample of zero.

- **A CONSTANT THAT IS RIGHT FOR EVERY MEMBER OF A SET IS INDISTINGUISHABLE FROM A CONSTANT THAT IS
  RIGHT FOR THE SET — UNTIL THE SET GROWS.** *Added 2026-10-08.*

  Four gates written while the `_v2` seam held only table kinds encoded a table kind's property as
  the seam's property, and all four broke on the first kind that was not a table:

  | gate | what it said | what it meant |
  |---|---|---|
  | `test_a_v2_kind_calls_no_layout_macro` | `class="trow thead"` is on the page | *a table kind's* body rendered |
  | `test_the_built_figures_match_the_live_pin` | `ceil((120 - page_1) / 26) + 1` | 26 is *the table body's* continuation capacity |
  | `test_the_cap_is_what_limits_the_listings` | rendered rows == `PDF_CONFIG` cap | the kind *has* a listings table |
  | the §2a forecast gate | live `PAGE_1_CAPACITY` is the forecast's input | the kind *has not been built yet* |

  None was wrong when written and each was wrong one kind later. The remedy in all four was the
  same and it is the general one: **pin the varying thing per member, and make an unrecorded member
  an error rather than a default.** `V2_BODY_MARKER`, `V2_CONTINUATION` and `RENDERED_DESPITE_CAP`
  each raise on a kind they do not know, so the next kind to join the seam is told what to record
  instead of inheriting the third kind's geometry.

  This is `V2_KINDS`-subtraction's counterpart. Subtracting the seam from a parametrisation stops a
  moved kind from being silently excluded; pinning per member stops the kinds that remain from
  sharing one member's properties.

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
