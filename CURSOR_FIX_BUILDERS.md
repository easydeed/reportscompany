# Cursor Prompt: Fix Builders & Apply Design System

Reference the TRENDYREPORTS_DESIGN_SYSTEM.md file I've added to the repo. That's the source of truth.

## Critical Fixes Needed

### 1. Layout: 40/60 Split (Config/Preview)

Current: Preview is either too small or showing below config
Fix: 
```tsx
<div className="grid grid-cols-[400px,1fr] gap-8">
  <div>{/* Config - fixed 400px */}</div>
  <div className="sticky top-6">{/* Preview - takes remaining space */}</div>
</div>
```

The preview is the product. It should dominate the screen.

### 2. Hide Sidebar in Builder Mode

Routes that should have NO sidebar:
- /app/schedules/new
- /app/schedules/[id]/edit  
- /app/reports/new

The builder should take full viewport width. Check app layout and conditionally hide sidebar based on route.

### 3. Simplify to 3 Report Types

Remove the 6-card approach. Use only:
- New Listings (`new_listings_gallery`) - Icon: `Images`
- Market Update (`market_snapshot`) - Icon: `BarChart3`
- Closed Sales (`closed`) - Icon: `Home`

These are what agents actually use.

### 4. Inline Audience Pills (Not Separate Accordion)

When "New Listings" is selected, show audience pills DIRECTLY BELOW the report type cards. Not as a separate section/accordion.

Use the existing SMART_PRESETS from `packages/ui/src/components/schedules/types.ts`. Don't recreate them.

Pills: All Listings, First-Time Buyers, Luxury Clients, Families, Condo Buyers, Investors

Show hint text below pills with the filter criteria. If area is selected, calculate and show the actual price threshold based on median.

### 5. Clean Up Visual Noise

**Remove:**
- Colored card backgrounds (no blue/purple/green cards)
- Gradient backgrounds in the UI
- Animated icons
- Emoji icons (📊 📸 etc)
- Heavy shadows
- Multiple accent colors

**Use:**
- White cards with gray-200 borders
- Violet-50 background + violet-600 border for SELECTED state only
- Gray icons (gray-400 default, violet-600 when selected)
- Green-500 checkmarks in green-50 circles for completed states
- Simple Lucide icons, no animation

### 6. Section Status Indicators

Each config section should show status:
- ✓ Green check (green-500) in green-50 circle = Complete
- ⚠ Amber icon (amber-500) in amber-50 circle = Needs attention
- Nothing = Not started / Optional

### 7. Stacked Sections, Not Heavy Accordions

Don't use collapsible accordions. Use simple stacked cards where all sections are visible:

```
┌─────────────────────────┐
│ Report Type        ✓    │
│ [content]               │
└─────────────────────────┘

┌─────────────────────────┐
│ Area               ✓    │
│ [content]               │
└─────────────────────────┘

┌─────────────────────────┐
│ Lookback Period    ✓    │
│ [content]               │
└─────────────────────────┘
```

## Files to Update

- `apps/web/components/report-builder/*` - Apply all fixes
- `apps/web/components/schedule-builder/*` - Apply all fixes
- `apps/web/app/app/layout.tsx` - Add sidebar hide logic for builder routes

## Files to Reference (Use These, Don't Recreate)

- `packages/ui/src/components/schedules/types.ts` - SMART_PRESETS, AUDIENCE_OPTIONS

## Expected Result

- Clean, professional, mature UI
- Preview takes 60% of screen and is the focus
- Config is compact and scannable
- No visual clutter
- Agent can build a report in 30 seconds
