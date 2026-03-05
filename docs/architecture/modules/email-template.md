# Module: Email Template (V16)

> `apps/worker/src/worker/email/template.py`

---

## Purpose

Generates email-safe HTML for all scheduled email reports using Python f-strings. This is the **only** file that produces email HTML — all 8 report types flow through `schedule_email_html()`, which delegates to modular layout builders.

---

## Architecture (V16 — Modular)

### Entry Point

```
schedule_email_html(report_type, data, brand, profile) → str
```

Accepts report type, MLS data dict, brand dict (colors, logos, display name), and agent profile. Returns a complete email HTML string.

### Color System

Colors are fully parameterized — no hardcoded brand colors anywhere:

| Variable | Source | Fallback |
|---|---|---|
| `primary_color` | `brand["primary_color"]` | `#6366f1` |
| `accent_color` | `brand["accent_color"]` | `#8b5cf6` |

These flow into every gradient, border, text color, button, and tinted background via f-strings.

### Component Layers

```
┌────────────────────────────────────────────┐
│  schedule_email_html()                     │
│  ├─ Email wrapper (head, CSS, VML)         │
│  ├─ Header gradient                        │
│  ├─ LAYOUT_MAP[report_type] → body builder │
│  ├─ Agent footer                           │
│  └─ Email footer                           │
├────────────────────────────────────────────┤
│  Layout Body Builders (7)                  │
│  ├─ _build_market_narrative_body           │
│  ├─ _build_gallery_2x2_body               │
│  ├─ _build_gallery_3x2_body               │
│  ├─ _build_single_stacked_body            │
│  ├─ _build_large_list_body                │
│  ├─ _build_closed_sales_body              │
│  └─ _build_analytics_body                 │
├────────────────────────────────────────────┤
│  Photo Card Builders (6)                   │
│  ├─ _build_photo_card_2x2                 │
│  ├─ _build_gallery_card_large             │
│  ├─ _build_gallery_card_compact           │
│  ├─ _build_stacked_property_card          │
│  ├─ _build_photo_card_with_badge          │
│  └─ _build_property_row                   │
├────────────────────────────────────────────┤
│  Shared Component Helpers (9+)             │
│  ├─ _build_ai_narrative                   │
│  ├─ _build_hero_stat                      │
│  ├─ _build_gallery_count                  │
│  ├─ _build_quick_take                     │
│  ├─ _build_cta                            │
│  ├─ _build_section_label                  │
│  ├─ _build_filter_blurb                   │
│  ├─ _build_stacked_stats                  │
│  ├─ _build_branded_divider                │
│  ├─ _build_trend_stats                    │
│  └─ _build_yoy_comparison                 │
└────────────────────────────────────────────┘
```

### Routing

```python
LAYOUT_MAP = {
    "market_snapshot": "market_narrative",
    "new_listings_gallery": _select_gallery_layout,  # adaptive
    "closed": "closed_sales",
    "inventory": "closed_sales",
    "price_bands": "analytics",
    "open_houses": "gallery_3x2",
    "featured_listings": "gallery_2x2",
    "new_listings": "large_list",
}
```

### Adaptive Gallery Layout

`_select_gallery_layout(listing_count)` selects the best layout based on how many listings the filter returned:

| Count | Layout | Builder |
|---|---|---|
| 0-3 | Single stacked | `_build_single_stacked_body` |
| 4 | 2×2 grid | `_build_gallery_2x2_body` |
| 5-6 | 3×2 grid | `_build_gallery_3x2_body` |
| 7+ | Large list | `_build_large_list_body` |

---

## Report Types (8)

| Type | Layout | Has Hero | Has Gallery | Has Table |
|---|---|---|---|---|
| `market_snapshot` | Market Narrative | Yes (median price) | Yes (2×2) | No |
| `new_listings_gallery` | Adaptive | Yes (count) | Yes (adaptive) | No |
| `closed` | Closed Sales | Yes (total closed) | Yes (2×2 SOLD) | Yes |
| `inventory` | Closed Sales | Yes (active count) | Yes (2×2 Active) | Yes |
| `price_bands` | Analytics | Yes | No | No |
| `open_houses` | Gallery 3×2 | Yes | Yes (3×2) | No |
| `featured_listings` | Gallery 2×2 | Yes | Yes (2×2) | No |
| `new_listings` | Large List | Yes | Yes (vertical) | No |

---

## Email Client Compatibility

- Table-based layout (no CSS Grid/Flexbox)
- VML fallback for Outlook gradient headers
- `color-scheme: light only` (prevents dark mode override)
- Dark mode CSS removed (no `.dark-card` class)
- Georgia serif for hero stats, system sans elsewhere
- All backgrounds explicitly `#ffffff` for content areas

---

## Related Files

| File | Purpose |
|---|---|
| `apps/worker/src/worker/tasks.py` | Calls `schedule_email_html()` in step 7 |
| `apps/worker/src/worker/email/__init__.py` | Package init |
| `scripts/gen_email_templates.py` | Dev script to generate all 8 types + adaptive variants |
| `output/email_reports/` | Generated HTML outputs for QA |
| `apps/web/components/shared/email-preview/` | React preview that mirrors V16 layouts |
