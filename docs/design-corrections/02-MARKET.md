# Corrections for Design — market reports

**Read `00-SHARED.md` first.** Three items are shared with the property report and answered
there once.

**One real decision in here** (§2), and it is a decision rather than an error — the cost is
measured and attached, and the choice is yours.

---

## What you got right

* **One template, seven kinds.** The live build *already* dispatches on layout from a single
  `market.jinja2`; collapsing the seven separate files matches where the code had gone and the
  handoff hadn't. The shared masthead / footer / table partials are the right decomposition.
* **Headline rules as builder functions that return `null`, with the template rendering a plain
  title on `null`.** That is exactly the right shape. The threshold lives in one place, and the
  absence of a headline is a *value* rather than a missing branch — which is the difference
  between a report that says nothing and a report with a hole in it.
* **"Counts of zero in the band → still render the number ('0 homes sold'). Zero is data, not
  absence."** You wrote, unprompted, the rule this codebase has filed three defects about. It
  belongs in the shared package verbatim.
* **Deltas under 1% render "flat"; headlines hidden under 10 sales.** Both stated as thresholds
  rather than judgement, which means they can be tested.
* **"Status/delta colour: text only, never fills."** Aimed precisely at this surface's only
  remaining contrast defect. It needs one more step to land — see `00-SHARED.md` §S3 — but the
  diagnosis is right and nobody here had made it.
* **Page count derived from row count**, and a continuation footer that states "Rows a–b of N".
* **The same designed missing-photo state as the property package**, which means the product has
  one treatment across both surfaces for the first time.

---

## 1 · The surface line names the legacy path

> *"Surface: `apps/web/templates/trendy-*.html` + the worker PDF builder"*

`apps/web/templates/trendy-*.html` is the **legacy** renderer. Not inferred — the repository
says so in its own comments:

```python
# tasks.py:1677
# Always render via the new MarketReportBuilder. The legacy
# /print/{runId} frontend path produced unbranded PDFs missing the
# Outfit font, themed header, and AI narrative — so we never fall back to it.
```

```python
# pdf_engine.py:75
# `{print_base}/print/{run_id}` renders the LEGACY build
# (apps/web/app/print/[runId]/page.tsx + the trendy-*.html templates),
# which is a different document from the one this function just produced:
# different pagination, no themed header, no AI narrative.
```

The live market PDF is `MarketReportBuilder` → `templates/market/market.jinja2` + `market/_base/`
(2,479 lines). The legacy renderer is still reachable in code, only when the caller passes no
HTML — and the market task always passes HTML.

**Two of the three things you report removing were never in a customer's PDF.** The violet→coral
gradient (`--pct-blue: #7C3AED`, `--pct-accent: #F26B2B`) and the red "PDF" badge exist in all
seven `trendy-*.html` and in **none** of the live market templates. The four-chip metric ribbon
and the generic explainer paragraphs are real and worth removing.

This is not your fault — nothing marked that path as legacy anywhere a designer would look. But
it is why §2 happened.

---

## 2 · THE DECISION: the running head

> *"No running head. The brand band on page 1 and the strip on pages 2+ are both body content.
> The only PDFShift element is the footer, starting at page 1."*

**The live market template has a running head**, and it was built four days before your handoff,
specifically to satisfy the constraint you quote correctly elsewhere.

### Why it exists

The original architecture asked for a full masthead on page 1 and a slim running head after it.
That is `header.start_at = 2` with `footer.start_at = 1` — and **PDFShift accepts that pair with
an HTTP 200 and silently applies `max(header, footer)` to both.** Ask for the footer from page 1
and the header from page 2, and you get neither: you get both from page 2, with no error and no
warning. Four renders, marker-searched per page, to establish that. The API does not document
the coercion.

So the masthead moved **out** of the header slot and into the document body, where it renders
once at the top of the flow, and the header slot carries only the slim running head. Both
`start_at` values stay at 1, nothing is asked to differ, nothing is coerced — and the running
head consequently appears on page 1 too, above the masthead.

### What it bought, measured

| | before | after |
|---|---|---|
| top reservation | 1.3in reserved / 1.165in painted, + 0.1in margin | **0.44in / 0.417in**, no margin |
| bottom | 0.9in / 0.781in, + 0.1in margin | **0.89in / 0.885in**, no margin |
| **reserved on every page** | **2.4in of 11in — 21.8%** | **1.33in — 12.1%** |

**1.07in recovered on every page.** In documents:

* `closed` went from 6 pages to **5**, and 25 rows per continuation page to **29**
* `new_listings` went from 18 pages to **16**

### What removing it costs

Your layout puts the band on page 1 and a strip on pages 2+, both as body content. That is
coherent, and it is **not** the same thing as the current architecture — the running head is
what makes pages 2+ cheap. Specifically:

1. **The page-1 band must carry its own background as body content.** That part you already
   have, and it is the same move variant A makes.
2. **The strip on pages 2+ is body content, so it has to be emitted per page.** In a paged flow
   there is no per-page body hook: CSS `padding-top` applies once at the start of the flow, not
   after each break. Today the strip's equivalent is the PDFShift header, which is per-page by
   construction. Without it, continuation pages either repeat the strip because the *table
   partial* emits it per chunk — which means pagination moves into the builder — or they sit
   flush against the top margin.
3. **The reservations go back to being negotiated.** `test_page_architecture.py` asserts that
   each reservation matches what its document paints; with no header document there is nothing
   to match, and the top reservation becomes whatever margin you set.

**None of that makes your version wrong.** A report with no running head and a per-chunk strip
is a legitimate architecture and arguably a cleaner one — you already compute `P` from the row
count, so the builder is already doing pagination arithmetic.

**What we need from you is the choice, knowingly made.** If the running head goes:

* the strip has to be emitted by the table partial per chunk, not by a page hook;
* `header.start_at` / `footer.start_at` must both stay at 1 regardless, or the footer vanishes
  from page 1 with a 200;
* the 1.07in comes back out of every page, so `PAGE_1_CAPACITY` and the continuation row counts
  both move — see §3.

If it stays, your page-1 band sits below a 40px running head, which is what the property report
already does and what the two surfaces would then share.

---

## 3 · Page-1 capacity, the title ladder, and the narrative box

These three are one problem: **page-1 capacity must not depend on content**, and the live build
spends three mechanisms on it.

### 3a · `PAGE_1_CAPACITY` is per type *and* per narrative state

Your spec: *"13 rows page 1, 26 on continuation"* for closed and inventory.

The live pinned values:

```
closed:    15 without narrative,  11 with
inventory: 15 without narrative,  11 with,  5 with trend
price_bands:  3 / 2
new_listings: 3 / 2
market_snapshot: 3 / 3 / 0 with trend
galleries:    6 / 6
```

13 is neither 15 nor 11, there is no narrative variant, and closed and inventory are given the
same number. **Your row heights differ from the live ones, so the live numbers do not transfer
either** — the point is the *shape*: a flat capacity is what these values exist to replace,
because a report that fits 13 rows with no narrative fits fewer with one, and the overflow is
silent.

**Re-measure for your layout, per type and per narrative state, and pin the numbers.**

### 3b · The narrative box needs a stated fixed height

The live `.ai-narrative-text` has a **fixed** `height: calc(N * Xem)`, and a test reads that CSS
rule to enforce it — because the decision was that page-1 capacity cannot depend on the length
of model-generated prose.

Your headline sentences are template-filled from data with stated thresholds, which bounds the
*content* well. But **no fixed box height is specified**, so there is nothing for the test to
read and nothing stopping a long interpolated city name or a two-clause headline from adding a
line. Give the box a height.

### 3c · The title ladder is a rule of thumb where the live one is a measurement

Yours: *"if an area name exceeds ~22 characters at 22px, shrink the label to 18px rather than
wrap to three lines."*

Live: a four-step ladder with a floor —

```python
_TITLE_LADDER = ((27, 24), (33, 21), (38, 18), (43, 16))
_TITLE_MIN_PX = 14
```

— derived from measured character capacities (24px/31 chars, 21px/38, 18px/43, 16px/49,
14px/56), with the comment noting they are fallback-font widths with a deliberate margin, so a
slightly-too-large step costs an ellipsis rather than a wrapped line.

Two steps may well be enough at your type sizes. **It has not been measured, and the height is
the thing page-1 capacity actually depends on.** Measure it, or state the box height and let the
ellipsis absorb the rest.

---

## 4 · Good news: this surface was measured, and it is in good shape

Nobody had a current number for the market reports. The last audit predates the rebuild that
Workstreams C and D did. So we measured it before judging your output, over the gate's own
60-document corpus — 10 report types × 6 brands — with the pixel instrument:

| | |
|---|---|
| text runs | **5,058** |
| failing WCAG | **66** |
| distinct combinations | **6** |
| unmeasurable | **0** |
| worst | **2.66:1** |

**1.3% of runs. The property surface is at 9.2%.**

**All sixty-six are status or tier badges.** No brand-colour failure. No neutral failure. No
text-over-image problem. Nothing else on the surface fails at all.

| ratio | pairing | runs |
|---|---|---|
| 2.66 | `#ca8a04` on `#faf3e5` — "Pending" | 18 |
| 2.85 | `#d97706` on `#fef1db` — tier "High" | 6 |
| 2.89 | `#16a34a` on `#def6e7` — tier "Median" | 6 |
| 2.95 | `#16a34a` on `#e7f6ed` — "Active" | 18 |
| 4.12 | `#dc2626` on `#fbe9e9` — "Closed" | 12 |
| 4.35 | `#2563eb` on `#e2ecfe` — tier "Low" | 6 |

**This is a surface in good shape, and it is the first time anyone has known that.** Your
redesign is not rescuing a broken page — it is replacing a working one, which is a different
brief and a higher bar. The one thing it must not do is lose the 66-and-nothing-else property.

Your *"status colour: text only, never fills"* is pointed at exactly these. It needs the ink
step from `00-SHARED.md` §S3 to finish the job.

---

## 5 · What we could not check

Stated rather than glossed.

* **`Report Page Gallery.dc.html` renders its seven frames empty** outside your environment —
  the embed mechanism does not resolve. So the contrast figure for *your* design is **one report
  type (snapshot) on one brand**: 57 runs, 4 failing, both of them the shared mistakes in
  `00-SHARED.md`. The other six types and every other brand are unmeasured.
* **Google Fonts is blocked in our container**, so type fell back to system faces. Font sizes are
  inline literals, so the WCAG thresholds are exact; glyph widths and wrapping are not.
* **`PDF Reports v2.dc.html`** — we read §3a as you directed and did not audit the rejected
  directions.

If you can supply the gallery as static renders, or tell us how to drive the Tweaks panel
headlessly, we will measure all seven across all six brands and send the table back.
