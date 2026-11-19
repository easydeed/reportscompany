# LR-011: durable Stripe ingestion — proposed design

Base main: `79661c427784a412a902037e1da636477cbb66fa`.
Status: design PASS at 6a36574b (Claude review 7023347174); implementation notes recorded below.
Not runtime implementation or paid-launch approval.
Stripe in production is **live**, per Jerry. No real-card checkout tests.

## Problem confirmed in source

`apps/api/src/api/routes/stripe_webhook.py` verifies the raw request signature,
then acknowledges database exceptions as HTTP 200. Missing configuration,
account metadata, items and price mappings are also acknowledged without a
durable disposition. There is no persisted event-ID deduplication or replay
source. Returning success can permanently lose the requested billing change.

Reuse `db_conn`, `get_plan_slug_for_stripe_price`, `update_account_billing_state`
and plan-cache invalidation. The active price lookup reads `plans.stripe_price_id`;
the older environment price map is not the webhook's authoritative mapping.

## Scope and sequence

| Ticket | Boundary |
|---|---|
| LR-011 | Verified-event receipt, transactional processing, deduplication, explicit retries/quarantine, replay evidence and backlog interface. |
| LR-012 | Customer/subscription binding, authoritative reconciliation and event ordering, including deferred downgrades. |
| LR-013 | Approved payment-status entitlements and persisted past-due grace. |
| LR-014 | One customer/subscription, pending-checkout reuse and the paid plan-change path. |

All four must be reviewed, merged and verified **before outreach**. LR-011 alone
does not make checkout safe. Preserve the sponsored checkout gate throughout.
No bulk correction, refund, cancellation, live event replay or live Stripe
configuration change is included in this design task.

## Durable record and acknowledgement

Propose one platform table, `billing_webhook_events`, distinct from outbound
customer `webhook_deliveries`. #323 and migration 0069 have landed. Coordinate
the next migration number before code review; Jerry applies the reviewed
billing migration before runtime merge. Add a separate subscription cursor
table for the monotonic guard below. Enable RLS with no tenant policies on
both platform tables; only the existing privileged server/operator role reads them.

Store only an allowlisted envelope: event ID, event type, live/test mode,
event API version, event creation and receipt times, Stripe customer and
subscription IDs, candidate account UUID, processing state, bounded attempt
counts/timestamps, and a fixed error/reconciliation code. Retain the minimum
subscription facts needed by the existing handler and LR-012, including price
IDs and supported period fields; document the exact allowlist in code review.
No full payment body, signature, secret, customer email, address, payment-method
details or arbitrary metadata. No automatic retention purge until its policy
is approved. An unknown account UUID must be recordable as quarantine rather
than fail a foreign key and erase the event evidence.

Proposed states: `pending`, `retryable`, `processed`, `quarantined`, `ignored`.
Use a unique verified event identity, including live/test context. Connected
account events are unsupported unless an explicit supported context is added;
they must not silently mutate an unrelated platform account.

| Condition | HTTP / durable outcome |
|---|---|
| Signature invalid or payload not verifiable | 400; no billing mutation. Never log the raw payload or signature. |
| SDK/signing configuration unavailable | 503; never acknowledge as received. |
| Receipt cannot commit | 503; Stripe must retain retry responsibility. |
| Normalized verified receipt committed | Continue to processing; receipt alone does not mean the change succeeded. |
| Account mutation and processed marker commit | 200. |
| Previously processed duplicate | 200 without another account mutation. |
| Another request currently owns processing | Bounded lock wait; 503 if it cannot establish a terminal disposition. |
| Transient processing/commit failure | Roll back the account mutation; retain pending/retryable evidence; 503. |
| Missing/invalid metadata, account, supported item or price mapping | Commit quarantine with a fixed reason; 200 only after that durable disposition. |
| Intentionally unsupported event type | Commit ignored disposition; 200. |

Mode/context validation happens after signature verification and before any
account mutation. Never reinterpret a verified test event as a live purchase.

## Processing and crash boundaries

1. Verify the original request bytes with Stripe's SDK and endpoint secret.
2. Validate the event identity and persist the normalized receipt in its own
   transaction using insert-on-conflict, then commit it.
3. In a second transaction, lock that receipt. A terminal duplicate does no
   work. Pending/retryable receipts run the handler under the lock.
4. The account change and `processed` marker commit together. No response or
   cache-invalidation failure may cause a committed account change to run twice.
5. Invalid business references commit quarantine without changing accounts.
   A transient failure rolls back processing and returns 503; a best-effort
   separate update may record its fixed failure class without masking the 503.

Keep processing inline for LR-011: there is no new queue or worker to pretend
will recover an acknowledged pending event. If the process dies after receipt
commit, redelivery finds pending work. If it dies after processing commit,
redelivery finds the terminal marker. Bound lock acquisition and statements;
prove timeout behavior against real PostgreSQL rather than relying on mocks.

LR-011 must itself serialize processing per subscription with a locked cursor
row keyed by mode and subscription ID. Store latest processed event creation
time and event ID. In the same transaction as the account mutation and receipt
disposition, advance this cursor. An event strictly older than the cursor is
`ignored` with reason `superseded`, returns 200, and mutates no account. The
receipt lock alone is insufficient for two different events. Replay uses this
same cursor and refuses superseded work by default; dry-run displays the reason.
Equal-second distinct events retain current processing behavior in LR-011;
LR-012 owns authoritative reconciliation of ties and customer binding. Event
IDs are not chronological tie-breakers. Tests deliver T2 then T1 through both
redelivery and replay, including concurrent requests and rollback boundaries.

## Replay, quarantine and operational signal

- Provide a read-only list of pending/retryable/quarantined receipts with age,
  reason and safe correlation IDs; include an explicit reviewed replay path.
- Replay defaults to dry-run, uses the same processor and locking, and never
  invents payment success. Retain operator reason and attempt outcome.
- Do not automatically replay historical live events. Use the stored minimal
  envelope or an explicitly authorized provider retrieval for reconciliation;
  do not assume Stripe retains every event indefinitely.
- Expose a real database-backed backlog function for LR-027: pending/retryable
  counts, oldest receipt age and bounded event-ID samples. Keep quarantine
  separately visible. Coordinate its integration with Claude after 0069; no
  invented pending count from outbound report webhook history.

## Verification required before code PASS

Use disposable migrated PostgreSQL and signed fixture bytes, with Stripe HTTP
calls blocked. Keep test credentials and signing secrets separate from live.

- Invalid/missing signature, invalid bytes and unavailable configuration.
- Missing metadata, malformed UUID, absent account/items and unknown price:
  no account mutation, a truthful durable quarantine or rejection.
- Failure before receipt commit, after receipt commit, during mutation, during
  processing commit, and after processing commit but before the response.
- Sequential and concurrent duplicates: one account mutation, one terminal
  disposition, bounded lock waits and safe retry after rollback/crash.
- A duplicate while the first attempt fails; a quarantined receipt replayed
  after its cause is corrected; unsupported event and mode/context mismatch.
- Redaction controls with sentinel secrets and contact/payment details.
- Existing billing/plan and sponsored-gate tests. LR-012/013/014 supply their
  own state/order/status/checkout proofs; do not call this suite sufficient
  paid-launch evidence. No real-card or live-customer checkout.

## Jerry's live configuration checklist

- Jerry alone creates/validates the live products and monthly USD prices:
  Growth = `starter`, **$19**; Growth Plus = `pro`, **$29**. Jerry confirmed
  the live IDs below on November 19; no Stripe or hosting setting was changed.
- The live server key stays on Render. Never copy it into chat, evidence,
  browser code or a local test configuration.
- Verify the live webhook URL is
  `https://reportscompany.onrender.com/v1/webhooks/stripe`, its supported
  snapshot API version and final reviewed event list, and its own signing
  secret on Render. Do not choose a new API version by copying an example.
- Confirm the live plan-to-price mapping after the billing code review.
  Dashboard/portal and checkout settings follow LR-014. The sponsored gate
  stays off until the complete paid-launch acceptance is approved.

## Primary references

[Stripe webhook handling](https://docs.stripe.com/webhooks) documents duplicate
delivery, retry behavior, signature verification and unordered events.
[Event retrieval](https://docs.stripe.com/api/events/retrieve) is limited to
events created within the previous 30 days. Those delivery guarantees inform
this proposed design; they do not authorize live replay or checkout tests.

## Source-to-envelope contract

The current handler reads `data.object.id`, `status`, `current_period_end`,
`metadata.account_id` and `items.data[0].price.id`; these are the exact minimum
subscription fields to normalize for LR-011. Preserve customer ID for LR-012
binding; do not treat arbitrary metadata as authoritative ownership. Multiple
items and version-specific period shapes require an explicit quarantine reason,
not silently selecting the first item or guessing a timestamp.

The existing `db_conn` commits on context exit. Receipt insertion therefore
needs its own context, followed by the processing context; catching an error
inside that second context must never accidentally commit partial account work.
Tests must force both commit failures independently. A paid-launch decision on
entitlements belongs to LR-013, not to this receipt layer.


## Revision 2: deterministic dispositions and cancellation safety

- Expected mode comes from configured server key prefix: `sk_live_` or
  `rk_live_` means live; `sk_test_` or `rk_test_` means test. Unknown or absent
  prefixes are unavailable configuration (503). A verified mismatching event
  is quarantined as `mode_mismatch` with no account mutation; test both ways.
- A signed event with an unexpected business shape must still commit a minimal
  receipt before quarantine. Normalization is total for verified event identity:
  safe identity fields and fixed shape errors survive; optional malformed
  fields never throw before evidence is committed. Unverifiable event identity
  is a separate invalid-envelope rejection, not a guessed identifier.
- Terminal `quarantined` and `ignored` redeliveries return 200 with no work.
  Dashboard resend does not reopen them. Only reviewed replay with dry-run and
  operator reason can reconsider a receipt, and never bypasses the cursor.
- `price.*` and `product.*` events are processed cache-only receipts, with no
  account mutation. Cache invalidation after commit is best effort; it cannot
  make a duplicate rerun a committed account change. Cross-process cache
  invalidation is a separate pre-existing defect, not claimed fixed here.
- A deleted subscription with absent/unrecognized period shape is quarantined
  as `period_shape_unsupported`, leaving paid access untouched. No missing
  timestamp can select immediate Free. Record the live webhook endpoint API
  version before implementation; fixtures must cover legacy top-level period
  and Basil item-level period shapes. Until a shape is explicitly supported,
  quarantine it. Immediate downgrade requires a validated expired period.
- Every new quarantined receipt is an LR-027 incident candidate for configured
  email then SMS, respecting the alert sender's off-by-default rollout. Add
  this actual billing-table signal in coordination with that lane; do not
  infer payment backlog from outbound report webhook logs.

Required regression additions: T2-before-T1 retries and replay; missing period
and Basil-shaped cancellation retaining access; both mode mismatch directions;
malformed signed business shapes retained durably; terminal Dashboard resend;
cache-only disposition; tenant access denied by RLS. All payment fixtures stay
local with provider HTTP blocked. No live payment tests.


## Design PASS implementation notes (Claude 7023347174)

Create the cursor row with INSERT ON CONFLICT DO NOTHING before SELECT FOR
UPDATE, so concurrent first events serialize. Key it by mode and subscription.
Advance it only in the transaction applying an account mutation, never for
quarantined, ignored or cache-only events. A newer quarantined event must not
supersede an older valid change that has not yet been applied.

No tenant route exposes these platform tables; that is the current access
boundary. The app currently connects as a superuser, which bypasses RLS.
Enabling RLS without tenant policies is future defence, not effective tenant
isolation under that connection. RLS tests must use a non-superuser probe role
with tenant context, and separately record the app connection's role flags.
When D-005 hardens the role, the writer must retain table-owner access (without
FORCE RLS), or an explicitly reviewed server-only policy. Do not silently
change database roles in LR-011 or rely on tenant-context tests as that change.


## Live endpoint version confirmed by Jerry

Jerry confirmed `2025-10-29.clover` on November 19. Treat this as the live
webhook endpoint version for signed fixtures, distinct from the SDK outgoing
API default. Include Clover item-level period fields, a legacy fixture and
missing/unsupported-period quarantine controls. This confirmation authorizes
no live provider call or payment test.


## Confirmed live prices and go-live configuration handoff

| Plan | Monthly USD | Live price ID | Live product ID |
|---|---:|---|---|
| Growth (`starter`) | $19 | `price_1UddpFBa27XowvTp6siwCZ3Q` | `prod_VexkO3eDQhdlDr` |
| Growth Plus (`pro`) | $29 | `price_1UddpaBa27XowvTpqu8acKJP` | `prod_VexlkMlXRRVr9r` |

Jerry supplied these IDs; this record is not a provider-side verification or
permission to change anything. Jerry sets live configuration at go-live.

Target handoff after LR-014 removes the obsolete validator (current legacy
price-variable requirements are listed in the source inventory below):

| Host/service | Variable | Value at go-live |
|---|---|---|
| Vercel `reportscompany-web` | No Stripe variables | None: hosted Checkout is created by the API; no Stripe browser SDK/key is consumed. |
| Render `reportscompany-api` | `STRIPE_SECRET_KEY` | Existing live secret key, entered directly by Jerry; exact secret never printed/stored here. |
| Render `reportscompany-api` | `STRIPE_WEBHOOK_SECRET` | Signing secret for the live `/v1/webhooks/stripe` endpoint, entered directly by Jerry; never printed/stored here. |
| Render worker/ticker/bridge | No billing Stripe variables | None required by their current code. |

Price selection is **database configuration** on the active checkout/webhook
path, but checkout and portal still call the legacy configuration validator
which requires both price environment names below. Jerry's go-live DB mapping is:

- `plans.stripe_price_id` for `starter` -> `price_1UddpFBa27XowvTp6siwCZ3Q`.
- `plans.stripe_price_id` for `pro` -> `price_1UddpaBa27XowvTpqu8acKJP`.

The legacy map is not the active price source, but its validator is NOT dead:
`routes/billing.py` calls it for checkout and portal. Missing either legacy
price variable currently refuses both routes. LR-014 must remove the obsolete
Team requirement before go-live; do not invent a Team price or substitute
Growth's price merely to pass validation. Product IDs are references, not
consumed environment values.
The final LR-014 handoff must repeat the exact variable -> value list separately
for Vercel and Render, identify secrets to enter directly, and list these DB
mappings separately. No environment, database mapping, product, price or webhook
was changed while recording this checklist. No live payment tests.


### Stripe variable inventory (source verified; deployed Render names pending)

Vercel production `reportscompany-web` was inspected read-only on November 19:
there are no Stripe-related variable names. The Render connector has no env-list
operation; Jerry has been asked for names only. Do not mistake this source list
for a verified inventory of configured Render variables.

| Code-read variable | Purpose | Identifier expected | Slug | Status / exact nonsecret value |
|---|---|---|---|---|
| `STRIPE_SECRET_KEY` | API Stripe SDK and plan-catalog reads; LR-011 mode derivation | Live secret key, neither `prod_` nor `price_` | All | Required; Jerry enters actual secret directly. |
| `STRIPE_WEBHOOK_SECRET` | Verify original webhook bytes | Endpoint `whsec_` signing secret, neither ID type | All | Required; Jerry enters live endpoint secret directly. |
| `STRIPE_PRICE_PRO_MONTH` | Legacy pro map AND current checkout/portal configuration validation | `price_` | `pro` = Growth Plus | `price_1UddpaBa27XowvTpqu8acKJP` if retained; not the active price selector. |
| `STRIPE_PRICE_TEAM_MONTH` | Legacy team map AND current checkout/portal configuration validation | `price_` | Retired `team`, not `starter` or `pro` | Stale requirement; no approved value. LR-014 removes the requirement before go-live. |

No source-read Starter price environment variable exists. Starter/Growth uses
`plans.stripe_price_id = price_1UddpFBa27XowvTp6siwCZ3Q`; Pro/Growth Plus uses
`plans.stripe_price_id = price_1UddpaBa27XowvTpqu8acKJP`. Neither accepts a product
ID. The legacy lookup/reverse-lookup helper functions have no callers, but
`validate_stripe_config` does. Any extra deployed Stripe product/price names
must be checked against this list and marked unused, not assumed wired up.

Final go-live variable/value handoff remains conditional on the reviewed
LR-014 cleanup. Nobody has edited Vercel, Render, DB plan mappings or Stripe
configuration during this inventory. Actual secret values are not requested,
printed or stored in the checklist.
