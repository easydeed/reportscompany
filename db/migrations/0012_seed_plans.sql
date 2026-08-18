-- Migration: Seed plans table with base plans
-- Date: 2024-11-21
-- Purpose: Initialize the plans catalog with Solo and Affiliate plans.

-- monthly_report_limit is NOT NULL with no default (0007). Omitting it made this
-- INSERT fail on any database where 0007 created the table, i.e. every fresh
-- build. Values match what 0051 later assigns to these slugs. Inert on any
-- database where the rows already exist (ON CONFLICT DO NOTHING).
INSERT INTO plans (plan_slug, plan_name, monthly_report_limit, stripe_price_id, description)
VALUES
  ('solo', 'Solo Agent', 25, 'price_1SO4sDBKYbtiKxfsUnKeJiox', 'Solo plan for individual agents - $19/month'),
  ('affiliate', 'Affiliate', 5000, 'price_1STMtfBKYbtiKxfsqQ4r29Cw', 'Affiliate plan for industry partners - $99/month')
ON CONFLICT (plan_slug) DO NOTHING;

COMMENT ON TABLE plans IS 'Plans are now pre-configured with Stripe Price IDs.';

