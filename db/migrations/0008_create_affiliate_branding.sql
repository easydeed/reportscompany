-- Phase 30: Affiliate Branding & White-Label Output
-- Migration: Create affiliate_branding table for white-label customization

-- ============================================================================
-- AFFILIATE BRANDING TABLE
-- ============================================================================
-- Purpose: Store branding/visual identity for industry affiliates
-- Used for: Client-facing PDFs and emails for sponsored accounts
-- ============================================================================

CREATE TABLE IF NOT EXISTS affiliate_branding (
  account_id uuid PRIMARY KEY
    REFERENCES accounts(id) ON DELETE CASCADE,
  
  -- Core branding
  brand_display_name text NOT NULL,
  logo_url text,             -- URL to logo image (hosted externally or R2)
  
  -- Colors
  primary_color text,        -- hex string, e.g. #1473e6 (header, ribbons)
  accent_color text,         -- hex string (buttons, highlights)
  
  -- Optional rep/contact info
  rep_photo_url text,        -- optional headshot for personalization
  contact_line1 text,        -- e.g. "John Doe • Senior Title Rep"
  contact_line2 text,        -- e.g. "555-123-4567 • john@company.com"
  website_url text,          -- affiliate website for footer links
  
  -- Metadata
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Index for fast lookups
CREATE INDEX idx_affiliate_branding_account_id ON affiliate_branding(account_id);

-- Comments for clarity
COMMENT ON TABLE affiliate_branding IS 'White-label branding configuration for industry affiliates';
COMMENT ON COLUMN affiliate_branding.brand_display_name IS 'Name shown to end clients on reports and emails';
COMMENT ON COLUMN affiliate_branding.logo_url IS 'URL to affiliate logo (replaces TrendyReports branding)';
COMMENT ON COLUMN affiliate_branding.primary_color IS 'Primary brand color (hex), used for headers and ribbons';
COMMENT ON COLUMN affiliate_branding.accent_color IS 'Accent brand color (hex), used for CTAs and highlights';
COMMENT ON COLUMN affiliate_branding.rep_photo_url IS 'Optional representative photo for email personalization';
COMMENT ON COLUMN affiliate_branding.contact_line1 IS 'Primary contact line (name, title)';
COMMENT ON COLUMN affiliate_branding.contact_line2 IS 'Secondary contact line (phone, email)';

-- ============================================================================
-- USAGE NOTES
-- ============================================================================
-- Brand Resolution Logic:
--   1. For REGULAR accounts with sponsor_account_id:
--      → Use sponsor's branding from this table
--   2. For INDUSTRY_AFFILIATE accounts:
--      → Use their own branding from this table
--   3. For unsponsored REGULAR accounts:
--      → Fall back to TrendyReports default branding
--
-- This table is optional - if no row exists, system uses sensible defaults
-- (account name + TrendyReports colors)
-- ============================================================================

