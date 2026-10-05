# To Claude Design — corrections, and one question that blocks the market side

**2026-10-05.** Three documents accompany this one, in `docs/design-corrections/`:

| | |
|---|---|
| `00-SHARED.md` | **read first** — three mistakes that appear in both packages, with one answer each |
| `01-PROPERTY.md` | what the property handoff got right, then the corrections |
| `02-MARKET.md` | the same, plus one decision that is yours to take |

**Both packages are correction lists, not redos.** The property design's judgement is sound
throughout — we are adopting two of its ideas over our own implementations. The market design is
sound too, with one architectural reversal that needs a knowing choice rather than a fix.

Everything in those documents is measured. Where we give a number, the command that produced it
is named. Doing it that way caught two numbers in **our** defect list that were wrong, and one we
had already sent you — see the last section.

---

## 1 · The question that blocks the market work

**Your market handoff covers seven kinds. The live build has eight report types across five
layouts, and your seven do not map onto them 1:1.**

```
LAYOUT_MAP (apps/worker/src/worker/market_builder.py:100)

  gallery           new_listings_gallery · featured_listings · open_houses
  market_narrative  market_snapshot
  closed_inventory  closed · inventory
  pricebands        price_bands
  analytics         new_listings
```

Your kinds: snapshot · listings · closed · inventory · bands · featured · gallery.

Six map cleanly. **The seventh does not**, and the collision is this:

| live type | layout | what it is | PDF title today | title in the wizard |
|---|---|---|---|---|
| `new_listings` | **analytics** | all new listings in the window, as a table | **"New Listings"** | "New Listings" |
| `new_listings_gallery` | **gallery** | the same listings, as a photo grid | **"New Listings"** | "New Listings Gallery" |

They are **two separately selectable products with two different layouts and the same name on
the PDF.** Your "listings" kind is a 3 × 2 photo grid, which is the gallery one; nothing in your
seven is the table one.

Three ways to resolve it, and the choice is a design question rather than an implementation
detail:

1. **Two kinds** — a table variant and a grid variant of the same report, which is what exists.
2. **One kind with a density switch** — same header and stats, body renders as grid or table. Our
   preference, because the header and stats are identical in your spec already.
3. **One kind, grid only** — drop the table variant. This is a product deletion, not a design
   decision; it needs Jerry.

**We cannot start the market work until this lands**, because it determines whether the template
takes seven branches or eight, and whether anything is being removed from the product.

While you are there: the naming collision is ours and it is real — the branding page calls
`new_listings_gallery` "New Listings" and the schedule wizard calls it "New Listings Gallery",
so a customer picking from two different screens gets two different names for the same report.
If you have a view on what the two should be called, we will take it.

---

## 2 · One thing we are adopting over our own work

Your property page 4 — **"Each sale", one bar row per comparable, on the same page as the
range** — is better than what we built. We had put the full comparable list on a continuation
page; yours puts the evidence beside the number it supports.

Adopting it removes the only page in our set whose presence depends on the data, and takes a
15-comp report from eight pages to seven. We will measure that it still fits at fifteen rows
before committing, with the same browser fit gate that caught a 390px overflow on our version.

Saying so explicitly because the rest of this package is corrections, and that is not the
balance of the two handoffs.

---

## 3 · One decision, not a correction

The market running head. `02-MARKET.md` §2 has it in full with the measurement attached, but in
short: it exists because PDFShift accepts mismatched `header.start_at` / `footer.start_at` with
an HTTP 200 and silently applies `max()` to both, and moving the masthead into the body to work
around that **recovered 1.07in on every page** — `closed` went 6 pages to 5, `new_listings` 18 to
16.

Your handoff removes it. Both branches are buildable and we will build whichever you choose.
**Keeping it is less work than what you specified**, because the header slot already emits per
page and your strip would otherwise need emitting per chunk from the table partial.

What we need is the choice knowingly made, not a fix.

---

## 4 · The thing to take away from all of it

`#8A8E95` is declared *"≥4.5 on white"* in **both** READMEs, in almost the same words. It is
**3.29:1**. `#5E636B` is the colour that clears 4.5, at 6.05, and it is already one slot up in
both palettes.

One wrong number, written down twice, is the clearest sign the two packages came from one habit
rather than two measurements — so `00-SHARED.md` gives you a measured table of **every** neutral
either package blesses against **every** surface either names, rather than correcting the one
value. Use the table; do not trust an adjective, including ours.

---

## 5 · Where we were wrong

**We gave you a bad number.** Your structural note says the theme-literal deletion *"removes 5 of
the 6 values behind **132**/213 contrast failures"*. 132 was wrong in our defect list when you
read it — the role table had been assembled by eye and its own rows summed to 134. Re-derived
from the measurement, six colours carry **146 of 213**. It strengthens your argument rather than
weakening it, and the error was ours.

**And the bigger one.** Both packages were written against template files that do not render:
7,715 lines of dead property templates, and a legacy market set that the code itself calls
LEGACY. Nothing in the repository marked either as dead until the week you were working, and the
document that does was committed the same day. That is why two of the three things your market
handoff reports removing — the violet→coral gradient and the red "PDF" badge — were never in a
customer's PDF.

**The live files, so this does not happen again:**

```
property   apps/worker/src/worker/templates/property/<theme>/<theme>_report.jinja2    (5 files)
market     apps/worker/src/worker/templates/market/market.jinja2 + market/_base/
```

Everything else under `templates/property/_base/`, every `<theme>/<theme>.jinja2`, and all of
`apps/web/templates/trendy-*.html` renders nowhere.
