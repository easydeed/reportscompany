# LR-012: customer-bound subscription reconciliation — proposed design

Design revision 3; reviewed runtime baseline: main `1519cd03` (LR-011 merged).
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

## Serialization and provider deadline (revision 2)

Every reconciliation and replay takes this exact order:
receipt row FOR UPDATE → account advisory lock → authoritative provider read →
subscription cursor FOR UPDATE → account FOR UPDATE → validated writes → commit.
Use `pg_advisory_xact_lock(hashtextextended('billing_account:' || id, 0))`.
The receipt lock only serializes that receipt. No cursor/account row lock is
held across the provider call, so normal account edits never wait for Stripe.
No provider snapshot fetched before the advisory lock may be applied afterward.
Acquire the advisory lock with `lock_timeout = '2s'`; contention is retryable
503 with the receipt preserved. Replay has no bypass or alternate lock order.

Use a dedicated `stripe.StripeClient` with `max_network_retries=0`,
`stripe_version='2025-10-29.clover'`, and `stripe.HTTPXClient` in async-only
mode (`allow_sync_methods=False`). Set HTTPX connect/read/write timeouts to
2 seconds and pool timeout to 1 second. Await `subscriptions.list_async`
with customer, `status='all'`, and `limit=10`, inside an `asyncio.timeout(6)`
covering the entire single request, response body and normalization. Do not
use module-global Stripe HTTP defaults (80 seconds), automatic pagination,
or a thread future that abandons an uncancelled request. Close the async
client in `finally`; cancellation must close the underlying connection.
`has_more` means incomplete inventory and quarantine, never a guessed winner.
All Stripe behavior is exercised using fake/local transports, never live calls.

The advisory-lock section has a 10-second total budget: at most 6 seconds
for the provider, leaving at most 4 seconds for database processing/commit.
Before each subsequent SQL statement, including commit, cap its timeout by
the remaining overall budget and abort when exhausted; transaction cleanup
must release the lock. A 5-second statement timeout alone is insufficient.
Measure lock-held elapsed time and cleanup in real PostgreSQL tests, including
provider stall, header/body trickle, lock contention, rollback and replay;
code PASS requires proof of this bound with explicit scheduling tolerance,
not merely inspection of configured timeout numbers. Log durations/reasons,
never raw customer/payment/contact payloads or keys.

### Event-loop boundary

Keep the synchronous database/transaction path, but the async webhook route
must `await run_in_threadpool(...)` for the entire receipt-store/process unit.
Receipt durability remains a separate commit before processing. Inside that
worker thread only, the bounded provider helper uses `asyncio.run(...)`; it
never calls it from the running API event loop and never uses a background
future whose timed-out caller abandons provider work. The worker awaits the
async cancellation and client cleanup before returning to the thread pool.
The replay CLI is synchronous and uses the same helper directly. Checkout
must follow the same boundary: if its route is async, offload the complete
synchronous customer-create/database unit using `await run_in_threadpool`;
if synchronous, FastAPI's normal worker-thread dispatch is sufficient.

Add a same-app concurrency test: hold a webhook's fake provider for the full
6-second budget while an unrelated `/health` request completes within 300 ms
(with explicit CI scheduling tolerance). Cover checkout and replay entry-point
compatibility too; `RuntimeError` from a nested event loop is not retry logic.

## Other billing writers: mandatory rules

| Writer on reviewed main | Rule |
|---|---|
| `admin.py` PATCH companies (~1557), affiliates (~1870), accounts (~2030) | Reject plan changes for Stripe-bound accounts. For unbound accounts, take the account advisory lock before the account row lock and recheck binding before writing. Other admin fields do not need the billing lock and never wait for provider work. |
| `affiliates.py` sponsorship end (~872) | Under the same advisory-before-row order, only convert sponsored_free to free for a still-unbound account. If Stripe-bound, refuse the billing transition; never overwrite its paid plan. |
| `usage.py` downgrade UPDATE (~120) | Remove it. Reads never take a billing lock or write billing state. |
| `billing.py` customer-id save (~193) | Acquire the account advisory lock before customer creation and before any account row lock; re-read binding after acquisition and reuse it. Never overwrite an existing different customer. Persist with a conditional null-binding check; fail safely if binding changed. Customer creation must use the same bounded provider client, without holding an account row lock. LR-014 still owns checkout/subscription deduplication and customer-create recovery. |
| `billing_state.py` helpers and LR-011 processing/replay | Internal writes only after validated reconciliation, under the complete receipt/advisory/provider/cursor/account order above. No direct unguarded helper caller. |

Before code PASS, search all billing-column UPDATE/INSERT writers again and
prove each existing-account mutation follows these rules. New-account creation
is not a reconciliation writer; it must not import an unverified paid binding.

### Customer-creation sequencing and operator recovery

Existing checkout races can already have produced mismatched bindings.
LR-012's serialized non-overwriting customer writer prevents new conflicting
bindings, but cannot establish the correct owner of historical subscriptions.
Expose customer-mismatch quarantine through LR-011 backlog/LR-027; do not
silently repair, acknowledge paid access as healthy, or reassign by metadata.
Include a dry-run operator inspection/repair procedure in LR-012: capture a
reviewed account/customer/subscription inventory, prove the intended customer
from provider evidence, specify exact expected old and proposed new bindings,
and require Jerry's explicit authorization before a conditional repair under
the same lock order and reviewed replay. No automatic backfill or live repair
is authorized by this design. Production rollout requires the read-only
inventory and reviewed repair path ready; LR-014's checkout uniqueness remains
a separate required gate before outreach. No live payment test is required.

## Effective plan and deferred deadlines

Inventory every API/worker entitlement consumer before choosing the shared
projection. Require one database-backed effective-plan rule, preserving zero
and unlimited overrides and the schedule/manual allowance separation.
Avoid duplicate Python implementations in separately deployed applications.

### Consumer inventory at this branch's main baseline

| Reader | Current source | Implementation review requirement |
|---|---|---|
| API report/plan allowances | `apps/api/src/api/services/usage.py:79-126` | Remove the read-time UPDATE; use the shared database projection. |
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

Remove the usage-read UPDATE unconditionally. No GET, usage/list read or
entitlement check changes stored plan, billing status, subscription or deadline.
Use one shared database projection for every entitlement consumer, computing
expired downgrade with the database clock and the inclusive boundary
`plan_downgrade_at <= now()`. Stored fields remain explicit diagnostics;
customer-visible access/allowances use the effective result. API and worker
must query the same projection; no Python/app-clock fallback and no optional
read-time materialization remain. Overrides retain zero/unlimited semantics;
existing schedules remain independent of manual-report allowance.

Other plans readers (`email.py` `_plan_limits`, `seats.py` `agent_plan`,
`plan_lookup.py`, and the `plans.py` catalog cache) are catalog/display reads,
not account entitlement enforcement. Preserve that distinction; do not widen
this ticket into catalog or unrelated metrics rewrites.

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
- Usage reads perform zero billing writes; racing reinstatement cannot downgrade a fresh subscription.
- Provider-held advisory lock does not block unrelated account-row edits; every
  other billing writer is serialized or refused for Stripe-bound accounts.
- Concurrent checkout customer creation cannot overwrite a binding; existing
  mismatches remain visible quarantine requiring reviewed operator repair.
- API and worker agree just before/at/after the same deadline, preserving all
  overrides and existing scheduled-send policy.
- Legacy/Clover periods and missing/conflicting periods; terminal redelivery.

The accompanying inventory SQL is read-only and has not been run against
production. Counts do not authorize a backfill. Any correction requires reviewed
before/after evidence and Jerry's explicit production authorization.
