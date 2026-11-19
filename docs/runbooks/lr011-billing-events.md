# LR-011 billing event recovery

Stripe is live. This runbook authorizes no checkout, provider retrieval, refund,
cancellation or bulk replay. LR-012 through LR-014 still gate paid launch.
The live endpoint version confirmed by Jerry is `2025-10-29.clover`.

## Rollout

Code review and a current-head green Release gate precede the handoff to Jerry.
Jerry applies `0070_billing_webhook_events.sql` from the reviewed checkout,
against mr-staging-db, before runtime merge. Status must show exactly that one
pending file; otherwise stop. Apply once, then verify zero pending and its
schema_migrations row. Never bootstrap or re-run 0012. The new tables contain no
historical data and modify no existing accounts. Both service guards require
0070. Verify the merged API/worker/ticker deployments and `/ready` afterward.

## Inspect before replay

Run from the repo with the authorized database configuration and matching
Stripe mode. Credentials stay in the environment; never paste them into chat.

```sh
python scripts/replay_billing_event.py --mode live
python scripts/replay_billing_event.py --mode live --event-id evt_REVIEWED
```

The first command lists backlog counts and up to 100 receipts. The second is a
read-only dry run. Review age, reason, account/subscription ownership and the
intended correction before allowing a specific receipt to run. Do not infer a
payment from an unknown price or missing period. Quarantined/ignored Dashboard
resends are terminal and never bypass this process.

Only for an explicitly reviewed receipt:

```sh
python scripts/replay_billing_event.py --mode live --event-id evt_REVIEWED \
  --apply --reason "reviewed mapping correction"
```

Replay uses the same transaction/ordering locks as redelivery. Superseded
receipts are refused by default. A quarantined event advances no cursor;
successful account mutation and cursor advancement commit atomically. Tied
event timestamps remain LR-012's reconciliation work. No force/reorder option
exists. The stored allowlist cannot repair malformed original metadata: leave
that quarantine for reviewed reconciliation rather than editing receipt JSON.

An account-processing error leaves a committed pending receipt and returns 503;
Stripe retains retry responsibility. There is no new acknowledgement queue.
Cache invalidation failure after commit cannot repeat account mutation.

## Access and monitoring

No tenant route reads these platform tables. RLS has no tenant policies, but
the current superuser connection bypasses it. Role hardening must preserve
explicit server writer access. Local tests use a separate non-superuser probe.
`billing_events.backlog` reads the actual inbound pending/retryable/quarantined
rows. Coordinate those counts and new quarantines with the LR-027 lane; outbound
report webhook rows are not a billing backlog. Alert sending stays off until
Jerry approves that rollout. No live event replay is a release smoke test.
