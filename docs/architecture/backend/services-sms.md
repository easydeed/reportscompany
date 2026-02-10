# Twilio SMS Service

> SMS notifications for lead capture events.
> File: `apps/api/src/api/services/twilio_sms.py`

## Overview

Sends SMS notifications to agents when new leads are captured from property report landing pages. Uses Twilio REST API directly via httpx (not the Twilio Python SDK).

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Sender phone number (E.164 format) |

## Key Functions

### is_configured() -> bool
Returns True if all three Twilio env vars are set. Called before attempting any SMS send.

### send_sms(to_phone, message) -> dict
- Low-level SMS send via Twilio REST API
- Posts to `https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json`
- Uses basic auth (SID:token)
- Validates E.164 phone format (must start with `+`)
- Truncates messages over 1600 characters
- Returns `{message_sid, status, to}`
- Raises `TwilioSMSError` on failure

### send_lead_notification_sms(to_phone, lead_name, property_address, lead_phone, lead_email) -> dict
- Builds formatted notification message with lead details
- Calls `send_sms()` internally
- Message format:
  ```
  New Lead Alert!

  {lead_name} is interested in:
  {property_address}
  {lead_phone}
  {lead_email}

  Respond quickly for best results!

  - TrendyReports
  ```

### format_phone_e164(phone, default_country="1") -> str | None
- Converts various phone formats to E.164
- 10 digits -> +1XXXXXXXXXX (US)
- 11 digits starting with 1 -> +1XXXXXXXXXX
- Already has + prefix -> pass through
- Returns None if invalid

## Callers

| Caller | Function | Trigger |
|--------|----------|---------|
| `routes/leads.py: capture_lead()` | `send_lead_notification_sms()` | New lead captured from landing page |

The SMS flow in lead capture:
1. Check `accounts.sms_credits > 0` and `twilio_is_configured()`
2. Fetch agent phone from users table
3. Format phone to E.164
4. Send notification SMS
5. Decrement `accounts.sms_credits`
6. Update `leads.sms_sent_at`
