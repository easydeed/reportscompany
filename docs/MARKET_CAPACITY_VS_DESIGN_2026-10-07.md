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
inventory.no_narrative = 15
inventory.with_narrative = 11
inventory.with_trend = 5
new_listings.no_narrative = 3
new_listings.with_narrative = 2
price_bands.no_narrative = 3
price_bands.with_narrative = 2
market_snapshot.no_narrative = 3
market_snapshot.with_narrative = 3
market_snapshot.with_trend = 0
new_listings_gallery.no_narrative = 6
new_listings_gallery.with_narrative = 6
featured_listings.no_narrative = 6
featured_listings.with_narrative = 6
open_houses.no_narrative = 6
open_houses.with_narrative = 6
```

Continuation pages, measured on the same run: `closed` / `inventory` 29 · `new_listings` 8 ·
`price_bands` 6 · `market_snapshot` 6 · gallery kinds 9.

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
