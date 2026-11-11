-- Migration 0066: a retried create cannot make a second report or schedule (LR-024, D-382/D-330).
--
-- The report wizard's create can succeed and lose its answer (a dropped
-- connection, a proxy timeout, a tab asleep). "Try again" then made a second
-- report (two usage counts, two emails to each recipient) or a second
-- schedule that sends on every run. The wizard now sends an Idempotency-Key
-- to POST /v1/idempotent/{reports,schedules}; this table remembers which
-- resource each key created, so a retry returns that resource instead.
--
--   account_id    the caller's account; a key is scoped to (account, endpoint)
--   endpoint      reports.create | schedules.create
--   idem_key      the client's key (8–100 of [A-Za-z0-9_-])
--   request_hash  sha256 of the validated request (canonical JSON); a reused
--                 key with a different body is refused (409)
--   resource_id   report_generations.id or schedules.id; no FK, because it
--                 names either table and a deleted schedule must still be
--                 recognised (410 gone, never recreated)
--   created_at    a key older than the 7-day replay window is refused (410),
--                 never treated as new; rows are kept
--
-- A row is written in the same transaction as the resource, so a refused or
-- failed create leaves no key. Design: docs/plans/launch-readiness-2026-11-06/
-- LR-024_SAFE_RETRY.md (rev 3, Codex design PASS).
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

SET LOCAL lock_timeout = '5s';

CREATE TABLE IF NOT EXISTS request_idempotency (
  account_id   UUID        NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  endpoint     TEXT        NOT NULL CHECK (endpoint IN ('reports.create', 'schedules.create')),
  idem_key     TEXT        NOT NULL CHECK (idem_key ~ '^[A-Za-z0-9_-]{8,100}$'),
  request_hash TEXT        NOT NULL,
  resource_id  UUID        NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (account_id, endpoint, idem_key)
);

COMMENT ON TABLE request_idempotency IS
  'LR-024: which resource each Idempotency-Key created, per account and endpoint. A retry replays it; rows are kept.';

ALTER TABLE request_idempotency ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS request_idempotency_rls ON request_idempotency;
CREATE POLICY request_idempotency_rls ON request_idempotency
    FOR ALL
    USING (
        account_id = current_setting('app.current_account_id', true)::uuid
        OR current_setting('app.current_user_role', true) = 'ADMIN'
    );
