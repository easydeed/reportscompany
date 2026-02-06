-- ============================================================================
-- Phase 4: Performance Indexes
-- Run this against Render PostgreSQL console or via a migration tool.
-- All indexes use IF NOT EXISTS so this is safe to re-run.
-- ============================================================================

-- Report generation queries (affiliate overview, usage tracking, report list)
CREATE INDEX IF NOT EXISTS idx_report_gen_account_status_generated
    ON report_generations(account_id, status, generated_at DESC);

-- Sponsored account lookups
CREATE INDEX IF NOT EXISTS idx_accounts_sponsor
    ON accounts(sponsor_account_id)
    WHERE sponsor_account_id IS NOT NULL;

-- Batch group membership lookups (after N+1 fix)
CREATE INDEX IF NOT EXISTS idx_cgm_member_lookup
    ON contact_group_members(member_type, member_id, account_id);

-- Schedule lookups for usage counting
CREATE INDEX IF NOT EXISTS idx_schedules_account
    ON schedules(account_id);

-- JWT blacklist checks (every authenticated request)
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_hash
    ON jwt_blacklist(token_hash);

-- Schedule runs for usage counting  
CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_date
    ON schedule_runs(schedule_id, created_at);

-- API key lookups (auth middleware)
CREATE INDEX IF NOT EXISTS idx_api_keys_hash
    ON api_keys(key_hash)
    WHERE is_active = TRUE;

-- Phase 6 (L3): Ensure signup_tokens table exists (was previously CREATE TABLE in request handler)
CREATE TABLE IF NOT EXISTS signup_tokens (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    account_id UUID NOT NULL REFERENCES accounts(id),
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
);

-- Verify indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
