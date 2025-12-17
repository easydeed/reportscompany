-- Migration 0020: Add footer_logo_url to affiliate_branding
-- Purpose: Allow affiliates to have a separate logo for PDF footers
-- (since header logos are on colored gradient, footer is on gray background)

-- Add footer_logo_url column
ALTER TABLE affiliate_branding
ADD COLUMN IF NOT EXISTS footer_logo_url text;

-- Add comment for clarity
COMMENT ON COLUMN affiliate_branding.footer_logo_url IS 
  'Logo URL for PDF footers (appears on gray background - use darker/colored version of logo)';

-- ============================================================================
-- USAGE NOTES
-- ============================================================================
-- logo_url: Used in hero header (on gradient background - white/light logos work best)
-- footer_logo_url: Used in PDF footer (on gray background - dark/colored logos work best)
-- If footer_logo_url is NULL, system can fall back to logo_url or text
-- ============================================================================
