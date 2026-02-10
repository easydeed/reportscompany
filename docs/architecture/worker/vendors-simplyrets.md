# SimplyRETS Integration

> `apps/worker/src/worker/vendors/simplyrets.py` (131 lines)
> MLS data API client with rate limiting, pagination, and retry logic.

## Overview

SimplyRETS provides MLS (Multiple Listing Service) property data via a REST API.
The worker uses it to fetch listings for all market report types and consumer CMA reports.

## Authentication

Basic Auth using `SIMPLYRETS_USERNAME` and `SIMPLYRETS_PASSWORD`.
The credentials are base64-encoded and sent as an `Authorization: Basic <token>` header.

## Rate Limiting

Token-bucket rate limiter with a 60-second sliding window:

```python
class RateLimiter:
    def __init__(self, rpm=60, burst=10):
        self.window = 60.0
        self.rpm = rpm
        self.burst = burst
```

- **Default rate:** 60 requests per minute
- **Burst allowance:** 10 additional requests
- **Behavior:** If the window is full, the caller sleeps until a slot frees up
- Rate limiter is a singleton (`_limiter`) shared across all requests in the worker process

## fetch_properties()

Main data fetch function with automatic pagination.

```python
def fetch_properties(params: Dict, limit: Optional[int] = None) -> List[Dict]
```

**Parameters:**
- `params` -- SimplyRETS query parameters (e.g., `{'q': 'San Diego', 'status': 'Active,Pending,Closed'}`)
- `limit` -- Safety cap across all pages (default: `SIMPLYRETS_MAX_RESULTS`)

**Pagination logic:**
- Page size: 500 (SimplyRETS maximum)
- Fetches pages sequentially using offset-based pagination
- Stops when: empty page, page smaller than requested, or total limit reached

**Returns:** Flat list of property dictionaries from all pages.

## Retry Logic

`_request_with_retries()` handles transient failures:

| Condition | Action |
|-----------|--------|
| HTTP 429 (rate limited) | Sleep with exponential backoff (doubled each attempt), retry |
| HTTP 5xx (server error) | Sleep with exponential backoff, retry |
| Timeout | Sleep with exponential backoff, retry |
| HTTP 4xx (client error, except 429) | Raise immediately |
| Max retries exceeded (3) | One final attempt, then raise |

Backoff sequence: 1s, 2s, 4s (doubled on each retry).

## Convenience Helper

```python
def build_market_snapshot_params(city: str, lookback_days: int = 30) -> Dict
```

Builds a SimplyRETS query for market snapshot reports:
- `q` = city name
- `status` = `Active,Pending,Closed`
- `mindate` / `maxdate` = date range based on lookback_days
- `sort` = `-listDate` (newest first)

**Note:** SimplyRETS `mindate`/`maxdate` filter by `listDate`, not `closeDate`.
The worker applies additional client-side date filtering in the report builders.

## HTTP Client

Uses `httpx.Client` with:
- Base URL: `https://api.simplyrets.com` (configurable)
- Timeout: 25 seconds (configurable)
- JSON content type
- Connection pooling (context manager)

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SIMPLYRETS_BASE_URL` | API base URL | `https://api.simplyrets.com` |
| `SIMPLYRETS_USERNAME` | Basic Auth username | `simplyrets` |
| `SIMPLYRETS_PASSWORD` | Basic Auth password | `simplyrets` |
| `SIMPLYRETS_RPM` | Rate limit (requests per minute) | `60` |
| `SIMPLYRETS_BURST` | Burst allowance above RPM | `10` |
| `SIMPLYRETS_TIMEOUT_S` | HTTP timeout in seconds | `25` |
| `SIMPLYRETS_MAX_RESULTS` | Max results safety cap | `1000` |

## Data Flow

```
query_builders.py         -- Build SimplyRETS query params from report config
  -> vendors/simplyrets.py  -- Fetch raw property data with pagination + rate limiting
    -> compute/extract.py   -- PropertyDataExtractor normalizes raw MLS data
      -> compute/validate.py -- Filter out invalid listings
        -> report_builders.py -- Build structured report JSON
```
