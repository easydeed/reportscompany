# A gallery continuation page holds three rows. Measured, not asked.

> ## RE-MEASURED 2026-10-10 AGAINST THE NEW ARCHITECTURE. The answer held; the numbers moved.
>
> Everything below was measured against the **legacy** gallery page. The three gallery kinds moved
> onto Design's `_v2` page on 2026-10-10, and **a fit measured against a page that no longer renders
> describes nothing** — the contrast-baseline rule applied to geometry. So it was taken again rather
> than carried forward.
>
> | | legacy (below) | `_v2` | moved |
> |---|---|---|---|
> | card | 258.0 | **238.3** | −19.7 |
> | row gap | 8 | 14 | +6 |
> | three rows | 790.0 | **743.0** | −47.0 |
> | **headroom** | **138.0** | **185.3** | **+47.3** |
> | a fourth row needs | 266 | 252.3 | — |
>
> **Three rows still fit, four still cannot, and it is less tight than it was** — 67px short of a
> fourth rather than 128px, but in the same direction and not near flipping. Robust to the gap: at
> the legacy 8px gap the `_v2` card gives 730.9px for three rows and a fourth still does not fit.
>
> The page BOX did not change — `pdf_engine.py`'s 0.44in/0.89in reserve is untouched since PR #101,
> so the body is still 928.3px. What changed is the card: Design moves the price onto the photo (the
> info block loses a 23px line) and sizes the photo from the column width instead of a fixed 180px.
>
> **What this re-measurement also found**, and could only have found by being retaken: Design's
> stated page-1 grids do not fit under Design's own band. The band is 265.4px, leaving 662.9px —
> `open_houses`' 3×3 is **80.1px short** and `featured_listings`' 2×2 is **4.7px short**. Full
> working in §8 of `MARKET_CAPACITY_VS_DESIGN_2026-10-07.md`.
>
> `featured_listings` has its own, taller card (326.8px) and carries **two rows** on a continuation
> page, not three. The section below is about the shared gallery card only; it never covered that one.

**2026-10-07.** Design's per-kind spec gives `new_listings_gallery` a **3×2** photo grid and
`open_houses` a **3×3** grid described as "same card as listings", and their continuation-pages
section covers only the three table kinds. So what a gallery continuation page carries was unstated,
and the two readings differ by **eleven pages across those two kinds**.

Jerry's call: measure it rather than spend a fourth round asking Design for a number we can take
ourselves — *"page 1's 3×2 may simply be the masthead's cost rather than a design choice."*

## The answer: 3×3 fits, with half a card to spare

| | px |
|---|---|
| body height of a market PDF page (11in − 0.44in header − 0.89in footer) | **928** |
| card height | **258** |
| row gap | **8** |
| three rows (`3 × 258 + 2 × 8`) | **790** |
| **headroom after three rows** | **138** — 0.53 of a card |
| four rows (`4 × 258 + 3 × 8`) | 1,056 — **128px over** |

So **three rows fit and four cannot**, and the margin is not tight: 138px spare is 46px per row,
roughly three extra text lines per card. Our current build already renders 9 per continuation page
on both kinds, and this is why.

**Design's 3×2 on page 1 is the masthead's cost, not a grid decision.** Their own spec puts nine of
the same card on `open_houses` page 1 — which carries the same fixed band — so the two numbers were
never in conflict. Nothing changes, and the question does not need to go to Design.

## Why the measurement is trustworthy

**The card height does not depend on content.** Measured at 3, 6, 9, 12, 24 and 40 listings, the
card is **258px every time** while the grid grows from 273px to 3,732px:

| listings | cards | grid px | card px |
|---|---|---|---|
| 3 | 3 | 273 | **258** |
| 6 | 6 | 539 | **258** |
| 9 | 9 | 805 | **258** |
| 12 | 12 | 1,071 | **258** |
| 24 | 24 | 2,136 | **258** |
| 40 | 40 | 3,732 | **258** |

That test was run because `.gallery-grid` carries `flex: 1`, which *could* have meant the rows
stretched to fill the page — in which case "how many fit" would have been a template decision
dressed up as geometry, and Design's 3×2 would have been a real design choice. It does not stretch.

**And the photo reserves its height in CSS, so a headless render is faithful.**
`.listing-photo { width: 100%; height: 180px }` — a fixed box with a `background-image`. The card is
180px of photo plus a 78px info block. Remote photos do not load in this container, and it does not
matter: the 180px is reserved either way, which is the only reason this measurement can be believed
without them.

The same card measures 258px on all three gallery kinds (`new_listings_gallery`, `open_houses`,
`featured_listings`) despite different badge text and different info lines — measured separately,
because 9 on one kind does not imply 9 on another.

## What was not measurable, and why it was abandoned rather than forced

The first attempt drove Design's own `Report Page.dc.html` in Chromium through
`window.__dcSetProps`, which would have measured **their** card rather than ours. It cannot work
here: the file loads React from unpkg and Geist from Google Fonts, and the browser refuses both with
`ERR_CERT_AUTHORITY_INVALID` because Chromium does not trust the agent proxy's CA. The remedy for
that is disabling certificate verification, which is not on the table.

Vendoring React, two font families and the photos would have measured a document assembled
differently from the one Design looks at — the fixture-is-not-production shape with extra steps. So
the measurement is of **our** render, which is the geometry that actually governs the PDF: the PDF
comes from `MarketReportBuilder`'s HTML through PDFShift, with our fonts and our card.

**The one remaining variable is Design's type.** Their spec gives the card's text sizes — address
13px/600, "{hood} · {specs}" 11.5px, price plate 15px/700 — and not the card's height. Ours renders
at 9/11/14/23px in a 78px info block. If their text block is taller than ours it eats into the
138px, and it has 46px per row to eat before a third row stops fitting. That is a wide margin, but
it is the thing to re-measure once the kind is wired rather than something to assume now.

## Method

`scripts/measure_gallery_continuation_fit.py`, Chromium at letter width, the real card from
`MarketReportBuilder`, grid and card found by **computed style** rather than class name so a rename
returns an error instead of zero rows. Not a gate — it needs a browser and CI has none, the same
reason `measure_market_pagination.py` is a script.
