# Schedule Pages

## Route: `/app/schedules` -- Schedule List

> `apps/web/app/app/schedules/page.tsx`

Lists all schedules. Uses components from `components/schedules/schedule-table.tsx`.

## Route: `/app/schedules/new` -- Schedule Builder

> `apps/web/app/app/schedules/new/page.tsx` -> `components/schedule-builder/index.tsx`

### Layout

Same two-column pattern as the report builder: 400px config panel on left, email preview on right.

### Sections (6 total)

1. **Schedule Name** - Text input (inline in main component)
2. **Report Type** (`sections/report-type-section.tsx`) - Same report types as report builder + audience filter presets
3. **Area** (`sections/area-section.tsx`) - City or ZIP codes
4. **Lookback Period** (`sections/lookback-section.tsx`) - 7/14/30/60/90 days
5. **Cadence** (`sections/cadence-section.tsx`)
   - Weekly: day of week (Mon default), hour, minute, timezone
   - Monthly: day of month, hour, minute, timezone
6. **Recipients** (`sections/recipients-section.tsx`) - Contact/group selection + manual email entry

### Email Preview (`email-preview.tsx`)

Live preview of the email that will be sent, updates as user builds the schedule.

### API Calls

On mount:
- `GET /v1/account/branding` - Brand colors, email logo
- `GET /v1/users/me` - Agent profile info

On save:
- `POST /v1/schedules` (new) or `PATCH /v1/schedules/{id}` (edit)
- Payload: name, report_type, city, zip_codes, lookback_days, cadence, weekly_dow, monthly_dom, send_hour, send_minute, timezone, recipients, include_attachment, active, filters

## Route: `/app/schedules/[id]` -- Schedule Detail

> `apps/web/app/app/schedules/[id]/page.tsx`

Shows schedule details and run history. Uses `components/schedules/schedule-detail.tsx`.

## Route: `/app/schedules/[id]/edit` -- Edit Schedule

> `apps/web/app/app/schedules/[id]/edit/page.tsx`

Loads existing schedule via `GET /v1/schedules/{id}` then renders the same `ScheduleBuilder` component in edit mode.

## Types

Defined in `components/schedule-builder/types.ts`:
- `ScheduleBuilderState` - All form state including cadence + recipients
- `BrandingContext` - Brand colors, email logo, display name
- `ProfileContext` - Agent info
- `Recipient` - Contact/group/manual email recipient
- `AudienceFilter` + `AUDIENCE_FILTER_PRESETS` - Same filter system as report builder

## Key Files

- `apps/web/app/app/schedules/page.tsx`
- `apps/web/app/app/schedules/new/page.tsx`
- `apps/web/app/app/schedules/[id]/page.tsx`
- `apps/web/app/app/schedules/[id]/edit/page.tsx`
- `apps/web/components/schedule-builder/index.tsx` - Main wizard
- `apps/web/components/schedule-builder/email-preview.tsx` - Live email preview
- `apps/web/components/schedule-builder/sections/` - All 5 section components
- `apps/web/components/schedule-builder/types.ts` - Types and constants
- `apps/web/components/schedules/schedule-detail.tsx` - Schedule detail view
- `apps/web/components/schedules/schedule-table.tsx` - Schedule list table
