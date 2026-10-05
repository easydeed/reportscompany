# Review — Claude Design's two handoffs

**Reviewed:** `docs/design-claude/design_handoff_property_report/` (at `d474fc2`) and
`docs/design-claude/reports-handoff/design_handoff_market_reports/` (at `709bfff`) ·
**Date:** 2026-10-01

| surface | verdict |
|---|---|
| **property report** | **a correction list.** The design holds; the implementation notes point at files that do not render |
| **market reports** | **a correction list with one architectural reversal.** Same, plus they deleted a running head that shipped four days ago |

**Both surfaces named a non-rendering template set as their surface**, and the market one is
worse: `apps/web/templates/trendy-*.html` is the path the code itself calls LEGACY. See §8.

Measured where measurable. The design renders — it needed React 18 served locally, which this
container's proxy blocked — and the pixel auditor ran over it. Numbers below are from that run
and from `derive_theme()` over the six golden brands, not from reading the spec.

---

## 0 · What they claim, before anything was checked

`README.md` (166 lines) and `STRUCTURAL_NOTE.md` (52 lines) are a specification, not a mood
board. They claim, in their own words:

* **Three themes survive** — elegant, bold, modern. Classic and teal are removed. The three
  differ **only** in typeface, weight, tracking, case and corner radius. "No theme carries a hue
  of its own — the gold, coral, sky and teal literals are gone, which removes 5 of the 6 values
  behind 132/213 contrast failures at the source."
* **Six pages, down from nine** — cover · your home · comparable sales · what the comps support ·
  your market (conditional) · next steps. The `contents` and `overview` pages are deleted; the
  summary becomes a bounded panel on the cover.
* **Variant A page architecture** — a 40px running head and the footer are the PDFShift
  header/footer, **both starting at page 1**; the brand masthead is body content.
* **Page 1 is bounded** — title box fixed at 78px with a five-step size ladder by character
  count and an ellipsis backstop; narrative panel `max-height: 81px` over a ~380-char generation
  cap; hero plate fixed; stats row four fixed cells. "Nothing else on page 1 grows with data."
* **No text over photography anywhere**, no gradients; plates on photos are solid white.
* **Every colour is a `derive_theme()` token or a fixed neutral.**
* **One recorded exception**, stated up front: the cover masthead is `#FFFFFF` on `primary` by
  owner decision of Oct 1, overriding `on_primary`; "on teal `#0D9488` this measures 3.74:1,
  amber and lime lower"; they ask for an auditor exclusion scoped to the cover band.
* **The 19 orphan fields stay as dashes** plus a "Not on record" strip — flagged as an owner
  choice, with the instruction for switching to removal.
* Their own self-check table says every constraint **"Holds"** except that exception.

They also claim things about the market reports, which are **not in the repo** — see §6.

---

## 1 · Which tree did they read? *(answered first, because it decides the rest)*

**They read the live Python and the dead templates.** Both, and it is visible in the split
between what they got right and what they got stale.

**Live — the Python, the tests and the defect list.** `compute_color_roles`, `_THEME_DARK_BG`,
`property_builder.py`, `tests/golden/themes.json`, `timeline_metrics.avg_marketing_days`,
`dom_distribution.under_30`, `price_cut_stats.rate`, `requester_name` on the consumer path
(shipped yesterday), `test_no_owner_identity_in_property_report.py` described with its
post-D-157 behaviour, and citations to D-097, D-114, D-122, D-125, D-126, D-127. None of that is
guessable from the dead tree.

**Dead — every template artefact they name.**

| they say | where it actually is |
|---|---|
| "Keep the font-trigger `<div>` in `base.jinja2`" | `_base/base.jinja2:1776, 2135` — **dead**. No live template has one |
| "the current `data_table` macro hides them" | `_base/_macros.jinja2:135` — **dead** |
| "`comp_grid` cap 4 → 6 (current macro caps at 4)" | `_base/_macros.jinja2:338`, called only from `_base/base.jinja2:2022` — **dead** |
| `comp_confidence_grade` "pill on the comps page header" | `_macros.jinja2:315,338` — **dead**. See §3 |

**This does not invalidate the design.** They did not inherit the dead tree's layout — they
replaced the page architecture outright, and the architecture they chose is the one the live
code supports. What they inherited is a **list of implementation instructions pointing at files
that do not render**: there is no `base.jinja2` to keep a div in, no `data_table` macro to stop
hiding rows, no `comp_grid` cap to raise from 4.

It is also the first measured instance of D-131's predicted cost. The warning went into the
handover document the same day they were working; it did not reach them in time.

**One stale fact that came from the live side, not the dead one:** "removes 5 of the 6 values
behind **132**/213". 132 was wrong in our defect list when they read it — the role table had
been assembled by eye. The correct figure is **146 of 213**, and it strengthens their case
rather than weakening it.

---

## 2 · What would break silently

| check | verdict |
|---|---|
| text on a gradient | **none.** Zero gradients in the design. The one in `support.js` is the viewer's loading skeleton |
| text on a photograph | **none.** Plates are solid white with `#14161A`; the cover photo carries no text |
| `background-clip: text` | **none.** The only `color:transparent` is viewer chrome |
| page-1 header/footer split | **correct, and deliberately so.** Variant A — both start at page 1, masthead in the body. That is exactly what D-103's probe established as the only safe option after PDFShift coerced mismatched `start_at` values to the later one and returned HTTP 200 |
| page numbers / contents literal | **derived.** `Page {{ pg.n }} of {{ pageCount }}`, N computed after the conditional drop. The contents page is deleted, which removes a derived-number surface rather than adding one |
| page-1 growth | **bounded, and the bounds are stated.** Title box 78px + a five-step ladder + ellipsis; narrative `max-height: 81px; overflow: hidden` on top of a generation cap |

**Nothing in category 1 is wrong.** This is the part of the brief they most clearly absorbed.

**One caveat they did not state:** `overflow: hidden` on the narrative panel truncates
mid-sentence with no visual signal. A four-line cap on AI-generated prose will sometimes cut a
sentence in half, and the reader cannot tell. The generation cap makes it rare, not impossible.

---

## 3 · Contrast, measured

`measure_contrast_by_pixel.py` over the rendered design, one theme × one brand (teal
`#0d9488`, the Tweaks default): **361 runs, 49 failing, 0 unmeasurable.** Six pairings.

| ratio | pairing | needs | runs | what | brand-dependent? |
|---|---|---|---|---|---|
| **3.29** | `#8a8e95` on white | 4.5 | **28** | comp-card third line: "Lot", "6,900 sq ft", "No HOA", separators | **no — every theme, every brand** |
| **1.92** | `#b9bbc1` on white | 4.5 | 6 | the dash itself | **no** |
| **3.74** | white on `#0d9488` | 4.5 | 7 | cover band *small* text | yes |
| **3.95** | `#dc2626` on `#fee2e2` | 4.5 | 5 | "Sold" pill | **no** |
| **2.86** | `#d97706` on `#fef3c7` | 4.5 | 1 | "Pending" pill | **no** |
| **4.33** | `#0b8378` on `#f0f9f8` | 4.5 | 2 | `primary_ink` on `tint` | yes |

**Their self-check says "Holds, except the recorded masthead exception." Five of these six are
not that exception**, and 42 of the 49 runs are outside it.

### 3a · `#8A8E95` — the README states a figure that is wrong

> *"Neutrals: `#14161A`, `#2A2D33`, `#5E636B`, `#8A8E95` (footer/disclaimer, ≥4.5 on white)"*

`#8A8E95` on white is **3.29:1**. `#5E636B` is the one that clears 4.5 (6.05:1). This is their
most-used failing colour and it is a fixed neutral, so it fails identically on all three themes
and all six brands. 28 runs in a single render.

### 3b · The status pills are declared fixed and all three fail

| | ratio |
|---|---|
| Sold `#dc2626` on `#fee2e2` | **3.95** |
| Pending `#d97706` on `#fef3c7` | **2.86** |
| Active `#059669` on `#d1fae5` | **3.32** |

Declared "semantic and fixed", 10px/700, no exception recorded. Brand-independent.

### 3c · The masthead exception is real, correctly measured, and wider than they scoped it

They are exactly right about the numbers:

| brand | white on `primary` | |
|---|---|---|
| violet `#7c3aed` | 5.70 | ok |
| coastal `#0e7490` | 5.36 | ok |
| demo_title `#dc2626` | 4.83 | ok |
| **luxury_estates `#0d9488`** | **3.74** | fails |
| **amber `#f59e0b`** | **2.15** | fails |
| **lime `#84cc16`** | **1.98** | fails |

**But the exception they ask for is scoped to the wrong thing.** On the cover band, the
*display* text — the 64px street, the 30px stat values — passes at 3.74 because the large-text
threshold is 3.0. What fails is the **small** text on the same band: the report-kind label
(11px), the brand name (18px), the city line (22px/500) and the four 11px stat labels. An
auditor exclusion "scoped to the cover band element" would suppress seven genuine small-text
failures in order to permit a display line that already passes.

**On lime, that small text sits at 1.98:1.** Near our 1.5 invisibility floor, on the first thing
a seller sees.

The remedy they name — *"a darker `primary_dark` fill behind the text, never moving the brand
colour"* — is the right one and should be the rule, not the fallback.

### 3d · `primary_ink` on `tint` fails for two of six brands

demo_title **4.41**, luxury_estates **4.33**. `tint` is the "In short" panel, the confidence
pill, the next-steps cards and the missing-photo tile, so this is a recurring surface, not an
edge.

### 3e · Did the palette move the brand fill?

**No.** Every fill is `primary`; contrast is solved by text and surface. The one exception is
documented and its remedy explicitly forbids moving the brand colour. This constraint holds.

### 3f · Did they distinguish literal / `theme_color` / `derive_theme`?

**Yes, and this is the strongest thing in the handoff.** Their colour-role table maps each of the
six `derive_theme()` tokens to its uses, and the structural note's first move is deleting the
four theme-specific literals (`--gold`, `--coral`, `--sky`, `--teal`) rather than re-picking them
— the fix for the three-literal group in our own analysis, done at the source. The failures that
remain are in the **fixed neutrals and semantics** they added, which is a different list.

*Measurement caveat:* Google Fonts was blocked, so type fell back to system faces. Font sizes are
inline literals, so the WCAG thresholds are unaffected; glyph widths and wrapping are not exact.

---

## 4 · Data reality

### 4a · Four school rows and two location rows have no producer anywhere

> *"Schools (`school_district`, `school_elementary`, `school_middle`, `school_high`) and Location
> (county, neighborhood, census tract) as two more groups on 'Your home'; rows dash when absent
> (the repo hides them — this keeps §3.6 consistent)."*

**The repo does not hide them. The repo does not have them.** There is no `school` anything in
`apps/worker` or `apps/api`. SiteX's `PropertyData` carries 32 fields and none is a school.
`school_district` exists on *market* listings from SimplyRETS; it has never been on the property
path. `neighborhood` likewise, and `census_tract` is already a known orphan.

So the design **adds six permanently-empty rows** to a page whose problem is permanently-empty
rows. The sample render shows all four schools filled with invented names, which is exactly what
makes a reviewer believe the data exists.

### 4b · The confidence pill reads a field the renderer never receives

`comp_confidence_grade` / `comp_confidence_reason` are computed in `apps/api`
(`routes/property.py:893`) and consumed only by the **dead** `comp_grid` macro. Nothing in
`apps/worker` reads either name. The design puts the grade on the comps page header **and** in
the range panel's label ("confidence A, strict match"), so two surfaces depend on a value that
does not reach the renderer.

This is D-113's family — a read with no producer — caught at design time instead of in
production. Either plumb it through the worker or drop both uses.

### 4c · Bathrooms: right instinct, wrong half

They handled the **subject's** bathrooms (cover stats drop a null and backfill with lot size;
`bathsKnown` is a Tweaks toggle). Good.

But D-106 is about the **comps**: `bathrooms` is absent from 301 rows of a real SimplyRETS
market. The comp card's second line is `"{bd} bd · {ba} ba · {sqft} sq ft"` — that renders
`3 bd · — ba · 1,642 sq ft` on **every card, six per page**. The analysis table's Bedrooms row is
fine; there is no Bathrooms row, which is the right call.

### 4d · Comp photos

Handled well — missing photo is a `tint` tile with the neighborhood name in `primary_ink` and
"No photo on file", no grey box and no broken-image glyph. **Nothing in the current build carries
`comp.photo_url`**, so today that treatment is the *only* state that renders, not the fallback.
Worth knowing before it is judged as a rare case.

### 4e · The 19 orphans

They chose **option B (label)** — keep the rows as dashes and add a "Not on record" strip
explaining that a dash means the record is silent. They flag it as an owner choice and state how
to switch to removal, which is the right way to pre-empt a decision.

Two notes. The strip in the sample lists **nine** fields; our orphan list for the decision is
**seventeen**. And §4a adds six more. The sentence "A dash anywhere in this report means the
public record doesn't say, not that the answer is no" is the best piece of copy in the handoff.

### 4f · "None"

The rendered page 2 shows **HOA → "None"**. Their own absence rule says *never "None"*; the spec
says HOA 0 → "No HOA". The reference render contradicts the specification on the one word D-137
is about.

---

## 5 · What they got right

Not a formality — several of these are things we flagged and could not solve.

* **Variant A, correctly reasoned.** They identified the PDFShift `start_at` constraint and put
  the masthead in the body rather than fighting it. D-103's probe cost a credential trip to
  establish; they applied it without being told twice.
* **Deleting the four theme literals rather than re-picking them.** This removes the largest
  group of our contrast failures at the source instead of managing it.
* **Every page-1 growth path bounded, with the bound stated as a number.** Title ladder, 81px
  narrative, fixed hero plate, four fixed cells. Page-1 capacity stays deterministic.
* **A designed missing-photo state** — the gap we had no treatment for at all.
* **The chart has values and an axis** (D-126) and **"PIQ" becomes "Your home"** (D-127).
* **"Each sale"** — one bar row per comparable, on the same page as the range. That is a better
  answer to D-159 than our continuation list: the evidence sits beside the number it supports
  instead of overleaf.
* **The range copy.** *"This is what recent sales of similar homes nearby support. It is a report
  of the market, not an appraisal, and a listing price is a conversation with your agent."*
  That is Jerry's "reporting, not stating" in one sentence.
* **Consumer/agent as three named branches** in one template, with owner identity on the agent
  path only — the D-157 architecture, understood.
* **An honest self-check table** that records an exception against itself rather than omitting
  it. The table is incomplete, but it is the right instrument and it is the reason the gaps in
  §3 are checkable at all.

---

## 6 · Two things outside the review

**~~The market report designs are not in the repo.~~ They are — at
`docs/design-claude/reports-handoff/design_handoff_market_reports/`, committed in `709bfff`,
after this review was started at `d474fc2`.** The claim above was true of the tree I was
reading and is false now. They are reviewed in §8, and the self-check claims the property
handoff makes about them turn out to be checkable and mostly right.

**Six comps, and the build returns up to fifteen.** The comps grid is 3 × 2 and the capacity note
says page 4 holds "6 bars". `COMP_SET_MAX` is 15. Three outcomes and only one is acceptable:
cap the ladder at 6 (a search change nobody decided), show 6 of 15 (D-159 reopened, four days
after it was closed), or let the page grow (their stated rule is "cap at the builder, not the
template"). **This needs deciding before implementation, not during.**

---

## 7 · What the package has to say

The review changes what the handover document is for. It is not a brief to design from — the
design exists and is largely sound. It is the **standard the implementation is measured against**,
and it now needs to carry:

1. **The dead tree, by filename, first.** Written in `CLAUDE_DESIGN_HANDOVER.md` §0 — **which
   is on the unmerged PR #138 and therefore not on `main`.** It did not reach them in time and
   it is the single highest-value paragraph in the document.
2. **The corrected contrast figures** — 146 of 213, not 132 — and the literal / `theme_color` /
   `derive_theme` distinction, which they independently arrived at and which should not be
   rediscovered a third time.
3. **A fixed-neutral contrast table.** Their `#8A8E95` claim was wrong by 1.2 and nothing caught
   it. The package should state the ratio of every neutral it blesses.
4. **The orphan list at full length, including the six they are adding.** Schools and Location
   are not in our list because we do not read them yet; a designer cannot infer that.
5. **`comp_confidence_grade` as an API-only field.** The worker/API boundary is invisible from
   the templates and they walked straight into it.
6. **`COMP_SET_MAX = 15` as a number the layout must survive**, not a detail.
7. **D-106 scoped to comps, not subjects.** They solved the half they could see.

---
---

# 8 · The market reports handoff

`docs/design-claude/reports-handoff/design_handoff_market_reports/` — README (93 lines),
`Report Page.dc.html` (the template, seven kinds via Tweaks), `Report Page Gallery.dc.html`,
`PDF Reports v2.dc.html` (design history), `support.js`.

## 8.0 · What they claim

* **One page template replaces the seven `trendy-*.html` files.** The report kind changes the
  header numbers and the body block; masthead, footer, type, spacing and colour roles are
  identical across all seven.
* **Removed:** the violet→coral gradient bar, the red "PDF" badge, the four-chip metric ribbon,
  the generic explainer paragraphs. Each report leads with one number in the affiliate's colour.
* **"No running head.** The brand band on page 1 and the strip on pages 2+ are both body
  content. The only PDFShift element is the footer, starting at page 1."
* **Two brand inputs only** — `primary` and `accent`. White on `primary` for all band text,
  with the property report's `on_primary` rule named as the remedy for light affiliates.
* **Headline sentences are template-filled from data, never free-written**, with stated
  thresholds, and hidden entirely under 10 sales.
* **13 rows on page 1, 26 on continuation, `P = ceil((N − 13) / 26) + 1`.**
* Same neutral palette as the property handoff, same missing-photo treatment, same absence
  rules — with one addition: *"Counts of zero in the band → still render the number. Zero is
  data, not absence."*

## 8.1 · Which tree did they read? *(the answer is worse here)*

> **"Surface: `apps/web/templates/trendy-*.html` + the worker PDF builder"**

`apps/web/templates/trendy-*.html` is the **legacy path**, and the repository says so in its own
comments rather than by inference:

```python
# tasks.py:1677
# Always render via the new MarketReportBuilder. The legacy
# /print/{runId} frontend path produced unbranded PDFs missing the
# Outfit font, themed header, and AI narrative — so we never fall
# back to it.
```

```python
# pdf_engine.py:75
# `{print_base}/print/{run_id}` renders the LEGACY build
# (apps/web/app/print/[runId]/page.tsx + the trendy-*.html templates),
# which is a different document from the one this function just produced:
# different pagination, no themed header, no AI narrative.
```

The live market PDF comes from `MarketReportBuilder` →
`apps/worker/src/worker/templates/market/market.jinja2` + `_base/` (2,479 lines). The legacy
renderer is still *reachable* in `pdf_engine.render_pdf_playwright` when `html_content` is
`None`, and the market task never passes `None`.

**Two of the three things they say they removed exist only in the legacy files.** The
violet→coral gradient (`--pct-blue: #7C3AED`, `--pct-accent: #F26B2B`) and the red "PDF" badge
are in all seven `trendy-*.html` and in **none** of the live market templates. They were never
in a customer's PDF.

**And one thing they removed is live, recent, and deliberate.** See §8.2.

## 8.2 · The reversal: "No running head"

The live market template has a running head. It is the PDFShift `header`, on every page
including page 1, with the masthead moved into the body — **variant A, built four days ago
specifically to satisfy §7.1 inside PDFShift's `start_at` constraint.** Its own header comment
says so at length, including the probe result.

Design's market handoff deletes it: *"No running head. … The only PDFShift element is the
footer."*

**This is the same constraint they got right on the property report.** There, they chose variant
A explicitly and cited §3.4. Here they removed the thing variant A exists to provide. The
difference maps exactly onto which code they read: the property handoff cites live Python, the
market handoff cites legacy templates — and the legacy templates have no running head, because
the running head is the thing Workstream D added.

Their market README even states the constraint correctly — *"(Same constraint as the property
report: header/footer `start_at` must match.)"* — and then draws the opposite conclusion from
it. Matching `start_at` values is an argument for putting the masthead in the body. It is not an
argument against having a running head.

**Removing it is a legitimate design choice, but it must be made knowingly**, and it reverses a
decision that cost a credential trip and a four-render probe to establish.

## 8.3 · Contrast, measured

`Report Page.dc.html` renders standalone once React 18 is served locally.
`Report Page Gallery.dc.html` renders its seven frames empty — the embed mechanism does not
work outside their environment — so **this is one report type (snapshot) on one brand**, not
seven.

**57 runs, 4 failing, 0 unmeasurable.**

| ratio | pairing | runs | size | what |
|---|---|---|---|---|
| 3.29 | `#8a8e95` on white | 1 | 9px | the "Source: CRMLS …" line |
| 3.74 | white on `#0d9488` | 3 | 11.5px | the counts inside the price-tier bars |

Both are **the same two mistakes as the property surface** — see §9.

**What I cannot report:** the other six report types, and any brand but the sample. The gallery
is the artefact that would have given both and it does not render here.

**Did the palette move the brand fill?** No. Fills are `primary` and `accent`; status and delta
colour is "text only, never fills", stated explicitly. The constraint holds.

## 8.3a · The market surface's CURRENT baseline — measured today, first time since C and D

There was no current number for this surface. D-129's 213 is the property report; the
2026-09-29 market audit predates Workstreams C and D, which rewrote it. So it was measured
before judging their output, over the gate's own 60-document market corpus (10 report types ×
6 brands), with the pixel instrument:

| | |
|---|---|
| runs measured | **5,058** |
| failing | **66** |
| combinations | **6** |
| declined | **0** |
| worst | **2.66:1** |

**All sixty-six are status or tier badges.** Coloured text on a tinted chip of the same hue.
Not one brand-colour failure. Not one neutral failure. Nothing else on the surface fails at all.

| ratio | pairing | runs | what |
|---|---|---|---|
| 2.66 | `#ca8a04` on `#faf3e5` | 18 | "Pending" |
| 2.85 | `#d97706` on `#fef1db` | 6 | tier "High" |
| 2.89 | `#16a34a` on `#def6e7` | 6 | tier "Median" |
| 2.95 | `#16a34a` on `#e7f6ed` | 18 | "Active" |
| 4.12 | `#dc2626` on `#fbe9e9` | 12 | "Closed" |
| 4.35 | `#2563eb` on `#e2ecfe` | 6 | tier "Low" |

**The market surface is in far better shape than the property one** — 1.3% of runs against 9.2%
— and its entire remaining defect is one construct used six ways. Workstreams C and D did that
and nobody had counted it.

### And this is where the two designs cross

Their market README says: **"Status/delta colour: text only, never fills."** That is aimed
squarely at these 66. Does it work?

| badge | on the chip today | on white, their rule | |
|---|---|---|---|
| Closed `#dc2626` | 4.12 | **4.83** | fixed |
| tier Low `#2563eb` | 4.35 | **5.17** | fixed |
| Active `#16a34a` | 2.95 | 3.30 | **still fails** |
| Pending `#ca8a04` | 2.66 | 2.94 | **still fails** |
| tier High `#d97706` | 2.85 | 3.19 | **still fails** |

Removing the tint buys roughly 0.35 and fixes two of six. **The hues themselves are too light
for 4.5 on white**, and the remedy is the one their own colour system already uses for the brand:
a darker *ink* variant for each semantic, not a different surface behind it.

**Meanwhile their property handoff reintroduces the construct this surface is failing on.**
Sold `#dc2626` on `#fee2e2` = 3.95, Pending `#d97706` on `#fef3c7` = 2.86, Active `#059669` on
`#d1fae5` = 3.32 — coloured text on a same-hue tinted chip, declared "semantic and fixed", on a
surface that has no status badges today.

So the one defect the live market surface has is **partly fixed on the surface that has it and
imported onto the surface that does not.** Neither package could see that; both were written
looking at one surface.

## 8.4 · The market architecture, item by item

| live, after Workstreams C and D | their handoff |
|---|---|
| running head in the PDFShift header, every page (D-103 variant A) | **deleted** — §8.2 |
| masthead as body content on page 1 | ✓ same |
| `_TITLE_LADDER = ((27,24),(33,21),(38,18),(43,16))`, min 14px, measured widths, fixed-height box | *"if an area name exceeds ~22 characters at 22px, shrink the label to 18px"* — **two steps, estimated, no stated box height** |
| `.ai-narrative-text` has a **fixed** `height: calc(N * Xem)` — §7.2's decision is that page-1 capacity must not depend on the length of model prose, and a test reads the CSS rule to enforce it | headline sentences are template-filled with thresholds, which bounds the *content* — **no fixed-height box is specified**, so the enforcement surface disappears |
| `PAGE_1_CAPACITY` pinned **per type and per narrative state** — e.g. `closed: 15 without narrative, 11 with`; `inventory: 15 / 11 / 5 with trend` | **"13 rows page 1, 26 on continuation"** — one number for closed and inventory, no narrative variant |
| page numbers derived | ✓ `P = ceil((N − 13) / 26) + 1` |

Three of these need work and none is a redo:

* **The title ladder** is a rule of thumb where the live one is a measurement. Theirs may well be
  right for their type sizes; it has not been measured, and the live ladder's comment is explicit
  that its numbers are fallback-font widths with a margin, i.e. that this is a thing you measure.
* **The narrative box** needs a stated fixed height, or `test_narrative_box.py` has nothing to
  read and page-1 capacity goes back to depending on prose length (D-102's defect).
* **`PAGE_1_CAPACITY` must be re-measured for their layout and keep the per-state split.** 13 is
  not 15 and not 11, and their row heights differ from the live ones, so neither number
  transfers. A single flat capacity is the shape the live numbers exist to replace.

## 8.5 · What they got right on this surface

* **One template, seven kinds** — the live build already dispatches on layout from one
  `market.jinja2`; collapsing the seven legacy files matches where the live code already went.
* **Headline sentences as builder functions returning `null`, with the template rendering a
  plain title on `null`.** That is the right shape for D-108's family: the threshold lives in
  one place and the absence of a headline is a value, not a missing branch.
* **"Counts of zero in the band → still render the number. Zero is data, not absence."** That is
  D-107/D-108 stated as a design rule, unprompted.
* **Deltas under 1% render "flat"**, headlines hidden under 10 sales — both bounded, both stated
  as thresholds rather than judgement.
* **Status and delta colour is text only, never fills** — which is how you keep a semantic colour
  off a brand surface.
* **Page count derived from row count**, and a one-line continuation footer that states
  "Rows a–b of N".
* The missing-photo treatment is the same designed state as the property side, which means it
  exists on both surfaces for the first time.

---

# 9 · What appears on both surfaces

A shared mistake is a different finding from two unrelated ones. Four things appear twice.

### 9.1 · `#8A8E95` is declared "≥4.5 on white" in both READMEs. It is **3.29:1**.

Property: 28 failing runs. Market: the source line. It is a fixed neutral in both palettes, so it
fails on every theme, every brand, every page that uses it. **One wrong number, written down
twice, and nothing in either package would have caught it** — which is the argument for the
package carrying a measured table of every neutral it blesses rather than an adjective.

`#5E636B` is the neutral that clears 4.5, at 6.05:1.

### 9.2 · Small text, white, on a brand fill

Property: the cover band's 11–22px text at 3.74 on teal, 2.15 on amber, **1.98 on lime**.
Market: the 11.5px counts inside the tier bars, 3.74.

Both packages handle the *large* case correctly — the 88–96px numbers pass at the 3.0 threshold
on a dark brand — and both put small text on the same fill without re-checking it against 4.5.
The property handoff at least records an exception; the market one does not.

**The remedy is already written in their own property README** and should be the rule on both:
*"a darker `primary_dark` fill behind the text, never moving the brand colour."*

### 9.2a · The status-badge construct, going both directions at once

The live market surface's **only** remaining contrast defect is coloured text on a same-hue
tinted chip — all 66 of its failures. Their market design removes the chip (fixing two of six,
leaving four, because the hues are too light for white). Their property design **adds the chip**
to a surface that has none.

One construct, two packages, opposite directions, and the net is worse than either alone.

### 9.3 · A non-rendering template set named as the surface

Property: the implementation notes (`base.jinja2`'s font div, `data_table`, `comp_grid`).
Market: the surface line itself, and two of the three things they say they removed.

**This is D-131's predicted cost, measured twice in one day.** The warning exists; it reached
neither package. On the property side it cost a handful of wrong instructions. On the market
side it cost an architectural reversal.

### 9.4 · The same constraint, understood once and reversed once

PDFShift's matched-`start_at` rule is cited in both handoffs. The property one concludes variant
A and keeps the running head; the market one concludes no running head at all. **Same sentence,
opposite outcome, and the difference is which template set was open.**

This is the finding that justifies reviewing both together: neither package contradicts itself,
and the pair does.

---

# 10 · What the package must now say

Updated from §7 by the market review.

1. **The dead and legacy trees, by name, in both packages.** `<theme>/<theme>.jinja2` and
   `_base/` on property; `apps/web/templates/trendy-*.html` and `app/print/[runId]/` on market.
   Say what renders: `property/<theme>/<theme>_report.jinja2` and
   `market/market.jinja2` + `market/_base/`.
2. **A measured contrast table for every fixed neutral and every semantic pair**, because the
   one adjective in both READMEs was wrong by 1.2.
3. **The `on_primary` rule as a rule, not a fallback** — including for small text on `accent`
   fills, which neither package covers.
4. **Variant A on both surfaces, with the running head named as part of it**, so the next reader
   cannot conclude from the same constraint that the head should go.
5. **`PAGE_1_CAPACITY` as a per-type, per-narrative-state measurement** that any new layout must
   re-derive, plus the fixed-height narrative box that makes it enforceable.
6. **The corrected property figures** — 146 of 213 — and the literal / `theme_color` /
   `derive_theme` split.
7. **The orphan list at full length**, including the six school and location rows the property
   design adds.
8. **`comp_confidence_grade` is API-only**, and **`COMP_SET_MAX = 15`** is a number the layout
   must survive.
9. **D-106 is about comps, not subjects.**
10. **The market surface's baseline: 66 of 5,058, all status and tier badges, worst 2.66.**
    Measured 2026-10-01, the first time since Workstreams C and D. Any redesign of that surface
    is measured against it, and a redesign that keeps coloured-text-on-tinted-chip inherits it.
11. **Semantic colours need an ink variant**, the same move `primary_ink` makes for the brand.
    Removing the tint buys 0.35 and is not enough.
