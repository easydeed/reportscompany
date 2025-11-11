# Phase 24B: Schedules API Routes - Summary

**Date:** November 10, 2025  
**Status:** ✅ Complete

---

## What Was Created

### 1. Schedules CRUD API (`apps/api/src/api/routes/schedules.py`)

**Endpoints:**
- `POST /v1/schedules` - Create new schedule (201)
- `GET /v1/schedules` - List all schedules (with `active_only` filter)
- `GET /v1/schedules/{id}` - Get single schedule
- `PATCH /v1/schedules/{id}` - Update schedule (nulls `next_run_at` for ticker recompute)
- `DELETE /v1/schedules/{id}` - Delete schedule (204, cascade deletes runs)
- `GET /v1/schedules/{id}/runs` - List execution history (audit trail)

**Features:**
- ✅ RLS enforcement via `set_rls(conn, account_id)`
- ✅ Email validation via Pydantic `EmailStr`
- ✅ Cadence validation (weekly requires `weekly_dow`, monthly requires `monthly_dom`)
- ✅ Auto-nulls `next_run_at` on updates so ticker recomputes schedule
- ✅ PostgreSQL array handling for `recipients` and `zip_codes`
- ✅ Full CRUD with proper status codes (201, 200, 204, 404)

---

### 2. Unsubscribe Endpoint (`apps/api/src/api/routes/unsubscribe.py`)

**Endpoints:**
- `POST /v1/email/unsubscribe` - Unsubscribe email with HMAC token verification (200)
- `GET /v1/email/unsubscribe/token` - Generate token for testing (dev only)

**Features:**
- ✅ HMAC-SHA256 token generation/verification
- ✅ Token format: `HMAC(email:account_id, secret)`
- ✅ No authentication required (uses HMAC token for security)
- ✅ Idempotent: `ON CONFLICT DO NOTHING` for suppressions
- ✅ Inserts into `email_suppressions` table
- ✅ Test endpoint disabled in production

**Security:**
- Uses `UNSUBSCRIBE_SECRET` environment variable
- Constant-time comparison via `hmac.compare_digest()`
- Finds account_id from schedules (validates email is in system)

---

### 3. API Integration (`apps/api/src/api/main.py`)

**Changes:**
- ✅ Added `schedules_router` import and registration
- ✅ Added `unsubscribe_router` import and registration
- ✅ No linting errors

---

## Request/Response Examples

### Create Schedule
```bash
POST /v1/schedules
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "name": "Weekly Market Snapshot - San Diego",
  "report_type": "market_snapshot",
  "city": "San Diego",
  "lookback_days": 30,
  "cadence": "weekly",
  "weekly_dow": 1,
  "send_hour": 9,
  "send_minute": 0,
  "recipients": ["client@example.com", "broker@example.com"],
  "active": true
}
```

**Response (201):**
```json
{
  "id": "abc-123-def-456",
  "name": "Weekly Market Snapshot - San Diego",
  "report_type": "market_snapshot",
  "city": "San Diego",
  "cadence": "weekly",
  "weekly_dow": 1,
  "send_hour": 9,
  "send_minute": 0,
  "recipients": ["client@example.com", "broker@example.com"],
  "active": true,
  "last_run_at": null,
  "next_run_at": null,
  "created_at": "2025-11-10T12:00:00Z"
}
```

---

### List Schedules
```bash
GET /v1/schedules?active_only=true
Authorization: Bearer <jwt>
```

**Response (200):**
```json
{
  "schedules": [
    {
      "id": "abc-123",
      "name": "Weekly Market Snapshot",
      "report_type": "market_snapshot",
      "cadence": "weekly",
      "weekly_dow": 1,
      "active": true,
      "...": "..."
    }
  ],
  "count": 1
}
```

---

### Update Schedule
```bash
PATCH /v1/schedules/{id}
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "active": false,
  "send_hour": 10
}
```

**Response (200):**
```json
{
  "id": "abc-123",
  "message": "Schedule updated"
}
```

**Note:** Updates automatically null `next_run_at` so ticker recomputes timing.

---

### Delete Schedule
```bash
DELETE /v1/schedules/{id}
Authorization: Bearer <jwt>
```

**Response (204 No Content)**

Foreign key cascade deletes all related `schedule_runs`.

---

### Unsubscribe
```bash
POST /v1/email/unsubscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "token": "a1b2c3d4e5f6...",
  "reason": "user_request"
}
```

**Response (200):**
```json
{
  "message": "Email unsubscribed successfully"
}
```

---

## Validation Rules

### Cadence Validation
- **Weekly:** Requires `weekly_dow` (0-6, where 0=Sunday, 6=Saturday)
- **Monthly:** Requires `monthly_dom` (1-28, capped at 28 for safety)

### Email Validation
- Uses Pydantic `EmailStr` for RFC-compliant email validation
- Recipients array must have at least 1 email

### Time Validation
- `send_hour`: 0-23 (24-hour format)
- `send_minute`: 0-59

---

## Database Behavior

### RLS (Row-Level Security)
All queries scope to `account_id` via `set_rls(conn, account_id)`:
```python
cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
```

Only schedules belonging to the authenticated account are visible/modifiable.

### Arrays in PostgreSQL
Recipients and zip_codes stored as PostgreSQL arrays:
```python
recipients_array = "{" + ",".join(payload.recipients) + "}"
cur.execute("... recipients = %s ...", (recipients_array,))
```

### Cascade Deletes
Deleting a schedule automatically deletes all `schedule_runs` via foreign key:
```sql
FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
```

---

## Next Steps

### Testing (Phase 24B continued)
1. Start local API server
2. Create test schedule via Swagger UI (`/docs`)
3. List schedules to verify RLS works
4. Update schedule, verify `next_run_at` nulled
5. Test unsubscribe with generated token

### Phase 24C: Ticker Process
- Create `apps/worker/src/worker/schedules_tick.py`
- Find due schedules every 60 seconds
- Compute `next_run_at` based on cadence
- Enqueue reports to Redis
- Deploy as separate Render Background Worker

---

## Environment Variables Required

### API Service
```bash
UNSUBSCRIBE_SECRET=<random-32-char-string>  # NEW for unsubscribe tokens
```

All other vars (DATABASE_URL, JWT_SECRET, etc.) already configured.

---

## Files Created

1. `apps/api/src/api/routes/schedules.py` (460 lines)
2. `apps/api/src/api/routes/unsubscribe.py` (103 lines)
3. `apps/api/src/api/main.py` (updated)

**Total:** ~563 lines of new API code

**Linting:** ✅ No errors

---

**Status:** 24B ✅ Complete, Ready for 24C (Ticker Process)

