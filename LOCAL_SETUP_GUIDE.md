# Local Development Setup Guide

**Date:** November 10, 2025  
**Status:** Fresh Docker Desktop installation

---

## Prerequisites ✅

- ✅ Docker Desktop installed
- ✅ Git Bash (or WSL) for running bash scripts
- ✅ Node.js v20+ (for frontend)
- ✅ Python 3.11+ (for API/Worker)
- ✅ pnpm (for monorepo)

---

## Step 1: Start Docker Services

### Start Docker Desktop
1. Open **Docker Desktop** application
2. Wait for it to fully start (green icon in system tray)
3. Verify it's running: Open PowerShell and run:
   ```powershell
   docker --version
   ```

### Start Database Services (PostgreSQL + Redis)

```powershell
# From project root
docker compose up -d
```

**What this does:**
- Starts PostgreSQL 15 on port 5432
- Starts Redis 7 on port 6379
- Creates persistent volumes for data
- Runs health checks

### Verify Services Running

```powershell
docker compose ps
```

**Expected output:**
```
NAME         IMAGE              STATUS         PORTS
mr_postgres  postgres:15-alpine Up (healthy)   0.0.0.0:5432->5432/tcp
mr_redis     redis:7-alpine     Up (healthy)   0.0.0.0:6379->6379/tcp
```

### Check Logs (if needed)

```powershell
# All services
docker compose logs

# Just Postgres
docker compose logs postgres

# Just Redis
docker compose logs redis
```

---

## Step 2: Run Database Migrations

Now that Postgres is running, apply all migrations:

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/market_reports"
bash scripts/migrate.sh
```

**What this does:**
- Runs all SQL files in `db/migrations/` in order
- Creates tables: accounts, users, reports, schedules, etc.
- Enables Row-Level Security
- Seeds demo account

**Expected output:**
```
Running migration: 0001_base.sql
Running migration: 0002_webhooks.sql
Running migration: 0003_billing.sql
Running migration: 0004_report_payloads.sql
Running migration: 0005_seed_demo.sql
Running migration: 0006_schedules.sql
✅ All migrations applied successfully
```

### Verify Tables Created

```powershell
docker exec mr_postgres psql -U postgres -d market_reports -c "\dt"
```

**Expected:** 13+ tables including `schedules`, `schedule_runs`, `email_log`, etc.

---

## Step 3: Install Dependencies

### API (FastAPI)

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install poetry
poetry install
```

### Worker (Celery)

```powershell
cd apps/worker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install poetry
poetry install

# Optional: Install Playwright for local PDF generation
python -m playwright install chromium
```

### Frontend (Next.js)

```powershell
# From project root
pnpm install
```

---

## Step 4: Configure Environment Variables

### API (.env)

Create `apps/api/.env`:
```bash
PORT=10000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/market_reports
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-secret-change-in-production
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Worker (.env)

Create `apps/worker/.env`:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/market_reports
REDIS_URL=redis://localhost:6379/0
SIMPLYRETS_USERNAME=simplyrets
SIMPLYRETS_PASSWORD=simplyrets
PRINT_BASE=http://localhost:3000
PDF_ENGINE=playwright
```

### Frontend (.env.local)

Create `apps/web/.env.local`:
```bash
NEXT_PUBLIC_API_BASE=http://localhost:10000
NEXT_PUBLIC_DEMO_ACCOUNT_ID=912014c3-6deb-4b40-a28d-489ef3923a3a
```

---

## Step 5: Start Development Services

### Terminal 1: API
```powershell
cd apps/api
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10000
```
→ API running at http://localhost:10000

### Terminal 2: Worker
```powershell
cd apps/worker
.\.venv\Scripts\Activate.ps1
celery -A worker.app.celery worker -l info --pool=solo
```
→ Celery worker ready

### Terminal 3: Frontend
```powershell
cd apps/web
pnpm dev
```
→ Frontend running at http://localhost:3000

---

## Step 6: Verify Everything Works

### Test API Health
Open browser: http://localhost:10000/health

**Expected:**
```json
{"ok": true, "service": "market-reports-api"}
```

### Test Frontend
Open browser: http://localhost:3000

**Expected:** Marketing site homepage

### Test Report Generation
1. Go to http://localhost:3000/app/reports/new
2. Select "Market Snapshot"
3. Enter "Houston" as city (demo account)
4. Select 30-day lookback
5. Click "Generate Report"

**Expected:** Report generates, shows in list with "Completed" status

---

## Daily Workflow

### Start Everything
```powershell
# Start Docker services
docker compose up -d

# Check they're healthy
docker compose ps
```

### Stop Everything
```powershell
# Stop Docker services (keeps data)
docker compose stop

# Or stop and remove containers (keeps data in volumes)
docker compose down
```

### Reset Database (WARNING: Deletes all data)
```powershell
# Stop and remove volumes
docker compose down -v

# Start fresh
docker compose up -d

# Re-run migrations
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/market_reports"
bash scripts/migrate.sh
```

---

## Useful Commands

### Docker

```powershell
# View logs
docker compose logs -f

# Restart a service
docker compose restart postgres

# Execute command in Postgres
docker exec -it mr_postgres psql -U postgres -d market_reports

# Execute command in Redis
docker exec -it mr_redis redis-cli
```

### Database

```powershell
# Connect to Postgres
docker exec -it mr_postgres psql -U postgres -d market_reports

# List tables
docker exec mr_postgres psql -U postgres -d market_reports -c "\dt"

# Run SQL
docker exec mr_postgres psql -U postgres -d market_reports -c "SELECT * FROM accounts;"
```

### Makefile Shortcuts

```powershell
# Start Docker services
make db-up

# Stop Docker services
make db-down

# Run migrations
make migrate

# Check status
make status
```

---

## Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:5432 failed: port is already allocated`

**Fix:**
```powershell
# Find what's using port 5432
netstat -ano | findstr :5432

# Stop the process (replace PID)
taskkill /PID <process_id> /F

# Or change port in docker-compose.yml
```

### Docker Not Starting

**Fix:**
1. Open Docker Desktop
2. Go to Settings → Resources
3. Ensure WSL 2 integration enabled (if using WSL)
4. Restart Docker Desktop

### Migration Fails

**Error:** `Connection refused`

**Fix:**
```powershell
# Check Postgres is running
docker compose ps

# Check logs
docker compose logs postgres

# Restart if needed
docker compose restart postgres
```

### "bash: command not found"

**Fix:** Use Git Bash or WSL to run bash scripts. Or convert to PowerShell:

```powershell
# Instead of: bash scripts/migrate.sh
# Use Docker directly:
Get-ChildItem db/migrations/*.sql | ForEach-Object {
    docker exec mr_postgres psql -U postgres -d market_reports -f "/tmp/$($_.Name)"
}
```

---

## What's Running Where

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| PostgreSQL | 5432 | localhost:5432 | Database |
| Redis | 6379 | localhost:6379 | Cache/Queue |
| API | 10000 | http://localhost:10000 | FastAPI Backend |
| Worker | - | - | Celery (background jobs) |
| Frontend | 3000 | http://localhost:3000 | Next.js App |

---

## Next Steps

After local setup:
1. ✅ Generate test report (verify end-to-end works)
2. ✅ Check worker logs (verify PDF generation)
3. ✅ Test schedules table (verify migration worked)
4. 🔄 Continue with Phase 24B (API routes for schedules)

---

**Status:** Ready for local development! 🚀

