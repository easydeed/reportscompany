-- Migration 0060: rep seats.
--
-- SEATS ARE REP SEATS. A title company pays for its own reps; a seat is what
-- one rep occupies. Agents do not take seats: they stay `sponsored_free` and
-- upgrade themselves. COMPLIANCE: giving sponsored agents more than the Free
-- plan's limits (today 3 market / 1 schedule / 1 property, the same as `free`)
-- is a thing of value from a title company to a referral source and needs a
-- compliance check before anyone builds it. Nothing here touches an agent's
-- plan; reassignment moves an agent's sponsor and leaves the plan alone.
--
-- 1. `accounts.rep_seats` — how many seats a TITLE_COMPANY has. NULL means
--    "not on seats": nothing is enforced, which is how every company behaved
--    before this migration. Set only by the platform admin, because companies
--    are billed outside the app. No company gets a number here: the count is
--    a business decision (Jerry), not a migration's.
--
-- 2. `rep_seat_assignments` — one row per period a rep holds a seat. The
--    open rows (ended_at IS NULL) are the seats held; open seats are
--    rep_seats minus that. A pending invite holds a seat from the moment it is
--    sent, an expired invite keeps holding it until someone cancels it, and a
--    reassignment closes one row and opens the next in one transaction. The
--    closed rows are the reassignment history.
--
--    No RLS on this table, the same as `accounts`: the app connects as a
--    superuser today (D-274), so isolation lives in the route predicates and
--    is proved by apps/api/tests/test_rep_seats.py's cross-tenant tests.
--
-- 3. Backfill: one open row per existing rep under a company, dated from the
--    rep account's creation, unless the rep's owner user is deactivated (a
--    deactivated rep is not using a seat). Only rows are added; no account,
--    user or agent changes. Idempotent.
--
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

ALTER TABLE accounts ADD COLUMN IF NOT EXISTS rep_seats INTEGER;
ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_rep_seats_check;
ALTER TABLE accounts ADD CONSTRAINT accounts_rep_seats_check
  CHECK (rep_seats IS NULL OR (rep_seats >= 0 AND account_type = 'TITLE_COMPANY'));

CREATE TABLE IF NOT EXISTS rep_seat_assignments (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- CASCADE like `account_users`: a seat row means nothing without its
  -- company and rep, and deleting an account is an admin or test act.
  company_account_id       UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  rep_account_id           UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  started_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at                 TIMESTAMPTZ,
  -- Why the seat stopped being this rep's. 'reassigned': the seat moved to
  -- `successor_rep_account_id`. 'invite_cancelled': the rep never joined and
  -- the invite was withdrawn, which frees the seat.
  ended_reason             TEXT
    CHECK (ended_reason IN ('reassigned', 'invite_cancelled')),
  successor_rep_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
  ended_by_user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
  -- How many agents moved with the seat, recorded at the time: the agents'
  -- own rows only say who sponsors them now.
  agents_moved             INTEGER,
  CONSTRAINT rep_seat_end_is_whole CHECK (
    (ended_at IS NULL AND ended_reason IS NULL AND successor_rep_account_id IS NULL
       AND agents_moved IS NULL)
    OR (ended_at IS NOT NULL AND ended_reason IS NOT NULL)
  ),
  -- Only a reassignment names a successor. (Not "and always does": the
  -- successor's account can be deleted, and the history row outlives it.)
  CONSTRAINT rep_seat_successor_only_on_reassign CHECK (
    successor_rep_account_id IS NULL OR ended_reason = 'reassigned'
  )
);

-- A rep holds at most one seat at a time.
CREATE UNIQUE INDEX IF NOT EXISTS uq_rep_seat_open_per_rep
  ON rep_seat_assignments (rep_account_id) WHERE ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_rep_seat_company
  ON rep_seat_assignments (company_account_id, started_at DESC);

INSERT INTO rep_seat_assignments (company_account_id, rep_account_id, started_at)
SELECT a.parent_account_id, a.id, a.created_at
  FROM accounts a
 WHERE a.account_type = 'INDUSTRY_AFFILIATE'
   AND a.parent_account_id IS NOT NULL
   AND NOT EXISTS (
         SELECT 1 FROM rep_seat_assignments s
          WHERE s.rep_account_id = a.id AND s.ended_at IS NULL)
   AND NOT EXISTS (
         SELECT 1 FROM account_users au
           JOIN users u ON u.id = au.user_id
          WHERE au.account_id = a.id AND au.role = 'OWNER' AND u.is_active = FALSE);

SELECT '0060_rep_seats.sql applied' AS migration;
