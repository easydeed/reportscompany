-- Migration 0015: Add timezone support to schedules
-- Date: November 24, 2025
-- Description: PASS S2 - Add timezone column to enable local time scheduling

-- Add timezone column (defaults to UTC for existing schedules)
ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS timezone TEXT NOT NULL DEFAULT 'UTC';

-- Add comment for documentation
COMMENT ON COLUMN schedules.timezone IS 'IANA timezone for schedule execution (e.g., America/Los_Angeles). send_hour and send_minute are interpreted in this timezone, then converted to UTC for next_run_at storage.';

-- Validation: Ensure timezone is not empty (we don't validate IANA at DB level)
ALTER TABLE schedules
ADD CONSTRAINT IF NOT EXISTS schedules_timezone_not_empty
CHECK (timezone != '');

