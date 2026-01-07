# Account Settings Implementation

This document describes the account settings feature implementation, including profile management, password change, and email update functionality.

## Overview

The Account Settings page allows users to:
- **Profile Tab**: Update personal information (first name, last name, company name, phone, avatar)
- **Security Tab**: Change password and update email address

## Features

### Profile Management
- First Name
- Last Name
- Company Name
- Phone Number (with input masking)
- Profile Picture/Avatar (uploaded via R2 storage)

**Option A Integration (December 2025):**
The user's avatar (`users.avatar_url`) is automatically used as their headshot on reports and emails. This means:
- Regular agents set their photo once (in Account Settings or during onboarding)
- It automatically appears on their branded reports
- No need to upload the same photo in multiple places

### Security Features
- **Password Change**
  - Requires current password verification
  - Minimum 8 characters for new password
  - Logs out other sessions after change (new JWT issued)

- **Email Change**
  - Requires current password verification
  - Validates email is not already in use
  - Updates immediately (future: could add email verification step)

---

## Files Modified/Created

### Database Migration
| File | Description |
|------|-------------|
| `db/migrations/0017_user_profile_fields.sql` | Adds profile fields to users table |

**New Columns Added to `users` table:**
- `first_name VARCHAR(100)`
- `last_name VARCHAR(100)`
- `company_name VARCHAR(200)`
- `phone VARCHAR(50)`
- `avatar_url VARCHAR(500)`
- `password_changed_at TIMESTAMP`

### Backend API (Python/FastAPI)
| File | Description |
|------|-------------|
| `apps/api/src/api/routes/users.py` | **NEW** - User profile endpoints |
| `apps/api/src/api/main.py` | Updated to include users router |

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/users/me` | Get current user profile |
| PATCH | `/v1/users/me` | Update user profile |
| POST | `/v1/users/me/password` | Change password |
| PATCH | `/v1/users/me/email` | Change email |

### Frontend Proxy Routes (Next.js)
| File | Description |
|------|-------------|
| `apps/web/app/api/proxy/v1/users/me/route.ts` | **NEW** - Profile GET/PATCH proxy |
| `apps/web/app/api/proxy/v1/users/me/password/route.ts` | **NEW** - Password change proxy |
| `apps/web/app/api/proxy/v1/users/me/email/route.ts` | **NEW** - Email change proxy |

### Frontend Pages (React/Next.js)
| File | Description |
|------|-------------|
| `apps/web/app/app/account/settings/page.tsx` | **NEW** - Account settings page |
| `apps/web/app/app-layout.tsx` | Updated sidebar navigation |

---

## API Documentation

### GET /v1/users/me

Returns the current user's profile.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Acme Real Estate",
  "phone": "(555) 123-4567",
  "avatar_url": "https://...",
  "email_verified": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### PATCH /v1/users/me

Update user profile fields.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Acme Real Estate",
  "phone": "(555) 123-4567",
  "avatar_url": "https://..."
}
```

**Response:** Updated user profile object

### POST /v1/users/me/password

Change user password. Issues new JWT token (invalidates other sessions).

**Request Body:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Password changed successfully. Other sessions have been logged out."
}
```

**Side Effects:**
- Updates `password_changed_at` timestamp
- Issues new JWT token via Set-Cookie header
- Other sessions become invalid

### PATCH /v1/users/me/email

Change user email address.

**Request Body:**
```json
{
  "new_email": "newemail@example.com",
  "current_password": "currentpassword123"
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Email updated successfully",
  "email": "newemail@example.com"
}
```

---

## Navigation

The Settings page is accessible from:
1. **Sidebar**: Settings link (between Branding and Billing)
2. **User Dropdown**: "Account Settings" option at top of dropdown

---

## Security Considerations

1. **Password Requirements**
   - Minimum 8 characters
   - New password must differ from current password

2. **Email Change Security**
   - Requires current password verification
   - Checks for email uniqueness

3. **Session Management**
   - Password change issues new JWT
   - Old tokens become invalid (logout other sessions)

4. **Avatar Upload**
   - Uses existing R2 upload infrastructure (`/api/proxy/v1/upload/branding/headshot`)
   - Supports PNG, JPEG, WebP, GIF
   - Max 5MB file size

---

## Future Enhancements

Potential improvements for future iterations:

1. **Email Verification Flow**
   - Send verification email to new address
   - Keep old email until verified

2. **Two-Factor Authentication (2FA)**
   - TOTP-based 2FA
   - Recovery codes

3. **Session Management**
   - View active sessions
   - Revoke individual sessions

4. **Account Deletion**
   - Soft delete with grace period
   - Data export before deletion

5. **Password Complexity**
   - Require uppercase, lowercase, numbers, special chars
   - Password strength indicator

---

## Testing

### Manual Testing Checklist

- [ ] Load profile data on page load
- [ ] Update first name, last name, company, phone
- [ ] Upload avatar image
- [ ] Remove avatar image
- [ ] Change password with correct current password
- [ ] Change password with incorrect current password (should fail)
- [ ] Change password with weak new password (should fail)
- [ ] Verify other sessions logged out after password change
- [ ] Change email with correct password
- [ ] Change email to existing email (should fail)
- [ ] Verify navigation links work (sidebar and dropdown)

### API Testing

```bash
# Get profile
curl -X GET https://api.example.com/v1/users/me \
  -H "Cookie: mr_token=..."

# Update profile
curl -X PATCH https://api.example.com/v1/users/me \
  -H "Content-Type: application/json" \
  -H "Cookie: mr_token=..." \
  -d '{"first_name": "John", "last_name": "Doe"}'

# Change password
curl -X POST https://api.example.com/v1/users/me/password \
  -H "Content-Type: application/json" \
  -H "Cookie: mr_token=..." \
  -d '{"current_password": "old", "new_password": "newpass123"}'

# Change email
curl -X PATCH https://api.example.com/v1/users/me/email \
  -H "Content-Type: application/json" \
  -H "Cookie: mr_token=..." \
  -d '{"new_email": "new@example.com", "current_password": "mypassword"}'
```

---

## Deployment Notes

1. **Run Database Migration**
   ```bash
   psql $DATABASE_URL < db/migrations/0017_user_profile_fields.sql
   ```

2. **Deploy Backend**
   - New route file `users.py` will be automatically picked up
   - Restart API server to load new routes

3. **Deploy Frontend**
   - New page and proxy routes included in build
   - No additional configuration needed

---

## Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Settings Page  │────▶│  Proxy Routes    │────▶│  Backend API    │
│  (React)        │     │  (Next.js)       │     │  (FastAPI)      │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                                                │
        │                                                │
        ▼                                                ▼
┌─────────────────┐                             ┌─────────────────┐
│                 │                             │                 │
│  R2 Storage     │                             │  PostgreSQL     │
│  (Avatars)      │                             │  (Users Table)  │
│                 │                             │                 │
└─────────────────┘                             └─────────────────┘
```

---

## Related Documentation

- [AUTH_ARCHITECTURE_V1.md](./AUTH_ARCHITECTURE_V1.md) - Authentication system details
