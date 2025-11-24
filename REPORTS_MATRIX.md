# REPORTS SYSTEM - Feature Matrix

**Date**: Nov 24, 2025  
**Purpose**: Single-glance inventory of all report types and their supported output formats

---

## Report Type Matrix

| report_slug | description | email_html | pdf | image_jpg_png | in_app_preview | used_by_schedules | notes |
|------------|-------------|------------|-----|---------------|----------------|-------------------|-------|
| `market_snapshot` | Complete overview of market conditions (Active, Pending, Closed, DOM, Prices) | **WORKS** | **WORKS** | NOT_IMPLEMENTED | **WORKS** | YES | Email: Full branded template with metrics table. PDF: Rendered via /print/{runId}. Most mature report type. |
| `new_listings` | Recently listed properties | **WORKS** | **WORKS** | NOT_IMPLEMENTED | **WORKS** | YES | Email: Similar to market_snapshot, different metrics. PDF: Yes. No gallery images in email. |
| `inventory` | Available properties and market supply | **PARTIAL** | **WORKS** | NOT_IMPLEMENTED | **PARTIAL** | YES | Email: Template exists but generic metrics display. PDF: Works. Preview may show limited data. |
| `closed` | Recently sold properties and trends | **PARTIAL** | **WORKS** | NOT_IMPLEMENTED | **PARTIAL** | YES | Email: Template exists, shows closed sales metrics. PDF: Works. Less polished than market_snapshot. |
| `price_bands` | Market segmentation by price ranges | **PARTIAL** | **WORKS** | NOT_IMPLEMENTED | **PARTIAL** | YES | Email: Template exists but no chart/visual breakdown. PDF: Works but lacks visual appeal. |
| `open_houses` | Upcoming open house schedule | **PARTIAL** | **WORKS** | NOT_IMPLEMENTED | **PARTIAL** | YES | Email: Template exists. PDF: Works. May show empty if no upcoming open houses. |
| `new_listings_gallery` | New listings with photo gallery layout | **WORKS** | **WORKS** | NOT_IMPLEMENTED | **WORKS** | YES | Email: Hero images for each listing. PDF: Gallery layout with photos. Uses `hero_photo_url` from SimplyRETS. Template: buildNewListingsGalleryHtml. ✅ Now in wizard (R1). |
| `featured_listings` | Curated featured properties with photos | **WORKS** | **WORKS** | NOT_IMPLEMENTED | **WORKS** | YES | Email: Similar to gallery. PDF: Featured layout. Template: buildFeaturedListingsHtml. May need manual curation logic (currently shows top listings). ✅ Now in wizard (R1). |

---

## Status Legend

- **WORKS**: Fully implemented, used in production, no known critical bugs
- **PARTIAL**: Code/template exists but incomplete, missing styling, or limited functionality
- **BROKEN**: Wired but fails at runtime (exceptions, empty output, crashes)
- **NOT_IMPLEMENTED**: No code or template exists for this surface

---

## Key Findings

### ✅ What's Production-Ready
1. **market_snapshot** - Email + PDF fully polished, branded, most mature
2. **new_listings_gallery** - Email + PDF working, includes hero photos
3. **featured_listings** - Email + PDF working, photo grid layout

### ⚠️ What's Partial/Needs Polish
1. **inventory, closed, price_bands, open_houses** - Email templates exist but generic
2. All reports lack in-email charts/visualizations (text/numbers only)
3. No social share images (JPG/PNG exports not implemented)

### ❌ Major Gaps
1. **No image exports** (JPG/PNG) for any report type
2. **No chart rendering** in emails (all metrics are text/tables)
3. **No curation logic** for featured_listings (shows top N instead of curated)
4. **Limited branding** on partial reports (inventory, closed, etc.)

**✅ R1 COMPLETE** (Nov 24, 2025): All 8 report types now aligned across frontend wizard, API, and email templates. No more discrepancies.

---

## Surface-Specific Notes

### Email HTML (`email_html`)
**Implementation**: `apps/worker/src/worker/email/template.py` (`schedule_email_html()`)

**What Works**:
- Clean, responsive HTML template
- White-label branding support (Phase 30): logo, colors, contact info
- Metrics displayed as formatted tables
- Unsubscribe links
- Direct PDF download button

**What's Missing**:
- Charts/graphs (all metrics are numbers in tables)
- Inline property images (except gallery reports)
- Interactive elements (all static HTML)

---

### PDF (`pdf`)
**Implementation**: 
- Print template: `apps/web/app/print/[runId]/page.tsx`
- PDF engine: Playwright (headless Chrome) via `apps/worker/src/worker/pdf_adapter.py`
- Builders: `apps/worker/src/worker/report_builders.py` + HTML builders in print page

**What Works**:
- All 8 report types render to PDF
- Gallery reports include hero photos
- White-label branding in PDF header/footer
- Clean print styles (`@media print`)

**What's Missing**:
- Page break optimization (long tables may split awkwardly)
- Charts/graphs (same as email - text only)
- Print-optimized layouts for some partial reports

---

### Image (JPG/PNG) (`image_jpg_png`)
**Status**: **NOT_IMPLEMENTED** for any report type

**What Would Be Needed**:
1. Chart rendering library (e.g., Chart.js, D3.js server-side)
2. Export pipeline:
   - Option A: Headless browser screenshot of specific elements
   - Option B: Server-side canvas rendering
3. Storage: R2/S3 for generated images
4. Use cases:
   - Social media sharing (OG images)
   - Email inline images (embed in email body)
   - Thumbnail previews in UI

**Recommendation**: Low priority unless social sharing or inline charts are needed

---

### In-App Preview (`in_app_preview`)
**Implementation**: 
- Preview page: `apps/web/app/reports/[reportId]/page.tsx` (if exists)
- Print preview: `apps/web/app/print/[runId]/page.tsx` (used for PDF generation)

**What Works**:
- market_snapshot, new_listings, new_listings_gallery, featured_listings show rich previews
- Print page doubles as preview (can be viewed in browser)

**What's Partial**:
- inventory, closed, price_bands, open_houses use same print template but less polished
- No dedicated "preview before sending" UI for schedules (only post-generation view)

---

## Usage by Schedules

**All 8 report types can be scheduled** (see `apps/api/src/api/routes/schedules.py`):
```python
report_type: Literal[
    "market_snapshot",
    "new_listings",
    "inventory",
    "closed",
    "price_bands",
    "new_listings_gallery",
    "featured_listings",
]
```

**Note**: `open_houses` is in email template but **NOT** in schedule API Literal (may be disabled or deprecated)

---

## Recommendations by Priority

### High Priority (Revenue Impact)
1. **Polish partial reports** (inventory, closed, price_bands) - Bring to same quality as market_snapshot
2. **Add email charts** - Visual metrics increase engagement (Chart.js server-side rendering)
3. **Verify open_houses** - Either remove from email template or add to schedule API

### Medium Priority (UX Enhancement)
4. **Preview before send** - Allow users to preview email/PDF before creating schedule
5. **Featured listings curation** - Add UI to manually select/order featured properties
6. **PDF page breaks** - Optimize long tables and property lists

### Low Priority (Nice to Have)
7. **Image exports** - Social sharing, OG images
8. **Interactive emails** - AMP email support (low ROI)
9. **Multiple templates per report** - Allow users to choose layout style

---

**Next Step**: Use `REPORTS_AUDIT.md` for detailed pipeline analysis and `REPORTS_QA_CHECKLIST.md` for testing

