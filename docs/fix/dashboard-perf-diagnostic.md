# DIAGNOSTIC: Dashboard First-Load Performance — Find the Bottleneck

## The Problem
First dashboard load takes ~10 seconds. Subsequent navigation is faster. Other Next.js sites on the same stack don't have this issue. We need to find and fix the root cause, not add more band-aids.

## Step 1: Trace the FULL Request Chain

Read these files and map every single external fetch() call that executes when a user navigates to `/app` (the dashboard). Document them IN ORDER of execution.

### Files to trace (in execution order):

```
1. apps/web/src/middleware.ts              ← Runs FIRST on every request
2. apps/web/src/app/app/layout.tsx         ← Runs SECOND (server component)
3. apps/web/src/app/app/page.tsx           ← Runs THIRD (server component)
4. apps/web/src/lib/api-server.ts          ← The server-side fetch wrapper
5. apps/web/src/lib/api.ts                 ← Client-side fetch (if any)
```

For EACH file, document:
- Every `fetch()`, `api.get()`, `api.post()`, or `createServerApi()` call
- The exact URL being called (e.g., `/v1/me`, `/v1/usage`)
- Whether it's `await`ed (blocking) or fired in parallel
- Any timeout configuration
- Any error handling / fallback behavior

**Output format:**
```
REQUEST CHAIN FOR GET /app:

1. middleware.ts
   └─ BLOCKING: GET {API_BASE}/v1/me (timeout: 5s)
   └─ Purpose: Check if user is admin
   └─ On failure: ???

2. layout.tsx  
   └─ BLOCKING: GET {API_BASE}/v1/me (timeout: 5s)
   └─ Purpose: Get user profile for sidebar
   └─ On failure: ???

3. page.tsx
   └─ BLOCKING: GET {API_BASE}/v1/usage (timeout: ???)
   └─ BLOCKING: GET {API_BASE}/v1/account/plan-usage (timeout: ???)
   └─ PARALLEL or SEQUENTIAL? ???
   └─ On failure: ???
```

## Step 2: Identify the Bottleneck

Based on the trace above, answer:

1. **How many total API calls** are made before the user sees the dashboard?
2. **Are any redundant?** (e.g., `/v1/me` called twice — once in middleware, once in layout)
3. **Are page.tsx calls sequential or parallel?** (Are they individual `await` calls, or `Promise.all()`?)
4. **Does middleware make an external API call?** This is the #1 suspect. Most Next.js middleware only reads cookies locally — calling an external API from middleware blocks the ENTIRE request.
5. **What is the Render API base URL?** Is it `https://something.onrender.com`? Render Starter plans spin down after inactivity, causing 5-10 second cold starts on the first request.

## Step 3: Implement the Fix

Based on what you find, apply these fixes IN ORDER:

### Fix 3A: Remove API Calls from Middleware (HIGHEST IMPACT)

Middleware should ONLY check the `mr_token` cookie locally — never call an external API. If middleware is currently calling `/v1/me` to check admin role, refactor it:

**Before (slow):**
```typescript
// middleware.ts — DON'T DO THIS
export async function middleware(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  if (!token) return redirect('/login');
  
  // THIS IS THE KILLER — external API call in middleware
  const res = await fetch(`${API_BASE}/v1/me`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const user = await res.json();
  
  if (request.nextUrl.pathname.startsWith('/app/admin') && user.role !== 'ADMIN') {
    return redirect('/app');
  }
}
```

**After (fast):**
```typescript
// middleware.ts — JUST CHECK THE COOKIE
import { jwtDecode } from 'jwt-decode'; // or use jose for edge-compatible JWT

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('mr_token')?.value;
  
  // No token → login
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Decode JWT locally (NO external API call)
  try {
    const decoded = jwtDecode<{ role: string; account_id: string; exp: number }>(token);
    
    // Check expiry
    if (decoded.exp * 1000 < Date.now()) {
      const response = NextResponse.redirect(new URL('/login', request.url));
      response.cookies.delete('mr_token');
      return response;
    }

    // Admin route protection — check role from JWT payload directly
    if (request.nextUrl.pathname.startsWith('/app/admin') && decoded.role !== 'ADMIN') {
      return NextResponse.redirect(new URL('/app', request.url));
    }

    // INDUSTRY_AFFILIATE redirect
    // NOTE: If account_type is in the JWT payload, check it here.
    // If not, let the layout/page handle this redirect instead.

    return NextResponse.next();
  } catch {
    // Invalid token → login
    const response = NextResponse.redirect(new URL('/login', request.url));
    response.cookies.delete('mr_token');
    return response;
  }
}
```

**IMPORTANT:** Install `jwt-decode` (lightweight, edge-compatible):
```bash
cd apps/web && npm install jwt-decode
```

If the JWT doesn't include `role` in the payload, check the API code at `apps/api/src/api/routes/auth.py` — the JWT payload likely has `role`, `account_id`, and `user_id`. If `account_type` is NOT in the JWT but is needed for the affiliate redirect, either:
- Add `account_type` to the JWT payload on the API side, OR
- Move the affiliate redirect logic to the layout/page (where you're already fetching `/v1/me`)

### Fix 3B: Deduplicate /v1/me Calls

If both `layout.tsx` and `page.tsx` call `/v1/me`, the layout should fetch it once and pass it down via context or props. Next.js 14+ deduplicates identical fetch calls within a single render, but ONLY if the URL and options are identical. Verify this is happening.

**Option A: Rely on Next.js fetch dedup** (if using native fetch with same URL)
```typescript
// layout.tsx
const user = await api.get('/v1/me'); // fetch #1

// page.tsx  
const user = await api.get('/v1/me'); // Next.js deduplicates this — same request, zero cost
```

**Option B: Explicit context passing** (more reliable)
```typescript
// layout.tsx
export default async function AppLayout({ children }) {
  const user = await getUser(); // single fetch
  return (
    <UserProvider value={user}>
      <Sidebar user={user} />
      {children}
    </UserProvider>
  );
}

// page.tsx — reads from context, no duplicate fetch
```

### Fix 3C: Parallelize Dashboard API Calls

If `page.tsx` makes multiple API calls sequentially:

**Before (slow):**
```typescript
const usage = await api.get('/v1/usage');           // waits...
const plan = await api.get('/v1/account/plan-usage'); // waits...
const onboarding = await api.get('/v1/onboarding'); // waits...
// Total: sum of all three response times
```

**After (fast):**
```typescript
const [usage, plan, onboarding] = await Promise.all([
  api.get('/v1/usage'),
  api.get('/v1/account/plan-usage'),
  api.get('/v1/onboarding'),
]);
// Total: max of the three response times (they run in parallel)
```

### Fix 3D: Add Timing Instrumentation (Temporary)

Add console.time markers to see exactly where time is spent. This is temporary — remove after diagnosis.

```typescript
// In layout.tsx
export default async function AppLayout({ children }) {
  console.time('[PERF] layout-fetch-user');
  const user = await getUser();
  console.timeEnd('[PERF] layout-fetch-user');
  // ...
}

// In page.tsx
export default async function DashboardPage() {
  console.time('[PERF] dashboard-fetch-all');
  const [usage, plan, onboarding] = await Promise.all([
    api.get('/v1/usage'),
    api.get('/v1/account/plan-usage'),
    api.get('/v1/onboarding'),
  ]);
  console.timeEnd('[PERF] dashboard-fetch-all');
  // ...
}
```

Check these timings in the **Vercel function logs** (not the browser console — these are server-side).

## Step 4: Verify the JWT Payload

Read `apps/api/src/api/routes/auth.py` and find the JWT token creation. Document every field in the payload:

```python
# What fields are in the JWT?
payload = {
    "user_id": ???,
    "account_id": ???,
    "role": ???,         # Need this for admin check in middleware
    "account_type": ???, # Need this for affiliate redirect (if present)
    "exp": ???,
}
```

If `role` is NOT in the JWT payload, add it. If `account_type` is needed for the affiliate redirect in middleware, add that too. This is a one-line change on the API side that eliminates an entire API call from middleware.

## Step 5: Verify the Keep-Alive (If Implemented)

Check if a keep-alive task exists in:
- `apps/worker/src/worker/celery_app.py` (beat schedule)
- `apps/worker/src/worker/tasks.py` (ping task)

If a keep-alive task pings `GET /health` on the API every 5 minutes via Celery Beat, Render should stay warm and cold starts shouldn't happen. If this ISN'T implemented yet, note that — but it's a band-aid. The middleware fix (Step 3A) is the real solution because it eliminates the dependency on API warmth for the critical path.

## Expected Outcome

After these fixes, the request chain should be:

```
User hits /app
  └─ middleware.ts ──── JWT decode locally ──── <1ms ✅
     └─ layout.tsx ──── GET /v1/me ──────────── 0.2-0.5s (even if cold, only ONE call wakes it)
        └─ page.tsx ─── Promise.all([3 calls]) ─ 0.3s (parallel, API already warm)
                                                 ≈ 0.5-1.0s total
```

That's a 10x improvement: from ~10 seconds to ~1 second.

## Summary Checklist

- [ ] Traced all fetch() calls in middleware → layout → page chain
- [ ] Confirmed whether middleware makes external API calls (THE #1 SUSPECT)
- [ ] Verified JWT payload contains `role` (and `account_type` if needed)
- [ ] Removed API calls from middleware — use local JWT decode instead
- [ ] Deduplicated `/v1/me` calls between layout and page
- [ ] Parallelized dashboard data fetches with Promise.all()
- [ ] Added timing instrumentation to verify improvement
- [ ] Checked if keep-alive task exists (nice-to-have, not the fix)
