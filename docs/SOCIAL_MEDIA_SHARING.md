# Social Media Sharing Feature

> **Status:** COMPLETE | **Last Updated:** December 27, 2025

## Overview

TrendyReports users can now generate **1080x1920 JPEG images** optimized for social media stories (Instagram, TikTok, Facebook Stories, LinkedIn Stories). These social images incorporate the user's full branding and key report metrics in an eye-catching vertical format.

## Feature Summary

| Aspect | Details |
|--------|---------|
| Output Format | JPEG, 1080x1920 pixels (9:16 aspect ratio) |
| Target Platforms | Instagram Stories, TikTok, Facebook Stories, LinkedIn |
| Branding | Full white-label support (logo, colors, headshot, contact) |
| Report Types | All 8 report types supported |
| User Experience | One-click share button in Reports table |

---

## Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   1. User generates report (any type)                                   │
│                    ↓                                                     │
│   2. Report appears in /app/reports with Share button (pink icon)       │
│                    ↓                                                     │
│   3. User clicks Share → opens /social/{runId} in new tab               │
│                    ↓                                                     │
│   4. Social template renders with their branding + metrics              │
│                    ↓                                                     │
│   5. User screenshots or uses browser "Save Image As"                   │
│                    ↓                                                     │
│   6. User uploads to Instagram/TikTok/Facebook                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technical Flow

```
/social/[runId]/page.tsx
        │
        ├── Fetches /v1/reports/{runId}/data (same as PDF)
        │
        ├── Selects social template based on report_type
        │
        ├── Calls buildSocial*Html() from lib/social-templates.ts
        │
        └── Returns server-rendered HTML (1080x1920)
```

---

## Files Created

### Frontend

| File | Purpose |
|------|---------|
| `apps/web/app/social/[runId]/page.tsx` | Social image render endpoint |
| `apps/web/lib/social-templates.ts` | Template builder functions |
| `apps/web/templates/social/social-market-snapshot.html` | Market Snapshot template |
| `apps/web/templates/social/social-new-listings.html` | New Listings template |
| `apps/web/templates/social/social-closed.html` | Closed Sales template |
| `apps/web/templates/social/social-inventory.html` | Inventory template |
| `apps/web/templates/social/social-gallery.html` | Gallery/Featured template |
| `apps/web/templates/social/social-price-bands.html` | Price Bands template |

### Backend (Worker)

| File | Purpose |
|------|---------|
| `apps/worker/src/worker/social_engine.py` | PDFShift JPEG conversion (optional) |

### UI Updates

| File | Change |
|------|--------|
| `apps/web/app/app/reports/page.tsx` | Added Share button with tooltip |

---

## Template Design Principles

### 1. Mobile-First Vertical Layout (1080x1920)

All templates follow the Instagram Story / TikTok format:
- **9:16 aspect ratio** (portrait)
- **1080px wide, 1920px tall**
- Optimized for mobile viewing

### 2. Bold, Eye-Catching Metrics

Each template features:
- **Hero metric**: Large, prominent number (e.g., $1.2M, 47 Homes Sold)
- **Supporting metrics**: 2-4 additional KPIs in card format
- **Period badge**: Shows timeframe (e.g., "Last 30 days")

### 3. Full Branding Integration

Templates include:
- **Header logo**: User's company logo
- **Brand colors**: Primary and accent colors from branding settings
- **Agent headshot**: Circular photo in footer
- **Contact info**: Name, phone/email, website
- **Footer logo**: Company logo for gray backgrounds

### 4. Call-to-Action Ready

Templates include:
- Professional layout that invites engagement
- Space for agent contact information
- Clean, modern design that stands out in feeds

---

## Template Breakdown

### 1. Market Snapshot (`social-market-snapshot.html`)

```
┌──────────────────────────┐
│ ▓▓▓ GRADIENT HEADER ▓▓▓  │
│    [LOGO]                │
│    Market Snapshot       │
│    Los Angeles, CA       │
├──────────────────────────┤
│                          │
│    $1.2M                 │
│    Median Sale Price     │
│                          │
│    ┌────┐  ┌────┐        │
│    │ 47 │  │ 28 │        │
│    │Sold│  │DOM │        │
│    └────┘  └────┘        │
│                          │
│    ┌────┐  ┌────┐        │
│    │2.1 │  │98% │        │
│    │MOI │  │CTL │        │
│    └────┘  └────┘        │
│                          │
├──────────────────────────┤
│ [Photo] Agent Name       │
│         Phone • Email    │
│    [COMPANY LOGO]        │
└──────────────────────────┘
```

**Metrics shown:**
- Median Sale Price (hero)
- Homes Sold
- Average Days on Market
- Months of Inventory
- Sale-to-List Ratio

### 2. New Listings (`social-new-listings.html`)

**Metrics shown:**
- New Listings Count (hero, green gradient)
- Median Price
- Average DOM
- CTA: "Contact me for a private showing!"

### 3. Closed Sales (`social-closed.html`)

**Metrics shown:**
- Homes Sold (hero, blue gradient)
- Median Close Price
- Average DOM
- Sale-to-List Ratio
- Insight card: "Homes are selling at X% of asking price"

### 4. Inventory (`social-inventory.html`)

**Metrics shown:**
- Active Listings (hero, purple gradient)
- Median Price
- Median DOM
- Months of Inventory

### 5. Gallery / Featured (`social-gallery.html`)

**Content:**
- Featured property hero photo (700px tall)
- Price (large)
- Address
- Beds / Baths / SqFt / Days on Market
- CTA: "Schedule Your Private Showing Today!"

### 6. Price Bands (`social-price-bands.html`)

**Content:**
- Total Listings & Median Price summary
- Top 3 price bands with visual bars
- Percentage distribution
- Median price and DOM per band

---

## Data Flow

### Social Template Builder (`lib/social-templates.ts`)

Each builder function:

1. **Extracts data** from `result_json` (same as PDF)
2. **Formats values** for compact display:
   - `$1,234,567` → `$1.2M`
   - `$567,000` → `$567K`
3. **Injects branding** via `injectBrand()`:
   - CSS color overrides
   - Logo URLs
   - Contact info
   - Conditional rendering for optional fields
4. **Returns complete HTML** ready for rendering

### Example: Market Snapshot

```typescript
export function buildSocialMarketSnapshotHtml(
  templateHtml: string,
  data: any
): string {
  const r = data.result_json || data;
  const metrics = r.metrics || {};
  const counts = r.counts || {};

  const replacements = {
    "{{market_name}}": r.city || "Market",
    "{{median_price}}": formatCurrency(metrics.median_close_price),
    "{{closed_sales}}": formatNumber(counts.Closed),
    "{{avg_dom}}": formatNumber(metrics.avg_dom),
    "{{moi}}": formatDecimal(moi),
    "{{close_to_list_ratio}}": formatPercent(closeToListRatio),
    // ...
  };

  // Apply replacements and inject branding
  return injectBrand(html, data.brand);
}
```

---

## UI Integration

### Reports Page (`/app/reports`)

The Share button appears in the Files column for completed reports:

```tsx
{r.status === "completed" && (
  <Tooltip>
    <TooltipTrigger asChild>
      <a href={`/social/${r.id}`} target="_blank">
        <Button variant="ghost" className="text-pink-600 hover:bg-pink-50">
          <Share2 className="w-4 h-4" />
        </Button>
      </a>
    </TooltipTrigger>
    <TooltipContent>
      <p>Share on Social Media</p>
      <p className="text-xs text-muted-foreground">1080x1920 for Stories</p>
    </TooltipContent>
  </Tooltip>
)}
```

**Button Design:**
- Pink color (`text-pink-600`) to differentiate from other actions
- Tooltip explains the format
- Opens in new tab for easy screenshot/save

---

## PDFShift JPEG Conversion (Optional)

For automated JPEG generation, the worker includes `social_engine.py`:

```python
from .social_engine import render_social_image

jpg_path, social_url = render_social_image(
    run_id="abc123",
    account_id="uuid",
    print_base="https://trendyreports.com"
)
```

**PDFShift Configuration:**
```python
payload = {
    "source": social_url,
    "format": "1080x1920",
    "quality": 90,
    "full_page": True,
    "delay": 3000,        # Wait for fonts/images
    "wait_for_network": True,
    "timeout": 60,
}
```

**Environment Variables:**
- `PDFSHIFT_API_KEY`: Required for JPEG conversion
- `PRINT_BASE`: Base URL for social pages

---

## CSS Variables

All templates use the same CSS variables as PDF templates for brand consistency:

```css
:root {
  --pct-blue: #7C3AED;    /* Primary color */
  --pct-accent: #F26B2B;  /* Accent color */
  --ink: #0f172a;         /* Text color */
  --muted: #64748b;       /* Secondary text */
  --light-gray: #f8fafc;  /* Background */
  --border: #e2e8f0;      /* Border color */
}
```

These are overridden by the user's branding colors via `injectBrand()`.

---

## Future Enhancements

1. **Pre-generated JPEGs**: Generate social image at report creation time, store in R2
2. **Multiple sizes**: Add 1200x630 for Facebook/LinkedIn feed posts
3. **Direct sharing**: Integrate Web Share API for mobile one-tap sharing
4. **Custom text overlays**: Allow users to add custom captions
5. **Video export**: Animate metrics for Instagram Reels / TikTok

---

## Related Documentation

- [PDF_REPORTS.md](./PDF_REPORTS.md) - PDF generation system
- [BRANDING.md](./BRANDING.md) - White-label branding configuration
- [EMAIL_SYSTEM.md](./EMAIL_SYSTEM.md) - Email delivery with branding
