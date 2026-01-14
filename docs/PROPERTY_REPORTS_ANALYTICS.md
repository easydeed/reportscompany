# Property Reports Analytics System

## Overview

Comprehensive analytics system for tracking property report usage, leads, and performance across three levels:

1. **Agent Level**: Individual account metrics
2. **Affiliate Level**: Roll-up of all sponsored agents
3. **Admin Level**: Platform-wide statistics

---

## Database Schema

### Migration: `0037_property_report_stats.sql`

#### Tables Created

| Table | Purpose |
|-------|---------|
| `property_report_stats` | Per-account aggregated statistics |
| `property_report_stats_daily` | Daily snapshots for trending/charts |
| `platform_property_stats` | Platform-wide totals (singleton) |

#### Key Functions

| Function | Purpose |
|----------|---------|
| `refresh_account_property_stats(uuid)` | Refresh stats for one account |
| `refresh_all_property_stats()` | Refresh all accounts + platform stats |
| `record_daily_property_stats()` | Record daily snapshot (run via cron) |

#### Auto-Refresh Triggers

Stats are automatically refreshed when:
- Property reports are created, updated (status), or deleted
- Leads are created, updated (status), or deleted

---

## API Endpoints

### Agent Level

```
GET /v1/property/stats
```

**Query Parameters:**
- `from_date` (optional): ISO date string
- `to_date` (optional): ISO date string

**Response:**
```json
{
  "period": { "from": "...", "to": "..." },
  "summary": {
    "total_reports": 25,
    "completed": 23,
    "failed": 1,
    "processing": 1,
    "completion_rate": 92.0
  },
  "report_types": { "seller": 20, "buyer": 5 },
  "themes": { "classic": 5, "modern": 8, "elegant": 3, "teal": 7, "bold": 2 },
  "engagement": {
    "total_views": 150,
    "unique_visitors": 85,
    "active_landing_pages": 12
  },
  "leads": {
    "total": 12,
    "from_qr": 8,
    "from_direct": 4,
    "converted": 3,
    "conversion_rate": 14.12
  },
  "top_reports": [...],
  "daily_trend": [...],
  "all_time": { ... }
}
```

### Affiliate Level

```
GET /v1/property/stats/affiliate
```

**Access:** INDUSTRY_AFFILIATE accounts only

**Response:**
```json
{
  "period": { ... },
  "summary": {
    "total_agents": 15,
    "active_agents": 8,
    "inactive_agents": 7
  },
  "aggregate": {
    "total_reports": 120,
    "total_views": 800,
    "total_leads": 45,
    "conversion_rate": 5.6
  },
  "themes": { ... },
  "leaderboard": [
    {
      "account_id": "...",
      "name": "John Smith",
      "email": "john@example.com",
      "reports": 15,
      "views": 120,
      "leads": 8,
      "last_activity": "2026-01-14T..."
    }
  ],
  "inactive_agents": [...]
}
```

### Admin Level

```
GET /v1/admin/property-reports/stats
GET /v1/admin/property-reports
GET /v1/admin/property-reports/top-affiliates
GET /v1/admin/property-reports/top-agents
POST /v1/admin/property-reports/refresh-stats
```

---

## Frontend Pages

### Admin Console

**Path:** `/admin/property-reports`

Features:
- Platform-wide KPIs (reports, views, leads, conversion rate)
- Breakdown by account type (regular, sponsored, affiliate)
- Theme popularity distribution
- Top affiliates leaderboard
- Top agents leaderboard
- Recent property reports table
- All-time statistics

### Affiliate Dashboard

**Path:** `/app/affiliate/property-reports`

Features:
- Agent summary (total, active, inactive)
- Aggregate metrics across all sponsored agents
- Lead source breakdown (QR vs direct)
- Theme popularity for sponsored agents
- Agent leaderboard with rankings
- Inactive agents alert list

---

## Metrics Tracked

### Per Account

| Metric | Description |
|--------|-------------|
| `total_reports` | Total property reports created |
| `completed_reports` | Successfully generated PDFs |
| `failed_reports` | Failed PDF generation |
| `seller_reports` | Seller report type |
| `buyer_reports` | Buyer report type |
| `theme_*` | Usage by theme (1-5) |
| `total_views` | Landing page views |
| `unique_visitors` | Unique landing page visitors |
| `active_landing_pages` | Currently active landing pages |
| `total_leads` | Total leads captured |
| `leads_from_qr` | Leads from QR scan |
| `leads_from_direct` | Leads from direct links |
| `leads_converted` | Leads marked as converted |
| `conversion_rate` | (leads / visitors) * 100 |
| `completion_rate` | (completed / total) * 100 |
| `reports_last_30d` | Rolling 30-day report count |
| `leads_last_30d` | Rolling 30-day lead count |

### Platform Level

| Metric | Description |
|--------|-------------|
| `reports_by_regular` | Reports by regular agents |
| `reports_by_sponsored` | Reports by sponsored agents |
| `reports_by_affiliate` | Reports by affiliate accounts |
| `accounts_with_reports` | Accounts that have used property reports |
| `avg_reports_per_account` | Average reports per active account |

---

## Stats Refresh

### Automatic Triggers

Database triggers automatically refresh stats when:
- `property_reports` INSERT/UPDATE(status)/DELETE
- `leads` INSERT/UPDATE(status)/DELETE

### Manual Refresh

Admin can manually refresh via:
```
POST /v1/admin/property-reports/refresh-stats
POST /v1/admin/property-reports/refresh-stats?account_id=<uuid>
```

### Scheduled Refresh (Recommended)

For high-volume systems, consider:
1. Disabling triggers
2. Running `refresh_all_property_stats()` via cron every 5-15 minutes
3. Running `record_daily_property_stats()` nightly

---

## Security

### RLS Policies

- `property_report_stats`: Scoped to own account or ADMIN
- `property_report_stats_daily`: Scoped to own account or ADMIN
- `platform_property_stats`: ADMIN only (SELECT)

### Endpoint Access

| Endpoint | Access |
|----------|--------|
| `/v1/property/stats` | Any authenticated user |
| `/v1/property/stats/affiliate` | INDUSTRY_AFFILIATE only |
| `/v1/admin/property-reports/*` | Platform admin only |

---

## Related Documentation

- [Property Reports Documentation](./PROPERTY_REPORTS_DOCUMENTATION.md)
- [Admin Console](./ADMIN_CONSOLE.md)
- [Title Company Onboarding](./TITLE_COMPANY_ONBOARDING.md)

