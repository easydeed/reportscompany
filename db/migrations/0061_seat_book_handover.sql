-- Migration 0061: a reassigned seat records where the leaving rep's book went.
--
-- On a reassignment the agents move to the new rep (or to another rep the
-- company names), and since 2026-10-28 the leaving rep's scheduled sends move
-- WITH them — schedules, the contacts and groups those schedules resolve
-- recipients from, and copies of the rep's unsubscribes. Same seat, same work,
-- new name on it.
--
-- `book_to_account_id` is the account that received all of that. It is what
-- the unsubscribe route follows when someone clicks a link sent BEFORE the
-- move: the token was signed for the leaving rep, and the opt-out has to land
-- on the account now doing the sending (routes/unsubscribe.py).
--
-- `schedules_moved` is the count at the time, as `agents_moved` is.
--
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

ALTER TABLE rep_seat_assignments
  ADD COLUMN IF NOT EXISTS book_to_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL;
ALTER TABLE rep_seat_assignments
  ADD COLUMN IF NOT EXISTS schedules_moved INTEGER;

CREATE INDEX IF NOT EXISTS idx_rep_seat_book_from
  ON rep_seat_assignments (rep_account_id) WHERE book_to_account_id IS NOT NULL;

SELECT '0061_seat_book_handover.sql applied' AS migration;
