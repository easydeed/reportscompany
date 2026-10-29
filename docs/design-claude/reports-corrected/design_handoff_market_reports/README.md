# Handoff: Market Reports redesign (7 PDF types)

Repo: `easydeed/reportscompany` · Live surface: `MarketReportBuilder` → `apps/worker/src/worker/templates/market/market.jinja2` + `market/_base/`. **`apps/web/templates/trendy-*.html` and `apps/web/app/print/[runId]/` are the LEGACY path and render no customer PDF — do not read them.**

**Corrections of 2026-10-05 are applied; see `RESPONSE_2026-10-05.md`.**
Design date: 2026-10-01 · Companion package: `design_handoff_property_report/` (shares colour roles and footer)

## Overview

One page template, dispatched on kind — matching the live `market.jinja2` + `LAYOUT_MAP`. The report type changes the header numbers and the body block; running head, masthead, footer, type, spacing and colour roles are identical. The four-chip metric ribbon and the generic explainer paragraphs are removed. Each report leads with one number in the affiliate's brand colour.

**Kind ↔ live type:** snapshot → `market_snapshot` · listings (grid) → `new_listings_gallery` · listings (table) → `new_listings` · closed → `closed` · inventory → `inventory` · bands → `price_bands` · featured → `featured_listings` · gallery → `open_houses`. Eight live types, seven kinds; `listings` takes `listingsDensity: grid | table`. PDF title and wizard both say "New Listings" (table) and "New Listings Gallery" (grid).

## About the design files

`.dc.html` files are **design references built in HTML**, not templates to copy. Open `Report Page.dc.html` in a browser (needs `support.js` beside it); the Tweaks panel switches `kind` (snapshot · listings · closed · inventory · bands · featured · gallery), brand `primary`/`accent`, area, brand name and agent name. `Report Page Gallery.dc.html` shows all seven side by side. `PDF Reports v2.dc.html` is the design history — section 3a (continuation pages, missing-photo tile, headline rules) is still authoritative; the 1a "Editorial" direction was rejected.

## Fidelity

**High-fidelity.** Dimensions, type sizes, colours and copy are final. Sample data (Irvine, Coastline Realty, Jordan Reyes, listings, numbers) is invented.

## Page geometry

- 8.5 × 11in = 816 × 1056px. Side padding 52px. Content column 712px.
- **Running head kept** (the live architecture; 1.07in recovered per page): 40px, PDFShift header from page 1, `border-bottom: 1px solid #ECECE8`, Geist Mono 10.5px uppercase `#5E636B`: "{Report} · {Area}" left (nowrap ellipsis), date range right. The brand band on page 1 is body content below it. Footer is the PDFShift footer from page 1. Both `start_at` = 1, always. Continuation pages carry the running head and the table — there is no separate brand strip.
- Footer, page 1 and gallery pages: `margin: 24px 52px 0; padding: 16px 0; border-top: 1px solid #E4E4E0`; 48px circle `primary` with initials (or headshot) in white; name 15px/600; "{brand} · DRE #{license}" 12px `#5E636B`; right column phone 12px/500 and email in `primary`. Below: source line 9px mono `letter-spacing: 0.04em` `#5E636B`, `padding: 0 52px 28px`: "Source: CRMLS {dataset} · Generated {date} · Deemed reliable, not guaranteed".
- Footer, table continuation pages: one line — `<b>{agent}</b> · {brand} · {phone}` left, "Rows a–b of N · CRMLS" right, 12px / 9px mono.

## Type

Body: Geist 400–700. Labels and running text: Geist Mono 400/500, uppercase, `letter-spacing: 0.08em`. Both Google Fonts. Big numbers use `font-variant-numeric: tabular-nums`, `letter-spacing: -0.045em`, `line-height: 0.88`. No serif anywhere on this surface.

## Colour roles

Only two brand inputs: `primary` (affiliate colour) and `accent`.

| role | used for |
|---|---|
| `primary` | page-1 band fill, continuation strip fill, initials circle, bars (price tiers, MOI cells, price-band bars), footer email, over-asking tint on "Status" column |
| `accent` | highlight bars (tier bars on snapshot, fastest band), "New" tag on inventory, over-asking percentages on closed |
| `#FFFFFF` on `primary` | **display only**: big number, 26px stat values, the band label (owner exception; `display_ink`: white where white ≥3.0 on `primary`, else `on_primary` — measured: red 4.83, teal 3.74, cyan 5.36, violet 5.70 white; amber 2.15 and lime 1.98 fall to `on_primary` (#14151a: 8.49 / 9.23)) |
| `on_primary` on `primary` | everything under 24px on the band: report title, logo fallback, pill sub, stat labels. White or `#14151a` by contrast ≥4.5 |
| `accent_ink` | **all accent-coloured text**: over-asking %, "New", "Fastest". Derived by darkening `accent` until ≥4.5 on white. No chips, no tinted fills behind semantic text — the live surface's only 66 failures are that construct |
| band rules | `rgba(255,255,255,0.3)` when `on_primary` is white, else `rgba(20,21,26,0.25)` |

Neutrals: ink `#14161A`, body `#2A2D33`, muted `#5E636B` (lightest text colour on the surface; also the dash, at weight 400), rules `#ECECE8` / `#E4E4E0`, bar track `#F4F4F1` / `#F1F1EE`, tint panel `#F6F5F1`, inactive MOI cell `#EDEDEA`, MOI legend rules `#14161A` / `#B9BBC1` / `#DADBDF`. Slowest-band tag `#B42318` (5.9:1). Semantic/delta colour: `accent_ink` text only, never fills.

No text over photography. Price plates on listing photos are solid white `#14161A` 15px/700 `padding: 4px 9px; border-radius: 4px`, top-left 10px.

## Page-1 band (shared)

`background: primary; color: on_primary; padding: 30px 52px 26px; gap: 30px`, below the 40px running head.
1. Row: report title 10.5px mono uppercase 500 `on_primary` (left) · brand logo slot 44px tall, max 200px, right-aligned; fallback brand name 20px/700 `on_primary`.
2. Lead row (`align-items: flex-end; justify-content: space-between`): big number 88px white (snapshot: 96px; bands: 64px headline) + label in a **fixed 50px box**, bottom-aligned, white 600 `line-height: 1.1`, size ladder by character count: ≤26 → 22px, ≤34 → 18px, ≤44 → 15px, else 13px; ellipsis backstop. Right: white pill (13px/600, `primary` text, `padding: 4px 10px`, 999px) + 12px/500 sublabel `on_primary`.
3. Stats row: top and left rules per the rule token, 3 cells (4 on snapshot), 26px/600 white value + 11.5px/500 `on_primary` label.

Band height is therefore fixed: nothing in it grows with data.

## Per-kind spec

| kind | big number / label | pill / sub | stats | body |
|---|---|---|---|---|
| snapshot | median sale price "$1.46M" (96px) / — | "▲ 3.1%" / "median sale price vs. prior 30 days" | Closed sales ▲6% · Days on market ▼2 · Sale-to-list · New listings ▲9% | three 200px/1fr rows: MOI headline block (**fixed 78px**: 1 nowrap headline + 3 clamped lines) + 8-cell bar + legend; tier headline block (fixed 78px) + 3 accent bars with the count as ink text beside the bar, median · MOI right; "By property type" 3 tint cards ($, sold, days) |
| listings · grid (`new_listings_gallery`) | count "24" / "new listings in {area}" | price range / "this week" | Median list · Under $1M · Of inventory | 3×2 photo grid, price plate, address 13px/600, "{hood} · {specs}" 11.5px |
| listings · table (`new_listings`) | same header | same | same | table `1fr 64 72 108 72 44`: Address+hood · Bd/Ba · Sq ft · List price · Listed ("Today" / "n d ago") · Days; 13 rows page 1 |
| closed | count "118" / "homes sold in {area}" | "99.1% of asking" / "last 30 days" | Median price · Avg. days · Sold over asking | table `1fr 64 72 108 72 44`: Address+hood · Bd/Ba · Sq ft · Sold for · vs. list · Days; >100% in `accent_ink` 600, else `#5E636B` 400; 13 rows page 1, 26 on continuation; "Showing 13 of N · page 1 of P" |
| inventory | count "212" / "homes for sale in {area}" | "1.9 months" / "of inventory · seller's market" | Median list · New this week · Avg. days listed | same table; "vs. list" column becomes "Status": "New" in `accent_ink` 600 when DOM ≤7, else "—" `#5E636B` 400 |
| bands | headline "$1–1.25M" (64px) / "is moving fastest" | "16 days" / "8 days faster than the area" | Active listings · Median list · Price range | 7 rows `120px 1fr 72 60 64`: band + tag (Fastest `accent_ink` / Slowest `#B42318`), 36px bar (`accent` for fastest, else `primary`) with the **count as 13px ink text beside the bar**, median, days (tag colour), $/sq ft |
| featured | count "4" / "featured homes in {area}" | "Hand-picked" / price range | Listings · Avg. price · Avg. sq ft | 2×2 photo grid, price plate 18px, address 15px/600, beds/baths/sq ft as three stacked mini-stats right |
| gallery (open houses) | count "9" / "homes to see this weekend" | "Open houses" / "Sat & Sun · {area}" | From · To · Neighborhoods | 3×3 photo grid (same card as listings) |

Headline sentences are **template-filled from data, never free-written** (rules in `PDF Reports v2.dc.html` §3a): MOI <4 "It's a seller's market" / 4–6 "The market is balanced" / >6 "Buyers have the edge"; "{Tier} homes lead" only when tier share ≥40%, else "Sales spread across price tiers"; "{band} is moving fastest" only when that band has ≥10 listings and is ≥3 days faster than the area average, else the plain title "{Area} · Price Bands"; every headline hidden under 10 sales/listings; deltas shown only when |change| ≥1%, otherwise "flat".

## Continuation pages (closed, inventory, new_listings table)

Running head (same as page 1) + table header + 26 rows + one-line footer. No brand strip. Page count P derived from row count: `ceil((N − 13) / 26) + 1`. **Page-1 capacity is one state per kind** — this design renders no AI narrative on table or gallery kinds, so there is no narrative variant. Re-measure the row counts in the browser fit gate for this layout and pin them.

## Missing photo

`tint` tile (`primary` at 8% over white) with neighborhood name 22px/600 in `primary` bottom-left and "Photos coming soon" 9.5px mono uppercase 75%. Price plate stays top-left. No broken-image icon, no stock house.

## Absence rules

Dash `#5E636B` weight 400 for unknown, label kept. 0 DOM → "New". Deltas <1% → "flat". Missing hood → omit the "· {hood}" segment, do not print "· —". Missing specs → omit segment. Counts of zero in the band → still render the number ("0 homes sold") — zero is data, not absence.

## Builder changes implied

- `market.jinja2` already dispatches on layout; add the `listings` density switch and the shared band/footer/table partials.
- Per-kind headline rules above as builder functions returning `null` when thresholds fail; template renders the plain title on `null`.
- Row pagination: 13 on page 1, 26 on continuation; P computed from `ceil((N − 13) / 26) + 1`.
- Logo slot: pass `brand_logo_url`; fall back to brand name text when null.
- Tier/band bar widths = value / max in the set; MOI cells = `round(moi)` of 8.
- `on_primary` and `accent_ink` derivations shared with the property builder (`themes.derive_theme`). `_TITLE_LADDER` for the band label: `((26, 22), (34, 18), (44, 15))`, floor 13.

## Files

- `Report Page.dc.html` — the template, all seven kinds via Tweaks.
- `Report Page Gallery.dc.html` — all seven at full size.
- `PDF Reports v2.dc.html` — design history; §3a headline rules and missing-photo tile authoritative, its continuation-page brand strip **superseded** by the running head; §2a the chosen direction, §1a rejected.
- `RESPONSE_2026-10-05.md` — decisions and changes against the correction list.
- `RESPONSE_2026-10-06.md` — structure answer (running head = header, masthead = body, one-line footer = footer, both `start_at = 1`), `display_ink`, themes.
- `support.js` — runtime for opening the `.dc.html` files locally.
