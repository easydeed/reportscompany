"""
Test Phase 3 - Gallery Report Types Support

Verifies that new photo-driven report types can be created via schedules API.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass JWT checks."""
    with patch('api.routes.schedules.require_account_id', return_value="test-account-id"):
        yield


@pytest.fixture
def mock_db():
    """Mock database operations."""
    with patch('api.routes.schedules.db_conn') as mock_db_conn, \
         patch('api.routes.schedules.set_rls'):
        
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db_conn.return_value.__enter__.return_value = (mock_conn, mock_cur)
        
        # Mock successful INSERT returning schedule data
        mock_cur.fetchone.return_value = (
            "schedule-id-123",  # id
            "Test Schedule",  # name
            "new_listings_gallery",  # report_type
            "Atlanta",  # city
            [],  # zip_codes
            30,  # lookback_days
            "weekly",  # cadence
            1,  # weekly_dow
            None,  # monthly_dom
            9,  # send_hour
            0,  # send_minute
            ["test@example.com"],  # recipients
            False,  # include_attachment
            True,  # active
            None,  # last_run_at
            "2025-11-22T09:00:00Z",  # next_run_at
            "2025-11-15T10:00:00Z",  # created_at
        )
        
        yield mock_cur


def test_create_schedule_with_new_listings_gallery(mock_auth, mock_db):
    """
    Task 3.1: Verify that 'new_listings_gallery' report type is accepted.
    """
    response = client.post(
        "/v1/schedules",
        json={
            "name": "Weekly Gallery Report",
            "report_type": "new_listings_gallery",
            "city": "Atlanta",
            "lookback_days": 7,
            "cadence": "weekly",
            "weekly_dow": 1,  # Monday
            "send_hour": 9,
            "send_minute": 0,
            "recipients": ["agent@example.com"],
            "include_attachment": False,
            "active": True
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["report_type"] == "new_listings_gallery"


def test_create_schedule_with_featured_listings(mock_auth, mock_db):
    """
    Task 3.1: Verify that 'featured_listings' report type is accepted.
    """
    response = client.post(
        "/v1/schedules",
        json={
            "name": "Featured Properties",
            "report_type": "featured_listings",
            "city": "Atlanta",
            "lookback_days": 30,
            "cadence": "monthly",
            "monthly_dom": 1,  # 1st of month
            "send_hour": 10,
            "send_minute": 0,
            "recipients": ["broker@example.com"],
            "include_attachment": True,
            "active": True
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["report_type"] == "featured_listings"


def test_all_report_types_accepted(mock_auth, mock_db):
    """
    Task 3.1: Verify all 7 report types are accepted by API validation.
    
    Original types: market_snapshot, new_listings, inventory, closed, price_bands
    New types: new_listings_gallery, featured_listings
    """
    all_types = [
        "market_snapshot",
        "new_listings",
        "inventory",
        "closed",
        "price_bands",
        "new_listings_gallery",
        "featured_listings",
    ]
    
    for report_type in all_types:
        # Update mock to return current report_type
        mock_db.fetchone.return_value = (
            f"schedule-{report_type}",
            f"Schedule for {report_type}",
            report_type,
            "Test City",
            [],
            30,
            "weekly",
            1,
            None,
            9,
            0,
            ["test@example.com"],
            False,
            True,
            None,
            "2025-11-22T09:00:00Z",
            "2025-11-15T10:00:00Z",
        )
        
        response = client.post(
            "/v1/schedules",
            json={
                "name": f"Test {report_type}",
                "report_type": report_type,
                "city": "Test City",
                "lookback_days": 30,
                "cadence": "weekly",
                "weekly_dow": 1,
                "send_hour": 9,
                "send_minute": 0,
                "recipients": ["test@example.com"],
                "active": True
            }
        )
        
        assert response.status_code == 201, f"Failed for report_type: {report_type}"
        assert response.json()["report_type"] == report_type


def test_invalid_report_type_rejected(mock_auth, mock_db):
    """
    Task 3.1: Verify that invalid/unknown report types are rejected with 422.
    """
    response = client.post(
        "/v1/schedules",
        json={
            "name": "Invalid Report",
            "report_type": "invalid_report_type",  # Not in Literal list
            "city": "Test City",
            "lookback_days": 30,
            "cadence": "weekly",
            "weekly_dow": 1,
            "send_hour": 9,
            "send_minute": 0,
            "recipients": ["test@example.com"],
            "active": True
        }
    )
    
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation error)
    assert "report_type" in response.text.lower()

