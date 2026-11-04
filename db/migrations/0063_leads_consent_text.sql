-- Migration 0063: a lead records the consent wording it was given beside (D-342, D-352).
--
-- `leads.consent_given` says a box was ticked, not what it said. Both forms
-- that create leads show a sentence beside the box — the property report page
-- (/p, "I consent to being contacted about this property and related
-- services.") and the Home Value Page (/cma, "I agree to receive my report and
-- to be contacted by {agent} about my property.", plus the brokerage's TCPA
-- wording once it is supplied). That sentence is the agreement. When the TCPA
-- wording goes in, a lead taken before it and one taken after must be told
-- apart, and only the stored wording can do that.
--
-- Nullable: leads taken before this migration have no wording on record, and
-- saying so (NULL) is the truth. New leads carry the text the form sent.
-- Additive only; nothing reads it yet but the record itself.

ALTER TABLE leads ADD COLUMN IF NOT EXISTS consent_text TEXT;

COMMENT ON COLUMN leads.consent_text IS
  'The consent wording shown beside the checkbox when this lead agreed, exactly as displayed. '
  'NULL for leads taken before 0063 (2026-11-04), which recorded only consent_given.';
