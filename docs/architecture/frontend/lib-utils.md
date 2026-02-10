# Utility Libraries

## `lib/utils.ts` -- Class Name Helper

Single utility: `cn()` -- merges Tailwind CSS classes using `clsx` + `tailwind-merge`.

```typescript
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

Used everywhere in components for conditional class names.

## `lib/templates.ts` -- Report Template Builders

Server-side HTML template builders for PDF/print report generation. Each function takes template HTML + report data and returns the final rendered HTML.

### Exported Functions

| Function | Report Type |
|----------|-------------|
| `buildMarketSnapshotHtml()` | Market Snapshot |
| `buildNewListingsHtml()` | New Listings (table, paginated) |
| `buildInventoryHtml()` | Inventory Report (paginated) |
| `buildClosedHtml()` | Closed Sales (paginated) |
| `buildPriceBandsHtml()` | Price Analysis |
| `buildNewListingsGalleryHtml()` | Photo Gallery (3x2 grid, paginated) |
| `buildFeaturedListingsHtml()` | Featured Listings (2x2 cards) |

### How They Work

1. Extract data from `result_json` (metrics, counts, listings)
2. Build replacement map for `{{placeholder}}` tokens
3. Replace all placeholders in the HTML template
4. Build paginated pages if needed (15 rows/page for tables, 6 cards/page for galleries)
5. Inject brand colors via `injectBrand()` (handles white-label branding)

### Security

All user-provided content is escaped via `escapeHtml()` to prevent XSS. URLs are sanitized via `sanitizeUrl()` (only `http://`, `https://`, `data:` allowed). Colors validated via regex.

### Branding (Phase 30)

`injectBrand()` handles:
- CSS color overrides (`--pct-blue`, `--pct-accent`)
- Brand name, logo, footer logo, rep photo
- Contact lines, website URL
- Handlebars-style conditionals (`{{#if logo_url}}...{{/if}}`)
- Cleanup of unmatched template tags

## `lib/social-templates.ts` -- Social Media Template Builders

1080x1920 HTML template builders for social media images (Instagram Stories, TikTok).

### Exported Functions

| Function | Template |
|----------|----------|
| `buildSocialMarketSnapshotHtml()` | Market Snapshot social |
| `buildSocialNewListingsHtml()` | New Listings social |
| `buildSocialClosedHtml()` | Closed Sales social |
| `buildSocialInventoryHtml()` | Inventory social |
| `buildSocialGalleryHtml()` | Gallery/Featured social (uses first listing as hero) |
| `buildSocialPriceBandsHtml()` | Price Bands social (top 3 bands) |

Same pattern: placeholder replacement + brand injection + XSS protection.

## `lib/wizard-types.ts` -- Property Wizard Types

Type definitions and constants for the property report wizard. See [components-property-wizard.md](./components-property-wizard.md).

## `lib/sample-report-data.ts` -- Sample Data

Sample report data for previews and demos. Used by the report builder preview and branding preview pages.

## `lib/property-report-assets.ts` -- Property Report Assets

R2-hosted asset manifest for property report themes. Includes:
- `THEMES` - 5 theme configurations with colors, fonts, page layouts
- `getThemeCoverUrl()`, `getPagePreviewUrl()` - Preview image URLs
- `FONTS` - Font file URLs (Bariol, Nexa, Montserrat)
- `ICONS` - Icon image URLs

Base URL: `NEXT_PUBLIC_ASSETS_URL` or `https://assets.trendyreports.com`

## Key Files

- `apps/web/lib/utils.ts` - cn() helper
- `apps/web/lib/templates.ts` - PDF template builders (~1200 lines)
- `apps/web/lib/social-templates.ts` - Social media template builders (~430 lines)
- `apps/web/lib/wizard-types.ts` - Property wizard types (~225 lines)
- `apps/web/lib/sample-report-data.ts` - Sample data for previews
- `apps/web/lib/property-report-assets.ts` - R2 asset manifest (~260 lines)
