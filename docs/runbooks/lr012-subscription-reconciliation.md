# LR-012 release and operator handoff

## Release sequence

Migration 0071_effective_account_plan.sql adds only a SECURITY INVOKER SQL
function. It changes no account, plan, price, override or environment value.
It has been applied only to disposable local test databases. After independent
Claude code PASS and a green Release gate, Jerry applies exactly 0071 before
runtime merge: status must show only that file pending; otherwise stop.
Apply normally, never bootstrap; status after must show zero pending. Leave
0012's existing checksum warning alone. Verify the function exists and its
before/equal/after database-clock boundary without changing an account.

Run scripts/readonly/lr012_billing_state_inventory.sql read-only before rollout.
A paid account without a binding or a mismatch is not silently repaired.
Quarantines are visible through LR-011 backlog and LR-027 billing alerts.
LR-014 checkout uniqueness remains required before outreach. LR-013 owns
payment-status/grace policy; this change does not claim those policies fixed.

## Concurrency and provider boundary

Signed receipt commits first. Processing holds receipt row → account advisory
lock → authoritative customer subscription list → cursor row → account row.
Only the advisory lock spans Stripe, never an account/cursor row lock. Reads
run in the worker thread; the route awaits the whole store/process operation.
A dedicated async Stripe client disables retries, uses 2-second operation
limits and a 6-second request budget. Cancellation closes the client before
return. Lock acquisition is limited to 2 seconds; the held section is budgeted
at 10 seconds with remaining statement/commit timeouts. Provider failure leaves
the durable receipt pending and returns retryable 503, without partial writes.

Every API/worker entitlement consumer uses effective_account_plan, evaluated
with PostgreSQL now() and deadline <= now(). Usage reads never materialize
billing state. Stored account plans remain diagnostic facts; plan-facing
account output projects access. Zero/unlimited overrides and scheduled/manual
allowance separation remain in the existing allowance resolvers.

When product limits establish a strictly ordered transition, increases apply
now and decreases wait for the authoritative period end. Mixed/equal/unknown
paid tiers are quarantined as plan_transition_ambiguous rather than inventing
a price or treating a plan name as a rank. No production catalog is changed.
Review this conservative boundary against LR-032's unsettled plan catalog.

## Historical customer mismatch: review then conditional repair

1. Inspect the restricted receipt with scripts/replay_billing_event.py in its
   default dry-run mode. Compare account binding, subscription and customer in
   Stripe dashboard evidence; do not create a payment, attach by metadata alone,
   retrieve arbitrary objects in the webhook, or paste contacts/keys into chat.
2. Produce a reviewed repair list with account, expected OLD customer/subscription,
   proposed NEW customer/subscription and the evidence of ownership. Include
   duplicate-customer and multiple-subscription checks. Ambiguous cases stay held.
3. Jerry must explicitly authorize each exact repair before any production write.
   No repair/backfill is authorized by this runbook or by migration approval.
4. For an authorized correction, use a transaction with lock_timeout=2s and
   statement_timeout=5s. Acquire the same billing_account:<account UUID> advisory
   lock, then SELECT that account FOR UPDATE. Recheck all expected old binding
   values. UPDATE only the approved binding with matching old-value predicates
   using IS NOT DISTINCT FROM; require exactly one returned row, otherwise
   ROLLBACK. Do not change plan_slug, prices, overrides or downgrade fields by
   hand, and never cancel/refund a subscription as part of this repair.
5. Re-run the read-only inventory; retain restricted before/after evidence.
   Replay only the reviewed quarantined receipt, explicitly by event ID and
   mode with --apply and a review reason. Replay uses the ordinary authoritative
   reconciliation and cannot bypass ordering or binding guards. A still
   ambiguous customer remains quarantined; do not force success or re-send
   customer communications. Recheck backlog/disposition after the approved replay.

No live provider request, payment test, production repair or replay has been
performed to develop or verify this PR.

## Regression maintenance

The old cursor-only-lock mutation is retired: LR-012's earlier account advisory
lock now serializes the entire transition, so removing the redundant cursor row
lock alone no longer creates the old overwrite race. The cursor lock remains
in production code and its lock order is reviewed. Its replacement mutation
removes account serialization and is caught by simultaneous distinct receipts.
The six other LR-011 mutations remain, with the cancellation anchor relocated
to billing_reconcile.py. This is not a claim that the old seven mutations ran
unchanged. New LR-012 mutations additionally cover binding, incomplete inventory,
provider retry policy, request-loop blocking, and the inclusive SQL deadline.
