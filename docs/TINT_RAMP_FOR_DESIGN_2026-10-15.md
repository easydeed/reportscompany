# Two questions about tints

**For Design. Short — this is a gap in `tokens.css`, not a disagreement.** We are adopting the
package onto the existing components and have stopped at the one thing we would otherwise have to
invent.

## What we have

`tokens.css` gives us the semantic pairs, fixed per state, and we are using them as specified:

    opened / done / called   #065F46 on #D1FAE5
    sent                     #64748B on #F1F5F9
    bounced / failed         #991B1B on #FEE2E2
    running                  #1E40AF on #DBEAFE
    hot                      #92400E on #FEF3C7
    new / lead               white on #0F172A

And one tint that is not a status: `--accent: #EEF2FF` with `--accent-foreground: #3730A3`, which
your README assigns to the Seller tag.

## What we do not have

**A tint ramp.** The authenticated app has **25** surfaces at `bg-indigo-50 / -100 / -200` that are
none of the above. Counted and read, they are three things:

| | what it is |
|---|---|
| highlight panels | `<Card className="border-indigo-200 bg-indigo-50/50">` — a card called out from its neighbours |
| icon chips | `w-10 h-10 rounded-lg bg-indigo-50` and `rounded-full bg-indigo-100 text-indigo-600` — a tinted square or circle behind a glyph |
| one bar track | `bg-indigo-200` as the track of a usage bar on an unlimited plan |

They are chrome, they are tinted, and no token in the file describes them.

We are not inventing one. Two questions:

1. **Is there a ramp in the system we should be reading** — or do these surfaces become semantic
   pills under the redesign, and the tints simply go away? If the answer is "they go away", that is
   a clean answer and we will treat each of the 25 as a state to classify rather than a colour to
   map.

2. **If a ramp exists, does it derive from `--link` indigo or from the agent's brand?**
   This is the one we think you are better placed to rule on than we are. Your constraint #1 is that
   the agent's brand never touches chrome — *"the same screen shows the agent's brand inside the
   artifact; brand on chrome makes the artifact disappear"* — and **a tinted panel is chrome**. So a
   brand-derived tint ramp would collide with your own rule, and a `--link`-derived one would put
   indigo back on surfaces across an app whose primary is now ink.

Until you answer, the 25 stay as they are: indigo tints, unconverted, listed in our adoption notes
as the one category we did not force into a bucket.

---

**Form note:** same as `GALLERY_GRID_FOR_DESIGN_2026-10-10.md` and
`TREND_CHART_FOR_DESIGN_2026-10-14.md` — the question, the measurement behind it, and no proposal.
