# TrendyReports PDF Report System

> Technical documentation for PDF report generation, templates, and white-label branding.

**Last Updated:** December 16, 2025

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
| Branding Preview | `apps/web/app/branding-preview/[reportType]/page.tsx` | Sample PDF preview |

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

### 2.2 PDFShift Configuration

```python
base_payload = {
    "sandbox": False,
    "use_print": True,
    "format": "Letter",
    "margin": {
        "top": "0",      # ZERO - CSS handles margins
        "right": "0",
        "bottom": "0",
        "left": "0"
    },
    "remove_blank": True,  # Remove blank trailing pages
}
```

#### PDFShift “page readiness” settings (recommended defaults)

When rendering from a URL (`source: https://.../print/<runId>`), PDFShift runs a Chromium instance remotely. Some pages (especially listing galleries) require extra time for images/layout to settle.

**Important mental model:** seeing images in the HTML preview does *not* guarantee they will render in PDFShift. The preview runs in the user’s browser (their IP, cookies/session, network), while PDFShift renders from its own cloud. MLS/CDN hosts may block PDFShift (hotlink protection, referrer checks, IP restrictions, auth/cookies).

We use these options to improve reliability:

- **`delay`**: wait a fixed time before capture (max 10s)
- **`wait_for_network`**: wait until there are no network requests for 500ms
- **`ignore_long_polling`**: do not wait for long-polling/websocket-style requests (prevents “never idle” pages)
- **`lazy_load_images`**: scroll to trigger lazy-loaded images
- **`timeout`**: allow the page to keep loading before PDFShift forcibly proceeds (seconds)

See PDFShift API parameter docs (same parameters apply across convert endpoints): `https://docs.pdfshift.io/api-reference/convert-to-jpeg#convert-to-jpeg`

### 2.3 Generation Process

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
| **V2.3** | Dec 16, 2025 | **PDFShift reliability** - avoid conversion failures due to image loading; gallery photos render as CSS `background-image` with graceful placeholder |
| **V2.2** | Dec 16, 2025 | **Refinements** - Increased header height (90px), centered metric text, larger logos (52px) |
| V2.1 | Dec 15, 2025 | **All templates hero headers** - uniform hero header across all report types |
| V2 | Dec 11, 2025 | **Hero Header Revamp** - full-bleed gradient banner (Market Snapshot) |
| V1 | Nov 2024 | Initial template with ribbon metrics |

### 3.2 Hero Header (All Templates - V2.2)

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

### 3.3 Hero Header Structure

```
┌─────────────────────────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ HERO HEADER (90px) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
│▓  [Logo 52px]  Brand Name (16px)            [PDF] ▓▓▓▓▓▓▓▓▓│
│▓               Report Type (13px)     [Affiliate Name] ▓▓▓▓│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
├─────────────────────────────────────────────────────────────┤
│ Market Snapshot — {{market_name}}                           │
│ Period: Last 30 days • Source: Live MLS Data • Dec 16       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  (Rest of report content - metrics, tables, etc.)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Header Elements (V2.2)

| Element | CSS Class | Description | Size |
|---------|-----------|-------------|------|
| Hero Header | `.hero-header` | Full-width gradient band | `min-height: 90px`, `padding: 24px 28px` |
| Logo | `.hero-logo` | Brand logo on left | `height: 52px`, `max-width: 140px` |
| Brand Name | `.hero-brand-name` | White text | `font-size: 16px` |
| Report Type | `.hero-report-type` | Report label | `font-size: 13px` |
| PDF Badge | `.pdf-badge` | Red badge top-right | `9px bold` |
| Affiliate Pill | `.affiliate-pill` | Semi-transparent pill | `max-width: 180px` |
| Title Bar | `.title-bar` | White area below hero | H1 + subline |

### 3.4 Content Sections

| Section | Description |
|---------|-------------|
| **Hero Ribbon** | 4-metric gradient bar (centered text) |
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

### 4.3 Branding Preview

The sample PDF generator in affiliate branding uses a dedicated preview page:

**File:** `apps/web/app/branding-preview/[reportType]/page.tsx`

This page mirrors the PDF templates exactly and is used for:
- Sample PDF downloads in the branding dashboard
- Testing branding changes before applying to real reports

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

### 6.3 Hero Header CSS (V2.2)

```css
.hero-header {
  background: linear-gradient(90deg, var(--pct-blue), var(--pct-accent));
  margin: calc(var(--page-padding) * -1);
  margin-bottom: 0;
  padding: 24px 28px;           /* Increased from 16px 20px */
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 90px;             /* Increased from 70px */
}

.hero-logo {
  height: 52px;                 /* Increased from 44px */
  width: auto;
  max-width: 140px;             /* Increased from 100px */
  object-fit: contain;
}

.hero-brand-name {
  font-size: 16px;              /* Increased from 15px */
  font-weight: 600;
}

.hero-report-type {
  font-size: 13px;              /* Increased from 12px */
  font-weight: 500;
}
```

### 6.4 Centered Metric Cards

```css
.ribbon .kpi .item {
  min-width: 120px;
  text-align: center;           /* V2.2: Centered text */
}

.ribbon .kpi .lbl {
  text-align: center;
}

.ribbon .kpi .val {
  text-align: center;
}
```

### 6.5 Key Classes

| Class | Purpose |
|-------|---------|
| `.page` | Main page container (exact letter size) |
| `.page-content` | Flex container for content flow |
| `.page-footer` | Footer container with `margin-top: auto` |
| `.hero-header` | Full-bleed gradient header (90px) |
| `.ribbon` | Gradient metric bar (centered text) |
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

### 7.2 Page Container (Blank Page Prevention)

```css
.page {
  width: var(--page-width);
  min-height: var(--page-height);
  max-height: var(--page-height);
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  overflow: hidden;               /* CRITICAL: Clip overflow */
  page-break-after: avoid;        /* Prevent blank pages */
  page-break-inside: avoid;
}
```

### 7.3 Print Media Query

```css
@media print {
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    background: white !important;
  }
  
  .page {
    box-shadow: none !important;
    margin: 0 !important;
    overflow: hidden !important;
    page-break-after: avoid !important;
  }
  
  .hero-header {
    min-height: 90px !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  
  /* Hide watermark in print */
  .sample-watermark {
    display: none !important;
  }
}
```

### 7.4 Avoiding Page Breaks

```css
.avoid-break {
  break-inside: avoid;
  page-break-inside: avoid;
}
```

### 7.5 PDFShift Settings for Single Page

The PDF engine is configured to prevent blank pages:

```python
base_payload = {
    "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
    "remove_blank": True,  # Remove blank trailing pages
}
```

### 7.6 PDFShift Image Loading (Why preview works but PDF breaks)

It’s common for listing photos to **show in the browser preview** but **fail in PDFShift**. The reason is simple:

- **Preview** runs in *your browser*, with your network, cookies, IP, and a normal user-agent.
- **PDFShift** runs in *PDFShift’s cloud*, which may be blocked by MLS/CDN hotlinking rules, referrer checks, IP allowlists/denylists, or slow image hosts.

#### What to avoid

- **Hard “wait until all images load”** (`wait_for` + custom JS) can cause the entire conversion to fail if even 1 image never loads. Per PDFShift docs, `wait_for` will fail the conversion if the function never returns truthy within its allowed window. See: `https://docs.pdfshift.io/api-reference/convert-to-jpeg#convert-to-jpeg`

#### What we do instead (current approach)

- **Don’t hard-fail conversions on image load**
  - Use `delay`, `wait_for_network`, `lazy_load_images`, and `timeout` to give the page a fair chance to load.
  - Use `ignore_long_polling` to prevent “network never goes idle” situations.
  - **Note:** PDFShift plan limits can cap `timeout` (we observed a hard cap of **100 seconds** returning a 400 when exceeded).
- **Avoid broken-image icons in PDFs**
  - For gallery cards, render photos as **CSS `background-image`** on `.photo-container` with a visible “No Image” placeholder behind it.
  - If the image is blocked/unreachable, the PDF still looks clean (no broken `<img>` icon).

#### Long-term “perfect photos” solution (when needed)

If we need MLS photos to *always* appear in PDFs, we must serve them from a URL we control:

- **Proxy/cache images** on our backend (download, store, and serve from R2 / our domain)
- Optionally **embed as base64** (larger HTML/PDF, but self-contained)

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `apps/web/templates/trendy-*.html` | PDF template files (7 templates) |
| `apps/web/app/branding-preview/[reportType]/page.tsx` | Sample PDF preview |
| `apps/worker/src/worker/pdf_engine.py` | PDF generation engine |
| `apps/web/app/print/[runId]/page.tsx` | Print page route |
| `apps/web/lib/templates.ts` | Template loading utilities |

### Template Dimensions (V2.2)

| Element | Size |
|---------|------|
| Hero Header Height | `90px` |
| Hero Padding | `24px 28px` |
| Logo Height | `52px` |
| Logo Max Width | `140px` |
| Brand Name Font | `16px` |
| Report Type Font | `13px` |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PDF_ENGINE` | `playwright` or `pdfshift` |
| `PDFSHIFT_API_KEY` | PDFShift API key |
| `PRINT_BASE` | Base URL for print pages |
| `R2_*` | Cloudflare R2 credentials |

---

*This document is the source of truth for TrendyReports PDF report generation.*
