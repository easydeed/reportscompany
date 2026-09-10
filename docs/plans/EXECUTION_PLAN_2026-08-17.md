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

- **No finding derived from a sample render counts until it is reproduced through the
  production path.** Three instances in this project — the property report aerial, the
  email placeholder links, and the inventory report's months-of-supply figure — where a
  reviewed artefact did not reflect what production emits. A sample can show what the
  code *can* produce; only production shows what it *does*.

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

- **Grep for the construct, not for the symptom, and re-run the check after the fix.**
  Three instances where the post-fix check found what the pre-fix survey missed: the third
  unguarded map pin, `CreateCompanyRequest`, and `bold_report.jinja2:848` — the last found
  only because a test ran after the change, since it used the right construct with a
  different string.

- **A guard that refuses input is a guard that can refuse legitimate input.** Check what
  it rejects, not only what it accepts. Twice a correct-looking security fix would have
  converted an injection into an outage: rejecting a non-hex colour by raising, and
  scheme-allowlisting the unsubscribe URL — which would have stripped a sentinel that is
  not a URL and aborted *every* send.

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
