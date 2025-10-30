from .app import celery
import os, time, json, psycopg, redis, hmac, hashlib, httpx
from psycopg import sql
from playwright.sync_api import sync_playwright

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("MR_REPORT_ENQUEUE_KEY", "mr:enqueue:reports")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_reports")
PDF_DIR = "/tmp/mr_reports"
os.makedirs(PDF_DIR, exist_ok=True)
DEV_BASE = os.getenv("PRINT_BASE", "http://localhost:3000")

@celery.task(name="ping")
def ping():
    return {"pong": True}

def _sign(secret: str, body: bytes, ts: str) -> str:
    mac = hmac.new(secret.encode(), msg=(ts + ".").encode() + body, digestmod=hashlib.sha256)
    return "sha256=" + mac.hexdigest()

def _deliver_webhooks(account_id: str, event: str, payload: dict):
    with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
            cur.execute("SELECT id::text, url, secret FROM webhooks WHERE is_active=TRUE")
            hooks = cur.fetchall()
        conn.commit()

    if not hooks:
        return

    body = json.dumps({"event": event, "timestamp": int(time.time()), "data": payload}).encode()
    for hook_id, url, secret in hooks:
        ts = str(int(time.time()))
        sig = _sign(secret, body, ts)
        started = time.perf_counter()
        status_code = None
        error = None
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Market-Reports-Event": event,
                        "X-Market-Reports-Timestamp": ts,
                        "X-Market-Reports-Signature": sig,
                    },
                )
                status_code = resp.status_code
        except Exception as e:
            error = str(e)

        elapsed = int((time.perf_counter()-started)*1000)
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Convert dict to JSON string for JSONB column
                payload_json = json.dumps(json.loads(body.decode()))
                cur.execute("""
                  INSERT INTO webhook_deliveries (account_id, webhook_id, event, payload, response_status, response_ms, error)
                  VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s)
                """, (account_id, hook_id, event, payload_json, status_code, elapsed, error))

@celery.task(name="generate_report")
def generate_report(run_id: str, account_id: str):
    started = time.perf_counter()
    try:
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("UPDATE report_generations SET status='processing' WHERE id = %s", (run_id,))

                # Render /print/:runId and save PDF
                url = f"{DEV_BASE}/print/{run_id}"
                pdf_path = os.path.join(PDF_DIR, f"{run_id}.pdf")
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page(device_scale_factor=2)
                    page.goto(url, wait_until="networkidle")
                    page.pdf(
                        path=pdf_path, 
                        format="Letter", 
                        print_background=True,
                        margin={"top":"0.5in","right":"0.5in","bottom":"0.5in","left":"0.5in"}
                    )
                    browser.close()

                html_url = url
                json_url = f"https://example.com/reports/{run_id}.json"  # placeholder
                pdf_url = f"http://localhost:10000/dev-files/reports/{run_id}.pdf"
                processing_time = int((time.perf_counter()-started)*1000)

                cur.execute("""
                  UPDATE report_generations
                  SET status='completed', html_url=%s, json_url=%s, pdf_url=%s, processing_time_ms=%s
                  WHERE id = %s
                """, (html_url, json_url, pdf_url, processing_time, run_id))

                cur.execute("""
                  INSERT INTO usage_tracking (account_id, event_type, report_id, billable_units, cost_cents)
                  VALUES (%s, 'report_generated', %s, 1, 0)
                """, (account_id, run_id))

            conn.commit()

        # Deliver webhook after commit
        payload = {
            "report_id": run_id, 
            "status": "completed", 
            "html_url": html_url, 
            "pdf_url": pdf_url,
            "processing_time_ms": processing_time
        }
        _deliver_webhooks(account_id, "report.completed", payload)
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

