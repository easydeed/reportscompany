-- Migration 0036: Add selected_pages column to property_reports
-- Date: 2026-01-12
-- Purpose: Allow users to select which pages to include in their property report PDF

-- ============================================================================
-- ALTER: property_reports table - Add selected_pages column
-- ============================================================================

ALTER TABLE property_reports
ADD COLUMN IF NOT EXISTS selected_pages JSONB;

COMMENT ON COLUMN property_reports.selected_pages IS 'Array of page IDs to include in PDF (NULL = include all pages based on theme)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT '0036_add_selected_pages_to_property_reports.sql applied successfully' AS migration;

