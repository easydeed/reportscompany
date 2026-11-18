"""Exercise pytest's real collection/setup/call skip paths in subprocesses.

The child preflight is stubbed only for skip-policy probes; separate tests
exercise preflight failure modes. No service or production credentials used.
"""
import os
import ast
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import database_ci as policy


def test_plugin_registration_allows_both_tests_packages_to_collect(tmp_path):
    # Both directories really are named tests; importing root tests too early
    # made API conftest resolve as the nonexistent root tests.conftest in CI.
    for directory in ("scripts", "tests", "apps/api/tests"):
        path = tmp_path / directory
        path.mkdir(parents=True)
        if directory != "tests":  # root tests is a namespace; API tests is a package
            (path / "__init__.py").write_text("")
    plugin = Path(policy.__file__).read_text(encoding="utf-8")
    for directory in ("scripts", "tests"):
        (tmp_path / directory / "database_ci.py").write_text(plugin, encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    registration = next(n for n in ast.parse((root / "conftest.py").read_text()).body
                        if isinstance(n, ast.Assign) and any(
                            isinstance(t, ast.Name) and t.id == "pytest_plugins" for t in n.targets))
    (tmp_path / "conftest.py").write_text(ast.unparse(registration))
    (tmp_path / "apps/api/tests/conftest.py").write_text("")
    (tmp_path / "apps/api/tests/test_api.py").write_text("def test_api(): pass\n")
    (tmp_path / "tests/test_root.py").write_text("def test_root(): pass\n")
    env = dict(os.environ, REQUIRE_DATABASE_TESTS="0", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    env.pop("PYTEST_ADDOPTS", None)
    result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 tests collected" in result.stdout


def probe(tmp_path, source, required=True, bypass_preflight=True, extra=""):
    (tmp_path / "db_guard.py").write_text(Path(policy.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    conftest = "import db_guard\n"
    if bypass_preflight:
        conftest += "db_guard.preflight = lambda: None\n"
    conftest += "pytest_plugins = ['db_guard']\n" + extra
    (tmp_path / "conftest.py").write_text(conftest, encoding="utf-8")
    (tmp_path / "test_probe.py").write_text(source, encoding="utf-8")
    env = os.environ.copy()
    for key in ("DATABASE_URL", "TEST_DATABASE_URL", "SCRATCH_DATABASE_URL", "PYTEST_ADDOPTS"):
        env.pop(key, None)
    env.update(REQUIRE_DATABASE_TESTS="1" if required else "0", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "--confcutdir", str(tmp_path)],
                          cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("phase", ["collection", "setup", "call", "teardown"])
def test_required_database_skips_fail_in_every_phase(tmp_path, phase):
    source = 'import pytest\nDATABASE_URL = "unused"\n'
    if phase == "collection":
        source += 'pytest.skip("driver unavailable", allow_module_level=True)\n'
    elif phase == "setup":
        source += '@pytest.fixture\ndef db(): pytest.skip("offline")\ndef test_db(db): pass\n'
    elif phase == "teardown":
        source += '@pytest.fixture\ndef db():\n yield\n pytest.skip("offline")\ndef test_db(db): pass\n'
    else:
        source += 'def test_db(): pytest.skip("temporarily unavailable")\n'
    result = probe(tmp_path, source)
    assert result.returncode != 0, result.stdout
    assert "LR-031: required database proof skipped" in result.stdout, result.stdout + result.stderr


def test_db_session_consumer_cannot_skip_even_without_a_module_database_import(tmp_path):
    result = probe(tmp_path, 'import pytest\ndef test_endpoint(db_session): pass\n', extra=(
        'import pytest\n@pytest.fixture\ndef db_session(): pytest.skip("offline")\n'))
    assert result.returncode != 0
    assert "LR-031" in result.stdout


def test_imported_database_fixture_is_also_required(tmp_path):
    (tmp_path / "test_shared.py").write_text(
        'import pytest\nDATABASE_URL = "unused"\n@pytest.fixture\ndef world(): pytest.skip("offline")\n')
    result = probe(tmp_path, 'from test_shared import world\ndef test_people(world): pass\n')
    assert result.returncode != 0
    assert "LR-031" in result.stdout


def test_local_optional_database_skips_stay_optional(tmp_path):
    result = probe(tmp_path, 'import pytest\nDATABASE_URL = "unused"\ndef test_db(): pytest.skip("offline")\n',
                   required=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 skipped" in result.stdout


def test_unrelated_optional_skip_remains_green(tmp_path):
    result = probe(tmp_path, 'import pytest, os\n'
                   'os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")\n'
                   'def test_redis(): pytest.skip("no redis configured")\n')
    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_strict_expected_failures_are_preserved(tmp_path):
    result = probe(tmp_path, 'import pytest\nDATABASE_URL = "unused"\n'
                   '@pytest.mark.xfail(strict=True, reason="documented defect")\ndef test_db(): assert False\n')
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 xfailed" in result.stdout


def test_existing_failure_stays_red(tmp_path):
    result = probe(tmp_path, 'def test_broken(): assert False\n')
    assert result.returncode == 1


def test_missing_ci_url_fails_before_collection(tmp_path):
    result = probe(tmp_path, 'raise RuntimeError("must not collect")\n', bypass_preflight=False)
    assert result.returncode != 0
    assert "DATABASE_URL is required" in result.stderr
    assert "must not collect" not in result.stdout + result.stderr


class Connection:
    def __init__(self, major=17, applied=(), tables=0, name="migrated"):
        self.info = type("Info", (), {"server_version": major * 10000 + 9})()
        self.applied, self.tables, self.name = applied, tables, name

    def __enter__(self): return self
    def __exit__(self, *args): pass

    def execute(self, sql):
        if "schema_migrations" in sql:
            return [(name,) for name in self.applied]
        row = (self.tables,) if "pg_tables" in sql else (self.name, "127.0.0.1", 5432)
        return type("Rows", (), {"fetchone": lambda _: row})()


def configure(monkeypatch, tmp_path, main=None, scratch=None):
    import psycopg
    directory = tmp_path / "db/migrations"
    directory.mkdir(parents=True)
    (directory / "0001_test.sql").write_text("SELECT 1;")
    monkeypatch.setattr(policy, "ROOT", tmp_path)
    monkeypatch.setenv("DATABASE_URL", "main")
    monkeypatch.setenv("TEST_DATABASE_URL", "scratch")
    main = main or Connection(applied=["0001_test.sql"])
    scratch = scratch or Connection(name="scratch")
    monkeypatch.setattr(psycopg, "connect", lambda url, **kw: main if url == "main" else scratch)


def test_supported_major_migrated_schema_and_empty_scratch_pass(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    policy.preflight()


@pytest.mark.parametrize("case,expected", [
    ("version", "must use PostgreSQL 17"), ("migration", "not fully migrated"),
    ("scratch", "empty scratch database"), ("same", "must be distinct"),
])
def test_preflight_rejects_invalid_ci_database_state(monkeypatch, tmp_path, case, expected):
    main = Connection(major=16 if case == "version" else 17,
                      applied=[] if case == "migration" else ["0001_test.sql"])
    scratch = Connection(tables=1 if case == "scratch" else 0,
                         name="migrated" if case == "same" else "scratch")
    configure(monkeypatch, tmp_path, main, scratch)
    with pytest.raises(pytest.UsageError, match=expected):
        policy.preflight()


def test_connection_errors_do_not_expose_credentials(monkeypatch, tmp_path):
    import psycopg
    configure(monkeypatch, tmp_path)
    def broken(*args, **kwargs):
        raise RuntimeError("postgresql://secret:password@private-host/database")
    monkeypatch.setattr(psycopg, "connect", broken)
    with pytest.raises(pytest.UsageError) as error:
        policy.preflight()
    assert "unreachable" in str(error.value)
    assert "secret" not in str(error.value)
