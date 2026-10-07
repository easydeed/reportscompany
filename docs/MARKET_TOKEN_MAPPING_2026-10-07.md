# Design's market colour roles, mapped to tokens that already exist

**Measured 2026-10-07, before wiring the first market kind.** The point of checking first is that
this project's most repeated defect is a second copy of something — five copies of the theme map
(D-163), two of the brand picker (D-175), two of the token set (D-171). **Adding `accent_ink` as a
new token when we already derive it would be the same mistake with a design handoff as the excuse.**

## All six roles exist. None needs building.

| Design's role (market README §colour roles) | what it is | ours | new? |
|---|---|---|---|
| `primary` | the affiliate's colour; band fill, bars, initials circle | `primary` / `--primary-color` | no |
| `accent` | highlight bars, "New" tag, over-asking % | `accent_color` / `--accent-color` | no |
| `on_primary` | everything under 24px on the band — white or `#14151a` by contrast ≥4.5 | `on_primary` (`derive_theme`) | no |
| `display_ink` | display text ≥24px — white where white ≥3.0 on `primary`, else `on_primary` | `display_ink` (`derive_theme`) | **added 2026-10-07, D-171** |
| `accent_ink` | all accent-coloured text; "derived by darkening `accent` until ≥4.5 on white" | **`accent_on_light`** (`compute_color_roles` → `theme_color_on_light`) | **no — it already is this** |
| `tint` | tint panel, over-asking column wash, missing-photo tile | `tint` (`derive_theme`) | no |
| band rules | `rgba(255,255,255,0.3)` when `on_primary` is white, else `rgba(20,21,26,0.25)` | the `--on-primary-rule` rule, in `property/_v2` | pattern exists, not yet on market |

## `accent_ink` is `accent_on_light`, verified rather than assumed — and the check found a defect

Design's definition is a guarantee, so it was checked as one, on both light surfaces the token lands
on. The tint half failed on four of nine brands; see D-177 below. Post-fix, nine brands — our six
presets plus the three of Design's samples we do not ship:

| brand | `accent` | `accent_on_light` | on white | on tint |
|---|---|---|---|---|
| Indigo | `#4F46E5` | `#4F46E5` | 6.29 | 5.75 |
| Ocean | `#0EA5E9` | `#0977a9` | 4.97 | 4.70 |
| Crimson | `#DC2626` | `#ce2323` | 5.40 | 4.93 |
| Forest | `#059669` | `#027c56` | 5.22 | 4.87 |
| Midnight | `#1E293B` | `#1E293B` | 14.63 | 13.08 |
| Royal | `#7C3AED` | `#7C3AED` | 5.70 | 5.21 |
| amber | `#F59E0B` | `#9c6404` | 4.95 | 4.72 |
| lime | `#84CC16` | `#4e790b` | 5.17 | 4.97 |
| teal | `#0D9488` | `#0a7a6f` | 5.22 | 4.87 |

**Worst case 4.70 across both surfaces**, and the brands that already clear 4.5 on both are returned
unchanged — it darkens only when it has to, which is the same behaviour `primary_ink` has and for
the same reason.

So the market wiring needs **no new colour token**. What it needs is the two roles that exist but
are not yet wired onto the market surface: `display_ink` (on `property/_v2` only) and the
`on_primary`-derived band rule.

## What this does not settle

* **`accent_ink`'s name.** Design says `accent_ink`, we say `accent_on_light`, and there is no
  third name. Renaming ours would touch the market template's `:root` block and
  `compute_color_roles`; adding theirs as an alias would be a second name for one fact, which is
  D-164's shape. **Left as `accent_on_light`**, with this table as the dictionary — the mapping is
  one row, and a rename is a change to working code for a vocabulary match.
* ~~**`accent_ink` on a tint** is not measured here.~~ **MEASURED, AND IT HAD THE GAP. D-177.**
  Design's rule is ≥4.5 on white, and their spec also puts accent text on the `tint` panel (the
  over-asking Status column). `accent_on_light` cleared white and **failed the tint on four of nine
  brands** — Crimson 4.41, Forest 4.39, lime 4.47, teal 4.38, two of them shipping presets.

  Exactly D-170's defect on the accent instead of the primary, because
  `_ensure_readable_on_light` and `themes._ink` are **two implementations of "darken until
  readable"** and only one got D-170's fix. Fixed the same way: the function now takes several light
  surfaces, as `_ensure_readable_on_dark` always has, and `compute_color_roles` passes white and the
  brand's own tint. Worst of either surface is now **4.70**, with four brands moving one or two
  steps.

  The table above is the post-fix measurement. Pre-fix values are on the defect entry.

---

## Applying the heuristic before building: what each market kind closes

D-171 closed zero and D-177 closed twenty, from the same shape of ticket, and the difference was
*which surface the token lands on*. The rule that came out of it — **ask where it paints before
estimating what it closes** — is a grep of the baseline, so it was run before writing any template.

All six `market__*` baseline rows are **one construct**:

```
market__new_listings   span.listing-tier-badge.tier-high
market__new_listings   span.listing-tier-badge.tier-low
market__new_listings   span.listing-tier-badge.tier-median
market__price_bands    span.status-badge.active
market__price_bands    span.status-badge.closed
market__price_bands    span.status-badge.pending
```

Six pairings, **66 failing text runs** of 5,058 — the 1.30% the whole market surface is held to. And
Design's spec addresses exactly this construct, twice: *"No chips, no tinted fills behind semantic
text — the live surface's only 66 failures are that construct"* and *"Semantic/delta colour:
`accent_ink` text only, never fills."*

So the contrast payoff of the market adoption is **all of it, and it is not on `closed`**:

| kind | market baseline rows | what wiring it closes |
|---|---|---|
| `new_listings` | 3 (tier badges) | **3 pairings** |
| `price_bands` | 3 (status badges) | **3 pairings** |
| `closed` · `inventory` · `market_snapshot` · the three gallery kinds | **0** | **nothing, by construction** |

**`closed` closes zero contrast failures**, and that was knowable before building it — the D-171
situation again, caught this time by asking first rather than measuring after.

That does **not** make `closed` the wrong first kind. It is first because it is the table kind with
continuation pages, so it exercises `header.start_at = 1`, `footer.start_at = 1` and the row
capacity together — the architectural risks, which if wrong invalidate the other seven. The contrast
win is a separate axis and it sits on `new_listings` and `price_bands`.

**Worth knowing for the order after `closed`:** `new_listings` is also the kind that saves ten pages
by moving off the analytics layout. It carries both the largest page saving and half the contrast
payoff, which makes it the obvious second rather than `inventory` (which is `closed`'s twin and
closes nothing).
