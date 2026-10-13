# The charts under the new architecture: scoped, not built

**Asked for before building.** Three questions: where a chart can go on the `_v2` page, what it
costs in rows, and whether the twelve-month trend is worth a page on `market_snapshot`. Plus the
gate for a specified output that silently stops existing.

**Two premises in the ticket are not what the repository says**, and both change the answer, so they
come first.

---

## 0 · Two corrections

### §7.3 specifies TWO chart families, not five

`DELIVERY_SURFACES_MASTER_PLAN` §7.3's own summary line:

> **7.3 Charts** — Two: the twelve-month median/pace trend and the price-band distribution. Both to
> the mark specs, both `primary_ink`, no legend, selective direct labels.

And the body opens *"there is currently no chart in any of the 32 pages. Single-series only in v1."*
So the specified set is **two**, both were built, and a third — `closed`'s DOM distribution — is
named in §7.3's own prose as **deliberately open** pending confirmation that D-105's fix is right in
production, because *"a histogram makes a number authoritative."*

### The twelve-month trend was NOT displaced. It still ships.

Measured by rendering all eight kinds and reading the **element**, not the class name:

| kind | trend SVG | band SVG | inline bars | `<svg>` count |
|---|---|---|---|---|
| `market_snapshot` (unwired) | **yes** | no | no | 1 |
| `price_bands` | no | no | **yes** | 0 |
| the other six | no | no | no | 0 |

**The median trend belongs to `market_snapshot`, which is the one kind not yet wired**, so it renders
exactly as it always did. What lost its page is the **pace** series on `inventory` — D-183, filed,
with the fetch cost removed at the same time.

The band-distribution SVG also no longer renders, and that one is **not** a loss: `price_bands`' `_v2`
body draws a bar per band as CSS, proportional to the largest count, with the count beside it. Same
information, same comparison, a different mark. §7.3's rules it still meets (no legend, selective
labels); the one it does not is "inline SVG", which was a means rather than an end.

> **A note on how the first version of this table was wrong.** `'band-chart' in html` reported a band
> chart on `market_snapshot`, because `.band-chart`'s **CSS rule** is in the `<style>` block of every
> page that shares the stylesheet. Class-name matching cannot distinguish a rule from an element.
> That is D-185's shape in the measurement written to scope D-185's gate, and it is the single most
> important design constraint on that gate.

---

## 1 · Where a chart can go

The `_v2` page is **one band plus one per-kind body**. Measured: band **265.4px**, leaving
**662.9px** on page 1; a continuation page has the full **928.3px**.

| body | what a chart displaces |
|---|---|
| table (`closed`, `inventory`, `new_listings`) | table rows |
| bands (`price_bands`) | band rows — and the body already *is* the distribution |
| grid (three galleries) | a whole card row, because cards do not reflow |
| **none** (`market_snapshot`, once wired) | nothing — but it competes with three body blocks |

So there are only two honest placements: **above the body on page 1**, or **as the body** on a kind
that has no listings. There is no third slot, because Design's page is a band and a body and nothing
else — adding a chart beside a body means inventing a region their spec does not have, which is what
the `.bnote` line already had to do once and was flagged for.

---

## 2 · What it costs, measured

| | measured |
|---|---|
| trend chart, rendered | **179.5px** (150 SVG + 13.5 note + 16 padding) |
| `_v2` table row pitch | **34.7px** |
| page-1 room below the band | **662.9px** |
| table header · showing line | 22px · 23px |

Page-1 rows today: `(662.9 − 22 − 23) / 34.7` = **17**, which is the pinned capacity.
With a chart: `(662.9 − 22 − 23 − 179.5) / 34.7` = **12**.

**A chart costs five rows on page 1 — and one page per table kind.**

| kind (120 listings) | now | with a page-1 chart |
|---|---|---|
| `closed` | 5 | `1 + ceil((120−12)/26)` = **6** |
| `inventory` | 5 | **6** |
| `new_listings` | 5 | **6** |

Three of the ten pages saved go back. Continuation pages are unaffected — a chart appears once.

On the **galleries** a chart is worse: the shared card is 238.3px, so 179.5px of chart displaces a
whole row of **three cards** on page 1 and page 1 drops from six cards to three.

---

## 3 · Is the trend worth a page on `market_snapshot`?

**The premise that it "already gained one" is wrong** — `market_snapshot` is unwired and renders at
**2 pages**, exactly as before. Nothing has been spent on it yet.

What the choice actually is, once it is wired:

| | pages | carries the trend |
|---|---|---|
| today (legacy) | 2 | **yes** |
| `_v2` without the trend | **1** (predicted) | no |
| `_v2` with the trend | **2** (predicted) | yes |

Design's body is three row-blocks — an MOI headline block with an 8-cell bar and legend, a tier
block with three bars, and three property-type cards. Against 662.9px of page-1 room, a 179.5px
chart leaves **483.4px** for all three. Their two stated fixed sub-blocks are 78px each before their
bars and legends; three blocks in 483px is tight to the point of unlikely, so **the chart almost
certainly means a second page.**

**Recommendation: keep it, and say so as a decision rather than discovering it.** The trend costs the
page it has always cost — a reader comparing today's report with the new one sees two pages either
way — and `market_snapshot` is the one kind whose entire job is "how is this market doing over time",
which is the question a twelve-month line answers and a band of current figures does not.

**This is not measurable until the body is built**, and the 1-vs-2 above is a prediction. Stated now
so it can be checked against the measurement rather than reconciled afterwards.

---

## 4 · The gate: a specified output that silently stops existing

**The failure class nothing here covers.** Every gate on this surface asks whether what renders is
correct — the right colour, the right size, the right page. None asks whether something the spec
requires renders **at all**. D-183 is the proof: the pace chart's producer, its note, its tests and
its fetch all survived, and the only thing that vanished was the output. It was found by a test that
happened to render the page, not by anything looking for it.

### Design

A registry of **specified outputs**, each naming its source, the kind that carries it, and an
**element-anchored** predicate:

```python
SPECIFIED_OUTPUT = {
    "median trend":        {"source": "§7.3", "kinds": {"market_snapshot"},
                            "marker": '<div class="trend-chart'},
    "pace trend":          {"source": "§7.3", "kinds": set(),
                            "marker": '<div class="trend-chart',
                            "absent_because": "D-183 — Design's `_v2` page has no chart slot"},
    "band distribution":   {"source": "§7.3", "kinds": {"price_bands"},
                            "marker": 'class="bbar'},
    "DOM distribution":    {"source": "§7.3", "kinds": set(),
                            "marker": None,
                            "absent_because": "unbuilt, blocked on D-105 in production"},
}
```

Four properties, each from something that has already gone wrong here:

1. **Element-anchored, never class-name-anchored.** `.band-chart`'s CSS rule is on every page; the
   first draft of §0's table said `market_snapshot` had a band chart because of it. The gate strips
   everything up to `</style>` before matching.
2. **Both directions.** Present on every kind that specifies it, **absent on every kind that does
   not** — which is what catches a chart appearing somewhere it was never designed for, and is the
   half the contrast and pagination gates do have and this class lacks.
3. **An empty `kinds` set is legal and must carry `absent_because`.** This is the whole point: it
   distinguishes *specified and deliberately not rendering* from *specified and quietly gone*. D-183
   and the DOM distribution are both legitimately absent and for different reasons, and a gate that
   could not say so would have to be deleted the moment either was accepted.
4. **An unregistered specified output is an error**, as `V2_BODY_MARKER` and `V2_CONTINUATION` are —
   so the next chart cannot be added without declaring where it belongs.

### What it does not do

It cannot know what the spec says. The registry is hand-maintained against §7.3 and Design's per-kind
table, which makes it **a second copy of a specification** — the family this project has filed most
often. The mitigation is that it is a copy of *four lines*, each citing its source, and that the
alternative is no coverage of the class at all. Worth stating plainly rather than discovering: this
gate is a pin, and pins go stale.

**Not built.** Reported first, as ticketed.
