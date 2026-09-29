# The first contrast measurement of the market and property PDFs

**2026-09-29** · `scripts/measure_pdf_contrast.py` · no fixes applied

These documents have never been audited for contrast. `test_email_contrast.py` has been green for
weeks and walks only the email templates; the PDF surfaces had two narrow assertions on one
chart's SVG and nothing else (`docs/TEST_DURABILITY.md`). This is the number, before anything is
changed, because the number matters on its own.

## Corpus

**90 documents, 10,746 text runs.** Eight market report types and five property themes, each
rendered across the six brand colours the email audit already uses, so a finding on one surface
can be compared with the same brand on the other. Plus the market running head and page footer,
which PDFShift composes onto every page and which are not part of the body render.

## The measurement

**A real browser, not a CSS parser.** PDFShift renders these with Chromium, so `getComputedStyle`
is the ground truth and anything else is a model of it. Each text run's colour and the thing
actually painted beneath it are read out of the page.

Three things the first version got wrong, each caught by disagreeing with the CSS when I went to
read it:

| | |
|---|---|
| an **ancestor walk** — what the email walker does | The property covers paint their background with absolutely-positioned **siblings** (`.cover-photo`, `.cover-overlay`, `inset:0`), which are nowhere in the text's ancestor chain. Reported white-on-white at 1.00:1 for every cover in the corpus. Replaced with `elementsFromPoint`, which returns the hit-test stack in paint order |
| hit-testing from **below** the text's own element | An element's background is painted behind its own text. Excluding it reported white-on-white for every coloured table header — 165 runs |
| trusting `elementsFromPoint` to be complete | **It skips `thead`, `tbody` and `tr`.** Measured, not assumed: hit-testing a `<th>` inside `thead { background: navy }` returns `th, table, body, html` and no `thead`. The chain is now expanded with the ancestors sitting between consecutive hits |

Each of those produced a confident, wrong, *loud* first report. They are written down because the
next person to point a walker at these documents will hit all three.

**Applied, not ignored:** WCAG's large-text allowance (3:1 at ≥24px, or ≥18.66px at weight 700).
The email walker deliberately reports everything at 4.5:1 and leaves the judgement to the reader;
here there are hundreds of headings and that would bury the findings. Both numbers are printed.

**Declined rather than guessed:** text over a `url()` background image (0 runs in this corpus —
the covers use gradients). **336 runs sit off-canvas at `top: -9997px`** and are never painted:
six per document, each a single `.`, a font warm-up trick. Counted and named rather than dropped.

## The result

| surface | runs | below 4.5:1 | below its WCAG threshold | worst |
|---|---|---|---|---|
| market | 5,730 | 1,002 | **734** | 1.08:1 |
| property | 5,016 | 746 | **653** | 1.00:1 |
| **total** | **10,746** | 1,748 | **1,387** | |

| severity | runs |
|---|---|
| **below 1.5:1 — effectively invisible** | **94** |
| 1.5–3.0:1 — severe | 852 |
| 3.0–4.5:1 — marginal | 441 |

**Every brand fails.** amber 286 · lime 317 · luxury_estates 243 · demo_title 196 · coastal 173 ·
violet 172. There is no brand colour in the set for which these documents are readable.

**The charts pass.** All 24 SVG text runs clear their threshold — the §7.3 work held.

---

## What it is, in five groups

Non-overlapping, and they account for all 1,387:

| | group | runs |
|---|---|---|
| 1 | the market masthead | 560 |
| 2 | a theme's fixed accent on a variable panel | 210 |
| 3 | white hardcoded where the surface is not dark | 229 |
| 4 | fixed semantic colours on their own tint | 72 |
| 5 | muted greys and brand inks on white | 316 |


### 1. The market masthead — 560 runs, the largest single finding

```css
.masthead {
  background: linear-gradient(135deg, var(--header-bg) 0%, var(--header-bg) 50%,
                                      var(--primary-color) 100%);
  color: #ffffff;
}
.masthead-title    { color: #ffffff; }
.masthead-subtitle { color: rgba(255,255,255,0.7); }
```

**Read the variable names carefully, because they are the opposite of what they say.**
`market.jinja2` sets `--header-bg` from the agent's **primary** colour and `--primary-color` from
their **accent**. So the gradient runs *brand → brand → accent*, and every piece of text on it is
hardcoded white or 70% white.

Measured at each stop, per brand:

| | white title / metric (24–28px, needs 3:1) | 70% white subtitle & metric label (11px, needs 4.5:1) |
|---|---|---|
| lime `#84cc16` | **1.98** | **1.61** |
| amber `#f59e0b` | **2.15** | **1.71** |
| demo_title `#dc2626` | 4.83 | **2.99** |
| coastal `#0e7490` | 5.36 | **3.47** |
| violet `#7c3aed` | 5.70 | **3.58** |
| luxury_estates `#0d9488` | 3.74 | **2.60** |

**The subtitle and the metric label fail for every brand, at every stop. There is no
configuration in which they pass.** That is 432 of the 570.

**And a third of those failures have nothing to do with the agent's brand.** `DEFAULT_ACCENT` is
`#0d9488`, so an affiliate who has not set an accent — the common case — gets a masthead that
fades into Luxury Estates' teal whoever they are. 70% white on that teal is **2.60:1 for all six
brands**, identical, because it is the same colour every time.

**The one element that uses the token layer is the one that nearly passes.**
`.masthead-highlight` reads `var(--accent-on-dark)`, which `compute_color_roles` derives by
picking the better of `#ffffff` and `#14151a` against both gradient ends — the fix D-097 put in
for exactly this band. It clears 4.5:1 for four of the six and reaches 3.74:1 for the other two,
**and the code already says so out loud**:

```
[CONTRAST] on_dark: cannot reach 4.5:1 for #0d9488 on #1B365D/#0d9488;
           best achievable 3.74:1. Returning it anyway
```

That line printed on every render in this session. The derivation works, knows its own limit, and
reports it to a log; the title, the city, the subtitle, the metric value and the metric label sit
beside it hardcoded to white and report nothing.

Breakdown: `p.masthead-subtitle` 288 · `span.masthead-metric-label` 144 · `h1.masthead-title` 32 ·
`span.masthead-city` 32 · `span.masthead-metric-value` 32 · `span.masthead-highlight` 32.

### 2. A theme's fixed accent on a variable panel — 210 runs

Each property theme hardcodes a decorative accent chosen to sit on **that theme's own dark navy** —
classic's sand `#c4b7a6`, bold's bronze `#d69649`, elegant's champagne `#e8d5a3` and gold
`#c9a962`. The panel behind them takes the agent's brand colour. The pairing collapses:

```
1.00:1  #c4b7a6 on #84cc16   .range-stat-label, .page-header-label   classic + lime
1.09:1  #c4b7a6 on #f59e0b   same                                     classic + amber
1.18:1  #d69649 on #f59e0b   .page-header-label, .cover-label, phone  bold + amber
1.48:1  #d69649 on #0d9488   same                                     bold + luxury_estates
1.36:1  #e8d5a3 on #84cc16   .cover-brand-text                        elegant + lime
```

**Same shape as the masthead** — a colour chosen against one backdrop and used against another —
and the same token layer answers it.

### 3. White hardcoded where the surface is not dark — 229 runs

```
1.00:1  #ffffff on #ffffff   .page-footer .brand / .num   classic + bold, aerial page   18 runs
1.06:1  #ffffff on #f8f8f9   .num                         teal, contents overlay        12 runs
1.98:1  #ffffff on #84cc16   th, h2.page-header-title     lime                          27 runs
2.15:1  #ffffff on #f59e0b   th, h2.page-header-title     amber                         27 runs
3.61:1  #ffffff on #4a90a4   td                           modern                        30 runs
```

`classic_report.jinja2:643` writes `style="color:#fff"` and `border-color: rgba(255,255,255,.2)`
onto the aerial page's footer, while `.aerial { background: var(--warm-white) }`. The inline
override was written for a dark full-bleed page; the page is light. **The footer is invisible** —
not faint, invisible, and it has presumably been invisible in every classic and bold report ever
sent.

The rest are table headers and page titles set in white over a cell whose background is the brand:
the masthead defect again, one element at a time.

### 4. Fixed semantic colours on their own tint — 72 runs

`span.status-badge.active` 2.96:1, `.pending` 2.66:1, `.closed` 4.13:1, and the three
`listing-tier-badge` chips at 2.84–4.35:1. Brand-independent, marginal rather than invisible, and
a single decision fixes all six: these are chip colours on a 10%-tint of themselves, which is a
recognisable pattern with a known remedy.

Plus `div.af-photo-placeholder` at 1.08:1 — the agent's initial, painted in the brand colour on a
circle derived from the same brand.

### 5. Muted greys and brand inks on white — 316 runs

The long tail, mostly 2.3–4.4:1: `#94a3b8` labels on white (2.56:1), `#4a90a4` on white (3.61:1),
`h2.gallery-heading` in the raw brand on white (3.74:1 for luxury_estates). Real, unglamorous, and
the class `primary_ink` was built for — a brand colour darkened until it clears 4.5:1 on white,
which `worker.themes` already computes and these templates do not use.

The worst of the tail is teal's `.cover-label` on the `#34d1c3` accent panel, which lands between
1.04:1 and 1.69:1 depending on brand.

## What this does not settle

- **The threshold is a judgement in places.** 441 of the 1,387 sit between 3.0 and 4.5, and some
  are large display type one size below the allowance. The list is precise about size and weight
  so each can be argued; the script does not argue it.
- **SVG text is measured against the nearest HTML background**, because an SVG has no background
  of its own and what a `<rect>` paints under a `<text>` is geometry. Right today — the chart
  labels sit outside the bars — and it would go wrong silently if a label moved inside one.
- **A live render may differ.** These are builder renders with fixture data, which is what the
  product emits, but no PDF was produced through PDFShift for this pass. Colours do not depend on
  the paginator, so the risk is low and it is named rather than assumed away.

## The gate

`apps/worker/tests/test_pdf_contrast.py`, with the board in `pdf_contrast_baseline.txt`.

A hard gate at 4.5:1 fails 1,387 runs on the first commit, so it is a **ratchet**: every failing
combination that exists today is recorded, and the build fails on one that is not. New unreadable
text cannot ship; the existing 1,387 become a debt with a number on it.

**Keyed on (family, selector, foreground, background) — no file path.**
`scripts/template_color_baseline.txt` keys on paths, which is its weakness: a template replacement
invalidates every line and "may only shrink" then constrains nothing. This survives a rewrite —
a replacement template set inherits the entries whose selectors it reuses and earns a failure for
every new pairing it introduces. **410 combinations** on the board today. No counts are recorded:
the number of runs is a function of fixture size, the pairing is the defect.

**A missing browser is a failure, not a skip.** `PDF_CONTRAST_REQUIRE_BROWSER=1` is set in CI.
A gate that goes quiet when its tooling is absent is the failure this whole exercise was about.
CI gains a node setup and `playwright install chromium`; the measurement itself is 38 seconds for
all 90 documents, so the install is the slow part.

**The baseline cannot rot in either direction.** A second test fails when an entry no longer
fails — meaning something was fixed and the board was not updated — and points at
`--regen-contrast-baseline`, whose diff is then the evidence of the fix. A third asserts the
measurement actually looked at something (>8,000 runs, 8 market families, 5 property themes),
because zero findings and zero runs are indistinguishable from outside and that confusion is
exactly what left these documents unaudited.

**Four regressions applied and each seen to fail:** a new unreadable pairing introduced in the
CSS (caught, 1.54:1 and 1.61:1, named in the failure) · the classic aerial footer genuinely fixed
without regenerating (caught as two stale entries) · the browser required and absent (failed with
the reason) · the browser absent and not required (skipped, as intended).

**The first regression did not regress.** Inserting `color: #cccccc` at the top of
`.stats-bar-label` left the rule's own `color: var(--gray-600)` below it, which won — so the gate
passed, correctly, on a template that had not changed. Worth recording: a contrast regression
written by hand into a CSS block is easy to write in a way that does nothing, and a gate that
"passes the regression test" then proves nothing at all.

## What has since been done

**2026-09-29, same day: group 1 is fixed** — `fix/masthead-contrast-and-neutral-default`, filed as
**D-112**.

| | before | after |
|---|---|---|
| market runs below threshold | **734** | **66** |
| worst ratio on the market surface | 1.08:1 | 2.66:1 |
| corpus total | 1,387 | **719** |
| board combinations | 410 | **220** |
| `[CONTRAST] cannot reach 4.5:1` log lines per 90 renders | one per render | **0** |

**The band was fixed, not the text**, because measurement said the text could not be: for three of
the six brands no single colour clears 4.5:1 on both ends. Each stop is now darkened until the
**translucent** subtitle is readable on it, which makes the opaque title safe by construction and
keeps the muted subtitle rather than flattening it.

`DEFAULT_ACCENT` moved off Luxury Estates' teal to the platform `#4F46E5`, along with thirteen
template-level fallbacks that were shades of the same teal — the same defect one layer down,
reachable through any render path that omits the context value.

The 66 that remain on the market surface are group 4, the six semantic badge colours: one
decision, brand-independent, not taken here. **Groups 2, 3 and 5 are property-report work and are
untouched** — 653 runs, and the 1.00:1 invisible footer in `classic_report.jinja2:643` is still
there.
