-- Migration: Add is_active flag to accounts table
-- Date: 2024-11-20
-- Purpose: Allow affiliates to suspend/reactivate sponsored agent accounts

ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT TRUE;

-- Index for filtering active/inactive accounts
CREATE INDEX IF NOT EXISTS idx_accounts_is_active ON accounts(is_active) WHERE is_active = FALSE;

COMMENT ON COLUMN accounts.is_active IS 'Whether the account is active. Affiliates can suspend sponsored accounts.';

