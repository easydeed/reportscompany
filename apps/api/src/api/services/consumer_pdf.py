"""A homeowner's PDF: a fresh link for one that exists, one job for one that is missing (LR-022).

Jerry, 2026-11-11:
  * Re-sign on click. The worker stores a 7-day presigned R2 URL as `pdf_url`,
    so every stored link stops working a week after the report is made. The
    download now gets a freshly signed, short-lived link to the SAME object,
    read from `pdf_object_key` or, for reports made before that column, from
    the stored URL's path. Same access rule (unguessable, expiring), no
    regeneration.
  * Render a missing PDF only, from the stored data, into a new object; never
    replace one. The worker's `generate_consumer_report_pdf` does the render;
    this module only queues it, once.
  * 20 generation requests per hour per visitor (the public-lookup limit).
"""
from __future__ import annotations

import ipaddress
import logging
import os
from typing import Optional
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")

#: How long a freshly signed download link works. The page asks for a new one
#: on every click, so this only has to outlast opening it.
SIGNED_LINK_SECONDS = 3600
#: Same window as the worker's claims (DUPLICATE_SEND_WINDOW_MINUTES): longer
#: than the worker's task_time_limit, so a live render is never taken as stale.
PDF_CLAIM_WINDOW_MINUTES = int(os.getenv("DUPLICATE_SEND_WINDOW_MINUTES", "10"))
#: Jerry, 2026-11-11: the public-lookup limit.
GENERATE_REQUESTS_PER_HOUR = 20
GENERATE_EVENT = "pdf_generate_request"

_DELIVERED = ("(consumer_sms_sent_at IS NOT NULL OR consumer_email_sent_at IS NOT NULL "
              "OR status = 'sent')")


def object_key_from_url(url: Optional[str], bucket: str = R2_BUCKET_NAME) -> Optional[str]:
    """The object key inside a stored R2 presigned URL, or None if it is not one.

    boto3 with a custom endpoint signs path-style URLs
    (`https://<account>.r2.cloudflarestorage.com/<bucket>/<key>?X-Amz-...`);
    virtual-host style (`https://<bucket>.<account>.r2...`) is handled too.
    """
    if not url:
        return None
    parsed = urlparse(url)
    if "X-Amz-Signature" not in (parsed.query or "") or not parsed.netloc.endswith("r2.cloudflarestorage.com"):
        return None
    path = unquote(parsed.path).lstrip("/")
    if parsed.netloc.startswith(f"{bucket}."):
        return path or None
    prefix = f"{bucket}/"
    if not path.startswith(prefix):
        return None
    return path[len(prefix):] or None


def _client():
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def download_link(pdf_object_key: Optional[str], pdf_url: Optional[str]) -> Optional[str]:
    """A working link to the report's existing PDF.

    A freshly signed link when the object is known and R2 is configured; the
    stored URL otherwise (a permanent CDN URL, or a local-dev stub). Never
    renders anything.
    """
    key = pdf_object_key or object_key_from_url(pdf_url)
    if key and all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        try:
            return _client().generate_presigned_url(
                "get_object", Params={"Bucket": R2_BUCKET_NAME, "Key": key},
                ExpiresIn=SIGNED_LINK_SECONDS)
        except Exception:
            logger.exception("could not sign a download link for %s", key)
    return pdf_url


def visitor_ip(ip: Optional[str]) -> Optional[str]:
    """The visitor's address if it is one; None otherwise (it is stored as INET)."""
    try:
        return str(ipaddress.ip_address((ip or "").strip()))
    except ValueError:
        return None


def generate_requests_last_hour(cur, ip: Optional[str]) -> int:
    """How many PDF generation requests this visitor made in the last hour."""
    ip = visitor_ip(ip)
    if not ip:
        return 0
    cur.execute("""
        SELECT COUNT(*) FROM report_analytics
        WHERE event_type = %s AND ip_address = %s::inet AND created_at > NOW() - INTERVAL '1 hour'
    """, (GENERATE_EVENT, ip))
    return cur.fetchone()[0]


def record_generate_request(cur, report_id, ip: Optional[str], user_agent: Optional[str]):
    cur.execute("""
        INSERT INTO report_analytics (report_id, event_type, event_data, ip_address, user_agent)
        VALUES (%s, %s, '{}'::jsonb, %s::inet, %s)
    """, (str(report_id), GENERATE_EVENT, visitor_ip(ip), (user_agent or "")[:500]))


def queue_missing_pdf(cur, report_id) -> bool:
    """Mark a delivered report's missing PDF as queued, if nobody has. True means: queue one job.

    Concurrent clicks race on this one conditional UPDATE, so exactly one of
    them queues the job. A stale claim (a queue or render older than the
    window) or a failed one may be queued again.
    """
    cur.execute(f"""
        UPDATE consumer_reports
        SET pdf_status = 'queued', pdf_claimed_at = NOW(), pdf_error = NULL
        WHERE id = %s
          AND pdf_url IS NULL AND pdf_object_key IS NULL
          AND {_DELIVERED}
          AND (pdf_status IS NULL OR pdf_status = 'failed'
               OR (pdf_status IN ('queued', 'generating')
                   AND pdf_claimed_at < NOW() - make_interval(mins => %s)))
        RETURNING id
    """, (str(report_id), PDF_CLAIM_WINDOW_MINUTES))
    return cur.fetchone() is not None


def mark_queue_failed(cur, report_id, reason: str):
    cur.execute("""
        UPDATE consumer_reports SET pdf_status = 'failed', pdf_error = %s
        WHERE id = %s AND pdf_status = 'queued'
    """, (reason[:500], str(report_id)))


def pdf_state(row: dict) -> str:
    """ready | generating | failed | missing | unavailable, from a consumer_reports row."""
    if row.get("pdf_url") or row.get("pdf_object_key"):
        return "ready"
    delivered = bool(row.get("consumer_sms_sent_at") or row.get("consumer_email_sent_at")
                     or row.get("status") == "sent")
    if not delivered:
        return "unavailable"
    status = row.get("pdf_status")
    if status in ("queued", "generating"):
        return "failed" if row.get("pdf_claim_stale") else "generating"
    if status == "failed":
        return "failed"
    return "missing"
