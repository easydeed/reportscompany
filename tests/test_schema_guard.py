"""The services refuse to start when the database is behind the code (D-310).

On 2026-10-28 #224 and #226 went live needing 0060 and 0061 while production
stopped at 0055; unsubscribes, rep invites and the company dashboard returned
500 for a day and nothing said so. `schema_guard.enforce` now runs at the start
of the API, the Celery worker, the schedules ticker and the bridge.

What is held here:
  * REQUIRED_MIGRATION is the newest migration in db/migrations, in both copies
    of the module — so a PR that adds a migration and forgets it fails CI;
  * the two copies are the same code;
  * against a real database: the check passes when the row is there, and
    refuses the exact state production was in (0056-0061 missing), and a
    database with no tracking table at all;
  * `enforce` exits on a database that is behind, starts on one it cannot
    reach, and honours the bypass only for the one migration it names;
  * each of the four processes calls it before doing anything else.
"""
import ast
import importlib
import importlib.util
import inspect
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "db/migrations"
API_GUARD = ROOT / "apps/api/src/api/schema_guard.py"
WORKER_GUARD = ROOT / "apps/worker/src/worker/schema_guard.py"
DB_URL = os.getenv("DATABASE_URL")
needs_db = pytest.mark.skipif(not DB_URL, reason="needs DATABASE_URL")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def guard():
    return _load(API_GUARD, "_schema_guard_under_test")


def _newest_migration():
    return max(p.name for p in MIGRATIONS.glob("*.sql") if p.name[:4].isdigit() and p.name[4] == "_")


# ── the constant and the mirror ──────────────────────────────────────────────

@pytest.mark.parametrize("path", [API_GUARD, WORKER_GUARD], ids=["api", "worker"])
def test_the_required_migration_is_the_newest_one(path):
    required = _load(path, f"_g_{path.parent.name}").REQUIRED_MIGRATION
    assert required == _newest_migration(), (
        f"{path.relative_to(ROOT)} requires {required}, but the newest migration is "
        f"{_newest_migration()}. Set REQUIRED_MIGRATION to it in BOTH schema_guard.py "
        f"files: the code that needs the new migration must not start without it.")


def test_the_worker_guard_is_the_api_guard():
    def body(path):
        tree = ast.parse(path.read_text())
        tree.body = tree.body[1:]          # the module docstring may differ
        return ast.dump(tree)
    assert body(API_GUARD) == body(WORKER_GUARD), (
        "apps/api/src/api/schema_guard.py and apps/worker/src/worker/schema_guard.py "
        "differ. Neither service can import the other's; change both.")


# ── the check, against a real database ──────────────────────────────────────

@needs_db
def test_a_database_with_the_migration_passes(guard):
    """POSITIVE CONTROL: the test database is migrated to the newest file."""
    import psycopg
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        guard.check(cur)


@needs_db
def test_production_as_it_was_on_october_28_is_refused(guard):
    """0056-0061 unapplied, the newest recorded 0055: the state the deploy of
    #224/#226 met. The message names what is needed and what is there."""
    import psycopg
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM schema_migrations WHERE filename >= '0056'")
        with pytest.raises(guard.SchemaBehind) as refused:
            guard.check(cur)
        conn.rollback()
    assert guard.REQUIRED_MIGRATION in str(refused.value)
    assert "0055_affiliate_branding_postal_address.sql" in str(refused.value)


@needs_db
def test_a_database_with_no_tracking_table_is_refused(guard):
    import psycopg
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("CREATE SCHEMA schema_guard_empty")
        cur.execute("SET LOCAL search_path = schema_guard_empty")
        with pytest.raises(guard.SchemaBehind, match="no schema_migrations table"):
            guard.check(cur)
        conn.rollback()


# ── enforce ──────────────────────────────────────────────────────────────────

def _behind(guard):
    def check(cur):
        raise guard.SchemaBehind("needs it")
    return check


@needs_db
def test_enforce_exits_when_the_database_is_behind(guard, monkeypatch):
    monkeypatch.setattr(guard, "check", _behind(guard))
    monkeypatch.delenv("SCHEMA_BEHIND_ACKNOWLEDGED", raising=False)
    with pytest.raises(SystemExit) as stopped:
        guard.enforce(DB_URL, "api")
    assert stopped.value.code == 1


@needs_db
def test_enforce_starts_when_the_database_is_current(guard):
    guard.enforce(DB_URL, "api")


@needs_db
def test_the_bypass_names_one_migration_and_only_that_one(guard, monkeypatch):
    monkeypatch.setattr(guard, "check", _behind(guard))
    monkeypatch.setenv("SCHEMA_BEHIND_ACKNOWLEDGED", guard.REQUIRED_MIGRATION)
    guard.enforce(DB_URL, "api")                       # acknowledged: starts
    monkeypatch.setenv("SCHEMA_BEHIND_ACKNOWLEDGED", "0055_affiliate_branding_postal_address.sql")
    with pytest.raises(SystemExit):                    # an old acknowledgement: refused
        guard.enforce(DB_URL, "api")
    monkeypatch.setenv("SCHEMA_BEHIND_ACKNOWLEDGED", "1")
    with pytest.raises(SystemExit):                    # a switch, not a name: refused
        guard.enforce(DB_URL, "api")


def test_an_unreachable_database_does_not_stop_the_start(guard, caplog):
    """A blip must not become a crash loop that outlasts it."""
    guard.enforce("postgresql://nobody@127.0.0.1:1/none?connect_timeout=1", "api")
    assert "could not check the database schema" in caplog.text


# ── every process calls it first ─────────────────────────────────────────────

class _Called(BaseException):
    """BaseException, like the SystemExit `enforce` raises: Celery's signal
    dispatch catches and logs `Exception` from a receiver, so only a
    BaseException stops the worker — and only one tests that it would."""


@pytest.fixture
def worker_enforce(monkeypatch):
    """Point the worker's enforce at a sentinel; a process that calls it raises."""
    monkeypatch.setenv("DATABASE_URL", DB_URL or "postgresql://nobody@127.0.0.1:1/none")
    sys.path.insert(0, str(ROOT / "apps/worker/src"))
    module = importlib.import_module("worker.schema_guard")
    calls = []

    def enforce(dsn, service):
        calls.append(service)
        raise _Called(service)

    monkeypatch.setattr(module, "enforce", enforce)
    return calls


def test_the_api_checks_at_startup():
    sys.path.insert(0, str(ROOT / "apps/api/src"))
    from api.main import app
    hooks = {f.__name__: f for f in app.router.on_startup}
    assert "_require_schema" in hooks, list(hooks)
    assert "enforce(" in inspect.getsource(hooks["_require_schema"])


def test_the_celery_worker_checks_before_taking_a_task(worker_enforce):
    from celery import signals
    importlib.import_module("worker.app")
    with pytest.raises(_Called):
        signals.worker_init.send(sender=None)
    assert worker_enforce == ["worker"]


class _Looped(BaseException):
    """The loop's first step was reached: the check was skipped. Raised so a
    process without the check fails here instead of looping forever."""


def _first_step(*_, **__):
    raise _Looped()


def test_the_ticker_checks_before_its_first_tick(worker_enforce, monkeypatch):
    tick = importlib.import_module("worker.schedules_tick")
    monkeypatch.setattr(tick, "keep_api_warm", _first_step)
    with pytest.raises(_Called):
        tick.run_forever()
    assert worker_enforce == ["schedules ticker"]


def test_the_bridge_checks_before_its_first_job(worker_enforce, monkeypatch):
    tasks = importlib.import_module("worker.tasks")
    monkeypatch.setattr(tasks, "create_redis_connection", _first_step)
    with pytest.raises(_Called):
        tasks.run_redis_consumer_forever()
    assert worker_enforce == ["bridge"]
