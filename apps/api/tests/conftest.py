"""
Test configuration and fixtures for API tests.
"""
import os
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# And this directory, so test modules can import the shared helpers beside them
# (`_query_rows`). It is needed because `apps/api/tests/__init__.py` exists,
# which makes this a package and stops pytest inserting the directory itself —
# the same thing that would otherwise make `from _query_rows import …` fail
# with ModuleNotFoundError in a directory where the file is plainly visible.
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_db_url():
    """
    Test database URL. Override with TEST_DATABASE_URL environment variable.
    Defaults to a local test database.
    """
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://localhost/market_reports_test"
    )


@pytest.fixture
def api_client():
    """
    FastAPI test client for integration tests.
    """
    from api.main import app
    return TestClient(app)


@pytest.fixture
def mock_db_connection():
    """
    Mock database connection for unit tests that don't need real DB.
    Tests can override this with actual DB if needed.
    """
    return None



@pytest.fixture
def db_session():
    """
    A live database, or a clean skip (D-091).

    `test_me_endpoint.py` asks for this fixture and it has never existed, so
    both of its tests ERRORED with `fixture 'db_session' not found` — which
    reads like a broken suite and is really a fixture that was removed, or never
    committed, while its callers stayed.

    They are integration tests: they INSERT accounts and users and then call the
    endpoint. There is no honest way to make them pass without a database, and
    faking one would turn an integration test into a worse unit test. So this
    follows the pattern `apps/worker/tests/test_deactivate_schedules.py`
    already uses for the same situation — run when a database is reachable, skip
    cleanly when it is not — which keeps CI green without pretending the
    coverage is there.

    It yields nothing: the tests open their own connections through `db_conn()`.
    Depending on this fixture is how they declare the requirement, and that is
    all it is for.
    """
    url = os.getenv("DATABASE_URL") or os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("needs a database: set DATABASE_URL or TEST_DATABASE_URL")
    try:
        import psycopg
    except ImportError:  # pragma: no cover - environment-dependent
        pytest.skip("needs psycopg")
    try:
        with psycopg.connect(url, connect_timeout=3):
            pass
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"database at DATABASE_URL is not reachable: {exc}")
    yield url
