# Authentication Flow

## Overview

TrendyReports uses JWT-based authentication with HTTP-only cookies. The system supports registration, email verification, login, logout, password reset, and invite-based onboarding.

## Registration Flow

```
USER: Visits /register
  1. Enters email + password
         |
         | POST /v1/auth/register
         v
API: Create Account
  1. Hash password (bcrypt)
  2. Create user record
  3. Create free account record
  4. Create account_users record (role: OWNER)
  5. Generate email_verification_token
  6. Send verification email (Resend)
  7. Return success (user must verify email)
         |
         v
USER: Clicks Verification Link
  1. GET /v1/auth/verify-email?token={token}
  2. API: validate token, set verified_at
  3. User can now log in
```

## Login Flow

```
USER: Visits /login
  1. Enters email + password
         |
         | POST /v1/auth/login
         v
API: Authenticate
  1. Look up user by email
  2. Verify password hash
  3. Log login_attempt (success/failure + IP)
  4. Generate JWT with claims:
     - user_id
     - account_id
     - role
     - is_platform_admin
  5. Set HTTP-only cookie: mr_token = JWT
  6. Return user profile
```

## Request Authentication (Middleware)

```
EVERY AUTHENTICATED REQUEST:
  1. Read mr_token cookie
  2. Decode + verify JWT
  3. Extract: user_id, account_id, role
  4. Set on request.state:
     - request.state.account_id
     - request.state.user
  5. Set RLS context:
     SET LOCAL app.current_account_id = '{account_id}'
     SET LOCAL app.current_user_role = '{role}'
  6. Proceed to route handler
```

## Logout Flow

```
USER: Clicks Logout
         |
         | POST /v1/auth/logout
         v
API: Revoke Token
  1. Hash the current JWT
  2. Insert into jwt_blacklist (token_hash, user_id, expires_at)
  3. Clear mr_token cookie
  4. Return success
```

Blacklisted tokens are checked during JWT verification. Expired blacklist entries can be periodically cleaned up.

## Password Reset Flow

```
USER: Clicks "Forgot Password"
  1. Enters email
         |
         | POST /v1/auth/forgot-password
         v
API: Generate Reset Token
  1. Create password_reset_tokens record
  2. Send reset email with token link (Resend)
         |
         v
USER: Clicks Reset Link
  1. Enters new password
         |
         | POST /v1/auth/reset-password
         v
API: Reset Password
  1. Validate token (exists, not expired, not used)
  2. Hash new password
  3. Update user.password_hash
  4. Mark token as used (set used_at)
  5. Return success
```

## Invite Flow (Affiliate -> Agent)

```
AFFILIATE: Invites Agent
  1. Enters agent email from /app/team page
         |
         | POST /v1/invites
         v
API: Create Invite
  1. Create user record (no password yet)
  2. Create signup_token
  3. Add account_users record (role based on invite)
  4. Send invite email with accept-invite link
         |
         v
AGENT: Clicks Accept Invite Link
  1. Navigates to /accept-invite?token={token}
  2. Sets password
         |
         | POST /v1/auth/accept-invite
         v
API: Complete Invite
  1. Validate signup_token
  2. Hash password, update user record
  3. Mark signup_token as used
  4. Return success, user can now log in
```

## Key Files

| Service | File | Purpose |
|---------|------|---------|
| Frontend | `app/login/page.tsx` | Login page |
| Frontend | `app/register/page.tsx` | Registration page |
| Frontend | `app/accept-invite/page.tsx` | Invite acceptance page |
| API | `routes/auth.py` | Auth endpoints (register, login, logout, verify, reset) |
| API | `middleware/auth.py` | JWT verification + RLS context setting |
| API | `services/email.py` | Verification + reset emails |

## Security Measures

| Measure | Implementation |
|---------|----------------|
| Password hashing | bcrypt |
| Token storage | JWT blacklist for revocation |
| Cookie security | HTTP-only, Secure, SameSite |
| Login tracking | login_attempts table with IP address |
| Token expiry | Verification tokens, reset tokens, and JWTs all have expiration |
| RLS enforcement | Every request sets tenant context at database level |
