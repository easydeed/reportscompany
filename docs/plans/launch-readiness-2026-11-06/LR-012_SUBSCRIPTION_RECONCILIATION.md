# LR-012: customer-bound subscription reconciliation — proposed design

Base main: `110f9a30327ae9c8506a981f953d97f390b15e22`.
Jerry authorized starting this design while Claude reviews LR-011 (#328).
This is not runtime implementation, migration approval or a live Stripe test.
LR-013 and LR-014 remain next, before outreach. No configuration changes.

## Confirmed source gaps

- `services/billing_state.py:22-65` writes subscription ID/status for the supplied
  account, without validating its stored Stripe customer.
- Main's `routes/stripe_webhook.py` selects that account from event metadata.
  LR-011 replaces this with durable receipts and per-subscription ordering,
  but customer binding and same-second reconciliation remain LR-012 work.
- `services/usage.py:108-126` can apply a deferred downgrade during a usage
  read. Its update does not condition on the deadline/subscription it read.
- `worker/limit_checker.py:46-62` joins plans using raw `accounts.plan_slug`;
  it does not apply the same deadline rule. API/worker can disagree.

## Required identity and transition rules

1. Match the receipt's account to its stored Stripe customer. Missing customer,
   missing account or metadata/customer mismatch quarantines; metadata alone
   never attaches a subscription. Do not silently repair customer ownership.
2. An update/deletion for an old subscription cannot revoke a different current
   subscription. A replacement must be corroborated by authoritative provider
   state for the same customer. Multiple current subscriptions or incomplete
   provider inventory are review cases, not grounds to guess or cancel one.
3. Preserve LR-011's receipt identity, terminal dispositions, stale-event guard
   and reviewed replay controls. An event ID is never a chronological tie-break.
4. Same-second/distinct events reconcile current subscription state, rather than
   applying whichever event body happens to arrive last. Retrieval failure is
   retryable (503), never an invented paid or Free state.
5. Cancellation reversal/resubscription clears an obsolete downgrade in the same
   transaction as the validated replacement billing state. A missing period
   never selects immediate Free. Support tested Clover and legacy shapes.
6. Retain approved immediate upgrades and period-end downgrades. LR-013 owns
   payment-status/grace entitlements; LR-014 owns checkout/customer uniqueness.
   No automatic refunds, cancellation or live historical replay is included.

## Serialization proposal for review

Reconcile one account at a time, including transitions between different
subscription IDs. The LR-011 subscription cursor alone cannot serialize those.
Use a consistently ordered transaction-scoped account advisory lock before
cursor/account row locks, with bounded acquisition. Every reconciliation and
replay path must follow that same order; test deadlock/timeout outcomes.

The authoritative retrieval must happen within that serialization scope: an
older snapshot fetched before the lock must not overwrite a newer commit.
Propose one bounded provider read with SDK retries disabled, while the lock is
held; transient read failure rolls back processing and retains the receipt.
Document and measure the maximum lock hold before code PASS. Do not hide an
unbounded provider wait behind PostgreSQL's statement timeout.

Only compare provider IDs/statuses/prices/period fields necessary for binding
and transition. Never store raw subscription/payment/contact objects. Test
provider retrieval with a fake client; no live customer or payment calls.

## Effective plan and deferred deadlines

Inventory every API/worker entitlement consumer before choosing the shared
projection. Prefer one database-backed effective-plan rule, preserving zero
and unlimited overrides and the schedule/manual allowance separation.
Avoid duplicate Python implementations in separately deployed applications.

### Consumer inventory at this branch's main baseline

| Reader | Current source | Implementation review requirement |
|---|---|---|
| API report/plan allowances | `apps/api/src/api/services/usage.py:79-126` | Raw-plan join plus deadline-triggered mutation; replace or serialize the stale read/write boundary. |
| Worker product allowances | `apps/worker/src/worker/limit_checker.py:46-62` | Raw-plan join; must use the same effective deadline as API enforcement. |
| Public lead capture | `apps/api/src/api/routes/leads.py:283` | Raw plan supplies `lead_capture_enabled`; include the post-deadline feature decision in parity tests. |
| Account billing output | `apps/api/src/api/routes/account.py:138,259` | Raw plan/status is returned; define stored versus effective fields so customer UI does not contradict enforcement. |
| Affiliate metrics | `apps/api/src/api/services/affiliates.py:142` | Raw-plan allowance join; audit displayed capacity without reopening unrelated counting defects. |
| Company metrics | `apps/api/src/api/routes/company.py:259` | Same raw-plan allowance join; preserve sponsorship and grandfathered-schedule policy. |
| Admin SMS summary | `apps/api/src/api/routes/admin.py:3637` | Raw plan supplies credits/features; distinguish diagnostic stored state from an entitlement decision. |

This is a source inventory, not approval to rewrite every listed route. Runtime
work must identify which outputs enforce access versus report stored billing
facts. Test customer-visible effective values and preserve explicit raw values
where an operator needs them. No read/list endpoint may introduce a new billing
mutation. No scope expands into CSV, pricing policy or unrelated dashboard math.

Remove usage-read mutation if all consumers can use that projection; otherwise
make any materialization conditional on the exact subscription/deadline state
still matching, under the same account serialization. A request that read an
old cancellation cannot undo a subsequent paid reinstatement. This choice
must be resolved in code review, not left as two competing behaviors.

Any new function/column migration waits until 0070 is applied and #328 merges.
No migration number is reserved by this design PR. Runtime branches remain
flat from main and are refreshed after the LR-011 dependency lands.

## Required proofs before code PASS

Real PostgreSQL plus fake Stripe snapshots:

- Customer mismatch, missing binding, cross-account metadata and ambiguous
  multiple subscriptions: quarantine with no account mutation.
- New subscription followed by an old update/deletion: current paid access
  stands, with auditable stale/obsolete disposition.
- Cancel then reverse/resubscribe before the deadline: stale downgrade clears.
- Two same-second events and concurrent distinct subscriptions: authoritative
  state wins regardless of arrival order; do not sort event IDs.
- Provider timeout/refusal, processing/commit failure and replay: no partial
  transition, no false acknowledgement and bounded waits.
- A usage read racing reinstatement cannot downgrade the fresh subscription.
- API and worker agree just before/at/after the same deadline, preserving all
  overrides and existing scheduled-send policy.
- Legacy/Clover periods and missing/conflicting periods; terminal redelivery.

The accompanying inventory SQL is read-only and has not been run against
production. Counts do not authorize a backfill. Any correction requires reviewed
before/after evidence and Jerry's explicit production authorization.
