import os, time, math
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
    - params: SimplyRETS query params (e.g., {'q':'San Diego','status':'Active,Pending,Closed',...})
    - limit: safety limit across pages (defaults to SIMPLYRETS_MAX_RESULTS)
    Returns a list of property dicts.
    """
    out: List[Dict] = []
    offset = 0
    page_max = 500
    total_limit = limit or MAX_RESULTS
    with _client() as c:
        while True:
            page_size = min(page_max, total_limit - len(out))
            if page_size <= 0:
                break
            q = {**params, "limit": page_size, "offset": offset}
            resp = _request_with_retries(c, "/properties", q)
            batch = resp.json()
            if not batch:
                break
            out.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
            if len(out) >= total_limit:
                break
    return out

# Convenience: a tiny helper for Market Snapshot queries
def build_market_snapshot_params(city: str, lookback_days: int = 30) -> Dict:
    # docs: /properties with q=<city>, status Active,Pending,Closed, mindate/maxdate, sort -listDate
    # dates leave as YYYY-MM-DD
    from datetime import datetime, timedelta
    end = datetime.utcnow().date()
    start = end - timedelta(days=lookback_days)
    return {
        "q": city,
        "status": "Active,Pending,Closed",
        "mindate": start.isoformat(),
        "maxdate": end.isoformat(),
        "sort": "-listDate",
    }









