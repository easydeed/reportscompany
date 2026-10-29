# Design handoff — TrendyReports redesign

Repo: `easydeed/reportscompany` · Prepared 2026-10-15 · Covers everything designed Sep 23 – Oct 6, 2026.

Three packages, each self-contained (open any `.dc.html` in a browser with the `support.js` beside it; no build step). Commit all three folders plus this file.

| package | scope | start with |
|---|---|---|
| `design_handoff_product/` | Landing page, authenticated app shell + 11 pages, four wizard flows (onboarding, new report, new schedule, property report + comps map), public Home Value Page | `README.md` |
| `design_handoff_market_reports/` | The 7 market-report PDF types (`market.jinja2`) — one page template dispatched on kind, running head / masthead / footer architecture, colour-role derivation, headline rules, continuation paging | `README.md`, then `RESPONSE_2026-10-06.md` (structure answer + `display_ink`) |
| `design_handoff_property_report/` | The 6-page property report / consumer CMA (`property/<theme>/<theme>_report.jinja2`) — three themes, agent vs consumer paths, absence rules, page-capacity bounds | `STRUCTURAL_NOTE.md`, then `README.md` |

## How the packages fit together
- The product surfaces **embed** the PDF designs: the landing hero, dashboard, report lists, branding page and every wizard step render `Report Page` (market) or `Property Report Cover` (property) live. Whatever the builders produce must look like those files — the product package assumes it.
- Colour has two layers. **Agent brand** (`primary` + `accent`, or the property `brand_hex`) appears only inside reports, the brand swatch picker and the Home Value Page. **Product UI** is ink `#0F172A` on white/cream with indigo `#4F46E5` reserved for links and the landing CTA. The derivation tokens (`on_primary`, `primary_ink`, `accent_ink`, `display_ink`, `tint`, `primary_on_dark`) are defined once in `themes.derive_theme` and shared by both PDF builders — the product never computes colour.
- Type: product = Plus Jakarta Sans; market PDFs = Geist + Geist Mono; property PDFs = per theme (Cormorant Garamond + Geist / Barlow Condensed + Barlow / Manrope). No other faces.

## Decisions already made (do not reopen without the owner)
1. Market reports: running head is the PDFShift header and the one-line footer is the PDFShift footer, both `start_at = 1`; the brand masthead and the agent block are body content. No continuation brand strip.
2. `display_ink = white if contrast(white, primary) ≥ 3.0 else on_primary` — a derived token, not an auditor exception. Applies to 3 sites in `Report Page` and 4 in `Property Report`.
3. Property report: three themes (elegant, bold, modern); classic and teal removed; six pages; no contents/overview page; "Not on record" strip keeps the 19 unsourced fields as dashes.
4. Pricing unit is reports sent per month (Free 3 / Growth 25 / Plus unlimited); cities and cadence are the plan gates.
5. Onboarding order: area → brand → real report sent to the agent → autopilot; the wizard hands off to the dashboard with `?from=onboarding`.
6. No text over photography anywhere, no status chips with tinted fills behind semantic text, no SVG illustration, no emoji.

## Open with engineering
- **Market package measurement**: the 2026-10-06 review listed a `Market Report.dc.html` and four themes — neither exists in `design_handoff_market_reports/`. Please confirm the path and modification date of what was measured; if it predates 2026-10-05, replace it with the folder wholesale. Details in `design_handoff_market_reports/RESPONSE_2026-10-06.md`.
- Product-package open items are listed at the end of `design_handoff_product/README.md` (hero render strategy, TCPA consent copy, weekly-cadence gating, comps-map mount, admin verification).

## File inventory
```
DESIGN_HANDOFF.md                         this index
design_handoff_product/
  README.md                               full spec: system, Landing, App (11 pages), Wizards (4 flows), Home Value Page
  Landing v4.dc.html                      marketing home
  App v3.dc.html                          app shell + pages (Tweaks: theme, firstRun, showAdmin, showUsage)
  Wizards v3.dc.html                      four flows (Tweaks: flow)
  Home Value Page.dc.html                 public funnel (Tweaks: brand)
  comps-map.html                          Leaflet comps picker, iframed by the property wizard
  Report Page.dc.html                     dependency — market report page
  Property Report.dc.html                 dependency — property report
  Property Report Cover.dc.html           dependency — cover wrapper
  support.js                              runtime
design_handoff_market_reports/
  README.md · RESPONSE_2026-10-05.md · RESPONSE_2026-10-06.md
  Report Page.dc.html · Report Page Gallery.dc.html · PDF Reports v2.dc.html · support.js
design_handoff_property_report/
  README.md · STRUCTURAL_NOTE.md · RESPONSE_2026-10-05.md
  Property Report.dc.html · Property Report Matrix.dc.html · Property Report Cover.dc.html · support.js
```
Each package's `.dc.html` set is a snapshot as of its README date; the working copies at the project root may move on after this commit.
