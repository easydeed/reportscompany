"""LR-006 November 12 policy. Generated identities, clocks and in-process counters."""
import asyncio
import hmac
import logging
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from starlette.requests import Request

from api.services import lookup_windows as windows
from api.services import public_lookup_budget as budget


@pytest.fixture(autouse=True)
def observation_mode(monkeypatch):
    monkeypatch.setenv("LOOKUP_BUDGET_ENFORCE", "0")


def request(page="sample", headers=()):
    return Request({"type": "http", "method": "POST", "path": f"/v1/cma/{page}/search",
                    "headers": [(name.encode(), value.encode()) for name, value in headers]})


@pytest.fixture
def signed(monkeypatch):
    # Independently generated positive signing examples; no deployment assumptions.
    monkeypatch.setenv("LOOKUP_TRUST_VERIFIED_PROXY", "1")
    monkeypatch.setenv("PROXY_SHARED_SECRET", "unit-proxy")
    monkeypatch.setenv("VISITOR_KEY_SECRET", "unit-keys")
    now = 1_800_000_000
    monkeypatch.setattr(budget, "time", SimpleNamespace(time=lambda: now))

    def create(n, ip, page="sample"):
        visitor = f"{n:032x}"
        body = f"{now}\nPOST /v1/cma/{page}/search\n{ip}\n{visitor}".encode()
        sig = hmac.digest(b"unit-proxy", body, "sha256").hex()
        return request(page, [("x-tr-visitor-id", visitor), ("x-tr-visitor-ip", ip),
                              ("x-tr-proxy-ts", str(now)), ("x-tr-proxy-sig", sig)])

    return create


def test_attribution_requires_operator_opt_in_and_config(signed, monkeypatch):
    example = signed(1, "192.0.2.1")
    monkeypatch.delenv("LOOKUP_TRUST_VERIFIED_PROXY")
    assert budget.request_limits(example) == budget.DIRECT
    monkeypatch.setenv("LOOKUP_TRUST_VERIFIED_PROXY", "1")
    monkeypatch.delenv("VISITOR_KEY_SECRET")
    assert budget.request_limits(example) == budget.DIRECT


def test_generated_identities_share_only_the_documented_budgets(signed):
    first = budget.request_limits(signed(1, "2001:db8:1::1"))
    neighbor = budget.request_limits(signed(2, "2001:db8:1::2"))
    other_page = budget.request_limits(signed(1, "2001:db8:1::1", "another"))
    assert first == other_page
    assert first[0] != neighbor[0] and first[1] == neighbor[1]
    assert first[0][1] == 20 and first[1][1] == 60
    assert len(first[0][0].removeprefix("lb:v:")) == 32
    assert first[1][0].startswith("lb:ip:") and "2001:" not in first[1][0]
    assert budget.request_limits(signed(1, "192.0.2.1"))[1] != budget.request_limits(signed(1, "192.0.2.2"))[1]
    assert budget.request_limits(signed(1, "::ffff:192.0.2.1")) == budget.request_limits(signed(1, "192.0.2.1"))


def test_shared_store_submits_both_limits_in_one_script_call(monkeypatch):
    from api import cache

    redis = Mock()
    redis.eval.return_value = [0, 20, 55, 123, 456]
    monkeypatch.setattr(cache, "get_redis", lambda: redis)
    assert windows.take_shared((("lb:v:generated", 20), ("lb:ip:generated", 60))) == (False, (20, 55), (123, 456))
    redis.eval.assert_called_once_with(windows._TAKE, 2, "lb:v:generated", "lb:ip:generated",
                                       300, 12, 3900, 20, 60)


def test_address_ceiling_and_refused_pair_are_atomic(signed):
    local = windows.LocalWindow(16, lambda: 0)
    people = [budget.request_limits(signed(n, "192.0.2.9")) for n in range(4)]
    for person in people[:3]:
        assert all(local.take(person)[0] for _ in range(20))
    assert local.take(people[3]) == (False, (0, 60), (3600, 3600))
    assert people[3][0][0] not in local.windows
    assert local.take(people[0]) == (False, (20, 60), (3600, 3600))


def test_rolling_hour_preserves_recent_buckets_and_reuses_expired_capacity():
    now = [3599]
    local = windows.LocalWindow(1, lambda: now[0])
    assert local.take(budget.DIRECT) == (True, (1,), (3301,))
    now[0] = 3600
    for _ in range(19):
        assert local.take(budget.DIRECT)[0]
    assert local.take(budget.DIRECT) == (False, (20,), (3300,))
    assert local.take((("lb:v:next", 20),)) == (False, (0,), ())
    now[0] = 6900  # first five-minute bucket has just left the rolling window
    assert local.take(budget.DIRECT) == (True, (20,), (300,))
    now[0] += 3600
    assert local.take((("lb:v:next", 20),)) == (True, (1,), (3600,))


def test_concurrent_fallback_takes_only_twenty():
    window = windows.LocalWindow(4, lambda: 0)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda _: window.take(budget.DIRECT), range(80)))
    assert sum(r.allowed for r in results) == 20


async def test_shared_provider_thresholds_and_separate_page_keys(monkeypatch, caplog):
    counter = windows.LocalWindow(10, lambda: 0)
    monkeypatch.setattr(budget, "take_shared", counter.take)
    caplog.set_level(logging.INFO, logger=budget.logger.name)
    for n in range(5):
        with budget.public_search(f"generated-page-{n}"):
            for _ in range(200):
                await budget.check_provider_attempt()
            await budget.check_provider_attempt()
            assert "would-refuse" in caplog.messages[-1]
    with budget.public_search("generated-page-extra"):
        await budget.check_provider_attempt()
    assert caplog.messages[-1].endswith("would-refuse counts=(0, 1000)")
    assert sum("decision=allow" in m for m in caplog.messages) == 1000
    assert "generated-page" not in caplog.text


async def test_outage_and_recovery(monkeypatch, caplog):
    shared = Mock(side_effect=OSError("synthetic outage"))
    monkeypatch.setattr(budget, "take_shared", shared)
    monkeypatch.setattr(budget, "_request_fallback", windows.LocalWindow(4, lambda: 0))
    monkeypatch.setattr(budget, "_provider_fallback", windows.LocalWindow(1, lambda: 0))
    monkeypatch.delenv("LOOKUP_TRUST_VERIFIED_PROXY", raising=False)
    caplog.set_level(logging.INFO, logger=budget.logger.name)
    for n in range(31):
        await budget.check_request(request())
        with budget.public_search(f"sample-{n}"):
            await budget.check_provider_attempt()
    assert "LOOKUP_LIMITER_DEGRADED stage=provider decision=would-refuse counts=(30,)" in caplog.messages
    assert "LOOKUP_LIMITER_DEGRADED stage=direct decision=would-refuse counts=(20,)" in caplog.messages
    assert sum("decision=allow" in m for m in caplog.messages) == 50
    assert "synthetic outage" not in caplog.text and "sample-" not in caplog.text
    shared.side_effect = None
    shared.return_value = windows.WindowResult(True, (1,), (3600,))
    await budget.check_request(request())
    assert caplog.messages[-1] == "LOOKUP_BUDGET stage=direct decision=allow counts=(1,)"


async def test_broken_fallback_records_would_refuse(monkeypatch, caplog):
    monkeypatch.setattr(budget, "take_shared", Mock(side_effect=OSError()))
    monkeypatch.setattr(budget, "_provider_fallback", Mock(take=Mock(side_effect=RuntimeError())))
    with budget.public_search("synthetic"):
        await budget.check_provider_attempt()
    assert caplog.messages[-1] == "LOOKUP_LIMITER_DEGRADED stage=provider decision=would-refuse counts=()"


async def test_public_and_private_tasks_keep_separate_contexts(monkeypatch):
    counter = Mock(return_value=windows.WindowResult(True, (1, 1), (3600, 3600)))
    monkeypatch.setattr(budget, "take_shared", counter)

    async def visit(page):
        with budget.public_search(page):
            await asyncio.sleep(0)
            await budget.check_provider_attempt()

    await asyncio.gather(visit("generated-a"), visit("generated-b"), budget.check_provider_attempt())
    await budget.check_provider_attempt()
    assert sorted(call.args[0][0][0] for call in counter.call_args_list) == ["lb:p:generated-a", "lb:p:generated-b"]


async def test_enforcement_switch_alone_keeps_observing(monkeypatch):
    monkeypatch.setenv("LOOKUP_BUDGET_ENFORCE", "1")
    monkeypatch.delenv("LOOKUP_TRUST_VERIFIED_PROXY", raising=False)
    monkeypatch.setattr(budget, "take_shared", lambda _: windows.WindowResult(False, (20,), (100,)))
    assert await budget.check_request(request()) == {}


async def test_admitted_headers_and_later_simultaneous_reset(signed, monkeypatch):
    monkeypatch.setenv("LOOKUP_BUDGET_ENFORCE", "1")
    shared = Mock(return_value=windows.WindowResult(True, (4, 51), (100, 150)))
    monkeypatch.setattr(budget, "take_shared", shared)
    person = signed(1, "192.0.2.2")
    assert await budget.check_request(person) == {
        "RateLimit-Remaining": "9", "RateLimit-Limit": "60", "RateLimit-Reset": "150"
    }
    shared.return_value = windows.WindowResult(False, (20, 60), (100, 150))
    with pytest.raises(budget.LookupRefusal) as result:
        await budget.check_request(person)
    assert result.value.headers["Retry-After"] == "150"
    assert result.value.body["detail"].endswith("in 3 minutes.")


async def test_failed_local_counter_uses_busy_response(signed, monkeypatch):
    monkeypatch.setenv("LOOKUP_BUDGET_ENFORCE", "1")
    monkeypatch.setattr(budget, "take_shared", Mock(side_effect=OSError()))
    monkeypatch.setattr(budget, "_request_fallback", Mock(take=Mock(side_effect=RuntimeError())))
    with pytest.raises(budget.LookupRefusal) as result:
        await budget.check_request(signed(1, "192.0.2.2"))
    assert result.value.body["code"] == "lookup_busy"
    assert result.value.headers == {"Retry-After": "60"}
