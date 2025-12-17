-- Migration 0022: Add full branding fields to accounts table
-- Purpose: Give regular users same branding capabilities as affiliates
-- This makes branding uniform across all user types

-- ============================================================================
-- ADD LOGO FIELDS
-- ============================================================================

-- Footer logo for PDF (appears on gray background - use dark version)
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS footer_logo_url TEXT;

-- Email header logo (appears on gradient - use light version)
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS email_logo_url TEXT;

-- Email footer logo (appears on white background - use dark version)
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS email_footer_logo_url TEXT;

-- ============================================================================
-- ADD CONTACT INFO FIELDS
-- ============================================================================

-- Representative/agent photo
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS rep_photo_url TEXT;

-- Contact line 1 (typically: Name • Title)
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS contact_line1 TEXT;

-- Contact line 2 (typically: Phone • Email)
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS contact_line2 TEXT;

-- Website URL
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS website_url TEXT;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN accounts.footer_logo_url IS 'Logo URL for PDF footers (gray background - use dark/colored version)';
COMMENT ON COLUMN accounts.email_logo_url IS 'Logo URL for email headers (gradient background - use light/white version)';
COMMENT ON COLUMN accounts.email_footer_logo_url IS 'Logo URL for email footers (white background - use dark/colored version)';
COMMENT ON COLUMN accounts.rep_photo_url IS 'Representative/agent headshot photo URL';
COMMENT ON COLUMN accounts.contact_line1 IS 'Primary contact line (e.g., "John Doe • Agent")';
COMMENT ON COLUMN accounts.contact_line2 IS 'Secondary contact line (e.g., "555-123-4567 • john@email.com")';
COMMENT ON COLUMN accounts.website_url IS 'Website URL for footer links';

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Accounts table now has same branding fields as affiliate_branding:
-- 
-- PDF Output:
--   logo_url           → PDF header (gradient background)
--   footer_logo_url    → PDF footer (gray background)
--
-- Email Output:
--   email_logo_url        → Email header (gradient background)
--   email_footer_logo_url → Email footer (white background)
--
-- Contact Info:
--   rep_photo_url, contact_line1, contact_line2, website_url
-- ============================================================================
