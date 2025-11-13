-- Phase 27A Certification Test Schedule
-- This will send a test email to gerardoh@gmail.com

-- First, let's check if a schedule already exists for this test
-- SELECT * FROM schedules WHERE name = 'Phase 27A Email Test - Gerard';

-- Create test schedule that will trigger on next ticker run
INSERT INTO schedules (
  account_id,
  name,
  report_type,
  city,
  lookback_days,
  cadence,
  weekly_dow,
  send_hour,
  send_minute,
  recipients,
  active,
  created_at,
  updated_at,
  next_run_at  -- Set to NULL or past time to trigger immediately
) VALUES (
  '912014c3-6deb-4b40-a28d-489ef3923a3a',  -- Demo account ID
  'Phase 27A Email Test - Gerard',
  'market_snapshot',
  'Houston',
  30,
  'weekly',
  1,  -- Monday
  14, -- 2 PM
  0,
  ARRAY['gerardoh@gmail.com'],
  true,
  NOW(),
  NOW(),
  NOW() - INTERVAL '1 minute'  -- Set to 1 minute ago to trigger immediately
)
RETURNING id, name, next_run_at;

-- After inserting, verify the schedule
-- SELECT id, name, report_type, city, cadence, recipients, active, next_run_at
-- FROM schedules 
-- WHERE name = 'Phase 27A Email Test - Gerard';

-- Monitor execution:
-- 
-- 1. Check schedule_runs table:
-- SELECT id, schedule_id, status, started_at, finished_at, report_run_id, created_at
-- FROM schedule_runs
-- WHERE schedule_id = (SELECT id FROM schedules WHERE name = 'Phase 27A Email Test - Gerard')
-- ORDER BY created_at DESC;
--
-- 2. Check email_log table:
-- SELECT id, provider, to_emails, subject, response_code, error, created_at
-- FROM email_log
-- ORDER BY created_at DESC
-- LIMIT 5;
--
-- 3. Check report_runs table for PDF:
-- SELECT id, report_type, status, pdf_url, created_at
-- FROM report_runs
-- ORDER BY created_at DESC
-- LIMIT 5;

-- Expected Timeline:
-- - Within 60 seconds: Ticker picks up schedule (next_run_at in past)
-- - Within 2-3 minutes: Report generates, PDF uploads to R2
-- - Within 4-5 minutes: Email sent via SendGrid
-- - Within 5-10 minutes: Email arrives at gerardoh@gmail.com

-- Cleanup after test (optional):
-- DELETE FROM schedules WHERE name = 'Phase 27A Email Test - Gerard';

