# Wizard Flow & External API Calls
## Property Reports + Market Reports

**TrendyReports.io — Internal Technical Reference**
*Last updated: February 24, 2026*

---

## Part 1 — Property Report Wizard

### Overview

The Property Report wizard lives at `/app/property/new` and is powered by the `PropertyWizard` React component (`apps/web/components/property-wizard/property-wizard.tsx`). It walks an agent through **4 steps** and produces a branded, multi-page seller CMA PDF.

---

### Step 1 — Property Search (SiteX Pro)

**What the agent sees:** Two text fields — Street Address and City/State/ZIP — with a Google Places Autocomplete hook wired to the street address field. Selecting a suggestion auto-fills both fields and immediately fires the search.

**What happens under the hood:**

1. The frontend posts to `POST /api/proxy/v1/property/search` with:
   ```
   { address: "714 Vine St", city_state_zip: "Anaheim, CA 92805" }
   ```

2. The API service (`apps/api/src/api/routes/property.py`) calls `lookup_property()` from `services/sitex.py`.

3. **SiteX Pro (ICE) is called:**
   - **Auth:** `POST /ls/apigwy/oauth2/v1/token` — OAuth2 client credentials flow using `SITEX_CLIENT_ID` and `SITEX_CLIENT_SECRET`. Token TTL is 10 minutes; a singleton `SiteXTokenManager` refreshes it at 9 minutes.
   - **Search:** `GET /realestatedata/search` — Authenticated with `Authorization: Bearer <token>`. Key query params:
     - `addr` = street address
     - `lastLine` = city/state/zip
     - `feedId` = feed identifier (e.g., `100001`)
     - `options` = `search_exclude_nonres=Y`
   - **Base URL:** Configured via `SITEX_BASE_URL` env var (UAT: `https://api.uat.bkitest.com`, Prod: production URL).

4. **SiteX returns property data** parsed into a `PropertyData` object:
   - Full address (street, city, state, zip, county)
   - APN (Assessor's Parcel Number) and FIPS code
   - Owner name and secondary owner
   - Legal description
   - Bedrooms, bathrooms, square footage, lot size, year built
   - Property type (UseCode, e.g., `SFR`, `Condo`)
   - Assessed value, tax amount, land/improvement values
   - Latitude & longitude coordinates
   - Results are cached in memory for 24 hours by address key.

5. **Multi-match handling:** If SiteX returns multiple properties, the API returns a `multiple_matches` list so the UI can display a disambiguation picker.

**Gate to next step:** Property must be found (`property !== null`).

---

### Step 2 — Sales Comparables (SimplyRETS)

**What the agent sees:** A list of comparable listings (cards with photo, address, beds/baths/sqft, price) with checkboxes. The agent must select **4–8 comps**. They can toggle between Active and Closed status.

**What happens under the hood:**

1. The frontend posts to `POST /api/proxy/v1/property/comparables` with the property data from Step 1:
   ```json
   {
     "address": "714 Vine St",
     "city_state_zip": "Anaheim, CA 92805",
     "latitude": 33.8294,
     "longitude": -117.9064,
     "beds": 3,
     "baths": 2,
     "sqft": 1450,
     "property_type": "SFR",
     "radius_miles": 0.5,
     "sqft_variance": 0.20,
     "status": "Active",
     "limit": 15
   }
   ```

2. **SimplyRETS is called** from the API service (`services/simplyrets.py`):
   - **Auth:** HTTP Basic Auth — `SIMPLYRETS_USERNAME` / `SIMPLYRETS_PASSWORD` env vars.
   - **Endpoint:** `GET https://api.simplyrets.com/properties`
   - **Query params built dynamically:**
     | Param | Value | Source |
     |---|---|---|
     | `type` | `residential` (or resolved from SiteX UseCode) | SiteX property_type mapping |
     | `subtype` | `SingleFamilyResidence`, `Condominium`, etc. | SiteX UseCode → PROPERTY_TYPE_MAP |
     | `status` | `Active` or `Closed` | User toggle |
     | `postalCodes` | ZIP code | Parsed from city_state_zip |
     | `q` | City name | Parsed from city_state_zip |
     | `minarea` / `maxarea` | sqft × (1 ± 0.20) | 20% variance from subject sqft |
     | `minbeds` / `maxbeds` | beds ± 1 | Subject beds |
     | `minbaths` / `maxbaths` | baths ± 1 | Subject baths |
     | `limit` | `payload.limit × 3` | Fetch extra for post-filtering |

3. **Post-filtering (server-side):**
   - **Distance filter:** Listings are filtered by haversine distance from the subject property's lat/lng. Default radius: 0.5 miles. Sorted by distance ascending.
   - **Property type filter:** A safety-net post-filter removes listings whose `property.subType` doesn't match allowed values for the requested subtype (e.g., SFR only gets `SingleFamilyResidence` and `Detached`).

4. **Response:** A list of normalized comparable dicts with MLS ID, address, price, beds/baths/sqft, photo URLs, DOM, and distance in miles.

**Gate to next step:** Exactly 4–8 comps selected.

---

### Step 3 — Theme & Pages

**What the agent sees:** 5 theme cards (Classic, Modern, Elegant, Teal, Bold), an accent color picker, and a checklist of report pages to include/exclude.

**Key details:**
- **Compact themes** (Teal, Bold): 8 core pages — `cover`, `contents`, `aerial`, `property`, `analysis`, `market_trends`, `comparables`, `range`.
- **Full themes** (Classic, Modern, Elegant): Same 8 core pages plus up to 12 extended pages (Introduction, Selling Roadmap, marketing sections, etc.) for future full-length reports.
- Required pages that cannot be deselected: **Property Details** (`property`) and **Sales Comparables** (`comparables`).
- A live preview is available via `POST /v1/property/preview` — renders the Jinja2 template server-side and returns HTML for the iframe.

> **⚠️ Page ID Contract:** The page `id` values sent in `selected_pages` **must exactly match** the keys used in the Jinja2 templates (`"property"`, not `"property_details"`; `"contents"`, not `"toc"`; `"analysis"`, not `"area_analysis"`). See `docs/architecture/modules/property-builder.md` for the full page key table.

**Gate to next step:** Theme selected (1–5), accent color set, required pages present.

---

### Step 4 — Generate

**What the agent sees:** An animated progress display while the report is built, then a success screen with a PDF download link and QR code.

**What happens under the hood:**

1. Frontend posts `POST /api/proxy/v1/property/reports` with all wizard state:
   - Address fields, theme, accent color, selected page IDs
   - `sitex_data` (full SiteX property data from Step 1)
   - `comparables` (the 4–8 selected comp objects from Step 2)

2. **API creates the DB record** (`property_reports` table) with status `draft`.

3. **QR code is generated** via `generate_qr_code()` — creates a colored QR pointing to `https://trendyreports.io/p/{short_code}`, uploaded to Cloudflare R2.

4. **Celery task is enqueued:** `enqueue_property_report(report_id)` → worker task `generate_property_report`.

5. **Worker generates the PDF:**
   - Fetches report + user/branding joins from DB.
   - `PropertyReportBuilder` renders the Jinja2 template (`templates/property/{theme}/`) with all property data, comps, and agent branding.
   - `render_pdf()` sends HTML to **PDFShift** for high-fidelity PDF conversion.
   - PDF uploaded to **Cloudflare R2** at `property-reports/{account_id}/{report_id}/`.
   - Report status updated to `complete`, `pdf_url` stored.

6. Frontend polls the report status until `complete`, then reveals the download link.

---

## Part 2 — Market Report Wizard

### Overview

The Market Report wizard lives at `/app/reports/new` and is powered by `ReportBuilderWizard` (`apps/web/components/v0-report-builder/report-builder.tsx`). It has **4 steps** and produces email-ready HTML/PDF market snapshots for a city or set of ZIP codes.

---

### Step 1 — Area

**What the agent sees:** A toggle between **City** (text input) or **ZIP Codes** (multi-tag input). The agent enters one city name or one or more ZIP codes.

**Gate to next step:** City name entered, OR at least one ZIP code added.

---

### Step 2 — Report Type

**What the agent sees:** Cards for each available report type:

| Report Type | What It Shows |
|---|---|
| Market Snapshot | Active + Closed + Pending summary metrics for the period |
| New Listings | Listings that came active within the lookback window |
| Closed Sales | Recently sold properties and price trends |
| Price Bands | Distribution of listings across price brackets |
| Inventory | Current active listings that became active in the window |
| Featured Listings | Curated listing gallery |
| Neighborhood / Market Trends | Trend lines over time |

**Gate to next step:** Report type selected.

---

### Step 3 — Timeframe

**What the agent sees:** Preset buttons for lookback window — **30 days**, **60 days**, **90 days**, **6 months**, **12 months**.

**Gate to next step:** Lookback days selected.

---

### Step 4 — Review & Generate

**What the agent sees:** A summary card showing area, report type, timeframe, and an estimated page count. A "Generate Report" button submits the job.

**What happens under the hood:**

1. Frontend posts `POST /v1/reports`:
   ```json
   {
     "report_type": "market_snapshot",
     "city": "Anaheim",
     "zips": ["92805", "92806"],
     "lookback_days": 30,
     "filters": { "type": "RES", "minprice": 400000 }
   }
   ```

2. **API checks monthly usage limits** (plan-based; returns HTTP 429 if exceeded).

3. **DB record created** in `report_generations` with status `pending`.

4. **Celery task enqueued:** `enqueue_generate_report(report_id, account_id, report_type, params)`.

5. **Worker fetches data from SimplyRETS** (`apps/worker/src/worker/vendors/simplyrets.py`):
   - **Auth:** HTTP Basic Auth — `SIMPLYRETS_USERNAME` / `SIMPLYRETS_PASSWORD`.
   - **Endpoint:** `GET https://api.simplyrets.com/properties`
   - **Query params** are built by `query_builders.py` — a dedicated builder function per report type:

   | Builder | Status | Date Filter | Sort |
   |---|---|---|---|
   | `build_market_snapshot` | Active | mindate/maxdate | — |
   | `build_market_snapshot_closed` | Closed | mindate/maxdate | — |
   | `build_market_snapshot_pending` | Pending | mindate/maxdate | — |
   | `build_new_listings` | Active | mindate/maxdate | `-listDate` (prod) |
   | `build_closed` | Closed | mindate/maxdate | `-closeDate` (prod) |
   | `build_inventory_by_zip` | Active | mindate/maxdate | `daysOnMarket` (prod) |

   - **Location:** ZIP codes → `postalCodes=92805,92806`; city → `q=Anaheim` (production credentials only).
   - **Filters:** `type=RES` (always, to exclude rentals), plus optional price range, beds, baths, subtype.
   - **Rate limiting:** Token-bucket limiter — 60 requests/minute with a burst of 10. Retries with exponential backoff on 429 or 5xx.
   - **Pagination:** Loops through 500-record pages until all results fetched (up to `SIMPLYRETS_MAX_RESULTS`, default 1000).

6. **Worker computes report metrics** (`compute/` module — `calc.py`, `extract.py`, `market_trends.py`) then **renders the Jinja2 HTML template** for the selected report type.

7. **PDF generated** (PDFShift) → **uploaded to Cloudflare R2** → `report_generations` record updated: `status=complete`, `html_url`, `pdf_url`, `json_url` stored.

---

## Summary — External API Call Map

```
PROPERTY REPORT WIZARD
│
├─ Step 1 (SiteX Pro)
│   POST /ls/apigwy/oauth2/v1/token   ← OAuth2 token (refreshed every 9 min)
│   GET  /realestatedata/search        ← Address → property record
│
└─ Step 2 (SimplyRETS)
    GET https://api.simplyrets.com/properties
        auth:    HTTP Basic (SIMPLYRETS_USERNAME / SIMPLYRETS_PASSWORD)
        filter:  zip/city, sqft ±20%, beds ±1, baths ±1, type/subtype
        post:    haversine distance filter (0.5 mi radius) + subtype safety-net


MARKET REPORT WIZARD
│
└─ Step 4 → Worker (SimplyRETS)
    GET https://api.simplyrets.com/properties  (1–3 calls per report)
        auth:    HTTP Basic (same credentials)
        filter:  status, date window, location (city or ZIP), type=RES
        paging:  500 records/page, up to 1000 results
        rate:    60 req/min, burst 10, exponential backoff on 429
```

---

## Environment Variables Required

| Variable | Used By | Purpose |
|---|---|---|
| `SITEX_BASE_URL` | API | SiteX Pro gateway URL (UAT or Prod) |
| `SITEX_CLIENT_ID` | API | OAuth2 client ID |
| `SITEX_CLIENT_SECRET` | API | OAuth2 client secret |
| `SITEX_FEED_ID` | API | Feed identifier (e.g., `100001`) |
| `SIMPLYRETS_BASE_URL` | API + Worker | Base URL (default: `https://api.simplyrets.com`) |
| `SIMPLYRETS_USERNAME` | API + Worker | SimplyRETS username |
| `SIMPLYRETS_PASSWORD` | API + Worker | SimplyRETS password |
| `SIMPLYRETS_TIMEOUT_S` | API + Worker | HTTP timeout in seconds (default: 25–30s) |
| `SIMPLYRETS_RPM` | Worker | Rate limit — requests per minute (default: 60) |
| `SIMPLYRETS_MAX_RESULTS` | Worker | Max listings fetched per report (default: 1000) |
| `SIMPLYRETS_VENDOR` | Worker | MLS vendor ID (optional, only if account requires it) |
| `SIMPLYRETS_ALLOW_SORT` | Worker | Enable sorting (set `true` if MLS account supports it) |
