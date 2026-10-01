# Handoff: Market Reports redesign (7 PDF types)

Repo: `easydeed/reportscompany` · Surface: `apps/web/templates/trendy-*.html` + the worker PDF builder
Design date: 2026-10-01 · Companion package: `design_handoff_property_report/` (shares colour roles and footer)

## Overview

One page template replaces the seven `trendy-*.html` files. The report type changes the header numbers and the body block; masthead, footer, type, spacing and colour roles are identical across all seven. The violet→coral gradient bar, the red "PDF" badge, the four-chip metric ribbon and the generic explainer paragraphs are removed. Each report leads with one number in the affiliate's brand colour.

## About the design files

`.dc.html` files are **design references built in HTML**, not templates to copy. Open `Report Page.dc.html` in a browser (needs `support.js` beside it); the Tweaks panel switches `kind` (snapshot · listings · closed · inventory · bands · featured · gallery), brand `primary`/`accent`, area, brand name and agent name. `Report Page Gallery.dc.html` shows all seven side by side. `PDF Reports v2.dc.html` is the design history — section 3a (continuation pages, missing-photo tile, headline rules) is still authoritative; the 1a "Editorial" direction was rejected.

## Fidelity

**High-fidelity.** Dimensions, type sizes, colours and copy are final. Sample data (Irvine, Coastline Realty, Jordan Reyes, listings, numbers) is invented.

## Page geometry

- 8.5 × 11in = 816 × 1056px. Side padding 52px. Content column 712px.
- No running head. The brand band on page 1 and the strip on pages 2+ are both **body content**. The only PDFShift element is the footer, starting at page 1. (Same constraint as the property report: header/footer `start_at` must match.)
- Footer, page 1 and gallery pages: `margin: 24px 52px 0; padding: 16px 0; border-top: 1px solid #E4E4E0`; 48px circle `primary` with initials (or headshot) in white; name 15px/600; "{brand} · DRE #{license}" 12px `#5E636B`; right column phone 12px/500 and email in `primary`. Below: source line 9px mono `letter-spacing: 0.04em` `#8A8E95`, `padding: 0 52px 28px`: "Source: CRMLS {dataset} · Generated {date} · Deemed reliable, not guaranteed".
- Footer, table continuation pages: one line — `<b>{agent}</b> · {brand} · {phone}` left, "Rows a–b of N · CRMLS" right, 12px / 9px mono.

## Type

Body: Geist 400–700. Labels and running text: Geist Mono 400/500, uppercase, `letter-spacing: 0.08em`. Both Google Fonts. Big numbers use `font-variant-numeric: tabular-nums`, `letter-spacing: -0.045em`, `line-height: 0.88`. No serif anywhere on this surface.

## Colour roles

Only two brand inputs: `primary` (affiliate colour) and `accent`.

| role | used for |
|---|---|
| `primary` | page-1 band fill, continuation strip fill, initials circle, bars (price tiers, MOI cells, price-band bars), footer email, over-asking tint on "Status" column |
| `accent` | highlight bars (tier bars on snapshot, fastest band), "New" tag on inventory, over-asking percentages on closed |
| white on `primary` | all band text. Design assumes `primary` is dark enough; for light affiliates apply the property report's `on_primary` rule (white or `#14151a` by contrast ≥4.5) |
| `rgba(255,255,255,0.78)` / `0.85` / `0.25` | band labels / band sublabels / band rules — only on `primary` fills that pass with white |

Neutrals: ink `#14161A`, body `#2A2D33`, muted `#5E636B`, faint `#8A8E95`, placeholder `#B9BBC1`, rules `#ECECE8` / `#E4E4E0`, bar track `#F4F4F1` / `#F1F1EE`, tint panel `#F6F5F1`, inactive MOI cell `#EDEDEA`, MOI legend rules `#14161A` / `#B9BBC1` / `#DADBDF`. Slowest-band tag `#B42318`. Status/delta colour: text only, never fills.

No text over photography. Price plates on listing photos are solid white `#14161A` 15px/700 `padding: 4px 9px; border-radius: 4px`, top-left 10px.

## Page-1 band (shared)

`background: primary; color: #fff; padding: 36px 52px 28–32px; gap: 28–30px`.
1. Row: date range 10.5px mono uppercase 78% white (left) · brand logo slot 44px tall, max 200px, right-aligned; fallback brand name 20px/700.
2. Lead row (`align-items: flex-end; justify-content: space-between`): big number 88px (snapshot: 96px; bands: 64px headline) + label 22px/600 `line-height: 1.1` beside it (e.g. "homes sold in Irvine"). Right: a white pill (13px/600, `primary` text, `padding: 4px 10px`, 999px) + 12px sublabel 85% white.
3. Stats row: `border-top: 1px solid rgba(255,255,255,0.25)`, 3 cells (4 on snapshot), left-bordered, 26–32px/600 number + 11.5px label.

Band height is fixed by content; the big number is nowrap and the label `text-wrap: balance`. City name is nowrap — if an area name exceeds ~22 characters at 22px, shrink the label to 18px rather than wrap to three lines.

## Per-kind spec

| kind | big number / label | pill / sub | stats | body |
|---|---|---|---|---|
| snapshot | median sale price "$1.46M" (96px) / — | "▲ 3.1%" / "median sale price vs. prior 30 days" | Closed sales ▲6% · Days on market ▼2 · Sale-to-list · New listings ▲9% | three 200px/1fr rows: MOI headline + 8-cell bar + legend; tier headline + 3 accent bars with median · MOI; "By property type" 3 tint cards ($, sold, days) |
| listings | count "24" / "new listings in {area}" | price range / "this week" | Median list · Under $1M · Of inventory | 3×2 photo grid, price plate, address 13px/600, "{hood} · {specs}" 11.5px |
| closed | count "118" / "homes sold in {area}" | "99.1% of asking" / "last 30 days" | Median price · Avg. days · Sold over asking | table `1fr 64 72 108 72 44`: Address+hood · Bd/Ba · Sq ft · Sold for · vs. list · Days; >100% in `accent` 600; 13 rows page 1, 26 on continuation; "Showing 13 of N · page 1 of P" |
| inventory | count "212" / "homes for sale in {area}" | "1.9 months" / "of inventory · seller's market" | Median list · New this week · Avg. days listed | same table; "vs. list" column becomes "Status": "New" in `accent` when DOM ≤7, else "—" `#B9BBC1` |
| bands | headline "$1–1.25M" (64px) / "is moving fastest" | "16 days" / "8 days faster than the area" | Active listings · Median list · Price range | 7 rows `120px 1fr 72 60 64`: band + tag (Fastest `accent` / Slowest `#B42318`), 36px bar (`accent` for fastest, else `primary`) with count inside, median, days (tag colour), $/sq ft |
| featured | count "4" / "featured homes in {area}" | "Hand-picked" / price range | Listings · Avg. price · Avg. sq ft | 2×2 photo grid, price plate 18px, address 15px/600, beds/baths/sq ft as three stacked mini-stats right |
| gallery (open houses) | count "9" / "homes to see this weekend" | "Open houses" / "Sat & Sun · {area}" | From · To · Neighborhoods | 3×3 photo grid (same card as listings) |

Headline sentences are **template-filled from data, never free-written** (rules in `PDF Reports v2.dc.html` §3a): MOI <4 "It's a seller's market" / 4–6 "The market is balanced" / >6 "Buyers have the edge"; "{Tier} homes lead" only when tier share ≥40%, else "Sales spread across price tiers"; "{band} is moving fastest" only when that band has ≥10 listings and is ≥3 days faster than the area average, else the plain title "{Area} · Price Bands"; every headline hidden under 10 sales/listings; deltas shown only when |change| ≥1%, otherwise "flat".

## Continuation pages (closed, inventory)

Strip `background: primary; padding: 18px 52px`: "{Report} · {Area}" 13px/600 + "{date range} · Page n of P" 10.5px mono (left) · logo slot 28px tall max 140px (right). Same table header, 26 rows, one-line footer. Page count P derived from row count.

## Missing photo

`tint` tile (`primary` at 8% over white) with neighborhood name 22px/600 in `primary` bottom-left and "Photos coming soon" 9.5px mono uppercase 75%. Price plate stays top-left. No broken-image icon, no stock house.

## Absence rules

Dash `#B9BBC1` for unknown, label kept. 0 DOM → "New". Deltas <1% → "flat". Missing hood → omit the "· {hood}" segment, do not print "· —". Missing specs → omit segment. Counts of zero in the band → still render the number ("0 homes sold") — zero is data, not absence.

## Builder changes implied

- Collapse seven templates into one with a `kind` switch; shared masthead/footer/table partials.
- Per-kind headline rules above as builder functions returning `null` when thresholds fail; template renders the plain title on `null`.
- Row pagination: 13 on page 1, 26 on continuation; P computed from `ceil((N − 13) / 26) + 1`.
- Logo slot: pass `brand_logo_url`; fall back to brand name text when null.
- Tier/band bar widths = value / max in the set; MOI cells = `round(moi)` of 8.
- `on_primary` contrast rule shared with the property builder for light affiliate colours.

## Files

- `Report Page.dc.html` — the template, all seven kinds via Tweaks.
- `Report Page Gallery.dc.html` — all seven at full size.
- `PDF Reports v2.dc.html` — design history; §3a (continuation, missing photo, headline rules) authoritative, §2a the chosen direction, §1a rejected.
- `support.js` — runtime for opening the `.dc.html` files locally.
