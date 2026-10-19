# Does "no tinted surfaces" reach inside the report?

**For Design. One question, and it is yours rather than ours.** Your 2026-10-19 answer removed every
tinted surface from chrome, and we have applied it: zero `bg-indigo-50/100/200` and
`border-indigo-200` on any surface reachable from an authenticated `/app` route.

Four occurrences remain on a **live** surface we did not touch, because your argument for the rule
is the reason to ask rather than act. You wrote that a tinted indigo panel *"competes with the
report, which is what the agent is selling."* These four are **inside the report**.

## The surface

`apps/web/components/mobile-report/MobileReportViewer.tsx`, mounted by `app/r/[id]/page.tsx`. It is
the consumer-facing home-value report: the link an agent sends a lead, opened on a phone, no login.
It is a **third** rendering of a report — the worker renders the PDF from Jinja templates with
`derive_theme`, and this is a separate React implementation of the same document.

## What we found while counting the four

The file is **half brand-driven and half hard-coded**, and nobody has reconciled the two.

**Five lines take the agent's brand** — six properties, since line 232 sets both a colour and a background — through inline styles with a fallback to `#6366f1`:

| line | what |
|---|---|
| 232 | active tab colour and its background wash |
| 253 | the hero panel — `linear-gradient(135deg, primary_color, accent_color)` |
| 484 | the comparables headline |
| 590 | the primary CTA button background |
| 602 | the secondary CTA border and label |

**Fourteen sites are hard-coded indigo or violet**, in two hues:

| line | what | shape, in your vocabulary |
|---|---|---|
| 254, 258, 271 | three labels, `text-violet-200` — **on the brand gradient at 253** | text on a branded surface |
| 299, 300 | address chip: `MapPin` in a `bg-indigo-100` circle | icon chip |
| 337, 339 | the phone button: `<a href="tel:">`, a 40px `bg-indigo-100` circle | icon chip that is a tap target |
| 498 | comparables carousel dot, active state `bg-indigo-600` | selection |
| 536, 537 | *"Based on N comparable sales within 2 miles…"* — `bg-indigo-50` panel with `text-violet-800` | context panel |
| 566, 569, 570 | agent photo and its fallback: `border-violet-100`, `bg-indigo-100`, `User` glyph in `text-violet-400` | the avatar shape |
| 648 | stat-tile icons, `text-indigo-600` | bare glyph |

Counted, not estimated: `indigo-600` ×4, `violet-200` ×3, `indigo-100` ×3, `indigo-50` ×1,
`violet-800` ×1, `violet-400` ×1, `violet-100` ×1.

**The collision we can state without rendering anything.** Lines 254, 258 and 271 are
`text-violet-200` on the surface whose colour comes from `primary_color` at line 253. For an agent
whose brand is teal, the hero is a teal gradient carrying violet labels. The hard-coded hues were
chosen to match the `#6366f1` / `#8b5cf6` fallback; they are only correct for an agent who has set
no brand at all.

## The question

**Does the no-tinted-surfaces rule apply inside the report, and if so, which of these fourteen
become brand-driven and which become neutral?**

We can see three readings and are not choosing between them:

1. **The rule is about chrome only.** The report is the artifact; tint inside it is fine, and the
   fourteen stay — but then lines 254/258/271 are still wrong, because they are a hue that does not
   follow the surface they sit on.
2. **The rule applies everywhere.** The fourteen become structure and neutral ink, like the chrome
   sweep, and the brand survives only at the six sites that already read `primary_color`.
3. **The report is where brand belongs** — your constraint #1 says the brand lives *inside* the
   artifact — so these fourteen should be brand-driven rather than neutral: the chip, the phone
   button, the carousel dot and the panel all take the agent's colour.

(1) and (3) are opposite answers and both follow from something you have written, which is why we
are asking instead of picking.

## What we have not done

Nothing in this file is changed. We also have not rendered it — this container has no
`node_modules`, so there is no screenshot of the teal-brand collision above, only the source. Your
answer on chrome is already applied and does not depend on this.

---

**Form note:** same as `TINT_RAMP_FOR_DESIGN_2026-10-15.md`, `GALLERY_GRID_FOR_DESIGN_2026-10-10.md`
and `TREND_CHART_FOR_DESIGN_2026-10-14.md` — the question, the measurement behind it, and no
proposal.
