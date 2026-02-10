# Market Reports Pages

## Route: `/app/reports` -- Report List

> `apps/web/app/app/reports/page.tsx`

Client component. Fetches `GET /v1/reports` on mount. Displays a table with columns: Report type, Area (city), Created date, Status, Actions.

**Actions per report:**
- Eye icon -> open `html_url` in new tab
- Download icon -> open `pdf_url` in new tab
- Share icon -> open `/social/{id}` for social media image (1080x1920)
- JSON icon -> open `json_url` in new tab

Empty state shows "No reports yet" with a CTA to create one.

## Route: `/app/reports/new` -- Report Builder

> `apps/web/app/app/reports/new/page.tsx` -> `components/report-builder/index.tsx`

### Layout

Two-column layout: 400px config panel on left, flexible live preview on right.

Sticky header shows progress ("X of 4 sections complete") and the "Generate Report" button.

### Sections (in order)

1. **Report Type** (`sections/report-type-section.tsx`)
   - Options: market_snapshot, new_listings, inventory, closed, price_bands, new_listings_gallery, featured_listings
   - Audience filter presets: All, First-Time Buyer, Luxury, Family Homes, Condo Watch, Investor Deals

2. **Area** (`sections/area-section.tsx`)
   - Toggle between City or ZIP code(s)
   - City: single text input
   - ZIP: multi-select

3. **Lookback Period** (`sections/lookback-section.tsx`)
   - Options: 7, 14, 30, 60, 90 days

4. **Delivery** (`sections/delivery-section.tsx`)
   - Checkboxes: View in Browser, Download PDF, Download Social Image, Send via Email
   - Email recipients input (when email selected)

### Live Preview (`report-preview.tsx`)

Shows a preview of the report as the user configures it. Loads branding and profile context on mount:
- `GET /v1/account/branding` - Brand colors, logo
- `GET /v1/users/me` - Agent name, title, avatar

### Submission Flow

1. `POST /v1/reports` with payload: `{ report_type, city, zips, lookback_days, filters }`
2. Returns `{ report_id }`
3. Polls `GET /v1/reports/{report_id}` every 2 seconds (max 60 attempts = 2 min)
4. When status is `ready` or `completed`, opens the report based on delivery options
5. If status is `failed`, shows error message

### Types

Defined in `components/report-builder/types.ts`:
- `ReportBuilderState` - All form state
- `BrandingContext` - Brand colors, logo, display name
- `ProfileContext` - Agent name, title, avatar, contact info
- `AudienceFilter` - Preset filter type
- `AUDIENCE_FILTER_PRESETS` - Filter parameters per preset

## Key Files

- `apps/web/app/app/reports/page.tsx` - Report list page
- `apps/web/app/app/reports/new/page.tsx` - New report page
- `apps/web/components/report-builder/index.tsx` - Wizard container
- `apps/web/components/report-builder/report-preview.tsx` - Live preview
- `apps/web/components/report-builder/types.ts` - Types and constants
- `apps/web/components/report-builder/sections/` - All 4 section components
