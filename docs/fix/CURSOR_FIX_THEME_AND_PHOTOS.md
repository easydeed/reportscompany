# Cursor Prompt: Fix Branding Theme + Comp Photos

Two bugs to fix. Both are straightforward.

---

## Fix 1: Branding Default Theme Not Carrying Over to Property Reports

The frontend is wired correctly on both sides — branding page sends `default_theme_id`, property wizard reads it. But the backend silently drops it. Four changes needed in `apps/api/src/api/routes/account.py` plus one DB migration.

### Step A: Create DB Migration

Create a new migration file that adds the column:

```sql
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS default_theme_id INTEGER DEFAULT 4;
```

Default is 4 (Teal) — matches the current hardcoded fallback.

Place the migration in whatever migration directory the project uses (check existing migrations for the pattern — likely `apps/api/migrations/` or `supabase/migrations/`).

### Step B: Update `BrandingPatch` Pydantic Model

In `apps/api/src/api/routes/account.py`, find the `BrandingPatch` model and add:

```python
default_theme_id: Optional[int] = None
```

### Step C: Update PATCH Handler

In the PATCH handler for branding, include `default_theme_id` in the UPDATE query. Follow the existing pattern — look at how `primary_color` and `secondary_color` are persisted and do the same for `default_theme_id`.

Only update it when the value is provided (not None) — same pattern as other optional fields.

### Step D: Update AccountOut Model + GET Query

In the `AccountOut` response model, add:

```python
default_theme_id: Optional[int] = None
```

In the GET handler's SELECT query, include `default_theme_id` in the columns fetched from the accounts table.

### Verification

After these changes:
1. Go to Branding page → select "Bold" theme → Save
2. Go to Property Reports → create new report
3. The theme selector should default to "Bold" (theme 5), not "Teal" (theme 4)

---

## Fix 2: Comparable Photos Not Used in Property Reports

All 5 standalone Jinja2 templates show a Google Map satellite image for comparables instead of the actual property photos provided in the wizard.

### The Bug

Each standalone template has something like this in the comparables section:

```jinja2
style="background-image: url('{{ comp.map_image_url }}')"
```

### The Fix

Change it to use the property photo first, falling back to the map:

```jinja2
style="background-image: url('{{ comp.photo_url | default(comp.map_image_url) }}')"
```

### Files to Update (5 files, 1 line each)

Find the comparables card/photo section in each of these files and apply the fix:

1. `apps/worker/src/worker/templates/property/bold_report.jinja2`
2. `apps/worker/src/worker/templates/property/classic_report.jinja2`
3. `apps/worker/src/worker/templates/property/elegant_report.jinja2`
4. `apps/worker/src/worker/templates/property/modern_report.jinja2`
5. `apps/worker/src/worker/templates/property/teal_report.jinja2`

Search each file for `comp.map_image_url` in the comparables section. Replace with `comp.photo_url | default(comp.map_image_url)`.

**Do NOT touch** any other `map_image_url` references (like the aerial page map) — only the comparable property cards.

### Verification

After this change:
1. Create a property report
2. In the wizard Step 2, select comparables — note that some have MLS photos
3. Generate the report
4. The comparables page should show the actual property photos, not satellite map thumbnails
5. If a comp has no photo_url, it should gracefully fall back to the map image

---

## Bonus Fix: Make TOC Dynamic for Executive Summary

The Table of Contents in all 5 templates hardcodes "Executive Summary" even when the page doesn't render (because AI generation failed or was skipped).

In each of the 5 template files, find the TOC entry for Executive Summary and wrap it in a conditional:

```jinja2
{# BEFORE: #}
<li>Executive Summary</li>

{# AFTER: #}
{% if "overview" in _pages and overview_text %}
<li>Executive Summary</li>
{% endif %}
```

Search for "Executive Summary" in the TOC section of each template and apply this conditional. The variables `_pages` and `overview_text` are already available in the template context.

Same 5 files as Fix 2.
