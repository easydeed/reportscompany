# Lead Capture Flow

## Overview

End-to-end flow from an agent publishing a property report to capturing and managing leads from prospective clients.

## Flow

```
AGENT: Creates Property Report
  1. Property report generated with short_code
  2. QR code generated pointing to /p/{short_code}
  3. Agent shares QR code (print materials, listings, etc.)
         |
         v
CONSUMER: Scans QR Code or Visits Link
  1. Navigates to /p/{short_code}
  2. Views property report landing page
  3. Fills lead capture form:
     - Name
     - Email
     - Phone
     - Message (optional)
         |
         | POST /v1/leads
         v
API: Process Lead
  1. Rate limit check (lead_rate_limits by IP + report)
  2. Blocked IP check (blocked_ips table)
  3. Create lead record:
     - account_id (from property report owner)
     - property_report_id
     - contact info + message
     - consent_given
     - source (qr, direct, referral)
  4. Trigger agent notifications
         |
         v
NOTIFICATIONS:
  a. SMS to agent (via Twilio):
     "New lead from {name} for {property_address}"
  b. Email to agent (via Resend):
     Lead details + contact info
         |
         v
AGENT: Lead Management
  1. Lead appears in /app/leads dashboard
  2. Agent can view, contact, and update lead status
  3. Analytics tracked (view_count, unique_visitors on report)
```

## Rate Limiting

| Protection | Description |
|------------|-------------|
| IP-based rate limit | Max submissions per IP per time window |
| Report-based rate limit | Max submissions per IP per property report |
| Blocked IPs | Known spam/abuse IPs are permanently blocked |

## Key Files

| Service | File | Purpose |
|---------|------|---------|
| Frontend | `app/p/[code]/page.tsx` | Public property report landing page |
| Frontend | `components/lead-form/*` | Lead capture form component |
| API | `routes/leads.py` | Lead creation endpoint |
| Worker | `sms/send.py` | SMS notification to agent |
| API | `services/email.py` | Email notification to agent |
| Frontend | `app/app/leads/page.tsx` | Agent leads dashboard |

## Failure Modes

| Failure | Handling |
|---------|----------|
| Rate limit exceeded | 429 response, form shows rate limit message |
| Blocked IP | 403 response, submission silently rejected |
| SMS delivery fails | Logged to sms_logs, lead still saved |
| Email delivery fails | Logged to email_log, lead still saved |
| Invalid short_code | 404 response |
