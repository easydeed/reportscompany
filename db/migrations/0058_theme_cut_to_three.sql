-- Migration 0058: the theme cut — bold, elegant, modern.
--
-- Jerry, 2026-10-05: three themes, and the new default is bold. Classic (id 1)
-- and teal (id 4) are retired; their Jinja templates are deleted in the same
-- commit, so an account left pointing at either would ask the renderer for a
-- file that does not exist. `theme_registry.resolve()` defaults rather than
-- raising, so the failure mode without this migration is silent: 41 accounts
-- rendering in bold while their branding page shows no selection at all.
--
-- WHAT THE NUMBERS ARE
-- 44 accounts. 41 on theme 4 (teal, the column's old DEFAULT). Two on 3
-- (elegant), one on 5 (bold). Nobody ever chose 1 or 2. So this moves 41 rows
-- and leaves three alone.
--
-- IDS ARE NOT RENUMBERED
-- The surviving ids stay 2, 3 and 5. `property_reports.theme` and the
-- `property_report_stats.theme_<name>` columns hold values written before the
-- cut; renumbering would relabel every report already generated. The gaps are
-- deliberate and ids are never reused. See apps/worker/src/worker/themes.json.
--
-- WHY THE CHECK CONSTRAINT IS LEFT ALONE
-- `property_reports.theme` carries `CHECK (theme >= 1 AND theme <= 5)` from
-- 0034. Tightening it to `IN (2, 3, 5)` would fail against the rows this
-- migration deliberately preserves. Selectability is enforced at the API
-- boundary instead (`routes/account.py`, against SELECTABLE_THEME_IDS).
--
-- FORWARD-ONLY, AND HISTORY IS NOT TOUCHED
-- Only `accounts.default_theme_id` changes — what the NEXT report will use.
-- Reports already generated keep the theme they were generated with.

-- `run_migrations.py` executes each file whole in one transaction
-- (autocommit=False), so an explicit BEGIN here would warn about a
-- transaction already in progress and the COMMIT would end the runner's.

-- 1. The column default. Was 4 (teal) from 0043.
ALTER TABLE accounts ALTER COLUMN default_theme_id SET DEFAULT 5;

-- 2. Move every account off a retired theme. NULL is left NULL: the
--    application resolves it through the registry, and writing 5 into rows
--    that never expressed a preference would claim a choice nobody made.
UPDATE accounts
   SET default_theme_id = 5
 WHERE default_theme_id IN (1, 4);

-- 3. Say what happened. A migration that moves 41 rows and prints nothing is
--    indistinguishable from one that moved none.
DO $$
DECLARE
    moved INTEGER;
    remaining INTEGER;
BEGIN
    SELECT COUNT(*) INTO moved
      FROM accounts WHERE default_theme_id = 5;
    SELECT COUNT(*) INTO remaining
      FROM accounts WHERE default_theme_id IN (1, 4);
    RAISE NOTICE 'accounts now on theme 5 (bold): %', moved;
    IF remaining > 0 THEN
        RAISE EXCEPTION 'theme cut incomplete: % accounts still on a retired theme', remaining;
    END IF;
END
$$;
