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
    monkeypatch.setattr(windows, "_breaker", windows._Breaker())
    monkeypatch.setattr(windows, "_client", None, raising=False)


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
    redis = Mock()
    redis.eval.return_value = [0, 20, 55, 123, 456]
    monkeypatch.setattr(windows, "_redis", lambda: redis)
    assert windows.take_shared((("lb:v:generated", 20), ("lb:ip:generated", 60))) == (False, (20, 55), (123, 456))
    redis.eval.assert_called_once_with(windows._TAKE, 3, "lb:v:generated", "lb:ip:generated",
                                       windows.SEQ_KEY, 3_600_000_000, 20, 60)


def test_address_ceiling_and_refused_pair_are_atomic(signed):
    local = windows.LocalWindow(16, lambda: 0)
    people = [budget.request_limits(signed(n, "192.0.2.9")) for n in range(4)]
    for person in people[:3]:
        assert all(local.take(person)[0] for _ in range(20))
    assert local.take(people[3]) == (False, (0, 60), (3600, 3600))
    assert people[3][0][0] not in local.windows
    assert local.take(people[0]) == (False, (20, 60), (3600, 3600))


def test_the_window_is_an_exact_sliding_hour():
    now = [3599]
    local = windows.LocalWindow(1, lambda: now[0])
    assert local.take(budget.DIRECT) == (True, (1,), (3600,))
    now[0] = 3600
    for _ in range(19):
        assert local.take(budget.DIRECT)[0]
    assert local.take(budget.DIRECT) == (False, (20,), (3599,))   # the 3599 entry frees in 3599 s
    assert local.take((("lb:v:next", 20),)) == (False, (0,), ())  # capacity 1: refused, nothing evicted
    now[0] = 7198
    assert local.take(budget.DIRECT) == (False, (20,), (1,))      # one second early
    now[0] = 7199                                                 # exactly 3,600 s after it
    assert local.take(budget.DIRECT) == (True, (20,), (1,))
    now[0] += 3600
    assert local.take((("lb:v:next", 20),)) == (True, (1,), (3600,))  # expired key dropped, slot reused


def test_rev1_bucket_burst_is_refused_twenty_in_any_hour():
    """Rev 1 forgot an entry 55-60 minutes on: 20 at 4:59 and 20 at 60:00 got 40 in 55:01."""
    now = [299]
    local = windows.LocalWindow(4, lambda: now[0])
    for _ in range(20):
        assert local.take(budget.DIRECT)[0]
    for t in (3300, 3600, 3898):
        now[0] = t
        assert local.take(budget.DIRECT) == (False, (20,), (299 + 3600 - t,))
    now[0] = 3899
    assert local.take(budget.DIRECT).allowed


def test_retry_after_is_the_largest_wait_among_exhausted_keys():
    now = [0]
    local = windows.LocalWindow(64, lambda: now[0])
    visitor, address = ("lb:v:a", 20), ("lb:ip:a", 60)
    for _ in range(40):                       # other visitors fill the address first
        now[0] += 1
        assert local.take((("lb:v:other%d" % now[0], 20), address)).allowed
    now[0] = 1000
    for _ in range(20):
        assert local.take((visitor, address)).allowed
    result = local.take((visitor, address))
    assert result == (False, (20, 60), (3600, 2601))   # visitor frees at 4600, address at 3601


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


# ── Codex re-review of #290: the actual bounds, measured ────────────────────

def test_the_limiter_client_is_its_own_with_250ms_waits_and_no_retries():
    from api import cache
    client = windows._redis()
    kwargs = client.connection_pool.connection_kwargs
    assert kwargs["socket_connect_timeout"] == 0.25 and kwargs["socket_timeout"] == 0.25
    assert client.get_retry()._retries == 0
    assert client is not cache.get_redis()


@pytest.fixture
def silent_redis(monkeypatch):
    """A TCP server that accepts and never answers: every read times out."""
    import socket
    import threading
    from api.settings import settings
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(16)
    accepted = []

    def accept():
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            accepted.append(conn)

    threading.Thread(target=accept, daemon=True).start()
    monkeypatch.setattr(settings, "REDIS_URL", f"redis://127.0.0.1:{server.getsockname()[1]}/0")
    yield accepted
    server.close()
    for conn in accepted:
        conn.close()


def test_an_unanswering_store_costs_about_half_a_second_then_the_breaker_skips_it(silent_redis):
    import time as clock
    clock_now = [100.0]
    started = clock.monotonic()
    with pytest.raises(Exception):
        windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0])
    elapsed = clock.monotonic() - started
    # Connect is instant here, so this is the 250 ms read timeout. With any
    # retry it would be at least 0.5 s more; the ~500 ms total is 250 ms
    # connect plus 250 ms read, and the connect half is pinned by the test above.
    assert 0.2 <= elapsed < 0.5, elapsed
    connections = len(silent_redis)

    started = clock.monotonic()
    with pytest.raises(windows.LimiterUnavailable):
        windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0] + 29.9)
    assert clock.monotonic() - started < 0.05            # breaker open: no wait at all
    assert len(silent_redis) == connections               # and no connection attempt

    clock_now[0] += 30.1                                  # breaker expired: one more try
    with pytest.raises(Exception) as tried:
        windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0])
    assert not isinstance(tried.value, windows.LimiterUnavailable)


# ── Codex #315 P2: at breaker expiry, ONE half-open probe, not one per caller ──

class SlowStore:
    """A store that takes `delay` seconds per call, then fails or answers."""

    def __init__(self, delay=0.2, fail=True):
        import threading
        self.calls, self.delay, self.fail = 0, delay, fail
        self.lock = threading.Lock()

    def eval(self, *_args):
        import time as clock
        with self.lock:
            self.calls += 1
        clock.sleep(self.delay)
        if self.fail:
            raise ConnectionError("store still down")
        n = (len(_args) - 3) // 2          # keys: (n + 1) - SEQ_KEY; see _TAKE
        return [1] + [1] * n + [3600] * n


def expired_breaker(clock_now):
    windows._breaker.settle(False, False, clock_now[0])     # a failure: open for 30 s
    clock_now[0] += windows.BREAKER_S + 0.1                 # now half-open


def race(n, fn):
    import threading
    barrier, results = threading.Barrier(n), []

    def run():
        barrier.wait()
        try:
            results.append(fn())
        except Exception as exc:  # noqa: BLE001
            results.append(exc)

    threads = [threading.Thread(target=run) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(5)
    return results


def test_at_breaker_expiry_ten_simultaneous_callers_send_one_probe(monkeypatch):
    store, clock_now = SlowStore(fail=True), [100.0]
    monkeypatch.setattr(windows, "_redis", lambda: store)
    expired_breaker(clock_now)
    results = race(10, lambda: windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0]))
    assert store.calls == 1, f"{store.calls} callers probed Redis"
    refused = [r for r in results if isinstance(r, windows.LimiterUnavailable)]
    assert len(refused) == 9                                # everyone else used the fallback
    # The probe failed: open for another 30 s, so the next caller is refused at once.
    with pytest.raises(windows.LimiterUnavailable):
        windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0] + 1)
    assert store.calls == 1


def test_a_successful_probe_closes_the_breaker_for_everyone(monkeypatch):
    store, clock_now = SlowStore(delay=0.05, fail=False), [100.0]
    monkeypatch.setattr(windows, "_redis", lambda: store)
    expired_breaker(clock_now)
    first = race(10, lambda: windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0]))
    assert store.calls == 1 and sum(isinstance(r, windows.WindowResult) for r in first) == 1
    after = race(10, lambda: windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0]))
    assert store.calls == 11                                # closed: every caller uses Redis
    assert all(isinstance(r, windows.WindowResult) for r in after)


def test_a_probe_that_raises_never_leaves_the_breaker_stuck_half_open(monkeypatch):
    clock_now = [100.0]

    def broken():
        raise RuntimeError("client construction failed")

    monkeypatch.setattr(windows, "_redis", broken)
    expired_breaker(clock_now)
    with pytest.raises(RuntimeError):
        windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0])
    assert windows._breaker.probing is False
    store = SlowStore(delay=0, fail=False)
    monkeypatch.setattr(windows, "_redis", lambda: store)
    clock_now[0] += windows.BREAKER_S + 0.1                 # the next window gets a probe
    assert windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0]).allowed
    assert store.calls == 1


def test_simultaneous_callers_open_one_connection_to_a_store_that_never_answers(silent_redis):
    clock_now = [100.0]
    expired_breaker(clock_now)
    before = len(silent_redis)
    results = race(10, lambda: windows.take_shared(budget.DIRECT, clock=lambda: clock_now[0]))
    import time as clock
    clock.sleep(0.1)                                        # let the accept thread record it
    assert len(silent_redis) - before <= 1
    assert sum(isinstance(r, windows.LimiterUnavailable) for r in results) == 9


def test_the_fallback_cap_counts_keys_not_visitors(signed):
    """4,096 keys. A signed visitor with their own address needs two (visitor, address)."""
    local = windows.LocalWindow(4096, lambda: 0)
    first = budget.request_limits(signed(0, "10.0.0.0"))
    for _ in range(20):
        assert local.take(first).allowed
    admitted = 1
    for n in range(1, 2100):
        limits = budget.request_limits(signed(n, f"10.{n // 65536}.{n // 256 % 256}.{n % 256}"))
        result = local.take(limits)
        assert len(local.windows) <= 4096
        if not result.allowed:
            assert result.waits == ()                     # refused for capacity: lookup_busy
            break
        admitted += 1
    assert admitted == 2048 and len(local.windows) == 4096
    assert local.take(first) == (False, (20, 20), (3600, 3600))   # visitor 1's count was not reset
    assert len(local.windows) == 4096


def test_a_full_fallback_still_admits_known_keys_and_refuses_new_ones(signed):
    local = windows.LocalWindow(4, lambda: 0)
    a, b = budget.request_limits(signed(1, "192.0.2.1")), budget.request_limits(signed(2, "192.0.2.2"))
    assert local.take(a).allowed and local.take(b).allowed           # 4 keys: full
    assert local.take(budget.request_limits(signed(3, "192.0.2.3"))) == (False, (0, 0), ())
    assert local.take(a).allowed                                      # existing keys keep working


def test_concurrent_final_slot_with_the_store_down_admits_exactly_one():
    window = windows.LocalWindow(4096, lambda: 0)
    for _ in range(19):
        assert window.take(budget.DIRECT).allowed
    import threading
    barrier = threading.Barrier(10)

    def race(_):
        barrier.wait()
        return window.take(budget.DIRECT).allowed

    with ThreadPoolExecutor(10) as pool:
        assert sum(pool.map(race, range(10))) == 1


async def test_a_store_outage_goes_to_the_bounded_fallback_without_waiting_again(silent_redis, monkeypatch, caplog):
    import time as clock
    monkeypatch.setattr(budget, "_request_fallback", windows.LocalWindow(4096, lambda: 0))
    caplog.set_level(logging.INFO, logger=budget.logger.name)
    await budget.check_request(request())                 # pays the ~0.25 s once, opens the breaker
    started = clock.monotonic()
    for _ in range(25):
        await budget.check_request(request())
    assert clock.monotonic() - started < 0.5              # 25 decisions without touching the store
    degraded = [m for m in caplog.messages if m.startswith("LOOKUP_LIMITER_DEGRADED stage=direct")]
    assert len(degraded) == 26 and degraded[-1].endswith("would-refuse counts=(20,)")
