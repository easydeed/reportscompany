-- Migration: Create contacts table for People view
-- Date: 2024-11-20
-- Purpose: Store client contacts, recipients, and lists for all account types

CREATE TABLE IF NOT EXISTS contacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  name text NOT NULL,
  email text NOT NULL,
  type text NOT NULL CHECK (type IN ('client', 'list', 'agent')),
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Index for fast lookups by account
CREATE INDEX IF NOT EXISTS idx_contacts_account_id ON contacts(account_id);

-- Index for email lookups (deduplication, search)
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);

-- RLS: Users can only see contacts for their current account
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY contacts_account_isolation ON contacts
  FOR ALL
  USING (account_id::text = current_setting('app.current_account_id', TRUE));

COMMENT ON TABLE contacts IS 'Client contacts, recipients, and lists for scheduling and People view';
COMMENT ON COLUMN contacts.type IS 'Type of contact: client (individual), list (group), agent (external)';

