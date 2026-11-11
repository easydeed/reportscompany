-- Migration 0064: who owns a consumer delivery, and what it recorded (LR-020, LR-021).
--
-- Design: docs/plans/launch-readiness-2026-11-06/LR-020-021_DELIVERY_STATE.md
-- (revision 3, Codex PASS on #280).
--
-- Two irreversible acts: the homeowner's report (LR-020) and the agent's new-lead
-- text (LR-021). Each gets its own claim (attempt id + claim time), a journal row
-- written before the provider call, and evidence that is never cleared. Both
-- tickets' columns are here because only one migration PR may be open at a time.
--
-- Additive and nullable, with no defaults: no row is rewritten. Each ALTER still
-- takes a brief ACCESS EXCLUSIVE lock, so the lock wait is bounded and a busy
-- table makes this fail fast (and roll back whole) instead of queueing reads
-- behind it. Re-run it if it times out.
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

SET LOCAL lock_timeout = '5s';

ALTER TABLE consumer_reports
  ADD COLUMN IF NOT EXISTS generation_id            UUID,
  ADD COLUMN IF NOT EXISTS delivery_claimed_at      TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS delivery_attempt_id      UUID,
  ADD COLUMN IF NOT EXISTS agent_notify_status      TEXT,
  ADD COLUMN IF NOT EXISTS agent_notify_claimed_at  TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS agent_notify_attempt_id  UUID,
  ADD COLUMN IF NOT EXISTS agent_notify_error       TEXT;

ALTER TABLE email_log
  ADD COLUMN IF NOT EXISTS idempotency_key      TEXT,
  ADD COLUMN IF NOT EXISTS provider_message_id  TEXT,
  ADD COLUMN IF NOT EXISTS resolution           TEXT,
  ADD COLUMN IF NOT EXISTS resolved_at          TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS resolved_by          TEXT,
  ADD COLUMN IF NOT EXISTS resolution_evidence  TEXT;

ALTER TABLE sms_logs
  ADD COLUMN IF NOT EXISTS resolution           TEXT,
  ADD COLUMN IF NOT EXISTS resolved_at          TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS resolved_by          TEXT,
  ADD COLUMN IF NOT EXISTS resolution_evidence  TEXT;

COMMENT ON COLUMN consumer_reports.generation_id IS
  'The generation (one run''s comps, values and PDF) the report currently shows. Only the run that '
  'published it may claim its delivery; nothing is published while a delivery is claimed or done.';
COMMENT ON COLUMN consumer_reports.delivery_claimed_at IS
  'When the current consumer delivery attempt was claimed. A claim older than '
  'DUPLICATE_SEND_WINDOW_MINUTES with no outcome is stale and is held for review, never resent.';
COMMENT ON COLUMN consumer_reports.delivery_attempt_id IS
  'The claimed consumer delivery attempt: the id of its sms_logs or email_log row. NULL when no '
  'attempt is claimed (a refusal known to have sent nothing releases it).';
COMMENT ON COLUMN consumer_reports.agent_notify_status IS
  'The agent new-lead text (LR-021): NULL (not yet due), sending, sent, failed, needs_review, skipped. '
  'Evidence is agent_sms_sent_at. Never changes the consumer status or credits.';
COMMENT ON COLUMN consumer_reports.agent_notify_claimed_at IS
  'When the current agent notification attempt was claimed (same stale rule as delivery_claimed_at).';
COMMENT ON COLUMN consumer_reports.agent_notify_attempt_id IS
  'The claimed agent notification attempt: the id of its sms_logs row (recipient_type = agent).';
COMMENT ON COLUMN consumer_reports.agent_notify_error IS
  'Why the agent notification failed, was skipped or is held. No contact details.';

COMMENT ON COLUMN email_log.idempotency_key IS
  'The Idempotency-Key sent to the provider. Consumer deliveries: consumer-report:<report_id>:<attempt_id>.';
COMMENT ON COLUMN email_log.provider_message_id IS
  'The provider''s id for the accepted email (Resend email id).';
COMMENT ON COLUMN email_log.resolution IS
  'Operator resolution of a held attempt: sent or not_sent (scripts/ops/held_sends.py). NULL otherwise.';
COMMENT ON COLUMN email_log.resolution_evidence IS
  'What the operator checked to resolve the attempt, as entered.';

COMMENT ON COLUMN sms_logs.resolution IS
  'Operator resolution of a held attempt: sent or not_sent (scripts/ops/held_sends.py). NULL otherwise.';
COMMENT ON COLUMN sms_logs.resolution_evidence IS
  'What the operator checked to resolve the attempt, as entered.';
