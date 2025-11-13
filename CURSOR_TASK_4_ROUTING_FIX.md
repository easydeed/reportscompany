# Task 4: Fix /app Routing (404 Issue)

**Estimated Time:** 30 minutes  
**Priority:** HIGH  
**Dependencies:** None

---

## 🎯 Goal

Fix 404 errors for `/app/*` routes on Vercel production deployment.

**Current State:**
- ✅ `https://reportscompany-web.vercel.app/` - Marketing site works
- ❌ `https://reportscompany-web.vercel.app/app` - 404 Not Found
- ❌ `https://reportscompany-web.vercel.app/app/schedules` - 404 Not Found

**Target State:**
- ✅ `/app` loads dark dashboard shell
- ✅ `/app/schedules` loads schedules list page
- ✅ `/app/schedules/new` loads schedule creation form
- ✅ `/app/schedules/[id]` loads schedule detail page

---

## 🔍 Root Cause Analysis

Possible causes for /app 404s:
1. Routes not built by Next.js
2. Middleware redirecting/blocking routes
3. Route group misconfiguration
4. Missing layout files
5. Vercel configuration issue

---

## 📂 Files to Investigate

### 1. Verify Route Structure

**Check directory structure:**
```
apps/web/app/
├── layout.tsx                    # Root layout
├── (marketing)/                  # Marketing route group
│   ├── page.tsx                 # Homepage (/)
│   └── ...
├── (app)/                        # App route group (optional)
│   └── app-layout.tsx           # Or direct app/ folder
└── app/                          # Dashboard routes
    ├── layout.tsx               # App shell layout
    ├── page.tsx                 # Dashboard home (/app)
    └── schedules/
        ├── page.tsx             # List (/app/schedules)
        ├── new/
        │   └── page.tsx         # Create (/app/schedules/new)
        └── [id]/
            └── page.tsx         # Detail (/app/schedules/[id])
```

**Required action:** Run this check:
```bash
cd apps/web
find app -name "page.tsx" -o -name "layout.tsx" | sort
```

Expected output should include:
```
app/app/layout.tsx
app/app/page.tsx
app/app/schedules/page.tsx
app/app/schedules/new/page.tsx
app/app/schedules/[id]/page.tsx
```

**If missing:** Create the missing files with minimal content.

---

### 2. Check Next.js Configuration

**File:** `apps/web/next.config.mjs`

**Look for problematic settings:**

```javascript
// BAD - These can break App Router
export default {
  output: 'export',           // ❌ Disables SSR
  trailingSlash: true,        // ⚠️  Can cause issues
  basePath: '/something',     // ⚠️  Unless intentional
}

// GOOD - Basic config
export default {
  reactStrictMode: true,
  transpilePackages: ['@repo/ui'],  // For monorepo
  // No output or basePath
}
```

**Required changes:**
1. Remove `output: 'export'` if present (breaks SSR)
2. Remove any `rewrites` or `redirects` that affect `/app/*`
3. Ensure no `exportPathMap` (deprecated with App Router)

---

### 3. Check Middleware

**File:** `apps/web/middleware.ts` (if exists)

**Common issue - middleware blocking /app routes:**

```typescript
// BAD - Redirects all /app to /
export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/app')) {
    return NextResponse.redirect(new URL('/', request.url));  // ❌
  }
}

// GOOD - Allow /app routes
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Only redirect if NOT authenticated (example logic)
  if (pathname.startsWith('/app') && !request.cookies.get('auth_token')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Otherwise, allow
  return NextResponse.next();
}

// IMPORTANT: Configure matcher to avoid static files
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)',
  ],
};
```

**Required changes:**
1. Ensure middleware doesn't block `/app/*` unintentionally
2. Add proper matcher to exclude static files
3. If auth check needed, make it conditional

---

### 4. Check Layout Files

**File:** `apps/web/app/layout.tsx` (Root Layout)

**Must include:**
```typescript
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

**File:** `apps/web/app/app/layout.tsx` (App Shell Layout)

**Must exist and render children:**
```typescript
export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="dark">  {/* Apply dark theme to dashboard */}
      <div className="min-h-screen bg-slate-900">
        {/* Navigation, sidebar, etc. */}
        <main>{children}</main>
      </div>
    </div>
  );
}
```

**Required action:** Verify these files exist and render children properly.

---

### 5. Check Build Output

**Run local build:**
```bash
cd apps/web
pnpm build
```

**Check for errors:**
- Look for: "Error: Route /app not found"
- Look for: TypeScript errors in app/ pages
- Look for: Missing dependencies

**Check build output:**
```bash
# After build, check .next/server/app/
ls -la .next/server/app/app/
```

Expected to see:
```
page.js
layout.js
schedules/
  page.js
  [id]/
    page.js
  new/
    page.js
```

If these don't exist, the routes aren't being built.

---

## 🛠️ Common Fixes

### Fix 1: Missing Route Files

If `/app/schedules/page.tsx` is missing:

```bash
mkdir -p apps/web/app/app/schedules
```

**Create minimal page:**
```typescript
// apps/web/app/app/schedules/page.tsx
export default function SchedulesPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Schedules</h1>
      <p>Schedules list will go here</p>
    </div>
  );
}
```

### Fix 2: Middleware Blocking Routes

**Option A: Allow /app routes in middleware:**
```typescript
export function middleware(request: NextRequest) {
  // Don't redirect /app routes
  if (request.nextUrl.pathname.startsWith('/app')) {
    return NextResponse.next();
  }
  // ... other logic
}
```

**Option B: Remove middleware if not needed:**
```bash
# If middleware isn't doing anything critical
rm apps/web/middleware.ts
```

### Fix 3: Route Group Issue

If you have `app/(app)/`:
```bash
# Move contents out of route group
mv apps/web/app/\(app\)/app apps/web/app/app
rmdir apps/web/app/\(app\)
```

### Fix 4: next.config.mjs Issues

**Remove problematic exports:**
```javascript
// apps/web/next.config.mjs
export default {
  reactStrictMode: true,
  // Remove: output: 'export'
  // Remove: basePath
  transpilePackages: ['@repo/ui'],
};
```

---

## ✅ Acceptance Criteria

### Local Testing
- [ ] `pnpm --filter web dev` starts without errors
- [ ] Visit `http://localhost:3000/app` - loads dashboard
- [ ] Visit `http://localhost:3000/app/schedules` - loads schedules page
- [ ] No console errors in browser
- [ ] `pnpm --filter web build` succeeds

### Production (After Deploy)
- [ ] `https://reportscompany-web.vercel.app/app` - loads (not 404)
- [ ] `https://reportscompany-web.vercel.app/app/schedules` - loads (not 404)
- [ ] Dark theme applied to dashboard routes
- [ ] Light theme on marketing routes (/)

### Build Output
- [ ] `.next/server/app/app/` directory exists after build
- [ ] Contains page.js, layout.js, and schedules/ subdirectory
- [ ] No build errors or warnings about missing routes

---

## 🧪 Testing Instructions

### Test 1: Local Development
```bash
cd apps/web
pnpm dev
```

Open browser:
- `http://localhost:3000/` - Should show marketing site (light mode)
- `http://localhost:3000/app` - Should show dashboard (dark mode)
- `http://localhost:3000/app/schedules` - Should show schedules list

Check browser console - no 404 errors for routes.

### Test 2: Local Build
```bash
cd apps/web
pnpm build
pnpm start
```

Test same URLs as above. Build should succeed with no errors.

### Test 3: Production (After Deploy)
```bash
# After pushing changes and Vercel deploys
open https://reportscompany-web.vercel.app/app
open https://reportscompany-web.vercel.app/app/schedules
```

Both should load successfully, no 404.

---

## 🚨 Common Pitfalls

1. **Route group confusion**
   - `(app)` creates a route group that doesn't add to URL
   - URL path is based on folder name, not group name

2. **Forgot to export default**
   - Every page.tsx MUST have `export default function`

3. **Missing layout.tsx**
   - Layouts are optional but recommended
   - Missing layout can cause hydration issues

4. **Middleware blocking everything**
   - Always test middleware logic carefully
   - Use matcher to exclude static files

5. **Build cache issues**
   - Clear `.next/` folder if routes still missing after fixes
   - `rm -rf .next && pnpm build`

---

## 📝 Commit Message

```
fix(web): resolve /app routing 404 issues on production

- Verify all /app route files exist (page.tsx, layout.tsx)
- Fix next.config.mjs (remove output: export if present)
- Update middleware to allow /app routes
- Ensure route groups configured correctly
- Verify build includes all dashboard routes

Issue: /app and /app/schedules return 404 on Vercel
Fix: Correct Next.js App Router configuration
```

---

**After completing this task, verify routes work locally before deploying to Vercel.**

