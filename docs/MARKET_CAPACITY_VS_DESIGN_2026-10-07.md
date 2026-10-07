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

**One extra page per report**, on the highest-volume kind. Worth their confirmation that it is
intended rather than a side effect of the row height, because it is the kind of thing that is cheap
to adjust in a design file and expensive to discover after eight kinds are wired.

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
closed.no_narrative = 15
closed.with_narrative = 11
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
