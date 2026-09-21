-- Stop the live schedules from sending. DO NOT DELETE THEM.
--
-- REQUIRES: -v expected_active=<n>. See HOW TO RUN IT below.
--
-- WHY DELETE IS THE WRONG VERB HERE
-- ---------------------------------
-- `schedule_runs.schedule_id` is declared
--
--     REFERENCES schedules(id) ON DELETE CASCADE        (0006_schedules.sql:41)
--
-- so `DELETE FROM schedules` does not just remove the schedules. It silently
-- removes every run those schedules ever produced — ten months of history,
-- 1,067 completed runs and the 58 stranded ones.
--
-- That history is not archive material. It is the working evidence base for
-- open defects:
--
--   D-062  the 58 stranded runs, and the four-way join against
--          report_generations that split them into 35 status-write bugs and
--          18 genuine losses. Delete the runs and the split cannot be redone.
--   D-064  the 20 runs with a completed generation and no email_log row.
--   D-070  the enqueue-to-delivery lag query, which needs schedule_runs
--          .created_at beside report_generations.generated_at. There is
--          nowhere else that pairing exists.
--   sweep  STALE_QUEUED_MINUTES = 30 is derived from observed burst drain
--          (26 enqueued in one pass on 2026-04-12). Re-deriving it later
--          needs the same rows.
--
-- A deleted row cannot be un-deleted, and none of those questions are closed.
-- `active = false` stops the ticker from enqueueing anything — which is the
-- whole of what was asked for — and costs nothing.
--
-- HOW THE TICKER READS THIS
-- -------------------------
-- `find_due_schedules` selects on `active = TRUE`. An inactive schedule is
-- never enqueued, regardless of `next_run_at`, so nothing further is needed:
-- leaving `next_run_at` in the past is harmless and preserves what the
-- schedule was going to do.
--
-- Reversible in one statement — see the bottom of this file.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- HOW TO RUN IT
--
--     psql "$DATABASE_URL" -v expected_active=3 -f scripts/deactivate_live_schedules.sql
--
-- `expected_active` IS REQUIRED AND THAT IS THE POINT. Run without it and psql
-- fails on `:expected_active` before reaching the UPDATE; run with the wrong
-- number and the scope guard below aborts the transaction and says so.
--
-- WHY IT IS REQUIRED. This file used to say "Look before you write. Expect 3
-- rows" above a SELECT, with the UPDATE in the same transaction directly
-- underneath. Run as a file — which is the only way anyone runs it — there is
-- no looking: psql executes the SELECT and the UPDATE in one pass and the
-- operator reads the list of what they were going to change AFTER it has
-- already been changed. An instruction that cannot be followed is not a
-- safeguard. Passing the expected count is the same decision, made at a moment
-- when it can still stop something.
--
-- It also closes the stale-snapshot hole. "3 are active" was true on
-- 2026-09-09. A schedule that went live after that was silently swept up —
-- confirmed on a scratch database by adding a fourth and re-running: it was
-- deactivated with no mention anywhere in the output.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- TESTED, 2026-09-21, scratch Postgres 16.13, through psql, against the real
-- table shapes: 43 schedules (3 active), 1,067 schedule_runs rows, and a
-- paused schedule held as a control. The data handling was already correct —
-- exactly the 3 rows changed, `next_run_at` preserved on each, the control
-- byte-identical (hashed before and after), all 1,067 runs retained. What was
-- wrong was everything above: an unfollowable instruction and two checks that
-- printed numbers with nothing to compare them against.

\set ON_ERROR_STOP on

BEGIN;

-- 1. Look. This is still the first thing that happens, and it is still worth
--    reading — but it is no longer what stands between you and the write.
SELECT id, name, report_type, active, next_run_at, last_run_at
FROM schedules
WHERE active = TRUE
ORDER BY next_run_at;

-- 2. SCOPE GUARD. Aborts unless the world is the size you said it was.
--
--    The CAST is the abort: a non-numeric string cast to INT raises, and the
--    string is the error message. Postgres has no ASSERT outside plpgsql, and
--    plpgsql is not an option here — psql does NOT interpolate `:variables`
--    inside dollar-quoted blocks, so a `DO $$ ... :expected_active ... $$`
--    guard is a syntax error. Measured, not assumed.
SELECT CASE WHEN COUNT(*) = :expected_active
            THEN 'scope confirmed: ' || COUNT(*) || ' active schedule(s)'
            ELSE CAST('STOP - you said to expect ' || :expected_active
                      || ' active schedules and there are ' || COUNT(*)
                      || '. Re-read the list above before running this.' AS INT)::text
       END AS scope_check
FROM schedules WHERE active = TRUE;

-- 3. Baseline for the history check. The old version asked for "the same count
--    as before" and never captured a before, so the number it printed was
--    unverifiable against anything. TEMP, so it exists only for this session.
CREATE TEMP TABLE _deactivate_baseline AS
SELECT COUNT(*) AS runs_before FROM schedule_runs;

-- 4. The write.
UPDATE schedules
SET active = FALSE
WHERE active = TRUE;

-- 5. Confirm nothing is still armed. An assertion now, not a printed number:
--    a check whose failure looks like a successful run is not a check.
SELECT CASE WHEN COUNT(*) = 0
            THEN 'no schedule is active'
            ELSE CAST('STOP - ' || COUNT(*) || ' schedule(s) still active after the update' AS INT)::text
       END AS still_active_check
FROM schedules WHERE active = TRUE;

-- 6. Confirm the history is untouched — against the baseline, not against
--    nothing. This is the promise the whole file is built on: `active = FALSE`
--    rather than DELETE, so that ten months of schedule_runs survive.
SELECT CASE WHEN (SELECT COUNT(*) FROM schedule_runs) = b.runs_before
            THEN 'history intact: ' || b.runs_before || ' schedule_runs rows'
            ELSE CAST('STOP - schedule_runs went from ' || b.runs_before
                      || ' to ' || (SELECT COUNT(*) FROM schedule_runs) AS INT)::text
       END AS history_check
FROM _deactivate_baseline b;

COMMIT;

-- TO REVERSE, per schedule rather than wholesale — reactivating all three at
-- once would enqueue all three on the next tick, since each next_run_at is by
-- then in the past:
--
--   UPDATE schedules
--   SET active = TRUE,
--       next_run_at = <the next intended send, computed forward from now>
--   WHERE id = '<schedule id>';
--
-- Setting next_run_at forward matters. `find_due_schedules` treats
-- `next_run_at <= NOW()` as due, so a reactivated schedule with a stale
-- timestamp fires immediately rather than at its scheduled hour.
