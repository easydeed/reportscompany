# Authentication Architecture V1

**Last Updated:** November 14, 2025  
**Purpose:** Document the authentication contract to prevent regressions and establish clear ownership

---

## Identity & Tokens

### The `mr_token` Cookie

- **`mr_token` is the ONLY auth token** used by the web app
- It is a **JWT issued by `/v1/auth/login`** and stored as an **HttpOnly cookie**
- **Expires:** 1 hour (login) or 7 days (invite acceptance)
- **Format:** JWT with claims: `sub`, `user_id`, `account_id`, `scopes`

### Token Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User logs in                                             │
│    POST /v1/auth/login { email, password }                  │
│    ↓                                                         │
│ 2. Backend validates credentials                            │
│    ↓                                                         │
│ 3. Backend signs JWT with JWT_SECRET                        │
│    token = sign_jwt({ sub, user_id, account_id, scopes })  │
│    ↓                                                         │
│ 4. Backend sets HTTP-only cookie                            │
│    response.set_cookie("mr_token", token, httponly=True)    │
│    ↓                                                         │
│ 5. Browser stores cookie automatically                      │
│    ↓                                                         │
│ 6. All subsequent requests include mr_token cookie          │
└─────────────────────────────────────────────────────────────┘
```

---

## Who Owns What

### Backend (API) Responsibilities

The **FastAPI backend** (`apps/api`) is the **ONLY** place that:
- **Signs JWTs** using `JWT_SECRET`
- **Verifies JWTs** using `JWT_SECRET`
- **Sets the `mr_token` cookie** via `Set-Cookie` header
- **Validates token expiration** and structure

**Key Files:**
- `apps/api/src/api/routes/auth.py` - Login, invite acceptance
- `apps/api/src/api/auth.py` - JWT signing and verification
- `apps/api/src/api/middleware/authn.py` - Authentication middleware

### Frontend Responsibilities

The **Next.js frontend** (`apps/web`):
- **NEVER writes** or overwrites `document.cookie` for `mr_token`
- **NEVER signs** or verifies JWTs
- **Uses proxy routes** (`apps/web/app/api/proxy/**`) to forward authenticated requests
- **Relies on browser** to automatically send cookies with `credentials: 'include'`

**Key Pattern:**
```typescript
// ✅ CORRECT: Frontend calls proxy, proxy forwards cookie
const response = await fetch('/api/proxy/v1/account/plan-usage', {
  credentials: 'include',  // Browser sends mr_token automatically
});

// ❌ WRONG: Frontend manipulates cookie directly
document.cookie = `mr_token=${token}`;  // NEVER DO THIS
```

### Proxy Routes Pattern

**Purpose:** Proxy routes (`apps/web/app/api/proxy/v1/**`) bridge frontend and backend:

1. **Receive requests** from frontend (browser context)
2. **Forward cookies** to backend API
3. **Optionally translate** `cookie` header to `Authorization: Bearer` if needed
4. **Return backend response** to frontend

**Example:** `apps/web/app/api/proxy/v1/account/plan-usage/route.ts`
```typescript
export async function GET(request: NextRequest) {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com';
  
  // Forward cookie to backend
  const cookieHeader = request.headers.get('cookie') || '';
  
  const response = await fetch(`${API_BASE}/v1/account/plan-usage`, {
    headers: { cookie: cookieHeader },
    cache: 'no-store',
  });
  
  return NextResponse.json(await response.json(), { status: response.status });
}
```

---

## Authentication Flows

### Flow 1: Login

```
┌──────────┐         ┌─────────────────┐         ┌─────────────┐
│ Browser  │         │ Next.js Proxy   │         │ FastAPI API │
└──────────┘         └─────────────────┘         └─────────────┘
     │                        │                          │
     │  POST /login           │                          │
     │  (email, password)     │                          │
     ├────────────────────────>                          │
     │                        │                          │
     │           POST /api/proxy/v1/auth/login           │
     │                        ├─────────────────────────>│
     │                        │                          │
     │                        │    Validate credentials  │
     │                        │    Sign JWT              │
     │                        │    Set-Cookie: mr_token  │
     │                        │<─────────────────────────┤
     │                        │                          │
     │  Forward Set-Cookie    │                          │
     │<────────────────────────                          │
     │                        │                          │
     │  (Cookie stored)       │                          │
     └────────────────────────┴──────────────────────────┘
```

**Key Points:**
- Backend issues JWT and sets cookie via `Set-Cookie` header
- Proxy forwards `Set-Cookie` to browser (same-origin context)
- Browser stores cookie automatically
- Frontend never touches the cookie value

### Flow 2: Authenticated Request

```
┌──────────┐         ┌─────────────────┐         ┌─────────────┐
│ Browser  │         │ Next.js Proxy   │         │ FastAPI API │
└──────────┘         └─────────────────┘         └─────────────┘
     │                        │                          │
     │  GET /account/plan     │                          │
     │  Cookie: mr_token=...  │                          │
     ├────────────────────────>                          │
     │                        │                          │
     │           GET /api/proxy/v1/account/plan-usage    │
     │           Cookie: mr_token=...                    │
     │                        ├─────────────────────────>│
     │                        │                          │
     │                        │    Verify JWT            │
     │                        │    Extract account_id    │
     │                        │    set_rls(...)          │
     │                        │    Query data            │
     │                        │<─────────────────────────┤
     │                        │                          │
     │  Plan & usage data     │                          │
     │<────────────────────────                          │
     └────────────────────────┴──────────────────────────┘
```

**Key Points:**
- Browser automatically sends `mr_token` cookie
- Proxy forwards cookie to backend
- Backend verifies JWT and sets RLS context
- Response flows back through proxy

### Flow 3: Invite Acceptance

```
┌──────────┐         ┌─────────────────┐         ┌─────────────┐
│ Browser  │         │ Next.js Proxy   │         │ FastAPI API │
└──────────┘         └─────────────────┘         └─────────────┘
     │                        │                          │
     │  POST /welcome         │                          │
     │  (token, password)     │                          │
     ├────────────────────────>                          │
     │                        │                          │
     │           POST /api/proxy/v1/auth/accept-invite   │
     │                        ├─────────────────────────>│
     │                        │                          │
     │                        │    Validate token        │
     │                        │    Set password hash     │
     │                        │    Mark token used       │
     │                        │    Sign JWT (7 days)     │
     │                        │    Set-Cookie: mr_token  │
     │                        │<─────────────────────────┤
     │                        │                          │
     │  Forward Set-Cookie    │                          │
     │<────────────────────────                          │
     │                        │                          │
     │  Redirect to /app      │                          │
     └────────────────────────┴──────────────────────────┘
```

**Key Points:**
- Affiliate invites agent → `signup_tokens` row created
- Agent clicks link → `/welcome?token=...`
- Backend validates token, sets password, issues JWT (7 days TTL)
- Same cookie-setting pattern as login

---

## Verification & RLS

### Middleware: `authn.py`

The authentication middleware runs on **every API request** and:

1. **Extracts token** from:
   - `Authorization: Bearer <token>` header, OR
   - `mr_token` cookie (fallback)

2. **Verifies JWT** using `JWT_SECRET`:
   ```python
   claims = verify_jwt(token, settings.JWT_SECRET)
   ```

3. **Extracts context**:
   - `user_id` from `claims['user_id']`
   - `account_id` from `claims['account_id']`
   - `user_role` (if present)

4. **Sets RLS context** for PostgreSQL:
   ```python
   set_rls(cur, account_id, user_id, user_role)
   ```

### Row-Level Security (RLS)

All protected data queries **assume RLS is set** by middleware:

```sql
-- RLS session variables set by middleware:
SET LOCAL app.current_account_id = '<account_id>';
SET LOCAL app.current_user_id = '<user_id>';
SET LOCAL app.current_user_role = '<role>';

-- Queries automatically filter by current account:
SELECT * FROM reports WHERE account_id = current_setting('app.current_account_id')::uuid;
```

**Key Functions:**
- `get_brand_for_account(db, account_id)` - Assumes RLS set
- `evaluate_report_limit(cur, account_id)` - Assumes RLS set
- `get_monthly_usage(cur, account_id)` - Assumes RLS set

---

## Critical Lessons (Phase 29D Debugging)

### ❌ The Bug That Cost 6 Hours

**Problem:** Frontend was setting `mr_token=undefined` in cookie

**Root Cause:**
```typescript
// ❌ BAD: Frontend login code was doing this:
const data = await response.json();
document.cookie = `mr_token=${data.token}; ...`;  // data.token was undefined!
```

**Why it happened:**
- Backend returned `{ access_token: <jwt> }` (not `{ token: <jwt> }`)
- Frontend tried to read `data.token` → `undefined`
- Frontend overwrote cookie with literal string `"undefined"`

**The Fix:**
1. ✅ Backend sets cookie via `Set-Cookie` header
2. ✅ Frontend uses proxy route (same-origin for cookie)
3. ✅ Frontend NEVER manually sets `mr_token`

### ✅ The Correct Pattern

**Backend** (`apps/api/src/api/routes/auth.py`):
```python
@router.post("/auth/login")
def login(body: LoginIn, response: Response):
    # ... validate credentials ...
    token = sign_jwt({...}, settings.JWT_SECRET, ttl_seconds=3600)
    
    # ✅ Backend owns cookie setting
    response.set_cookie(
        key="mr_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    
    return {"access_token": token}  # Optional: for debugging
```

**Frontend** (`apps/web/app/login/page.tsx`):
```typescript
const res = await fetch("/api/proxy/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
  credentials: "include",  // ✅ Allow browser to accept Set-Cookie
});

// ✅ NO cookie manipulation here!
if (res.ok) {
  router.push("/app");  // Cookie already set by backend
}
```

---

## Security Checklist

### Production Requirements

- [ ] `JWT_SECRET` is set to a strong, random value (not `"dev-secret"`)
- [ ] `JWT_SECRET` is the **same value** on all API instances (Render services)
- [ ] Cookies use `httponly=True`, `secure=True`, `samesite="lax"`
- [ ] CORS `ALLOWED_ORIGINS` includes only trusted domains
- [ ] API keys are hashed before storage (`hash_api_key`)
- [ ] Passwords are hashed with bcrypt before storage

### Development vs Production

| Setting | Development | Production |
|---------|-------------|------------|
| `JWT_SECRET` | `"dev-secret"` (default) | `"mr-prod-jwt-secret-2024-..."` |
| `secure` cookie | `False` (http://localhost) | `True` (https://) |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | `["https://reportscompany-web.vercel.app", ...]` |
| Cookie `samesite` | `"lax"` | `"lax"` |

---

## Testing Auth Changes

When modifying authentication logic, **ALL** of these must pass:

### Backend Tests (pytest)
- `test_accept_invite_*` (all green)
- `test_plans_limits_*` (all green)

### Frontend Tests (Jest)
- `AccountSwitcher.test.tsx`
- `PlanPage.test.tsx`

### E2E Tests (Playwright)
- `auth.spec.ts` – login to `/app` works
- `plan.spec.ts` – `/account/plan` works after login
- `affiliate.spec.ts` – `/app/affiliate` works for affiliate
- (Optional) Invite E2E: invite → welcome → `/app`

**See:** `docs/AUTH_TEST_CHECKLIST.md` for full test matrix

---

## References

- **JWT Spec:** RFC 7519 (https://tools.ietf.org/html/rfc7519)
- **HTTP-only Cookies:** OWASP recommendations
- **Next.js Cookies:** https://nextjs.org/docs/app/api-reference/functions/cookies
- **FastAPI Responses:** https://fastapi.tiangolo.com/advanced/response-cookies/

---

**Status:** 🔒 Locked Contract  
**Last Tested:** November 14, 2025 (Phase 29D completion)

