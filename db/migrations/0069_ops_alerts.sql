-- Migration 0069: operator alert state (LR-027).
--
-- Design: docs/plans/launch-readiness-2026-11-06/LR-027_OPERATIONAL_ALERTS.md
-- (rev 3, Codex design PASS, merged as #317), section 5.
--
-- Three new tables, owned by the monitor that runs in the ticker. Nothing here
-- alters an existing table, so applying it changes no current behaviour, and an
-- older binary after a rollback ignores the tables.
--
--   ops_alerts               one row per incident. At most one OPEN incident per
--                            signal key (partial unique index). Kept 90 days
--                            after it resolves.
--   ops_alert_members        the incident's COMPLETE membership: one row per
--                            attempt identity (run:<id>, email:<id>,
--                            schedule:<id>, ...). "New" means no row yet, so a
--                            member is announced once, never every 5 minutes.
--   ops_alert_notifications  one row per incident x event x channel, with a
--                            claim committed BEFORE the provider call. Used by
--                            the sender (slice 3); the observe-only monitor
--                            (slice 2) never writes it.
--
-- No account data lives here: identities are UUID-based references, counts and
-- timestamps. No RLS: these are platform tables, read by the ticker and by
-- admin routes only.
--
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

SET LOCAL lock_timeout = '5s';

CREATE TABLE IF NOT EXISTS ops_alerts (
  id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  key                TEXT        NOT NULL,
  opened_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at        TIMESTAMPTZ,
  last_value         JSONB       NOT NULL DEFAULT '{}'::jsonb,
  member_count       INTEGER     NOT NULL DEFAULT 0,
  -- More outstanding identities than one run stores (5,000): "new" then means
  -- the count grew past notified_count, not "an identity outside the set".
  members_truncated  BOOLEAN     NOT NULL DEFAULT FALSE,
  notified_count     INTEGER     NOT NULL DEFAULT 0,
  last_evaluated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ops_alerts_one_open_per_key
  ON ops_alerts (key) WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS ops_alerts_resolved_at
  ON ops_alerts (resolved_at) WHERE resolved_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS ops_alert_members (
  alert_id      UUID        NOT NULL REFERENCES ops_alerts (id) ON DELETE CASCADE,
  identity      TEXT        NOT NULL,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (alert_id, identity)
);

CREATE TABLE IF NOT EXISTS ops_alert_notifications (
  id                  BIGSERIAL   PRIMARY KEY,
  alert_id            UUID        NOT NULL REFERENCES ops_alerts (id) ON DELETE CASCADE,
  event               TEXT        NOT NULL,   -- open, renotify:<n>, resolved
  channel             TEXT        NOT NULL CHECK (channel IN ('email', 'sms')),
  state               TEXT        NOT NULL DEFAULT 'pending'
                      CHECK (state IN ('pending', 'claimed', 'accepted', 'not_sent', 'unknown')),
  claimed_at          TIMESTAMPTZ,
  claim_token         UUID,
  attempts            INTEGER     NOT NULL DEFAULT 0,
  outcome_at          TIMESTAMPTZ,
  provider_message_id TEXT,
  last_error_class    TEXT,
  resolution          TEXT        CHECK (resolution IN ('received', 'not_received')),
  resolution_evidence TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (alert_id, event, channel)
);

COMMENT ON TABLE ops_alerts IS
  'LR-027: one row per operator-alert incident; at most one open per key. Platform table, no account data.';
COMMENT ON TABLE ops_alert_members IS
  'LR-027: complete incident membership by attempt identity; a member is new only when it has no row.';
COMMENT ON TABLE ops_alert_notifications IS
  'LR-027: per incident x event x channel. claimed_at is committed before the provider call; accepted = provider acknowledged; unknown is never retried automatically.';
