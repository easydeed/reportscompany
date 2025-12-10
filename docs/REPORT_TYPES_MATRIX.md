# TrendyReports - Report Types Matrix

> **Single Source of Truth** for all report types, their parameters, filtering logic, and expected outputs.

**Last Updated:** December 10, 2024  
**Version:** 1.0

---

## Table of Contents

1. [Report Types Overview](#1-report-types-overview)
2. [Universal Options](#2-universal-options)
3. [Report Type Specifications](#3-report-type-specifications)
   - [Market Snapshot](#31-market-snapshot)
   - [New Listings](#32-new-listings)
   - [Inventory](#33-inventory)
   - [Closed Sales](#34-closed-sales)
   - [Price Bands](#35-price-bands)
   - [New Listings Gallery](#36-new-listings-gallery)
   - [Featured Listings](#37-featured-listings)
   - [Open Houses](#38-open-houses)
4. [Date Filtering Quick Reference](#4-date-filtering-quick-reference)
5. [Email Content by Report Type](#5-email-content-by-report-type)
6. [Code Reference](#6-code-reference)

---

## 1. Report Types Overview

| Report Type | ID | Description | Primary Use Case |
|-------------|-----|-------------|------------------|
| **Market Snapshot** | `market_snapshot` | Complete market overview with all key metrics | Monthly/quarterly market updates |
| **New Listings** | `new_listings` | Table of recently listed properties | Weekly new listing alerts |
| **Inventory** | `inventory` | Current active listings snapshot | Market availability analysis |
| **Closed Sales** | `closed` | Recently sold properties | Sales activity tracking |
| **Price Bands** | `price_bands` | Market segmented by price ranges | Price tier analysis |
| **New Listings Gallery** | `new_listings_gallery` | 3×3 photo grid of newest listings | Visual marketing piece |
| **Featured Listings** | `featured_listings` | 2×2 photo grid of premium listings | Luxury/highlight showcase |
| **Open Houses** | `open_houses` | Upcoming open house events | Weekend open house guide |

---

## 2. Universal Options

These options are available for **ALL** report types:

### 2.1 Location Options

| Option | Type | Required | Values | Description |
|--------|------|----------|--------|-------------|
| `city` | string | No* | Any city name | Target city (e.g., "La Verne") |
| `zips` | array | No* | 5-digit ZIP codes | Target ZIP codes (max 10) |

*At least one of `city` or `zips` must be provided.

### 2.2 Time Period Options

| Option | Type | Default | Values | Description |
|--------|------|---------|--------|-------------|
| `lookback_days` | integer | 30 | 7, 14, 30, 60, 90 | How far back to look for data |

### 2.3 Property Filters

| Option | Type | Default | Values | Description |
|--------|------|---------|--------|-------------|
| `type` | string | "RES" | RES, CND, MUL, LND, COM | Property type (always RES for residential) |
| `subtype` | string | null | SingleFamilyResidence, Condominium, Townhouse | Property subtype filter |
| `minprice` | integer | null | Any | Minimum price filter |
| `maxprice` | integer | null | Any | Maximum price filter |
| `minbeds` | integer | null | 1-10 | Minimum bedrooms |
| `minbaths` | integer | null | 1-10 | Minimum bathrooms |

---

## 3. Report Type Specifications

### 3.1 Market Snapshot

**Purpose:** Comprehensive market overview with Active, Pending, and Closed metrics.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 30 | Affects closed sales filtering |
| `city` or `zips` | Yes | — | Location filter |

#### Date Filtering Logic

| Status | Filter Field | Filter Logic | Rationale |
|--------|--------------|--------------|-----------|
| Active | None | All current active | Current inventory snapshot |
| Pending | None | All current pending | Current contracts |
| **Closed** | `close_date` | `close_date >= (today - lookback_days)` | Only sales that CLOSED within period |

#### Key Metrics Produced

| Metric | Source | Description |
|--------|--------|-------------|
| `active_count` | Active listings | Current inventory count |
| `closed_count` | Date-filtered Closed | Sales in lookback period |
| `pending_count` | Pending listings | Contracts pending |
| `median_list_price` | Active listings | Median asking price |
| `median_close_price` | Date-filtered Closed | Median sale price |
| `avg_dom` | Date-filtered Closed | Average days on market |
| `months_of_inventory` | Active / Monthly Closed Rate | Market health indicator |
| `close_to_list_ratio` | Date-filtered Closed | Sale price vs asking |

#### Email Metrics

```
📊 Your Market Snapshot Report
- Active Listings: {active_count}
- Median Price: {median_close_price}
- Avg DOM: {avg_dom} days
- Months of Inventory: {moi}
```

---

### 3.2 New Listings

**Purpose:** Table of properties recently listed for sale.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 30 | Listings added in this period |
| `city` or `zips` | Yes | — | Location filter |

#### Date Filtering Logic

| Status | Filter Field | Filter Logic | Rationale |
|--------|--------------|--------------|-----------|
| **Active** | `list_date` | `list_date >= (today - lookback_days)` | Only NEW listings from period |

#### Key Metrics Produced

| Metric | Source | Description |
|--------|--------|-------------|
| `total_new` | Date-filtered Active | Count of new listings |
| `median_list_price` | Date-filtered Active | Median asking price |
| `avg_dom` | Date-filtered Active | Average days on market |
| `avg_ppsf` | Date-filtered Active | Average price per sqft |

#### Email Metrics

```
📊 Your New Listings Report
- New Listings: {total_new}
- Median Price: {median_list_price}
- Avg DOM: {avg_dom} days
```

---

### 3.3 Inventory

**Purpose:** Current active listings that were listed within the lookback period.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 30 | Listings LISTED within this period |
| `city` or `zips` | Yes | — | Location filter |

#### Date Filtering Logic

| Status | Filter Field | Filter Logic | Rationale |
|--------|--------------|--------------|-----------|
| **Active** | `list_date` | `list_date >= (today - lookback_days)` | Only listings LISTED within period |

> ⚠️ **User Expectation:** When selecting 30-day lookback, only show properties that were **listed within the last 30 days**, NOT all active inventory.

#### Key Metrics Produced

| Metric | Source | Description |
|--------|--------|-------------|
| `total_active` | Date-filtered Active | Listings from period |
| `new_this_month` | Active with list_date in current month | Brand new listings |
| `median_dom` | Date-filtered Active | Median days on market |
| `months_of_inventory` | Active / Closed rate | Market indicator |

#### Email Metrics

```
📊 Your Inventory Report
- Active Listings: {total_active}
- New This Month: {new_this_month}
- Median DOM: {median_dom} days
```

---

### 3.4 Closed Sales

**Purpose:** Properties that sold within the lookback period.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 30 | Sales that CLOSED within this period |
| `city` or `zips` | Yes | — | Location filter |

#### Date Filtering Logic

| Status | Filter Field | Filter Logic | Rationale |
|--------|--------------|--------------|-----------|
| **Closed** | `close_date` | `close_date >= (today - lookback_days)` | Only sales that CLOSED within period |

> ✅ **Verified Correct:** This report filters by `close_date`, showing only properties that **sold** within the selected period.

#### Key Metrics Produced

| Metric | Source | Description |
|--------|--------|-------------|
| `total_closed` | Date-filtered Closed | Sales count |
| `median_close_price` | Date-filtered Closed | Median sale price |
| `avg_dom` | Date-filtered Closed | Average days to sell |
| `close_to_list_ratio` | Date-filtered Closed | Sale vs asking price |

#### Email Metrics

```
📊 Your Closed Sales Report
- Closed Sales: {total_closed}
- Median Price: {median_close_price}
- Avg DOM: {avg_dom} days
- Close-to-List: {ctl}%
```

---

### 3.5 Price Bands

**Purpose:** Market analysis segmented by price ranges.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 30 | Not used for filtering (all active) |
| `city` or `zips` | Yes | — | Location filter |

#### Date Filtering Logic

| Status | Filter Field | Filter Logic | Rationale |
|--------|--------------|--------------|-----------|
| Active | None | All current active | Full market analysis |

> **Note:** Price Bands analyzes ALL current active inventory, not date-filtered.

#### Key Metrics Produced

| Metric | Source | Description |
|--------|--------|-------------|
| `total_listings` | All Active | Total count |
| `median_list_price` | All Active | Overall median |
| `price_bands[]` | Grouped by quartiles | Entry, Move-Up, Luxury tiers |
| `hottest_band` | Lowest avg DOM | Fastest moving tier |
| `slowest_band` | Highest avg DOM | Slowest tier |

#### Price Band Tiers

| Tier | Range | Description |
|------|-------|-------------|
| Entry | $0 – Median | Below median price |
| Move-Up | Median – 75th percentile | Mid-range |
| Luxury | 75th percentile+ | Premium properties |

#### Email Metrics

```
📊 Your Price Bands Report
- Total Listings: {total_listings}
- Median Price: {median_list_price}
- Hottest Band: {hottest_band}
- Slowest Band: {slowest_band}
```

---

### 3.6 New Listings Gallery

**Purpose:** Visual 3×3 photo grid of the 9 newest listings.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 30 | Listings added in this period |
| `city` or `zips` | Yes | — | Location filter |

#### Date Filtering Logic

| Status | Filter Field | Filter Logic | Rationale |
|--------|--------------|--------------|-----------|
| **Active** | `list_date` | `list_date >= (today - lookback_days)` | Only NEW listings from period |

#### Output

- **9 listings** (3×3 grid)
- Sorted by `list_date` descending (newest first)
- Each card shows: photo, address, price, beds/baths

#### Email Metrics

```
📊 Your New Listings Gallery
- {total_listings} New Listings
- See the newest properties in {city}
```

---

### 3.7 Featured Listings

**Purpose:** Visual 2×2 photo grid of the 4 most expensive listings.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 30 | Not strictly used (highest priced active) |
| `city` or `zips` | Yes | — | Location filter |

#### Selection Logic

| Status | Sort | Limit | Rationale |
|--------|------|-------|-----------|
| Active | `list_price` DESC | 4 | Top 4 most expensive |

#### Output

- **4 listings** (2×2 grid)
- Sorted by `list_price` descending (most expensive first)
- Each card shows: photo, address, price, beds/baths, sqft, DOM

#### Email Metrics

```
📊 Your Featured Listings
- {total_listings} Premium Properties
- Top listings in {city}
```

---

### 3.8 Open Houses

**Purpose:** Properties with upcoming open house events.

#### Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `lookback_days` | No | 7 | Default 7 days for open houses |
| `city` or `zips` | Yes | — | Location filter |

#### Filtering Logic

| Status | Filter | Rationale |
|--------|--------|-----------|
| Active | Has `openHouse` data | Only listings with scheduled open houses |

> **Note:** SimplyRETS API doesn't have a direct "hasOpenHouse" filter. We fetch active listings and filter for those with open house data in the compute layer.

#### Email Metrics

```
📊 Your Open Houses Report
- {total_open_houses} Open Houses This Week
- See what's open in {city}
```

---

## 4. Date Filtering Quick Reference

| Report Type | Filter Field | Filter Logic | Example (30-day lookback) |
|-------------|--------------|--------------|---------------------------|
| **Market Snapshot** | `close_date` (Closed only) | `close_date >= cutoff` | Closed sales from last 30 days |
| **New Listings** | `list_date` | `list_date >= cutoff` | Listed in last 30 days |
| **Inventory** | `list_date` | `list_date >= cutoff` | Listed in last 30 days |
| **Closed Sales** | `close_date` | `close_date >= cutoff` | Sold in last 30 days |
| **Price Bands** | None | All active | All current inventory |
| **New Listings Gallery** | `list_date` | `list_date >= cutoff` | Listed in last 30 days |
| **Featured Listings** | None | Top 4 by price | Most expensive active |
| **Open Houses** | `openHouse` presence | Has open house data | Has scheduled open house |

---

## 5. Email Content by Report Type

Each scheduled report email includes:

### Standard Elements (All Reports)

| Element | Source | Notes |
|---------|--------|-------|
| Subject | `📊 {Report Type}: {City/ZIP}` | Dynamic based on report |
| Header | Brand colors + logo | From `affiliate_branding` |
| Greeting | `Hi {account_name},` | Account name |
| PDF Link | `{pdf_url}` | R2 presigned URL |
| Footer | Rep photo, contact info, website | From `affiliate_branding` |
| Unsubscribe | HMAC-signed link | Per-account suppression |

### Report-Specific Metrics in Email

| Report Type | Metrics Shown |
|-------------|---------------|
| Market Snapshot | Active Count, Median Price, Avg DOM, MOI |
| New Listings | New Count, Median Price, Avg DOM |
| Inventory | Active Count, New This Month, Median DOM |
| Closed Sales | Closed Count, Median Price, Avg DOM, CTL |
| Price Bands | Total Count, Median Price, Hottest/Slowest Band |
| New Listings Gallery | Total Count only |
| Featured Listings | Total Count only |
| Open Houses | Open House Count only |

---

## 6. Code Reference

### Key Files

| File | Purpose |
|------|---------|
| `apps/worker/src/worker/query_builders.py` | Build SimplyRETS API queries |
| `apps/worker/src/worker/report_builders.py` | Process data, apply date filters, calculate metrics |
| `apps/worker/src/worker/compute/extract.py` | Normalize API responses |
| `apps/worker/src/worker/email/template.py` | Generate email HTML |
| `apps/web/lib/sample-report-data.ts` | Frontend report type definitions |

### Report Builder Functions

| Report Type | Builder Function |
|-------------|------------------|
| `market_snapshot` | `build_market_snapshot_result()` |
| `new_listings` | `build_new_listings_result()` |
| `inventory` | `build_inventory_result()` |
| `closed` | `build_closed_result()` |
| `price_bands` | `build_price_bands_result()` |
| `new_listings_gallery` | `build_new_listings_gallery_result()` |
| `featured_listings` | `build_featured_listings_result()` |
| `open_houses` | `build_inventory_result()` (reused) |

### Query Builder Functions

| Report Type | Query Function |
|-------------|----------------|
| `market_snapshot` | `build_market_snapshot()` + `build_market_snapshot_closed()` + `build_market_snapshot_pending()` |
| `new_listings` | `build_new_listings()` |
| `inventory` | `build_inventory_by_zip()` |
| `closed` | `build_closed()` |
| `price_bands` | `build_price_bands()` |
| `open_houses` | `build_open_houses()` |

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| Dec 10, 2024 | 1.0 | Initial version |

---

*This document is the single source of truth for TrendyReports report type specifications.*

