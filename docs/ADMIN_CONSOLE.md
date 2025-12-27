# Admin Console — TrendyReports (Source of Truth)

The Admin Console provides platform operators with system-wide visibility and management capabilities at `/admin`. This document is the single source of truth for all admin-related architecture, authorization, and implementation details.

---

## 1. Definitions (Critical — Do Not Mix)

### 1.1 Platform Admin vs Tenant Role

| Concept | Storage | Values | Purpose |
|---------|---------|--------|---------|
| **Platform Admin** | `users.is_platform_admin` | `TRUE / FALSE` | Access to `/admin` console (system-wide) |
| **Tenant Role** | `account_users.role` | `OWNER / ADMIN / MEMBER` | Permissions inside `/app` (per-account) |

> **Rule:** Platform admin is ops/staff. Tenant roles are customer permissions. Never mix them.

### 1.2 Account Types

| Type | `account_type` | `plan_slug` | Description |
|------|----------------|-------------|-------------|
| Regular User | `REGULAR` | `free`, `solo`, `team` | Individual agents |
| Sponsored Agent | `REGULAR` | `sponsored_free` | Agents sponsored by affiliates |
| Title Company | `INDUSTRY_AFFILIATE` | `affiliate` | Title companies sponsoring agents |
| Platform Ops | `REGULAR` | `team` | Internal ops account (e.g., `trendyreports-ops`) |

---

## 2. Access Control

### 2.1 Platform Admin Credentials

```
Email: admin@trendyreports.io
Password: Alpha637#
Account: TrendyReports Operations (trendyreports-ops)
```

### 2.2 Authentication Flow

```
User visits /admin
        │
        ▼
┌─────────────────┐
│  Has mr_token?  │───No───▶ Redirect to /admin/login
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────────────┐
│  is_platform_admin?     │───No───▶ Redirect to /access-denied
└────────┬────────────────┘
         │ Yes
         ▼
    Access Granted
```

### 2.3 Dedicated Admin Login Page

The admin console has its own login page at `/admin/login` with:
- **Unique styling**: Dark gradient background with violet/purple accents
- **Admin-only validation**: After login, checks `is_platform_admin` and rejects non-admins
- **Separate from main app**: Users don't see the regular login page

### 2.4 SQL Reference

```sql
-- Check who has platform admin access
SELECT email, is_platform_admin FROM users WHERE is_platform_admin = TRUE;

-- Grant platform admin (ops/staff only)
UPDATE users SET is_platform_admin = TRUE WHERE email = 'ops@trendyreports.io';

-- Revoke platform admin
UPDATE users SET is_platform_admin = FALSE WHERE email = 'former-admin@example.com';
```

---

## 3. Architecture

### 3.1 File Structure

```
apps/web/
├── lib/
│   └── api-server.ts              # Shared server-side API utility
├── app/
│   ├── admin/
│   │   ├── (auth)/                # Public route group (no auth required)
│   │   │   └── login/
│   │   │       └── page.tsx       # Dedicated admin login page
│   │   ├── (dashboard)/           # Protected route group (requires is_platform_admin)
│   │   │   ├── layout.tsx         # Admin layout with sidebar
│   │   │   ├── logout-button.tsx  # Client component for logout
│   │   │   ├── page.tsx           # Dashboard with KPIs
│   │   │   ├── accounts/
│   │   │   │   ├── page.tsx       # Account list
│   │   │   │   └── [id]/page.tsx  # Account detail
│   │   │   ├── users/page.tsx     # User management (shows BOTH roles)
│   │   │   ├── affiliates/page.tsx
│   │   │   ├── plans/page.tsx
│   │   │   ├── reports/page.tsx
│   │   │   ├── emails/page.tsx
│   │   │   └── settings/page.tsx
│   ├── access-denied/page.tsx     # Unauthorized access page
│   └── api/v1/admin/              # Proxy routes for client components

apps/api/src/api/
├── deps/
│   └── admin.py                   # get_admin_user dependency (checks is_platform_admin)
├── middleware/
│   └── authn.py                   # Auth middleware (populates is_platform_admin)
└── routes/
    ├── admin.py                   # All /v1/admin/* endpoints
    └── me.py                      # Returns is_platform_admin in response
```

**Route Groups Explained:**
- `(auth)` — Public routes (login page), no authentication required
- `(dashboard)` — Protected routes, requires `is_platform_admin = TRUE`
- URLs remain clean: `/admin/login`, `/admin`, `/admin/users`, etc.

### 3.2 API Proxy Routes

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

---

## 4. Database Schema

### 4.1 Platform Admin Column

```sql
-- Migration 0026: Added is_platform_admin
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE;
```

### 4.2 Key Tables & Columns

| Table | Column | Type | Notes |
|-------|--------|------|-------|
| `users` | `is_platform_admin` | BOOLEAN | Platform admin access (system-wide) |
| `users` | `account_id` | UUID | Direct FK to accounts |
| `account_users` | `role` | VARCHAR | Tenant role: `OWNER`, `ADMIN`, `MEMBER` |
| `accounts` | `account_type` | VARCHAR | `REGULAR`, `INDUSTRY_AFFILIATE` |
| `accounts` | `plan_slug` | VARCHAR | FK to plans table |
| `accounts` | `is_active` | BOOLEAN | Account status |
| `plans` | `plan_slug` | VARCHAR | **Primary key** (not `id`) |
| `report_generations` | `generated_at` | TIMESTAMP | (not `created_at`) |
| `report_generations` | `processing_time_ms` | INTEGER | (not `started_at`/`finished_at`) |
| `reports` | `input_params` | JSONB | (not `params`) |

### 4.3 RLS Admin Bypass

Admin queries must bypass RLS to see all tenant data:

```sql
-- RLS policies include admin bypass (migration 0025)
CREATE POLICY "..." ON report_generations
FOR SELECT USING (
    account_id::text = current_setting('app.current_account_id', true)
    OR current_setting('app.current_user_role', true) = 'ADMIN'  -- Admin bypass
);
```

---

## 5. Backend Implementation

### 5.1 Auth Middleware (`authn.py`)

Populates `request.state.user` with `is_platform_admin`:

```python
cur.execute("""
    SELECT id, email, role, is_platform_admin FROM users
    WHERE id=%s::uuid AND account_id=%s::uuid
""", (claims["user_id"], acct))
user_row = cur.fetchone()
if user_row:
    user_info = {
        "id": str(user_row[0]),
        "email": user_row[1],
        "role": (user_row[2] or "USER").upper(),
        "is_platform_admin": bool(user_row[3]) if user_row[3] is not None else False,
        "account_id": acct
    }
```

### 5.2 Admin Dependency (`deps/admin.py`)

Gates all `/v1/admin/*` endpoints:

```python
def get_admin_user(request: Request):
    user_info = getattr(request.state, "user", None)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check platform admin flag (NOT tenant role)
    if not user_info.get("is_platform_admin", False):
        raise HTTPException(status_code=403, detail="Platform admin only")
    
    return user_info
```

### 5.3 `/v1/me` Endpoint (`me.py`)

Returns `is_platform_admin` for frontend authorization:

```python
return {
    "account_id": account_id,
    "user_id": user_info.get("id"),
    "email": user_info.get("email"),
    "role": user_info.get("role", "USER"),
    "account_type": account_type,
    "is_platform_admin": user_info.get("is_platform_admin", False)
}
```

### 5.4 Admin Endpoints Pattern

All admin endpoints must:
1. Use `Depends(get_admin_user)`
2. Set RLS context for cross-tenant queries

```python
@router.get("/users")
def list_users(_admin: dict = Depends(get_admin_user)):
    with db_conn() as (conn, cur):
        set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
        cur.execute("SELECT ... FROM users ...")
```

---

## 6. Frontend Implementation

### 6.1 Admin Layout Gate (`admin/layout.tsx`)

```typescript
async function verifyAdmin() {
  const api = await createServerApi()
  
  if (!api.isAuthenticated()) {
    return null  // Triggers redirect to /login?next=/admin
  }

  const { data, error } = await api.get<any>('/v1/me')
  
  if (error || !data) {
    return null
  }

  // Check platform admin flag (NOT tenant role)
  if (!data.is_platform_admin) {
    return null  // Triggers redirect to /access-denied
  }
  
  return data
}
```

### 6.2 Users Page — Display BOTH Roles

The `/admin/users` page shows:

| Column | Source | Display |
|--------|--------|---------|
| Platform Admin | `users.is_platform_admin` | Badge: "Yes" with shield icon |
| Tenant Role | `account_users.role` | Badge: "OWNER", "ADMIN", "MEMBER" |

This prevents confusion between platform and tenant permissions.

---

## 7. Dashboard Features

### 7.1 Primary KPIs

- **Total Accounts**: Count of all accounts (regular + affiliate)
- **Total Users**: Count of all registered users
- **Reports (7d)**: Reports generated in last 7 days
- **Error Rate**: Percentage of failed reports (7d)

### 7.2 Secondary KPIs

- Completed reports (7d)
- Currently processing
- Pending in queue
- Average render time

### 7.3 Pages Reference

| Page | Path | Purpose |
|------|------|---------|
| **Login** | `/admin/login` | Dedicated admin login (public) |
| Dashboard | `/admin` | KPIs and recent activity |
| Accounts | `/admin/accounts` | All accounts with plans and user counts |
| Users | `/admin/users` | All users with platform admin + tenant roles |
| Affiliates | `/admin/affiliates` | Title company management |
| **Schedules** | `/admin/schedules` | All automated schedules (pause/resume) |
| Plans | `/admin/plans` | Subscription plan configuration |
| Reports | `/admin/reports` | Report generation monitoring |
| Emails | `/admin/emails` | Email delivery logs |
| Settings | `/admin/settings` | System health, integrations, stats |

### 7.4 Sidebar Features

- **Navigation**: All protected pages accessible from sidebar
- **User Info**: Shows admin name and email
- **Log Out**: Logs out and redirects to `/admin/login`

---

## 8. Troubleshooting

### 8.1 "Access Denied" When User Should Have Access

1. **Verify `is_platform_admin` flag** (not tenant role):
   ```sql
   SELECT email, is_platform_admin FROM users WHERE email = 'user@example.com';
   ```

2. **Grant platform admin**:
   ```sql
   UPDATE users SET is_platform_admin = TRUE WHERE email = 'user@example.com';
   ```

3. **User must log out and back in** to refresh JWT

### 8.2 Dashboard Shows Zeros

1. **Check Render logs** for database errors
2. **Verify RLS bypass** is working:
   ```sql
   SELECT tablename, policyname FROM pg_policies 
   WHERE policyname LIKE '%admin%';
   ```
3. **Ensure admin.py sets RLS context**:
   ```python
   set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
   ```

### 8.3 Common Column Mismatches

| Code References | Actual Column |
|-----------------|---------------|
| `r.params` | `r.input_params` |
| `created_at` (report_generations) | `generated_at` |
| `started_at`, `finished_at` | `processing_time_ms` |
| `u.last_login_at` | *(doesn't exist)* |
| `plans.id` | `plans.plan_slug` |

### 8.4 API Calls Failing (401/403)

1. Check `mr_token` cookie is being forwarded
2. Verify JWT hasn't expired (default 1 hour)
3. Ensure user has `is_platform_admin = TRUE`

---

## 9. Verification Checklist

### A) Platform Admin Access Works
- [ ] `is_platform_admin = TRUE` for ops user
- [ ] Log in with admin credentials
- [ ] `/admin` loads successfully
- [ ] `/v1/admin/metrics` returns real data

### B) Tenant Admin is Blocked from /admin
- [ ] Log in as tenant user with `account_users.role = ADMIN`
- [ ] `/admin` redirects to `/access-denied`

### C) Tenant Permissions Still Work
- [ ] In `/app`, tenant roles behave correctly
- [ ] OWNER can manage billing, users, branding
- [ ] MEMBER can generate reports

---

## 10. Security Considerations

1. **Separation of concerns**: Platform admin ≠ Tenant admin
2. **Server-side verification**: Layout verifies `is_platform_admin` before rendering
3. **API protection**: All `/v1/admin/*` endpoints require platform admin
4. **Cookie-based auth**: JWT stored in httpOnly cookie
5. **RLS bypass**: Only admin endpoints bypass RLS, with explicit context setting

---

## 11. One-Liner Rule (Sticky Note)

> **Tenant role** lives in `account_users.role`.  
> **Platform admin** lives in `users.is_platform_admin`.  
> If you mix them, you'll ship a security bug.

---

---

## 12. Admin Actions Reference

### 12.1 User Management Actions

| Action | API Endpoint | Description |
|--------|--------------|-------------|
| Activate User | `PATCH /v1/admin/users/{id}?is_active=true` | Enable user login |
| Deactivate User | `PATCH /v1/admin/users/{id}?is_active=false` | Disable user login |
| Verify Email | `PATCH /v1/admin/users/{id}?email_verified=true` | Mark email as verified |
| Grant Platform Admin | `PATCH /v1/admin/users/{id}?is_platform_admin=true` | Grant /admin access |
| Revoke Platform Admin | `PATCH /v1/admin/users/{id}?is_platform_admin=false` | Remove /admin access |
| Force Password Reset | `POST /v1/admin/users/{id}/force-password-reset` | Send password reset email |
| Resend Invite | `POST /v1/admin/users/{id}/resend-invite` | Resend welcome email |

### 12.2 Schedule Management Actions

| Action | API Endpoint | Description |
|--------|--------------|-------------|
| Pause Schedule | `PATCH /v1/admin/schedules/{id}?active=false` | Stop schedule from running |
| Resume Schedule | `PATCH /v1/admin/schedules/{id}?active=true` | Reactivate schedule |
| List All Schedules | `GET /v1/admin/schedules` | View all schedules with filters |

### 12.3 Account Management Actions

| Action | API Endpoint | Description |
|--------|--------------|-------------|
| Change Plan | `PATCH /v1/admin/accounts/{id}?plan_slug=pro` | Update account plan |
| Set Limit Override | `PATCH /v1/admin/accounts/{id}?monthly_report_limit_override=500` | Custom report limit |
| Trigger Report | `POST /v1/admin/accounts/{id}/trigger-report` | Manually generate report |

### 12.4 System Monitoring

| Endpoint | Description |
|----------|-------------|
| `GET /v1/admin/system/health` | Live health check (DB, Redis, Worker) |
| `GET /v1/admin/metrics` | Dashboard KPIs |
| `GET /v1/admin/metrics/timeseries` | Charts data |
| `GET /v1/admin/stats/revenue` | Revenue & growth stats |

---

## 13. API Proxy Routes

All admin API calls go through Next.js proxy routes at `/api/v1/admin/*`:

```
/api/v1/admin/metrics           → /v1/admin/metrics
/api/v1/admin/accounts          → /v1/admin/accounts
/api/v1/admin/accounts/[id]     → /v1/admin/accounts/{id}
/api/v1/admin/users             → /v1/admin/users
/api/v1/admin/users/[id]        → /v1/admin/users/{id}
/api/v1/admin/users/[id]/force-password-reset
/api/v1/admin/users/[id]/resend-invite
/api/v1/admin/schedules         → /v1/admin/schedules
/api/v1/admin/schedules/[id]    → /v1/admin/schedules/{id}
/api/v1/admin/affiliates        → /v1/admin/affiliates
/api/v1/admin/reports           → /v1/admin/reports
/api/v1/admin/emails            → /v1/admin/emails
/api/v1/admin/plans             → /v1/admin/plans
/api/v1/admin/system/health     → /v1/admin/system/health
```

---

## Related Documentation

- [User Onboarding](./USER_ONBOARDING.md) - User setup flow
- [Account Settings](./ACCOUNT_SETTINGS.md) - User account management
- [Branding](./BRANDING.md) - White-label branding system
- [Email System](./EMAIL_SYSTEM.md) - Email delivery infrastructure
- [Title Company Onboarding](./TITLE_COMPANY_ONBOARDING.md) - Affiliate setup
- [Schedules](./SCHEDULES.md) - Scheduling system documentation
