-- Migration 0054: set the Growth (starter) plan's market report limit to 25.
--
-- G1a. The pricing page advertises "25 Market Reports / month" for Growth;
-- production enforces 15. Jerry's decision was to change the DATA, not the
-- copy — so the copy is untouched and this brings the plan row up to it.
--
-- WHY BOTH COLUMNS. They are not derived from one another; they feed two
-- independent code paths in apps/api/src/api/services/usage.py:
--
--   market_reports_limit  -> market_limit    (:131) -> evaluate_product_limit,
--                            get_full_plan_usage (:248-255). This is the LIVE
--                            enforcement path for report creation and the
--                            source of the sidebar usage bar.
--
--   monthly_report_limit  -> effective_limit (:135) -> evaluate_report_limit
--                            (:324). Legacy; one caller remains, routes/
--                            admin.py:621. Also surfaced verbatim in the
--                            account API responses (routes/account.py:180,299).
--
-- Updating only one would leave the two disagreeing, which is worse than
-- either value: the account API would report one number while enforcement
-- applied another. Note also that :135 reads `plan_limit or 100` — a NULL
-- monthly_report_limit silently grants 100 on the legacy path, so this sets it
-- explicitly rather than relying on the column being populated.
--
-- WHY NOT plan_name. Production has this row named "Growth"; the repository's
-- migrations call it "Starter" (0051:59). The production plans table has been
-- edited by hand since 0051 ran — 0051:60-63 sets market_reports_limit = 25 on
-- conflict, and production reads 15, so something changed it afterwards. This
-- migration therefore touches only the two limit columns and leaves the
-- display name alone; renaming it here would overwrite a deliberate production
-- change with a stale repository value. That divergence is worth a separate
-- look, but not a silent fix inside a limits migration.
--
-- Idempotent: a plain UPDATE with an explicit WHERE, safe to re-run.

UPDATE plans
SET market_reports_limit = 25,
    monthly_report_limit = 25
WHERE plan_slug = 'starter';

-- Verification — run this after applying. Both columns must read 25, and the
-- row count must be 1. Zero rows means the paid tier is not called 'starter'
-- in this database, in which case STOP and re-check before editing anything:
-- the pricing page's Growth tier maps to plan_slug 'starter'
-- (apps/web/app/app/settings/billing/page.tsx:63-102).
--
--   SELECT plan_slug, plan_name, monthly_report_limit, market_reports_limit,
--          schedules_limit, property_reports_per_month
--   FROM plans
--   WHERE plan_slug = 'starter';

SELECT '0054_growth_plan_report_limit.sql applied' AS migration;
