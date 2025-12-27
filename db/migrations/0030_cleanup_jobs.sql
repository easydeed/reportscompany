-- Migration: Cleanup functions for expired data
-- Run these periodically via cron or scheduled task

-- Function to clean up expired password reset tokens
CREATE OR REPLACE FUNCTION cleanup_expired_password_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM password_reset_tokens
    WHERE expires_at < NOW() - INTERVAL '24 hours'
       OR used_at IS NOT NULL AND used_at < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old login attempts
CREATE OR REPLACE FUNCTION cleanup_old_login_attempts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM login_attempts
    WHERE attempted_at < NOW() - INTERVAL '24 hours';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Indexes for cleanup performance
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_cleanup 
ON password_reset_tokens(expires_at) 
WHERE used_at IS NULL;

COMMENT ON FUNCTION cleanup_expired_password_tokens() IS 'Call daily to remove expired/used password reset tokens';
COMMENT ON FUNCTION cleanup_old_login_attempts() IS 'Call daily to remove old login attempt records';

