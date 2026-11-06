# TrendyReports Launch Readiness Execution Plan

**Status:** Proposed; awaiting Claude Code review
**Scope:** November 6 audit findings, supporting hardening, and explicit reconciliation of the older backlog
**Planning base:** `821f71ad03587cdc8243f0aaaf59ff698ddc8a50`
**Roles:** Cursor builds; Claude Code reviews; a designated merger merges; Jerry owns policy and launch decisions.

Read the [business brief](LAUNCH_READINESS_BRIEF_2026-11-06.md) first. Ticket details are divided into [security and billing](launch-readiness-2026-11-06/01-security-and-billing.md), [reports and delivery](launch-readiness-2026-11-06/02-reports-and-delivery.md), and [operations and acceptance](launch-readiness-2026-11-06/03-operations-and-acceptance.md).

## Hours and scope boundaries

The 31 tickets total **146–260 focused engineering hours**. A 20 percent reserve produces **175.2–312 hours**, rounded to a planning budget of **180–315 hours**. Working forecast: **200–250 hours**. These are planning estimates, not a fixed-price commitment.

The range includes implementation, meaningful regression proof, review/rework, and scoped deployment verification. It assumes the current architecture remains in use, test-mode access is supplied, and no undocumented billing customization must be preserved. Provider latency and a **3–5 business-day observed pilot** affect elapsed time separately.

The estimate covers all issues identified in the audit, including secondary issues. LR-001 reconciles every currently open/recorded historical entry; new repairs outside this catalog get their own estimate before execution. Re-baseline after LR-001 and again after the dependency upgrade and billing/delivery design work.

## Ticket ledger

All tickets begin `proposed`. The ticket ID is an execution identifier, not an invented defect-board D-number. LR-001 maps each to existing D-numbers or creates a new documented defect only when required.

Gate definitions: `PILOT` blocks the affected pilot feature; `PAID` blocks accepting subscription payments; `PUBLIC` blocks broad acquisition; `PROCESS` establishes release discipline. An item is not waived merely because another gate opens.

| ID | Ticket | Gate | Hours | Depends on |
|---|---|---|---:|---|
| LR-001 | Reproduce findings and reconcile the full open backlog | PROCESS | 8–14 | Claude packet review |
| LR-002 | Enforce reviewed releases on main | PROCESS | 2–4 | 001 |
| LR-003 | Patch and reconcile production dependencies | PILOT | 6–12 | 002 |
| LR-004 | Authorize branding deletion by canonical account key | PILOT | 2–4 | 001 |
| LR-005 | Reject throttled work before handler execution | PILOT | 4–7 | 001 |
| LR-006 | Bound anonymous property lookup and provider cost | PILOT | 3–5 | 005 |
| LR-007 | Validate or safely convert uploaded SVG assets | PILOT | 3–6 | 004 |
| LR-008 | Neutralize spreadsheet formulas in lead exports | PUBLIC | 2–3 | 001 |
| LR-009 | Revoke older sessions on password changes | PILOT | 4–7 | 001 |
| LR-010 | Add browser response security controls | PUBLIC | 2–4 | 003 |
| LR-011 | Make webhook ingestion durable and retryable | PAID | 8–14 | 001 |
| LR-012 | Reconcile current subscription state and old downgrades | PAID | 8–14 | 011 |
| LR-013 | Enforce approved payment-status entitlements | PAID | 4–7 | 012 and Jerry policy |
| LR-014 | Prevent duplicate subscription creation | PAID | 5–9 | 012, 013 |
| LR-015 | Enforce zero report allowance exactly | PILOT | 2–4 | 001 |
| LR-016 | Serialize schedule-capacity admission | PUBLIC | 3–5 | 015 |
| LR-017 | Consume invitations atomically | PILOT | 3–5 | 009 |
| LR-018 | Use recorded sale prices for sale-derived figures | PILOT | 3–5 | 001 |
| LR-019 | Persist consumer failures against the actual schema | PILOT | 2–4 | 001 |
| LR-020 | Claim consumer delivery durably and preserve terminal state | PILOT | 10–18 | 019 |
| LR-021 | Recover agent notifications independently | PILOT | 4–8 | 020 |
| LR-022 | Recover missing PDFs with bounded viewer states | PILOT | 6–10 | 019, 020 |
| LR-023 | Recover committed scheduled work after broker failure | PILOT | 8–14 | 005 |
| LR-024 | Surface wizard failures and stop endless polling | PILOT | 3–5 | 022, 023 |
| LR-025 | Match acquisition promises to report behavior | PUBLIC | 1–2 | 018 and wording confirmation |
| LR-026 | Run isolated browser journeys automatically | PUBLIC | 10–18 | Functional tickets, 031 |
| LR-027 | Monitor dependency readiness and stalled outcomes | PILOT | 8–14 | 011, 020, 021, 023 |
| LR-028 | Prove backup restoration and operational recovery | PUBLIC | 6–10 | 001 and agreed targets |
| LR-029 | Measure capacity, vendor limits, and per-report costs | PUBLIC | 6–10 | 003, 006, 020, 023, 027 |
| LR-030 | Complete role-based acceptance and supervised pilot | PUBLIC | 8–14 | All other applicable tickets |
| LR-031 | Match database CI to production and real failure tests | PROCESS | 2–4 | 001 |

## Recommended implementation sequence

Dependency independence does not authorize concurrent implementations. This sequence front-loads protections and fast correctness fixes while leaving the larger state machines for focused review.

1. **Establish the baseline and release process:** 001 → 002 → 031.
2. **Close immediate security exposure:** 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010 → 017.
3. **Close report and delivery correctness:** 015 → 018 → 019 → 020 → 021 → 022 → 023 → 024 → 016 → 025.
4. **Make paid state coherent:** 011 → 012 → 013 → 014.
5. **Prove the release:** 027 → 026 → 028 → 029 → 030.

If policy or access blocks a ticket, choose another dependency-ready ticket after reporting the blocked requirement. Never guess a billing, legal, retention, or refund policy to keep moving.

## Ticket workflow

1. Verify current `origin/main` and the exact base SHA. Use an isolated clean worktree; the existing working folder contains unrelated edits.
2. Read the named files and applicable tests. Reproduce the reported premise. If fixed already, close the ticket by current evidence rather than rewriting it.
3. Confirm the write scope and any migration/provider change in the PR description. Use a branch such as `fix/lr-004-branding-delete-ownership`, cut from current main.
4. Implement one ticket. Import shared behavior; avoid a parallel pipeline. Keep new modules small and separate responsibilities.
5. Test the failure, success, tenant boundary, and replay/concurrency cases relevant to that ticket. A mock alone cannot establish schema compatibility or real database locking.
6. Review the actual staged diff and scope. Commit and push the ticket branch; attach the exact evidence and residual limits.
7. Claude Code reviews the full acceptance list. A BLOCK stays blocked until fixed and re-reviewed. The reviewer does not approve its own implementation.
8. The designated merger merges only after PASS and required checks. Verify the relevant deployed behavior using authorized test identities and recipients. Then start the next ticket.

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

Follow [migrations and deploys](../runbooks/migrations-and-deploys.md). Reserve migration numbers from main when each ticket starts; do not assume 0064 remains available. Keep the API and worker `REQUIRED_MIGRATION` values synchronized and tested.

Each migration PR includes read-only prechecks, exact pending filenames, changes/backfills, verification queries, and an operator runbook. Prepare compatible additive schema before application code relies on it. Where the documented merge/startup-refusal sequence is used, verify previous-version retention for every affected service, including background workers, before the merge. If it cannot be guaranteed, review a compatible staged rollout first. Do not disable schema guards to hide an incomplete rollout.

Payment, messaging, migration, repository-rule, and infrastructure mutations are separately identified operational steps with before/after evidence. Test-mode providers and isolated data are the default for acceptance. Real delivery checks use approved recipients. No bulk replay, customer-data purge, automatic refunds, production load test, database-IP restriction, or service-tier purchase is implicit in a code fix.

Rollback must preserve durable webhook/delivery/outbox evidence and consent data. Stop new side effects if needed; do not delete the evidence and retry. Reconcile pending/unknown work by its durable identifier before resuming it.

## Decisions to resolve before dependent tickets

| Decision | Required result | Ticket |
|---|---|---|
| Billing status policy | Approved allowance for active/trialing/past_due/unpaid/incomplete/paused/canceled, duration of grace, and cancellation effective time | 013 |
| Subscription changes | Change-plan behavior, pending-checkout behavior, duplicate-subscription reconciliation and refund authority | 014 |
| Public lookup allowance | Per-IP/page and global budgets, outage response, and acceptable shared-IP impact | 006 |
| Delivery recovery | Supported provider idempotency and operator resolution for uncertain sends | 020, 021 |
| Consent and retention | Approved wording and retention, without engineering-authored legal copy | 025, 030 |
| Recovery targets | Acceptable recovery time and data-loss window, backup retention, authorized operators | 028 |
| Capacity and costs | Pilot/launch volumes, peak concurrency, latency and vendor spend ceilings | 029 |

Builders can prepare concrete options and tests before these decisions. They cannot silently select business/legal policy.

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

The docs-only PR is for Claude to review scope, evidence strength, architecture choices, dependencies, hours, and policy decisions. After that review, LR-001 starts. No application fixes or production changes are part of this packet.
