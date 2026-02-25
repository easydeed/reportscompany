# Module: SiteX Pro API Service

> `apps/api/src/api/services/sitex.py`

---

## Purpose

Integrates with the **SiteX Pro** property assessor/recorder REST API to look up subject property data by address or APN.
Used as the **first step** in the property report wizard — the frontend sends an address, and SiteX returns structured property characteristics (beds, baths, sqft, APN, owner, assessed value, legal description, county FIPS, property type UseCode).

The resulting `UseCode` is critical: it drives the `property_type` field used by the comparables route to select the correct SimplyRETS `type` + `subtype` filters.

---

## Inputs / Outputs

### `SiteXClient` (class, singleton)

Manages OAuth2 token lifecycle (client credentials grant).

| Field | Type | Notes |
|-------|------|-------|
| `token` | `str\|None` | Current bearer token |
| `token_expires_at` | `datetime\|None` | Expiry; refreshed at 9-minute mark (TTL = 10 min) |

### `search_by_address(address: str, city: str, state: str, zip: str) → PropertyData | None`

| Direction | Field | Notes |
|-----------|-------|-------|
| In | Full address components | Street address, city, state, ZIP |
| Out | `PropertyData` | Normalised property data (or `None` if not found) |
| Out | Multi-match error | Raises `MultiMatchError` if SiteX returns >1 result |

### `search_by_apn(fips: str, apn: str) → PropertyData | None`

Most precise lookup method.

| Direction | Field | Notes |
|-----------|-------|-------|
| In | `fips` | County FIPS code (5 digits) |
| In | `apn` | Assessor's Parcel Number |
| Out | `PropertyData` | Normalised property data (or `None`) |

---

## Key Functions / Classes

| Name | Description |
|------|-------------|
| `SiteXClient.__init__` | Initialises token state; reads credentials from settings |
| `SiteXClient._refresh_token` | POSTs OAuth2 `client_credentials` grant, caches token + expiry |
| `SiteXClient._get_headers` | Returns `Authorization: Bearer <token>` header, auto-refreshing if needed |
| `SiteXClient.search_by_address` | `GET /v2/property/search?address=...` |
| `SiteXClient.search_by_apn` | `GET /v2/property/search?fips=...&apn=...` |
| `SiteXClient._parse_response` | Extracts `PropertyCharacteristics`, `OwnerInformation`, `AssessmentTaxInfo` from raw API response |
| `normalize_sitex` (module-level) | Converts `_parse_response` output → `PropertyData` Pydantic model |

### Critical Field Mappings

| SiteX Field | PropertyData Field | Notes |
|-------------|--------------------|-------|
| `PropertyCharacteristics.UseCode` | `property_type` | Drives SimplyRETS type selection |
| `PropertyCharacteristics.LivingArea` | `sqft` | Living square footage |
| `PropertyCharacteristics.Bedrooms` | `beds` | Bedroom count |
| `PropertyCharacteristics.TotalBaths` | `baths` | Total bathrooms (full + half) |
| `AssessmentTaxInfo.TotalAssessedValue` | `assessed_value` | Tax assessed value |
| `OwnerInformation.OwnerName` | `owner_name` | Current owner name |
| `PropertyCharacteristics.YearBuilt` | `year_built` | Construction year |
| `PropertyCharacteristics.LotSize` | `lot_size` | Lot size (sq ft) |
| `PropertyCharacteristics.LegalDescription` | `legal_description` | Legal parcel description |

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `apps/api/src/api/settings.py` | `SITEX_CLIENT_ID`, `SITEX_CLIENT_SECRET` |
| `apps/api/src/api/schemas/property.py` | `PropertyData` Pydantic model |

### External
| Library / Service | Usage |
|---|---|
| `httpx` (async) | HTTP client |
| SiteX Pro REST API | `https://api.sitexpro.com/v2/property/search` |
| OAuth2 token endpoint | `https://api.sitexpro.com/oauth/token` (client credentials) |

---

## Caching

| Cache Type | TTL | Key |
|------------|-----|-----|
| In-memory (`dict`) | 24 hours | `f"{address}:{city}:{state}:{zip}"` for address; `f"{fips}:{apn}"` for APN |
| Token cache | 9 minutes effective (10 min TTL) | Singleton instance variable |

Caching is in-process only; does **not** use Redis. A process restart clears all cached lookups.

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| HTTP 401 (bad token) | Attempts one token refresh then raises `HTTPException(503)` |
| No results | Returns `None` — wizard shows "property not found" state |
| Multiple results | Raises `MultiMatchError` — frontend should prompt for APN search |
| Token refresh failure | Raises `SiteXAuthError` → `HTTPException(503)` |
| Network timeout | Raises `httpx.TimeoutException` → caller logs + `HTTPException(504)` |
| Missing optional field | `_parse_response` uses `.get()` with `None` defaults; never raises on missing fields |

---

## Tests / How to Validate

```bash
# Smoke test against live SiteX API (requires credentials in .env)
python scripts/test_sitex.py
# Tests: 714 Vine St, Anaheim, CA 92805 — prints all property fields

# Integration test: full property search flow
python scripts/test_property_report_flow.py
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01 | Added 24-hour in-memory cache for address + APN lookups |
| 2025-12 | Added `search_by_apn()` for higher-precision lookup |
| 2025-11 | Initial implementation with `search_by_address()` and OAuth2 token management |
