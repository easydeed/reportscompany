# Contrast audit — property PDFs — 2026-09-29

**The first contrast measurement the property report has had**, and the first measurement of any
kind taken through the path production takes.

## What was measured

Ten documents: five themes (`bold`, `classic`, `elegant`, `modern`, `teal`) × two variants.

* **bare** — no `GOOGLE_MAPS_API_KEY`, no agent photo, the default seven-page set. The common
  production state.
* **full** — Maps key set, agent photo set, all nine pages including `overview` and
  `market_trends`. Those two pages had never been measured by anything.

Rendered by `scripts/render_property_production.py`, which shapes `report_data` exactly as
`property_tasks/property_report.py`'s `fetch_report_with_joins()` returns it and then calls the
real `PropertyReportBuilder`. It reimplements no filter and no context key — which is precisely
what `scripts/generate_all_property_pdfs.py` does, and why the six PDFs the E register was written
from are not evidence about production.

Measured by `scripts/measure_contrast_by_pixel.py`, which reads the rendered pixel rather than
hit-testing the DOM. See **D-130** for why: the existing `measure_pdf_contrast.py` walker produces
22 false positives on this surface in 1,965 shared runs, by two mechanisms, and **zero** misses.
As a gate the walker is sound; as a count it is inflated here by roughly 10%.

## How this relates to the 653 figure

The 2026-09-29 market audit reported **653** failing runs on the property surface. Different
corpus and different method: 30 documents (five themes × six brand colours), rendered from
`measure_pdf_contrast.py`'s own minimal fixture with no market-trends or overview page, measured
by the DOM walker.

**229 is the production-path, pixel-verified number for ten documents.** Neither supersedes the
other. The brand sweep is still owed on this surface and will raise the count.

## Headline

* **229** of 2,344 text runs fail their WCAG threshold, in **48** distinct
  (selector, colour, background) combinations. Large-text allowance applied, not ignored.
* **Worst is 1.00:1** — literally invisible. The page number on the Aerial View page is white on
  white in bold and classic, and 1.07:1 / 1.11:1 in teal and elegant. That is E15's real
  mechanism: the register read it as "the aerial page carries no number".
* **Modern is four times worse than elegant** (91 vs 16), and almost all of it is two token
  definitions: `#94a3b8` for every secondary string, and `#ff6b5b` as a fill behind white text.
  This is D-112's shape again — a handful of role definitions, not a long tail.
* The market-trends gauge zone labels (`Seller's`, `Balanced`, `Buyer's`) fail in all four themes
  that carry the page, at 2.25–3.30:1. The plan calls that page "the strongest single page in the
  entire product".

Filed as **D-129**. The walker's false positives are filed separately as **D-130**.

## Reproducing

```
python3 scripts/render_property_production.py /tmp/eprop bare
python3 scripts/render_property_production.py /tmp/eprop full
python3 scripts/measure_contrast_by_pixel.py /tmp/eprop --json /tmp/eprop/findings.json
```

## The measurement

```
2344 text runs in 10 documents
250 below 4.5:1 · 229 below their WCAG threshold · worst 1.00:1
206 runs straddle two backdrops across their own width (modal pixel used)

document                        runs    fail
----------------------------------------------
property__bold__bare             200      14
property__bold__full             250      27
property__classic__bare          199      13
property__classic__full          249      26
property__elegant__bare          200       2
property__elegant__full          250      14
property__modern__bare           188      29
property__modern__full           238      62
property__teal__bare             260      11
property__teal__full             310      31

229 failing runs in 48 distinct (selector, colour, background) combinations

 1.00:1  #ffffff on #ffffff  needs 4.5:1  (4 runs)
         div.num
         property__bold__bare, property__bold__full, property__classic__bare, property__classic__full
         e.g. '03'

 1.00:1  #ffffff on #ffffff  needs 4.5:1  (2 runs)
         div.brand
         property__classic__bare, property__classic__full
         e.g. 'Classic Collection • TrendyReports'

 1.07:1  #ffffff on #f7f7f9  needs 4.5:1  (2 runs)
         div.num
         property__teal__bare, property__teal__full
         e.g. '03'

 1.11:1  #ffffff on #f3f3f3  needs 4.5:1  (2 runs)
         div.num
         property__elegant__bare, property__elegant__full
         e.g. '03'

 1.31:1  #e8d5a3 on #f3f3f3  needs 4.5:1  (2 runs)
         div.brand
         property__elegant__bare, property__elegant__full
         e.g. 'Elegant Collection'

 1.78:1  #34d1c3 on #f7f7f9  needs 4.5:1  (2 runs)
         div.brand
         property__teal__bare, property__teal__full
         e.g. 'TrendyReports'

 1.90:1  #ffffff on #34d1c3  needs 4.5:1  (4 runs)
         span.ico
         property__teal__bare, property__teal__full
         e.g. '☎'

 1.90:1  #34d1c3 on #ffffff  needs 3.0:1  (2 runs)
         div.cover-logo-text
         property__teal__bare, property__teal__full
         e.g. 'TR'

 1.90:1  #34d1c3 on #ffffff  needs 3.0:1  (10 runs)
         h2.section-title
         property__teal__bare, property__teal__full
         e.g. 'PROSPECTIVE PROPERTY'

 2.17:1  #aaaaaa on #faf7f2  needs 4.5:1  (2 runs)
         p
         property__elegant__full
         e.g. 'Data source: MLS ·\n            La Verne ·\n            Last 9'

 2.25:1  #ffffff on #c9a962  needs 4.5:1  (2 runs)
         div.mt-gauge-zone.mt-gauge-zone--balanced
         property__elegant__full
         e.g. 'Balanced'

 2.34:1  #94a3b8 on #f1f5f9  needs 4.5:1  (4 runs)
         div.brand
         property__modern__bare, property__modern__full
         e.g. 'Modern Collection'

 2.34:1  #94a3b8 on #f1f5f9  needs 4.5:1  (6 runs)
         div.mt-card-label
         property__modern__full
         e.g. 'Median Sale Price'

 2.34:1  #94a3b8 on #f1f5f9  needs 4.5:1  (1 runs)
         div.mt-card-note
         property__modern__full
         e.g. 'Avg $745,000'

 2.52:1  #d69649 on #ffffff  needs 4.5:1  (2 runs)
         div.cover-agent-title
         property__bold__bare, property__bold__full
         e.g. 'Real Estate Professional • CA BRE#01234567'

 2.52:1  #d69649 on #ffffff  needs 4.5:1  (13 runs)
         div.contents-page
         property__bold__bare, property__bold__full
         e.g. '04'

 2.52:1  #d69649 on #ffffff  needs 4.5:1  (13 runs)
         div.brand
         property__bold__bare, property__bold__full
         e.g. 'Bold Collection • TrendyReports'

 2.55:1  #ff6b5b on #f1f5f9  needs 3.0:1  (2 runs)
         div.range-slider-price.low
         property__modern__bare, property__modern__full
         e.g. '$470k'

 2.56:1  #94a3b8 on #ffffff  needs 4.5:1  (7 runs)
         div.brand
         property__modern__bare, property__modern__full
         e.g. 'Modern Collection'

 2.56:1  #94a3b8 on #ffffff  needs 4.5:1  (2 runs)
         div
         property__modern__full
         e.g. 'Real Estate Professional · TrendyReports'

 2.56:1  #94a3b8 on #ffffff  needs 4.5:1  (1 runs)
         div.mt-subtitle
         property__modern__full
         e.g. 'La Verne - Last 90 Days'

 2.56:1  #94a3b8 on #ffffff  needs 4.5:1  (1 runs)
         div.mt-gauge-label
         property__modern__full
         e.g. 'Months of Inventory'

 2.56:1  #94a3b8 on #ffffff  needs 4.5:1  (5 runs)
         span
         property__modern__full
         e.g. '0 mo'

 2.56:1  #94a3b8 on #ffffff  needs 4.5:1  (2 runs)
         p
         property__modern__full
         e.g. 'Data source: MLS ·\n            La Verne ·\n            Last 9'

 2.58:1  #ffffff on #ff786a  needs 3.0:1  (2 runs)
         span
         property__modern__bare, property__modern__full
         e.g. 'Report'

 2.64:1  #999999 on #f8f6f3  needs 4.5:1  (1 runs)
         div.mt-card-note
         property__elegant__full
         e.g. 'Avg $745,000'

 2.66:1  #faf3e6 on #ca8a04  needs 4.5:1  (8 runs)
         div.mt-gauge-zone.mt-gauge-zone--balanced
         property__bold__full, property__classic__full, property__modern__full, property__teal__full
         e.g. 'Balanced'

 2.67:1  #999999 on #faf7f2  needs 4.5:1  (5 runs)
         span
         property__elegant__full
         e.g. '0 mo'

 2.80:1  #ff6b5b on #ffffff  needs 4.5:1  (2 runs)
         div.cover-agent-title
         property__modern__bare, property__modern__full
         e.g. 'Real Estate Professional'

 2.80:1  #ffffff on #ff6b5b  needs 4.5:1  (10 runs)
         td
         property__modern__bare, property__modern__full
         e.g. 'Sale Price'

 2.80:1  #ffffff on #ff6b5b  needs 4.5:1  (8 runs)
         div.comp-card-price
         property__modern__bare, property__modern__full
         e.g. '$631,500'

 2.96:1  #e8f6ed on #16a34a  needs 4.5:1  (8 runs)
         div.mt-gauge-zone.mt-gauge-zone--sellers
         property__bold__full, property__classic__full, property__modern__full, property__teal__full
         e.g. "Seller's"

 3.01:1  #16a34a on #f1f5f9  needs 4.5:1  (5 runs)
         div.mt-card-change.mt-card-change--good
         property__modern__full
         e.g. '▲              4.3% vs prior 90 days'

 3.05:1  #16a34a on #f4f6fb  needs 4.5:1  (5 runs)
         div.mt-card-change.mt-card-change--good
         property__teal__full
         e.g. '▲              4.3% vs prior 90 days'

 3.12:1  #16a34a on #fdf8f3  needs 4.5:1  (5 runs)
         div.mt-card-change.mt-card-change--good
         property__bold__full
         e.g. '▲              4.3% vs prior 90 days'

 3.19:1  #16a34a on #fdfbf7  needs 4.5:1  (5 runs)
         div.mt-card-change.mt-card-change--good
         property__classic__full
         e.g. '▲              4.3% vs prior 90 days'

 3.30:1  #ffffff on #16a34a  needs 4.5:1  (2 runs)
         div.mt-gauge-zone.mt-gauge-zone--sellers
         property__elegant__full
         e.g. "Seller's"

 3.36:1  #279c92 on #ffffff  needs 4.5:1  (2 runs)
         div.agent-role
         property__teal__bare, property__teal__full
         e.g. 'Real Estate Professional'

 3.42:1  #34d1c3 on #535d7d  needs 4.5:1  (2 runs)
         div.brand
         property__teal__bare, property__teal__full
         e.g. 'TrendyReports'

 3.55:1  #4a90a4 on #fefdfa  needs 4.5:1  (2 runs)
         div.cover-label
         property__classic__bare, property__classic__full
         e.g. 'Comprehensive Property Analysis'

 3.61:1  #4a90a4 on #ffffff  needs 4.5:1  (12 runs)
         div.page-header-label
         property__classic__bare, property__classic__full
         e.g. 'Report Overview'

 3.61:1  #ffffff on #4a90a4  needs 4.5:1  (10 runs)
         td
         property__classic__bare, property__classic__full
         e.g. 'Sale Price'

 4.01:1  #94a3b8 on #3b4053  needs 4.5:1  (2 runs)
         div.cover-city
         property__modern__bare, property__modern__full
         e.g. 'La Verne, CA 91750'

 4.13:1  #fce9e9 on #dc2626  needs 4.5:1  (8 runs)
         div.mt-gauge-zone.mt-gauge-zone--buyers
         property__bold__full, property__classic__full, property__modern__full, property__teal__full
         e.g. "Buyer's"

 4.13:1  #c55145 on #f1f5f9  needs 4.5:1  (13 runs)
         div.contents-num
         property__modern__bare, property__modern__full
         e.g. '02'

 4.13:1  #c55145 on #f1f5f9  needs 4.5:1  (12 runs)
         span.pill
         property__modern__bare, property__modern__full
         e.g. 'Location Overview'

 4.47:1  #6b7280 on #f4f6fb  needs 4.5:1  (6 runs)
         div.mt-card-label
         property__teal__full
         e.g. 'Median Sale Price'

 4.47:1  #6b7280 on #f4f6fb  needs 4.5:1  (1 runs)
         div.mt-card-note
         property__teal__full
         e.g. 'Avg $745,000'

```
