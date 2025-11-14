# Auth Fix Summary - Plan & Usage Page

## Root Cause Identified ✅

**Problem**: Auth middleware only checked `Authorization` header, not `mr_token` cookie.

**Impact**: When proxy forwarded requests, cookies weren't being checked as fallback.

## Fix Applied

### Backend (`apps/api/src/api/middleware/authn.py`)
✅ Added cookie fallback logic:
1. Try Authorization header first (JWT or API key)
2. Fall back to `mr_token` cookie if header not present
3. Added diagnostic logging to show which auth method succeeded

### Frontend (`apps/web/app/api/proxy/v1/account/plan-usage/route.ts`)
✅ Simplified proxy to forward cookies directly:
- Removed Bearer header construction
- Now forwards entire `cookie` header to API
- Matches same auth flow as direct browser requests

## Deployment Status

- **Render API**: ✅ DEPLOYED (19:40:05 UTC) - Cookie fallback active
- **Vercel Frontend**: ⏳ PENDING - Proxy fix not yet deployed

## Testing Results

1. **Direct API Call**: ✅ Works (seen 200 OK in logs)
2. **Via Proxy**: ❌ Still failing - No "Auth via" messages in logs
   - Indicates proxy isn't forwarding cookies correctly YET
   - Vercel likely hasn't deployed the proxy fix

## Next Steps

1. Wait for Vercel deployment to complete (~5-10 minutes)
2. Test again with fresh login
3. Expected result: "Auth via mr_token cookie" messages in logs
4. Plan page should load successfully

## Diagnostic Commands

```bash
# Check if cookie is present in request
curl -H "Cookie: mr_token=<token>" https://reportscompany.onrender.com/v1/account/plan-usage

# Check Vercel deployment status
# (User has Vercel access)
```

## Timeline

- 19:37 - Code committed & pushed
- 19:40 - Render deployed ✅  
- 19:43 - Vercel auto-deployment should trigger
- 19:45-19:50 - Vercel deployment expected to complete
- 19:50+ - Testing should succeed

