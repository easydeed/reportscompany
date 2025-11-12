from .app import celery
import os, time, json, psycopg, redis, hmac, hashlib, httpx
from datetime import datetime, date
from psycopg import sql
from .vendors.simplyrets import fetch_properties
from .compute.extract import PropertyDataExtractor
from .compute.validate import filter_valid
from .compute.calc import snapshot_metrics
from .cache import get as cache_get, set as cache_set
from .query_builders import build_params
from .redis_utils import create_redis_connection
from .pdf_engine import render_pdf
from .email.send import send_schedule_email
import boto3
from botocore.client import Config

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

# Cloudflare R2 Configuration
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""

def upload_to_r2(local_path: str, s3_key: str) -> str:
    """
    Upload file to Cloudflare R2 and return presigned URL.
    
    Args:
        local_path: Local file path to upload
        s3_key: S3 key (e.g., "reports/account-id/run-id.pdf")
    
    Returns:
        Presigned URL valid for 7 days
    """
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        # Fallback for local dev: return local file URL
        print("⚠️  R2 credentials not set, skipping upload")
        return f"http://localhost:10000/dev-files/{s3_key}"
    
    # Create R2 client (S3-compatible)
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto',  # R2 uses 'auto' region
        config=Config(signature_version='s3v4')
    )
    
    # Upload file
    print(f"☁️  Uploading to R2: {s3_key}")
    with open(local_path, 'rb') as f:
        s3_client.upload_fileobj(
            f,
            R2_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
    
    # Generate presigned URL (7 days)
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': R2_BUCKET_NAME,
            'Key': s3_key
        },
        ExpiresIn=604800  # 7 days in seconds
    )
    
    print(f"✅ Uploaded to R2: {presigned_url[:100]}...")
    return presigned_url

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

        # 4) Generate PDF (via configured engine: playwright or pdfshift)
        pdf_path, html_url = render_pdf(
            run_id=run_id,
            account_id=account_id,
            html_content=None,  # Will navigate to /print/{run_id}
            print_base=DEV_BASE
        )
        
        # 5) Upload PDF to Cloudflare R2
        s3_key = f"reports/{account_id}/{run_id}.pdf"
        pdf_url = upload_to_r2(pdf_path, s3_key)
        
        # JSON URL (future: could upload result_json to R2 too)
        json_url = f"{DEV_BASE}/api/reports/{run_id}/data"

        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("""
                    UPDATE report_generations
                    SET status='completed', html_url=%s, json_url=%s, pdf_url=%s, processing_time_ms=%s
                    WHERE id = %s
                """, (html_url, json_url, pdf_url, int((time.perf_counter()-started)*1000), run_id))

        # 6) Send email if this was triggered by a schedule
        schedule_id = (params or {}).get("schedule_id")
        if schedule_id and pdf_url:
            try:
                print(f"📧 Sending schedule email for schedule_id={schedule_id}")
                
                # Load schedule details and account name
                with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                        
                        # Get schedule recipients
                        cur.execute("""
                            SELECT recipients, city, zip_codes
                            FROM schedules
                            WHERE id = %s
                        """, (schedule_id,))
                        schedule_row = cur.fetchone()
                        
                        if not schedule_row:
                            print(f"⚠️  Schedule {schedule_id} not found, skipping email")
                        else:
                            recipients, city, zip_codes = schedule_row
                            
                            # Get account name
                            cur.execute("SELECT name FROM accounts WHERE id = %s", (account_id,))
                            account_row = cur.fetchone()
                            account_name = account_row[0] if account_row else None
                            
                            # Build email payload
                            email_payload = {
                                "report_type": report_type,
                                "city": city,
                                "zip_codes": zip_codes,
                                "lookback_days": lookback,
                                "metrics": result.get("metrics", {}),
                                "pdf_url": pdf_url,
                            }
                            
                            # Send email
                            status_code, response_text = send_schedule_email(
                                account_id=account_id,
                                recipients=recipients,
                                payload=email_payload,
                                account_name=account_name,
                            )
                            
                            # Log email send
                            subject = f"Your {report_type.replace('_', ' ').title()} Report"
                            cur.execute("""
                                INSERT INTO email_log (account_id, schedule_id, report_id, provider, to_emails, subject, response_code, error)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                account_id,
                                schedule_id,
                                run_id,
                                'sendgrid',
                                recipients,
                                subject,
                                status_code,
                                response_text if status_code != 202 else None
                            ))
                            
                            # Update schedule_runs to mark as completed
                            cur.execute("""
                                UPDATE schedule_runs
                                SET status = 'completed',
                                    report_run_id = %s,
                                    finished_at = NOW()
                                WHERE schedule_id = %s
                                  AND status = 'queued'
                                  AND started_at IS NULL
                                ORDER BY created_at DESC
                                LIMIT 1
                            """, (run_id, schedule_id))
                            
                            conn.commit()
                            print(f"✅ Email sent to {len(recipients)} recipient(s), status: {status_code}")
                
            except Exception as email_error:
                print(f"⚠️  Email send failed: {email_error}")
                # Don't fail the whole task if email fails
                with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO email_log (account_id, schedule_id, report_id, provider, to_emails, subject, response_code, error)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            account_id,
                            schedule_id,
                            run_id,
                            'sendgrid',
                            [],
                            'Failed to send',
                            500,
                            str(email_error)
                        ))

        # 7) Webhook
        payload = {"report_id": run_id, "status": "completed", "html_url": html_url, "pdf_url": pdf_url, "json_url": json_url}
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

