"""Atomic rolling counters for LR-006. Only the lb:* namespace holds budget state."""
import time
from collections import OrderedDict
from threading import Lock
from typing import NamedTuple

BUCKET_SECONDS = 300
BUCKETS = 12
TTL = (BUCKETS + 1) * BUCKET_SECONDS
Limits = tuple[tuple[str, int], ...]


class WindowResult(NamedTuple):
    allowed: bool
    counts: tuple[int, ...]
    # Seconds until the oldest counted bucket expires, in store clock time.
    waits: tuple[int, ...]


# Use the store's clock across workers. Each hash holds at most twelve
# bucket/count pairs. Inspect every limit before incrementing any of them.
_TAKE = """
if redis.replicate_commands then redis.replicate_commands() end
local width, slots, ttl = tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3])
local now = tonumber(redis.call('TIME')[1])
local bucket = math.floor(now / width)
local counts, expired, waits = {}, {}, {}
local admit = 1
for i, key in ipairs(KEYS) do
    local fields = redis.call('HGETALL', key)
    counts[i], expired[i] = 0, {}
    local oldest = bucket
    for j = 1, #fields, 2 do
        if tonumber(fields[j]) > bucket - slots then
            counts[i] = counts[i] + tonumber(fields[j + 1])
            oldest = math.min(oldest, tonumber(fields[j]))
        else
            table.insert(expired[i], fields[j])
        end
    end
    if counts[i] >= tonumber(ARGV[3 + i]) then admit = 0 end
    waits[i] = (oldest + slots) * width - now
end
if admit == 1 then
    for i, key in ipairs(KEYS) do
        for _, field in ipairs(expired[i]) do redis.call('HDEL', key, field) end
        redis.call('HINCRBY', key, bucket, 1)
        redis.call('EXPIRE', key, ttl)
        counts[i] = counts[i] + 1
    end
end
table.insert(counts, 1, admit)
for _, wait in ipairs(waits) do table.insert(counts, wait) end
return counts
"""


def take_shared(limits: Limits) -> WindowResult:
    from ..cache import get_redis

    keys, ceilings = zip(*limits)
    admitted, *values = get_redis().eval(
        _TAKE, len(keys), *keys, BUCKET_SECONDS, BUCKETS, TTL, *ceilings
    )
    if admitted not in (0, 1) or len(values) != 2 * len(keys):
        raise ValueError("Invalid lookup budget response")
    return WindowResult(bool(admitted), tuple(values[:len(keys)]), tuple(values[len(keys):]))


class LocalWindow:
    """Process-local fallback. Never evict a live counter to admit a new key."""

    def __init__(self, capacity: int, clock=time.monotonic):
        self.capacity = capacity
        self.clock = clock
        self.lock = Lock()
        self.windows: OrderedDict[str, dict[int, int]] = OrderedDict()

    def take(self, limits: Limits) -> WindowResult:
        with self.lock:
            now = int(self.clock())
            bucket = now // BUCKET_SECONDS
            cutoff = bucket - BUCKETS
            # Entries are ordered by last increment. Expired keys won't
            # occupy the cardinality budget when unrelated visitors arrive.
            while self.windows:
                oldest = next(iter(self.windows.values()))
                if max(oldest) > cutoff:
                    break
                self.windows.popitem(last=False)

            keys, ceilings = zip(*limits)
            active = [
                {b: n for b, n in self.windows.get(k, {}).items() if b > cutoff}
                for k in keys
            ]
            counts = tuple(sum(w.values()) for w in active)
            waits = tuple((min(w, default=bucket) + BUCKETS) * BUCKET_SECONDS - now for w in active)
            if any(n >= limit for n, limit in zip(counts, ceilings)):
                return WindowResult(False, counts, waits)
            if len(self.windows) + sum(k not in self.windows for k in keys) > self.capacity:
                return WindowResult(False, counts, ())
            for key, window in zip(keys, active):
                window[bucket] = window.get(bucket, 0) + 1
                self.windows[key] = window
                self.windows.move_to_end(key)
            return WindowResult(True, tuple(n + 1 for n in counts), waits)
