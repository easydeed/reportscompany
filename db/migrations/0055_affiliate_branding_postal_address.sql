-- Migration 0055: per-account sender postal address on affiliate_branding.
--
-- D-060. Every commercial email this product sends has shipped without the
-- physical postal address CAN-SPAM §7704(a)(5) requires. The render slot has
-- existed since #49 and has been collapsing to nothing because there was
-- nowhere to store a value — no postal-address column on `accounts`, none on
-- `affiliate_branding`, none anywhere in the schema.
--
-- WHY affiliate_branding AND NOT accounts. The address of record is the
-- SENDER'S. For a white-labelled send the sender is the affiliate whose brand
-- is on the email, and `affiliate_branding` is already the row that decides
-- whose brand that is — same key (account_id), same lifecycle, same
-- inheritance rules in services/brand_resolver.py. Putting it on `accounts`
-- would split the sender's identity across two tables and leave the resolver
-- reading one and the footer reading the other.
--
-- WHY NULLABLE, WITH NO DEFAULT HERE. A DEFAULT would write the platform's
-- address into every affiliate's row, and a row containing TrendyReports'
-- address under an affiliate's brand is an affirmative false statement about
-- who that business is — worse than the omission it replaces. The fallback
-- belongs in the render path, where it can say whose address it is; see
-- PLATFORM_POSTAL_ADDRESS in apps/worker/src/worker/email/template.py. NULL
-- here means "this account has not set one", which is a fact worth being able
-- to query.
--
-- NO VALIDATION CONSTRAINT. A postal address has no format this database can
-- check that is not also wrong somewhere — apartment lines, rural routes,
-- international, military. A CHECK here would reject a legitimate address at
-- the moment someone was trying to become compliant, which is §0.6's guard
-- trap: a guard that refuses input is a guard that can refuse legitimate
-- input. Length is bounded and nothing else is.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS, safe to re-run.
--
-- APPLIED BY JERRY, NOT BY THIS BRANCH. Nothing in CI or in the worker runs
-- migrations; see 0053's bootstrap note for what happens when a file is
-- assumed applied and is not. The code shipped alongside this reads the
-- column through COALESCE and falls back to the platform address, so it is
-- correct BEFORE this migration runs as well as after — the migration adds
-- the per-account override, it does not switch compliance on.

ALTER TABLE affiliate_branding
  ADD COLUMN IF NOT EXISTS postal_address text;

COMMENT ON COLUMN affiliate_branding.postal_address IS
  'Sender physical postal address for CAN-SPAM 15 U.S.C. 7704(a)(5). NULL '
  'means this account has not set one and the platform address is used '
  'instead, attributed to TrendyReports rather than to the account. D-060.';

-- Verification — run after applying. Expect one row, data_type text,
-- is_nullable YES.
--
--   SELECT column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'affiliate_branding' AND column_name = 'postal_address';
--
-- And to see how many accounts have set their own once a settings surface
-- exists (none will today — the column is new and nothing writes it yet):
--
--   SELECT COUNT(*) FILTER (WHERE postal_address IS NOT NULL) AS with_own,
--          COUNT(*)                                          AS total
--   FROM affiliate_branding;

SELECT '0055_affiliate_branding_postal_address.sql applied' AS migration;
