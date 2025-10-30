from .app import celery
import os, time, json, psycopg, redis
from psycopg import sql

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("MR_REPORT_ENQUEUE_KEY", "mr:enqueue:reports")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_reports")

@celery.task(name="ping")
def ping():
    return {"pong": True}

@celery.task(name="generate_report")
def generate_report(run_id: str, account_id: str):
    # Simulate processing; in the future this will render /print/:runId with Playwright and upload to R2/S3
    started = time.perf_counter()
    try:
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            with conn.cursor() as cur:
                # Set RLS context (SET LOCAL doesn't support parameter binding)
                cur.execute(
                    sql.SQL("SET LOCAL app.current_account_id = {}").format(sql.Literal(account_id))
                )
                # mark processing
                cur.execute("UPDATE report_generations SET status='processing' WHERE id = %s", (run_id,))
                # pretend work
                time.sleep(0.5)
                # final urls (placeholders)
                html_url = f"https://example.com/reports/{run_id}.html"
                json_url = f"https://example.com/reports/{run_id}.json"
                cur.execute(
                    """
                    UPDATE report_generations
                    SET status='completed', html_url=%s, json_url=%s, processing_time_ms=%s
                    WHERE id = %s
                    """,
                    (html_url, json_url, int((time.perf_counter()-started)*1000), run_id)
                )
                # usage event
                cur.execute(
                    """
                    INSERT INTO usage_tracking (account_id, event_type, report_id, billable_units, cost_cents)
                    VALUES (%s, 'report_generated', %s, 1, 0)
                    """,
                    (account_id, run_id)
                )
            conn.commit()
        return {"ok": True, "run_id": run_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_redis_consumer_forever():
    r = redis.from_url(REDIS_URL)
    while True:
        item = r.blpop(QUEUE_KEY, timeout=5)
        if not item:
            continue
        _, payload = item
        data = json.loads(payload)
        generate_report.delay(data["run_id"], data["account_id"])

# NOTE: To start the consumer alongside the worker, we will run a second process
# in dev (e.g., `poetry run python -c "from worker.tasks import run_redis_consumer_forever as c;c()"`)
# In Render, we can use a process manager or a small separate service to run the consumer.

