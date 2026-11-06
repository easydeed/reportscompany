# TrendyReports Launch Readiness Execution Plan

**Status:** Claude review amendments and Jerry decisions incorporated; execute after PR #272 merges
**Scope:** November 6 audit findings, supporting hardening, and explicit reconciliation of the older backlog
**Planning base:** `821f71ad03587cdc8243f0aaaf59ff698ddc8a50`
**Roles:** Codex and Claude Code build in disjoint lanes and review each other; Codex is Jerry's named merger; Jerry owns policy/launch decisions. [Decisions and file ownership](launch-readiness-2026-11-06/DECISIONS_AND_LANES.md) govern.

Read the [business brief](LAUNCH_READINESS_BRIEF_2026-11-06.md) first. Ticket details are divided into [security and billing](launch-readiness-2026-11-06/01-security-and-billing.md), [reports and delivery](launch-readiness-2026-11-06/02-reports-and-delivery.md), and [operations and acceptance](launch-readiness-2026-11-06/03-operations-and-acceptance.md).

## Hours and scope boundaries

Claude's amended 31 tickets total **164–282 focused engineering hours**. A 20 percent reserve produces **196.8–338.4 hours**, rounded to a planning budget of **200–340 hours**. Working forecast: **220–270 hours**. These are planning estimates, not a fixed-price commitment.

The range includes implementation, meaningful regression proof, review/rework, and scoped deployment verification. It assumes the current architecture remains in use, test-mode access is supplied, and no undocumented billing customization must be preserved. Provider latency and a **3–5 business-day observed pilot** affect elapsed time separately.

The estimate covers all issues identified in the audit, including secondary issues. LR-001 reconciles every currently open/recorded historical entry; new repairs outside this catalog get their own estimate before execution. Re-baseline after LR-001 and again after the dependency upgrade and billing/delivery design work.

## Ticket ledger

Tickets are ready after the reviewed amendments merge, subject to their stated policy/access dependencies. The ticket ID is an execution identifier, not an invented defect-board D-number. LR-001 maps each to existing D-numbers or creates a new documented defect only when required.

Gate definitions: `PILOT` blocks the affected pilot feature; `PAID` blocks accepting subscription payments; `PUBLIC` blocks broad acquisition; `PROCESS` establishes release discipline. An item is not waived merely because another gate opens.

| ID | Ticket | Gate | Hours | Depends on |
|---|---|---|---:|---|
| LR-001 | Reproduce findings and reconcile the full open backlog | PROCESS | 8–14 | Reviewed amendments merged |
| LR-002 | Enforce reviewed releases on main | PROCESS | 2–4 | 001 |
| LR-003 | Patch and reconcile production dependencies | PILOT | 6–12 | 002 |
| LR-004 | Authorize branding deletion by canonical account key | PILOT | 2–4 | 001 |
| LR-005 | Reject throttled work before handler execution | PILOT | 4–7 | 001 |
| LR-006 | Bound anonymous property lookup and provider cost | PILOT | 6–10 | 005 |
| LR-007 | Validate all uploaded image bytes; convert existing SVG logos | PILOT | 4–6 | 004 |
| LR-008 | Neutralize spreadsheet formulas in lead exports | PUBLIC | 2–3 | 001 |
| LR-009 | Revoke older sessions on password changes | PILOT | 4–7 | 001 |
| LR-010 | Add browser response security controls | PUBLIC | 5–8 | 003 |
| LR-011 | Make webhook ingestion durable and retryable | PAID | 8–14 | 001 |
| LR-012 | Reconcile current subscription state and old downgrades | PAID | 8–14 | 011 |
| LR-013 | Enforce approved payment-status entitlements | PAID | 4–7 | 012 and Jerry policy |
| LR-014 | Prevent duplicate subscription creation | PAID | 5–9 | 012, 013 |
| LR-015 | Enforce zero report allowance exactly | PILOT | 3–5 | 001 |
| LR-016 | Serialize schedule-capacity admission | PUBLIC | 4–7 | 001; independent of 015 |
| LR-017 | Consume invitations atomically | PILOT | 2–4 | 001; independent of 009 |
| LR-018 | Use recorded sale prices for sale-derived figures | PILOT | 5–8 | Packet merge; source recheck |
| LR-019 | Persist consumer failures against the actual schema | PILOT | 2–4 | Packet merge; source recheck |
| LR-020 | Claim consumer delivery durably and preserve terminal state | PILOT | 10–18 | 019 |
| LR-021 | Recover agent notifications independently | PILOT | 4–8 | 020 |
| LR-022 | Recover missing PDFs with bounded viewer states | PILOT | 6–10 | 019 |
| LR-023 | Recover committed scheduled work after broker failure | PILOT | 5–9 | 031 |
| LR-024 | Surface wizard failures and stop endless polling | PILOT | 3–5 | Packet merge; independent of 022/023 |
| LR-025 | Match acquisition promises to report behavior | PUBLIC | 1–2 | 018; wording approved |
| LR-026 | Run isolated browser journeys automatically | PUBLIC | 20–30 | Functional tickets, 031 |
| LR-027 | Monitor dependency readiness and stalled outcomes | PILOT | 8–14 | 011, 020, 021, 023 |
| LR-028 | Prove backup restoration and operational recovery | PUBLIC | 6–10 | 001; RTO/RPO approved |
| LR-029 | Measure capacity, vendor limits, and per-report costs | PUBLIC | 6–10 | 003, 006, 020, 023, 027 |
| LR-030 | Complete role-based acceptance and supervised pilot | PUBLIC | 8–14 | All other applicable tickets |
| LR-031 | Match database CI to production and real failure tests | PROCESS | 3–5 | 001 |

## Reviewed implementation lanes

1. **Codex:** LR-001 -> LR-002 -> LR-031 -> security LR-003 through LR-010 -> billing/admission LR-011 through LR-017 -> LR-028/LR-029 (**92–160 h**).
2. **Claude Code:** LR-019 -> LR-018 -> LR-020/LR-021 (one reviewed state design, two PRs) -> LR-022 -> LR-024 -> LR-023 -> LR-025 -> LR-027 -> LR-026 (**64–108 h**).
3. **Joint with Jerry:** LR-030 (**8–14 h**, plus pilot observation).

Each lane works sequentially in its own worktree; the two lanes may run concurrently. Claude can begin LR-019 immediately after the amended packet merges while Codex reconciles LR-001. Dependencies remain real: LR-023 waits for LR-031; LR-027 needs Codex's webhook signal; LR-026 waits for functional work in both lanes. LR-016 and LR-017 are independent of LR-015 and LR-009 respectively; LR-022 needs LR-019 only; LR-024 is independent of consumer-PDF/dispatch tickets.

File ownership is explicit in [decisions and lanes](launch-readiness-2026-11-06/DECISIONS_AND_LANES.md). Codex owns board statuses/counts/new D-numbers. Claude adds evidence and requests status changes. Only one open migration PR across the lanes; both guards move together and the number is claimed in the PR title. Claude's LR-018 edit of property.py precedes Codex LR-015; Codex's workflow edits merge before Claude's E2E workflow work.

If policy or access blocks a ticket, report the concrete input needed and choose another dependency-ready ticket. User-approved decisions in the lane document supersede generic sequential-only repo guidance for this program.

## Ticket workflow

1. Verify current `origin/main` and the exact base SHA. Use an isolated clean worktree and inspect its status; never assume another agent's checkout has the same local state.
2. Read the named files and applicable tests. Use the review's completed reproduction and recheck intervening source changes. If fixed already, close by current evidence rather than rewriting; LR-001 does not block Claude's lane.
3. Confirm the write scope and any migration/provider change in the PR description. Use a branch such as `fix/lr-004-branding-delete-ownership`, cut from current main.
4. Implement one ticket. Import shared behavior; avoid a parallel pipeline. Keep new modules small and separate responsibilities.
5. Test the failure, success, tenant boundary, and replay/concurrency cases relevant to that ticket. A mock alone cannot establish schema compatibility or real database locking.
6. Review the actual staged diff and scope. Commit and push the ticket branch; attach the exact evidence and residual limits.
7. The other lane reviews the full acceptance list. A BLOCK stays blocked until fixed and re-reviewed. The reviewer does not approve its own implementation.
8. Codex, Jerry's named merger, merges only after independent PASS and required checks. Verify the relevant deployed behavior using authorized test identities and recipients. Then start the next ticket in that lane.

## Common acceptance standard

Every implementation PR includes:

- Base SHA, ticket ID, files changed, and the business failure it prevents.
- A regression that fails for the old behavior and passes for the new behavior; use real PostgreSQL for SQL and concurrency guarantees, real local Redis where broker behavior is the subject, and controlled provider fakes for deterministic failure injection.
- Results from affected suites and mandatory CI; web changes include typecheck. A dependency update also includes an actual production build and frozen-lockfile install.
- Rendered changed pages at 390px and 820px, plus a desktop width when the affected layout needs it. Exercise error, empty, loading, and successful states; test keyboard behavior for changed forms.
- Evidence that another tenant's data/assets and the public owner-name boundary remain protected where relevant.
- Migration order, rollout, rollback, and reconciliation of uncertain external effects when applicable. Never blindly resend messages or retry charges after an ambiguous outcome.
- Reviewer PASS, deployed verification result, and updated ticket/defect status. A successful build alone is not deployed functional verification.

For provider delivery, distinguish `accepted` from actually delivered. Do not claim universal exactly-once delivery across a provider/database crash window. Use supported idempotency, durable state, and a visible reconciliation path for uncertain outcomes.

## Migrations and operational changes

Follow [migrations and deploys](../runbooks/migrations-and-deploys.md). Only one open migration PR may exist across both lanes. Claim the number in its title from current main; do not assume 0064 remains available. Keep the API and worker `REQUIRED_MIGRATION` values synchronized and tested.

Each migration PR includes read-only prechecks, exact pending filenames, changes/backfills, verification queries, and an operator runbook. Prepare compatible additive schema before application code relies on it. Where the documented merge/startup-refusal sequence is used, Jerry confirms previous-version retention for every affected Render service, including worker, ticker, and bridge, and the result is recorded before the first migration merges. If it cannot be guaranteed, review a compatible staged rollout first. Do not disable schema guards to hide an incomplete rollout.

Payment, messaging, migration, repository-rule, and infrastructure mutations are separately identified operational steps with before/after evidence. Test-mode providers and isolated data are the default for acceptance. Real delivery checks use approved recipients. No bulk replay, customer-data purge, automatic refunds, production load test, database-IP restriction, or service-tier purchase is implicit in a code fix.

Rollback must preserve durable webhook/delivery/outbox evidence and consent data. Stop new side effects if needed; do not delete the evidence and retry. Reconcile pending/unknown work by its durable identifier before resuming it.

## Policy and operating inputs

The [approved decisions](launch-readiness-2026-11-06/DECISIONS_AND_LANES.md) set payment grace, upgrades/downgrades, single-subscription/portal behavior, manual refunds, grandfathered schedules, lookup budget, recovery targets, wording, SVG conversion/rejection, initiating-device retention, uncertain-send handling, merger/emergency review, and the Pacific Coast pilot cohort.

Still pending: PCT legal consent/retention (four years is not approved), paused/other unaddressed Stripe state policy, visitor identification/shared-IP/outage design, workload/latency/spend ceilings, alert destination/access, and failed-deploy retention confirmation before a migration. The relevant ticket stops at its unresolved decision; independent work can continue.

## Launch acceptance matrix

| Journey or failure | Required result |
|---|---|
| Register, verify, sign in, reset password | Correct account, usable onboarding, and old sessions revoked when required |
| Agent creates each of eight market kinds | Correct filters, trustworthy metrics, branded PDF/email/social output, visible limits |
| Property report across current themes | Recorded-sale rules, requester identity, honest missing data and PDF behavior |
| Homeowner submits by SMS and email | Correct request fields and stored consent; no assessor name; receipt and report verified |
| Two concurrent consumer tasks | One owned send; no duplicate notification/credit charge; ambiguous outcome reconciled |
| Provider refuses or times out | Durable truthful outcome; bounded retry and customer-visible recovery |
| PDF rendering/upload fails after report preparation | Real retry or explicit terminal state; no permanent generating spinner |
| Scheduled publication fails after database commit | Due occurrence remains recoverable and is dispatched without duplicate delivery |
| Purchase/change/cancel/resubscribe | Stripe and account allowance agree through duplicate, old, and replayed events |
| Two requests consume the final schedule slot or invite token | One admission/consumption; correct conflict and capacity behavior |
| Rep/company seat management | Correct role, capacity, deactivation, handover, and cross-company rejection |
| Export/upload/delete | Safe CSV, safe image handling, and exact account ownership |
| Restore and outage | Restored isolated data passes checks; alerts reach the operator; recovery time is recorded |

## Status and handoff

Ticket lifecycle: `proposed` → `ready` → `in_progress` → `review` → `merged` → `verified` → `closed`. Use `blocked` with a concrete dependency and owner; never change status because a test merely exists.

Claude reviewed PR #272 with AMEND, then start; the packet incorporates that review and Jerry's decisions. After merge, Codex starts LR-001 and Claude may start LR-019. Application fixes and production changes remain in their own reviewed tickets.
