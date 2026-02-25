# Module: Admin Metrics Routes

> `apps/api/src/api/routes/admin_metrics.py`

---

## Purpose

Provides **platform-wide analytics** endpoints for the admin console. Returns aggregated data about platform usage, agent performance, conversion funnels, device breakdowns, and recent activity. All endpoints are restricted to users with `is_platform_admin = true`.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/admin/metrics/overview` | High-level platform KPIs |
| `GET` | `/v1/admin/metrics/daily` | Daily report generation activity |
| `GET` | `/v1/admin/metrics/agents` | Per-agent usage breakdown |
| `GET` | `/v1/admin/metrics/conversion` | Signup → paid conversion funnel |
| `GET` | `/v1/admin/metrics/devices` | Device/client breakdown (email open tracking) |
| `GET` | `/v1/admin/metrics/recent` | Recent report generations |

---

## Key Metrics Returned

### `/overview`
```json
{
  "total_accounts": 412,
  "active_accounts_30d": 87,
  "total_reports_30d": 1243,
  "total_property_reports_30d": 156,
  "revenue_mrr_cents": 290000,
  "free_accounts": 305,
  "paid_accounts": 107
}
```

### `/daily`
```json
{
  "days": [
    { "date": "2026-02-24", "reports": 42, "property_reports": 8 }
  ]
}
```

### `/agents`
```json
{
  "agents": [
    {
      "account_id": "...",
      "account_name": "John Smith",
      "reports_30d": 12,
      "plan_slug": "pro",
      "last_active": "2026-02-24T10:00:00Z"
    }
  ]
}
```

### `/conversion`
```json
{
  "signups_30d": 45,
  "activated_30d": 32,
  "converted_to_paid_30d": 8,
  "conversion_rate": 0.178
}
```

---

## Dependencies

### Internal
| Module | Usage |
|--------|-------|
| `deps/admin.py` | `require_platform_admin` FastAPI dependency |
| `db.py` | PostgreSQL connection |
| `auth.py` | JWT validation |

### External
| Service | Usage |
|---------|-------|
| PostgreSQL | All metrics derived from DB queries |

---

## Authentication

All routes use `Depends(require_platform_admin)` which:
1. Validates JWT bearer token
2. Queries `users.is_platform_admin = true`
3. Returns `HTTP 403` if not admin

---

## Failure Modes / Guardrails

| Scenario | Behaviour |
|----------|-----------|
| Non-admin user | `HTTP 403 Forbidden` |
| DB query error | `HTTP 500` with error logged |
| No data for date range | Returns empty arrays / zero counts |

---

## Tests / How to Validate

```bash
# Check admin metrics with admin token
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://reportscompany.onrender.com/v1/admin/metrics/overview

# Database query check
python scripts/check_admin_users.py
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01 | Added `/conversion` funnel endpoint |
| 2026-01 | Added `/devices` breakdown endpoint |
| 2025-12 | Added `property_reports_30d` to `/overview` and `/daily` |
| 2025-11 | Initial implementation with `/overview`, `/daily`, `/agents`, `/recent` |
