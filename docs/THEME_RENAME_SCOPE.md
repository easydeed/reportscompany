# Renaming a theme: what it costs

**Scoped, not implemented.** Jerry, 2026-10-05: *"Renaming is open… Not a decision yet — he'll take
it once the designs are wired and comparable side by side. Scope it while you're in the theme cut,
don't implement it."*

The live themes after the cut are **bold, elegant, modern** (ids 5, 3, 2); `classic` (1) and
`teal` (4) are retired and ids are never reused.

Every number here is produced by `scripts/derive_theme_name_scope.py`, which discovers rather than
asserts a list. Run it to reproduce them. **Measured after the theme cut**, on `feat/theme-cut`.

---

## The answer in one paragraph

**A rename is one mapping change plus one directory rename per theme. It is not a sweep, and it does
not need a data migration.** Change the `name` in `apps/worker/src/worker/themes.json`, run
`python3 scripts/gen_theme_registries.py`, rename the template directory and its two files, and you
are done — roughly **four edits and three file moves per theme renamed**. Nothing in the database
holds a theme name that anything reads. **Deferring the decision is cheap and stays cheap**, with
one exception, below.

Before the theme cut this answer would have been different: the pairing was stated in **18 places**
and two of them were wrong (D-163). The cut collapsed that to **one canonical file and two generated
ones**, which is what makes a rename small. The expensive part of renaming was never the names — it
was that nobody knew how many copies there were.

---

## 1 · Where a theme NAME appears, and where an ID appears

**82 name occurrences across 16 files** (was 147 across 18 before the cut). Grouped by what a rename
would have to do to them:

| group | files | occurrences | what a rename costs |
|---|---|---|---|
| **canonical** — `worker/themes.json` | 1 | 6 | **the edit itself** |
| **generated** — `api/theme_registry.py`, `web/lib/themes.generated.ts` | 2 | 17 | **nothing** — one command |
| **derives from the registry** — `property_builder`, `theme_registry`, `unified-wizard`, `wizard-types`, `gen_theme_registries`, `measure_pdf_contrast` | 6 | 17 | **nothing** — they import it |
| **historical, deliberately keeps retired names** — `affiliate/property-reports/page.tsx` | 1 | 10 | **nothing** — see §4 |
| **per-theme presentation metadata** — `web/lib/property-report-assets.ts` | 1 | 11 | **one `key:` per theme** |
| **the gate and the derivation** — `test_theme_registry_is_single_sourced.py`, `derive_theme_name_scope.py` | 2 | 12 | **nothing** — they read the registry |
| **golden/corpus scripts naming themes to seed data** — `regen_color_roles_golden.py`, `test_property_templates.py`, `test_market_templates.py` | 3 | 9 | **one literal each** |

The **ids** are what everything load-bearing actually keys on:
`accounts.default_theme_id` (INTEGER), `property_reports.theme` (INTEGER, `CHECK 1..5`),
`property_report_stats.theme_<name>` (five INTEGER columns), and every live theme list in the web app.
**A rename does not touch any of them.** That is the whole reason the answer is "cheap".

## 2 · The filesystem

**Three directories and six files** carry a theme name:

```
apps/worker/src/worker/templates/property/{bold,elegant,modern}/
  <theme>_report.jinja2   <- live, named in themes.json
  <theme>.jinja2          <- DEAD (D-131); renders nowhere
```

A rename is `git mv` on the directory and the two files, plus the one `"template"` string in
`themes.json`. Nothing else constructs those paths: `property_builder` reads
`THEME_TEMPLATES[name]`, which comes from the registry.

**Inside** a live template, each theme names itself **9 times** — all nine are the `<title>` tag and
eight CSS comments. Zero CSS custom properties are named after a theme. That was not true a day ago:
`teal_report.jinja2` had **39** `--teal-*` custom properties and 45 self-references, and renaming
*that* theme would have been a real sweep through its own stylesheet. **The three survivors have none.**

## 3 · The database

**Nothing in the database holds a theme name that anything reads.**

| place | holds | a rename needs |
|---|---|---|
| `accounts.default_theme_id` | INTEGER | nothing |
| `property_reports.theme` | INTEGER | nothing |
| `property_report_stats.theme_classic … theme_bold` | 5 INTEGER **columns named after themes** | see below |
| `report_generations.theme_id` | VARCHAR(20) holding a **mix of names and stringified ids** | nothing — **read by nothing** |

Two of these are worth stating plainly.

**`report_generations.theme_id` does hold names.** The market wizard POSTs a name (`"bold"`);
`routes/reports.py` writes a stringified id (`"5"`) into the same column when the caller sends none.
So the column is a mix. It would normally make a rename a data migration — except
**`MarketReportBuilder` reads no theme at all**, so every value in it is inert. That is filed as
**D-164**; it is a write with no consumer, and it is the single fact that keeps a rename off the
migration list.

**The five `theme_<name>` stats columns would need a rename to be a migration** — `ALTER TABLE …
RENAME COLUMN` on three tables, in two of which they appear twice. But they are *historical counters*
and two of them already name retired themes. The right answer is **don't rename them**: let
`theme_teal` keep meaning "reports generated in teal". `property_stats.py` now generates both the SQL
aliases and the response keys from the registry, so if a *rename* ever is wanted there, it is one
migration and no code change.

## 4 · Retired names stay, on purpose

Three surfaces deliberately keep `classic` and `teal`:

- `property_report_stats.theme_classic` / `theme_teal` — the counts of reports already generated.
- `/app/affiliate/property-reports` — the per-theme chart, keyed by name off the API response.
- `/admin/property-reports` — the per-row theme label, built from the generated **retired** set.

**41 of 44 accounts defaulted to teal before the cut**, so most of the history in those charts is a
retired theme. Dropping the two series would produce a dashboard saying those reports never happened.
`test_theme_registry_is_single_sourced.py::test_no_live_code_path_names_a_retired_theme` lists these
files in `RETIRED_NAME_ALLOWED`, each with its reason, and fails on any *other* file that names one.

## 5 · The tests and baselines

| artefact | theme-keyed rows | a rename needs |
|---|---|---|
| `apps/worker/tests/pdf_contrast_baseline.txt` | 118 entries: bold 37, elegant 50, modern 25, market 6 | **a `sed` on the family column** — the key is `property__<theme>` |
| `apps/worker/tests/golden/color_roles.json` | 3 `property_themes` keys | regenerate (`regen_color_roles_golden.py`) |
| `scripts/template_color_baseline.txt` | 34 lines naming a `property/<theme>/` path | **a `sed` on the path** |

This is the one place a rename is mechanical-but-fiddly: **152 baseline rows** key on the theme name,
and both files are ratchets whose whole point is that they may only shrink. A rename is a pure
substitution in both — the measured colours and selectors are unchanged — but it must be done as a
substitution, **not** by regenerating, or the diff stops being evidence of anything.

That is the exception to "cheap": **it is cheap only if done as a rename.** Regenerating those two
ratchets during a rename would discard the evidence that nothing else changed, and the review would
have no way to tell a rename from a colour regression.

## 6 · Is deferring cheap?

**Yes, and the cost does not grow with the designs landing — with one caveat.**

What makes it cheap is the single-sourced registry, which exists now and is gated. Nothing about
wiring Design's packages adds copies of the pairing: the gate fails any file that states two or more
id/name pairs, so a new copy cannot be introduced quietly. Measured: the gate fires on all **13**
regressions tried, including "a sixth copy of the map appears" and "a picker offers a theme the
renderer retired".

**The caveat is §5.** Every theme Design rewires adds contrast-baseline rows under
`property__<theme>`, and bold/elegant/modern already carry 112 between them. Renaming *after* three
rewires means a larger `sed` over a larger ratchet — more rows, same operation, same risk. So:

- **Renaming before the rewire**: ~4 edits, 3 file moves, 152 baseline-row substitutions.
- **Renaming after the rewire**: the same 4 edits and 3 moves, over however many baseline rows the
  new templates produce.

The decision does not get *harder*, only slightly more mechanical. **Jerry can take it after seeing
the designs side by side, as he wanted.** If he wants it to stay at today's size, the cheapest moment
is between the theme cut and the first rewire — i.e. now — but the difference is a substitution over
more rows, not a different kind of work.

## 7 · What would make it expensive, and does not apply

For the record, so the next reader can tell what changed:

- **A name in a URL or an asset path.** Preview images are id-keyed (`/previews/5.jpg`,
  `previews/<themeId>/<n>.jpg`), not name-keyed. Nothing to re-upload.
- **A name in a template's own stylesheet.** Teal had 39 `--teal-*` custom properties. The three
  survivors have **zero**.
- **A name persisted and read.** `report_generations.theme_id` holds names and is read by nothing
  (D-164).
- **A name in a customer-visible saved object.** Schedules store `default_theme_id` (an integer) via
  the account; nothing stores a name.
