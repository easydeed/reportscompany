# Module: Filter Resolver

> `apps/worker/src/worker/filter_resolver.py` (255 lines)

---

## Change Log

| Date | Change |
|------|--------|
| 2026-04 | **Audit:** Verified all function signatures and line numbers against code. Added `preset_display_name` passthrough (L103). Corrected `price_strategy` format to `{"mode": ..., "value": ...}` (nested dict, not top-level `price_pct`). Added exact line numbers. |
| 2026-01 | Added `elastic_widen_filters()` with 4-step progressive price widening. |
| 2025-12 | Added `build_filters_label()` for human-readable filter descriptions. |
| 2025-11 | Added 4 price strategy modes (list/close × min/max). |
| 2025-10 | Initial implementation with static price filters. |

---

## Purpose

Converts **market-adaptive filter "intents"** stored in a schedule's `filters` JSONB column into concrete SimplyRETS query parameters at report-generation time. This module is what makes the Smart Presets system "live" — the price caps are calculated dynamically against the current market median, not hardcoded at schedule creation.

It also handles **elastic widening**: if the resolved filters produce fewer than 6 listings, the module progressively relaxes the price strategy until results are sufficient.

---

## Key Functions / Classes

| Name | Signature | Line | Description |
|------|-----------|------|-------------|
| `compute_market_stats` | `(listings: List[Dict]) → Dict[str, Optional[float]]` | L29 | Derive median list/close prices from raw listings |
| `resolve_filters` | `(filters_intent: Dict[str, Any], market_stats: Dict[str, Optional[float]]) → Dict[str, Any]` | L65 | Convert intent → concrete SimplyRETS params |
| `build_filters_label` | `(filters_intent: Dict[str, Any], resolved_filters: Dict[str, Any], market_stats: Dict[str, Optional[float]]) → str` | L152 | Human-readable label for PDF/email headers |
| `elastic_widen_filters` | `(filters_intent: Dict[str, Any], market_stats: Dict[str, Optional[float]], current_results_count: int, min_results: int = 6) → Optional[Dict[str, Any]]` | L198 | Progressive price relaxation when results are thin |

---

## Inputs / Outputs

### `compute_market_stats` (L29–62)

| Direction | Field | Type | Notes |
|-----------|-------|------|-------|
| In | `listings` | `List[Dict]` | Raw SimplyRETS listing objects (Active, Pending, or Closed) |
| Out | `median_list_price` | `float \| None` | Median asking price (Active + Pending listings only) |
| Out | `median_close_price` | `float \| None` | Median close price (Closed listings only) |
| Out | `count` | `int` | Total listings passed in |

**Note:** Computed BEFORE applying bed/bath filters so the market median is stable and representative.

### `resolve_filters` (L65–149)

Converts intent → concrete SimplyRETS filter params.

| Direction | Field | Type | Notes |
|-----------|-------|------|-------|
| In | `filters_intent` | `dict` | Contains `minbeds`, `minbaths`, `subtype`, `preset_display_name`, `price_strategy` |
| In | `filters_intent.price_strategy` | `dict` | `{"mode": "maxprice_pct_of_median_list", "value": 0.70}` |
| In | `market_stats` | `dict` | Output of `compute_market_stats()` |
| Out | resolved params | `dict` | Concrete `type`, `minbeds`, `minbaths`, `subtype`, `maxprice`/`minprice` for SimplyRETS |

**Always sets `type: "RES"` (L100)** to exclude rentals.

**Passthrough keys (L103):** `minbeds`, `minbaths`, `subtype`, `preset_display_name`

**`_resolved_from` metadata:** When a price strategy is resolved, the dict includes a `_resolved_from` string (e.g., `"70% of median list $2,400,000"`) for labeling purposes.

### `build_filters_label` (L152–195)

Returns a human-readable label for the filter set, used in PDF/email headers.

**Examples:**
- `"2+ beds, 2+ baths, SFR, under $1,680,000 (70% of median list $2,400,000)"`
- `"4+ beds, all prices"`
- `"Condos, 1+ beds"`
- `"All listings"`

### `elastic_widen_filters` (L198–254)

If `current_results_count < min_results`, returns a new `filters_intent` with a relaxed price strategy. Returns `None` if no further widening is possible.

Widened dicts include `"_widened": True` and `"_widened_reason": "Expanded price range from 70% to 85%"`.

---

## Price Strategy Modes

| Mode | Description | Example (70%) |
|------|-------------|---------------|
| `maxprice_pct_of_median_list` | Cap price at X% of median list price | ≤70% of $800k = $560k cap |
| `maxprice_pct_of_median_close` | Cap price at X% of median close price | ≤70% of $785k = $549.5k cap |
| `minprice_pct_of_median_list` | Floor price at X% of median list price | ≥150% of $800k = $1.2M floor |
| `minprice_pct_of_median_close` | Floor price at X% of median close price | ≥150% of $785k = $1.178M floor |
| _(none)_ | Absolute `maxprice`/`minprice` values — no market calculation | Pass through as-is |

**Fallback (L134–140):** If a price strategy is set but market stats are unavailable (e.g., no Active listings to compute median), falls back to absolute `maxprice`/`minprice` values from `filters_intent` if present, otherwise no price filter.

---

## Elastic Widening Sequence

If `current_results_count < min_results` (default 6), `elastic_widen_filters` adjusts the `value` in `price_strategy`:

**For `maxprice_*` strategies (First-Time Buyer, Investor):**

| Step | value |
|------|-------|
| Initial | 0.70 |
| Widen 1 | 0.85 |
| Widen 2 | 1.00 |
| Widen 3 | 1.20 |
| Exhausted | `None` |

**For `minprice_*` strategies (Luxury):**

| Step | value |
|------|-------|
| Initial | 1.50 |
| Widen 1 | 1.30 |
| Widen 2 | 1.10 |
| Widen 3 | 0.90 |
| Exhausted | `None` |

---

## Smart Preset Definitions

| Preset | type | minbeds | minbaths | price_strategy.mode | price_strategy.value |
|--------|------|---------|----------|---------------------|---------------------|
| First-Time Buyer | SFR | 2 | 2 | `maxprice_pct_of_median_list` | 0.70 |
| Investor Deals | All | — | — | `maxprice_pct_of_median_close` | 0.50 |
| Luxury Showcase | SFR | — | — | `minprice_pct_of_median_list` | 1.50 |
| Condo Watch | Condo | 1 | — | — | — |
| Family Homes | SFR | 4 | 2 | — | — |

Preset definitions live in `packages/ui/src/components/schedules/types.ts` (`SMART_PRESETS`).

---

## Dependencies

### Internal

| Module | Usage |
|--------|-------|
| `apps/worker/src/worker/vendors/simplyrets.py` | Caller fetches baseline market listings, passes to `compute_market_stats` |
| `apps/worker/src/worker/tasks.py` | Calls `resolve_filters()`, `elastic_widen_filters()`, `build_filters_label()` during report generation |

### External

| Library | Usage |
|---------|-------|
| `statistics` (stdlib) | `statistics.median()` for price calculations |
| `typing` (stdlib) | Type hints |

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| No listings to compute stats | `median_list_price = None`, `median_close_price = None` (L59–61) |
| Strategy set but no market_stats | Falls back to absolute price values from `filters_intent`, or no price filter (L134–140) |
| `elastic_widen_filters` exhausted | Returns `None` — caller sends report with available (possibly 0) results |
| Median is 0 or None | `resolve_filters` skips price filter entirely |
| No `price_strategy` in intent | Passes through absolute `maxprice`/`minprice` if present (L142–147) |

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
