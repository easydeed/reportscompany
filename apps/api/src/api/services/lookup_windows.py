"""Atomic sliding-hour counters for LR-006 (design #290 rev 2, sections 3 and 5).

Only the `lb:*` namespace holds budget state.

THE WINDOW IS AN EXACT SLIDING HOUR. Each key is a log of admitted timestamps.
An admission removes entries at least 3,600 s old, counts the rest, and adds
`now` to every key only if all of them are below their limit. An admitted
request is therefore counted until exactly 3,600 s after it was admitted, and
no key ever holds more than its limit in any 3,600 s span. Rev 1's twelve
5-minute buckets ("current bucket plus the previous eleven") forgot an entry
55-60 minutes after admission, which allowed 40 lookups inside 60 minutes.
Only admitted requests are logged, so a key holds at most `limit` entries.

`waits[i]` is the number of seconds, rounded up, until key i's oldest entry
leaves the window: when a slot frees there. For an empty key it is the full
window, the reset an admission now would have.

Two stores, one algorithm:
  * Redis (shared across workers): one Lua script per admission, timed by
    the store's own clock (TIME, in microseconds), so every worker agrees.
    It uses a dedicated client with 250 ms connect and 250 ms read timeouts
    and no retries, about 500 ms in the worst case. The shared client in
    `cache.py` allows 2 s for each. After a failure, a breaker sends the
    process straight to the fallback for 30 s, so an outage does not add a
    timeout to every search. When the 30 s are up the breaker is HALF-OPEN:
    exactly one caller probes Redis while every other caller keeps using the
    fallback. Success closes the breaker; failure opens it for another 30 s.
    Without that, every request arriving at expiry would each spend up to
    ~500 ms on a store that is still down (Codex review of #315).
  * LocalWindow (the per-process fallback): the same window in memory,
    bounded in keys and entries, and locked.
"""
import math
import threading
import time
from collections import OrderedDict, deque
from typing import NamedTuple, Optional

WINDOW_SECONDS = 3600
WINDOW_US = WINDOW_SECONDS * 1_000_000
SEQ_KEY = "lb:seq"            # makes two admissions in one microsecond distinct
REDIS_TIMEOUT_S = 0.25        # connect, and separately read: ~0.5 s worst case
BREAKER_S = 30.0
Limits = tuple[tuple[str, int], ...]


class WindowResult(NamedTuple):
    allowed: bool
    counts: tuple[int, ...]
    # Seconds until each key's oldest counted entry leaves the window.
    waits: tuple[int, ...]


class LimiterUnavailable(RuntimeError):
    """The breaker is open: the shared store is skipped for now."""


# KEYS[1..n] are the budget keys, KEYS[n+1] the sequence key.
# ARGV[1] is the window in µs, ARGV[2..n+1] the limits.
_TAKE = """
if redis.replicate_commands then redis.replicate_commands() end
local window = tonumber(ARGV[1])
local t = redis.call('TIME')
local now = tonumber(t[1]) * 1000000 + tonumber(t[2])
local n = #KEYS - 1
local counts, waits, admit = {}, {}, 1
for i = 1, n do
    redis.call('ZREMRANGEBYSCORE', KEYS[i], '-inf', now - window)
    counts[i] = redis.call('ZCARD', KEYS[i])
    if counts[i] >= tonumber(ARGV[1 + i]) then admit = 0 end
end
if admit == 1 then
    local member = string.format('%.0f-%d', now, redis.call('INCR', KEYS[n + 1]))
    for i = 1, n do
        redis.call('ZADD', KEYS[i], now, member)
        redis.call('PEXPIRE', KEYS[i], math.floor(window / 1000))
        counts[i] = counts[i] + 1
    end
end
for i = 1, n do
    local oldest = redis.call('ZRANGE', KEYS[i], 0, 0, 'WITHSCORES')
    if oldest[2] then
        waits[i] = math.max(1, math.ceil((tonumber(oldest[2]) + window - now) / 1000000))
    else
        waits[i] = math.floor(window / 1000000)
    end
end
local out = {admit}
for i = 1, n do table.insert(out, counts[i]) end
for i = 1, n do table.insert(out, waits[i]) end
return out
"""

_client = None
_client_lock = threading.Lock()


class _Breaker:
    """Closed -> open (30 s) -> half-open (one probe) -> closed or open again.

    `admit()` decides, under one lock, whether this caller may use Redis:
      * closed: everyone may;
      * open: nobody may (LimiterUnavailable);
      * half-open: the first caller becomes the probe, everyone else is
        refused until the probe settles. `settle()` always runs for a probe,
        so a probe that raises can never leave the breaker stuck half-open.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.open_until = 0.0
        self.tripped = False        # a failure since the last success
        self.probing = False        # a half-open probe is in flight

    def admit(self, now: float) -> bool:
        """True if this caller is the half-open probe. Raises if refused."""
        with self.lock:
            if now < self.open_until:
                raise LimiterUnavailable("lookup limiter breaker open")
            if not self.tripped:
                return False
            if self.probing:
                raise LimiterUnavailable("lookup limiter breaker half-open; probe in flight")
            self.probing = True
            return True

    def settle(self, probe: bool, ok: bool, now: float) -> None:
        with self.lock:
            if ok:
                self.tripped = False
                self.open_until = 0.0
            else:
                self.tripped = True
                self.open_until = now + BREAKER_S
            if probe:
                self.probing = False


_breaker = _Breaker()


def _redis():
    """The limiter's own client: 250 ms connect, 250 ms read, no retries."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                import redis
                from redis.backoff import NoBackoff
                from redis.retry import Retry
                from ..settings import settings
                _client = redis.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=REDIS_TIMEOUT_S,
                    socket_timeout=REDIS_TIMEOUT_S,
                    retry_on_timeout=False,
                    retry=Retry(NoBackoff(), 0),
                )
    return _client


def take_shared(limits: Limits, clock=time.monotonic) -> WindowResult:
    breaker = _breaker
    probe = breaker.admit(clock())
    keys, ceilings = zip(*limits)
    ok = False
    try:
        admitted, *values = _redis().eval(_TAKE, len(keys) + 1, *keys, SEQ_KEY, WINDOW_US, *ceilings)
        ok = True
    finally:
        # Every outcome settles: a probe that raises frees the half-open slot.
        breaker.settle(probe, ok, clock())
    if admitted not in (0, 1) or len(values) != 2 * len(keys):
        raise ValueError("Invalid lookup budget response")
    return WindowResult(bool(admitted), tuple(values[:len(keys)]), tuple(values[len(keys):]))


class LocalWindow:
    """Process-local fallback: the same sliding hour, bounded, locked.

    At most `capacity` live keys, each with at most `limit` entries. Expired
    keys are dropped on every admission. A request that would need a key
    beyond the capacity is REFUSED: a live counter is never evicted, because
    eviction would reset someone's allowance. Prune, check and add run under
    one lock, so two threads cannot both take a key's last slot.
    """

    def __init__(self, capacity: int, clock=time.monotonic):
        self.capacity = capacity
        self.clock = clock
        self.lock = threading.Lock()
        # Ordered by last admission, so expired keys are always at the front.
        self.windows: "OrderedDict[str, deque]" = OrderedDict()

    def _waits(self, logs, now) -> tuple[int, ...]:
        return tuple(max(1, math.ceil(log[0] + WINDOW_SECONDS - now)) if log else WINDOW_SECONDS
                     for log in logs)

    def take(self, limits: Limits) -> WindowResult:
        with self.lock:
            now = self.clock()
            cutoff = now - WINDOW_SECONDS
            while self.windows:
                first = next(iter(self.windows.values()))
                if first and first[-1] > cutoff:
                    break
                self.windows.popitem(last=False)

            keys, ceilings = zip(*limits)
            logs: list[Optional[deque]] = []
            for key in keys:
                log = self.windows.get(key)
                while log and log[0] <= cutoff:
                    log.popleft()
                logs.append(log)
            counts = tuple(len(log) if log else 0 for log in logs)
            if any(n >= limit for n, limit in zip(counts, ceilings)):
                return WindowResult(False, counts, self._waits(logs, now))
            new_keys = {key for key in keys if key not in self.windows}
            if len(self.windows) + len(new_keys) > self.capacity:
                return WindowResult(False, counts, ())
            admitted = []
            for key, log in zip(keys, logs):
                if log is None:
                    log = deque()
                    self.windows[key] = log
                log.append(now)
                self.windows.move_to_end(key)
                admitted.append(log)
            return WindowResult(True, tuple(n + 1 for n in counts), self._waits(admitted, now))
