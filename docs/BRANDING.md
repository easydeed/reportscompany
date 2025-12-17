# TrendyReports Branding System

> Complete documentation for the white-label branding system, including logo management, color customization, and contact information.

**Last Updated:** December 17, 2025

---

## Table of Contents

1. [Overview](#1-overview)
2. [User Types & Branding Sources](#2-user-types--branding-sources)
3. [Branding Page](#3-branding-page)
4. [Logo Management](#4-logo-management)
5. [Color System](#5-color-system)
6. [Contact Information](#6-contact-information)
7. [Headshot Handling (Option A)](#7-headshot-handling-option-a)
8. [Database Schema](#8-database-schema)
9. [API Endpoints](#9-api-endpoints)
10. [Preview & Testing](#10-preview--testing)

---

## 1. Overview

TrendyReports supports full white-label branding for PDF reports and email communications. The branding system allows customization of:

- **Logos**: Header and footer logos for both PDFs and emails
- **Colors**: Primary and accent colors for gradients and accents
- **Contact Info**: Representative photo, name, title, phone, email, website
- **Brand Name**: Display name shown on reports

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Unified UI** | All user types see the same branding interface |
| **Option A Headshots** | Regular users use their profile avatar; affiliates upload a rep photo |
| **Consistent Layout** | All app pages use `space-y-6` for uniform spacing |
| **Low Cognitive Load** | Clear sections, helpful tips, live preview |

---

## 2. User Types & Branding Sources

Branding is resolved differently based on user type:

| User Type | Branding Source | Headshot Source | Can Edit |
|-----------|-----------------|-----------------|----------|
| **Regular Agent** | `accounts` table | `users.avatar_url` | ✅ |
| **Sponsored Agent** | Sponsor's `affiliate_branding` | Sponsor's `rep_photo_url` | ❌ (inherits) |
| **Affiliate** | `affiliate_branding` table | `rep_photo_url` | ✅ |

### Brand Resolution Logic

**File:** `apps/api/src/api/services/branding.py`

```python
def get_brand_for_account(cur, account_id: str) -> Brand:
    """
    1. Sponsored REGULAR → Sponsor's affiliate_branding
    2. INDUSTRY_AFFILIATE → Own affiliate_branding
    3. Un-sponsored REGULAR → accounts table + users.avatar_url
    4. Fallback → TrendyReports defaults
    """
```

---

## 3. Branding Page

**Location:** `/app/branding`

The unified branding page is accessible to all user types and provides:

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Brand Studio                          [Save Changes]│
├─────────────────────────────────────────────────────────────┤
│ Color Preview Bar (live gradient)                           │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐ ┌─────────────────────────┐ │
│ │ LEFT COLUMN (2/3)           │ │ RIGHT COLUMN (1/3)      │ │
│ │                             │ │                         │ │
│ │ • Brand Identity            │ │ Live Preview            │ │
│ │   - Company Name            │ │ - PDF Header/Footer     │ │
│ │   - Primary Color           │ │ - Email Header/Footer   │ │
│ │   - Accent Color            │ │                         │ │
│ │                             │ │ Tips                    │ │
│ │ • PDF Logos                 │ │                         │ │
│ │   - Header Logo             │ │                         │ │
│ │   - Footer Logo             │ │                         │ │
│ │                             │ │                         │ │
│ │ • Email Logos               │ │                         │ │
│ │   - Header Logo             │ │                         │ │
│ │   - Footer Logo             │ │                         │ │
│ │                             │ │                         │ │
│ │ • Contact Information       │ │                         │ │
│ │   - Photo (see Option A)    │ │                         │ │
│ │   - Name, Title             │ │                         │ │
│ │   - Email, Phone            │ │                         │ │
│ │   - Website                 │ │                         │ │
│ │                             │ │                         │ │
│ │ • Test Section              │ │                         │ │
│ │   - Download Sample PDF     │ │                         │ │
│ │   - Send Test Email         │ │                         │ │
│ └─────────────────────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `apps/web/app/app/branding/page.tsx` | Unified branding page (all users) |
| `apps/web/app/app/affiliate/branding/page.tsx` | Redirects to `/app/branding` |

---

## 4. Logo Management

### Logo Types

| Logo | Purpose | Background | Recommendation |
|------|---------|------------|----------------|
| **PDF Header Logo** | Report header gradient | Dark (primary→accent) | Light/white logo |
| **PDF Footer Logo** | Report footer | Light gray | Dark/colored logo |
| **Email Header Logo** | Email header gradient | Dark (primary→accent) | Light/white logo |
| **Email Footer Logo** | Email footer | White | Dark/colored logo |

### Database Fields

**affiliate_branding table:**
- `logo_url` - PDF header logo
- `footer_logo_url` - PDF footer logo
- `email_logo_url` - Email header logo
- `email_footer_logo_url` - Email footer logo

**accounts table (for regular users):**
- Same fields added in migration `0022_add_branding_to_accounts.sql`

### Upload Endpoint

```
POST /api/proxy/v1/upload/branding/logo
Content-Type: multipart/form-data

file: <image file>
```

Returns: `{ "url": "https://r2.../branding/logo-xxx.png" }`

---

## 5. Color System

### Default Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **Primary** | `#7C3AED` | Trendy violet - gradients, buttons, metric values |
| **Accent** | `#F26B2B` | Trendy coral - gradient end, accents |

### Color Picker UI

The branding page provides:
- **Color picker input** (native `<input type="color">`)
- **Hex text input** (for precise entry)
- **Live preview** showing the gradient result

### How Colors Are Used

| Location | Primary | Accent |
|----------|---------|--------|
| Header gradient | Start | End |
| CTA buttons | Background | — |
| Metric values | Text color | — |
| Price tier borders | Opacity variants | — |

---

## 6. Contact Information

Contact details appear in report/email footers:

| Field | Format | Example |
|-------|--------|---------|
| `contact_line1` | Name • Title | "John Smith • Senior Agent" |
| `contact_line2` | Phone • Email | "(555) 123-4567 • john@company.com" |
| `website_url` | Full URL | "https://www.company.com" |

### Parsing/Building Functions

**File:** `apps/web/app/app/branding/page.tsx`

```typescript
// Parse "John Smith • Senior Agent" → { name: "John Smith", title: "Senior Agent" }
function parseContactLine1(line: string | null): { name: string; title: string }

// Build "John Smith • Senior Agent" from separate fields
function buildContactLine1(name: string, title: string): string | null
```

---

## 7. Headshot Handling (Option A)

**Implemented:** December 2025

### The Problem

Previously, the system had different approaches for user photos:
- Affiliates: Upload `rep_photo_url` in Branding page
- Regular users: Upload `avatar_url` in Account Settings AND `rep_photo_url` in Branding

This led to confusion and duplicate uploads.

### The Solution (Option A)

**For Regular Users:**
- Their profile photo (`users.avatar_url`) is automatically used as their report headshot
- The Branding page shows a read-only preview with "Edit in Profile →" link
- No duplicate upload needed

**For Affiliates:**
- Keep the separate `rep_photo_url` upload in Branding page
- This is their "representative" photo for sponsored agent reports

### UI Implementation

```tsx
{isAffiliate ? (
  // Affiliates: Upload rep photo
  <ImageUpload 
    label="Rep Photo"
    value={formData.rep_photo_url}
    onChange={(url) => setFormData({ ...formData, rep_photo_url: url })}
  />
) : (
  // Regular users: Show profile photo (read-only)
  <div>
    <img src={userAvatarUrl || formData.rep_photo_url} />
    <a href="/app/account/settings">Edit in Profile →</a>
  </div>
)}
```

### Backend Resolution

**File:** `apps/api/src/api/services/branding.py`

```python
def _get_regular_user_brand(cur, account_id: str, account_name: str) -> Brand:
    """
    For un-sponsored regular users:
    - Get branding from accounts table
    - Use users.avatar_url as rep_photo_url
    """
    cur.execute("""
        SELECT a.*, u.avatar_url
        FROM accounts a
        LEFT JOIN users u ON u.active_account_id = a.id
        WHERE a.id = %s::uuid
    """, (account_id,))
    # ...returns Brand with rep_photo_url = user's avatar_url
```

---

## 8. Database Schema

### affiliate_branding Table

```sql
CREATE TABLE affiliate_branding (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    brand_display_name TEXT NOT NULL,
    -- Logos
    logo_url TEXT,
    footer_logo_url TEXT,
    email_logo_url TEXT,
    email_footer_logo_url TEXT,
    -- Colors
    primary_color TEXT DEFAULT '#7C3AED',
    accent_color TEXT DEFAULT '#F26B2B',
    -- Contact
    rep_photo_url TEXT,
    contact_line1 TEXT,
    contact_line2 TEXT,
    website_url TEXT,
    -- Timestamps
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

### accounts Table Branding Columns

**Migration:** `db/migrations/0022_add_branding_to_accounts.sql`

Added same branding columns to `accounts` table for regular users:
- `footer_logo_url`
- `email_logo_url`
- `email_footer_logo_url`
- `rep_photo_url`
- `contact_line1`
- `contact_line2`
- `website_url`

---

## 9. API Endpoints

### For Affiliates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/affiliate/branding` | Get affiliate branding |
| POST | `/v1/affiliate/branding` | Update affiliate branding |

### For Regular Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/account` | Get account including branding fields |
| PATCH | `/v1/account/branding` | Update account branding |

### Upload Endpoints

| Method | Endpoint | Asset Type |
|--------|----------|------------|
| POST | `/v1/upload/branding/logo` | Logo images |
| POST | `/v1/upload/branding/headshot` | Rep photo (affiliates) |

---

## 10. Preview & Testing

### Sample PDF Download

Users can download a sample PDF with their branding applied:

```
GET /api/proxy/v1/branding/sample-pdf?report_type={type}
```

### Test Email

Users can send a test email to verify branding:

```
POST /api/proxy/v1/branding/test-email
{
  "email": "user@example.com",
  "report_type": "market_snapshot"
}
```

### Live Preview

The branding page shows live previews of:
- PDF header with gradient and logo
- PDF footer with contact info
- Email header with gradient and logo
- Email footer with contact info

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `apps/web/app/app/branding/page.tsx` | Unified branding page |
| `apps/api/src/api/services/branding.py` | Brand resolution logic |
| `apps/api/src/api/routes/account.py` | Regular user branding endpoints |
| `apps/api/src/api/routes/affiliate.py` | Affiliate branding endpoints |
| `apps/worker/src/worker/email/template.py` | Email template with branding |
| `apps/web/lib/templates.ts` | PDF template processing |

### Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `R2_BUCKET_NAME` | API, Worker | Storage for uploaded assets |
| `R2_ACCESS_KEY_ID` | API, Worker | R2 credentials |
| `R2_SECRET_ACCESS_KEY` | API, Worker | R2 credentials |

---

## Related Documentation

- [PDF_REPORTS.md](./PDF_REPORTS.md) - PDF generation and branding
- [EMAIL_SYSTEM.md](./EMAIL_SYSTEM.md) - Email branding
- [USER_ONBOARDING.md](./USER_ONBOARDING.md) - Onboarding branding step
- [ACCOUNT_SETTINGS.md](./ACCOUNT_SETTINGS.md) - Profile avatar (Option A)

---

*This document is the source of truth for TrendyReports branding system.*
