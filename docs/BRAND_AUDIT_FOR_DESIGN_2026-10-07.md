# Your colour rule generalised to four brands it had never seen

**To:** Design · **Date:** 2026-10-07 · **Re:** `RESPONSE_2026-10-06.md`, colour roles

**`display_ink` holds on brands that were not in your sample.** That is the finding, and it is the
reason we are sending measurements rather than a verdict.

We adopted the rule, wired it on the property cover, and then measured it against the six brand
presets the product actually offers. **Four of those six were not in your sample.** All four clear
your stated thresholds, with the token resolving correctly on each:

| brand not in your sample | hex | white on it | `display_ink` resolves to | clears |
|---|---|---|---|---|
| Indigo | `#4F46E5` | 6.29 | `#ffffff` | 3.0 and 4.5 |
| Ocean | `#0EA5E9` | 2.77 | `#14151a` | 3.0 and 4.5 |
| Forest | `#059669` | 3.77 | `#ffffff` | 3.0; sub-24px falls to `#14151a` at 4.84 |
| Midnight | `#1E293B` | 14.63 | `#ffffff` | 3.0 and 4.5 |

**A stated bound could not have done that.** "White clears 3.0 on the sample brands" is a fact about
six hexes; `contrast(white, primary) >= 3.0 ? white : on_primary` is a fact about any hex, and it
came out right on four we never discussed. Third round for this class of claim and the first where
the method arrived rather than a corrected number.

Your own six also reproduce exactly against our `themes.contrast` — red 4.83, teal 3.74, cyan 5.36,
violet 5.70, amber 2.15, lime 1.98.

---

## 1 · The two sets are two populations with a two-brand overlap

Your rule was measured on six sample brands. The product's brand picker offers six presets
(`apps/web/app/app/settings/branding/page.tsx:51`, duplicated in the company page). **Four of each
six are not in the other.**

| | hex | in your sample | in our picker |
|---|---|---|---|
| Crimson / red | `#DC2626` | yes | yes |
| Royal / violet | `#7C3AED` | yes | yes |
| Indigo | `#4F46E5` | — | **yes** |
| Ocean | `#0EA5E9` | — | **yes** |
| Forest | `#059669` | — | **yes** |
| Midnight | `#1E293B` | — | **yes** |
| teal | `#0D9488` | **yes** | — |
| cyan | `#0E7490` | **yes** | — |
| amber | `#F59E0B` | **yes** | — |
| lime | `#84CC16` | **yes** | — |

`#4F46E5` is the platform default accent and `#1E293B` is a near-black; neither behaves like the
mid-saturation hues the sample is made of. `#0D9488` is one affiliate's colour (Luxury Estates) and
is the brand your recorded exception is about — it is in our **contrast corpus**, which is why both
sides have measured it, but it is not a preset anyone can pick.

So the sample and the product are two different populations with a two-brand overlap. That is the
only thing here we would ask you to look at.

## 2 · Both populations pass your thresholds — all twelve brands

Your stated thresholds are 3.0 for display text ≥24px (`display_ink`) and **≥4.5 for everything
under 24px on the band** (`on_primary`). `on_primary` always takes the better of white and
`#14151a`, so the failure mode is a `primary` where **neither** clears 4.5.

**Our six:**

| brand | hex | white | `#14151a` | best | `on_primary` | `display_ink` |
|---|---|---|---|---|---|---|
| Indigo | `#4F46E5` | 6.29 | 2.90 | **6.29** | `#ffffff` | `#ffffff` |
| Ocean | `#0EA5E9` | 2.77 | 6.58 | **6.58** | `#14151a` | `#14151a` |
| Crimson | `#DC2626` | 4.83 | 3.77 | **4.83** | `#ffffff` | `#ffffff` |
| Forest | `#059669` | 3.77 | 4.84 | **4.84** | `#14151a` | `#ffffff` |
| Midnight | `#1E293B` | 14.63 | 1.25 | **14.63** | `#ffffff` | `#ffffff` |
| Royal | `#7C3AED` | 5.70 | 3.20 | **5.70** | `#ffffff` | `#ffffff` |

**Yours:** red 4.83 · teal 4.87 · cyan 5.36 · violet 5.70 · amber 8.49 · lime 9.23 (best-of).

**Zero of twelve fall below 4.5.** Your rule holds on a population it was never measured on, which
is the better outcome and worth saying plainly.

## 3 · `#0D9488` is one affiliate's colour, not a preset

This is the detail worth your attention, and it explains the other two sections.

The brand your recorded exception is written around — and the brand both of us have now measured,
exception-written and tolerance-derived against — **is not in the product's picker.** It is one
affiliate's chosen colour (Luxury Estates). It is in our *contrast corpus*, which is why it keeps
appearing in both sides' measurements, and it is the brand that produced the 3.74 figure the owner
decision turned on.

So the hex that has anchored three rounds of colour decisions is one nobody can select. A customer
reaches it only by typing it into the custom field. Everything about it is correct; it is just not
representative, and neither of us noticed we were treating it as though it were.

## 4 · The one place the two sets behave differently

`Forest` (`#059669`) is the only brand where `display_ink` and `on_primary` disagree in our set —
white is 3.77, so display text keeps white while sub-24px text goes to `#14151a`. In your set the
same split lands on `teal` (3.74). **Two different brands, the same mechanism, and in both cases it
is the behaviour you specified.** Nothing to change; worth knowing that the brand your exception is
written around is not one a customer can choose.

`Ocean` (`#0EA5E9`, white 2.77) is the only preset where the owner's white-on-brand preference
cannot be honoured at any size. Your sample has two such brands (amber, lime); ours has one.

## 5 · On a fixed ink value

If a specific ink hex is on the table for text on light and tinted surfaces: we already derive one,
and we would rather reconcile the two than add a constant beside a rule that covers it.
`primary_ink` darkens `primary` until it clears **4.5 on white and on the brand's own tint**
(our D-170 — it used to clear white only, which is half of its own definition). Measured on the six
presets, ink on white / on tint:

| brand | `primary_ink` | on white | on tint |
|---|---|---|---|
| Indigo | `#4f46e5` | 6.29 | 5.75 |
| Ocean | `#0979ab` | 4.84 | 4.58 |
| Crimson | `#cf2424` | 5.34 | 4.87 |
| Forest | `#057d57` | 5.15 | 4.80 |
| Midnight | `#1e293b` | 14.63 | 13.08 |
| Royal | `#7c3aed` | 5.70 | 5.21 |

Worst case 4.58. A fixed hex would be one brand's answer; the derivation is every brand's, and it
already ships.

---

## The pattern, said once

Three bounds have now reached us **derived from a sample and stated as a property of the
surface** — `#8A8E95`, then the display-size exception, now the brand set behind both.

The difference matters, and it is in your favour: the first two were corrected because the *number*
was wrong. **This time the method is sound and only the population is narrow** — which is why the
rule held anyway.

We are not asking for a re-cut. One question only: should the sample be the product's six? That
would put the next bound you derive on the brands customers can actually pick, and it would stop
`#0D9488` being read as a representative case when it is one affiliate's colour.

## What we are not asking

Whether to tighten the picker, derive a compliant variant, or accept the spread is a product
decision, not a design one. It is with Jerry. Nothing in this document needs an answer before the
market templates land.
