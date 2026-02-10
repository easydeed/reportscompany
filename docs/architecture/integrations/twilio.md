# Twilio Integration

## Overview

Twilio provides SMS delivery for consumer report notifications and agent lead alerts.

## Service Details

- **Used by:** Worker service (`sms/send.py`)
- **Auth method:** Account SID + Auth Token
- **SMS types:**
  - Consumer report delivery (send report link to consumer)
  - Agent lead notification (alert agent when a new lead is captured)
- **Phone format:** E.164 international format (e.g., `+15551234567`)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Twilio sender phone number (E.164 format) |

## Key Behaviors

- SMS messages are sent from the worker during report processing pipelines
- SMS delivery status is logged to the `sms_logs` table
- Phone numbers are validated and formatted to E.164 before sending
- SMS credits are tracked per account and deducted on send
