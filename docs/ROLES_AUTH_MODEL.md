# Roles & Authorization Model — TrendyReports (Source of Truth)

**Purpose:** Prevent role confusion by separating **platform admin access** (system-wide `/admin`) from **tenant membership roles** (OWNER/ADMIN/MEMBER inside an Account).

This doc is written to be **Cursor-executable**: implement in order, don’t freestyle.

---

## 0) Definitions (Do Not Mix)

### A) Account (Tenant / Customer)
- Represents a company/org **or** an individual tenant.
- Has: `account_type`, `plan_slug`, `sponsor_account_id`
- Types:
  - `REGULAR`
  - `INDUSTRY_AFFILIATE`
- Plans:
  - `free`, `solo` (pro), `team`, `affiliate`, `sponsored_free`

### B) User (Person / Login)
- Represents a human identity with email/password.
- Belongs to exactly **one** Account in the current product model.

### C) Membership (User-in-Account)
- Stored in `account_users`.
- The **only** place where `OWNER | ADMIN | MEMBER` belongs.

---

## 1) Sources of Truth

### 1.1 Tenant membership roles (Account-level)
- **Table:** `account_users`
- **Field:** `account_users.role`
- **Values:** `OWNER | ADMIN | MEMBER`

Used for:
- Permissions inside `/app`
- Managing tenant things (branding, people, schedules, reports)
- Account-level team permissions

### 1.2 Platform admin permission (System-wide)
- **Table:** `users`
- **Field:** `users.is_platform_admin` (BOOLEAN)

Used ONLY for:
- Access to `/admin`
- Ability to call `/v1/admin/*`
- System-wide actions (all accounts/users visibility)

**Rule:** Platform admin is ops/staff — not a tenant role.

---

## 2) Database Migration (Do This First)

### 2.1 Add `is_platform_admin`
```sql
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE;
```

### 2.2 Backfill ops/admin user(s)
```sql
UPDATE users
SET is_platform_admin = TRUE
WHERE email = 'admin@yourcompany.com';
```

### 2.3 Deprecate `users.role` (If currently used)
If your code uses `users.role = 'ADMIN'` to gate `/admin`, treat that as deprecated immediately.
Leave the column in place if needed for backward compatibility, but stop using it for auth checks.

---

## 3) Backend Authorization (FastAPI)

### 3.1 Create dependency: `get_platform_admin_user`
**File suggestion:** `apps/api/src/api/deps/platform_admin.py`

Behavior:
1. Read authenticated user from `request.state.user`
2. Require `is_platform_admin == True`
3. If not authenticated → 401
4. If not platform admin → 403

Example:
```python
from fastapi import HTTPException, Request

def get_platform_admin_user(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.get("is_platform_admin", False):
        raise HTTPException(status_code=403, detail="Platform admin only")
    return user
```

### 3.2 Gate ALL admin routes with the dependency
All `/v1/admin/*` endpoints must use:
```python
_admin = Depends(get_platform_admin_user)
```

Example:
```python
@router.get("/v1/admin/metrics")
def admin_metrics(_admin = Depends(get_platform_admin_user)):
    ...
```

### 3.3 Ensure admin endpoints set RLS context correctly
Admin routes query across tenants, so they must explicitly set RLS context to bypass tenant filters.

Pattern:
- Call your `set_rls(...)` helper with an admin bypass mode before SELECTs.

Example:
```python
with db_conn() as (conn, cur):
    set_rls(cur, _admin.get("account_id", ""), user_role="ADMIN")
    cur.execute("SELECT ...")
```

### 3.4 RLS policies must include an admin bypass
If any admin endpoints return “all zeros” or empty sets, RLS is likely filtering.
Ensure your policies include a clause like:
```sql
OR current_setting('app.current_user_role', true) = 'ADMIN'
```

---

## 4) Frontend Authorization (Next.js Admin App)

### 4.1 `/admin/layout.tsx` gate (Server Component)
Rules:
1. No auth → redirect to `/login?next=/admin`
2. Auth but not platform admin → redirect `/access-denied`
3. Platform admin → render admin UI

Implementation:
- Ensure `/v1/me` returns `is_platform_admin` in its payload.
- Layout checks the boolean.

Pseudo:
```ts
const me = await api.get("/v1/me")
if (!me) redirect("/login?next=/admin")
if (!me.is_platform_admin) redirect("/access-denied")
return <AdminLayout />
```

### 4.2 Do NOT use tenant role for `/admin` access
Never gate `/admin` using:
- `account_users.role == ADMIN`
- OR any “admin” inside account context

Platform admin access is separate.

---

## 5) Tenant Permissions (OWNER / ADMIN / MEMBER)

### 5.1 Read from `account_users.role`
Any permission checks inside `/app` should use:
- `account_users.role`

### 5.2 Recommended default policy (simple)
- `OWNER`: full control (billing, branding, users, schedules)
- `ADMIN`: full control except billing/plan changes (optional rule)
- `MEMBER`: can generate reports & schedules; cannot manage users/billing

Keep it simple unless you need more.

---

## 6) Affiliate / Sponsored Accounts (No New “User Type”)

### 6.1 Affiliate (Title/Lender) is an Account
- `accounts.account_type = INDUSTRY_AFFILIATE`
- `accounts.plan_slug = affiliate`

### 6.2 Sponsored agent is an Account
- `accounts.account_type = REGULAR`
- `accounts.plan_slug = sponsored_free`
- `accounts.sponsor_account_id = <affiliate_account_id>`

Branding resolution uses the sponsor relationship and is not a role system.

---

## 7) Admin Console: Users Page — Required UX Clarity

On `/admin/users`, show BOTH:
1. **Platform Admin:** `users.is_platform_admin` (Yes/No)
2. **Tenant Role:** `account_users.role` (OWNER/ADMIN/MEMBER)

Never show a single “Role” label without specifying which one it is.

---

## 8) Verification Checklist (Fast)

### A) Platform admin access works
- Set `is_platform_admin = true` for your ops user
- Log in
- `/admin` loads
- `/v1/admin/metrics` returns real data

### B) Tenant admin is blocked from `/admin`
- Log in as a tenant user with `account_users.role = ADMIN`
- `/admin` redirects to `/access-denied`

### C) Tenant permissions still work
- In `/app`, tenant roles behave correctly based on `account_users.role`

---

## 9) One-liner rule (Sticky Note)

> **Tenant role** lives in `account_users.role`.  
> **Platform admin** lives in `users.is_platform_admin`.  
> If you mix them, you’ll ship a security bug.
