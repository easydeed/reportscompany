"""
The deactivate proposal does what it says, and refuses when it cannot be sure.

WHY THIS EXISTS
---------------
`scripts/deactivate_live_schedules.sql` is the proposal Jerry is most likely to
actually run against production — he asked for the live schedules to stop
sending — and until 2026-09-21 it had never been parsed by a Postgres. The
stranded-runs backfill had just demonstrated what an untested production-write
proposal looks like from the inside: three defects, two of which would have
written false data.

WHAT RUNNING IT FOUND
---------------------
**Its data handling was already correct**, which is worth saying plainly: on a
seeded world of 43 schedules (3 active), 1,067 `schedule_runs` rows and a paused
schedule held as a control, it changed exactly the three intended rows,
preserved `next_run_at` on each, left the control byte-identical, and retained
every run. `UPDATE` does not cascade; the history survived exactly as the file
promises.

What was wrong was the part around the write:

  1. **"Look before you write" could not be followed.** The SELECT and the
     UPDATE sat in one transaction in one file. Run as a file — the only way
     anyone runs it — psql does both in one pass, and the operator reads the
     list of what they were about to change after it has already changed.

  2. **"This must return the same count as before" had no before.** The file
     never captured a baseline, so the number it printed was unverifiable
     against anything.

  3. **"Expect 3 rows" was a stale snapshot with no enforcement.** A schedule
     that went live after 2026-09-09 was swept up silently — confirmed by
     adding a fourth and re-running: deactivated, no mention in the output.

All three are now one mechanism: `expected_active` is a REQUIRED psql variable,
and both post-write checks are assertions rather than printed numbers.

NEEDS A DATABASE and `psql`, and skips cleanly without them. Runs the file the
way Jerry will run it.
"""
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "scripts" / "deactivate_live_schedules.sql"
)

DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("SCRATCH_DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required")
pytestmark = pytest.mark.skipif(
    not DB_URL or not shutil.which("psql"),
    reason="Needs TEST_DATABASE_URL (a throwaway database) and psql on PATH",
)

PSQL = shutil.which("psql")

PAUSED = 40
ACTIVE = 3
RUNS = 120          # the shape of ten months of history, not the volume
CONTROL = "22222222-0000-0000-0000-000000000001"

SCHEMA = """
CREATE TABLE accounts (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT);
CREATE TABLE schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  name TEXT, report_type TEXT, cadence TEXT, recipients TEXT[],
  active BOOLEAN DEFAULT TRUE, next_run_at TIMESTAMPTZ, last_run_at TIMESTAMPTZ,
  consecutive_failures INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW());
-- ON DELETE CASCADE is the whole reason this file says active=FALSE and not
-- DELETE. Reproduced so the history check means something.
CREATE TABLE schedule_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  report_run_id UUID, status TEXT NOT NULL DEFAULT 'queued',
  error TEXT, started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW());
"""


def run_script(schema, expected_active="4"):
    """
    Run the file through psql exactly as the operator will, including the
    required `-v expected_active`. Pass `expected_active=None` to omit it.
    """
    cmd = [PSQL, DB_URL]
    if expected_active is not None:
        cmd += ["-v", f"expected_active={expected_active}"]
    cmd += ["-f", str(SCRIPT)]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60,
        env=dict(os.environ, PGOPTIONS=f"-c search_path={schema}"),
    )
    # A malformed argv makes psql exit non-zero too, and the refusal tests here
    # assert exactly that. The first version of this helper inserted `-v` at the
    # wrong index, so psql rejected the ARGUMENTS and three tests passed while
    # proving nothing about the guard. Anything psql says before connecting is
    # therefore a test bug, not a result.
    assert "extra command-line argument" not in result.stderr, result.stderr
    assert "No such file or directory" not in result.stderr, result.stderr
    return result


def fingerprint(cur, where="TRUE"):
    """Every field of the matching schedules, hashed. Any change shows."""
    cur.execute(f"""
        SELECT md5(string_agg(
            id::text || coalesce(name,'') || coalesce(report_type,'') ||
            coalesce(next_run_at::text,'') || coalesce(last_run_at::text,'') ||
            active::text || consecutive_failures::text ||
            coalesce(array_to_string(recipients,','),''),
            '|' ORDER BY id))
        FROM schedules WHERE {where}
    """)
    return cur.fetchone()[0]


@pytest.fixture
def world():
    schema = f"deact_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {schema}")
            cur.execute(f"SET search_path TO {schema}")
            cur.execute(SCHEMA)
            acct = "a1111111-1111-1111-1111-111111111111"
            cur.execute("INSERT INTO accounts (id,name) VALUES (%s,'A')", (acct,))
            cur.execute("""
                INSERT INTO schedules (account_id,name,report_type,cadence,recipients,
                                       active,next_run_at,last_run_at)
                SELECT %s,'paused '||i,'market_snapshot','weekly','{a@b.c}',
                       FALSE, NOW() - interval '3 days', NOW() - interval '10 days'
                FROM generate_series(1,%s) i
            """, (acct, PAUSED))
            for n in range(1, ACTIVE + 1):
                cur.execute("""
                    INSERT INTO schedules (id,account_id,name,report_type,cadence,
                                           recipients,active,next_run_at,last_run_at)
                    VALUES (%s::uuid,%s,%s,'market_snapshot','weekly','{a@b.c}',
                            TRUE, NOW() + (%s||' days')::interval, NOW() - interval '5 days')
                """, (f"11111111-0000-0000-0000-00000000000{n}", acct, f"live {n}", n))
            # THE CONTROL: already paused, with distinctive values in every
            # column this file could plausibly touch.
            cur.execute("""
                INSERT INTO schedules (id,account_id,name,report_type,cadence,recipients,
                                       active,next_run_at,last_run_at,consecutive_failures)
                VALUES (%s::uuid,%s,'control paused','inventory','monthly','{keep@me.c}',
                        FALSE,'2026-01-01T00:00:00Z','2026-01-02T00:00:00Z',2)
            """, (CONTROL, acct))
            cur.execute("""
                INSERT INTO schedule_runs (schedule_id, report_run_id, status, created_at)
                SELECT '11111111-0000-0000-0000-000000000001'::uuid, gen_random_uuid(),
                       (ARRAY['completed','failed','queued'])[1+(i%%3)],
                       NOW() - (i||' days')::interval
                FROM generate_series(1,%s) i
            """, (RUNS,))
        try:
            yield schema, conn
        finally:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA {schema} CASCADE")


def cursor(conn, schema):
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {schema}")
    return cur


# ── the happy path ──────────────────────────────────────────────────────────

def test_it_parses_and_runs(world):
    schema, _ = world
    r = run_script(schema, expected_active=str(ACTIVE))
    assert r.returncode == 0, f"psql exited {r.returncode}\n{r.stderr}"
    assert "scope confirmed" in r.stdout


def test_it_deactivates_exactly_the_active_ones(world):
    schema, conn = world
    run_script(schema, expected_active=str(ACTIVE))
    cur = cursor(conn, schema)
    cur.execute("SELECT COUNT(*) FROM schedules WHERE active")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM schedules")
    assert cur.fetchone()[0] == PAUSED + ACTIVE + 1, "a schedule was deleted"


def test_next_run_at_is_preserved(world):
    """
    Deliberate, per the header: an inactive schedule is never enqueued
    regardless of `next_run_at`, and keeping it preserves what the schedule was
    going to do. Nulling it would quietly destroy that.
    """
    schema, conn = world
    run_script(schema, expected_active=str(ACTIVE))
    cur = cursor(conn, schema)
    cur.execute("""
        SELECT COUNT(*) FROM schedules
        WHERE id::text LIKE '11111111%' AND next_run_at IS NULL
    """)
    assert cur.fetchone()[0] == 0


def test_the_history_survives(world):
    """
    The claim the whole file is built on. `schedule_runs.schedule_id` is
    `ON DELETE CASCADE`, so `DELETE FROM schedules` would take ten months of
    runs with it. `UPDATE` does not cascade — asserted rather than assumed.
    """
    schema, conn = world
    run_script(schema, expected_active=str(ACTIVE))
    cur = cursor(conn, schema)
    cur.execute("SELECT COUNT(*) FROM schedule_runs")
    assert cur.fetchone()[0] == RUNS


def test_an_already_paused_schedule_is_byte_identical_afterwards(world):
    """
    THE CONTROL. The UPDATE is `WHERE active = TRUE`, so a paused row should be
    outside it entirely — but "should be outside the predicate" and "was not
    touched" are different claims, and only one of them is checked by running it.
    """
    schema, conn = world
    cur = cursor(conn, schema)
    before = fingerprint(cur, f"id = '{CONTROL}'::uuid")
    run_script(schema, expected_active=str(ACTIVE))
    cur = cursor(conn, schema)
    assert fingerprint(cur, f"id = '{CONTROL}'::uuid") == before


# ── the refusals ────────────────────────────────────────────────────────────

def test_a_wrong_expectation_aborts_and_changes_nothing(world):
    """
    FINDING 3. "Expect 3 rows (43 schedules exist, 3 are active)" was a comment
    describing 2026-09-09. Running it later, with a fourth schedule live, swept
    that one up silently. Now the count is something the operator states and the
    file checks.
    """
    schema, conn = world
    cur = cursor(conn, schema)
    before = fingerprint(cur)

    r = run_script(schema, expected_active=str(ACTIVE + 1))   # wrong on purpose
    assert r.returncode != 0, "a wrong expectation was accepted"
    assert "STOP" in r.stderr, r.stderr

    cur = cursor(conn, schema)
    assert fingerprint(cur) == before, "the aborted run still changed something"


def test_omitting_the_expectation_aborts_before_the_write(world):
    """
    The property that makes the guard more than a formality: you cannot run this
    file without saying what you expect to find. psql leaves `:expected_active`
    uninterpolated, which is a syntax error, which — with ON_ERROR_STOP set
    inside the file — ends the transaction before the UPDATE.
    """
    schema, conn = world
    cur = cursor(conn, schema)
    before = fingerprint(cur)

    r = run_script(schema, expected_active=None)
    assert r.returncode != 0, "the file ran without an expected_active"

    cur = cursor(conn, schema)
    assert fingerprint(cur) == before, "a run with no expectation changed data"


def test_the_guard_runs_before_the_update_not_after(world):
    """
    Ordering, asserted on the outcome rather than on the file's text. A guard
    placed after the UPDATE would still abort the transaction — the rollback
    would save the data — but it would also mean the operator's stated
    expectation was never what decided anything. The distinction shows up if
    the transaction is ever split, which is exactly the kind of edit nobody
    re-tests.
    """
    schema, conn = world
    r = run_script(schema, expected_active="999")
    assert r.returncode != 0
    # psql prints statements as they fail; the UPDATE must never have reported.
    assert "UPDATE" not in r.stdout, (
        f"the UPDATE ran before the scope guard rejected the run:\n{r.stdout}"
    )
