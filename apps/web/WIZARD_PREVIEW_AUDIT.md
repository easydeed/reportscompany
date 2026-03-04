# Wizard Preview System Audit

**Date:** February 2026  
**Scope:** `/app/property/new` — 4-step property report wizard  
**Method:** Read-only code investigation

---

## Current Wizard Flow

| Step | Label | Component | What it does |
|------|-------|-----------|--------------|
| 0 | Property | `StepProperty` | Address search → SiteX lookup → shows property card with confirmed details |
| 1 | Comparables | `StepComparables` | Fetches real MLS comps via SimplyRETS, user selects 4–8; Active/Closed toggle reloads |
| 2 | Theme & Pages | `StepTheme` | 5 theme cards + accent color picker + page toggle grid |
| 3 | Generate | `StepGenerate` | Review summary → POST to create report → polling loop → success/error screen |

**Entry point:** `apps/web/app/app/property/new/page.tsx` → mounts `PropertyWizard`  
**Orchestrator:** `apps/web/components/property-wizard/property-wizard.tsx`

---

## Current Preview Implementation

### Right Sidebar (always visible, `lg:` breakpoint and above)
- **What exists:** A mini cover mockup rendered entirely in React/Tailwind — no images, no API calls
- **Preview type:** CSS gradient (`selectedTheme.gradient`) + property address text + beds/baths/sqft chips + accent color bar
- **When it shows:** Persistent sidebar throughout all 4 steps
- **Data source:** Live wizard state — real property data + selected theme + accent color
- **Updates dynamically:** Yes — updates immediately on theme/color/property changes
- **What it does NOT show:** Any real page layout, actual template output, font rendering, inner pages

### Step 2 — "Live Preview" button (StepTheme)
- **What exists:** A `<Button>` that opens a shadcn `<Dialog>` modal
- **Preview type:** CSS gradient cover panel only — identical to the sidebar preview, just bigger
- **When it shows:** Only when user clicks the button on Step 2
- **Data source:** Selected theme gradient + accent color line + theme name text
- **Updates dynamically:** N/A — it is a static CSS mockup
- **Modal text:** Literally reads "Full preview available after generation"
- **NOT connected to the preview API** — no fetch calls are made

### Step 2 — Theme Cards
- **Display:** 5 cards in a `grid-cols-2 sm:grid-cols-3 lg:grid-cols-5` grid
- **Visual preview:** CSS gradient (`theme.gradient`) with fake decorative lines and the theme name in `theme.displayFont` — no screenshots
- **Fallback:** Same gradient if there are no images

### Step 2 — Page Selection Grid
- **Display:** Cards with `8.5/11` aspect ratio mini thumbnails
- **Visual preview:** Three colored lines (varying width/opacity) as content placeholder — no content
- **No images, no API calls**

---

## Theme Selection UI

- **How themes are displayed:** 5 gradient cards in a responsive grid
- **Visual preview per theme:** CSS gradient only — no screenshots of real report output
- **Color picker:** 9 preset swatches (navy, blue, purple, green, teal, amber, red, pink, gray) + free-text hex input + live color swatch box; updates accent color in the gradient immediately
- **Page selection:** Toggle grid of mini page placeholders (lines as content); "Select All" / "Minimum Only" buttons; required pages have a lock icon and cannot be toggled
- **Live preview button:** Opens a dialog with "Full preview available after generation" — **no real preview rendered**

---

## Existing Preview Infrastructure

### Backend API — `POST /v1/property/preview`
- **File:** `apps/api/src/api/routes/property.py`
- **What it does:** Accepts `PreviewRequest` (theme, accent_color, property address, sitex_data, comparables, optional agent/branding), instantiates `PropertyReportBuilder`, calls `builder.render_html()`, returns full `HTMLResponse`
- **Pages rendered:** Hardcoded to `["cover", "contents", "aerial", "property", "analysis", "comparables", "range"]`
- **Status:** Endpoint exists and is documented as "Used by wizard Step 3" — but the active wizard (`StepTheme`) does NOT call it

### Frontend Proxy — `POST /api/proxy/v1/property/preview`
- **File:** `apps/web/app/api/proxy/v1/property/preview/route.ts`
- **What it does:** Proxies to the backend, returns `text/html`
- **Status:** Proxy exists and works — but has no callers in the active wizard

### Worker — `PropertyReportBuilder.render_preview()`
- **File:** `apps/worker/src/worker/property_builder.py` (line 799)
- **What it does:** Accepts optional list of page names, temporarily overrides `page_set`, calls `render_html()`, restores state
- **Default pages:** `["cover", "property_details", "comparables"]`
- **Status:** Method exists but is NOT called by the preview API endpoint (the endpoint calls `render_html()` directly)

### Dormant component — `ThemeSelector`
- **File:** `apps/web/components/property/ThemeSelector.tsx`
- **What it does:** Full live preview system with:
  - "Live Preview" toggle button (only shown when `propertyData` prop is provided)
  - 500px `<iframe>` panel, expandable to fullscreen overlay
  - Calls `POST /api/proxy/v1/property/preview` with real property data, comps, theme, accent color
  - 500ms debounce — auto-refreshes on theme or accent color change
  - Per-page thumbnail images loaded from R2: `https://assets.trendyreports.com/property-reports/previews/{themeId}/{pageNumber}.jpg`
  - Full-screen page preview modal with keyboard navigation (← →)
  - Falls back to CSS gradient if R2 images fail
- **Status:** **NOT imported by the active wizard.** Only imported in `components/property/index.ts`. The wizard uses `StepTheme` instead.

### R2 Asset Manifest — `lib/property-report-assets.ts`
- Defines `THEMES` array with `id`, `key`, `name`, `description`, `defaultColor`, `pageCount`, `previewBg`, `fontStyle`, `pages`
- Defines 7 unified pages per theme (all themes now use the same page set)
- `getThemeCoverUrl(themeId)` → `assets.trendyreports.com/property-reports/previews/{id}.jpg`
- `getPagePreviewUrl(themeId, previewNumber)` → `assets.trendyreports.com/property-reports/previews/{id}/{n}.jpg`
- **Status:** Infrastructure exists — it is used by `ThemeSelector` (dormant) but NOT by `StepTheme` (active)

### Branding Sample PDF — `POST /api/proxy/v1/branding/sample-pdf`
- **File:** `apps/web/app/api/proxy/v1/branding/sample-pdf/route.ts`
- **Backend:** `apps/api/src/api/routes/branding_tools.py`
- **How it works:** Reads account branding, builds a `branding-preview` URL with query params, sends that URL to PDFShift to render as PDF, streams PDF back
- **Pipeline:** PDFShift renders the Next.js `branding-preview` page → PDF blob
- **Reusable for wizard?** Partially — the PDFShift pipeline is the same one used for property reports. But the source page and data flow are different (no property/comp data, branding-only).

---

## Post-Generation View

### Step 4 success screen (StepGenerate)
- Green checkmark animation
- Property address subtitle
- QR code image (from `qr_code_url`)
- "Download PDF" button — opens `pdf_url` in new tab
- "Copy Share Link" button — copies `origin/p/{short_code}`
- Share URL displayed as plain text
- "View All Reports" redirects to `/app/property`
- "Create Another Report" resets wizard state
- **No inline PDF embed on the success screen**

### Detail page — `/app/property/[id]`
- Full `<iframe src="${pdf_url}#toolbar=0">` embed at 8.5/11 aspect ratio
- Download PDF button + Open in new tab button
- QR code image (160×160)
- Landing page URL with copy + open-in-new-tab buttons
- Analytics card: total views + unique visitors + last viewed timestamp
- Recent leads panel (5 most recent, links to full leads view)
- Settings and Delete actions
- Polls every 3 seconds if status is `"processing"`

---

## Gap Analysis

### What exists
| Capability | Status |
|---|---|
| CSS gradient "mini cover" mockup in sidebar | ✅ Active |
| Theme cards with CSS gradients (no screenshots) | ✅ Active |
| Page selection toggle grid (CSS only, no thumbnails) | ✅ Active |
| Backend HTML preview endpoint (`POST /v1/property/preview`) | ✅ Built, not wired |
| Next.js proxy for preview endpoint | ✅ Built, not wired |
| R2 per-page screenshot images | ✅ Infrastructure defined, not uploaded |
| `ThemeSelector` with full live preview system | ✅ Built, not imported in wizard |
| `render_preview()` method on PropertyReportBuilder | ✅ Built, not called by API |
| Post-generation inline PDF embed (detail page) | ✅ Active |

### What's missing / not wired

1. **The active wizard never calls the live preview API.** `StepTheme` shows a CSS mockup only. The full `ThemeSelector` component (which does call the API) is not used in the wizard.

2. **R2 screenshot images are not uploaded.** `getThemeCoverUrl()` and `getPagePreviewUrl()` point to `assets.trendyreports.com/property-reports/previews/` — these URLs 404 unless real screenshots are uploaded. `ThemeSelector` has fallback gradients for when they fail.

3. **The preview API ignores the `render_preview()` method.** It calls `render_html()` directly, rendering all 7 pages every time. `render_preview()` exists specifically to limit pages for performance but isn't used.

4. **Wizard ends at Step 4 success screen with no PDF embed.** User must navigate to the detail page to see the PDF inline. The success screen only offers "Download PDF" (opens new tab) or "View All Reports".

### What's needed to wire up live previews in the wizard

| What | Where | Effort |
|---|---|---|
| Replace `StepTheme` usage with `ThemeSelector` (or wire `ThemeSelector` into the wizard and pass `propertyData` + `comparables` props) | `property-wizard.tsx` | Low — props already match |
| Upload per-page JPG screenshots to R2 for each theme | R2 bucket | Medium — need to screenshot each page |
| Optionally: fix `render_preview()` to be called from the preview endpoint | `property.py` | Low |
| Optionally: add inline PDF embed to Step 4 success screen | `step-generate.tsx` | Low |
