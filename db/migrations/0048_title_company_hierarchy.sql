-- Add parent_account_id for title-company → rep hierarchy
-- and expand account_type to include TITLE_COMPANY.

-- 1. Add parent_account_id column (company that owns this rep account)
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS parent_account_id UUID REFERENCES accounts(id);

-- 2. Replace the account_type check constraint to allow TITLE_COMPANY
ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_account_type_check;
ALTER TABLE accounts ADD CONSTRAINT accounts_account_type_check
  CHECK (account_type IN ('REGULAR', 'INDUSTRY_AFFILIATE', 'TITLE_COMPANY'));

-- 3. Index for fast company → reps lookup
CREATE INDEX IF NOT EXISTS idx_accounts_parent_account
  ON accounts(parent_account_id) WHERE parent_account_id IS NOT NULL;

-- 4. idx_accounts_sponsor already exists (migration 0042) — no-op guard
CREATE INDEX IF NOT EXISTS idx_accounts_sponsor
  ON accounts(sponsor_account_id) WHERE sponsor_account_id IS NOT NULL;

SELECT '0048_title_company_hierarchy.sql applied' AS migration;
