# Corrections for Design — shared across both surfaces

**Read this one first.** Three mistakes appear in both handoffs. Each needs **one** answer, not
two, because fixing them separately is how two surfaces end up with two different greens.

Everything here is measured, 2026-10-05, with `scripts/measure_contrast_by_pixel.py` over
rendered output or by computing WCAG ratios directly.

---

## S1 · `#8A8E95` is not ≥4.5 on white. It is **3.29:1**.

Both READMEs say so, in almost the same words:

> property — *"Neutrals: `#14161A`, `#2A2D33`, `#5E636B`, `#8A8E95` (footer/disclaimer, ≥4.5 on
> white)"*
> market — the same neutral, the same role, in the source line

**`#5E636B` is the one that clears 4.5.** It is in both palettes already, one slot up.

One wrong number, written down twice, and nothing in either package would have caught it. So
here is every neutral both packages bless, against every surface either names. `!` fails 4.5.

| | white | `#F6F6F3` strip | `#F6F5F1` tint | `#F1F1EE` track | `#EDEDEA` inactive |
|---|---|---|---|---|---|
| ink `#14161A` | 18.11 | 16.73 | 16.60 | 16.01 | 15.44 |
| body `#2A2D33` | 13.80 | 12.75 | 12.65 | 12.20 | 11.77 |
| **muted `#5E636B`** | **6.05** | 5.58 | 5.54 | 5.34 | 5.15 |
| **faint `#8A8E95`** | **3.29 !** | 3.04 ! | 3.02 ! | 2.91 ! | 2.80 ! |
| **dash `#B9BBC1`** | **1.92 !** | 1.77 ! | 1.76 ! | 1.70 ! | 1.64 ! |

**What to change:** everywhere `#8A8E95` carries text, use `#5E636B`. On the property report
that is 28 runs in a single render — the comp cards' third line ("Lot", "6,900 sq ft", "No HOA")
— and on the market report the source line.

**The dash is a separate decision, not an oversight.** `#B9BBC1` at 1.92:1 is a deliberately
quiet mark, and a dash carries no information a reader loses by not seeing it. But it is the
*value* in a value cell, and a dash nobody can see reads as a blank — which is the opposite of
what the "Not on record" strip is for. Our own floor test fails anything under 1.5:1, so it is
not invisible; it is your call whether it should be legible. **If it stays, say so in the
package** so the auditor exclusion is recorded rather than argued about later.

---

## S2 · Small white text on a brand fill — one rule for both

Both packages handle the **large** case correctly: an 88–96px number on a dark brand passes at
the 3.0 large-text threshold. Both then put **small** text on the same fill without re-checking
it against 4.5.

| | where | measured |
|---|---|---|
| property | cover band: report kind 11px, brand name 18px, city 22px, four 11px stat labels | **7 runs** |
| market | the counts inside the price-tier bars, 11.5px | **3 runs** |

White on `primary`, across the six sample brands:

| brand | ratio | |
|---|---|---|
| violet `#7c3aed` | 5.70 | ok |
| coastal `#0e7490` | 5.36 | ok |
| demo_title `#dc2626` | 4.83 | ok |
| luxury_estates `#0d9488` | **3.74** | fails 4.5 |
| amber `#f59e0b` | **2.15** | fails |
| lime `#84cc16` | **1.98** | fails |

**On lime, the first small text a seller reads is at 1.98:1.**

The property package records this as an owner-decision exception and asks for an auditor
exclusion "scoped to the cover band element". **That scope is wrong in a way worth catching
now:** on that band the 64px street and the 30px stat values *already pass* at 3.0. Excluding
the whole band suppresses seven genuine small-text failures in order to permit lines that need
no permission.

**The rule, and it is already written in your own property README:**

> *"If a real affiliate colour makes the masthead unreadable, the remedy is a darker
> `primary_dark` fill behind the text, never moving the brand colour."*

Make that the rule rather than the fallback, on both surfaces, and apply it to any text under
24px on a `primary` **or `accent`** fill. Then the exception shrinks to the display line only,
and the auditor exclusion can be scoped to that one element honestly.

---

## S3 · The status-badge construct — one answer, and it points opposite ways today

**This is the finding neither package could have produced alone.**

The live market surface's **only** remaining contrast defect is coloured text on a same-hue
tinted chip. All 66 of its failures, nothing else. Your market handoff proposes
*"Status/delta colour: text only, never fills"* — aimed exactly at it. Your property handoff
**adds the same construct** to a surface that has no status badges at all.

| | on the chip (live market, today) | on white (your market rule) | |
|---|---|---|---|
| `#dc2626` Closed | 4.12 | **4.83** | fixed |
| `#2563eb` tier Low | 4.35 | **5.17** | fixed |
| `#16a34a` Active | 2.95 | 3.30 | **still fails** |
| `#ca8a04` Pending | 2.66 | 2.94 | **still fails** |
| `#d97706` tier High | 2.85 | 3.19 | **still fails** |

Removing the tint buys about **0.35** and fixes two of six. **The hues themselves are too light
for 4.5 on white at badge size.**

And your property palette's pills are the same construct again:

| | |
|---|---|
| Sold `#dc2626` on `#fee2e2` | **3.95** |
| Pending `#d97706` on `#fef3c7` | **2.86** |
| Active `#059669` on `#d1fae5` | **3.32** |

### The one answer

**Derive a darker ink per semantic, the way `primary_ink` is derived for the brand**, and use it
wherever a semantic colour carries text. The fill, if any, stays a tint; the text stops being
the brand-bright hue.

Darkened to the first value that clears 4.5 on white:

| semantic | as specified | ink |
|---|---|---|
| green / Active | `#16a34a` 3.30 | **`#12873d`** 4.61 |
| yellow / Pending | `#ca8a04` 2.94 | **`#9e6c03`** 4.57 |
| orange / High | `#d97706` 3.19 | **`#b26205`** 4.52 |
| your Active | `#059669` 3.77 | **`#05875f`** 4.53 |
| red / Sold | `#dc2626` 4.83 | no change needed |
| blue / Low | `#2563eb` 5.17 | no change needed |

Those are computed by darkening in HLS until the ratio clears, not chosen — treat them as the
floor, not the palette. Pick hues you like that meet it.

**And use them only where badges exist.** The market report has status and tier badges and
always has. **The property report has none**, and the pills in that handoff would import this
surface's only defect onto a surface that does not have it. Drop them there.

---

## S4 · Both packages named a template set that does not render

Not a design error — nothing in the repository marked either set as dead until this week, and
the warning document landed the same day you were working. But it cost real instructions in one
package and an architectural decision in the other, so here is the answer once.

| surface | **renders** | **does not render** |
|---|---|---|
| property | `apps/worker/src/worker/templates/property/<theme>/<theme>_report.jinja2` — 5 files, 5,767 lines | `<theme>/<theme>.jinja2` and everything in `property/_base/` — 7 files, **7,715 lines** |
| market | `apps/worker/src/worker/templates/market/market.jinja2` + `market/_base/` — 2,479 lines | `apps/web/templates/trendy-*.html` + `apps/web/app/print/[runId]/page.tsx` — the **legacy** path |

> **NUMBERS IN THIS TABLE ARE AS SENT (2026-10-05) AND HAVE MOVED SINCE.** The theme cut retired
> classic and teal and bold moved onto the shared architecture, so the property row is now 4 live
> files / 2,284 lines and 5 dead / 5,570. Left as sent, with the current figures derivable from
> `scripts/derive_template_reachability.py`, because a document already in someone else's hands is
> a record of what they were told.
>
> The `property/` qualifier on the dead column was added 2026-10-06. The table was right — it is
> per surface and lists `market/_base/` as LIVE — but the phrase "everything in `_base/`" appeared
> unqualified in eight other places, and one of them was the handover.

The property dead tree is larger than the live one, and `teal.jinja2` looks exactly as current
as `teal_report.jinja2`. The market legacy path is named LEGACY in the repository's own
comments and is never rendered for a customer PDF.

There is nothing in the dead property tree worth porting: it still says *"sold within the last
12 months"* over a query that has used six since September, and still caps comparables at four.
