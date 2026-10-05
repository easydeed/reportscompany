# Review — Design's corrected packages

**Reviewed:** `docs/design-corrections/corrected-version/` at `0f02c7d9` · **2026-10-05**

**The corrections landed. The blocker is cleared. The market work can start.**

Both packages were re-rendered and re-measured, and this time the measurement gap is closed:
32 market documents (8 kinds × 4 brands) and 18 property documents (3 themes × 6 brands), built
with the harness Design suggested rather than their gallery file, which still does not render.

| | before | after |
|---|---|---|
| property design | 49 failing of 361 — **1 brand** | **45 of 6,192 — 18 documents** |
| market design | 4 failing of 57 — **1 brand** | **96 of 2,672 — 32 documents** |

**Every one of the property's 45 is the owner exception.** Nothing else fails on any theme or
any brand. The market's 96 are all on the two light brands and three of its four pairings are
the same exception; one is not.

**And the exception's own stated bound is wrong, in both packages, in the same words** — see §7.
That is the one thing to send back.

---

## 1 · The type mapping — RESOLVED

`design_handoff_market_reports/README.md:12` gives all eight, explicitly:

```
snapshot          → market_snapshot        closed    → closed
listings (grid)   → new_listings_gallery   inventory → inventory
listings (table)  → new_listings           bands     → price_bands
featured          → featured_listings      gallery   → open_houses
```

Option 2 as we recommended: **one `listings` kind with `listingsDensity: grid | table`**, header
and stats identical, body swapping between the 3 × 2 photo grid and a six-column table. Nothing
deleted from the product. Each row of the per-kind spec table is now keyed to its live type
name, so the mapping cannot drift from the spec.

**Naming decided: "New Listings" = the table, "New Listings Gallery" = the grid**, on the PDF
title and both wizard screens. That is a complete answer to **D-162** — it tells us which of the
two existing names belongs to which type, which was the part we could not decide ourselves.

**The market side is unblocked.**

## 2 · The running head — KEPT, and reasoned rather than routed around

> *"Running head kept (the live architecture; 1.07in recovered per page): 40px, PDFShift header
> from page 1 … **Both `start_at` = 1, always.** Continuation pages carry the running head and
> the table — there is no separate brand strip."* — market README:25

They engaged with the constraint, not around it. The pages-2+ brand strip from the first package
is **withdrawn**, and `PDF Reports v2.dc.html` §3a is explicitly marked superseded on that point
(README:99) rather than left to contradict the new decision. The property package already had
variant A and still does.

This is the cheaper branch and the one that keeps `test_page_architecture.py` unchanged.

## 3 · The three shared corrections

### S1 · `#8A8E95` — landed, and they adopted the method

Gone from both live design files (`Property Report.dc.html` 0 occurrences, `Report Page.dc.html`
0) and from both neutral tables, replaced by `#5E636B` throughout. The surviving `#B9BBC1` in
the design files is a **border on the MOI legend**, not text — correctly re-scoped.

They went further than asked: the property README's neutral list now carries **measured ratios
inline** — *"ink `#14161A` (18.1:1 on white), body `#2A2D33` (13.8), muted `#5E636B` (6.05 …)"*.
That is the discipline the correction was about, adopted rather than complied with.

**The dash is withdrawn as a colour**: `const dash = "—", DASHC = "#5E636B"` with weight 400
against 600 for known values — unknown distinguished by weight rather than by being faint. No
auditor exclusion needed. Better than what we asked for.

### S2 · Small white text on a brand fill — landed, scope narrowed by name

The band now splits: **everything under 24px takes `on_primary`** (white or `#14151a` by
contrast), display text stays white. The auditor exclusion went from "the cover band element"
to:

> *"Scope any auditor exclusion to the **city line element only**."*

They identified the one sub-threshold case themselves — the city line is 22px/500, under the
24px large-text bar, so it needs 4.5 and gets 3.74. **Measured: exactly one failing run per
theme on teal, and it is that element.** The scope is now honest.

### S3 · The badge collision — one answer, both surfaces

* **Property: status pills removed entirely.** Status is text in the "when" line — "Sold Jul
  2026", "Pending · listed sep". The construct is not imported onto a surface that had none.
* **Market: `accent_ink`**, derived by darkening `accent` until ≥4.5 on white, text only, no
  chip. Over-asking %, "New", "Fastest" all use it.

One answer, applied in the direction each surface needed. **Measured: zero chip failures on
either surface, on any brand.** D-161's 66 would be closed by this.

## 4 · The dead tree — market clean, property three lines short

**Market: fully corrected.** README:3 now reads *"Live surface: `MarketReportBuilder` →
`market.jinja2` + `market/_base/`. **`apps/web/templates/trendy-*.html` and
`apps/web/app/print/[runId]/` are the LEGACY path and render no customer PDF — do not read
them.**"* The gradient / PDF-badge "removals" are struck.

**Property: the headline is corrected and three citations survive.**

| | |
|---|---|
| ✅ `README.md:3` | names the five live files and the 7,715 dead lines |
| ✅ `README.md:46` | *"No live template has a font-trigger div; if one is needed, add it to each of the five `*_report.jinja2`"* |
| ❌ `README.md:18` | *"recreate them in the existing Jinja2 + **`base.jinja2`** + PDFShift pipeline"* |
| ❌ `README.md:137` | *"**`comp_grid`** cap 4 → 6"* — doubly stale: the macro is dead **and** their own response now says six pictured, all 15 on page 4 |
| ❌ `STRUCTURAL_NOTE.md:48` | *"keep the **base.jinja2** font-trigger div"* |

`data_table` and `_macros` references are gone.

**Two of these contradict other lines in the same package.** README:46 says there is no
font-trigger div; STRUCTURAL_NOTE:48 says keep it. A spec that disagrees with itself is how the
wrong one gets implemented.

## 5 · What changed that we did not ask for

Diff against the originals: property README 30 changed lines, market 54. `support.js` byte-identical — the runtime did not move.

**Good, unasked:**

* measured ratios inline in the neutral tables (§3 above)
* **"Each sale" bars compress to 14px / 5px gaps above 8 comps**, so 15 rows fit beside the
  range panel — they solved the thing we said we would have to measure
* header copy that states the split: *"15 sales within 0.75 miles · last 6 months · nearest 6
  pictured, all 15 on page 4"* — the report says what it is showing
* `-webkit-line-clamp: 4` on the narrative, so an overrun ellipsises instead of cutting a word
* the per-kind spec table keyed to live type names

**Stale, not re-synced — all in the property package:**

| | says | should say |
|---|---|---|
| `README.md:128` | *"Unknown → '—' `#B9BBC1`"* | `#5E636B` at weight 400 — their own decision |
| `README.md:131` | *"page 3 holds 6 comps; page 4 holds 5 compare rows + 6 bars"* | page 4 carries all 15 |
| `README.md:162` | *"Market reports have no separate running head"* | the running head is kept |
| `STRUCTURAL_NOTE.md:6` | *"132/213 contrast failures"* | **146 of 213** — the number we corrected |

Plus the three in §4. **Seven stale lines, every one in the property package, none in the
market package.** The market README was re-read end to end; the property one was patched where
the correction letter pointed and not re-read. None of them changes a design decision — all
seven are a document disagreeing with its own design file or with a decision taken in the
accompanying response.

**One structural note:** `RESPONSE_2026-10-05.md` is **byte-identical in both folders**. One
joint response, shipped twice. Fine, and worth knowing before someone diffs them.

## 6 · The theme set — held at three, and the mapping does NOT hold

`elegant`, `bold`, `modern`. `classic` and `teal` removed, no hue carried by any theme. Design
held to it.

**The id→name mapping was asked to be verified rather than inferred. It does not hold, and the
check found a live defect — D-163.**

There is **no themes table**; the mapping is code-only, in four places, and they disagree:

| source | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **`property_builder.THEME_NUMBER_MAP`** — the renderer | classic | modern | elegant | **teal** | bold |
| `api/services/property_stats.py:49` | classic | — | — | — | — |
| `web/components/unified-wizard/index.tsx:29` | **teal** | **bold** | **classic** | **elegant** | **modern** |
| `web/components/onboarding/guided-get-started.tsx:57` | **teal** | **bold** | **classic** | **elegant** | **modern** |

**The renderer is right. The two web copies are wrong on every id**, and they do not merely
display the wrong name — they submit it (`setThemeId(THEME_ID_MAP[...])` → `theme_id: themeId`),
and the builder accepts a name, so it renders without error. Three live routes use them:
`/app/reports/new`, `/app/schedules/new`, `/app/schedules/[id]/edit`, plus onboarding.

| stored id | accounts | renderer | what the wizard sends |
|---|---|---|---|
| 4 | **41** | teal | **elegant** |
| 3 | 2 | elegant | **classic** |
| 5 | 1 | bold | **modern** |
| 1 | 0 | classic | teal |

**The decision's premise survives; one of its supporting statements does not.** No account
deliberately chose classic or teal — 41 of 44 chose nothing, and the three that chose picked 3
and 5. That holds. But *"nobody is on classic"* is true of the stored ids and **false of what
renders**: the two accounts on theme 3 are being sent `classic` today, by the wizard, and it is
one of the themes being deleted.

**So: cut the themes, and fix the mapping as part of the cut, not after it.** Correcting a map
of five themes that is about to become three is work done twice — but planning the cut against
the stored ids alone would miss that `classic` is in production output right now.

## 7 · The one thing to send back

> *"White display text on the brand fill stays (owner decision). Scope is now honest: street
> line, city line, stat values, big numbers — **all ≥3.0 on the six sample brands**."*
> — both RESPONSE files, and market README:46 in the same words

**It is not ≥3.0 on all six.** White on `primary`, computed and confirmed in the render:

| brand | ratio | 3.0 display threshold |
|---|---|---|
| violet `#7c3aed` | 5.70 | ok |
| coastal `#0e7490` | 5.36 | ok |
| demo `#dc2626` | 4.83 | ok |
| teal `#0d9488` | 3.74 | ok |
| **amber `#f59e0b`** | **2.15** | **fails** |
| **lime `#84cc16`** | **1.98** | **fails** |

**42 of the property design's 45 failures are this**, on amber and lime, at 64px and 30px. It is
the same shape as `#8A8E95`: a bound stated as a fact, in both packages, in the same words,
without being computed. The remedy is already written in their own README — *"a darker
`primary_dark` fill behind the text, never moving the brand colour"* — and it needs to fire
automatically when `primary` is too light, not be available as advice.

**And the market surface has two failures that are not the exception at all:**

| ratio | pairing | runs | size | what |
|---|---|---|---|---|
| 1.98 / 3.74 | `#84cc16` / `#0d9488` **as text on white** | 32 | 13px | the bands "days" column |
| 3.74 | white on `#0d9488` | 16 | 22px | the band label — *"is moving fastest"* |

The first is raw `primary`/`accent` used as small text where the spec says `accent_ink`. The
second is a 22px band label, the market twin of the property city line, and it is **not**
declared as an exception on that surface. Both are on every kind, so they are one rule each.

## 8 · Still cannot be measured

**The gallery file still renders empty** — 7 frames, 0 with text, with `support.js` beside it,
which was their stated diagnosis. Their fallback worked: driving `Report Page.dc.html` with the
props rewritten gives every kind. That harness is how the 32 documents above were produced and
it should ship with the package rather than being rebuilt each time.

The market design exposes **4 brand options**, not six — `#18235c`, `#7C3AED`, `#0D9488`,
`#84CC16`. Lime and teal are the two worst, so the coverage is meaningful, but amber and the red
are untested on that surface.

---

## Is it adoptable, and does the estimate hold?

**Adoptable. Yes — with the seven stale lines fixed and the ≥3.0 claim answered.** Neither is
a redraw; both are text.

**The estimate improves, and the theme answer is why.**

| | scoped | now |
|---|---|---|
| property | 2–3 weeks | **2–2.5 weeks** |
| market | 1–2 weeks | **1–1.5 weeks** |
| **total** | **3–5 weeks** | **3–4 weeks** |

What moved:

* **The theme migration is gone.** It was the largest single item and it was costed as
  *"migrating live accounts onto a theme they didn't pick"*. Jerry's query says nobody picked
  either. What remains is a new `accounts.default_theme_id`, a new builder fallback, and a
  one-line update of the 41 default rows. **A day, not a week** — plus D-163's mapping, which
  has to be collapsed to one server-owned source in the same change rather than corrected
  four times. Call it two days together.
* **The type mapping is answered**, so the market template takes a known shape.
* **The running head is kept**, which is the branch that leaves `test_page_architecture.py`
  unchanged.
* **"Each sale" at 15 comps is solved in the design**, so §2's measurement risk is retired.

What did not move: **596 gate tests across 18 files still have to be re-derived**, and that was
always the long pole. Three themes instead of five shrinks the parametrised cases but not the
reading.

**Step 3 can start** — one theme end to end, the live pipeline, the existing gates re-pointed —
as soon as Jerry picks the new default theme. That is the only remaining input.
