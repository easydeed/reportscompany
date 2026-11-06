# Launch Readiness Operations and Acceptance Tickets

**Status:** Reviewed and amended. **Owners:** Codex LR-001/002/028/029/031; Claude LR-026/027; joint LR-030. **Reviewer:** The other lane. **Decision owner:** Jerry.
The [decisions and lanes](DECISIONS_AND_LANES.md) and [execution plan](../LAUNCH_READINESS_PLAN_2026-11-06.md) governs all tickets. An operational ticket needs recorded before/after results and a recovery procedure even when it changes no application code.

## LR-001 Reproduce the baseline and reconcile the backlog

**Branch:** `fix/lr-001-launch-baseline` · **Gate:** PROCESS · **Hours:** 8–14 · **Depends:** Reviewed amendments merged in PR #272.

**Problem and scope:** The audit used commit `28157e74`; the board lists 47 open and 84 recorded entries, including some obsolete claims. Read `docs/DEFECT_LIST.md`, its count parser/tests, existing plans, and audit evidence. Map every live audit issue to an existing D-number or a new evidence-backed entry without duplicating records. Classify every older open/recorded entry as current, superseded, gated, unverified, or requiring investigation; link the reason and owner.

**Acceptance:** Reproduce priority failures on current main using safe fakes or isolated data; distinguish source, in-memory reproduction, real-schema proof, provider test, and deployed observation. Keep an explicit ledger for entries not yet verified; never close by age or absence of recent usage. Current launch-relevant gaps outside these 31 tickets get scoped follow-on tickets, hours, dependencies, and an updated total. Codex alone owns status tokens, D-number allocation, count/severity tables, and totals. Claude adds evidence only and requests status changes in PR descriptions. Import the existing canonical parser used by scripts/derive.py; no second parser. Correct the accepted prose to list D-360 as well as D-184. Verify derived board counts and xfail links. Record the exact baseline CI, migrations, and deployed service revisions.

**Boundary:** This ticket classifies the full backlog and closes only what current evidence proves. It does not promise to reproduce 131 unrelated mechanisms within 8–14 hours; unresolved verification becomes explicit estimated work. No implementation fixes are mixed into this documentation ticket.

## LR-002 Enforce review and checks on main

**Branch:** `fix/lr-002-required-release-checks` · **Gate:** PROCESS · **Hours:** 2–4 · **Depends:** LR-001 and repository admin access.

**Problem and scope:** Main had neither traditional branch protection nor repository rules. Configure reviewed PRs, required applicable checks, stale-approval handling, and a narrow documented emergency path. Read existing path filters before making checks required: a check skipped by path filtering must not leave unrelated docs-only PRs permanently blocked. Build an always-running gate first, with conditional jobs and correct change detection. Lockfiles, .nvmrc, e2e/, and packages/ currently trigger no CI and must be classified. Verify actual protection/rulesets from the platform rather than the repository alone.

**Acceptance:** An unreviewed or failing PR cannot merge through the ordinary builder account. Relevant backend/frontend checks run, and unrelated documentation PRs remain mergeable after their required review. Record effective rules via API, bypass actors, and a harmless draft/test PR result. No self-approval substitutes for independent review. Codex is Jerry's named merger. Emergency bypasses record the reason/SHA and receive independent review within 24 hours; ordinary merges keep prior PASS and checks.

**Rollout:** Repository changes are an explicit operational action with a reversible configuration record. After LR-026 supplies a stable browser gate, require it on the intended PRs. Do not lock out the designated operator without a documented recovery route.

## LR-026 Automate complete customer journeys

**Branch:** `fix/lr-026-automated-customer-journeys` · **Gate:** PUBLIC · **Hours:** 20–30 · **Depends:** Functional tickets and LR-031.

**Problem and scope:** `.github/workflows/e2e.yml` is manual-only. Provision or identify an isolated environment with controlled database/Redis and deterministic vendor doubles. Read `e2e/*` and `playwright.config.ts`; replace aspirational skipped tests with executable journeys, then enable automatic appropriate PR triggers. The four current specs contain 15 smoke tests; playwright.config.ts currently defaults to the production web host and built-in credentials, while Stripe specs create checkout sessions. The first change must default to nonproduction, remove credential fallbacks, and fail closed when safe test configuration is absent. CI must never point a write-capable suite at production by default.

**Acceptance:** Regular, sponsored, rep, company, and admin journeys use their real role boundaries. Cover signup/verification/reset, onboarding, report create/download/share, schedule admission, public consented capture by SMS/email, seat/invite/deactivation, and checkout/webhook transitions in test mode. Seed repeatable nonproduction identities without secret leakage. Fail fast for missing configuration. Retain traces/screenshots and failing request identifiers without exposing PII. Deliberately break a route/refusal to prove the required gate fails. Keep live-provider contract checks separate from deterministic per-PR runs.

**Rollout:** Validate from a GitHub-hosted runner before requiring the check. Track flaky tests as failures to repair, not blanket retries, exclusions, or permanent skips.

## LR-027 Monitor readiness and customer outcomes

**Branch:** `fix/lr-027-operational-alerts` · **Gate:** PILOT · **Hours:** 8–14 · **Depends:** LR-011, LR-020, LR-021, LR-023.

**Problem and scope:** `/health` returns a static success/schema response; logs alone do not demonstrate an operator receives an alert. Keep liveness cheap and add a bounded dependency-readiness signal where useful. Claude owns the report/send/dispatch signals; Codex supplies the webhook-backlog signal. Monitor queue age, ticker heartbeat, stale report/send attempts, webhook failures/backlog, provider refusal rates, unknown needs-review outcomes, and persistent rendering errors. Use the existing platform/stack before adding a new service.

**Acceptance:** Inject a database outage, broker outage, stopped ticker, stranded job, failed webhook, and provider refusal in the isolated environment. Readiness and alerts distinguish the failure without conflating it with auth rejection. Alerts reach a named operator with correlation ID, consequence, and recovery link. No contact details, tokens, full payment bodies, or property-owner names leak into telemetry. Measure alerts against approved thresholds and test recovery/noise behavior. Frontend API-outage errors remain useful.

**Rollout:** Document thresholds, retention, escalation, and cost. Never make a provider outage cause a destructive restart loop. Prove an alert is received, not merely configured, before closure.

## LR-028 Demonstrate backup restoration and recovery

**Branch:** `fix/lr-028-restore-recovery-runbook` · **Gate:** PUBLIC · **Hours:** 6–10 · **Depends:** LR-001 and authorized operator; RTO four hours/RPO one day approved.

**Problem and scope:** A successful restore and measured recovery targets were not established. Inventory database backup/PITR settings, storage durability/versioning where applicable, secrets/config recovery, operator access, and dependencies needed for a restored system. Inspect actual settings rather than assuming a provider plan includes a feature. Include the externally open database allowlist in the access review; identify dependencies before narrowing it.

**Acceptance:** Restore an approved backup to an isolated target and prove recovery within four hours with at most one day of data loss (RTO <= 4h, RPO <= 24h). Verify schema, tenant boundaries, consent records, paid state, current report links, durable dispatch/send records, and application startup. Restored workers cannot emit old emails/SMS or replay billing effects. Test the chosen rollback/recovery procedure and record its operator and date. List any recovery target that the current plan cannot meet and price the change.

**Rollout:** No overwrite of production, bulk deletion, or unapproved infrastructure purchase. Jerry decides HA/retention/tier changes from measured requirements. Clean up the disposable restore only after verifying its exact target and retention decision.

## LR-029 Measure capacity and unit costs

**Branch:** `fix/lr-029-capacity-and-cost-proof` · **Gate:** PUBLIC · **Hours:** 6–10 · **Depends:** LR-003, LR-006, LR-020, LR-023, LR-027; agreed workload.

**Problem and scope:** Recent production activity does not demonstrate burst capacity. Define the expected pilot and launch accounts, concurrent generation, scheduled send burst, public searches, and provider quotas. Measure the current infrastructure with realistic data and rendering sizes; determine per-report and per-lead vendor, PDF, storage, email, SMS, and optional AI cost where observable.

**Acceptance:** Controlled isolated load captures p50/p95/p99 latency, queue delay, failures, memory/connection saturation, vendor throttling, delivery lag, and duplicate suppression. Verify shared vendor limits across workers rather than treating each worker's budget as the total. Simulate expensive/incomplete-data reports and outage/recovery. Compare measured cost and capacity with plans and Jerry's target margin/latency. Document a supported launch envelope and stop thresholds.

**Rollout:** Start with provider doubles, then a bounded approved vendor sample. No stress test against production or uncapped chargeable requests. Infrastructure upgrades need a priced operator decision; a small tier alone does not prove inadequate capacity.

## LR-030 Complete acceptance and observe the pilot

**Branch:** `fix/lr-030-launch-acceptance` · **Gate:** PUBLIC · **Hours:** 8–14 plus 3–5 business days elapsed · **Depends:** All other applicable tickets and backlog additions.

**Problem and scope:** Individual fixes do not establish a complete working release. Use the execution plan's acceptance matrix with approved test identities and actual deployed revisions. Confirm the regular, sponsored, rep, company, and platform-admin boundaries and first-run flows. Verify outputs rather than only response codes.

**Acceptance:** Exercise all eight market kinds and the current property themes; review filters/metrics, PDF/email/social branding, browser/tab/favicon, mobile and desktop pages, public lead fields/consent, SMS/email receipt, download recovery, unsubscribe, limits, seat handover, and Stripe test lifecycle. Include failure and replay cases from the tickets. Inbox/handset receipt and provider acceptance are recorded separately. Demonstrate signed-out, wrong-role, and cross-account refusals. Run the approved restore/alert/capacity checks without destructive production tests.

**Pilot:** Use three to five Pacific Coast agents, an agreed workload, and the named operator for 3–5 business days. Stop on any wrong number in a sent report or any data seen across accounts. Configure short test cadences instead of waiting for a month; do not indiscriminately activate existing schedules. Count attempted/completed/failed/unknown outcomes and reconcile each discrepancy. Record pilot costs and support issues. Any isolation, billing, sale-accuracy, consent, duplicate-send, or data-loss defect stops expansion and becomes a repair ticket.

**Exit:** Claude gives a final evidence-based review, and Jerry signs broad launch. All unresolved live issues have a repair or Jerry's explicit documented risk decision; a green build alone cannot open the gate.

## LR-031 Match database CI and exercise real SQL

**Branch:** `fix/lr-031-database-ci-parity` · **Gate:** PROCESS · **Hours:** 3–5 · **Depends:** LR-001.

**Problem and scope:** `.github/workflows/backend-tests.yml` uses PostgreSQL 16 with a comment claiming production parity; production is 17.9. Establish the production-supported test version, update that assertion, and ensure a new database is migrated with the same runner. Retain a version matrix only when intentionally supported. Nine API suites already fail when the CI database is missing, and test_ci_runs_the_database_suites.py guards the workflow; preserve that work. Extend explicit required-CI behavior to db_session, tenant-isolation suites, and roughly 27 remaining skip-only files rather than claiming no guard existed.

**Acceptance:** Full migrated-schema tests run in required CI against the production major version. Core failure-path suites cannot silently skip their database proof when an environment variable is missing. Preserve throwaway databases for suites that construct schemas and keep real service credentials out of CI logs. New SQL/locking regressions from subsequent tickets execute against this service; mocks remain useful for provider injection, not as substitutes for schema validation.

**Boundary:** This three-to-five-hour ticket extends existing database guards; it does not convert every historical text-assertion test. LR-019 and the state/concurrency tickets own their specific integration tests. LR-001 identifies any broader verification gaps that need additional tickets.
