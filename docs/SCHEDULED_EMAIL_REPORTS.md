# Scheduled Email Reports — Complete Catalog

What can agents send to their clients? This document covers every report type, audience preset, and combination currently available in the platform.

---

## The Big Picture

There are **8 base report types** and **6 audience filters** (including "All"). The audience filters only apply to listing-based reports, creating targeted variants like "Luxury New Listings" or "First-Time Buyer Homes."

In practice, the system produces up to **48 distinct email experiences** (8 types × 6 audiences), though not all combinations make sense. The most useful combos are called out below.

---

## Base Report Types

### Tier 1 — Primary (shown first in the wizard)

| Report | Internal Key | What It Shows | Best For |
|---|---|---|---|
| **Market Snapshot** | `market_snapshot` | Median sale price, closed sales count, DOM, months of inventory, pending sales, sale-to-list ratio, property type breakdown, price tier breakdown | Monthly market updates to sphere of influence |
| **New Listings** | `new_listings_gallery` | Photo gallery of recently listed homes with prices, beds/baths, sqft. Auto-selects layout by count (1–3: full cards, 4: 2×2 grid, 6: 3×2 grid, 7+: list) | Buyer alerts, prospecting, "just listed" campaigns |
| **Closed Sales** | `closed` | Total closed, median price, DOM, close-to-list ratio + photo grid of sold homes + data table with address, specs, price, DOM | CMAs, seller prospecting, "just sold" evidence |
| **Inventory Report** | `inventory` | Active listings count, new this month, median DOM, months of inventory + photo grid + data table | Market supply tracking, buyer patience coaching |

### Tier 2 — Secondary (collapsed under "Show More" in wizard)

| Report | Internal Key | What It Shows | Best For |
|---|---|---|---|
| **Price Bands** | `price_bands` | Total listings, median price, DOM, price range + tier analysis (Entry/Move-Up/Luxury) | Buyer/seller positioning, market segmentation |
| **Open Houses** | `open_houses` | Open house count, Saturday count, Sunday count | Weekend marketing, open house promotion |
| **Featured Listings** | `featured_listings` | Top 4 most expensive active listings with photos, always 2×2 grid | Agent listing promotion, luxury showcase |
| **New Listings (Table)** | `new_listings` | Same data as New Listings gallery but displayed as stats + metrics instead of photos | Weekly prospecting for data-oriented agents |

### What's the difference?

**New Listings vs New Listings Gallery** — Same MLS data, different presentation. `new_listings` shows stats and metrics (Market Narrative layout). `new_listings_gallery` shows photo cards (Gallery layout). Most agents pick the gallery version.

**Featured Listings vs New Listings Gallery** — Different selection logic. Featured always picks the 4 most expensive active homes regardless of when they listed. Gallery picks the newest homes within the lookback period. Featured = agent's best inventory. Gallery = what just hit the market.

**Inventory vs Closed** — Inventory shows active supply (what's available now). Closed shows recent sales (what already sold). Both use the same table+photo layout but with different data and labels.

---

## Audience Presets

When an agent selects **New Listings** (gallery or table), they can choose an audience filter. This narrows the listings to match a specific buyer profile.

| Audience | Internal Key | Filters Applied | Email Display Name |
|---|---|---|---|
| **All Listings** | `all` | No filters | — |
| **First-Time Buyers** | `first_time` | 2+ beds, 2+ baths, Single Family, ≤70% of area median price | "First-Time Buyer" |
| **Luxury Clients** | `luxury` | Single Family, ≥150% of area median price | "Luxury" |
| **Family Homes** | `families` | 3+ beds, 2+ baths, Single Family | "Family Homes" |
| **Condo Buyers** | `condo` | Condominiums only | "Condo Watch" |
| **Investor Deals** | `investors` | ≤50% of area median price | "Investor Deals" |

### How price filtering works

Price filters use **percentage of area median list price**, not fixed dollar amounts. This means:
- In Beverly Hills (median $3.2M): "First-Time Buyer" filters to homes ≤$2.24M
- In Riverside (median $520K): "First-Time Buyer" filters to homes ≤$364K

The system auto-scales to each market. If a filter returns too few results, "elastic widening" expands the price range to ensure the email has enough content.

### Audience caps (max listings per email)

| Audience | Max Listings |
|---|---|
| All | 24 |
| First-Time Buyers | 24 |
| Family Homes | 18 |
| Condo Buyers | 18 |
| Investors | 12 |
| Luxury | 8 |
| Featured Listings | 4 (fixed) |

---

## Real-World Combinations

Here are the most common scheduled email setups agents use:

### The Sphere Package (monthly)
- **Market Snapshot** → entire database
- **Closed Sales** → past clients, sphere

### The Buyer Drip (weekly)
- **New Listings Gallery + First-Time Buyer** → first-time buyer leads
- **New Listings Gallery + Luxury** → high-net-worth leads
- **New Listings Gallery + Families** → family relocation leads
- **New Listings Gallery + Condo** → condo buyer leads

### The Investor Package (biweekly)
- **New Listings Gallery + Investor Deals** → investor contacts
- **Inventory Report** → investor contacts (supply analysis)

### The Listing Agent Package (weekly)
- **Featured Listings** → agent's sphere (showcasing their own inventory)
- **Market Snapshot** → seller prospects

---

## What's NOT in the system

These have been discussed but do not currently exist as report types:

| Concept | Status | Notes |
|---|---|---|
| **Below Market** | Not a preset | Closest equivalent is "Investor Deals" (≤50% median) |
| **Starter Homes** | Not a preset | Closest equivalent is "First-Time Buyer" (≤70% median, 2+/2+, SFR) |
| **Market Analytics / Trends** | No email report | Exists only as a property PDF page. V0 design reference (`market-analytics.tsx`) and builder function (`_build_analytics_body`) exist but are not wired to any report type |
| **Year-over-Year Comparison** | No email report | `_build_yoy_comparison()` function exists in template.py but is never called |
| **Price Reduction Alerts** | Does not exist | Would require a new query builder tracking price changes |
| **Back on Market** | Does not exist | Would require status change tracking |
| **Expired Listings** | Does not exist | Would need access to expired/withdrawn MLS status |
| **Coming Soon** | Does not exist | Would need "Coming Soon" status from MLS |

---

## Where Everything Lives

| Layer | File | What It Does |
|---|---|---|
| **Wizard UI (v0)** | `apps/web/components/v0-report-builder/types.ts` | Defines `ReportType`, `AudienceFilter`, `AUDIENCE_FILTER_PRESETS` |
| **Wizard UI (schedule)** | `apps/web/components/schedule-builder/types.ts` | Parallel definitions for the schedule builder |
| **Report type selector** | `apps/web/components/v0-report-builder/step-report-type.tsx` | Primary/Secondary type cards + audience pills |
| **API validation** | `apps/api/src/api/routes/schedules.py` | `ScheduleCreate` model with `report_type` Literal |
| **Filter resolution** | `apps/worker/src/worker/filter_resolver.py` | Converts audience presets to MLS query filters |
| **Report builders** | `apps/worker/src/worker/report_builders.py` | Builds report data per type, applies audience caps |
| **Email template** | `apps/worker/src/worker/email/template.py` | V16 layout-based HTML generation |
| **AI insights** | `apps/worker/src/worker/ai_insights.py` | Audience-aware narrative generation + email caps |
