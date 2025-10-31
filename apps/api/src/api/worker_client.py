import os, json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("MR_REPORT_ENQUEUE_KEY", "mr:enqueue:reports")

def enqueue_generate_report(run_id: str, account_id: str, report_type: str, params: dict):
    r = redis.from_url(REDIS_URL)
    r.rpush(QUEUE_KEY, json.dumps({
        "run_id": run_id,
        "account_id": account_id,
        "report_type": report_type,
        "params": params
    }))

