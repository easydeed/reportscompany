-- Migration: Seed plans table with base plans
-- Date: 2024-11-21
-- Purpose: Initialize the plans catalog with Solo and Affiliate plans.

-- monthly_report_limit is NOT NULL with no default (0007). Omitting it made this
-- INSERT fail on any database where 0007 created the table, i.e. every fresh
-- build. Values match what 0051 later assigns to these slugs. Inert on any
-- database where the rows already exist (ON CONFLICT DO NOTHING).
--
-- WHY THE UNCONDITIONAL SEED BELOW IS SAFE, which is not stated by the
-- statement itself. `ON CONFLICT DO NOTHING` protects against DUPLICATES; it
-- does not protect against RE-CREATION after a row is deliberately deleted.
-- Those are different guarantees and the idiom reads like the stronger one.
--
-- What makes this file safe is one layer away: both runners
-- (`scripts/migrate.sh`, `scripts/run_migrations.py`) skip any migration whose
-- basename is recorded in `schema_migrations`, so this never re-executes. See
-- db/schema_migrations.sql for that contract and
-- tests/test_migration_bootstrap_guard.py for its gate.
--
-- IF THAT CONTRACT EVER CHANGES — a runner that replays migrations, or a fresh
-- database seeded by replay — this file will resurrect any row removed from
-- the table since. Recorded here because nothing near these statements says
-- what they depend on (D-189).
--
INSERT INTO plans (plan_slug, plan_name, monthly_report_limit, stripe_price_id, description)
VALUES
  ('solo', 'Solo Agent', 25, 'price_1SO4sDBKYbtiKxfsUnKeJiox', 'Solo plan for individual agents - $19/month'),
  ('affiliate', 'Affiliate', 5000, 'price_1STMtfBKYbtiKxfsqQ4r29Cw', 'Affiliate plan for industry partners - $99/month')
ON CONFLICT (plan_slug) DO NOTHING;

COMMENT ON TABLE plans IS 'Plans are now pre-configured with Stripe Price IDs.';

