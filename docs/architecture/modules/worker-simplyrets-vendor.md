# Module: Worker SimplyRETS Vendor

> `apps/worker/src/worker/vendors/simplyrets.py`

---

## Purpose

Provides the **worker-layer** (synchronous) SimplyRETS client used by Celery background tasks during market report and schedule generation.

This is distinct from the API-layer service (`apps/api/src/api/services/simplyrets.py`). The worker variant:
- Is **synchronous** (blocking HTTP calls inside Celery tasks)
- Implements a **token-bucket rate limiter** (60 RPM, burst 10)
- Supports **pagination** (up to 500 listings per page, follows `Link` headers)
- Has **retry logic** with exponential back-off for 429 and 5xx errors

---

## Inputs / Outputs

### `fetch_properties(params: dict, paginate: bool = True) → list[dict]`

| Direction | Field | Type | Notes |
|-----------|-------|------|-------|
| In | `params` | `dict` | SimplyRETS query parameters |
| In | `paginate` | `bool` | If `True`, follows `Link: rel=next` headers to collect all pages |
| Out | listings | `list[dict]` | Raw SimplyRETS listing objects |

### `build_market_snapshot_params(filters: dict) → dict`

Constructs SimplyRETS query parameters for market snapshot queries. Used by schedule/market report tasks.

| Direction | Field | Notes |
|-----------|-------|-------|
| In | `filters.city` | City name |
| In | `filters.type` | SimplyRETS listing type |
| In | `filters.minprice` / `maxprice` | Price range |
| In | `filters.minbeds` / `minbaths` | Bed/bath minimums |
| In | `filters.status` | `["Active"]` or `["Closed"]` |
| Out | params | Ready-to-send query dict |

---

## Key Functions / Classes

### `RateLimiter` (class)

Token-bucket rate limiter.

| Attribute | Value |
|-----------|-------|
| Rate | 60 requests/minute |
| Burst | 10 tokens |
| Storage | Thread-local (in-process only) |

```python
limiter = RateLimiter(rate=60, burst=10)
limiter.acquire()  # Blocks until token available
```

### `fetch_properties(params, paginate=True)`

1. Acquires rate-limit token
2. `GET https://api.simplyrets.com/properties` with Basic Auth
3. If response is HTTP 429: exponential back-off (1s → 2s → 4s, max 3 retries)
4. If `paginate=True`: reads `X-Total-Count` + `Link` headers, fetches subsequent pages
5. Returns combined list

### `build_market_snapshot_params(filters)`

Builds the query parameter dict. Does **not** validate inputs; expects caller (filter_resolver) to provide clean values.

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `apps/worker/src/worker/filter_resolver.py` | Provides `filters` dict consumed by `build_market_snapshot_params` |
| Worker task context | Called from Celery tasks in `tasks.py` |

### External
| Library / Service | Usage |
|---|---|
| `requests` (sync) | HTTP client |
| `threading.local` | Thread-safe rate limiter state |
| SimplyRETS REST API | `https://api.simplyrets.com/properties` — HTTP Basic Auth |

---

## Pagination Strategy

SimplyRETS returns at most **500 listings per page**. For large markets, the vendor follows `Link: <url>; rel="next"` response headers automatically when `paginate=True`.

| Header | Usage |
|--------|-------|
| `X-Total-Count` | Total listing count (used for progress logging) |
| `Link` | Next page URL when more results exist |

Market snapshot tasks typically set `limit=500&offset=0` and allow the vendor to auto-paginate.

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| HTTP 429 (rate limit) | Exponential back-off: 1 s → 2 s → 4 s, then raises `SimplyRETSRateLimitError` |
| HTTP 5xx | Retry up to 3 times, then raises `SimplyRETSServerError` |
| HTTP 401 (bad credentials) | Raises `SimplyRETSAuthError` immediately (no retry) |
| Empty result | Returns `[]` (not an error) |
| Pagination loop (>50 pages) | Safety circuit breaker — raises `SimplyRETSPaginationError` |

---

## Tests / How to Validate

```bash
# Direct SimplyRETS vendor test (worker layer)
python scripts/test_simplyrets.py
# Also indirectly tested by full report generation
python scripts/test_all_reports.py

# Market report flow test
python scripts/test_report_flow.py
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01 | Added `RateLimiter` class (token-bucket, 60 RPM + 10 burst) |
| 2025-12 | Added pagination support with `Link` header following |
| 2025-11 | Added retry logic with exponential back-off for 429/5xx |
| 2025-10 | Initial implementation |
