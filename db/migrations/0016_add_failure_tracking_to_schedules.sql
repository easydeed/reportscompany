-- Migration 0016: Add failure tracking to schedules
-- Date: November 24, 2025
-- Description: PASS S3 - Track consecutive failures and auto-pause after threshold

-- Add failure tracking columns
ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS consecutive_failures INT NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_error TEXT,
ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMPTZ;

-- Add comments for documentation
COMMENT ON COLUMN schedules.consecutive_failures IS 'Count of consecutive failed executions. Reset to 0 on successful run. Auto-pause schedule after 3.';
COMMENT ON COLUMN schedules.last_error IS 'Error message from most recent failure (truncated to ~2KB).';
COMMENT ON COLUMN schedules.last_error_at IS 'Timestamp of most recent failure.';

-- Add index for querying schedules with failures
CREATE INDEX IF NOT EXISTS idx_schedules_failures ON schedules (consecutive_failures, active) WHERE consecutive_failures > 0;

