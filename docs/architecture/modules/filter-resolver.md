# Module: Filter Resolver

> `apps/worker/src/worker/filter_resolver.py`

---

## Purpose

Converts **market-adaptive filter "intents"** stored in a schedule's `filters_intent` JSON blob into concrete SimplyRETS query parameters at report-generation time. This module is what makes the Smart Presets system "live" — the price caps are calculated dynamically against the current market median, not hardcoded at schedule creation.

It also handles **elastic widening**: if the resolved filters produce fewer than 6 listings, the module progressively relaxes the price strategy until results are sufficient.

---

## Inputs / Outputs

### `compute_market_stats(listings: list[dict]) → MarketStats`

| Direction | Field | Notes |
|-----------|-------|-------|
| In | `listings` | Raw SimplyRETS listing objects (Active or Closed) |
| Out | `median_list_price` | Median asking price (from Active listings) |
| Out | `median_close_price` | Median close price (from Closed listings) |

**Note:** Computed BEFORE applying bed/bath filters so the market median is stable and representative.

### `resolve_filters(filters_intent: dict, market_stats: MarketStats) → dict`

Converts intent → concrete SimplyRETS filter params.

| Direction | Field | Notes |
|-----------|-------|-------|
| In | `filters_intent.minbeds` | Minimum bedrooms |
| In | `filters_intent.minbaths` | Minimum bathrooms |
| In | `filters_intent.type` | SimplyRETS type |
| In | `filters_intent.price_strategy` | Price strategy mode (see below) |
| In | `filters_intent.price_pct` | Percentage of median for price strategy |
| In | `market_stats` | Output of `compute_market_stats()` |
| Out | Resolved params | Dict with concrete `minprice`/`maxprice` values ready for SimplyRETS |

### `build_filters_label(filters_intent: dict, resolved: dict) → str`

Returns a human-readable label for the filter set, used in PDF/email headers.

**Example:** `"3+ beds, 2+ baths, under $1,680,000 (70% of Irvine median)"`

### `elastic_widen_filters(filters_intent: dict, market_stats: MarketStats, current_count: int) → dict | None`

If `current_count < 6`, returns a new `filters_intent` with a relaxed price strategy.
Returns `None` if no further widening is possible.

---

## Price Strategy Modes

| Strategy | Description | Example (70%) |
|----------|-------------|---------------|
| `maxprice_pct_of_median_list` | Cap price at X% of median list price | ≤70% of $800k = $560k cap |
| `maxprice_pct_of_median_close` | Cap price at X% of median close price | ≤70% of $785k = $549.5k cap |
| `minprice_pct_of_median_list` | Floor price at X% of median list price | ≥150% of $800k = $1.2M floor |
| `minprice_pct_of_median_close` | Floor price at X% of median close price | ≥150% of $785k = $1.178M floor |
| _(none)_ | Absolute price values — no market calculation | Pass through as-is |

---

## Elastic Widening Sequence

If `current_count < 6`, `elastic_widen_filters` adjusts `price_pct` progressively:

**For `maxprice_*` strategies (First-Time Buyer, Investor):**

| Step | price_pct |
|------|-----------|
| Initial | 70% |
| Widen 1 | 85% |
| Widen 2 | 100% |
| Widen 3 | 120% |
| Exhausted | `None` |

**For `minprice_*` strategies (Luxury):**

| Step | price_pct |
|------|-----------|
| Initial | 150% |
| Widen 1 | 130% |
| Widen 2 | 110% |
| Widen 3 | 90% |
| Exhausted | `None` |

---

## Smart Preset Definitions

| Preset | type | minbeds | minbaths | price_strategy | price_pct |
|--------|------|---------|----------|----------------|-----------|
| First-Time Buyer | SFR | 2 | 2 | `maxprice_pct_of_median_list` | 70 |
| Investor Deals | All | — | — | `maxprice_pct_of_median_close` | 50 |
| Luxury Showcase | SFR | — | — | `minprice_pct_of_median_list` | 150 |
| Condo Watch | Condo | 1 | — | — | — |
| Family Homes | SFR | 4 | 2 | — | — |

---

## Key Functions / Classes

| Name | Description |
|------|-------------|
| `compute_market_stats` | Derives median prices from raw listing arrays |
| `resolve_filters` | Applies price strategy to produce concrete SimplyRETS params |
| `build_filters_label` | Human-readable filter description for report headers |
| `elastic_widen_filters` | Progressive price relaxation when results are thin |

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `apps/worker/src/worker/vendors/simplyrets.py` | Fetches baseline market listings for `compute_market_stats` |
| `apps/worker/src/worker/tasks.py` | Calls `resolve_filters` and `elastic_widen_filters` during report generation |

### External
| Library | Usage |
|---------|-------|
| `statistics` (stdlib) | `statistics.median()` for price calculations |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| No listings to compute stats | `median_list_price = None`, `median_close_price = None` |
| Strategy set but no market_stats | Falls back to absolute price values (or no price filter) |
| `elastic_widen_filters` exhausted | Returns `None` — caller sends report with available (possibly 0) results |
| Median is 0 or None | `resolve_filters` skips price filter entirely |

---

## Tests / How to Validate

```bash
# Delivered reports use filter resolution; QA tool exercises the full path
python qa_deliver_reports.py \
  --base-url https://reportscompany.onrender.com \
  --token $JWT_TOKEN \
  --deliver-to qa@example.com \
  --city Irvine

# Test report flow (exercises filter_resolver in worker context)
python scripts/test_report_flow.py
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01 | Added `elastic_widen_filters()` with 4-step progressive price widening |
| 2025-12 | Added `build_filters_label()` for human-readable filter descriptions in reports |
| 2025-11 | Added 4 price strategy modes (list/close × min/max) |
| 2025-10 | Initial implementation with static price filters |
