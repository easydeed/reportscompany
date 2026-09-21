-- Who would lose sending when D-019's gate ships?
--
-- READ ONLY. Three SELECTs, no writes, no DDL. Run against production before
-- merging `fix/d019-verified-sending`.
--
-- The gate asks one question per account: does it have any active user with a
-- confirmed email address? An account where the answer is no keeps logging in,
-- building and previewing, and stops being able to send or to arm a schedule.
-- Because production is test data there is no grandfathering to design — but
-- there is still a difference between "nobody is affected" and "these three
-- accounts stop working on Tuesday", and only the database can tell them apart.
--
-- The predicate below is the same one the code runs
-- (api/verification.py::sender_verification and
--  worker/schedules_tick.py::account_can_send). If you change one, change all
-- three.
--
-- AND THAT SAMENESS IS CHECKED, not asserted. It appears here in three shapes —
-- a `HAVING bool_or(...)` in section 1, a `NOT EXISTS` in section 2, a
-- subquery in section 3 — because the three sections need different SQL, not
-- because the rule differs. `apps/api/tests/test_sender_query_matches_code.py`
-- seeds a world covering every shape of account (verified owner; unverified;
-- no users at all; one verified and one not; a verified user who is INACTIVE)
-- and asserts all three formulations pick the same set, and that the set
-- matches `sender_verification()`. 6 accounts, 0 disagreements, both
-- directions.
--
-- The reason that test exists rather than a comment saying "keep these in
-- sync": a diagnostic query that has drifted from the code does not fail. It
-- returns zero rows, which is the answer everybody is hoping for, so nobody
-- questions it. See §0.6.
--
-- VALIDATED ON POSTGRES 16.13, on a scratch database. **Production is
-- documented as PostgreSQL 15** (`docs/architecture/SOURCE_OF_TRUTH.md:168`),
-- which is documentation rather than a live reading. Nothing used here —
-- `bool_or`, `FILTER (WHERE ...)`, `STRING_AGG`, `ARRAY_LENGTH` — behaves
-- differently across those versions, but "tested" should not be read as
-- "tested on production's version", so section 0 prints the server version
-- this is actually running on.

\echo '=== 0. Which server is this? ==='
SELECT version() AS server_version;
\echo ''

\echo '=== 1. Accounts that would be blocked from sending ==='
SELECT
    a.id                                        AS account_id,
    a.name,
    a.account_type,
    a.plan_slug,
    COUNT(u.id)                                 AS active_users,
    COALESCE(
        STRING_AGG(u.email, ', ' ORDER BY u.created_at), '(none)'
    )                                           AS addresses
FROM accounts a
LEFT JOIN users u
       ON u.account_id = a.id
      AND COALESCE(u.is_active, TRUE) = TRUE
GROUP BY a.id, a.name, a.account_type, a.plan_slug
HAVING COALESCE(bool_or(COALESCE(u.email_verified, FALSE)), FALSE) = FALSE
ORDER BY a.name;

\echo ''
\echo '=== 2. …of those, the ones with an ACTIVE schedule (the ticker stops these) ==='
-- This is the sharp end. Accounts in section 1 with no schedules simply lose an
-- action they were not using. These have a standing instruction to email people
-- that will stop firing, silently from the schedule owner's point of view — the
-- evidence will be an `email_log` row with status 'blocked_unverified' per
-- skipped tick, which is exactly what that row is for.
SELECT
    a.id            AS account_id,
    a.name,
    s.id            AS schedule_id,
    s.name          AS schedule_name,
    s.cadence,
    s.next_run_at,
    ARRAY_LENGTH(s.recipients, 1) AS recipient_count
FROM accounts a
JOIN schedules s ON s.account_id = a.id AND s.active = TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM users u
    WHERE u.account_id = a.id
      AND COALESCE(u.is_active, TRUE) = TRUE
      AND COALESCE(u.email_verified, FALSE) = TRUE
)
ORDER BY s.next_run_at NULLS FIRST;

\echo ''
\echo '=== 3. Scale check: verified vs not, across all accounts ==='
-- Sanity, and the number to sanity-check the other two against. If section 1
-- returns nearly every account, the likely explanation is not that everyone
-- skipped the link — it is that `users.email_verified` defaults to false
-- (0001_base.sql:35) and some path creates users without setting it. Two such
-- paths exist and both are accounted for: `accept_invite` sets it TRUE
-- (auth.py:466), and `seed_test_accounts.py` sets it TRUE. A third would be a
-- finding, not a reason to weaken the gate.
SELECT
    CASE WHEN has_verified THEN 'can send' ELSE 'would be blocked' END AS state,
    COUNT(*) AS accounts
FROM (
    SELECT a.id,
           COALESCE(bool_or(COALESCE(u.email_verified, FALSE)), FALSE) AS has_verified
    FROM accounts a
    LEFT JOIN users u
           ON u.account_id = a.id
          AND COALESCE(u.is_active, TRUE) = TRUE
    GROUP BY a.id
) t
GROUP BY has_verified
ORDER BY has_verified DESC;
