from .app import celery
import os, time, json, psycopg, redis, hmac, hashlib, httpx, logging
from datetime import datetime, date

logger = logging.getLogger(__name__)
from psycopg import sql
from .vendors.simplyrets import fetch_properties
from .compute.extract import PropertyDataExtractor
from .compute.validate import filter_valid
from .compute.calc import snapshot_metrics
from .cache import get as cache_get, set as cache_set
from .query_builders import build_params, build_market_snapshot, build_market_snapshot_closed, build_market_snapshot_pending
from .redis_utils import create_redis_connection
from .pdf_engine import render_pdf
from .email.send import send_schedule_email
from .report_builders import build_result_json
from .limit_checker import check_usage_limit, log_limit_decision_worker
from .utils.photo_proxy import proxy_report_photos_inplace
from .filter_resolver import compute_market_stats, resolve_filters, build_filters_label, elastic_widen_filters
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

@celery.task(
    name="generate_report",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_kwargs={"max_retries": 3},
)
def generate_report(self, run_id: str, account_id: str, report_type: str, params: dict):
    started = time.perf_counter()
    pdf_url = html_url = None
    schedule_id = (params or {}).get("schedule_id")  # Check if this is a scheduled report
    
    # PHASE 1: STRUCTURED LOGGING FOR DEBUGGING
    print(f"🔍 REPORT RUN {run_id}: start (account={account_id}, type={report_type})")
    
    try:
        # 1) Persist 'processing' + input
        print(f"🔍 REPORT RUN {run_id}: step=persist_status")
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("""
                    UPDATE report_generations
                    SET status='processing', input_params=%s, source_vendor='simplyrets'
                    WHERE id=%s
                """, (safe_json_dumps(params or {}), run_id))
            conn.commit()
        print(f"✅ REPORT RUN {run_id}: persist_status complete")
        
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
        print(f"🔍 REPORT RUN {run_id}: step=data_fetch")
        # Fix: Properly extract city from params - don't default to Houston
        _params = params or {}
        city = _params.get("city")
        zips = _params.get("zips")
        if not city and zips:
            # For ZIP-based reports, use ZIP code(s) as the "city" label
            # The _filter_by_city function knows to skip filtering when city is a ZIP
            city = ", ".join(zips[:3]) + ("..." if len(zips) > 3 else "")
        if not city:
            city = "Unknown"  # Don't default to Houston - this indicates a problem
        print(f"🔍 REPORT RUN {run_id}: city={city}, zips={zips}")
        lookback = int(_params.get("lookback_days") or 30)
        # ===== MARKET-ADAPTIVE FILTER RESOLUTION =====
        # If filters include a price_strategy, resolve percentages to actual dollars
        # based on the market's median prices. This makes presets work across all markets.
        filters = _params.get("filters") or {}
        print(f"🔍 REPORT RUN {run_id}: filters={filters}")  # DEBUG: Show what filters we received
        resolved_filters = None
        market_stats = None
        filters_label = None
        
        if filters.get("price_strategy"):
            print(f"🔍 REPORT RUN {run_id}: Market-adaptive pricing detected, computing median first")
            
            # Step 1: Fetch baseline listings for median calculation
            # Use location + type=RES + subtype only (don't apply bed/bath filters yet)
            baseline_params = {
                "city": city,
                "zips": zips,
                "lookback_days": 90,  # Use 90 days for stable median
                "filters": {"subtype": filters.get("subtype")} if filters.get("subtype") else {}
            }
            baseline_query = build_params("inventory", baseline_params)
            print(f"🔍 REPORT RUN {run_id}: baseline_query for median={baseline_query}")
            baseline_raw = fetch_properties(baseline_query, limit=500)
            print(f"🔍 REPORT RUN {run_id}: fetched {len(baseline_raw)} baseline listings for median")
            
            # Step 2: Compute market stats
            baseline_extracted = PropertyDataExtractor(baseline_raw).run()
            market_stats = compute_market_stats(baseline_extracted)
            print(f"🔍 REPORT RUN {run_id}: market_stats={market_stats}")
            
            # Step 3: Resolve filters (convert % to actual $)
            resolved_filters = resolve_filters(filters, market_stats)
            print(f"🔍 REPORT RUN {run_id}: resolved_filters={resolved_filters}")
            
            # Step 4: Build human-readable label for PDF/email
            filters_label = build_filters_label(filters, resolved_filters, market_stats)
            print(f"🔍 REPORT RUN {run_id}: filters_label={filters_label}")
            
            # Update params with resolved filters for query builders
            _params = {**_params, "filters": resolved_filters}
        
        cache_payload = {"type": report_type, "params": params}
        result = cache_get("report", cache_payload)
        if not result:
            print(f"🔍 REPORT RUN {run_id}: cache_miss, fetching from SimplyRETS")
            
            # Normalize report type for comparison
            rt_normalized = (report_type or "market_snapshot").lower().replace("_", "-").replace(" ", "-")
            
            # For Market Snapshot: Query Active, Closed, and Pending SEPARATELY for accurate metrics
            # Per ReportsGuide.md: Each status type needs its own query for accurate counts
            if rt_normalized in ("market-snapshot", "snapshot"):
                print(f"🔍 REPORT RUN {run_id}: Using separate Active/Closed/Pending queries")
                
                # Query 1: Active listings (current inventory)
                active_query = build_market_snapshot(_params)
                print(f"🔍 REPORT RUN {run_id}: active_query={active_query}")
                active_raw = fetch_properties(active_query, limit=1000)
                print(f"🔍 REPORT RUN {run_id}: fetched {len(active_raw)} Active properties")
                
                # Query 2: Closed listings (recent sales for metrics)
                closed_query = build_market_snapshot_closed(_params)
                print(f"🔍 REPORT RUN {run_id}: closed_query={closed_query}")
                closed_raw = fetch_properties(closed_query, limit=1000)
                print(f"🔍 REPORT RUN {run_id}: fetched {len(closed_raw)} Closed properties")
                
                # Query 3: Pending listings (contracts pending)
                pending_query = build_market_snapshot_pending(_params)
                print(f"🔍 REPORT RUN {run_id}: pending_query={pending_query}")
                pending_raw = fetch_properties(pending_query, limit=500)
                print(f"🔍 REPORT RUN {run_id}: fetched {len(pending_raw)} Pending properties")
                
                # Combine for extraction (mark each with status for metrics)
                raw = active_raw + closed_raw + pending_raw
                print(f"🔍 REPORT RUN {run_id}: combined {len(raw)} total properties")
            else:
                # Standard single query for other report types
                q = build_params(report_type, _params)
                print(f"🔍 REPORT RUN {run_id}: simplyrets_query={q}")
                raw = fetch_properties(q, limit=800)
                print(f"🔍 REPORT RUN {run_id}: fetched {len(raw)} properties from SimplyRETS")
            
            extracted = PropertyDataExtractor(raw).run()
            clean = filter_valid(extracted)
            print(f"🔍 REPORT RUN {run_id}: cleaned to {len(clean)} valid properties")
            
            # ===== ELASTIC WIDENING (auto-expand filters if too few results) =====
            # This ensures users almost never see empty reports
            widening_note = None
            if filters.get("price_strategy") and market_stats and len(clean) < 6:
                # Determine minimum results based on report type
                min_results = 4 if "featured" in (report_type or "").lower() else 6
                
                if len(clean) < min_results:
                    print(f"⚠️  REPORT RUN {run_id}: Only {len(clean)} results, attempting elastic widening")
                    
                    # Try widening up to 3 times
                    current_filters_intent = filters.copy()
                    for attempt in range(3):
                        widened = elastic_widen_filters(
                            current_filters_intent, 
                            market_stats, 
                            len(clean), 
                            min_results
                        )
                        if not widened:
                            print(f"⚠️  REPORT RUN {run_id}: Cannot widen further after {attempt} attempts")
                            break
                        
                        # Resolve widened filters
                        widened_resolved = resolve_filters(widened, market_stats)
                        widened_params = {**_params, "filters": widened_resolved}
                        
                        # Re-query with widened filters
                        q2 = build_params(report_type, widened_params)
                        print(f"🔍 REPORT RUN {run_id}: widened_query (attempt {attempt+1})={q2}")
                        raw2 = fetch_properties(q2, limit=800)
                        extracted2 = PropertyDataExtractor(raw2).run()
                        clean2 = filter_valid(extracted2)
                        print(f"🔍 REPORT RUN {run_id}: widened results: {len(clean2)} properties")
                        
                        if len(clean2) >= min_results:
                            # Success! Use widened results
                            clean = clean2
                            resolved_filters = widened_resolved
                            filters_label = build_filters_label(widened, widened_resolved, market_stats)
                            widening_note = widened.get("_widened_reason", "Expanded price range to match local market conditions")
                            print(f"✅ REPORT RUN {run_id}: elastic widening successful: {widening_note}")
                            break
                        
                        current_filters_intent = widened
            
            # Build context for report builders (include market-adaptive data)
            context = {
                "city": city,
                "lookback_days": lookback,
                "generated_at": int(time.time()),
                "filters": resolved_filters or filters,  # Pass resolved filters
            }
            
            # Add market-adaptive metadata for PDF/email rendering
            if market_stats:
                context["market_stats"] = market_stats
            if filters_label:
                context["filters_label"] = filters_label
            
            print(f"🔍 REPORT RUN {run_id}: step=build_context")
            # Use report builder dispatcher to create result_json
            result = build_result_json(report_type, clean, context)
            
            # Add widening note if filters were expanded
            if widening_note:
                result["widening_note"] = widening_note
            
            # Add resolved filter info to result for PDF header display
            if filters_label:
                result["filters_label"] = filters_label
            if resolved_filters and resolved_filters.get("_resolved_from"):
                result["price_resolved_from"] = resolved_filters["_resolved_from"]
            
            cache_set("report", cache_payload, result, ttl_s=900)  # 15 minutes
            print(f"✅ REPORT RUN {run_id}: data_fetch complete (from SimplyRETS)")
        else:
            print(f"✅ REPORT RUN {run_id}: data_fetch complete (from cache)")

        # 3) Photo proxy (gallery/featured): rewrite MLS photo URLs to R2 presigned URLs.
        #
        # IMPORTANT:
        # - Do this *after* cache_get/cache_set so we don't cache run-specific signed URLs.
        # - Do this *before* saving result_json so the /print/[runId] page uses proxied photos.
        rt_norm = (report_type or "").lower()
        if rt_norm in ("new_listings_gallery", "featured_listings") and isinstance(result, dict):
            try:
                print(f"🖼️  Photo proxy to R2: report_type={rt_norm}, run_id={run_id}")
                # Mutate in place; safe because we only do this on the per-run `result`
                # and we intentionally avoid caching the mutated/signed URLs.
                proxy_report_photos_inplace(result, account_id=account_id, run_id=run_id)
            except Exception as e:
                # Never fail the report run just because photos couldn't be proxied.
                print(f"⚠️  Photo proxy failed; continuing with original URLs: {type(e).__name__}: {e}")

        # 4) Save result_json
        print(f"🔍 REPORT RUN {run_id}: step=save_result_json")
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("UPDATE report_generations SET result_json=%s WHERE id=%s", (safe_json_dumps(result), run_id))
        print(f"✅ REPORT RUN {run_id}: save_result_json complete")

        # 5) Generate PDF (via configured engine: playwright or pdfshift)
        print(f"🔍 REPORT RUN {run_id}: step=generate_pdf")
        print(f"🔍 REPORT RUN {run_id}: pdf_backend=<checking pdf_engine module>")
        pdf_path, html_url = render_pdf(
            run_id=run_id,
            account_id=account_id,
            html_content=None,  # Will navigate to /print/{run_id}
            print_base=DEV_BASE
        )
        print(f"✅ REPORT RUN {run_id}: generate_pdf complete (path={pdf_path})")
        
        # 6) Upload PDF to Cloudflare R2
        print(f"🔍 REPORT RUN {run_id}: step=upload_pdf")
        # Create descriptive filename: City_ReportType_RunId.pdf
        # Sanitize city name (remove spaces, special chars)
        safe_city = (city or "Market").replace(" ", "_").replace(",", "").replace(".", "")[:30]
        
        # Use preset_display_name if available (e.g., "First-Time Buyer" instead of "NewListingsGallery")
        preset_name = result.get("preset_display_name") if isinstance(result, dict) else None
        if preset_name:
            # Convert "First-Time Buyer" to "FirstTimeBuyer"
            safe_report_type = preset_name.replace("-", "").replace(" ", "").replace("'", "")
        else:
            # Map report_type to title case
            report_type_map = {
                "market_snapshot": "MarketSnapshot",
                "new_listings": "NewListings",
                "closed": "ClosedSales",
                "inventory": "Inventory",
                "price_bands": "PriceBands",
                "open_houses": "OpenHouses",
                "new_listings_gallery": "NewListingsGallery",
                "featured_listings": "FeaturedListings",
            }
            safe_report_type = report_type_map.get(report_type, report_type.replace("_", "").title())
        pdf_filename = f"{safe_city}_{safe_report_type}_{run_id[:8]}.pdf"
        s3_key = f"reports/{account_id}/{pdf_filename}"
        pdf_url = upload_to_r2(pdf_path, s3_key)
        print(f"✅ REPORT RUN {run_id}: upload_pdf complete (url={pdf_url[:100] if pdf_url else None}...)")
        
        # JSON URL (future: could upload result_json to R2 too)
        json_url = f"{DEV_BASE}/api/reports/{run_id}/data"

        print(f"🔍 REPORT RUN {run_id}: step=mark_completed")
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("""
                    UPDATE report_generations
                    SET status='completed', html_url=%s, json_url=%s, pdf_url=%s, processing_time_ms=%s
                    WHERE id = %s
                """, (html_url, json_url, pdf_url, int((time.perf_counter()-started)*1000), run_id))
        print(f"✅ REPORT RUN {run_id}: mark_completed SUCCESS")

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
                                    
                                    if acc_type == 'REGULAR' and sponsor_id:
                                        # Sponsored regular user: use sponsor's branding from affiliate_branding
                                        cur.execute("""
                                            SELECT
                                                brand_display_name,
                                                logo_url,
                                                email_logo_url,
                                                primary_color,
                                                accent_color,
                                                rep_photo_url,
                                                contact_line1,
                                                contact_line2,
                                                website_url
                                            FROM affiliate_branding
                                            WHERE account_id = %s::uuid
                                        """, (sponsor_id,))
                                        brand_row = cur.fetchone()
                                        if brand_row:
                                            brand = {
                                                "display_name": brand_row[0],
                                                "logo_url": brand_row[1],
                                                "email_logo_url": brand_row[2],
                                                "primary_color": brand_row[3],
                                                "accent_color": brand_row[4],
                                                "rep_photo_url": brand_row[5],
                                                "contact_line1": brand_row[6],
                                                "contact_line2": brand_row[7],
                                                "website_url": brand_row[8],
                                            }
                                    elif acc_type == 'INDUSTRY_AFFILIATE':
                                        # Affiliate: use their own branding from affiliate_branding
                                        cur.execute("""
                                            SELECT
                                                brand_display_name,
                                                logo_url,
                                                email_logo_url,
                                                primary_color,
                                                accent_color,
                                                rep_photo_url,
                                                contact_line1,
                                                contact_line2,
                                                website_url
                                            FROM affiliate_branding
                                            WHERE account_id = %s::uuid
                                        """, (account_id,))
                                        brand_row = cur.fetchone()
                                        if brand_row:
                                            brand = {
                                                "display_name": brand_row[0],
                                                "logo_url": brand_row[1],
                                                "email_logo_url": brand_row[2],
                                                "primary_color": brand_row[3],
                                                "accent_color": brand_row[4],
                                                "rep_photo_url": brand_row[5],
                                                "contact_line1": brand_row[6],
                                                "contact_line2": brand_row[7],
                                                "website_url": brand_row[8],
                                            }
                                    else:
                                        # Un-sponsored regular user: use accounts table branding + user avatar
                                        # Get user_id for this schedule to fetch their avatar
                                        cur.execute("""
                                            SELECT u.avatar_url, a.name, a.logo_url, a.primary_color, 
                                                   a.secondary_color, a.contact_line1, a.contact_line2, a.website_url
                                            FROM accounts a
                                            LEFT JOIN users u ON u.active_account_id = a.id
                                            WHERE a.id = %s::uuid
                                            LIMIT 1
                                        """, (account_id,))
                                        acc_brand_row = cur.fetchone()
                                        if acc_brand_row:
                                            brand = {
                                                "display_name": acc_brand_row[1],
                                                "logo_url": acc_brand_row[2],
                                                "primary_color": acc_brand_row[3],
                                                "accent_color": acc_brand_row[4],
                                                "rep_photo_url": acc_brand_row[0],  # user's avatar_url
                                                "contact_line1": acc_brand_row[5],
                                                "contact_line2": acc_brand_row[6],
                                                "website_url": acc_brand_row[7],
                                            }
                            except Exception as e:
                                print(f"⚠️  Error loading brand for email: {e}")
                                # Continue without brand (will use default branding)
                            
                            # Build email payload
                            # Flatten counts into metrics for email template compatibility
                            email_metrics = result.get("metrics", {}).copy()
                            counts = result.get("counts", {})
                            # Map counts to what email template expects
                            email_metrics["total_active"] = counts.get("Active", 0)
                            email_metrics["total_closed"] = counts.get("Closed", 0)
                            email_metrics["total_pending"] = counts.get("Pending", 0)
                            email_metrics["new_listings_7d"] = counts.get("NewListings", email_metrics.get("new_listings_count", 0))
                            # Normalize key names for template compatibility
                            if "close_to_list_ratio" in email_metrics and "sale_to_list_ratio" not in email_metrics:
                                email_metrics["sale_to_list_ratio"] = email_metrics["close_to_list_ratio"]
                            # Inventory report uses median_dom, template expects avg_dom
                            if "median_dom" in email_metrics and "avg_dom" not in email_metrics:
                                email_metrics["avg_dom"] = email_metrics["median_dom"]
                            
                            # Add property type breakdown for Market Snapshot
                            by_property_type = result.get("by_property_type", {})
                            if by_property_type:
                                email_metrics["sfr_count"] = by_property_type.get("SingleFamilyResidence", {}).get("count", 0) or by_property_type.get("Single Family Residence", {}).get("count", 0)
                                email_metrics["condo_count"] = by_property_type.get("Condominium", {}).get("count", 0) or by_property_type.get("Condo", {}).get("count", 0)
                                email_metrics["townhome_count"] = by_property_type.get("Townhouse", {}).get("count", 0) or by_property_type.get("Townhome", {}).get("count", 0)
                            
                            # Add price tier breakdown for Market Snapshot
                            price_tiers = result.get("price_tiers", {})
                            if price_tiers:
                                entry_tier = price_tiers.get("Entry", {})
                                moveup_tier = price_tiers.get("Move-Up", {})
                                luxury_tier = price_tiers.get("Luxury", {})
                                email_metrics["entry_tier_count"] = entry_tier.get("count", 0) + entry_tier.get("active_count", 0)
                                email_metrics["moveup_tier_count"] = moveup_tier.get("count", 0) + moveup_tier.get("active_count", 0)
                                email_metrics["luxury_tier_count"] = luxury_tier.get("count", 0) + luxury_tier.get("active_count", 0)
                            
                            # For gallery reports, ensure total_listings is set from result
                            # (metrics dict includes this, but also set it explicitly for backwards compat)
                            if report_type in ("new_listings_gallery", "featured_listings"):
                                email_metrics["total_listings"] = result.get("total_listings", len(result.get("listings", [])))
                            
                            email_payload = {
                                "report_type": report_type,
                                "city": city,
                                "zip_codes": zip_codes,
                                "lookback_days": lookback,
                                "metrics": email_metrics,
                                "pdf_url": pdf_url,
                                # Pass preset_display_name for email headers (e.g., "First-Time Buyer" instead of "New Listings Gallery")
                                "preset_display_name": result.get("preset_display_name") if isinstance(result, dict) else None,
                                # V11: Pass filter_description for email blurb (e.g., "2+ beds, Condos, under $1.2M")
                                "filter_description": result.get("filters_label") if isinstance(result, dict) else None,
                            }
                            
                            # For gallery reports, include listings with photos
                            if report_type in ("new_listings_gallery", "featured_listings"):
                                email_payload["listings"] = result.get("listings", [])
                            
                            # For inventory reports, include listings table data
                            if report_type == "inventory":
                                # Get top 10 listings for email table (sorted by DOM desc)
                                listings_sample = result.get("listings_sample", [])[:10]
                                email_payload["listings"] = [
                                    {
                                        "street_address": l.get("street_address"),
                                        "city": l.get("city"),
                                        "bedrooms": l.get("bedrooms"),
                                        "bathrooms": l.get("bathrooms"),
                                        "list_price": l.get("list_price"),
                                    }
                                    for l in listings_sample
                                ]
                            
                            # For closed reports, include listings table data (recently sold)
                            if report_type == "closed":
                                # Get top 10 closed listings for email table (sorted by close_date desc)
                                listings_sample = result.get("listings_sample", [])[:10]
                                email_payload["listings"] = [
                                    {
                                        "street_address": l.get("street_address"),
                                        "city": l.get("city"),
                                        "bedrooms": l.get("bedrooms"),
                                        "bathrooms": l.get("bathrooms"),
                                        "list_price": l.get("close_price"),  # Use close_price for sold properties
                                    }
                                    for l in listings_sample
                                ]
                            
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

        # 7) PASS S3: Reset consecutive failures on success
        if schedule_id:
            try:
                with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                        cur.execute("""
                            UPDATE schedules
                            SET consecutive_failures = 0,
                                last_error = NULL,
                                last_error_at = NULL
                            WHERE id = %s::uuid
                        """, (schedule_id,))
                        print(f"✅ Reset failure count for schedule {schedule_id}")
            except Exception as reset_error:
                print(f"⚠️  Failed to reset failure count (non-critical): {reset_error}")
        
        # 8) Webhook
        payload = {"report_id": run_id, "status": "completed", "html_url": html_url, "pdf_url": pdf_url, "json_url": json_url}
        _deliver_webhooks(account_id, "report.completed", payload)
        return {"ok": True, "run_id": run_id}

    except Exception as e:
        # PASS S3: Track failures and auto-pause after threshold
        error_msg = str(e)[:2000]  # Truncate to 2KB
        
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                
                # Update report_generations
                cur.execute("UPDATE report_generations SET status='failed', error=%s WHERE id=%s", (error_msg, run_id))
                
                # Update schedule_runs if this was a scheduled report
                if schedule_id:
                    try:
                        cur.execute("""
                            UPDATE schedule_runs
                            SET status = 'failed',
                                error = %s,
                                finished_at = NOW()
                            WHERE report_run_id = %s::uuid
                        """, (error_msg, run_id))
                    except Exception:
                        pass  # Non-critical
                
                # PASS S3: Increment consecutive failures and check threshold
                if schedule_id:
                    cur.execute("""
                        UPDATE schedules
                        SET consecutive_failures = consecutive_failures + 1,
                            last_error = %s,
                            last_error_at = NOW()
                        WHERE id = %s::uuid
                        RETURNING consecutive_failures
                    """, (error_msg, schedule_id))
                    
                    result = cur.fetchone()
                    if result:
                        consecutive_failures = result[0]
                        print(f"⚠️  Schedule {schedule_id} failure count: {consecutive_failures}")
                        
                        # Auto-pause after 3 consecutive failures
                        if consecutive_failures >= 3:
                            cur.execute("""
                                UPDATE schedules
                                SET active = false
                                WHERE id = %s::uuid
                            """, (schedule_id,))
                            print(f"🛑 Auto-paused schedule {schedule_id} after {consecutive_failures} consecutive failures")
        
        return {"ok": False, "error": error_msg}


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

