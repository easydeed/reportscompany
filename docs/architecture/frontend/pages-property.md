# Property Report Pages

## Route: `/app/property` -- Property Report List

> `apps/web/app/app/property/page.tsx`

Lists all property reports for the user. Fetches `GET /v1/property/reports`.

## Route: `/app/property/new` -- Property Report Wizard

> `apps/web/app/app/property/new/page.tsx`

Multi-step wizard to create a CMA/seller property report. Steps:

### Step 1: Property Search (PropertySearchForm)
- Google Places autocomplete for address input
- On selection, calls backend to look up property via SiteX
- Displays: beds/baths, sqft, year built, assessed value, owner, APN, property type, legal description

### Step 2: Comparables (ComparablesPicker)
- Fetches comparable sales via `GET /v1/property/comparables`
- Search params: radius (0.5mi default), sqft variance (20% default)
- User selects 4-8 comps from the results
- Map view available via ComparablesMapModal

### Step 3: Theme & Pages (ThemeSelector)
- 5 themes: Classic, Modern, Elegant, Teal, Bold
- Each has a default accent color and page layout
- Themes 1-3 have "full" page set (20 pages); Themes 4-5 have "compact" set (9 pages)
- Page previews hosted on R2 (`assets.trendyreports.com/property-reports/previews/`)
- User can toggle individual pages on/off (some are required: cover, property_details, comparables, back_cover)
- Color picker for accent color customization

### Step 4: Review & Generate
- Submits to `POST /v1/property/reports`
- Returns: report ID, PDF URL, QR code URL, short code

## Route: `/app/property/[id]` -- Property Detail

> `apps/web/app/app/property/[id]/page.tsx`

Shows property report details:
- View count, lead count
- QR code for the property landing page (`/p/{code}`)
- PDF download link
- Lead list from this property

## Route: `/app/property/[id]/settings` -- Property Settings

> `apps/web/app/app/property/[id]/settings/page.tsx`

Edit property report settings after creation.

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `PropertySearchForm` | `components/property/PropertySearchForm.tsx` | Google Places + SiteX lookup |
| `ComparablesPicker` | `components/property/ComparablesPicker.tsx` | Select 4-8 comps from results |
| `ComparablesMapModal` | `components/property/ComparablesMapModal.tsx` | Map view of comps |
| `ThemeSelector` | `components/property/ThemeSelector.tsx` | Pick theme + pages |

## Types

Defined in `lib/wizard-types.ts`:
- `PropertyData` - SiteX property response
- `Comparable` - Normalized comp data
- `WizardState` - Full wizard state (address, comps, theme, pages)
- `THEMES` - 5 theme definitions with colors and page sets
- `ALL_PAGES` - 20 available report pages
- `COMPACT_PAGES` - 9-page subset for themes 4-5
- `ThemeId`, `PageId` - Type unions

## Key Files

- `apps/web/app/app/property/page.tsx`
- `apps/web/app/app/property/new/page.tsx`
- `apps/web/app/app/property/[id]/page.tsx`
- `apps/web/app/app/property/[id]/settings/page.tsx`
- `apps/web/components/property/` - All property components
- `apps/web/lib/wizard-types.ts` - Types and constants
- `apps/web/lib/property-report-assets.ts` - R2 asset URLs, theme configs, helper functions
