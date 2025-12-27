-- Migration: Email Verification Tokens
-- Stores tokens for email verification on registration

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast token lookups
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token 
ON email_verification_tokens(token);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id 
ON email_verification_tokens(user_id);

-- Update users table to track email verification properly
-- (email_verified column should already exist)

COMMENT ON TABLE email_verification_tokens IS 'Stores email verification tokens. Tokens expire after 24 hours.';

