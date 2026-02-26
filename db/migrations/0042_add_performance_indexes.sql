-- =============================================================================
-- Migration 0042 — Performance Indexes
-- Phase 6.6 of cursor-enhancement-plan
--
-- All indexes use IF NOT EXISTS — safe to re-run, no data modified.
-- Run during low-traffic window; large tables may take a moment to index.
-- =============================================================================

-- Monthly usage count
-- Used in: routes/reports.py, services/usage.py  (report count per account per month)
CREATE INDEX IF NOT EXISTS idx_report_generations_account_generated
    ON report_generations (account_id, generated_at);

-- Sponsored accounts lookup
-- Used in: services/affiliates.py  (WHERE sponsor_account_id = ?)
CREATE INDEX IF NOT EXISTS idx_accounts_sponsor
    ON accounts (sponsor_account_id)
    WHERE sponsor_account_id IS NOT NULL;

-- Group membership batch lookup
-- Used in: services/affiliates.py  (WHERE member_type = ? AND member_id = ANY(?))
CREATE INDEX IF NOT EXISTS idx_cgm_member
    ON contact_group_members (member_type, member_id);

-- JWT blacklist token hash lookup
-- Used in: middleware/authn.py  (WHERE token_hash = ? AND expires_at > NOW())
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_hash
    ON jwt_blacklist (token_hash);

-- Schedule run count per schedule
-- Used in: services/usage.py  (WHERE schedule_id = ? ORDER BY created_at)
CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_created
    ON schedule_runs (schedule_id, created_at);

-- API key authentication
-- Used in: middleware/authn.py  (WHERE key_hash = ? AND is_active = TRUE)
CREATE INDEX IF NOT EXISTS idx_api_keys_hash
    ON api_keys (key_hash);

-- Property reports by account (list view, status polling)
-- Used in: routes/property.py, routes/reports.py
CREATE INDEX IF NOT EXISTS idx_property_reports_account_created
    ON property_reports (account_id, created_at DESC);
