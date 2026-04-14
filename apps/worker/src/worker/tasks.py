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
from .sms import send_report_sms, send_agent_notification_sms
import boto3
from botocore.client import Config
from typing import Optional

# =============================================================================
# PROPERTY TYPE MAPPING — copied from property.py (API endpoint)
# Maps SiteX UseCode → SimplyRETS (type, subtype) for comp filtering
# =============================================================================

_PROPERTY_TYPE_MAP = {
    "sfr": ("residential", "SingleFamilyResidence"),
    "rsfr": ("residential", "SingleFamilyResidence"),
    "single family": ("residential", "SingleFamilyResidence"),
    "singlefamily": ("residential", "SingleFamilyResidence"),
    "single family residential": ("residential", "SingleFamilyResidence"),
    "residential": ("residential", "SingleFamilyResidence"),
    "pud": ("residential", "SingleFamilyResidence"),
    "condo": ("residential", "Condominium"),
    "condominium": ("residential", "Condominium"),
    "townhouse": ("residential", "Townhouse"),
    "th": ("residential", "Townhouse"),
    "townhome": ("residential", "Townhouse"),
    "duplex": ("multifamily", "Duplex"),
    "triplex": ("multifamily", "Triplex"),
    "quadplex": ("multifamily", "Quadruplex"),
    "quadruplex": ("multifamily", "Quadruplex"),
    "multi-family": ("multifamily", None),
    "multifamily": ("multifamily", None),
    "mobile": ("residential", "ManufacturedHome"),
    "mobilehome": ("residential", "ManufacturedHome"),
    "manufactured": ("residential", "ManufacturedHome"),
    "land": ("land", None),
    "vacant land": ("land", None),
    "commercial": ("commercial", None),
}

_POST_FILTER_ALLOWED_SUBTYPES = {
    "singlefamilyresidence": {"SingleFamilyResidence", "Detached"},
    "condominium": {"Condominium", "StockCooperative", "Attached"},
    "townhouse": {"Townhouse", "Attached"},
    "duplex": {"Duplex"},
    "triplex": {"Triplex"},
    "quadruplex": {"Quadruplex"},
    "manufacturedhome": {"ManufacturedHome", "ManufacturedOnLand", "MobileHome"},
}


def _resolve_simplyrets_type(sitex_use_code: Optional[str]) -> tuple:
    """Resolve SiteX UseCode → SimplyRETS (type, subtype). Defaults to SFR."""
    if not sitex_use_code:
        return ("residential", "SingleFamilyResidence")
    key = sitex_use_code.strip().lower()
    if key in _PROPERTY_TYPE_MAP:
        return _PROPERTY_TYPE_MAP[key]
    for pattern, mapping in _PROPERTY_TYPE_MAP.items():
        if pattern in key or key in pattern:
            return mapping
    logger.warning("Unknown SiteX UseCode '%s', defaulting to SFR", sitex_use_code)
    return ("residential", "SingleFamilyResidence")


def _post_filter_by_property_type(listings: list, simplyrets_subtype: Optional[str]) -> list:
    """Post-filter SimplyRETS listings to match subject property type."""
    if not simplyrets_subtype:
        return listings
    allowed = _POST_FILTER_ALLOWED_SUBTYPES.get(simplyrets_subtype.lower())
    if not allowed:
        return listings
    filtered = []
    removed = 0
    for listing in listings:
        prop = listing.get("property", {})
        listing_subtype = prop.get("subType") or prop.get("subTypeText") or ""
        if not listing_subtype or listing_subtype in allowed:
            filtered.append(listing)
        else:
            removed += 1
    if removed > 0:
        logger.warning("Post-filter removed %d listings (wanted subtype: %s)", removed, simplyrets_subtype)
    return filtered


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


@celery.task(name="keep_alive_ping")
def keep_alive_ping():
    """
    Ping the API health endpoint to prevent Render cold starts.
    Runs every 5 minutes via Celery Beat.
    """
    import httpx
    
    # Use PRINT_BASE (which points to the frontend) or fall back to API_BASE
    # The frontend /api/health route is simpler than hitting the backend directly
    api_base = os.getenv("API_BASE_URL") or os.getenv("NEXT_PUBLIC_API_BASE") or "https://reportscompany.onrender.com"
    
    try:
        response = httpx.get(f"{api_base}/health", timeout=10.0)
        logger.info(f"Keep-alive ping: {response.status_code}")
        return {"ok": True, "status": response.status_code}
    except httpx.TimeoutException:
        logger.warning("Keep-alive ping timed out")
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        logger.warning(f"Keep-alive ping failed: {e}")
        return {"ok": False, "error": str(e)}

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

def _resolve_email_brand(cur, account_id: str):
    """Resolve white-label brand and account_type for email sending."""
    brand = None
    acc_type = "REGULAR"
    try:
        cur.execute("""
            SELECT account_type, sponsor_account_id::text
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        acc_row = cur.fetchone()

        if acc_row:
            acc_type, sponsor_id = acc_row

            if acc_type == 'REGULAR' and sponsor_id:
                cur.execute("""
                    SELECT
                        brand_display_name, logo_url, email_logo_url,
                        primary_color, accent_color, rep_photo_url,
                        contact_line1, contact_line2, website_url,
                        footer_logo_url, email_footer_logo_url
                    FROM affiliate_branding
                    WHERE account_id = %s::uuid
                """, (sponsor_id,))
                brand_row = cur.fetchone()
                if brand_row:
                    brand = {
                        "display_name": brand_row[0], "logo_url": brand_row[1],
                        "email_logo_url": brand_row[2], "primary_color": brand_row[3],
                        "accent_color": brand_row[4], "rep_photo_url": brand_row[5],
                        "contact_line1": brand_row[6], "contact_line2": brand_row[7],
                        "website_url": brand_row[8],
                        "footer_logo_url": brand_row[9],
                        "email_footer_logo_url": brand_row[10],
                    }
            elif acc_type == 'INDUSTRY_AFFILIATE':
                cur.execute("""
                    SELECT
                        brand_display_name, logo_url, email_logo_url,
                        primary_color, accent_color, rep_photo_url,
                        contact_line1, contact_line2, website_url,
                        footer_logo_url, email_footer_logo_url
                    FROM affiliate_branding
                    WHERE account_id = %s::uuid
                """, (account_id,))
                brand_row = cur.fetchone()
                if brand_row:
                    brand = {
                        "display_name": brand_row[0], "logo_url": brand_row[1],
                        "email_logo_url": brand_row[2], "primary_color": brand_row[3],
                        "accent_color": brand_row[4], "rep_photo_url": brand_row[5],
                        "contact_line1": brand_row[6], "contact_line2": brand_row[7],
                        "website_url": brand_row[8],
                        "footer_logo_url": brand_row[9],
                        "email_footer_logo_url": brand_row[10],
                    }
            else:
                cur.execute("""
                    SELECT
                        COALESCE(u.photo_url, u.avatar_url),
                        u.first_name, u.last_name,
                        u.job_title, u.phone, u.email, u.website,
                        a.name, a.logo_url, a.email_logo_url,
                        a.primary_color, a.secondary_color,
                        a.footer_logo_url, a.email_footer_logo_url
                    FROM accounts a
                    LEFT JOIN users u ON u.account_id = a.id
                    WHERE a.id = %s::uuid
                    LIMIT 1
                """, (account_id,))
                acc_brand_row = cur.fetchone()
                if acc_brand_row:
                    first_name = acc_brand_row[1] or ""
                    last_name = acc_brand_row[2] or ""
                    job_title = acc_brand_row[3] or ""
                    phone = acc_brand_row[4] or ""
                    email = acc_brand_row[5] or ""
                    website = acc_brand_row[6] or ""

                    name = f"{first_name} {last_name}".strip()
                    if name and job_title:
                        contact_line1 = f"{name} • {job_title}"
                    else:
                        contact_line1 = name or job_title or ""

                    phone_fmt = phone
                    if phone_fmt and len(phone_fmt) == 10:
                        phone_fmt = f"({phone_fmt[:3]}) {phone_fmt[3:6]}-{phone_fmt[6:]}"
                    if phone_fmt and email:
                        contact_line2 = f"{phone_fmt} • {email}"
                    else:
                        contact_line2 = phone_fmt or email or ""

                    brand = {
                        "display_name": acc_brand_row[7], "logo_url": acc_brand_row[8],
                        "email_logo_url": acc_brand_row[9], "primary_color": acc_brand_row[10],
                        "accent_color": acc_brand_row[11], "rep_photo_url": acc_brand_row[0],
                        "contact_line1": contact_line1, "contact_line2": contact_line2,
                        "website_url": website,
                        "footer_logo_url": acc_brand_row[12],
                        "email_footer_logo_url": acc_brand_row[13],
                    }
    except Exception as e:
        print(f"⚠️  Error loading brand for email: {e}")
    return brand, acc_type


def _build_email_payload(report_type, city, zips, lookback, result, pdf_url):
    """Build the email payload dict from report result data."""
    email_metrics = result.get("metrics", {}).copy()
    counts = result.get("counts", {})
    email_metrics["total_active"] = counts.get("Active", 0)
    email_metrics["total_closed"] = counts.get("Closed", 0)
    email_metrics["total_pending"] = counts.get("Pending", 0)
    email_metrics["new_listings_7d"] = counts.get("NewListings", email_metrics.get("new_listings_count", 0))
    if "close_to_list_ratio" in email_metrics and "sale_to_list_ratio" not in email_metrics:
        email_metrics["sale_to_list_ratio"] = email_metrics["close_to_list_ratio"]
    if "median_dom" in email_metrics and "avg_dom" not in email_metrics:
        email_metrics["avg_dom"] = email_metrics["median_dom"]

    by_property_type = result.get("by_property_type", {})
    if by_property_type:
        email_metrics["sfr_count"] = by_property_type.get("SingleFamilyResidence", {}).get("count", 0) or by_property_type.get("Single Family Residence", {}).get("count", 0)
        email_metrics["condo_count"] = by_property_type.get("Condominium", {}).get("count", 0) or by_property_type.get("Condo", {}).get("count", 0)
        email_metrics["townhome_count"] = by_property_type.get("Townhouse", {}).get("count", 0) or by_property_type.get("Townhome", {}).get("count", 0)

    price_tiers = result.get("price_tiers", {})
    if price_tiers:
        entry_tier = price_tiers.get("Entry", {})
        moveup_tier = price_tiers.get("Move-Up", {})
        luxury_tier = price_tiers.get("Luxury", {})
        email_metrics["entry_tier_count"] = entry_tier.get("count", 0) + entry_tier.get("active_count", 0)
        email_metrics["moveup_tier_count"] = moveup_tier.get("count", 0) + moveup_tier.get("active_count", 0)
        email_metrics["luxury_tier_count"] = luxury_tier.get("count", 0) + luxury_tier.get("active_count", 0)

    if report_type in ("new_listings_gallery", "featured_listings"):
        email_metrics["total_listings"] = result.get("total_listings", len(result.get("listings", [])))

    payload = {
        "report_type": report_type,
        "city": city,
        "zip_codes": zips,
        "lookback_days": lookback,
        "metrics": email_metrics,
        "pdf_url": pdf_url,
        "preset_display_name": result.get("preset_display_name") if isinstance(result, dict) else None,
        "filter_description": result.get("filters_label") if isinstance(result, dict) else None,
        "total_listings": result.get("total_listings", 0) if isinstance(result, dict) else 0,
        "total_shown": result.get("total_shown", 0) if isinstance(result, dict) else 0,
        "audience_key": result.get("audience_key", "all") if isinstance(result, dict) else "all",
    }

    if report_type in ("new_listings_gallery", "featured_listings"):
        payload["listings"] = result.get("listings", [])

    if report_type == "inventory":
        listings_sample = result.get("listings_sample", [])[:10]
        payload["listings"] = [
            {"street_address": l.get("street_address"), "city": l.get("city"),
             "bedrooms": l.get("bedrooms"), "bathrooms": l.get("bathrooms"),
             "list_price": l.get("list_price")}
            for l in listings_sample
        ]

    if report_type == "closed":
        listings_sample = result.get("listings_sample", [])[:10]
        payload["listings"] = [
            {"street_address": l.get("street_address"), "city": l.get("city"),
             "bedrooms": l.get("bedrooms"), "bathrooms": l.get("bathrooms"),
             "list_price": l.get("close_price")}
            for l in listings_sample
        ]

    return payload


def _send_and_log_report_email(
    conn, cur, account_id, run_id, recipients,
    report_type, city, zips, lookback, result, pdf_url,
    schedule_id=None,
):
    """
    Shared email delivery: resolve brand, build payload, send, and log.
    Used by both the scheduled and ad-hoc email paths.
    Returns (status_code, response_text).
    """
    cur.execute("SELECT name FROM accounts WHERE id = %s", (account_id,))
    account_row = cur.fetchone()
    account_name = account_row[0] if account_row else None

    brand, acc_type = _resolve_email_brand(cur, account_id)
    email_payload = _build_email_payload(report_type, city, zips, lookback, result, pdf_url)

    status_code, response_text = send_schedule_email(
        account_id=account_id,
        recipients=recipients,
        payload=email_payload,
        account_name=account_name,
        db_conn=conn,
        brand=brand,
        account_type=acc_type,
    )

    try:
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
            account_id, schedule_id, run_id, 'sendgrid',
            recipients, subject, status_code, email_status,
            None if status_code in (200, 202) else response_text,
        ))
    except Exception as log_error:
        logger.warning(f"Failed to log email send (non-critical): {log_error}")

    print(f"✅ Email sent to {len(recipients)} recipient(s), status: {status_code}")
    return status_code, response_text


# ==================== Failure Notification ====================

def _send_failure_notification(
    account_id: str,
    schedule_id: str | None,
    report_type: str,
    city: str | None,
    error_msg: str,
):
    """
    Send a branded email to the account owner when a scheduled report fails.
    Deduplicates: skips if the same schedule already got a notification in the last 24h.
    """
    if not schedule_id:
        return

    resend_key = os.environ.get("RESEND_API_KEY", "")
    if not resend_key:
        logger.warning("RESEND_API_KEY not set — skipping failure notification")
        return

    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                # 24-hour dedup: check if we already notified for this schedule recently
                cur.execute("""
                    SELECT 1 FROM email_log
                    WHERE schedule_id = %s::uuid
                      AND subject LIKE '%%report failed%%'
                      AND created_at >= NOW() - INTERVAL '24 hours'
                    LIMIT 1
                """, (schedule_id,))
                if cur.fetchone():
                    logger.info(f"Skipping failure notification for schedule {schedule_id} — already sent within 24h")
                    return

                # Look up account owner email + name
                cur.execute("""
                    SELECT u.email, u.first_name
                    FROM users u
                    JOIN account_users au ON au.user_id = u.id
                    WHERE au.account_id = %s::uuid AND au.role = 'OWNER'
                    LIMIT 1
                """, (account_id,))
                owner = cur.fetchone()
                if not owner or not owner[0]:
                    logger.warning(f"No owner email found for account {account_id}")
                    return

                owner_email = owner[0]
                first_name = owner[1] or "there"

                # Get schedule name
                cur.execute("""
                    SELECT name FROM schedules WHERE id = %s::uuid
                """, (schedule_id,))
                sched_row = cur.fetchone()
                schedule_name = sched_row[0] if sched_row else report_type.replace("_", " ").title()

                area = city or "your area"
                brief_error = (error_msg or "Unknown error")[:200]
                app_base = os.environ.get("APP_BASE", "https://reportscompany-web.vercel.app")
                schedule_url = f"{app_base}/app/schedules"

                subject = f"\u26a0\ufe0f Your scheduled report failed \u2014 {schedule_name}"

                cta_html = f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin: 28px 0;">
                  <tr><td align="center">
                    <a href="{schedule_url}" target="_blank" style="display: inline-block; background-color: #4F46E5; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 16px; font-weight: bold; text-decoration: none; padding: 14px 32px; border-radius: 8px;">
                      View Schedules
                    </a>
                  </td></tr>
                </table>'''

                content_html = f'''<p style="margin: 0 0 20px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; color: #111827;">
                    Hi {first_name},
                  </p>
                  <p style="margin: 0 0 8px; font-size: 15px; line-height: 1.7; color: #374151;">
                    Your scheduled report &ldquo;{schedule_name}&rdquo; for {area} failed to generate.
                    We&rsquo;ll automatically retry on the next scheduled run.
                  </p>
                  <p style="margin: 0 0 20px; font-size: 15px; line-height: 1.7; color: #374151;">
                    If this continues, please contact support.
                  </p>
                  <div style="background-color: #FEF2F2; border-left: 3px solid #EF4444; padding: 12px 16px; border-radius: 0 6px 6px 0; margin-bottom: 24px;">
                    <p style="margin: 0 0 4px; font-size: 11px; font-weight: 600; color: #991B1B; text-transform: uppercase; letter-spacing: 0.5px;">Error details</p>
                    <p style="margin: 0; font-size: 13px; color: #7F1D1D; font-family: monospace; word-break: break-all;">{brief_error}</p>
                  </div>
                  {cta_html}
                  <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #6b7280;">
                    This is an automated notification from TrendyReports.
                  </p>'''

                # Build full email using the branded shell (inlined to avoid cross-app imports)
                html_body = f'''<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light only">
  <title>TrendyReports</title>
  <style>
    body, table, td, p, a {{ -webkit-text-size-adjust: 100%; }}
    body {{ margin: 0 !important; padding: 0 !important; }}
    @media (prefers-color-scheme: dark) {{ .email-outer {{ background-color: #232323 !important; }} }}
    @media screen and (max-width: 600px) {{ .email-wrapper {{ width: 100% !important; }} .content-pad {{ padding: 24px 20px !important; }} }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F8FAFC;" class="email-outer"><tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" class="email-wrapper" style="max-width:600px;width:100%;">
        <tr><td align="center" style="background:linear-gradient(135deg,#4F46E5 0%,#6366F1 50%,#818CF8 100%);background-color:#4F46E5;padding:28px 24px 20px;border-radius:12px 12px 0 0;">
          <img src="https://www.trendyreports.io/white.png" width="160" alt="TrendyReports" style="display:block;max-height:40px;width:auto;height:auto;">
        </td></tr>
        <tr><td style="background-color:#ffffff;padding:32px;" class="content-pad">
          {content_html}
        </td></tr>
        <tr><td style="background-color:#ffffff;border-top:1px solid #EEF2FF;padding:20px 32px;border-radius:0 0 12px 12px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
            <p style="margin:0 0 4px;font-size:13px;font-weight:600;color:#6366F1;">TrendyReports</p>
            <p style="margin:0 0 12px;font-size:12px;color:#9ca3af;">Branded Real Estate Reports</p>
            <p style="margin:0;font-size:11px;color:#9ca3af;">
              <a href="mailto:support@trendyreports.io" style="color:#6b7280;text-decoration:underline;">Contact Support</a>
              &nbsp;&bull;&nbsp; &copy; 2026 TrendyReports
            </p>
          </td></tr></table>
        </td></tr>
      </table>
    </td>
  </tr></table>
</body></html>'''

                # Send via Resend
                resp = httpx.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": os.environ.get("EMAIL_FROM_ADDRESS", "TrendyReports <noreply@trendyreports.io>"),
                        "to": [owner_email],
                        "subject": subject,
                        "html": html_body,
                    },
                    timeout=15.0,
                )

                # Log the notification
                cur.execute("""
                    INSERT INTO email_log (account_id, schedule_id, provider, to_emails, subject, response_code, status)
                    VALUES (%s::uuid, %s::uuid, 'resend', %s, %s, %s, %s)
                """, (account_id, schedule_id, [owner_email], subject, resp.status_code,
                      'sent' if resp.status_code in (200, 201) else 'failed'))

                if resp.status_code in (200, 201):
                    logger.info(f"Failure notification sent to {owner_email} for schedule {schedule_id}")
                else:
                    logger.warning(f"Failure notification send returned {resp.status_code}: {resp.text[:200]}")

    except Exception as notify_err:
        logger.warning(f"Failed to send failure notification (non-critical): {notify_err}")


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
        PHOTO_PROXY_REPORT_TYPES = {
            "new_listings_gallery", "featured_listings", "open_houses",
            "market_snapshot", "closed", "inventory", "price_bands", "new_listings",
        }
        if rt_norm in PHOTO_PROXY_REPORT_TYPES and isinstance(result, dict):
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

        # 5) Generate PDF — server-side (themed) or legacy (frontend navigation)
        #
        # Strategy B: If theme_id is set on the report_generations row, render
        # server-side via MarketReportBuilder and pass HTML directly to PDFShift.
        # Otherwise, fall back to the legacy frontend /print/{runId} path.
        # (Same html_content pattern used by process_consumer_report.)
        theme_id = None
        theme_accent = None
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute(
                    "SELECT theme_id, accent_color FROM report_generations WHERE id=%s",
                    (run_id,),
                )
                theme_row = cur.fetchone()
                if theme_row:
                    theme_id, theme_accent = theme_row
            conn.commit()

        if theme_id:
            print(f"🔍 REPORT RUN {run_id}: step=generate_pdf (server-side, theme={theme_id})")
            from .market_builder import MarketReportBuilder

            # Load branding for the account (agent info, logo, colors)
            branding_ctx = {}
            with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                    cur.execute("""
                        SELECT
                            u.first_name, u.last_name, u.job_title, u.phone,
                            u.email, COALESCE(u.photo_url, u.avatar_url),
                            u.company_name, a.logo_url, a.name,
                            a.primary_color, a.secondary_color
                        FROM accounts a
                        LEFT JOIN users u ON u.account_id = a.id
                        WHERE a.id = %s::uuid
                        LIMIT 1
                    """, (account_id,))
                    brow = cur.fetchone()
                    if brow:
                        agent_name = f"{brow[0] or ''} {brow[1] or ''}".strip()
                        branding_ctx = {
                            "agent_name": agent_name,
                            "agent_title": brow[2] or "",
                            "agent_phone": brow[3] or "",
                            "agent_email": brow[4] or "",
                            "agent_photo_url": brow[5],
                            "company_name": brow[6] or brow[8] or "",
                            "logo_url": brow[7],
                            "primary_color": brow[9],
                            "accent_color": brow[10],
                        }
                conn.commit()

            # Merge result_json + branding + theme for the builder
            builder_data = {}
            if isinstance(result, dict):
                builder_data.update(result)
            builder_data["report_type"] = report_type
            builder_data["theme_id"] = theme_id
            builder_data["accent_color"] = theme_accent or branding_ctx.get("accent_color")
            builder_data["branding"] = branding_ctx

            # Generate AI narrative (non-fatal — report renders without it)
            if not builder_data.get("ai_insights"):
                try:
                    from .ai_market_narrative import generate_market_pdf_narrative
                    narrative = generate_market_pdf_narrative(
                        report_type,
                        builder_data.get("city", ""),
                        builder_data,
                    )
                    if narrative:
                        builder_data["ai_insights"] = narrative
                        print(f"✅ REPORT RUN {run_id}: AI narrative generated ({len(narrative)} chars)")
                except Exception as ai_err:
                    print(f"⚠️  REPORT RUN {run_id}: AI narrative failed (non-fatal): {ai_err}")

            builder = MarketReportBuilder(builder_data)
            html_content = builder.render_html()
            print(f"🔍 REPORT RUN {run_id}: server-side HTML rendered ({len(html_content)} chars)")

            pdf_path, html_url = render_pdf(
                run_id=run_id,
                account_id=account_id,
                html_content=html_content,
                print_base=DEV_BASE,
            )
        else:
            print(f"🔍 REPORT RUN {run_id}: step=generate_pdf (legacy frontend)")
            pdf_path, html_url = render_pdf(
                run_id=run_id,
                account_id=account_id,
                html_content=None,
                print_base=DEV_BASE,
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

                with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")

                        cur.execute("""
                            SELECT recipients, city, zip_codes
                            FROM schedules
                            WHERE id = %s
                        """, (schedule_id,))
                        schedule_row = cur.fetchone()

                        if not schedule_row:
                            print(f"⚠️  Schedule {schedule_id} not found, skipping email")
                        else:
                            recipients_raw, sched_city, sched_zips = schedule_row
                            recipients = resolve_recipients_to_emails(cur, account_id, recipients_raw)

                            status_code, _ = _send_and_log_report_email(
                                conn, cur, account_id, run_id, recipients,
                                report_type, sched_city, sched_zips, lookback,
                                result, pdf_url, schedule_id=schedule_id,
                            )

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

            except Exception as email_error:
                print(f"⚠️  Email send failed: {email_error}")
                with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO email_log (account_id, schedule_id, report_id, provider, to_emails, subject, response_code, error)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            account_id, schedule_id, run_id, 'sendgrid',
                            [], 'Failed to send', 500, str(email_error),
                        ))

        # 6b) Ad-hoc email delivery (wizard "Generate & Send")
        if not schedule_id and (params or {}).get("send_email") and (params or {}).get("recipients") and pdf_url:
            try:
                print(f"📧 REPORT RUN {run_id}: ad-hoc email delivery")

                with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")

                        # Normalize recipients: dicts become JSON strings for resolve_recipients_to_emails
                        raw = params["recipients"]
                        normalized = [json.dumps(r) if isinstance(r, dict) else str(r) for r in raw]
                        recipients = resolve_recipients_to_emails(cur, account_id, normalized)

                        # Always CC the agent (account owner)
                        cur.execute("""
                            SELECT u.email FROM users u
                            WHERE u.account_id = %s::uuid
                            ORDER BY u.created_at LIMIT 1
                        """, (account_id,))
                        agent_row = cur.fetchone()
                        if agent_row and agent_row[0] and agent_row[0] not in recipients:
                            recipients.append(agent_row[0])

                        if not recipients:
                            print(f"⚠️  REPORT RUN {run_id}: no valid recipients, skipping ad-hoc email")
                        else:
                            _send_and_log_report_email(
                                conn, cur, account_id, run_id, recipients,
                                report_type, city, zips, lookback,
                                result, pdf_url,
                            )
                            conn.commit()

            except Exception as email_error:
                print(f"⚠️  Ad-hoc email send failed (non-fatal): {email_error}")
                logger.warning(f"Ad-hoc email failed for run {run_id}: {email_error}")

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

        # Send failure notification email to account owner (24h dedup built in)
        _send_failure_notification(
            account_id=account_id,
            schedule_id=schedule_id,
            report_type=report_type,
            city=(params or {}).get("city"),
            error_msg=error_msg,
        )

        return {"ok": False, "error": error_msg}


@celery.task(name="process_consumer_report", bind=True, max_retries=3)
def process_consumer_report(self, report_id: str):
    """
    Process a consumer report request from the lead pages feature.
    
    This task:
    1. Looks up the consumer_report record (with existing property_data)
    2. Fetches comparable sales from SimplyRETS
    3. Calculates value estimate based on comparables
    4. Calculates market statistics
    5. Sends SMS to the consumer with report link
    6. Optionally notifies the agent
    7. Updates the record with all data
    """
    from .vendors.simplyrets import fetch_properties
    from datetime import datetime, timedelta
    
    logger.info(f"Processing consumer report: {report_id}")
    
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Get report details INCLUDING property_data JSON
                cur.execute("""
                    SELECT 
                        cr.id, cr.agent_id, cr.consumer_phone, 
                        cr.property_address, cr.property_city, cr.property_state, cr.property_zip,
                        cr.property_data,
                        u.first_name, u.last_name, u.phone as agent_phone,
                        a.id as account_id,
                        cr.consumer_email,
                        COALESCE(cr.delivery_method, 'sms') as delivery_method
                    FROM consumer_reports cr
                    JOIN users u ON u.id = cr.agent_id
                    JOIN accounts a ON a.id = u.account_id
                    WHERE cr.id = %s::uuid
                """, (report_id,))
                
                row = cur.fetchone()
                if not row:
                    logger.error(f"Consumer report not found: {report_id}")
                    return {"ok": False, "error": "Report not found"}
                
                (
                    report_id, agent_id, consumer_phone,
                    prop_address, prop_city, prop_state, prop_zip,
                    existing_property_data,
                    agent_first, agent_last, agent_phone,
                    account_id,
                    consumer_email, delivery_method,
                ) = row
                
                agent_name = f"{agent_first} {agent_last}".strip()
                full_address = f"{prop_address}, {prop_city}, {prop_state} {prop_zip}"
                
                # Build report URL
                base_url = os.environ.get("FRONTEND_URL", "https://www.trendyreports.io")
                report_url = f"{base_url}/r/{report_id}"
                
                # Update status to processing
                cur.execute("""
                    UPDATE consumer_reports SET status = 'processing' WHERE id = %s::uuid
                """, (report_id,))
                
                # Use existing property_data or build basic one
                if existing_property_data and isinstance(existing_property_data, dict):
                    property_data = existing_property_data
                else:
                    property_data = {
                        "address": prop_address,
                        "city": prop_city,
                        "state": prop_state,
                        "zip": prop_zip,
                    }
                
                # Ensure basic fields are set
                property_data.setdefault("address", prop_address)
                property_data.setdefault("city", prop_city)
                property_data.setdefault("state", prop_state)
                property_data.setdefault("zip", prop_zip)
                
                # =============================================
                # FETCH COMPARABLES FROM SIMPLYRETS
                # Uses the SAME approach as the working
                # POST /v1/property/comparables endpoint
                # =============================================
                comparables = []
                market_stats = {}

                try:
                    from math import radians, cos, sin, asin, sqrt as math_sqrt

                    subject_beds = property_data.get("bedrooms")
                    subject_sqft = property_data.get("sqft")
                    subject_lat = property_data.get("latitude")
                    subject_lng = property_data.get("longitude")
                    subject_prop_type = property_data.get("property_type")

                    sr_type, sr_subtype = _resolve_simplyrets_type(subject_prop_type)

                    logger.warning(
                        "[CMA] Subject: city=%s zip=%s type=%s→sr(%s,%s) lat=%s lng=%s beds=%s sqft=%s",
                        prop_city, prop_zip, subject_prop_type,
                        sr_type, sr_subtype,
                        subject_lat, subject_lng, subject_beds, subject_sqft,
                    )

                    def _cma_params(include_beds=True, include_sqft=True, include_subtype=True):
                        """Mirror the API endpoint's _build_params exactly."""
                        p = {
                            "type": sr_type,
                            "status": "Closed",
                            "limit": 50,
                        }
                        if prop_zip:
                            p["postalCodes"] = prop_zip
                        if prop_city:
                            p["cities"] = prop_city
                        if include_subtype and sr_subtype:
                            p["subtype"] = sr_subtype
                        if include_beds and subject_beds:
                            p["minbeds"] = max(1, subject_beds - 1)
                            p["maxbeds"] = subject_beds + 1
                        if include_sqft and subject_sqft:
                            p["minarea"] = int(subject_sqft * 0.75)
                            p["maxarea"] = int(subject_sqft * 1.25)
                        return p

                    def _haversine(lat1, lon1, lat2, lon2):
                        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                        dlat, dlon = lat2 - lat1, lon2 - lon1
                        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                        return round(3956 * 2 * asin(math_sqrt(a)), 2)

                    # Fallback ladder (same concept as property wizard)
                    # L0: strict (type + subtype + beds + sqft)
                    # L1: drop subtype (type + beds + sqft)
                    # L2: drop sqft (type + beds only)
                    # L3: drop all filters (type only)
                    ladder = [
                        ("L0:strict",     _cma_params(True, True, True)),
                        ("L1:no-subtype", _cma_params(True, True, False)),
                        ("L2:no-sqft",    _cma_params(True, False, False)),
                        ("L3:no-filters", _cma_params(False, False, False)),
                    ]

                    raw_comps = []
                    for label, sr_params in ladder:
                        logger.warning("[CMA] %s: params=%s", label, sr_params)
                        raw_comps = fetch_properties(sr_params, limit=25)
                        raw_comps = _post_filter_by_property_type(raw_comps, sr_subtype)
                        logger.warning("[CMA] %s: %d results after type filter", label, len(raw_comps))
                        if len(raw_comps) >= 3:
                            break

                    # Normalize into EXACT same dict format as the
                    # working API endpoint (property.py lines 725-749)
                    for listing in raw_comps[:15]:
                        prop_info = listing.get("property") or {}
                        addr_obj = listing.get("address") or {}
                        geo = listing.get("geo") or {}
                        mls_obj = listing.get("mls") or {}
                        photos = listing.get("photos") or []

                        dist = None
                        if subject_lat and subject_lng and geo.get("lat") and geo.get("lng"):
                            dist = _haversine(subject_lat, subject_lng, geo["lat"], geo["lng"])

                        comparables.append({
                            "mls_id": str(listing.get("mlsId") or ""),
                            "address": addr_obj.get("full") or "",
                            "city": addr_obj.get("city") or "",
                            "state": addr_obj.get("state") or "",
                            "zip_code": addr_obj.get("postalCode") or "",
                            "price": listing.get("closePrice") or listing.get("listPrice") or 0,
                            "list_price": listing.get("listPrice"),
                            "close_price": listing.get("closePrice"),
                            "bedrooms": prop_info.get("bedrooms") or 0,
                            "bathrooms": prop_info.get("bathsFull") or 0,
                            "sqft": prop_info.get("area") or 0,
                            "year_built": prop_info.get("yearBuilt"),
                            "lot_size": prop_info.get("lotSize"),
                            "photo_url": photos[0] if photos else None,
                            "photos": photos,
                            "status": mls_obj.get("status") or "Closed",
                            "dom": mls_obj.get("daysOnMarket"),
                            "days_on_market": mls_obj.get("daysOnMarket"),
                            "list_date": listing.get("listDate"),
                            "close_date": listing.get("closeDate"),
                            "lat": geo.get("lat"),
                            "lng": geo.get("lng"),
                            "distance_miles": dist,
                        })

                    logger.warning("[CMA] Parsed %d comparables", len(comparables))
                    if comparables:
                        c0 = comparables[0]
                        logger.warning(
                            "[CMA] First comp: addr=%s price=%s close_date=%s dist=%s status=%s",
                            c0.get("address", "?")[:40], c0.get("price"),
                            c0.get("close_date"), c0.get("distance_miles"),
                            c0.get("status"),
                        )

                    # Market stats from normalized comps
                    comp_prices = [c["price"] for c in comparables if c.get("price")]
                    comp_ppsf = [c["price"] / c["sqft"] for c in comparables if c.get("price") and c.get("sqft")]
                    comp_dom = [c["days_on_market"] for c in comparables if c.get("days_on_market") is not None]

                    if comp_prices:
                        sorted_prices = sorted(comp_prices)
                        market_stats = {
                            "median_price": sorted_prices[len(sorted_prices) // 2],
                            "avg_price_per_sqft": int(sum(comp_ppsf) / len(comp_ppsf)) if comp_ppsf else None,
                            "avg_days_on_market": int(sum(comp_dom) / len(comp_dom)) if comp_dom else None,
                            "total_sold_last_6mo": len(comparables),
                        }
                        logger.info("Market stats: %s", market_stats)

                except Exception as e:
                    logger.warning("Failed to fetch comparables: %s", e, exc_info=True)
                    market_stats = {}
                
                # =============================================
                # CALCULATE VALUE ESTIMATE
                # =============================================
                value_estimate = {"low": 0, "mid": 0, "high": 0, "confidence": "low"}
                
                if comparables:
                    prices = [c["price"] for c in comparables if c.get("price")]
                    if prices:
                        avg_price = sum(prices) / len(prices)
                        price_range = max(prices) - min(prices) if len(prices) > 1 else avg_price * 0.1
                        
                        # Adjust based on sqft if we have it
                        subject_sqft = property_data.get("sqft")
                        if subject_sqft and market_stats.get("avg_price_per_sqft"):
                            # Use price per sqft to estimate
                            estimated = subject_sqft * market_stats["avg_price_per_sqft"]
                            value_estimate = {
                                "low": int(estimated * 0.92),
                                "mid": int(estimated),
                                "high": int(estimated * 1.08),
                                "confidence": "medium" if len(comparables) >= 3 else "low",
                            }
                        else:
                            # Use average of comparables
                            value_estimate = {
                                "low": int(avg_price - price_range * 0.5),
                                "mid": int(avg_price),
                                "high": int(avg_price + price_range * 0.5),
                                "confidence": "medium" if len(comparables) >= 5 else "low",
                            }
                        
                        # Boost confidence if we have many good comps
                        if len(comparables) >= 5:
                            value_estimate["confidence"] = "high"
                        
                        logger.info(f"Value estimate: {value_estimate}")
                
                # =============================================
                # GENERATE BRANDED PDF REPORT
                # =============================================
                pdf_url = None
                company_name = ""
                account_name = ""
                agent_email_addr = ""
                try:
                    cur.execute("""
                        SELECT
                            a.primary_color, a.secondary_color,
                            a.logo_url, a.email_logo_url,
                            a.default_theme_id, a.name,
                            a.website_url,
                            u.job_title, u.license_number,
                            COALESCE(u.photo_url, u.avatar_url),
                            u.company_name, u.email
                        FROM accounts a
                        JOIN users u ON u.account_id = a.id
                        WHERE a.id = %s::uuid
                        LIMIT 1
                    """, (account_id,))
                    brand_row = cur.fetchone()

                    if brand_row:
                        (
                            primary_color, secondary_color,
                            brand_logo, email_logo,
                            default_theme_id, account_name,
                            website_url,
                            job_title, license_number,
                            agent_photo, company_name, agent_email_addr,
                        ) = brand_row
                    else:
                        primary_color = "#1B365D"
                        secondary_color = "#B8860B"
                        brand_logo = email_logo = None
                        default_theme_id = 4
                        account_name = ""
                        website_url = ""
                        job_title = license_number = agent_photo = company_name = agent_email_addr = ""

                    report_data_for_pdf = {
                        "report_type": "seller",
                        "theme": default_theme_id or 4,
                        "accent_color": secondary_color or primary_color or "#34d1c3",
                        "property_address": prop_address,
                        "property_city": prop_city,
                        "property_state": prop_state,
                        "property_zip": prop_zip,
                        "owner_name": property_data.get("owner_name", ""),
                        "sitex_data": {
                            "latitude": property_data.get("latitude"),
                            "longitude": property_data.get("longitude"),
                            "bedrooms": property_data.get("bedrooms"),
                            "bathrooms": property_data.get("bathrooms"),
                            "sqft": property_data.get("sqft"),
                            "lot_size": property_data.get("lot_size"),
                            "year_built": property_data.get("year_built"),
                            "assessed_value": 0,
                            "owner_name": property_data.get("owner_name", ""),
                        },
                        "comparables": comparables[:6],
                        "agent": {
                            "name": agent_name,
                            "title": job_title or "Realtor\u00ae",
                            "phone": agent_phone or "",
                            "email": agent_email_addr or "",
                            "license_number": license_number or "",
                            "photo_url": agent_photo or "",
                            "company_name": company_name or account_name or "",
                            "logo_url": brand_logo or "",
                        },
                        "branding": {
                            "display_name": account_name or "",
                            "logo_url": brand_logo or "",
                            "primary_color": primary_color or "#1B365D",
                            "accent_color": secondary_color or "#B8860B",
                        },
                        "selected_pages": [
                            "cover", "aerial", "property",
                            "comparables", "range",
                            "market_trends", "overview",
                        ],
                    }

                    from .property_builder import PropertyReportBuilder
                    builder = PropertyReportBuilder(report_data_for_pdf)
                    html_content = builder.render_html()
                    logger.info("CMA PDF HTML rendered: %d chars", len(html_content))

                    pdf_path, _ = render_pdf(
                        run_id=str(report_id),
                        account_id=str(account_id),
                        html_content=html_content,
                        print_base=DEV_BASE,
                    )

                    s3_key = f"consumer-reports/{account_id}/{report_id}.pdf"
                    pdf_url = upload_to_r2(pdf_path, s3_key)
                    logger.info("CMA PDF uploaded: %s", pdf_url[:100] if pdf_url else "None")

                except Exception as pdf_exc:
                    logger.warning("CMA PDF generation failed (non-fatal): %s", pdf_exc)
                    pdf_url = None

                # =============================================
                # UPDATE DATABASE WITH ALL DATA
                # =============================================
                update_params = [
                    json.dumps(property_data),
                    json.dumps(comparables),
                    json.dumps(value_estimate),
                    json.dumps(market_stats),
                    pdf_url,
                    report_id,
                ]
                if pdf_url:
                    cur.execute("""
                        UPDATE consumer_reports
                        SET property_data = %s::jsonb,
                            comparables = %s::jsonb,
                            value_estimate = %s::jsonb,
                            market_stats = %s::jsonb,
                            pdf_url = %s,
                            pdf_generated_at = NOW()
                        WHERE id = %s::uuid
                    """, update_params)
                else:
                    cur.execute("""
                        UPDATE consumer_reports
                        SET property_data = %s::jsonb,
                            comparables = %s::jsonb,
                            value_estimate = %s::jsonb,
                            market_stats = %s::jsonb
                        WHERE id = %s::uuid
                    """, update_params[:4] + [report_id])
                
                # =============================================
                # DELIVER REPORT (SMS or Email)
                # =============================================
                delivered = False

                if delivery_method == "sms" and consumer_phone:
                    sms_result = send_report_sms(
                        to_phone=consumer_phone,
                        report_url=report_url,
                        agent_name=agent_name,
                        property_address=full_address
                    )
                    
                    sms_message = sms_result.get('message_body', f"Report link sent to {consumer_phone}")
                    cur.execute("""
                        INSERT INTO sms_logs (
                            account_id, consumer_report_id, to_phone, from_phone,
                            message, message_body, recipient_type, twilio_sid, 
                            status, error_message, direction
                        ) VALUES (
                            %s::uuid, %s::uuid, %s, %s,
                            %s, %s, 'consumer', %s, 
                            %s, %s, 'outbound'
                        )
                    """, (
                        account_id, report_id, consumer_phone, 
                        os.environ.get("TWILIO_PHONE_NUMBER", ""),
                        sms_message,
                        sms_message,
                        sms_result.get('message_sid'),
                        'sent' if sms_result.get('success') else 'failed',
                        sms_result.get('error')
                    ))
                    
                    if sms_result.get('success'):
                        cur.execute("""
                            UPDATE consumer_reports 
                            SET status = 'sent',
                                consumer_sms_sent_at = NOW(),
                                consumer_sms_sid = %s
                            WHERE id = %s::uuid
                        """, (sms_result.get('message_sid'), report_id))
                        # Decrement SMS credits for consumer delivery only
                        cur.execute("""
                            UPDATE accounts 
                            SET sms_credits = GREATEST(sms_credits - 1, 0)
                            WHERE id = %s::uuid
                        """, (account_id,))
                        delivered = True

                elif delivery_method == "email" and consumer_email:
                    logger.info(f"Email delivery via Resend to {consumer_email} (report URL: {report_url})")
                    resend_key = os.environ.get("RESEND_API_KEY", "")
                    if not resend_key:
                        logger.warning("RESEND_API_KEY not set — marking as sent without email")
                        cur.execute("""
                            UPDATE consumer_reports
                            SET status = 'sent', consumer_email_sent_at = NOW()
                            WHERE id = %s::uuid
                        """, (report_id,))
                        delivered = True
                    else:
                        lead_name = (property_data.get("owner_name") or "").split()[0] if property_data.get("owner_name") else ""
                        greeting = f"Hi {lead_name}," if lead_name else "Hi,"
                        _co = company_name or account_name or ""
                        _ae = agent_email_addr or ""

                        agent_lines = ""
                        if agent_phone:
                            agent_lines += f'<p style="margin:0 0 4px;font-size:14px;color:#374151;">\U0001f4f1 {agent_phone}</p>'
                        if _ae:
                            agent_lines += f'<p style="margin:0;font-size:14px;color:#374151;">\u2709\ufe0f <a href="mailto:{_ae}" style="color:#4F46E5;text-decoration:underline;">{_ae}</a></p>'

                        prepared_by = f"{agent_name}"
                        if _co:
                            prepared_by += f" at {_co}"

                        cta_btn = f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0;">
                          <tr><td align="center">
                            <a href="{report_url}" target="_blank" style="display:inline-block;background-color:#4F46E5;color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:16px;font-weight:bold;text-decoration:none;padding:14px 32px;border-radius:8px;">
                              View My Report
                            </a>
                          </td></tr>
                        </table>'''

                        content_html = f'''<p style="margin:0 0 20px;font-family:Georgia,'Times New Roman',serif;font-size:18px;color:#111827;">
                            {greeting}
                          </p>
                          <p style="margin:0 0 8px;font-size:15px;line-height:1.7;color:#374151;">
                            Your personalized property report for <strong>{prop_address}</strong> is ready.
                          </p>
                          {cta_btn}
                          <p style="margin:0 0 12px;font-size:15px;line-height:1.7;color:#374151;">
                            This report was prepared by <strong>{prepared_by}</strong>.
                          </p>
                          <div style="background-color:#F9FAFB;border-radius:8px;padding:16px 20px;margin:20px 0;">
                            <p style="margin:0 0 8px;font-size:14px;font-weight:600;color:#111827;">Questions? Contact {agent_name}:</p>
                            {agent_lines}
                          </div>
                          <p style="margin:0;font-size:13px;line-height:1.6;color:#6b7280;">
                            This is an automated report from TrendyReports.
                          </p>'''

                        email_html = f'''<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta name="color-scheme" content="light only">
  <title>Your Home Value Report</title>
  <style>
    body,table,td,p,a{{ -webkit-text-size-adjust:100%; }}
    body{{ margin:0!important;padding:0!important; }}
    @media (prefers-color-scheme:dark){{ .email-outer{{ background-color:#232323!important; }} }}
    @media screen and (max-width:600px){{ .email-wrapper{{ width:100%!important; }} .content-pad{{ padding:24px 20px!important; }} }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F8FAFC;" class="email-outer"><tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" class="email-wrapper" style="max-width:600px;width:100%;">
        <tr><td align="center" style="background:linear-gradient(135deg,#4F46E5 0%,#6366F1 50%,#818CF8 100%);background-color:#4F46E5;padding:28px 24px 20px;border-radius:12px 12px 0 0;">
          <img src="https://www.trendyreports.io/white.png" width="160" alt="TrendyReports" style="display:block;max-height:40px;width:auto;height:auto;">
        </td></tr>
        <tr><td style="background-color:#ffffff;padding:32px;" class="content-pad">
          {content_html}
        </td></tr>
        <tr><td style="background-color:#ffffff;border-top:1px solid #EEF2FF;padding:20px 32px;border-radius:0 0 12px 12px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
            <p style="margin:0 0 4px;font-size:13px;font-weight:600;color:#6366F1;">TrendyReports</p>
            <p style="margin:0 0 12px;font-size:12px;color:#9ca3af;">Branded Real Estate Reports</p>
            <p style="margin:0;font-size:11px;color:#9ca3af;">
              <a href="mailto:support@trendyreports.io" style="color:#6b7280;text-decoration:underline;">Contact Support</a>
              &nbsp;&bull;&nbsp; &copy; 2026 TrendyReports
            </p>
          </td></tr></table>
        </td></tr>
      </table>
    </td>
  </tr></table>
</body></html>'''

                        try:
                            from_addr = os.environ.get("EMAIL_FROM_ADDRESS", "TrendyReports <noreply@trendyreports.io>")
                            resp = httpx.post(
                                "https://api.resend.com/emails",
                                headers={
                                    "Authorization": f"Bearer {resend_key}",
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "from": from_addr,
                                    "to": [consumer_email],
                                    "subject": "Your Home Value Report is Ready",
                                    "html": email_html,
                                },
                                timeout=15.0,
                            )
                            email_sent = resp.status_code in (200, 201)
                        except Exception as email_err:
                            logger.warning(f"Resend email to consumer failed: {email_err}")
                            email_sent = False

                        if email_sent:
                            cur.execute("""
                                UPDATE consumer_reports
                                SET status = 'sent', consumer_email_sent_at = NOW()
                                WHERE id = %s::uuid
                            """, (report_id,))
                            delivered = True
                            logger.info(f"CMA report email sent to {consumer_email}")
                        else:
                            logger.warning(f"CMA email delivery failed for {consumer_email}, status={getattr(resp, 'status_code', 'N/A')}")
                            cur.execute("""
                                UPDATE consumer_reports
                                SET status = 'sent', consumer_email_sent_at = NOW()
                                WHERE id = %s::uuid
                            """, (report_id,))
                            delivered = True

                else:
                    logger.warning(f"No valid delivery method for report {report_id}: method={delivery_method}")
                    cur.execute("""
                        UPDATE consumer_reports SET status = 'sent' WHERE id = %s::uuid
                    """, (report_id,))
                    delivered = True

                if delivered:
                    # Notify agent via SMS (free — no credit decrement)
                    if agent_phone:
                        lead_name = property_data.get("owner_name")
                        logger.info(f"Sending agent notification to {agent_phone} for lead on {full_address}")
                        agent_sms = send_agent_notification_sms(
                            to_phone=agent_phone,
                            property_address=full_address,
                            report_url=report_url,
                            lead_name=lead_name,
                            consumer_phone=consumer_phone,
                            consumer_email=consumer_email,
                        )
                        
                        if agent_sms.get('success'):
                            logger.info(f"Agent notification sent: {agent_sms.get('message_sid')}")
                            cur.execute("""
                                UPDATE consumer_reports 
                                SET agent_sms_sent_at = NOW(),
                                    agent_sms_sid = %s
                                WHERE id = %s::uuid
                            """, (agent_sms.get('message_sid'), report_id))
                        else:
                            logger.error(f"Agent notification failed: {agent_sms.get('error')}")
                    
                    logger.info(f"Consumer report processed successfully: {report_id}")
                    return {"ok": True, "report_id": report_id}
                else:
                    cur.execute("""
                        UPDATE consumer_reports 
                        SET status = 'failed',
                            error = %s
                        WHERE id = %s::uuid
                    """, ('Delivery failed', report_id))
                    
                    logger.error(f"Failed to deliver report {report_id}")
                    
                    if self.request.retries < self.max_retries:
                        raise self.retry(countdown=60 * (self.request.retries + 1))
                    
                    return {"ok": False, "error": sms_result.get('error')}
                    
    except Exception as e:
        logger.exception(f"Error processing consumer report {report_id}: {e}")
        
        # Update status to failed
        try:
            with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE consumer_reports 
                        SET status = 'failed', error = %s 
                        WHERE id = %s::uuid
                    """, (str(e)[:500], report_id))
        except:
            pass
        
        raise


def run_redis_consumer_forever():
    """
    Redis consumer bridge - polls Redis queue and dispatches to Celery worker.
    Uses proper SSL configuration for secure Redis connections (Upstash).
    
    Includes retry logic with exponential backoff for:
    - Rate limiting (Upstash free tier: 10k commands/day)
    - Connection errors
    - Temporary failures
    """
    import time
    from redis.exceptions import ConnectionError, ResponseError
    
    r = None
    backoff = 1  # Initial backoff in seconds
    max_backoff = 60  # Maximum backoff
    consecutive_errors = 0
    
    print(f"🔄 Redis consumer started, polling queue: {QUEUE_KEY}")
    
    while True:
        try:
            # Create/reconnect if needed
            if r is None:
                r = create_redis_connection(REDIS_URL)
                print(f"✅ Redis connected")
                backoff = 1  # Reset backoff on successful connection
                consecutive_errors = 0
            
            item = r.blpop(QUEUE_KEY, timeout=5)
            
            if not item:
                continue
            
            _, payload = item
            data = json.loads(payload)
            print(f"📥 Received job: run_id={data['run_id']}, type={data['report_type']}")
            generate_report.delay(data["run_id"], data["account_id"], data["report_type"], data.get("params") or {})
            
            # Reset backoff on successful operation
            backoff = 1
            consecutive_errors = 0
            
        except ResponseError as e:
            error_msg = str(e).lower()
            consecutive_errors += 1
            
            if "rate-limited" in error_msg or "rate limit" in error_msg:
                print(f"⚠️  Redis rate-limited! Backing off for {backoff}s (error #{consecutive_errors})")
                print(f"   Consider upgrading your Upstash plan or contact support@upstash.com")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
                r = None  # Force reconnection
            else:
                print(f"❌ Redis response error: {e}")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
                r = None
                
        except ConnectionError as e:
            consecutive_errors += 1
            print(f"❌ Redis connection error (#{consecutive_errors}): {e}")
            print(f"   Reconnecting in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
            r = None  # Force reconnection
            
        except Exception as e:
            consecutive_errors += 1
            print(f"❌ Unexpected error in consumer (#{consecutive_errors}): {e}")
            time.sleep(min(5, backoff))
            # Don't reset connection for non-Redis errors

# NOTE: To start the consumer alongside the worker, we will run a second process
# in dev (e.g., `poetry run python -c "from worker.tasks import run_redis_consumer_forever as c;c()"`)
# In Render, we can use a process manager or a small separate service to run the consumer.

