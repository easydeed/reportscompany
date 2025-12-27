-- Migration: Login Attempts (Brute-force protection)
-- Tracks login attempts for rate limiting

CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    ip_address INET,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for checking recent failed attempts
CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time 
ON login_attempts(email, attempted_at DESC) 
WHERE success = FALSE;

-- Auto-cleanup: Remove attempts older than 24 hours
-- (Should be run via cron job or periodic task)
-- DELETE FROM login_attempts WHERE attempted_at < NOW() - INTERVAL '24 hours';

COMMENT ON TABLE login_attempts IS 'Tracks login attempts for brute-force protection. 5 failed attempts in 15 min = lockout.';

