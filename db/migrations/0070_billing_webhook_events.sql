-- LR-011: verified allowlisted receipts and per-subscription ordering.
-- Additive only; Jerry applies before runtime merge. No existing rows changed.
SET LOCAL lock_timeout = '5s';
CREATE TABLE billing_webhook_events (
  event_id text NOT NULL,
  livemode boolean NOT NULL,
  envelope jsonb NOT NULL,
  state text NOT NULL DEFAULT 'pending'
    CHECK (state IN ('pending','retryable','processed','quarantined','ignored')),
  reason text,
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz,
  attempts integer NOT NULL DEFAULT 0,
  replay_reason text,
  replayed_at timestamptz,
  PRIMARY KEY (livemode, event_id)
);
CREATE INDEX billing_webhook_events_backlog ON billing_webhook_events (received_at)
  WHERE state IN ('pending','retryable','quarantined');
CREATE TABLE billing_subscription_cursors (
  livemode boolean NOT NULL,
  subscription_id text NOT NULL,
  created bigint,
  event_id text,
  PRIMARY KEY (livemode, subscription_id)
);
-- No tenant policies. The server currently uses a superuser (D-005), so RLS
-- is defence for a future hardened role, not today's access boundary.
-- A hardened writer must own these tables without FORCE RLS or receive an
-- explicitly reviewed server-only policy. No tenant route exposes receipts.
ALTER TABLE billing_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_subscription_cursors ENABLE ROW LEVEL SECURITY;
