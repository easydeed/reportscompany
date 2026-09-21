-- Can any existing schedule make `compute_next_run` raise?
--
-- READ ONLY. Four SELECTs. No writes, no DDL, not even a temp view.
--
-- WHY THIS QUERY EXISTS
-- ---------------------
-- `schedules_tick.py`'s verification skip (D-019) and its usage-limit skip both
-- call `compute_next_run` before advancing `next_run_at`. If that call raises,
-- the per-schedule handler clears the lock and calls `conn.rollback()` — which
-- discards the advance. The schedule is therefore due again 60 seconds later,
-- and again, and again, logging a traceback each time and never sending.
--
-- The auto-pause that would otherwise catch a schedule failing repeatedly does
-- NOT apply here. It lives in the Celery task's failure handler
-- (`tasks.py:1985`, `consecutive_failures >= 3`), and a `compute_next_run`
-- failure happens in the TICKER, before any task exists. Nothing increments the
-- counter, so nothing ever pauses it.
--
-- THE REASON THIS IS A QUERY AND NOT A CODE READ
-- ----------------------------------------------
-- The obvious answer is "the API validates cadence on create, so no row can be
-- like this". That answer covers rows written AFTER the validator existed. It
-- says nothing about rows written before it. `schedules` was created in
-- migration 0006; `timezone` arrived in 0015, dated November 2025; much of this
-- codebase's validation is weeks old. **A validator on the write path proves
-- what gets written from now on, not what is already there.**
--
-- The same applies to the CHECK constraint, which is why section 0 exists
-- rather than being assumed. `ADD CONSTRAINT ... NOT VALID` installs a
-- constraint that enforces new rows and skips existing ones, and a constraint
-- that was dropped and re-added leaves no trace in the table definition.
--
-- WHAT RAISES — measured, not reasoned about
-- ------------------------------------------
-- Every case below was run through `compute_next_run` directly, and the
-- predicate in section 1 was then checked against the function row by row on a
-- scratch database holding one example of each: 10 rows, 0 disagreements, in
-- both directions. See `apps/worker/tests/test_cadence_hazard_query.py`, which
-- reads the CASE expression **out of this file** so the two cannot drift.
--
--   weekly, weekly_dow IS NULL      ValueError: weekly_dow required
--   monthly, monthly_dom IS NULL    ValueError: monthly_dom required
--   monthly, monthly_dom < 1        ValueError: day is out of range for month
--                                   (`min(dom, 28)` caps the top and lets 0 and
--                                    negatives straight through)
--   send_hour IS NULL               TypeError: NoneType not an integer
--   send_minute IS NULL             TypeError: NoneType not an integer
--   send_hour NOT IN 0..23          ValueError: hour must be in 0..23
--   send_minute NOT IN 0..59        ValueError: minute must be in 0..59
--   cadence not 'weekly'/'monthly'  ValueError: Unknown cadence
--                                   (including 'Weekly' — the comparison is
--                                    case-sensitive, and so is the CHECK)
--
-- These do NOT raise, and are reported separately in section 3 because they are
-- wrong rather than fatal:
--
--   monthly_dom > 28   capped to 28 — documented intent, not a defect
--   weekly_dow 99      (99-1) mod 7 = 0 → sends Monday, silently
--   weekly_dow -1      (-1-1) mod 7 = 5 → sends Saturday, silently
--   timezone NULL or unknown   falls back to UTC with a logged warning, so the
--                              report lands at the wrong local hour
--
-- HOW TO READ THE RESULT
-- ----------------------
--   Sections 1 and 2 empty  → the loop is unreachable. Close it with this
--                             query as the evidence.
--   Any rows                → it is reachable. File it; the fix is both sides —
--                             a guard in the ticker that marks the schedule
--                             failed instead of spinning, and cleanup of the
--                             rows.
--   Section 0 shows the cadence CHECK missing or NOT VALID → the 'unknown
--                             cadence' arm of section 1 is load-bearing rather
--                             than belt-and-braces.

\echo '=== 0. Is the cadence CHECK actually there, and is it VALID? ==='
-- convalidated = false means the constraint was added NOT VALID: it enforces
-- new rows and was never checked against the existing ones. That is precisely
-- the gap this whole query is about.
SELECT
    c.conname,
    c.convalidated,
    pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
JOIN pg_class t ON t.oid = c.conrelid
WHERE t.relname = 'schedules'
  AND c.contype = 'c'
ORDER BY c.conname;

\echo ''
\echo '=== 1. Schedules that would raise — the whole answer is here ==='
-- ONE copy of the rule. The earlier draft of this file repeated the predicate
-- three times — once as a CASE, twice as a WHERE — which is three places to
-- update and two chances to update only some of them. The CASE is now the
-- single source of truth and everything else is `why_it_raises IS NOT NULL`.
--
-- The markers below are not decoration: the test extracts the expression
-- between them and runs it against `compute_next_run` case by case.
WITH hazards AS (
    SELECT
        s.*,
        -- >>> HAZARD-CASE
        CASE
            WHEN s.cadence NOT IN ('weekly', 'monthly')
                THEN 'unknown cadence'
            WHEN s.cadence = 'weekly'  AND s.weekly_dow  IS NULL
                THEN 'weekly with no weekly_dow'
            WHEN s.cadence = 'monthly' AND s.monthly_dom IS NULL
                THEN 'monthly with no monthly_dom'
            WHEN s.cadence = 'monthly' AND s.monthly_dom < 1
                THEN 'monthly_dom below 1 (min(dom,28) does not floor it)'
            WHEN s.send_hour   IS NULL THEN 'send_hour is NULL'
            WHEN s.send_minute IS NULL THEN 'send_minute is NULL'
            WHEN s.send_hour   NOT BETWEEN 0 AND 23 THEN 'send_hour out of range'
            WHEN s.send_minute NOT BETWEEN 0 AND 59 THEN 'send_minute out of range'
        END
        -- <<< HAZARD-CASE
        AS why_it_raises
    FROM schedules s
)
SELECT
    id, account_id, name, active, created_at,
    cadence, weekly_dow, monthly_dom, send_hour, send_minute,
    timezone, next_run_at, consecutive_failures,
    why_it_raises
FROM hazards
WHERE why_it_raises IS NOT NULL
ORDER BY active DESC, created_at;

\echo ''
\echo '=== 2. The same rows, split by active — the ticker only claims active ones ==='
-- An inactive bad row is inert: the claim query filters on `active = true`, so
-- it is never picked up and never spins. It still wants fixing, because
-- switching it on would start the loop, but it is not happening now. Reported
-- as a count so "zero" is unambiguous even when section 1 scrolls.
WITH hazards AS (
    SELECT
        s.active,
        CASE
            WHEN s.cadence NOT IN ('weekly', 'monthly')
                THEN 'unknown cadence'
            WHEN s.cadence = 'weekly'  AND s.weekly_dow  IS NULL
                THEN 'weekly with no weekly_dow'
            WHEN s.cadence = 'monthly' AND s.monthly_dom IS NULL
                THEN 'monthly with no monthly_dom'
            WHEN s.cadence = 'monthly' AND s.monthly_dom < 1
                THEN 'monthly_dom below 1 (min(dom,28) does not floor it)'
            WHEN s.send_hour   IS NULL THEN 'send_hour is NULL'
            WHEN s.send_minute IS NULL THEN 'send_minute is NULL'
            WHEN s.send_hour   NOT BETWEEN 0 AND 23 THEN 'send_hour out of range'
            WHEN s.send_minute NOT BETWEEN 0 AND 59 THEN 'send_minute out of range'
        END AS why_it_raises
    FROM schedules s
)
SELECT
    COUNT(*) FILTER (WHERE why_it_raises IS NOT NULL AND active)       AS active_and_would_raise,
    COUNT(*) FILTER (WHERE why_it_raises IS NOT NULL AND NOT active)   AS paused_and_would_raise,
    COUNT(*)                                                           AS schedules_total
FROM hazards;

\echo ''
\echo '=== 3. Every distinct cadence value present, with the oldest row for each ==='
-- Tests the "the CHECK makes this impossible" assumption against the DATA
-- rather than against the schema. Expect exactly two rows: weekly, monthly.
-- Anything else — 'daily', 'Weekly', '' — is a row that predates or evaded the
-- constraint, and its `oldest` timestamp says which.
SELECT
    cadence,
    COUNT(*)                        AS schedules,
    COUNT(*) FILTER (WHERE active)  AS active,
    MIN(created_at)                 AS oldest,
    MAX(created_at)                 AS newest
FROM schedules
GROUP BY cadence
ORDER BY schedules DESC;

\echo ''
\echo '=== 4. Wrong but not fatal — no loop, just the wrong day or the wrong hour ==='
-- Reported because these are the rows worth cleaning up alongside anything
-- section 1 turns up, and because nobody is going to notice a weekly report
-- arriving on the wrong weekday by reading the logs.
SELECT
    s.id, s.name, s.active, s.cadence,
    s.weekly_dow, s.monthly_dom, s.timezone,
    CASE
        WHEN s.cadence = 'weekly' AND s.weekly_dow NOT BETWEEN 0 AND 6
            THEN 'weekly_dow outside 0..6 — (dow-1) mod 7 silently picks another day'
        WHEN s.cadence = 'monthly' AND s.monthly_dom > 28
            THEN 'monthly_dom above 28 — capped to 28 (documented intent)'
        WHEN s.timezone IS NULL OR s.timezone = ''
            THEN 'no timezone — falls back to UTC, so it sends at the wrong local hour'
    END AS note
FROM schedules s
WHERE (s.cadence = 'weekly'  AND s.weekly_dow  NOT BETWEEN 0 AND 6)
   OR (s.cadence = 'monthly' AND s.monthly_dom > 28)
   OR s.timezone IS NULL
   OR s.timezone = ''
ORDER BY s.active DESC, s.created_at;
