-- Migration 0021: Add email_footer_logo_url to affiliate_branding
-- Purpose: Allow separate footer logos for email output (vs PDF output)

-- Add email_footer_logo_url column
ALTER TABLE affiliate_branding
ADD COLUMN IF NOT EXISTS email_footer_logo_url text;

-- Add comment for clarity
COMMENT ON COLUMN affiliate_branding.email_footer_logo_url IS 
  'Logo URL for email footers (appears on light background - use dark/colored version)';

-- ============================================================================
-- LOGO FIELDS SUMMARY
-- ============================================================================
-- PDF Output:
--   logo_url           → PDF header (gradient background - light/white logo)
--   footer_logo_url    → PDF footer (gray background - dark/colored logo)
--
-- Email Output:
--   email_logo_url        → Email header (gradient background - light/white logo)
--   email_footer_logo_url → Email footer (light background - dark/colored logo)
-- ============================================================================
