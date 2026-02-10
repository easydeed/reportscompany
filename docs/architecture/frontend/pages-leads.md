# Lead Management Pages

## Route: `/app/leads` -- Lead List

> `apps/web/app/app/leads/page.tsx`

### Overview

Displays leads captured from property report QR codes and landing pages. Uses `apiFetch()` from `lib/api.ts`.

### API Calls

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/leads` | Fetch leads with optional filters (`status`, `property_report_id`) |
| `GET /v1/property/reports?limit=100` | Load property reports for filter dropdown |
| `PATCH /v1/leads/{id}` | Update lead status |
| `GET /v1/leads/export/csv` | Export leads as CSV download |

### Features

**Stats Cards (4 columns):**
- Total Leads
- New This Week (leads with status "new" created in last 7 days)
- Contacted
- Converted

**Filters:**
- Text search (name, email, phone, property address)
- Status dropdown: All, New, Contacted, Converted
- Property dropdown: filter by specific property report
- Clear all filters button

**Lead Table:**
- Columns: Lead (name/email/phone), Property, Source (QR Scan / Direct Link), Status, Date
- Click row to open lead detail modal
- Dropdown menu per row: Mark as New/Contacted/Converted, View Property Report

**Lead Detail Modal:**
- Contact info with mailto/tel links
- Message (if provided)
- Linked property report
- Notification status (SMS sent? Email sent?)
- Quick status toggle buttons

**Export:**
- Downloads CSV via blob, triggers browser download with dated filename

## Route: `/app/lead-page` -- Lead Page Editor

> `apps/web/app/app/lead-page/page.tsx` -> `components/lead-pages/ConsumerLandingWizard.tsx`

Editor for the consumer-facing lead capture landing page. Configures what the lead sees when they scan a property QR code or visit the `/p/{code}` URL.

### Lead Capture Flow

```
Property Report (printed/shared)
  -> QR Code scanned by consumer
    -> /p/{code} (public landing page)
      -> Consumer fills out form (name, email, phone, message)
        -> Lead captured in backend
          -> Agent notified via SMS + email
            -> Lead appears in /app/leads
```

## Key Files

- `apps/web/app/app/leads/page.tsx` - Lead list page
- `apps/web/app/app/lead-page/page.tsx` - Lead page editor
- `apps/web/components/lead-pages/ConsumerLandingWizard.tsx` - Landing page wizard
