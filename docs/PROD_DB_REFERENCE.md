# Production Database Reference

**Date:** November 20, 2025  
**Status:** Active

---

## Production Stack

### API Service
- **Name:** `reportscompany-api`
- **URL:** https://reportscompany.onrender.com
- **Service ID:** `srv-d474u66uk2gs73eijtlg`
- **Region:** Oregon

### Database
- **Name:** `mr-staging-db` (serves as production database)
- **Database ID:** `dpg-d474qiqli9vc738g17e0-a`
- **Database Name:** `mr_staging_db`
- **Database User:** `mr_staging_db_user`
- **Region:** Oregon
- **PostgreSQL Version:** 17
- **Plan:** `basic_256mb`
- **Storage:** 15 GB

### Connection
The production API service connects to this database via the `DATABASE_URL` environment variable configured in Render.

**Dashboard:** https://dashboard.render.com/d/dpg-d474qiqli9vc738g17e0-a

---

## How to Connect

### Via psql (External Connection)

1. Go to: https://dashboard.render.com/d/dpg-d474qiqli9vc738g17e0-a
2. Click **"Connect"** → **"External Connection"**
3. Copy the connection string:
   ```
   postgresql://mr_staging_db_user:PASSWORD@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db
   ```
4. Connect:
   ```bash
   psql "postgresql://mr_staging_db_user:PASSWORD@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
   ```

### Via Render Web Shell

1. Go to dashboard (link above)
2. Click **"PSQL Command"** tab
3. Opens an authenticated web terminal

---

## Production Domain

- **Frontend:** https://www.trendyreports.io
- **API:** https://reportscompany.onrender.com

Both production services connect to the same PostgreSQL database (`mr-staging-db`).

---

## Demo Accounts

See `docs/PROD_DEMO_ACCOUNTS_CHECKLIST.md` for the canonical demo accounts that must exist in this database.

---

## Schema Management

- Migrations are NOT automated
- Schema changes must be applied manually via SQL scripts
- Always test in staging before applying to production
- Keep migration scripts in `db/migrations/` directory

---

## Backup & Recovery

Render provides automated daily backups for the database. To restore:

1. Go to database dashboard
2. Click "Backups" tab
3. Select backup and restore

---

## Notes

⚠️ **Important:** Despite the name "staging-db", this is the PRODUCTION database used by www.trendyreports.io. The name is historical and should be considered production for all operational purposes.

