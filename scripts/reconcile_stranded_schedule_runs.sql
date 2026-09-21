-- Reconcile the 57 stranded schedule_runs rows.
--
-- NOT APPLIED TO PRODUCTION. This is a proposal for review. It is not a
-- numbered migration and must not become one — it is a one-off correction of
-- historical rows, not a schema change.
--
-- IT HAS, HOWEVER, BEEN RUN. 2026-09-21, scratch Postgres 16.13, against the
-- real table shapes (0006 + the columns the statements touch), seeded to the
-- distribution below plus a live mid-flight run as a control. It parses and all
-- seven statements execute. Doing that found three defects in it — two that
-- would have corrupted data and one that made its own success criterion
-- unreachable — none of which reading it had found, and none of which the
-- text-assertion test in apps/worker/tests/test_schedule_run_lifecycle.py
-- could see. See the comments at sections 3 and VERIFY.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- WHAT STRANDED THESE ROWS
--
-- Every schedule_runs status write lived on a success path inside the worker.
-- Two separate defects left rows at 'queued':
--
--   D-061  the completed/failed_email writer keyed on "the newest queued row
--          for this schedule" rather than on report_run_id, so once a row was
--          stranded no later run ever reclaimed it; and a crash on the email
--          path was caught by a handler that wrote only email_log.
--   D-062  runs consumed and killed mid-flight, or never consumed at all,
--          leave no code running to record anything.
--
-- Both are fixed going forward on fix/schedule-run-lifecycle. This file is
-- only about the rows already in the table.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- RUN THIS FIRST. It must return the same distribution the investigation did.
-- If it does not, STOP: the data has changed and the statements below are
-- reasoning about a different population.

SELECT g.status AS gen_status,
       (g.pdf_url IS NULL) AS no_pdf,
       COUNT(*)            AS rows,
       MIN(r.created_at)   AS oldest,
       MAX(r.created_at)   AS newest
FROM schedule_runs r
LEFT JOIN report_generations g ON g.id = r.report_run_id
WHERE r.status = 'queued'
GROUP BY 1, 2
ORDER BY 3 DESC;

-- Expected, as of the 2026-09-09 investigation:
--   completed  + pdf     27
--   processing + no pdf  18
--   failed     + no pdf   8
--   queued     + no pdf   3
--   (no generation row)   1     <- gen_status NULL

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. The 27 that completed with a PDF.
--
-- These are the only rows that can be reconciled *deterministically*: the
-- generation finished and the file exists, so the run did its work and only
-- the status write was lost. Recorded as 'completed'.
--
-- finished_at is taken from report_generations.generated_at rather than NOW(),
-- so the audit trail keeps the real time. Stamping NOW() would make ten months
-- of history look like it all finished the day the backfill ran.

UPDATE schedule_runs r
SET status      = 'completed',
    finished_at = g.generated_at,
    error       = 'backfilled: generation completed with a PDF; status write lost (D-061)'
FROM report_generations g
WHERE g.id = r.report_run_id
  AND r.status = 'queued'
  AND g.status = 'completed'
  AND g.pdf_url IS NOT NULL;

-- NOTE — 'completed' here means the REPORT completed, not that the email was
-- delivered. Those are different claims and this backfill cannot settle the
-- second one. Check delivery separately before treating these as sent:
--
--   SELECT r.id, r.created_at, e.status, e.response_code, e.error
--   FROM schedule_runs r
--   LEFT JOIN email_log e ON e.report_id = r.report_run_id
--   WHERE r.report_run_id IN (...the 27...);
--
-- Any of the 27 with no email_log row is a report that was built and never
-- sent — a real delivery loss hiding inside the benign-looking bucket.

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. The 8 whose generation failed.
--
-- The outer handler recorded 'failed' on report_generations correctly; only
-- schedule_runs did not follow. Copy the real error across rather than
-- inventing one.

UPDATE schedule_runs r
SET status      = 'failed',
    finished_at = g.generated_at,
    error       = COALESCE(g.error, 'backfilled: report generation failed (D-061)')
FROM report_generations g
WHERE g.id = r.report_run_id
  AND r.status = 'queued'
  AND g.status = 'failed';

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. The 18 stuck at 'processing', and the 3 never consumed.
--
-- These are the real delivery losses: 18 reports that a schedule said to send
-- and that were never made. They are marked failed with a reason that says
-- which, so the count stays visible rather than being tidied away.
--
-- report_generations is corrected too — 18 rows have sat at 'processing' since,
-- and check_usage_limit counts 'processing' toward the monthly total. These
-- particular rows are excluded from that count because they have schedule_runs
-- rows, but leaving a decade of phantom 'processing' rows in the table is how
-- the next person's usage query goes wrong.

-- BOTH STATEMENTS ARE GUARDED ON r.created_at, AND THAT IS THE FIX FOR TWO
-- OPPOSITE ERRORS FOUND BY RUNNING THIS FILE (2026-09-21, scratch Postgres
-- 16.13, seeded to the distribution above).
--
--   The runs UPDATE had NO age guard. A run created seconds earlier, whose
--   generation was legitimately 'processing' RIGHT NOW, was marked
--   'failed — consumed then killed mid-flight; report never produced'. This
--   file is a backfill: it must not be able to fabricate a failure for work
--   that is still running. 22 rows updated where 21 were stranded.
--
--   The generations UPDATE was guarded on `g.generated_at`, which is NULL for
--   a generation that was NEVER CONSUMED — the API's INSERT writes status and
--   no timestamp (reports.py:247). `NULL < ...` is NULL, not true, so the
--   three never-picked-up rows were silently skipped and left at 'queued'
--   forever. 18 rows updated where 21 were stranded.
--
-- Together those two produced the exact inconsistency this file exists to
-- remove: four rows whose schedule_runs said 'failed' while their
-- report_generations still said 'processing' or 'queued'.
--
-- `schedule_runs.created_at` has DEFAULT now() (0006_schedules.sql:47) and is
-- the enqueue time, so it is always present and always the right clock for
-- "has this been stranded long enough to be sure". Seven days is inherited
-- from the original guard; it is far outside STALE_QUEUED_MINUTES (30), so a
-- burst draining normally is never caught.

UPDATE schedule_runs r
SET status      = 'failed',
    finished_at = NOW(),
    error       = CASE g.status
                    WHEN 'processing' THEN 'backfilled: consumed then killed mid-flight; report never produced (D-062)'
                    ELSE 'backfilled: never picked up by a worker (D-062)'
                  END
FROM report_generations g
WHERE g.id = r.report_run_id
  AND r.status = 'queued'
  AND g.status IN ('processing', 'queued')
  AND r.created_at < NOW() - interval '7 days';

UPDATE report_generations g
SET status = 'failed',
    error  = COALESCE(g.error, 'backfilled: task killed mid-flight, no handler ran (D-062)')
WHERE g.status IN ('processing', 'queued')
  AND EXISTS (
        SELECT 1 FROM schedule_runs r
        WHERE r.report_run_id = g.id
          AND r.created_at < NOW() - interval '7 days'
      );

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. The 1 row with no matching generation.
--
-- DELIBERATELY NOT TOUCHED. schedule_runs.report_run_id has no FOREIGN KEY
-- (0006_schedules.sql:42 — a bare UUID with a comment pointing at
-- report_generations.id), so a dangling value violates nothing and the most
-- likely cause is that the generation row was deleted while the run row
-- survived: schedule_runs cascades on schedules, not on report_generations.
--
-- Inspect it before deciding. One row does not justify a guess:

SELECT r.*
FROM schedule_runs r
LEFT JOIN report_generations g ON g.id = r.report_run_id
WHERE r.status = 'queued' AND g.id IS NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERIFY.
--
-- This used to say "should return zero rows", and it COULD NOT — section 4
-- deliberately leaves the dangling row alone, and that row is old and still
-- 'queued', so it is counted. A correct run reported failure. Found by running
-- the file rather than reading it.
--
-- Two numbers instead, so the expectation is stated rather than implied:
-- everything reconcilable must be gone, and what remains must be exactly the
-- rows section 4 left on purpose.

SELECT
    COUNT(*) FILTER (
        WHERE EXISTS (SELECT 1 FROM report_generations g WHERE g.id = r.report_run_id)
    )                                          AS still_stranded_must_be_zero,
    COUNT(*) FILTER (
        WHERE NOT EXISTS (SELECT 1 FROM report_generations g WHERE g.id = r.report_run_id)
    )                                          AS dangling_left_on_purpose
FROM schedule_runs r
WHERE r.status = 'queued'
  AND r.created_at < NOW() - interval '7 days';
