# Your market colour rule, measured against the brands the product ships

**To:** Design · **Date:** 2026-10-07 · **Re:** `RESPONSE_2026-10-06.md`, colour roles

**The rule is right. We measured it against our own brand set and are sending the numbers rather
than a verdict, because the interesting part is where the two sets differ.**

`display_ink` is in `themes.derive_theme` and wired on the property cover. Measured, your six
figures reproduce exactly against our `themes.contrast` on your own hexes — red 4.83, teal 3.74,
cyan 5.36, violet 5.70, amber 2.15, lime 1.98. Third round for this class of claim and the first
where the method came back as a derivation rather than a corrected number. Noted and adopted.

---

## 1 · Only two of the six brands are shared

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

## 2 · Both populations pass your own thresholds

We checked this before sending it, and the answer is the comfortable one. Your stated thresholds
are 3.0 for display text ≥24px (`display_ink`) and **≥4.5 for everything under 24px on the band**
(`on_primary`). `on_primary` always takes the better of white and `#14151a`, so the failure mode is
a `primary` where **neither** clears 4.5.

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

## 3 · The one place the two sets behave differently

`Forest` (`#059669`) is the only brand where `display_ink` and `on_primary` disagree in our set —
white is 3.77, so display text keeps white while sub-24px text goes to `#14151a`. In your set the
same split lands on `teal` (3.74). **Two different brands, the same mechanism, and in both cases it
is the behaviour you specified.** Nothing to change; worth knowing that the brand your exception is
written around is not one a customer can choose.

`Ocean` (`#0EA5E9`, white 2.77) is the only preset where the owner's white-on-brand preference
cannot be honoured at any size. Your sample has two such brands (amber, lime); ours has one.

## 4 · On a fixed ink value

If a specific ink hex is on the table for text on light and tinted surfaces: we already derive one.
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
already ships. We would rather reconcile the two than add a constant beside a rule that covers it.

---

## The pattern, said once

This is the third time a bound has come to us **derived from a sample and stated as a property of
the surface** — `#8A8E95`, then the display-size exception, now the brand set behind both.

The difference matters: the first two were corrected because the *number* was wrong. **This time the
method is sound and only the population is narrow.** Your rule survived contact with four brands it
had never seen, which is what a derived rule is for and what a stated bound could not have done.

We are not asking for a re-cut. We are asking whether the sample should be the product's six, so the
next bound you derive is derived on the brands customers actually have — and so that
`#0D9488`, which both of us keep measuring, is understood as one affiliate's colour rather than as a
representative case.

## What we are not asking

Whether to tighten the picker, derive a compliant variant, or accept the spread is a product
decision, not a design one. It is with Jerry. Nothing in this document needs an answer before the
market templates land.
