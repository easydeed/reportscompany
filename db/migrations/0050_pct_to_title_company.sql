-- One-time migration: promote Pacific Coast Title from INDUSTRY_AFFILIATE to TITLE_COMPANY.
-- After running, the PCT admin must log out and log back in to get a fresh JWT.

-- Verify current state (informational — run SELECT first to confirm the right row)
-- SELECT id, name, account_type, plan_slug FROM accounts
--   WHERE name ILIKE '%pacific coast%' OR slug ILIKE '%pct%';

UPDATE accounts
SET account_type = 'TITLE_COMPANY',
    updated_at   = NOW()
WHERE account_type = 'INDUSTRY_AFFILIATE'
  AND (name ILIKE '%pacific coast%' OR slug ILIKE '%pacific-coast%')
RETURNING id::text, name, account_type, plan_slug;

SELECT '0050_pct_to_title_company.sql applied' AS migration;
