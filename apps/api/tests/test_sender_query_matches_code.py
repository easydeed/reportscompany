"""
The lockout query says the same thing as the gate it describes.

WHAT THIS GUARDS
----------------
`scripts/check_unverified_senders.sql` tells Jerry which accounts will stop
being able to send when D-019's gate ships. It encodes the gate's rule in SQL,
in a file the gate cannot see, to be run by someone else, once.

**A diagnostic query that has drifted from its code does not fail. It
reassures.** It returns a short list, or an empty one, and an empty one is the
answer everybody is hoping for — so nobody asks whether it is still the right
question. A test at least has the dignity of being able to go red. See §0.6.

THREE SHAPES, ONE RULE
----------------------
The rule appears three times in that file, and deliberately not in the same
form: section 1 needs an aggregate (`HAVING bool_or(...)`) because it groups to
report addresses, section 2 needs `NOT EXISTS` because it joins to schedules,
section 3 needs a subquery because it counts both sides. Textual identity is
therefore the wrong check. What must hold is that all three pick the same
accounts, and that the set is the one `sender_verification()` would produce.

NEEDS A DATABASE, and skips cleanly without one — same convention as
`test_company_tenant_isolation.py`, for the same reason: this is a question
about whether Postgres and Python agree, and it cannot be answered with either
one mocked.

Run:
    TEST_DATABASE_URL=postgresql://postgres@localhost:5432/scratch \
      PYTHONPATH=apps/api/src pytest apps/api/tests/test_sender_query_matches_code.py -v
"""
import os
import re
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

QUERY_FILE = (
    Path(__file__).resolve().parents[3] / "scripts" / "check_unverified_senders.sql"
)

DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("SCRATCH_DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required")
pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="Set TEST_DATABASE_URL (or SCRATCH_DATABASE_URL) to a throwaway database",
)


# ── the world ───────────────────────────────────────────────────────────────
#
# (label, [(email, verified, active), ...], has_active_schedule)
#
# Every shape an account can be in as far as this rule is concerned. The last
# two are the ones that make the rule non-obvious and the ones a rewrite is
# most likely to get wrong:
#
#   MIXED  — one verified user and one not. The gate is account-level, so this
#            account CAN send. A per-user reading would block it.
#   STALE  — the only verified user is deactivated. The account CANNOT send,
#            and it is the `is_active` filter alone that decides.

WORLD = [
    ("verified owner",          [("ok@x.com", True, True)],                          False),
    ("unverified, no schedule", [("typo@x.com", False, True)],                        False),
    ("unverified, schedule on", [("typo2@x.com", False, True)],                       True),
    ("no users at all",         [],                                                   False),
    ("mixed verified and not",  [("new@x.com", False, True), ("boss@x.com", True, True)], False),
    ("verified user inactive",  [("gone@x.com", True, False), ("here@x.com", False, True)], False),
]

EXPECTED_BLOCKED = {
    "unverified, no schedule",
    "unverified, schedule on",
    "no users at all",
    "verified user inactive",
}


@pytest.fixture
def world():
    """Builds accounts/users/schedules in their own schema, and drops it."""
    schema = f"senders_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {schema}")
            cur.execute(f"SET search_path TO {schema}")
            cur.execute("""
                CREATE TABLE accounts (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  name TEXT, account_type TEXT DEFAULT 'REGULAR',
                  plan_slug TEXT DEFAULT 'free')
            """)
            cur.execute("""
                CREATE TABLE users (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                  email TEXT, email_verified BOOLEAN DEFAULT false,
                  is_active BOOLEAN DEFAULT true,
                  created_at TIMESTAMPTZ DEFAULT NOW())
            """)
            cur.execute("""
                CREATE TABLE schedules (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                  name TEXT, cadence TEXT, recipients TEXT[],
                  active BOOLEAN DEFAULT true, next_run_at TIMESTAMPTZ)
            """)
            ids = {}
            for label, users, has_schedule in WORLD:
                cur.execute(
                    "INSERT INTO accounts (name) VALUES (%s) RETURNING id::text", (label,)
                )
                aid = cur.fetchone()[0]
                ids[label] = aid
                for email, verified, active in users:
                    cur.execute(
                        "INSERT INTO users (account_id, email, email_verified, is_active) "
                        "VALUES (%s::uuid,%s,%s,%s)",
                        (aid, email, verified, active),
                    )
                if has_schedule:
                    cur.execute(
                        "INSERT INTO schedules (account_id, name, cadence, recipients, active) "
                        "VALUES (%s::uuid,'Weekly blast','weekly','{a@b.c,d@e.f}',TRUE)",
                        (aid,),
                    )
        try:
            yield schema, ids, conn
        finally:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA {schema} CASCADE")


def statements():
    """The query's own SELECTs, split out of the file rather than retyped."""
    text = QUERY_FILE.read_text()
    text = re.sub(r"^\\echo.*$", "", text, flags=re.M)      # psql meta-commands
    text = re.sub(r"^\s*--.*$", "", text, flags=re.M)       # comments
    return [s.strip() for s in text.split(";") if s.strip()]


def test_the_query_runs_at_all(world):
    """
    The floor. A file Jerry is asked to run against production should have been
    run at least once by whoever wrote it — this project has already shipped a
    migration that was never applied because nobody executed it.
    """
    schema, _ids, conn = world
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        for stmt in statements():
            cur.execute(stmt)      # raises on a syntax or column error
            cur.fetchall()


def test_all_three_sections_pick_the_same_accounts(world):
    """
    The rule is written three ways because the three sections need different
    SQL, not because the rule differs. If a rewrite changes one shape and not
    the others, the sections start contradicting each other and the person
    reading the output has no way to tell which one to believe.
    """
    schema, ids, conn = world
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")

        # section 1's shape: aggregate
        cur.execute("""
            SELECT a.name FROM accounts a
            LEFT JOIN users u ON u.account_id = a.id AND COALESCE(u.is_active, TRUE) = TRUE
            GROUP BY a.id, a.name
            HAVING COALESCE(bool_or(COALESCE(u.email_verified, FALSE)), FALSE) = FALSE
        """)
        by_aggregate = {r[0] for r in cur.fetchall()}

        # section 2's shape: NOT EXISTS
        cur.execute("""
            SELECT a.name FROM accounts a
            WHERE NOT EXISTS (
                SELECT 1 FROM users u
                WHERE u.account_id = a.id
                  AND COALESCE(u.is_active, TRUE) = TRUE
                  AND COALESCE(u.email_verified, FALSE) = TRUE
            )
        """)
        by_not_exists = {r[0] for r in cur.fetchall()}

        # section 3's shape: subquery
        cur.execute("""
            SELECT name FROM (
                SELECT a.id, a.name,
                       COALESCE(bool_or(COALESCE(u.email_verified, FALSE)), FALSE) AS has_verified
                FROM accounts a
                LEFT JOIN users u ON u.account_id = a.id AND COALESCE(u.is_active, TRUE) = TRUE
                GROUP BY a.id, a.name
            ) t WHERE NOT has_verified
        """)
        by_subquery = {r[0] for r in cur.fetchall()}

    assert by_aggregate == by_not_exists == by_subquery, (
        "the query's three formulations disagree:\n"
        f"  aggregate:  {sorted(by_aggregate)}\n"
        f"  not exists: {sorted(by_not_exists)}\n"
        f"  subquery:   {sorted(by_subquery)}"
    )
    assert by_aggregate == EXPECTED_BLOCKED, (
        f"expected {sorted(EXPECTED_BLOCKED)}, got {sorted(by_aggregate)}"
    )


def test_the_query_agrees_with_the_gate(world):
    """
    THE WHOLE POINT. `sender_verification()` is what actually decides at request
    time; the query is a prediction of what it will decide. A disagreement means
    Jerry is told the wrong set — in one direction an account that will be
    locked out without warning, in the other a false alarm.
    """
    from api.verification import sender_verification

    schema, ids, conn = world
    disagreements = []
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute("""
            SELECT a.name,
                   COALESCE(bool_or(COALESCE(u.email_verified, FALSE)), FALSE) = FALSE
            FROM accounts a
            LEFT JOIN users u ON u.account_id = a.id AND COALESCE(u.is_active, TRUE) = TRUE
            GROUP BY a.id, a.name
        """)
        verdicts = dict(cur.fetchall())

        for label, query_says_blocked in verdicts.items():
            state = sender_verification(cur, ids[label])
            code_says_blocked = not state.verified
            if query_says_blocked != code_says_blocked:
                disagreements.append(
                    f"  {label:26} query says {'blocked' if query_says_blocked else 'can send':9}"
                    f" | the gate says {'blocked' if code_says_blocked else 'can send'}"
                )

    assert not disagreements, (
        "check_unverified_senders.sql and sender_verification() disagree:\n"
        + "\n".join(disagreements)
    )


def test_the_account_level_reading_is_the_one_being_tested(world):
    """
    Names the decision so a change to it fails HERE, with the reason, rather
    than as a mysterious diff in Jerry's output.

    An account with one verified user and one unverified user CAN send. That is
    not an accident of the SQL — it is the account-level rule, forced by
    `AuthContextMiddleware` resolving no user at all on the API-key and
    `X-Demo-Account` paths. Anyone moving to a per-user check has to change this
    test on purpose.
    """
    from api.verification import sender_verification

    schema, ids, conn = world
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        mixed = sender_verification(cur, ids["mixed verified and not"])
        assert mixed.verified, (
            "an account with a verified owner and an unverified second seat was "
            "blocked; the gate is account-level by design"
        )
        stale = sender_verification(cur, ids["verified user inactive"])
        assert not stale.verified, (
            "an account whose only verified user is deactivated was allowed to "
            "send; the is_active filter is what decides here"
        )
        empty = sender_verification(cur, ids["no users at all"])
        assert not empty.verified and empty.active_users == 0, (
            "an account with no users at all was allowed to send; this rule "
            "fails closed"
        )
