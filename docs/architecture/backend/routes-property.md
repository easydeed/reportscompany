# Property API

> Property search, comparables, property report CRUD, stats, preview, and public landing pages.
> File: `apps/api/src/api/routes/property.py`

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /v1/property/search | Search property by address | Required |
| POST | /v1/property/search-by-apn | Search by FIPS + APN | Required |
| POST | /v1/property/comparables | Get comparable properties | Required |
| GET | /v1/property/stats | Agent property report stats | Required |
| GET | /v1/property/stats/affiliate | Affiliate aggregate stats | Required (Affiliate only) |
| POST | /v1/property/preview | Generate live HTML preview | Required |
| POST | /v1/property/reports | Create property report | Required |
| GET | /v1/property/reports | List property reports | Required |
| GET | /v1/property/reports/{id} | Get report detail | Required |
| DELETE | /v1/property/reports/{id} | Delete report | Required |
| GET | /v1/property/reports/{id}/settings | Get landing page settings | Required |
| PATCH | /v1/property/reports/{id}/settings | Update landing page settings | Required |
| POST | /v1/property/reports/{id}/regenerate-qr | Regenerate QR + short code | Required |
| GET | /v1/property/public/{short_code} | Public landing page data | Public |

## Key Functions

### POST /v1/property/search
- Uses SiteX Pro API via `services/sitex.py`
- Returns `PropertySearchResponse` with full property data (APN, owner, characteristics, tax)
- Handles multi-match (returns multiple locations for UI picker)

### POST /v1/property/comparables
- Uses SimplyRETS API via `services/simplyrets.py`
- Filters: SQFT variance (+/- percentage), radius (Haversine distance), bed/bath range, property type
- Post-filters by geographic distance if lat/lng available
- Returns comparables sorted by distance with search metadata

### POST /v1/property/reports
1. Checks plan limits via `check_property_report_limits()`
2. Uses provided `sitex_data` or looks up via SiteX
3. Generates 8-char short_code (auto via DB trigger or manual)
4. Generates QR code and uploads to R2 via `qr_service.py`
5. Inserts into `property_reports` table
6. Enqueues PDF generation via `enqueue_property_report()`
- Returns `{id, status, short_code, qr_code_url, property_address, report_type, created_at}`

### POST /v1/property/preview
- Imports `PropertyReportBuilder` from worker service
- Renders HTML preview with provided theme, colors, property data, and comparables
- Returns HTML response for iframe display in wizard Step 3

### GET /v1/property/public/{short_code}
- **Public endpoint** (no auth)
- Checks landing page controls: is_active, expires_at, max_leads
- Increments view_count
- Fetches agent info and branding
- Returns property data + agent info + branding for landing page rendering

### PATCH /v1/property/reports/{id}/settings
- Updates landing page controls: is_active, expires_at, max_leads, access_code

### POST /v1/property/reports/{id}/regenerate-qr
- Generates new 8-char short_code
- Regenerates QR code with report accent_color
- **Warning:** Invalidates existing QR code and short link

## Dependencies
- `services/sitex.py`: `lookup_property()`, `lookup_property_by_apn()`
- `services/simplyrets.py`: `fetch_properties()`, `build_comparables_params()`, `normalize_listing()`
- `services/qr_service.py`: `generate_qr_code()`
- `services/property_stats.py`: `get_agent_stats()`, `get_affiliate_stats()`
- `worker_client.py`: `enqueue_property_report()`

## Related Files
- Frontend: `/app/property` (list), `/app/property/new` (wizard), `/app/property/[id]` (detail)
- Frontend public: `/p/[code]` (landing page)
- Worker: `property_tasks/property_report.py` processes PDF generation
