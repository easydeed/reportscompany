# The market PDF surface: seven of eight kinds, measured

**Status at 2026-10-11.** Seven of the eight market report types render Design's `_v2` page.
**`market_snapshot` is not wired** — it is scoped (below) and is the remaining work.

**The old-beside-new review pack is not committed, and is regenerated rather than stored:**

    python3 scripts/build_review_pack.py --out <dir>

One PDF, ~3MB, 46 pages: a cover, then per report type a divider saying what changed and what to look
at, the current report, then the new one. One brand, 24 listings each.

**Deliberately not in the repository.** A rendered comparison is a recorded measurement of two
documents, and this project's standing rule is that such a record may not outlive its subject — a
committed pack would be stale the first time a template changed, and stale with no gate to say so
(the contrast baseline and the gallery fit measurement have both already been through that). The
generator is committed, so the pack can be rebuilt from any commit and will describe *that* commit.
It also means a reviewer's copy can never silently disagree with `main`.

Everything here is produced by rendering, not by reading. `scripts/measure_market_pagination.py`
(Chromium's own paginator, Letter, PDFShift's reservations) for pages and rows;
`scripts/measure_contrast_by_pixel.py` for contrast; `scripts/measure_gallery_continuation_fit.py`
for the gallery geometry.

---

## 1 · Pages and rows, legacy against `_v2`

Both columns measured on **one render path** — the seam was emptied to produce the "before" figures
rather than checking out an old commit, so the only variable is which page each kind renders.

| kind | pages | rows carried | wired |
|---|---|---|---|
| `closed` | 5 → **5** | 120 → 120 | yes |
| `new_listings` | 16 → **5** | 120 → 120 | yes |
| `price_bands` | 2 → **1** | 8 → **0** | yes |
| `inventory` | 5 → **5** | 120 → 120 | yes |
| `new_listings_gallery` | 14 → **14** | 120 → 120 | yes |
| `open_houses` | 12 → **12** | 100 → 100 | yes |
| `featured_listings` | 2 → **4** | 12 → 12 | yes |
| `market_snapshot` | 2 → 2 | 9 → 9 | **no** |
| **total** | **58 → 48** | **609 → 601** | |

**Ten pages saved.** Not from truncation: **every kind carries the identical rows** except
`price_bands`, which no longer renders a listings table at all — its `_v2` body is the six-row band
table, which is the point of the kind. That is a deliberate body change, not a cut.

**Density: 10.5 → 12.5 rows per page**, a 19% rise. That is the number that answers "did we just
truncate things", and it answers no: the same content in fewer pages, plus one kind whose content
changed on purpose.

**One kind got longer.** `featured_listings` 2 → 4, because Design's featured card is 326.8px against
the shared gallery card's 238.3 — 18px price plate, 15px address, and a 2-column grid whose photo is
260px tall. Accepted rather than worked around; D-184 records that **4.7 pixels** would take it back
to 3 and asks Design which five to give up.

---

## 2 · Contrast

| | rows |
|---|---|
| market baseline, 2026-10-07 | 6 |
| market baseline now | **0** |
| property baseline | 0 (linen 0, harbor 0, atlas 0) — 26, all linen's, until 2026-10-26, when harbor and linen moved onto the shared six-page architecture and the old layouts' failures went with them; was 55 on 2026-10-21 morning; D-205/D-206 retired 12, the muted/primary_ink swaps 5, the `ink_on` per-ground inks 9, and `on_primary` on harbor's brand-filled table row 3 |

**Zero baselined contrast failures on the market surface**, across 5,058 measured text runs, six brand
colours and eight report types. Held by
`test_pdf_contrast.py::test_the_market_surface_has_no_baselined_failure_left` and
`test_market_token_mapping.py::test_the_market_baseline_is_spent`, both of which a recorded mutation
is seen to break.

**The heuristic that predicted it, stated before any `_v2` template existed:** all six market rows
were badge selectors — three tier badges on `new_listings`, three status badges on `price_bands`, none
on `closed`. So: 0 for `closed`, 3 for `new_listings`, 3 for `price_bands`. Measured **0, 3, 3.**

Its last two predictions carried **no information** and are recorded as such rather than counted:
`inventory` and the galleries were predicted to close zero on a surface already at zero. A prediction
of zero against an empty set is not a hit.

---

## 3 · Page-1 capacity is deterministic on every kind

`PAGE_1_CAPACITY` reads **one number per kind** for all seven wired kinds — the same figure with and
without an AI narrative. `market_snapshot` still reads `3 / 3 / 0`: its third state is the trend
chart, which is a chart rather than prose, so the number does not depend on model output there either.

That was the architectural point of the adoption. Before it, `closed` and `inventory` read 15 without
a narrative and 11 with one, so **how long an LLM happened to write decided where page 1 ended.**

---

## 4 · What each kind cost and saved

| kind | pages | contrast | the finding it produced |
|---|---|---|---|
| `closed` | 0 | 0 | **D-178** — the close-to-list ratio arrives on two scales, reconciled by a `< 2` guess written twice in a template |
| `new_listings` | **−11** | **−3** | the largest single saving on the surface; off the analytics layout |
| `price_bands` | −1 | **−3** | **D-180** (four defects found by repointing the old chart's tests instead of deleting them), **D-181** (D-111's disclosure lost its only consumer while its test stayed green) |
| `inventory` | 0 | 0 | **D-182** — "seller's market" meant under 4 months on the PDF and under 3 in the email, six implementations, two thresholds. **D-183** — the pace chart lost its page and nearly kept its vendor fetch |
| the three galleries | **+2** | 0 | **D-184** (Design's page-1 grids do not fit under Design's band), **D-185** (a page-size assertion covered one report type and read as if it covered the class), **D-186** (three facts the card dropped, each caught by a gate written for a zero) |

---

## 5 · What is still open on this surface

| | what |
|---|---|
| **`market_snapshot` unwired** | the remaining kind. Scoped in §6 |
| **D-184** `open` | Design's page-1 grids. Two asks, relayed with the arithmetic in `GALLERY_GRID_FOR_DESIGN_2026-10-10.md` |
| **D-182** `[JERRY]` | which seller's-market threshold is right. Four `moi < 3` sites are live email copy and an LLM prompt; aligning them is a content change, now a one-line edit in one file |
| **D-183** `[JERRY]` | the inventory report carries no trend at all. Restoring it is one line plus a chart slot Design would have to agree to |
| **three dead layout macros** | `analytics_layout`, `closed_inventory_layout`, `gallery_layout`, `pricebands_layout` — no kind reaches any of them. Pinned in `UNREACHABLE_LAYOUT_MACROS`; they are the rollback path while one kind is unwired |
| **unsent to Design** | the 13-and-26 row counts are not simultaneously satisfiable (costs nothing — we render 17 and 26 at five pages, not six) |

---

## 6 · `market_snapshot`, scoped

Design's snapshot is the most complex band in the package: median sale price at 96px with no label, a
delta pill, **four** stat cells, and a body of three row-blocks — an MOI headline block with an 8-cell
bar and legend, a tier headline block with three accent bars, and "By property type" as three tint
cards.

**Every part of the body already has a producer**, which is the "grep for one before building it"
rule paying off:

| Design's block | producer |
|---|---|
| MOI headline + 8-cell bar | `compute/moi.condition()` (centralised by D-182) and `gauge_pct` |
| tier bars: 3 × count, median, MOI | `build_market_snapshot_result`'s `price_tiers` |
| "By property type" 3 cards | the same builder's `by_property_type` |

**The deltas do not.** `fetch_and_compute_market_trends` is called from `property_builder.py` and
**nowhere on the market path**, so the `▲ 3.1%` pill and the arrows on three of the four stats have no
producer here. Two further problems if it were wired: it performs its own vendor fetch, and it
compares 0–90 days against 90–180 under a label that reads *"vs. prior 30 days."*

So the build is Design's layout with the four stat **values** and **no invented arrows** — pill
dropped per D-137, slots left with the reason recorded, per the standing rule on gated values.

**Expected shape, stated before building:** zero contrast rows closed (the surface is at zero), and
**2 pages → 1**, because Design's snapshot body has no listings table and `price_bands` is the
precedent for a kind whose body stops paginating.

---

## 7 · §07's unbuilt items, and one that is untracked

**Tracked and deliberately open:** `closed`'s DOM distribution chart. `DELIVERY_SURFACES_MASTER_PLAN`
§7.3 says why — the column it would plot was **D-105**, every DOM in the product read from the wrong
path, and "a histogram makes a number authoritative, so it waits for" a live payload confirming the
fix. That reasoning stands.

**§7.3's inventory months-of-supply trend** was already recorded as unbuildable (no past month's
active count is recoverable from a feed fetched as Active/Pending/Closed). The sales-pace substitute
that shipped in its place now has no page either — **D-183**. So that §7.3 item is now neither
buildable nor rendered, and both halves are on the board.

### Untracked: a test suite for code that is not in the product

`tests/test_new_metrics.py` is 36 passing tests, and **every function it tests is defined inside the
test file**:

| function | in `apps/`? |
|---|---|
| `compute_price_cut_stats` | **no** |
| `compute_dom_distribution` | **no** |
| `comp_confidence` | **no** |
| `parse_options_meta` | **no** |

`compute_dom_distribution` is the computation §7.3's unbuilt chart needs. It has a specification, 36
green tests and **no implementation anywhere in `apps/`** — and `scripts/gen_la_verne_all_themes.py`
feeds a hand-written `dom_distribution` dict into sample data, so the shape exists in a fixture with
nothing producing it.

The defect list already notes this suite as *"fully green — at least one of these suites has been
correct and unrun for its whole life"*, which was about the runner. **What was not noticed is that it
tests nothing that ships.** 36 tests reading as coverage of four metrics the product does not compute
is the strongest form of §0.6's *an assertion with no content is worse than none, because it reads as
coverage* — filed as **D-187**.
