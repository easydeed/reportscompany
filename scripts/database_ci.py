"""LR-031: required database proof cannot silently become a skipped suite.

Lives outside the competing root/API `tests` packages, and is loaded by the
initial conftest; optional on developer machines. CI opts in
with REQUIRE_DATABASE_TESTS=1. Existing per-suite guards stay in place.
"""
import ast
import os
from functools import lru_cache
from pathlib import Path

import pytest

PRODUCTION_MAJOR = 17
ROOT = Path(__file__).resolve().parents[1]
_required_ci = False


def required():
    return os.getenv("REQUIRE_DATABASE_TESTS") == "1"


def pytest_configure(config):
    # Tests may monkeypatch their environment. The job's policy cannot be
    # disabled halfway through a test or by a module's fallback URL setup.
    global _required_ci
    _required_ci = required()


def preflight():
    """Read-only checks before collection, including importorskip markers.

    Never echo URLs or driver exceptions: either may contain credentials.
    The migration runner, not this plugin, creates the CI schema.
    """
    urls = {key: os.getenv(key) for key in ("DATABASE_URL", "TEST_DATABASE_URL")}
    for key, url in urls.items():
        if not url:
            raise pytest.UsageError(f"LR-031: {key} is required for database CI")
    try:
        import psycopg
    except ImportError:
        raise pytest.UsageError("LR-031: psycopg is required for database CI") from None
    identities = []
    for key, url in urls.items():
        try:
            with psycopg.connect(url, connect_timeout=5) as conn:
                version = conn.info.server_version // 10000
                if version != PRODUCTION_MAJOR:
                    raise pytest.UsageError(
                        f"LR-031: {key} must use PostgreSQL {PRODUCTION_MAJOR}; got {version}")
                identity = conn.execute(
                    "SELECT current_database(), inet_server_addr()::text, inet_server_port()"
                ).fetchone()
                identities.append(identity)
                if key == "DATABASE_URL":
                    applied = {row[0] for row in conn.execute("SELECT filename FROM schema_migrations")}
                    expected = {p.name for p in (ROOT / "db/migrations").glob("*.sql")}
                    missing = expected - applied
                    if missing:
                        raise pytest.UsageError(
                            "LR-031: CI schema is not fully migrated: " + ", ".join(sorted(missing)))
                else:
                    tables = conn.execute(
                        "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'"
                    ).fetchone()[0]
                    if tables:
                        raise pytest.UsageError("LR-031: TEST_DATABASE_URL must be an empty scratch database")
        except pytest.UsageError:
            raise
        except Exception:
            raise pytest.UsageError(f"LR-031: {key} is unreachable or its schema is invalid") from None
    if identities[0] == identities[1]:
        raise pytest.UsageError("LR-031: migrated and scratch databases must be distinct")


def pytest_sessionstart(session):
    if _required_ci:
        preflight()


@lru_cache(maxsize=None)
def database_file(path, seen=frozenset()):
    """Recognise DB suites by executable dependencies, not skip prose.

    This includes mixed files with an inline SQL regression and files using
    importorskip before pytest has collected any items. db_session users are
    also recognised from pytest's resolved fixture closure below.
    """
    path = Path(path).resolve()
    if path in seen:
        return False
    seen = seen | {path}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in {"DATABASE_URL", "TEST_DATABASE_URL", "DB_URL"}:
            return True
        if isinstance(node, ast.Import) and any(n.name.split(".")[0] == "psycopg" for n in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "psycopg":
            return True
        # Importing a pytest fixture does not import its module's pytestmark.
        # Follow same-directory test helpers too (e.g. company_people -> rep_seats).
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("test_"):
            if database_file(str(path.parent / (node.module + ".py")), seen):
                return True
        # importorskip("psycopg") is a DB dependency. Merely seeding a fake
        # DATABASE_URL via os.environ.setdefault is not (render/Redis tests).
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (node.func.attr == "importorskip" and node.args
                    and isinstance(node.args[0], ast.Constant) and node.args[0].value == "psycopg"):
                return True
    return False


def _fail_skip(report):
    report.outcome = "failed"
    report.longrepr = f"LR-031: required database proof skipped: {report.nodeid}\n{report.longrepr}"


@pytest.hookimpl(tryfirst=True)
def pytest_collectreport(report):
    if _required_ci and report.skipped and database_file(report.nodeid.split("::")[0]):
        _fail_skip(report)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    if (_required_ci and report.skipped and not hasattr(report, "wasxfail")
            and ("db_session" in item.fixturenames or database_file(str(item.path)))):
        _fail_skip(report)
