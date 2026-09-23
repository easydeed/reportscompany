"""
D-095 — a cache key must depend on what the payload means, not on typing order.

THE DEFECT
----------
`cache._key` hashed `json.dumps(payload)` with no `sort_keys`. Python dicts
preserve insertion order, so the same logical payload written two ways produced
two different keys:

    {"city": "Glendora", "month": "2026-09"}
    {"month": "2026-09", "city": "Glendora"}

The consequence is the quiet kind: a **silent 100% miss rate** between the two
call sites. No error, no warning — a cache that never hits, work done twice, and
a vendor bill that looks like the cache was never installed. Same family as
every other defect on this board that returns a plausible answer instead of
raising.

WHY IT IS FIXED NOW RATHER THAN WHEN IT BITES
---------------------------------------------
It was harmless: the only live payload (`{"type": report_type, "params": params}`,
tasks.py:1311) is built in exactly one place, so both sides always agreed.

The §7.3 rate-limit analysis then recommended caching 12-month bucket counts on
`(city, month)` — shared across twelve report types, which means several call
sites constructing the same two-key dict. That is exactly the shape that trips
this, and it would have presented as "the bucket cache does nothing" rather than
as a bug in the cache.

WHAT CHANGING IT COSTS
----------------------
Every existing key changes, so the report cache is cold after deploy. That is
safe precisely because a cache miss has no correctness consequence — the orphans
expire on their own TTL and the next request refills. Worth stating because "we
changed all the keys" sounds alarming and is the cheapest part of this.
"""
import os
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.cache import _key, safe_json_dumps  # noqa: E402


def test_key_order_does_not_change_the_key():
    """
    THE REGRESSION, at the exact shape the bucket cache would use.
    """
    a = _key("closed_buckets", {"city": "Glendora", "month": "2026-09"})
    b = _key("closed_buckets", {"month": "2026-09", "city": "Glendora"})
    assert a == b, (
        "two identical payloads written in different key order produced "
        "different cache keys — every lookup from one call site misses every "
        "write from the other, silently"
    )


def test_it_holds_for_nested_payloads():
    """
    The live payload is `{"type": …, "params": {…}}`, so the nesting is where
    this actually has to work. `sort_keys` applies at every level; asserted
    rather than assumed, because a fix that only sorted the top level would
    pass the test above and still miss on the real shape.
    """
    a = _key("report", {"type": "inventory",
                        "params": {"city": "Glendora", "lookback_days": 30, "zips": []}})
    b = _key("report", {"params": {"zips": [], "lookback_days": 30, "city": "Glendora"},
                        "type": "inventory"})
    assert a == b


def test_different_payloads_still_get_different_keys():
    """
    THE GUARD ON THE FIX. Sorting must not collapse distinct payloads — a key
    function that returns one value for everything would pass every test above
    and destroy the cache.
    """
    base = {"city": "Glendora", "month": "2026-09"}
    assert _key("closed_buckets", base) != _key("closed_buckets",
                                                {"city": "Glendora", "month": "2026-10"})
    assert _key("closed_buckets", base) != _key("closed_buckets",
                                                {"city": "La Verne", "month": "2026-09"})
    # and the namespace still separates
    assert _key("closed_buckets", base) != _key("report", base)


def test_list_order_is_still_significant():
    """
    `sort_keys` sorts mapping keys, not sequence elements — and it should not.
    `["91750", "91711"]` and `["91711", "91750"]` are the same SET of ZIPs but
    the code does not treat them as interchangeable anywhere, so the cache must
    not either. Pinned so nobody later "improves" this into sorting values.
    """
    a = _key("report", {"zips": ["91750", "91711"]})
    b = _key("report", {"zips": ["91711", "91750"]})
    assert a != b


def test_datetimes_still_serialise():
    """
    `safe_json_dumps` exists because payloads carry dates; adding `sort_keys`
    must not disturb the `default=` handler that makes them serialisable.
    """
    k = _key("report", {"as_of": date(2026, 9, 23), "run_at": datetime(2026, 9, 23, 10, 0)})
    assert k.startswith("mr:report:")


def test_the_value_serialiser_is_left_unsorted_by_default():
    """
    `sort_keys` is opt-in, and `set()` does not opt in. The stored blob's field
    order is cosmetic, and sorting it would rewrite every cached value for no
    benefit — a bigger change than the one this defect needed.
    """
    assert safe_json_dumps({"b": 1, "a": 2}) == '{"b": 1, "a": 2}'
    assert safe_json_dumps({"b": 1, "a": 2}, sort_keys=True) == '{"a": 2, "b": 1}'
