# Launch Hardening Decisions and File Ownership

**Authority:** Jerry's November 6 decisions and [Claude Code's review of PR 272](https://github.com/easydeed/reportscompany/pull/272#issuecomment-6698368476).

The review verdict is **AMEND, then start**. All findings hold. The amendments in the ticket packs and execution plan implement the review; this record supplies the approved policy and coordination rules. These explicit two-lane instructions supersede the generic sequential-only rule for this program. Each lane remains sequential and uses a separate worktree.

## Approved decisions

| Topic | Decision | Acceptance consequence |
|---|---|---|
| Active and trialing payment status | Full plan access. | API and worker resolve the same allowance. |
| Past due | Keep plan access for seven days, then Free. | Persist/derive an authoritative grace start; test the seventh-day boundary and recovery before expiry. Replayed events cannot restart grace. |
| Incomplete and unpaid | Free. | Paid price alone does not grant paid access. |
| Upgrades | Effective immediately, prorated. | Stripe test-mode invoice and access state agree. |
| Downgrades | Effective at period end. | Retain paid access through the approved period; worker and API apply the same transition. |
| Duplicate subscriptions | One per customer; another checkout directs the customer to the billing portal. | Handle concurrent customer creation and pending checkout so two Stripe customers/sessions cannot bypass this rule. |
| Refunds | Manual, case by case. | No automatic live refund or cancellation batch. |
| Already over schedule allowance | Existing schedules keep running. No new or reactivated schedules until below the limit. | Enforce create and every reactivation atomically; do not bulk pause existing schedules. Include book handover in the compatibility review. |
| Manual reports versus schedules (November 9) | Scheduled sends use schedule capacity, never the manual report allowance. Exhausting manual reports must not stop an existing schedule. | LR-023 removes the ticker's manual-usage veto; LR-015 supplies manual allowance behavior. Correct account limit-reached email and contradictory wizard copy, with regression proof. |
| Public lookup budget | Twenty lookups per visitor per hour. | Preserve trusted visitor attribution through the web proxy and API. Design shared-IP and spoofing behavior explicitly; changing agent code cannot reset the effective budget. |
| Recovery | Restore service within four hours; lose at most one day of data. | Demonstrate RTO <= 4 hours and RPO <= 24 hours in an isolated restore. |
| Acquisition wording | “See what homes like yours sold for” and “Get my report.” | Cover all four identified locations, including the live Home Value Page. Do not add an estimate model. |
| Historical asking-price reports | Consumer-send question closed November 9: Jerry confirmed all 7 affected consumer reports (March 10–April 13, 2026; 105 comparables) were test sends. No corrected reports go out. | Do not rerender or resend these reports. Agent-report classification/inventory remains separate and provisional; this decision does not close LR-018 implementation/review. |
| Unknown send outcome | Mark `needs review` and alert Codex/the named operator. Never automatically resend an uncertain text. | Keep durable attempt evidence. Twilio message creation and SendGrid send do not offer an idempotency key this design can rely on. Other provider semantics must be verified. |
| Uploaded SVG logos | Convert existing uploaded logos to PNG; block new SVG uploads. | Validate actual bytes for every accepted format. Inventory existing assets; use safe conversion and update active references while preserving previously referenced email/report assets. Bundled trusted Design SVGs remain separate. |
| Password change | Sign out every other device; retain the initiating device. | Issue/retain a valid replacement session without a same-second timestamp revocation bug. Password-reset initiation gets its own valid session according to the existing reset flow. |
| Named merger | Codex for ordinary reviewed merges. | Other-lane PASS is recorded as a PR comment for the current head; applicable checks must pass. No required GitHub approval count. |
| Main protection (November 9) | Required passing checks and PRs; no direct or force pushes. No separate reviewer account or native required approval. | Enforce the final Release gate, PR requirement with zero required approvals, and admin-inclusive direct/force-push restrictions. Review remains the cross-agent process. |
| Emergency merge (November 9) | Jerry is the emergency merger; independent review within 24 hours. | Codex does not use an outage as emergency authorization. Record Jerry's reason, exact SHA, bypass/change used, reviewer and deadline; restore any temporary rule change. |
| Pilot | Three to five Pacific Coast agents. | Stop on any wrong number in a sent report or any data seen across accounts. Other isolation, billing, consent, duplicate-send, or data-loss blockers still prevent expansion. |
| Consent and retention | PCT legal owns the wording and period. “At least four years” is an expectation, not an approved retention policy. | Preserve currently approved wording/evidence. No legal-copy invention or retention purge while the decision is pending. |

## Decisions still needed for the affected ticket

- November 9 scope decision: defer LR-032–LR-051's broader backlog until after the pilot. Bring forward only D-188/D-106/D-168 numeric repairs (Claude after LR-018) and D-014/D-274 read-only production hierarchy/RLS verification (Codex). No full additional backlog budget is approved. New confirmed isolation or wrong-number defects still trigger the pilot stop rule.
- D-332 ownership is settled: Claude LR-023 owns schedules_tick.py and the contradictory account-email copy; Codex LR-015 supplies the manual allowance function and coordinates the wizard copy. The November 9 rule above is approved; it is no longer an open policy question.
- GitHub identity is settled: no separate reviewer account and no required GitHub approval. Preserve the current-head cross-agent PASS comment before an ordinary merge, with passing enforced checks. Jerry alone handles emergencies.
- Paused subscription access and any unaddressed Stripe states require an explicit policy before LR-013 closes. Cancellation follows the approved effective-period rules; do not infer immediate Free from a missing period field.
- Define how the 20-per-visitor budget identifies visitors, handles shared networks, and behaves during limiter outage. The amount is approved; trusted attribution and abuse resistance still need design and review.
- Pilot/launch peak volume, latency ceilings, provider cost/margin targets, and operator alert destination/access must be documented for LR-027/LR-029. Recovery targets and cohort are already approved.
- PCT legal must confirm consent wording and retention. No date-based deletion is authorized by this packet.
- Before the first migration merges, Jerry confirms previous-version retention on failed deployment for every affected Render service, including worker, ticker, and bridge; record the result with the migration runbook.

## Two implementation lanes

| Lane | Sequence | Focused hours |
|---|---|---:|
| Codex | LR-001 -> LR-002 -> LR-031 -> LR-003 through LR-010 -> LR-011 through LR-017 -> LR-028, LR-029 | 92–160 |
| Claude Code | LR-019 -> LR-018 -> LR-020 and LR-021 (one reviewed design, two PRs) -> LR-022 -> LR-024 -> LR-023 -> LR-025 -> LR-027 -> LR-026 | 64–108 |
| Joint with Jerry | LR-030, after both lanes | 8–14 |
| **Total** | **Reviewed estimate** | **164–282** |

Dependencies still apply: Claude can start LR-019 after the amended plan merges, in parallel with Codex's LR-001. LR-023 waits for LR-031. LR-027 waits for Codex's webhook signal and the delivery/dispatch state. LR-026 waits for the functional tickets in both lanes. A lane may choose another dependency-ready ticket while reporting the specific blocker.

## Shared files and coordination

- **Defect board:** Codex alone edits `docs/DEFECT_LIST.md` status tokens, count/severity tables, total, and new D-number allocation. Claude may add evidence prose without changing status. Claude lists “status changes requested” in each PR; Codex applies verified changes in its next board update. Use `scripts/derive.py`'s imported canonical parser; do not maintain another parser or hand-count.
- **Migrations and guards:** At most one open migration PR across both lanes. Claim the number in its PR title before editing. The same PR moves both API and worker `REQUIRED_MIGRATION`. Coordinate additive rollout, deploy retention, and verification before merge.
- **Property route:** `apps/api/src/api/routes/property.py` is shared by Claude LR-018 normalization and Codex LR-015's evaluator call. Claude's LR-018 goes first; Codex waits for its merge and branches again from main before modifying that route.
- **Workflow files:** Codex owns LR-002/LR-031 changes; Claude LR-026 takes them only after those PRs merge. The always-running required gate must be preserved.
- **Worker/state modules:** Claude owns report and delivery changes. Codex billing/limit changes touching `limit_checker.py` coordinate with Claude before any change to common task imports, quota checks, or state helpers. Name overlapping files in each PR before editing; a ticket label alone is not isolation.
- **Plan documents:** Codex owns the brief, estimate/ledger, decisions, and reconciliation ledgers. Claude requests plan/status changes through its review/PR evidence rather than concurrently rewriting them.

Each lane branches from current main, records its base SHA, reviews the other lane's changes, and completes its own ticket before starting its next. Codex's merger role does not substitute for independent review. No production side effect is hidden inside a documentation/status update.
