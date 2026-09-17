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
from .property_tasks.property_report import embed_images_as_base64
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

def _fetch_affiliate_branding(cur, account_id: str) -> dict | None:
    """Fetch a single affiliate_branding row as a dict, or None."""
    cur.execute("""
        SELECT brand_display_name, logo_url, email_logo_url,
               primary_color, accent_color, rep_photo_url,
               contact_line1, contact_line2, website_url,
               footer_logo_url, email_footer_logo_url,
               COALESCE(branding_override, false) AS branding_override,
               -- D-060. NULL means this account has not set its own, and the
               -- render path falls back to the platform address attributed to
               -- TrendyReports rather than to this brand. Selected last so the
               -- positional indices above are untouched.
               postal_address
        FROM affiliate_branding
        WHERE account_id = %s::uuid
    """, (account_id,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        "display_name": row[0], "logo_url": row[1],
        "email_logo_url": row[2], "primary_color": row[3],
        "accent_color": row[4], "rep_photo_url": row[5],
        "contact_line1": row[6], "contact_line2": row[7],
        "website_url": row[8],
        "footer_logo_url": row[9], "email_footer_logo_url": row[10],
        "branding_override": row[11],
        "postal_address": row[12],   # D-060
    }


def _resolve_email_brand(cur, account_id: str):
    """
    Resolve white-label brand and account_type for email sending.

    REGULAR accounts (sponsored or not) always use their own branding
    from the accounts table. No sponsor/affiliate fallback.

    INDUSTRY_AFFILIATE / TITLE_COMPANY use the affiliate_branding table
    (with company→rep inheritance when branding_override is false).
    """
    brand = None
    acc_type = "REGULAR"
    try:
        cur.execute("""
            SELECT account_type, parent_account_id::text
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        acc_row = cur.fetchone()

        if acc_row:
            acc_type, parent_id = acc_row

            if acc_type == 'REGULAR':
                brand = _build_regular_brand(cur, account_id)

            elif acc_type in ('INDUSTRY_AFFILIATE', 'TITLE_COMPANY'):
                own_brand = _fetch_affiliate_branding(cur, account_id)

                if acc_type == 'INDUSTRY_AFFILIATE' and parent_id and own_brand and not own_brand.get("branding_override"):
                    company_brand = _fetch_affiliate_branding(cur, parent_id)
                    if company_brand:
                        brand = {
                            **company_brand,
                            "rep_photo_url": own_brand.get("rep_photo_url") or company_brand.get("rep_photo_url"),
                            "contact_line1": own_brand.get("contact_line1") or company_brand.get("contact_line1"),
                            "contact_line2": own_brand.get("contact_line2") or company_brand.get("contact_line2"),
                        }
                        brand.pop("branding_override", None)
                    else:
                        brand = {k: v for k, v in own_brand.items() if k != "branding_override"}
                elif own_brand:
                    brand = {k: v for k, v in own_brand.items() if k != "branding_override"}

    except Exception as e:
        print(f"⚠️  Error loading brand for email: {e}")
    return brand, acc_type


def _build_regular_brand(cur, account_id: str) -> dict | None:
    """Build brand dict from accounts + users tables for a REGULAR account."""
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
    row = cur.fetchone()
    if not row:
        return None

    first_name = row[1] or ""
    last_name = row[2] or ""
    job_title = row[3] or ""
    phone = row[4] or ""
    email = row[5] or ""
    website = row[6] or ""

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

    return {
        "display_name": row[7],
        "logo_url": row[8],
        "email_logo_url": row[9],
        "primary_color": row[10] or "#4F46E5",
        "accent_color": row[11] or "#1a1a1a",
        "rep_photo_url": row[0],
        "contact_line1": contact_line1,
        "contact_line2": contact_line2,
        "website_url": website,
        "footer_logo_url": row[12],
        "email_footer_logo_url": row[13],
    }


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

    # ── EMAIL-DEPTH-PASS1: every report type that has listings should
    # render them in the email. Source from whichever key the builder
    # populated (`listings` or `listings_sample`) and apply a per-type
    # cap so we don't blow past Gmail's 102 KB clip threshold.
    available_listings = (
        result.get("listings")
        or result.get("listings_sample")
        or []
    )

    EMAIL_LISTING_CAPS = {
        "market_snapshot":      8,
        "new_listings_gallery": 15,
        "new_listings":         15,
        "closed":               12,
        "inventory":            12,
        "featured_listings":    8,
        "open_houses":          12,
        "price_bands":          6,
    }
    # CAPS-SPLIT-SNAPSHOT-CATALOG — `audience_email_cap` is an optional hint
    # from the builder (currently used by new_listings_gallery for audience-
    # based caps). If present, it overrides the per-type default. Falls back
    # to EMAIL_LISTING_CAPS for everything else.
    email_cap_default = EMAIL_LISTING_CAPS.get(report_type, 10)
    audience_override = (
        result.get("audience_email_cap") if isinstance(result, dict) else None
    )
    cap = audience_override or email_cap_default
    capped_listings = available_listings[:cap]

    payload = {
        "report_type": report_type,
        "city": city,
        "zip_codes": zips,
        "lookback_days": lookback,
        "metrics": email_metrics,
        "pdf_url": pdf_url,
        "preset_display_name": result.get("preset_display_name") if isinstance(result, dict) else None,
        "filter_description": result.get("filters_label") if isinstance(result, dict) else None,
        # total_listings preserved for legacy AI-prompt context.
        "total_listings": result.get("total_listings", len(available_listings)) if isinstance(result, dict) else 0,
        "total_shown": result.get("total_shown", len(capped_listings)) if isinstance(result, dict) else 0,
        "audience_key": result.get("audience_key", "all") if isinstance(result, dict) else "all",
        # New EMAIL-DEPTH-PASS1 fields:
        "listings": capped_listings,
        "total_available": len(available_listings),
        "showing": min(cap, len(available_listings)),
    }

    return payload


# ── email_log lifecycle (D-065) ─────────────────────────────────────────────
#
# THE ORDERING DECISION, AND WHY IT IS THIS ONE.
#
# The delivery record used to be a single INSERT after the send, on the caller's
# cursor, inside the caller's transaction — which commits only at the very end
# of the block. So a record of a send that really happened could be undone by a
# later failure, or by the process dying before the commit. The email is already
# gone: SendGrid accepted it over the network and no database rollback retracts
# that. Only the evidence disappeared.
#
# Neither ordering is free, and the choice is between which way you want to be
# wrong:
#
#   log AFTER the send, commit immediately
#       loses the record if the process dies in the gap between the provider
#       returning and the commit. FAILS TOWARDS SILENCE — the same failure this
#       is meant to fix, just with a smaller window.
#
#   log BEFORE the send, commit immediately, update after   <-- CHOSEN
#       can leave a row saying 'sending' for an attempt that never reached the
#       provider. FAILS TOWARDS AN HONEST "we tried and do not know", which is
#       legible to whoever reads the table and, unlike silence, is something a
#       person can act on.
#
# The asymmetry is the whole argument: a false absence hides a delivery that
# happened; a false 'sending' records an attempt that also happened. Only one of
# those misleads.
#
# Both writes use their own short-lived autocommit connection, so neither can be
# rolled back by anything the caller does afterwards. `status` is plain TEXT with
# no CHECK constraint (0027), so 'sending' needs no migration — but 0027's
# COMMENT still lists only sent/suppressed/failed/unknown and is now incomplete.
#
# Row cardinality is deliberately unchanged: one row per attempt, created then
# updated. admin.py:113 and :197 COUNT(*) this table, and an extra row per send
# would silently inflate every email metric in the admin dashboard.


def _open_log_connection():
    """Own connection, autocommit, RLS session var set."""
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    return conn


def _log_email_attempt(account_id, run_id, schedule_id, recipients, subject):
    """
    Record that a send is about to be attempted. Committed before the provider
    is called. Returns the row id, or None if even this failed — in which case
    the send still proceeds, because losing the log is not a reason to withhold
    a report.
    """
    try:
        with _open_log_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT set_config('app.current_account_id', %s, false)",
                    (str(account_id),),
                )
                cur.execute("""
                    INSERT INTO email_log (
                        account_id, schedule_id, report_id, provider,
                        to_emails, subject, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'sending')
                    RETURNING id::text
                """, (account_id, schedule_id, run_id, 'sendgrid', recipients, subject))
                return cur.fetchone()[0]
    except Exception as e:
        logger.warning(f"Could not record email attempt (proceeding with send): {e}")
        return None


def _finalise_email_log(log_id, account_id, status, status_code, error):
    """
    Close out the attempt row. Committed on its own connection so it cannot be
    rolled back by the caller's transaction. A row left at 'sending' means the
    process died between the provider call and here — which is exactly what it
    should say.
    """
    if not log_id:
        return
    try:
        with _open_log_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT set_config('app.current_account_id', %s, false)",
                    (str(account_id),),
                )
                cur.execute("""
                    UPDATE email_log
                    SET status = %s, response_code = %s, error = %s
                    WHERE id = %s::uuid
                """, (status, status_code, (error or None), log_id))
    except Exception as e:
        logger.warning(f"Could not finalise email log {log_id} (non-critical): {e}")


# Window within which an unfinished 'sending' row is treated as a live attempt
# by another worker rather than as debris from a dead one. Comfortably past
# task_time_limit (300s), so a send that is genuinely in flight is never
# mistaken for a stuck row — and short enough that a row stranded by a crash
# stops blocking legitimate retries within the hour.
DUPLICATE_SEND_WINDOW_MINUTES = int(os.getenv("DUPLICATE_SEND_WINDOW_MINUTES", "10"))


def _already_delivered(account_id, run_id):
    """
    Has this report already been sent, or is a send in flight right now?

    THE QUESTION THIS ANSWERS: if generate_report runs twice for the same
    report_run_id, what must not happen twice? Rendering is wasteful but
    harmless — it overwrites its own R2 object and reuses the same
    report_generations row, and check_usage_limit excludes scheduled runs, so
    nothing double-counts. Sending is the one step that cannot be taken back:
    the recipient has the email. So the guard is scoped to delivery, not to the
    task.

    Returns a reason string when the send should be refused, else None.

    WHAT IT BLOCKS ON, AND WHAT IT DELIBERATELY DOES NOT:

      'sent'       blocks unconditionally and forever. The email exists in
                   someone's inbox; no elapsed time makes it safe to send again.

      'sending'    blocks only inside DUPLICATE_SEND_WINDOW_MINUTES. A recent
                   one means another worker is mid-send and this is a genuine
                   concurrent duplicate. An OLD one is debris from a process
                   that died between the provider call and the finalise (D-065
                   documents that window) — and blocking on it forever would
                   mean one crash permanently barred an account's reports.
                   That is the §0.6 trap: a guard that refuses input is a guard
                   that can refuse LEGITIMATE input.

      'failed'     never blocks. A failed send is exactly what a retry is for.

      'suppressed' never blocks. Nothing was delivered, and re-running simply
                   suppresses again — harmless, and blocking would hide a
                   later re-subscription.
    """
    try:
        with _open_log_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT set_config('app.current_account_id', %s, false)",
                    (str(account_id),),
                )
                cur.execute("""
                    SELECT status, created_at
                    FROM email_log
                    WHERE report_id = %s::uuid
                      AND (
                            status = 'sent'
                         OR (status = 'sending'
                             AND created_at > NOW() - (%s || ' minutes')::interval)
                      )
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (run_id, DUPLICATE_SEND_WINDOW_MINUTES))
                row = cur.fetchone()
    except Exception as e:
        # Failing open is deliberate. If the check itself cannot run we do not
        # know whether the report was sent, and withholding a scheduled report
        # on a database hiccup is a worse outcome than a rare duplicate — the
        # product's whole promise is that reports go out.
        logger.warning(f"Duplicate-send check failed, proceeding with send: {e}")
        return None

    if not row:
        return None
    status, when = row
    if status == 'sent':
        return f"already sent at {when.isoformat()}"
    return f"another send is in flight (started {when.isoformat()})"


def _record_refused_send(account_id, run_id, schedule_id, recipients, subject, reason):
    """
    A refusal is an event. Record it.

    Without this the guard would be the SEVENTH instance of the shape this
    project keeps finding: correct behaviour, silently. A retry that is refused
    leaves no trace, and the next person asking "why did this run not send?"
    finds a completed report, no email_log row for the retry, and nothing to
    explain the gap.

    A log line is not enough — that lesson is D-064's: retention is short and
    logs are not queryable alongside the rows they explain.

    CARDINALITY NOTE, now acted on: this adds a row to email_log, and the two
    admin counters COUNT(*)ed that table for "emails in the last 24 hours". A
    refusal is not an email. Those queries now filter on a delivery-status
    allowlist — which matters from here, because enabling acks_late makes
    redelivery (and therefore refusal) a routine event rather than a manual
    re-run. See apps/api/src/api/routes/admin.py.
    """
    try:
        with _open_log_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT set_config('app.current_account_id', %s, false)",
                    (str(account_id),),
                )
                cur.execute("""
                    INSERT INTO email_log (
                        account_id, schedule_id, report_id, provider,
                        to_emails, subject, status, error
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'duplicate_suppressed', %s)
                """, (account_id, schedule_id, run_id, 'sendgrid',
                      recipients, subject, f"send refused: {reason}"))
    except Exception as e:
        logger.warning(f"Could not record the refused send (non-critical): {e}")


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
    subject = f"Your {report_type.replace('_', ' ').title()} Report"

    # Delivery idempotency. Scoped to the send, not to the task: a second
    # render is wasteful, a second send is not retractable.
    refusal = _already_delivered(account_id, run_id)
    if refusal:
        logger.error(
            "REPORT RUN %s: refusing duplicate send for schedule %s — %s",
            run_id, schedule_id, refusal,
        )
        _record_refused_send(account_id, run_id, schedule_id, recipients, subject, refusal)
        # 200 rather than an error: from the caller's point of view the report
        # has been delivered, and returning a failure would make the run record
        # itself as failed_email for a report that is sitting in the recipient's
        # inbox.
        return (200, f"duplicate send refused: {refusal}")

    # Committed BEFORE the provider is called — see the block above this
    # function for why this ordering and not the other one.
    log_id = _log_email_attempt(account_id, run_id, schedule_id, recipients, subject)

    try:
        status_code, response_text = send_schedule_email(
            account_id=account_id,
            recipients=recipients,
            payload=email_payload,
            account_name=account_name,
            db_conn=conn,
            brand=brand,
            account_type=acc_type,
        )
    except Exception as send_error:
        # Close the row out before the exception leaves this function, so the
        # record survives whatever the caller's transaction does next.
        _finalise_email_log(log_id, account_id, 'failed', 500, str(send_error)[:2000])
        raise

    if status_code == 202:
        email_status = 'sent'
    elif status_code == 200 and 'suppressed' in response_text.lower():
        email_status = 'suppressed'
    else:
        email_status = 'failed'

    _finalise_email_log(
        log_id, account_id, email_status, status_code,
        None if status_code in (200, 202) else response_text,
    )

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

    D-033. Returning early when the key is missing is the right SHAPE — unlike
    D-031 it never claimed to have sent anything. What was wrong is that the
    skip left nothing behind but a `logger.warning`, and this is the only
    mechanism that tells an account owner a scheduled report failed. A schedule
    can then break every week and the customer's first signal is a recipient
    asking where the report went.

    Worse in combination: the same missing key that disables this alert is what
    D-031 needed the alert for. Fix the reporting and the cause together or the
    fix is unverifiable — you cannot tell from production whether it worked,
    because the thing that would tell you is the thing that is off.

    So the suppression is now RECORDED, in the same table the notification
    would have been logged in. D-064's lesson: a log line is not a record.
    "Was the owner told?" has to be answerable from `email_log` beside the rows
    it explains, not from worker logs that have rotated.
    """
    if not schedule_id:
        return

    resend_key = os.environ.get("RESEND_API_KEY", "")
    if not resend_key:
        logger.error(
            "FAILURE NOTIFICATION SUPPRESSED for schedule %s: RESEND_API_KEY is "
            "not configured on the worker. The account owner has NOT been told "
            "their scheduled report failed. Original error: %s",
            schedule_id, error_msg,
        )
        # Recorded on its own connection so it survives whatever the caller
        # does next — same reasoning as D-065, which is why `email_log` is
        # trustworthy enough to be worth writing to at all.
        try:
            with _open_log_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT set_config('app.current_account_id', %s, false)",
                        (str(account_id),),
                    )
                    cur.execute("""
                        INSERT INTO email_log (
                            account_id, schedule_id, provider, to_emails,
                            subject, response_code, status, error
                        ) VALUES (
                            %s::uuid, %s::uuid, 'resend', %s,
                            %s, NULL, 'suppressed', %s
                        )
                    """, (
                        account_id, schedule_id, [],
                        f"[not sent] {report_type} report failed",
                        "RESEND_API_KEY not configured — failure notification "
                        f"suppressed. Underlying failure: {str(error_msg)[:400]}",
                    ))
        except Exception as record_error:
            logger.error(
                "Could not even record the suppressed failure notification for "
                "schedule %s: %s", schedule_id, record_error, exc_info=True,
            )
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


# THIS TASK DOES NOT RETRY, AND NOW SAYS SO (D-071).
#
# It used to be decorated `autoretry_for=(Exception,)`, `retry_backoff=True`,
# `retry_backoff_max=600`, `retry_kwargs={"max_retries": 3}` — and it had never
# retried, not once. The body is a single `try` whose handler RETURNS a dict
# instead of raising, so nothing ever escaped for `autoretry_for` to catch.
# Four lines of resilience config describing behaviour the code prevented.
#
# Compare `generate_property_report`, which carries the same decorator and ends
# its handler with a bare `raise` and the comment "Re-raise to trigger Celery
# retry". Same intent, one letter of difference in outcome. That task does
# retry. This one is the one that sends email.
#
# THE ONE ROUTE THAT DID REACH IT WAS THE WORST POSSIBLE ONE. The failure
# handler below was itself unguarded: it opens a database connection and runs
# four UPDATEs. If that raised — and a database it cannot reach is exactly the
# sort of thing that put it in the handler to begin with — the exception
# escaped, autoretry fired, and the whole task re-ran from the top: re-render,
# re-upload, RE-SEND. A retry path that opens only when the error handler
# itself fails is a guard that arms exactly when everything else has already
# gone wrong. That is the inverse of the shape this project keeps finding: not
# "silent when it works", but "active only when nothing else is".
#
# The handler is now guarded, so that route is closed regardless. The decorator
# is removed rather than made to work, because making retries real here is NOT
# the one-line change it looks like:
#
#   - The handler increments `schedules.consecutive_failures` and AUTO-PAUSES
#     the schedule at 3. It runs on every attempt, so four attempts would be
#     four increments — one transient failure would pause the schedule.
#   - It writes terminal status to `report_generations` and `schedule_runs` on
#     every attempt too, so a run that failed twice and then succeeded would
#     have been recorded as failed — a false negative in the tables D-061 and
#     D-062 exist to make trustworthy.
#
# Real retries want the handler to distinguish "attempt failed" from "task
# failed", writing terminal state only on the last attempt. Worth doing — a
# transient SimplyRETS or PDFShift blip currently costs that day's report
# outright — but it is a behaviour change with its own review, not a decorator.
#
# `bind=True` is kept deliberately: `self` is unused today, but it is what a
# retry implementation needs, and removing it would change the signature for no
# benefit.
@celery.task(
    name="generate_report",
    bind=True,
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

                # Mark the schedule run as actually started.
                #
                # schedule_runs.started_at existed since 0006 and was NEVER
                # WRITTEN by anything — declared, read by the API, and used as
                # a predicate at the old :1289 writer where it silently matched
                # every row. Without this, "enqueued but never picked up" is
                # indistinguishable from "picked up and stranded later", which
                # is exactly the ambiguity that made 58 stranded rows hard to
                # diagnose. The staleness sweep in schedules_tick.py depends on
                # this being honest. See D-062.
                cur.execute("""
                    UPDATE schedule_runs
                    SET status = 'processing', started_at = NOW()
                    WHERE report_run_id = %s::uuid AND started_at IS NULL
                """, (run_id,))
            conn.commit()
        print(f"✅ REPORT RUN {run_id}: persist_status complete")
        
        # ===== PRICING-003: CHECK MARKET REPORT LIMIT FOR SCHEDULED REPORTS =====
        if schedule_id:
            limit_result = check_usage_limit(account_id, product="market_reports")
            log_limit_decision_worker(account_id, limit_result)

            if not limit_result["can_proceed"]:
                msg = (
                    f"Market report limit reached "
                    f"({limit_result['used']}/{limit_result['limit']})"
                )
                print(f"🚫 Skipping scheduled report: {msg}")

                with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                        cur.execute("""
                            UPDATE report_generations
                            SET status='skipped_limit',
                                error_message=%s,
                                processing_time_ms=%s
                            WHERE id=%s
                        """, (
                            msg,
                            int((time.perf_counter() - started) * 1000),
                            run_id
                        ))

                        try:
                            cur.execute("""
                                UPDATE schedule_runs
                                SET status='skipped_limit', finished_at=NOW()
                                WHERE report_run_id=%s
                            """, (run_id,))
                        except Exception:
                            pass  # schedule_runs may not exist yet

                    conn.commit()

                return {"ok": False, "reason": "limit_reached", "run_id": run_id}
        # ===== END PRICING-003 =====

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
            elif rt_normalized == "inventory":
                # INVENTORY: total Active + recent Closed, IN PARALLEL.
                #
                # Two queries because months of supply needs two different
                # windows and one request cannot carry both: the numerator is
                # ALL current inventory (no date filter) and the denominator is
                # closings in the last 90 days. They are fetched concurrently
                # rather than back-to-back, so the added wall-clock is
                # max(0, closed - active) rather than the sum — the same
                # ThreadPoolExecutor shape market_trends.py already uses for
                # the property report's gauge.
                #
                # The listings TABLE is served from the Active result, filtered
                # by list_date client-side in build_inventory_result, which is
                # what it already did. So this replaces one query with two, not
                # two with three.
                from concurrent.futures import ThreadPoolExecutor
                from .query_builders import build_inventory_active, build_inventory_closed
                from .vendors.simplyrets import count_properties

                active_query = build_inventory_active(_params)
                closed_query = build_inventory_closed(_params)
                print(f"🔍 REPORT RUN {run_id}: inventory active_query={active_query}")
                print(f"🔍 REPORT RUN {run_id}: inventory closed_query={closed_query}")

                INVENTORY_FETCH_LIMIT = 1000
                with ThreadPoolExecutor(max_workers=3) as pool:
                    # THE NUMERATOR IS A COUNT, NOT A LIST (D-081). Months of
                    # supply divides total inventory by a sales rate; it never
                    # needed the listings. One `count=true` request answers it
                    # exactly at any size, so the 1000-row ceiling that made
                    # large markets read as "not enough recent sales" (D-078)
                    # stops existing rather than moving.
                    fut_count = pool.submit(count_properties, active_query)
                    # The listings are still fetched, for the TABLE — which
                    # shows recently-listed actives and filters client-side,
                    # because `mindate` does nothing (D-075, confirmed in
                    # production). Truncation here costs table rows, not a
                    # wrong metric, and the PDF caps the table at 200 anyway.
                    fut_active = pool.submit(fetch_properties, active_query, INVENTORY_FETCH_LIMIT)
                    fut_closed = pool.submit(fetch_properties, closed_query, INVENTORY_FETCH_LIMIT)
                    active_total = fut_count.result(timeout=90)
                    active_raw = fut_active.result(timeout=90)
                    closed_raw = fut_closed.result(timeout=90)

                # A fetch that hit its limit returns a FLOOR, not a count, and
                # months of supply divides by one and multiplies by the other.
                # Rather than publishing a number built on a truncated input,
                # the flags travel with the data and moi refuses. See D-056 —
                # the failure this whole line of work exists to stop is a
                # number that looks like a measurement and is not.
                # THE DENOMINATOR STILL COMES FROM THE LISTINGS, deliberately.
                # It could be a count too — `status=Closed&minclosedate=…` with
                # `count=true` — but that would make the sales rate depend
                # entirely on `minclosedate` being honoured, and the production
                # probe has confirmed only that the parameter FILTERS, not that
                # it filters correctly at a real date (D-074). The listings are
                # fetched and re-filtered on `close_date` client-side, which is
                # right under either answer. Switch this to a count when D-074's
                # 90-day corroboration lands, and not before.
                #
                # The numerator no longer needs a truncation flag at all: a
                # count cannot be truncated. `active_was_truncated` is kept for
                # the case where the feed does not return the header, in which
                # case `count_properties` returns None and the row count is a
                # floor again.
                _params = {
                    **_params,
                    "active_total": active_total,
                    "active_was_truncated": (
                        active_total is None
                        and len(active_raw) >= INVENTORY_FETCH_LIMIT
                    ),
                    "closed_was_truncated": len(closed_raw) >= INVENTORY_FETCH_LIMIT,
                }
                print(
                    f"🔍 REPORT RUN {run_id}: inventory active_total={active_total} "
                    f"(authoritative count), fetched {len(active_raw)} Active listings "
                    f"for the table, {len(closed_raw)} Closed "
                    f"(truncated: active={_params['active_was_truncated']}, "
                    f"closed={_params['closed_was_truncated']})"
                )
                raw = active_raw + closed_raw

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
                # Set by the inventory branch above. A truncated fetch is a
                # floor, not a count, and months of supply must not be built
                # on one — the builder passes these straight to compute.moi.
                "active_was_truncated": _params.get("active_was_truncated", False),
                "closed_was_truncated": _params.get("closed_was_truncated", False),
                # The authoritative active count (D-081), or None when the feed
                # did not return one — in which case the builder falls back to
                # counting the rows it was given.
                "active_total": _params.get("active_total"),
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
        # Always render via the new MarketReportBuilder. The legacy
        # /print/{runId} frontend path produced unbranded PDFs missing the
        # Outfit font, themed header, and AI narrative — so we never fall
        # back to it. Reports created without an explicit theme_id default
        # to theme 1 (teal) so the builder still has a layout to use.
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

        effective_theme_id = theme_id or 1
        print(
            f"🔍 REPORT RUN {run_id}: step=generate_pdf "
            f"(server-side, theme={effective_theme_id}"
            f"{' [defaulted]' if not theme_id else ''})"
        )
        from .market_builder import MarketReportBuilder

        # Load agent info + hierarchy-resolved branding
        branding_ctx = {}
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
                cur.execute("""
                    SELECT u.first_name, u.last_name, u.job_title, u.phone,
                           u.email, COALESCE(u.photo_url, u.avatar_url),
                           u.company_name, a.name
                    FROM accounts a
                    LEFT JOIN users u ON u.account_id = a.id
                    WHERE a.id = %s::uuid LIMIT 1
                """, (account_id,))
                brow = cur.fetchone()
                brand, _ = _resolve_email_brand(cur, account_id)
                if brow:
                    agent_name = f"{brow[0] or ''} {brow[1] or ''}".strip()
                    branding_ctx = {
                        "agent_name": agent_name,
                        "agent_title": brow[2] or "",
                        "agent_phone": brow[3] or "",
                        "agent_email": brow[4] or "",
                        "agent_photo_url": brow[5] or (brand or {}).get("rep_photo_url"),
                        "company_name": (brand or {}).get("display_name") or brow[6] or brow[7] or "",
                        "logo_url": (brand or {}).get("logo_url"),
                        # PDFShift footer uses a dark-on-light logo; falls back to
                        # the header logo when no dedicated footer_logo_url is set.
                        "footer_logo_url": (brand or {}).get("footer_logo_url") or (brand or {}).get("logo_url"),
                        "primary_color": (brand or {}).get("primary_color"),
                        "accent_color": (brand or {}).get("accent_color"),
                    }
            conn.commit()

        # Merge result_json + branding + theme for the builder
        builder_data = {}
        if isinstance(result, dict):
            builder_data.update(result)
        builder_data["report_type"] = report_type
        builder_data["theme_id"] = effective_theme_id
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
        # HERO-EVERY-PAGE — Big gradient hero header repeats on EVERY page via
        # PDFShift's `header` param. Agent footer repeats on every page via
        # PDFShift's `footer` param. Both use start_at=1 (PDFShift requires
        # header.start_at and footer.start_at to match when either > 1).
        # Inline body hero (macros.report_header) has been removed from base.jinja2.
        header_html = builder.render_page_header_html()
        footer_html = builder.render_page_footer_html()
        print(
            f"🔍 REPORT RUN {run_id}: server-side HTML rendered "
            f"(body={len(html_content)} chars, header={len(header_html)}, "
            f"footer={len(footer_html)})"
        )

        # Embed external image URLs as base64 in body + header + footer docs.
        # PDFShift renders header/footer in a separate context — external images
        # need to be inlined to render reliably (avoid R2 presigned URL escaping
        # issues, MLS allowlists, etc.).
        logger.info("Embedding images as base64 for market report PDF (body + header + footer)...")
        html_content = embed_images_as_base64(html_content)
        header_html = embed_images_as_base64(header_html)
        footer_html = embed_images_as_base64(footer_html)

        pdf_path, html_url = render_pdf(
            run_id=run_id,
            account_id=account_id,
            html_content=html_content,
            header_html=header_html,
            footer_html=footer_html,
            header_start_at=1,
            footer_start_at=1,
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
        #
        # D-063. This used to read `if schedule_id and pdf_url:` — a single
        # condition guarding the entire email block, so a falsy pdf_url skipped
        # the send in its entirety: no email, no exception, nothing logged, and
        # (before D-061) no status update either. A scheduled report would be
        # marked `completed`, the recipient would get nothing, and the only
        # trace anywhere would be a NULL pdf_url on a row nobody queries.
        #
        # NOT CURRENTLY REACHABLE, and this is written down rather than
        # implied: `upload_to_r2` (utils/r2.py:29) returns a public URL, a
        # presigned URL, or a dev stub, and raises on failure — it has no path
        # that returns None or "". `pdf_url` is bound only at :1355 from that
        # call, so if control reaches here it is truthy. A raise instead lands
        # in the outer handler, which records `failed` correctly.
        #
        # It is guarded anyway because the distance to reachable is one
        # plausible refactor of upload_to_r2 — "return None instead of raising
        # so one bad upload doesn't kill the run" is a change someone makes on
        # purpose, and it would turn this into silent non-delivery the same
        # day, with nothing in any table to show for it.
        if schedule_id and not pdf_url:
            logger.error(
                "REPORT RUN %s: report completed but no PDF URL — schedule %s "
                "will not be emailed. Recording as failed rather than skipping "
                "silently.",
                run_id, schedule_id,
            )
            try:
                with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT set_config('app.current_account_id', %s, false)",
                            (str(account_id),),
                        )
                        cur.execute("""
                            UPDATE schedule_runs
                            SET status = 'failed',
                                error = 'report completed without a PDF URL; nothing was sent',
                                finished_at = NOW()
                            WHERE report_run_id = %s::uuid
                        """, (run_id,))
            except Exception as e:
                logger.warning(f"Could not record the missing-PDF failure: {e}")

        elif schedule_id and pdf_url:
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
                                # Keyed on report_run_id, like the skipped_limit
                                # writer above and the failed writer below.
                                #
                                # It used to select "the newest queued row for
                                # this schedule", which is not the same row as
                                # the run that is finishing. Once any row was
                                # stranded, a later successful run updated its
                                # own newer row and left the old one at 'queued'
                                # forever — 35 of the 57 stranded rows in
                                # production are that, over work that had
                                # completed. See D-061.
                                cur.execute("""
                                    UPDATE schedule_runs
                                    SET status = %s,
                                        finished_at = NOW()
                                    WHERE report_run_id = %s::uuid
                                """, (run_status, run_id))
                            except Exception as update_error:
                                logger.warning(f"Failed to update schedule_run status (non-critical): {update_error}")

                            conn.commit()

            except Exception as email_error:
                print(f"⚠️  Email send failed: {email_error}")
                with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        # Only when no attempt row exists — i.e. the failure
                        # happened BEFORE _send_and_log_report_email got as far
                        # as recording one (the schedule lookup, the recipient
                        # resolution). If it did record one, that row has
                        # already been closed out as 'failed' on its own
                        # connection, and inserting here would double-count:
                        # admin.py:113 and :197 COUNT(*) this table.
                        cur.execute("""
                            INSERT INTO email_log (account_id, schedule_id, report_id, provider, to_emails, subject, response_code, status, error)
                            SELECT %s, %s, %s, %s, %s, %s, %s, 'failed', %s
                            WHERE NOT EXISTS (
                                SELECT 1 FROM email_log WHERE report_id = %s::uuid
                            )
                        """, (
                            account_id, schedule_id, run_id, 'sendgrid',
                            [], 'Failed to send', 500, str(email_error),
                            run_id,
                        ))
                        # The run must reach a terminal state here. This handler
                        # catches before the outer one at the end of the task
                        # sees anything, so without this write the run sits at
                        # 'queued' forever with the traceback only in email_log.
                        # That is why a crash on the email path was invisible in
                        # the failed-runs table. See D-061.
                        cur.execute("""
                            UPDATE schedule_runs
                            SET status = 'failed_email',
                                error = %s,
                                finished_at = NOW()
                            WHERE report_run_id = %s::uuid
                        """, (str(email_error)[:2000], run_id))

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

        # GUARDED, because an exception raised in here escapes the task (D-071).
        # Everything below is bookkeeping about a failure that has already
        # happened; none of it can undo that failure, and none of it is worth
        # losing the `return` at the end of this handler for. Before this guard
        # the connection attempt was the one route that reached the retry
        # decorator, and it reached it by re-running the send.
        #
        # A failure to record the failure is itself worth seeing, so it is
        # logged with the original error beside it — a bare `except: pass` here
        # would mean a run that failed twice over, visibly neither time.
        try:
            _record_generation_failure(run_id, account_id, schedule_id, error_msg)
        except Exception as bookkeeping_error:
            logger.error(
                "REPORT RUN %s: failed to RECORD the failure — the run may be "
                "left mid-flight for the stale sweep to catch. Original error: "
                "%s. Bookkeeping error: %s",
                run_id, error_msg, bookkeeping_error, exc_info=True,
            )

        # Guarded here as well, in its own block so a bookkeeping failure does
        # not also cost the owner their notification.
        #
        # This function does guard itself internally — but its first three
        # statements sit OUTSIDE that guard, and a test written to exempt it
        # caught that rather than taking the exemption on trust. Depending on
        # another function's internal shape for this handler's safety is the
        # implicit coupling this project keeps getting caught by. Three lines
        # here removes the dependency instead of documenting it.
        try:
            _send_failure_notification(
                account_id=account_id,
                schedule_id=schedule_id,
                report_type=report_type,
                city=(params or {}).get("city"),
                error_msg=error_msg,
            )
        except Exception as notify_error:
            logger.error(
                "REPORT RUN %s: failure notification raised. Original error: "
                "%s. Notification error: %s",
                run_id, error_msg, notify_error, exc_info=True,
            )

        return {"ok": False, "error": error_msg}


def _record_generation_failure(run_id, account_id, schedule_id, error_msg):
    """
    Write the terminal failure state for a run, and count it against the
    schedule's auto-pause threshold.

    Lifted out of `generate_report`'s handler unchanged, so that the handler
    can guard it. See D-071: inline, this code's own failure escaped the task
    and triggered a retry that re-sent the report.

    NOTE for whoever makes retries real: this runs on every attempt. Called
    from a retrying task it would increment `consecutive_failures` once per
    attempt — auto-pausing a schedule after a single transient failure — and
    would mark `schedule_runs` failed for a run that later succeeded. It needs
    to become last-attempt-only before `autoretry_for` goes back on.
    """
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Parameterised rather than interpolated into SQL text — the
            # same construct hardened in the ticker in #64, found by
            # grepping for it rather than for its symptom (§0.6 rule 4).
            # Note this connection is autocommit, so `is_local => true`
            # would scope the setting to a transaction that does not exist;
            # false is correct here, and the connection closes with the
            # `with` block.
            cur.execute(
                "SELECT set_config('app.current_account_id', %s, false)",
                (str(account_id),),
            )

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


def _consumer_already_delivered(cur, report_id: str):
    """
    Has this consumer report already gone out? Returns a reason, or None.

    D-069. `task_acks_late` is worker-wide, so a worker that dies mid-task
    hands this one back too — and it sets `status='processing'` at the top with
    no already-sent check, so a redelivery repeats the whole thing: a second
    text to the consumer, a second SMS credit spent, and a second "you have a
    new lead" to the agent.

    Same shape as `_already_delivered` for scheduled reports (#61), and the
    same reasoning about what it must NOT block on: `failed` never blocks,
    because a retry is exactly what that state is for.

    Reads the timestamps rather than only the status, because they are the
    columns that record an irreversible act. A row whose status was later
    changed but which carries `consumer_sms_sent_at` has still had a text sent.
    """
    cur.execute("""
        SELECT status, consumer_sms_sent_at, consumer_email_sent_at
        FROM consumer_reports
        WHERE id = %s::uuid
    """, (report_id,))
    row = cur.fetchone()
    if not row:
        return None
    status, sms_at, email_at = row
    if sms_at:
        return f"an SMS was already sent at {sms_at.isoformat()}"
    if email_at:
        return f"an email was already sent at {email_at.isoformat()}"
    if status == 'sent':
        return "the report is already marked sent"
    return None


def _record_consumer_delivery_failure(cur, report_id: str, reason: str):
    """
    Record that delivery did NOT happen, and why.

    D-031/D-032. Four separate branches used to write `status='sent'` for an
    email that was never attempted, an email the provider rejected, and a
    report with no usable delivery method at all. `sent` is not a hopeful
    default; it is a claim, and `consumer_sms_sent_at` / `consumer_email_sent_at`
    are the evidence for it.

    Uses the EXISTING `failed` status rather than inventing a value. That is
    #56's answer applied: `email_log` gained `sending` because it needed to
    express a state that did not exist — an attempt in flight. Here the state
    does exist and is already used on the adjacent path (`Delivery failed`),
    so a new value would only be a status no UI has ever seen, which is the
    note #56 and #61 both had to write about themselves.

    The reason is stored, not just logged. D-064's lesson: a log line is not a
    record — retention is short and logs cannot be queried beside the rows they
    explain. "Why did this lead never get their report?" has to be answerable
    from the table.
    """
    cur.execute("""
        UPDATE consumer_reports
        SET status = 'failed', error = %s
        WHERE id = %s::uuid
    """, (reason[:500], report_id))
    logger.error("CONSUMER REPORT %s: not delivered — %s", report_id, reason)


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
                            "title": job_title or "Real Estate Agent",
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

                    logger.info("Embedding images as base64 for CMA PDF...")
                    html_content = embed_images_as_base64(html_content)

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
                #
                # D-069: refuse a redelivery before any provider is called.
                # Everything below this line is irreversible — a text to a
                # member of the public, a credit spent, an agent told they have
                # a lead. `acks_late` means a worker that dies mid-task hands
                # this one back, and the task sets `status='processing'` at the
                # top with nothing to stop it running the whole thing again.
                #
                # Returns ok=True. From the caller's point of view the report
                # HAS been delivered, and reporting failure for something
                # sitting in someone's inbox is the false negative the rest of
                # this branch exists to remove.
                already = _consumer_already_delivered(cur, report_id)
                if already:
                    logger.error(
                        "CONSUMER REPORT %s: refusing redelivery — %s",
                        report_id, already,
                    )
                    return {"ok": True, "report_id": report_id,
                            "note": f"redelivery refused: {already}"}

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
                        # D-031. This wrote status='sent' AND a
                        # consumer_email_sent_at timestamp for an email it had
                        # just decided not to attempt — and then fell through
                        # to SMS the agent that they had a new lead. The agent
                        # chased someone who had received nothing, and no row
                        # anywhere contradicted the claim.
                        _record_consumer_delivery_failure(
                            cur, report_id,
                            "RESEND_API_KEY is not configured on the worker, so no "
                            "email was attempted",
                        )
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
                            # NOT IN THE ORIGINAL SURVEY, and the most direct
                            # instance of the shape in this file: the code logs
                            # "delivery failed" and the very next statement
                            # records success. Resend rejected the message, or
                            # the call raised — and the row said sent, with a
                            # timestamp, and the agent got their lead
                            # notification. Found while fixing D-031 two
                            # branches up; §0.6 rule 4, re-run the survey after
                            # the fix.
                            _record_consumer_delivery_failure(
                                cur, report_id,
                                f"the email provider did not accept the message "
                                f"(status {getattr(resp, 'status_code', 'no response')})",
                            )

                else:
                    # D-032. Same claim, third trigger: no phone for SMS, no
                    # address for email, or a delivery_method this dispatch
                    # does not recognise. Nothing was sent and nothing could
                    # have been. The reason names the method, because "failed"
                    # without it sends whoever investigates back to the logs.
                    _record_consumer_delivery_failure(
                        cur, report_id,
                        f"no usable delivery method: delivery_method={delivery_method!r}, "
                        f"phone={'present' if consumer_phone else 'missing'}, "
                        f"email={'present' if consumer_email else 'missing'}",
                    )

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
                    # The branches above have already written status='failed'
                    # with the SPECIFIC reason. This used to overwrite all of
                    # them with the string 'Delivery failed', which is the one
                    # fact everybody already had — so the reason survives now
                    # and only a branch that somehow reached here without
                    # recording anything gets the generic text.
                    cur.execute("""
                        UPDATE consumer_reports
                        SET status = 'failed',
                            error = COALESCE(NULLIF(error, ''), %s)
                        WHERE id = %s::uuid
                    """, ('Delivery failed', report_id))

                    logger.error(f"Failed to deliver report {report_id}")

                    if self.request.retries < self.max_retries:
                        raise self.retry(countdown=60 * (self.request.retries + 1))

                    # `sms_result` is bound only inside the SMS branch. On the
                    # email and no-method paths this raised NameError, which
                    # the outer handler caught and rewrote as a generic failure
                    # — hiding the real reason behind a second, unrelated bug.
                    # Read the reason back from the row instead, which is now
                    # where it lives.
                    cur.execute(
                        "SELECT error FROM consumer_reports WHERE id = %s::uuid",
                        (report_id,),
                    )
                    row = cur.fetchone()
                    return {"ok": False, "error": (row[0] if row else None) or "Delivery failed"}
                    
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

