-- Migration: seed the `free` plan row
-- Date: 2026-09-22
-- Defect: D-093
--
-- WHY THIS EXISTS
-- ---------------
-- `resolve_plan_for_account` sends an account with no `plan_slug` to the
-- `free` plan. There has never been a `free` row to send it to on a fresh
-- database: 0012 seeds `solo` and `affiliate` and nothing else, and 0051
-- assigns per-product limits with an UPDATE — which touches rows that exist and
-- creates none. Production has the row (monthly_report_limit = 3); a database
-- built from this directory does not.
--
-- That gap is why three different numbers each claimed to be the free
-- allowance: 100 hard-coded in usage.py, 50 asserted by a test, 3 in the
-- production row. The code now reads the plans table instead of choosing, so
-- the table has to have the row.
--
-- THE VALUES ARE NOT INVENTED. Every one is what 0051 already assigns to
-- `free`, copied from its own CASE expressions:
--
--     market_reports_limit        3
--     schedules_limit             1
--     property_reports_per_month  1
--
-- and `monthly_report_limit = 3`, which matches both `market_reports_limit`
-- above and the value reported from the production row. Nothing here is a new
-- product decision; it writes down one that was already made in two places and
-- stored in a third.
--
-- 0012 IS NOT EDITED. It has been applied, and an applied migration that gains
-- a new statement is a file whose name no longer describes what ran. This is a
-- separate migration so that every database converges on the same state
-- regardless of when it was built.
--
-- Idempotent: ON CONFLICT DO NOTHING, so it is inert on production, where the
-- row already exists and may carry values chosen there. This migration does not
-- UPDATE — it will not overwrite a limit somebody set deliberately.

INSERT INTO plans (
    plan_slug,
    plan_name,
    monthly_report_limit,
    market_reports_limit,
    schedules_limit,
    property_reports_per_month,
    description
)
VALUES (
    'free',
    'Free',
    3,
    3,
    1,
    1,
    'Default plan for accounts with no plan assigned - see D-093'
)
ON CONFLICT (plan_slug) DO NOTHING;
