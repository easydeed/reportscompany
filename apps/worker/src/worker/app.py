import os
from celery import Celery

BROKER = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BACKEND = os.getenv("CELERY_RESULT_URL", BROKER)

celery = Celery(
    "market_reports",
    broker=BROKER,
    backend=BACKEND,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "ping": {"queue": "celery"},
    },
    task_time_limit=300,
)

# Import tasks to register them with Celery
from . import tasks  # noqa

