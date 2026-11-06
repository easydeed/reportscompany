# Launch Readiness Security and Billing Tickets

**Status:** All proposed pending Claude Code review. **Builder:** Cursor. **Reviewer:** Claude Code.
Evidence references are from audit commit `28157e74`; re-read current main before implementation. The [execution plan](../LAUNCH_READINESS_PLAN_2026-11-06.md) supplies the common testing, review, migration, rollout, and completion rules. Each ticket is one branch and one logical PR. Intentional dependency lockfile changes are part of LR-003; incidental lockfile drift is excluded from every other ticket.

## LR-003 Patch production dependencies

**Branch:** `fix/lr-003-patched-dependencies` · **Gate:** PILOT · **Hours:** 6–12 · **Depends:** LR-002.

**Problem and scope:** `apps/web/package.json`, root/workspace manifests, and `pnpm-lock.yaml` pin Next 16.0.7 and affected dependencies. The scan returned 61 advisories, whose applicability differs. Inspect all lockfile consumers, including `packages/ui` and the root npm lock used by backend CI. Update to a currently patched supported Next/React combination, not merely the first historical fix. Preserve the existing design and framework structure.

**Acceptance:** Frozen-lockfile install, production web build, typecheck, frontend suites, and relevant backend render checks pass. Retain before/after audit reports; classify each residual production advisory by reachable feature, upstream resolution, and owner. No reachable critical/high issue closes by a severity downgrade alone. Render rail, landing, login, authenticated creation, public report, and social/PDF-related paths. Confirm request handlers, cookies, routing, fonts, and browser compatibility survive the upgrade.

**Rollout:** Deploy the reviewed dependency set as a unit. Revert the release if journeys regress; do not leave mixed manifests and lockfiles. A major compatibility surprise triggers re-estimation, not a framework rewrite in this ticket.

## LR-004 Enforce branding object ownership

**Branch:** `fix/lr-004-branding-delete-ownership` · **Gate:** PILOT · **Hours:** 2–4 · **Depends:** LR-001.

**Problem and scope:** `apps/api/src/api/routes/upload.py:75` checks whether the account ID occurs anywhere in a URL; `services/upload.py:186` extracts the deletion key independently. Replace this with one canonical key parser and exact authenticated-account prefix authorization. Inspect all callers before altering the helper signature.

**Acceptance:** Own objects remain deletable. Another tenant's key is rejected even when the caller ID appears in a hostname, username, query, encoded segment, or unrelated path. Reject malformed/foreign origins and ambiguous keys. Assert the fake storage client's delete method is never called for a foreign key. Test existing accepted URL formats explicitly instead of silently breaking legitimate assets.

**Rollout:** No storage migration or real-object deletion is required. Verify a disposable own-account asset and rejection using approved test accounts; preserve customer branding URLs.

## LR-005 Reject rate-limited requests before execution

**Branch:** `fix/lr-005-preexecution-rate-limit` · **Gate:** PILOT · **Hours:** 4–7 · **Depends:** LR-001.

**Problem and scope:** `apps/api/src/api/middleware/authn.py:387` calls the route before returning a throttle response. Move the decision ahead of side effects while preserving honest rate headers and the explicitly chosen Redis-outage behavior. Keep account authentication and per-product allowance checks distinct.

**Acceptance:** With limit one, three requests cause one handler execution and responses 200/429/429. Assert zero uploads, SQL mutations, task publications, and provider calls for refused requests. Test boundary/reset behavior, concurrent requests using local Redis, normal headers, and Redis-outage handling. A 429 must not inherit a successful handler's cookie or misleading content headers.

**Rollout:** Verify the rejection with a harmless test handler/account. Do not generate chargeable work or deliberately flood production. Observe unexpected throttle rates after deploy.

## LR-006 Bound public property searches

**Branch:** `fix/lr-006-public-lookup-budget` · **Gate:** PILOT · **Hours:** 3–5 · **Depends:** LR-005; Jerry approves budgets and outage behavior.

**Problem and scope:** `routes/lead_pages.py:230` invokes vendor lookup anonymously; the global limiter skips requests without an account. Add shared limits for the real search endpoint and vendor budget, covering direct API access as well as web proxies. Determine the trusted client-IP chain rather than trusting arbitrary forwarding headers.

**Acceptance:** Repeated requests across workers reach the shared limit before vendor execution. Verify per-page/global budgets, response headers, cooldown, and no PII in keys or errors. Test shared-IP behavior, altered agent codes, spoofed headers, and limiter outage. Valid nearby requests remain usable. Confirm what any platform edge limit covers; it cannot substitute for an unverified application assumption.

**Decision:** Document actual limits, expected public traffic, and fail behavior before enabling the policy. Vendor calls for the test use a fake or approved sandbox.

## LR-007 Make SVG upload handling safe

**Branch:** `fix/lr-007-safe-branding-images` · **Gate:** PILOT · **Hours:** 3–6 · **Depends:** LR-004.

**Problem and scope:** `services/upload.py:53` skips SVG image parsing and later derives response MIME type from the filename. Determine current consumers; choose the smallest compatible policy: reject SVG for now, safely rasterize it, or use a reviewed sanitizer. Preserve Design's trusted bundled SVGs; this ticket concerns untrusted uploads.

**Acceptance:** MIME/extension disagreements, oversized input, scripts, event attributes, external references, XML entities, and malformed SVG cannot become active trusted content. Ordinary approved images remain usable in the web UI and report renderers. Verify response content type and storage handling, and render an uploaded logo in the actual consumer.

**Rollout:** Inventory existing SVG uploads first. A breaking rejection requires an explicit compatibility approach. No bulk asset deletion or silent conversion of existing customer files.

## LR-008 Neutralize formulas in CSV exports

**Branch:** `fix/lr-008-safe-lead-csv` · **Gate:** PUBLIC · **Hours:** 2–3 · **Depends:** LR-001.

**Problem and scope:** `routes/leads.py:619` sends public form values directly to `csv.writer`. Add one export-boundary neutralizer and reuse it for every lead export path. Preserve stored customer text and valid numeric/date columns; this is an export representation change.

**Acceptance:** Formula-leading text, including leading whitespace/control characters, does not execute as a formula in supported spreadsheet software. Test `=`, `+`, `-`, `@`, tab/newline prefixes, quotes, commas, and Unicode; distinguish actual numeric cells from arbitrary text. Verify normal names, international phone numbers, multiline messages, and row/column fidelity. Document the chosen safe representation.

**Rollout:** A generated fixture export is sufficient; no real leads need exporting. Include evidence from the supported spreadsheet viewer or explicitly record the remaining compatibility check.

## LR-009 Revoke sessions after password changes

**Branch:** `fix/lr-009-password-session-revocation` · **Gate:** PILOT · **Hours:** 4–7 · **Depends:** LR-001.

**Problem and scope:** Password change/reset updates `password_changed_at`, but authentication does not compare token issuance with it. Read all token issuers and middleware. Define migration-free compatibility where possible; otherwise propose additive schema with the normal guards. Preserve existing deactivation and blacklist enforcement.

**Acceptance:** Sessions minted before a password change or reset are rejected afterward; sessions intentionally minted after it work. Test same-second timestamps, missing/invalid issuance claims, multiple devices, logout, disabled users, and database outage. Explicitly decide whether the initiating device receives a replacement session. API keys follow their own documented policy, not accidental JWT behavior.

**Rollout:** Test against a disposable user with the real authentication stack. Never mint a fabricated production admin token. Document any intentional one-time sign-in impact for legacy tokens.

## LR-010 Set browser security headers

**Branch:** `fix/lr-010-browser-security-headers` · **Gate:** PUBLIC · **Hours:** 2–4 · **Depends:** LR-003.

**Problem and scope:** Live web responses lacked CSP, framing control, nosniff, and an explicit referrer policy. Inspect `apps/web/next.config.ts`, middleware, external fonts/maps, public report embeds, and Next script behavior. Define a compatible policy instead of applying an arbitrary restrictive header set.

**Acceptance:** Verify headers on production-like responses and document public/embedded route exceptions. Test login, dashboards, maps, reports, previews, uploaded assets, and sharing. CSP uses an approach compatible with the framework; evaluate violations before enforcement. No blanket unsafe policy is presented as effective protection.

**Rollout:** Use report-only CSP where needed, then enforce the validated policy. Confirm legitimate embeds and report generation are still possible. Any exception is narrow and explained.

## LR-011 Make Stripe event ingestion durable

**Branch:** `fix/lr-011-retryable-stripe-events` · **Gate:** PAID · **Hours:** 8–14 · **Depends:** LR-001.

**Problem and scope:** `routes/stripe_webhook.py:130` acknowledges database exceptions as success. Design the smallest durable receipt/processing record using Stripe event IDs and existing DB patterns. Keep signature validation. Use explicit non-2xx retry behavior when receipt cannot be persisted; acknowledge only durably accepted work under a documented processing model.

**Acceptance:** Test invalid signature, missing configuration, DB failure before receipt, failure during processing, duplicate delivery, concurrent duplicate delivery, worker restart if applicable, and safe replay after recovery. No failed state change is lost behind an unconditional 200. Validate SQL against migrated PostgreSQL. Redact secrets and minimize retained payment payloads.

**Rollout:** Include retention, replay, alerting, and reconciliation instructions. Use Stripe test mode. No automatic replay of old live events or changes to real invoices/subscriptions.

## LR-012 Reconcile subscription identity and transitions

**Branch:** `fix/lr-012-subscription-state-order` · **Gate:** PAID · **Hours:** 8–14 · **Depends:** LR-011.

**Problem and scope:** Subscription updates/deletions mutate an account by metadata ID alone; successful updates do not clear an obsolete deferred downgrade. Review `stripe_webhook.py:111`, `services/billing_state.py:44`, and deferred resolution in `services/usage.py`. Use one coherent transition model bound to the current customer/subscription and authoritative state. Event timestamps alone are insufficient if ties or concurrent processing can still reverse state.

**Acceptance:** Real-DB tests cover a new subscription followed by an old update/deletion, cancel/resubscribe before a downgrade deadline, cancellation reversal, duplicate/tied events, concurrent events, and replay. An obsolete downgrade cannot revoke current paid access. Incorrect/missing metadata fails safely and is observable; another Stripe customer's subscription cannot be attached through an unchecked mapping.

**Rollout:** Inventory current subscriptions and pending downgrades read-only. Backfills or reconciliation changes require reviewed before/after evidence. Preserve auditable history rather than deleting stale-event evidence.

## LR-013 Enforce payment status entitlements

**Branch:** `fix/lr-013-payment-status-entitlements` · **Gate:** PAID · **Hours:** 4–7 · **Depends:** LR-012 and Jerry's policy.

**Problem and scope:** The current resolver grants the price's plan even for `incomplete` and `unpaid`. Create a shared approved mapping for active, trialing, past_due, unpaid, incomplete, incomplete_expired, paused, and canceled states. Inspect API and worker entitlement paths so a UI-only restriction does not leave a generation bypass.

**Acceptance:** A table-driven transition suite proves limits, allowed actions, grace duration, billing UI, and downgrade timing for every state. Include sponsored/self-paid transitions and explicit zero/unlimited overrides. Document whether existing schedules pause, skip, or continue under each state. Changes in payment grace must not be confused with the separate usage overage policy.

**Decision:** Engineering proposes options and consequences; Jerry chooses the commercial policy before implementation. No invented grace period or automatic customer suspension policy.

## LR-014 Prevent duplicate subscription checkout

**Branch:** `fix/lr-014-single-subscription-checkout` · **Gate:** PAID · **Hours:** 5–9 · **Depends:** LR-012 and LR-013.

**Problem and scope:** `routes/billing.py:115` does not reconcile an existing subscription before creating another subscription Checkout Session. Use an intentional plan-change path for paid customers and durable reuse/idempotency for a pending purchase. Inspect the paid Change Plan UI and provider semantics.

**Acceptance:** Concurrent checkout requests, double clicks, retries after a response timeout, abandoned sessions, expired sessions, and an already-paid customer create no unintended second recurring subscription. Confirm upgrade/downgrade, portal, sponsored self-payment, and cancellation/resubscription in Stripe test mode. A hosted checkout success redirect alone cannot grant paid access.

**Rollout:** Read-only inventory identifies existing duplicate subscriptions, if any. Refunds, cancellations, and customer communication require a separate explicit operator decision; never automatically cancel a real subscription in this ticket.

## LR-015 Honor zero report allowances

**Branch:** `fix/lr-015-zero-report-limit` · **Gate:** PILOT · **Hours:** 2–4 · **Depends:** LR-001.

**Problem and scope:** API usage resolution preserves zero as a freeze, but ratio checks using `max(limit, 1)` still admit work. Check `services/usage.py:180,294` and worker `limit_checker.py:108`. Apply the same boundary interpretation at admission and execution, using existing shared patterns.

**Acceptance:** At allowance zero, usage zero and usage one both refuse new work. Test positive limits, existing grace behavior, null/default values, unlimited sentinel, overrides, manual reports, and scheduled execution. Verify refused work is not queued, counted, billed, or sent. Preserve legitimate existing paid and sponsored allowances.

**Rollout:** Use synthetic accounts to exercise boundaries. Do not freeze or change any production customer's allowance as a test.

## LR-016 Serialize schedule capacity

**Branch:** `fix/lr-016-schedule-capacity-admission` · **Gate:** PUBLIC · **Hours:** 3–5 · **Depends:** LR-015.

**Problem and scope:** `routes/schedules.py:331` counts capacity before insertion without serializing competing requests. Reuse the repo's account-row locking pattern. Inspect create, reactivate, duplicate, import, and any company/affiliate admission paths; a single protected endpoint is not enough if another creates active schedules.

**Acceptance:** Two real database connections competing for one slot yield one admitted active schedule. Include simultaneous reactivation, company/sponsored ownership, zero/unlimited limits, transaction rollback, and plan changes. Refused requests leave no partial schedule or queued side effect. Avoid cross-account global locks.

**Rollout:** Count existing over-limit accounts read-only and report them. No unapproved bulk schedule deactivation or grandfathering decision.

## LR-017 Consume invitation tokens once

**Branch:** `fix/lr-017-atomic-invitation-acceptance` · **Gate:** PILOT · **Hours:** 3–5 · **Depends:** LR-009.

**Problem and scope:** `routes/auth.py:401` reads an unused invitation without locking and later updates its use state unconditionally. Make token validation, password/account changes, and consumption one atomic operation. Preserve company seat, user deactivation, and membership boundaries.

**Acceptance:** Concurrent acceptance attempts for the same token yield one success/session and a deterministic rejection; the losing request cannot replace the password. Test expiry, already-used token, disabled user, wrong account, cancellation during acceptance, and rollback. Use real PostgreSQL rather than a mock that serializes all access. Repeated acceptance after success remains rejected.

**Rollout:** Keep existing valid invitations compatible unless a reviewed security requirement says otherwise. Do not resend all invitations or alter existing memberships automatically.
