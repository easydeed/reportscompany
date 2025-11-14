# Testing Blocked - Plan Page Investigation

**Date:** November 14, 2025  
**Issue:** Plan page consistently fails to load with "Failed to load plan information"

---

## 🎯 What We've Accomplished

### ✅ Completed Successfully
1. **Password Reset:** Test account credentials set and documented
2. **Authentication:** Login flow works perfectly
3. **Navigation:** Dashboard, Branding pages load correctly
4. **Deployments:** All code deployed to Render (API) and Vercel (Web)
5. **Stripe Config:** All environment variables set on Render

### ❌ Blocked
- **Plan & Usage Page:** Cannot load, blocking all Stripe testing

---

## 🔍 Problem Analysis

### Symptom
```
URL: /account/plan
Error: "Failed to load plan information"
```

### Root Cause Investigation

**Attempted Fixes:**
1. ✅ Added default `API_BASE` value → Still failed
2. ✅ Used proxy route → Still failed  
3. ✅ Improved error logging → Deployed, waiting for logs

**Hypothesis:**
Server component in Next.js is calling the API during SSR, but something in the authentication flow isn't working. Possible causes:
- Cookie not being extracted correctly in server component
- JWT token format issue
- API endpoint returning 401/500 (we saw 401 in logs earlier)
- CORS or networking issue between Vercel and Render

---

## 📊 Current Status

### Working Services
- ✅ **Render API:** https://reportscompany.onrender.com (LIVE)
- ✅ **Vercel Web:** https://reportscompany-web.vercel.app (READY)
- ✅ **Login:** Authentication successful
- ✅ **Dashboard:** Loads correctly
- ✅ **Branding:** Loads correctly

### Not Working
- ❌ **Plan Page:** `/account/plan` fails to load data

---

## 🔧 Next Steps

### Option 1: Check Vercel Logs (Recommended)
1. Go to: https://vercel.com/easydeeds-projects/reportscompany-web
2. Click on latest deployment
3. View "Function Logs" or "Runtime Logs"
4. Look for errors from `/account/plan`
5. Check what the actual error message is

### Option 2: Test API Endpoint Directly
Test if the API works when called with a valid token:

```bash
# 1. Get the JWT token from browser (after login)
# Open DevTools → Application → Cookies → mr_token

# 2. Test the API directly
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  https://reportscompany.onrender.com/v1/account/plan-usage
```

Expected response: JSON with plan data
If 401: Token is invalid or expired
If 500: Server error (check Render logs)

### Option 3: Simplify the Plan Page
Convert the plan page to a client component that fetches data client-side:

```typescript
'use client';

export default function PlanPage() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    fetch('/api/proxy/v1/account/plan-usage')
      .then(res => res.json())
      .then(setData);
  }, []);
  
  // render...
}
```

This would bypass SSR issues entirely.

### Option 4: Add Environment Variable on Vercel
Even though we added defaults, officially set it:
1. Go to: https://vercel.com/easydeeds-projects/reportscompany-web/settings/environment-variables
2. Add: `NEXT_PUBLIC_API_BASE` = `https://reportscompany.onrender.com`
3. Redeploy

---

## 🐛 Debug Checklist

- [ ] Check Vercel Function Logs for actual error
- [ ] Test API endpoint directly with curl
- [ ] Verify JWT token is valid (not expired)
- [ ] Check Render API logs for incoming requests
- [ ] Try converting to client component
- [ ] Set NEXT_PUBLIC_API_BASE environment variable
- [ ] Test with a fresh login (new session)

---

## 📝 Test Credentials (For Manual Testing)

**Account:**
- Email: `gerardoh@gmail.com`
- Password: `Test123456!`
- Account ID: `912014c3-6deb-4b40-a28d-489ef3923a3a`

**URLs:**
- Login: https://reportscompany-web.vercel.app/login
- Dashboard: https://reportscompany-web.vercel.app/app
- Plan Page: https://reportscompany-web.vercel.app/account/plan (BROKEN)

---

## 💡 Recommended Immediate Action

**For fastest resolution:**

1. **Check Vercel logs** (2 minutes)
   - See actual error message
   - Determine if it's token, API, or network issue

2. **Test API directly** (2 minutes)
   - Confirms if API endpoint works
   - Isolates problem to frontend or backend

3. **Convert to client component** (5 minutes)
   - Quick workaround if SSR is the issue
   - Can continue with Stripe testing

---

**Status:** Blocked pending investigation  
**Priority:** HIGH (blocks all Stripe testing)  
**Estimated Fix Time:** 10-30 minutes once root cause identified

