# Unified Plan: Wizard + Branding + Live Preview

> Three systems that should be one experience. This document specifies how to rebuild the schedule wizard, fix the branding page, and connect them through a shared live preview.

---

## What's Broken Today

1. **Two wizards showing different report types.** Schedule Builder shows 3 types. Report Builder shows 8. Neither uses the "story" framing agents actually think in.

2. **Branding page is disconnected.** Agents set colors and logos in branding. Those colors flow into emails. But there's no default theme for property reports, no real preview of what emails actually look like, and the accent color doesn't sync to the property wizard.

3. **Preview is fake.** The schedule builder's email preview is a React mockup with hardcoded sample data and stock photos. The branding page preview is a static wireframe that looks nothing like the actual V16 templates. Agents have no idea what their clients will receive.

4. **No shared preview component.** The schedule builder has `email-preview.tsx`. The branding page has a fake wireframe. Neither renders the real template structure. We need ONE preview component used everywhere.

---

## The Plan: 3 Workstreams, Connected

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  WORKSTREAM A: Unified Wizard                       │
│  Merge Schedule Builder + Report Builder into one   │
│  "story-first" wizard with Send Now / Schedule mode │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  WORKSTREAM B: Branding Overhaul                    │
│  Default theme, real preview, accent sync,          │
│  brand name, font awareness                         │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  WORKSTREAM C: Shared Email Preview Component       │
│  One component, used in both wizard and branding,   │
│  reflecting the real V16 template layouts            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## WORKSTREAM A: Unified Wizard

### Why Merge?

The Schedule Builder and Report Builder do the same thing with different UIs. One is a single-page form, the other is a 4-step wizard. One shows 3 report types, the other shows 8. An agent shouldn't need to figure out which wizard to use — there's one flow, and at the end they choose: send now or schedule.

### The New Flow: 4 Steps

```
① What story?  →  ② Who's it for?  →  ③ Where & When?  →  ④ Deliver
```

### Step 1: What Story?

Five use-case cards replace 8 report type IDs:

| Card | Icon | Title | Description | Best For | Internal `report_type` |
|---|---|---|---|---|---|
| 1 | 🏠 | What Just Listed | Photo gallery of newest homes on the market | Buyer drips, prospecting | `new_listings_gallery` |
| 2 | 💰 | What Just Sold | Recent sales with prices, DOM & a data table | Seller prospecting, CMAs | `closed` |
| 3 | 📊 | Market Update | Median prices, inventory levels, trends — the full picture | Monthly sphere updates | `market_snapshot` |
| 4 | 📦 | What's Available | Current active listings, supply levels, inventory months | Buyer coaching, investors | `inventory` |
| 5 | ⭐ | Showcase My Listings | Your top 4 most impressive active listings | Listing agents, luxury | `featured_listings` |

**Eliminated from user view:** `new_listings` (table — absorbed into gallery), `price_bands`, `open_houses`. Backend stays intact for existing schedules.

### Step 2: Who's It For?

**Only appears when Step 1 = "What Just Listed."** All other stories skip to Step 3.

Six audience cards:

| Card | Internal Key | Filter Logic |
|---|---|---|
| All Listings | `all` | No filters |
| First-Time Buyers | `first_time` | 2+ bed, 2+ bath, SFR, ≤70% median |
| Luxury Homes | `luxury` | SFR, ≥150% median |
| Family Homes | `families` | 3+ bed, 2+ bath, SFR |
| Condo Watch | `condo` | Condos only |
| Investor Deals | `investors` | ≤50% median |

### Step 3: Where & When?

Combined area + timeframe (both are quick selections).

**Area:** City search (Google Places) or ZIP codes (up to 5). Show recent areas as clickable pills.

**Timeframe:** 7 / 14 / 30 / 60 / 90 days. Smart defaults by story:

| Story | Default | Why |
|---|---|---|
| What Just Listed | 14 days | Freshest inventory |
| What Just Sold | 30 days | Enough sales volume |
| Market Update | 30 days | Standard reporting period |
| What's Available | 30 days | Supply context |
| Showcase My Listings | 90 days | Wider pool for top 4 |

### Step 4: Deliver

Toggle between **Send Now** and **Schedule**.

**Send Now:**
- Checkboxes: View in browser, Download PDF, Send via email
- If email selected: recipient search (contacts/groups/manual entry)

**Schedule:**
- Frequency: Weekly / Biweekly / Monthly / Quarterly
- Day and time picker
- Recipient search (contacts/groups)
- Schedule name (auto-generated but editable: "Weekly Luxury Listings – Silver Lake")

### Sidebar: Summary + Live Preview

Desktop layout: wizard steps on the left (~55%), live email preview on the right (~45%).

The preview is NOT hardcoded sample data. It uses the **Shared Email Preview Component** (Workstream C) that reflects the actual V16 template layout for the selected story, with the agent's real branding (colors, logo, agent photo).

```
┌──────────────────────────┬─────────────────────────┐
│                          │                         │
│  Step Content            │  Live Email Preview     │
│  (wizard controls)       │  (real V16 layout)      │
│                          │                         │
│                          │  ┌───────────────────┐  │
│                          │  │ ████ HEADER ████  │  │
│                          │  │ Agent's gradient  │  │
│                          │  ├───────────────────┤  │
│                          │  │                   │  │
│                          │  │  AI Narrative...  │  │
│                          │  │                   │  │
│                          │  │   $925,000        │  │
│                          │  │   Median Price    │  │
│                          │  │                   │  │
│                          │  │  [photo] [photo]  │  │
│                          │  │  [photo] [photo]  │  │
│                          │  │                   │  │
│                          │  │  Active: 42       │  │
│                          │  │  DOM: 24          │  │
│                          │  │                   │  │
│                          │  │  [View Report]    │  │
│                          │  │                   │  │
│                          │  │  Agent Footer     │  │
│                          │  └───────────────────┘  │
│                          │                         │
├──────────────────────────┴─────────────────────────┤
│                    [← Back]  [Continue →]           │
└────────────────────────────────────────────────────┘
```

**What updates live as the agent configures:**
- Story selection → switches preview layout (gallery vs narrative vs table)
- Audience → updates header title and listing count
- Area → updates header title ("Market Snapshot – Silver Lake")
- Timeframe → updates period line

**What stays as sample data:**
- Metric values (need MLS data to be real)
- Property photos (Unsplash placeholders)
- AI narrative (placeholder text)
- Listing details (sample addresses/prices)

This is honest — the preview shows the real LAYOUT and BRANDING, with placeholder CONTENT. The agent sees exactly what the email structure looks like with their colors, not a fake wireframe.

### Routes

| Route | What It Does |
|---|---|
| `/app/reports/new` | Opens unified wizard in "Send Now" default mode |
| `/app/schedules/new` | Opens unified wizard in "Schedule" default mode |
| `/app/schedules/[id]/edit` | Opens unified wizard pre-filled with existing schedule data |

Both routes mount the same `UnifiedReportWizard` component. The only difference is the default delivery mode.

### API Contract (Unchanged)

```typescript
// Send Now (existing)
POST /api/proxy/v1/reports
{
  report_type: "new_listings_gallery",
  audience_filter: "luxury",
  city: "Silver Lake",
  zip_codes: [],
  lookback_days: 14,
  delivery: { view_in_browser: true, download_pdf: false, send_via_email: true },
  recipient_emails: ["jane@example.com"]
}

// Schedule (existing)
POST /api/proxy/v1/schedules
{
  name: "Weekly Luxury Listings – Silver Lake",
  report_type: "new_listings_gallery",
  audience_filter: "luxury",
  city: "Silver Lake",
  zip_codes: [],
  lookback_days: 14,
  cadence: "weekly",
  day_of_week: "monday",
  time_of_day: "09:00",
  timezone: "America/Los_Angeles",
  recipients: [{ type: "group", id: "grp_luxury" }]
}
```

**Zero backend changes.** The wizard maps stories to report_type keys, audiences to filter keys, and submits the same payload.

---

## WORKSTREAM B: Branding Overhaul

### Current State (from audit)

The branding page has 3 tabs: Colors (2 pickers + 6 presets), Logos (4 uploads), Preview & Test (fake wireframes + download/send buttons).

Missing: default property theme, accent sync, real preview, brand name, font awareness.

### New Branding Page Structure

Replace the 3-tab layout with a single-page layout that shows everything at once, with a persistent live preview on the right (same pattern as the wizard).

```
┌──────────────────────────┬─────────────────────────┐
│                          │                         │
│  BRANDING CONTROLS       │  LIVE PREVIEW           │
│                          │                         │
│  ┌────────────────────┐  │  Toggle:                │
│  │ Brand Identity     │  │  [Email] [Property PDF] │
│  │                    │  │                         │
│  │ Display Name:      │  │  ┌───────────────────┐  │
│  │ [Acme Realty    ]  │  │  │ Rendered preview  │  │
│  │                    │  │  │ using real V16    │  │
│  │ Tagline (optional):│  │  │ template layout   │  │
│  │ [Your Home Expert] │  │  │ with agent's      │  │
│  └────────────────────┘  │  │ actual branding   │  │
│                          │  │                   │  │
│  ┌────────────────────┐  │  │                   │  │
│  │ Colors             │  │  │                   │  │
│  │                    │  │  │                   │  │
│  │ Primary: [■ pick]  │  │  │                   │  │
│  │ Accent:  [■ pick]  │  │  │                   │  │
│  │                    │  │  │                   │  │
│  │ Presets:           │  │  │                   │  │
│  │ [Ind][Ocn][Crm]   │  │  │                   │  │
│  │ [For][Mid][Roy]   │  │  │                   │  │
│  │                    │  │  │                   │  │
│  │ Gradient preview:  │  │  │                   │  │
│  │ ████████████████   │  │  │                   │  │
│  └────────────────────┘  │  └───────────────────┘  │
│                          │                         │
│  ┌────────────────────┐  │  Actions:               │
│  │ Default Theme      │  │  [Send Test Email]      │
│  │                    │  │  [Download Sample PDF]   │
│  │ Property reports:  │  │                         │
│  │ ┌────┐┌────┐┌────┐│  │                         │
│  │ │Clas││Mod ││Eleg││  │                         │
│  │ └────┘└────┘└────┘│  │                         │
│  │ ┌────┐┌────┐      │  │                         │
│  │ │Teal││Bold│      │  │                         │
│  │ └────┘└────┘      │  │                         │
│  │                    │  │                         │
│  │ Selected: Bold     │  │                         │
│  │ Fonts: Clash +     │  │                         │
│  │        DM Sans     │  │                         │
│  └────────────────────┘  │                         │
│                          │                         │
│  ┌────────────────────┐  │                         │
│  │ Logos              │  │                         │
│  │                    │  │                         │
│  │ Header (light):    │  │                         │
│  │ [upload/preview]   │  │                         │
│  │                    │  │                         │
│  │ Footer (dark):     │  │                         │
│  │ [upload/preview]   │  │                         │
│  └────────────────────┘  │                         │
│                          │                         │
│  ┌────────────────────┐  │                         │
│  │ Agent Info         │  │                         │
│  │                    │  │                         │
│  │ Photo: [upload]    │  │                         │
│  │ Name:  [Sarah..]   │  │                         │
│  │ Title: [Senior..]  │  │                         │
│  │ Phone: [(310)..]   │  │                         │
│  │ Email: [sarah@..]  │  │                         │
│  │ License: [DRE#..]  │  │                         │
│  └────────────────────┘  │                         │
│                          │                         │
│         [ Save Changes ] │                         │
└──────────────────────────┴─────────────────────────┘
```

### Section Details

#### Brand Identity (NEW)
- **Display Name** — editable text, saved to `accounts.display_name` (new column, falls back to `accounts.name`)
- **Tagline** — optional, shown in email footer below brand name

#### Colors (ENHANCED)
- Same primary/accent pickers + 6 presets
- **Key change:** When accent color changes, it becomes the default accent for property reports too (accent sync)

#### Default Property Theme (NEW)
- 5 mini theme cards showing visual thumbnails (cover page preview)
- Each card shows the theme name and font pairing: "Bold — Clash Display + DM Sans"
- Selected theme is saved to `accounts.default_theme_id` (new DB column)
- The property wizard reads this as its initial value instead of hardcoded Teal

#### Logos (SIMPLIFIED)
- Reduce from 4 uploads to 2: **Header logo** (light, for gradient backgrounds) and **Footer logo** (dark, for white backgrounds)
- Email templates use header logo in header, footer logo in footer. Property reports use footer logo.
- If only one is uploaded, derive the other (or show a warning)

#### Agent Info (NEW — moved from Account Settings)
- Agent photo, name, title, phone, email, license number
- These are the values that render in every email footer and property report cover page
- Currently scattered across account settings — consolidate here since it's branding

### Live Preview (Right Panel)

Toggle between Email preview and Property PDF preview at the top.

**Email preview:** Uses the Shared Email Preview Component (Workstream C). Shows a Market Snapshot layout by default (the richest layout). Updates in real time as colors, logos, and agent info change.

**Property PDF preview:** Shows a mini cover page thumbnail for the selected theme, with the agent's colors and logo applied. This replaces the current fake wireframe.

**Actions at the bottom:**
- "Send Test Email" — generates a real email using the agent's current branding and sends it to their own address
- "Download Sample PDF" — generates a real property report PDF with the selected theme and current branding

### Database Changes

```sql
ALTER TABLE accounts ADD COLUMN display_name TEXT;
ALTER TABLE accounts ADD COLUMN tagline TEXT;
ALTER TABLE accounts ADD COLUMN default_theme_id INTEGER DEFAULT 4;  -- Teal
```

### API Changes

```python
# PATCH /api/v1/accounts/{id}/branding
{
  "display_name": "Acme Realty",
  "tagline": "Your Home Expert",
  "primary_color": "#1B365D",
  "secondary_color": "#B8860B",
  "default_theme_id": 5,          # Bold
  "header_logo_url": "...",
  "footer_logo_url": "...",
  "agent_name": "Sarah Chen",
  "agent_title": "Senior Realtor",
  "agent_phone": "(310) 555-1234",
  "agent_email": "sarah@acmerealty.com",
  "agent_license": "DRE #01234567",
  "agent_photo_url": "..."
}
```

### Accent Color Sync

When `secondary_color` (accent) is updated on the branding page:
1. Save to `accounts.secondary_color` (existing)
2. Property wizard reads `account.secondary_color` as the initial accent color in `step-theme.tsx`, instead of reading from the theme's hardcoded default
3. Agent can still override per-report in the property wizard, but the default matches their branding

```typescript
// In step-theme.tsx
const initialAccent = account.secondary_color || theme.defaultAccent;
```

---

## WORKSTREAM C: Shared Email Preview Component

### The Problem

Two preview implementations exist:
1. `schedule-builder/email-preview.tsx` — React mockup with hardcoded sample data, shows 3 report types
2. Branding page — static wireframe that looks nothing like real emails

Neither reflects the V16 templates we built. We need one component used everywhere.

### The Solution: `SharedEmailPreview`

A single React component that renders a scaled-down version of the actual V16 email template layouts. Not a pixel-perfect replica of the f-string HTML — a React interpretation that matches the visual structure, uses the agent's real branding, and swaps content based on the selected report type.

```typescript
interface SharedEmailPreviewProps {
  // Branding (from account)
  primaryColor: string;
  accentColor: string;
  headerLogoUrl?: string;
  agentName: string;
  agentTitle?: string;
  agentPhone?: string;
  agentEmail?: string;
  agentPhotoUrl?: string;

  // Report configuration
  reportType: 'new_listings_gallery' | 'closed' | 'market_snapshot' | 'inventory' | 'featured_listings';
  audienceFilter?: string;
  areaName?: string;
  lookbackDays?: number;

  // Display
  scale?: number;       // 0.0-1.0, for fitting in sidebar (default 0.6)
  interactive?: boolean; // click to zoom sections
}
```

### What It Renders Per Report Type

| Report Type | Preview Shows |
|---|---|
| `market_snapshot` | AI narrative placeholder → 56px hero stat → 2×2 photo grid (Unsplash) → stacked stats → quick take → CTA → agent footer |
| `new_listings_gallery` | AI narrative → gallery count badge → auto-layout photo cards (count based on audience cap) → quick take → CTA → agent footer |
| `closed` | AI narrative → hero stat → 2×2 SOLD badges → data table (2-3 rows) → quick take → CTA → agent footer |
| `inventory` | AI narrative → hero stat → 2×2 Active badges → data table (2-3 rows) → quick take → CTA → agent footer |
| `featured_listings` | AI narrative → gallery count "4" → 2×2 large cards → quick take → CTA → agent footer |

### What's Real vs Sample

| Element | Real (from account) | Sample (placeholder) |
|---|---|---|
| Header gradient | ✅ primaryColor → accentColor | — |
| Logo | ✅ agent's uploaded logo | — |
| Report title | ✅ "{Type} – {Area}" | Falls back to "Market Snapshot – Your Area" |
| Period line | ✅ "Last {N} days" | — |
| AI narrative | — | ✅ Placeholder paragraph per type |
| Hero stat value | — | ✅ Sample: "$925,000" or "42" etc |
| Property photos | — | ✅ Unsplash real estate photos |
| Listing prices | — | ✅ Sample: "$1.29M", "$875K" etc |
| Table data | — | ✅ 2-3 sample rows |
| Quick take | — | ✅ Placeholder per type |
| CTA button | ✅ primaryColor | — |
| Agent footer | ✅ All agent info from account | — |

### Where It's Used

| Location | Props Source | Scale |
|---|---|---|
| Unified Wizard (right panel) | Wizard state + account branding | 0.55 |
| Branding page (right panel) | Branding form state (live as user edits) | 0.55 |
| Schedule list (hover/expand) | Schedule config + account branding | 0.4 (future) |

### Component Structure

```
components/shared/
├── email-preview/
│   ├── index.tsx                    ← Main component, layout router
│   ├── preview-header.tsx           ← Gradient header with logo
│   ├── preview-narrative.tsx        ← AI narrative placeholder
│   ├── preview-hero-stat.tsx        ← Big serif number
│   ├── preview-photo-grid.tsx       ← 2×2, 3×2, stacked, list
│   ├── preview-stacked-stats.tsx    ← Vertical stat rows
│   ├── preview-data-table.tsx       ← Sales/inventory table
│   ├── preview-quick-take.tsx       ← Accent callout
│   ├── preview-cta.tsx              ← Button in tinted area
│   ├── preview-agent-footer.tsx     ← Photo + pills
│   ├── preview-gallery-count.tsx    ← Count badge
│   └── sample-data.ts              ← Per-type placeholder content
```

Each sub-component mirrors a V16 layout builder but renders React/Tailwind instead of email HTML tables. The visual output should be indistinguishable from the real email at preview scale.

---

## Implementation Order

### Phase 1: Shared Email Preview Component (Workstream C)

Do this first. Both the wizard and branding page depend on it.

1. Create `components/shared/email-preview/` component structure
2. Build `preview-header.tsx` — gradient, logo, title, period (uses real branding)
3. Build `preview-agent-footer.tsx` — photo, name, pills (uses real branding)
4. Build `preview-hero-stat.tsx` — 56px serif number
5. Build `preview-narrative.tsx` — 16px placeholder paragraph
6. Build `preview-photo-grid.tsx` — 2×2, 3×2, stacked, list layouts with Unsplash photos
7. Build `preview-stacked-stats.tsx` — vertical stat rows
8. Build `preview-data-table.tsx` — branded header, 2-3 sample rows
9. Build `preview-quick-take.tsx` — accent callout
10. Build `preview-cta.tsx` — branded button
11. Build `preview-gallery-count.tsx` — count badge
12. Build `sample-data.ts` — per-type placeholder content
13. Build `index.tsx` — routes to correct layout based on reportType
14. Test with all 5 active report types and 3 color schemes

### Phase 2: Branding Overhaul (Workstream B)

15. Add DB columns: `display_name`, `tagline`, `default_theme_id`
16. Update API: PATCH endpoint accepts new fields
17. Rebuild branding page: single-page layout with controls left, preview right
18. Add Brand Identity section (display name, tagline)
19. Add Default Theme section (5 theme cards with font info)
20. Add Agent Info section (consolidate from account settings)
21. Simplify Logos to 2 uploads (header + footer)
22. Mount `SharedEmailPreview` in right panel
23. Add Email/Property PDF toggle for preview
24. Wire accent sync: branding accent → property wizard default
25. Wire default theme: branding theme → property wizard default
26. Test: change colors → preview updates live → save → send test email → verify

### Phase 3: Unified Wizard (Workstream A)

27. Create `UnifiedReportWizard` component with 4-step flow
28. Build Step 1: 5 story cards with mapping to report_type
29. Build Step 2: 6 audience cards with skip logic
30. Build Step 3: area (city/ZIP) + timeframe with smart defaults
31. Build Step 4: Send Now / Schedule toggle with delivery options
32. Mount `SharedEmailPreview` in right panel (same as branding)
33. Wire preview to update on every wizard state change
34. Wire Submit to POST /reports (send now) or POST /schedules (schedule)
35. Update routes: `/app/reports/new` and `/app/schedules/new` both mount unified wizard
36. Handle edit mode: `/app/schedules/[id]/edit` pre-fills wizard from schedule data
37. Test all 5 stories × send now + schedule × city + ZIP

### Phase 4: Cleanup

38. Remove old `schedule-builder/email-preview.tsx` (replaced by shared component)
39. Remove old branding page wireframe previews
40. Keep old `v0-report-builder/` components as fallback until unified wizard is stable
41. Update schedule list page to show story-based labels instead of report_type IDs
42. Add gallery empty state message for 0-listing reports

---

## File Map (New + Modified)

```
NEW FILES:
components/shared/email-preview/
  ├── index.tsx
  ├── preview-header.tsx
  ├── preview-narrative.tsx
  ├── preview-hero-stat.tsx
  ├── preview-photo-grid.tsx
  ├── preview-stacked-stats.tsx
  ├── preview-data-table.tsx
  ├── preview-quick-take.tsx
  ├── preview-cta.tsx
  ├── preview-agent-footer.tsx
  ├── preview-gallery-count.tsx
  └── sample-data.ts

components/unified-wizard/
  ├── index.tsx                      ← Main shell, step nav, sidebar
  ├── types.ts                       ← Story type, state interface, mappings
  ├── step-story.tsx                 ← 5 story cards
  ├── step-audience.tsx              ← 6 audience cards
  ├── step-where-when.tsx            ← Area + timeframe combined
  ├── step-deliver.tsx               ← Send Now / Schedule toggle
  └── sidebar-summary.tsx            ← Text summary + preview mount

MODIFIED FILES:
app/app/settings/branding/page.tsx   ← Full rebuild
app/app/reports/new/page.tsx         ← Mount UnifiedWizard (sendNow mode)
app/app/schedules/new/page.tsx       ← Mount UnifiedWizard (schedule mode)
app/app/schedules/[id]/edit/page.tsx ← Mount UnifiedWizard (edit mode)
components/property-wizard/step-theme.tsx ← Read default_theme_id + accent from account

DB MIGRATION:
accounts table: +display_name, +tagline, +default_theme_id

API:
PATCH /api/v1/accounts/{id}/branding ← Accept new fields
```

---

## What We're NOT Doing

- **No new backend report types.** Same 6 active types, same API contracts.
- **No real MLS data in preview.** Preview uses placeholder content with real branding. Real data comes after generation.
- **No email layout variants/themes.** The V16 templates have one visual system. Differentiation comes from colors, not multiple email themes. This is correct — email clients are too constrained for multiple visual systems.
- **No font selection for emails.** Email fonts are limited to Georgia (serif) and system sans-serif. This is a hard email client constraint, not a product decision.
- **No custom CSS / white-label override.** Future phase for enterprise accounts.
