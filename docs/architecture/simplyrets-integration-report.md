# SimplyRETS Integration Report

**Audited against live code on 2026-09-01.** This document supersedes
`modules/simplyrets-api-service.md` and the SimplyRETS sections of
`WIZARD_AND_API_CALLS.md` for behavioural claims. Those files were flagged
as partially falsified in `docs/DOCS_AUDIT_2026-08-17.md` (wrong env var
names, fictional exception classes, Link-header pagination that does not
exist). Every claim below cites the current implementation.

SimplyRETS is the MLS listing feed. SiteX is the assessor/subject-property
feed. They are not interchangeable: SiteX identifies the house; SimplyRETS
identifies what is for sale or recently sold around it.

---

## 1. Why SimplyRETS exists in this product

TrendyReports has two product lines that both need live MLS listings:

| Product | Who consumes SimplyRETS | What they need |
|---------|-------------------------|----------------|
| **Market reports** (scheduled + on-demand) | Celery worker `generate_report` | City/ZIP inventory: Active, Pending, Closed listings for KPIs, galleries, price bands |
| **Property / CMA reports** (wizard + consumer lead pages) | FastAPI `POST /v1/property/comparables` and worker `process_consumer_report` | Nearby comps matched to a SiteX subject (beds, baths, sqft, type, radius) |

A third path, **Market Trends** on seller property PDFs, is a hybrid: the
property builder calls `fetch_and_compute_market_trends()`, which issues
three SimplyRETS queries (Closed / Active / Pending) for the subject's city
and computes seller-oriented trend arrows.

`report_generations.source_vendor` defaults to `'simplyrets'`. That column
is set when a market report starts processing.

---

## 2. Architecture: two clients, one vendor

API and worker are **separate Render deployments**. They cannot share a
Python process, so each has its own client.

```
┌──────────────────────────┐     HTTP Basic Auth      ┌─────────────────────┐
│  apps/web (Vercel)       │                          │                     │
│  Property wizard         │─── /v1/property/* ───►   │  FastAPI (Render)   │
│  Market report wizard    │─── /v1/reports/* ────►   │  services/          │
└──────────────────────────┘                          │  simplyrets.py      │
                                                      │  (async, no pager,  │
                                                      │   no rate limiter)  │
                                                      └──────────┬──────────┘
                                                                 │ enqueue
                                                                 ▼
┌──────────────────────────┐                          ┌─────────────────────┐
│  Scheduled tick          │─── generate_report ───►  │  Celery worker      │
│  Consumer lead pages     │─── process_consumer_*    │  vendors/           │
└──────────────────────────┘                          │  simplyrets.py      │
                                                      │  (sync, offset      │
                                                      │   paging, token-    │
                                                      │   bucket limiter)   │
                                                      └──────────┬──────────┘
                                                                 │
                                                                 ▼
                                                      https://api.simplyrets.com
                                                      GET /properties
```

### 2.1 Worker client — `apps/worker/src/worker/vendors/simplyrets.py`

This is the production-grade client.

- **Auth:** `Authorization: Basic base64(SIMPLYRETS_USERNAME:SIMPLYRETS_PASSWORD)`
- **Base URL:** `SIMPLYRETS_BASE_URL` (default `https://api.simplyrets.com`)
- **Timeout:** `SIMPLYRETS_TIMEOUT_S` (default 25s)
- **Rate limit (local):** token-bucket, `SIMPLYRETS_RPM` default 60, `SIMPLYRETS_BURST` default 10. Sleeps when the minute window is full.
- **Retries:** up to 3 extra attempts on HTTP 429, 5xx, and timeouts, with exponential backoff. Then one final attempt that raises.
- **Pagination:** offset paging. Page size 500 (SimplyRETS max). Stops when a page is short, or when `SIMPLYRETS_MAX_RESULTS` (default 1000) is reached. Does **not** follow `Link: rel=next` headers.
- **Public API:** `fetch_properties(params, limit=None)` and a convenience `build_market_snapshot_params(city, lookback_days=30)`.

### 2.2 API client — `apps/api/src/api/services/simplyrets.py`

This is a thinner async replica used only by the comparables route.

- **Auth:** `httpx` `auth=(USERNAME, PASSWORD)` — same Basic Auth, different call style.
- **Timeout:** `SIMPLYRETS_TIMEOUT_S` (default 30s).
- **No local rate limiter.** A 429 becomes a raised `Exception("SimplyRETS rate limit exceeded")`.
- **No pagination.** Single GET; `limit` is capped at 500.
- **Default type:** if the caller omits `type`, it injects `type=RES` to keep rentals out.
- **Helpers:** `build_comparables_params(...)` (used less than the inline ladder in `property.py`) and `normalize_listing(...)`.

### 2.3 Credentials and demo vs production

| Env var | Used by | Default | Purpose |
|---------|---------|---------|---------|
| `SIMPLYRETS_USERNAME` | API + worker | `simplyrets` | Basic Auth user |
| `SIMPLYRETS_PASSWORD` | API + worker | `simplyrets` | Basic Auth password |
| `SIMPLYRETS_BASE_URL` | API + worker | `https://api.simplyrets.com` | Override for staging |
| `SIMPLYRETS_TIMEOUT_S` | API + worker | 25 worker / 30 API | Request timeout |
| `SIMPLYRETS_RPM` | Worker only | 60 | Local rate limit |
| `SIMPLYRETS_BURST` | Worker only | 10 | Burst allowance |
| `SIMPLYRETS_MAX_RESULTS` | Worker only | 1000 | Safety cap across pages |
| `SIMPLYRETS_VENDOR` | Worker query builders | unset | Optional MLS feed id (`vendor=`) |
| `SIMPLYRETS_ALLOW_SORT` | Worker query builders | unset | Enable `sort=-listDate` / `-closeDate` |

If `SIMPLYRETS_USERNAME` is the literal string `simplyrets`, query builders
enter **demo mode**: Houston-only data, city search disabled (ZIP only),
sorting off. Production usernames enable `q=<city>` fuzzy search.

`SIMPLYRETS_VENDOR` is **not** per-affiliate at runtime. It is a single
process-wide env var. Docs that claim the worker swaps credentials per
affiliate account are not implemented in the current vendor module.

---

## 3. What SimplyRETS actually returns

The only endpoint used in production is `GET /properties`. We do not call
`/openhouses`, `/properties/{id}`, or `/openHouse` as standalone resources.

A listing is a nested JSON object. The fixtures
`tests/fixtures/listing_active_minimal.json` and
`listing_closed_minimal.json` match the shape we consume.

### 3.1 Top-level listing fields

| Field | Type | What it is | Used for |
|-------|------|------------|----------|
| `mlsId` | int | SimplyRETS listing id | Dedup, `mls_id` |
| `listingId` | str | MLS number (e.g. `IV26039109`) | Present in raw; not extracted into market rows |
| `listPrice` | int | Current asking price | Medians, PPSF, price bands, comps |
| `originalListPrice` | int | Original ask | Present in raw; **not extracted** in `extract.py` (price-cut helpers therefore never fire) |
| `listDate` | ISO datetime | When it hit the market | DOM, new-listings window, client-side date filter |
| `closeDate` | ISO datetime | Top-level close date | API comps path reads this; worker extract does **not** |
| `closePrice` | int | Top-level close price | API comps path; worker extract reads `sales.closePrice` instead |
| `modified` | ISO datetime | Last MLS update | Unused |
| `remarks` | str | Public remarks | Unused |
| `photos` | `[url]` | Photo URLs | Hero image for galleries; first photo for comps |
| `status` | str | Sometimes duplicated at top level | Fallback if `mls.status` missing |

### 3.2 `property` (physical characteristics)

| Field | Type | Used for |
|-------|------|----------|
| `type` | `"RES"`, `"CND"`, `"MLF"`, … | Stored as `property_type`; rental exclusion |
| `subType` | `"SingleFamilyResidence"`, `"Condominium"`, `"Townhouse"`, `"ManufacturedHome"`, `"Duplex"`, … | Type mapping, post-filter, subtype breakdown |
| `subTypeText` | Human / vendor code | Post-filter fallback |
| `area` | int | Living sqft → minarea/maxarea, PPSF, sqft variance |
| `bedrooms` | int | Comp matching, gallery cards |
| `bathrooms` | float | Worker extract (keeps halves) |
| `bathsFull` | int | API comps (full baths only unless `normalize_comparable` adds half baths) |
| `bathsHalf` | int | Added as 0.5 in `normalize_comparable` |
| `yearBuilt` | int | Comp cards, area-analysis table |
| `lotSize` / `lotSizeArea` | int | Comp cards |
| `garageSpaces` | int | Comp cards when the frontend/API passes it through |
| `stories` | int | Area-analysis table |
| `pool` | str | Comp cards (`"Private,In Ground"` etc.) |

### 3.3 `address`

`full`, `streetName`, `streetNumber`, `city`, `state`, `postalCode`,
`country`, `unit`. Market reports key off `city` and `postalCode`. Comp
cards use `full`.

### 3.4 `geo`

`lat`, `lng`, `county`, `marketArea`. Haversine distance for comps.
`county` / `marketArea` are unused.

### 3.5 `mls`

`status` (`Active` / `Pending` / `Closed` / plus expired/withdrawn in
validation), `daysOnMarket`, `area`, `originatingSystemName`.
**Closed listings often have `daysOnMarket` null** — we recompute DOM
from dates (see §5.1).

### 3.6 `sales` (closed listings only)

| Field | Used for |
|-------|----------|
| `closeDate` | Worker extract + market-snapshot date filter (authoritative close window) |
| `closePrice` | Worker extract, CTL, median sale price |
| `contractDate` | Unused in production metrics |
| `office` / `agent` | Unused |

### 3.7 Present in the payload but not used for metrics

`school` (district, elementary/middle/high), `association` (HOA fee /
frequency / amenities), `tax` (APN / tax year / amount), `office`,
`coAgent`, `specialListingConditions`, `ownership`, `internetAddressDisplay`,
`openHouse` / `openHouseDates` (open-house report tries to read these;
the unified wizard currently hides the open-house report type because the
data is not reliably updated).

---

## 4. How we query SimplyRETS

### 4.1 Query parameters we send

| Param | Meaning | Who sets it |
|-------|---------|-------------|
| `q` | Fuzzy text (city, address, MLS #) | Market query builders in production city mode |
| `cities` | Deterministic city | Comparables ladder; market-trends (production) |
| `postalCodes` | Comma-separated ZIPs | ZIP schedules; comps when ZIP is known |
| `status` | `Active`, `Pending`, `Closed`, or comma-joined | Every query |
| `type` | Market reports: `RES` (default). Comps: `residential` / `multifamily` / `land` / `commercial` | See §4.4 |
| `subtype` | CamelCase: `SingleFamilyResidence`, `Condominium`, … | Presets + comps L0 |
| `minarea` / `maxarea` | Living-area band | Comps ladder, CMA |
| `minbeds` / `maxbeds` | Bedroom band | Presets, comps |
| `minbaths` / `maxbaths` | Bathroom band | Comps L0 only |
| `minprice` / `maxprice` | Dollar band | Filter resolver after % → $ |
| `mindate` / `maxdate` | List-date window (NOT close date) | Market queries |
| `minlistdate` | Wider list-date floor | Market trends closed fetch |
| `limit` / `offset` | Paging | Worker vendor |
| `sort` | `-listDate`, `-closeDate`, `daysOnMarket` | Only if `SIMPLYRETS_ALLOW_SORT=true` |
| `vendor` | MLS feed id | Only if `SIMPLYRETS_VENDOR` is set |

### 4.2 Market-report query builders

`apps/worker/src/worker/query_builders.py` maps each report type to a
parameter set. Location priority: ZIPs → `postalCodes`; else city (production)
→ `q`; else demo → no location (Houston feed).

| Builder | Status | Date window | Notes |
|---------|--------|-------------|-------|
| `build_market_snapshot` | Active | lookback | Inventory for snapshot |
| `build_market_snapshot_closed` | Closed | lookback | Separate call so closed counts are clean |
| `build_market_snapshot_pending` | Pending | lookback | Pending-sales KPI |
| `build_new_listings` | Active | lookback | Optional `sort=-listDate` |
| `build_closed` | Closed | lookback | Optional `sort=-closeDate` |
| `build_inventory_by_zip` | Active | lookback | Optional `sort=daysOnMarket` |
| `build_open_houses` | Active | 7 days | No `hasOpenHouse` param — post-filtered later |
| `build_price_bands` | Active | none | Full current inventory; bands computed client-side |

`generate_report` for `market_snapshot` fires the three status queries
separately (Active 1000 + Closed 1000 + Pending 500) and concatenates
them before extract. Other report types use one `build_params()` call,
limit 800.

### 4.3 Known SimplyRETS filter bugs we work around

1. **`mindate`/`maxdate` filter by `listDate`, not `closeDate`.** Closed-sales
   reports therefore over-fetch and filter `sales.closeDate` in Python.
2. **Active `mindate`/`maxdate` is unreliable.** New-listings, inventory, and
   gallery builders re-filter by `list_date` client-side.
3. **`q=` is fuzzy.** Searching "La Verne" can return East Los Angeles.
   `_filter_by_city()` exact-matches `address.city` (skipped when the
   "city" is actually a ZIP).
4. **`subtype` is vendor-dependent.** We always post-filter `property.subType`
   on comps, even when we omitted `subtype` from the query.
5. **Rentals leak into `type=RES`.** `_exclude_rentals()` drops status
   containing lease/rent, or any price under $50,000.

### 4.4 Property-type mapping (SiteX → SimplyRETS)

Subject search is SiteX. Comparables are SimplyRETS. The bridge is
`PROPERTY_TYPE_MAP` in `apps/api/src/api/routes/property.py` (duplicated
on the worker as `_PROPERTY_TYPE_MAP`).

Lookup: lowercase UseCode → exact map → substring match → default
`("residential", "SingleFamilyResidence")`.

| SiteX UseCode examples | SimplyRETS `type` | SimplyRETS `subtype` |
|------------------------|-------------------|----------------------|
| sfr, rsfr, single family, pud | `residential` | `SingleFamilyResidence` |
| condo, condominium | `residential` | `Condominium` |
| townhouse, th, townhome | `residential` | `Townhouse` |
| duplex | `multifamily` | `Duplex` |
| triplex | `multifamily` | `Triplex` |
| quadplex, quadruplex | `multifamily` | `Quadruplex` |
| multi-family | `multifamily` | _(none)_ |
| mobile, manufactured | `residential` | `ManufacturedHome` |
| land, vacant land | `land` | _(none)_ |
| commercial | `commercial` | _(none)_ |

Post-filter allowed `property.subType` values:

| Wanted subtype | Keep |
|----------------|------|
| SingleFamilyResidence | `SingleFamilyResidence`, `Detached`, empty |
| Condominium | `Condominium`, `StockCooperative`, `Attached` |
| Townhouse | `Townhouse`, `Attached` |
| Duplex / Triplex / Quadruplex | exact match |
| ManufacturedHome | `ManufacturedHome`, `ManufacturedOnLand`, `MobileHome` |

Empty subtype is kept on purpose so we do not over-filter vendors that
omit `subType`.

**Type-code split:** market reports send `type=RES` (legacy short code).
Comparables send full words (`residential`) per the public SimplyRETS
docs. Both work against the same account; they are not interchangeable
in our code.

---

## 5. Normalization: raw listing → typed row

### 5.1 Worker extract — `PropertyDataExtractor`

`apps/worker/src/worker/compute/extract.py` is the market-report contract.

Per listing it builds:

| Output field | Source / formula |
|--------------|------------------|
| `mls_id` | `mlsId` |
| `list_date` | `listDate` parsed ISO, tz stripped |
| `close_date` | `sales.closeDate` parsed ISO, tz stripped |
| `status` | `mls.status` or top-level `status` |
| `days_on_market` | `daysOnMarket` if present; else `close_date − list_date` for closed; else `now − list_date` for active/pending; negatives clamped to 0 |
| `list_price` | `listPrice` as int |
| `close_price` | `sales.closePrice` as int |
| `city` / `zip_code` | `address.city` / `address.postalCode` |
| `property_type` | `property.type` (default `RES`) |
| `property_subtype` | Mapped: SFR / Condo / Townhome / Manufactured / Multi-Family / Other |
| `sqft` | `property.area` |
| `price_per_sqft` | `round(list_price / sqft, 2)` — **list** price, not close |
| `close_to_list_ratio` | `round((close_price / list_price) * 100, 2)` |
| `hero_photo_url` | `photos[0]` |
| `bedrooms` / `bathrooms` | `property.bedrooms`, `property.bathrooms` (float) |
| `street_address` | `address.full` or `streetName` |

Invalid rows are skipped (`try/except continue`). `filter_valid()` then
drops rows missing `mls_id`, unknown status, negative list price, sqft
&lt; 100, or future `list_date`. Allowed statuses:
`Active, Pending, Closed, Expired, Withdrawn, Temp Off Market`.

### 5.2 API listing normalize — `normalize_listing`

Used by the API client helper (comps route currently inlines a similar
dict). Maps to frontend-shaped fields: `price = closePrice or listPrice`,
`bathrooms = bathsFull` (no half baths), `dom` from `mls.daysOnMarket`
only (no date fallback), `close_date` from **top-level** `closeDate`.

### 5.3 Cross-source normalize — `normalize_comparable`

`apps/api/src/api/schemas/property.py` accepts SimplyRETS, SiteX, or
wizard payloads. It is the CMA schema: `sale_price`, `sold_date`,
`price_per_sqft = sale_price / sqft`, half baths added, geo from
`lat`/`lng` or `geo.lat`/`geo.lng`.

### 5.4 Field-path inconsistency (important)

| Concept | Worker extract | API comps / consumer CMA |
|---------|----------------|--------------------------|
| Close price | `sales.closePrice` | top-level `closePrice` |
| Close date | `sales.closeDate` | top-level `closeDate` |
| Baths | `property.bathrooms` (float) | `property.bathsFull` (int) |
| DOM | API value or computed | API value only |

The fixtures put close data under `sales`, not at the top level. Market
reports therefore see close price/date; the API comps path can miss them
unless the vendor also duplicates those fields at the root.

---

## 6. Calculations we created

All of these are **ours**. SimplyRETS does not return MOI, absorption,
CTL, PPSF, confidence grades, or value estimates.

### 6.1 Per-listing derived fields (extract)

```
PPSF_list     = list_price / sqft
CTL           = (close_price / list_price) * 100
DOM_closed    = (close_date − list_date).days     if API DOM is null
DOM_active    = (now − list_date).days            if API DOM is null
```

### 6.2 Market Snapshot KPIs — `build_market_snapshot_result`

After city filter and status split:

| Metric | Formula | Notes |
|--------|---------|-------|
| Median close price | `median(close_price)` of closed-in-window | Closed must have `close_date ≥ now − lookback` |
| Median list price | `median(list_price)` of current Active | |
| Avg DOM | `mean(days_on_market)` of closed-in-window | |
| Avg PPSF | `mean(price_per_sqft)` of Active | Uses list-price PPSF from extract |
| Close-to-list | `mean(CTL)` of closed-in-window, default 100 | |
| Months of inventory | `active_count / (closed_count × 30.437 / lookback_days)` | `30.437 = 365.25 / 12`. No closings → 99.9 |
| New listings | Active with `list_date` in lookback | |
| Counts | Active (current), Pending (all fetched), Closed (date-filtered), NewListings | |

**By property type:** for each mapped subtype, closed-in-window count,
active count, median price (close if any, else list), avg DOM.

**Price tiers (dynamic):** quartiles of closed prices in the window.

| Tier | Bounds |
|------|--------|
| Entry | `[0, p50)` |
| Move-Up | `[p50, p75)` |
| Luxury | `[p75, ∞)` |

Each tier gets closed count, active count, median close, and its own MOI
using the same monthly-sales-rate formula.

### 6.3 Older snapshot helper — `compute/calc.py`

`snapshot_metrics()` still exists and is imported by `tasks.py` but
**market reports do not call it**. It uses a simpler MOI
(`active / closed`, no day-normalization) and an absorption rate
(`closed / active * 100`). Live PDFs/emails use `report_builders`.

### 6.4 New Listings / Gallery

Client-side Active + `list_date` in lookback, sorted newest first.

- Table report: median list, avg DOM, avg PPSF.
- Gallery: median / min / max list, avg DOM (from `dom` if present),
  plus audience email cap derived from the Smart Preset.

### 6.5 Inventory

Active listed inside the lookback (fail-open if `list_date` is missing).

| Metric | Formula |
|--------|---------|
| Median DOM | median of Active DOM |
| New this month | Active with `list_date ≥ first of current month` |
| MOI | `(active / closed) * (lookback_days / 30)` |

This MOI is **not** the same as Market Snapshot MOI. Inventory divides
raw counts and scales by `lookback/30`. Snapshot uses `30.437` and a
true monthly sales rate. Do not mix them in one sentence to a client.

### 6.6 Closed Listings

Closed with `close_date` in lookback, sorted newest close first.
Median close, avg DOM, mean CTL (default 100).

### 6.7 Price Bands

All fetched listings (typically Active). Quartile bands on
`list_price or close_price`:

- Under p50
- p50–p75
- p75+

Per band: count, median price, avg DOM, avg PPSF.
**Hottest band** = lowest avg DOM (ignoring 0). **Slowest** = highest avg DOM.

### 6.8 Featured Listings

Active, sorted by list price descending, top 15. Metrics: count, max
price, average sqft. Audience forced to `luxury`.

### 6.9 Open Houses

Post-filter `openHouseDates` / `open_house_dates` to the next 7 days.
Capped at 100. No KPI math. The unified wizard currently hides this
report type because SimplyRETS open-house data is not reliably updated.

### 6.10 Market-adaptive Smart Presets — `filter_resolver.py`

Presets store **intent**, not dollars. At generation time:

1. Fetch a 90-day baseline (location + optional subtype, no bed/bath).
2. `compute_market_stats`:
   - `median_list_price` = median list of Active + Pending
   - `median_close_price` = median close of Closed
3. `resolve_filters` always sets `type=RES`, passes through beds/baths/
   subtype, and resolves:

| Mode | Result |
|------|--------|
| `maxprice_pct_of_median_list` | `maxprice = median_list * pct` |
| `maxprice_pct_of_median_close` | `maxprice = median_close * pct` |
| `minprice_pct_of_median_list` | `minprice = median_list * pct` |
| `minprice_pct_of_median_close` | `minprice = median_close * pct` |

If the strategy cannot resolve (no median), fall back to absolute
min/max if the intent had them.

**Elastic widening** when results &lt; 6 (featured: &lt; 4), up to 3 steps:

- Max-price strategies: 70% → 85% → 100% → 120%
- Min-price strategies: 150% → 130% → 110% → 90%

A human label is stored on the result (`"2+ beds, under $1,680,000
(70% of median list $2,400,000)"`) for PDF/email headers.

### 6.11 Comparables fallback ladder (property wizard)

`POST /v1/property/comparables` does **not** call SiteX. The wizard
already has subject beds/baths/sqft/lat/lng/type from step 1.

Haversine (miles), Earth radius 3956:

```
a = sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlng/2)
d = 3956 · 2 · asin(√a)
```

Listings with coordinates outside the radius are dropped; listings
without coordinates are kept (`distance_miles = null`) and sorted last.

| Level | Sqft | Beds | Baths | Subtype query | Radius |
|-------|------|------|-------|---------------|--------|
| L0 strict | ± `sqft_variance` (default 20%; 0 = skip) | ±1 | ±1 | yes | request radius (default 1 mi) |
| L1 | same | ±1 | ±1 | **removed** | same |
| L2 | ±30% | ±1 | ±1 | removed | same |
| L3 | ±50% | ±2 | dropped | removed | same |
| L4 | none | ±3 | dropped | removed | same |
| L5 | none | ±3 | dropped | removed | **×3** |

Target is ≥5 after distance + type post-filter. The engine keeps the
**best (largest)** set seen so a looser level cannot shrink the result.
Stops early when the target is met.

**Confidence grade:**

| Grade | When |
|-------|------|
| A | L0, and ≥3 comps returned |
| B | L1 (subtype relaxed) or L2 (sqft +30%) |
| C | L3/L4 (beds loosened) or L5 (thin market) |
| D | fewer than 3 comps, any level |

Beds at L0 are already `subject ± 1`, not exact. Bath filter is dropped
as soon as `extra_beds > 0` (L3+).

### 6.12 Consumer CMA value estimate — `process_consumer_report`

A shorter ladder (Closed only, ZIP + city):

- L0: type + subtype + beds ±1 + sqft ±25%
- L1: drop subtype
- L2: drop sqft
- L3: type only

Stop at ≥3 after type post-filter. Then:

**Market stats from comps**

- `median_price` = middle of sorted comp prices
- `avg_price_per_sqft` = mean(`price / sqft`)
- `avg_days_on_market` = mean DOM
- `total_sold_last_6mo` = count of returned comps (not a true 6-month query)

**Value estimate**

If subject sqft and avg PPSF exist:

```
mid  = subject_sqft × avg_ppsf
low  = mid × 0.92
high = mid × 1.08
```

Else:

```
mid  = mean(comp prices)
range = max − min  (or 10% of mean if only one)
low  = mid − 0.5 × range
high = mid + 0.5 × range
```

Confidence: `high` if ≥5 comps; `medium` if ≥3 (PPSF path) or ≥5
(average path); else `low`.

### 6.13 Property-report stats from selected comps — `PropertyReportBuilder`

Once the agent picks comps, the PDF builder computes:

- Per-comp PPSF = `price / sqft`
- Range of sales: avg sqft/beds/baths, `price_min`/`price_max` in thousands
- Area Sales Analysis table:
  - **PIQ** (property in question): SiteX sqft/year/lot/beds/baths; PPSF from `estimated_value` or `assessed_value`
  - **Low / Medium / High:** comps sorted by price; first, middle, last
  - Aggregates: avg sqft/beds/baths, avg PPSF, avg DOM, max distance, price low/high

### 6.14 Market Trends page (seller PDF) — `compute/market_trends.py`

Three parallel fetches (ThreadPoolExecutor):

| Call | Status | Date filter |
|------|--------|-------------|
| Closed | Closed | `minlistdate = now − 210 days` (wide net) |
| Active | Active | **none** (full current inventory for MOI) |
| Pending | Pending | none (count only) |

Then: extract → city filter → rental exclusion → split closed by
**actual `close_date`**:

- Current period: last 90 days
- Prior period: 90–180 days ago

Guards: &lt; 3 current closed → page omitted. &lt; 5 prior closed → no
trend arrows (`has_prior_data = false`).

| Metric | Current | Comparison |
|--------|---------|------------|
| Median sale price | median(`close_price`) | vs prior median |
| Avg DOM | mean DOM of current closed | vs prior |
| List-to-sale | mean(`close/list * 100`) | vs prior |
| Price per sqft | mean(`close_price / sqft`) — **close**, not list | vs prior |
| Closed sales | count | vs prior count |
| Active listings | count + mean list price | snapshot only |
| MOI | `active / (current_closed × 30.437 / 90)` | snapshot only |

**Trend packaging** (`_build_metric`):

```
change_pct = (current − prior) / |prior| * 100
direction  = up if change_pct > 0.05, down if < −0.05, else flat
sentiment  = good if direction matches good_direction, else bad; flat → neutral
```

Seller-oriented `good_direction`: price/CTL/PPSF/sales **up**, DOM **down**.
Templates color by `sentiment`, never by `direction` (so falling DOM is green).

**Market condition** (NAR-style MOI bands):

| MOI | Label | Score |
|-----|-------|-------|
| &lt; 4 | Seller's Market | `max(5, min(10, round(10 − MOI × 1.25)))` |
| 4–6 | Balanced Market | 5 |
| &gt; 6 | Buyer's Market | `max(1, min(4, round(11 − MOI)))` |

Gauge: `min(int(MOI / 12 * 100), 98)` on a 0–12 month scale.

**B1–B3 extended metrics** (`price_cut_stats`, `dom_distribution`,
`timeline_metrics`) are *imported* from `report_builders` but **are not
defined there**. They exist only as test helpers in
`tests/test_new_metrics.py`. The import fails, the exception is swallowed,
and those template blocks stay empty. Price-cut math would need
`original_list_price`, which extract does not populate even though
SimplyRETS sends `originalListPrice`.

### 6.15 Haversine (shared)

Used in API comps and consumer CMA. Same 3956-mile radius. Results
rounded to 2 decimals and attached as `distance_miles`.

---

## 7. End-to-end pipelines

### 7.1 Market report (scheduled or wizard)

```
params (city / zips / lookback / filters)
    │
    ├─ if price_strategy:
    │     baseline fetch (90d) → compute_market_stats
    │     → resolve_filters (% → $) → filters_label
    │
    ├─ cache key = {report_type, original params}  TTL 15 min
    │
    ├─ SimplyRETS fetch (1 or 3 queries)
    │     → PropertyDataExtractor → filter_valid
    │     → elastic widen (up to 3×) if too few rows
    │
    ├─ build_result_json(report_type, rows, context)
    │
    ├─ proxy MLS photo URLs → R2 (not cached)
    ├─ save result_json
    └─ MarketReportBuilder → PDFShift → email / PDF
```

Redis cache is keyed on the **unresolved** params, so two runs with the
same intent can share a payload for 15 minutes. Photo URLs are rewritten
after cache get/set so signed R2 URLs never land in cache.

### 7.2 Property wizard comps

```
Step 1: Google Places → POST /v1/property/search → SiteX (subject)
Step 2: POST /v1/property/comparables
           → type map → L0–L5 SimplyRETS ladder
           → haversine + subtype post-filter
           → confidence grade
Step 3: agent picks comps / pages / theme
Step 4: POST /v1/property/reports/{id}/generate
           → generate_property_report_task
           → PropertyReportBuilder
           → optional market_trends (3 more SimplyRETS calls)
           → PDF
```

### 7.3 Consumer / lead-page CMA

```
Lead submits address → SiteX property_data stored
process_consumer_report
    → Closed comps ladder (L0–L3)
    → market_stats + value_estimate
    → branded PDF + SMS/email link
```

---

## 8. What the UI / PDFs / emails do with the numbers

| Surface | SimplyRETS-derived content |
|---------|----------------------------|
| Market Snapshot PDF + email | Hero KPIs (median, closed, DOM, MOI), CTL, new/pending, type + tier tables, AI narrative |
| New Listings / Inventory / Closed | Listing tables, hero medians |
| Price Bands | Hottest/slowest band, quartile shares |
| Gallery / Featured | Hero photos (`photos[0]` proxied to R2), price/beds/baths/sqft |
| Social templates | Same KPI tokens (`{{close_to_list_ratio}}`, MOI) |
| Property PDF comps page | Up to 6 cards: photo, price, DOM, distance, PPSF, beds/baths/year/lot/pool |
| Area Sales Analysis | PIQ vs low/med/high comps |
| Market Trends page | 90-day vs prior-90 trends, MOI gauge, seller/buyer badge |
| Consumer report | Value low/mid/high + median sold + avg PPSF |
| Admin system page | SimplyRETS listed as configured MLS provider |

---

## 9. Tests and smoke tools

| Path | Role |
|------|------|
| `tests/test_simplyrets_query_builder.py` | Query-builder unit tests (note: some assertions expect `cities=` / no `type=RES`, which does **not** match current `query_builders.py` — that file uses `q=` and defaults `type=RES`) |
| `tests/test_new_metrics.py` | Isolated helpers for price-cut / DOM buckets / confidence (not wired into report_builders) |
| `tests/fixtures/listing_*_minimal.json` | Canonical raw payload shape |
| `scripts/test_simplyrets.py` | Live GET /properties smoke |
| `apps/worker/test_simplyrets.py` | Worker-client smoke |
| `tools/simplyrets_smoke.py` | CLI smoke |

---

## 10. Guardrails and failure modes

| Failure | Behaviour |
|---------|-----------|
| HTTP 401 | API: raise auth exception. Worker: `raise_for_status` after retries |
| HTTP 429 | API: raise, UI sees failure. Worker: backoff and retry |
| HTTP 5xx / timeout | Worker retries; API raises timeout exception |
| Empty city | Market trends skip; market report labels city `Unknown` (does not default to Houston) |
| Demo credentials | Houston feed, no city `q`, no sort |
| Thin comps | Return best set found; grade D if &lt; 3 |
| Thin market report + preset | Widen price % up to 3 times; still send whatever remains |
| Missing optional fields | Jinja `{% if %}` hides the section |
| Photo proxy failure | Keep original MLS URLs; run continues |
| Market trends API/extract/compute error | `market_trends` omitted from the PDF page set |

---

## 11. Gaps and inconsistencies (from this audit)

1. **Close price/date path differs** between worker extract (`sales.*`) and
   API comps (top-level). Fixtures only have `sales.*`.
2. **Two MOI formulas** (snapshot vs inventory) will disagree on the same
   dataset.
3. **PPSF basis differs:** extract/snapshot use list price; market trends
   and CMA use close/sale price.
4. **`originalListPrice` is unused**, so price-cut rate cannot be computed
   even though the API sends it.
5. **B1–B3 helpers are not implemented** in `report_builders.py`; market
   trends silently drops them.
6. **Query-builder tests disagree with current `_location` / `_filters`**
   (`cities` vs `q`, `type=RES`).
7. **Type codes are split** (`RES` vs `residential`) across market vs comps.
8. **No per-affiliate vendor credential swap** in the worker client,
   despite older docs.
9. **API client does not paginate or rate-limit**; wizard ladder can issue
   up to 6 sequential GETs and hit 429.
10. **Open-house report is implemented but hidden** in the wizard.
11. **`snapshot_metrics` is dead code** relative to live report builders.
12. **Existing architecture module docs are stale**; treat this file as
    the current SimplyRETS source of truth.

---

## 12. File map

| File | Role |
|------|------|
| `apps/worker/src/worker/vendors/simplyrets.py` | Sync client, limiter, pager |
| `apps/api/src/api/services/simplyrets.py` | Async client, comps helpers |
| `apps/worker/src/worker/query_builders.py` | Market report query params |
| `apps/worker/src/worker/compute/extract.py` | Raw → typed rows + PPSF/CTL/DOM |
| `apps/worker/src/worker/compute/validate.py` | Row guards |
| `apps/worker/src/worker/compute/calc.py` | Legacy snapshot metrics |
| `apps/worker/src/worker/compute/market_trends.py` | Seller-report trend math |
| `apps/worker/src/worker/report_builders.py` | All market-report KPI builders |
| `apps/worker/src/worker/filter_resolver.py` | % of median → dollars, widening |
| `apps/worker/src/worker/tasks.py` | `generate_report` fetch pipeline + consumer CMA |
| `apps/api/src/api/routes/property.py` | Comps ladder, type map, haversine |
| `apps/api/src/api/schemas/property.py` | Cross-source comparable schema |
| `apps/worker/src/worker/property_builder.py` | Comp/PIQ stats for property PDFs |
| `docs/architecture/property-type-data-contract.md` | Type-mapping intent (verify against `property.py`; some table values drifted) |
