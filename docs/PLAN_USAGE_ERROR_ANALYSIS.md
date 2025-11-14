# Plan Usage Error Analysis

## Error Summary

**Endpoint**: `/v1/account/plan-usage`  
**Status**: 500 (frontend proxy) → 401 (backend)  
**Timestamp**: 2025-11-14 18:37:55 UTC

## Root Cause

The backend is returning `401: Unauthorized` when the Vercel proxy forwards requests to `/v1/account/plan-usage`.

### Stack Trace
```
File "/opt/render/project/src/apps/api/src/api/middleware/authn.py", line 57, in dispatch
  raise HTTPException(status_code=401, detail="Unauthorized")
fastapi.exceptions.HTTPException: 401: Unauthorized
```

## Analysis

The authentication middleware (`authn.py`) is rejecting the request because:
1. No valid `Authorization: Bearer <JWT>` header present
2. No API key present
3. The `mr_token` cookie from the logged-in browser session is **not being forwarded** from the Vercel proxy to the Render API

## Fix Required

The proxy route at `apps/web/app/api/proxy/v1/account/plan-usage/route.ts` needs to:
1. Extract the `mr_token` cookie from the incoming Next.js request
2. Forward it as an `Authorization: Bearer <token>` header to the backend API
3. NOT forward it as a cookie header (Render API expects JWT in Authorization header, not cookies)

## Files to Modify

1. `apps/web/app/api/proxy/v1/account/plan-usage/route.ts` - Fix cookie → auth header forwarding
2. Potentially other proxy routes have the same issue

