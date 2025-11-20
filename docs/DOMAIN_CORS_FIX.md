# Domain + CORS Fix for www.trendyreports.io

**Date**: 2025-11-20  
**Issue**: CORS errors and 405 on reports after domain change

---

## 🐛 **The Problem**

After switching to `www.trendyreports.io`:
1. **CORS errors**: `https://reportscompany.onrender.com/v1/reports` blocked by CORS
2. **405 errors**: `/api/proxy/v1/reports` returns 405 Method Not Allowed on GET
3. **Reports page broken**: Can't load reports list

**Root Cause**:
- `ALLOWED_ORIGINS` on Render only has `https://trendyreports.io` (no `www`)
- Proxy route for reports only has POST/DELETE, missing GET handler

---

## ✅ **Step 1: Fix ALLOWED_ORIGINS on Render**

### **Update Environment Variable**

1. Go to: https://dashboard.render.com (find `reportscompany-api` service)
2. Click **Environment** tab
3. Find `ALLOWED_ORIGINS` variable
4. **Current value** (example):
   ```json
   ["http://localhost:3000","https://trendyreports.io","https://reportscompany-web.vercel.app"]
   ```

5. **New value** (add `www` subdomain):
   ```json
   ["http://localhost:3000","https://trendyreports.io","https://www.trendyreports.io","https://reportscompany-web.vercel.app","https://reportscompany-web-*.vercel.app"]
   ```

6. Click **Save Changes**
7. Render will auto-redeploy (takes 2-3 minutes)

### **Why This Fixes CORS**

- Browser treats `trendyreports.io` and `www.trendyreports.io` as **different origins**
- Without `www.trendyreports.io` in `ALLOWED_ORIGINS`, API rejects requests from www subdomain
- Adding it to the list allows the API to send `Access-Control-Allow-Origin: https://www.trendyreports.io` header

---

## ✅ **Step 2: Add GET Handler to Reports Proxy**

**File**: `apps/web/app/api/proxy/v1/reports/route.ts`

**Problem**: Route only has POST (create report) and DELETE, but `/app/reports` needs GET (list reports)

**Fix**: Add GET handler to forward list requests to backend

See code changes in commit.

---

## 🧪 **Testing After Fix**

### **Test CORS**
1. Visit: https://www.trendyreports.io/app/reports
2. Open browser DevTools → Console
3. **Before fix**: See CORS error
4. **After fix**: No CORS errors

### **Test Reports List**
1. Visit: https://www.trendyreports.io/app/reports
2. **Before fix**: 405 error, empty list
3. **After fix**: Reports list loads (or shows "No reports yet")

### **Test Domain Variations**
- https://trendyreports.io/app/reports → ✅ Works
- https://www.trendyreports.io/app/reports → ✅ Works (after fix)
- Both should work without CORS errors

---

## 📝 **Related Issues**

This fix also resolves:
- Schedule creation failing (CORS on `/v1/schedules`)
- Account switching failing (CORS on `/v1/account/use`)
- Any other API calls from `www.trendyreports.io`

---

**Status**: Ready to deploy once ALLOWED_ORIGINS is updated on Render

