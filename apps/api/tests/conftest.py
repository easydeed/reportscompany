"""
Test configuration and fixtures for API tests.
"""
import os
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

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

