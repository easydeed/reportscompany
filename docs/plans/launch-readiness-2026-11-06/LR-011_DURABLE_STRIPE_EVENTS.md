# LR-011: durable Stripe ingestion — proposed design

Base main: `79661c427784a412a902037e1da636477cbb66fa`.
Status: design preparation, not runtime implementation or paid-launch approval.
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
customer `webhook_deliveries`. Do not reserve a migration number yet: #323 owns
0069 and remains the one open migration PR. Jerry applies a reviewed billing
migration before the associated runtime merge when that slot becomes available.

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

LR-012 must serialize/reconcile distinct events for one subscription; receipt
deduplication by event ID does **not** solve out-of-order or tied events.

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
  Growth = `starter`, **$19**; Growth Plus = `pro`, **$29**. Existing live
  product names/prices still need confirmation; do not silently reuse test IDs.
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
