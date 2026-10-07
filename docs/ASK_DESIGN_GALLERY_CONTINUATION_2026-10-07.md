# One question before we wire the market kinds

**To:** Design · **Date:** 2026-10-07 · **Re:** `RESPONSE_2026-10-06.md`, continuation pages

Your per-kind spec gives the page-1 grids — `new_listings_gallery` 3×2, `open_houses` 3×3,
`featured_listings` 2×2 — and the continuation-pages section covers the three table kinds (`closed`,
`inventory`, `new_listings`). So for the gallery kinds we know what page 1 holds and not what page 2
holds.

**Is a gallery continuation page a 3×3 of the same card, or the kind's own page-1 grid repeated?**

It matters more than it sounds, because the two readings diverge badly on the two kinds that already
carry the most pages on the surface. Measured on our paginator (Chromium, your margins, 0.44in
header and 0.89in footer reserved):

| if a gallery continuation page carries… | `new_listings_gallery` at 120 | `open_houses` at 100 |
|---|---|---|
| **9** — a 3×3 of the same card | 14 pages — **unchanged from ours** | 12 pages — **unchanged** |
| **6** — the page-1 grid repeated | **20 pages**, up from 14 | **17 pages**, up from 12 |

Ours is 9 on both today.

## Why we are asking rather than picking the safe one

Across the three kinds you did specify row counts for, **your layout saves us eight pages**:

| type | our pages | your pages |
|---|---|---|
| `closed` | 5 | 6 |
| `inventory` | 5 | 6 |
| `new_listings` | **16** | **6** |
| | **26** | **18** |

`new_listings` is the whole of it. It has been rendering on our *analytics* layout — 3 rows on page
1, 8 on continuation — and your table layout at 13 and 26 takes it to six. Two pages given up on
`closed` and `inventory`, ten bought back on one kind.

If we inferred the 3×2 reading for the galleries, that would add **eleven pages across two kinds**
and hand most of the saving straight back — and nobody would see it until the PDFs rendered. Which
is why it is a question and not an assumption.

**Either answer is one line and we will build to it.** If the card itself changes size between the
two grids, say that instead and we will measure it rather than guess.

---

*Everything above is re-derived on each run by `scripts/measure_market_pagination.py` and checked
against the pinned capacity by `tests/test_market_capacity_doc_is_current.py` — the numbers in this
document cannot go stale without a test failing. Full working:
`docs/MARKET_CAPACITY_VS_DESIGN_2026-10-07.md`.*
