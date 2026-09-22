import os, time, math, logging
from collections import deque
from typing import Dict, List, Optional
import base64
import httpx

BASE = os.getenv("SIMPLYRETS_BASE_URL", "https://api.simplyrets.com")
USER = os.getenv("SIMPLYRETS_USERNAME", "simplyrets")
PASS = os.getenv("SIMPLYRETS_PASSWORD", "simplyrets")
RPM  = int(os.getenv("SIMPLYRETS_RPM", "60"))
BURST = int(os.getenv("SIMPLYRETS_BURST", "10"))
TIMEOUT = float(os.getenv("SIMPLYRETS_TIMEOUT_S", "25"))
MAX_RESULTS = int(os.getenv("SIMPLYRETS_MAX_RESULTS", "1000"))

logger = logging.getLogger(__name__)

AUTH = "Basic " + base64.b64encode(f"{USER}:{PASS}".encode()).decode()

class RateLimiter:
    """
    Token-bucket-ish limiter: keep a minute window (docs: 60 rpm + burst).
    """
    def __init__(self, rpm: int = 60, burst: int = 10):
        self.window = 60.0
        self.rpm = rpm
        self.burst = burst
        self.times = deque()

    def acquire(self):
        now = time.time()
        # purge old
        while self.times and (now - self.times[0]) > self.window:
            self.times.popleft()
        # hard cap: rpm; soft burst allowance
        if len(self.times) >= max(self.rpm, self.burst):
            wait = self.window - (now - self.times[0])
            if wait > 0:
                time.sleep(wait)
        self.times.append(time.time())

_limiter = RateLimiter(RPM, BURST)

def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE,
        headers={
            "Authorization": AUTH,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=TIMEOUT
    )

def _request_with_retries(c: httpx.Client, path: str, params: Dict, max_retries: int = 3):
    backoff = 1.0
    for attempt in range(max_retries + 1):
        _limiter.acquire()
        try:
            resp = c.get(path, params=params)
            if resp.status_code == 429:
                # rate limited — exponential backoff
                time.sleep(backoff * 2)
                backoff *= 2
                continue
            if 500 <= resp.status_code < 600:
                time.sleep(backoff)
                backoff *= 2
                continue
            resp.raise_for_status()
            return resp
        except httpx.TimeoutException:
            time.sleep(backoff)
            backoff *= 2
        except httpx.HTTPError:
            raise
    # final try
    r = c.get(path, params=params)
    r.raise_for_status()
    return r

def fetch_properties(params: Dict, limit: Optional[int] = None) -> List[Dict]:
    """
    GET /properties with paging.
    - params: SimplyRETS query params (e.g., {'q':'San Diego','status':['Active','Pending','Closed'],...})
    - limit: safety limit across pages (defaults to SIMPLYRETS_MAX_RESULTS)
    Returns a list of property dicts.

    MULTI-VALUE PARAMETERS MUST BE LISTS, NOT COMMA-SEPARATED STRINGS (D-076).
    This docstring used to show the comma form, and it does not work:

        status='Active,Closed'      -> status=Active%2CClosed  -> 42 rows, Active ONLY
        status=['Active','Closed']  -> status=Active&status=Closed -> 55 rows, both

    Measured against api.simplyrets.com. The comma form returns HTTP 200 and
    silently discards everything after the first value — no error, no warning,
    just a smaller answer than the one asked for. A caller computing a ratio
    across statuses gets a denominator of zero and no indication why. That is
    D-056's failure mode arriving through the transport layer.

    httpx expands a list value into repeated parameters, which is what the API
    wants. Anything passing several values here must pass a list.
    """
    out: List[Dict] = []
    offset = 0
    page_max = 500
    total_limit = limit or MAX_RESULTS
    available: Optional[int] = None

    with _client() as c:
        while True:
            page_size = min(page_max, total_limit - len(out))
            if page_size <= 0:
                break

            q = {**params, "limit": page_size, "offset": offset}
            if available is None:
                # Ask for the total on the FIRST page only. It is what makes
                # the stop condition below exact — see D-080.
                q["count"] = "true"

            resp = _request_with_retries(c, "/properties", q)
            if available is None:
                available = _total_count(resp)

            batch = resp.json()
            if not batch:
                break
            out.extend(batch)

            # ── THE STOP CONDITION (D-080) ──────────────────────────────────
            #
            # This used to be "stop when a page comes back shorter than asked
            # for", which infers the end of the data from a page's size. When
            # the total is an EXACT MULTIPLE of the page size, no page is ever
            # short: the loop advanced past the end and asked for one more, and
            # SimplyRETS answers that with
            #
            #     HTTP 400 {"error":"InvalidArguments",
            #               "errors":["offset too high"]}
            #
            # — not an empty list. `_request_with_retries` re-raises 4xx, so the
            # exception propagated out of the fetch and failed the whole report
            # generation. Not a truncated report: no report. Reproduced against
            # the live feed with 65 rows and a page size of 65.
            #
            # The fix is to stop on a fact rather than on an inference. When the
            # feed tells us how many rows exist, that is the terminator and the
            # boundary case cannot arise.
            #
            # NOT a try/except around the 400: that would treat a genuine
            # argument error — a malformed filter, a bad date — as a normal end
            # of data, and the report would silently come back short.
            if available is not None and offset + len(batch) >= available:
                break
            if len(batch) < page_size:
                break

            offset += page_size
            if len(out) >= total_limit:
                break

    if available is not None and available > len(out):
        logger.warning(
            "fetch_properties: %d rows available, %d fetched (limit %d) — the "
            "caller is seeing a truncated set",
            available, len(out), total_limit,
        )
    return out


def _total_count(resp) -> Optional[int]:
    """
    The exact number of rows matching a query, from `X-Total-Count`.

    Returned only when the request carries `count=true` — measured: absent on
    four other query shapes, present with that parameter. It is listed in the
    feed's own `Access-Control-Expose-Headers`.
    """
    raw = resp.headers.get("X-Total-Count")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        logger.warning("fetch_properties: unparseable X-Total-Count %r", raw)
        return None


def count_properties(params: Dict) -> Optional[int]:
    """
    How many properties match, WITHOUT fetching them. Returns None if the feed
    does not say.

    D-081. Months of supply needs a COUNT of active inventory, not the
    listings. The inventory report used to page up to 1000 listings to get one,
    and refused to publish a figure when it hit that limit (D-078) — so a large
    market, the one most likely to have both plenty of sales and more than a
    thousand listings, was told it had too few sales.

    One request, `limit=1`, and the answer is exact at any size. That removes
    the ceiling rather than raising it, and costs FEWER calls than paging, not
    more — so the latency and the per-process rate bucket stop being the
    constraints they were.

    Returns None rather than 0 when the header is absent, because those are
    different facts and a caller that treats "the feed did not say" as "there
    are none" would compute months of supply from a zero it invented.
    """
    q = {**params, "limit": 1, "offset": 0, "count": "true"}
    with _client() as c:
        resp = _request_with_retries(c, "/properties", q)
        return _total_count(resp)


def count_properties_if_exact(params: Dict) -> Optional[int]:
    """
    `count_properties`, but only when counting the query answers the question.

    D-087. `count=true` replies with `X-Total-Count` — one number covering
    everything the API matched. Rows from a fuzzy query get cleaned afterwards
    by `_filter_by_city`; a number cannot be. So when the location filter is
    `q=<city>` (free-text: measured, `q=Houston` matches 13 where
    `cities=Houston` matches 12, the extra being a Tomball listing), the count
    is a count of a DIFFERENT population than the rows beside it.

    Returning None here is not a failure signal and not a fallback to zero — it
    is the same "the feed did not say" that the missing-header case already
    produces, and callers already handle it by falling back to the city-filtered
    row count with a truncation flag. A floor that announces itself beats an
    exact count of the wrong thing.

    No request is sent in the fuzzy case, so this costs a call rather than
    adding one.
    """
    from ..query_builders import location_is_exact

    if not location_is_exact(params):
        return None
    return count_properties(params)

# Convenience: a tiny helper for Market Snapshot queries
def build_market_snapshot_params(city: str, lookback_days: int = 30) -> Dict:
    """
    Reached only by two ad-hoc scripts (`apps/worker/test_pipeline.py`,
    `test_simplyrets.py`), not by the production path — `query_builders.py`
    builds its own, one status at a time. Fixed anyway, because it was the
    documented idiom and the next multi-status query would have copied it.

    Two corrections, both measured rather than read (D-075, D-076):

      status  a list, so httpx emits `status=Active&status=Pending&...`.
              The comma string it used before came back with Active only.

      dates   `mindate`/`maxdate` did nothing at all — `mindate=2030-01-01`
              returned every row. Callers must filter client-side, which the
              production report builders already do. Left in place rather than
              removed, because whether they work is a property of the feed and
              the production probe has not come back; the comment is the
              warning.
    """
    # docs: /properties with q=<city>, status Active/Pending/Closed, sort -listDate
    # dates leave as YYYY-MM-DD
    from datetime import datetime, timedelta
    end = datetime.utcnow().date()
    start = end - timedelta(days=lookback_days)
    return {
        "q": city,
        "status": ["Active", "Pending", "Closed"],
        "mindate": start.isoformat(),   # see D-075 — may be ignored by the feed
        "maxdate": end.isoformat(),     # see D-075 — may be ignored by the feed
        "sort": "-listDate",
    }










