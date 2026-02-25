# Module: Property Routes — Comparables & Subject Lookup

> `apps/api/src/api/routes/property.py`

---

## Purpose

Implements the **property-report API surface**: subject property lookup (via SiteX), comparable search (via SimplyRETS with a 6-level fallback ladder), and property-report management endpoints. This is the core orchestration layer that connects the wizard frontend to the data vendors.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/v1/property/search` | Bearer JWT | Look up subject property by street address |
| `POST` | `/v1/property/search-by-apn` | Bearer JWT | Look up subject property by FIPS + APN (high precision) |
| `POST` | `/v1/property/comparables` | Bearer JWT | Fetch comparable listings with fallback ladder |
| `POST` | `/v1/property/reports` | Bearer JWT | Create a property report record |
| `GET` | `/v1/property/reports` | Bearer JWT | List property reports for account |
| `GET` | `/v1/property/reports/{id}` | Bearer JWT | Get single property report |
| `PUT` | `/v1/property/reports/{id}` | Bearer JWT | Update property report (pages, comps, status) |
| `DELETE` | `/v1/property/reports/{id}` | Bearer JWT | Delete property report |
| `POST` | `/v1/property/reports/{id}/generate` | Bearer JWT | Enqueue PDF generation task |
| `GET` | `/v1/property/stats` | Bearer JWT | Property report usage stats (agent/affiliate/admin) |

---

## Comparables Fallback Ladder (L0 – L5)

The `POST /v1/property/comparables` endpoint implements a progressive relaxation strategy to always return the best available results, even in thin markets.

### Property Type Mapping

Before querying SimplyRETS, the subject's `property_type` (SiteX `UseCode`) is mapped to a SimplyRETS `(type, subtype)` pair via `PROPERTY_TYPE_MAP`:

| SiteX UseCode | SimplyRETS type | SimplyRETS subtype |
|---------------|-----------------|--------------------|
| `sfr`, `rsfr`, `single family`, `single family residence` | `residential` | `SingleFamilyResidence` |
| `condo`, `condominium` | `residential` | `Condominium` |
| `townhouse`, `th`, `town house` | `residential` | `Townhouse` |
| `duplex` | `residential` | `Duplex` |
| `triplex` | `residential` | `Triplex` |
| `quadruplex`, `four-plex` | `residential` | `Quadruplex` |
| `mobile`, `manufactured` | `residential` | `ManufacturedHome` |
| `multi-family`, `multifamily` | `multifamily` | _(none)_ |
| `land` | `land` | _(none)_ |
| `commercial` | `commercial` | _(none)_ |
| _(default / unknown)_ | `residential` | `SingleFamilyResidence` |

### Ladder Levels

| Level | sqft tolerance | radius | beds tolerance | subtype | Target results |
|-------|---------------|--------|----------------|---------|----------------|
| **L0** | ±20% (base) | base | exact | included | ≥5 |
| **L1** | ±20% | base | exact | **removed** | ≥5 |
| **L2** | **±30%** | base | exact | removed | ≥5 |
| **L3** | **±50%** | base | **±1** | removed | ≥5 |
| **L4** | **none** | base | **±2** | removed | ≥5 |
| **L5** | none | **×3** | ±2 | removed | ≥5 |

- At each level, results are **post-filtered** by property type to maintain consistency.
- The engine **tracks the best results seen** across all levels. If a later (looser) level returns fewer matches than an earlier level, the earlier results are returned.
- The ladder stops as soon as `≥5` results are found (or L5 is exhausted).

### Confidence Grades

| Grade | Condition |
|-------|-----------|
| `A` | L0 returned ≥5 results (strict match) |
| `B` | L1–L2 used (sqft/subtype relaxed) |
| `C` | L3–L4 used (beds + sqft relaxed) |
| `D` | L5 used or <3 results total (thin market) |

### Post-Filter Rules

After each SimplyRETS call, results are filtered to enforce property type consistency:

| property_type | Allowed SimplyRETS subtypes |
|---------------|-----------------------------|
| SFR | `SingleFamilyResidence`, `null`, `""` |
| Condo | `Condominium`, `StockCooperative` |
| Townhouse | `Townhouse` |
| Duplex | `Duplex` |
| Triplex | `Triplex` |
| Quadruplex | `Quadruplex` |
| Mobile/Manufactured | `ManufacturedHome`, `ManufacturedOnLand` |
| Multi-Family | `Duplex`, `Triplex`, `Quadruplex` |

---

## Key Functions / Classes

| Name | Description |
|------|-------------|
| `search_property` | Calls `SiteXClient.search_by_address()`, returns `PropertyData` |
| `search_by_apn` | Calls `SiteXClient.search_by_apn()`, returns `PropertyData` |
| `get_comparables` | Implements full fallback ladder; calls `simplyrets.fetch_properties()` at each level |
| `_post_filter_by_property_type` | Enforces subtype consistency on each ladder result set |
| `_haversine_distance` | Computes great-circle distance (miles) for distance filtering |
| `_grade_confidence` | Returns `A`/`B`/`C`/`D` based on ladder level reached |
| `create_property_report` | Inserts property report record; enforces plan limits |
| `generate_property_report` | Enqueues Celery task `generate_property_report_task` |

---

## Inputs / Outputs

### `POST /v1/property/comparables`

**Request body:**
```json
{
  "property_type": "sfr",
  "city": "La Verne",
  "sqft": 1850,
  "beds": 3,
  "baths": 2.0,
  "lat": 34.1003,
  "lng": -117.7678,
  "sqft_tolerance": 0.20,
  "radius_miles": 1.5,
  "status": ["Active", "Closed"],
  "max_results": 20
}
```

**Response:**
```json
{
  "comparables": [...],
  "confidence": "A",
  "ladder_level_used": 0,
  "total_found": 12,
  "filtered_count": 12
}
```

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `services/simplyrets.py` | Fetch comparable listings |
| `services/sitex.py` | Fetch subject property data |
| `services/property_stats.py` | Property report statistics |
| `schemas/property.py` | `PropertyData`, `ComparableData` models |
| `auth.py` | JWT validation |
| `worker_client.py` | Celery task enqueueing |
| `db.py` | PostgreSQL connection |

### External
| Service | Usage |
|---------|-------|
| SimplyRETS API | Comparable listings |
| SiteX Pro API | Subject property data |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| SiteX returns no results | `HTTP 404` with `"property_not_found"` code |
| SiteX multiple matches | `HTTP 422` with `"multiple_matches"` + prompt to use APN search |
| All 6 ladder levels exhausted with 0 results | Returns `confidence: "D"`, empty `comparables: []` |
| SimplyRETS 429 rate limit | `HTTP 429` propagated to client |
| Invalid `property_type` | Defaults to `residential`/`SingleFamilyResidence` |
| Plan limit exceeded | `HTTP 429` from `limit_checker`; report creation blocked |

---

## Tests / How to Validate

```bash
# Full property report flow test
python scripts/test_property_report_flow.py

# Test SimplyRETS queries (underlying service)
python scripts/test_simplyrets.py

# Template rendering tests (downstream)
pytest tests/test_property_templates.py -v
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02 | Added `sqft_tolerance` and `radius_miles` as request params (user-controllable via UI pills) |
| 2026-02 | Fixed post-filter applied at every ladder level (previously only applied to L0) |
| 2026-02 | Fixed "best results" tracking — result set never shrinks across ladder levels |
| 2026-01 | Added 6-level fallback ladder replacing simple single-query approach |
| 2026-01 | Added confidence grading (A/B/C/D) |
| 2025-12 | Initial property routes module |
