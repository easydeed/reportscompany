# LR-001 baseline and backlog reconciliation

Status: review required. Owner: Codex. Reviewer: Claude Code. Branch: `fix/lr-001-launch-baseline`, cut from merged PR #272 at `fd859a28fc7e723bd42f7e58adef9a225b565a84`.

## What this establishes

All 131 entries that were open or recorded on the frozen board have individual evidence, a classification, proposed next action and scope/effort where outside the launch tickets. The canonical board status is deliberately retained for historical closure candidates until independent review and any missing reproduction. No issue is closed merely because its renderer was replaced.

| Classification | Entries | Meaning |
| --- | ---: | --- |
| Current source | 83 | Mechanism exists; production impact is not automatically established. |
| Superseded source | 21 | Specific historical implementation replaced; review and remaining output proof still required. |
| Unverified | 11 | Named missing observation or reproduction, not presumed fixed. |
| Decision | 16 | Product, policy or data-contract decision needed before implementation. |
| Total | 131 | Exact frozen open/recorded set, with no omission or duplication. |

Evidence: [part 1](LR-001_BACKLOG_1.md), [part 2](LR-001_BACKLOG_2.md), [part 3](LR-001_BACKLOG_3.md), [part 4](LR-001_BACKLOG_4.md). The [31-ticket mapping](LR-001_FINDING_MAP.md) connects the launch program to canonical defects without duplicate allocations.

D-191's investigator lacked hosted-CI evidence; the hosted results below supply a green baseline but do not establish mandatory release checks. Its historical status remains for review. Proposed follow-ups sharing a name represent one scope, not additive estimates: notably schedule editing, MLS parameters, city handoff and onboarding. LR-024 covers the unified wizard, not every mutation handler. LR-021 recovery does not add a new agent-email feature. Do not silently absorb those gaps into the original estimate.

## Fresh read-only production observations

Observed 2026-11-06 against mr-staging-db; no migrations, sends, provider mutations or customer edits.

| Check | Observed result |
| --- | --- |
| Latest applied migrations | 0063 (Nov 4), 0062 (Oct 30), 0061 (Oct 29). |
| consumer delivery error column | `error_message` is the schema field. Current worker references `error` (D-378/LR-019); schema observation is distinct from executing a failure path. |
| Last 30 days | report_generations 1; consumer_reports 0; schedule_runs 0; email_log 0. |
| Active schedules | 0. Low activity is not launch/load proof. |
| API live revision | `28157e74`, deploy `dep-dbn4l3dckfvc73f8ldg0`. |
| Worker live revision | `15b80ddd`, deploy `dep-dbma6qijnfac73d7bl1g`. |
| Ticker / bridge live revision | `15b80ddd`, deploys `dep-dbma6qijnfac73d7bljg` / `dep-dbma6qijnfac73d7blr0`. |
| Worker code difference to frozen main | No difference under apps/worker between 15b80ddd and fd859a28; revision age alone is not missing code. |
| Main protections | Effective branch rules empty; repository rulesets empty. LR-002 remains necessary. |
| Backend hosted CI | Successful runs [42304286379](https://github.com/easydeed/reportscompany/actions/runs/42304286379) at 821f71ad and [42299378600](https://github.com/easydeed/reportscompany/actions/runs/42299378600) at 28157e74. |
| Frontend hosted CI | Successful run [42299378248](https://github.com/easydeed/reportscompany/actions/runs/42299378248) at 28157e74. |

Hosted results are dated observations, not runs of every test against fd859a28. Local investigator suites are identified in each row. Windows property render attempts encountered unsupported date formatting at property_builder.py:2899 and path assumptions; these failures do not prove Linux production failures or complete visual verification. LR-031 must record platform requirements; LR-030 still needs successful rendered acceptance.

## Board changes

Twenty-eight new entries D-361–D-388 record the reviewed launch gaps. Existing D-069 is reopened for consumer-delivery concurrency, D-330 for swallowed errors, and D-347 for schedule reactivation admission; D-347 is WRONG rather than cosmetic. D-360 is added to accepted summary prose. No application fix is included.

Derived totals: 388 entries; fixed 213, open 75, closed-not-live 12, duplicate 1, accepted 2, recorded 85. Open severity: BROKEN 9, WRONG 39, FRAGILE 27, ROUGH 0. Canonical parser and count tests are authoritative.

## Review gate and remaining work

This is a reconciliation candidate, not full LR-001 acceptance. Before closing LR-001, Claude must review the mappings/closure candidates and agree which uncovered current defects block launch. The follow-up rows provide individual provisional hours and dependencies; overlapping scopes require consolidation and an updated approved total before implementation. The original working forecast remains 220–270 hours for the amended 31-ticket program only; it is not an all-backlog quote. No unsupported sum of 131 estimates is presented as a budget.

Remaining reproduction includes deployed RLS role/policies, failed worker-child recovery, vendor date boundaries, stale image output, consent/retention decisions and actual customer journeys. No production test lead, message or checkout was created to supply this evidence. Until that work is agreed, LR-001 stays in review and LR-002/LR-031 implementation does not begin.
