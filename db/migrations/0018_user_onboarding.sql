-- Migration: 0018_user_onboarding.sql
-- Description: Add onboarding tracking for users
-- Idempotent: Can be run multiple times safely

-- Add onboarding fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_step VARCHAR(50) DEFAULT 'welcome';
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_data JSONB DEFAULT '{}';

-- Create onboarding_progress table for detailed tracking
CREATE TABLE IF NOT EXISTS onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    step_key VARCHAR(50) NOT NULL,
    completed_at TIMESTAMP,
    skipped_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, step_key)
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_user ON onboarding_progress(user_id);

-- Define standard onboarding steps (stored as reference)
COMMENT ON TABLE onboarding_progress IS 'Tracks individual onboarding step completion. Steps: profile_complete, branding_setup, first_report, first_schedule, invite_sent';

-- Confirmation
SELECT '0018_user_onboarding.sql applied' AS migration;
