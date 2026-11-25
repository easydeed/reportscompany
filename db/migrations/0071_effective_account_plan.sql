-- LR-012: read-only shared plan projection, database clock and inclusive boundary.
-- Jerry applies after code PASS, before merge. No account/price mappings changed.
SET LOCAL lock_timeout = '5s';
CREATE FUNCTION effective_account_plan(stored text, deadline timestamptz, target text)
RETURNS text LANGUAGE sql STABLE PARALLEL SAFE SECURITY INVOKER
AS $$ SELECT CASE WHEN deadline IS NOT NULL AND target IS NOT NULL AND deadline <= now()
                  THEN target ELSE COALESCE(stored, 'free') END $$;
