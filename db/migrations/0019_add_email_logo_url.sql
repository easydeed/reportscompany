-- Migration 0019: Add email_logo_url to affiliate_branding
-- Allows affiliates to specify a separate logo for email headers (light version for gradient backgrounds)

ALTER TABLE affiliate_branding
ADD COLUMN IF NOT EXISTS email_logo_url TEXT;

COMMENT ON COLUMN affiliate_branding.email_logo_url IS 'Separate logo URL for email headers (light version for gradient backgrounds)';

