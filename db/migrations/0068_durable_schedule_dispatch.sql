-- Migration 0068: a committed scheduled send survives a broker failure (LR-023, D-381).
--
-- The ticker commits a schedule run and then publishes its Celery task. When the
-- publish failed, or the worker died mid-run, the occurrence was lost: the
-- stale sweep marked it failed and next_run_at had already moved to next week.
-- These columns let the ticker and the sweep republish an occurrence safely,
-- and let the worker prove it alone owns the run before it sends anything.
--
-- Design: docs/plans/launch-readiness-2026-11-06/LR-023_DURABLE_DISPATCH.md
-- (rev 3, Codex design PASS on #286).
--
--   recovery_tracked   TRUE only on rows the new ticker inserts. Every existing
--                      row, and any row an old ticker writes during the rollout,
--                      stays FALSE and keeps today's stale-sweep path exactly.
--                      No backfill; nothing is inferred from timestamps.
--   dispatched_at      a publish the broker acknowledged; NULL = not yet / unknown
--   dispatch_attempts  publishes attempted, the first included (cap: 6)
--   last_dispatch_at   when the last publish attempt started (backoff 2/4/8/16 min)
--   last_dispatch_error the last publish failure, for operators
--   owner_token,       the execution lease: one conditional UPDATE takes it, so
--   lease_at           exactly one worker owns the run; every later write by an
--                      owner is conditioned on its token
--   send_claimed_at,   the durable pre-send claim, committed after the render and
--   send_token         before the first HTTP POST. Never cleared. A run with a
--                      claim and no recorded outcome is needs_review, never resent.
--   send_recipients    the exact recipients the claim committed to
--   send_outcomes      one entry per recipient POSTed: {email, outcome, status_code, at}
--
-- New schedule_runs.status values (free text since 0006, no constraint):
-- cancelled, expired, blocked_unverified, needs_review.
--
-- Every ADD COLUMN has a constant default or none, so none rewrites the table.
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

SET LOCAL lock_timeout = '5s';

ALTER TABLE schedule_runs
  ADD COLUMN IF NOT EXISTS recovery_tracked    BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS dispatched_at       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS dispatch_attempts   INTEGER     NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS last_dispatch_at    TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_dispatch_error TEXT,
  ADD COLUMN IF NOT EXISTS owner_token         UUID,
  ADD COLUMN IF NOT EXISTS lease_at            TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS send_claimed_at     TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS send_token          UUID,
  ADD COLUMN IF NOT EXISTS send_recipients     TEXT[],
  ADD COLUMN IF NOT EXISTS send_outcomes       JSONB       NOT NULL DEFAULT '[]'::jsonb;

-- The sweep reads only tracked, open rows.
CREATE INDEX IF NOT EXISTS idx_schedule_runs_tracked_open
  ON schedule_runs (created_at)
  WHERE recovery_tracked AND status IN ('queued', 'processing');

COMMENT ON COLUMN schedule_runs.recovery_tracked IS
  'LR-023: TRUE only on rows the durable ticker inserts; FALSE rows follow the legacy stale sweep and are never republished, leased or send-claimed.';
COMMENT ON COLUMN schedule_runs.send_claimed_at IS
  'LR-023: committed before the first provider POST and never cleared. Set with no recorded outcome means the send may have happened: needs_review, never resent.';
COMMENT ON COLUMN schedule_runs.status IS
  'queued, processing, completed, failed, failed_email, skipped_empty, skipped_limit (historical), '
  'and for recovery-tracked rows (LR-023): cancelled, expired, blocked_unverified, needs_review.';

COMMENT ON COLUMN email_log.status IS
  'Delivery status. Deliveries: sending (attempt recorded before the provider call), sent, failed, '
  'needs_review (a scheduled send whose provider outcome is unknown for at least one recipient; never resent, LR-023). '
  'Not deliveries: suppressed (provider-suppressed, no email key, or a report that matched nothing), '
  'duplicate_suppressed (a redelivery refused), blocked_unverified (unverified account email), '
  'queued (company test email before its send). unknown: historical rows only.';
