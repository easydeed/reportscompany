# Module: SimplyRETS API Service (API Layer)

> `apps/api/src/api/services/simplyrets.py`

---

## Purpose

Provides the **API-layer** SimplyRETS client used by property-report routes to search for comparable listings.
This is distinct from the worker-layer vendor (`apps/worker/src/worker/vendors/simplyrets.py`), which is used by background Celery tasks.

The service builds structured query parameters from property attributes, executes authenticated requests to the SimplyRETS REST API, and normalises raw responses into a consistent `PropertyData` schema.

---

## Inputs / Outputs

### `fetch_properties(params: dict) → list[dict]`

| Direction | Field | Type | Notes |
|-----------|-------|------|-------|
| In | `params` | `dict` | SimplyRETS query parameters (see `build_comparables_params`) |
| Out | listings | `list[dict]` | Raw SimplyRETS listing objects, each normalised to `PropertyData` shape |

### `build_comparables_params(subject: dict, options: dict) → dict`

| Direction | Field | Type | Notes |
|-----------|-------|------|-------|
| In | `subject.city` | `str` | City to filter by |
| In | `subject.sqft` | `int` | Subject living area |
| In | `subject.beds` | `int` | Beds filter |
| In | `subject.baths` | `float` | Baths filter |
| In | `options.sqft_tolerance` | `float` | Fraction variance e.g. `0.20` for ±20 % |
| In | `options.type` | `str` | SimplyRETS listing type e.g. `"residential"` |
| In | `options.subtype` | `str\|None` | SimplyRETS subtype e.g. `"singlefamilyresidence"` |
| In | `options.radius` | `float\|None` | Search radius in miles |
| Out | params | `dict` | Query string parameters ready for SimplyRETS |

### `normalize_listing(raw: dict) → dict`

Converts raw SimplyRETS API response to a uniform property shape consumed by the property report builder.

---

## Key Functions / Classes

| Name | Signature | Description |
|------|-----------|-------------|
| `fetch_properties` | `async (params) → list` | HTTP GET to `https://api.simplyrets.com/properties` with Basic Auth |
| `build_comparables_params` | `(subject, options) → dict` | Assembles SimplyRETS query parameters from subject + options |
| `normalize_listing` | `(raw) → dict` | Maps API fields → `PropertyData` schema (lat, lng, price, sqft, beds, baths, etc.) |

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `apps/api/src/api/settings.py` | `SIMPLYRETS_API_KEY`, `SIMPLYRETS_API_SECRET` credentials |
| `apps/api/src/api/schemas/property.py` | `PropertyData` Pydantic model for normalised output |

### External
| Library / Service | Usage |
|---|---|
| `httpx` (async) | HTTP client for SimplyRETS REST API |
| SimplyRETS REST API | `https://api.simplyrets.com/properties` — HTTP Basic Auth |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| Rate limit (HTTP 429) | Raises `HTTPException(429)` — caller (comparables route) logs and propagates |
| Timeout (>30 s) | Raises `httpx.TimeoutException` — treated as empty results by caller |
| Auth failure (HTTP 401) | Raises `HTTPException(503)` — misconfigured credentials |
| Empty result | Returns `[]` — comparables route records and advances to next ladder level |
| Missing field in response | `normalize_listing` uses `.get()` with safe defaults; never raises |

**Rate limit:** SimplyRETS enforces 60 RPM per credential pair with a burst allowance. The API layer does **not** implement a local rate limiter (unlike the worker vendor). If the comparables endpoint is called in rapid succession by the frontend, the 429 will propagate to the UI.

---

## Tests / How to Validate

```bash
# Smoke test: requires SIMPLYRETS_API_KEY + SIMPLYRETS_API_SECRET in env
python scripts/test_simplyrets.py

# Full property report flow test (includes comparables call)
python scripts/test_property_report_flow.py

# Unit tests (test_property_templates.py covers downstream consumers)
pytest tests/test_property_templates.py -v
```

See also: [`modules/cli-tools.md`](./cli-tools.md) for full CLI reference.

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02 | Added `sqft_tolerance` and `radius` options to `build_comparables_params`; tightened field mapping in `normalize_listing` for `lat`/`lng` variants |
| 2025-12 | Initial implementation — basic fetch + normalize |
