# Admin Dashboard Documentation

**Last Updated**: December 2, 2024 (v2)
**Purpose**: Comprehensive guide to the admin console for platform operators

---

## Overview

The Admin Dashboard provides system-wide control over all accounts, users, and affiliates. Access is restricted to users with the `ADMIN` role.

### Access Control

- **URL**: `/app/admin`
- **Required Role**: `ADMIN` in `account_users` table
- **Authentication**: JWT token in `mr_token` cookie
- **Demo Account**: `admin@trendyreports-demo.com` / `DemoAdmin123!`

---

## Navigation Structure

```
/app/admin
├── Overview (main dashboard)
├── /affiliates          ← Title company management
│   ├── List all affiliates
│   ├── /new             ← Create new affiliate
│   └── /[id]            ← Affiliate detail + agents
├── /accounts            ← All accounts list
└── /users               ← All users list
```

---

## 1. Admin Overview (`/app/admin`)

The main dashboard provides:

### Quick Navigation Cards
- **Title Companies** → `/app/admin/affiliates`
- **All Accounts** → `/app/admin/accounts`
- **All Users** → `/app/admin/users`

### KPI Metrics
| Metric | Description |
|--------|-------------|
| Active Schedules | Number of enabled report schedules |
| Reports/Day | Average daily report generation |
| Emails/Day | Average daily emails sent |
| Avg Render (ms) | Average PDF generation time |

### Charts
- **Reports Trend**: 30-day line chart of report generations
- **Emails Trend**: 30-day line chart of emails sent

---

## 2. Title Companies (`/app/admin/affiliates`)

Manage industry affiliates (title companies) and their sponsored agents.

### List View

| Column | Description |
|--------|-------------|
| Company | Logo, name, and slug |
| Plan | Current plan (affiliate, etc.) |
| Agents | Number of sponsored agents |
| Reports/Month | Reports generated this month by all agents |
| Status | Active/Inactive badge |
| Created | Account creation date |

### Features
- **Search**: Filter by company name
- **Add Title Company**: Create new affiliate

### API Endpoints

```
GET    /v1/admin/affiliates                    # List affiliates
GET    /v1/admin/affiliates/:id                # Get affiliate detail
POST   /v1/admin/affiliates                    # Create affiliate
PATCH  /v1/admin/affiliates/:id                # Update affiliate
POST   /v1/admin/affiliates/:id/invite-agent   # Invite single agent
POST   /v1/admin/affiliates/:id/bulk-import    # Bulk import agents from CSV
PATCH  /v1/admin/agents/:accountId/headshot    # Update agent headshot
```

---

## 3. Affiliate Detail (`/app/admin/affiliates/[id]`)

Comprehensive view of a single affiliate.

### Sections

#### Stats Cards
- Agents count
- Reports this month
- Created date
- Website link

#### Admin Contact
- Primary account administrator
- Email and status

#### Branding
- Display name
- Logo and colors
- Contact lines
- Website URL

#### Invite New Agent
Form to add agents to this affiliate:
- Agent/Company Name
- Email Address
- Sends automatic invite email

#### Bulk Import Agents
For full-service onboarding, import multiple agents at once from CSV:

1. Download the CSV template
2. Fill in agent data: `email, first_name, last_name, name`
3. Upload the CSV file
4. Preview the agents to be imported
5. Click "Import" to create all accounts and send invites

**CSV Columns:**
| Column | Required | Description |
|--------|----------|-------------|
| email | Yes | Agent's email address |
| first_name | No | Agent's first name |
| last_name | No | Agent's last name |
| name | No | Business/Account name (auto-generated from names if empty) |

**Import Results:**
- Success count with green badge
- Error count with red badge (e.g., duplicate emails)
- Detailed results per agent

#### Sponsored Agents Table
| Column | Description |
|--------|-------------|
| Agent | Avatar, name, and contact name |
| Email | Agent's email |
| Reports/Month | Monthly report count |
| Last Report | Date of last report |
| Status | Active/Inactive |
| Joined | Account creation date |
| Headshot | Upload button to set agent photo |

#### Admin Headshot Upload
For each agent in the table, admins can upload a professional headshot:
1. Click the camera icon in the Headshot column
2. Drag & drop or click to upload image
3. Image uploads to R2 automatically
4. Click Save to apply the headshot

This is useful for full-service onboarding where the title company provides agent photos.

### Actions
- **Activate/Deactivate**: Toggle affiliate status

---

## 4. Create Affiliate (`/app/admin/affiliates/new`)

Form to onboard a new title company.

### Required Fields
- **Company Name**: Title company name
- **Admin Email**: Primary contact email

### Optional Fields
- **Admin First/Last Name**: Contact name
- **Website URL**: Company website
- **Logo**: Drag-and-drop upload to R2 (PNG/SVG recommended)
- **Primary Color**: Main brand color (hex) with color picker
- **Accent Color**: Secondary brand color (hex) with color picker

### Logo Upload
The logo upload uses the R2-backed ImageUpload component:
- Drag & drop or click to upload
- Automatically uploads to Cloudflare R2
- Supports PNG, JPG, SVG
- Transparent backgrounds recommended
- Wide aspect ratio for report headers

### What Happens
1. Creates `INDUSTRY_AFFILIATE` account
2. Creates admin user with `OWNER` role
3. Creates branding record (if provided)
4. Generates invite token
5. Sends invitation email via Resend
6. Returns invite URL for manual sharing

---

## 5. All Accounts (`/app/admin/accounts`)

System-wide account listing.

### Filters
- **Search**: By name or slug
- **Account Type**: REGULAR or INDUSTRY_AFFILIATE
- **Plan**: free, pro, team, affiliate, sponsored_free

### Table Columns
| Column | Description |
|--------|-------------|
| Account | Name and slug |
| Type | Regular or Affiliate badge |
| Plan | Current plan |
| Sponsor | Sponsoring affiliate (if any) |
| Users | Number of users |
| Reports/Month | Monthly report count |
| Status | Active/Inactive |
| Created | Creation date |

### API Endpoints

```
GET    /v1/admin/accounts               # List accounts
GET    /v1/admin/accounts/:id/plan-usage # Plan usage debug
PATCH  /v1/admin/accounts/:id           # Update account
```

---

## 6. All Users (`/app/admin/users`)

System-wide user listing.

### Filters
- **Search**: By email or name
- **Status**: Active/Inactive
- **Role**: OWNER, MEMBER, ADMIN

### Table Columns
| Column | Description |
|--------|-------------|
| User | Email and name |
| Account | Account name and type |
| Role | User role badge |
| Status | Active/Inactive with icon |
| Verified | Email verification status |
| Last Login | Last login date |
| Joined | Account creation date |
| Actions | Resend invite button (for unverified) |

### Actions
- **Resend Invite**: For unverified users, resend the invitation email

### API Endpoints

```
GET    /v1/admin/users                  # List users
GET    /v1/admin/users/:id              # Get user detail
PATCH  /v1/admin/users/:id              # Update user
POST   /v1/admin/users/:id/resend-invite # Resend invite email
```

---

## API Reference

### Authentication

All admin endpoints require:
1. Valid JWT token in `mr_token` cookie
2. User must have `ADMIN` role in `account_users`

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (no token) |
| 403 | Forbidden (not admin) |
| 404 | Resource not found |
| 500 | Server error |

### Affiliates API

#### List Affiliates
```
GET /v1/admin/affiliates?search=&limit=100
```

Response:
```json
{
  "affiliates": [
    {
      "account_id": "uuid",
      "name": "Pacific Coast Title",
      "slug": "pacific-coast-title",
      "plan_slug": "affiliate",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00",
      "logo_url": "https://...",
      "primary_color": "#03374f",
      "brand_display_name": "Pacific Coast Title",
      "agent_count": 15,
      "reports_this_month": 234
    }
  ],
  "count": 1
}
```

#### Create Affiliate
```
POST /v1/admin/affiliates
Content-Type: application/json

{
  "company_name": "Pacific Coast Title",
  "admin_email": "admin@pct.com",
  "admin_first_name": "John",
  "admin_last_name": "Doe",
  "plan_slug": "affiliate",
  "logo_url": "https://...",
  "primary_color": "#03374f",
  "accent_color": "#f26b2b",
  "website_url": "https://pct.com"
}
```

Response:
```json
{
  "ok": true,
  "account_id": "uuid",
  "user_id": "uuid",
  "name": "Pacific Coast Title",
  "slug": "pacific-coast-title",
  "admin_email": "admin@pct.com",
  "invite_url": "https://app.../welcome?token=..."
}
```

#### Invite Agent
```
POST /v1/admin/affiliates/:affiliateId/invite-agent
Content-Type: application/json

{
  "affiliate_id": "uuid",
  "agent_name": "John Smith Realty",
  "agent_email": "john@example.com"
}
```

Response:
```json
{
  "ok": true,
  "account_id": "uuid",
  "user_id": "uuid",
  "name": "John Smith Realty",
  "email": "john@example.com",
  "affiliate_id": "uuid",
  "affiliate_name": "Pacific Coast Title",
  "invite_url": "https://app.../welcome?token=..."
}
```

#### Bulk Import Agents
```
POST /v1/admin/affiliates/:affiliateId/bulk-import
Content-Type: application/json

{
  "affiliate_id": "uuid",
  "agents": [
    {
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "name": "John Doe Realty"
    },
    {
      "email": "jane@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "name": "Jane Smith Team"
    }
  ]
}
```

Response:
```json
{
  "ok": true,
  "affiliate_id": "uuid",
  "affiliate_name": "Pacific Coast Title",
  "total": 2,
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "email": "john@example.com",
      "success": true,
      "account_id": "uuid",
      "user_id": "uuid"
    },
    {
      "email": "jane@example.com",
      "success": true,
      "account_id": "uuid",
      "user_id": "uuid"
    }
  ]
}
```

#### Update Agent Headshot
```
PATCH /v1/admin/agents/:accountId/headshot
Content-Type: application/json

{
  "headshot_url": "https://r2.example.com/headshots/uuid.jpg"
}
```

Response:
```json
{
  "ok": true,
  "account_id": "uuid",
  "user_id": "uuid",
  "email": "john@example.com",
  "headshot_url": "https://r2.example.com/headshots/uuid.jpg"
}
```

---

## Database Schema

### Key Tables

#### accounts
```sql
id                          UUID PRIMARY KEY
name                        VARCHAR(200)
slug                        VARCHAR(100) UNIQUE
account_type                TEXT  -- 'REGULAR' | 'INDUSTRY_AFFILIATE'
plan_slug                   TEXT  -- 'free' | 'pro' | 'affiliate' | 'sponsored_free'
sponsor_account_id          UUID  -- Links to sponsor (for sponsored accounts)
is_active                   BOOLEAN DEFAULT TRUE
monthly_report_limit_override INT  -- Optional limit override
```

#### users
```sql
id                          UUID PRIMARY KEY
account_id                  UUID REFERENCES accounts(id)
email                       VARCHAR(255) UNIQUE
first_name                  VARCHAR(100)
last_name                   VARCHAR(100)
is_active                   BOOLEAN DEFAULT TRUE
email_verified              BOOLEAN DEFAULT FALSE
```

#### account_users
```sql
account_id                  UUID REFERENCES accounts(id)
user_id                     UUID REFERENCES users(id)
role                        TEXT  -- 'OWNER' | 'MEMBER' | 'ADMIN'
```

#### affiliate_branding
```sql
account_id                  UUID PRIMARY KEY REFERENCES accounts(id)
brand_display_name          VARCHAR(200)
logo_url                    TEXT
primary_color               VARCHAR(20)
accent_color                VARCHAR(20)
website_url                 TEXT
```

---

## File Structure

```
apps/
├── api/src/api/routes/
│   └── admin.py                    # All admin API endpoints
│
└── web/app/
    ├── app/admin/
    │   ├── page.tsx                # Overview page
    │   ├── affiliates/
    │   │   ├── page.tsx            # List affiliates
    │   │   ├── new/
    │   │   │   └── page.tsx        # Create affiliate (with ImageUpload)
    │   │   └── [id]/
    │   │       ├── page.tsx        # Affiliate detail
    │   │       ├── invite-agent-form.tsx
    │   │       ├── affiliate-actions.tsx
    │   │       ├── bulk-import-form.tsx    # CSV import UI
    │   │       └── agent-headshot-upload.tsx # Headshot upload dialog
    │   ├── accounts/
    │   │   └── page.tsx            # List accounts
    │   └── users/
    │       ├── page.tsx            # List users
    │       └── resend-invite-button.tsx
    │
    └── api/proxy/v1/admin/
        ├── affiliates/
        │   ├── route.ts            # List/create affiliates
        │   └── [affiliateId]/
        │       ├── route.ts        # Get/update affiliate
        │       ├── invite-agent/
        │       │   └── route.ts    # Invite single agent
        │       └── bulk-import/
        │           └── route.ts    # Bulk import agents
        ├── agents/
        │   └── [accountId]/
        │       └── headshot/
        │           └── route.ts    # Update agent headshot
        ├── accounts/
        │   ├── route.ts            # List accounts
        │   └── [accountId]/
        │       └── route.ts        # Update account
        └── users/
            ├── route.ts            # List users
            └── [userId]/
                ├── route.ts        # Get/update user
                └── resend-invite/
                    └── route.ts    # Resend invite
```

---

## Security Considerations

1. **Role Verification**: Every admin endpoint verifies `ADMIN` role
2. **Token Required**: All requests require valid JWT
3. **Input Validation**: Pydantic models validate all inputs
4. **Password Security**: Admin never sees or sets passwords
5. **Invite Flow**: Users set their own passwords via invite tokens
6. **Audit Trail**: All changes are timestamped (created_at, updated_at)

---

## Common Operations

### Onboard a New Title Company

1. Go to `/app/admin/affiliates`
2. Click "Add Title Company"
3. Fill in company name and admin email
4. Upload logo (drag & drop to R2)
5. Set brand colors with color picker
6. Submit → Admin receives invite email
7. Admin clicks link → Sets password → Account ready

### Add Agent to Title Company (Single)

1. Go to `/app/admin/affiliates`
2. Click on the title company
3. Scroll to "Invite New Agent"
4. Enter agent name and email
5. Submit → Agent receives invite email
6. Agent clicks link → Sets password → Can generate reports

### Bulk Import Agents (Full-Service Onboarding)

For title companies that want hands-off onboarding:

1. Go to `/app/admin/affiliates`
2. Click on the title company
3. Scroll to "Bulk Import Agents"
4. Download the CSV template
5. Fill in agent data (email, first_name, last_name, name)
6. Upload the completed CSV
7. Review the preview
8. Click "Import" → All agents receive invite emails
9. Optionally upload headshots for each agent (see below)

### Upload Agent Headshots (Admin)

For full-service onboarding where admin manages agent photos:

1. Go to `/app/admin/affiliates`
2. Click on the title company
3. In the "Sponsored Agents" table, find the agent
4. Click the camera icon in the "Headshot" column
5. Drag & drop the headshot image
6. Click "Save"

### Resend Lost Invite

1. Go to `/app/admin/users`
2. Find the unverified user
3. Click the mail icon → New invite sent
4. Copy the invite URL if needed

---

## Troubleshooting

### Common Issues

#### "Application error: a client-side exception has occurred"

**Symptom**: Page crashes with a generic error message.

**Common Causes**:
1. **Empty Select values**: Radix UI `<SelectItem>` components cannot have empty string values (`value=""`). Use a sentinel value like `"all"` instead.
2. **Missing API data**: Backend returns null/undefined where UI expects an object.
3. **Invalid date parsing**: Dates from API may be null or malformed.

**Fix**: Check browser console for specific error. Common pattern:
```
Error: A <Select.Item /> must have a value prop that is not an empty string.
```

**Solution**: Change `<SelectItem value="">` to `<SelectItem value="all">` and update filter logic to ignore "all" values.

#### Filters Not Working

**Symptom**: Selecting a filter doesn't change results.

**Checklist**:
1. Verify the filter value is being sent to API (check Network tab)
2. Confirm API endpoint accepts that query parameter
3. Check that "all" values are excluded from API calls

#### Data Shows 0 or Empty

**Symptom**: Stats cards show 0 even though data exists.

**Causes**:
1. API endpoint not returning expected fields
2. Response shape changed (e.g., `accounts` vs `data`)
3. User doesn't have ADMIN role

**Debug**: Check Network tab for API response structure.

---

## Known Limitations

1. **No Pagination**: Account and user lists load all records (fine for <1000)
2. **No Bulk Delete**: Can only deactivate accounts, not delete
3. **No Export**: No CSV export of account/user data yet
4. **No Batch Headshot Upload**: Must upload headshots one at a time

---

## Changelog

### December 2, 2024
- **Fixed**: Select component empty value error on Accounts and Users pages
- **Added**: Quick navigation cards on Admin Overview
- **Added**: Bulk CSV import for agents
- **Added**: Admin headshot upload for agents
- **Added**: Direct logo upload (R2) on Create Affiliate form
- **Added**: Color pickers for brand colors
- **Added**: Collapsible admin sub-navigation in sidebar
  - Overview, Title Companies, All Accounts, All Users
  - Auto-expands when in admin section