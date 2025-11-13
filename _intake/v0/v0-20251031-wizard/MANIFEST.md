# V0 Import Manifest - Wizard Component

**Date:** October 31, 2025  
**Source:** v0-20251031-wizard.zip

## Files Extracted

### Main Components
- `components/report-wizard.tsx` - Main wizard component with 4 steps
- `components/stepper.tsx` - Animated stepper component with progress indicator

### UI Components (shadcn/ui)
- `components/ui/button.tsx` - Button component
- `components/ui/card.tsx` - Card, CardHeader, CardTitle, CardDescription, CardContent
- `components/ui/input.tsx` - Input component
- `components/ui/label.tsx` - Label component
- `components/ui/badge.tsx` - Badge component

### Utilities
- `lib/utils.ts` - Utility functions (cn, clsx, tailwind-merge)

### Pages (Not Used)
- `app/dashboard/reports/new/page.tsx` - Example implementation (reference only)

### Public Assets
- Multiple images in `public/` directory (not copied - using placeholder text instead)

## Components Copied to Repo

1. **apps/web/components/Wizard.tsx** (from report-wizard.tsx)
   - Full wizard with 4 steps: Type, Area, Filters, Review
   - Validation functions
   - Payload builder
   - Export: `default Wizard`, `validateStep`, `buildPayload`

2. **apps/web/components/stepper.tsx**
   - Animated progress stepper with framer-motion
   - Check marks for completed steps

3. **apps/web/components/ui/** (5 components)
   - button.tsx
   - card.tsx
   - input.tsx
   - label.tsx
   - badge.tsx

4. **apps/web/lib/utils.ts**
   - cn() utility for className merging

## Dependencies Installed

```bash
pnpm --filter web add:
  - framer-motion (animations)
  - lucide-react (icons)
  - class-variance-authority (button variants)
  - clsx (className utilities)
  - tailwind-merge (Tailwind class merging)
  - @radix-ui/react-label
  - @radix-ui/react-slot
```

## Files Modified

1. **apps/web/app/app/reports/new/page.tsx**
   - Replaced old simple form
   - Now uses <Wizard> component
   - Implements API calls to POST /v1/reports
   - Polls for status
   - Shows PDF/HTML links on completion

## Import Path Updates

All components use `@/` prefix which maps to `apps/web/` root via tsconfig.json paths.
No import path changes needed - already compatible with our setup.

## Features

### Wizard Steps
1. **Report Type** - Select from 6 report templates (market_snapshot, new_listings, inventory, closed, price_bands, open_houses)
2. **Area** - Choose city, ZIP codes, or polygon (polygon disabled for now)
3. **Filters** - Set lookback period, property type, price range, beds/baths
4. **Review** - Summary and API payload preview

### Validation
- Step 1: Requires report type selection
- Step 2: Requires city name or at least one ZIP code
- Step 3: Requires lookback period selection
- Step 4: Ready to generate

### Payload Format
Matches API spec exactly:
```json
{
  "report_type": "market_snapshot",
  "city": "Houston",
  "lookback_days": 30,
  "filters": {
    "type": "RES",
    "minprice": 100000,
    "maxprice": 500000,
    "beds": 3,
    "baths": 2
  }
}
```

## Not Copied

- Images/public assets (wizard works without them)
- Full shadcn/ui library (only copied 5 needed components)
- Example pages (used as reference only)
- next.config, tailwind.config (conflicts with our setup)
- Other dashboard pages (not needed)

## Integration Status

✅ Wizard component copied and adapted  
✅ Dependencies installed  
✅ New report page wired up  
✅ API calls integrated  
✅ Polling implemented  
✅ Result display working  
✅ All imports resolved  
✅ Ready for testing  










