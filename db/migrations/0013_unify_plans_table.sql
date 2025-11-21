-- Migration 0013: Unify plans table with Stripe integration
-- Date: 2024-11-21
-- Purpose: Add Stripe fields to existing plans table and ensure consistency

-- Add missing Stripe and metadata columns to plans table
ALTER TABLE plans
ADD COLUMN IF NOT EXISTS stripe_price_id TEXT,
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Rename 'slug' to 'plan_slug' for consistency (if not already done)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plans' AND column_name = 'slug'
    ) THEN
        ALTER TABLE plans RENAME COLUMN slug TO plan_slug;
    END IF;
END $$;

-- Rename 'name' to 'plan_name' for consistency (if not already done)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plans' AND column_name = 'name'
    ) THEN
        ALTER TABLE plans RENAME COLUMN name TO plan_name;
    END IF;
END $$;

-- Create index for Stripe price lookups
CREATE INDEX IF NOT EXISTS idx_plans_stripe_price_id 
ON plans(stripe_price_id) 
WHERE stripe_price_id IS NOT NULL;

-- Create index for active plans
CREATE INDEX IF NOT EXISTS idx_plans_active 
ON plans(is_active) 
WHERE is_active = TRUE;

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_plans_updated_at ON plans;
CREATE TRIGGER update_plans_updated_at
    BEFORE UPDATE ON plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add helpful comments
COMMENT ON TABLE plans IS 'Central catalog of subscription plans with Stripe integration and usage limits';
COMMENT ON COLUMN plans.plan_slug IS 'Plan identifier: free, pro, team, affiliate, sponsored_free';
COMMENT ON COLUMN plans.plan_name IS 'Human-readable plan name displayed in UI';
COMMENT ON COLUMN plans.stripe_price_id IS 'Stripe Price ID (price_...). NULL for free/internal plans.';
COMMENT ON COLUMN plans.monthly_report_limit IS 'Base monthly report generation limit';
COMMENT ON COLUMN plans.allow_overage IS 'Whether plan allows usage beyond limit (with charges)';
COMMENT ON COLUMN plans.overage_price_cents IS 'Cost per report beyond limit (cents)';
COMMENT ON COLUMN plans.is_active IS 'Whether plan is currently available for new subscriptions';
COMMENT ON COLUMN plans.description IS 'Marketing description of plan features';

