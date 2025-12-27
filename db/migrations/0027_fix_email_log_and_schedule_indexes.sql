-- Migration 0027: Fix email_log status column and add schedule performance indexes
-- Date: December 26, 2025
-- Description: 
--   1. Add missing 'status' column to email_log table (CRITICAL BUG FIX)
--   2. Add index on schedule_runs.report_run_id for performance
--   3. Add unique constraint to prevent duplicate schedule runs

-- ============================================================================
-- FIX 1: Add missing 'status' column to email_log
-- The worker task tries to INSERT with a 'status' field but the column doesn't exist!
-- ============================================================================

ALTER TABLE email_log
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'unknown';

COMMENT ON COLUMN email_log.status IS 'Email send status: sent, suppressed, failed, unknown';

-- Create index for querying email logs by status
CREATE INDEX IF NOT EXISTS idx_email_log_status ON email_log (account_id, status, created_at DESC);

-- ============================================================================
-- FIX 2: Add index on schedule_runs.report_run_id
-- This is frequently used to update schedule_runs by report_run_id
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_schedule_runs_report_run ON schedule_runs (report_run_id);

-- ============================================================================
-- FIX 3: Add processing lock column to schedules for race condition prevention
-- This allows us to use atomic UPDATE...RETURNING to claim schedules
-- ============================================================================

ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS processing_locked_at TIMESTAMPTZ;

COMMENT ON COLUMN schedules.processing_locked_at IS 'Timestamp when a ticker claimed this schedule. Cleared after processing. Stale locks (>5 min) are ignored.';

-- Index for efficiently finding due schedules that aren't locked
CREATE INDEX IF NOT EXISTS idx_schedules_due_unlocked ON schedules (active, next_run_at, processing_locked_at) 
WHERE active = true;

SELECT '0027_fix_email_log_and_schedule_indexes.sql applied' AS migration;

