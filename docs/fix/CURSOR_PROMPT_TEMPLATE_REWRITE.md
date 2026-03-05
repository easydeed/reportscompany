# Cursor Prompt: Rewrite template.py Email Architecture

## CRITICAL: What This IS and IS NOT

**THIS IS:** A Python rewrite of `apps/worker/src/worker/email/template.py`
**THIS IS NOT:** Creating React/TSX files. The `.tsx` files in `apps/web/app/email-templates/layouts/` already exist as DESIGN REFERENCES. Do not touch them. Do not create new ones.

**The only file you are modifying is `template.py`.**

---

## Context

`template.py` is a ~2,020-line Python file that generates email-safe HTML using f-strings. It currently has one monolithic `schedule_email_html()` function that assembles all report types through inline conditionals.

The V0 React components in `apps/web/app/email-templates/layouts/` show what the emails SHOULD look like. Your job is translating those React designs into Python f-string HTML inside `template.py`.

Read `THEMED_EMAIL_IMPLEMENTATION.md` for the complete spec with every HTML code block ready to copy.

---

## What Currently Exists in template.py (Keep or Replace)

### KEEP — Do not modify these:
- `_format_price()` — price formatting helper
- `_get_hero_4_metrics()` — metric extraction helper  
- `_build_preheader()` — preheader text builder
- All `REPORT_CONFIG` dict entries — section toggle flags
- All `@media` CSS blocks (dark mode, mobile responsive)
- All `<!--[if mso]>` VML/Outlook conditionals in the header and agent footer
- The function signature of `schedule_email_html()` and its parameters
- The email wrapper HTML (outer `<table>`, body background, etc.)
- The header gradient HTML (already looks good)
- The agent footer HTML (already has serif name, pill buttons)
- The footer HTML (Powered by, Unsubscribe)

### REPLACE — These are the old builders to rewrite:
- `_build_vertical_list_html` → becomes part of `_build_large_list_body()` and `_build_single_stacked_body()`
- `_build_gallery_grid_html` → becomes `_build_gallery_2x2_body()` and `_build_gallery_3x2_body()`
- `_build_listings_table_html` → becomes part of `_build_closed_sales_body()`
- `_build_kpi_card_html` → replaced by `_build_trend_stats()` and `_build_hero_stat()`
- `_build_yoy_comparison_table_html` → replaced by `_build_yoy_comparison()`
- The inline f-string HTML blocks in `schedule_email_html()` that build the body content

### ADD — New functions that don't exist yet:
```python
# Shared component helpers
_build_ai_narrative(insight_text)
_build_hero_stat(value, label, trend, trend_positive, primary_color)
_build_gallery_count(count, label, primary_color)
_build_quick_take(quick_take, accent_color)
_build_cta(pdf_url, primary_color, cta_text)
_build_section_label(label, primary_color)
_build_filter_blurb(filter_text, primary_color)
_build_stacked_stats(stats)
_build_branded_divider(primary_color, accent_color)

# Photo card builders
_build_photo_card_2x2(listing, primary_color)
_build_gallery_card_large(listing, primary_color)
_build_gallery_card_compact(listing, primary_color)
_build_stacked_property_card(listing, primary_color, accent_color)
_build_photo_card_with_badge(listing, primary_color, accent_color, badge_text)
_build_property_row(listing, primary_color, is_last)

# Layout-specific body builders
_build_market_narrative_body(data, primary_color, accent_color)
_build_gallery_2x2_body(data, primary_color, accent_color)
_build_gallery_3x2_body(data, primary_color, accent_color)
_build_single_stacked_body(data, primary_color, accent_color)
_build_large_list_body(data, primary_color, accent_color)
_build_closed_sales_body(data, primary_color, accent_color)
_build_analytics_body(data, primary_color, accent_color)

# Data table builder
_build_sales_table(rows, primary_color)

# Trend stats builders
_build_trend_stats(stats)
_build_yoy_comparison(last_year, this_year, primary_color)

# Layout routing
_select_gallery_layout(report_type, listing_count)
LAYOUT_MAP dict
```

---

## Implementation Order (Follow This Exactly)

### Phase 1: Shared Component Helpers

Add these functions ABOVE schedule_email_html() in template.py. The exact HTML for each is in THEMED_EMAIL_IMPLEMENTATION.md sections 2A-2H.

1. `_build_ai_narrative()` — 16px text on white. NO background color, NO border. Just a `<p>` in a `<table>`.
2. `_build_hero_stat()` — 56px Georgia serif number, centered, with optional trend arrow below.
3. `_build_gallery_count()` — Branded pill badge + label + horizontal rule.
4. `_build_quick_take()` — Accent-colored callout card with `$` icon.
5. `_build_cta()` — Tinted container with branded button + VML Outlook fallback.
6. `_build_section_label()` — 20×2px accent bar + uppercase branded label.
7. `_build_filter_blurb()` — Optional report criteria callout.
8. `_build_stacked_stats()` — Full-width rows: label left, big serif number right.
9. `_build_branded_divider()` — 64px gradient bar between stacked cards.

### Phase 2: Photo Card Builders

10. `_build_photo_card_2x2()` — Card with 160px photo, 18px serif price, badges. Used in Market Narrative.
11. `_build_gallery_card_large()` — Card with 180px photo, 20px serif price. Used in Gallery 2×2.
12. `_build_gallery_card_compact()` — Card with 110px photo, 15px serif price. Used in Gallery 3×2.
13. `_build_stacked_property_card()` — Full-width 240px hero photo, 22px price, description. Used in Single Stacked.
14. `_build_photo_card_with_badge()` — Card with SOLD/NEW badge overlay. Used in Closed Sales.
15. `_build_property_row()` — Photo-left (160×120), details-right row. Used in Large List.

### Phase 3: Layout Body Builders

Each of these assembles the shared components + photo cards into a complete layout body. They return the HTML between the header and footer.

16. `_build_market_narrative_body()` — AI narrative → hero stat → 2×2 photos → stacked stats → quick take → CTA
17. `_build_gallery_2x2_body()` — AI narrative → gallery count → 2×2 large cards → quick take → CTA
18. `_build_gallery_3x2_body()` — AI narrative → gallery count → 3×2 compact cards → quick take → CTA
19. `_build_single_stacked_body()` — AI narrative → full-width cards with dividers → CTA
20. `_build_large_list_body()` — AI narrative → gallery count → property rows → quick take → CTA
21. `_build_closed_sales_body()` — AI narrative → hero stat → 2×2 SOLD photos → data table → quick take → CTA
22. `_build_analytics_body()` — AI narrative → hero stat with trend → trend stats → YoY comparison → quick take → CTA

### Phase 4: Routing & Integration

23. Add `LAYOUT_MAP` dict mapping report_type → layout builder function name
24. Add `_select_gallery_layout()` for auto-selecting gallery layout by listing count
25. Update `schedule_email_html()`:
    - Keep the header assembly (gradient, logo, badge, title, accent strip)
    - Keep the content wrapper (`<td style="background-color: #ffffff; padding: 40px;">`)
    - Replace the inline body HTML with a call to the appropriate layout builder
    - Keep the agent footer assembly
    - Keep the footer assembly (Powered by, Unsubscribe)
    - Keep the email wrapper closing tags

---

## HTML Rules (Non-Negotiable)

- **ALL layout = `<table role="presentation">`** — No `<div>` layouts, no flexbox, no CSS grid
- **ALL colors parameterized** — Use `{primary_color}` and `{accent_color}` f-string variables everywhere. Never hardcode `#1B365D` or `#B8860B`.
- **Background = WHITE** — `background-color: #ffffff` on the content area. NOT `#fafaf9` or `#f5f5f4`. Brand colors appear on elements (text, borders, badges, buttons), not backgrounds.
- **Serif font ONLY on numbers/prices** — `font-family: Georgia, 'Times New Roman', serif` for hero stats, prices, metric values. Everything else uses the system sans-serif stack.
- **Hex+alpha for subtle tints** — e.g., `{primary_color}0D` for badge backgrounds, `{accent_color}0F` for quick take background. These are progressive enhancements that degrade gracefully in Outlook.
- **Keep ALL existing Outlook VML** — The `<!--[if mso]>` blocks for header gradient, agent photo circle, CTA button. Don't remove them.
- **Keep ALL dark mode CSS** — `@media (prefers-color-scheme: dark)` stays untouched.
- **Keep ALL mobile CSS** — `@media only screen and (max-width: 600px)` stays untouched.

## Photo Size Reference

| Layout | Photo Dimensions | Price Font Size |
|--------|-----------------|-----------------|
| Single Stacked | full-width × 240px | 22px Georgia serif |
| Gallery 2×2 | half-width × 180px | 20px Georgia serif |
| Market Narrative grid | half-width × 160px | 18px Georgia serif |
| Closed Sales grid | half-width × 130px | 16px Georgia serif |
| Large List rows | 160px × 120px | 18px Georgia serif |
| Gallery 3×2 | third-width × 110px | 15px Georgia serif |

---

## V0 Design Reference Files (READ ONLY — Do Not Modify)

These show what each layout should look like visually:

| Layout | V0 File | Python Function |
|--------|---------|-----------------|
| Market Narrative | `layouts/market-narrative.tsx` | `_build_market_narrative_body()` |
| Gallery 2×2 | `layouts/gallery-2x2.tsx` | `_build_gallery_2x2_body()` |
| Gallery 3×2 | `layouts/gallery-3x2.tsx` | `_build_gallery_3x2_body()` |
| Single Stacked | `layouts/single-stacked.tsx` | `_build_single_stacked_body()` |
| Large List | `layouts/large-list.tsx` | `_build_large_list_body()` |
| Closed Sales | `layouts/closed-sales-table.tsx` | `_build_closed_sales_body()` |
| Market Analytics | `layouts/market-analytics.tsx` | `_build_analytics_body()` |
| Header | `layouts/email-header.tsx` | Keep existing header |
| Footer | `layouts/email-footer.tsx` | Keep existing agent footer |

---

## Verification

After implementation, generate test HTML for each report type:

```python
for rt in ['market_snapshot', 'new_listings', 'featured_listings',
           'new_listings_gallery', 'closed_sales', 'inventory',
           'price_bands', 'open_houses']:
    html = schedule_email_html(report_type=rt, ...)
    with open(f"/tmp/email_{rt}.html", "w") as f:
        f.write(html)
```

Open each in Chrome and verify:
- White background (not gray)
- Georgia serif on prices and hero stats
- Photos at correct heights per layout
- Brand colors flowing through elements
- Agent footer with pill buttons
- No broken HTML or missing sections
