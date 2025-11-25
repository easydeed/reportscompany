# Affiliate Branding System Analysis

**Date**: November 25, 2025  
**Status**: Gap Analysis & Improvement Roadmap

---

## Executive Summary

The current branding system allows affiliates to customize their white-label appearance on reports and emails. However, there are significant gaps between what's implemented and what affiliates need for a professional, complete white-label experience.

### What Works ✅
- Basic brand customization (name, colors, contact info)
- Simple live previews (email header, PDF cover)
- Branding applied to PDF reports and emails

### What's Missing ❌
- **No template previews** - Cannot see how branding looks on actual report types
- **No logo upload** - Only URL input (requires external hosting)
- **No headshot/rep photo upload** - URL input only
- **No downloadable assets** - Cannot export branded materials
- **No email template preview** - Only a tiny header snippet
- **No PDF template preview** - Only a minimal cover preview

---

## Current Implementation Details

### 1. Branding Data Model (`affiliate_branding` table)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `brand_display_name` | text | Company name shown on reports | ✅ Working |
| `logo_url` | text | URL to logo image | ⚠️ URL only, no upload |
| `primary_color` | text | Hex color for headers/ribbons | ✅ Working |
| `accent_color` | text | Hex color for CTAs/highlights | ✅ Working |
| `rep_photo_url` | text | URL to headshot | ⚠️ URL only, no upload |
| `contact_line1` | text | Phone/name line | ✅ Working |
| `contact_line2` | text | Email/secondary info | ✅ Working |
| `website_url` | text | Affiliate website | ✅ Working |

### 2. Branding Form UI (`/app/branding`)

**Current Fields:**
- Brand Display Name (text input)
- Logo URL (text input - **no file upload**)
- Primary Color (color picker + hex input)
- Accent Color (color picker + hex input)
- Contact Line 1 (text input) - Affiliate only
- Contact Line 2 (text input) - Affiliate only
- Website URL (text input) - Affiliate only

**Current Previews:**
1. **Email Preview** - Tiny header snippet showing logo + name + contact
2. **PDF Cover Preview** - Minimal card showing logo + name + contact lines

### 3. How Branding is Applied to Reports

The `injectBrand()` function in `apps/web/lib/templates.ts`:

```typescript
function injectBrand(html: string, brand: any): string {
  // Injects CSS color variables
  // Replaces {{brand_name}}, {{brand_logo_url}}, {{brand_badge}}, {{brand_tagline}}
}
```

**Template Placeholders Used:**
- `{{brand_name}}` → Display name
- `{{brand_logo_url}}` → Logo URL
- `{{brand_badge}}` → "[Name] Insights"
- `{{brand_tagline}}` → "[Name] • Market Intelligence"

### 4. What Affiliates Cannot Do Currently

| Feature | Current State | Impact |
|---------|---------------|--------|
| Upload logo file | Must host elsewhere & paste URL | Friction, broken images |
| Upload headshot | Must host elsewhere & paste URL | Friction, not used in templates |
| See report preview with branding | Only tiny email/PDF snippets | Cannot verify appearance |
| Preview each report type | Not available | No confidence in output |
| Download branded templates | Not available | Cannot share samples |
| Preview email body | Only header shown | Cannot see full email |
| Test send branded email | Not available | Cannot verify delivery |

---

## Gap Analysis: What Affiliates Need

### Priority 1: File Upload for Logo & Headshot 🔴

**Problem**: Affiliates must host images externally (Dropbox, Google Drive, etc.) and paste URLs. This is:
- Confusing for non-technical users
- Prone to broken images (URL changes, permissions)
- No validation of image dimensions/quality

**Solution**:
```
1. Add file upload component to branding form
2. Upload to Cloudflare R2 (already used for PDFs)
3. Return permanent URL
4. Store URL in affiliate_branding table
```

**Implementation Effort**: Medium (2-3 days)

### Priority 2: Live Report Template Previews 🔴

**Problem**: The current previews are tiny snippets that don't show how branding actually appears on real reports.

**Current Preview:**
```
┌─────────────────────────────────────┐
│ [Logo] Brand Name                   │
│         Contact info                │
└─────────────────────────────────────┘
```

**What Affiliates Need:**
```
┌─────────────────────────────────────┐
│ Full Market Snapshot Preview        │
│ with actual header, ribbon, tables, │
│ footer - all using their branding   │
└─────────────────────────────────────┘
```

**Solution**:
```
1. Add "Preview Report" section with report type selector
2. Render actual report template with sample data + current branding
3. Show in iframe or modal
4. Allow switching between report types
```

**Implementation Effort**: Medium-High (3-5 days)

### Priority 3: Downloadable Branded Assets 🟡

**Problem**: Affiliates cannot download their branded materials to share with prospects or verify quality.

**Solution**:
```
1. "Download Sample PDF" button
2. Generates a Market Snapshot with sample data + their branding
3. Returns downloadable PDF file
```

**Implementation Effort**: Low (1-2 days)

### Priority 4: Full Email Preview 🟡

**Problem**: Current preview only shows the email header, not the full email body with report summary, CTA buttons, and footer.

**Solution**:
```
1. Add "Full Email Preview" tab/section
2. Render complete email template with sample data
3. Show desktop and mobile views
```

**Implementation Effort**: Medium (2-3 days)

### Priority 5: Headshot Integration 🟢

**Problem**: `rep_photo_url` field exists in the database but is not used in any templates.

**Current State**:
- Field exists in form
- Field saved to database
- **Not rendered anywhere in reports or emails**

**Solution**:
```
1. Add headshot to email template (optional)
2. Add headshot to PDF footer/header (optional)
3. Make it toggleable (some affiliates may not want personal photos)
```

**Implementation Effort**: Low (1 day)

---

## Recommended Roadmap

### Phase 1: Core Fixes (Week 1)
1. **Add file upload for logo** - Cloudflare R2 integration
2. **Add file upload for headshot** - Same infrastructure
3. **Integrate headshot into email template** - Optional display

### Phase 2: Preview Enhancements (Week 2)
4. **Add report type selector** - Dropdown with all 8 report types
5. **Live report preview** - Render actual template with sample data
6. **Full email preview** - Complete email body, not just header

### Phase 3: Download & Export (Week 3)
7. **"Download Sample PDF" button** - Generate branded sample
8. **"Send Test Email" button** - Send branded email to self
9. **Asset export** - Download logo/headshot in various sizes

---

## Technical Implementation Notes

### File Upload Architecture

```
Frontend (Branding Page)
    │
    ▼
POST /api/proxy/v1/upload/branding-asset
    │
    ▼
Backend (FastAPI)
    │
    ▼
Cloudflare R2 (or S3)
    │
    ▼
Return permanent URL
    │
    ▼
Store in affiliate_branding.logo_url
```

### Report Preview Architecture

```
Frontend (Branding Page)
    │
    ├── Select Report Type (dropdown)
    │
    ├── Current Branding State
    │
    ▼
Render Template Client-Side
    │
    ├── Load template HTML
    ├── Inject branding colors/name
    ├── Use sample data for metrics
    │
    ▼
Display in iframe/modal
```

### Sample Data for Previews

```typescript
const SAMPLE_REPORT_DATA = {
  city: "Beverly Hills",
  lookback_days: 30,
  metrics: {
    median_close_price: 2850000,
    avg_dom: 45,
    median_list_price: 2950000,
  },
  counts: {
    Active: 127,
    Pending: 34,
    Closed: 89,
  },
  // ... etc
};
```

---

## Current Code References

| Component | File | Purpose |
|-----------|------|---------|
| Branding Page | `apps/web/app/app/branding/page.tsx` | Form + previews |
| Branding API | `apps/api/src/api/routes/affiliates.py` | GET/POST branding |
| Brand Injection | `apps/web/lib/templates.ts` | Apply branding to HTML |
| DB Schema | `db/migrations/0008_create_affiliate_branding.sql` | Table definition |
| Branding Service | `apps/api/src/api/services/branding.py` | Brand resolution |

---

## Summary: What to Build Next

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 🔴 P1 | Logo file upload | 2-3 days | High |
| 🔴 P1 | Headshot file upload | 1 day | Medium |
| 🔴 P1 | Live report preview by type | 3-5 days | High |
| 🟡 P2 | Download sample PDF | 1-2 days | Medium |
| 🟡 P2 | Full email preview | 2-3 days | Medium |
| 🟢 P3 | Headshot in templates | 1 day | Low |
| 🟢 P3 | Test email send | 1 day | Low |

**Total Estimated Effort**: 2-3 weeks for complete branding overhaul

---

## Appendix: Current Branding Form Screenshot Reference

The current form shows:
- Text inputs for all fields
- Color pickers for primary/accent
- Two small preview cards (Email Header, PDF Cover)
- No file upload capability
- No full template preview
- No download functionality

