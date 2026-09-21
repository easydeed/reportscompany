"""
The stranded-runs backfill does what its comments say, when actually executed.

WHY THIS EXISTS
---------------
`scripts/reconcile_stranded_schedule_runs.sql` is a proposal for a live
database: seven statements, four of them `UPDATE`s against ten months of
history. Until 2026-09-21 it had never been parsed by a Postgres.

It was not uncovered. `apps/worker/tests/test_schedule_run_lifecycle.py` reads
it as **text** and asserts substrings appear in it —
`"finished_at = g.generated_at" in sql`. That catches the mistake it was written
for (stamping `NOW()` over ten months of real timestamps) and it is not
execution. From the outside the file looked tested.

Running it found three defects that reading it had not:

  1. Section 3's `schedule_runs` UPDATE had NO age guard, so a run created
     seconds earlier — generation legitimately `processing` — was marked
     "consumed then killed mid-flight; report never produced". A backfill that
     can fabricate a failure for work still in progress.

  2. Section 3's `report_generations` UPDATE was guarded on `g.generated_at`,
     which is NULL for a generation that was never consumed (the API writes
     status and no timestamp). `NULL < ...` is NULL, so the never-picked-up
     rows were silently skipped.

  3. The VERIFY said "should return zero rows" and could not: section 4
     deliberately leaves the dangling row, which the verify counted. A correct
     run reported failure.

1 and 2 are opposite errors from one missing idea — the population belongs to
the RUN's age, which always exists, not the generation's timestamp, which may
be NULL or may be recent. Together they produced the exact inconsistency the
file exists to remove.

NEEDS A DATABASE and skips cleanly without one. What is being tested is whether
Postgres does what the SQL says, which cannot be answered with Postgres mocked.

Run:
    TEST_DATABASE_URL=postgresql://postgres@localhost:5432/scratch \
      PYTHONPATH=apps/worker/src pytest apps/worker/tests/test_reconcile_backfill.py -v
"""
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

BACKFILL = (
    Path(__file__).resolve().parents[3]
    / "scripts" / "reconcile_stranded_schedule_runs.sql"
)

DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("SCRATCH_DATABASE_URL")

psycopg = pytest.importorskip("psycopg", reason="psycopg is required")
pytestmark = pytest.mark.skipif(
    not DB_URL or not shutil.which("psql"),
    reason="Needs TEST_DATABASE_URL (a throwaway database) and psql on PATH",
)

# The distribution the file's own header says to expect, at the real
# proportions, plus one row the investigation never had: a run that is stranded
# in the same SHAPE but is not stranded at all — it is happening right now.
STRANDED = {"completed_with_pdf": 27, "failed": 8, "processing": 18, "never_consumed": 3}

SCHEMA = """
CREATE TABLE accounts (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT);
CREATE TABLE schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  name TEXT, cadence TEXT, recipients TEXT[], active BOOLEAN DEFAULT TRUE,
  next_run_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE report_generations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID, report_type TEXT, input_params JSONB,
  status TEXT, pdf_url TEXT, error TEXT,
  generated_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT NOW());
-- report_run_id is a BARE UUID with no foreign key (0006_schedules.sql:42).
-- Reproduced exactly: section 4 depends on a dangling value being legal.
CREATE TABLE schedule_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  report_run_id UUID,
  status TEXT NOT NULL DEFAULT 'queued',
  error TEXT, started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW());
"""


PSQL = shutil.which("psql")


def run_backfill(conn, schema):
    """
    Run the file THROUGH PSQL, which is how Jerry will run it.

    The first version of this helper split the file on `;` and fed the pieces to
    psycopg. That failed immediately, and correctly: one of the error strings is

        'backfilled: generation completed with a PDF; status write lost (D-061)'

    — a semicolon INSIDE a quoted literal, which a naive split cuts in half.
    psql parses it fine, so the failure was in the test, not the file.

    Re-implementing SQL lexing to test a SQL file is the wrong shape anyway.
    Invoking the real client is both simpler and more faithful: it exercises
    the exact path the file is meant to be used through, including `\echo` and
    anything else psql-specific that a hand-rolled splitter would silently
    mishandle.

    `-v ON_ERROR_STOP=1` makes a parse error a non-zero exit rather than a
    message psql prints and carries on past — without it this whole suite would
    pass on a file that failed to run.
    """
    env = dict(os.environ, PGOPTIONS=f"-c search_path={schema}")
    result = subprocess.run(
        [PSQL, DB_URL, "-v", "ON_ERROR_STOP=1", "-q", "-f", str(BACKFILL)],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert result.returncode == 0, (
        f"psql exited {result.returncode}\n"
        f"--- stderr ---\n{result.stderr}\n--- stdout ---\n{result.stdout[-2000:]}"
    )
    return result


@pytest.fixture
def world():
    schema = f"backfill_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {schema}")
            cur.execute(f"SET search_path TO {schema}")
            cur.execute(SCHEMA)
            cur.execute(
                "INSERT INTO accounts (id,name) VALUES "
                "('a1111111-1111-1111-1111-111111111111','A')"
            )
            cur.execute(
                "INSERT INTO schedules (id,account_id,name,cadence,recipients) VALUES "
                "('c1111111-1111-1111-1111-111111111111',"
                "'a1111111-1111-1111-1111-111111111111','S','weekly','{a@b.c}')"
            )
            old = "NOW() - interval '200 days'"
            sched = "'c1111111-1111-1111-1111-111111111111'"
            acct = "'a1111111-1111-1111-1111-111111111111'"

            def gen(status, pdf=None, err=None, generated=True, created=old):
                cur.execute(
                    f"INSERT INTO report_generations "
                    f"(account_id,report_type,status,pdf_url,error,generated_at,created_at) "
                    f"VALUES ({acct},'market_snapshot',%s,%s,%s,"
                    f"{old if generated else 'NULL'},{created}) RETURNING id::text",
                    (status, pdf, err),
                )
                gid = cur.fetchone()[0]
                cur.execute(
                    f"INSERT INTO schedule_runs (schedule_id,report_run_id,status,created_at) "
                    f"VALUES ({sched},%s::uuid,'queued',{created})",
                    (gid,),
                )
                return gid

            for _ in range(STRANDED["completed_with_pdf"]):
                gen("completed", pdf="https://r2/x.pdf")
            for _ in range(STRANDED["failed"]):
                gen("failed", err="SimplyRETS 502")
            for _ in range(STRANDED["processing"]):
                gen("processing")
            for _ in range(STRANDED["never_consumed"]):
                # generated_at NULL, which is what the API's INSERT writes.
                gen("queued", generated=False)

            # dangling report_run_id — section 4 must not touch it
            cur.execute(
                f"INSERT INTO schedule_runs (schedule_id,report_run_id,status,created_at) "
                f"VALUES ({sched}, gen_random_uuid(), 'queued', {old})"
            )
            # THE CONTROL: a run enqueued seconds ago, generation processing
            # right now. Same shape as the stranded ones, not stranded at all.
            live = gen("processing", created="NOW()")

        try:
            yield schema, conn, live
        finally:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA {schema} CASCADE")


def test_it_parses_and_every_statement_executes(world):
    """
    The floor, and the thing that was missing. Seven statements against a live
    Postgres; a typo in any of them raises here instead of in front of Jerry.
    """
    schema, conn, _ = world
    run_backfill(conn, schema)


def test_it_reconciles_every_stranded_row(world):
    schema, conn, _ = world
    run_backfill(conn, schema)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute("SELECT status, COUNT(*) FROM schedule_runs GROUP BY 1")
        by_status = dict(cur.fetchall())

    assert by_status.get("completed") == STRANDED["completed_with_pdf"]
    # 8 failed generations + 18 killed mid-flight + 3 never consumed
    assert by_status.get("failed") == (
        STRANDED["failed"] + STRANDED["processing"] + STRANDED["never_consumed"]
    )
    # what is left: the dangling row, and the live one
    assert by_status.get("queued") == 2, by_status


def test_it_does_not_condemn_a_run_that_is_still_in_flight(world):
    """
    FINDING 1. Without an age guard on the runs UPDATE, this row was marked
    'failed — consumed then killed mid-flight; report never produced' while its
    report was being generated. A backfill must not be able to fabricate a
    failure for work in progress.
    """
    schema, conn, live = world
    run_backfill(conn, schema)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute(
            "SELECT r.status, r.error FROM schedule_runs r WHERE r.report_run_id = %s::uuid",
            (live,),
        )
        status, error = cur.fetchone()
    assert status == "queued", (
        f"a run enqueued seconds ago was marked {status!r} ({error!r}); the "
        f"backfill condemned work that is still running"
    )


def test_the_never_consumed_generations_are_corrected_too(world):
    """
    FINDING 2. Guarded on `g.generated_at`, which is NULL for a generation
    nothing ever picked up, these three were silently skipped and left at
    'queued' — while their runs were marked failed. The file's own comment says
    leaving phantom rows in this table is how the next person's usage query
    goes wrong; the queued ones have exactly that problem.
    """
    schema, conn, live = world
    run_backfill(conn, schema)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute(
            "SELECT COUNT(*) FROM report_generations "
            "WHERE status = 'queued' AND generated_at IS NULL"
        )
        left = cur.fetchone()[0]
    assert left == 0, (
        f"{left} never-consumed generation(s) left at 'queued'; the guard is "
        f"reading a column that is NULL for exactly those rows"
    )


def test_the_two_tables_agree_afterwards(world):
    """
    Findings 1 and 2 are opposite errors from one missing idea, and this is the
    symptom they shared: rows whose `schedule_runs` said failed while their
    `report_generations` still said processing or queued — the inconsistency
    this file exists to remove, created by this file.
    """
    schema, conn, _ = world
    run_backfill(conn, schema)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute("""
            SELECT COUNT(*) FROM schedule_runs r
            JOIN report_generations g ON g.id = r.report_run_id
            WHERE r.status = 'failed' AND g.status IN ('processing','queued')
        """)
        disagreements = cur.fetchone()[0]
    assert disagreements == 0, (
        f"{disagreements} row(s) where the run says failed and the generation "
        f"does not agree"
    )


def test_real_timestamps_are_preserved_for_completed_runs(world):
    """
    The claim the existing text-assertion test makes, checked by execution.
    Stamping NOW() would make ten months of history look like it finished the
    day the backfill ran.
    """
    schema, conn, _ = world
    run_backfill(conn, schema)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute("""
            SELECT COUNT(*) FROM schedule_runs r
            JOIN report_generations g ON g.id = r.report_run_id
            WHERE r.status = 'completed' AND r.finished_at IS DISTINCT FROM g.generated_at
        """)
        wrong = cur.fetchone()[0]
    assert wrong == 0, f"{wrong} completed run(s) did not inherit generated_at"


def test_the_dangling_row_is_left_alone(world):
    """Section 4 is explicit that one row does not justify a guess."""
    schema, conn, _ = world
    run_backfill(conn, schema)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute("""
            SELECT COUNT(*) FROM schedule_runs r
            WHERE r.status = 'queued'
              AND NOT EXISTS (SELECT 1 FROM report_generations g WHERE g.id = r.report_run_id)
        """)
        assert cur.fetchone()[0] == 1


def test_the_backfill_is_not_a_migration():
    """
    Kept from `test_schedule_run_lifecycle.py`'s coverage: a one-off correction
    of historical rows must never end up in db/migrations/, where the runner
    would apply it to every environment forever.
    """
    migrations = Path(__file__).resolve().parents[3] / "db" / "migrations"
    assert not any("reconcile_stranded" in p.name for p in migrations.glob("*.sql"))
