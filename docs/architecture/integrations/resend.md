# Resend Integration

## Overview

Resend handles transactional email delivery for authentication and system notifications.

## Service Details

- **Used by:** API service (`services/email.py`)
- **Auth method:** API Key
- **Transport:** Async HTTP via `httpx`
- **Email types:**
  - Email verification (signup flow)
  - Password reset
  - Welcome emails
  - Invite emails (affiliate inviting agents)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Resend API key |
| `EMAIL_FROM_ADDRESS` | Sender email address |
| `EMAIL_REPLY_TO` | Reply-to email address |

## Key Behaviors

- All email sends are asynchronous (non-blocking) using httpx async client
- Email templates are defined in the API service
- Verification tokens and reset tokens are included as URL parameters in email links
- Email delivery status is not tracked at the Resend level (fire-and-forget for transactional emails)
