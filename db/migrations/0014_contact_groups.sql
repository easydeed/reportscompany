-- Migration 0014: Contact Groups for People & Schedules
-- Date: 2025-11-21
-- Purpose: Add contact_groups and contact_group_members to support groups of contacts
--          and sponsored agents for use in People and Schedules.

-- ============================================================================
-- contact_groups: Named groups owned by an account
-- ============================================================================
CREATE TABLE IF NOT EXISTS contact_groups (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_contact_groups_account_id
  ON contact_groups(account_id);

-- RLS: Only see groups for current account
ALTER TABLE contact_groups ENABLE ROW LEVEL SECURITY;

CREATE POLICY contact_groups_account_isolation ON contact_groups
  FOR ALL
  USING (account_id::text = current_setting('app.current_account_id', TRUE));

COMMENT ON TABLE contact_groups IS 'Named groups of contacts and sponsored agents for an account';
COMMENT ON COLUMN contact_groups.name IS 'Group name (e.g., Top Clients, Sponsored Agents – West)';

-- Reuse generic updated_at trigger function if present
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
  ) THEN
    DROP TRIGGER IF EXISTS update_contact_groups_updated_at ON contact_groups;

    CREATE TRIGGER update_contact_groups_updated_at
      BEFORE UPDATE ON contact_groups
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at_column();
  END IF;
END $$;

-- ============================================================================
-- contact_group_members: Members of a group (contacts or sponsored agents)
-- ============================================================================
CREATE TABLE IF NOT EXISTS contact_group_members (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id uuid NOT NULL REFERENCES contact_groups(id) ON DELETE CASCADE,
  account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  member_type text NOT NULL CHECK (member_type IN ('contact', 'sponsored_agent')),
  member_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- A member can appear at most once per group
ALTER TABLE contact_group_members
  ADD CONSTRAINT contact_group_members_unique_member
  UNIQUE (group_id, member_type, member_id);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_contact_group_members_group_id
  ON contact_group_members(group_id);

CREATE INDEX IF NOT EXISTS idx_contact_group_members_account_id
  ON contact_group_members(account_id);

-- RLS: Only see members for current account
ALTER TABLE contact_group_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY contact_group_members_account_isolation ON contact_group_members
  FOR ALL
  USING (account_id::text = current_setting('app.current_account_id', TRUE));

COMMENT ON TABLE contact_group_members IS 'Members of contact groups (contacts or sponsored agents)';
COMMENT ON COLUMN contact_group_members.member_type IS 'contact | sponsored_agent';
COMMENT ON COLUMN contact_group_members.member_id IS 'ID of contact (contacts.id) or sponsored account (accounts.id)';


