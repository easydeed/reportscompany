# Plan Usage Error Analysis

## Error Summary

**Endpoint**: `/v1/account/plan-usage`  
**Status**: 500 (frontend proxy) → 401 (backend)  
**Timestamp**: 2025-11-14 19:03:00 UTC (still failing after fresh login)

## Root Cause - CONFIRMED

The authentication middleware (`authn.py`) line 57 raises `401: Unauthorized` when:

```python
# Line 34: Try to decode JWT
claims = verify_jwt(token, settings.JWT_SECRET)
if claims and claims.get("account_id"):
    acct = claims["account_id"]  # Line 36
else:
    # Try API key fallback...
    
# Line 56-57: If acct is still None
if not acct:
    raise HTTPException(status_code=401, detail="Unauthorized")  # THIS LINE
```

### The Failure Condition

The JWT decode is either:
1. **Failing completely** (`verify_jwt` returns None), OR
2. **Succeeding but missing `account_id` claim**

### JWT Structure Mismatch - THE SMOKING GUN

**Login JWT** (`/v1/auth/login` line 32):
```python
{"sub": user_id, "account_id": account_id, "scopes": [...]}
# MISSING: "user_id" field
```

**Accept-Invite JWT** (`/v1/auth/accept-invite` line 180-186):
```python
{"sub": user_id, "user_id": user_id, "account_id": account_id, "scopes": [...]}
# HAS: "user_id" field  
```

### Why This Causes 401

The middleware needs **BOTH** `account_id` AND `user_id` in claims to work properly:
- Line 35-36: Extracts `account_id`
- Line 65: Checks `if claims and claims.get("user_id"):` to populate `request.state.user`

**Hypothesis**: Without `user_id`, something downstream (possibly RLS or account validation in line 69-73) fails silently, causing acct to become None.

## Fix Required

1. **Make login JWT consistent with accept-invite JWT** - Add `user_id` to login token
2. **Add defensive logging** - Log when JWT decode fails or when claims are missing expected fields
3. **Standardize all JWT creation** - Ensure all auth endpoints produce identical JWT structure

## Files to Modify

1. `apps/api/src/api/routes/auth.py` line 32 - Add `user_id` to login JWT payload
2. `apps/api/src/api/middleware/authn.py` - Add debug logging for JWT decode failures

