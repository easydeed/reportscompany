# Execution Plan — Revision A

**Date:** 2026-08-17
**Supersedes:** Phases 2–6 of `EXECUTION_PLAN_2026-08-17.md`
**Unchanged:** §0 Rules of Engagement, Phase 0, Phase 1 — both already in flight

**Goal change:** the original plan optimized for converting new prospects. The goal is now
**product stability and codebase cleanup**. New-customer acquisition work is deferred.

That inverts the order. Verification moves from last to first, because verification is what
produces the defect list everything else works from. Marketing trust fixes move to the back —
they only matter to people who haven't signed up yet, and nobody is being sent there.

---

## Definition of Stable — the finish line

This is not a mood. It is a checklist, and when it is checked, this phase of work is
**done** and the project moves on.

- [ ] **S1.** Every one of the five account types (`REGULAR`, `INDUSTRY_AFFILIATE`,
      `TITLE_COMPANY`, `COMPANY_REP`, `SPONSORED`) can complete: register → verify →
      onboard → create a report → receive it by email. Verified by a real run, not by
      reading code.
- [ ] **S2.** A schedule created through the UI fires on time and delivers to real
      recipients. Confirmed by receipt, end to end. This is the product's core promise and
      nothing currently proves it works.
- [ ] **S3.** For every plan: the limit displayed equals the limit enforced, asserted by a
      test that fails if they diverge.
- [ ] **S4.** PDF engine selection is deterministic, documented, and the production path is
      verified against production config.
- [ ] **S5.** No route in the app returns a 5xx under an authenticated smoke test, for
      every account type.
- [ ] **S6.** Every subsystem shipped after 2026-05-14 has a behavioural doc: company
      portal, onboarding, per-product limits, the second `/admin` tree, the second
      migrations directory.
- [ ] **S7.** Every piece of dead code is either deleted or explicitly registered as
      intentionally dead in one place.

Seven items. Not "no bugs" — that isn't a finish line, it's a horizon.

---

## Revised Phase Order

| Phase | Branch | Nature | Depends on |
|---|---|---|---|
| 0 | `chore/p0-security-tooling` | Security + tooling | — (in flight) |
| 1 | `chore/p1-docs-purge` | Deletions + banners | P0 |
| **2** | `test/p2-verification-sweep` | **Investigation only — produces the defect list** | P0 |
| **3** | `fix/p3-plan-limits-truth` | Billing correctness | P0 |
| **4** | `fix/p4-defects` | Fix what P2 found | P2 |
| **5** | `chore/p5-dead-code` | Cleanup | P1, P2 |
| **6** | `docs/p6-rebuild` | Docs rebuild — now in scope | P1, P2, P4 |
| — | deferred | Marketing trust fixes (old P3), title companies page (old P4) | — |

Phases 2 and 3 can run in parallel after Phase 0.

---

## Phase 2 — Verification Sweep

**Branch:** `test/p2-verification-sweep`
**Nature:** **Investigation and observation only. No production code changes.**
Test scaffolding and seed scripts are allowed; nothing else.
**Output:** `docs/DEFECT_LIST.md` — the input to Phase 4

Both audits examined the front door. This examines the interior. Priority order is set by
one signal: **code that shipped after the docs froze on 2026-05-14 has never been
documented and, as far as anything shows, never systematically tested.** That is where
defects live.

### Phase 2A / 2B split

Claude Code has no staging or production credentials, and several tickets need them.
Rather than block the phase, it splits:

**Phase 2A — runs locally, starts immediately.** Branch `test/p2a-verification-local`.
`docker-compose.yml` brings up Postgres 15 + Redis; `scripts/migrate.sh` applies all 53
migrations including `0048`–`0050`. Run the API and worker in-container.

- T2.1 test account provisioning
- T2.2 company portal — including the RLS isolation test
- T2.4 registration → onboarding → first-run
- T2.6 authenticated smoke test
- T2.7 migration state (local half: what the runner applies, whether a fresh bring-up
  produces the expected schema)

**What 2A proves:** the code is correct. RLS policies live in the migrations, so a local
cross-tenant test exercises the same policy logic production runs. A failure here is a real
defect. A pass here does not prove production is configured correctly — that's 2B.

**Phase 2B — deployed verification. Blocked on credentials.** Branch
`test/p2b-verification-deployed`.

- T2.3 scheduled delivery end-to-end (needs: staging API access + a readable inbox)
- T2.5 PDF engine determinism, production half
- T2.7 migration drift (local schema vs. deployed schema)
- T2.9 silent-failure audit, "is it set in production?" half
- T2.10 environment selector audit, "what is the actual value?" half

**Unblocking 2B without handing over credentials:** most of T2.9 and T2.10 need only the
env-var *configuration*, not database or admin access. Jerry pastes the variable names and
non-secret values from the Render worker, Render API, and Vercel dashboards — secrets
redacted to set/unset, since what matters is whether a key exists, not what it is. The
values that decide these tickets are all non-secret: `PDF_ENGINE`, `PDF_API_URL`,
`SITEX_BASE_URL`, `NEXT_PUBLIC_API_URL`, `API_URL`, and whether `RESEND_API_KEY` and
`PDFSHIFT_API_KEY` are set at all.

T2.3 cannot be unblocked this way. It needs a real send and a readable inbox.

### Rules for this phase

- **Observe, do not fix.** Every defect goes in `DEFECT_LIST.md` with a severity and a
  reproduction. If a one-line fix is obvious, still do not fix it — record it. Fixing
  during investigation is how investigations stop being systematic.
- Every entry must have: what you did, what you expected, what happened, `file:line` if
  known, severity, and which account type(s) it affects.
- Severity: **BROKEN** (does not work) / **WRONG** (works, produces incorrect output) /
  **FRAGILE** (works, will break under normal conditions) / **ROUGH** (works, poor
  experience).
- If a subsystem cannot be tested without production credentials or data, say so and mark
  it UNVERIFIED. Do not simulate a pass.

### T2.1 — Test account provisioning

Seed/teardown script producing a throwaway account per account type at a known state.
Prerequisite for everything else in this phase.

**Acceptance:** one command creates all five; one command removes them.

### T2.2 — Company / title-company portal

**Coverage gap #1. Highest priority in this phase.**

Surface: `apps/api/src/api/routes/company.py` (mounted `main.py:120`), 9 proxy routes,
6 pages under `apps/web/app/app/company/`, migrations `0048_title_company_hierarchy.sql`
through `0050_pct_to_title_company.sql`.

Zero documentation. Zero known tests. Newest code in the system.

Walk every page and every route as `TITLE_COMPANY` and as `COMPANY_REP`:
- Can a title company invite, provision, and manage reps?
- Can a rep sponsor agents? What does the sponsored agent see?
- Does branding inherit correctly down the hierarchy (company → rep → agent)?
- What happens when a rep is removed — orphaned agents? Broken reports?
- Are RLS boundaries correct? Can a rep from company A see anything from company B?
  **Test this explicitly; it is the highest-severity failure available in a multi-tenant
  system.**
- Does every page render for both roles, or do some assume a role and blow up?

**Acceptance:** every route and page exercised for both roles; findings in `DEFECT_LIST.md`;
RLS isolation explicitly confirmed or refuted with evidence.

### T2.3 — Scheduled delivery, end to end

The core promise. Nothing in either audit proves it works.

- Create a schedule through the UI as an agent. Real recipients you control.
- Confirm the tick fires (`schedules_tick.py`), the task runs, the report generates, the
  email sends, and it **arrives**.
- Check the received email: correct branding, correct data, working links, images loading,
  unsubscribe present and functional.
- Confirm `schedule_runs` records the run accurately (`status`, `sent_count`).
- Test the failure path: what happens with an empty recipient list, a suppressed email, an
  invalid city?

**Acceptance:** a received email in an inbox, or a documented reason it did not arrive.
This satisfies **S2** or produces the highest-priority defect in the project.

### T2.4 — Registration → onboarding → first-run

**Coverage gap #2.** For each of the five account types, walk register → verify → onboard →
first `/app` load. Record every step: what is required, what breaks, what has no empty
state, what assumes data that a new account does not have.

**Acceptance:** all five walked; findings recorded. Satisfies **S1** or produces defects.

### T2.5 — PDF engine determinism

The audit found engine selection is `PDF_ENGINE` env, default **playwright**
(`pdf_engine.py:30`), that `PDF_ENGINE=pdfshift` with no key **raises** (`:159-160`), and
that a third undocumented selector exists (`PDF_API_URL`, `pdf_adapter.py:17-18,37`). Docs
describe a different mechanism entirely.

- What is `PDF_ENGINE` set to in production? In staging?
- If production is running playwright when PDFShift was intended, that is a live stability
  issue — Playwright in a Render worker is a different reliability profile.
- What does `PDF_API_URL` do, and does it override the others?
- Generate the same report through each path and diff the output.

**Acceptance:** the actual selection logic documented, production config confirmed, outputs
compared. Satisfies **S4** or produces a defect.

### T2.6 — Authenticated smoke test

Hit every route in the app as each account type. Record every 5xx and every route that
renders an error state.

Include the second top-level `/admin` tree (14 pages under `apps/web/app/admin/`, separate
from `/app/admin`) — coverage gap #3, mentioned by no document.

**Acceptance:** a route-by-route pass/fail matrix. Satisfies **S5** or produces defects.

### T2.7 — Migration state

The audit found a second migrations directory: `apps/api/migrations/phase4_indexes.sql`
creates `signup_tokens` outside `db/migrations/`. No runner and no doc acknowledges it.

- Which directories contain migrations?
- What does `scripts/run_migrations.py` actually run?
- Is `phase4_indexes.sql` applied in production? How would anyone know?
- Does a fresh local bring-up produce the same schema as production?

**Acceptance:** the true migration story documented. Flag any drift as a defect.

### T2.8 — Compile `DEFECT_LIST.md`

Every finding, sorted by severity, then by account types affected. Head the document with a
count per severity.

**→ PR: `test/p2-verification-sweep`.**

---

## Phase 3 — Billing Truth Chain

**Branch:** `fix/p3-plan-limits-truth`

Unchanged from the original Phase 2 (tickets T2.1–T2.3 in the original document, renumbered
T3.1–T3.3 here). It stays in scope because a displayed limit that does not match the
enforced limit is a correctness defect, not a marketing one.

The **[JERRY] decision gate** still applies: investigation stops, you answer what the
intended model is, then reconciliation proceeds. Exit criterion **S3**.

Also carry forward one item from the deferred marketing phase: **Terms §4 says the free
trial expires; no expiry mechanism exists in the code.** That is a legal document
describing behaviour the product does not have. Fix it here rather than deferring it with
the rest of the copy work.

---

## Phase 4 — Fix the Defects

**Branch:** `fix/p4-defects`
**Depends on:** Phase 2 merged

Written after Phase 2 delivers `DEFECT_LIST.md`. One ticket per defect, ordered
BROKEN → WRONG → FRAGILE → ROUGH. ROUGH items are candidates for deferral, not automatic
inclusion.

Standing rule: **any defect in the company portal or in scheduled delivery outranks
everything else regardless of severity label.** Those are the two surfaces where failure is
invisible to you and visible to a customer.

---

## Phase 5 — Dead Code Removal

**Branch:** `chore/p5-dead-code`
**Promoted from out-of-scope.** Cleanup is now a stated goal.

Candidates identified by the audit:

| Target | Evidence | Caution |
|---|---|---|
| `apps/web/components/v0-report-builder/` | 6 files, zero importers | Confirm zero importers before deleting |
| `apps/web/lib/templates.ts` + 7 `trendy-*.html` | Legacy templates, playbook P4-T3 | Verify nothing renders them |
| `/print/[runId]` | Docs claim removed | **NOT DEAD.** The worker builds URLs against it (`tasks.py:1069,1096`, `PRINT_BASE` at `:249`). Two docs assert it was removed and both are wrong. **Do not delete.** Document it as live. |

Rules:
- Prove death before deleting: zero importers, zero route references, zero runtime string
  construction. Grep for the filename as a *string*, not just as an import — that is how
  `/print/[runId]` fooled two documents.
- One commit per removal, so any single one can be reverted alone.
- Anything that cannot be proven dead stays, and gets a comment recording why it looks dead
  but isn't.

**Acceptance:** satisfies **S7**.

### T5.4 — Dead-code register

Create `docs/DEAD_CODE.md`: what was removed, what looks dead but is live and why. This is
what stops the next audit from re-litigating `/print/[runId]`.

---

## Phase 6 — Docs Rebuild

**Branch:** `docs/p6-rebuild`
**No longer deferred** — codebase cleanup is now a goal, and Phase 2 will have generated
the behavioural knowledge that makes the rewrite cheap.

### T6.1 — Ban the rot first

Before writing any doc, build `scripts/docs_stats.py`, emitting every countable fact
(routers, migrations, services, components, pages, proxy routes). Then adopt the standard:

- **No counts in prose. Ever.** Counts come from the script.
- **No line numbers.** Cite `file.py::symbol_name` — symbols survive refactors; line 823
  does not.
- Docs describe **contracts and behaviour**, not inventory.

Two-thirds of the audit's falsified claims were counts or line numbers, and every single
cross-doc contradiction in §2.2 was a count. Rewriting without changing the rules
regenerates the identical problem by spring.

### T6.2 — Build the target doc set

Per §4 of the audit, plus the new subsystem docs Phase 2 makes possible:

| Doc | Source |
|---|---|
| `README.md` | Rewrite; working dev commands |
| `docs/SETUP.md` | Rewrite of `LOCAL_SETUP_GUIDE.md`; both migration directories; a CRMLS city |
| `docs/architecture/SOURCE_OF_TRUTH.md` | V17; no counts |
| `docs/architecture/backend.md` | Merge core + middleware + routes + services; **include `company.py`** |
| `docs/architecture/frontend.md` | Merge core + pages + components; **both admin trees, company portal** |
| `docs/architecture/worker.md` | Merge worker-core + tasks + builders; **PDF engine selection per T2.5** |
| `docs/architecture/wizards-and-apis.md` | Already merged in P1 |
| `docs/architecture/company-portal.md` | **New** — from T2.2 observations |
| `docs/architecture/onboarding.md` | **New** — from T2.4 observations |
| `docs/architecture/plans-and-limits.md` | **New** — from Phase 3 |
| Keep as-is | `filter-resolver.md`, `qr-landing-leads-sms.md`, `db-schema.md`, the 4 design HTMLs |

The new docs are written from **observed behaviour**, not from reading code. That is the
difference between this rebuild and the one that produced the docs the audit just
demolished.

**Acceptance:** satisfies **S6**. Staleness banners from T1.5 removed only from docs
actually rewritten.

---

## Deferred

Not cancelled — parked, with the reasoning recorded so it can be picked up cleanly.

- **Marketing trust fixes** (original Phase 3, tickets T3.2–T3.12): social proof numbers,
  demo-data fixture, fictional brokerages, legal address, shared layout, 404, tooltips.
  Only prospects see these, and no prospects are being sent there. Terms §4 moves into
  Phase 3; the rest waits.
- **`/for-title-companies`** (original Phase 4). Same reason.

Both become live again the day outreach starts. The tickets are written and still valid.

---

## Immediate Sequence

1. Phase 0 — T0.2 through T0.4 (in flight)
2. Phase 1 — docs purge, with the `9dc446a` cherry-pick amendment to T1.4
3. Phase 2 and Phase 3 in parallel
4. Phase 4 written from `DEFECT_LIST.md`
5. Phases 5 and 6

**Checkpoint:** when Phase 2 delivers `DEFECT_LIST.md`, stop and reassess. That list is the
first honest picture of the product's interior anyone has had, and it may reorder
everything after it.
