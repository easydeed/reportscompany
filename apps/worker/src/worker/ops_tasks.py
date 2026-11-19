"""LR-027 worker tasks. `ops_heartbeat` is published by the ticker every tick."""
from .app import celery
from .ops_heartbeat import TASK_NAME, WORKER_KEY, WORKER_TTL_S, beat


@celery.task(name=TASK_NAME, ignore_result=True)
def ops_heartbeat():
    """Idempotent: running it twice only rewrites one key."""
    beat(WORKER_KEY, WORKER_TTL_S)
