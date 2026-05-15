-- Migration 0052: simplify contact types
-- Collapse contacts.type to a single value ('client'). Migrate existing
-- type='group' contacts into real contact_groups rows. Convert type='agent'
-- and type='list' contacts to client.
--
-- See: CONTACTS-SIMPLIFY-TO-CLIENT-AND-GROUP ticket.
-- Pre-migration audit: 1 row type='group', 1 row type='agent', 0 rows type='list'.
-- Zero schedules reference any of these rows. Safe migration.

BEGIN;

-- Safety check: the pre-migration audit found zero name collisions. Abort
-- instead of deleting a type='group' contact if a real group with the same
-- account/name already exists in this environment.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM contacts c
    JOIN contact_groups cg
      ON cg.account_id = c.account_id
     AND cg.name = c.name
    WHERE c.type = 'group'
  ) THEN
    RAISE EXCEPTION 'Cannot migrate type=group contacts: matching contact_groups rows already exist';
  END IF;
END $$;

-- Step 1: Migrate type='group' contacts into contact_groups.
-- Their `notes` field becomes the group's description. Guard against duplicate
-- group names because contact_groups currently has no unique (account_id, name)
-- constraint and this migration should not create duplicates if a same-name
-- group already exists.
INSERT INTO contact_groups (account_id, name, description, created_at, updated_at)
SELECT c.account_id, c.name, c.notes, c.created_at, c.updated_at
FROM contacts c
WHERE c.type = 'group'
  AND NOT EXISTS (
    SELECT 1
    FROM contact_groups cg
    WHERE cg.account_id = c.account_id
      AND cg.name = c.name
  );

-- Step 2: Remove memberships for the soon-to-be-deleted type='group' contacts,
-- then delete the now-migrated contacts rows. contact_group_members.member_id is
-- polymorphic and does not have a foreign key to contacts, so this avoids
-- orphaned member rows.
DELETE FROM contact_group_members cgm
USING contacts c
WHERE cgm.member_type = 'contact'
  AND cgm.member_id = c.id
  AND c.type = 'group';

DELETE FROM contacts WHERE type = 'group';

-- Step 3: Convert type='agent' and type='list' to 'client' (preserve all other fields).
UPDATE contacts SET type = 'client' WHERE type IN ('agent', 'list');

-- Step 4: Tighten the CHECK constraint to only allow 'client'.
ALTER TABLE contacts DROP CONSTRAINT IF EXISTS contacts_type_check;
ALTER TABLE contacts ADD CONSTRAINT contacts_type_check CHECK (type = 'client');

COMMIT;

-- Rollback note:
-- This migration deletes type='group' contact rows after copying them into
-- contact_groups. A down migration cannot safely recreate the original contact
-- UUIDs without a backup. If rollback is needed, restore code first and manually
-- recreate affected contact rows from database backup/audit logs.
