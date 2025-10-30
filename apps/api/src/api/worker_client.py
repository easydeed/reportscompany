import os
import json
import redis

# We push a simple JSON job into a Redis list for the worker to pop (decoupled from Celery import).
# The worker will read from this list and call Celery internally. This avoids Celery as an API dep.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("MR_REPORT_ENQUEUE_KEY", "mr:enqueue:reports")


def enqueue_generate_report(run_id: str, account_id: str):
    r = redis.from_url(REDIS_URL)
    r.rpush(QUEUE_KEY, json.dumps({"run_id": run_id, "account_id": account_id}))

