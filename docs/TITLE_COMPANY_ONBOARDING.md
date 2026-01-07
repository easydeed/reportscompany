# Title Company Onboarding Guide

**Purpose**: Scalable process for onboarding title companies and their representatives  
**Admin Dashboard**: `/app/admin/affiliates`

---

## 🎉 Self-Service Admin Dashboard Now Available!

The admin dashboard at `/app/admin` provides a complete UI for onboarding title companies and their agents. **No SQL required!**

### Quick Start (3 Steps)

1. **Go to** `/app/admin/affiliates/new`
2. **Fill in** company name, admin email, logo URL, colors
3. **Click** "Create Affiliate" → Admin receives invite email automatically

That's it! The admin can then log in and invite their own agents.

---

## Executive Summary

TrendyReports supports **white-label branding** for title companies (Industry Affiliates) and their sponsored reps. This document outlines the onboarding process and data requirements.

### Account Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│  INDUSTRY AFFILIATE (Title Company)                     │
│  - Pacific Coast Title                                  │
│  - plan_slug: "affiliate"                               │
│  - account_type: "INDUSTRY_AFFILIATE"                   │
├─────────────────────────────────────────────────────────┤
│  ↓ Sponsors multiple REGULAR accounts                   │
├─────────────────────────────────────────────────────────┤
│  REGULAR (Rep 1)        REGULAR (Rep 2)                 │
│  - John Smith           - Jane Doe                      │
│  - sponsor_account_id   - sponsor_account_id            │
│    → Pacific Coast        → Pacific Coast               │
│  - plan_slug:           - plan_slug:                    │
│    "sponsored_free"       "sponsored_free"              │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Data Requirements

### 1.1 Title Company (Parent Account)

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | ✅ | Company name | "Pacific Coast Title" |
| `slug` | ✅ | URL-safe identifier | "pacific-coast-title" |
| `logo_url` | ✅ | Company logo (PNG/SVG, transparent bg) | "https://cdn.../pct-logo.png" |
| `primary_color` | ✅ | Main brand color (hex) | "#03374f" |
| `accent_color` | ⬚ | Secondary color (hex) | "#f26b2b" |
| `website_url` | ⬚ | Company website | "https://pct.com" |

### 1.2 Rep Profiles (Individual Accounts)

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | ✅ | Rep's full name | "John Smith" |
| `email` | ✅ | Login email (unique) | "john@pct.com" |
| `title` | ⬚ | Job title | "Senior Title Rep" |
| `phone` | ⬚ | Contact phone | "555-123-4567" |
| `headshot_url` | ⬚ | Profile photo (square, 400x400+) | "https://cdn.../john.jpg" |

---

## 2. Onboarding Process

### Phase 1: Company Setup (Admin Task)

```sql
-- 1. Create the title company account
INSERT INTO accounts (
  name, 
  slug, 
  account_type, 
  plan_slug,
  logo_url,
  primary_color,
  secondary_color,
  status
) VALUES (
  'Pacific Coast Title',
  'pacific-coast-title',
  'INDUSTRY_AFFILIATE',
  'affiliate',
  'https://cdn.example.com/pct-logo.png',
  '#03374f',
  '#f26b2b',
  'active'
) RETURNING id;

-- Save the returned ID (e.g., 'abc123-...')
```

```sql
-- 2. Create branding configuration
INSERT INTO affiliate_branding (
  account_id,
  brand_display_name,
  logo_url,
  primary_color,
  accent_color,
  website_url
) VALUES (
  'abc123-...',  -- from step 1
  'Pacific Coast Title',
  'https://cdn.example.com/pct-logo.png',
  '#03374f',
  '#f26b2b',
  'https://pct.com'
);
```

### Phase 2: Rep Account Creation

**Option A: Manual (Admin creates each rep)**

```sql
-- 1. Create user account
INSERT INTO users (email, password_hash, role, email_verified, is_active)
VALUES ('john@pct.com', 'HASHED_PASSWORD', 'member', true, true)
RETURNING id;

-- 2. Create rep's account (sponsored by title company)
INSERT INTO accounts (
  name,
  slug,
  account_type,
  plan_slug,
  sponsor_account_id,
  status
) VALUES (
  'John Smith',
  'john-smith-pct',
  'REGULAR',
  'sponsored_free',
  'abc123-...',  -- Title company account ID
  'active'
) RETURNING id;

-- 3. Link user to account
INSERT INTO account_users (account_id, user_id, role)
VALUES ('rep-account-id', 'user-id', 'OWNER');

-- 4. Add rep branding (inherits from sponsor, but can add headshot)
INSERT INTO affiliate_branding (
  account_id,
  brand_display_name,
  logo_url,
  primary_color,
  accent_color,
  rep_photo_url,
  contact_line1,
  contact_line2,
  website_url
) VALUES (
  'rep-account-id',
  'Pacific Coast Title',  -- Uses company name
  'https://cdn.example.com/pct-logo.png',
  '#03374f',
  '#f26b2b',
  'https://cdn.example.com/john-headshot.jpg',
  'John Smith • Senior Title Rep',
  '555-123-4567 • john@pct.com',
  'https://pct.com'
);
```

**Option B: Self-Service (Rep signs up with invite code)**

*Future feature - not yet implemented*

### Phase 3: Asset Upload

**Logo Requirements:**
- Format: PNG or SVG
- Background: Transparent
- Size: 400px+ width
- Aspect: Horizontal preferred (4:1 to 2:1)

**Headshot Requirements:**
- Format: JPG or PNG
- Size: 400x400px minimum
- Shape: Square (will be displayed as circle)
- Background: Professional/neutral

**Upload Destination:**
- Cloudflare R2 bucket: `trendy-reports-assets`
- Path convention: `/branding/{account_slug}/{asset_type}.{ext}`
- Example: `/branding/pacific-coast-title/logo.png`

---

## 3. Bulk Onboarding (CSV Import)

For onboarding many reps at once, prepare a CSV:

### Company CSV (`company.csv`)

```csv
name,slug,logo_url,primary_color,accent_color,website_url
Pacific Coast Title,pacific-coast-title,https://cdn.../logo.png,#03374f,#f26b2b,https://pct.com
```

### Reps CSV (`reps.csv`)

```csv
email,name,title,phone,headshot_url
john@pct.com,John Smith,Senior Title Rep,555-123-4567,https://cdn.../john.jpg
jane@pct.com,Jane Doe,Title Officer,555-987-6543,https://cdn.../jane.jpg
```

### Import Script (Future)

```python
# scripts/onboard_title_company.py
# TODO: Create this script to automate bulk onboarding

def onboard_company(company_csv: str, reps_csv: str):
    """
    1. Read company CSV, create INDUSTRY_AFFILIATE account
    2. Create affiliate_branding for company
    3. Read reps CSV
    4. For each rep:
       - Create user (generate temp password)
       - Create REGULAR account with sponsor_account_id
       - Create affiliate_branding with rep details
       - Send welcome email with login credentials
    """
    pass
```

---

## 4. Branding Resolution Flow

When a rep generates a report, the system determines branding:

```
┌─────────────────────────────────────────────────────────┐
│  Rep generates report                                   │
│  account_id = rep's account                             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  get_brand_for_account(account_id)                      │
│  (apps/api/src/api/services/branding.py)                │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│ Has sponsor_id?     │ NO  │ Use own branding or default │
│ (sponsored rep)     │────▶│ TrendyReports               │
└─────────────────────┘     └─────────────────────────────┘
          │ YES
          ▼
┌─────────────────────────────────────────────────────────┐
│  Look up affiliate_branding for sponsor account         │
│  → Returns title company's logo, colors, etc.           │
│  → Rep's headshot/contact from their own branding row   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Final Brand:                                           │
│  - Logo: Title Company                                  │
│  - Colors: Title Company                                │
│  - Rep Photo: Rep's headshot                            │
│  - Contact: Rep's info                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Checklist

### Already Built ✅

- [x] Account types (REGULAR, INDUSTRY_AFFILIATE)
- [x] Sponsor relationship (`sponsor_account_id`)
- [x] Plans system (affiliate, sponsored_free)
- [x] Branding table (`affiliate_branding`)
- [x] Branding service (`get_brand_for_account()`)
- [x] Branding UI page (`/app/branding`)
- [x] Image upload component
- [x] PDF branding injection
- [x] **Invite system** - Rep invitation via `/v1/affiliate/invite-agent`
- [x] **Invite emails** - Automated Resend email with invite link
- [x] **Accept invite flow** - `/welcome?token=` page for password setup
- [x] **Affiliate onboarding checklist** - Dashboard guidance for new affiliates
- [x] **User onboarding system** - Step-by-step setup wizard

### ✅ Recently Added

- [x] **Bulk CSV import** - Import 50+ agents at once via UI
- [x] **Direct logo upload** - Drag & drop in create affiliate form
- [x] **Agent headshot upload** - Camera icon per agent in table

### 🔧 Nice to Have (Future)

- [ ] **Branding preview** - Live preview before saving
- [ ] **Batch headshot upload** - Upload multiple headshots at once

---

## 6. Recommended Approach

### ✅ Use the Admin Dashboard (Recommended)

**No SQL required!** Full UI for everything:

#### Step 1: Create Title Company
1. Go to `/app/admin/affiliates/new`
2. Fill in:
   - Company Name (required)
   - Admin Email (required)
   - **Drag & drop logo** (uploads to R2 automatically!)
   - Pick colors with color picker
   - Website URL (optional)
3. Click "Create Affiliate"
4. Admin receives invite email automatically

#### Step 2: Add Agents

**Option A: Single Agent**
1. Go to `/app/admin/affiliates/[id]`
2. Scroll to "Invite New Agent"
3. Enter name and email → Click "Send Invite"

**Option B: Bulk Import (CSV)** 🆕
1. Go to `/app/admin/affiliates/[id]`
2. Scroll to "Bulk Import Agents"
3. Download CSV template
4. Fill in: `email, first_name, last_name, name`
5. Upload CSV → Preview → Import
6. All agents receive invite emails automatically!

#### Step 3: Upload Headshots 🆕

For each agent in the "Sponsored Agents" table:
1. Click the **camera icon** in the "Headshot" column
2. **Drag & drop** the headshot image
3. Click "Save" → Uploads to R2 automatically!

**Option C: Title Company does it (self-service)**
1. Title company admin logs in
2. Goes to their affiliate dashboard
3. Uses invite agent form
4. ~~Automate **welcome emails** via Resend~~ ✅ Done - `send_invite_email()`

### What's Now Automated

When you invite an agent via the affiliate dashboard:

1. **Account Creation**: User + Account + Branding automatically created
2. **Email Delivery**: Invite email sent via Resend with accept link
3. **Self-Service Setup**: Agent visits `/welcome?token=...` to set password
4. **Auto-Linking**: Agent sees affiliate branding on all their reports

---

## 7. Database Schema Reference

### accounts

```sql
id                        UUID PRIMARY KEY
name                      VARCHAR(200)
slug                      VARCHAR(100) UNIQUE
account_type              TEXT ('REGULAR' | 'INDUSTRY_AFFILIATE')
plan_slug                 VARCHAR(50) → plans.slug
sponsor_account_id        UUID → accounts.id (for sponsored reps)
logo_url                  VARCHAR(500)
primary_color             VARCHAR(7)
secondary_color           VARCHAR(7)
status                    VARCHAR(20)
```

### affiliate_branding

```sql
account_id                UUID PRIMARY KEY → accounts.id
brand_display_name        TEXT
logo_url                  TEXT
primary_color             TEXT
accent_color              TEXT
rep_photo_url             TEXT
contact_line1             TEXT  -- "Name • Title"
contact_line2             TEXT  -- "Phone • Email"
website_url               TEXT
```

### plans

```sql
slug                      TEXT PRIMARY KEY
name                      TEXT
monthly_report_limit      INT
allow_overage             BOOLEAN
overage_price_cents       INT
```

---

---

## Appendix: Quick SQL Reference

### Create Title Company + First Rep

```sql
-- Variables (replace these)
\set company_name 'Pacific Coast Title'
\set company_slug 'pacific-coast-title'
\set logo_url 'https://cdn.example.com/pct-logo.png'
\set primary_color '#03374f'
\set accent_color '#f26b2b'
\set website 'https://pct.com'

\set rep_name 'John Smith'
\set rep_email 'john@pct.com'
\set rep_title 'Senior Title Rep'
\set rep_phone '555-123-4567'
\set rep_photo 'https://cdn.example.com/john.jpg'

-- Execute
BEGIN;

-- Company account
INSERT INTO accounts (name, slug, account_type, plan_slug, logo_url, primary_color, secondary_color, status)
VALUES (:'company_name', :'company_slug', 'INDUSTRY_AFFILIATE', 'affiliate', :'logo_url', :'primary_color', :'accent_color', 'active')
RETURNING id AS company_id \gset

-- Company branding
INSERT INTO affiliate_branding (account_id, brand_display_name, logo_url, primary_color, accent_color, website_url)
VALUES (:'company_id', :'company_name', :'logo_url', :'primary_color', :'accent_color', :'website');

-- Rep user
INSERT INTO users (email, password_hash, role, email_verified, is_active)
VALUES (:'rep_email', crypt('TempPass123!', gen_salt('bf')), 'member', true, true)
RETURNING id AS user_id \gset

-- Rep account
INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id, status)
VALUES (:'rep_name', :'company_slug' || '-' || lower(replace(:'rep_name', ' ', '-')), 'REGULAR', 'sponsored_free', :'company_id', 'active')
RETURNING id AS rep_account_id \gset

-- Link user to account
INSERT INTO account_users (account_id, user_id, role)
VALUES (:'rep_account_id', :'user_id', 'OWNER');

-- Rep branding
INSERT INTO affiliate_branding (account_id, brand_display_name, logo_url, primary_color, accent_color, rep_photo_url, contact_line1, contact_line2, website_url)
VALUES (:'rep_account_id', :'company_name', :'logo_url', :'primary_color', :'accent_color', :'rep_photo', :'rep_name' || ' • ' || :'rep_title', :'rep_phone' || ' • ' || :'rep_email', :'website');

COMMIT;

-- Verify
SELECT a.name, a.account_type, a.plan_slug, ab.brand_display_name
FROM accounts a
LEFT JOIN affiliate_branding ab ON ab.account_id = a.id
WHERE a.slug LIKE :'company_slug' || '%';
```

