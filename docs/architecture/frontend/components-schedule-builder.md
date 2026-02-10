# Schedule Builder Component

> `apps/web/components/schedule-builder/`

## Architecture

Same layout pattern as the report builder: single-page wizard with 6 sections on the left, email preview on the right. Supports both create and edit modes.

## Files

### `index.tsx` -- Main Wizard Container

**Props:**
- `scheduleId` (optional) - If provided, loads existing schedule for editing

**State Management:**
- `ScheduleBuilderState` - All form values
- `BrandingContext` - From `GET /v1/account/branding`
- `ProfileContext` - From `GET /v1/users/me`
- `touched` tracker - 6 sections: name, reportType, area, lookback, cadence, recipients

**Edit Mode:**
- Loads existing schedule via `GET /v1/schedules/{scheduleId}`
- Maps API response to state via `mapApiToState()`
- Marks all sections as touched
- Submit uses `PATCH /v1/schedules/{id}` instead of `POST /v1/schedules`

**Submission Payload:**
```json
{
  "name": "Weekly Market Update",
  "report_type": "market_snapshot",
  "city": "Anaheim",
  "zip_codes": null,
  "lookback_days": 30,
  "cadence": "weekly",
  "weekly_dow": 1,
  "monthly_dom": null,
  "send_hour": 9,
  "send_minute": 0,
  "timezone": "America/Los_Angeles",
  "recipients": [
    { "type": "contact", "id": "uuid" },
    { "type": "group", "id": "uuid" },
    { "type": "manual_email", "email": "john@example.com" }
  ],
  "include_attachment": true,
  "active": true,
  "filters": null
}
```

### `email-preview.tsx` -- Email Preview

Live preview of the email that will be sent. Shows subject line, branding, area, and scheduling info.

### Sections

**1. Schedule Name** (inline in index.tsx)
- Simple text input

**2. Report Type** (`sections/report-type-section.tsx`)
- Same as report builder: 7 report types + audience filter presets

**3. Area** (`sections/area-section.tsx`)
- City or ZIP codes

**4. Lookback Period** (`sections/lookback-section.tsx`)
- 7, 14, 30, 60, 90 days

**5. Cadence** (`sections/cadence-section.tsx`)
- Weekly: day of week selector (Mon-Sun), time, timezone
- Monthly: day of month (1-28), time, timezone
- Timezone picker

**6. Recipients** (`sections/recipients-section.tsx`)
- Select from existing contacts/groups
- Add manual email addresses

### `types.ts`

Type definitions:
- `ScheduleBuilderState` - name, reportType, area, lookback, cadence config, recipients, includeAttachment
- `BrandingContext` - primaryColor, accentColor, emailLogoUrl, displayName
- `ProfileContext` - name, jobTitle, avatarUrl, phone, email
- `Recipient` - type (contact/group/manual_email), id, name, email, memberCount
- `AudienceFilter` + `AUDIENCE_FILTER_PRESETS` - Same filter system
- `getAreaDisplay()` - Helper to format area for display
- `getEmailSubject()` - Helper to generate email subject line

## Key Files

- `apps/web/components/schedule-builder/index.tsx`
- `apps/web/components/schedule-builder/email-preview.tsx`
- `apps/web/components/schedule-builder/types.ts`
- `apps/web/components/schedule-builder/sections/report-type-section.tsx`
- `apps/web/components/schedule-builder/sections/area-section.tsx`
- `apps/web/components/schedule-builder/sections/lookback-section.tsx`
- `apps/web/components/schedule-builder/sections/cadence-section.tsx`
- `apps/web/components/schedule-builder/sections/recipients-section.tsx`
