-- Migration 0051: Add per-product limit columns to plans and accounts tables.
-- Idempotent: uses ADD COLUMN IF NOT EXISTS and ON CONFLICT.

-- 1. Add per-product limit columns to plans
ALTER TABLE plans ADD COLUMN IF NOT EXISTS market_reports_limit INTEGER;
ALTER TABLE plans ADD COLUMN IF NOT EXISTS schedules_limit INTEGER;
-- property_reports_per_month already exists from migration 0034

-- 2. Populate from existing data (only rows where new column is still NULL)
UPDATE plans SET
    market_reports_limit = CASE plan_slug
        WHEN 'free'            THEN 3
        WHEN 'sponsored_free'  THEN 3
        WHEN 'starter'         THEN 25
        WHEN 'pro'             THEN 99999
        WHEN 'team'            THEN 99999
        WHEN 'affiliate'       THEN 5000
        WHEN 'solo'            THEN 25
        ELSE 3
    END,
    schedules_limit = CASE plan_slug
        WHEN 'free'            THEN 1
        WHEN 'sponsored_free'  THEN 1
        WHEN 'starter'         THEN 3
        WHEN 'pro'             THEN 99999
        WHEN 'team'            THEN 99999
        WHEN 'affiliate'       THEN 99999
        WHEN 'solo'            THEN 3
        ELSE 1
    END,
    property_reports_per_month = CASE plan_slug
        WHEN 'free'            THEN 1
        WHEN 'sponsored_free'  THEN 1
        WHEN 'starter'         THEN 5
        WHEN 'pro'             THEN 25
        WHEN 'team'            THEN 25
        WHEN 'affiliate'       THEN 100
        WHEN 'solo'            THEN 5
        ELSE 1
    END
WHERE market_reports_limit IS NULL;

-- 3. Add per-product override columns to accounts
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS market_reports_limit_override INTEGER;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS schedules_limit_override INTEGER;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS property_reports_limit_override INTEGER;

-- 4. Migrate existing single override to market reports override
UPDATE accounts
SET market_reports_limit_override = monthly_report_limit_override
WHERE monthly_report_limit_override IS NOT NULL
  AND market_reports_limit_override IS NULL;

-- 5. Add starter plan if it doesn't exist
INSERT INTO plans (plan_slug, plan_name, monthly_report_limit, market_reports_limit, schedules_limit, property_reports_per_month)
VALUES ('starter', 'Starter', 25, 25, 3, 5)
ON CONFLICT (plan_slug) DO UPDATE SET
    market_reports_limit       = 25,
    schedules_limit            = 3,
    property_reports_per_month = 5;

-- 6. Add trial plan (same as free, different display)
INSERT INTO plans (plan_slug, plan_name, monthly_report_limit, market_reports_limit, schedules_limit, property_reports_per_month)
VALUES ('trial', 'Trial', 3, 3, 1, 1)
ON CONFLICT (plan_slug) DO NOTHING;

SELECT '0051_per_product_limits.sql applied' AS migration;
