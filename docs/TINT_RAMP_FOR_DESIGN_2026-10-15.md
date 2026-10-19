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

---

# ANSWERED — 2026-10-19

**No ramp.** Design's answer, relayed in full:

> NO RAMP, and no tinted surfaces on chrome at all. With the primary now ink, a tinted indigo
> panel is the strongest colour on the page and competes with the report, which is what the agent
> is selling.

So question 2 does not arise: neither a `--link`-derived nor a brand-derived ramp exists, because
there is nothing for a ramp to colour.

## The three shapes, answered

| shape we counted | Design's disposition |
|---|---|
| highlight panels | **structure, not fill.** Selected = 1.5px ink border on white. Status = a semantic pill, not a panel. Context = white card, `--border`, 11px uppercase label. |
| icon chips | **removed entirely.** Bare 18px glyph in `--body`; or the initials circle filled with the agent's primary (sanctioned exception, because the circle *is* the agent); or deleted if decorative. |
| the unlimited bar track | **no bar at all.** "Unlimited" with a full-width tinted track reads as 100% used, which is the opposite. Filed separately as a defect — see D-195. |

Two tokens adopted into `app/globals.css` from this answer:

    --surface-selected: #FFFFFF;
    --border-selected:  #0F172A;

together with Design's constraint that **the semantic status pairs are the only tinted fills
permitted on chrome**, and the avatar exception written out beside it so the next reader does not
read the filled initials circle as a surface that escaped the sweep.

## Design's fourth case

> If a panel fits none of these, it is probably two cards that should be one.

**Nothing landed there.** Every surface we converted fitted one of the three rows above. The fourth
case is recorded here because it is the right disposition for the next panel that does not fit, not
because it was used.

## What the sweep actually covered

The ask said 25, counted in `app/app/**`. Converting them to the rule rather than to the literal
grep target reached a few neighbouring surfaces in the same files and in the chrome those routes
render — the account-type tag in `app-layout.tsx`, the affiliate dashboard shell, the recipient
chips, the comparables status pill. The grep target (`bg-indigo-50/100/200`, `border-indigo-200`)
is now **zero across every surface reachable from an authenticated `/app` route**.

It is **not** zero app-wide. **46 hits remain across 15 files**, and none of them is app chrome.
These are occurrences, not lines — `grep -c` counts a line that carries both `bg-indigo-50` and
`border-indigo-200` once, and five of these lines do:

| where | hits | why it is out of scope here |
|---|---|---|
| `app/about`, `app/docs`, `app/security`, `app/careers`, `app/blog` | 19 | public marketing pages, not app chrome — a separate surface and a separate decision |
| `app/admin/(dashboard)/**` | 19 | **unreachable.** `middleware.ts` redirects every `/admin/*` to `/app/admin/*` before any auth check, so this whole tree renders for nobody |
| `components/branding-form.tsx` | 4 | `BrandingForm` is exported and imported by nothing |
| `components/mobile-report/MobileReportViewer.tsx` | 4 | live on `/r/[id]`, but it renders **the report**, not chrome. Design's whole argument is that chrome must not compete with the report; restyling the report itself is a different question and is not answered above |
