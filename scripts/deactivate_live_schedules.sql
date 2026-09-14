-- Stop the live schedules from sending. DO NOT DELETE THEM.
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

BEGIN;

-- Look before you write. Expect 3 rows (43 schedules exist, 3 are active).
SELECT id, name, report_type, active, next_run_at, last_run_at
FROM schedules
WHERE active = TRUE
ORDER BY next_run_at;

UPDATE schedules
SET active = FALSE
WHERE active = TRUE;

-- Confirm: this must return 0.
SELECT COUNT(*) AS still_active FROM schedules WHERE active = TRUE;

-- Confirm the history is untouched. This must return the same count as before.
SELECT COUNT(*) AS schedule_runs_retained FROM schedule_runs;

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
