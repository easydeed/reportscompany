# TrendyReports · Delivery Surfaces · Master Plan v2

**Merged:** `delivery surfaces plan v1` (design system) + `REPORT_DESIGN_REVIEW_v2` (findings)
**Date:** 2026-09-08
**Surfaces:** 8 delivery emails · 8 market report PDFs · 1 property report / CMA across 5 themes
**Register:** 42 items — 31 shipping to clients today
**Governs:** §0 Rules of Engagement from `EXECUTION_PLAN_2026-08-17.md`

---

## What changed in the merge

The v1 plan's design direction, token layer, data contract, QA matrix, and sequencing are adopted
wholesale. Three things were added:

1. **Workstream E — the property report / CMA.** v1 scoped to the eight market reports. The
   property report is also a delivery surface, it ships in five themes, and — confirmed — it is
   the same document as the CMA, delivered to consumer leads through the capture funnel. My most
   severe findings live there.
2. **Eleven email and market-report findings** folded into the bug register as B13–B23.
3. **Five open decisions** added to §12, including two that block Workstream E entirely.

Severities use the `DEFECT_LIST.md` model: **BROKEN** / **WRONG** / **FRAGILE** / **ROUGH**.

---

## 01 · Design decision

Unchanged from v1. Both surfaces adopt the **Editorial** direction: no colored banner, a
letterspaced wordmark over a rule, a headline that states a finding rather than naming a report,
figures as a rule-separated list. The email becomes the first page of the PDF compressed to 600px.

Shared vocabulary, not shared layout — tokens, rule weights, color budget, and type roles. At
600px the email cannot carry the PDF's type scale.

**Extended to the property report.** Workstream E adopts the same tokens and type scale but keeps
its own page architecture; it is a nine-page bound document, not a one-page brief. What it must
share is the token layer, the micro-label treatment, the status colors, and the placeholder
handling.

---

## 02 · Root cause

v1 identified one root cause and it is correct: **the theme injects raw hex and templates paint
it onto every element.** Eleven elements at equal emphasis means no emphasis, and nothing decides
what text color belongs on a brand fill.

The merge surfaces a **second root cause of equal weight: the same report renders different
numbers depending on which pipeline generation produced it.**

Six property report PDFs of the same address, generated the same day, split into two groups:

| | Group A | Group B |
|---|---|---|
| Files | `bold_report` · `classic_report` · `modern_report` · `teal` | `elegant` · `teal_report` |
| Subject sale price | **$369,000** | **$428,248** |
| Subject $/sqft | $469 | $544 |
| "Medium" comp | $610,750 (a computed median) | $631,500 (an actual comp) |
| Executive summary | absent | present |
| Market Trends page | absent | present |
| Aerial imagery | stock drone photo | real Google map |

A seventh render (`1358_5TH_ST_Seller_Report.pdf`) belongs to neither, showing a third subject
value of $436,812.

**Three valuations for one property.** This is not a template problem and the token layer does not
touch it. It is the same class of defect as the count contradictions in B1/B8 — one number written
into slots that should be derived — and it is resolved by the same instrument: §08's data contract.

### Contrast of the current build, measured

| Theme | Primary | As text on white | Result |
|---|---|---|---|
| Demo Title | `#DC2626` | 4.83:1 | Passes |
| **Luxury Estates** | `#0D9488` | **3.74:1** | **Fails — shipping now** |
| Coastal | `#0E7490` | 5.36:1 | Passes |
| Amber | `#F59E0B` | 2.15:1 | Fails badly |
| Lime | `#84CC16` | 1.98:1 | Fails badly |
| Violet | `#7C3AED` | 5.70:1 | Passes |

Luxury Estates ships `#0D9488` as the price color on every listing card in every PDF today.

---

## 03 · Design system

Unchanged from v1 §3. Reproduced in brief; the v1 document remains authoritative for the full
token tables.

**3.1 Derived tokens** — affiliate picks one color; five values derived at render time.
`primary` (fills only) · `primary_dark` (×0.78) · `primary_ink` (darkened in 6% steps until ≥4.5:1
on white — the only brand value permitted on a light surface) · `on_primary` (whichever of white
or `#14151A` scores higher against primary) · `tint` (6% alpha, pre-flattened because Outlook
drops rgba).

Amber and lime — the two that break the current build — resolve automatically. The picker needs
no restrictions.

**3.2 Fixed neutrals** — canvas, card, panel, ink, body, muted, quiet, rule. Not themeable.
Identical across all three surfaces.

**3.3 Status colors** — reserved, never drawn from the brand palette, always paired with a text
label. Note "Closed" is currently rendered red, which reads as an error.

**3.4 Typography** — six steps, no others. Gmail strips `@import`, so the system is designed for
the fallback stack rather than pretending the Outfit webfont loads. System mono carries
micro-labels on all surfaces.

**3.5 Brand color budget** — three placements per surface, hard limit. This is what fixes
"everything is red"; the token layer only makes the color *safe*, not *quiet*.

**3.6 Logo fallback** — uploaded logo at 28px optical height, or the company name in letterspaced
caps at the same size. The strings `Footer Logo`, `Logo`, `Placeholder` must never reach a
rendered document.

---

## 04 · Workstream A · Token layer

**Blocking.** C, D, and E all consume it. Ships behind existing templates with no visual change.

Implementation per v1 §4.1 (`themes.py`, `derive_theme()`). Required tests per §4.2: property test
over 5,000 random hex values, degenerate inputs (`#FFFFFF`, `#000000`, `#FFFF00`), determinism,
and golden-file regression lock on the six known themes.

**Acceptance:** no template contains a brand hex literal, enforced by lint over the template
directory. Existing sends render within a perceptible-difference threshold.

**Effort: S.** One file, one test module.

---

## 05 · Workstream B · Bug register

Independent of the redesign and of each other. Every item is reproducible in current output. Ship
this workstream before any design work begins.

### From v1

| # | Type | Surface | Symptom | Fix |
|---|---|---|---|---|
| **B1** | BROKEN | PDF ×8 | `117` is the masthead figure on every report, labelled with the report name rather than a metric. Closed Sales reads "thirty-eight homes closed" in the insight and "all 50 closed sales" in the caption. | §08 contract |
| **B2** | BROKEN | PDF | `Footer Logo` renders as literal placeholder text in client-facing output | §3.6 + §08 string check |
| **B3** | BROKEN | Email — open_houses | Quick Take label `#1D4ED8` on a `#DC2626` panel. Measured **1.4:1** | `on_primary`; panel removed in rebuild |
| **B4** | BROKEN | Email ×8 | `.mobile-stack`, `.metric-card`, `.band-row` defined in CSS and applied to **zero elements**. The four-across metric strip never stacks; 10px labels wrap to three lines at ~75px | Attach classes to real cells. Highest-impact single fix given mobile open share |
| **B5** | BROKEN | PDF — price_bands + | Missing photo renders as broken-image glyph with alt `Property` beside it; the same listing is a blank grey box elsewhere | One labelled placeholder: hatched fill, camera glyph, "Photo pending" |
| **B6** | WRONG | Email — price_bands | Bars normalised to the largest band while labels show share of total. Move-Up reads 43% beside a bar filled to 100% | Bar width equals the percentage shown |
| **B7** | WRONG | PDF — price_bands | Band counts 12/18/11/6 sum to **47** beside a total of **117** | §08 assertion |
| **B8** | WRONG | Email ×8 | `347` appears as active listings, new listings, total listings, open houses and featured homes, while the same documents report 23 and 58. featured_listings reads "these 347 featured homes" above a grid of six | Same root as B1 |
| **B9** | ROUGH | PDF ×8 | Continuation pages repeat the full masthead (~90pt) then carry few rows. ~⅓ of every page empty | Masthead page 1 only; running head after. §7.2 |
| **B10** | ROUGH | PDF ×8 | Commentary labelled "AI Market Insight" directly above the agent's photo, license and mobile | **See open decision 10 — do not implement as specified** |
| **B11** | FRAGILE | Email ×8 | `color-scheme: light` plus a rule that dark mode must never touch the content card. Gmail Android force-inverts anyway | Real `prefers-color-scheme` block against §3.2 dark neutrals |
| **B12** | ROUGH | Both | Empty cell renders as a bare hyphen. Status chip sits on the photo in galleries and past the price in list rows | "no data" in muted type; one chip position |

### Added in merge — market reports

| # | Type | Surface | Symptom | Fix |
|---|---|---|---|---|
| **B13** | WRONG | PDF ×8 | Filter line reads "under $1.5M (First-Time Buyer)" while listings show $1,762,500 · $1,837,500 · $1,912,500. Price Bands renders a **"$1.5M+" band** under an "under $1.5M" filter | Determine whether the filter is applied and the chip is wrong, or the reverse. Different severities |
| **B14** | WRONG | PDF — market_snapshot | Hero reads `$907,500 MEDIAN SALE PRICE`; the insight two inches below reads "a median of $922K" | Same figure computed twice. §08 |
| **B15** | WRONG | PDF — inventory | Displays `SALE RATIO 98.2%` and `AVG DOM 12` — closed-sale metrics on a report about listings that haven't sold | Per §09 report matrix: inventory shows months of supply, active DOM, price reductions |
| **B16** | WRONG | PDF — closed | No **sale date** column — the primary field for a closed comp. DOM column runs 3, 6, 9 … 87 then restarts at `-`, 3, 6 | Add sale date; verify DOM source |
| **B17** | ROUGH | PDF ×8 | No generation date anywhere. "Last 30 days" is relative with no anchor | Date on page 1 and in every page footer |
| **B18** | ROUGH | PDF ×8 | Every card in Featured Listings tagged `FEATURED`; every card in Open Houses, `OPEN HOUSE`. The title already said it | Badges only where the value varies between cards. Market Snapshot does this correctly |

### Added in merge — emails

| # | Type | Surface | Symptom | Fix |
|---|---|---|---|---|
| **B19** | BROKEN | Email ×8 | **Every link is a placeholder:** `example.com/report.pdf`, `example.com/unsubscribe`, `href="#"`, `mailto:affiliate@trendyreports-demo.com` | Verify against a production render. If these are what production emits, variables aren't substituting |
| **B20** | BROKEN | Email ×8 | **No physical postal address in the footer.** Entire footer is "Powered by TrendyReports / Unsubscribe • Update Preferences" | CAN-SPAM requires one. Blocked on open decision 09 — same answer as the marketing site's legal pages |
| **B21** | WRONG | Email ×8 | `href="tel:(213) 309-7286"` — parentheses and spaces in a `tel:` URI | `tel:+12133097286`, formatted number as link text |
| **B22** | WRONG | Email ×8 | "Update Preferences" is `href="#"` | Build the preference centre or remove the link. A dead preference link beside a working unsubscribe pushes people to unsubscribe |
| **B23** | ROUGH | Email ×8 | Agent email address renders as the word "Email"; `Realtor` used generically (REALTOR® is a restricted NAR mark) | Show the address. Change the default title to "Real Estate Agent" |

**Effort: S each.** B1 and B8 share a fix and are one ticket. B19–B22 are one ticket.

---

## 06 · Workstream C · Email template

Unchanged from v1 §06. One Jinja2 template replaces eight; body assembled from blocks selected by
report type; masthead, agent block and footer invariant.

**Blocks:** `masthead` · `spec_list` · `read` · `table` · `gallery` · `bands` · `cta` · `signature`.

**Constraints:** 80KB budget (Gmail clips at 102KB and hides the CTA and unsubscribe) · table
layout with VML CTA fallback · font stack declared once on `<body>` · rgba pre-flattened · every
mobile class attached to a real cell (B4) · dark mode designed, not opted out of · preheader per
report type stating the headline figure.

**Merge addition:** the `signature` and footer blocks must carry the physical postal address
(B20) and real link targets (B19).

**Effort: M.** Blocked by A.

---

## 07 · Workstream D · Market report PDFs

Unchanged from v1 §07.

**7.1 Page architecture** — full masthead page 1 (~150pt); one-line running head after (~38pt).
Footer pinned to page bottom on every page.

**7.2 Pagination** — 26 table rows per page · 9 gallery cards in 3×3 · 70% minimum fill · never
orphan fewer than four rows · truncation stated in a line beneath the list.

> **Discrepancy to reconcile before this lands.** v1 states table pages "carry five rows" today.
> The `closed.pdf` render reviewed carries **13, then 25, then 12**. Either v1 was written against
> a different render, or two builds are in play — which is exactly the Group A / Group B problem
> in §02. Confirm which build the pagination targets are set against.

**7.3 Charts** — there is currently no chart in any of the 32 pages. Single-series only in v1.
Marks in `primary_ink`, never raw primary. Direct-label the endpoint and the largest bar, never
every point.

**Effort: L.** Blocked by A and by open decision 01.

---

## 08 · Workstream E · Property report / CMA — **NEW**

Not in v1. Five themes, six renders reviewed, plus one older render.

### Why this outranks D

**The property report is the CMA**, and it is delivered through the consumer lead-capture funnel
(`lead_pages.py` → consumer CMA task) as well as by an agent directly. On that path it reaches a
stranger who has just entered their address on a landing page, with no agent in the loop to catch
anything.

It is also the surface where a seller decides what their home is worth.

### E-tier 1 · Live, and materially misleading

| # | Type | Symptom |
|---|---|---|
| **E1** | BROKEN | **The owner's legal name is printed** — `HERNANDEZ GERARDO J` / `MENDOZA YESSICA S` — under a heading reading **"Prospective Property"**. Teal and Modern go further: the aerial page reads *"the neighborhood in which your prospective property is located."* An automated document arriving after a web form, leading with assessor-roll name data, reads as surveillance. **Fix first.** Remove the block; the recipient knows who they are |
| **E2** | BROKEN | **Comps sold 5/10/23, 3/15/23, 4/25/22, 4/8/22 — 3.4 to 4.4 years old — under headings reading "SALES IN THE PAST 12 MONTHS"** and body copy stating "comparable homes sold within the last 12 months." Either the comp date window is broken or it correctly found nothing recent and the copy must say so. Blocked on open decision 08 |
| **E3** | WRONG | Subject sale price is **$369,000 in Group A, $428,248 in Group B, $436,812 in the older render**. $428,248 is the **tax assessment**, printed verbatim on the same report's Tax & Assessment block — a Prop 13 figure in a sale-price row beside comps at $470k–$635k |
| **E4** | BROKEN | **The aerial page is a stock photograph of a different country.** Bold, Classic, Modern and `teal.pdf` render a drone photo of a suburb with red tile roofs — not La Verne — and Modern and `teal.pdf` **drop a location pin on it**, captioned "your property's prime location within the neighborhood." Group B renders a real Google map. Same substitution on Range of Sales |

### E-tier 2 · Internal contradictions

| # | Type | Symptom |
|---|---|---|
| **E5** | WRONG | **"Medium" means two different things.** Group B: an actual comp ($631,500). Group A: the *median* ($610,750) — not a comp, not any property — while every other row in that column (sqft, year, beds) is drawn from a real listing. Group A's Medium column is a chimera |
| **E6** | WRONG | **The fourth comp vanishes.** Four comps are gathered, four appear on Sales Comparables, four feed the Range of Sales averages — but Area Sales Analysis shows only Low/Medium/High. **$590,000 (1848 1st St) appears nowhere in the analysis table** in any theme |
| **E7** | WRONG | Group A rows sorted independently then presented as three properties. The 698 sqft comp sold for $590,000, not the $470,000 in its column. Group B is correct — that is the target behaviour |
| **E8** | WRONG | Missing data as zero persists in Teal: **`Stories 0 0 0 0`**. And `Pools 1 0 0 0` for the subject while the same report's property page reads **`Pool/Spa: None`** — contradiction one page apart. The two Teal renders also disagree on whether the subject has a pool |
| **E9** | WRONG | **Market Trends is six months stale** — "JAN 2026 – MAR 2026", "Generated Mar 3, 2026", in a September render. Credit where due: it says so. But the older render showed La Verne median at **$921,750** and Group B shows **$615,000** — a 33% swing depending on which render arrives |
| **E10** | ROUGH | The date row above the analysis table carries four dates over a five-column table whose first column is the subject. The first date reads as the subject's |

### E-tier 3 · Rendering

| # | Type | Symptom |
|---|---|---|
| **E11** | BROKEN | **`teal.pdf` contents page renders as a skewed 3D-perspective card** on a grey-purple field, showing one entry where seven belong, page number rendering as **`0033`**, ~70% of the page an empty coloured panel. The worst-rendering page in any document reviewed |
| **E12** | BROKEN | `teal.pdf` cover prints **`123 Main St, Los Angeles, CA 90012`** — a placeholder — and the **"TrendyReports" wordmark strikes through the agent's phone number**. Two elements in the same space |
| **E13** | BROKEN | `teal_report` Area Sales summary row is **dark navy text on a dark navy band** — the most important row in the table is the one you can't read. Elegant solves it with a gold band |
| **E14** | BROKEN | **Agent headshot renders as an empty shape in all five themes** — navy square (Bold), absent (Classic), empty gold circle (Elegant), grey rounded square (Modern), grey circle (Teal). Not one theme handles a missing photo. Same class as B2/B5 |
| **E15** | ROUGH | **Page numbering broken in every theme.** The aerial page either carries no number (Bold, Classic, Modern) or duplicates the contents page's (Elegant and `teal_report` both print `03` twice). Contents entries then disagree with printed footers for every subsequent page |

### E-tier 4 · Parity and polish

| # | Type | Symptom |
|---|---|---|
| **E16** | FRAGILE | **Field sets differ by theme.** Modern omits Lot Size and Bathrooms; Teal adds Stories and Pools; Elegant and Bold carry the base set. An agent switching themes silently changes what analysis their client receives |
| **E17** | ROUGH | Contents labels don't match page titles: "Estimated Value Range" → "Range of Sales"; "Aerial Property View" → "Aerial View"; "Comparable Sales" → "Sales Comparables"; "Property Information" → "Prospective Property" |
| **E18** | ROUGH | **`PIQ`** as the subject column header in both Teal renders. Industry shorthand, meaningless to a homeowner. Every other theme says "Subject" |
| **E19** | ROUGH | Float formatting persists in Group B: `786.0` · `1949.0` · `2.0` · `770.0`. `Bathrooms 1.0` on every theme's property page. Group A formats correctly — the fix exists, unevenly applied |
| **E20** | ROUGH | **Classic renders no imagery at all** — no cover photo, no comp photos — while still carrying the stock aerial. **Modern's comps have no photos** while its cover and aerial do |
| **E21** | ROUGH | Executive summary occupies a full page with two sentences and ~80% whitespace (Group B) |
| **E22** | ROUGH | Elegant's bar chart has no values and no axis; `teal.pdf`'s labels render as **four apostrophes**. `teal_report` gets it right — labelled `$632k · $635k · $470k · $590k` with dates. Standardise on that |

### Theme parity

| | Bold | Classic | Elegant | Modern | Teal (new) | Teal (old) |
|---|---|---|---|---|---|---|
| Cover photo | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Executive summary | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ |
| Contents renders | ✓ | ✓ | ✓ | ✓ | ✓ | **broken** |
| Real map, not stock | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ |
| Market Trends page | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ |
| Comp photos | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ |
| Chart labelled | — | — | ✗ | — | ✓ | ✗ |
| Agent headshot | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Pages | 7 | 7 | 9 | 7 | 9 | 7 |

**An agent choosing Classic delivers a materially thinner product than one choosing Elegant** — a
two-page and four-feature gap on identical data.

### Target

**`teal_report` and Elegant are the reference implementations.** They are the only renders with an
executive summary, a real map, and a Market Trends page — and **Market Trends is the strongest
single page in the entire product**: the seller's/balanced/buyer's gauge with a marker at 2.8
months, six metrics with change indicators, and a data-source line naming SimplyRETS and the date
range.

Bring the other three themes to that feature set. Port the gauge and the change indicators to the
market reports (§09).

**Effort: L.** Blocked by A and by open decisions 07 and 08.

---

## 09 · Data contract

Unchanged from v1 §08, extended to cover E3–E7.

```python
{
  "headline": {"value": "$907,500", "label": "Median sale price",
               "delta": {"dir": "up", "label": "2.4% vs. July"}},
  "metrics":  [{"value": "12", "label": "Avg. days on market"}, ...],
  "universe": {"count": 117, "label": "active listings"},
  "shown":    {"count": 26, "of": 50},
  "series":   [...],
  "rows":     [...],
}
```

### Assertions at render time

1. Every figure appearing in generated copy exists in `headline` or `metrics`. **Fail the render
   otherwise** — a wrong number in a client document is worse than a late send.
2. Band and category counts sum to `universe.count`, or the discrepancy is labelled.
3. `shown.count == len(rows)`.
4. No rendered string matches `/^(Footer )?Logo$|Placeholder|Lorem|123 Main St|example\.com/i`
   *(extended: covers E12 and B19)*.
5. Every listing has a photo URL or an explicit `photo: None` that triggers the placeholder. A 404
   is not a valid state.
6. **New — property report:** the subject's sale-price field is either a genuine transaction or is
   explicitly labelled as an assessment. An assessed value may never occupy an unlabelled sale
   price row *(E3)*.
7. **New — property report:** every comp in `rows` appears in the analysis table, or the omission
   is stated *(E6)*.
8. **New — property report:** comps carry a real sale date, and the copy describing the window is
   derived from the actual date range rather than hardcoded *(E2)*.
9. **New — property report:** Low / Medium / High columns describe the same three properties
   across every row, or the columns are relabelled *(E5, E7)*.

**Effort: M.** Independent of A; runs in parallel.

---

## 10 · Report matrix

Unchanged from v1 §09. Each report declares its own headline metric; copy interpolates the same
variable it prints.

| Report | Headline metric | Chart | Email blocks | PDF pages |
|---|---|---|---|---|
| Market Snapshot | Median sale price | 12-mo median trend + band distribution | spec_list, read, table, cta | 3 |
| New Listings | New listings this period | New listings by week ×8 | spec_list, read, table, cta | 2–3 |
| Inventory | Months of supply | Months-of-supply trend | spec_list, read, table, cta | 3 |
| Closed Sales | Closed sales this period | Median close trend + DOM distribution | spec_list, read, table, cta | 3 |
| Price Bands | Active listings | Band distribution — the point of the report | spec_list, read, bands, cta | 2 |
| Open Houses | Open houses this weekend | None — a schedule, not a distribution | spec_list, read, gallery, cta | 2 |
| New Listings Gallery | New listings this period | None | read, gallery, cta | 2–3 |
| Featured Listings | Featured homes | None | read, gallery, cta | 2 |

**Merge note:** only `market_snapshot` and `new_listings_gallery` have actually run in production
since July 1 (24 of 24 generations). The other six may not warrant equal effort in Phase 4 —
worth confirming before the rollout scope is fixed.

---

## 11 · QA & acceptance

### Automated

- **Contrast property test** — §04, every commit
- **Theme matrix render** — every template × six themes, asserting no rendered text/background pair
  falls below 4.5:1. *This is the check that would have caught the live Luxury Estates defect*
- **Placeholder string scan** — §09 assertion 4
- **Email size gate** — fail above 80KB
- **Page fill check** — fail any PDF page below 70% fill that is not the last page
- **Image resolution check** — every photo URL returns 200 before render begins
- **New — render determinism:** the same input renders identical figures across themes. Catches
  §02's Group A / Group B divergence

### Manual client matrix

Once per release. Litmus or Email on Acid covers the first eight; dark-mode rows need real devices.
Gmail Web · Gmail iOS/Android · **Gmail Android dark** (forced inversion) · Apple Mail macOS/iOS ·
Outlook 365 Windows (VML CTA, no radius, no background images) · Outlook.com · Yahoo/AOL.

### Definition of done

- All 42 register items closed and verified **in rendered output, not in code review**
- All 8 market reports render on both surfaces under all 6 themes with zero contrast failures
- The property report renders in all 5 themes with identical figures and full feature parity
- No PDF page below 70% fill; every page numbered; no placeholder strings anywhere
- Email under 80KB; mobile stacking confirmed on a real Android device
- An email and its attached PDF, viewed side by side, read as one document to someone who was not
  told to look for it

---

## 12 · Sequencing

```
PHASE 1        PHASE 1         PHASE 2       PHASE 3            PHASE 4
B · BUGS       DATA CONTRACT   A · TOKENS    C+D+E one report   ROLLOUT
ship first     parallel        blocking      end to end         all surfaces
no deps        closes B1/B7/B8 no visual Δ   pilot affiliate    full
```

| Phase | Contains | Blocked by | Effort | Ships to clients |
|---|---|---|---|---|
| 1 | Bug register B1–B23 | — | S × 23 | Yes, incrementally |
| 1 | **E1 and E4** — pulled forward | — | S | **Yes — consumer-facing** |
| 1 | Data contract §09 | — | M | Closes B1, B7, B8, E3, E6 |
| 2 | Token layer §04 | — | S | No visible change |
| 3 | Email template, one report end-to-end | 2 | M | Pilot affiliate |
| 3 | PDF architecture + first chart | 2 | L | Pilot affiliate |
| 3 | Property report — Elegant as reference | 2, decisions 07/08 | L | Pilot affiliate |
| 4 | Remaining reports and themes | 3 | M | Full rollout |

**E1 and E4 are pulled into Phase 1** ahead of the design work. Removing the owner block and
replacing a foreign stock photo with an honest failure state are both small changes, and both are
on documents reaching consumer leads today.

Phase 3 deliberately takes **Market Snapshot** all the way through email and PDF before the others
start — it exercises every block. The property report runs **Elegant** as its reference for the
same reason.

---

## 13 · Open decisions

| # | Question | Blocks | Owner |
|---|---|---|---|
| 01 | **Does the pipeline hold historical data?** Four reports are specified with a 12-month trend line; every sample covers 30 days. If only the current period is fetched, trend charts are blocked and Phase 3 ships distributions only | Workstream D scope | Eng |
| 02 | **Drop the secondary brand color?** Templates consume two; the system needs one. Two means deriving and validating a second set and checking every pairing against each other, not just against white. **Recommend one** | Workstream A | Product |
| 03 | **Who writes the commentary, and from what?** If copy comes from a separate query than the rendered metrics, that coupling is the actual fix for B1/B8. **Note:** `generate_insight()` takes no `account_id` and is gated only by a process-wide `AI_INSIGHTS_ENABLED` whose production value is **still unknown** — the commentary may not be running at all | Data contract | Eng |
| 04 | **Does "Powered by TrendyReports" stay in a white-label send?** Sits in the footer under the affiliate's own branding | Email footer | Product |
| 05 | **Are MLS photos licensed for redistribution in a forwardable PDF?** Emails hotlink; the PDF embeds. Different posture | Phase 4 | Compliance |
| 06 | **Is logo upload guaranteed at onboarding?** If mandatory, B2 is an onboarding validation gap as well as a rendering one | B2 | Product |
| **07** | **Which property render group is production — A or B?** Three different subject valuations exist for one address. Every Workstream E theme finding depends on the answer | **Workstream E** | Eng |
| **08** | **Is the comp date window broken, or did it correctly find nothing recent?** Determines whether E2 is a query fix or a copy fix | **E2** | Eng |
| **09** | **What is the registered business postal address?** Required for the email footer (B20) and the marketing site's legal pages (G3 in the marketing plan). **One answer closes both** | B20, G3 | Jerry |
| **10** | **B10 attribution.** Putting a named agent's byline on LLM-generated commentary that feeds a pricing decision, with no disclosure, is a liability question rather than a design one — especially while the figures are still inconsistent. **Recommend:** attribute as a prepared summary, retain a "prepared with market data from SimplyRETS" line | B10 | Product / legal |
| **11** | **Pagination baseline.** v1 says table pages carry five rows; the reviewed render carries 13/25/12. Reconcile before §7.2 targets are set — likely the same Group A/B split as decision 07 | Workstream D | Eng |

---

## 14 · Out of scope

The application UI · replacing the PDF generation engine · deliverability, sending infrastructure
and list management · copy generation quality (this plan changes where commentary sits and how it
is attributed, not how it is written) · localisation and RTL · any surface beyond email and PDF.
