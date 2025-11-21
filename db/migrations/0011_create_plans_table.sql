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

CREATE INDEX IF NOT EXISTS idx_plans_stripe_price_id ON plans(stripe_price_id) WHERE stripe_price_id IS NOT NULL;

COMMENT ON TABLE plans IS 'Central catalog of subscription plans. stripe_price_id links to Stripe Price objects for paid plans.';
COMMENT ON COLUMN plans.plan_slug IS 'Internal identifier: free, pro, team, affiliate';
COMMENT ON COLUMN plans.stripe_price_id IS 'Stripe Price ID (price_...). NULL for free plans.';

