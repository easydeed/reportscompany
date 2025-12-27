-- Migration: Schedule Filters for Presets Feature
-- Adds filters JSONB column to schedules table for preset-based filtering
-- 
-- ROLLBACK INSTRUCTIONS:
-- To rollback this migration, run the commands in the ROLLBACK section below
-- ============================================================================

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Add filters column to store preset filter criteria
-- Stores: minbeds, minbaths, minprice, maxprice, subtype
ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS filters JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN schedules.filters IS 'JSON object containing filter criteria: minbeds, minbaths, minprice, maxprice, subtype. Empty {} means no filters (show all).';

-- Create index for potential future queries on filter criteria
CREATE INDEX IF NOT EXISTS idx_schedules_filters ON schedules USING gin (filters);

-- ============================================================================
-- ROLLBACK (run these commands to undo this migration)
-- ============================================================================
-- 
-- DROP INDEX IF EXISTS idx_schedules_filters;
-- ALTER TABLE schedules DROP COLUMN IF EXISTS filters;
--
-- ============================================================================


