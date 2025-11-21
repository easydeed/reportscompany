-- Migration: Seed plans table with base plans
-- Date: 2024-11-21
-- Purpose: Initialize the plans catalog. stripe_price_id will be filled later with real Stripe IDs.

INSERT INTO plans (plan_slug, plan_name, stripe_price_id, description)
VALUES
  ('free', 'Free', NULL, 'Free plan for individual agents'),
  ('pro', 'Pro', NULL, 'Pro plan for growing teams'),
  ('team', 'Team', NULL, 'Team plan for large organizations'),
  ('affiliate', 'Affiliate', NULL, 'Affiliate plan for industry partners')
ON CONFLICT (plan_slug) DO NOTHING;

COMMENT ON TABLE plans IS 'After running this migration, update stripe_price_id for paid plans (pro, team, affiliate) with real Stripe Price IDs from your dashboard.';

