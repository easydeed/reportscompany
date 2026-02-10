# Report Builder Component

> `apps/web/components/report-builder/`

## Architecture

The report builder is a single-page wizard with 4 sections displayed simultaneously (not stepped). A vertical progress line on the left tracks completion. A live preview panel on the right updates as the user configures options.

## Files

### `index.tsx` -- Main Wizard Container

**State Management:**
- `ReportBuilderState` - All form values (report type, area, lookback, delivery options)
- `BrandingContext` - Loaded from `GET /v1/account/branding` on mount
- `ProfileContext` - Loaded from `GET /v1/users/me` on mount
- `touched` tracker - Tracks which sections the user has interacted with (sections only show as "complete" when touched AND filled)

**Layout:**
- Sticky header with back link, progress counter ("X of 4 sections complete"), Cancel + Generate buttons
- Two-column grid: 400px config panel | flexible preview panel

**Submission Flow:**
1. Validates all required fields (`canGenerate` computed property)
2. `POST /v1/reports` with `{ report_type, city, zips, lookback_days, filters }`
3. Receives `{ report_id }`
4. Polls `GET /v1/reports/{report_id}` every 2 seconds, max 60 attempts
5. On `ready`/`completed`: opens HTML/PDF URLs based on delivery options
6. On `failed`: shows error message via alert

### `report-preview.tsx` -- Live Preview

Renders a preview of the report layout based on current state. Shows:
- Report type visual
- Area/city name
- Lookback period
- Brand colors and logo

### `sections/report-type-section.tsx`

Report type selection grid with audience filter presets.

Available report types:
- `market_snapshot` - Market Snapshot
- `new_listings` - New Listings (table)
- `inventory` - Inventory Report
- `closed` - Closed Sales
- `price_bands` - Price Analysis
- `new_listings_gallery` - New Listings Gallery (photo grid)
- `featured_listings` - Featured Listings (large cards)

Audience filters (optional): All, First-Time Buyer, Luxury, Family Homes, Condo Watch, Investor Deals

### `sections/area-section.tsx`

Toggle between City (single text input) and ZIP codes (multi-select).

### `sections/lookback-section.tsx`

Radio-style selection: 7, 14, 30, 60, or 90 days.

### `sections/delivery-section.tsx`

Checkbox options:
- View in Browser (opens HTML URL)
- Download PDF (opens PDF URL)
- Download Social Image (1080x1920)
- Send via Email (shows email recipients input)

### `types.ts`

Type definitions:
- `ReportBuilderState` - Complete form state
- `BrandingContext` - Primary/accent color, PDF header logo URL, display name
- `ProfileContext` - Name, job title, avatar URL, phone, email
- `AudienceFilter` - `"all" | "first_time" | "luxury" | "families" | "condo" | "investors" | null`
- `AUDIENCE_FILTER_PRESETS` - Maps each filter to API params (property_type, min_price, max_price, min_beds, etc.)
