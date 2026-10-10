# Your page-1 photo grids against our measured fit

**For Design. One question per kind, each with the arithmetic.** Nothing here is a request to change
the design — two of the three numbers cost nothing and we have built to what fits. What we need is
whether the density was deliberate at the card size you specified.

**Measured 2026-10-10** on the `_v2` page as specified, rendered through our PDF path (PDFShift,
letter, 0.44in header and 0.89in footer reserved → **928.3px** of body), Chromium headless.
Reproduce with `scripts/measure_gallery_continuation_fit.py`.

---

## What we measured

Your package states the page-1 grid per kind and the type sizes, and **does not state the photo
height or the card height** — so the card height is an output of your spec rather than a number in
it. We set the photo from the column width at 4:3 (the common listing ratio) because something had
to reserve the box; a different ratio moves every figure below.

| | measured |
|---|---|
| page body | 928.3px |
| **page-1 band** (title · big number · pill · three stats) | **265.4px** |
| room left on page 1 | **662.9px** |
| shared gallery card (3-column) | **238.3px** = 169.5 photo + 68.8 text |
| `featured` card (2-column) | **326.8px** = 260.2 photo + 66.5 text |
| row gap | 14px |

Your continuation-pages section covers *"closed, inventory, new_listings table"* and says nothing
about a grid, so the continuation row count is ours: **three rows of the shared card fit a
continuation page with 185.3px spare**, and a fourth needs 252.3px. Two rows of the `featured` card.

---

## The three page-1 grids

| kind | you state | fits | |
|---|---|---|---|
| `new_listings_gallery` | 3×2 = 6 | **6** | fits, 172.2px spare |
| `open_houses` | 3×3 = 9 | **6** | **80.1px short** |
| `featured_listings` | 2×2 = 4 | **2** | **4.7px short** |

**The band is the reason, and it is the same change that improved every other kind.** You moved the
brand band into the body — *"The brand band on page 1 is body content below it"* — which is why the
running head now costs 40px instead of a 1.07in reservation, and why `new_listings` went from sixteen
pages to five. On a table kind the band costs page 1 and the rows reflow onto page 2 at no charge. On
a grid, **a row that does not fit is a row, not a part of one.**

---

## Question 1 — `featured_listings`: five pixels, worth a page

    cap 12 cards
    ours    page 1 holds 2, continuation 4   ->  1 + ceil((12 - 2) / 4)  =  4 pages
    yours   page 1 holds 4, continuation 4   ->  1 + ceil((12 - 4) / 4)  =  3 pages

**4.7 pixels.** One point of line-height on the 15px address, or five pixels off the photo, and 2×2
fits — and the report drops from four pages to three.

**Which five pixels do you want to give up?** We have not taken them ourselves because the 18px price
plate and 15px address are explicitly yours and distinguish this card from the listings card.

---

## Question 2 — `open_houses`: eighty pixels, worth nothing

    cap 100 cards
    ours    page 1 holds 6, continuation 9   ->  1 + ceil((100 - 6) / 9)  =  12 pages
    yours   9 everywhere                     ->      ceil(100 / 9)        =  12 pages

Measured render: `[6, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 4]`.

**The shortfall costs no pages at all.** The three cards page 1 cannot hold are absorbed by
continuation pages that were not full anyway. So this is purely a question about page 1:

> **Is nine cards on page 1 deliberate at the card size you specified, or was the card size chosen
> for the three-grid kinds and 3×3 inherited from a reference where the card was shorter?**

Our measured card is 238.3px against your 662.9px of page-1 room. **Nine cards would need a card of
about 208px** — roughly 30px shorter, which is most of the text block. We are not proposing that; we
are asking which of the two numbers is the one you meant.

If 3×3 is deliberate, the card has to lose ~30px. If the card is right, page 1 carries six and the
spec should say six — it changes nothing we render either way, and it stops the next person
re-deriving this.

---

## Question 3 — the photo ratio, which we had to choose

Your spec gives the type and not the photo. We chose **4:3 on the column width**, which makes the
photo 169.5px in a 3-column grid and 260.2px in a 2-column one — and that difference is most of why
the `featured` card is 88px taller than the shared one. **If you intended a fixed photo height
instead of a ratio, say so**: it would make the two cards much closer and would change the
`featured_listings` answer above.

---

## What we have built, and why we did not honour the stated grids

Page 1 carries **6 / 6 / 2**, because that is what fits. The alternative is putting a ninth card 80px
below the page edge, where the paginator breaks it onto page 2 as an orphan row — **a spec number
that does not fit is not a target to reach by overflowing.**

Everything else in your gallery spec is built as written: the solid white price plate at `#14161A`,
no text over photography, the `tint` missing-photo tile with the neighbourhood 22px/600 and *"Photos
coming soon"* 9.5px mono, address 13px/600, `{hood} · {specs}` at 11.5px, and `featured`'s three
stacked mini-stats.

**One addition we made and want your word on.** Your gallery card names no date, and the page it
replaced marked a listing that went live today. On `new_listings_gallery` we put `Today` / `n d ago`
in the card's third line — the slot `open_houses` already uses for its viewing time, so it is your
card structure carrying a per-kind line rather than a line invented beside it. **One conditional
removes it.** We did not want to drop the most useful fact on a new-listings report to a spec that
did not ask for it to go, but it should be your sentence either way.

---

## Still open from before

* **The 13-and-26 row counts are not simultaneously satisfiable.** 26 rows on a continuation page
  needs a row ≤34.8px; 13 of those on page 1 needs 441–476px of chrome above them. Your band spec
  computes to ~295px and ours measures 265px. We render 17 and 26 and the reports are five pages
  rather than six, so this costs nothing — but the two numbers in the package cannot both be met.
* **Four colours specified without checking them at the size they are used.** `.band-pill` at
  13px/600 takes the raw brand colour (measured 3.74:1 on teal, 2.15 on amber, 1.98 on lime) and
  `.band-label` takes `display_ink` at ≤22px, which is not large text by either WCAG definition. Both
  now take derived tokens that clear AA; the fills and the brand are unchanged. **The market surface
  is at zero baselined contrast failures** across 5,058 text runs, six brands and eight kinds.
