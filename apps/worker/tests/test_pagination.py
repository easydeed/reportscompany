"""
Pagination stops on a fact, not on an inference.

D-080 — THE CASE NOBODY WOULD THINK TO WRITE
--------------------------------------------
`fetch_properties` used to stop when a page came back SHORTER than it asked
for. That infers the end of the data from a page's size, and it is right for
every total except one: when the total is an exact multiple of the page size,
no page is ever short. The loop advanced past the end and asked for one more,
and SimplyRETS answers that with

    HTTP 400 {"error":"InvalidArguments","errors":["offset too high"]}

not an empty list. `_request_with_retries` re-raises 4xx, so the exception left
the fetch and failed the whole report generation. **Not a truncated report: no
report** — and it presents as an unexplained failure rather than a wrong
number, so it would be chased as a transient.

Reproduced against the live feed before it was fixed, by replaying the loop's
own arithmetic with 65 rows and a page size of 65.

D-081 — A COUNT IS NOT A LIST
-----------------------------
Months of supply divides total inventory by a sales rate. It never needed the
listings. `?count=true` returns the exact total in `X-Total-Count` on a single
`limit=1` request, which removes D-078's ceiling rather than raising it — and
costs fewer calls than paging, so latency and the per-process rate bucket stop
being the constraints.

The same header is what makes D-080's stop condition exact, which is why the
two are one change.

WHAT THESE TESTS ARE
--------------------
Behavioural. The transport is replaced with a fake feed that reproduces what
the real one does — including the 400 — so the loop is exercised rather than
read. That is the difference between a test that would have caught this and the
AST assertions elsewhere in this suite, which would not have.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.vendors import simplyrets  # noqa: E402


class FakeResponse:
    def __init__(self, rows, total=None):
        self._rows = rows
        self.headers = {} if total is None else {"X-Total-Count": str(total)}

    def json(self):
        return self._rows


class FakeFeed:
    """
    A stand-in for /properties that behaves the way the real one was measured
    to behave: honours limit/offset, returns `X-Total-Count` only when
    `count=true` is asked for, and **raises on an offset past the end** rather
    than returning nothing.
    """

    def __init__(self, total, *, supports_count=True):
        self.total = total
        self.supports_count = supports_count
        self.calls = []

    def __call__(self, client, path, params):
        self.calls.append(dict(params))
        offset = int(params.get("offset", 0))
        limit = int(params.get("limit", 500))
        if offset >= self.total and self.total > 0:
            raise RuntimeError(
                'HTTP 400 {"error":"InvalidArguments","errors":["offset too high"]}'
            )
        rows = [{"mlsId": i} for i in range(offset, min(offset + limit, self.total))]
        wants_count = str(params.get("count", "")).lower() == "true"
        total = self.total if (wants_count and self.supports_count) else None
        return FakeResponse(rows, total)


@pytest.fixture
def feed(monkeypatch):
    def install(total, *, supports_count=True):
        fake = FakeFeed(total, supports_count=supports_count)
        monkeypatch.setattr(simplyrets, "_request_with_retries", fake)
        monkeypatch.setattr(simplyrets, "_client", lambda: _NullClient())
        return fake
    return install


class _NullClient:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# ── the boundary (D-080) ────────────────────────────────────────────────────

@pytest.mark.parametrize("total", [500, 1000, 1500])
def test_an_exact_multiple_of_the_page_size_does_not_blow_up(feed, total):
    """
    THE REGRESSION. Every one of these totals leaves no short page, so the old
    stop condition never fired and the loop asked for an offset past the end.
    """
    feed(total)
    rows = simplyrets.fetch_properties({"status": "Active"}, limit=2000)
    assert len(rows) == total, (
        f"expected {total} rows for a feed holding exactly {total}, got {len(rows)}"
    )


@pytest.mark.parametrize("total", [0, 1, 499, 501, 999, 1001])
def test_totals_that_are_not_on_the_boundary_still_work(feed, total):
    """The fix must not break the case that already worked."""
    feed(total)
    rows = simplyrets.fetch_properties({"status": "Active"}, limit=2000)
    assert len(rows) == total


def test_the_loop_never_requests_an_offset_it_cannot_know_is_valid(feed):
    """
    Asserted on the REQUESTS, not only on the result. A `try/except` around the
    400 would also make the test above pass while still making the doomed
    request — and would treat a genuine argument error as end-of-data.
    """
    fake = feed(1000)
    simplyrets.fetch_properties({"status": "Active"}, limit=2000)
    offsets = [int(c.get("offset", 0)) for c in fake.calls]
    assert max(offsets) < 1000, (
        f"the loop requested offset {max(offsets)} against a 1000-row feed; "
        f"the real API answers that with HTTP 400, not an empty page"
    )


def test_a_feed_without_the_count_header_still_terminates(feed):
    """
    The stop condition prefers the total but must not depend on it. Without the
    header the short-page rule still applies — the boundary case returns to
    being possible on such a feed, which is a property of the feed, not a
    regression here.
    """
    fake = feed(750, supports_count=False)
    rows = simplyrets.fetch_properties({"status": "Active"}, limit=2000)
    assert len(rows) == 750
    assert all("X-Total-Count" not in FakeResponse([], None).headers for _ in [0])


# ── the count (D-081) ───────────────────────────────────────────────────────

def test_count_properties_returns_the_total_without_fetching_the_rows(feed):
    fake = feed(4321)
    assert simplyrets.count_properties({"status": "Active"}) == 4321
    assert len(fake.calls) == 1, "counting should take exactly one request"
    assert int(fake.calls[0]["limit"]) == 1, "counting should not fetch rows"
    assert str(fake.calls[0]["count"]).lower() == "true"


def test_the_count_is_exact_far_above_any_paging_limit(feed):
    """
    THE POINT OF D-081. 12,000 active listings is twelve times the fetch limit
    that made D-078 fire; the count is unaffected by it.
    """
    feed(12000)
    assert simplyrets.count_properties({"status": "Active"}) == 12000


def test_count_properties_returns_none_when_the_feed_does_not_say(feed):
    """
    None, not 0. They are different facts, and a caller that read "the feed did
    not say" as "there are none" would compute months of supply from a zero it
    invented — which is D-056's failure with a new cause.
    """
    feed(900, supports_count=False)
    assert simplyrets.count_properties({"status": "Active"}) is None


def test_the_first_page_asks_for_the_count_and_later_pages_do_not(feed):
    """
    One extra parameter on one request. Asking on every page would be harmless
    but wasteful, and the loop only needs the answer once.
    """
    fake = feed(1200)
    simplyrets.fetch_properties({"status": "Active"}, limit=2000)
    asked = [str(c.get("count", "")).lower() == "true" for c in fake.calls]
    assert asked[0] is True, "the first page does not ask for the total"
    assert not any(asked[1:]), "later pages ask for the total again"


def test_a_truncated_fetch_is_reported(feed, caplog):
    """
    The caller has to be able to tell a complete set from a capped one — that
    is what months of supply refuses to publish on.
    """
    feed(5000)
    rows = simplyrets.fetch_properties({"status": "Active"}, limit=1000)
    assert len(rows) == 1000
    assert any("truncated" in r.message or "truncated" in r.getMessage()
               for r in caplog.records), "a truncated fetch is silent"
