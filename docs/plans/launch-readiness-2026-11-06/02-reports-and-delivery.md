# Launch Readiness Reports and Delivery Tickets

**Status:** Reviewed and amended; ready after packet merge. **Builder:** Claude Code. **Reviewer:** Codex.
Scope incorporates Claude review at `821f71ad`; evidence references are from audit commit `28157e74`. The [decisions and lanes](DECISIONS_AND_LANES.md) and [execution plan](../LAUNCH_READINESS_PLAN_2026-11-06.md) defines common verification and rollout rules. Preserve requester identity, approved consent wording, current report themes, and truthful missing-data behavior throughout these tickets.

## LR-018 Keep asking prices out of sale calculations

**Branch:** `fix/lr-018-recorded-sale-prices` · **Gate:** PILOT · **Hours:** 5–8 · **Depends:** Amended packet merged; review reproduction complete.

**Problem and scope:** `apps/worker/src/worker/tasks.py:2568` substitutes list price for missing close price; `consumer_comps_range` then treats it as a sale. Trace consumer normalization through `consumer_report_data.py`, `property_builder.py`, the PDF, and `apps/api/src/api/routes/mobile_reports.py`. Include the agent property PDF path: routes/property.py:864, services/simplyrets.py:184, schemas/property.py:225 also fall back to listPrice; property_builder._v2_closed_prices reads price first. Unknown MLS status is defaulted to Closed at tasks.py:2579/property.py:874; exclude unknown status from sale-derived figures. Share the strict rule instead of adding another calculation. Claude owns this property.py change before Codex LR-015.

**Acceptance:** Closed/sold comps lacking a valid recorded sale price cannot affect sale-derived bounds, medians, or price-per-square-foot figures. Test absent/zero/negative/malformed prices, active comps, mixed data, no comps, and one valid comp. A fixture with no closing price and $950,000 asking price does not produce a $950,000 sale range. Keep asking prices clearly available for appropriate listing display. Render PDF and digital output for current themes with complete and incomplete data; both must agree on truthful figures.

**Rollout:** Jerry requests the read-only affected-report count first, for consumer and agent property paths, with valid/unknown sale/status distinctions. Stored comps retain close_price and list_price separately, so a strict rule can correct rerenders without a data migration. No historical rerender, resend, or notice until the count and a specific decision.

## LR-019 Record delivery failures in the real schema

**Branch:** `fix/lr-019-consumer-failure-schema` · **Gate:** PILOT · **Hours:** 2–4 · **Depends:** Amended packet merged; review reproduction complete.

**Problem and scope:** Worker consumer-failure SQL uses `error` at `tasks.py:2354,2980,2996,3011`; the migrated and live `consumer_reports` table has `error_message`. Repair every failure write/read in this flow, including the outer exception path. Use the existing column unless a demonstrated requirement justifies migration. Do not change tasks.py:3041 for report_generations: that table legitimately has error. Failure bookkeeping currently crashes and can leave processing forever, feeding downstream endless waiting.

**Acceptance:** Integration tests against the fully migrated database exercise email refusal, SMS refusal, missing configuration, missing destination, provider timeout, and an unexpected processing exception. Each stores an honest terminal/retry state and useful bounded error text without leaking contact details or secrets. Retry exhaustion is visible. Successful processing clears obsolete failure information under the chosen state model. A nonexistent-column regression must fail a real SQL test, not merely match text.

**Rollout:** Record counts of stale pending/processing reports read-only. Historical repair or resend is separate from deploying the correct future behavior; preserve all timestamps and consent records.

## LR-020 Claim and reconcile consumer delivery

**Branch:** `fix/lr-020-consumer-delivery-ownership` · **Gate:** PILOT · **Hours:** 10–18 · **Depends:** LR-019.

**Problem and scope:** `tasks.py:2402` uses autocommit; a plain already-delivered check at `:2778` does not serialize sends. Replay also overwrites `sent` with `processing`. Design durable delivery ownership and an attempt journal using the existing provider and database patterns. Separate report generation state from irreversible delivery evidence. Use one conditional UPDATE WHERE eligible RETURNING for the claim. Reuse sms_logs/email_log as attempt journals; propose only the needed additive claim/state columns. Review one shared state model with LR-021 before coding, then ship two PRs. Twilio message create and SendGrid send supply no reliable idempotency key for this design; ambiguous outcomes become needs review, alert the operator, and never automatically resend a text. Only consumer SMS debits a credit.

**Acceptance:** Two real task executions synchronized at delivery produce one owned provider attempt and one credit debit. Test SMS and email; worker death before send, provider refusal, provider acceptance followed by lost response, timestamp-write failure, stale claim, retry exhaustion, and replay of a delivered record. Preserve terminal state and existing delivery timestamps. Use a stable provider idempotency key where actually supported; otherwise put ambiguous outcomes into a visible reconciliation state rather than blindly resending. Record who can resolve ambiguity and what evidence is required.

**Rollout:** Apply Jerry's needs-review policy and inventory provider capabilities and existing attempt records first. No claim of universal exactly-once behavior. Stage schema/code compatibly; stop new sends and reconcile by attempt ID if rollback occurs. Never clear sent timestamps or replay all historical records to test the new flow.

## LR-021 Recover agent notifications independently

**Branch:** `fix/lr-021-agent-notification-recovery` · **Gate:** PILOT · **Hours:** 4–8 · **Depends:** LR-020.

**Problem and scope:** `tasks.py:2784` returns on an existing consumer send before the agent-notification stage at `:2938`. Design this with LR-020 as one state model, ship it in a second PR, and add a separately owned/retryable agent-notification outcome using those primitives. Unknown outcomes remain needs review; never automatically resend an uncertain text. Do not duplicate the delivery subsystem or resend the homeowner's report to recover an agent notification.

**Acceptance:** Consumer already delivered + agent not notified resumes only the notification. Consumer delivered + agent already notified performs neither action. Test concurrent recovery, agent provider refusal/timeout, missing agent phone, worker death between stages, and a change of configured contact. Notifications use requester name or the generic fallback, never assessor name. Agent notifications remain correctly accounted for under the existing credit policy.

**Rollout:** Recovery eligibility and message destination are explicit. Historical notification replay needs a bounded reviewed list and approved recipients; it is not automatic.

## LR-022 Generate missing PDFs and bound viewer waiting

**Branch:** `fix/lr-022-pdf-download-recovery` · **Gate:** PILOT · **Hours:** 6–10 · **Depends:** LR-019 only.

**Problem and scope:** `apps/api/src/api/routes/mobile_reports.py:353` schedules analytics but no PDF task; `MobileReportViewer.tsx:145` polls without a deadline. A successfully delivered report may have no PDF after a non-fatal render failure. Implement a real idempotent PDF recovery path and explicit state/status response, reusing the current report builder. Never enqueue the complete consumer delivery task merely to regenerate a PDF.

**Acceptance:** Existing PDF downloads immediately. A terminal sent report with no PDF queues one generation task and eventually returns its URL or an honest failure. Concurrent clicks create no duplicate jobs. Test rendering failure, object-storage failure, stale generation claim, API/status errors, timeout, page unmount, and retry. Polling stops and the user receives an actionable message. The PDF contains no assessor greeting or invented estimate, and retains the correct account theme. Render loading, ready, failed, and expired states at 390px/820px.

**Rollout:** Preserve working share links and public-access rules. Rate-limit the public recovery action and prevent arbitrary task creation. Do not overwrite historical report content without an explicit versioning decision.

## LR-023 Recover committed scheduled dispatch

**Branch:** `fix/lr-023-durable-schedule-dispatch` · **Gate:** PILOT · **Hours:** 5–9 · **Depends:** LR-031.

**Problem and scope:** `schedules_tick.py:630` advances next_run_at before direct Celery publication; publication failure has no durable redispatch route. The outbox rows already exist: report_generations and schedule_runs are committed as queued; _already_delivered(run_id) at tasks.py:786 deduplicates delivery. Retain commit-before-publication and teach sweep_stale_runs to republish queued, never-started rows instead of failing them. Prefer those durable rows and existing dedupe over a new table. Reuse the queue/worker stack and explicitly distinguish queued from started/uncertain sends.

**November 9 allowance decision:** Claude owns D-332 ticker changes; LR-015 supplies the manual allowance helper. Scheduled sends use schedule capacity, never the manual report allowance. Exhausted or zero manual allowance must not stop an existing schedule. Remove the ticker's manual-usage veto. Update `apps/api/src/api/services/email.py:689–702` limit-reached copy that says scheduled sends are skipped until the 1st, plus its policy comment; preserve the existing truthful warning copy. Coordinate `step-deliver.tsx:44` with Codex so the wizard no longer says every scheduled run consumes a report. Test the email with the existing fake sender, not a real inbox.

**Acceptance:** A broker failure immediately after commit leaves a recoverable occurrence. Restart of the dispatcher eventually publishes it, and duplicate publication cannot duplicate delivery. Test concurrent tickers, crash before/after publication and before recording acknowledgement, stale queued work, disabled schedules, deactivated accounts, changed recipients, allowance exhaustion, and unsubscribe suppression. The same occurrence has one durable identity; skip/failure and retry policies remain visible to operators. Use local Redis/Celery plus real PostgreSQL for the handoff proof.

An account with exhausted manual reports still dispatches its existing active schedule; schedule-capacity admission remains LR-016. Account-email and wizard copy must state the same rule. Do not charge scheduled runs to the manual counter or bulk pause existing schedules.

**Rollout:** No new table is expected. If a concrete recovery invariant needs schema, claim the single migration slot and use the normal runbook. Define bounded retries, stale thresholds, operator reconciliation, and alerting. No bulk activation of the 43 inactive schedules or replay of old scheduled sends.

## LR-024 Show wizard failures and stop endless polling

**Branch:** `fix/lr-024-wizard-failure-recovery` · **Gate:** PILOT · **Hours:** 3–5 · **Depends:** Amended packet merged; independent of LR-022/LR-023.

**Problem and scope:** `apps/web/components/unified-wizard/index.tsx:398` handles errors only for immediate reports; `:225` ignores repeated polling failures. It polls /v1/reports, not the consumer-PDF status endpoint, so this ticket is independent of LR-022/LR-023. Give scheduled creation the same explicit error path and define bounded report-status waiting. Reuse existing verification/limit refusal components rather than erasing those specific responses.

**Acceptance:** Network disconnect, ordinary validation error, 5xx, 401/session expiry, repeated status errors, a slow legitimate job, and terminal generation failure produce distinct useful states. Retry cannot duplicate a previously created schedule/report after a response is lost; reconcile using the endpoint's idempotency/current result where needed. Timers stop on unmount and retry. Preserve form state and accessibility focus. Render changed success/error/loading states at 390px, 820px, and desktop; verify by keyboard.

**Rollout:** No new client-side estimate or price. If safe retry requires an API contract change, document and review the narrow scope rather than introducing a speculative client-only workaround.

## LR-025 Align acquisition wording with report output

**Branch:** `fix/lr-025-report-promise-copy` · **Gate:** PUBLIC · **Hours:** 1–2 · **Depends:** LR-018; wording approved. Legal confirmation gates consent changes, not these literal swaps.

**Problem and scope:** `apps/web/components/marketing/lead-capture.tsx:61` offers an estimate while the report deliberately presents comparable-sale bounds. Cover all four identified locations: marketing/lead-capture.tsx, the live cma-funnel.tsx:212 heading, lead-page-client.tsx:234 default headline, and marketing/property-reports.tsx:49/110 Estimated value copy. Inventory related metadata/transactional wording too. Jerry approved See what homes like yours sold for and Get my report, including the Home Value Page. Replace clear misleading literals with accurate language describing the existing report. The ticket does not introduce a valuation model or change the report product.

**Acceptance:** Active acquisition copy does not promise an estimate the product does not deliver. Correct public titles, previews, and CTA labels agree with the actual result. Preserve approved legal/consent wording verbatim; record the policy owner's confirmation rather than authoring TCPA language. Render each changed page and verify its destination. Distinguish historical Design samples from live customer-facing output.

**Rollout:** Implement the approved wording at all four locations. Consent wording/retention remains with PCT legal; the anticipated four-year period is not approval. Any broader product/marketing decision returns to Jerry with exact alternatives and affected surfaces. No page is marked legally approved by an engineering check.
