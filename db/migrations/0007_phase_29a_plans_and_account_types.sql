-- Migration: 0007_phase_29a_plans_and_account_types.sql
-- Description: Phase 29A - Account types, plans system, multi-account users
-- Date: November 14, 2025
-- Idempotent: Safe to run multiple times

-- =====================================================
-- PART 1: CREATE NEW TABLES
-- =====================================================

-- 1.1) Plans table (replaces subscription_plans for new system)
CREATE TABLE IF NOT EXISTS plans (
  slug TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  monthly_report_limit INT NOT NULL,
  allow_overage BOOLEAN NOT NULL DEFAULT false,
  overage_price_cents INT NOT NULL DEFAULT 0
);

COMMENT ON TABLE plans IS 'Usage-based plans with monthly report limits and overage settings';
COMMENT ON COLUMN plans.slug IS 'Plan identifier (free, pro, team, affiliate, sponsored_free)';
COMMENT ON COLUMN plans.monthly_report_limit IS 'Base monthly report generation limit';
COMMENT ON COLUMN plans.allow_overage IS 'Whether plan allows usage beyond limit (with charges)';
COMMENT ON COLUMN plans.overage_price_cents IS 'Cost per report beyond limit (cents)';

-- 1.2) Account Users table (multi-account user membership)
CREATE TABLE IF NOT EXISTS account_users (
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('OWNER', 'MEMBER', 'AFFILIATE', 'ADMIN')),
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (account_id, user_id)
);

COMMENT ON TABLE account_users IS 'Many-to-many: users can belong to multiple accounts with different roles';
COMMENT ON COLUMN account_users.role IS 'OWNER=full control, MEMBER=read/write, AFFILIATE=sponsor relationship, ADMIN=platform admin';

CREATE INDEX IF NOT EXISTS idx_account_users_user ON account_users(user_id);
CREATE INDEX IF NOT EXISTS idx_account_users_account ON account_users(account_id);

-- =====================================================
-- PART 2: ALTER ACCOUNTS TABLE
-- =====================================================

-- 2.1) Add new columns
DO $$
BEGIN
  -- account_type: REGULAR or INDUSTRY_AFFILIATE
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='accounts' AND column_name='account_type'
  ) THEN
    ALTER TABLE accounts ADD COLUMN account_type TEXT NOT NULL DEFAULT 'REGULAR';
  END IF;

  -- monthly_report_limit_override: per-account override of plan limit
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='accounts' AND column_name='monthly_report_limit_override'
  ) THEN
    ALTER TABLE accounts ADD COLUMN monthly_report_limit_override INT;
  END IF;

  -- sponsor_account_id: for sponsored accounts (links to affiliate)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='accounts' AND column_name='sponsor_account_id'
  ) THEN
    ALTER TABLE accounts ADD COLUMN sponsor_account_id UUID;
  END IF;
END $$;

-- 2.2) Add constraints
DO $$
BEGIN
  -- Check constraint for account_type
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint 
    WHERE conname = 'accounts_account_type_check'
  ) THEN
    ALTER TABLE accounts 
    ADD CONSTRAINT accounts_account_type_check 
    CHECK (account_type IN ('REGULAR', 'INDUSTRY_AFFILIATE'));
  END IF;

  -- Foreign key for sponsor_account_id
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint 
    WHERE conname = 'accounts_sponsor_fk'
  ) THEN
    ALTER TABLE accounts
    ADD CONSTRAINT accounts_sponsor_fk
      FOREIGN KEY (sponsor_account_id)
      REFERENCES accounts(id)
      ON DELETE SET NULL;
  END IF;

  -- Foreign key for plan_slug (note: plan_slug already exists from 0003_billing)
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint 
    WHERE conname = 'accounts_plan_fk'
  ) THEN
    ALTER TABLE accounts
    ADD CONSTRAINT accounts_plan_fk
      FOREIGN KEY (plan_slug)
      REFERENCES plans(slug)
      ON DELETE SET NULL;
  END IF;
END $$;

COMMENT ON COLUMN accounts.account_type IS 'REGULAR=standard user, INDUSTRY_AFFILIATE=can sponsor other accounts';
COMMENT ON COLUMN accounts.monthly_report_limit_override IS 'Override plan limit for this specific account (nullable)';
COMMENT ON COLUMN accounts.sponsor_account_id IS 'If set, this account is sponsored by another (affiliate) account';

-- =====================================================
-- PART 3: SEED DEFAULT PLANS
-- =====================================================

INSERT INTO plans (slug, name, monthly_report_limit, allow_overage, overage_price_cents)
VALUES
  ('free',           'Free',                  50,   false, 0),
  ('pro',            'Pro',                  300,   true,  150),  -- $1.50 per overage report
  ('team',           'Team',                1000,   true,  100),  -- $1.00 per overage report
  ('affiliate',      'Industry Affiliate', 5000,   true,  0),     -- No overage charge
  ('sponsored_free', 'Sponsored Free',       75,   false, 0)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  monthly_report_limit = EXCLUDED.monthly_report_limit,
  allow_overage = EXCLUDED.allow_overage,
  overage_price_cents = EXCLUDED.overage_price_cents;

-- =====================================================
-- PART 4: BACKFILL EXISTING DATA
-- =====================================================

-- 4.1) Set account_type to REGULAR for all existing accounts
UPDATE accounts
SET account_type = 'REGULAR'
WHERE account_type IS NULL OR account_type = '';

-- 4.2) Set plan_slug to 'free' for accounts without a plan
UPDATE accounts
SET plan_slug = 'free'
WHERE plan_slug IS NULL OR plan_slug = '';

-- 4.3) Backfill account_users: existing users become OWNERs of their primary account
-- Note: users.account_id represents the user's primary account (from original schema)
INSERT INTO account_users (account_id, user_id, role)
SELECT u.account_id, u.id, 'OWNER'
FROM users u
WHERE u.account_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM account_users au
    WHERE au.account_id = u.account_id
      AND au.user_id = u.id
  );

-- =====================================================
-- PART 5: RLS UPDATES (Placeholder for Phase 29C)
-- =====================================================

-- Note: Existing RLS policies remain unchanged
-- Phase 29C will add:
-- - Affiliate users can see sponsored accounts
-- - ADMIN users can see all accounts
-- - Regular users see accounts via account_users membership
-- For now, keep existing app.current_account_id pattern

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Show plan counts
DO $$
DECLARE
  plan_count INT;
  account_count INT;
  account_user_count INT;
BEGIN
  SELECT COUNT(*) INTO plan_count FROM plans;
  SELECT COUNT(*) INTO account_count FROM accounts WHERE account_type IS NOT NULL;
  SELECT COUNT(*) INTO account_user_count FROM account_users;
  
  RAISE NOTICE '✅ Plans seeded: % rows', plan_count;
  RAISE NOTICE '✅ Accounts migrated: % rows', account_count;
  RAISE NOTICE '✅ Account users backfilled: % rows', account_user_count;
END $$;

-- Confirmation
SELECT '0007_phase_29a_plans_and_account_types.sql applied successfully' AS migration;


