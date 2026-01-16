# TrendyReports Design System & Builder Specification

## Design Philosophy

**Mature. Clean. Professional.**

This is a tool for real estate professionals, not a tech demo. Every pixel should serve a purpose. When in doubt, remove it.

### Core Principles

1. **Content over chrome** - The report preview is the product. UI should fade into the background.
2. **Reduce, don't add** - Fewer options, fewer colors, fewer animations. Simplicity is sophistication.
3. **Consistent everywhere** - One design language across the entire platform. No exceptions.
4. **Respect the user** - Agents are busy professionals. Don't make them think.

---

## Color Palette

### Base Colors (90% of the UI)

```
White:       #FFFFFF    - Cards, panels, backgrounds
Gray 50:     #F9FAFB    - Page backgrounds, subtle sections
Gray 100:    #F3F4F6    - Borders, dividers, disabled backgrounds
Gray 200:    #E5E7EB    - Input borders, secondary borders
Gray 400:    #9CA3AF    - Placeholder text, tertiary text
Gray 500:    #6B7280    - Secondary text, labels
Gray 700:    #374151    - Primary text, headings
Gray 900:    #111827    - Bold headings, emphasis
```

### Accent Colors (Used sparingly)

```
Violet 600:  #7C3AED    - Primary buttons, selected states, links
Violet 50:   #F5F3FF    - Selected card backgrounds, hover states

Green 500:   #22C55E    - Success states, completed indicators
Green 50:    #F0FDF4    - Success backgrounds (very subtle)

Amber 500:   #F59E0B    - Warning states, needs attention
Red 500:     #EF4444    - Errors only (rare)
```

### Usage Rules

| Element | Color | Notes |
|---------|-------|-------|
| Page background | Gray 50 | Subtle, not pure white |
| Cards/Panels | White | With gray-200 border or subtle shadow |
| Primary text | Gray 700 | Not pure black |
| Secondary text | Gray 500 | Labels, hints |
| Primary button | Violet 600 | Solid, white text |
| Secondary button | White | Gray-200 border, gray-700 text |
| Selected state | Violet 50 bg + Violet 600 border | Cards, options |
| Completed indicator | Green 500 | Checkmark with green-50 background circle |
| Input borders | Gray 200 | Gray 400 on focus |
| Disabled | Gray 100 bg, Gray 400 text | |

### What NOT To Do

- ❌ No gradients in the UI (save for report preview only)
- ❌ No colored card backgrounds (blue cards, purple cards, etc.)
- ❌ No animated icons with changing colors
- ❌ No emoji as primary UI elements
- ❌ No shadows heavier than `shadow-sm`
- ❌ No borders heavier than 1px
- ❌ No more than 2 colors visible at once (excluding grays)

---

## Typography

```
Font:        Inter (or system-ui fallback)
Headings:    font-semibold (600), gray-900
Body:        font-normal (400), gray-700
Labels:      font-medium (500), gray-500, text-sm
Hints:       font-normal (400), gray-400, text-sm
```

### Scale

```
Page title:     text-xl (20px), font-semibold
Section title:  text-base (16px), font-semibold
Card title:     text-sm (14px), font-medium
Body text:      text-sm (14px), font-normal
Small/hint:     text-xs (12px), font-normal
```

---

## Component Patterns

### Cards

```tsx
// Standard card
<div className="bg-white border border-gray-200 rounded-lg p-4">

// Selectable card (unselected)
<div className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-gray-300">

// Selectable card (selected)
<div className="bg-violet-50 border-2 border-violet-600 rounded-lg p-4">
```

### Buttons

```tsx
// Primary
<button className="bg-violet-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-violet-700">

// Secondary
<button className="bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50">

// Ghost
<button className="text-gray-500 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 hover:text-gray-700">
```

### Inputs

```tsx
<input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-600 focus:ring-1 focus:ring-violet-600" />
```

### Status Indicators

```tsx
// Completed step
<div className="w-6 h-6 rounded-full bg-green-50 flex items-center justify-center">
  <Check className="w-4 h-4 text-green-500" />
</div>

// Current/Active step
<div className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center">
  <span className="text-white text-xs font-medium">2</span>
</div>

// Incomplete step
<div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">
  <span className="text-gray-400 text-xs font-medium">3</span>
</div>
```

---

## Icons

### Rules

1. **Use Lucide icons only** - Consistent stroke width and style
2. **One color per icon** - Gray 400 default, Gray 700 on hover/active, Violet 600 when selected
3. **No animations** - Icons are static
4. **Size consistently** - 16px (w-4) for inline, 20px (w-5) for buttons, 24px (w-6) for features

### What To Remove

- ❌ Animated loading spinners with color changes (use simple gray spinner)
- ❌ Emoji icons (📊 📸 🏠) - use Lucide equivalents
- ❌ Multi-colored icon sets
- ❌ Bouncing, pulsing, or wobbling icons

---

## Builder Layout Specification

### Two-Panel Layout (Applies to Schedule Builder & Report Builder)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back                                               [Cancel]  [Generate]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │                         │  │                                         │  │
│  │   CONFIGURATION         │  │   PREVIEW                               │  │
│  │   40% width             │  │   60% width                             │  │
│  │                         │  │   (this is the product)                 │  │
│  │                         │  │                                         │  │
│  │                         │  │                                         │  │
│  │                         │  │                                         │  │
│  │                         │  │                                         │  │
│  └─────────────────────────┘  └─────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Grid

```tsx
<div className="grid grid-cols-[400px,1fr] gap-8">
  <div>{/* Config panel - fixed 400px */}</div>
  <div className="sticky top-6">{/* Preview - flexible, takes remaining space */}</div>
</div>
```

### No Sidebar

When in builder mode (`/app/schedules/new`, `/app/schedules/[id]/edit`, `/app/reports/new`):
- Hide the main sidebar completely
- Builder takes full viewport width
- Only show: Back link, Cancel button, Primary action button

---

## Report Type Selection

### Use 3 Cards, Not 6

Agents use three report types. Show three cards.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  What type of report?                                           │
│                                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │                 │ │                 │ │                 │   │
│  │  [Icon]         │ │  [Icon]         │ │  [Icon]         │   │
│  │                 │ │  ● SELECTED     │ │                 │   │
│  │  New Listings   │ │  Market Update  │ │  Closed Sales   │   │
│  │                 │ │                 │ │                 │   │
│  │  Photo gallery  │ │  Stats & trends │ │  Recent sales   │   │
│  │  of new homes   │ │  for the area   │ │  in the area    │   │
│  │                 │ │                 │ │                 │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Card Styling

```tsx
// Unselected
<div className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-gray-300 transition-colors">
  <BarChart3 className="w-6 h-6 text-gray-400 mb-3" />
  <h3 className="text-sm font-medium text-gray-900">Market Update</h3>
  <p className="text-xs text-gray-500 mt-1">Stats & trends for the area</p>
</div>

// Selected
<div className="bg-violet-50 border-2 border-violet-600 rounded-lg p-4">
  <BarChart3 className="w-6 h-6 text-violet-600 mb-3" />
  <h3 className="text-sm font-medium text-gray-900">Market Update</h3>
  <p className="text-xs text-gray-500 mt-1">Stats & trends for the area</p>
</div>
```

### Report Type Values

| Display | Internal Value | Icon |
|---------|----------------|------|
| New Listings | `new_listings_gallery` | `Images` |
| Market Update | `market_snapshot` | `BarChart3` |
| Closed Sales | `closed` | `Home` |

---

## Audience Filter (Inline Pills)

**Only show when "New Listings" is selected.** Appears directly below the report type cards, not as a separate section.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Target audience (optional)                                     │
│                                                                 │
│  ┌────────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐ │
│  │ All        │ │ First-Time   │ │ Luxury     │ │ Families   │ │
│  │ Listings   │ │ Buyers ✓     │ │ Clients    │ │            │ │
│  └────────────┘ └──────────────┘ └────────────┘ └────────────┘ │
│                                                                 │
│  ┌──────────────┐ ┌────────────┐                               │
│  │ Condo        │ │ Investors  │                               │
│  │ Buyers       │ │            │                               │
│  └──────────────┘ └────────────┘                               │
│                                                                 │
│  ℹ 2+ beds, 2+ baths, SFR, ≤70% of median price               │
│    (~$805K in Irvine based on current market)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Pill Styling

```tsx
// Unselected pill
<button className="px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-200 rounded-full hover:bg-gray-50">
  Luxury Clients
</button>

// Selected pill
<button className="px-3 py-1.5 text-sm text-violet-700 bg-violet-50 border border-violet-200 rounded-full">
  <Check className="w-3 h-3 inline mr-1" />
  First-Time Buyers
</button>
```

### Smart Presets (PRESERVE THESE)

Use the existing SMART_PRESETS from `packages/ui/.../types.ts`. These are market-adaptive:

```typescript
const AUDIENCE_PRESETS = {
  all: {
    label: "All Listings",
    description: "No filters",
    filters: null
  },
  first_time: {
    label: "First-Time Buyers",
    description: "2+ beds, 2+ baths, SFR, ≤70% median",
    filters: {
      beds_min: 2,
      baths_min: 2,
      property_types: ["SFR"],
      price_strategy: { mode: "maxprice_pct_of_median_list", value: 70 }
    }
  },
  luxury: {
    label: "Luxury Clients", 
    description: "SFR, ≥150% median",
    filters: {
      property_types: ["SFR"],
      price_strategy: { mode: "minprice_pct_of_median_list", value: 150 }
    }
  },
  families: {
    label: "Families",
    description: "3+ beds, 2+ baths, SFR",
    filters: {
      beds_min: 3,
      baths_min: 2,
      property_types: ["SFR"]
    }
  },
  condo: {
    label: "Condo Buyers",
    description: "Condos only",
    filters: {
      property_types: ["CONDO"]
    }
  },
  investors: {
    label: "Investors",
    description: "≤50% median",
    filters: {
      price_strategy: { mode: "maxprice_pct_of_median_list", value: 50 }
    }
  }
};
```

**The hint text should show the calculated price based on the selected area's median.**

---

## Configuration Sections (Left Panel)

Use simple stacked sections, not heavy accordions. Each section is always visible.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ● Report Type                                     ✓    │   │
│  │                                                         │   │
│  │  [3 cards + audience pills if New Listings]             │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ● Area                                            ✓    │   │
│  │                                                         │   │
│  │  [City autocomplete or ZIP tags]                        │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ● Lookback Period                                 ✓    │   │
│  │                                                         │   │
│  │  ○ 7d   ○ 14d   ● 30d   ○ 60d   ○ 90d                  │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Additional sections for Schedule Builder only:]              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ● Cadence                                         ✓    │   │
│  │                                                         │   │
│  │  Weekly ▼   Monday ▼   9:00 AM ▼   Pacific ▼           │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ○ Recipients                                      ⚠    │   │
│  │                                                         │   │
│  │  [Search input + recipient list]                        │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Section Header

```tsx
<div className="flex items-center justify-between mb-3">
  <h3 className="text-sm font-medium text-gray-900">Report Type</h3>
  {isComplete ? (
    <div className="w-5 h-5 rounded-full bg-green-50 flex items-center justify-center">
      <Check className="w-3 h-3 text-green-500" />
    </div>
  ) : needsAttention ? (
    <div className="w-5 h-5 rounded-full bg-amber-50 flex items-center justify-center">
      <AlertCircle className="w-3 h-3 text-amber-500" />
    </div>
  ) : null}
</div>
```

---

## Preview Panel (Right Side)

### Schedule Builder → Email Preview

Shows the actual email that will be sent.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Preview                                                        │
│                                                                 │
│  Subject: Your Market Update for Irvine, CA is Ready           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  [Scaled email mockup - see email template spec]        │   │
│  │                                                         │   │
│  │  - Gradient header with logo                            │   │
│  │  - Report content                                       │   │
│  │  - Agent footer                                         │   │
│  │  - Powered by footer                                    │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Next send: Monday, Jan 20 at 9:00 AM PT                       │
│  Recipients: 3 contacts (14 emails)                            │
│                                                                 │
│  [Send Test Email]                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Report Builder → Report Preview

Shows the actual report that will be generated.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Preview                                                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  [Scaled report mockup]                                 │   │
│  │                                                         │   │
│  │  - Header with branding                                 │   │
│  │  - Hero metric                                          │   │
│  │  - Stats                                                │   │
│  │  - Content sections                                     │   │
│  │  - Footer                                               │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Market Update · Irvine, CA · Last 30 days                     │
│                                                                 │
│  [Preview Full Report]                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Form Elements

### Lookback Period (Radio Pills)

```tsx
<div className="flex gap-2">
  {[7, 14, 30, 60, 90].map(days => (
    <button
      key={days}
      className={cn(
        "px-3 py-1.5 text-sm rounded-lg transition-colors",
        selected === days
          ? "bg-violet-600 text-white"
          : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
      )}
    >
      {days}d
    </button>
  ))}
</div>
```

### City Autocomplete

```tsx
<div className="relative">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
  <input
    type="text"
    placeholder="Search city..."
    className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-violet-600"
  />
</div>

{/* Selected city */}
<div className="mt-2 flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
  <MapPin className="w-4 h-4 text-gray-400" />
  <span className="text-sm text-gray-700">Irvine, CA</span>
  <button className="ml-auto text-gray-400 hover:text-gray-600">
    <X className="w-4 h-4" />
  </button>
</div>
```

### ZIP Code Tags

```tsx
<div className="flex flex-wrap gap-2">
  {zipCodes.map(zip => (
    <span key={zip} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm text-gray-700">
      {zip}
      <button className="text-gray-400 hover:text-gray-600">
        <X className="w-3 h-3" />
      </button>
    </span>
  ))}
</div>
```

### Cadence Dropdowns (Schedule Builder)

Use simple, compact dropdowns in a row:

```tsx
<div className="flex items-center gap-3">
  <Select value={frequency}>
    <option>Weekly</option>
    <option>Monthly</option>
  </Select>
  
  <Select value={dayOfWeek}>
    <option>Monday</option>
    {/* ... */}
  </Select>
  
  <Select value={time}>
    <option>9:00 AM</option>
    {/* ... */}
  </Select>
  
  <Select value={timezone}>
    <option>Pacific</option>
    {/* ... */}
  </Select>
</div>
```

---

## Loading States

Simple, not flashy:

```tsx
// Button loading
<button disabled className="bg-violet-600 text-white px-4 py-2 rounded-lg opacity-75">
  <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
  Generating...
</button>

// Content loading
<div className="animate-pulse">
  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
</div>
```

---

## Summary: What To Implement

### Immediate Fixes

1. **Remove sidebar** in builder mode
2. **40/60 split** - Config 400px fixed, Preview flexible
3. **3 report cards** - New Listings, Market Update, Closed Sales only
4. **Inline audience pills** - Below report cards when New Listings selected
5. **Preserve SMART_PRESETS** - Use existing market-adaptive logic
6. **Clean up colors** - Gray base, violet accents only, green for complete
7. **Remove animated/colored icons** - Static Lucide icons, single color
8. **Simple sections** - Not heavy accordions, just stacked cards

### Files to Update

```
apps/web/components/report-builder/
apps/web/components/schedule-builder/
apps/web/app/app/layout.tsx (sidebar hide logic)
```

### Files to Reference (Don't Reinvent)

```
packages/ui/src/components/schedules/types.ts (SMART_PRESETS, AUDIENCE_OPTIONS)
```

---

## The Test

When done, the builders should feel like:
- A professional tool, not a startup demo
- Calm and focused, not busy and overwhelming
- The preview is the star, config is supporting actor
- An agent can create a report in 30 seconds without confusion
