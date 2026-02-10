# Admin Console Pages

All admin pages require `role: ADMIN` in the JWT (enforced by middleware).

## Route: `/app/admin` -- Admin Dashboard

> `apps/web/app/app/admin/page.tsx`

Client component that fetches data in parallel on mount.

### API Calls

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/admin/metrics/overview` | Key metrics (accounts, users, reports, error rate, avg render, schedules) |
| `GET /v1/admin/reports?limit=10` | Recent reports with account name, type, status, duration |
| `GET /v1/admin/schedules?limit=10` | Active schedules |
| `GET /v1/admin/emails?limit=10` | Recent email delivery logs |

### UI Sections

1. **Key Metrics** (6-column grid): Total Accounts, Total Users, Reports (7d), Error Rate, Avg Render, Schedules
2. **Report Status Breakdown** (4-column): Completed, Processing, Pending, Failed (color-coded cards)
3. **Management Quick Links** (3-column): Title Companies, All Accounts, All Users
4. **Recent Reports** table: Account, Type, Status, Duration, Time
5. **Two-column grid**: Active Schedules + Recent Emails

## Route: `/app/admin/accounts` -- Account Management

> `apps/web/app/app/admin/accounts/page.tsx`

Lists all accounts. API: `GET /v1/admin/accounts`

## Route: `/app/admin/accounts/[id]` -- Account Detail

> `apps/web/app/app/admin/accounts/[id]/page.tsx`

Single account view. API: `GET /v1/admin/accounts/{id}`, `GET /v1/admin/accounts/{id}/plan-usage`

## Route: `/app/admin/users` -- User Management

> `apps/web/app/app/admin/users/page.tsx`

Lists all users. API: `GET /v1/admin/users`

Supports: resend invite (`POST /v1/admin/users/{id}/resend-invite`), edit user (`PATCH /v1/admin/users/{id}`)

## Route: `/app/admin/affiliates` -- Affiliate Management

> `apps/web/app/app/admin/affiliates/page.tsx`

Lists affiliates with CRUD. APIs:
- `GET /v1/admin/affiliates`
- `POST /v1/admin/affiliates/{id}/invite-agent`
- `POST /v1/admin/affiliates/{id}/bulk-import`

Sub-pages: `/app/admin/affiliates/new`, `/app/admin/affiliates/[id]`

## Route: `/app/admin/leads` -- Lead Management

> `apps/web/app/app/admin/leads/page.tsx`

Lists all leads across all accounts. API: `GET /v1/admin/leads`

## Route: `/app/admin/property-reports` -- Property Report Management

> `apps/web/app/app/admin/property-reports/page.tsx` + `[id]/page.tsx`

Lists and manages property reports. APIs: `GET /v1/admin/property-reports`, `GET/PATCH /v1/admin/property-reports/{id}`

## Route: `/app/admin/sms` -- SMS Management

> `apps/web/app/app/admin/sms/page.tsx`

SMS credit management and log viewing. APIs: `GET /v1/admin/sms/credits`, `GET /v1/admin/sms/logs`

## Legacy Admin (separate auth)

There is also a legacy admin at `/admin/(dashboard)/` with its own auth flow (`/admin/(auth)/login`). This uses a separate layout and has pages for accounts, users, affiliates, emails, plans, property-reports, reports, schedules, settings, lead-pages, blocked-ips.

## Key Files

- `apps/web/app/app/admin/page.tsx` - Main admin dashboard
- `apps/web/app/app/admin/accounts/` - Account pages
- `apps/web/app/app/admin/users/page.tsx` - User management
- `apps/web/app/app/admin/affiliates/` - Affiliate management
- `apps/web/app/app/admin/leads/page.tsx` - Lead management
- `apps/web/app/app/admin/property-reports/` - Property report management
- `apps/web/app/app/admin/sms/page.tsx` - SMS management
- `apps/web/components/admin/` - Shared admin components (overview, tables, types)
