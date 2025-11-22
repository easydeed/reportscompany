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
from .report_builders import build_result_json
from .limit_checker import check_usage_limit, log_limit_decision_worker
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


def resolve_recipients_to_emails(cur, account_id: str, recipients_raw: list) -> list:
    """
    Resolve typed recipients to a list of email addresses.

    Handles recipient types:
    - contact: {"type":"contact","id":"<contact_id>"} -> lookup from contacts table
    - sponsored_agent: {"type":"sponsored_agent","id":"<account_id>"} -> lookup from users/accounts
    - group: {"type":"group","id":"<group_id>"} -> expand members to contact/sponsored_agent and resolve
    - manual_email: {"type":"manual_email","email":"<email>"} -> use directly
    - Plain strings: Legacy format, treated as manual_email

    Returns a deduplicated list of valid email addresses.
    """
    emails: list[str] = []

    def add_contact_email(contact_id: str):
        cur.execute(
            """
            SELECT email
            FROM contacts
            WHERE id = %s::uuid AND account_id = %s::uuid
            """,
            (contact_id, account_id),
        )
        row = cur.fetchone()
        if row and row[0]:
            emails.append(row[0])
        else:
            print(f"⚠️  Contact {contact_id} not found or has no email")

    def add_sponsored_agent_email(agent_account_id: str):
        # Verify sponsorship
        cur.execute(
            """
            SELECT a.id::text
            FROM accounts a
            WHERE a.id = %s::uuid
              AND a.sponsor_account_id = %s::uuid
            """,
            (agent_account_id, account_id),
        )

        if cur.fetchone():
            # Get agent's primary email from users
            cur.execute(
                """
                SELECT u.email
                FROM users u
                WHERE u.account_id = %s::uuid
                ORDER BY u.created_at
                LIMIT 1
                """,
                (agent_account_id,),
            )
            row = cur.fetchone()
            if row and row[0]:
                emails.append(row[0])
            else:
                print(f"⚠️  Sponsored agent {agent_account_id} has no user email")
        else:
            print(f"⚠️  Sponsored agent {agent_account_id} not sponsored by {account_id}")

    for recipient_str in recipients_raw:
        try:
            # Try to parse as JSON
            if recipient_str.startswith("{"):
                recipient = json.loads(recipient_str)
                recipient_type = recipient.get("type")

                if recipient_type == "contact":
                    contact_id = recipient.get("id")
                    if contact_id:
                        add_contact_email(contact_id)

                elif recipient_type == "sponsored_agent":
                    agent_account_id = recipient.get("id")
                    if agent_account_id:
                        add_sponsored_agent_email(agent_account_id)

                elif recipient_type == "group":
                    group_id = recipient.get("id")
                    if group_id:
                        # Verify group belongs to this account and load members
                        cur.execute(
                            """
                            SELECT 1 FROM contact_groups
                            WHERE id = %s::uuid AND account_id = %s::uuid
                            """,
                            (group_id, account_id),
                        )
                        if not cur.fetchone():
                            print(f"⚠️  Group {group_id} not found for account {account_id}")
                            continue

                        cur.execute(
                            """
                            SELECT member_type, member_id::text
                            FROM contact_group_members
                            WHERE group_id = %s::uuid AND account_id = %s::uuid
                            """,
                            (group_id, account_id),
                        )
                        for member_type, member_id in cur.fetchall():
                            if member_type == "contact":
                                add_contact_email(member_id)
                            elif member_type == "sponsored_agent":
                                add_sponsored_agent_email(member_id)

                elif recipient_type == "manual_email":
                    # Use email directly
                    email = recipient.get("email")
                    if email:
                        emails.append(email)
                else:
                    print(f"⚠️  Unknown recipient type: {recipient_type}")
            else:
                # Legacy plain email string
                emails.append(recipient_str)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"⚠️  Error parsing recipient '{recipient_str}': {e}")
            # Treat as plain email if JSON parsing fails
            if "@" in recipient_str:
                emails.append(recipient_str)

    # Deduplicate and filter empties
    return list(set([e for e in emails if e and "@" in e]))

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
    schedule_id = (params or {}).get("schedule_id")  # Check if this is a scheduled report
    
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
        
        # ===== PHASE 29B: CHECK USAGE LIMITS FOR SCHEDULED REPORTS =====
        if schedule_id:
            with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
                with conn.cursor() as cur:
                    decision, info = check_usage_limit(cur, account_id)
                    log_limit_decision_worker(account_id, decision, info)
                    
                    # Block scheduled reports if limit reached (non-overage plans)
                    if decision == "BLOCK":
                        print(f"🚫 Skipping scheduled report due to limit: {info.get('message', '')}")
                        
                        # Mark report as skipped
                        cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                        cur.execute("""
                            UPDATE report_generations
                            SET status='skipped_limit', 
                                error_message=%s,
                                processing_time_ms=%s
                            WHERE id=%s
                        """, (
                            info.get('message', 'Monthly report limit reached'),
                            int((time.perf_counter()-started)*1000),
                            run_id
                        ))
                        
                        # Update schedule_runs if it exists
                        try:
                            cur.execute("""
                                UPDATE schedule_runs
                                SET status='skipped_limit', finished_at=NOW()
                                WHERE report_run_id=%s
                            """, (run_id,))
                        except Exception:
                            pass  # Table might not exist yet
                        
                        conn.commit()
                        
                        # Return early - don't generate report
                        return {"ok": False, "reason": "limit_reached", "run_id": run_id}
        # ===== END PHASE 29B =====

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
            
            # Build context for report builders
            context = {
                "city": city,
                "lookback_days": lookback,
                "generated_at": int(time.time()),
            }
            
            # Use report builder dispatcher to create result_json
            result = build_result_json(report_type, clean, context)
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
                            recipients_raw, city, zip_codes = schedule_row
                            
                            # Resolve typed recipients to email addresses
                            recipients = resolve_recipients_to_emails(cur, account_id, recipients_raw)
                            
                            # Get account name
                            cur.execute("SELECT name FROM accounts WHERE id = %s", (account_id,))
                            account_row = cur.fetchone()
                            account_name = account_row[0] if account_row else None
                            
                            # Phase 30: Resolve brand for white-label emails
                            brand = None
                            try:
                                # Determine branding account (sponsor for REGULAR, self for AFFILIATE)
                                cur.execute("""
                                    SELECT account_type, sponsor_account_id::text
                                    FROM accounts
                                    WHERE id = %s::uuid
                                """, (account_id,))
                                acc_row = cur.fetchone()
                                
                                if acc_row:
                                    acc_type, sponsor_id = acc_row
                                    branding_account_id = sponsor_id if (acc_type == 'REGULAR' and sponsor_id) else account_id
                                    
                                    # Load branding config
                                    cur.execute("""
                                        SELECT
                                            brand_display_name,
                                            logo_url,
                                            primary_color,
                                            accent_color,
                                            rep_photo_url,
                                            contact_line1,
                                            contact_line2,
                                            website_url
                                        FROM affiliate_branding
                                        WHERE account_id = %s::uuid
                                    """, (branding_account_id,))
                                    
                                    brand_row = cur.fetchone()
                                    if brand_row:
                                        brand = {
                                            "display_name": brand_row[0],
                                            "logo_url": brand_row[1],
                                            "primary_color": brand_row[2],
                                            "accent_color": brand_row[3],
                                            "rep_photo_url": brand_row[4],
                                            "contact_line1": brand_row[5],
                                            "contact_line2": brand_row[6],
                                            "website_url": brand_row[7],
                                        }
                            except Exception as e:
                                print(f"⚠️  Error loading brand for email: {e}")
                                # Continue without brand (will use default branding)
                            
                            # Build email payload
                            email_payload = {
                                "report_type": report_type,
                                "city": city,
                                "zip_codes": zip_codes,
                                "lookback_days": lookback,
                                "metrics": result.get("metrics", {}),
                                "pdf_url": pdf_url,
                            }
                            
                            # Send email (with suppression checking + Phase 30 white-label brand)
                            status_code, response_text = send_schedule_email(
                                account_id=account_id,
                                recipients=recipients,
                                payload=email_payload,
                                account_name=account_name,
                                db_conn=conn,  # Pass connection for suppression checking
                                brand=brand,  # Phase 30: white-label branding
                            )
                            
                            # Log email send (defensive try/except)
                            try:
                                # Determine status based on response
                                if status_code == 202:
                                    email_status = 'sent'
                                elif status_code == 200 and 'suppressed' in response_text.lower():
                                    email_status = 'suppressed'
                                else:
                                    email_status = 'failed'
                                
                                subject = f"Your {report_type.replace('_', ' ').title()} Report"
                                cur.execute("""
                                    INSERT INTO email_log (
                                        account_id, schedule_id, report_id, provider,
                                        to_emails, subject, response_code, status, error
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    account_id,
                                    schedule_id,
                                    run_id,
                                    'sendgrid',
                                    recipients,
                                    subject,
                                    status_code,
                                    email_status,
                                    None if status_code in (200, 202) else response_text
                                ))
                            except Exception as log_error:
                                logger.warning(f"Failed to log email send (non-critical): {log_error}")
                            
                            # Update schedule_runs to mark as completed (defensive try/except)
                            try:
                                run_status = 'completed' if status_code in (200, 202) else 'failed_email'
                                cur.execute("""
                                    UPDATE schedule_runs
                                    SET status = %s,
                                        report_run_id = %s,
                                        finished_at = NOW()
                                    WHERE id = (
                                        SELECT id
                                        FROM schedule_runs
                                        WHERE schedule_id = %s
                                          AND status = 'queued'
                                          AND started_at IS NULL
                                        ORDER BY created_at DESC
                                        LIMIT 1
                                    )
                                """, (run_status, run_id, schedule_id))
                            except Exception as update_error:
                                logger.warning(f"Failed to update schedule_run status (non-critical): {update_error}")
                            
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

