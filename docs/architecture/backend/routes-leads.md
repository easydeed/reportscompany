# Leads API

> Lead capture from property report landing pages and lead management.
> File: `apps/api/src/api/routes/leads.py`

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /v1/leads/capture | Public lead capture | Public |
| GET | /v1/leads | List leads with filters | Required |
| GET | /v1/leads/{id} | Get single lead | Required |
| PATCH | /v1/leads/{id} | Update lead status/notes | Required |
| DELETE | /v1/leads/{id} | Delete lead | Required |
| GET | /v1/leads/export/csv | Export leads as CSV | Required |

## Lead Pages Endpoints (Consumer CMA)

> File: `apps/api/src/api/routes/lead_pages.py`

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | /v1/cma/{agent_code} | Get agent landing page info | Public |
| POST | /v1/cma/{agent_code}/search | Search property by address | Public |
| POST | /v1/cma/{agent_code}/request | Submit report request | Public |
| GET | /v1/cma/{agent_code}/settings | Get landing page settings | Public |

## Key Functions

### POST /v1/leads/capture (Public)
Anti-spam pipeline (10 checks in order):
1. **Honeypot:** `website` field must be empty (silent success for bots)
2. **Find report:** Look up property_report by short_code
3. **is_active check:** 410 if landing page disabled
4. **expires_at check:** 410 if expired
5. **max_leads check:** 410 if lead cap reached
6. **access_code check:** 403 if wrong code
7. **IP block list:** 403 if IP in `blocked_ips` table
8. **Rate limit:** 5 submissions per hour per IP (429 if exceeded)
9. **Duplicate email:** Silent success if same email already submitted to same report
10. **Store lead + SMS notification**

After storing the lead:
- Records rate limit entry
- Updates landing page analytics (view_count, unique_visitors)
- Sends SMS notification via Twilio if credits available
- Decrements account SMS credits

### POST /v1/cma/{agent_code}/request
- Consumer submits phone + property details
- Rate limit: 5 per hour per IP
- Detects device type from user-agent
- Creates `consumer_reports` record with property_data JSONB
- Queues `process_consumer_report` Celery task

### GET /v1/leads
- Filters: status (new/contacted/converted), property_report_id
- JOINs property_reports for address display
- Pagination: limit (1-200), offset
- Returns `{leads, total, limit, offset}`

### GET /v1/leads/export/csv
- Exports all leads as CSV download
- Optional status filter
- Columns: ID, Name, Email, Phone, Message, Source, Consent, Status, Created, Property info

## Dependencies
- `services/twilio_sms.py`: `send_lead_notification_sms()`, `format_phone_e164()`, `is_configured()`
- `services/agent_code.py`: `get_agent_by_code()`, `increment_landing_page_visits()`
- `services/sitex.py`: `lookup_property()` (for CMA address search)

## Related Files
- Frontend: `/app/leads` (lead management)
- Frontend public: `/p/[code]` (property landing page with lead form)
- Frontend public: `/cma/[code]` (consumer CMA wizard)
- Worker: `tasks.py` processes consumer reports
