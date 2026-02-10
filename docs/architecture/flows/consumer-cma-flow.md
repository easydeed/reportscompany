# Consumer CMA Flow

## Overview

End-to-end flow for a consumer requesting an instant home valuation report through an agent's personalized CMA landing page.

## Flow

```
AGENT: Has Unique Agent Code
  - Each agent has a unique agent_code (auto-generated)
  - Agent's CMA landing page: /cma/{agent_code}
  - Agent shares link via marketing, social media, etc.
         |
         v
CONSUMER: Visits /cma/{agent_code}
  1. Sees agent-branded landing page
  2. Enters:
     - Phone number
     - Property address (Google Places autocomplete)
  3. Gives consent for contact
  4. Submits request
         |
         | POST /v1/consumer-reports
         v
API: Create Consumer Report
  1. Look up agent by agent_code
  2. Create consumer_reports record (status: pending)
  3. Store consumer phone, address, consent
  4. Enqueue Celery task
  5. Return 202 with report_id
         |
         | Redis queue -> Celery
         v
WORKER: process_consumer_report task
  1. Set status: processing
  2. Fetch comparable properties from SimplyRETS
  3. Calculate value estimate based on comps
  4. Build market stats summary
  5. Generate report (HTML -> PDF)
  6. Upload PDF to R2
  7. Set status: completed
         |
         v
NOTIFICATIONS (parallel):
  a. SMS to consumer (Twilio):
     "Your home value report is ready: {link to /r/{id}}"
  b. SMS to agent (Twilio):
     "New CMA lead: {consumer_phone} for {property_address}"
         |
         v
CONSUMER: Views Report
  1. Clicks link in SMS -> /r/{id}
  2. Views interactive report with:
     - Property details
     - Comparable properties
     - Value estimate range
     - Market statistics
  3. Analytics tracked (views, device type, session)
```

## Key Files

| Service | File | Purpose |
|---------|------|---------|
| Frontend | `app/cma/[code]/page.tsx` | Consumer-facing CMA landing page |
| Frontend | `app/r/[id]/page.tsx` | Consumer report viewer |
| API | `routes/consumer_reports.py` | Consumer report endpoints |
| Worker | `tasks.py` -> `process_consumer_report` | Report generation pipeline |
| Worker | `sms/send.py` | SMS delivery (consumer + agent) |

## Agent Branding

- The `/cma/{agent_code}` landing page displays the agent's branding:
  - Agent name and photo
  - Custom headline, subheadline, and CTA text (from `users.landing_page_*` fields)
  - Account-level branding (logo, colors) if affiliate branding is configured

## Failure Modes

| Failure | Handling |
|---------|----------|
| Invalid agent_code | 404 response |
| SimplyRETS fetch fails | Retry with backoff; on final failure, status=failed |
| Value estimate cannot be calculated | Report generated without estimate, flagged |
| SMS delivery fails | Logged to sms_logs, report still available via direct link |
| PDF generation fails | Retry; consumer can still view HTML report |
