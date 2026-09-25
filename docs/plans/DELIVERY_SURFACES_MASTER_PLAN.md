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

**3.1 Derived tokens** — affiliate picks one color; **six** values derived at render time.
`primary` (fills only) · `primary_dark` (×0.78) · `primary_ink` (darkened in 6% steps until ≥4.5:1
on white — the only brand value permitted on a light surface) · `on_primary` (whichever of white
or `#14151A` scores higher against primary) · `tint` (6% alpha, pre-flattened because Outlook
drops rgba) · **`primary_on_dark`** (brightened until ≥4.5:1 on one fixed dark neutral).

**The sixth token, added 2026-09-23.** The original five had no counterpart for brand text on a
*dark* surface — `primary_ink` guarantees a ratio on white and §3.1 had no concept of a dark
surface at all, while three property themes and the market header put brand-coloured text on one.
The survey that established this counted every `var()` reference: the `-light` family is decorative
(36 uses, none carrying text) and the `-on-dark` family is text every time (15 uses, all `color:`).
So the set was short exactly one token, not two.

**`DARK_SURFACE = #0f172a`, fixed, not per-theme** (Jerry, 2026-09-23): *"§3.2 already fixes
neutrals for this reason, and five surfaces means five drift paths."* `#0f172a` because it is the
dark neutral these templates already use most, so the token converges on the design rather than
adding to it — and it is a neutral, where the previous default `#18235c` has chroma 68 and is
somebody's brand colour doing a neutral's job.

> **The guarantee is against that surface and no other, which is a condition rather than a detail.**
> Six of the eight dark surfaces the templates paint today are lighter than `#0f172a`, so a value
> clearing 4.5:1 there does not clear it here — **3.24:1 on classic's `#1B365D`**, 3.80 on bold's
> `#15216E`, 3.91 on `#18235c`, 4.47 on `#0f1a45`. That is the migration this decision implies: the
> dark panels become the neutral. Until they do, `primary_on_dark` is correct about a surface the
> page does not yet have. The four shortfalls are asserted exactly in
> `test_the_guarantee_is_against_the_fixed_surface_and_no_other`, so the list is a checklist that
> fails when a panel migrates rather than a note that goes stale.

Brightening raises HSV value first and spends saturation only once value has maxed out — the rule
D-099 established by measurement on the PDF path, where reducing saturation every step turned a
navy brand into a grey (chroma 33 against 156). Both derivations now use it, so they cannot drift.

Amber and lime — the two that break the current build — resolve automatically. The picker needs
no restrictions.

Amber and lime — the two that break the current build — resolve automatically. The picker needs
no restrictions.

**3.2 Fixed neutrals** — canvas, card, panel, ink, body, muted, quiet, rule. Not themeable.
Identical across all three surfaces.

> ### A background that varies cannot be made accessible by choosing a foreground
>
> **A design constraint, reached independently from two directions, and it binds Workstreams D and
> E harder than it binds C.**
>
> Contrast is a relation between two colours. Every derivation in §3.1 works by moving one of them
> until the ratio clears — which requires the other one to be known and fixed. Where it is not,
> there is nothing to derive against, and no choice of text colour is correct.
>
> Two surfaces in this product already fail that way:
>
> - **The market report's header band** runs `linear-gradient(135deg, header-bg → primary-color)`.
>   No single text colour clears 4.5:1 against both ends; the label measures 9.90:1 where it starts
>   and 2.53:1 where the brand takes over. `_ensure_readable_on_dark` now returns the best worst
>   case and logs that it fell short, which is the honest answer and not a fix.
> - **The teal cover overlay** composites a three-stop alpha gradient over whichever photo the
>   listing carries. The effective backdrop differs from the top of the panel to the bottom and
>   again for every property. There is no value to compute a ratio from at all.
>
> The remedies are structural, never chromatic: a **scrim** (a fixed layer between image and text,
> which then IS a surface and can be guaranteed against), a **solid plate** behind the text block,
> or **text off the image**. Picking a different colour is not among them.
>
> **Why this matters most for D and E.** Photo-backed covers are the norm on the PDF surfaces, and
> §7 and §9 assume text over imagery in several places. Any such composition needs its scrim
> specified as part of the design, not discovered when the contrast audit reports a ratio it cannot
> compute. Treat "text over a photograph" as requiring a named opaque surface, the same way §3.2
> treats the neutrals — because that is exactly what it is.

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

### 04.1 · Built — and two findings that change what A is

*2026-09-23, `feat/workstream-a-token-layer`.*

`apps/worker/src/worker/themes.py` implements §3.1 exactly: `derive_theme()` returns the five
tokens, pure and `lru_cache`d on the colour. `apps/worker/tests/test_themes.py` carries the four
required test classes plus the guards that a degenerate implementation fails, and
`apps/worker/tests/golden/themes.json` locks the six themes. `scripts/lint_template_colors.py`
carries the acceptance criterion.

**It does not consume `compute_color_roles`, and it does not replace it yet.** The live six-role
derivation in `property_builder.py` stays exactly where it is; the two modules coexist with a test
asserting their shared luminance agrees, so they cannot diverge silently. Replacing it is the
migration, not this.

**Finding 1 — A cannot ship invisibly. The current colours are worse than §02 recorded.**

§02 measured the six *picker presets*. The values the *templates* ship are a different set, and
five of the seven brand/text pairs fail AA:

| surface | fill | text on fill | brand text on white |
|---|---|---|---|
| property/teal | `#34D1C3` | `#1a1a1a` 9.16 | `#1abaae` **2.42 FAIL** |
| property/bold | `#0F1629` | `#ffffff` 17.99 | `#15216E` 14.24 |
| property/classic | `#1B365D` | `#ffffff` 12.12 | `#1B365D` 12.12 |
| property/modern | `#FF6B5B` | `#ffffff` **2.80 FAIL** | `#d94e3f` **4.11 FAIL** |
| property/elegant | `#1A1A1A` | `#ffffff` 17.40 | `#1a1a1a` 17.40 |
| market | `#0d9488` | `#ffffff` **3.74 FAIL** | `#0f766e` 5.47 |

`#1abaae` at **2.42:1** is worse than the 3.74 that motivated the workstream, and it sits in the
slot whose only job is to be readable on a light surface.

Substituting the tokens therefore moves 12 of 17 brand-role values past ΔE 2.3, two of them by
ΔE 93 — `--coral-text` and `--accent-text` flip from white to `#14151a` because white on those
fills is unreadable. **Those moves are the fix.** But "ships behind existing templates with no
visual change" is not available, and the migration needs to be reviewed as a visible change per
surface. Filed as **D-097**.

**Finding 2 — §4.2 asks for a property §3.1 cannot deliver.**

`contrast(on_primary, primary) >= 4.5` is unachievable for ~5% of sRGB. White and `#14151A` are
fixed; their curves cross at *L* = 0.196 where both score **4.27:1**. Measured: 1,056 of 20,000
random colours fall short, worst `#9158f5` at 4.27. Nothing shipping is affected. Left as a strict
xfail rather than quietly relaxed; remedies and the **[JERRY]** decision are on **D-098**.

**The `--*-light` / `--*-on-dark` gap, surveyed 2026-09-23 rather than guessed.** Every `var()`
reference was classified by the CSS property it lands in:

- **`-light` is decorative** — 36 uses across six tokens, **zero** that carry text once classic's
  three are seen for what they are (brand text on a *dark* panel, wearing the wrong token name).
  `tint` and `primary_dark` cover it. The set is not short on this account.
- **`-on-dark` is text, every time** — 15 uses, all `color:`. `primary_ink` guarantees 4.5:1 **on
  white**; §3.1 has no concept of a dark surface, and three property themes plus the market header
  put brand text on one.

**So the set is short one token, not two: a brand value readable on a dark neutral.** What the
decision has to settle is whether that neutral is fixed (`compute_color_roles` assumes `#18235c`;
the themes' actual darks are `#18235c`, `#0f1a45`, `#0b0f1a`, `#1a1f36`) or an argument. **[JERRY]**

Three tokens — `--teal-light`, `--navy-light`, `--navy-on-dark` — are declared and never
referenced. They are the only baselined literals removable with provably zero visual change.

**`on_primary` may not adjust the fill (decided 2026-09-23).** The fill is the affiliate's colour
and stays exactly as given; contrast is satisfied by choosing the text. This closes the one remedy
that would have delivered §4.2's property, so the D-098 shortfall is now by design. §3.1's
acceptance criterion was wrong, not `themes.py`.

**Acceptance status.** The lint exists and is wired into CI. It reports **111 brand hex literals
across 26 of 30 template files** — run against `main` before anything was touched, because a rule
that has never been seen to fire is indistinguishable from one that matches nothing. The 111 are
baselined in `scripts/template_color_baseline.txt`; CI fails on a new one and the file may only
shrink. The criterion is met when it is empty.

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
| **B5** | BROKEN | PDF — price_bands + | Missing photo renders as broken-image glyph with alt `Property` beside it; the same listing is a blank grey box elsewhere | One labelled placeholder: hatched fill, camera glyph, "Photo pending" — **STILL OPEN**, see note |
| **B6** | WRONG | Email — price_bands | Bars normalised to the largest band while labels show share of total. Move-Up reads 43% beside a bar filled to 100% | Bar width equals the percentage shown — **STILL OPEN**, see note |
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

> **B5 and B6 are NOT closed by the consolidation, and the risk is that they look it.**
>
> Both are named in comments in the code the consolidation produced — B6 beside `_band_rows()`,
> which now computes the bar width and the percentage label together because two calculations in
> two files is how they drifted apart; B5 beside `_GALLERY_SIZES`, whose missing-photo branch is a
> grey block on all three card sizes.
>
> Those comments explain **why the code has its shape**, not that the defect is fixed. The
> restructure deliberately preserved current behaviour: the bars are still normalised to the
> largest band, and the placeholder is still an unlabelled grey box rather than a hatched fill with
> a camera glyph. A restructure whose acceptance is an empty render diff cannot also change what
> renders.
>
> Both fixes belong in a branch where the visible change is the point. Recorded here because a
> register item with its number written in a code comment is exactly the kind of thing that gets
> marked done by proximity.

### 05.1 · The email half of the register, re-checked against live renders

*2026-09-23, before starting C.* The register is a pre-remediation audit and eight months of
defect work has happened since. Every email-side item was re-run through `schedule_email_html`
rather than read — and each "does not reproduce" carries a positive control, because a negative
grep and a broken grep produce the same output.

| # | re-check | note |
|---|---|---|
| **B3** | **reproduces, worse than recorded** | Not `#1D4ED8` on `#DC2626`. The label is `accent_color` and the panel is `primary_color` — two independent brand columns with nothing relating them. 1.13–2.14:1 across the six themes, and **1.00:1** when an account sets one colour rather than two. **Fixed.** |
| **B4** | **reproduces** | `.mobile-stack`, `.metric-card`, `.band-row` defined and attached to zero elements, exactly as recorded. **Fixed** (`.band-row` is dead — the band rows are single-cell and have nothing to stack). |
| **B11** | **partially** | A `prefers-color-scheme: dark` block exists, so it is not opted out. But it adapts the outer chrome only and its own comment says the content card must NEVER be touched, which is the complaint. Its `#232323` is not a §3.2 neutral — and §3.2's dark neutrals do not exist yet. **Left open**, needs the token set first. |
| **B12** | does not reproduce | Positive control: a listing with every field `None` renders "no data" in three cells, zero bare hyphens, zero `None`. Closed by D-090. |
| **B19** | does not reproduce | Closed by `fix/postal-address`; the placeholder links are gone and tests hold them. |
| **B20** | does not reproduce | The slot exists **and is honoured** — positive control: setting `postal_address` renders it. A real platform address ships as the fallback (D-060). Not gated any more. |
| **B21** | does not reproduce | `_tel_uri` normalises; twelve input formats pinned. |
| **B22** | does not reproduce | The dead "Update Preferences" link is gone. |
| **B23** | **reproduced, now fixed** | The email pill rendered the word "Email" while the phone pill beside it showed the number. The `Realtor` half was already closed by D-066. |

**Two the register did not have**, both found by measuring rather than by reading:

- **The unsubscribe link is 2.41:1.** D-060's follow-up raised the postal address off `#9ca3af` and
  *named the unsubscribe link as the thing it was matching* — then left it there. The same
  "clearly and conspicuously" argument covers the opt-out. **Fixed.**
- **The status palette fails its own labels.** White on `#16a34a` is 3.30:1, on `#f59e0b` 2.15:1.
  **Fixed**, with values already present in the PDF templates.

**Size is not a problem.** The §06 budget is 80KB against Gmail's 102KB clip; the eight report
types render 23.9–34.5KB.

---

## 06 · Workstream C · Email template

Unchanged from v1 §06. One Jinja2 template replaces eight; body assembled from blocks selected by
report type; masthead, agent block and footer invariant.

> ### Correction: "selected by report type" is not how selection works
>
> *2026-09-24, from building it.* The phrasing above implies the report type — or the layout it
> maps to — determines the block sequence. **It does not. Selection is conditional on the DATA as
> much as on the type**, and the difference is not cosmetic: it decides what shape the map that
> describes it can have.
>
> The case that proves it: `market_snapshot`, `new_listings` and `open_houses` all use the
> `market_narrative` layout and produce **two different sequences**. `open_houses` renders the
> Quick Take panel where the other two render the market-insight callout, because the panel is
> emitted only `if not insight_text` — a data condition, not a type one. Three further blocks
> (`chrome:filter_blurb`, `chrome:section_label`, `bands`) appear only when a filter description or
> band data is present.
>
> So `REPORT_BLOCKS` in `email/template.py` is keyed by report type rather than by layout, and even
> then it describes the sequence **for a given fixture**; a layout-keyed map could not express the
> `open_houses` case at all. It is checked against an instrumented render rather than maintained by
> hand.
>
> **Carried forward for Workstream D.** The PDF surfaces have the same shape — a page set selected
> per report with sections that appear only when their data does — so an equivalent map there will
> be data-conditional too. Writing it as "sections selected by report type" would inherit this
> error, and the version that gets written from reading the builders will be wrong in the same way
> this one was: seven of eight entries, corrected only by instrumenting an actual render.

**Blocks:** `masthead` · `spec_list` · `read` · `table` · `gallery` · `bands` · `cta` · `signature`.

**Constraints:** 80KB budget (Gmail clips at 102KB and hides the CTA and unsubscribe) · table
layout with VML CTA fallback · font stack declared once on `<body>` · rgba pre-flattened · every
mobile class attached to a real cell (B4) · dark mode designed, not opted out of · preheader per
report type stating the headline figure.

**Merge addition:** the `signature` and footer blocks must carry the physical postal address
(B20) and real link targets (B19).

**Effort: M.** Blocked by A.

### 06.1 · Started — the colour layer, ahead of the template consolidation

*2026-09-23, `feat/workstream-c-email-rebuild`.* The one-template-replaces-eight rebuild has not
started. What has landed is the part A exists to enable, and it was larger than B3 suggested.

**Measured with a walker over rendered documents** (`apps/worker/tests/_contrast_audit.py`), which
resolves each text run's real background through the table nesting, measures gradients at every
stop and flattens rgba over its backdrop:

    1,167 unreadable text runs out of 3,822  →  0
    seven brands (the six themes plus unbranded) × eight report types

The rule applied throughout: **a builder derives the role it needs from the colour it was handed.**
Not threaded from the caller — a threaded role can be threaded wrongly, and `_build_quick_take`
being passed a label colour and a panel colour as unrelated arguments is precisely how it came to
paint one brand colour on another.

Open, and on the entries rather than here: the dark-mode block (B11, needs §3.2's dark neutrals),
the eight-into-one template consolidation, the 80KB budget work (not currently binding), and the
preheader per report type.

**The consolidation's acceptance is the auditor at 0.** Correctness first means the eight-into-one
rebuild is a pure restructure with a measurable invariant, instead of a redesign and a bug-fix in
one diff with no way to attribute a change to either.

### 06.2 · D-099 taken before continuing, because D inherits it

*2026-09-23, `fix/d099-readability-helpers`.* `compute_color_roles` feeds both PDF paths and would
have carried a 3.0:1 target into Workstream D's charts. Every role on every theme now clears 4.5,
locked with its achieved ratio in `apps/worker/tests/golden/color_roles.json`.

Seven of the fifteen role values on the five property themes move past ΔE 2.3, and all seven go
from failing to passing. The eight that do not move are the eight that already passed.

Two things came out of it that belong to the plan rather than the entry:

- **`theme_color_text` has D-098's ceiling too**, arrived at independently on the PDF path by a
  function written years apart from `derive_theme`. D-098 reads like a fact about `themes.py`; it
  is a fact about any binary choice of text against a fill that may not move. Both now gate a
  strict xfail.
- **The market header band cannot be satisfied as designed.** Guaranteeing against both ends — which
  is what §04.1's finding asked for — shows that no single colour clears 4.5:1 against a very dark
  navy *and* a mid-tone brand. The helper returns the best worst case and reports the shortfall.
  Narrowing the gradient, moving the label off the changing part, or accepting 3:1 there is a design
  decision. **[JERRY]**

---

## 07 · Workstream D · Market report PDFs

Unchanged from v1 §07.

**7.1 Page architecture** — full masthead page 1 (~150pt); one-line running head after (~38pt).
Footer pinned to page bottom on every page.

> ### Correction: this is case C, and PDFShift will not do it
>
> *2026-09-24, from running the probe.* The spec above asks for three things at once: a full
> masthead on page 1, a slim running head from page 2, and a footer on **every** page. In PDFShift's
> terms that is `header.start_at = 2` with `footer.start_at = 1`.
>
> `scripts/probe_pdfshift_start_at.py` rendered one four-page document four ways. **PDFShift accepts
> differing `start_at` values with a 200 and silently applies `max(header, footer)` to both.** Ask
> for header@2 and footer@1 and both arrive at page 2 — no error, no warning, and page 1 loses its
> footer. Full verdict table on **D-103**.
>
> The instrument mattered more than the answer here: the probe searched the rendered pages for
> marker strings rather than checking the HTTP status, and the status was 200 in every case. A
> docs-based answer, or a probe that stopped at "accepted", would have reported no constraint at
> all.
>
> **The architecture that replaces it: the masthead moves out of PDFShift's header slot and into the
> document body.**
>
> | | today | corrected |
> |---|---|---|
> | page 1 masthead | PDFShift `header`, repeated at full size on every page | ordinary body content, first thing on page 1 |
> | pages 2+ head | the same full masthead again | PDFShift `header`, slim running head |
> | footer | PDFShift `footer`, every page | unchanged, every page |
> | reserved band | 1.4in top on every page | the running head only |
>
> This gets §7.1's intent within the constraint rather than around it, and it puts the masthead
> under CSS control instead of a height negotiated with a vendor's reservation — which is also the
> other half of D-103, where 2.4in of every page is reserved for 1.946in of paint.
>
> **ONE CORRECTION TO THE CORRECTION, AND IT IS THE SAME TRAP AGAIN.** Moving the masthead into the
> body does not by itself let `header.start_at` and `footer.start_at` differ. The slim running head
> still wants to start at page 2 and the footer still wants page 1, and PDFShift coerces that pair
> exactly as it coerced case C — the page-1 footer disappears. What changes is the masthead's
> location, not what the two `start_at` values are asking for.
>
> Two variants survive the verdict, and they differ in what page 1 shows:
>
> **A — both `start_at` at 1, running head on page 1 too.** Nothing differs, so nothing is coerced.
> Page 1 carries the slim running head band *and* the body masthead below it; pages 2+ carry the
> running head. Footer on every page, as specified. The cost is a thin band above page 1's
> masthead, which is a design problem with a design answer (make the band read as the masthead's
> top rule) rather than a missing footer.
>
> **B — both at 2, page-1 footer rendered in the body.** Matched, so nothing is coerced, and page 1
> shows only the masthead. But pinning a footer to the bottom of page 1 inside a flowing document
> needs page 1 to be a fixed-height section, which is brittle in exactly the way the rest of this
> layout is not.
>
> **A is the one to build**, and B is recorded rather than dropped so the rejected option stays
> legible: it delivers the same page 1, and it pays for it by making page 1 a fixed-height section
> inside a document whose whole layout is flow — a structural constraint, against A's cosmetic one.
> A delivers every clause of §7.1 except "no head on page 1", which the spec never said: it said a
> full masthead on page 1, and A has one.
>
> ---
>
> **BUILT 2026-09-24. Variant A.**
>
> | piece | where it lives now | appears on |
> |---|---|---|
> | masthead | document body, first in the flow (`macros.report_masthead`) | page 1 |
> | running head | PDFShift `header`, `start_at` 1 | every page |
> | agent footer | PDFShift `footer`, `start_at` 1 | every page |
>
> Both `start_at` values are 1 and `test_page_architecture.py` fails if either moves — the change
> that breaks this is silent everywhere else, because PDFShift returns 200 and takes the page-1
> footer away without saying so.
>
> **The reservations now equal what their documents paint**, which is the other half of D-103:
>
> | | before | after |
> |---|---|---|
> | top | 1.3in reserved / 1.165in painted, + 0.1in margin | **0.44in / 0.417in**, no margin |
> | bottom | 0.9in / 0.781in, + 0.1in margin | **0.89in / 0.885in**, no margin |
> | total reserved | 2.4in of 11in (21.8%) | **1.33in (12.1%)** |
>
> Both PDFShift margins are 0 and the breathing room moved *inside* the header and footer
> documents. It has to: a CSS `padding-top` applies once at the start of the flow, not after each
> page break, so continuation pages would sit flush against the band.
>
> **Measured outcome. Continuation pages gain; page 1 pays for the masthead as content.**
>
> | report type | pages before → after | continuation rows | page 1 with narrative |
> |---|---|---|---|
> | `closed` · `inventory` | 6 → **5** | 25 → **29** | 12 → 11 |
> | `new_listings` | 18 → **16** | 7 → **8** | 3 → 3 |
> | gallery types | unchanged | 9 → 9 | 6 → 6 |
> | `market_snapshot` | 2 → 2 | — | 3 → **0** |
> | `price_bands` | 2 → 2 | — | 3 → 3 |
>
> `market_snapshot`'s 0 is quantisation rather than a bug: its cards are a row of three that moves
> as a unit, and page 1 no longer fits the row once the masthead, hero stat and narrative box are
> on it. The report is still two pages and every listing is on page 2. Whether that is the right
> page 1 is a design question, and it belongs with D-102's rather than being settled here.
>
> **One piece of residue, stated rather than hidden.** On page 1 the running head says
> "Closed Sales — Irvine · 117 CLOSED SALES" and the masthead immediately below says it again. The
> band and the masthead share `header_bg` so they read as one block rather than two, and the
> duplication is small — but it is duplication, and it is the price of A. Cheapest fix if it grates:
> make the running head carry the brand rather than the report title. That is a content decision,
> not a structural one.
>
> §7.2's pinned page-1 capacities were re-measured against this architecture and re-recorded in
> `test_narrative_box.py::PAGE_1_CAPACITY`. The old numbers are not comparable to the new ones and
> the entry says so.

**7.2 Pagination** — 26 table rows per page · 9 gallery cards in 3×3 · 70% minimum fill · never
orphan fewer than four rows · truncation stated in a line beneath the list.

> **Discrepancy to reconcile before this lands.** v1 states table pages "carry five rows" today.
> The `closed.pdf` render reviewed carries **13, then 25, then 12**. Either v1 was written against
> a different render, or two builds are in play — which is exactly the Group A / Group B problem
> in §02. Confirm which build the pagination targets are set against.

> ### Correction: a single rows-per-page number cannot be a target for page 1
>
> *2026-09-24, from measuring it.* The targets above read as constants — 26 rows, 9 cards, 70%
> fill — applied uniformly to every page. **Page 1 cannot hold a constant**, and the reason is not
> a layout detail that tuning fixes.
>
> Page 1 carries the hero stat, the section header and the **AI narrative**, and the narrative is
> model-generated prose of no fixed length. Measured: shortening it by one sentence (~48
> characters) moves `closed` from **13 rows on page 1 to 14**, and `new_listings` from 3 to 4.
> Continuation pages do not move at all — a stable 25 and 7 respectively. Same build, same
> listings, same everything else; one sentence of copy.
>
> So "26 table rows per page" is two different claims wearing one number, and only one of them can
> be a guarantee:
>
> - **Continuation pages take a measured target.** They hold a fixed box with fixed-height rows,
>   and 25 is what they hold today against a target of 26. That is a real number to tune toward.
> - **Page 1 takes a computed budget, not a target.** What fits is the box minus whatever the
>   narrative occupies, and that is knowable only at render time. Writing 26 against it does not
>   make it true; it makes the spec unfalsifiable, because any render can be said to have missed.
>
> The same split applies to **70% minimum fill**: a floor is meetable on continuation pages and is
> not a property page 1 controls, since the copy above the table is not the layout's to size.
>
> **Three ways out, and this is a design decision rather than a measurement.** Give the narrative a
> fixed height and clip or scroll the overflow; move the narrative off page 1 so page 1 becomes a
> continuation page like the others; or state the spec as it actually works — a measured
> continuation target plus a page-1 budget computed from the copy. The third is the honest one and
> costs the least, but it means the spec stops containing a single number, and whoever writes
> §7.1's page architecture should know that before they start.
>
> **Why this is filed rather than edited into the sentence above.** The original wording is the
> evidence for how the target was arrived at — from a render, without noticing that the render's
> first page was a function of its copy. Whoever writes Workstream E's equivalent will be reading
> a PDF too, and will get the same answer the same way.
>
> ---
>
> **RESOLVED 2026-09-24 — Jerry's call: cap the narrative's height.** Of the three, the only one
> that keeps the page architecture predictable without losing anything. Moving the narrative off
> page 1 costs the thing that makes these reports read as written rather than generated; speccing
> page 1 as variable makes every later layout decision inherit an unknown.
>
> **The box is four lines, and four is measured rather than picked.**
>
> | narrative | renders as |
> |---|---|
> | two sentences | 3 lines |
> | three sentences | 4 lines |
> | 150 tokens — `max_tokens`, the hard API ceiling | 8 lines |
>
> Eight lines is the box nothing could ever overflow, and it was tried and rejected **on the
> render**: `market_snapshot`'s page 1 held zero listings and the report went from two pages to
> three, while `closed` fell from 13 rows to 9. A box sized for copy nobody writes costs every
> report four blank lines. Four lines is the measured height of three sentences, which is what the
> prompt asks for in those words.
>
> **What it costs, against the identical render with the height released:**
>
> | report type | 2 sentences | 3 sentences | 150 tokens | **fixed** |
> |---|---|---|---|---|
> | `closed` · `inventory` | 13 | 12 | 9 | **12** |
> | `market_snapshot` | 3 | 3 | 0 *(3 pages)* | **3** |
> | `price_bands` | 4 | 3 | 3 | **3** |
> | `new_listings` | 3 | 3 | 2 | **3** |
> | gallery types | 6 | 6 | 3 | **6** |
>
> A two-sentence narrative gives up one row; a three-sentence one gives up nothing; the worst case
> that used to cost four rows and a whole extra page cannot happen. Page counts are unchanged from
> the baseline for all eight types.
>
> **The box does not clip, so generation enforces the budget.** There is no `overflow: hidden`
> anywhere near it. `NARRATIVE_MAX_CHARS = 380` (four lines at ~97 characters a line, measured by
> bisecting rendered height against a long-word corpus so real prose has margin) drops an
> over-budget narrative and logs it, as does a `finish_reason == "length"` response — see
> **D-104**, which is a real defect this turned up: the worker read `finish_reason` nowhere, so a
> sentence the API had cut off shipped in a customer's PDF.
>
> **Page-1 capacity is now pinned per report type**, the way continuation pages are, in
> `test_narrative_box.py::PAGE_1_CAPACITY` — two deterministic states, with a narrative and
> without, since a report with no narrative renders no box.
>
> **On the precedent.** The property report's Market Trends page was cited as the model to match —
> a fixed-height narrative block that reads well. It does read well, but not for that reason:
> `.mt-condition-desc` has **no height constraint at all** (`font-size:10px; line-height:1.6;
> margin:0`), and no template in this repository fixes the height of any text block. What makes it
> stable is that its copy is generated by `_classify_market_condition` — four template strings with
> numbers interpolated, bounded by construction. Which is the same principle arrived at from the
> other end: **bound the copy, not the container.** The box here is the belt; the budget is the
> braces, and it is the braces doing the work.

**7.3 Charts** — there is currently no chart in any of the 32 pages. Single-series only in v1.
Marks in `primary_ink`, never raw primary. Direct-label the endpoint and the largest bar, never
every point.

> ### Built and measured, 2026-09-24 — the first chart, and what it costs
>
> `market_snapshot`'s twelve-month median closed price, as inline SVG in the document body (no
> script, no external request, nothing for PDFShift to fetch). Built to §7.3's rules and to the
> mark specs: 2px line with round joins, endpoint marker r=4.5 with a 2px surface ring, hairline
> **solid** gridlines one step off the surface, labels on the endpoint and the extreme only, no
> legend (one series — the heading names it), axis ticks and value labels in text grays rather than
> the series colour. Mark colour is `primary_ink`, and this page's surface is white, so that
> token's "clears 4.5:1 on white" guarantee holds here exactly rather than approximately.
>
> No hover layer, which is the one deliberate departure from how this chart would be built for a
> screen: there is no pointer in a PDF. Nothing is gated behind one either — the axis carries the
> scale, two direct labels carry the values that matter, and a note states the sample.
>
> **The data costs two requests, not thirteen, and decision 01 does not cover it.** Decision 01
> priced a twelve-month **count** series at 13 requests by differencing cumulative `minclosedate`
> counts. A **median** cannot be differenced out of counts at any price — it needs the prices. One
> `minclosedate = today − 365` fetch returns closed rows carrying `close_date` and `close_price`
> already, and twelve medians fall out of bucketing them client-side: **two requests at
> `page_max = 500`**, cheaper than the count series rather than dearer. The ceiling is
> `SIMPLYRETS_MAX_RESULTS` (1000): past that the fetch truncates, and a median over a truncated,
> order-dependent subset is a wrong number that looks right, so the series is refused rather than
> drawn (D-078's rule). Months with fewer than three closings are a **gap in the line, not a zero** —
> a zero would draw a crash that did not happen.
>
> **What it costs in page space — measured twice, and the first answer is void.**
>
> Under the OLD architecture the chart took page 1's entire listing set and added a page (2 → 3,
> `[3, 6]` → `[0, 6, 3]`). That was measured before §7.1 variant A moved the masthead into the
> body, and it is recorded here only because the reversal is the point: **re-measured under variant
> A, the chart is free.**
>
> | | pages | listings per page |
> |---|---|---|
> | `market_snapshot` without the chart | 2 | 0, 9 |
> | `market_snapshot` with the chart | **2** | **0, 9** |
>
> Nothing moves, because page 1 already cannot fit a row of cards and the chart lands in space that
> was going to waste. **This is what "do not settle placement on numbers measured under the old
> architecture" meant in practice** — the same chart, the same fixture, opposite answers.
>
> **The page-1 budget, which is what makes the free lunch conditional:**
>
> | page 1 of `market_snapshot` | | |
> |---|---|---|
> | masthead | 1.39in | 14% |
> | hero stat | 1.14in | 12% |
> | narrative box | 1.42in | 15% |
> | stats bar | 2.42in | 25% |
> | section heading + note | 0.78in | 8% |
> | **before a single listing** | **7.15in** | **74%** |
> | free | 2.52in | |
> | a row of three cards | 2.77in | **short by 0.25in** |
>
> So the chart is free *while* page 1 is 0.25in short of a card row. Recover that 0.25in — from
> 3.56in of metric blocks carrying six numbers — and a row of three listings comes back, and the
> chart stops being free. **Those are one decision, not two**, and it is the decision D-102 is
> already waiting on.

**Effort: L.** Blocked by A and by open decision 01.

---

> ### Measured, 2026-09-24 — what this surface actually does before anything changes
>
> Everything below is produced by rendering, not by reading. The instrument is
> `scripts/measure_market_pagination.py` (Chromium's own paginator, Letter, PDFShift's
> reservations) and `apps/worker/tests/test_market_layout_map.py` (a hook on
> `jinja2.runtime.Macro.__call__`). The Workstream C rule applies here and is why: the
> equivalent map for the email surface was written from reading the builders and **seven of
> its eight entries were wrong.**
>
> **There is one PDF path, and it is not the one §07's neighbours describe.** All three
> `render_pdf` call sites in the worker pass `html_content`, so `MarketReportBuilder` renders
> every market-report PDF and the `/print/{runId}` route is never reached by the renderer.
> It is still reached by people — see **D-101**, which is this surface's own Group A / Group B.
>
> **Layouts, recorded from the render.** Five layouts, not the four the builder's docstring
> claimed (it filed `price_bands` under "Analytics"; it has its own `pricebands_layout`). The
> docstring is gone rather than corrected — a second copy of a mapping is a second thing to keep
> right, and this one was not kept right.
>
> | layout | report types |
> |---|---|
> | `gallery_layout` | `new_listings_gallery` · `featured_listings` · `open_houses` |
> | `market_narrative_layout` | `market_snapshot` |
> | `closed_inventory_layout` | `closed` · `inventory` |
> | `pricebands_layout` | `price_bands` |
> | `analytics_layout` | `new_listings` |
>
> **Pagination, measured on 120 listings.** This settles **decision 11**.
>
> | report type | pages | listings per page |
> |---|---|---|
> | `closed` · `inventory` | 6 | 12, 25, 25, 25, 25, 8 |
> | `new_listings` | 18 | 3, then 7 |
> | `new_listings_gallery` | 14 | 6, then 9, last 6 |
> | `open_houses` | 12 | 6, then 9, last 4 |
> | `market_snapshot` | 2 | 3, 6 |
> | `price_bands` | 2 | 3, 5 |
> | `featured_listings` | 2 | 6, 6 |
>
> Page-1 figures are as of the fixed narrative box (§7.2's correction below, resolved
> 2026-09-24). Before it, page 1 moved with the copy — `closed` read 13 here with a two-line
> narrative and 9 with a full-length one. Page counts are the same either way.
>
> **Decision 11's answer: neither build produces five rows.** The reviewed `closed.pdf` carrying
> 13 / 25 / 12 is the production build — this harness reproduces 13 then 25 from it, which is
> also the evidence that the emulation is faithful. The legacy `/print` build hard-codes
> **fifteen** (`ROWS_PER_PAGE = 15`, three call sites in `apps/web/lib/templates.ts`). v1's
> "five rows" matches neither, and no source for it survives in the code.
>
> **§7.2's targets are set against a page-1 capacity that is not fixed.** Shortening the AI
> narrative by one sentence (~48 characters) moves `closed` from 13 rows on page 1 to 14 and
> `new_listings` from 3 to 4; continuation pages do not move. The narrative is model-generated
> prose of no fixed length, so "26 rows per page" and "70% minimum fill" cannot both be
> guarantees about page 1 unless the copy above the table is given a fixed height. Continuation
> pages are stable and can carry a real target.
>
> **§7.1's page architecture is not what ships, and the obvious way to build it may be
> unavailable.** The same masthead repeats at full size on every page — 1.165in measured,
> against §7.1's ~150pt for page 1 and ~38pt after — and 2.4in of every 11in page is reserved
> for 1.946in of paint. Moving the running head to `start_at: 2` also moves the **footer** off
> page 1 if `tasks.py`'s recorded PDFShift constraint holds. That constraint is a code comment
> and has not been verified; verify it before designing around it. **D-103.**
>
> **Three "1-page" report types render two pages.** `market_snapshot`, `price_bands` and
> `featured_listings` are all documented as one-page snapshots in `PDF_CONFIG`'s own comment and
> all spill. **D-102.**
>
> **What did not need filing.** `more_listings_callout` is invoked on every render and can never
> emit, because every `PDF_CONFIG` entry has `more_template: None` — deliberately, since the
> "+ N more, contact me" copy was removed as dishonest. A test records that the path is inert so
> that restoring a template is a decision someone makes on purpose.

---


### Rate-limit headroom for §7.3's trend line — settled 2026-09-23

Decision 01's answer is **13 requests per 12-month trend**. Whether that is affordable is a
separate question, and it is now calculated rather than assumed. Every number below is either read
from the code or produced by running the real `RateLimiter` against a virtual clock.

**The limiter, as configured.** `RateLimiter(rpm=60, burst=10)`, module-level in
`vendors/simplyrets.py`. Its cap is `max(self.rpm, self.burst)` — **so `burst` is inert**: 60 always
wins, and the "+ burst" in its own docstring describes an allowance the arithmetic cannot reach.
Not a defect (the effective limit is the stricter one) but the parameter is decoration.

**Does a twelve-report batch exceed the bucket?** Yes, and it waits rather than failing. Taking a
trend-bearing report at ~17 requests (existing fetches plus 13 buckets):

| back-to-back reports in one process | requests | first limiter wait | wall-clock floor |
|---|---|---|---|
| 1 | 17 | none | 17s |
| 3 | 51 | none | 51s |
| **4** | **68** | **60s** | 68s |
| 12 | 204 | 60s | **~3.4 min** |

So three reports pass freely and the fourth pays. A twelve-report batch cannot finish faster than
about 3.4 minutes however it is scheduled, because 204 requests at 60/min is a floor.

**Does exceeding it mean waiting, or a failed report?** Both, on different layers, and the
distinction matters:

- **The client limiter waits.** `acquire()` calls `time.sleep()`; it never raises. A single report
  arriving at a full window waits at most 60s, which against `task_time_limit = 300` and a
  production p99 render of 41s is comfortable. **No report fails from local throttling.**
- **The server can still 429**, and that path does fail. `_request_with_retries` retries a 429 four
  times with backoff 2 → 4 → 8 → 16s, then makes **one final unguarded attempt** whose
  `raise_for_status()` raises. A sustained 429 fails the report after ~30s.

**And that is the real exposure, which is about concurrency, not arithmetic.** `_limiter` is a
module-level object, so under Celery's prefork pool **each worker process gets its own 60/min** —
and no `--concurrency` is set anywhere, so the pool is one process per CPU. The vendor account
limit is 60 rpm (the limiter's own docstring cites it). **With N busy processes the aggregate is
N × 60 against an account ceiling of 60.** The local limiter cannot see that, so it throttles
nothing and the 429s arrive from the far side.

> **This is already true today** and trend charts do not create it — they multiply it, by roughly
> quadrupling requests per report. Worth knowing before §7.3 is written, and worth knowing
> independently of §7.3.

**The cache does NOT absorb the repeats, and that is the actionable finding.** `cache_set("report",
{"type": report_type, "params": params}, …, ttl_s=900)` — **`report_type` is part of the key.** So
twelve report types for one city are twelve misses, and a naive implementation would fetch **the
same thirteen monthly bucket counts twelve times** — 156 requests for 13 distinct answers.

The buckets are a property of *(city, month)* and nothing else. Cached in their own namespace they
cost **13 requests per city per window, shared across every report type**, which takes the batch
from 204 requests to about 60. The existing `cache.get/set` already supports this — a different
namespace is all it needs.

> **One trap if you do that: `cache._key` hashes `json.dumps(payload)` with no `sort_keys`.**
> Measured: `{"city": …, "month": …}` and `{"month": …, "city": …}` produce **different keys**, so
> two logically identical lookups miss each other silently. Harmless today because the report
> payload is constructed in one place; a bucket payload built at several call sites is exactly the
> shape that trips it. Filed as **D-095**.

**Verdict for the chart spec: affordable, with one condition.** Bucket counts must be cached on
*(city, month)* rather than recomputed per report. Without that, a twelve-report batch triples its
vendor traffic for no new information and pushes a per-process limit that is already being
multiplied by concurrency.

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
| 01 | ~~**Does the pipeline hold historical data?**~~ **NARROWED 2026-09-23 — see the note below §12.** History is fetchable; the open question is only whether twelve monthly buckets are affordable | Workstream D scope | Eng |
| 02 | **Drop the secondary brand color?** Templates consume two; the system needs one. Two means deriving and validating a second set and checking every pairing against each other, not just against white. **Recommend one** | Workstream A | Product |
| 03 | **Who writes the commentary, and from what?** If copy comes from a separate query than the rendered metrics, that coupling is the actual fix for B1/B8. **Note:** `generate_insight()` takes no `account_id` and is gated only by a process-wide `AI_INSIGHTS_ENABLED` whose production value is **still unknown** — the commentary may not be running at all | Data contract | Eng |
| 04 | **Does "Powered by TrendyReports" stay in a white-label send?** Sits in the footer under the affiliate's own branding | Email footer | Product |
| 05 | **Are MLS photos licensed for redistribution in a forwardable PDF?** Emails hotlink; the PDF embeds. Different posture | Phase 4 | Compliance |
| 06 | **Is logo upload guaranteed at onboarding?** If mandatory, B2 is an onboarding validation gap as well as a rendering one | B2 | Product |
| **07** | **Which property render group is production — A or B?** Three different subject valuations exist for one address. Every Workstream E theme finding depends on the answer | **Workstream E** | Eng |
| **08** | **Is the comp date window broken, or did it correctly find nothing recent?** Determines whether E2 is a query fix or a copy fix | **E2** | Eng |
| **09** | **What is the registered business postal address?** Required for the email footer (B20) and the marketing site's legal pages (G3 in the marketing plan). **One answer closes both** | B20, G3 | Jerry |
| **10** | **B10 attribution.** Putting a named agent's byline on LLM-generated commentary that feeds a pricing decision, with no disclosure, is a liability question rather than a design one — especially while the figures are still inconsistent. **Recommend:** attribute as a prepared summary, retain a "prepared with market data from SimplyRETS" line | B10 | Product / legal |
| ~~**11**~~ | ~~**Pagination baseline.**~~ **ANSWERED 2026-09-24 by measurement — see the block under §07.** The reviewed 13/25/12 render is the production build (`MarketReportBuilder`), reproduced by `scripts/measure_market_pagination.py`. The legacy `/print` build is a fixed 15. **Five matches neither**, and nothing in the code produces it. The Group A/B split is real but sits elsewhere: the PDF and the customer-facing "view in browser" link render different builds of the same report — **D-101** | Workstream D | ~~Eng~~ |

---


### Note on decision 01 — narrowed, 2026-09-23

**The question as written is half answered by work done since.** D-074 established that
`minclosedate` filters (confirmed against the production feed), and months-of-supply already
computes a 90-day sales rate from real closings. Historical closed sales are fetchable by close
date. *"Does the pipeline hold historical data"* is no longer the question.

**What is genuinely open is the cost of twelve monthly buckets**, which is what §7.3's trend line
needs — and that turns on one measurable thing: whether there is an upper bound on close date.

| if | then monthly buckets cost |
|---|---|
| `maxclosedate` filters | **12 requests** — one `count=true` per month, `limit=1` each |
| it does not | **13 requests** — difference cumulative `minclosedate` counts: `bucket(N) = count(≥ start N) − count(≥ start N+1)` |
| neither works | every row for 12 months fetched and bucketed client-side, **and that cost scales with the market** |

**Measured on the demo feed: `maxclosedate` is accepted and ignored.** `1990-01-01`, `2000-01-01`
and the nonsense value `notadate` all returned the full 13, exactly like the deliberately
misspelled `maxclosedatex`. `minclosedate` filters correctly (`2005-01-01` → 4 of 13), and
differencing reproduced the true per-period histogram exactly. So the demo answer is **13
requests, independent of market size** — which would make the trend line affordable.

That is the demo answer, and D-084's whole lesson is that a filter's behaviour is a property of the
feed. **`scripts/probe_simplyrets_behaviour.py` section 6 re-runs it against production** and
prints a `DECISION-01` verdict in one of those three shapes. The demo feed cannot settle it on its
own terms either way: its thirteen closed sales closed between 1990 and 2013, so a 12-month window
returns nothing there.

> **One thing to carry into any work on this: `closeDate` lives at `row["sales"]["closeDate"]`, not
> at the top level.** Reading it top-level returns `None` for every row and looks exactly like a
> feed with no close dates — which is how the first run of this check nearly reported the wrong
> answer. `extract.py:26` reads the correct path.

---

### Correction: 13 requests prices the COUNT series, and §7.3's first chart is not one

*2026-09-24, from building it.* Everything above answers "what does a twelve-month trend cost" with
**13 requests**, by differencing cumulative `minclosedate` counts. That is right, and it is the
price of **one particular series**: how many homes sold each month. The correction is that it was
then carried as the price of §7.3's trend line generally, and §7.3's first chart is a **median**.

**A median cannot be differenced out of counts at any price.** `count=true` returns a total, and no
arithmetic over totals recovers the middle of a distribution. The 13-request technique does not get
cheaper or dearer for a median — it does not apply.

**What a median costs instead: two requests, not thirteen.** One
`minclosedate = today − 365` query returns the closed rows themselves, and `extract.py` already puts
`close_date` and `close_price` on each one. Twelve medians then fall out of bucketing those rows
client-side, at no further vendor cost. At `page_max = 500` that is two requests for up to 1000
closings — **cheaper than the count series, not dearer** — and the same rows yield the monthly
counts for free, so a volume series alongside it costs nothing extra either.

| series | what it needs | requests |
|---|---|---|
| monthly **count** | a total per month | 13 (differenced), or 12 if `maxclosedate` ever filters |
| monthly **median** | the prices | **2** — one 365-day fetch, bucketed client-side |
| both together | the prices | **2** — the counts come out of the same rows |

**Where it does get expensive is the row ceiling, and that is a different risk.**
`SIMPLYRETS_MAX_RESULTS` is 1000. A market with more closings than that in twelve months returns a
truncated set, and a median over a truncated, order-dependent subset is a wrong number that looks
like a right one. `compute/median_trend.py` refuses the series rather than drawing it, which is
D-078's rule. **The cost model for a median is therefore two requests with a correctness cliff,
not thirteen requests with a smooth scale** — a different shape of risk from the one decision 01
analysed, and it should be planned as one.

**The original analysis is preserved above rather than edited** because it is correct about the
series it priced, and because the mistake worth remembering is not the arithmetic — it is
generalising a cost from one series to "the trend line".

## 14 · Out of scope

The application UI · replacing the PDF generation engine · deliverability, sending infrastructure
and list management · copy generation quality (this plan changes where commentary sits and how it
is attributed, not how it is written) · localisation and RTL · any surface beyond email and PDF.
