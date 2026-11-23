"""LR-006: the shared sliding hour, against real Redis (database 15).

Entries are seeded at scores relative to the store's own TIME, the clock the
script reads, so the boundaries are exact. CI provides Redis and sets
REQUIRE_REDIS_TESTS=1 (#322): there, a missing Redis fails instead of skipping.
"""
import os
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

redis = pytest.importorskip("redis")

from api.services import lookup_windows as windows  # noqa: E402

# An explicitly disposable Redis (TEST_REDIS_URL; CI sets it). Cleanup deletes
# only the keys these tests own, never the database (Codex review of #322).
URL = os.getenv("TEST_REDIS_URL")
HOUR_US = 3_600_000_000
V, IP = ("lb:v:test", 20), ("lb:ip:test", 60)


@pytest.fixture
def r(monkeypatch):
    from api.settings import settings
    if not URL:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is not set")
        pytest.skip("Set TEST_REDIS_URL to a disposable Redis database")
    conn = redis.from_url(URL)
    try:
        conn.ping()
    except redis.exceptions.ConnectionError:
        if os.getenv("REQUIRE_REDIS_TESTS") == "1":
            pytest.fail("REQUIRE_REDIS_TESTS=1 but TEST_REDIS_URL is unreachable")
        pytest.skip("TEST_REDIS_URL is unreachable")
    monkeypatch.setattr(settings, "REDIS_URL", URL)
    monkeypatch.setattr(windows, "_client", None, raising=False)
    monkeypatch.setattr(windows, "_breaker", windows._Breaker())
    owned = (V[0], IP[0], windows.SEQ_KEY)
    conn.delete(*owned)
    yield conn
    conn.delete(*owned)


def test_cleanup_leaves_unrelated_keys(r):
    r.set("unrelated:sentinel", "keep")
    try:
        windows.take_shared((V,))
        r.delete(V[0], IP[0], windows.SEQ_KEY)
        assert r.get("unrelated:sentinel") == b"keep"
    finally:
        r.delete("unrelated:sentinel")


def now_us(r):
    s, us = r.time()
    return s * 1_000_000 + us


def seed(r, key, count, age_s):
    at = now_us(r) - int(age_s * 1_000_000)
    r.zadd(key, {f"seed-{at}-{i}": at for i in range(count)})


@pytest.mark.parametrize("age_s, admitted", [(3599, False), (3600, True), (3601, True)])
def test_an_entry_counts_for_exactly_one_hour(r, age_s, admitted):
    seed(r, V[0], 20, age_s)
    assert windows.take_shared((V,)).allowed is admitted


def test_rev1s_minute_five_burst_is_refused(r):
    seed(r, V[0], 20, 3300)                       # bucket math forgot these after 55 minutes
    result = windows.take_shared((V,))
    assert result == (False, (20,), (300,))


def test_retry_after_inputs_are_each_keys_own_wait(r):
    seed(r, V[0], 20, 100)                        # frees in 3500 s
    seed(r, IP[0], 60, 3000)                      # frees in 600 s
    result = windows.take_shared((V, IP))
    assert not result.allowed and result.counts == (20, 60)
    assert result.waits[0] in (3500, 3501) and result.waits[1] in (600, 601)


def test_a_refusal_changes_nothing_on_any_key(r):
    seed(r, IP[0], 60, 10)
    assert not windows.take_shared((V, IP)).allowed
    assert r.zcard(V[0]) == 0 and r.zcard(IP[0]) == 60


def test_admission_adds_to_every_key_and_sets_an_hour_ttl(r):
    assert windows.take_shared((V, IP)) == (True, (1, 1), (3600, 3600))
    assert r.zcard(V[0]) == r.zcard(IP[0]) == 1
    assert 3_590_000 < r.pttl(V[0]) <= 3_600_000


def test_a_key_never_holds_more_than_its_limit(r):
    for _ in range(50):
        windows.take_shared((V,))
    assert r.zcard(V[0]) == 20


def test_two_admissions_in_quick_succession_are_two_entries(r):
    windows.take_shared((V,))
    windows.take_shared((V,))
    assert r.zcard(V[0]) == 2


def test_the_final_slot_goes_to_exactly_one_concurrent_caller(r):
    seed(r, V[0], 19, 10)
    barrier = threading.Barrier(10)

    def race(_):
        barrier.wait()
        return windows.take_shared((V,)).allowed

    with ThreadPoolExecutor(10) as pool:
        assert sum(pool.map(race, range(10))) == 1
    assert r.zcard(V[0]) == 20
