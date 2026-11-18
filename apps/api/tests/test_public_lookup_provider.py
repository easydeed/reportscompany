"""Drive the public handler, cache and SiteX retries with generated data only."""
from contextlib import nullcontext
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from starlette.requests import Request
from starlette.responses import Response

from api.routes import lead_pages
from api.services import public_lookup_budget as budget
from api.services.lookup_windows import WindowResult
from api.services import sitex


@pytest.mark.parametrize("responses, expected_attempts", [
    ([200], 1),       # normal lookup
    ([401, 200], 2),  # token refresh
    ([404, 200], 2),  # second street form
])
async def test_observe_requests_before_cache_and_each_provider_attempt(
    responses, expected_attempts, monkeypatch
):
    address = f"{len(responses)} Generated Street"
    events = []

    def shared(limits):
        events.append(tuple(key for key, _ in limits))
        # Even a would-refuse on both tiers leaves the normal response intact.
        return WindowResult(False, tuple(ceiling for _, ceiling in limits), (3600,) * len(limits))

    answers = iter(responses)

    def fake_provider(req):
        events.append("property GET")
        return httpx.Response(next(answers), json={"Feed": {"PropertyProfile": {"SiteAddress": address}}})

    monkeypatch.setattr(budget, "take_shared", shared)
    monkeypatch.delenv("LOOKUP_TRUST_VERIFIED_PROXY", raising=False)
    monkeypatch.setattr(lead_pages, "db_conn", lambda: nullcontext((None, None)))
    monkeypatch.setattr(lead_pages, "get_agent_by_code", lambda cur, code: {"id": "generated-page"})
    monkeypatch.setattr(sitex, "_property_cache", {})
    async with httpx.AsyncClient(transport=httpx.MockTransport(fake_provider)) as transport:
        client = sitex.SiteXClient(SimpleNamespace(search_url="https://provider.invalid/search", feed_id="unit"))
        client._client = transport
        client._initialized = True
        client._token_manager = SimpleNamespace(get_token=AsyncMock(return_value="generated-token"))
        monkeypatch.setattr(sitex, "get_sitex_client", AsyncMock(return_value=client))
        request = Request({"type": "http", "method": "POST", "path": "/v1/cma/sample/search", "headers": []})
        payload = lead_pages.PropertySearchRequest(address=address)
        for _ in range(2):
            result = await lead_pages.search_property("sample", payload, request, Response())
            assert result[0].address == address

    assert events == [
        ("lb:v:direct",),
        *([("lb:p:generated-page", "lb:g"), "property GET"] * expected_attempts),
        ("lb:v:direct",),
    ]


@pytest.mark.parametrize("refused_stage, code", [("request", "lookup_limit"), ("provider", "lookup_busy")])
async def test_local_refusal_contract_with_a_fake_provider(refused_stage, code, monkeypatch):
    monkeypatch.setenv("LOOKUP_BUDGET_ENFORCE", "1")
    monkeypatch.setenv("LOOKUP_TRUST_VERIFIED_PROXY", "1")
    monkeypatch.setenv("PROXY_SHARED_SECRET", "unit-proxy")
    monkeypatch.setenv("VISITOR_KEY_SECRET", "unit-keys")
    checks = []

    def shared(limits):
        stage = "request" if limits == budget.DIRECT else "provider"
        checks.append(stage)
        allowed = stage != refused_stage
        counts = tuple(1 if allowed else ceiling for _, ceiling in limits)
        return WindowResult(allowed, counts, (120,) * len(limits))

    monkeypatch.setattr(budget, "take_shared", shared)
    read_page = Mock(side_effect=lambda: nullcontext((None, None)))
    monkeypatch.setattr(lead_pages, "db_conn", read_page)
    monkeypatch.setattr(lead_pages, "get_agent_by_code", lambda cur, code: {"id": "generated"})
    monkeypatch.setattr(sitex, "_property_cache", {})
    client = sitex.SiteXClient(SimpleNamespace(search_url="https://provider.invalid/search", feed_id="unit"))
    client._client = AsyncMock()
    client._initialized = True
    client._token_manager = SimpleNamespace(get_token=AsyncMock(return_value="unit"))
    monkeypatch.setattr(sitex, "get_sitex_client", AsyncMock(return_value=client))
    request = Request({"type": "http", "method": "POST", "path": "/v1/cma/sample/search", "headers": []})
    response = await lead_pages.search_property(
        "sample", lead_pages.PropertySearchRequest(address="4 Generated Street"), request, Response()
    )
    assert checks == (["request"] if refused_stage == "request" else ["request", "provider"])
    client._client.get.assert_not_awaited()
    client._token_manager.get_token.assert_not_awaited()
    assert response.status_code == 429 and json.loads(response.body)["code"] == code
    assert response.headers["Retry-After"] == "120"
    if refused_stage == "request":
        read_page.assert_not_called()
        assert response.headers["RateLimit-Remaining"] == "0" and response.headers["RateLimit-Limit"] == "20"


async def test_attempt_that_stops_at_token_refresh_consumes_one_slot(monkeypatch):
    checks = []

    def shared(limits):
        checks.append(limits)
        return WindowResult(True, (1, 1), (3600, 3600))

    monkeypatch.setattr(budget, "take_shared", shared)
    client = sitex.SiteXClient(SimpleNamespace(search_url="https://provider.invalid/search"))
    client._client = AsyncMock()
    client._token_manager = SimpleNamespace(get_token=AsyncMock(side_effect=sitex.SiteXAuthError("unit refresh")))
    with budget.public_search("generated"), pytest.raises(sitex.SiteXAuthError):
        await client._make_request({})
    client._client.get.assert_not_awaited()
    assert checks == [(("lb:p:generated", 200), ("lb:g", 1000))]
