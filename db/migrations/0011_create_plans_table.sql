-- Migration: Create plans table
-- Date: 2024-11-21
-- Purpose: Central catalog of plans with Stripe price IDs

CREATE TABLE IF NOT EXISTS plans (
  plan_slug text PRIMARY KEY,           -- 'free', 'pro', 'team', 'affiliate'
  plan_name text NOT NULL,             -- 'Free', 'Pro', 'Team', 'Affiliate'
  stripe_price_id text,                -- 'price_123' for paid plans, NULL for free
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Reconcile a pre-existing plans table from 0007 (columns: slug, name, and no
-- Stripe fields) to the shape this migration and 0012 expect. Without this, a
-- fresh run of db/migrations dies here: CREATE TABLE IF NOT EXISTS no-ops
-- against the 0007 table and the index below then references a column that
-- does not exist yet. Same guarded pattern 0013 uses, so this is a no-op on
-- any database where 0013 has already run.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plans' AND column_name = 'slug'
    ) THEN
        ALTER TABLE plans RENAME COLUMN slug TO plan_slug;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plans' AND column_name = 'name'
    ) THEN
        ALTER TABLE plans RENAME COLUMN name TO plan_name;
    END IF;
END $$;

ALTER TABLE plans ADD COLUMN IF NOT EXISTS stripe_price_id text;
ALTER TABLE plans ADD COLUMN IF NOT EXISTS description text;

CREATE INDEX IF NOT EXISTS idx_plans_stripe_price_id ON plans(stripe_price_id) WHERE stripe_price_id IS NOT NULL;

COMMENT ON TABLE plans IS 'Central catalog of subscription plans. stripe_price_id links to Stripe Price objects for paid plans.';
COMMENT ON COLUMN plans.plan_slug IS 'Internal identifier: free, pro, team, affiliate';
COMMENT ON COLUMN plans.stripe_price_id IS 'Stripe Price ID (price_...). NULL for free plans.';

