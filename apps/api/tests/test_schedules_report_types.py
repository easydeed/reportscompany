"""
Test Phase 3 - Gallery Report Types Support

Verifies that new photo-driven report types can be created via schedules API.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from test_plans_limits import plan_row
from api.main import app

client = TestClient(app)


@pytest.fixture
def mock_auth():
    """
    Authenticate the way the app itself allows (D-091).

    THREE SEAMS; ONLY THE THIRD REACHES.

    1. `patch('api.routes.schedules.require_account_id', ...)` — what this was.
       FastAPI captures the Depends CALLABLE in the route signature at import
       time, so rebinding the module attribute changes a name nothing looks up
       again. The patch succeeded and every request still returned 401.
    2. `app.dependency_overrides` — FastAPI's real seam, and still not enough:
       `AuthContextMiddleware` returns 401 on its own (authn.py:137), before
       any dependency runs.
    3. `X-Demo-Account`, which that middleware accepts as an account id
       (authn.py:130-133) and writes to `request.state.account_id` — exactly
       what `require_account_id` reads. The app's own seam, so the real
       middleware still runs.

    Removed afterwards: a leaked header would authenticate every later test.
    """
    client.headers.update({"X-Demo-Account": "test-account-id"})
    yield
    client.headers.pop("X-Demo-Account", None)


@pytest.fixture(autouse=True)
def _rate_limiter_without_redis():
    """
    Give `RateLimitMiddleware` a working fake store (D-094).

    It calls Redis four times with no guard (authn.py:215, 233, 239, 241), so
    with no Redis reachable every authenticated request raises
    `redis.exceptions.ConnectionError` out of the middleware and 500s before any
    route runs. Filed as D-094 — a real defect, deliberately NOT fixed here
    because what a rate limiter should do when its store is down is a posture
    decision, not a test fix.

    `__init__` calls `redis.from_url` when Starlette BUILDS the middleware
    stack, which is lazy — `app.middleware_stack` is None until the first
    request. The first version of this fixture walked that stack looking for the
    instance, found None, patched nothing, and the tests failed exactly as
    before. So: patch the factory, force the build, rebuild on the way out.
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

    real_from_url = authn.redis.from_url
    authn.redis.from_url = lambda *a, **k: _FakeRedis()
    app.middleware_stack = app.build_middleware_stack()
    try:
        yield
    finally:
        authn.redis.from_url = real_from_url
        app.middleware_stack = app.build_middleware_stack()


def _route_fetchone(mock_cur, schedule_row):
    """
    Answer each `fetchone()` with a row shaped for the query that just ran (D-091).

    `fetchone.return_value = <the schedule row>` answers EVERY call with the
    same tuple, which was fine until `POST /v1/schedules` gained the D-019
    verification gate. That gate queries first and unpacks three values, and got
    the fourteen-column schedule row:

        verification.py:165  ValueError: too many values to unpack (expected 3)
        -> 500 "Failed to create schedule"

    A fixed `return_value` cannot survive a route learning a new query. Routing
    on the SQL can.
    """
    executed = []

    def record(sql, *a, **k):
        executed.append(sql if isinstance(sql, str) else str(sql))

    def answer():
        sql = executed[-1] if executed else ""
        if "email_verified" in sql:
            # sender_verification(): (any_verified, resend_email, active_users)
            return (True, None, 1)
        if "monthly_report_limit_override" in sql:
            # resolve_plan_for_account() — 15 columns, built from the query
            # itself so it cannot fall behind the way the old tuples did.
            return plan_row(plan_slug="pro", account_type="REGULAR",
                            plan_name="Pro", plan_limit=300,
                            allow_overage=False, overage_price_cents=0)
        if "count(" in sql.lower():
            return (0,)
        if "INSERT INTO schedules" in sql or "RETURNING" in sql:
            return schedule_row
        raise AssertionError(
            "the route ran a query this double does not know:\n"
            f"{' '.join(sql.split())[:200]}\n"
            "Add a branch above rather than letting it take the schedule row — "
            "that is how this fixture broke the last time a query was added "
            "(D-019's verification gate, which unpacked three values from a "
            "fourteen-column tuple)."
        )

    mock_cur.execute.side_effect = record
    mock_cur.fetchone.side_effect = answer


@pytest.fixture
def mock_db():
    """Mock database operations."""
    with patch('api.routes.schedules.db_conn') as mock_db_conn, \
         patch('api.routes.schedules.set_rls'):
        
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_db_conn.return_value.__enter__.return_value = (mock_conn, mock_cur)
        
        # Mock successful INSERT returning schedule data
        _route_fetchone(mock_cur, (
            "schedule-id-123",  # id
            "Test Schedule",  # name
            "new_listings_gallery",  # report_type
            "Anaheim",  # city
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
        ))
        
        yield mock_cur


@pytest.mark.usefixtures("db_session")
def test_create_schedule_with_new_listings_gallery(mock_auth, mock_db):
    """
    Task 3.1: Verify that 'new_listings_gallery' report type is accepted.
    """
    response = client.post(
        "/v1/schedules",
        json={
            "name": "Weekly Gallery Report",
            "report_type": "new_listings_gallery",
            "city": "Anaheim",
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


@pytest.mark.usefixtures("db_session")
def test_create_schedule_with_featured_listings(mock_auth, mock_db):
    """
    Task 3.1: Verify that 'featured_listings' report type is accepted.
    """
    response = client.post(
        "/v1/schedules",
        json={
            "name": "Featured Properties",
            "report_type": "featured_listings",
            "city": "Anaheim",
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


@pytest.mark.usefixtures("db_session")
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
        _route_fetchone(mock_db, (
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
        ))
        
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


# THESE THREE NEED A DATABASE, AND SAYING SO IS THE HONEST FIX (D-091).
#
# They POST to /v1/schedules and assert 201. That route now does far more than
# insert a row: the D-019 verification gate queries first, then
# `get_full_plan_usage` resolves the plan and the month's usage — through a
# POOLED connection, not the `api.routes.schedules.db_conn` these fixtures
# patch. Chasing that with more mocks means faking the whole data layer to
# assert one field of one response, and every future query added to the route
# breaks it again. That is the treadmill this entire ticket is about.
#
# `db_session` runs them when a database is reachable and skips cleanly when it
# is not — the pattern `test_deactivate_schedules.py` already uses. It is not a
# skip of an unfixable test; it is a correct statement of what the test needs.
#
# The coverage they were NAMED for — "the API accepts these report types" — does
# not need a database at all, and is now asserted directly against the schema in
# `test_every_report_type_is_accepted_by_the_schema` below. That runs in CI.


def test_every_report_type_is_accepted_by_the_schema():
    """
    The report-type contract, with no database, no middleware and no mocks.

    `ScheduleCreate.report_type` is a `Literal[...]` whose comment names three
    other files it must stay in sync with. This asserts the whole set in one
    place, which is what the three end-to-end tests above were really checking
    through four layers of stand-ins.
    """
    from api.routes.schedules import ScheduleCreate

    expected = {
        "market_snapshot", "new_listings", "inventory", "closed",
        "price_bands", "open_houses", "new_listings_gallery",
        "featured_listings",
    }
    for report_type in sorted(expected):
        model = ScheduleCreate(
            name="Test",
            report_type=report_type,
            city="Anaheim",
            cadence="weekly",
            weekly_dow=1,
            recipients=["agent@example.com"],
        )
        assert model.report_type == report_type

    import typing
    declared = set(typing.get_args(
        ScheduleCreate.model_fields["report_type"].annotation))
    assert declared == expected, (
        f"ScheduleCreate.report_type declares {declared ^ expected} that this "
        f"test does not. Keep it in sync with reportTypes.ts, template.py's "
        f"report_type_display map and report_builders.py's builders dict — the "
        f"Literal's own comment names all three."
    )
