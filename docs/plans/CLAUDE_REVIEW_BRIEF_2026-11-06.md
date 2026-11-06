# Claude Code Review Brief for Launch Hardening

**Requested action:** Review the proposed brief and ticket plan before implementation. Return PASS or precise amendments. Do not start an overlapping implementation from this handoff.

Jerry requested a complete repair plan after the November 6 readiness audit. The packet is on branch `docs/launch-readiness-2026-11-06`, cut from main at `821f71ad03587cdc8243f0aaaf59ff698ddc8a50`. The audit examined `28157e74`; the additional commit is a defect-board note only.

Read:

1. [Business brief](LAUNCH_READINESS_BRIEF_2026-11-06.md).
2. [Execution plan and 31-ticket ledger](LAUNCH_READINESS_PLAN_2026-11-06.md).
3. [Security and billing acceptance criteria](launch-readiness-2026-11-06/01-security-and-billing.md).
4. [Report and delivery acceptance criteria](launch-readiness-2026-11-06/02-reports-and-delivery.md).
5. [Operations, backlog reconciliation, and launch acceptance](launch-readiness-2026-11-06/03-operations-and-acceptance.md).

## What needs your review

- Recheck the evidence, especially the cross-account storage deletion, after-execution limiter, Stripe transitions, sale/list-price confusion, nonexistent consumer failure column, and delivery ownership under concurrency. Sources and regression criteria are in each ticket.
- Challenge assumptions. Advisory counts do not prove every advisory is reachable; low usage does not prove broken code; mocked provider reproduction does not prove live delivery. Preserve these distinctions.
- Review the proposed durable billing/delivery/dispatch state before implementation. Prefer existing patterns and small additive migrations. Do not promise exactly-once external effects without provider support and a reconciliation path.
- Confirm all audit findings are mapped, including secondary zero-limit, schedule-admission, invite-consumption, CSV/SVG/session/header issues. LR-001 must classify the 47 open/84 recorded older entries and price any additional live repairs.
- Confirm the dependency order and realistic hours: **146–260 focused hours; 180–315 with reserve; working forecast 200–250**. Pilot observation and access waits affect calendar separately.
- Confirm policy questions for Jerry: payment/grace states, supported plan changes, public-lookup budgets, delivery ambiguity, consent/retention, recovery targets, and expected load/cost envelope.
- Review required-check path filtering before enabling repository rules. An unrelated docs PR must not wait forever for a deliberately skipped check.
- Review migration rollout against `docs/runbooks/migrations-and-deploys.md`, especially previous-version retention for background workers. No blanket guard bypass or production migration is authorized by this docs PR.

## Proposed working agreement

Cursor builds each approved ticket on a fresh branch from the then-current main. Claude Code independently reviews the complete acceptance list. A designated merger merges only after PASS and required checks, then verifies the deployed result. Implementation is sequential; read-only investigation may be parallel. Do not implement the next overlapping concern while the current ticket is being reviewed.

Every failure needs observable evidence: actual migrated SQL for column names, two real DB connections for concurrency, deterministic provider failures, and a bounded live check with approved test recipients when appropriate. Update the defect entry from the actual result, not from the existence of a test.

## What to return

1. PASS, or a list of amendments with file/section and rationale.
2. Any finding you could not reproduce or that is already fixed, with current commit evidence.
3. Any missing ticket, dependency, migration constraint, or estimate adjustment.
4. Confirmation of the first implementation ticket: **LR-001**, followed by **LR-002** and **LR-031** before functional repairs.

The packet changes documentation only. Application fixes, configuration changes, migrations, live sends, payment mutations, and historical replays have not started. Once the packet passes review, execute its approved sequence and record completion evidence per ticket.
