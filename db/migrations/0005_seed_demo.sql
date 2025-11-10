-- Seed Demo Account for Staging
-- This runs automatically via scripts/migrate.sh
-- Creates the account used by NEXT_PUBLIC_DEMO_ACCOUNT_ID

-- Insert demo account if it doesn't exist
INSERT INTO accounts (id, name, slug, status, monthly_report_limit, api_rate_limit)
VALUES (
  '912014c3-6deb-4b40-a28d-489ef3923a3a',
  'Demo Account',
  'demo',
  'active',
  1000,
  1000
)
ON CONFLICT (id) DO NOTHING;

-- Verify
SELECT id, name, slug, status FROM accounts WHERE id = '912014c3-6deb-4b40-a28d-489ef3923a3a';

