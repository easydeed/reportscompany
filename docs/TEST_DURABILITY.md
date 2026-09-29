# Which tests survive a template replacement, and which leave with the templates

**Written 2026-09-28**, on the news that Claude Design is producing new market and property
templates that will be wired in. Workstream C's and D's visual output is therefore interim; the
tests written alongside it are not, or should not be. This is an inventory of which is which.

**The question each row answers:** if every `.jinja2` under `templates/` were replaced tomorrow
with a differently-structured set that rendered the same reports, would this test still be doing
its job — would it still catch the defect it was written for?

Three verdicts:

| | |
|---|---|
| **DURABLE** | keeps working, unchanged, against templates nobody has written yet |
| **NEEDS GENERALISING** | tests a real property but reads it through markup that will not survive |
| **GOES WITH THE TEMPLATES** | asserts a specific rendering; expected to be rewritten, and that is correct |

---

## DURABLE — keep these, they are the valuable half

| test | what makes it durable |
|---|---|
| `test_zero_conditionals.py` + `_zero_conditionals.py` | Numeric names **derived** from the builders' own contexts; templates found by walking the tree; each parsed with Jinja's parser and `ast`; "handled" judged as *the conditional has an `{% else %}`*, never as the presence of a word. Exemptions keyed by leaf name, so a new template inherits the ones it has earned. Covers Python too. |
| `test_themes.py`, `test_color_roles.py` | Test `worker.themes` — a Python token layer with no markup in it at all. Templates consume it; nothing here reads one. |
| `test_monthly_trend.py` (the series half) | `compute/monthly_trend.py`'s maths: gaps stay gaps, a one-sale month is not a median, a truncated fetch is refused. No markup. |
| `test_extract_field_paths.py` | Runs the extractor over captured fixtures and checks each read against the payload's real shape. Vendor-facing, template-blind. |
| `test_market_layout_map.py` | Derives the layout map by **instrumenting `jinja2.runtime.Macro.__call__`** rather than reading the source. Survives any macro set — though `REPORT_BLOCKS`, the declaration it compares against, is content that will need re-deriving (see below). |
| `test_pdf_source_url.py`, `test_pagination.py`, `test_months_of_supply.py`, `test_inventory_median_price.py` | Builder and engine behaviour, asserted on returned values. |
| `tests/test_defect_list_counts.py` | Parses this repo's defect list. Nothing to do with templates. |

---

## NEEDS GENERALISING — real properties, read through markup that will not survive

These are the ones worth spending time on **before** the new templates land, because each will
either break loudly (fine) or pass vacuously (not fine) once the markup moves.

### 1. `_contrast_audit.py` — the contrast walker

**The property is exactly right and the walker is good work:** resolve every text run's background
by walking ancestors, measure the ratio, fail on anything unreadable. It found 1,167 unreadable
runs and drove them to 0.

**What pins it:** it resolves backgrounds from **inline `style="…"` attributes only**, because
email has no usable cascade and every rule in the email templates is inline. Its only caller is
`test_email_contrast.py`. **The market and property PDFs are not audited at all** — they are
rendered by a real browser from a `<style>` block, so their colours are set by CSS rules the
walker cannot see.

**Generalising it:** resolve a `<style>` block's rules too, at least for class and element
selectors, and point it at the market and property renders. That is the difference between a
contrast gate for one surface and a contrast gate for the product. New templates are the moment to
do it, because whatever Claude Design produces will be stylesheet-driven and currently arrives
unaudited.

### 2. `scripts/lint_template_colors.py` + `template_color_baseline.txt`

**What pins it:** the baseline is 119 lines keyed by **file path**, one per hex literal. A
replacement template set invalidates every line whose path changes. The rule ("this file may only
shrink") then means nothing, because the file it shrinks against describes files that no longer
exist.

**Generalising it:** the baseline should be a **count per rule**, or keyed by something stabler
than a path; and the check should assert the count does not grow rather than that a specific line
is still present. The lint's detection logic is path-independent already — only the baseline is
pinned.

### 3. `test_block_structure.py` — the block gate

**The property is the one nothing else can check:** a restructure's premise is that output does not
change, so every output-shaped assertion passes whether or not the restructure happened. This
catches an orphaned block, and it caught a real one.

**What pins it:** `REPORT_BLOCKS` is a **declaration of which blocks each report type renders**,
by name. It is currently correct because it was derived from a trace, but it is a list of the
present block set and a new template set replaces it wholesale. The mechanism (compare a traced
render against a declaration) is durable; the declaration is content.

**Generalising it:** keep the mechanism, and make `REPORT_BLOCKS` **regenerable by the same trace
that verifies it** — with the regeneration a deliberate, reviewable step, the way
`golden/themes.json` works. The gate then survives the replacement at the cost of one re-derive,
rather than being deleted as broken.

### 4. `test_page_architecture.py` — the §7.1 four facts

**The property matters more than most:** both PDFShift `start_at` values must be 1, the header slot
must carry the running head and not the masthead, the masthead must be body content, and each
reservation must equal what its document paints. PDFShift accepts a mismatched pair with a 200 and
silently applies `max(header, footer)` to both, so nothing else in this repository can see the
damage.

**What pins it:** it reads `page_header.jinja2`, `page_footer.jinja2`, `base.jinja2` and
`macros.jinja2` **by filename**, and checks for the strings `running-head`, `.rh-gap`, `.pf-gap`
and `<span class="rh-name">`. A new template set with different filenames or class names makes
these either error (loudly, fine) or — worse — pass on a template that no longer does what the
test thinks.

**Generalising it:** the `start_at` half is already durable, because it reads `PDF_CONFIG` in
Python. The rest should assert against **what `render_page_header_html()` and
`render_page_footer_html()` return** rather than against the files behind them, and measure the
painted height rather than look for a named gap element.

### 5. `test_narrative_box.py` — the §7.2 budget, and `PAGE_1_CAPACITY`

**What pins it:** it regex-matches the `.ai-narrative-text { height: calc(N * Xem) }` rule out of
`base.jinja2`, and `PAGE_1_CAPACITY` pins measured per-page listing counts for eight report types.
Both describe the current layout precisely, and both are meaningless against a different one.

**Generalising it:** the pairing it protects — *a copy budget and the box it must fit are one
decision* — is durable and worth restating for whatever box replaces this one. The numbers are
not, and `scripts/measure_market_pagination.py --emit-capacity` already exists to re-derive them.
**Point the re-pin at the script, not at a person**: the capacity table has been re-pinned three
times and transcription is the step that has failed.

### 6. `test_email_render_diff.py` — the render-facts baseline

**What pins it:** a recorded baseline of every text run, link, image, custom property and class in
the email documents. It is doing exactly its job for Workstream C's restructure — but it is a
snapshot, and a redesign is a legitimate reason for all of it to change. Regenerating it is a
one-line script (`scripts/regen_email_facts.py`); the risk is that regenerating becomes reflexive
and stops being read.

**Generalising it:** nothing to change mechanically. Worth stating on the entry that a regeneration
diff is **the review artefact**, not a chore, and should not be squashed into an unrelated commit.

---

## GOES WITH THE TEMPLATES — expected to be rewritten, and that is correct

These assert a specific rendering. They are not defects; they are the copy and layout decisions
made in Workstreams C and D, written down where they can be checked. A new template set is
entitled to make them differently, and these should be rewritten alongside it rather than
preserved.

* `test_zero_conditionals.py`'s last three tests — "Studio", "New", and the empty-state wording.
  **Deliberately separated from the structural gate in the same file**, with a docstring saying so.
* `test_band_chart.py`, `test_monthly_trend.py`'s SVG-shape assertions — bar geometry, marker
  radius, label placement.
* `test_theme_cover_title.py`, `test_null_columns_render.py`, `test_email_mobile_and_contact.py`,
  `test_email_footer_links.py` — each asserts on rendered HTML for a specific template.
* The `golden/` files.

---

## The one thing to do first

**Point the contrast auditor at the PDF surfaces before the new templates land, not after.**

Every other item here fails loudly when its markup moves — a missing file, a regex that matches
nothing, a count that disagrees. The contrast auditor is the only one that will keep passing while
covering nothing, because it already covers nothing on those surfaces. `test_email_contrast.py` is
green today and walks only the email documents. **No document-wide contrast walk has ever been run
over a market or property PDF.** What exists there is two narrow assertions in
`test_monthly_trend.py` — the trend line wears `primary_ink`, and axis text wears neither the ink
nor the raw brand colour — each found by regex over the chart's own SVG, covering one element in
one chart.

A new template set arriving into that gap looks exactly like a new template set arriving into a
working gate: `test_email_contrast.py` stays green, because it was never looking.
