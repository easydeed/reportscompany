# Admin Dashboard

The Admin Dashboard provides platform operators with system-wide visibility and management capabilities for TrendyReports.

## Overview

The admin console is a dedicated section at `/admin` with a dark theme UI, separate from the main application. It provides:

- **Platform Metrics**: Real-time stats on accounts, users, reports, and system health
- **Account Management**: View and manage all accounts across the platform
- **User Management**: View, activate/deactivate users, resend invites
- **Affiliate Management**: Create and manage title company affiliates
- **Plans & Pricing**: Configure subscription plans and limits
- **Report Monitoring**: View all report generations with status tracking
- **Email Logs**: Monitor email deliveries across the platform
- **System Settings**: View system status and configuration

## Access Control

### Admin Role Requirement

Only users with `role = 'ADMIN'` can access the admin console. The role is stored in the `users` table.

```sql
-- Grant admin access to a user
UPDATE users 
SET role = 'ADMIN' 
WHERE email = 'admin@example.com';
```

### Authentication Flow

1. **No token**: Redirects to `/login?next=/admin`
2. **Valid token, non-admin**: Redirects to `/access-denied` page
3. **Valid token, admin**: Access granted to admin console

### Access Denied Page

Located at `/access-denied` (outside the admin layout), this page:
- Shows a clear "Access Denied" message
- Offers "Log in as Admin" button (logs out current user, redirects to login)
- Provides "Back to App" button to return to main application

## Architecture

### Frontend Structure

```
apps/web/
├── lib/
│   └── api-server.ts       # Shared server-side API utility
├── app/
│   ├── admin/
│   │   ├── layout.tsx          # Admin layout with sidebar navigation
│   │   ├── page.tsx            # Dashboard with KPIs
│   │   ├── accounts/
│   │   │   ├── page.tsx        # Accounts list
│   │   │   └── [id]/page.tsx   # Account detail
│   │   ├── users/page.tsx      # Users management
│   │   ├── affiliates/page.tsx # Title companies
│   │   ├── plans/page.tsx      # Plans & pricing
│   │   ├── reports/page.tsx    # Report monitoring
│   │   ├── emails/page.tsx     # Email logs
│   │   └── settings/page.tsx   # System settings
│   ├── access-denied/page.tsx  # Unauthorized access page
│   └── api/v1/admin/           # Proxy routes for client components
```

### Server-Side API Utility

All server components use the shared `api-server.ts` utility for consistent API calls:

```typescript
import { createServerApi } from "@/lib/api-server"

// In a server component
const api = await createServerApi()

// Check authentication
if (!api.isAuthenticated()) {
  redirect('/login')
}

// Make API calls
const { data, error } = await api.get<MyType>('/v1/admin/metrics')

// Parallel calls
const [metrics, accounts] = await Promise.all([
  api.get('/v1/admin/metrics'),
  api.get('/v1/admin/accounts'),
])
```

This provides:
- Centralized API base URL configuration
- Consistent cookie/auth handling
- Proper error handling and logging
- Type-safe responses

### API Proxy Routes

All admin API calls go through Next.js proxy routes to handle authentication cookies:

| Proxy Route | Backend Endpoint | Purpose |
|-------------|------------------|---------|
| `/api/v1/admin/metrics` | `/v1/admin/metrics` | Dashboard metrics |
| `/api/v1/admin/accounts` | `/v1/admin/accounts` | List accounts |
| `/api/v1/admin/accounts/[id]` | `/v1/admin/accounts/{id}` | Account details |
| `/api/v1/admin/users` | `/v1/admin/users` | List users |
| `/api/v1/admin/users/[id]` | `/v1/admin/users/{id}` | Update user |
| `/api/v1/admin/affiliates` | `/v1/admin/affiliates` | List/create affiliates |
| `/api/v1/admin/reports` | `/v1/admin/reports` | List all reports |
| `/api/v1/admin/emails` | `/v1/admin/emails` | Email delivery logs |
| `/api/v1/admin/plans` | `/v1/admin/plans` | List/manage plans |
| `/api/v1/admin/stats/revenue` | `/v1/admin/stats/revenue` | Revenue statistics |

### Backend Endpoints

All admin endpoints are in `apps/api/src/api/routes/admin.py` with the prefix `/v1/admin`.

Protected by the `get_admin_user` dependency which:
1. Checks `request.state.user` set by auth middleware
2. Verifies `role == 'ADMIN'`
3. Returns 403 if not admin

## Dashboard Metrics

The main dashboard displays:

### Primary KPIs
- **Total Accounts**: Count of all accounts (regular + affiliate)
- **Total Users**: Count of all registered users
- **Reports (7d)**: Reports generated in last 7 days
- **Error Rate**: Percentage of failed reports (7d)

### Secondary KPIs
- Completed reports (7d)
- Currently processing
- Pending in queue
- Average render time

### Quick Stats
- Active schedules
- Emails sent (24h)
- Queue depth
- Average processing time

### Recent Activity
- Last 5 reports with status
- Last 5 accounts created

## Pages Reference

### Accounts Page (`/admin/accounts`)

Lists all accounts with:
- Name and slug
- Account type (Regular/Affiliate)
- Plan
- Sponsor (if sponsored)
- User count
- Reports this month
- Status (Active/Inactive)
- Created date

**Filters**: Search, account type, plan

### Users Page (`/admin/users`)

Lists all users with:
- Name and email
- Account name
- Role (Owner/Admin/Member)
- Status (Active/Inactive)
- Email verified status
- Last login
- Created date

**Actions**:
- Activate/Deactivate user
- Mark email as verified
- Resend invite email

### Affiliates Page (`/admin/affiliates`)

Lists all title company affiliates with:
- Company name and slug
- Logo preview
- Agent count
- Reports this month
- Status

**Actions**:
- Create new affiliate
- View affiliate details
- Manage sponsored agents

### Plans Page (`/admin/plans`)

Lists all subscription plans with:
- Plan name and slug
- Monthly report limit
- Overage settings
- Account count using plan
- Active status

**Actions**:
- Edit plan limits
- Enable/disable plans
- Create new plans

### Reports Page (`/admin/reports`)

Lists all report generations with:
- Account name
- Report type
- Status (pending/processing/completed/failed)
- Error message (if failed)
- Processing time
- PDF link (if completed)

**Filters**: Status, report type

### Emails Page (`/admin/emails`)

Lists email delivery logs with:
- Account name
- Recipient count
- Subject
- Status (success/failed)
- Response code
- Timestamp

### Settings Page (`/admin/settings`)

Displays:
- System status (Database, API, Email service)
- Platform statistics by plan
- Growth metrics

## Environment Variables

Required for admin functionality:

```env
# Frontend (Vercel)
NEXT_PUBLIC_API_BASE=https://reportscompany.onrender.com

# Backend (Render)
DATABASE_URL=postgresql://...
JWT_SECRET=...
```

## Troubleshooting

### "Access Denied" when user should be admin

1. Verify user has `role = 'ADMIN'` in database:
   ```sql
   SELECT email, role FROM users WHERE email = 'user@example.com';
   ```

2. User may need to log out and log back in to refresh their JWT

### Dashboard shows zeros

1. Check `NEXT_PUBLIC_API_BASE` is set correctly on Vercel
2. Verify RLS policies allow admin access (migration 0025):
   ```sql
   -- Check if admin RLS bypass is in place
   SELECT tablename, policyname FROM pg_policies WHERE policyname LIKE '%rls%';
   ```
3. Ensure the backend `admin.py` sets admin role for RLS:
   ```python
   set_rls(cur, account_id, user_role="ADMIN")
   ```
4. Check Vercel function logs for API errors
5. Verify backend API is accessible

### API calls failing

1. Check browser console for errors
2. Verify proxy routes exist in `/api/v1/admin/`
3. Check backend logs on Render for 401/403 errors

## Security Considerations

1. **Role-based access**: Only ADMIN role users can access
2. **Server-side verification**: Layout verifies admin status before rendering
3. **API protection**: All backend admin endpoints require ADMIN role
4. **Cookie-based auth**: JWT stored in httpOnly cookie, passed via proxy routes
5. **No client-side secrets**: All sensitive operations go through backend

## Related Documentation

- [User Onboarding](./USER_ONBOARDING.md) - User setup flow
- [Account Settings](./ACCOUNT_SETTINGS.md) - User account management
- [Branding](./BRANDING.md) - White-label branding system
- [Email System](./EMAIL_SYSTEM.md) - Email delivery infrastructure
