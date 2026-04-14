-- Add branding_override flag to affiliate_branding.
-- When FALSE (default), the row inherits updates from the parent company branding.
-- When TRUE, the rep has customized their own branding and company cascades skip them.

ALTER TABLE affiliate_branding
  ADD COLUMN IF NOT EXISTS branding_override BOOLEAN NOT NULL DEFAULT FALSE;

SELECT '0049_branding_override_flag.sql applied' AS migration;
