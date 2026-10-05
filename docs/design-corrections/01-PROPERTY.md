# Corrections for Design — property report

**Read `00-SHARED.md` first.** Three of the items here are shared with the market report and are
answered there once; this document covers what is specific to this surface.

**The design survives. Only the implementation notes point at files that do not render.**

---

## What you got right

Not a formality — several of these are things we flagged and could not solve ourselves.

* **Variant A, reasoned from the constraint.** You identified PDFShift's matched-`start_at` rule
  and put the masthead in the body rather than fighting it. That constraint cost us a credential
  trip and a four-render probe to establish, because PDFShift accepts mismatched values with an
  HTTP 200 and silently applies `max(header, footer)` to both. You applied it without being told
  twice. **Please keep doing exactly this on the market surface too — see `02-MARKET.md`.**
* **Deleting the four theme literals rather than re-picking them.** `--gold`, `--coral`, `--sky`,
  `--teal` were three of the six colour roles carrying 146 of our 213 contrast failures. Removing
  the hue from the theme removes them at the source instead of managing them.
* **Every page-1 growth path bounded, with the bound stated as a number.** 78px title box, a
  five-step ladder by character count, an ellipsis backstop, `max-height: 81px` on the narrative.
  Page-1 capacity stays deterministic, which is the property it needs.
* **A designed missing-photo state.** We had none — no tile, no fallback, nothing. A `tint` tile
  with the neighborhood name and "No photo on file" is the first answer this product has had.
* **The chart carries values and an axis**, and **"PIQ" becomes "Your home"**. Both were on our
  list and neither had an owner.
* **"Each sale" — one bar row per comparable, on the same page as the range.** This is a better
  answer than ours. We had put the full comparable list on a continuation page; yours puts the
  evidence beside the number it supports. Adopt yours.
* **The range copy.** *"This is what recent sales of similar homes nearby support. It is a report
  of the market, not an appraisal, and a listing price is a conversation with your agent."* That
  is the product owner's "reporting, not stating" in one sentence, which nobody had managed.
* **Agent and consumer as three named branches in one template**, with owner identity on the
  agent path only. That is the architecture we shipped last week, understood from the code.
* **A self-check table that records an exception against itself.** Incomplete, as it turns out —
  but it is the right instrument, and it is the reason the gaps below are discussable at all.

---

## 1 · The implementation notes point at the dead tree

Everything you name at the template level is in the 7,715 lines that render nowhere. See
`00-SHARED.md` §S4 for the file map.

| your note | reality |
|---|---|
| *"Keep the font-trigger `<div>` in `base.jinja2`"* | that div is at `_base/base.jinja2:1776` and `:2135`. **No live template has one.** If the three Google faces need a load trigger, it has to be added to each of the five `*_report.jinja2` |
| *"the current `data_table` macro hides them"* | `data_table` is `_base/_macros.jinja2:135`. There is no macro to change. Each live template writes its rows inline — which is good news: "rows are never hidden when null" is a property you write once per template, not a macro behaviour to override |
| *"`comp_grid` cap 4 → 6 (current macro caps at 4)"* | `comp_grid` is `_base/_macros.jinja2:338`, called only from the dead base. **The live build no longer caps at 4 either** — see §6 |

None of this touches the design. It is a list of edits to make somewhere else.

---

## 2 · The cover-band exception is real and scoped to the wrong thing

Covered in `00-SHARED.md` §S2. Short version: your measurement is right (3.74 teal, 2.15 amber,
1.98 lime), the exception is honest, and the **auditor exclusion you ask for would suppress
seven genuine small-text failures** to permit display text that already passes at the 3.0
threshold. Narrow the exception to the display line; apply `primary_dark` behind everything
under 24px on a `primary` fill.

---

## 3 · Drop the status pills from this surface

Covered in `00-SHARED.md` §S3. The property report has no status badges today and yours measure
3.95 / 2.86 / 3.32. Adding them imports the market surface's only remaining contrast defect onto
a surface that does not have it.

---

## 4 · `primary_ink` on `tint` fails for two of six brands

| brand | `primary_ink` on `tint` | |
|---|---|---|
| violet | 5.21 | ok |
| coastal | 4.95 | ok |
| lime | 4.76 | ok |
| amber | 4.53 | ok |
| **demo_title** | **4.41** | fails |
| **luxury_estates** | **4.33** | fails |

`tint` is the "In short" panel, the confidence pill, the next-steps cards and the missing-photo
tile — a recurring surface, not an edge. Two of six brands is a third of our sample. `tint` is
derived (`derive_theme`), so this is ours to fix in `themes.py`, **but the target is yours**:
tell us whether `primary_ink` must clear 4.5 against `tint` as well as against white, and we
will derive to it.

---

## 5 · Six rows you added have no producer at all

> *"Schools (`school_district`, `school_elementary`, `school_middle`, `school_high`) and Location
> (county, neighborhood, census tract) as two more groups on 'Your home'; rows dash when absent
> (**the repo hides them** — this keeps §3.6 consistent)."*

**The repo does not hide them. The repo does not have them.** There is no `school` anything in
`apps/worker` or `apps/api`. SiteX's `PropertyData` carries 32 fields and not one is a school.
`school_district` exists on *market* listings from the MLS feed; it has never been on the
property path. `neighborhood` likewise. `census_tract` is already on the orphan list.

Of the seven rows in those two groups, **`county` is the only one with a producer.**

So the design adds six permanently-empty rows to the page whose problem is permanently-empty
rows — and the sample render shows all four schools filled with invented names, which is exactly
what makes a reviewer believe the data exists.

**Not a reason to drop them.** If schools belong on this page, that is a sourcing decision worth
making — it is a real gap and your design is the first thing to name it. But they belong in the
"Not on record" strip on day one, and the package the product owner is deciding against needs
them on the list.

---

## 6 · `COMP_SET_MAX = 15`, and your page holds six

The comps grid is 3 × 2 and the capacity note says page 4 holds "6 bars". The builder returns up
to **fifteen**. Three outcomes and only one is acceptable:

* **cap the ladder at 6** — a change to what the search returns, which nobody has decided;
* **show 6 of 15** — the report then says it analysed fifteen and shows six, which is a defect we
  closed four days ago (the page said "every one of the 15 appears" and showed four);
* **let the page grow** — your own stated rule is *"If data can exceed these, cap at the builder,
  not the template"*, which argues for the first.

**This needs deciding before implementation, not during.** Your "Each sale" bar list is the
natural place for all fifteen; it is one row each, and it is the page where the range is printed.

---

## 7 · `comp_confidence_grade` never reaches the renderer

The confidence pill on the comps page header, and the range panel's "confidence A, strict match"
label, both read `comp_confidence_grade` / `comp_confidence_reason`.

Those are computed in **`apps/api`** (`routes/property.py:893`) and consumed only by the dead
`comp_grid` macro. **Nothing in `apps/worker` reads either name**, and `apps/worker` is what
renders the PDF.

That is a read with no producer — the defect family that has cost this project more entries than
any other — and you caught it at design time, which is the first time that has happened. Either
we plumb it through to the worker, or both uses come out. **Our recommendation is to plumb it:**
the grade is the honest answer to "how close are these comps", and the range panel is stronger
for carrying it.

---

## 8 · Bathrooms: you fixed the half you could see

The **subject's** bathrooms are handled well — the cover stats row drops a null and backfills
with lot size, with `bathsKnown` as a Tweaks toggle. SiteX does carry `bathrooms` for the
subject, so that is the defensive half.

The defect is on the **comparables**. `bathrooms` is absent from 301 rows of a real MLS market —
measured, not inferred. Your comp card's second line is `"{bd} bd · {ba} ba · {sqft} sq ft"`, so
it renders:

```
3 bd · — ba · 1,642 sq ft
```

on **every card, six per page**. Either drop the `ba` segment the way you drop a missing
neighborhood (*"omit the segment, do not print '· —'"* — your own rule, one section up), or
accept it until the feed changes.

The analysis table has a Bedrooms row and no Bathrooms row, which is the right call.

---

## 9 · Two smaller things

**The rendered page 2 shows `HOA  None`.** Your absence rules say never "None"; your spec says
HOA null → "HOA —", HOA 0 → "No HOA". The reference render contradicts the specification on the
one word the absence rule is about. Probably sample data; worth fixing in the reference so
nobody implements what they see.

**`overflow: hidden` on the narrative truncates mid-sentence with no signal.** The ~380-character
generation cap makes it rare rather than impossible, and a four-line box plus a soft cap will
eventually cut a sentence in half with nothing on the page saying so. A fade, an ellipsis, or a
hard cap at generation that respects sentence boundaries — your call, but it should be a choice.

---

## One number we gave you wrong

Your structural note says the theme-literal deletion *"removes 5 of the 6 values behind
**132**/213 contrast failures"*. **132 was wrong in our defect list when you read it** — the role
table had been assembled by eye and its own rows summed to 134. Re-derived from the measurement:
six colours carry **146 of 213**, counting a colour that fails in both directions once.

It strengthens your case rather than weakening it. Apologies for the bad input.
