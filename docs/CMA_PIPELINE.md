# CMA Pipeline — Architecture & Data Reference

> Last updated: March 2026 (commits `323d5be`→`965908b`)

## Overview

The CMA (Comparative Market Analysis) pipeline generates branded property reports for homeowners who visit an agent's lead page (`/cma/{agent_code}`). It is separate from the property wizard pipeline (which agents use to manually build reports).

**Key difference:** The property wizard lets agents manually select comps and pick themes. The CMA pipeline auto-selects everything — comps are fetched from SimplyRETS, branding comes from the agent's account, and the report is generated and delivered without human intervention.

---

## Data Flow

```
[Consumer enters address on /cma/{agent_code}]
        │
        ▼
[Google Places Autocomplete → parsed address]
        │
        ▼
[POST /v1/cma/{code}/search → SiteX lookup]
  Returns: address, beds, baths, sqft, year_built,
           latitude, longitude, property_type
        │
        ▼
[Consumer confirms property, enters phone/email]
        │
        ▼
[POST /v1/cma/{code}/request → creates consumer_reports row, queues Celery task]
  Stores in property_data JSONB: all SiteX fields including lat/lng, property_type
        │
        ▼
[Worker: process_consumer_report]
  1. Fetch comps from SimplyRETS (fallback ladder)
  2. Post-filter by property type
  3. Compute market stats + value estimate
  4. Fetch agent branding from accounts table
  5. Build report_data_for_pdf → PropertyReportBuilder → HTML → PDF
  6. Upload PDF to R2
  7. Store comps, stats, estimate in consumer_reports
  8. Deliver via SMS/email
  9. Notify agent via SMS
        │
        ▼
[Consumer views report at /r/{report_id}]
  - MobileReportViewer (React) ← /v1/r/{report_id}/data (mobile_reports.py)
  - PDF download available
```

---

## Files Involved

| File | Role |
|------|------|
| `apps/web/app/cma/[code]/cma-funnel.tsx` | Consumer-facing funnel UI |
| `apps/api/src/api/routes/lead_pages.py` | API: property search + report request |
| `apps/api/src/api/routes/mobile_reports.py` | API: serves report JSON to MobileReportViewer |
| `apps/worker/src/worker/tasks.py` | Worker: `process_consumer_report` Celery task |
| `apps/worker/src/worker/property_builder.py` | Renders HTML from report data dict |
| `apps/worker/src/worker/vendors/simplyrets.py` | SimplyRETS API wrapper |
| `apps/web/components/mobile-report/MobileReportViewer.tsx` | Consumer report viewer UI |

---

## Canonical Comparable Format

The worker normalizes SimplyRETS responses into this dict format. This is stored in `consumer_reports.comparables` JSONB and consumed by **both** the PDF builder and the mobile viewer API.

```python
{
    "mls_id": str,
    "address": str,           # e.g. "123 Main St"
    "city": str,
    "state": str,
    "zip_code": str,
    "price": int,             # closePrice preferred, fallback listPrice
    "list_price": int | None,
    "close_price": int | None,
    "bedrooms": int,
    "bathrooms": int,
    "sqft": int,
    "year_built": int | None,
    "lot_size": int | None,
    "photo_url": str | None,  # first MLS photo
    "photos": list[str],
    "status": str,            # "Closed"
    "dom": int | None,        # days on market from MLS
    "days_on_market": int | None,
    "list_date": str | None,  # ISO date
    "close_date": str | None, # ISO date (e.g. "2025-11-15T00:00:00Z")
    "lat": float | None,
    "lng": float | None,
    "distance_miles": float | None,  # haversine from subject
}
```

### Field Consumers

| Consumer | How it reads fields |
|----------|-------------------|
| **PropertyReportBuilder** (`_build_comparables_context`) | Handles aliases: `price` / `close_price` / `sale_price`; `close_date` / `sold_date`; `sqft` / `living_area`. Computes `price_per_sqft` from price/sqft. |
| **mobile_reports.py** (`get_report_data`) | Maps to Pydantic `Comparable` model. Computes derived values: `sold_price` ← `price`, `sold_date` ← formatted `close_date`, `days_ago` ← computed from `close_date`, `price_per_sqft` ← `price / sqft`, `distance_miles` ← passthrough. |
| **MobileReportViewer.tsx** | Renders `sold_date` (formatted date), `distance_miles`, `price_per_sqft`, `sold_price`. Gracefully handles zeros with "—" fallback. |

---

## SimplyRETS Query Strategy

### Parameters (built by `_cma_params` in tasks.py)

```python
{
    "type": sr_type,        # from _resolve_simplyrets_type() — usually "residential"
    "status": "Closed",     # ALWAYS Closed for CMA
    "postalCodes": zip,
    "cities": city,
    "subtype": sr_subtype,  # e.g. "SingleFamilyResidence" (conditional)
    "minbeds" / "maxbeds",  # subject ± 1
    "minarea" / "maxarea",  # subject ± 25%
    "limit": 50,
}
```

### Fallback Ladder

If fewer than 3 results, relaxes filters progressively:

| Level | Filters Applied |
|-------|----------------|
| L0: strict | type + subtype + beds + sqft |
| L1: no-subtype | type + beds + sqft |
| L2: no-sqft | type + beds only |
| L3: no-filters | type only (broadest) |

### Property Type Mapping

`_resolve_simplyrets_type(sitex_use_code)` converts SiteX UseCode to SimplyRETS parameters:

| SiteX UseCode | SimplyRETS type | SimplyRETS subtype |
|--------------|----------------|-------------------|
| Single Family / SFR | residential | SingleFamilyResidence |
| Condominium / Condo | residential | Condominium |
| Townhouse | residential | Townhouse |
| Multi-Family / Duplex / Triplex / Fourplex | residential | MultiFamily |
| Mobile / Manufactured Home | residential | MobileManufactured |
| *(default/unknown)* | residential | *(none)* |

### Post-Filtering

`_post_filter_by_property_type(listings, sr_subtype)` filters results after fetch to exclude mismatched property types. Uses `_POST_FILTER_ALLOWED_SUBTYPES` mapping to handle variations (e.g., "Detached" is allowed for SFR).

---

## Distance Calculation

Uses haversine formula (exact same as `POST /v1/property/comparables` in property.py):

- Subject lat/lng comes from `property_data.latitude` / `property_data.longitude`
- Comp lat/lng comes from SimplyRETS `geo.lat` / `geo.lng`
- If either is missing, `distance_miles` is `None`
- The mobile viewer shows "—" when distance is 0 or null

**Important:** Lat/lng must flow from SiteX → frontend → API → consumer_reports.property_data for distances to work. This flow was established in commit `4ad73da`.

---

## Value Estimate

Computed from comparables:

1. If subject sqft and avg_price_per_sqft are available: `estimated = sqft * avg_ppsf`
   - Low: estimated * 0.92
   - Mid: estimated
   - High: estimated * 1.08
2. Fallback: uses average of comp prices ± half the price range
3. Confidence: "high" (5+ comps), "medium" (3-4 comps), "low" (< 3 comps)

---

## PDF Generation

Uses the same `PropertyReportBuilder` as the property wizard:

```python
report_data_for_pdf = {
    "report_type": "seller",
    "theme": default_theme_id,          # from accounts.default_theme_id
    "accent_color": secondary_color,    # from accounts.secondary_color
    "property_address", "property_city", "property_state", "property_zip",
    "owner_name",
    "sitex_data": { latitude, longitude, bedrooms, bathrooms, sqft, ... },
    "comparables": comparables[:6],     # top 6 comps
    "agent": { name, title, phone, email, license_number, photo_url, ... },
    "branding": { display_name, logo_url, primary_color, accent_color },
    "selected_pages": [
        "cover", "aerial", "property",
        "comparables", "range",
        "market_trends", "overview",
    ],
}
```

---

## Mobile Report Viewer

The `/r/{report_id}` page renders a consumer-facing interactive report. Data is served by `GET /v1/r/{report_id}/data` (mobile_reports.py).

### Field Mapping (mobile_reports.py → MobileReportViewer.tsx)

The API transforms the canonical comp format into the viewer's expected schema:

| Viewer Field | Source (canonical) | Computation |
|-------------|-------------------|-------------|
| `sold_price` | `price` or `close_price` | Direct map |
| `sold_date` | `close_date` | Formatted: "Mar 15, 2024" |
| `days_ago` | `close_date` | `(now - close_date).days` |
| `price_per_sqft` | `price` / `sqft` | Computed if not stored |
| `distance_miles` | `distance_miles` | Rounded to 1 decimal |

The viewer shows "—" for zero values (distance, price_per_sqft) instead of misleading zeros.

---

## Database: consumer_reports Table

Key JSONB columns:

| Column | Contents |
|--------|----------|
| `property_data` | SiteX data: address, beds, baths, sqft, lat, lng, property_type, owner_name |
| `comparables` | Array of canonical comp dicts (see format above) |
| `value_estimate` | `{low, mid, high, confidence}` |
| `market_stats` | `{median_price, avg_price_per_sqft, avg_days_on_market, total_sold_last_6mo}` |

---

## Known Limitations

1. **Distance requires lat/lng**: Reports created before the lat/lng fix (commit `4ad73da`) have `distance_miles: null`. Existing reports won't retroactively get distances.

2. **Email delivery is a no-op**: The email branch in `process_consumer_report` marks as "sent" but doesn't actually send an email yet (TODO: integrate Resend).

3. **No comp photos for old closed sales**: SimplyRETS often returns no photos for older closed listings. Fallback: Google Maps satellite thumbnail if comp has lat/lng.
