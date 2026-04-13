# Skill: Market Report PDF Templates

> Place this file at `.cursor/rules/market-report-templates.md` or reference it in `.cursorrules`
> This skill applies when working on any file in `apps/worker/src/worker/templates/market/`

---

## What This Is

TrendyReports generates branded 8.5×11" PDF market reports for real estate agents. The PDFs are rendered by PDFShift (headless Chromium) from Jinja2 HTML templates. Every report must fit on exactly ONE letter page.

---

## The Rendering Pipeline

```
MarketReportBuilder.render_html()
  → Jinja2 template (market.jinja2 extends base.jinja2, imports macros.jinja2)
  → Complete HTML string
  → PDFShift (headless Chromium) captures at 8.5" × 11"
  → PDF bytes uploaded to R2
```

**Key implication:** PDFShift uses Chromium, so CSS Grid, Flexbox, and Google Fonts all work. But there is NO JavaScript execution — CSS only for layout. No `onerror` handlers, no `onload`, no DOM manipulation.

---

## Page Geometry — The Iron Rules

```css
.report-page {
  width: 8.5in;
  height: 11in;
  display: flex;
  flex-direction: column;
  overflow: hidden;        /* Content beyond 11in is CLIPPED, not paginated */
}
```

The page is a flex column. Sections stack vertically. The single-page constraint is enforced by `overflow: hidden` — if content exceeds 11 inches, it's invisible. There is no page 2.

**Section flex behavior:**
| Section | Flex | Why |
|---------|------|-----|
| `.report-header` | `flex-shrink: 0` | Header never compresses |
| `.content-zone` | `flex: 1` | Content absorbs remaining space |
| `.agent-footer` | `flex-shrink: 0` | Footer always visible |
| `.powered-by` | `flex-shrink: 0` | Footer always visible |

If content overflows, the `content-zone` clips internally. The footer is ALWAYS on the page.

---

## The 4 Layout Families

Every report type maps to one of 4 layouts. The layout is selected in `macros.jinja2` based on `report_type`.

### Layout A — Gallery
**Used by:** `new_listings_gallery`, `featured_listings`, `open_houses`
**Structure:** Header → 3×2 photo grid → footer
**Key CSS:**
```css
.gallery-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.listing-card .photo {
  aspect-ratio: 3/2.4;    /* NOT 16:9, NOT 4:3 — this specific ratio fits 6 cards on one page */
}
```
**Badges:**
- `featured_listings` → `.badge.featured` (gold, "Featured")
- `open_houses` → `.badge.time` (accent, "SAT 1-4PM")
- `new_listings_gallery` → no badge

### Layout B — Market Narrative
**Used by:** `market_snapshot`
**Structure:** Header → hero metric + AI insight (side by side) → 4-col photo grid with overlays → stats bar → quick take → footer
**Key CSS:**
```css
.snapshot-top {
  display: flex;
  gap: 10px;
}
.hero-metric {
  width: 110px;         /* Fixed width — does not grow */
  flex-shrink: 0;
}
.ai-insight {
  flex: 1;              /* Takes remaining width */
}
.photo-grid-4 {
  flex: 1;
  grid-template-columns: repeat(4, 1fr);
}
```
**Photo overlay pattern:** Price and address are overlaid on the photo using absolute positioning + gradient fade:
```css
.photo-item .overlay {
  position: absolute;
  bottom: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 100%);
}
```

### Layout C — Closed/Inventory
**Used by:** `closed`, `inventory`
**Structure:** Header → 5-col grid (hero card + 4 photo cards) → data table → small stats bar → quick take → footer
**Key CSS:**
```css
.ci-grid-5 {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}
.ci-hero {
  aspect-ratio: 3/2.5;   /* Same ratio as photo cards so they align */
}
```
**Status badges on photos:**
- `closed` → `.status-badge.sold` (red)
- `inventory` → `.status-badge.active` (green) or `.status-badge.pending` (yellow)
**Data table:** 9px font, compact padding (4px 3px), accent header row optional.

### Layout D — Analytics
**Used by:** `price_bands`, `new_listings`
**Structure:** Header → hero metric + stat cards row → vertical listing rows → quick take → footer
**Key CSS:**
```css
.analytics-hero {
  width: 90px;
  flex-shrink: 0;
}
.listing-row .thumb {
  width: 120px;
  aspect-ratio: 4/3;
}
```
**Listing rows** are horizontal cards: thumbnail left, info center, price right, badge far right.

---

## The Header

The header uses the V0 gradient design with brand logo, badge, and title.

```html
<header class="report-header">
  <div class="header-top">
    <div class="header-brand">
      <img class="header-logo" src="{{ agent.logo_url }}" alt="Logo">
      <span class="header-brand-name">{{ agent.company_name }}</span>
    </div>
    <span class="header-badge">Closed Sales</span>
  </div>
  <h1 class="header-title">Closed Sales — Downey</h1>
  <p class="header-subtitle">Last <span>30 days</span> · All Properties · Live MLS Data</p>
</header>
```

**Rules:**
- Top row: brand logo + company name (left), report type badge (right, frosted glass pill)
- Title: Outfit 26px, report name + em dash + city
- Subtitle: period (accent-on-dark span), audience, data source
- Gradient: `--header-bg` (navy) to `--primary-color` (accent) at 135deg
- No metric in header — hero stat is in the content area

---

## Color System

All colors are CSS custom properties. The agent's brand colors flow in from `compute_color_roles()`.

```css
:root {
  --primary-color: #18235c;      /* Agent's primary — header gradient start */
  --accent-color: #0d9488;       /* Agent's accent — gradient end, badges, highlights */
  --accent-light: #ccfbf1;       /* Subtle accent backgrounds (AI insight, quick take) */
  --accent-on-dark: #5eead4;     /* Text that sits on dark backgrounds — WCAG safe */
  --accent-on-light: #0f766e;    /* Text that sits on light backgrounds — WCAG safe */
  --header-bg: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color) 50%, var(--accent-color) 100%);
}
```

**Never hardcode hex colors for brand elements.** Use the CSS variables. Status badge colors (sold=red, active=green, pending=yellow) ARE hardcoded — they're semantic, not brand colors.

---

## Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Prices / hero metrics | Outfit, Inter, sans-serif | 13-22px | 600-700 |
| Body text / addresses | Inter, sans-serif | 9-12px | 400-500 |
| Specs (beds/baths/sqft) | Inter | 9px | 400 |
| Meta lines | Inter | 10px | 400 |
| Table data | Inter | 9px | 400 |
| Quick take label | Inter | 8px | 600, uppercase |
| Page base font-size | — | 10px | — |

**The base font size is 10px** (set on `html, body`). All `em`-based sizing is relative to this. Most text uses explicit pixel sizes.

---

## Image Handling

MLS photos are proxied through R2 before PDF generation (the worker rewrites URLs). But images can still fail to load.

**Fallback pattern:**
```css
.photo, .thumb {
  background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%);
}
```
The gray gradient IS the fallback. If the `<img>` fails to load, the gradient shows through. No JavaScript `onerror` handlers — PDFShift doesn't execute JS.

For Jinja2 templates:
```jinja2
{% if listing.photo_url %}
  <img src="{{ listing.photo_url }}" alt="" style="width:100%;height:100%;object-fit:cover;">
{% endif %}
```
The `<img>` is optional. If no `photo_url`, the gray gradient background shows.

---

## Font Loading

PDFShift captures the page before fonts may finish loading, causing fallback glyphs. We force-load fonts with invisible divs:

```html
<!-- Before </body> — forces browser to download and rasterize all fonts -->
<div style="position:absolute;left:-9999px;top:-9999px;font-size:1px;line-height:1;">
  <span style="font-family:'Outfit',sans-serif;font-weight:400;">.</span>
  <span style="font-family:'Outfit',sans-serif;font-weight:500;">.</span>
  <span style="font-family:'Outfit',sans-serif;font-weight:600;">.</span>
  <span style="font-family:'Outfit',sans-serif;font-weight:700;">.</span>
  <span style="font-family:'Inter',sans-serif;font-weight:400;">.</span>
  <span style="font-family:'Inter',sans-serif;font-weight:500;">.</span>
  <span style="font-family:'Inter',sans-serif;font-weight:600;">.</span>
</div>
```

**Always include this in base.jinja2.** If you add a new font, add a trigger span for it.

---

## Jinja2 Patterns

### Always guard optional data
```jinja2
{# GOOD — section hidden when no data #}
{% if listings and listings|length > 0 %}
  <div class="gallery-grid">
    {% for listing in listings %}...{% endfor %}
  </div>
{% endif %}

{# BAD — crashes on None #}
<div class="gallery-grid">
  {% for listing in listings %}...{% endfor %}
</div>
```

### Use filters for currency
```jinja2
{{ listing.price | format_currency }}        → $470,000
{{ listing.price | format_currency_short }}   → $470k
{{ listing.sqft | format_number }}            → 1,234
```

### Layout dispatch pattern
```jinja2
{# In base.jinja2 — the builder passes layout_type in context #}
{% if layout_type == "gallery" %}
  {{ macros.gallery_layout(listings, stats) }}
{% elif layout_type == "narrative" %}
  {{ macros.narrative_layout(listings, stats, ai_insight) }}
{% elif layout_type == "closed_inventory" %}
  {{ macros.closed_inventory_layout(listings, stats, table_data) }}
{% elif layout_type == "analytics" %}
  {{ macros.analytics_layout(listings, stats, stat_cards) }}
{% endif %}
```

---

## Testing

```bash
# Render all 8 report types as HTML (no PDFShift needed)
python scripts/gen_market_reports.py --html-only

# Render a single type
python scripts/gen_market_reports.py --report-type market_snapshot --html-only

# Run template tests
pytest tests/test_market_templates.py -v

# Visual check: open in Chrome, Cmd+P for print preview at Letter size
```

**Always check in print preview.** Browser view can look fine while print preview clips content.

---

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Adding a section without checking page height | Content clips at 11in | Always check print preview after changes |
| Using `box-shadow` on cards | Shadows get clipped at page edge and look broken in PDF | Use `border` instead |
| Setting `margin` on `.report-page` | Breaks the 8.5×11 geometry | Use `padding` on `.content-zone` instead |
| Using `vh` or `vw` units | PDFShift viewport is unpredictable | Use `in` (inches) or `px` |
| Adding JS-dependent features | PDFShift doesn't execute JavaScript | CSS only |
| Hardcoding brand colors | Breaks when agent has different branding | Use CSS custom properties |
| Forgetting `overflow: hidden` | Content spills to invisible page 2 | Always on `.report-page` |
| Using `aspect-ratio` without fallback | Older Chromium builds may not support it | PDFShift uses recent Chromium, but verify |
| Adding fonts without font-trigger div | Fallback glyphs in PDF | Add a span to the font-trigger div |

---

## File Map

| File | Purpose | Lines |
|------|---------|-------|
| `templates/market/_base/base.jinja2` | Page shell, CSS, layout dispatch, font loading | ~700 |
| `templates/market/_base/macros.jinja2` | All 4 layout macros + shared components | ~350 |
| `templates/market/market.jinja2` | Brand color injection, extends base | ~16 |
| `market_builder.py` | Python builder class, context assembly | ~190 |
| `template_filters.py` | Jinja2 filters (currency, number, truncate) | ~48 |
| `scripts/gen_market_reports.py` | Local HTML/PDF generation for QA | ~280 |
| `tests/test_market_templates.py` | Template test suite (57 tests) | ~320 |

---

## V0 Design Spec

The definitive visual reference files are in `docs/design/` — 4 layout HTML files (gallery-layout.html, market-narrative-layout.html, closed-inventory-layout.html, analytics-layout.html). When in doubt about how something should look, open these files.

All template changes must produce HTML that visually matches the V0 spec. If you need to deviate, document why.
