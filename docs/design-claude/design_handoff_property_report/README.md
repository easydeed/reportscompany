# Handoff: Property Report & Consumer CMA redesign

Repo: `easydeed/reportscompany` · Surface: `apps/worker/src/worker/templates/property/` + `property_builder.py`
Design date: 2026-10-01 · Brief: "Property Report & CMA — Design Brief" (§ references below are to it)

## Overview

One page architecture replaces the five per-theme templates. Three themes survive (elegant, bold, modern) and differ only in display/body typeface, weight, tracking, case and corner radius. Everything else — layout, page set, spacing, colour roles, copy — is shared. Every colour on every page is one of the six `derive_theme()` tokens or a fixed neutral; no theme carries a hue of its own.

Six pages, down from nine: cover · your home · comparable sales · what the comps support · your market (conditional) · next steps. Contents and executive-summary pages are removed. Agent and consumer paths render from the same template with three branches (see Paths).

Read `STRUCTURAL_NOTE.md` first — it maps every structural change to the §3 constraint it satisfies.

## About the design files

The `.dc.html` files are **design references built in HTML** — they show the intended look and behaviour. They are not Jinja templates to copy. The job is to recreate them in the existing Jinja2 + `base.jinja2` + PDFShift pipeline, passing the seven CI gates in §5. Open `Property Report.dc.html` in a browser (needs `support.js` beside it) and use the Tweaks panel to switch theme, brand, path, confidence grade, market page and missing-photo state.

`Property Report Matrix.dc.html` shows all 18 theme × brand covers at once. `Property Report Cover.dc.html` is a thin wrapper used by the matrix; ignore it.

## Fidelity

**High-fidelity.** Dimensions, type sizes, colours and copy are final. Sample data (La Verne address, comps, agent, market numbers) is invented; the structure of what is shown is not.

## Owner decision: cover band text is white

The cover masthead text is `#FFFFFF` on `primary` by owner decision (Oct 1), overriding `on_primary`. On teal `#0D9488` this measures 3.74:1, amber and lime lower; the pixel contrast auditor will flag the cover band on those brands. Treat this as a recorded §3.1 exception for the masthead only — scope the auditor exclusion to the cover band element, not the page. Everywhere else (agent panel, grade square, initials circle) stays on `on_primary`. If a real affiliate colour makes the masthead unreadable, the remedy is a darker `primary_dark` fill behind the text, never moving the brand colour.

## Page geometry

- Page: 8.5 × 11in (816 × 1056 CSS px at 96dpi). Side margins 52px. Content column 712px.
- Running head (PDFShift header, every page incl. page 1): 40px tall, `border-bottom: 1px solid #ECECE8`, 10.5px uppercase `letter-spacing: 0.06em` `#5E636B`. Left: "Property report · {street}" (nowrap, ellipsis). Right: generation date.
- Footer (PDFShift footer, every page): `border-top: 1px solid #E4E4E0`, padding 14px 0 22px, 11.5px. Left: `<b>{agent}</b> · {brand} · {phone}` (`#5E636B` after the name). Right: "Page {n} of {N}" tabular nums. N is derived after conditional pages are dropped (§3.5).
- Header and footer both start at page 1 (variant A, §3.4). The brand masthead on page 1 is body content.
- Body font 13–13.5px, line-height 1.5. Minimum type on page: 10.5px (labels, disclaimers; all ≥ 4.5:1).

## Themes (type + radius only)

| theme | display face | weight | tracking | case | body face | radius |
|---|---|---|---|---|---|---|
| elegant | Cormorant Garamond | 500 | −0.01em | none | Geist | 0 |
| bold | Barlow Condensed | 700 | 0 | uppercase | Barlow | 4px |
| modern | Manrope | 800 | −0.035em | none | Manrope | 14px |

All Google Fonts. Keep the font-trigger `<div>` in `base.jinja2`. `radius` applies to photo plates, tint panels, the dark range panel, the agent panel and the phone pill. Section headings (h2) are 40px display face, line-height 1. The `text-transform: uppercase` on bold applies to the cover street line and h2s, not to body copy or labels.

## Colour roles (§3.1)

From `derive_theme(brand_hex)`:

| token | used for |
|---|---|
| `primary` | cover band fill, agent panel fill, bar fills (price bars, inventory cells, chart bars), confidence grade square, initials circle |
| `primary_dark` | prior-month chart bars |
| `primary_ink` | all brand-coloured text on white/tint: section labels (10.5px uppercase), "Prepared for", market median price, missing-photo tile text, initials on white circle, phone pill text |
| `on_primary` | all text on `primary` fills. Rule lines on primary: `rgba(255,255,255,0.3)` if on_primary is white, else `rgba(20,21,26,0.25)` |
| `tint` | "In short" panel, confidence pill, next-steps cards, photo-plate background before image loads, missing-photo tile |
| `primary_on_dark` | the range band and the label on the `#0f172a` panel — and nowhere else |

Fixed neutrals: ink `#14161A`, body `#2A2D33`, muted `#5E636B`, faint `#8A8E95`, dash `#B9BBC1`, rules `#ECECE8` / `#E4E4E0` / `#D9DADF`, bar track `#F1F1EE`, strip `#F6F6F3`, inactive cells `#EDEDEA`, dark panel `#0f172a` (the only dark surface). Status pills (semantic, never brand): Sold `#dc2626` on `#fee2e2`; Pending `#d97706` on `#fef3c7`; Active `#059669` on `#d1fae5`.

No text over photography anywhere (§3.2). Plates on photos are solid white with `#14161A` text.

## Pages

### 1 · Cover (`cover`, required)
Masthead = body content, `background: primary; color: on_primary; padding: 36px 52px 32px; gap: 26px`:
- Row: report kind (11px uppercase 0.12em, 85% opacity) — "Seller's report" (agent) / "Home value report" (consumer). Right: brand logo slot, 40px tall, max 200px wide; falls back to brand name 18px/700.
- Title box: **fixed height 78px**, `overflow: hidden`, contents bottom-aligned. Street on one `nowrap` line, `line-height 1.15`, size ladder by character count: ≤18 → 64px, ≤24 → 54px, ≤30 → 46px, ≤38 → 38px, else 32px; `text-overflow: ellipsis` backstop. Below: "{City}, {ST} {ZIP}" 22px/500, 92% opacity. (§3.3)
- Stats row: 4 cells, top rule, display face 30px + 11px label: Bedrooms, Bathrooms, Sq ft, Built. Zero beds renders "Studio"; null renders "—".

Below masthead, padding 24px 52px 20px:
- Hero photo plate: `flex: 1; min-height: 300px`, radius, no text. Missing photo → `tint` tile with city name 28px display in `primary_ink`, bottom-left, and "No photo on file" 11px uppercase.
- Two-column grid `200px / 1fr`, gap 28px:
  - "Prepared for" label (10.5px uppercase 0.1em `primary_ink` 600) → name 22px display → note 13px `#5E636B`. Agent path: "The owners of {street}" / "Prepared at the request of {agent}". Consumer path: "{requester name}" / "Requested from {brand}'s home-value page".
  - "In short" panel on `tint`, padding 18px 20px, radius: label + narrative 13.5px/1.5 `#2A2D33`, **`max-height: 81px; overflow: hidden`** (4 lines). Narrative is the AI text, capped at generation (§3.3). Replaces the `overview` page.

### 2 · Your home (`property`, required)
Padding 28px 52px 0, gap 18px.
- h2 "Your home" 40px display; right: full address + "APN {apn}" 12px `#5E636B` right-aligned.
- Two photo plates side by side, 220px tall, radius, white label plate bottom-left ("Aerial", "Street view") 11px/600 padding 5px 9px radius 4px.
- Four detail groups in a 2-column grid (gap 0 40px, `align-items: start`), flowing in order: **The home** (Bedrooms, Bathrooms, Living area, Lot size, Year built, Property type, Stories, Pool / spa) · **Record & taxes** (Owner of record [agent path only], APN, Last sale, Assessed value, Land / improvements, Annual tax + year, Tax status, HOA, Zoning, Garage) · **Schools** (District, Elementary, Middle, High) · **Location** (County, Neighborhood, Census tract).
  - Group title 10.5px uppercase `primary_ink`, padding 14px 0 6px, `border-bottom: 1.5px solid #14161A`.
  - Row: `grid-template-columns: auto minmax(0,1fr)`, padding 8px 0, 12.5px, `border-bottom: 1px solid #ECECE8`. Label `#5E636B` nowrap. Value 600, right-aligned, nowrap + ellipsis. Unknown → "—" in `#B9BBC1` (§3.6). Rows are **never hidden** when null — the current `data_table` macro hides them; this design keeps them.
- "Not on record" strip: `#F6F6F3`, radius, padding 14px 16px, 12px. Bold label + list of every dashed field (from the table plus the always-empty fields: Fireplace, Total rooms, Use code, Census tract) + "A dash anywhere in this report means the public record doesn't say, not that the answer is no." Renders only when ≥1 unknown.
- Integers never carry decimals (§6 D-125).

### 3 · Comparable sales (`comparables`, required)
Padding 32px 52px 0, gap 20px.
- h2 "Comparable sales". Right column: confidence pill then "{n} homes within {radius} · last {window}" 12px.
  - Pill: `tint` bg, `primary_ink` text 11.5px/600, padding 5px 10px, radius 4px, nowrap; leading 20px square `primary`/`on_primary` with the grade letter. Label by grade: A "Strict match", B "{reason}" default "Relaxed match", C "{reason}" default "Broad match", D "Thin market". From `comp_confidence_grade` / `comp_confidence_reason`.
- Grid 3 × 2, gap 20px 16px, `flex: 1`. Up to 6 comps (current macro caps at 4 — raise to 6).
  - Photo plate `flex: 1`, radius; price plate top-left (white, 14px/700, padding 4px 8px, radius 4px); status pill top-right (10px/700 uppercase, semantic colours). Missing photo → `tint` tile with neighborhood 20px display in `primary_ink` + "No photo on file" (§6 D-122/114).
  - Lines (padding-top 9px, gap 3px): address 12.5px/600 nowrap ellipsis · "{bd} bd · {ba} ba · {sqft} sq ft" 11px `#5E636B` · "${ppsf} /sq ft · {dist} · {Sold Mon YYYY | Listed Mon}" 11px `#5E636B` · "Lot {lot} · {No HOA | HOA $x/mo | HOA —}" 11px `#8A8E95`.

### 4 · What the comparable sales support (`range`, new — replaces `analysis` + `range`)
Padding 32px 52px 0, gap 24px.
- h2 "What the comparable sales support".
- Dark panel `#0f172a`, white text, radius, padding 36px: label 10.5px uppercase in `primary_on_dark` "Range supported by {closed count} closed sales · confidence {grade}, {label lowercase}" → headline display 72px nowrap "{low} – {high}" + "median {mid}" 13px 80% white → band: track `rgba(255,255,255,0.14)` 10px, fill `primary_on_dark` from low to high on a fixed axis (axis = floor(low×0.92) .. ceil(high×1.06), rounded to $1K), white 3×22px marker at the subject's last recorded sale → axis labels 11px with centre "▲ your home's last recorded sale · ${price} in {year}" → disclaimer 12px 80% white: "This is what recent sales of similar homes nearby support. It is a report of the market, not an appraisal, and a listing price is a conversation with your agent." Range uses closed comps only; pending/active excluded.
- Comparison table, header 10.5px uppercase with "Your home" in `primary_ink` 700, columns `1fr 110px 110px 110px 110px`: Sale price (subject = last sale + year) · Price per sq ft (derive from last sale ÷ sqft when both known) · Living area · Year built · Bedrooms. Low / Median / High from closed comps. Rows 13.5px tabular, padding 13px 0. Header label "Your home" replaces "PIQ" (§6 D-127).
- "Each sale": one row per comp, `170px 1fr 90px`, bar 22px `primary` on `#F1F1EE`, width = price / max; address gets " · pending" suffix when not closed; price right 600.

### 5 · Your market (`market_trends`, conditional on live MLS fetch)
Padding 32px 52px 0, gap 32px, content stretches to footer.
- h2 "Your market"; right "{city} · {window}".
- 4 stat cells, top rule 1.5px, display 44px + 11.5px label: Median sale price (value in `primary_ink`, label carries "▲ x%"), Days to contract (`timeline_metrics.avg_marketing_days`, "▼ n"), Sold in 30 days or less (`dom_distribution.under_30`), Took a price cut (`price_cut_stats.rate`, "median ${median_cut}"). Arrows text-only; no red/green. Omit the delta when |change| < 1%.
- Months-of-inventory row: left 200px copy block (13px/700 headline by threshold — "It's a seller's market" <4 / "The market is balanced" 4–6 / "Buyers have the edge" >6 — and 12px note) · right: 8 cells 44px tall, `round(moi)` filled `primary`, rest `#EDEDEA`; legend 10px uppercase with top rules `#14161A` / `#B9BBC1` / `#DADBDF` for Seller's · under 4 mo / Balanced / Buyer's · 6+.
- Bar chart (fills remaining height): label "Median sale price · last 6 months" `primary_ink` + "Thousands of dollars"; y-axis 3 ticks 10px `#8A8E95`; plot area `border-left: 1px solid #D9DADF; border-bottom: 1px solid #14161A`, dashed midline; 6 bars, values 11px/700 above each bar, prior months `primary_dark`, latest `primary`; x labels 10.5px. Values and axis present on every theme (§6 D-126).

### 6 · Next steps (new — closing page)
Padding 32px 52px 0, gap 32px.
- h2 "Next steps".
- Agent panel `primary` / `on_primary`, radius, padding 44px 40px, grid `120px 1fr auto`: 120px white circle with initials in `primary_ink` (or headshot if present) · name 32px display, "{brand} · DRE #{license}" 14px, one-line blurb 13px max 400px (agent: "Happy to walk through this with you and talk about timing, pricing and what buyers in {city} are looking for right now." consumer: "You asked what your home is worth. Here's what nearby sales say. When you're ready, I'll walk you through what a listing could look like.") · right: phone on white pill 15px/700 padding 12px 18px, email 13px.
- Two explainers (grid 1fr 1fr, gap 40px): "How the comparables were chosen" and "Where the data comes from", 15px/1.6 `#2A2D33`. Copy in the design file; parameterise radius, window and date.
- "If you're thinking about selling": 3 `tint` cards, padding 18px 20px: number 30px display `primary_ink`, title 14px/700, body 13px `#5E636B`.
- Disclaimer 10.5px `#8A8E95`, top rule: "Information is deemed reliable but not guaranteed. This report is not an appraisal and is not intended to be relied upon as one." Consumer path appends: "Prepared for the person who requested it and addressed to them by name; it does not contain owner-of-record information."

## Paths (agent vs consumer, §1 / §7)

Three branches only, all in one template:
1. Report kind label: "Seller's report" / "Home value report".
2. Cover "Prepared for": owners of {street} + agent note / {requester_name} + landing-page note. Consumer requires `requester_name` from the form.
3. Owner of record row and any owner identity: agent path only. `test_no_owner_identity_in_property_report.py` should pass on the consumer render with zero template literals needing exclusion.

## Absence rules (§3.6)

Unknown → "—" `#B9BBC1`, label kept. Never "No", "None", "Current", "0". Beds 0 → "Studio". DOM 0 → "New". HOA null → "HOA —"; HOA 0 → "No HOA". Metric with no data → "no data". Deltas under 1% → omitted. No `{% if x %}` over numerics where 0 is meaningful (zero-conditional sweep).

## Page capacity (§3.3)

Only two things on page 1 grow with data and both are bounded (title box 78px with ladder; narrative 81px). Pages 2–6 are fixed-row layouts: page 2 holds up to 25 rows across four groups at 8px padding (current sample is 24 + strip); page 3 holds 6 comps; page 4 holds 5 compare rows + 6 bars; page 5 has 4 cells + 8-cell MOI + 6-bar chart. If data can exceed these, cap at the builder, not the template.

## Builder changes implied

- Drop `overview` and `contents` from the page set and the wizard. Default order: `cover, property, comparables, range, market_trends, notes`. `analysis` folds into `range`.
- `comp_grid` cap 4 → 6; comps carry `status`, `lot_display`, `hoa_fee`, `hoa_frequency`, `distance_miles`, `sold_date`, `photo_url`, `neighborhood`.
- New stats: closed-only `low/mid/high`, axis bounds, subject last sale + year, `ppsf` derived when sale price and sqft are known.
- Title size ladder computed from `len(street_address)`.
- `requester_name` on the consumer path; owner fields stripped from the consumer context, not just hidden.
- `_THEME_DARK_BG` collapses to `#0f172a` for all themes; `compute_color_roles` → `derive_theme` tokens (the migration D-097 anticipates).
- Remove `classic` and `teal` theme directories; migrate accounts on those to `elegant` (closest in intent) with a note in the wizard.

## Assets

Photos in the design are Unsplash placeholders; production uses `images.hero`, `images.aerial`, Street View, and `comp.photo_url` / `map_image_url`. Fonts: Google Fonts (Cormorant Garamond 500/600, Geist 400–700, Barlow Condensed 600/700, Barlow 400–700, Manrope 400–800). No icons.

## Files

- `Property Report.dc.html` — the full report, all states via Tweaks (theme, brand, path, confidence, hasMarket, missingPhotos, street, city). Token derivation in the logic class mirrors `themes.derive_theme()`.
- `Property Report Matrix.dc.html` — 18 covers (3 themes × 6 brands from `tests/golden/themes.json`).
- `Property Report Cover.dc.html` — wrapper for the matrix.
- `STRUCTURAL_NOTE.md` — §3 compliance map and what was dropped.
- `support.js` — runtime for opening the `.dc.html` files locally.

## Self-check against the conformance constraints (Oct 1)

| constraint | property report | market reports (Report Page / PDF Reports v2) |
|---|---|---|
| Brand fill never moves; contrast via text/surface | Holds, except the recorded masthead exception above | Holds — every fill is `primary`, text is white; brand colours used in the design (navy, indigo, green, maroon) all pass. Light affiliate colours need the same `on_primary` logic the property report uses — the market templates currently assume white. |
| No foreground over a varying background | Holds — no text on photos, no gradients; price plates are solid white | Holds — same plate treatment on listing cards |
| PDFShift header/footer start at page 1 | Holds — running head + footer are the header/footer; masthead is body | Market reports have no separate running head; page-1 band and page-2+ strip are both body content, footer is the only PDFShift element |
| Page-1 capacity bounded | Holds — title box 78px + ladder; narrative 81px | Holds — city name is nowrap; headline sentences are template-filled with thresholds (see PDF Reports v2 section 3a) |
| Page numbers derived | Holds — N computed after conditional drop. **Deliberate conflict:** overview is removed, not rendered second; the summary is the bounded "In short" panel on the cover | Holds — "Page n of N" from the row count; continuation pages share one template |
| Absent ≠ zero, no confident default | Holds — dashes, Studio, New, "HOA —". Bathrooms: the feed key is absent, so the cover stats row now drops null stats and backfills (Lot sq ft); toggle `bathsKnown` in Tweaks to see it | Holds — deltas <1% render "flat"; headline hidden under 10 sales |
| `primary_on_dark` against one neutral | Holds — `#0f172a` only | No dark surface used |

Open for the reviewer: the 19 orphan fields are kept as dashes + a "Not on record" strip (owner choice). If the decision later becomes "remove", drop the Location group and the Zoning / Garage / Stories / Pool rows and the strip disappears on its own.
