"""
The cadence hazard query says the same thing as the code it describes.

WHAT THIS GUARDS
----------------
`scripts/check_schedule_cadence_validity.sql` answers one question: can any
existing schedule make `compute_next_run` raise, leaving the ticker to re-claim
it every 60 seconds forever? Jerry runs it against production; the answer
decides whether that loop gets filed or closed as unreachable.

A diagnostic query is a claim about code, written in a different language, in a
different file, run by someone else. It is exactly the kind of artefact that is
right on the day it is written and wrong six weeks later, and its being wrong is
invisible — it returns zero rows either way, and zero rows is the answer
everybody is hoping for. **A query that has silently stopped matching the code
does not fail. It reassures.**

So the SQL is not retyped here. The test reads the CASE expression **out of the
file**, between its `-- >>> HAZARD-CASE` markers, and runs it against
`compute_next_run` case by case. Edit the function's failure modes without
editing the query, or the other way round, and this fails.

NEEDS A DATABASE, and skips cleanly without one — same convention as
`apps/api/tests/test_company_tenant_isolation.py`, for the same reason: what is
being tested is whether Postgres and Python agree, which cannot be demonstrated
with one of them mocked. It builds its own table and drops it.

Run:
    DATABASE_URL=postgresql://postgres@localhost:5432/scratch \
      PYTHONPATH=apps/worker/src pytest apps/worker/tests/test_cadence_hazard_query.py -v
"""
import os
import re
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/does-not-exist")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.schedules_tick import compute_next_run  # noqa: E402

QUERY_FILE = (
    Path(__file__).resolve().parents[3] / "scripts" / "check_schedule_cadence_validity.sql"
)

DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("SCRATCH_DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required")
pytestmark = pytest.mark.skipif(
    not DB_URL,
    reason="Set TEST_DATABASE_URL (or SCRATCH_DATABASE_URL) to a throwaway database",
)


# ── the case matrix ─────────────────────────────────────────────────────────
#
# (label, cadence, weekly_dow, monthly_dom, send_hour, send_minute, timezone)
#
# Both directions matter. A predicate that flags everything would catch every
# hazard and be useless, so the healthy rows are as load-bearing as the broken
# ones — they are what stops the query reporting the whole table as at risk.

CASES = [
    # healthy
    ("healthy weekly",        "weekly",  1,    None, 9,    0,    "America/Los_Angeles"),
    ("healthy monthly",       "monthly", None, 15,   9,    0,    "UTC"),
    ("midnight weekly",       "weekly",  0,    None, 0,    0,    "UTC"),
    ("last minute weekly",    "weekly",  6,    None, 23,   59,   "UTC"),
    ("monthly dom 28",        "monthly", None, 28,   9,    0,    "UTC"),
    # wrong but not fatal — must NOT be flagged by section 1
    ("dom 31 (capped)",       "monthly", None, 31,   9,    0,    "UTC"),
    ("dow 99 (wrong day)",    "weekly",  99,   None, 9,    0,    "UTC"),
    ("dow -1 (wrong day)",    "weekly",  -1,   None, 9,    0,    "UTC"),
    ("unknown timezone",      "weekly",  1,    None, 9,    0,    "Mars/Olympus"),
    # raises
    ("weekly, no dow",        "weekly",  None, None, 9,    0,    "UTC"),
    ("monthly, no dom",       "monthly", None, None, 9,    0,    "UTC"),
    ("monthly, dom 0",        "monthly", None, 0,    9,    0,    "UTC"),
    ("monthly, dom -3",       "monthly", None, -3,   9,    0,    "UTC"),
    ("send_hour NULL",        "weekly",  1,    None, None, 0,    "UTC"),
    ("send_minute NULL",      "weekly",  1,    None, 9,    None, "UTC"),
    ("send_hour 24",          "weekly",  1,    None, 24,   0,    "UTC"),
    ("send_hour -1",          "weekly",  1,    None, -1,   0,    "UTC"),
    ("send_minute 60",        "weekly",  1,    None, 9,    60,   "UTC"),
    ("send_minute -1",        "weekly",  1,    None, 9,    -1,   "UTC"),
]

# `cadence` carries a CHECK in the real schema, so the 'unknown cadence' arm
# cannot be exercised through a table that has it. It is covered directly
# against the function instead — see the last test.
UNKNOWN_CADENCES = ["daily", "Weekly", "MONTHLY", "", "biweekly"]


def hazard_case_sql() -> str:
    """The CASE expression, read out of the query file rather than retyped."""
    text = QUERY_FILE.read_text()
    blocks = re.findall(
        r"--\s*>>>\s*HAZARD-CASE\s*\n(.*?)--\s*<<<\s*HAZARD-CASE",
        text,
        re.S,
    )
    assert len(blocks) == 1, (
        f"expected exactly one marked HAZARD-CASE block in {QUERY_FILE.name}, "
        f"found {len(blocks)}"
    )
    return blocks[0].strip()


def raises(cadence, dow, dom, hour, minute, tz) -> bool:
    try:
        compute_next_run(cadence, dow, dom, hour, minute, tz)
        return False
    except Exception:
        return True


@pytest.fixture
def table():
    """
    A real `schedules`-shaped table, built to match db/migrations 0006 + 0015 +
    0016 + 0027 + 0033, and dropped afterwards. Named per-run so a crashed
    previous run cannot collide.
    """
    name = f"schedules_hazard_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE {name} (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  name TEXT NOT NULL,
                  cadence TEXT NOT NULL CHECK (cadence IN ('weekly','monthly')),
                  weekly_dow INT,
                  monthly_dom INT,
                  send_hour INT DEFAULT 9,
                  send_minute INT DEFAULT 0,
                  timezone TEXT NOT NULL DEFAULT 'UTC',
                  active BOOLEAN DEFAULT TRUE
                )
            """)
        try:
            yield name, conn
        finally:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {name}")


def test_the_query_and_the_function_agree_on_every_case(table):
    """
    THE WHOLE POINT. Postgres evaluates the query's own CASE; Python calls the
    real `compute_next_run`. Any row where they disagree is a row the query
    would misreport in production — in one direction a hazard it misses, in the
    other a healthy schedule it condemns.
    """
    name, conn = table
    case_sql = hazard_case_sql()

    with conn.cursor() as cur:
        for label, cadence, dow, dom, hour, minute, tz in CASES:
            cur.execute(
                f"INSERT INTO {name} (name, cadence, weekly_dow, monthly_dom, "
                f"send_hour, send_minute, timezone) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (label, cadence, dow, dom, hour, minute, tz),
            )

        cur.execute(f"SELECT name, ({case_sql}) FROM {name} s ORDER BY name")
        verdicts = {row[0]: row[1] for row in cur.fetchall()}

    assert len(verdicts) == len(CASES), "not every case made it into the table"

    disagreements = []
    for label, cadence, dow, dom, hour, minute, tz in CASES:
        query_says = verdicts[label] is not None
        actually = raises(cadence, dow, dom, hour, minute, tz)
        if query_says != actually:
            disagreements.append(
                f"  {label:22} query says {'raises' if query_says else 'fine':6} "
                f"| the function {'raises' if actually else 'does not'}"
            )

    assert not disagreements, (
        "the hazard query and compute_next_run disagree:\n" + "\n".join(disagreements)
    )


def test_the_reason_the_query_gives_is_the_reason_the_function_has(table):
    """
    Agreeing on *whether* it raises is not enough — the `why_it_raises` string
    is what someone reads to decide what to fix. A row reported as
    "send_hour is NULL" that actually dies on a missing `weekly_dow` sends
    whoever cleans it up to the wrong column.

    Checked by shape rather than by exact text: the reason must name the field
    the function actually complains about.
    """
    name, conn = table
    case_sql = hazard_case_sql()

    expectations = {
        "weekly, no dow":   "weekly_dow",
        "monthly, no dom":  "monthly_dom",
        "monthly, dom 0":   "monthly_dom",
        "monthly, dom -3":  "monthly_dom",
        "send_hour NULL":   "send_hour",
        "send_minute NULL": "send_minute",
        "send_hour 24":     "send_hour",
        "send_hour -1":     "send_hour",
        "send_minute 60":   "send_minute",
        "send_minute -1":   "send_minute",
    }

    with conn.cursor() as cur:
        for label, cadence, dow, dom, hour, minute, tz in CASES:
            cur.execute(
                f"INSERT INTO {name} (name, cadence, weekly_dow, monthly_dom, "
                f"send_hour, send_minute, timezone) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (label, cadence, dow, dom, hour, minute, tz),
            )
        cur.execute(f"SELECT name, ({case_sql}) FROM {name} s")
        verdicts = dict(cur.fetchall())

    for label, field in expectations.items():
        reason = verdicts[label]
        assert reason and field in reason, (
            f"{label}: the query says {reason!r}, which does not name {field}"
        )


def test_the_healthy_rows_are_not_flagged(table):
    """
    The direction that makes the query useful rather than merely safe. A
    predicate that flags everything never misses a hazard and tells Jerry
    nothing.
    """
    name, conn = table
    case_sql = hazard_case_sql()
    healthy = [c for c in CASES if not raises(*c[1:])]
    assert len(healthy) >= 8, "the matrix has too few healthy cases to prove this"

    with conn.cursor() as cur:
        for label, cadence, dow, dom, hour, minute, tz in healthy:
            cur.execute(
                f"INSERT INTO {name} (name, cadence, weekly_dow, monthly_dom, "
                f"send_hour, send_minute, timezone) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (label, cadence, dow, dom, hour, minute, tz),
            )
        cur.execute(
            f"SELECT name FROM (SELECT name, ({case_sql}) AS why FROM {name} s) t "
            f"WHERE why IS NOT NULL"
        )
        flagged = [r[0] for r in cur.fetchall()]

    assert flagged == [], f"healthy schedules reported as hazards: {flagged}"


def test_an_unknown_cadence_raises_even_though_the_check_forbids_it(table):
    """
    The one arm the table cannot exercise, because the real schema's CHECK
    rejects the row — which is exactly why the query keeps the arm. Section 0 of
    the query asks whether that CHECK is present and VALID; if it was ever added
    `NOT VALID`, rows written before it are unconstrained and this arm is the
    only thing that finds them.

    Tested against the function directly, and against the SQL with the value
    supplied as a literal rather than through the constrained column.
    """
    name, conn = table
    case_sql = hazard_case_sql()

    for cadence in UNKNOWN_CADENCES:
        assert raises(cadence, 1, 1, 9, 0, "UTC"), (
            f"compute_next_run accepted cadence {cadence!r}; the query's "
            f"'unknown cadence' arm is describing a failure that no longer exists"
        )

    with conn.cursor() as cur:
        for cadence in UNKNOWN_CADENCES:
            cur.execute(
                f"SELECT ({case_sql}) FROM (SELECT %s::text AS cadence, "
                f"1::int AS weekly_dow, 1::int AS monthly_dom, "
                f"9::int AS send_hour, 0::int AS send_minute) s",
                (cadence,),
            )
            assert cur.fetchone()[0] == "unknown cadence", (
                f"the query does not flag cadence {cadence!r}"
            )


def test_the_second_copy_of_the_case_has_not_drifted():
    """
    The query uses the CASE twice — once for the detail rows and once for the
    active/paused counts — and only the first is inside the markers. Two copies
    is two things to edit and one chance to edit only one of them, which is the
    drift this whole file exists to prevent, one level up.

    So: they must be character-for-character identical once whitespace is
    normalised. If a third copy ever appears it fails here too.
    """
    text = QUERY_FILE.read_text()
    bodies = [
        " ".join(m.split())
        for m in re.findall(r"CASE\s+WHEN s\.cadence NOT IN.*?END", text, re.S)
    ]
    assert len(bodies) == 2, f"expected 2 copies of the hazard CASE, found {len(bodies)}"
    assert bodies[0] == bodies[1], (
        "the two copies of the hazard CASE in the query have diverged:\n"
        f"  marked: {bodies[0]}\n"
        f"  second: {bodies[1]}"
    )
