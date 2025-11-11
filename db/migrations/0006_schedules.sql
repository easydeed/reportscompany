-- Migration 0006: Schedules System
-- Date: November 10, 2025
-- Description: Add schedules, schedule_runs, email_log, and email_suppressions with RLS

-- ============================================================================
-- Schedules: Automated report generation and delivery
-- ============================================================================

CREATE TABLE IF NOT EXISTS schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  report_type TEXT NOT NULL,                 -- e.g., market_snapshot, new_listings, closed, inventory, price_bands, open_houses
  city TEXT,                                 -- simple v1 target area
  zip_codes TEXT[],                          -- or ZIP list
  lookback_days INT DEFAULT 30,

  cadence TEXT NOT NULL CHECK (cadence IN ('weekly','monthly')),
  weekly_dow INT,                            -- 0=Sun .. 6=Sat
  monthly_dom INT,                           -- 1..28
  send_hour INT DEFAULT 9,                   -- 0..23
  send_minute INT DEFAULT 0,                 -- 0..59

  recipients TEXT[] NOT NULL,                -- list of recipient emails (audiences later)
  include_attachment BOOLEAN DEFAULT FALSE,  -- v1: false (link-only)
  active BOOLEAN DEFAULT TRUE,

  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schedules_due ON schedules (account_id, active, next_run_at);

-- ============================================================================
-- Schedule Runs: Audit trail for schedule-triggered report executions
-- ============================================================================

CREATE TABLE IF NOT EXISTS schedule_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  report_run_id UUID,                        -- link to report_generations.id
  status TEXT NOT NULL DEFAULT 'queued',     -- queued|processing|completed|failed
  error TEXT,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schedule_runs_sched ON schedule_runs (schedule_id, created_at DESC);

-- ============================================================================
-- Email Log: Track all email deliveries (provider response)
-- ============================================================================

CREATE TABLE IF NOT EXISTS email_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  schedule_id UUID,
  report_id UUID,
  provider TEXT,                 -- e.g., 'sendgrid'
  to_emails TEXT[],
  subject TEXT,
  response_code INT,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_log_acct ON email_log (account_id, created_at DESC);

-- ============================================================================
-- Email Suppressions: Unsubscribe list
-- ============================================================================

CREATE TABLE IF NOT EXISTS email_suppressions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(account_id, email)
);

-- ============================================================================
-- Enable Row-Level Security
-- ============================================================================

ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedule_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_suppressions ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies: Scoped by account_id
-- ============================================================================

DO $$
BEGIN
  -- Schedules policy
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='schedules' AND policyname='schedules_rls') THEN
    EXECUTE 'CREATE POLICY schedules_rls ON schedules
      FOR ALL USING (account_id = current_setting(''app.current_account_id'', true)::uuid)
      WITH CHECK  (account_id = current_setting(''app.current_account_id'', true)::uuid)';
  END IF;

  -- Schedule runs policy (via schedules join)
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='schedule_runs' AND policyname='schedule_runs_rls') THEN
    EXECUTE 'CREATE POLICY schedule_runs_rls ON schedule_runs
      FOR ALL USING (schedule_id IN (SELECT id FROM schedules WHERE account_id = current_setting(''app.current_account_id'', true)::uuid))
      WITH CHECK  (schedule_id IN (SELECT id FROM schedules WHERE account_id = current_setting(''app.current_account_id'', true)::uuid))';
  END IF;

  -- Email log policy
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='email_log' AND policyname='email_log_rls') THEN
    EXECUTE 'CREATE POLICY email_log_rls ON email_log
      FOR ALL USING (account_id = current_setting(''app.current_account_id'', true)::uuid)
      WITH CHECK  (account_id = current_setting(''app.current_account_id'', true)::uuid)';
  END IF;

  -- Email suppressions policy
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='email_suppressions' AND policyname='email_suppressions_rls') THEN
    EXECUTE 'CREATE POLICY email_suppressions_rls ON email_suppressions
      FOR ALL USING (account_id = current_setting(''app.current_account_id'', true)::uuid)
      WITH CHECK  (account_id = current_setting(''app.current_account_id'', true)::uuid)';
  END IF;
END $$;

SELECT '0006_schedules.sql applied' AS migration;


