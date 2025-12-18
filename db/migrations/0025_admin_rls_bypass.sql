-- Migration 0025: Admin RLS Bypass
-- Allows users with ADMIN role to see all data across accounts
-- Fixes admin dashboard showing zeros due to RLS blocking queries

-- ============================================================================
-- UPDATE RLS POLICIES TO ALLOW ADMIN ACCESS
-- ============================================================================

-- Drop and recreate report_generations policy with admin bypass
DROP POLICY IF EXISTS report_rls ON report_generations;
CREATE POLICY report_rls ON report_generations
  FOR ALL USING (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  )
  WITH CHECK (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  );

-- Drop and recreate schedules policy with admin bypass
DROP POLICY IF EXISTS schedules_rls ON schedules;
CREATE POLICY schedules_rls ON schedules
  FOR ALL USING (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  )
  WITH CHECK (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  );

-- Drop and recreate email_log policy with admin bypass
DROP POLICY IF EXISTS email_log_rls ON email_log;
CREATE POLICY email_log_rls ON email_log
  FOR ALL USING (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  )
  WITH CHECK (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  );

-- Drop and recreate usage_tracking policy with admin bypass
DROP POLICY IF EXISTS usage_rls ON usage_tracking;
CREATE POLICY usage_rls ON usage_tracking
  FOR ALL USING (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  )
  WITH CHECK (
    account_id = current_setting('app.current_account_id', true)::uuid
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  );

-- Drop and recreate schedule_runs policy with admin bypass
DROP POLICY IF EXISTS schedule_runs_rls ON schedule_runs;
CREATE POLICY schedule_runs_rls ON schedule_runs
  FOR ALL USING (
    schedule_id IN (SELECT id FROM schedules WHERE account_id = current_setting('app.current_account_id', true)::uuid)
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  )
  WITH CHECK (
    schedule_id IN (SELECT id FROM schedules WHERE account_id = current_setting('app.current_account_id', true)::uuid)
    OR current_setting('app.current_user_role', true) = 'ADMIN'
  );

-- NOTE: The accounts and users tables don't have RLS, so admin can already query those


