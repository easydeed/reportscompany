-- Migration: JWT Blacklist
-- Stores invalidated JWT tokens until they expire

CREATE TABLE IF NOT EXISTS jwt_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 hash of the JWT
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,  -- When the JWT would naturally expire
    invalidated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookups during auth
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_token_hash ON jwt_blacklist(token_hash);

-- Index for cleanup of expired entries
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);

-- Cleanup function (removes expired tokens)
CREATE OR REPLACE FUNCTION cleanup_jwt_blacklist()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM jwt_blacklist
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE jwt_blacklist IS 'Stores invalidated JWTs until their natural expiry. Check this table on auth to reject logged-out tokens.';

