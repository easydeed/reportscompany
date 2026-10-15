# Where a trend chart goes on your `_v2` page

**For Design. One question, with the arithmetic.** Nothing here asks you to change the page. We have
built to what fits and we are not proposing a region your package does not have — what we need is
whether the page-1 band is deliberate at the height it measures, because that height is what decides
whether a chart costs a page.

**Measured 2026-10-12/14** on the `_v2` page as specified, through our PDF path (PDFShift, letter,
0.44in header and 0.89in footer reserved → **928.3px** of body), Chromium headless. The page counts
are recomputed from the live row capacity rather than quoted, and
`tests/test_trend_chart_relay_is_current.py` fails if either drifts.

---

## 1 · What the specification asks for, and what renders today

Our §7.3 specifies **two** charts: a twelve-month median/pace trend and the price-band distribution.

| chart | where it lives today |
|---|---|
| **band distribution** | **renders** — as your `_v2` bands body, a CSS bar per band rather than our old inline SVG. Same comparison, same rules on legends and labels. No question here. |
| **median trend** | renders on `market_snapshot`, which is the one kind **not yet on your page** |
| **pace trend** | **does not render.** It was `inventory`'s, and your `_v2` page for `inventory` is the band over the listings table with no chart. |

So the question is not "may we add a chart" — it is where a chart can go on your page at all.

---

## 2 · Your page is a band and a body, and there is no third region

| body | what a chart would displace |
|---|---|
| table — `closed`, `inventory`, `new_listings` | table rows |
| bands — `price_bands` | band rows, and the body already *is* the distribution |
| grid — the three galleries | a whole card row; cards do not reflow |
| **none** — `market_snapshot`, once wired | **nothing** |

Two honest placements: **above the body on page 1**, or **as the body** on a kind that has no
listings. There is no third, and we would rather not invent one: we have already had to put one line
of our own into your bands body — the price-band disclosure, which says the boundaries may shift
between reports — and adding a region your package does not describe is how two documents start
disagreeing about what the page is.

---

## 3 · The arithmetic on page 1

| | measured |
|---|---|
| page body | 928.3px |
| **your page-1 band** (title · big number · pill · three stats) | **265.4px** |
| room left for the body | **662.9px** |
| table header · showing line | 22px · 23px |
| table row pitch | **34.7px** |
| our trend chart, rendered | **179.5px** (150 SVG + 13.5 note + 16 padding) |

    page-1 rows today      (662.9 − 22 − 23)         / 34.7  =  17
    page-1 rows with chart (662.9 − 22 − 23 − 179.5)  / 34.7  =  12

**A chart costs five rows on page 1, and five rows costs one page on each table kind** at the 120
listings we size for:

| kind | pages now | with a page-1 chart |
|---|---|---|
| `closed` | 5 | **6** |
| `inventory` | 5 | **6** |
| `new_listings` | 5 | **6** |
| **three table kinds** | **15** | **18** |

Continuation pages are unaffected — a chart appears once, and a continuation page carries 26 rows
either way.

---

## 4 · The part that is about the band rather than the chart

**The chart is not too tall; page 1 is already full.** Your band is 265.4px of a 928.3px page —
**28.6% before a single listing row.** Hold everything else and ask what band height would make the
chart free:

    page-1 rows with chart  =  (928.3 − band − 45 − 179.5) / 34.7
    five pages needs 16 rows on page 1
    →  band ≤ 148.6px

**The band would have to come down by 117px — 265.4 to 148.6 — for a trend chart to cost nothing.**
That is not a request; it is the number that turns "can we have a chart" into a trade you can weigh.
A band at its current height and a chart on page 1 are three extra pages across three kinds.

And the free option, for completeness: **`market_snapshot` has no listings table**, so a chart there
displaces nothing. It already carries the median trend, and when that kind moves to your page we
intend to keep it — your snapshot body is three row-blocks against 483.4px once a chart is placed,
which is tight, so we expect it to be a two-page kind either way and it is two pages today.

---

## 5 · What we are asking

1. **Is the 265.4px band deliberate at that height?** If it is, we will take the answer in §3 as the
   cost and stop asking.
2. **If so: is one extra page on each of `closed`, `inventory` and `new_listings` acceptable for a
   trend chart** — 18 pages against 15 — or should the trend stay on `market_snapshot` only, where it
   is free?

We are not blocked on this. `market_snapshot` keeps its chart whatever you answer, and the pace
series stays out of the three table kinds until you do.

---

**Same form as `GALLERY_GRID_FOR_DESIGN_2026-10-10.md`**, which asked about the page-1 grids and the
`open_houses` 3×3: the arithmetic first, one question, and no proposal.
