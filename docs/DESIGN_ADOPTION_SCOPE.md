# Scope — what adopting Claude Design's output costs

**Date:** 2026-10-05 · **Status: scope only, nothing started.** ·
**Inputs:** the two handoffs, `DESIGN_HANDOFF_REVIEW_2026-10-01.md`, `design-corrections/`.

Counted, not estimated: file sizes from `wc`, test counts from `pytest --collect-only`, page
sets and maps read from the code that declares them.

---

## The short answer

**Another workstream, not days.** Two to three weeks of engineering for the property report and
one to two for the market reports, and the long pole on both is **re-deriving gates, not writing
templates**. The templates are the smaller half.

| | |
|---|---|
| live property templates replaced | **5,767 lines**, 5 files → 1 |
| live market templates replaced | **2,479 lines**, 5 files → 1 |
| gate tests touching what moves | **596** of the suite's 1,551 — **38%** |
| gates that must be *re-derived*, not just re-baselined | the page-set, capacity and theme-parametrised ones |
| **blocking product decisions** | **3** — none of them engineering's to make |

The three blockers are listed in §6. **Two of them have to land before any of this starts**,
because they change what gets built rather than how.

---

## 1 · What is adoptable, what needs correcting, what needs rebuilding

### Adoptable as-is — take it

| | why |
|---|---|
| **"Each sale"** (property, p4) | better than what we built; see §2 |
| **Missing-photo tile**, both surfaces | we had no treatment at all |
| **The range copy** | the product owner's "reporting, not stating" in one sentence |
| **"Your home" replacing "PIQ"** | already on our list, no owner |
| **Chart values + axis** | same |
| **"Zero is data, not absence"** (market) | our rule, written better than we wrote it |
| **Headline functions returning `null`**, template renders the plain title (market) | the right shape; threshold in one place |
| **`primary_dark` behind text, never move the brand** | should be the rule on both surfaces |
| **Deltas <1% → "flat"; headlines hidden under 10 sales** | bounded, stated, testable |

### Needs correcting first — the design holds, the spec does not

| | correction |
|---|---|
| all neutrals | `#8A8E95` → `#5E636B`. One find-and-replace in the spec, 28 runs on the page |
| cover band small text | `primary_dark` behind anything under 24px on a fill |
| status pills (property) | **delete** — this surface has no badges |
| status/tier colours (market) | darker ink per semantic; removing the tint is not enough |
| `#B9BBC1` dash | a decision: keep at 1.92 and record the exclusion, or lift it |
| Schools + Location groups | six rows no producer writes; into the "Not on record" strip on day one |
| `comp_confidence_grade` | plumb it to the worker, or drop both uses |
| comp `ba` segment | omit when absent, per their own rule |
| HOA "None" in the reference render | contradicts their own spec |

**All of these are spec edits.** None requires re-drawing anything.

### Needs rebuilding against the live templates — the notes, not the designs

Every template-level instruction in the property package points at the dead tree, and the
market package's surface line points at the legacy path. **Nothing in either design needs
redrawing because of it** — what needs rewriting is the implementation plan, which is a
document we can write ourselves from the designs we have.

### One thing is not yet a design

Design's market handoff covers **seven kinds**. The live build has **eight report types across
five layouts**:

```
gallery          : new_listings_gallery, featured_listings, open_houses
market_narrative : market_snapshot
closed_inventory : closed, inventory
pricebands       : price_bands
analytics        : new_listings
```

Their "listings" and "gallery" kinds do not cover both `new_listings` (analytics layout) and
`new_listings_gallery` (gallery layout) — two different reports today. **A type-by-type mapping
is required and it is not 1:1.** That is a design question, not an engineering one, and it is
the first thing to send back.

---

## 2 · "Each sale" replacing the continuation page

**Recommend adopting it.** The evidence belongs beside the number it supports, not overleaf.

### What it changes

| | today | with "Each sale" |
|---|---|---|
| comparables shown as cards | 4 | 4 (unchanged) |
| the rest | a continuation **page** of 8-column rows | bar rows on the range page |
| pages at n > 4 | 8 | **7** |
| `PAGE_ORDER` | `comparables_all` between `comparables` and `range` | key removed |
| the conditional-add in `render_html` | adds the page when `n > CARDS_PER_COMPARABLES_PAGE` | removed |

**One page shorter, and one conditional page fewer.** The conditional page is the expensive
part: it is the only key in `PAGE_ORDER` whose presence depends on data, so removing it makes
the page set a function of the request alone again.

### What moves

* **`test_one_comp_set.py` (88 tests)** — the invariant survives unchanged and is the reason
  this swap is safe. "Every count in the document is the same count" does not care *where* the
  comps are listed. The continuation-page tests (10 of the 88) are replaced by the same
  assertions pointed at the range page. **The Chromium page-fit gate transfers directly** and is
  the thing that will say whether 15 bar rows fit beside a range panel — my expectation is yes,
  a bar row is shorter than a table row, but that is measured, not assumed.
* **`test_contents_matches_the_document.py` (48)** — loses one row. Trivial.
* **`test_a_dropped_page_is_reported.py` (10)** — one test asserts an *added* page is not
  reported as a drop. It becomes unnecessary and should be deleted, not neutered.
* **`paginate()` and `CONTENTS_OMITS`** — unchanged.

### The one risk

The range page currently holds a dark panel, a 5-row comparison table and the bar list. At 15
comps that is 15 bar rows on the same sheet. **Measure before committing** — the same Chromium
fit gate that caught the 390px overflow on the continuation page. If it does not fit, the answer
is Design's own rule: cap at the builder, not the template, which puts `COMP_SET_MAX` back on
the table (§6).

---

## 3 · Is the market design workable once the running-head decision lands?

**Yes, either way.** Both branches are buildable; they cost different things.

### If the running head stays (our recommendation)

Design's page-1 band sits below a 40px running head, exactly as the property report already
does. **Their layout needs one change**: the band moves down 40px and page-1 content loses that
much. Everything else in their spec is unaffected — the strip on pages 2+ becomes the running
head rather than body content, which is *less* work than what they specified, because the
header slot already does it per page.

* `test_page_architecture.py` (13 tests): **unchanged.**
* `PAGE_1_CAPACITY`: re-measured for their row heights. Required either way.
* Cost: a 40px band on every page that their design does not currently show.

### If the running head goes

* The strip on pages 2+ must be emitted **per chunk by the table partial**, because a paged flow
  has no per-page body hook — CSS `padding-top` applies once at the start of the flow. Their
  builder already computes `P` from the row count, so the pagination arithmetic exists.
* **`header.start_at` and `footer.start_at` must both stay 1 regardless**, or the footer vanishes
  from page 1 with an HTTP 200 and no warning. This is the trap, and it is silent.
* `test_page_architecture.py`'s four legs need rewriting — three of them assert against a header
  document that would no longer exist.
* The **1.07in per page** that variant A recovered comes back out, and the measured page counts
  go with it: `closed` 5 pages → 6, `new_listings` 16 → 18.

**Neither branch is blocked.** The first is cheaper and the second is defensible. It is a
product call about whether a running head on page 1 is worth 1.07in of every page.

---

## 4 · What the gates say about their output today

Only two gates can run against a `.dc.html` at all. Both did.

| gate | property design | market design |
|---|---|---|
| pixel contrast auditor | **49 failing of 361** (1 theme × 1 brand) | **4 failing of 57** (1 type × 1 brand) |
| 1.5:1 invisibility floor | **passes** — worst run 1.92 | **passes** — worst 3.29 |
| unmeasurable text (`background-clip`) | **0** | **0** |

Every other gate needs the real pipeline and cannot be pointed at a design file: the page-set
and contents gates import `paginate()`; the comp-set invariant imports `COMP_SET_MAX`; the owner
gate parses Jinja; the capacity gates measure a rendered Jinja template.

**What that means for sequencing:** the design cannot be validated before it is wired. The first
wiring milestone should be *one theme, the live pipeline, the existing gates re-pointed* — not
all three themes — because that is the first moment any of the 596 tests can say anything.

**Still unmeasured:** six of seven market types and five of six brands. Their gallery file
renders empty outside their environment. Asking them for static renders is one message and
would close it.

---

## 5 · The honest size

> ## MEASURED AGAINST ONE THEME — 2026-10-06
>
> bold is wired and rendering through the production path (#146). The estimate below was made
> before any of it was built, so the parts of it that are now **measured** rather than estimated
> are recorded here. **The remaining two themes are not yet wired, so the total is not restated —
> what follows is what one theme cost and what it implies, which is a different claim.**
>
> | line | estimated | what bold measured |
> |---|---|---|
> | one template replacing five, three themes | 3–4 days | **the shared file is 735 lines and written once.** bold's own entry file is **34 lines** — eight `{% set %}`s and an `{% include %}`, down from 1,290. The per-theme marginal cost is that file |
> | `derive_theme` migration | 2 days | **already written.** `themes.derive_theme` produced the six tokens Design asks for before this started; the wiring was adding them to the context. The one real change was D-170 — `primary_ink` was below AA on its own `tint`, half its own definition |
> | builder changes | 2–3 days | **done, in one pass**, plus four defects the render found that reading would not have |
> | **re-deriving gate tests** | **4–6 days** | **55 failures, and this is the line the estimate got most wrong in shape.** Four were defects in the new build; the rest were re-points. The re-pointing made the gates **architecture-aware** — `_template_chain` resolves a theme's includes and every gate asks `SHARED_THEMES` / `SELF_CONTAINED_THEMES`. That work is **done once, not once per theme** |
> | contrast baseline across 3 themes × 6 brands | 1–2 days | bold needed **no regeneration at all**: 13 new pairings, all 13 fixed in the template, 37 orphans deleted by key. It ended with **zero** baselined failures. elegant and modern carry 75 rows between them and will regenerate under the policy Jerry set on 2026-10-06 |
> | theme migration for live accounts | 1 day + a decision | **done** (#145). 41 rows, one migration, and the decision was bold |
>
> **What the overstatement was made of, so far as one theme can show it.** The estimate priced the
> gate re-pointing as proportional to the themes, because at the time a theme WAS a file and there
> was no reason to think otherwise. It is proportional to the **architectures**, and there are two.
> It also priced the `derive_theme` migration as work when it was already written, and priced a
> baseline regeneration that the first theme did not need.
>
> **What it did not overstate.** The defects. Six were filed from wiring one theme (D-167 to
> D-172), two of them — the three market metric functions that do not exist, and Design's cover
> decision resting on a false premise — worth more than the wiring. Nothing in the estimate had a
> line for "what the render tells you", and that is where the week went and where it was worth
> going.
>
> **The remaining two themes are not measured.** The claim above is that their marginal cost is a
> 34-line file plus a baseline regeneration, and the only thing that establishes it is wiring one of
> them. Until then it is an inference from a sample of one, which is the error this document was
> written to avoid making twice.

### Property — 2 to 3 weeks (as estimated; see the box above)

| | |
|---|---|
| one template replacing five, three themes | 3–4 days |
| `derive_theme` migration (`compute_color_roles` → tokens, `_THEME_DARK_BG` → `#0f172a`) | 2 days |
| builder changes: page set, title ladder, closed-only stats, `ppsf`, `requester_name` | 2–3 days |
| **re-deriving 494 gate tests** | **4–6 days** |
| contrast baseline regeneration + brand sweep across 3 themes × 6 brands | 1–2 days |
| theme migration for live accounts (§6) | 1 day + a product decision |

### Market — 1 to 2 weeks

| | |
|---|---|
| one template replacing the layout dispatch, 8 types | 3–4 days |
| `PAGE_1_CAPACITY` re-measured per type **and per narrative state**, narrative box given a fixed height | 2 days |
| the running-head branch (either) | 1–3 days |
| **re-deriving 102 gate tests** | 2–3 days |

### Why the gates dominate

**494 of the 596 tests are on the property surface, and 12 test files are parametrised over the
theme set.** Dropping 5 themes to 3 does not delete tests, it changes what every parametrised
case renders — so each one has to be re-read rather than re-run. The contrast baseline is 209
lines, **58 of which name classic or teal** and are simply deleted; the rest must be regenerated
against a different document, which is the one regeneration this project's own rules say never
to do casually.

**This is not padding.** The gates are what caught every defect in the last three weeks, and a
redesign that re-baselines them wholesale throws away the thing that makes the redesign safe.

---

## 6 · Three decisions that block the start

**None are engineering's.** Two change what gets built.

### 6.1 · Removing `classic` and `teal` — **blocking**

`accounts.default_theme_id DEFAULT 4`. **Theme 4 is teal.** Every account that never chose a
theme is on one of the two being deleted, and `classic` is theme 1. The builder's own fallback
for an unknown theme is `teal`.

So this is not a config change: it is a **migration of live accounts onto a theme they did not
pick**, plus a new default, plus a new fallback. Design proposes migrating them to `elegant`
"with a note in the wizard". That is a customer-visible change to documents already being sent,
and it needs the product owner, not a ticket.

### 6.2 · The running head — **blocking the market work only**

§3. Either branch is buildable; the choice changes the architecture and the page counts.

### 6.3 · `COMP_SET_MAX = 15` against a page that holds six — **blocking the property work**

Already open from the review. "Each sale" (§2) probably absorbs it, and "probably" is why it is
measured before it is promised.

### And one that does not block

The 17 always-empty fields (`JERRY_PROPERTY_FIELDS_DECISION.md`) can be answered during the
build. Design's "Not on record" strip is option B and degrades cleanly to option C — if the
answer later becomes "remove", the rows and the strip go together.

---

## 7 · What I would do first

In order, and the first two are not engineering:

1. **Send `design-corrections/` to Design** and get the market type mapping back (§1), which is
   the only genuine hole in either package.
2. **Get the theme decision** (§6.1). It is the largest single item in the property estimate and
   it is the one that touches live accounts.
3. **Wire one theme end to end** — `elegant`, the live pipeline, the existing gates re-pointed
   and nothing re-baselined. This is the first moment any of the 596 tests can speak, and it
   will be wrong about something; better to be wrong once than three times.
4. **Measure "Each sale" at 15 comps** with the Chromium fit gate before committing to it,
   because the recommendation in §2 rests on it fitting.

Steps 1 and 2 are messages. Step 3 is roughly a week and answers most of what the estimate above
is guessing at.
