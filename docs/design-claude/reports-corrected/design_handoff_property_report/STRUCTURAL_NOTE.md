# Property report redesign — structural note

Check these against §3 of the brief rather than letting a gate find them.

## Themes
Three survive: elegant, bold, modern. Classic and teal are removed. The three differ only in type (display + body face, weight, tracking, case) and corner radius. Layout, page set, spacing and every colour role are shared. No theme carries a hue of its own — the gold, coral, sky and teal literals are gone, which removes 5 of the 6 values behind 132/213 contrast failures at the source.

## Colour (§3.1, §3.2)
- Fills: `primary`. Text on fills: `on_primary`. Brand text on white: `primary_ink`. Zebra/panels: `tint`. Brand text on dark: `primary_on_dark`, and the only dark surface painted is `#0f172a`.
- Status pills are semantic and fixed (Sold `#dc2626/#fee2e2`, Pending `#d97706/#fef3c7`, Active `#059669/#d1fae5`).
- No text over photography anywhere. Price/label plates on photos are solid white with `#14161A` text. Cover photo carries no text. Missing photo = `tint` tile with `primary_ink` text; no glyph, no grey box.
- Neutrals: `#14161A`, `#2A2D33`, `#5E636B`, `#8A8E95` (footer/disclaimer, ≥4.5 on white), rules `#ECECE8`/`#E4E4E0`.

## Page 1 bounds (§3.3)
- Title box is fixed at 66px. Street line is a single `nowrap` line with a size ladder by character count (64→54→46→38→32px) and ellipsis backstop. City is a fixed 22px second line.
- Narrative panel is `max-height: 81px` (4 lines at 13.5/1.5) with `overflow: hidden`, on top of the ~380-char generation cap.
- Hero photo is a fixed 300px plate. Stats row is 4 fixed cells. Nothing else on page 1 grows with data.

## Page architecture (§3.4)
- Variant A. The 40px running head (report · address | date) is the PDFShift header on every page including page 1; the brand masthead on page 1 is body content at the top of the flow. Footer (agent line | Page n of N) is the PDFShift footer on every page. Header and footer both start at page 1.
- Page box: 816×1056 with 52px side margins; running head 40px + footer ~58px reserved.

## Page set and numbering (§3.5)
Six pages: cover · your home · comparable sales · what the comps support · your market (conditional on MLS fetch) · next steps. The `overview` page is gone — the summary is the bounded "In short" panel on the cover. The contents page is gone — six pages do not need one, and it removes a derived-number surface. Page numbers are computed from the final page list after the conditional drop; a 5-page and a 6-page render both number correctly. `comparables` and `property` remain required.

## Fields carried from the current build
- `comp_confidence_grade` / `comp_confidence_reason` — pill on the comps page header and named in the range panel label. Grade square uses `primary`/`on_primary`; label on `tint` uses `primary_ink`.
- `comp.lot_display`, `comp.hoa_fee` / `hoa_frequency` — third line on each comp card; HOA null renders "HOA —".
- `market_trends`: median sale price + change, days to contract (`timeline_metrics.avg_marketing_days`), `dom_distribution.under_30`, `price_cut_stats.rate` + `median_cut`. Sentiment arrows only; no red/green fills.
- Schools (`school_district`, `school_elementary`, `school_middle`, `school_high`) and Location (county, neighborhood, census tract) as two more groups on "Your home"; rows dash when absent (the repo hides them — this keeps §3.6 consistent).
- Tax: land / improvement value, tax year.
- Dropped deliberately: contents page, overview page, "Market Overview" and "Aerial View" filler copy, coordinates row, 10-dot condition score, three-colour gauge, per-page agent headshot.

## Absence (§3.6, §3.7)
- Every unknown renders `—` in `#B9BBC1` with the label kept. 0 beds → "Studio". 0 DOM → "New". No decimals on integers (sq ft, year, counts).
- The 19 unsourced fields stay in the table as dashes AND are listed once in a "Not on record" strip on the "Your home" page, with the sentence "A dash means the record is silent, not that the answer is no." When sourcing lands, rows fill and the strip shrinks.
- "PIQ" is replaced with "Your home" as the column header.

## Estimated range (§7)
Page "What the comparable sales support": low–high of closed comps (pending/active shown for context, excluded from the range), median, a band on a fixed axis, and the subject's last recorded sale as a marker. Copy: "This is what recent sales of similar homes nearby support. It is a report of the market, not an appraisal, and a listing price is a conversation with your agent."

## Paths (§1, §7)
- Consumer: "Home value report", "Prepared for {requester name}", no owner-of-record row anywhere, disclosure line in footer notes.
- Agent: "Seller's report", "Prepared for the owners of {street}", owner-of-record row in Record & taxes.
- Both paths render the same six-page set from one template; the only branches are the three above.

## Fonts
Elegant: Cormorant Garamond 500 + Geist. Bold: Barlow Condensed 700 caps + Barlow. Modern: Manrope 800 + Manrope. All from Google Fonts; keep the base.jinja2 font-trigger div.

## Known open items
- The chart on "Your market" is bar-with-values-and-axis; if MLS fetch fails, the whole page drops (existing behaviour).
- Six sample brands are golden/themes.json; real affiliate colours will need a pass through the pixel auditor, not just this preview.
