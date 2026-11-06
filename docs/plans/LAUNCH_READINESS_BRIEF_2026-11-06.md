# TrendyReports Launch Readiness Brief

**Date:** November 6, 2026
**Owner:** Jerry
**Status:** Reviewed by Claude Code; amendments and Jerry decisions incorporated; ready for merge and execution
**Audit revision:** `28157e74c257efa6e4c7267ee40a8b93dd7c8223`
**Planning revision:** `821f71ad03587cdc8243f0aaaf59ff698ddc8a50`

TrendyReports needs a release-hardening cycle before broad paid acquisition. The core report product and its automated checks have improved substantially. The remaining audit findings affect account isolation, subscription correctness, comparable-sale accuracy, delivery recovery, and complete customer journeys. These findings determine the implementation order.

The planning revision adds only a defect-board note after the audited revision. It changes no application code. Claude checked all 31 tickets at `821f71ad`; premise reproduction is complete at the evidence depth stated in the review. Each builder rechecks current source and any intervening changes before editing, without making Claude's lane wait for LR-001.

## Business outcome

An agent can register, receive the correct allowance, create an accurate branded report, and deliver it once to the intended person. A homeowner can submit consented contact details, receive their report, and download it or see an honest recovery state. A company can manage reps and seats without accessing another company's assets or records. A subscription purchase, change, cancellation, and resubscription produce the correct bill and access. Operators can detect failures, recover work, restore data, and control releases.

Release readiness requires evidence for those outcomes, including concurrent requests and provider failures. Passing a happy-path test or deploying a healthy process does not close an entire journey.

## Scope and effort

The accompanying plan contains **31 tickets**, covering every actionable issue from the November 6 audit and its supporting investigations, plus the controls needed to demonstrate readiness.

| Work | Focused engineering hours |
|---|---:|
| Baseline, backlog reconciliation, and enforced review | 10–18 |
| Dependencies, tenant isolation, abuse controls, sessions, uploads, exports, headers | 33–57 |
| Billing, entitlements, schedule capacity, and invitation consumption | 34–60 |
| Sale-price accuracy, consumer delivery, PDF recovery, dispatch recovery, and UX | 36–64 |
| Automated journeys, monitoring, restore, capacity, release acceptance, and CI parity | 51–83 |
| **Known ticket total** | **164–282** |
| **20 percent contingency** | **32.8–56.4** |
| **Planning budget, rounded** | **200–340** |

An initial working forecast is about **220–270 focused engineering hours**. At 40 focused hours per week, the reserved budget represents roughly **5–8.5 engineer-weeks of total effort**, followed by or including a separately observed **3–5 business-day pilot**. Availability of review, provider accounts, and operators determines calendar duration. The approved two lanes shorten the parallel portion of the calendar; review, shared-file handoffs, the migration slot, and the pilot still constrain elapsed time.

Ticket estimates include diagnosis, implementation, targeted regression tests, review/rework, and a scoped deployment check. LR-030 covers additional cross-system acceptance work; it does not charge those per-ticket checks twice. Passive CI/provider waiting and pilot observation are elapsed time rather than additional engineering hours.

**The estimate is bounded.** The audit board lists 47 open and 84 recorded entries, some historical or obsolete. LR-001 reconciles all of them and maps current issues to this plan. Fixes newly established by that reconciliation require additional priced tickets and a revised total. No live issue is silently deferred, and this estimate does not promise that every historical entry is already covered by a known repair.

## Evidence and proposed response

| Finding | Established evidence | Ticket response |
|---|---|---|
| Vulnerable web dependencies | `next` is pinned at 16.0.7. Production-dependency audit: 4 critical, 29 high, 23 moderate, 5 low advisories. Applicability varies by feature and hosting. | LR-003 updates to a currently patched supported combination and documents residual applicability. |
| Branding deletion crosses accounts | The actual authorization and key-extraction functions passed a foreign object key to mocked storage. | LR-004 authorizes a canonical object key under the caller's exact account prefix. |
| Throttled work still executes | Actual middleware returned 200/429/429 while invoking the mocked handler three times with a limit of one. | LR-005 rejects before execution; LR-006 covers public vendor-backed search. |
| Subscription changes can be lost or applied out of order | Mocked executions acknowledged database failure, let old events replace current plans, and applied an old downgrade after resubscription. | LR-011 through LR-014 repair ingestion, state transitions, payment policy, and checkout. |
| Zero overrides and concurrent admission are unsafe | Source paths allow a zero-limit report and use non-serialized schedule/token checks. | LR-015 through LR-017 add exact boundary and real-database concurrency proof. |
| Asking prices enter closed-sale figures | A closed comp with no sale price and a $950,000 asking price produced a $950,000 sale range through actual functions. | LR-018 separates asking-price display from recorded-sale calculations. |
| Delivery failure recording uses the wrong column | Production has `error_message`; a read-only `SELECT error FROM consumer_reports LIMIT 0` returned SQLSTATE 42703. Worker failure paths use `error`. | LR-019 exercises failures against the migrated schema. |
| Consumer delivery can duplicate and replay can regress state | Two synchronized executions made two mocked SMS calls. A delivered replay returned with status `processing`. | LR-020 adds durable delivery ownership; LR-021 separately recovers agent notification. |
| Missing PDF download never starts generation | Actual download handler queued analytics only and repeatedly returned `generating`; completed delivery with a null PDF is reachable. | LR-022 implements bounded PDF recovery. |
| Failed broker publication loses the occurrence | The schedule advances before publication; the failure path does not durably redispatch it. | LR-023 establishes durable handoff and recovery. |
| Errors leave customers waiting without explanation | Source confirms silent schedule-submit failures and unlimited report polling. | LR-024 provides bounded, useful recovery states. |
| Hardening and wording gaps | Session revocation, SVG validation, CSV formula handling, response headers, and estimate wording require changes. | LR-007 through LR-010 and LR-025. |
| Release and operating proof is incomplete | Manual-only E2E; no enforced main rules; static health response; restore, alerting, capacity, and full billing proof outstanding. | LR-002 and LR-026 through LR-031. |

## Existing protections to preserve

- The audited CI revision passed 3,849 backend tests and 580 frontend tests; backend results also included 33 skips and 15 expected failures.
- Production migration 0063 matches the required schema. Keep both schema guards and the migration runner discipline.
- Seat capacity allocation locks the company row, counts pending invitations, and rejects reductions below held capacity.
- Authentication enforces user deactivation. Lead paths enforce consent and store submitted wording.
- Customer greetings use the requester rather than the record owner. Keep the assessor name out of public rendering and notifications.
- MLS pagination terminates by exact count and affected inventory figures are withheld when data truncates.
- A recent AI 429 logged the explicit narrative fallback. Preserve graceful degradation and truthful output.

## Release gates

**Before a pilot:** all applicable security and accuracy blockers are resolved; consumer failure/replay/PDF paths pass; safe billing is proven before accepting pilot payments; alerts and recovery procedures work. Tickets marked `PILOT` or `PAID` must meet their acceptance criteria before that activity starts.

**Before broad paid release:** all 31 tickets and any additional launch-relevant findings from LR-001 are resolved and independently reviewed. The pilot has no unresolved account-isolation, billing, accuracy, consent, duplicate-delivery, or data-loss defect. Jerry signs the release decision with the evidence linked to its commit and environment.

There is no automatic waiver for a small issue. Any proposed deferral needs Jerry's explicit decision, a customer-impact explanation, an owner, and a revisit date. Until then, it remains in scope.

## Approved decisions and remaining access

Jerry's [decisions and lane ownership](launch-readiness-2026-11-06/DECISIONS_AND_LANES.md) are binding: active/trialing full access; past_due seven days then Free; incomplete/unpaid Free; upgrades immediate/prorated; downgrades at period end; one subscription/customer; manual refunds; grandfather existing schedules; 20 lookups/visitor/hour; RTO four hours/RPO one day; approved report wording; needs-review uncertain sends with no automatic text resend; existing SVG conversion/new SVG rejection; retain the password-change initiating device; Codex as merger; and three to five Pacific Coast pilot agents.

PCT legal still owns consent wording and retention. Four years is an expectation, not an approved duration. Paused-status policy, workload/latency/cost ceilings, trusted visitor-budget design, operator credentials, and failed-deploy retention for each Render service remain explicit inputs for their affected tickets. Historical asking-price reports get a read-only count before any action. No secrets belong in documents or chat; use normal approved sign-in, never a fabricated production admin session.

## Execution agreement

The reviewed [two-lane split](launch-readiness-2026-11-06/DECISIONS_AND_LANES.md) governs. Codex owns LR-001, release controls, database parity, security, billing/admission, restore and capacity. Claude owns reports, delivery, monitoring, and browser journeys. LR-030 is joint with Jerry. Each lane is sequential in its own worktree; cross-lane work may run in parallel. The other lane reviews each PR; Codex is the named merger after independent PASS and required checks.

Codex alone changes defect status tokens/counts/new numbers. At most one open migration PR exists across both lanes; it claims its number in the title and updates both schema guards. Claude's LR-018 property normalization precedes Codex's LR-015 edit of the same route. Required CI/plan shared-file ownership is recorded in the lane document.

This documentation PR changes the plan only. After it merges, Codex starts LR-001 while Claude can start LR-019. Production mutations, historical replays, legal decisions, and the first migration's deploy-retention confirmation remain explicit operational steps.

See [the execution plan](LAUNCH_READINESS_PLAN_2026-11-06.md), [the completed review handoff](CLAUDE_REVIEW_BRIEF_2026-11-06.md), and [Claude's review](https://github.com/easydeed/reportscompany/pull/272#issuecomment-6698368476).
