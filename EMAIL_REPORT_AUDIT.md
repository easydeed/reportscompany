# Email Report Type Audit

Generated from `apps/worker/src/worker/email/template.py` (V16 architecture).

---

## 1. REPORT_CONFIG Flags

| Report Type | Label | `has_hero_4` | `has_core_indicators` | `has_insight` | `has_listings_table` | `has_property_types` | `has_price_tiers` | `has_price_bands` | `has_extra_stats` | `section` |
|---|---|---|---|---|---|---|---|---|---|---|
| `market_snapshot` | Market Snapshot | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | None |
| `new_listings` | New Listings | ✅ | — | ✅ | — | — | — | — | — | None |
| `inventory` | Inventory Report | ✅ | — | ✅ | ✅ | — | — | — | — | None |
| `closed` | Closed Sales | ✅ | — | ✅ | ✅ | — | — | — | — | None |
| `price_bands` | Price Analysis | ✅ | — | ✅ | — | — | — | ✅ | — | None |
| `open_houses` | Open Houses | — | — | — | — | — | — | — | — | "Open Houses" |
| `new_listings_gallery` | New Listings Gallery | — | — | ✅ | — | — | — | — | — | "New Listings" |
| `featured_listings` | Featured Listings | — | — | ✅ | — | — | — | — | — | "Featured Properties" |

**Notes:**
- `has_hero_4` = uses `_get_hero_4_metrics()` for 4-metric hero row (PDF-aligned).
- `has_core_indicators` = only `market_snapshot` — shows New Listings, Pending Sales, Sale-to-List Ratio.
- `has_insight` = receives AI-generated or template-based narrative paragraph.
- `has_listings_table` = receives individual property listing data for table display.
- `has_property_types` / `has_price_tiers` = only `market_snapshot` — breakdown charts.
- `has_price_bands` = only `price_bands` — price tier analysis.
- `open_houses` is the only type with NO `has_hero_4` and NO `has_insight`.

---

## 2. Data Shape Per Report Type

### market_snapshot

| Data Field | Source | Value |
|---|---|---|
| **Hero metric (h1)** | `_get_hero_4_metrics` | Median Sale Price (e.g., "$1.2M") |
| **Supporting metrics** | h2: Closed Sales, h3: Avg Days on Market, h4: Months of Inventory |  |
| **Core indicators** | `_get_core_indicators` | New Listings, Pending Sales, Sale-to-List Ratio |
| **Listings data** | None passed | — |
| **AI insight** | `_get_insight_paragraph` | AI or template fallback |
| **Quick take** | `_get_quick_take` | "Seller's market conditions: X months inventory..." |
| **Extra sections** | `property_types` breakdown, `price_tiers` breakdown | SFR/Condo/Townhome counts, Entry/Move-Up/Luxury tiers |

**V16 note:** `property_types`, `price_tiers`, and `extra_stats` are computed but NOT currently passed to the layout builder (`_build_market_narrative_body`). They are dead data. Only hero + stacked stats + quick take render.

### new_listings

| Data Field | Source | Value |
|---|---|---|
| **Hero metric (h1)** | `_get_hero_4_metrics` | New Listings count |
| **Supporting metrics** | h2: Median Price, h3: Avg DOM, h4: Avg $/SqFt |  |
| **Listings data** | None passed | — |
| **AI insight** | `_get_insight_paragraph` | AI or template fallback |
| **Quick take** | `_get_quick_take` | "X new listings hitting the market..." |

### inventory

| Data Field | Source | Value |
|---|---|---|
| **Hero metric (h1)** | `_get_hero_4_metrics` | Active Listings count |
| **Supporting metrics** | h2: New This Month, h3: Median DOM, h4: Months of Inventory |  |
| **Listings data** | ✅ Active listings (address, price, beds, baths, sqft, DOM, photo) | Up to 10 rows |
| **AI insight** | `_get_insight_paragraph` | AI or template fallback |
| **Quick take** | `_get_quick_take` | "X active listings on the market..." |

### closed

| Data Field | Source | Value |
|---|---|---|
| **Hero metric (h1)** | `_get_hero_4_metrics` | Total Closed count |
| **Supporting metrics** | h2: Median Price, h3: Avg DOM, h4: Close-to-List Ratio |  |
| **Listings data** | ✅ Closed sales (address, price, beds, baths, sqft, DOM, close_price, photo) | Up to 10 rows |
| **AI insight** | `_get_insight_paragraph` | AI or template fallback |
| **Quick take** | `_get_quick_take` | "X homes sold at a median of..." |

### price_bands

| Data Field | Source | Value |
|---|---|---|
| **Hero metric (h1)** | `_get_hero_4_metrics` | Total Listings count |
| **Supporting metrics** | h2: Median Price, h3: Avg DOM, h4: Price Range |  |
| **Listings data** | None | — |
| **AI insight** | `_get_insight_paragraph` | AI or template fallback |
| **Quick take** | `_get_quick_take` | "The market spans from..." |
| **Extra sections** | `price_bands` list | [{name, range, count},...] |

**V16 note:** `price_bands` data is computed but NOT passed to `_build_market_narrative_body`. Dead data.

### open_houses

| Data Field | Source | Value |
|---|---|---|
| **Hero metric** | `_get_metrics_for_report_type` (3-metric legacy) | Open Houses count |
| **Supporting metrics** | m2: Saturday count, m3: Sunday count |  |
| **Listings data** | None | — |
| **AI insight** | None (`has_insight: False`) | — |
| **Quick take** | `_get_quick_take` | "X open houses this weekend..." |

**Note:** Only report type with NO `has_hero_4`, NO `has_insight`. Uses legacy 3-metric path.

### new_listings_gallery

| Data Field | Source | Value |
|---|---|---|
| **Hero metric** | None (gallery layout skips hero) | — |
| **Listings data** | ✅ Photo gallery listings (address, price, beds, baths, sqft, photo_url, city, zip) | 1–9+ listings |
| **AI insight** | `_get_insight_paragraph` | AI or template fallback |
| **Quick take** | `_get_quick_take` | — |
| **Gallery label** | From `preset_display_name` or "New Listings" | — |
| **Filter description** | From schedule config | "Single Family Homes · $500K – $2M · 3+ Bedrooms" |

### featured_listings

| Data Field | Source | Value |
|---|---|---|
| **Hero metric** | None (gallery layout skips hero) | — |
| **Listings data** | ✅ Top 4 by price (address, price, beds, baths, sqft, photo_url, city, zip) | Typically 4 listings |
| **AI insight** | `_get_insight_paragraph` | AI or template fallback |
| **Quick take** | `_get_quick_take` | — |
| **Gallery label** | "Featured Listings" | — |
| **Filter description** | From schedule config | — |

### Listing Fields Used Across All Types

| Field | Photo Cards | Property Rows | Sales Table |
|---|---|---|---|
| `hero_photo_url` | ✅ | ✅ | — |
| `street_address` | ✅ | ✅ | ✅ |
| `city` | ✅ | ✅ | — |
| `zip_code` | ✅ | ✅ | — |
| `list_price` | ✅ | ✅ | ✅ |
| `close_price` | ✅ (fallback) | ✅ (fallback) | ✅ |
| `bedrooms` | ✅ | ✅ | ✅ |
| `bathrooms` | ✅ | ✅ | ✅ |
| `sqft` | ✅ | ✅ | — |
| `days_on_market` | — | — | ✅ |

---

## 3. Gallery Layout Selection Logic

Location: `_select_gallery_layout()` at line ~900 of template.py.

```
Listing Count → Layout
─────────────────────────────
  0 listings  → single_stacked (empty state — shows AI narrative + CTA only)
  1 listing   → single_stacked (full-width 240px hero card)
  2 listings  → single_stacked (2 full-width cards with gradient dividers)
  3 listings  → single_stacked (3 full-width cards with gradient dividers)
  4 listings  → gallery_2x2   (2×2 grid, 180px photos, 20px serif prices)
  5 listings  → large_list    (photo-left rows, 160×120 photos)
  6 listings  → gallery_3x2   (3×2 grid, 110px photos, 15px serif prices)
  7 listings  → large_list
  8 listings  → large_list
  9 listings  → gallery_3x2
  10+ listings → large_list
```

**Selection is based solely on listing count.** There is no per-report-type or per-config override. Both `new_listings_gallery` and `featured_listings` use the same auto-selection logic.

**Current thresholds:**
- `<= 3` → `single_stacked`
- `== 4` → `gallery_2x2`
- `== 6 or 9` → `gallery_3x2`
- Everything else (5, 7, 8, 10+) → `large_list`

**Observation:** Count 5 maps to `large_list` but could be a good fit for `gallery_3x2` (two rows of 3 with one empty cell). Count 8 maps to `large_list` but could work as `gallery_2x2` (two pages of 4).

---

## 4. Active vs Deprecated Types

| Report Type | API Route | Query Builder | Report Builder | Frontend Wizard | Email Template | Status |
|---|---|---|---|---|---|---|
| `market_snapshot` | ✅ `schedules.py:80` | ✅ 3 queries | ✅ `build_market_snapshot_result` | ✅ | ✅ | **Active** |
| `new_listings` | ✅ `schedules.py:79` | ✅ `build_new_listings` | ✅ `build_new_listings_result` | ✅ | ✅ | **Active** |
| `inventory` | ✅ `schedules.py:81` | ✅ `build_inventory_by_zip` | ✅ `build_inventory_result` | ✅ | ✅ | **Active** |
| `closed` | ✅ `schedules.py:80` | ✅ `build_closed` | ✅ `build_closed_result` | ✅ | ✅ | **Active** |
| `price_bands` | ✅ `schedules.py:82` | ✅ `build_price_bands` | ✅ `build_price_bands_result` | ✅ | ✅ | **Active** |
| `open_houses` | ✅ `schedules.py:83` | ✅ `build_open_houses` | Reuses `build_inventory_result` | ✅ | ✅ | **Active** |
| `new_listings_gallery` | ✅ `schedules.py:84` | ✅ `build_new_listings` | ✅ `build_new_listings_gallery_result` | ✅ | ✅ | **Active** |
| `featured_listings` | ✅ `schedules.py:85` | ✅ `build_new_listings` | ✅ `build_featured_listings_result` | ✅ | ✅ | **Active** |

**All 8 report types are fully wired** — API, query builder, report builder, frontend wizard, and email template. None are deprecated.

**Note:** `price_bands` and `open_houses` were marked for exclusion in the prompt spec, but the codebase shows them fully active across all layers. Removing them would require changes to:
1. API route Literal type
2. Frontend wizard options
3. REPORT_CONFIG dict
4. LAYOUT_MAP dict
5. Worker tasks.py report_type_map

---

## 5. Current Section Rendering Map

### market_snapshot → `market_narrative` layout

```
✅ Header (gradient + VML fallback)
✅ AI Insight (16px narrative paragraph)
✅ Hero Metric (56px serif — Median Sale Price)
✅ Stacked Stats (3 secondary: Closed Sales, Avg DOM, MOI)
   + Core Indicators appended (New Listings, Pending, Sale-to-List)
❌ Property Types breakdown (computed but NOT passed to layout builder)
❌ Price Tiers breakdown (computed but NOT passed to layout builder)
❌ Photo Gallery (no listings passed)
❌ Listings Table (no listings passed)
✅ Quick Take (accent callout card)
✅ CTA Button (View Full Report)
✅ Agent Footer (branded bg, serif name, pill buttons)
✅ Footer (Powered by, Unsubscribe)
```

### new_listings → `market_narrative` layout

```
✅ Header (gradient)
✅ AI Insight
✅ Hero Metric (New Listings count)
✅ Stacked Stats (3 secondary: Median Price, Avg DOM, Avg $/SqFt)
❌ Photo Gallery
❌ Listings Table
✅ Quick Take
✅ CTA Button
✅ Agent Footer
✅ Footer
```

### inventory → `closed_sales` layout

```
✅ Header (gradient)
✅ AI Insight
✅ Hero Metric (Active Listings count)
✅ Photo Cards (2×2 grid with Active badge, if 2+ listings)
✅ Sales Table (branded header, address/bd-ba/price/DOM columns)
✅ Stacked Stats (3 secondary: New This Month, Median DOM, MOI)
✅ Quick Take
✅ CTA Button (Get Your Home's Value)
✅ Agent Footer
✅ Footer
```

### closed → `closed_sales` layout

```
✅ Header (gradient)
✅ AI Insight
✅ Hero Metric (Total Closed count)
✅ Photo Cards (2×2 grid with Sold badge, if 2+ listings)
✅ Sales Table (branded header, address/bd-ba/price/DOM columns)
✅ Stacked Stats (3 secondary: Median Price, Avg DOM, Close-to-List)
✅ Quick Take
✅ CTA Button (Get Your Home's Value)
✅ Agent Footer
✅ Footer
```

### price_bands → `market_narrative` layout

```
✅ Header (gradient)
✅ AI Insight
✅ Hero Metric (Total Listings count)
✅ Stacked Stats (3 secondary: Median Price, Avg DOM, Price Range)
❌ Price Bands visual breakdown (computed but NOT passed to layout builder)
❌ Photo Gallery
❌ Listings Table
✅ Quick Take
✅ CTA Button
✅ Agent Footer
✅ Footer
```

### open_houses → `market_narrative` layout

```
✅ Header (gradient)
❌ AI Insight (has_insight: False)
✅ Hero Metric (Open Houses count — via legacy 3-metric fallback)
✅ Stacked Stats (2 secondary: Saturday, Sunday — via legacy 3-metric fallback)
❌ Photo Gallery
❌ Listings Table
✅ Quick Take
✅ CTA Button
✅ Agent Footer
✅ Footer
```

### new_listings_gallery → `gallery` layout (auto-selects by count)

```
✅ Header (gradient)
✅ Section Label ("New Listings")
✅ AI Insight
✅ Filter Blurb (if filter_description provided)
✅ Gallery Count Badge (branded pill)
✅ Photo Cards (layout auto-selected: single_stacked / 2×2 / 3×2 / large_list)
✅ Quick Take (except single_stacked)
✅ CTA Button
✅ Agent Footer
✅ Footer
```

### featured_listings → `gallery` layout (auto-selects by count)

```
✅ Header (gradient)
✅ Section Label ("Featured Properties")
✅ AI Insight
✅ Filter Blurb (if filter_description provided)
✅ Gallery Count Badge (branded pill)
✅ Photo Cards (layout auto-selected — typically gallery_2x2 with 4 listings)
✅ Quick Take (except single_stacked)
✅ CTA Button
✅ Agent Footer
✅ Footer
```

---

## 6. V0 Layout Recommendations

### Current LAYOUT_MAP (V16)

| Report Type | V16 Layout | V0 Reference File | Notes |
|---|---|---|---|
| `market_snapshot` | `market_narrative` | `market-narrative.tsx` | ✅ Good fit — hero + stats + optional photos |
| `new_listings` | `market_narrative` | `market-narrative.tsx` | ✅ Good fit — hero + stats, no photos |
| `inventory` | `closed_sales` | `closed-sales-table.tsx` | ✅ Good fit — hero + photo grid + data table |
| `closed` | `closed_sales` | `closed-sales-table.tsx` | ✅ Good fit — hero + SOLD grid + data table |
| `price_bands` | `market_narrative` | `market-narrative.tsx` | ⚠️ Missing price bands visual (data computed but not rendered) |
| `open_houses` | `market_narrative` | `market-narrative.tsx` | ⚠️ No AI insight, no hero_4 — falls back to legacy 3-metric path |
| `new_listings_gallery` | `gallery` (auto) | `gallery-3x2.tsx` / `gallery-2x2.tsx` / `single-stacked.tsx` / `large-list.tsx` | ✅ Auto-selects by listing count |
| `featured_listings` | `gallery` (auto) | `gallery-2x2.tsx` (typically) | ✅ Typically 4 listings → gallery_2x2 |

### Gallery Auto-Selection

| Listing Count | Layout | V0 Reference |
|---|---|---|
| 0 | single_stacked (empty) | `single-stacked.tsx` |
| 1–3 | single_stacked | `single-stacked.tsx` |
| 4 | gallery_2x2 | `gallery-2x2.tsx` |
| 5 | large_list | `large-list.tsx` |
| 6 | gallery_3x2 | `gallery-3x2.tsx` |
| 7–8 | large_list | `large-list.tsx` |
| 9 | gallery_3x2 | `gallery-3x2.tsx` |
| 10+ | large_list | `large-list.tsx` |

### Recommended Exclusions (per product decision)

- **`price_bands`** — Excluding per product decision. Currently active in all layers; removal requires API, worker, frontend, and template changes.
- **`open_houses`** — Excluding per product decision (MLS status data unreliable). Currently active in all layers; same removal scope.

### 6 Active Types (post-exclusion)

| Report Type | Layout | Purpose |
|---|---|---|
| `market_snapshot` | Market Narrative | Comprehensive market overview with hero + 6 stats |
| `new_listings` | Market Narrative | New listings summary with hero + 3 stats |
| `closed` | Closed Sales Table | Sold homes: hero + photo grid + data table |
| `inventory` | Closed Sales Table | Active supply: hero + photo grid + data table |
| `new_listings_gallery` | Gallery (auto) | Photo-first newest listings, audience-capped |
| `featured_listings` | Gallery (auto) | Top 4 by price, photo-first showcase |

---

## 7. Open Questions

### Q1: `new_listings` vs `new_listings_gallery` distinction

**Answer:** Same data source (`build_new_listings` query — Active status, list_date within lookback). Different report builders:
- `new_listings` → `build_new_listings_result` — returns KPIs (median, avg DOM, avg ppsf) with optional `listings_sample` for table display.
- `new_listings_gallery` → `build_new_listings_gallery_result` — returns `gallery_listings` with photo URLs (proxied via R2), audience-based cap (6–9 listings), 3-column grid layout.

The email template renders `new_listings` as Market Narrative (stats-only) and `new_listings_gallery` as Gallery (photo cards).

### Q2: `featured_listings` vs `new_listings_gallery` distinction

**Answer:** Same query (`build_new_listings`), different selection logic:
- `featured_listings` → `build_featured_listings_result` — ALL active listings sorted by `list_price` desc, top 4. No date filter. Fixed "luxury" audience. Always exactly 4 listings → always `gallery_2x2` layout.
- `new_listings_gallery` → sorted by `list_date` desc, audience-capped (6–9). Date-filtered to lookback window. Variable listing count → auto-selects gallery layout.

### Q3: `inventory` vs `closed` template differences

**Answer:** Both use the `closed_sales` layout (`_build_closed_sales_body`), but:
- `inventory` — hero is "Active Listings" count, photo badges say "Active", table shows active listings sorted by DOM desc.
- `closed` — hero is "Total Closed" count, photo badges say "Sold", table shows sold listings with close_price.

The layout is identical; only the data and labels differ.

### Q4: Gallery report with 0 listings

**Answer:** Falls into `single_stacked` layout (count <= 3). `_build_single_stacked_body` will render:
- AI insight (if available)
- No property cards (empty loop)
- CTA button

There is **no explicit empty state** — no "No listings found" message. The email just shows the AI narrative and CTA without any cards. This could be improved with a dedicated empty state component.

### Q5: `market_analytics` / `market_trends` report type

**Answer:** Neither exists as an email report type.
- `market_analytics` — exists only as a V0 design reference (`layouts/market-analytics.tsx`). Not wired to any report type. The `_build_analytics_body()` function exists in template.py but is never called by the LAYOUT_MAP routing.
- `market_trends` — exists only in the property PDF pipeline (`compute/market_trends.py`, `property_builder.py`). Not an email report type.

### Q6: Dead data in V16 architecture

The following data is computed in `schedule_email_html()` but **never passed** to layout builders:
- `property_types` (only for `market_snapshot`)
- `price_tiers` (only for `market_snapshot`)
- `price_bands` (only for `price_bands`)
- `extra_stats` (for `market_snapshot` and `closed`)
- `has_gallery` flag (replaced by LAYOUT_MAP routing)
- `has_listings_table` flag (replaced by LAYOUT_MAP routing)

These could be:
1. Wired into the layout builders (e.g., pass `property_types` to `_build_market_narrative_body`)
2. Removed if the product decision is to simplify the email content
3. Left as-is (harmless dead code) until a design decision is made

### Q7: `_build_analytics_body()` is orphaned

The function `_build_analytics_body()` was added in the V16 rewrite but is not referenced by `LAYOUT_MAP` or called anywhere. It implements the `market-analytics.tsx` V0 design (hero + trend stats + YoY comparison). It would need a new report type (e.g., `market_analytics`) to be wired up, or it could be used as an alternative layout for `market_snapshot`.
