# TrendyReports PDF Report System

> Technical documentation for PDF report generation, templates, and white-label branding.

**Last Updated:** December 15, 2025

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [PDF Generation Pipeline](#2-pdf-generation-pipeline)
3. [Report Templates](#3-report-templates)
4. [White-Label Branding](#4-white-label-branding)
5. [Template Variables](#5-template-variables)
6. [Styling Guidelines](#6-styling-guidelines)
7. [Print Optimization](#7-print-optimization)

---

## 1. Architecture Overview

PDF reports are generated from HTML templates, rendered via headless browser or cloud API.

### Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     PDF Generation Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Worker     │────▶│  HTML Render │────▶│ PDF Engine   │     │
│  │   (task)     │     │  (Next.js)   │     │              │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │  SimplyRETS  │     │   Template   │     │  Playwright  │     │
│  │  (MLS data)  │     │   (HTML)     │     │  or PDFShift │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                                                   │              │
│                                                   ▼              │
│                                            ┌──────────────┐     │
│                                            │ Cloudflare   │     │
│                                            │     R2       │     │
│                                            └──────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| PDF Engine | `apps/worker/src/worker/pdf_engine.py` | Playwright or PDFShift rendering |
| Print Page | `apps/web/app/print/[runId]/page.tsx` | Server-side HTML generation |
| Templates | `apps/web/templates/*.html` | HTML template files |
| Template Lib | `apps/web/lib/templates.ts` | Template loading and variable injection |

---

## 2. PDF Generation Pipeline

### 2.1 Engines

TrendyReports supports two PDF engines:

| Engine | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Playwright** | Development, self-hosted | Free, precise | Requires Chromium |
| **PDFShift** | Production cloud | No dependencies | API costs |

```python
# Environment variable controls engine
PDF_ENGINE = os.getenv("PDF_ENGINE", "playwright")  # or "pdfshift"
```

### 2.2 Generation Process

1. **Worker receives job** with `run_id`, `account_id`, `report_type`, `params`
2. **Fetch MLS data** from SimplyRETS API
3. **Calculate metrics** (median prices, DOM, MOI, etc.)
4. **Build print URL** → `{PRINT_BASE}/print/{run_id}`
5. **Render PDF** via Playwright or PDFShift
6. **Upload to R2** and return presigned URL
7. **Send email** with PDF link (if scheduled)

---

## 3. Report Templates

### 3.1 Template Version History

| Version | Date | Changes |
|---------|------|---------|
| **V2.1** | Dec 15, 2025 | **All templates hero headers** - uniform hero header across all report types |
| V2 | Dec 11, 2025 | **Hero Header Revamp** - full-bleed gradient banner (Market Snapshot) |
| V1 | Nov 2024 | Initial template with ribbon metrics |

### 3.2 Hero Header (All Templates - V2.1)

All PDF templates now share a consistent hero header structure:

| Template | Hero Header |
|----------|:-----------:|
| `trendy-market-snapshot.html` | ✅ |
| `trendy-new-listings.html` | ✅ |
| `trendy-closed.html` | ✅ |
| `trendy-inventory.html` | ✅ |
| `trendy-price-bands.html` | ✅ |
| `trendy-featured-listings.html` | ✅ |
| `trendy-new-listings-gallery.html` | ✅ |

### 3.3 Market Snapshot Template

**File:** `apps/web/templates/trendy-market-snapshot.html`

#### Hero Header Structure (shared across all templates)

```
┌─────────────────────────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ HERO HEADER ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
│▓  [Logo]  Brand Name                        [PDF] ▓▓▓▓▓▓▓▓│
│▓          Market Snapshot            [Affiliate Name] ▓▓▓▓│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
├─────────────────────────────────────────────────────────────┤
│ Market Snapshot — {{market_name}}                           │
│ Period: Last 30 days • Source: Live MLS Data • Dec 11       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  (Rest of report content - metrics, tables, etc.)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Header Elements

| Element | CSS Class | Description |
|---------|-----------|-------------|
| Hero Header | `.hero-header` | Full-width gradient band (primary → accent) |
| Logo | `.hero-logo` | Brand logo on left (max 120px height) |
| Brand Name | `.hero-brand-name` | White text, 16px |
| Report Type | `.hero-report-type` | "Market Snapshot" label |
| PDF Badge | `.pdf-badge` | Red badge top-right |
| Affiliate Pill | `.affiliate-pill` | Semi-transparent pill with account name |
| Title Bar | `.title-bar` | White area below hero with H1 + subline |

#### Content Sections

| Section | Description |
|---------|-------------|
| **Hero Ribbon** | 4-metric gradient bar (Median, Closed, DOM, MOI) |
| **Core Indicators** | 3-card section (New Listings, Pending, Sale-to-List) |
| **By Property Type** | Table with SFR, Condo, Townhome breakdown |
| **By Price Tier** | Table with Entry, Move-Up, Luxury tiers |
| **Branded Footer** | Rep photo + contact + logo |
| **Gray Footer** | Generated by / data source line |

---

## 4. White-Label Branding

### 4.1 Brand Variables

Templates receive these brand variables:

| Variable | Source | Fallback |
|----------|--------|----------|
| `{{brand_name}}` | `affiliate_branding.brand_display_name` | "TrendyReports" |
| `{{logo_url}}` | `affiliate_branding.logo_url` | None (text fallback) |
| `{{brand_badge}}` | Account name or brand display name | "TrendyReports" |
| `{{pct-blue}}` | `affiliate_branding.primary_color` | `#7C3AED` |
| `{{pct-accent}}` | `affiliate_branding.accent_color` | `#F26B2B` |

### 4.2 Footer Branding

| Variable | Description |
|----------|-------------|
| `{{rep_photo_url}}` | Circular headshot (52px) |
| `{{contact_line1}}` | Name or title |
| `{{contact_line2}}` | Phone/email |
| `{{website_url}}` | Company website |

---

## 5. Template Variables

### 5.1 Market Snapshot Variables

| Variable | Type | Description |
|----------|------|-------------|
| `{{market_name}}` | string | City or ZIP area name |
| `{{period_label}}` | string | "Last 30 Days" |
| `{{lookback_days}}` | int | Number of days (30, 60, 90) |
| `{{report_date}}` | string | Report generation date |
| `{{median_price}}` | string | Formatted median close price |
| `{{closed_sales}}` | int | Total closed transactions |
| `{{avg_dom}}` | int | Average days on market |
| `{{moi}}` | float | Months of inventory |
| `{{new_listings}}` | int | New listings count |
| `{{pendings}}` | int | Pending sales count |
| `{{close_to_list_ratio}}` | float | Sale-to-list percentage |

### 5.2 Property Type Variables

| Variable | Description |
|----------|-------------|
| `{{sfr_median}}`, `{{sfr_closed}}`, `{{sfr_dom}}` | Single Family stats |
| `{{condo_median}}`, `{{condo_closed}}`, `{{condo_dom}}` | Condo stats |
| `{{th_median}}`, `{{th_closed}}`, `{{th_dom}}` | Townhome stats |

### 5.3 Price Tier Variables

| Variable | Description |
|----------|-------------|
| `{{tier1_median}}`, `{{tier1_closed}}`, `{{tier1_moi}}` | Entry tier |
| `{{tier2_median}}`, `{{tier2_closed}}`, `{{tier2_moi}}` | Move-Up tier |
| `{{tier3_median}}`, `{{tier3_closed}}`, `{{tier3_moi}}` | Luxury tier |

---

## 6. Styling Guidelines

### 6.1 CSS Variables

```css
:root {
  --pct-blue: #7C3AED;      /* Primary (overridden by brand) */
  --pct-accent: #F26B2B;    /* Accent (overridden by brand) */
  --pct-gray: rgb(247,249,252);
  --ink: #0f172a;
  --muted: #6b7280;
  --border: #e5e7eb;
  --success: #16a34a;
  --danger: #dc2626;
}
```

### 6.2 Layout Constants

```css
:root {
  --page-width: 8.5in;      /* US Letter */
  --page-height: 11in;
  --page-padding: 0.25in;
}
```

### 6.3 Key Classes

| Class | Purpose |
|-------|---------|
| `.page` | Main page container (exact letter size) |
| `.page-content` | Flex container for content flow |
| `.hero-header` | Full-bleed gradient header |
| `.ribbon` | Gradient metric bar |
| `.card` | White card with border |
| `.mini` | Small stat box |
| `.avoid-break` | Prevent page breaks within element |

---

## 7. Print Optimization

### 7.1 @page Rules

```css
@page {
  size: letter;
  margin: 0;  /* Handled by .page padding */
}
```

### 7.2 Print Adjustments

The template includes `@media print` rules that:
- Reduce spacing to fit content on one page
- Remove box shadows
- Ensure colors print correctly (`print-color-adjust: exact`)
- Hide non-print elements (`.no-print`)

### 7.3 Avoiding Page Breaks

```css
.avoid-break {
  break-inside: avoid;
  page-break-inside: avoid;
}
```

### 7.4 Content Overflow

```css
.page {
  overflow: hidden;  /* Clip overflow to prevent blank pages */
}
```

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `apps/web/templates/trendy-market-snapshot.html` | Market Snapshot PDF template |
| `apps/worker/src/worker/pdf_engine.py` | PDF generation engine |
| `apps/web/app/print/[runId]/page.tsx` | Print page route |
| `apps/web/lib/templates.ts` | Template loading utilities |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PDF_ENGINE` | `playwright` or `pdfshift` |
| `PDFSHIFT_API_KEY` | PDFShift API key |
| `PRINT_BASE` | Base URL for print pages |
| `R2_*` | Cloudflare R2 credentials |

---

*This document is the source of truth for TrendyReports PDF report generation.*

