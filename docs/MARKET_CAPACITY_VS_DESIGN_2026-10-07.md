# Design's market row counts, against what our paginator actually fits

**Measured 2026-10-07**, before any market wiring, because Design's package asks for it directly:
*"Re-measure the row counts in the browser fit gate for this layout and pin them."*

Method: `scripts/measure_market_pagination.py`, which reproduces the production path
(`MarketReportBuilder` → `render_html` + header/footer → `render_pdf(html_content=…)`) in Chromium's
own paginator with PDFShift's reserved space — 0.44in top, 0.89in bottom, so the body flows in
9.67in. 120 listings.

## 1 · What Design specifies, and what we fit

| | Design's spec | ours, no narrative | ours, as production renders |
|---|---|---|---|
| `closed` page 1 | **13** | **15** | 11 |
| `closed` continuation | **26** | **29** | 29 |
| `new_listings` (table) page 1 | 13 | 3 | 2 |

**The comparison that matters is the middle column.** Design removes the AI narrative from the table
and gallery kinds — *"this design renders no AI narrative on table or gallery kinds, so there is no
narrative variant. Page-1 capacity is one state per kind"* — so their 13 should be read against our
no-narrative 15, not against the 11 production renders today.

So **Design's layout is less dense than ours in both positions**: two fewer rows on page 1, three
fewer on continuation. Their band and table rows are taller. Nothing about that is wrong; it is a
deliberate choice about air, and it has a page cost.

## 2 · The page cost, computed from their own formula

Design gives `P = ceil((N − 13) / 26) + 1`. For a 118-row `closed` report — the figure in their own
per-kind table — against ours:

| | pages for N=118 |
|---|---|
| Design's spec (13 + 26/page) | **6** |
| ours, no narrative (15 + 29/page) | **5** |
| **the built `_v2` page (17 + 26/page)** | **5** |

**UPDATED 2026-10-07, AFTER BUILDING IT.** The +1 was an artefact of their page-1 figure, not of
their density. Built to their continuation number exactly — **26 rows, measured** — `closed` renders
**5 pages for 120 listings**, the same as before. Their layout does not cost a page on this kind.

**And their two numbers do not agree with each other.** 26 continuation rows needs a row of at most
`(928 − 22) / 26 = 34.8px`; 13 page-1 rows at that height needs a page-1 chrome of **441–476px**,
while their own band spec computes to ~295px and ours measures **265px**. No single row height
satisfies both against their band: hitting 26 puts page 1 at 17, and hitting 13 would put the
continuation at 19 and cost two pages per report. Resolved by hitting the continuation number —
that is what drives page count — and 17 on page 1 is *more* rows than specified, which costs the
customer nothing.

But `closed` alone is the wrong basis for the decision, so:

## 2a · The same arithmetic on all eight kinds, which reverses the headline

Each type at its own `PDF_CONFIG` cap (a `market_snapshot` never renders 120 listings — its cap is
9), ours measured no-narrative, theirs from their per-kind spec:

| type | cap | N | our pages | their pages | delta |
|---|---|---|---|---|---|
| `closed` | 200 | 120 | 5 | **6** | **+1** |
| `inventory` | 200 | 120 | 5 | **6** | **+1** |
| `new_listings` | 200 | 120 | **16** | **6** | **−10** |
| `new_listings_gallery` | 200 | 120 | 14 | 3×2 grid, continuation not stated | — |
| `open_houses` | 100 | 100 | 12 | 3×3 grid, continuation not stated | — |
| `featured_listings` | 12 | 12 | 2 | 2×2 grid, one page | — |
| `market_snapshot` | 9 | 9 | 2 | one page, no listings table | — |
| `price_bands` | 8 | 8 | 2 | one page, 7 fixed band rows | — |
| **the three stated kinds** | | | **26** | **18** | **−8** |

**The inputs this forecast used**, recorded with it so the arithmetic stays checkable after the
build changes them. Without this the table could only be validated against live capacity, which is
exactly how a forecast stops being one:

```forecast
closed.page_1 = 15
closed.continuation = 29
inventory.page_1 = 15
inventory.continuation = 29
new_listings.page_1 = 3
new_listings.continuation = 8
price_bands.page_1 = 3
price_bands.continuation = 6
featured_listings.page_1 = 6
featured_listings.continuation = 9
new_listings_gallery.page_1 = 6
new_listings_gallery.continuation = 9
open_houses.page_1 = 6
open_houses.continuation = 9
```

**`new_listings` is the finding.** It runs on our `analytics` layout today at 3 rows on page 1 and 8
on continuation — sixteen pages for 120 listings. Design puts it on the **table** layout at 13 and
26, which is six. The two pages their density costs on `closed` and `inventory` are bought back four
times over on one kind.

So the trade is not "a page per report". Across the three kinds Design specifies row counts for, it
is **eight pages saved**, and the two regressions are on the kinds whose current layout was already
the dense one.

**What we still need from them** is the continuation capacity for the two gallery kinds. Their
package states the grids (3×2, 3×3) but not what a continuation page carries, and those are the two
kinds where our current 14 and 12 pages are the largest absolute numbers on the surface. A 3×3 grid
on continuation would be nine per page against our nine — no change; a 3×2 would be fourteen pages
becoming twenty.

Worth their confirmation that the `closed` row height is intended rather than a side effect, because
it is cheap to adjust in a design file and expensive to discover after eight kinds are wired.

## 3 · The improvement their design brings, which is real

Page 1 is currently **not a fixed capacity**. Measured on the same fixture:

| `closed` page 1 | rows |
|---|---|
| with the narrative | 11 |
| without it | **15** |
| continuation, either way | 29 |

A four-row swing driven by model-generated prose of no fixed length. Removing the narrative from the
table kinds makes page-1 capacity **deterministic**, which is a property our current build does not
have and cannot be given without the same decision. That is the strongest argument in their layout
and it is worth saying back to them.

`market_snapshot` is the extreme case: `with_trend` fits **zero** listings on page 1. Design's
snapshot carries no listings table at all, which resolves it rather than working around it.

## 4 · What was stale, and what was not

`PAGE_1_CAPACITY` in `apps/worker/tests/test_narrative_box.py` is **current** — it matches this
measurement exactly, because it is re-pinned from `--emit-capacity` rather than retyped, which is
what that mode exists for.

The **docstring of the measurement script was not**. It stated "13 rows on page 1 and 25 on page 2"
and a one-row narrative effect; the harness now produces 11 then 29, and a four-row effect. §7.1's
running-head change recovered 1.07in of every page and the continuation pages took the gain. The
derived value was maintained and the prose beside it was not — the same shape as the cap table in
`sample_report_data.py` (D-173), in the file whose own docstring argues for derivation over
transcription.

Corrected, with its date attached.

## 5 · Pinned for the wiring

These are the numbers the first market kind gets built against, and the ones to re-measure after:

One line per `(kind, state)`, in a form a test can parse — `str(rows) in text`
matched `17` inside `D-173` on the first attempt, which is this project's
substring-is-not-a-construct defect in the gate written to stop a document going
stale.

```capacity
closed.no_narrative = 17
closed.with_narrative = 17
inventory.no_narrative = 17
inventory.with_narrative = 17
new_listings.no_narrative = 17
new_listings.with_narrative = 17
price_bands.no_narrative = 0
price_bands.with_narrative = 0
market_snapshot.no_narrative = 3
market_snapshot.with_narrative = 3
market_snapshot.with_trend = 0
new_listings_gallery.no_narrative = 6
new_listings_gallery.with_narrative = 6
featured_listings.no_narrative = 2
featured_listings.with_narrative = 2
open_houses.no_narrative = 6
open_houses.with_narrative = 6
```

Continuation pages, measured on the same run: `closed` / `inventory` 29 · `new_listings` 8 ·
`price_bands` 6 · `market_snapshot` 6 · gallery kinds 9.

**`inventory`'s third state is gone, not equalised.** It read
`no_narrative 15 · with_narrative 11 · with_trend 5` — three capacities, because the page could
carry a narrative box, a sales-pace chart, both or neither. Design's `_v2` page has neither slot, so
there is one number. **The pace chart is not relocated, it is removed**: `inventory` was the only
report type drawing the count series and `MarketReportBuilder.TREND_SERIES` no longer lists it, which
also stops `tasks.py` paying for a twelve-month closings fetch it cannot use (D-113's shape,
inverted). That is a loss of information and it is Design's call, not a cleanup — see §8.

**`price_bands` reads 0 in both narrative states and that is not a regression.** Its `_v2` body is
the band table — five columns of price-band aggregates — and it carries **no listings table at all**,
so the number of listings that fit on page 1 is zero because none render. The report is one page and
holds every band. The figure is pinned at 0 rather than removed so that a listings table appearing
on this kind is a change somebody has to write down; `test_market_layout_map.py`'s
`RENDERED_DESPITE_CAP` records the same fact from the other side, that
`PDF_CONFIG["price_bands"]["cap"] = 8` now governs nothing that renders.

A kind whose rendered capacity moves away from these after wiring has changed the layout's density,
which is a reviewable fact rather than a surprise.


---

## 6 · Gallery continuation: measured, and it is three rows

Design's spec left this unstated — the per-kind table gives the page-1 grids (`new_listings_gallery`
3×2, `open_houses` 3×3 "same card as listings") and the continuation-pages section covers only the
three table kinds. The two readings differed by **eleven pages across those two kinds**, so it was
worth settling before wiring.

**Settled by measuring, not by asking.** A market PDF page has 928px of body
(11in − 0.44in header − 0.89in footer). The card is **258px**, the row gap **8px**:

| | px |
|---|---|
| three rows | **790** |
| headroom | **138** — 0.53 of a card |
| four rows | 1,056 — 128px over |

**Three rows fit; four cannot.** Our build already does 9 per continuation page on both kinds, and
Design's 3×2 on page 1 is the masthead's cost rather than a grid decision — their own spec puts nine
of the same card on `open_houses` page 1, which carries the same fixed band. So the two numbers were
never in conflict and the gallery kinds stay at 14 and 12 pages.

The card height is invariant to content (258px at 3 listings and at 40) and the photo reserves its
180px in CSS, so a headless render without photos is faithful. Full working, including why Design's
own reference file could not be measured in this container:
`docs/GALLERY_CONTINUATION_MEASURED_2026-10-07.md`.


---

## 7 · Built, measured: the two wired kinds

**§1, §2 and §2a above are the PREDICTION and are left exactly as they were taken.** Editing a
forecast after the result is in destroys the only thing it was for — this section is worth reading
because it can be compared with that one. Where they differ, the forecast was wrong and the
difference is the finding.

| kind | before | built | Design's formula said |
|---|---|---|---|
| `closed` | 5 | **5** | 6 |
| `new_listings` | **16** | **5** | 6 |
| `price_bands` | 2 | **1** | — (their package states no row counts for it) |
| `inventory` | 5 | **5** | 6 |
| `new_listings_gallery` | 14 | **14** | — (no continuation row count given) |
| `open_houses` | 12 | **12** | — |
| `featured_listings` | 2 | **4** | — |
| | **56** | **46** | 18 for the three kinds they gave rows for |

**Ten pages saved across seven kinds**, and **the galleries cost two** — all of them on
`featured_listings`, which goes 2 → 4. See §8 for the measurement.

Previously stated as twelve saved across four kinds; that was true of the four table-and-bands kinds
and is superseded by the galleries landing. **Twelve pages saved across four kinds**, against the eight their arithmetic predicted across three
— because `closed` and `new_listings` both land on 5 rather than 6, and `price_bands` was not in
their forecast at all.

**`inventory` saves nothing and closes no contrast failure, and both were known before it was
built.** It is `closed`'s twin — the same layout, the same table, 5 pages before and 5 after — and
the market contrast baseline was already at zero, so there was nothing left for it to close. Its
payoff is that the surface becomes uniform: four of eight kinds on one page now, and the three that
remain are the galleries and `market_snapshot`. Saying so in advance is the same discipline that
said `closed` would close zero contrast rows, and for the same reason — a kind whose payoff is
consistency should be chosen on that argument and not discovered to have no other.

`price_bands` going 2 → 1 is the cheapest of the three and the forecast had it at 2 → 2. The saving
is the stat cards and the SVG chart coming out: the `_v2` body is one five-column table of the same
six bands, and six rows at 48px plus the band fit inside one page where a hero card, a six-card stat
row, an SVG bar chart and a narrative box did not.

`new_listings` is the whole of it. It had been rendering on the `analytics` layout at 3 rows on page
1 and 8 on continuation; on Design's table it is 17 and 26.

And page-1 capacity is now **one number for both** — `17` in every narrative state — where the old
page gave 15/11 and 3/2. That is the determinism their design buys, measured on two kinds rather
than argued from one.

### The contrast payoff landed exactly where the heuristic said

Predicted before any template was written: `new_listings` 3 pairings, `closed` 0. Measured:

| kind | baseline rows closed |
|---|---|
| `closed` | **0** |
| `new_listings` | **3** — the tier badges, `#d97706 on #fef1db`, `#2563eb on #e2ecfe`, `#16a34a on #def6e7` |

Design's spec removes the construct ("no chips, no tinted fills behind semantic text"), so the rows
had nothing left to fail on. The baseline went **61 → 58**, and `market__new_listings` is gone from
it entirely. The only market rows left are `price_bands`' three badges — which is the remaining
contrast payoff on this surface, and it is the next kind's.


---

## 8 · The galleries, re-measured against the new architecture

**#156's measurement was taken against the LEGACY gallery page and is superseded.** It said: card
258px, row gap 8px, three rows fit a continuation page with **138px to spare**. Re-measured
2026-10-10 because the page under it was replaced — and a fit measured against a page that no longer
renders describes nothing, which is the contrast-baseline rule applied to geometry.

**The page box did not move.** `pdf_engine.py`'s 0.44in header and 0.89in footer reserve are
untouched since PR #101, so the body is still **928.3px**. What changed is the card: Design moves the
price onto the photo (the info block loses a 23px line) and sizes the photo from the column width
instead of a fixed 180px.

### The continuation page

| | legacy | `_v2` | moved |
|---|---|---|---|
| shared gallery card (3-col) | 258.0 | **238.3** = 169.5 photo + 68.8 text | −19.7 |
| row gap | 8 | 14 | +6 |
| three rows | 790.0 | **743.0** | −47.0 |
| headroom after three rows | 138.0 | **185.3** | **+47.3** |
| a fourth row would need | 266 | **252.3** | — |

**Three rows still fit and 3×3 holds, with more room than before.** A fourth row is 67px short, so
the answer is not close to flipping — and it is robust to the gap: at the legacy 8px gap three rows
are 730.9px and a fourth still does not fit.

`featured_listings`' own card is **326.8px** (260.2 photo + 66.5 text) in a 2-column grid, so its
continuation page carries **two rows, four cards**.

### Design's page-1 grids do not fit under Design's band

The band measures **265.4px**, leaving **662.9px** above the footer.

| kind | Design's page 1 | measured | verdict |
|---|---|---|---|
| `new_listings_gallery` | 3×2 = 6 | **6** | fits, 172.2px spare |
| `open_houses` | 3×3 = 9 | **6** | **80.1px short** |
| `featured_listings` | 2×2 = 4 | **2** | **4.7px short** |

**This is the third instance of their stated numbers not being self-consistent**, after the 13-and-26
row counts and the gradient contradiction.

### What each shortfall actually costs, which is not the same as how big it is

| kind | short by | pages ours | pages if their grid fitted | cost |
|---|---|---|---|---|
| `open_houses` (cap 100) | **80.1px** | 12 | 12 | **nothing** |
| `featured_listings` (cap 12) | **4.7px** | 4 | 3 | **one page per report** |

**The bigger shortfall is the free one.** `open_houses` renders `[6, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 4]`
— 100 cards over 12 pages. Design's 3×3 everywhere would be `ceil(100 / 9)` = **also 12**, because
the three cards page 1 cannot hold are absorbed by continuation pages that are not full. The
shortfall moves cards between pages without adding one.

`featured_listings` is the opposite: 4.7 pixels, and it costs a page on every report. At cap 12,
`1 + ceil((12 − 2) / 4)` = 4 pages; with 2×2 on page 1 it is `1 + ceil((12 − 4) / 4)` = **3**.

So the ask to Design is two different asks, and conflating them by shortfall size would have put the
effort on the wrong one:

* **`featured_listings`** — five pixels, worth a page. A line-height point or a slightly shorter
  photo.
* **`open_houses`** — eighty pixels, worth nothing in pages. Purely a question about **page-1
  density**: is nine cards at that card size deliberate, or was the card size chosen for the
  three-grid kinds and the 3×3 inherited from a sample that had a shorter card? Not ours to decide
  either way.

### What the galleries cost, and why it is one kind

| kind | before | built |
|---|---|---|
| `new_listings_gallery` | 14 | **14** |
| `open_houses` | 12 | **12** |
| `featured_listings` | 2 | **4** |

Two of the three are unchanged. `featured_listings` doubles because Design's featured card is 88px
taller than the shared one — 18px price plate, 15px address, and a 349px-wide column whose 4:3 photo
is 260px tall. **That is their design decision and it is recorded rather than worked around**; the
4.7px above is the cheapest way back to 3.
