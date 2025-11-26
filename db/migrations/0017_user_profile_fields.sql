-- Migration: 0017_user_profile_fields.sql
-- Description: Add profile fields to users table for account settings
-- Idempotent: Can be run multiple times safely

-- Add profile fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS company_name VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);

-- Add password_changed_at for session invalidation after password change
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP;

-- Create index for faster user lookups by email (if not exists)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Confirmation
SELECT '0017_user_profile_fields.sql applied' AS migration;
