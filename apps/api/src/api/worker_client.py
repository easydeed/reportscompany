import os, json
import redis
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("MR_REPORT_ENQUEUE_KEY", "mr:enqueue:reports")

# Celery client for sending tasks to worker
celery_app = Celery('worker', broker=REDIS_URL)


def enqueue_generate_report(run_id: str, account_id: str, report_type: str, params: dict):
    """Queue a market report generation task (via Redis queue for consumer bridge)"""
    r = redis.from_url(REDIS_URL)
    r.rpush(QUEUE_KEY, json.dumps({
        "run_id": run_id,
        "account_id": account_id,
        "report_type": report_type,
        "params": params
    }))


def enqueue_property_report(report_id: str):
    """Queue a property report PDF generation task via Celery"""
    celery_app.send_task(
        'generate_property_report',
        args=[report_id],
        queue='celery'
    )

