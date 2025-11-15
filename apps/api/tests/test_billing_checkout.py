"""
Test Phase 29D Stripe Billing - Checkout and Portal
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


@pytest.fixture
def mock_stripe():
    """Mock Stripe API for testing without hitting real API."""
    with patch('api.routes.billing.stripe') as mock:
        # Mock Stripe customer creation
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        mock.Customer.create.return_value = mock_customer
        
        # Mock Stripe checkout session creation
        mock_session = Mock()
        mock_session.url = "https://checkout.stripe.com/session_test"
        mock.checkout.Session.create.return_value = mock_session
        
        # Mock Stripe portal session creation
        mock_portal = Mock()
        mock_portal.url = "https://billing.stripe.com/portal_test"
        mock.billing_portal.Session.create.return_value = mock_portal
        
        # Mock StripeError
        mock.error.StripeError = Exception
        
        yield mock


@pytest.fixture
def mock_db_with_account():
    """Mock database with a valid REGULAR account."""
    with patch('api.routes.billing.db_conn') as mock_db, \
         patch('api.routes.billing.set_rls'):
        
        # Mock connection context manager
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db.return_value.__enter__.return_value = (mock_conn, mock_cur)
        
        # Mock account query
        mock_cur.fetchone.side_effect = [
            # First call: account details
            (
                "test-account-id",
                "Test Account",
                "REGULAR",
                "free",
                None,  # sponsor_account_id
                None,  # stripe_customer_id
            ),
            # Second call: user email
            ("test@example.com",),
        ]
        
        yield mock_cur


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass JWT checks."""
    with patch('api.routes.billing.require_account_id', return_value="test-account-id"):
        yield


@pytest.fixture
def mock_stripe_config():
    """Mock Stripe configuration validation."""
    with patch('api.routes.billing.validate_stripe_config', return_value=(True, [])), \
         patch('api.routes.billing.get_stripe_price_for_plan', return_value="price_test123"):
        yield


def test_checkout_url_uses_correct_path(
    mock_stripe, 
    mock_db_with_account, 
    mock_auth, 
    mock_stripe_config
):
    """
    Task 2.1: Verify that Stripe checkout URLs use /account/plan, not /app/account/plan.
    
    This test ensures the fix for Task 2.1 is working:
    - success_url should be {WEB_BASE}/account/plan?checkout=success
    - cancel_url should be {WEB_BASE}/account/plan?checkout=cancel
    """
    response = client.post(
        "/v1/billing/checkout",
        json={"plan_slug": "pro"}
    )
    
    assert response.status_code == 200
    assert "url" in response.json()
    
    # Verify Stripe checkout.Session.create was called with correct URLs
    mock_stripe.checkout.Session.create.assert_called_once()
    call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    
    # Extract WEB_BASE from environment or use default
    import os
    web_base = os.getenv("WEB_BASE", "https://reportscompany-web.vercel.app")
    
    # CRITICAL: URLs should use /account/plan, NOT /app/account/plan
    assert call_kwargs["success_url"] == f"{web_base}/account/plan?checkout=success"
    assert call_kwargs["cancel_url"] == f"{web_base}/account/plan?checkout=cancel"
    
    # Ensure old path is NOT present
    assert "/app/account/plan" not in call_kwargs["success_url"]
    assert "/app/account/plan" not in call_kwargs["cancel_url"]


def test_portal_url_uses_correct_path(mock_stripe, mock_auth):
    """
    Task 2.1: Verify that Stripe portal return_url uses /account/plan, not /app/account/plan.
    """
    with patch('api.routes.billing.db_conn') as mock_db, \
         patch('api.routes.billing.set_rls'), \
         patch('api.routes.billing.validate_stripe_config', return_value=(True, [])):
        
        # Mock connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db.return_value.__enter__.return_value = (mock_conn, mock_cur)
        
        # Mock account with existing Stripe customer
        mock_cur.fetchone.return_value = ("cus_existing123",)
        
        response = client.get("/v1/billing/portal")
        
        assert response.status_code == 200
        assert "url" in response.json()
        
        # Verify portal session was created with correct return URL
        mock_stripe.billing_portal.Session.create.assert_called_once()
        call_kwargs = mock_stripe.billing_portal.Session.create.call_args.kwargs
        
        import os
        web_base = os.getenv("WEB_BASE", "https://reportscompany-web.vercel.app")
        
        # CRITICAL: return_url should use /account/plan, NOT /app/account/plan
        assert call_kwargs["return_url"] == f"{web_base}/account/plan"
        assert "/app/account/plan" not in call_kwargs["return_url"]


def test_checkout_rejects_sponsored_account(mock_stripe, mock_auth, mock_stripe_config):
    """Verify that sponsored accounts cannot self-upgrade via Stripe."""
    with patch('api.routes.billing.db_conn') as mock_db, \
         patch('api.routes.billing.set_rls'):
        
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db.return_value.__enter__.return_value = (mock_conn, mock_cur)
        
        # Mock sponsored account (has sponsor_account_id)
        mock_cur.fetchone.return_value = (
            "sponsored-account-id",
            "Sponsored Account",
            "REGULAR",
            "sponsored_free",
            "sponsor-id",  # sponsor_account_id is NOT None
            None,
        )
        
        response = client.post(
            "/v1/billing/checkout",
            json={"plan_slug": "pro"}
        )
        
        assert response.status_code == 400
        assert "sponsored_account" in response.json()["detail"]["error"]


def test_checkout_rejects_invalid_account_type(mock_stripe, mock_auth, mock_stripe_config):
    """Verify that only REGULAR accounts can upgrade."""
    with patch('api.routes.billing.db_conn') as mock_db, \
         patch('api.routes.billing.set_rls'):
        
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db.return_value.__enter__.return_value = (mock_conn, mock_cur)
        
        # Mock affiliate account (not REGULAR)
        mock_cur.fetchone.return_value = (
            "affiliate-account-id",
            "Affiliate Account",
            "INDUSTRY_AFFILIATE",  # Not REGULAR
            "affiliate",
            None,
            None,
        )
        
        response = client.post(
            "/v1/billing/checkout",
            json={"plan_slug": "pro"}
        )
        
        assert response.status_code == 400
        assert "invalid_account_type" in response.json()["detail"]["error"]

