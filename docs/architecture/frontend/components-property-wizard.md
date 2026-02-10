# Property Report Wizard Components

> `apps/web/components/property/`

## PropertySearchForm

> `components/property/PropertySearchForm.tsx`

### Purpose
Address lookup form using Google Places Autocomplete + SiteX property data.

### How It Works
1. User types an address -- Google Places Autocomplete suggests matching addresses
2. On selection, `useGooglePlaces` hook parses the address components (street, city, state, zip, county)
3. City/State/ZIP field auto-fills from Google Places data
4. Search triggers a backend call to look up property details via SiteX
5. Results show: full address, beds/baths, sqft, year built, assessed value, owner, APN, property type, legal description

### Props
- `address`, `cityStateZip` - Controlled form values
- `property` - Found property data (or null)
- `loading`, `error` - Loading/error states
- `onSearch` - Trigger property lookup
- `onContinue` - Proceed to next wizard step (enabled when property is found)

## ComparablesPicker

> `components/property/ComparablesPicker.tsx`

### Purpose
Select 4-8 comparable properties from search results.

### How It Works
1. Backend returns comparables based on search params (radius, sqft variance)
2. User selects/deselects comps with checkboxes
3. Validation: minimum 4, maximum 8 selected
4. Shows: address, price, beds/baths, sqft, year built, distance, status, DOM

## ComparablesMapModal

> `components/property/ComparablesMapModal.tsx`

### Purpose
Google Maps view showing the subject property and all comparables plotted on a map. Helps users visually evaluate which comps to include.

## ThemeSelector

> `components/property/ThemeSelector.tsx`

### Purpose
Choose from 5 report themes and customize page selection + accent color.

### Themes

| ID | Name | Style | Default Color |
|----|------|-------|---------------|
| 1 | Classic | Navy, serif fonts (Bariol/Nexa) | `#0d294b` |
| 2 | Modern | Bold orange, Montserrat | `#f2964a` |
| 3 | Elegant | Sophisticated gradients | `#0d294b` |
| 4 | Teal | Minimal, teal accent | `#16d3ba` |
| 5 | Bold | Navy & gold, Bebas Neue | `#d79547` |

Theme previews are hosted on R2 at `assets.trendyreports.com/property-reports/previews/{themeId}.jpg`.

### Pages

All themes now use a unified 7-page layout:
1. Cover (required)
2. Table of Contents
3. Aerial View
4. Property Details (required)
5. Area Sales Analysis
6. Sales Comparables (required)
7. Range of Sales

Page previews: `assets.trendyreports.com/property-reports/previews/{themeId}/{pageNumber}.jpg`

### Accent Color

10 preset colors available + custom color picker. Presets range from navy to pink to black.

## Key Types (from `lib/wizard-types.ts`)

- `PropertyData` - Full property info from SiteX
- `Comparable` - Normalized comp with id, address, price, beds/baths, sqft, lat/lng, photo, distance, status
- `WizardState` - address, property, selectedCompIds, theme, accentColor, selectedPages, reportId
- `SearchParams` - radius_miles (default 0.5), sqft_variance (default 0.2)
- `GeneratedReport` - id, pdf_url, qr_code_url, short_code

## Key Files

- `apps/web/components/property/PropertySearchForm.tsx`
- `apps/web/components/property/ComparablesPicker.tsx`
- `apps/web/components/property/ComparablesMapModal.tsx`
- `apps/web/components/property/ThemeSelector.tsx`
- `apps/web/components/property/index.ts` - Barrel exports
- `apps/web/lib/wizard-types.ts` - Types, theme definitions, validation helpers
- `apps/web/lib/property-report-assets.ts` - R2 asset URLs, theme configs, font/icon URLs
