"""
Test Phase 29D Stripe Billing - Checkout and Portal
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

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



@pytest.fixture(autouse=True)
def _rate_limiter_without_redis():
    """
    Give `RateLimitMiddleware` a working fake store (D-094).

    The middleware calls Redis FOUR times with no guard
    (middleware/authn.py:215, 233, 239, 241), so with no Redis reachable every
    authenticated request raises `redis.exceptions.ConnectionError` out of the
    middleware and 500s before any route runs. That is filed as D-094 — a real
    defect, not a test problem, and deliberately NOT fixed here because "what a
    rate limiter should do when its store is down" is a posture decision.

    The middleware still RUNS in these tests; only its store is fake. Disabling
    it instead would be removing a layer the request really passes through, and
    then a defect in it could never show up here.
    """
    from api.middleware import authn

    store = {}

    class _FakeRedis:
        def get(self, k):
            return store.get(k)

        def setex(self, k, _ttl, v):
            store[k] = v

        def incr(self, k):
            store[k] = str(int(store.get(k, 0)) + 1)
            return int(store[k])

        def expire(self, k, _ttl):
            return True

    # `RateLimitMiddleware.__init__` calls `redis.from_url` — and it runs when
    # Starlette BUILDS the middleware stack, which is lazy: `app.middleware_stack`
    # is None until the first request. The first version of this fixture walked
    # that stack looking for the instance, found None, patched nothing, and the
    # tests failed exactly as before — a fixture that did nothing and said
    # nothing. So: patch the factory, force the build, and rebuild on the way
    # out so no later test inherits a fake store.
    real_from_url = authn.redis.from_url
    authn.redis.from_url = lambda *a, **k: _FakeRedis()
    app.middleware_stack = app.build_middleware_stack()
    try:
        yield
    finally:
        authn.redis.from_url = real_from_url
        app.middleware_stack = app.build_middleware_stack()

# THESE NEED A DATABASE (D-091), FOR THE SAME REASON AS
# test_schedules_report_types.py's three.
#
# `POST /v1/billing/checkout` resolves the plan with `get_plan_by_slug(cur, …)`
# and reads the account through a POOLED connection these fixtures do not
# patch, so without a database the request spends ~40s in connection timeouts
# and then 500s. Faking that means faking the data layer to assert a URL path.
#
# `db_session` runs them where a database exists and skips cleanly where none
# does. The auth and rate-limit fixtures above are still the right fixes and
# stay: they were masking a 401 and a ConnectionError that had nothing to do
# with the database.

@pytest.fixture
def mock_auth():
    """
    Authenticate the way the app itself allows (D-091).

    THREE SEAMS, AND ONLY THE THIRD ONE WORKS HERE.

    1. `patch('api.routes.billing.require_account_id', ...)` — what this used to
       do. FastAPI captures the Depends CALLABLE in the route signature at
       import time, so rebinding the module attribute changes a name nothing
       looks up again. The patch succeeded and every request still returned
       401.

    2. `app.dependency_overrides[require_account_id]` — the seam FastAPI
       provides, and still not enough: `AuthContextMiddleware` runs BEFORE any
       dependency and returns 401 on its own (middleware/authn.py:137). A
       dependency override cannot reach past middleware.

    3. The `X-Demo-Account` header, which that middleware accepts as an
       account id (:130-133) and writes to `request.state.account_id` — which
       is exactly what `require_account_id` reads. The app's own seam, so the
       test exercises the real middleware instead of removing it.

    Headers are set on the module-level client and removed afterwards; a leaked
    header would silently authenticate every later test in the session.
    """
    client.headers.update({"X-Demo-Account": "test-account-id"})
    yield
    client.headers.pop("X-Demo-Account", None)


@pytest.fixture
def mock_stripe_config():
    """Mock Stripe configuration validation."""
    # D-091 — PATCHING A NAME THE ROUTE DOES NOT IMPORT.
    #
    # `api.routes.billing.get_stripe_price_for_plan` does not exist:
    # routes/billing.py imports only STRIPE_SECRET_KEY and
    # validate_stripe_config from config.billing (:13-16), and resolves the
    # price from the DATABASE instead — `get_plan_by_slug(cur, slug)` then
    # `plan["stripe_price_id"]` (:93, :103). `mock.patch` raises
    # AttributeError for a name the target module does not have, which is why
    # these showed up as ERRORS rather than failures.
    #
    # The price now comes from the plans table, so the double belongs on
    # `get_plan_by_slug` — patched where routes/billing LOOKS IT UP, not where
    # it is defined, because the route bound the name at import.
    with patch('api.routes.billing.validate_stripe_config', return_value=(True, [])), \
         patch('api.routes.billing.get_plan_by_slug',
               return_value={"plan_slug": "pro", "stripe_price_id": "price_test123"}):
        yield


@pytest.mark.usefixtures("db_session")
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


@pytest.mark.usefixtures("db_session")
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


@pytest.mark.usefixtures("db_session")
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


@pytest.mark.usefixtures("db_session")
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

