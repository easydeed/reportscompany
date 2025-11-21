-- Migration: Seed plans table with base plans
-- Date: 2024-11-21
-- Purpose: Initialize the plans catalog with Solo and Affiliate plans.

INSERT INTO plans (plan_slug, plan_name, stripe_price_id, description)
VALUES
  ('solo', 'Solo Agent', 'price_1SO4sDBKYbtiKxfsUnKeJiox', 'Solo plan for individual agents - $19/month'),
  ('affiliate', 'Affiliate', 'price_1STMtfBKYbtiKxfsqQ4r29Cw', 'Affiliate plan for industry partners - $99/month')
ON CONFLICT (plan_slug) DO NOTHING;

COMMENT ON TABLE plans IS 'Plans are now pre-configured with Stripe Price IDs.';

