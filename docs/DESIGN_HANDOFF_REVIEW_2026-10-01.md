# Review — Claude Design's property report handoff

**Reviewed:** `docs/design-claude/design_handoff_property_report/` at `d474fc2` ·
**Date:** 2026-10-01 · **Verdict: correction list, not a redo.**

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

**The market report designs are not in the repo.** `docs/design-claude/` contains only
`design_handoff_property_report/`. Their self-check table has a filled-in column for "market
reports (Report Page / PDF Reports v2)" making specific claims — that every fill is `primary`
with white text, that light affiliate colours will need the same `on_primary` logic, that there
is no separate running head. **Those claims cannot be checked against anything.** Jerry says the
designs exist; they were not handed over.

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

1. **The dead tree, by filename, first.** Already in `CLAUDE_DESIGN_HANDOVER.md` §0. It did not
   reach them in time and it is the single highest-value paragraph in the document.
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
