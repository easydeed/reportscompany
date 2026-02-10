# Email Service (Resend)

> Email delivery via Resend API for transactional emails.
> File: `apps/api/src/api/services/email.py`

## Overview

The API service uses Resend for transactional emails (welcome, verification, password reset, invites). The Worker service uses SendGrid for report delivery emails.

## EmailService Class

Singleton instance at module level: `email_service = EmailService()`

### Configuration

| Setting | Source | Description |
|---------|--------|-------------|
| api_key | `settings.RESEND_API_KEY` | Resend API key |
| from_address | `settings.EMAIL_FROM_ADDRESS` | Sender address |
| reply_to | `settings.EMAIL_REPLY_TO` | Reply-to address |
| app_base | `settings.APP_BASE` | Frontend URL for generated links |

### Key Methods

#### send_email(to, subject, html, text, reply_to, tags)
- Async method using `httpx.AsyncClient`
- Posts to `https://api.resend.com/emails`
- Returns `{ok: true, id: "..."}` or `{ok: false, error: "..."}`
- Gracefully handles missing configuration (logs warning, returns error)

#### send_email_sync(to, subject, html, text, reply_to, tags)
- Synchronous version using `httpx.Client`
- Used by background tasks (FastAPI BackgroundTasks)
- Same return format as async version

## Email Templates

All templates are inline HTML in the service file. Each email has HTML and plain text versions.

### send_welcome_email(email, user_name)
- Subject: "Welcome to Market Reports!"
- CTA: "Get Started" button linking to `/app`
- Tags: `category: welcome`

### send_verification_email(email, user_name, verification_token)
- Subject: "Welcome to TrendyReports - Verify Your Email"
- CTA: "Verify Email Address" button linking to `/verify-email?token=...`
- Token TTL note: "24 hours"
- Tags: `category: verification`

### send_password_reset_email(email, user_name, reset_token)
- Subject: "Reset your TrendyReports password"
- CTA: "Reset Password" button linking to `/reset-password?token=...`
- Token TTL note: "1 hour"
- Tags: `category: password-reset`

### send_invite_email(email, inviter_name, company_name, invite_token)
- Subject: "{inviter_name} invited you to Market Reports"
- CTA: "Accept Invitation" button linking to `/welcome?token=...`
- Token TTL note: "7 days"
- Tags: `category: invite`
- Lists sponsored agent benefits (75 free reports, branding, schedules)

## Callers

| Caller | Email | Trigger |
|--------|-------|---------|
| `routes/auth.py: register()` | Verification | New user registration |
| `routes/auth.py: resend_verification()` | Verification | User requests resend |
| `routes/auth.py: forgot_password()` | Password reset | Forgot password form |
| `routes/admin.py: invite()` | Invite | Admin invites sponsored agent |

All email sends use FastAPI `BackgroundTasks` to avoid blocking the response.
