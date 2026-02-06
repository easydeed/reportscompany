# Task: Add Keep-Alive Ping to Celery Worker

## Goal

Add a scheduled Celery task that pings the API every 5 minutes to prevent cold starts on Render.

## Background

The API service at `https://reportscompany.onrender.com` can go cold after periods of inactivity, causing slow first requests (13+ second TTFB). We already have a Celery worker with beat scheduler running — use it to keep the API warm.

---

## Implementation

### Step 1: Add the task to `apps/worker/src/worker/tasks.py`

Add this task near the other utility tasks (like `ping` if it exists):

```python
@celery.task(name="keep_api_warm")
def keep_api_warm():
    """
    Ping the API health endpoint to prevent Render cold starts.
    Runs every 5 minutes via Celery beat.
    """
    import httpx
    import os
    
    api_url = os.getenv("API_BASE_URL", "https://reportscompany.onrender.com")
    
    try:
        response = httpx.get(f"{api_url}/health", timeout=10.0)
        logger.info(f"API keep-alive ping: {response.status_code}")
    except httpx.TimeoutException:
        logger.warning("API keep-alive ping timed out")
    except Exception as e:
        logger.warning(f"API keep-alive ping failed: {e}")
    
    # Always succeed — this is just a ping, failures don't matter
    return {"status": "pinged"}
```

### Step 2: Add to Celery beat schedule

Find where `beat_schedule` is defined. It's likely in one of these files:
- `apps/worker/src/worker/celery_app.py`
- `apps/worker/src/worker/celery_config.py`
- `apps/worker/src/worker/config.py`

Add the keep-alive task to the schedule:

```python
beat_schedule = {
    # ... existing schedules like schedules_tick ...
    
    "keep-api-warm": {
        "task": "keep_api_warm",
        "schedule": 300.0,  # Every 5 minutes (300 seconds)
    },
}
```

If using `crontab` style instead of seconds:

```python
from celery.schedules import crontab

beat_schedule = {
    # ... existing schedules ...
    
    "keep-api-warm": {
        "task": "keep_api_warm",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}
```

### Step 3: Verify httpx is available

Check `apps/worker/pyproject.toml` — httpx should already be there since it's used elsewhere in the worker. If not, add it:

```toml
[tool.poetry.dependencies]
httpx = "^0.27.0"
```

---

## Environment Variable

Add `API_BASE_URL` to the worker's environment in Render (or it will default to production URL):

```
API_BASE_URL=https://reportscompany.onrender.com
```

This lets you point to different environments if needed.

---

## Verification

After deploying:

1. Check Celery beat logs — should see the task being scheduled
2. Check worker logs — should see "API keep-alive ping: 200" every 5 minutes
3. Check Render API metrics — should see consistent traffic instead of gaps

---

## Files to Modify

| File | Change |
|------|--------|
| `apps/worker/src/worker/tasks.py` | Add `keep_api_warm` task |
| `apps/worker/src/worker/celery_app.py` (or config file) | Add to `beat_schedule` |
| Render worker environment | Add `API_BASE_URL` variable (optional) |

---

## Expected Result

The API will receive a health check ping every 5 minutes from your own worker, preventing cold starts without relying on external cron services.
