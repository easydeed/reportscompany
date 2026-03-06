# Cursor Prompt: Fix All Property Report Issues (8 Items)

## Overview

8 issues found during property report testing. 4 are code fixes, 2 are env config (already done), 1 is a CSS bug, and 1 is a future enhancement. This prompt handles all the code fixes.

**Environment variables are already set on the worker.** Do not suggest setting them as a fix — they're configured. If maps or AI still don't work after these code fixes and a redeploy, it's a different issue.

---

## Fix 1: Modern Theme Aerial Footer — Undefined CSS Variable

**File:** `apps/worker/src/worker/templates/property/modern_report.jinja2`

**Bug:** The aerial page footer uses `var(--accent)` which is never defined in the Modern theme. Modern defines `--coral` and `--coral-on-dark`, not `--accent`.

**Fix:** Find the aerial page footer styles in `modern_report.jinja2` and replace `var(--accent)` with `var(--coral)` (or `var(--coral-on-dark)` if it's on a dark background).

**Also check:** All 5 theme templates should use consistent footer styling on the aerial page. The aerial page has a dark background, so the footer needs light/white text. Audit all 5 templates and make sure the aerial page footer:
- Has white or light text (not dark text on dark bg)
- Uses the theme's actual CSS variable names (not undefined ones)
- Matches the footer styling from other pages in the same theme (just color-inverted for dark bg)

Files to check:
- `apps/worker/src/worker/templates/property/bold_report.jinja2`
- `apps/worker/src/worker/templates/property/classic_report.jinja2`
- `apps/worker/src/worker/templates/property/elegant_report.jinja2`
- `apps/worker/src/worker/templates/property/modern_report.jinja2`
- `apps/worker/src/worker/templates/property/teal_report.jinja2`

---

## Fix 2: Comp Photos — Template Already Fixed, Ensure Deployed

**Files:** All 5 standalone Jinja2 templates (same 5 as Fix 1)

**Verify** that each template's comparables section uses:
```jinja2
{{ comp.photo_url | default(comp.map_image_url) }}
```
NOT just:
```jinja2
{{ comp.map_image_url }}
```

If any file still has only `comp.map_image_url` in the comparables card/photo area, update it. This fix was committed previously but may not be in all 5 files.

---

## Fix 3: Google Maps — Already Configured

**No code changes needed.** `GOOGLE_MAPS_API_KEY` is set on the worker. After the worker redeploys with these other code fixes, maps should render.

**However**, verify in `apps/worker/src/worker/property_builder.py` that the env var is read correctly:

```python
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
```

If the key is being read from a different env var name, or if there's a caching issue, that could explain why maps aren't appearing despite the key being set. Print/log the key length (NOT the key itself) at startup to verify:

```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"GOOGLE_MAPS_API_KEY configured: {bool(GOOGLE_MAPS_API_KEY)} (length: {len(GOOGLE_MAPS_API_KEY)})")
```

---

## Fix 4: Theme Resets to Teal After "Create Another Report"

**File:** `apps/web/components/property-wizard/property-wizard.tsx` (or wherever `handleReset` lives)

**Bug:** `handleReset()` hardcodes Teal:
```typescript
setSelectedThemeId(4);          // hardcoded Teal
setAccentColor("#34d1c3");      // hardcoded Teal accent
```

The `loadAccountDefaults` useEffect only fires on mount (empty dependency `[]`), so it never re-runs after reset.

**Fix:** Make `handleReset` load account defaults instead of hardcoding:

```typescript
// Option A: Refetch account data on reset
const handleReset = async () => {
  // ... existing reset logic for other fields ...
  
  // Fetch account defaults instead of hardcoding
  try {
    const res = await fetch('/api/proxy/v1/account');
    const data = await res.json();
    setSelectedThemeId(data.default_theme_id || 4);
    setAccentColor(data.secondary_color || "#34d1c3");
  } catch {
    // Fallback to Teal only if fetch fails
    setSelectedThemeId(4);
    setAccentColor("#34d1c3");
  }
};
```

```typescript
// Option B: Cache account defaults and reuse on reset (no extra API call)
// Store the account defaults in a ref on initial load:
const accountDefaultsRef = useRef({ themeId: 4, accentColor: "#34d1c3" });

// In the loadAccountDefaults useEffect:
useEffect(() => {
  async function load() {
    const res = await fetch('/api/proxy/v1/account');
    const data = await res.json();
    const themeId = data.default_theme_id || 4;
    const accent = data.secondary_color || "#34d1c3";
    setSelectedThemeId(themeId);
    setAccentColor(accent);
    accountDefaultsRef.current = { themeId, accentColor: accent };
  }
  load();
}, []);

// In handleReset:
const handleReset = () => {
  // ... existing reset logic ...
  setSelectedThemeId(accountDefaultsRef.current.themeId);
  setAccentColor(accountDefaultsRef.current.accentColor);
};
```

**Option B is preferred** — no extra API call on reset, uses cached values from initial load.

---

## Fix 5: Agent Photo Not Saving from Branding Page

**File:** `apps/web/app/app/settings/branding/page.tsx` (or wherever the branding save function lives)

**Bug:** The save function PATCHes account branding fields (logos, colors, theme) but never persists the agent photo. Agent photo lives in `users.avatar_url`, not the accounts table.

**Fix:** When saving branding, also call the user profile endpoint if the agent photo changed:

```typescript
async function saveBranding() {
  // Existing: save account branding
  await fetch('/api/proxy/v1/account/branding', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      primary_color: branding.primaryColor,
      secondary_color: branding.accentColor,
      default_theme_id: branding.defaultThemeId,
      header_logo_url: branding.headerLogoUrl,
      footer_logo_url: branding.footerLogoUrl,
      // ... other account fields
    }),
  });

  // NEW: save agent photo to user profile if it changed
  if (agentPhotoChanged) {
    await fetch('/api/proxy/v1/users/me', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        avatar_url: branding.agentPhotoUrl,
      }),
    });
  }
}
```

**Check:** Verify the backend `PATCH /api/v1/users/me` endpoint accepts `avatar_url`. If it doesn't, add it to the user update Pydantic model and handler.

Also save any other agent info fields that live on the user record rather than the account record (name, title, phone, email, license). Check which table each field lives in and route the PATCH accordingly.

---

## Fix 6: Comparables Map Modal — No Map + Wrong Position

**Part A — No map:**

**File:** The MapModal component (likely in `apps/web/components/property/ComparablesMapModal.tsx` or similar)

**Bug:** The component reads `process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`. If this is not set on the frontend (Vercel), the map won't render.

**Verify** that `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is set in your Vercel environment variables (this is the FRONTEND key, separate from the worker's `GOOGLE_MAPS_API_KEY`).

If the key IS set but maps still don't show, check if the component has a null check that's too aggressive:

```typescript
// This might be blocking even when the key exists:
if (!apiKey || !property?.latitude || !property?.longitude) return null;
```

Add a console.log to debug:
```typescript
console.log('MapModal debug:', { 
  hasApiKey: !!apiKey, 
  lat: property?.latitude, 
  lng: property?.longitude 
});
```

**Part B — Wrong position (top-right instead of centered):**

The modal uses shadcn Dialog with `max-w-3xl` that may conflict with the default `sm:max-w-lg`. Fix the positioning:

```typescript
// Find the DialogContent and ensure proper centering:
<DialogContent className="max-w-3xl w-full">
  {/* If using custom positioning, ensure these classes are present: */}
  {/* fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] */}
</DialogContent>
```

If the Dialog uses a custom `className` that overrides the default centering, remove the override and let shadcn's default positioning handle it. The issue is likely a CSS specificity conflict.

Check if there's a `style` prop or custom class setting `top`, `right`, or `transform` that's fighting the default centering.

---

## Fix 7: Accent Color Overridden by Branding Primary

**File:** `apps/worker/src/worker/property_builder.py`

**Bug:** `_get_theme_color()` prioritizes branding primary_color over the wizard's accent_color:

```python
return (
    branding.get("primary_color") or   # <-- takes priority!
    self.accent_color or                # <-- wizard choice ignored
    self._THEME_DEFAULT_COLORS.get(...)
)
```

Since every account has a primary_color set, the wizard's per-report accent color choice is always overridden.

**Fix:** Flip the priority — the wizard's explicit choice should win:

```python
return (
    self.accent_color or                # wizard choice takes priority
    branding.get("primary_color") or    # branding fallback
    self._THEME_DEFAULT_COLORS.get(...)  # theme default fallback
)
```

**Logic:** If the agent explicitly picked an accent color in the wizard (Step 3 theme selection), that should be what renders. If they didn't change it, `self.accent_color` will be the account's `secondary_color` (from accent sync), which is also correct. The branding `primary_color` should only kick in as a last-resort fallback, not override an explicit choice.

---

## Fix 8: Page Preview JPGs (Future Enhancement — Skip for Now)

This requires a new pipeline to render each page of each theme as a JPG preview. The infrastructure exists (`getPagePreviewUrl`, PDFShift JPG rendering) but the actual preview images haven't been generated.

**Do not implement this now.** Mark it as a TODO for a future sprint. The current decorative line placeholders work fine for MVP.

If you want to add a simple improvement now: use the existing theme cover JPGs (`/previews/1-5.jpg`) as a representative thumbnail for the theme card, rather than trying to show individual pages.

---

## Verification Checklist

After all fixes, test this exact flow:

1. **Branding page:** Select Bold theme → pick a custom accent color → upload agent photo → Save
2. **Verify save:** Refresh branding page → Bold is still selected, accent color persisted, agent photo shows
3. **Property wizard:** Create new report → theme should default to Bold (not Teal)
4. **Accent color:** The theme preview should show your custom accent, not Bold's default
5. **Comparables:** Add comps with MLS photos → generate report
6. **Generated PDF check:**
   - Cover page uses Bold theme with your accent color
   - Comparables page shows MLS property photos (not satellite maps)
   - Aerial page shows Google Maps aerial view (not placeholder)
   - Aerial page footer is readable (not dark text on dark bg)
   - Executive Summary page appears (with AI-generated content)
   - Table of Contents matches actual pages in the report
7. **Map modal:** Click a comparable's map icon → modal appears centered, shows Google Map
8. **Create Another:** Click "Create Another Report" → theme resets to Bold (your saved default), not Teal
