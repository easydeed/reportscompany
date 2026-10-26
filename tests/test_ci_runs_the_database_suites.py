"""CI provisions the database that the tenant-isolation proofs need (D-285).

`apps/api/tests/test_*_tenant_isolation.py` are the only red-to-green proof
that one sponsor cannot read another's agents, and they skip without
DATABASE_URL. For as long as `backend-tests.yml` provisioned no database they
skipped on every run, and the job was green either way. A skip is not a pass,
but nothing in the check's colour tells them apart.

This reads the workflow and fails if the job could quietly go back to skipping
them: no Postgres service, no migration step, or a test step without the
database URLs. `scripts/regressions/ci_database.json` removes each one in turn
and each goes red.
"""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github/workflows/backend-tests.yml"


def _job():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["test"]


def _step(job, name):
    found = [s for s in job["steps"] if s.get("name") == name]
    assert len(found) == 1, f"backend-tests.yml has {len(found)} steps named {name!r}"
    return found[0]


def test_the_job_runs_a_postgres_service():
    image = (_job().get("services") or {}).get("postgres", {}).get("image", "")
    assert image.startswith("postgres:"), "backend-tests.yml provisions no Postgres service"


def test_migrations_run_before_the_tests():
    job = _job()
    names = [s.get("name") for s in job["steps"]]
    migrate = _step(job, "Apply migrations")
    assert "scripts/run_migrations.py" in migrate["run"]
    assert "CREATE DATABASE scratch" in migrate["run"]
    assert names.index("Apply migrations") < names.index("Run tests")


def test_the_test_step_points_at_both_databases():
    env = _step(_job(), "Run tests").get("env") or {}
    assert env.get("DATABASE_URL", "").endswith("/market_reports"), (
        "Run tests has no DATABASE_URL: every db_session and tenant-isolation test skips"
    )
    assert env.get("TEST_DATABASE_URL", "").endswith("/scratch"), (
        "Run tests has no TEST_DATABASE_URL: the worker's operator-SQL suites skip"
    )
    assert env["DATABASE_URL"] != env["TEST_DATABASE_URL"], (
        "the throwaway database must not be the migrated one the app reads"
    )


def test_the_isolation_suites_read_the_database_the_app_reads():
    """With both URLs set, a suite that seeds TEST_DATABASE_URL seeds the empty
    scratch database while the routes read DATABASE_URL — every test errors."""
    for name in ("test_affiliate_tenant_isolation.py", "test_company_tenant_isolation.py"):
        src = (REPO / "apps/api/tests" / name).read_text(encoding="utf-8")
        assert 'DB_URL = os.getenv("DATABASE_URL")\n' in src, name
        assert 'getenv("TEST_DATABASE_URL")' not in src, name
