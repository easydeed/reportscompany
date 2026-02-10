# Auth API

> Authentication endpoints: login, register, logout, password reset, email verification.
> File: `apps/api/src/api/routes/auth.py`

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /v1/auth/login | JWT + cookie login | Public |
| POST | /v1/auth/register | Create user + free account | Public |
| POST | /v1/auth/logout | Token blacklisting | Public (reads token) |
| POST | /v1/auth/accept-invite | Sponsored agent invite acceptance | Public |
| POST | /v1/auth/forgot-password | Send reset email | Public |
| POST | /v1/auth/reset-password | Reset with token | Public |
| POST | /v1/auth/verify-email | Email verification | Public |
| POST | /v1/auth/resend-verification | Resend verification email | Public |
| POST | /v1/auth/seed-dev | Development seeding | Public (dev only) |

## Key Functions

### POST /v1/auth/login
- **Input:** `{email, password}`
- **Brute-force protection:** 5 failed attempts per email in 15 minutes -> 429
- Records all attempts in `login_attempts` table
- Prioritizes INDUSTRY_AFFILIATE account if user belongs to one
- JWT payload includes: `sub`, `user_id`, `account_id`, `role`, `account_type`, `scopes`
- JWT TTL: 1 hour
- Sets `mr_token` HTTP-only cookie (secure, samesite=lax, 1 hour)
- Returns `{access_token}`

### POST /v1/auth/register
- **Input:** `{name, email, password}`
- Password minimum: 8 characters
- Creates: account (REGULAR, free plan), user (email_verified=FALSE), account_users (OWNER)
- Generates email verification token (24 hour TTL)
- Sends verification email via background task
- JWT TTL: 7 days (longer for new users)
- Sets `mr_token` cookie (7 days)
- Returns `{ok: true, email_verified: false}`

### POST /v1/auth/logout
- Reads token from cookie or Authorization header
- Hashes token with SHA-256
- Inserts into `jwt_blacklist` table with expiry
- Deletes `mr_token` cookie
- Returns `{ok: true}`

### POST /v1/auth/accept-invite
- **Input:** `{token, password}`
- Validates token from `signup_tokens` table (not used, not expired)
- Sets user password and marks email_verified=TRUE
- Marks token as used
- Returns auth session (JWT + cookie, 7 day TTL)

### POST /v1/auth/forgot-password
- **Input:** `{email}`
- Always returns success (prevents email enumeration)
- If user exists: invalidates existing tokens, generates new token (1 hour TTL)
- Sends reset email via background task

### POST /v1/auth/reset-password
- **Input:** `{token, new_password}`
- Validates token (not used, not expired, user active)
- Updates password_hash and password_changed_at
- Marks token as used
- Returns new auth session (JWT + cookie)

### POST /v1/auth/verify-email
- **Input:** `{token}`
- Validates token from `email_verification_tokens`
- Sets `verified_at` on token and `email_verified=TRUE` on user
- Idempotent: returns success if already verified

### POST /v1/auth/resend-verification
- **Input:** `{email}`
- Always returns success (prevents enumeration)
- Invalidates existing verification tokens
- Generates new token (24 hour TTL)
- Sends via background task

## Dependencies
- `auth.py` module: `sign_jwt()`, `verify_jwt()`, `check_password()`, `hash_password()`
- `services/email.py`: `send_welcome_email()`, `send_password_reset_email()`, `send_verification_email()`
- All endpoints use raw `psycopg.connect()` (not the `db_conn()` helper)

## Related Files
- Frontend: `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/welcome`
- Middleware: `authn.py` reads JWT and checks blacklist on every request
