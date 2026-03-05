# Schedule Wizard — How It Works

---

## Two Wizards, Two Purposes

| Wizard | Route | Purpose |
|---|---|---|
| **Schedule Builder** | `/app/schedules/new`, `/app/schedules/[id]/edit` | Create/edit recurring automated email reports |
| **Report Builder (v0)** | `/app/reports/new` | Generate a one-off report on demand |

The Schedule Builder is the primary flow for setting up client email campaigns. The Report Builder is for agents who want a quick report right now.

---

## Schedule Builder Flow

The Schedule Builder is a **single-page form** — all sections visible at once. Left panel (400px) has the controls; right panel shows a live email preview that updates as the user configures.

### Steps (top to bottom)

| # | Section | Component | What the User Does |
|---|---|---|---|
| 1 | **Schedule Name** | Inline input | Types a name (e.g., "Weekly LA Buyer Alerts") |
| 2 | **Report Type** | `report-type-section.tsx` | Picks one of 3 cards: **New Listings**, **Market Update**, or **Closed Sales** |
| 3 | **Audience** | Same component | If New Listings selected: picks audience pill — All, First-Time Buyers, Luxury, Families, Condo, Investors |
| 4 | **Area** | `area-section.tsx` | Toggles City vs ZIP, then searches/enters location |
| 5 | **Lookback** | `lookback-section.tsx` | Picks time window: 7, 14, 30, 60, or 90 days |
| 6 | **Cadence** | `cadence-section.tsx` | Weekly or Monthly, picks day/time, timezone |
| 7 | **Recipients** | `recipients-section.tsx` | Searches contacts/groups from CRM, or enters manual emails |

### Report Type Cards

Only 3 types are exposed in the schedule builder:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  📸 Images  │  │  📊 Chart   │  │  🏠 Home    │
│             │  │             │  │             │
│ New Listings│  │Market Update│  │Closed Sales │
│ Photo       │  │Stats &      │  │Recent sales │
│ gallery of  │  │trends for   │  │in the area  │
│ new homes   │  │the area     │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

The other 5 report types (Inventory, Price Bands, Open Houses, Featured Listings, New Listings Table) are available through the Report Builder or API but not surfaced in the schedule wizard.

### Audience Pills (conditional)

Only appear when **New Listings** is selected:

```
[ All Listings ] [ First-Time Buyers ] [ Luxury Clients ]
[ Families ] [ Condo Buyers ] [ Investors ]
```

Each pill applies MLS filters (beds, baths, property type, price %-of-median). The preview header updates to show the audience name (e.g., "Luxury Clients – Los Angeles").

### Submission

- **Create**: `POST /api/proxy/v1/schedules`
- **Edit**: `PATCH /api/proxy/v1/schedules/{id}`

Payload includes: name, report_type, city/zip_codes, lookback_days, cadence (weekly/monthly), day/time/timezone, recipients list, filters (audience preset if selected).

---

## Email Preview (Schedule Builder)

The right panel shows a **React mockup** that mirrors the real email template structure. It is NOT a live render from `template.py` — it's a local React component (`email-preview.tsx`) using the user's actual branding and sample data.

### What the preview shows

**Always present (all types):**
- Header gradient using the agent's `primaryColor` → `accentColor`
- Agent's email logo (or brand name fallback)
- Report type badge pill
- Title: "{Report Label} – {Area}" (or "{Audience Name} – {Area}" for filtered galleries)
- Period line: "Last 30 days • Live MLS Data"
- AI insight placeholder: "The {area} market showed strong activity..."
- CTA button: "View Full Report →" in brand color
- Agent footer: photo, name, title, phone, email
- Powered by footer with unsubscribe link

**Per report type:**

| Type | Preview Content |
|---|---|
| **Market Snapshot** | Hero: "$1.15M" Median Sale Price. 3-column metric row: Closed (42), Avg DOM (24), MOI (2.4) |
| **New Listings** | Hero: "127" with audience label. 2-column metrics: Median ($985K), Starting ($425K). 3×2 photo grid with 6 sample Unsplash property images, each with a price overlay ($650K–$1.28M) |
| **Closed Sales** | Hero: "42" Total Closed. 3-column metrics: Median ($1.08M), Avg DOM (18), Close-List (98.2%). 2-row data table: Address, Beds, Baths, Price |
| **No type selected** | "Select a report type to preview" |
| **Other types** | "Preview for this report type" (generic placeholder) |

### What updates live

As the user changes settings, these preview elements update immediately:
- **Report type** → switches preview content (stats vs gallery vs table)
- **Audience filter** → updates header title and hero label
- **Area** → updates header title ("Market Snapshot – Los Angeles")
- **Lookback** → updates period line ("Last 7 days" vs "Last 90 days")
- **Branding** → gradient colors, logo, agent footer all use real account branding

### What does NOT update

- Metric values are hardcoded sample data (not from MLS)
- Property photos are Unsplash stock images
- Listing counts/prices are static
- AI insight is a generic placeholder sentence

---

## Report Builder (v0) Flow

The Report Builder uses a **4-step wizard** with Back/Continue navigation and animated transitions.

### Steps

| Step | Component | What the User Does |
|---|---|---|
| 0. **Area** | `step-area.tsx` | City (from preset list) or ZIP codes (up to 5) |
| 1. **Report Type** | `step-report-type.tsx` | All 8 types shown: 4 Primary cards + 4 Secondary (collapsed under "Show More"). Audience pills for New Listings + New Listings Table |
| 2. **Timeframe** | `step-timeframe.tsx` | 7, 14, 30, 60, or 90 days. Hint text varies by report type |
| 3. **Review** | `step-review.tsx` | Summary card + delivery options (View in Browser, PDF, Social Image, Email) + Generate button |

### No Preview

The Report Builder has **no email preview**. Step 3 (Review) shows a text summary of selections and delivery options. After clicking "Generate," it calls the API and polls until the report is ready, then opens the result.

### Submission

- `POST /api/proxy/v1/reports`
- Polls `GET /api/proxy/v1/reports/{id}` every 2 seconds until status is `"ready"` or `"completed"` (max 60 attempts)
- On completion, user opens `html_url` or `pdf_url`

---

## File Map

```
apps/web/
├── app/app/schedules/
│   ├── new/page.tsx                    ← Mounts ScheduleBuilder
│   └── [id]/edit/page.tsx              ← Mounts ScheduleBuilder (edit mode)
├── app/app/reports/
│   └── new/page.tsx                    ← Mounts ReportBuilderWizard
├── components/schedule-builder/
│   ├── index.tsx                       ← Main layout, state, submit logic
│   ├── email-preview.tsx               ← React mockup preview
│   ├── types.ts                        ← State types, branding context, audience presets
│   └── sections/
│       ├── report-type-section.tsx      ← 3 type cards + audience pills
│       ├── area-section.tsx             ← City/ZIP input
│       ├── lookback-section.tsx         ← Time window selector
│       ├── cadence-section.tsx          ← Weekly/Monthly + day/time
│       └── recipients-section.tsx       ← Contact/group search
└── components/v0-report-builder/
    ├── report-builder.tsx              ← Main wizard shell, step navigation
    ├── types.ts                        ← All 8 types, audience presets, filter mappings
    ├── step-area.tsx                   ← City/ZIP selection
    ├── step-report-type.tsx            ← 8 type cards + audience pills
    ├── step-timeframe.tsx              ← Lookback selector
    └── step-review.tsx                 ← Summary + delivery + generate
```
