# Property report — handover to Claude Design

**Date:** 2026-10-01 · **Surface:** the five property-report themes
(`bold`, `classic`, `elegant`, `modern`, `teal`) · **Branch at handover:** `main`

Everything here is **measured**, not reviewed. Where a number appears, the command that
produced it is named, and it was re-run against `main` on the date above rather than quoted
from an earlier write-up. Two numbers in the defect list were wrong when re-derived this way;
both are corrected below and in `DEFECT_LIST.md`.

---

## 0 · Read this first: there are two template trees and one of them renders nowhere

**`<theme>/<theme>.jinja2` and everything in `templates/property/_base/` render nowhere. Do not read them, do not
port them, do not take their copy as current.** (D-131.)

> **UPDATED 2026-10-05 — THE THEME SET IS NOW THREE.** Jerry cut the themes to
> **bold, elegant and modern**. `classic` and `teal` are retired and their templates are
> deleted, which is why the counts below are smaller than in the copy you were sent. The
> rest of this document stands; where it says "five themes" or names classic or teal, read
> three. The six colours in section 1 are unchanged — none of them is teal's or classic's.

| tree | files | lines | rendered |
|---|---|---|---|
| `templates/property/_v2/report.jinja2` | 1 | **735** | **yes** — the shared page architecture |
| `templates/property/<theme>/<theme>_report.jinja2` | 3 | **1,549** | **yes** — `THEME_TEMPLATES` maps to exactly these |
| `templates/property/<theme>/<theme>.jinja2` | 3 | 2,749 | **no** |
| `templates/property/_base/base.jinja2` | 1 | 2,146 | **no** |
| `templates/property/_base/_macros.jinja2` | 1 | 675 | **no** |
| | **5 dead** | **5,570** | |

> **UPDATED AGAIN 2026-10-06 — BOLD IS ON YOUR ARCHITECTURE.** `bold_report.jinja2` is now
> **34 lines** — eight `{% set %}`s and an `{% include %}` — and the six pages live in
> `_v2/report.jinja2`, shared. elegant (720) and modern (795) are still self-contained and move
> next. The 1,549 in the table is those two plus bold's 34.

**There is still more dead property-template code than live.** 5,570 lines against 2,284 —
the ratio got *worse*, because the cut deleted one live file and one dead file per retired
theme while `templates/property/_base/` (2,821 lines, none of it rendered) stayed exactly where it was.

> **`templates/market/_base/` IS LIVE and is a different directory.** `market/market.jinja2` is one
> line — `{% extends '_base/base.jinja2' %}` — and that base imports `_base/macros.jinja2`. The two
> builders give their Jinja loaders different directories, so the same string names two different
> files depending on which surface is rendering. Every `_base/` in this document means the property
> one. (`docs/design-corrections/00-SHARED.md` already had this right: its table is per surface and
> lists `market/_base/` in the LIVE column.)

The dead three are near-complete copies of the live three and `bold.jinja2` looks exactly as
current as `bold_report.jinja2`. They are stale in ways you cannot see by reading them: they
still say *"comparable homes sold within the last **12 months**"* over a query that has used
**six** since D-117, and they still cap the comparables at four, which the live templates
stopped doing.

The live set is asserted to be exactly those three —
`test_one_comp_set.py::test_the_live_template_set_is_the_five_entry_files` fails if any of them
grows an `extends`, `import`, `include` or `from`. If you need shared markup, that test is the
thing to change deliberately, not to work around.

**The only files to open:**

```
apps/worker/src/worker/templates/property/_v2/report.jinja2          <- the six pages
apps/worker/src/worker/templates/property/bold/bold_report.jinja2    <- bold's type only
apps/worker/src/worker/templates/property/elegant/elegant_report.jinja2
apps/worker/src/worker/templates/property/modern/modern_report.jinja2
```

---

## 1 · Contrast: 213 failing runs, and six colours carry 146 of them

```
python3 scripts/render_property_production.py OUT bare
python3 scripts/render_property_production.py OUT full
python3 scripts/measure_contrast_by_pixel.py OUT --json OUT/measured.json
```

Ten documents — five themes × two variants (`bare` = the default 7-page set with no API keys,
the common case; `full` = market-trends and overview injected, Maps key present).

| | |
|---|---|
| text runs measured | **2,311** |
| failing WCAG (large-text allowance applied) | **213** |
| distinct `(family, selector, fg, bg)` combinations | **51** |
| declined — cannot be measured, see §3 | **2** |
| worst ratio | **1.90:1** |

| theme | failing |
|---|---|
| modern | **90** |
| teal | 40 |
| bold | 38 |
| classic | 35 |
| elegant | **12** |

**Nothing on this surface is invisible any more.** Six runs at 1.00–1.31:1 — including the page
number `03` rendered white-on-white on the aerial page in four themes — were fixed on
2026-10-01. A separate floor test, `test_no_invisible_text_in_property_reports.py`, fails on
anything below **1.5:1** with no baseline and no exceptions, because a ratchet can absorb an
invisible pairing by regeneration and that is exactly how white-on-white survived long enough
to be filed as a *missing* page number rather than an unreadable one.

### The six values

| # | theme | colour | against | ratio | needs | runs | where | **kind** |
|---|---|---|---|---|---|---|---|---|
| 1 | modern | `#94a3b8` | white, `#f1f5f9`, `#3b4053` | 2.34–4.01 | 4.5 | **31** | every secondary string, 9 selectors | **literal** `--silver` |
| 2 | bold | `#d69649` | white | 2.52 | 4.5 | **27** | `div.brand`, contents pages, cover agent title | **literal** `--gold` |
| 3 | classic | `#4a90a4` | white, `#fefdfa`, **and reversed** | 3.55–3.61 | 4.5 | **24** | page-header labels, Sale Price row | **literal** `--sky` |
| 4 | modern | `#c55145` | `#f1f5f9` | 4.13 | 4.5 | **24** | `div.contents-num`, `span.pill` | **derived** |
| 5 | modern | `#ff6b5b` | white on it | 2.55–2.80 | 4.5 | **22** | comp-card price, Sale Price row | **brand default** `--coral` |
| 6 | teal | `#34d1c3` | white, `#535d7d` | 1.90–3.42 | 3.0 / 4.5 | **18** | every `h2.section-title`, cover logo | **brand default** `--teal` |
| | | | | | | **146** | **of 213 — 69%** | |

**The three kinds are three different jobs, and this is the part a hex list hides.**

* **Literal (1, 2, 3 — 82 runs).** Hard-coded in the theme's `:root`. Change the hex and it is
  fixed. This is design work and nothing else.
* **Brand default (5, 6 — 40 runs).** `--coral` and `--teal` are
  `{{ theme_color | default('#FF6B5B') }}`. Changing the hex fixes the *default* and leaves
  every affiliate who chose their own colour with the identical failure. **The fix is a rule in
  the derivation, not a swatch** — "white on the brand colour" and "the brand colour on white"
  must both be guaranteed for any colour an affiliate can pick, which is a decision about what
  the system does when their brand fails, not about these two hexes.
* **Derived (4 — 24 runs).** `#c55145` is `derive_theme('#ff6b5b')['primary_ink']`. It appears
  as a literal nowhere. Fixing it means changing `worker/themes.py`, which is ours, not yours —
  but the *target ratio* it should derive to is yours.

The remaining 67 runs are a tail of fives: `#16a34a` in the market-trends change chips on each
theme's off-white, and `#999999` / `#6b7280` muted text.

### The tolerance: 12, and why it exists

`apps/worker/tests/test_pdf_contrast.py` holds a baseline keyed on
`(family, selector, foreground, background)` that may only shrink. The background is **sampled
from the rendered pixel**, so over a gradient it is "whatever shade sat under that run's own
rectangle" — not a property of the rule.

Which means **moving text changes its key**. Observed end to end on a failing run: modern's
`div.cover-city`, `#94a3b8` on `#3b4053` at 4.01:1. Add `padding-top: 120px` to `.cover-left`,
change no colour at all, and the sampled backdrop becomes `#3c4155` — distance 4, a new key,
and the gate reports a new colour pairing on a build where nothing about contrast moved. A
reviewer then either investigates a non-defect or regenerates the baseline, and regenerating to
clear a new failure is the one thing that file says never to do.

So keys match within a **total RGB distance of 12**, in both directions. The bound, measured
over the gate's 90-document corpus:

| distance | the two colours | what they are |
|---|---|---|
| 3 | elegant `#57860e` vs `#58880e` | one finding, two points on one gradient |
| 9 | teal `#3b4569` vs `#3e486c` | same |
| **18** | elegant `#f2faf9` vs `#faf7f2` | **mint-tinted page vs cream page — genuinely different** |
| 30 | modern `#f1f5f9` vs `#ffffff` | tinted panel vs page |
| 41 | bold `#0d9488` vs `#0e7490` | **two different brand colours** |

Twelve is above the observed churn (2, 3, 4) with headroom and below the closest pair that
genuinely differ (18). **The first recommendation was 48, and 48 merges two brands** — derived
from ten single-brand renders and applied to a ninety-document six-brand corpus.

**What this means for you:** layout changes are free; a colour change of more than ~4 per
channel will correctly show up as a new finding. If you move a lot of text and the ratchet
reports pairings you did not create, that is a bug in the tolerance and not in your work —
raise it rather than regenerating.

### The declined element

**Modern's cover title, `span "Report"`, cannot be measured and is counted as declined rather
than dropped** (2 runs — one per variant).

It is painted with a gradient clipped to the glyphs:

```css
background: var(--gradient-coral);
-webkit-background-clip: text;
color: transparent;
```

Both measurers are blind to it for the same reason and from opposite directions: the DOM walker
reads `color: transparent` and scores against nothing, and the pixel measurer blanks glyphs by
setting them transparent — the same property the template uses to paint them — so blanking it
is a no-op and it is sampled as its own backdrop.

Measured by hand against its gradient stops, its worst pair is **4.47:1 against a 3.0 threshold
for large text. It passes.** It was previously reported at 2.58:1, which was fiction.

**If you introduce more `background-clip: text`, the gate cannot see it.** Across the whole
90-document corpus there is exactly **one** such element today — this one, appearing in six
documents because modern renders under six brand colours. The sweep is
`scripts/find_unmeasurable_text.py` and it is cheap to run. Each element you add is a run
nobody is checking, and it will be reported as a number rather than as a gap.

---

## 2 · 19 fields that are always empty (17 of them undecided)

**Do not design a table around these.** They are read by the builders and written by nothing —
neither SiteX's `PropertyData` (28 keys) nor the wizard's payload (25 keys) produces them — so
they render `-` on every real report, permanently. **19 of the 41 fields the builders read off
that blob** (D-135).

```
zoning   garage   fireplace   census_tract   stories   housing_tract
lot_number   page_grid   partial_bath   tax_status   tax_rate_area
total_rooms   num_units   use_code   notes   pool   percent_improved
mailing_address   estimated_value
```

Two of the nineteen are already settled and are not open questions: **`mailing_address` is deliberately
excluded** on both the agent and consumer paths — for an absentee owner it is where a person
lives, not a fact about the property — and **`estimated_value` is D-134**, a separate decision
about what the product may compute.

The other seventeen are with Jerry as a product decision, framed as three options (source /
label / remove). **Until he answers, the Property Information block has rows that will never
have values in them**, and a redesign that gives them equal visual weight to the APN and the
legal description is a redesign of a block that is two-thirds empty.

The gate that found them is `apps/worker/tests/test_render_context_contract.py`; it asserts the
orphan set **exactly**, so it fails when one is fixed as well as when one appears.

---

## 3 · What changed under you in the last week

Not history for its own sake — each of these is a thing a redesign would otherwise undo.

| | what | why it is not negotiable |
|---|---|---|
| **D-116 / D-157** | the owner-of-record block renders **only** when `audience == 'agent'`; the consumer path does not carry the data at all | a report anyone can request on any address must not print a third party's name from the assessor roll |
| **D-157** | the consumer cover reads `Prepared for <the name on the lead form>`, and renders **no line** when the form supplied none | the fallback to the owner's name is the defect, not a graceful degradation |
| **D-159** | the comparables page shows four cards; **every** comparable appears on a continuation page; the range is computed over the set the reader can see | the page said "every one of the 15 appears" and showed four, with the range drawn over the eleven they could not see |
| **D-121** | the contents page and every page number are **derived from the page set** at render time | both were hardcoded, disagreed with each other, and claimed Market Trends at page 07 in reports with no such page |
| **D-137 / D-135** | an unknown value renders `-` or "N/A", never a default | `pool or "No"` asserted that a stranger's home has no pool |
| **D-125** | numbers are formatted in the **template**, via `| format_measure` | formatting them in the builder turned them into strings and silently narrowed an unrelated audit |
| **D-136** | two context builders that invented demographics (`51.5% female`) are **deleted** | nothing rendered them; the first "Neighborhood" page would have shipped fabricated census data |

**A copy inconsistency, flagged rather than fixed, because picking one is yours:** the document
now spells absence two ways — **`"N/A"`** from `format_currency(None)` and **`"-"`** from the
`ABSENT` constant. Both are honest. They are not the same word, and they appear in adjacent
cells of the same table.

---

## 4 · How to see your changes

```bash
# the ten production documents, through the real builder — not a sample harness
python3 scripts/render_property_production.py /tmp/out bare
python3 scripts/render_property_production.py /tmp/out full

# contrast, by reading the rendered pixel
python3 scripts/measure_contrast_by_pixel.py /tmp/out --json /tmp/out/m.json

# text no measurer can read
python3 scripts/find_unmeasurable_text.py

# brand hex literals that should be tokens
python3 scripts/lint_template_colors.py

# the gates
cd apps/worker && python -m pytest tests/test_pdf_contrast.py \
  tests/test_no_invisible_text_in_property_reports.py \
  tests/test_one_comp_set.py tests/test_contents_matches_the_document.py -q
```

**Render, do not read, to verify.** `scripts/generate_all_property_pdfs.py` exists and builds
its own Jinja environment rather than using the production builder — six PDFs reviewed from it
were not production renders, and that is why a $369,000 figure in them could not be accounted
for. `render_property_production.py` calls the real path and reimplements no filter.
