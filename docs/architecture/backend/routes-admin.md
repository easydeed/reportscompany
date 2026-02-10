# Admin API

> Platform-wide admin endpoints for metrics, management, and monitoring.
> Files: `apps/api/src/api/routes/admin.py` and `admin_metrics.py`

## Admin Endpoints (admin.py)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | /v1/admin/metrics | System-wide metrics | Admin |
| GET | /v1/admin/accounts | List all accounts | Admin |
| GET | /v1/admin/accounts/{id} | Get account detail | Admin |
| GET | /v1/admin/users | List all users | Admin |
| GET | /v1/admin/affiliates | List affiliates | Admin |
| POST | /v1/admin/invite | Invite sponsored agent | Admin |
| GET | /v1/admin/email-log | Email delivery log | Admin |
| GET | /v1/admin/schedules | All schedules (cross-account) | Admin |
| GET | /v1/admin/reports | All reports (cross-account) | Admin |
| GET | /v1/admin/sms-log | SMS delivery log | Admin |
| GET | /v1/admin/property-stats | Platform property stats | Admin |
| POST | /v1/admin/property-stats/refresh | Refresh stats cache | Admin |

## Admin Metrics Endpoints (admin_metrics.py)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | /v1/admin/metrics/overview | High-level dashboard stats | Admin |
| GET | /v1/admin/metrics/daily | Daily metrics for charting | Admin |
| GET | /v1/admin/metrics/agents | Agent leaderboard | Admin |
| GET | /v1/admin/metrics/hourly | Hourly report distribution | Admin |
| GET | /v1/admin/metrics/devices | Device type breakdown | Admin |
| GET | /v1/admin/metrics/recent | Recent reports feed | Admin |
| GET | /v1/admin/metrics/conversion-funnel | Conversion funnel | Admin |

## Key Functions

### GET /v1/admin/metrics
Returns system health dashboard:
- reports_24h, reports_7d, reports_failed_7d, error_rate_7d
- avg_processing_ms_7d
- schedules_active, schedules_total
- emails_24h
- total_accounts, total_users, total_affiliates

### GET /v1/admin/metrics/overview
Consumer report metrics:
- total_reports, total_views, total_pdfs, total_contacts
- pdf_rate_pct, contact_rate_pct
- Today/week/month counts
- reports_trend_pct (vs previous month)

### GET /v1/admin/metrics/agents
Agent leaderboard sortable by:
- total_reports (default)
- contacts
- contact_rate_pct
Returns: agent_id, name, email, account_name, total_reports, reports_30d, total_views, contacts, pdfs_downloaded

### GET /v1/admin/metrics/conversion-funnel
6-stage funnel for consumer reports:
1. Reports Requested
2. Reports Generated (status=ready)
3. Reports Viewed (view_count > 0)
4. Multiple Views (view_count > 1)
5. Agent Contacted (agent_contact_clicked=true)
6. PDF Downloaded (pdf_url IS NOT NULL)

### POST /v1/admin/invite
Invites a sponsored agent:
- Creates user with placeholder password
- Creates account with plan_slug and sponsor_account_id
- Creates signup_token (7 day TTL)
- Sends invite email via `send_invite_email()`

## Auth Dependency

All admin endpoints use `Depends(get_admin_user)` from `deps/admin.py`. This checks:
- request.state.user exists
- user.is_platform_admin is True
- Sets RLS with `user_role="ADMIN"` to bypass row-level security

## Dependencies
- `deps/admin.py`: `get_admin_user()` dependency
- `services/email.py`: `send_invite_email()`
- `services/property_stats.py`: `get_platform_stats()`, `refresh_stats()`
- `services/usage.py`: `get_monthly_usage()`, `resolve_plan_for_account()`

## Related Files
- Frontend: `/app/admin/*` (admin dashboard pages)
