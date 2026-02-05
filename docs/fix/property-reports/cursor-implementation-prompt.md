# Property Report PDF System — Implementation Plan for Cursor

## Context

I'm rebuilding the property report PDF template system. I have:

1. **New template files** in the `property-reports/` reference folder (base template, macros, 5 themes)
2. **An audit document** (`AssessmentPDF.md`) that documents the current system's bugs and inconsistencies
3. **A README** with the full architecture spec

The existing templates live in `apps/worker/src/worker/templates/property/` and the builder logic is in the worker app.

---

## Phase 1: Fix the PDF Engine Bug (DO THIS FIRST)

**File:** `apps/worker/src/worker/pdf_engine.py` (or wherever `render_pdf` lives)

The Playwright PDF renderer currently sets margins to `0.5in`. PDFShift (production) sets margins to `0`. This causes different output between local dev and production.

**Change:** Set Playwright margins to `0` on all sides. The CSS in the templates handles all margins internally via `--page-margin: 0.5in`.

```python
# Change Playwright options from:
margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"}

# To:
margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
```

Do NOT change the PDFShift configuration. Only change Playwright.

---

## Phase 2: Install New Template Files

Copy the new template structure into the worker templates directory:

```
apps/worker/src/worker/templates/property/
├── _base/
│   ├── base.jinja2          # Shared 7-page structure with {% block %} inheritance
│   └── _macros.jinja2       # 15 reusable component macros
├── bold/
│   └── bold.jinja2          # Extends _base/base.jinja2
├── classic/
│   └── classic.jinja2       # Extends _base/base.jinja2
├── elegant/
│   └── elegant.jinja2       # Extends _base/base.jinja2
├── modern/
│   └── modern.jinja2        # Extends _base/base.jinja2
└── teal/
    └── teal.jinja2          # Extends _base/base.jinja2
```

**Keep the old templates** until Phase 4 is complete. Don't delete them yet.

---

## Phase 3: Update the PropertyReportBuilder

**File:** `apps/worker/src/worker/property_report_builder.py` (or similar)

The builder needs to:

### 3a. Update the template mapping

```python
# Old mapping (theme number → filename)
THEME_TEMPLATES = {
    1: "bold_report.jinja2",
    2: "classic_report.jinja2",
    3: "elegant_report.jinja2",
    4: "modern_report.jinja2",
    5: "teal_report.jinja2",
}

# New mapping (theme number → path relative to templates/property/)
THEME_TEMPLATES = {
    1: "bold/bold.jinja2",
    2: "classic/classic.jinja2",
    3: "elegant/elegant.jinja2",
    4: "modern/modern.jinja2",
    5: "teal/teal.jinja2",
}
```

### 3b. Update the Jinja2 environment

The template loader needs to resolve `{% extends '_base/base.jinja2' %}` and `{% import '_base/_macros.jinja2' %}` correctly.

Set the Jinja2 `FileSystemLoader` search path to the `templates/property/` directory:

```python
from jinja2 import Environment, FileSystemLoader

template_dir = Path(__file__).parent / "templates" / "property"
env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=False,
)
```

This way when a theme file says `{% extends '_base/base.jinja2' %}`, Jinja2 will look for `templates/property/_base/base.jinja2`.

### 3c. Ensure custom filters are registered

The templates use these custom Jinja2 filters. Make sure they're registered:

```python
env.filters['format_currency'] = format_currency  # 1234567 → "$1,234,567"
env.filters['format_number'] = format_number       # 1234567 → "1,234,567"
```

These should already exist in the current codebase. Just verify they're still registered on the new environment.

### 3d. Ensure the context dict is unchanged

The data contract is identical to v1. The templates expect:
- `property` (dict)
- `agent` (dict) 
- `comparables` (list of dicts)
- `stats` (dict)
- `images` (dict)
- `theme_color` (string or None)

No changes needed to how the context is built.

---

## Phase 4: Test & Verify

Test each theme by generating a PDF with the sample data:

1. Generate a PDF for each theme (1-5) using both Playwright (local) and verify the output
2. Check that:
   - All 7 pages render correctly
   - Agent info appears on the LEFT, logo on the RIGHT
   - Footer is consistent on pages 2-7
   - `theme_color` override works (pass a hex color and verify primary color changes)
   - Agent photo renders in a circle
   - Logo handles different aspect ratios (test with wide, tall, and square logos)
   - Comparables grid shows 4 cards in 2x2 layout
   - Data tables display all property fields
3. Once verified, delete the old template files (bold_report.jinja2, classic_report.jinja2, etc.)

---

## Important Notes

- **Do NOT modify the new template files** — they've been designed as a coordinated system. CSS variables, macros, and blocks are interdependent.
- **The base template handles ALL shared structure** — headers, footers, page breaks, print CSS. Themes only override visual styling.
- **`theme_color` is the primary color** — when an agent picks a color in the wizard, it gets passed as `theme_color` and each theme applies it via `{{ theme_color | default('#...') }}` in the CSS.
- **Margins are now CSS-only** — the `--page-margin: 0.5in` variable controls all internal padding. The PDF engine must use margin: 0 on all sides.

---

## Files to modify (summary):

1. `pdf_engine.py` — Set Playwright margins to 0
2. `property_report_builder.py` — Update template paths and Jinja2 loader
3. `templates/property/` — Add new template files (keep old ones until verified)
4. Delete old templates after testing
