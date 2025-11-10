from .app import celery
import os, time, json, psycopg, redis, hmac, hashlib, httpx
from datetime import datetime, date
from psycopg import sql
from playwright.sync_api import sync_playwright
from .vendors.simplyrets import fetch_properties
from .compute.extract import PropertyDataExtractor
from .compute.validate import filter_valid
from .compute.calc import snapshot_metrics
from .cache import get as cache_get, set as cache_set
from .query_builders import build_params
from .redis_utils import create_redis_connection

def safe_json_dumps(obj):
    """
    JSON serialization with datetime handling.
    Recursively converts datetime/date objects to ISO format strings.
    This ensures we never have JSON serialization errors.
    """
    def default_handler(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    
    return json.dumps(obj, default=default_handler)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("MR_REPORT_ENQUEUE_KEY", "mr:enqueue:reports")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_reports")
DEV_BASE = os.getenv("PRINT_BASE", "http://localhost:3000")
PDF_DIR = "/tmp/mr_reports"
os.makedirs(PDF_DIR, exist_ok=True)

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

    body = safe_json_dumps({"event": event, "timestamp": int(time.time()), "data": payload}).encode()
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
                payload_json = body.decode()  # Already JSON from safe_json_dumps
                cur.execute("""
                  INSERT INTO webhook_deliveries (account_id, webhook_id, event, payload, response_status, response_ms, error)
                  VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s)
                """, (account_id, hook_id, event, payload_json, status_code, elapsed, error))

@celery.task(name="generate_report")
def generate_report(run_id: str, account_id: str, report_type: str, params: dict):
    started = time.perf_counter()
    pdf_url = html_url = None
    try:
        # 1) Persist 'processing' + input
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("""
                    UPDATE report_generations
                    SET status='processing', input_params=%s, source_vendor='simplyrets'
                    WHERE id=%s
                """, (safe_json_dumps(params or {}), run_id))
            conn.commit()

        # 2) Compute results (cache by report_type + params hash)
        city = (params or {}).get("city") or (params or {}).get("zips", [])[0] if (params or {}).get("zips") else "Houston"
        lookback = int((params or {}).get("lookback_days") or 30)
        cache_payload = {"type": report_type, "params": params}
        result = cache_get("report", cache_payload)
        if not result:
            # Build SimplyRETS query using query_builders
            q = build_params(report_type, params or {})
            raw = fetch_properties(q, limit=800)
            extracted = PropertyDataExtractor(raw).run()
            clean = filter_valid(extracted)
            metrics = snapshot_metrics(clean)
            result = {
                "report_type": report_type,
                "city": city,
                "lookback_days": lookback,
                "generated_at": int(time.time()),
                "counts": {
                    "Active": metrics["total_active"],
                    "Pending": metrics["total_pending"],
                    "Closed": metrics["total_closed"],
                },
                "metrics": metrics,
                "listings_sample": clean[:20]
            }
            cache_set("report", cache_payload, result, ttl_s=3600)

        # 3) Save result_json
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("UPDATE report_generations SET result_json=%s WHERE id=%s", (safe_json_dumps(result), run_id))

        # 4) Generate PDF (Playwright) and final links
        url = f"{DEV_BASE}/print/{run_id}"
        pdf_path = os.path.join(PDF_DIR, f"{run_id}.pdf")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(device_scale_factor=2)
            page.goto(url, wait_until="networkidle")
            page.pdf(path=pdf_path, format="Letter", print_background=True,
                     margin={"top":"0.5in","right":"0.5in","bottom":"0.5in","left":"0.5in"})
            browser.close()
        html_url = url
        json_url = f"https://example.com/reports/{run_id}.json"
        pdf_url  = f"http://localhost:10000/dev-files/reports/{run_id}.pdf"

        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("""
                    UPDATE report_generations
                    SET status='completed', html_url=%s, json_url=%s, pdf_url=%s, processing_time_ms=%s
                    WHERE id = %s
                """, (html_url, json_url, pdf_url, int((time.perf_counter()-started)*1000), run_id))

        # 5) Webhook
        payload = {"report_id": run_id, "status": "completed", "html_url": html_url, "pdf_url": pdf_url}
        _deliver_webhooks(account_id, "report.completed", payload)
        return {"ok": True, "run_id": run_id}

    except Exception as e:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("UPDATE report_generations SET status='failed', error=%s WHERE id=%s", (str(e), run_id))
        return {"ok": False, "error": str(e)}


def run_redis_consumer_forever():
    """
    Redis consumer bridge - polls Redis queue and dispatches to Celery worker.
    Uses proper SSL configuration for secure Redis connections (Upstash).
    """
    r = create_redis_connection(REDIS_URL)
    print(f"🔄 Redis consumer started, polling queue: {QUEUE_KEY}")
    while True:
        item = r.blpop(QUEUE_KEY, timeout=5)
        if not item:
            continue
        _, payload = item
        data = json.loads(payload)
        print(f"📥 Received job: run_id={data['run_id']}, type={data['report_type']}")
        generate_report.delay(data["run_id"], data["account_id"], data["report_type"], data.get("params") or {})

# NOTE: To start the consumer alongside the worker, we will run a second process
# in dev (e.g., `poetry run python -c "from worker.tasks import run_redis_consumer_forever as c;c()"`)
# In Render, we can use a process manager or a small separate service to run the consumer.

