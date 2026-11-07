-- LR-019 rollout: how many consumer reports are stuck, and since when?
-- READ ONLY. Runs inside a read-only transaction and ends with ROLLBACK; it writes nothing.
-- It selects no phone numbers, email addresses or names.
--
-- Before LR-019 every consumer failure wrote consumer_reports.error, a column the table
-- does not have. The write raised, the outer handler's write raised too and was
-- swallowed, and the row stayed at 'processing' (or 'pending') for good. Run this
-- before and after the deploy. The fix changes future behaviour only; these rows are
-- not repaired or resent by it, and any historical repair is a separate decision.

BEGIN TRANSACTION READ ONLY;

-- 1. Every status, with age. Anything 'pending'/'processing' older than an hour is stuck:
--    the task retries for at most a few minutes.
SELECT status,
       count(*)                                                  AS reports,
       count(*) FILTER (WHERE created_at < now() - interval '1 hour') AS older_than_1h,
       min(created_at)                                           AS oldest,
       max(created_at)                                           AS newest
FROM consumer_reports
GROUP BY status
ORDER BY status;

-- 2. Stuck rows that never sent anything (no delivery timestamp), by delivery method.
SELECT coalesce(delivery_method, 'sms') AS delivery_method,
       count(*)                          AS stuck_never_sent,
       min(created_at)                   AS oldest,
       max(created_at)                   AS newest
FROM consumer_reports
WHERE status IN ('pending', 'processing')
  AND created_at < now() - interval '1 hour'
  AND consumer_sms_sent_at IS NULL
  AND consumer_email_sent_at IS NULL
GROUP BY 1
ORDER BY 1;

-- 3. Rows already marked failed with no reason recorded (the reason was lost to the bug).
SELECT count(*) AS failed_without_reason
FROM consumer_reports
WHERE status = 'failed' AND (error_message IS NULL OR error_message = '');

-- 4. Reports held for review: a send whose outcome is unknown (a timeout or 5xx after
--    the provider may have accepted it). Never resent automatically; each needs a
--    person to check the provider's own log (Twilio / Resend) and decide.
SELECT coalesce(delivery_method, 'sms') AS delivery_method,
       count(*)                          AS needs_review,
       min(created_at)                   AS oldest,
       max(created_at)                   AS newest
FROM consumer_reports
WHERE status = 'needs_review'
GROUP BY 1
ORDER BY 1;

ROLLBACK;
