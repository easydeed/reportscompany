# Two left, both yours — and the renders of two calls we made

**For Design.** Everything else from your 2026-10-21 ruling is applied and the build is green.
What remains are two things we cannot settle without you, and two judgement calls of ours you
should **see** rather than read about.

---

## What we closed since your ruling, so you know what is not in this note

| | |
|---|---|
| `harbor` cover title | solid `primary_on_dark` on a flat `#0f172a`, gradient and circles gone |
| `linen` footer band | flat `#0f172a` + a 3px `primary` rule, `primary_on_dark` type |
| `harbor` brand mark | `#94a3b8` → the role table's muted `#5E636B` (2.56 → 6.05) |
| `harbor` cover agent title | raw brand → `primary_ink` on white |
| every tinted panel in both themes | **an ink derived against the ground it sits on** |

That last row is the one worth a sentence. `primary_ink` is derived against **white**, and the role
table applies it to *"white/tint"* — four grounds, one derivation. Over 38 brands it clears 4.5 on
white for all of them and fails on every tint: 6 on `linen`'s cream, 14 on `harbor`'s ghost, 30 on
cream-dark, **34 on gold-light**. `primary_on_dark` has the same shape against a lighter dark panel:
15 of 38. Both are now derived per ground and all of them clear. Contrast baseline **55 rows this
morning → 29**.

---

## 1 · Text on `linen`'s cover gradient — composition, not contrast

The cover fill is `linear-gradient(135deg, primary, primary_dark)`. Under your rule 3 that fill is
legal — both are permitted brand surfaces. What fails is the **type on it**, for most of the brand
space:

| element | today's ink | brands failing, of 38 |
|---|---|---|
| `div.cover-label` | `--gold` `#C9A962` | **36** |
| `div.cover-brand-text` | `--gold-light` `#E8D5A3` | 34 |
| `th` / `div.range-stat-label` | white | 29 |
| `h1.cover-title` | white | 21 |
| `div.cover-street` | white | 19 |
| `div.cover-city` | white | 25 |

**The role table's answer is `on_primary` — *"all text on `primary` fills"* — and it does not quite
close it.** `on_primary` is derived against `primary`, and the fill runs to `primary_dark`:

| | on `primary` | on `primary_dark` |
|---|---|---|
| luxury_estates | 4.87 | **3.02** |
| the other five presets | 4.83 – 9.23 | 4.87 – 8.59 |

Five of six. `luxury_estates` fails on the darker stop because its `on_primary` is dark ink chosen
for the lighter end. Today's inks are far worse — gold measures **1.05:1** and gold-light
**1.36:1** — so moving to `on_primary` is a large improvement either way, and still not a fix.

**A flat `primary` fill would close it for all six by your own rules**, which is the same move as
the footer band. But `linen`'s cover gradient is the theme's signature, and flattening it is a
composition decision rather than a token swap. **We have not touched it.** Three ways we can see:

1. **flatten the cover fill to `primary`** — `on_primary` becomes correct by the existing rule, and
   `linen` loses its gradient;
2. **keep the gradient and derive the ink against its darker stop** — one more per-ground ink,
   the mechanism we just built, and the type gets darker than `on_primary` on most brands;
3. **a plate behind the title block**, as on the harbor cover — the gradient stays and the type
   sits on a declared ground.

**`harbor`'s brand-filled table row is now done and is not part of this question.** It was white
on the raw brand, 29 of 38 failing; `on_primary` — your token, as your role table specifies — takes
it to **1 of 38**, and that one is at `L=0.190`, the same ramp step as the eight `atlas` surfaces
below. So it belongs to §2 rather than here. With it, **`harbor` has no baselined contrast failure
on any of the six presets** — the second theme to reach that after `atlas`.

---

## 2 · `atlas`, eight surfaces, one brand — your derivation, not our template

Eight surfaces on your shared `_v2` page fail at **exactly one** point in the brand space and
nowhere else:

    span.masthead-brand   span.masthead-kind   span.cover-city   span.cover-stat-label
    span.conf-grade       span.agentpanel-meta span.agentpanel-email span.agentpanel-blurb

All eight fail at brand relative luminance **0.190** and pass at 0.167 and below and at 0.218 and
above. One ramp step out of thirty-eight, and `atlas` is otherwise the cleanest of the three
themes — which is what we would expect from the theme that is already on your architecture with
your roles.

**And it is not only `atlas`.** `harbor`'s brand-filled table row, fixed today to `on_primary`,
fails at **the same single luminance** — 4.38:1 at `L=0.190` — having cleared every other brand in
the sweep. Two different roles (`display_ink`/`on_primary` on your page, `on_primary` on ours)
coming up short at the same point looks less like eight surfaces and more like **one luminance
where a derived role lands just under**, which is a single thing to fix in the derivation rather
than nine places to patch.

It looks like a gap in the derivation at one luminance rather than anything about the page. We have
not changed `_v2`.

---

## 3 · Two calls we made, rendered

Both were permitted by your ruling and both are visible, so they are images rather than
sentences — attached, `harbor` and `linen` covers, before and after, at the violet brand.

**`harbor`'s panel is flat now, not a gradient.** You said the ground may stay a gradient elsewhere
on the cover and be flattened under the title box. A flat plate needs padding and a radius nobody
specified, so we took the permission to flatten and applied it to the whole left panel. **That
removes a gradient you allowed to remain.** If you want it kept, the plate geometry is yours to
give.

**The two brand circles are gone, not moved.** You allowed either. Moving a 400px circle inside an
`overflow:hidden` panel is a composition change; dropping is not. The cover now carries two fewer
brand presences than your description assumes.

---

## What we are not asking

Nothing about tokens. The vocabulary did the work: `primary_on_dark`, `primary_ink`, `on_primary`
and `ink_on` against a declared ground covered every surface except the two above. Both of those
are about **where the brand sits**, not about which value goes on it.
