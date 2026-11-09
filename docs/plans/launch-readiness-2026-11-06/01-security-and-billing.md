# Launch Readiness Security and Billing Tickets

**Status:** Reviewed and amended; ready after packet merge. **Builder:** Codex. **Reviewer:** Claude Code.
Scope incorporates Claude review at `821f71ad`; evidence references are from audit commit `28157e74`; re-read current main before implementation. The [decisions and lanes](DECISIONS_AND_LANES.md) and [execution plan](../LAUNCH_READINESS_PLAN_2026-11-06.md) supplies the common testing, review, migration, rollout, and completion rules. Each ticket is one branch and one logical PR. Intentional dependency lockfile changes are part of LR-003; incidental lockfile drift is excluded from every other ticket.

## LR-003 Patch production dependencies

**Branch:** `fix/lr-003-patched-dependencies` · **Gate:** PILOT · **Hours:** 6–12 · **Depends:** LR-002.

**Problem and scope:** `apps/web/package.json`, root/workspace manifests, and `pnpm-lock.yaml` pin Next 16.0.7 and affected dependencies. The scan returned 61 advisories, whose applicability differs. Inspect all lockfile consumers, including `packages/ui`, the root npm lock used by backend CI, and the independent lockfiles in `emailpreview/`, `reportsbuilder/`, and `scheduledreports/` (which pin Next 16.0.10). Establish whether those apps deploy. Claude found 43 Next advisories including all four critical; its reviewed minimum was 16.4.1, not a substitute for checking the currently patched release. Update to a currently patched supported Next/React combination, not merely the first historical fix. Preserve the existing design and framework structure.

**Acceptance:** Frozen-lockfile install, production web build, typecheck, frontend suites, and relevant backend render checks pass. Retain before/after audit reports; classify each residual production advisory by reachable feature, upstream resolution, and owner. No reachable critical/high issue closes by a severity downgrade alone. Render rail, landing, login, authenticated creation, public report, and social/PDF-related paths. Confirm request handlers, cookies, routing, fonts, and browser compatibility survive the upgrade.

**Rollout:** Deploy the reviewed dependency set as a unit. Revert the release if journeys regress; do not leave mixed manifests and lockfiles. A major compatibility surprise triggers re-estimation, not a framework rewrite in this ticket.

## LR-004 Enforce branding object ownership

**Branch:** `fix/lr-004-branding-delete-ownership` · **Gate:** PILOT · **Hours:** 2–4 · **Depends:** LR-001.

**Problem and scope:** `apps/api/src/api/routes/upload.py:75` checks whether the account ID occurs anywhere in a URL; `services/upload.py:186` extracts the deletion key independently. Replace this with one canonical key parser and exact authenticated-account prefix authorization. Inspect all callers before altering the helper signature.

**Acceptance:** Own objects remain deletable. Another tenant's key is rejected even when the caller ID appears in a hostname, username, query, encoded segment, or unrelated path. Reject malformed/foreign origins and ambiguous keys. Assert the fake storage client's delete method is never called for a foreign key. Test existing accepted URL formats explicitly instead of silently breaking legitimate assets. Hostname and arbitrary path-prefix insertion are reproduced foreign-key vectors; query/fragment insertion only yielded a nonexistent key in the review. A missing object must not be reported as successfully deleted.

**Rollout:** No storage migration or real-object deletion is required. Verify a disposable own-account asset and rejection using approved test accounts; preserve customer branding URLs.

## LR-005 Reject rate-limited requests before execution

**Branch:** `fix/lr-005-preexecution-rate-limit` · **Gate:** PILOT · **Hours:** 4–7 · **Depends:** LR-001.

**Problem and scope:** `apps/api/src/api/middleware/authn.py:387` calls the route before returning a throttle response. Move the decision ahead of side effects while preserving honest rate headers and the explicitly chosen Redis-outage behavior. Keep account authentication and per-product allowance checks distinct. Correct the token-bucket comment: this is a fixed one-minute window. Explicitly verify a 429 does not copy handler Set-Cookie or Content-Length headers.

**Acceptance:** With limit one, three requests cause one handler execution and responses 200/429/429. Assert zero uploads, SQL mutations, task publications, and provider calls for refused requests. Test boundary/reset behavior, concurrent requests using local Redis, normal headers, and Redis-outage handling. A 429 must not inherit a successful handler's cookie or misleading content headers.

**Rollout:** Verify the rejection with a harmless test handler/account. Do not generate chargeable work or deliberately flood production. Observe unexpected throttle rates after deploy.

## LR-006 Bound public property searches

**Branch:** `fix/lr-006-public-lookup-budget` · **Gate:** PILOT · **Hours:** 6–10 · **Depends:** LR-005; 20/visitor/hour approved; visitor/outage design reviewed.

**Problem and scope:** `routes/lead_pages.py:230` invokes vendor lookup anonymously; the global limiter skips requests without an account. Add shared limits for the real search endpoint and vendor budget, covering direct API access as well as web proxies. The Next search proxy currently does not forward visitor IP; the /request per-IP check shares that flaw. Inspect deployed uvicorn forwarded-header configuration, which is not recorded in the repo. Establish a trusted forwarding chain; never trust arbitrary client headers.

**Acceptance:** Repeated requests across workers reach the shared limit before vendor execution. Verify per-page/global budgets, response headers, cooldown, and no PII in keys or errors. Test shared-IP behavior, altered agent codes, spoofed headers, and limiter outage. Valid nearby requests remain usable. Confirm what any platform edge limit covers; it cannot substitute for an unverified application assumption.

**Decision:** Jerry approved 20 lookups per visitor per hour. Document trusted visitor identification, shared-network fairness, additional page/global vendor budgets, and outage behavior before enabling it. The /request check must receive the same correct visitor attribution. Vendor calls for the test use a fake or approved sandbox.

## LR-007 Make SVG upload handling safe

**Branch:** `fix/lr-007-safe-branding-images` · **Gate:** PILOT · **Hours:** 4–6 · **Depends:** LR-004.

**Problem and scope:** `services/upload.py:53` skips SVG image parsing and later derives response MIME type from the filename. Validate actual bytes for every accepted format, not just SVG: the review stored non-image bytes declared as SVG and named .gif as image/gif. Jerry approved blocking new SVG uploads and converting existing uploaded SVG logos to PNG. Preserve Design's trusted bundled SVGs; this ticket concerns untrusted uploads.

**Acceptance:** MIME/extension disagreements, oversized input, scripts, event attributes, external references, XML entities, and malformed SVG cannot become active trusted content. Ordinary approved images remain usable in the web UI and report renderers. Verify response content type and storage handling, and render an uploaded logo in the actual consumer.

**Rollout:** Inventory existing SVG uploads and active references first, then use safe rasterization and update active references to PNG with a reviewed rollback. Preserve previously emailed/referenced asset URLs and original evidence; do not delete historical assets or create a path for unsafe SVG execution during conversion.

## LR-008 Neutralize formulas in CSV exports

**Branch:** `fix/lr-008-safe-lead-csv` · **Gate:** PUBLIC · **Hours:** 2–3 · **Depends:** LR-001.

**Problem and scope:** `routes/leads.py:619` sends public form values directly to `csv.writer`. Add one export-boundary neutralizer and reuse it for both the normal lead export and the cross-account admin export at `routes/admin.py:3513`. Preserve stored customer text and valid numeric/date columns; this is an export representation change.

**Acceptance:** Formula-leading text, including leading whitespace/control characters, does not execute as a formula in supported spreadsheet software. Test `=`, `+`, `-`, `@`, tab/newline prefixes, quotes, commas, and Unicode; distinguish actual numeric cells from arbitrary text. Verify normal names, international phone numbers, multiline messages, and row/column fidelity. Document the chosen safe representation.

**Rollout:** A generated fixture export is sufficient; no real leads need exporting. Include evidence from the supported spreadsheet viewer or explicitly record the remaining compatibility check.

## LR-009 Revoke sessions after password changes

**Branch:** `fix/lr-009-password-session-revocation` · **Gate:** PILOT · **Hours:** 4–7 · **Depends:** LR-001.

**Problem and scope:** Password change/reset updates `password_changed_at`, but authentication does not compare token issuance with it. Read all six token issuers and middleware, including seven-day register/invite tokens. JWT iat is whole seconds while password_changed_at has microseconds. Correct the false revocation promise at users.py:216; investigate authn.py:229 allowing requests through during a DB outage. Define migration-free compatibility where possible; otherwise propose additive schema with the normal guards. Preserve existing deactivation and blacklist enforcement.

**Acceptance:** Sessions minted before a password change or reset are rejected afterward; sessions intentionally minted after it work. Test same-second timestamps, missing/invalid issuance claims, multiple devices, logout, disabled users, and database outage. Jerry approved signing out every other device while retaining the initiating device. Prove its replacement token remains valid even when issued in the same request/second. Password reset follows its existing initiating-session behavior without retaining old devices. API keys follow their own documented policy, not accidental JWT behavior.

**Rollout:** Test against a disposable user with the real authentication stack. Never mint a fabricated production admin token. Document any intentional one-time sign-in impact for legacy tokens.

## LR-010 Set browser security headers

**Branch:** `fix/lr-010-browser-security-headers` · **Gate:** PUBLIC · **Hours:** 5–8 · **Depends:** LR-003.

**Problem and scope:** Live web responses lacked CSP, framing control, nosniff, and an explicit referrer policy. Inspect `apps/web/next.config.ts`, middleware, external fonts/maps, public report embeds, and Next script behavior. Set the headers through next.config headers(), because middleware only matches /app and /admin. Preserve same-origin report frames with frame-ancestors self. Begin CSP in report-only mode and investigate the observed access-control-allow-origin wildcard rather than presuming it is needed.

**Acceptance:** Verify headers on production-like responses and document public/embedded route exceptions. Test login, dashboards, maps, reports, previews, uploaded assets, and sharing. CSP uses an approach compatible with the framework; evaluate violations before enforcement. No blanket unsafe policy is presented as effective protection.

**Rollout:** Use report-only CSP where needed, then enforce the validated policy. Confirm legitimate embeds and report generation are still possible. Any exception is narrow and explained.

## LR-011 Make Stripe event ingestion durable

**Branch:** `fix/lr-011-retryable-stripe-events` · **Gate:** PAID · **Hours:** 8–14 · **Depends:** LR-001.

**Problem and scope:** `routes/stripe_webhook.py:130` acknowledges database exceptions as success. Design the smallest durable receipt/processing record using Stripe event IDs and existing DB patterns. Keep signature validation. Use explicit non-2xx retry behavior when receipt cannot be persisted; acknowledge only durably accepted work under a documented processing model.

**Acceptance:** Test invalid signature, missing configuration, missing account metadata, unknown price mapping, DB failure before receipt, failure during processing, duplicate delivery, concurrent duplicate delivery, and safe replay after recovery. Missing configuration/metadata/price currently return success and are defects to resolve with truthful retry or durable quarantine. Processing is currently inline; worker-restart criteria apply only if the reviewed implementation introduces a worker. No failed state change is lost behind an unconditional 200. Validate SQL against migrated PostgreSQL. Redact secrets and minimize retained payment payloads.

**Rollout:** Include retention, replay, alerting, and reconciliation instructions. Use Stripe test mode. No automatic replay of old live events or changes to real invoices/subscriptions.

## LR-012 Reconcile subscription identity and transitions

**Branch:** `fix/lr-012-subscription-state-order` · **Gate:** PAID · **Hours:** 8–14 · **Depends:** LR-011.

**Problem and scope:** Subscription updates/deletions mutate an account by metadata ID alone; successful updates do not clear an obsolete deferred downgrade. Review update and deletion branches in stripe_webhook.py:111/151/168, services/billing_state.py:44, and deferred resolution in services/usage.py. Check subscription.customer against accounts.stripe_customer_id. The worker reads raw plan_slug and never applies a deferred downgrade; it must resolve the same effective state. Verify the webhook endpoint Stripe API version: newer versions move current_period_end onto items, and a missing field must not turn cancellation into immediate downgrade. Use one coherent transition model bound to the current customer/subscription and authoritative state. Event timestamps alone are insufficient if ties or concurrent processing can still reverse state.

**Acceptance:** Real-DB tests cover a new subscription followed by an old update/deletion, cancel/resubscribe before a downgrade deadline, cancellation reversal, duplicate/tied events, concurrent events, and replay. An obsolete downgrade cannot revoke current paid access. Incorrect/missing metadata fails safely and is observable; another Stripe customer's subscription cannot be attached through an unchecked mapping.

**Rollout:** Inventory current subscriptions and pending downgrades read-only. Backfills or reconciliation changes require reviewed before/after evidence. Preserve auditable history rather than deleting stale-event evidence.

## LR-013 Enforce payment status entitlements

**Branch:** `fix/lr-013-payment-status-entitlements` · **Gate:** PAID · **Hours:** 4–7 · **Depends:** LR-012 and Jerry's policy.

**Problem and scope:** The current resolver grants the price's plan even for `incomplete` and `unpaid`. Create a shared approved mapping for active, trialing, past_due, unpaid, incomplete, incomplete_expired, paused, and canceled states. Inspect API and worker entitlement paths so a UI-only restriction does not leave a generation bypass.

**Acceptance:** A table-driven transition suite proves limits, allowed actions, grace duration, billing UI, and downgrade timing for every state. Include sponsored/self-paid transitions and explicit zero/unlimited overrides. Document whether existing schedules pause, skip, or continue under each state. Changes in payment grace must not be confused with the separate usage overage policy.

**Decision:** Jerry approved full access for active/trialing; past_due retains paid access seven days, then Free; incomplete/unpaid get Free. API and worker both need changing because the webhook currently writes the price plan regardless of status. Use an authoritative persisted grace start that replay cannot extend. Apply period-end downgrade policy. Paused and any otherwise unaddressed states still require a decision; do not invent it.

## LR-014 Prevent duplicate subscription checkout

**Branch:** `fix/lr-014-single-subscription-checkout` · **Gate:** PAID · **Hours:** 5–9 · **Depends:** LR-012 and LR-013.

**Problem and scope:** `routes/billing.py:115` does not reconcile an existing subscription before creating another subscription Checkout Session. Use an intentional plan-change path for paid customers and durable reuse/idempotency for a pending purchase. Inspect the paid Change Plan UI and provider semantics. Serialize or otherwise make Customer.create safe too: billing.py:167–186 can create duplicate Stripe customers before duplicate subscriptions even arise. Jerry approved upgrades now/prorated, downgrades at period end, one subscription per customer, repeat checkout directed to the billing portal, and manual refunds.

**Acceptance:** Concurrent checkout requests, double clicks, retries after a response timeout, abandoned sessions, expired sessions, and an already-paid customer create no unintended second recurring subscription. Confirm upgrade/downgrade, portal, sponsored self-payment, and cancellation/resubscription in Stripe test mode. A hosted checkout success redirect alone cannot grant paid access.

**Rollout:** Read-only inventory identifies existing duplicate subscriptions, if any. Refunds, cancellations, and customer communication require a separate explicit operator decision; never automatically cancel a real subscription in this ticket.

## LR-015 Honor zero report allowances

**Branch:** `fix/lr-015-zero-report-limit` · **Gate:** PILOT · **Hours:** 3–5 · **Depends:** LR-001.

**Problem and scope:** API usage resolution preserves zero as a freeze, but ratio checks using `max(limit, 1)` still admit work. Check services/usage.py:180/294 and worker limit_checker.py:108, plus legacy evaluate_report_limit at usage.py:409 (used by admin.py:639 and property.py:1141), which treats nonpositive limits as unlimited. November 9 decision: scheduled runs intentionally do not consume the manual market allowance; do not add them to that count. Claude LR-023 removes the ticker's manual-limit veto and owns schedules_tick.py. Codex supplies the manual allowance helper and coordinates contradictory wizard copy. Claude owns property.py normalization in LR-018 first; coordinate that route before editing it.

**Acceptance:** At manual allowance zero, usage zero and usage one both refuse new manual work. Test positive limits, existing grace, null/default, unlimited sentinel and overrides. Scheduled sends use schedule capacity and must continue despite exhausted/zero manual allowance; cover this integration contract with LR-023. Refused manual work is not queued, counted, billed or sent. Preserve legitimate paid/sponsored allowances.

**Rollout:** Use synthetic accounts to exercise boundaries. Do not freeze or change any production customer's allowance as a test.

## LR-016 Serialize schedule capacity

**Branch:** `fix/lr-016-schedule-capacity-admission` · **Gate:** PUBLIC · **Hours:** 4–7 · **Depends:** LR-001; independent of LR-015.

**Problem and scope:** `routes/schedules.py:331` counts capacity before insertion without serializing competing requests. Reuse the repo's account-row locking pattern. Inspect create, every PATCH active=true (currently no capacity check at schedules.py:610), seats.hand_over_book moving active schedules, and company/affiliate admission paths; a single protected endpoint is not enough if another creates active schedules.

**Acceptance:** Two real database connections competing for one slot yield one admitted active schedule. Include every reactivation, concurrent admission, book handover, company/sponsored ownership, zero/unlimited limits, transaction rollback, and plan changes. Refused requests leave no partial schedule or queued side effect. Avoid cross-account global locks.

**Rollout:** Jerry approved grandfathering existing active schedules: keep them running, but forbid new or reactivated schedules while usage is at/above the limit. Count over-limit accounts read-only first; do not bulk deactivate them. Document handover behavior without silently violating that preservation rule.

## LR-017 Consume invitation tokens once

**Branch:** `fix/lr-017-atomic-invitation-acceptance` · **Gate:** PILOT · **Hours:** 2–4 · **Depends:** LR-001; independent of LR-009.

**Problem and scope:** `routes/auth.py:401` reads the boolean used flag without locking and later updates it unconditionally. Two accepts succeeded in four of four review runs, and the last password won. Seat cancellation during acceptance races the same way. Make token validation, password/account changes, and consumption one atomic operation. Preserve company seat, user deactivation, and membership boundaries.

**Acceptance:** Concurrent acceptance attempts for the same token yield one success/session and a deterministic rejection; the losing request cannot replace the password. Test expiry, already-used token, disabled user, wrong account, cancellation during acceptance, and rollback. Use real PostgreSQL rather than a mock that serializes all access. Repeated acceptance after success remains rejected.

**Rollout:** Keep existing valid invitations compatible unless a reviewed security requirement says otherwise. Do not resend all invitations or alter existing memberships automatically.
