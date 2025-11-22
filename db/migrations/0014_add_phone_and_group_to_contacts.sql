-- Migration: Add phone column and 'group' type to contacts
-- This supports the Phase 1 enhancement: type-first conditional fields

-- Add phone column (optional for all types)
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS phone text;

-- Update the type CHECK constraint to include 'group'
ALTER TABLE contacts 
DROP CONSTRAINT IF EXISTS contacts_type_check;

ALTER TABLE contacts 
ADD CONSTRAINT contacts_type_check 
CHECK (type IN ('client', 'list', 'agent', 'group'));

-- Make email nullable (groups don't require email)
ALTER TABLE contacts 
ALTER COLUMN email DROP NOT NULL;

-- Add comment for clarity
COMMENT ON COLUMN contacts.phone IS 'Phone number - optional for all contact types';
COMMENT ON COLUMN contacts.email IS 'Email address - required for agent, optional for group';

