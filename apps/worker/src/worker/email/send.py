"""Orchestrator for sending schedule notification emails."""
import os
import logging
import hashlib
import hmac
from typing import List, Tuple, Dict, Optional
from urllib.parse import quote

from .providers.sendgrid import send_email
from .template import schedule_email_html, schedule_email_subject

logger = logging.getLogger(__name__)

WEB_BASE = os.getenv("WEB_BASE", "http://localhost:3000")

# CRITICAL: This MUST be set in production environment variables!
#
# This module SIGNS the unsubscribe token; apps/api/src/api/routes/unsubscribe.py
# VERIFIES it. The two must hold the same value or every link returns 400.
#
# DO NOT "fix" the dev fallback by making it equal to the API's fallback. The
# two defaults differ deliberately. If they matched, an environment that forgot
# to set EMAIL_UNSUB_SECRET would appear to work while signing with a secret
# published in this repository — anyone could then forge a token and suppress
# delivery for any address on any account. Mismatched defaults fail closed;
# matched defaults fail open.
EMAIL_UNSUB_SECRET = os.getenv("EMAIL_UNSUB_SECRET")
if not EMAIL_UNSUB_SECRET:
    logger.critical(
        "EMAIL_UNSUB_SECRET not set (ENVIRONMENT=%s) — falling back to a dev "
        "default. It will NOT match the API's verifying secret, so every "
        "unsubscribe link in every email sent by this process will return 400 "
        "and no recipient will be able to opt out. Set EMAIL_UNSUB_SECRET on "
        "this service to the same value as the API service, then restart.",
        os.getenv("ENVIRONMENT", "unset"),
    )
    EMAIL_UNSUB_SECRET = "dev-only-secret-do-not-use-in-production"

# Sentinel substituted per recipient after the body is rendered once. The body
# is rendered a single time on purpose: schedule_email_html() reaches OpenAI for
# the insight paragraph (template.py:1494-1506), so rendering per recipient
# would cost one AI call each AND give recipients of the same report different
# copy. Render once, swap only the link.
_UNSUB_URL_SENTINEL = "__TRENDYREPORTS_UNSUBSCRIBE_URL__"


def generate_unsubscribe_token(account_id: str, email: str) -> str:
    """
    Generate HMAC-SHA256 token for unsubscribe link.
    Must match the token generation in the API unsubscribe endpoint
    (apps/api/src/api/routes/unsubscribe.py:24-34).
    """
    message = f"{account_id}:{email}".encode()
    signature = hmac.new(
        EMAIL_UNSUB_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature


def build_unsubscribe_url(account_id: str, email: str) -> str:
    """
    Build the unsubscribe URL for ONE recipient.

    The token is bound to that recipient's own address, so the link only ever
    unsubscribes the person who received it. `email` is percent-encoded: an
    unencoded '+' in a plus-addressed recipient decodes as a space on the API
    side and the token then fails to verify.
    """
    token = generate_unsubscribe_token(account_id, email)
    return f"{WEB_BASE}/api/v1/email/unsubscribe?token={token}&email={quote(email, safe='')}"


def send_schedule_email(
    account_id: str,
    recipients: List[str],
    payload: Dict,
    account_name: Optional[str] = None,
    db_conn=None,
    brand: Optional[Dict] = None,
    account_type: str = "REGULAR",
) -> Tuple[int, str]:
    """
    Send a scheduled report notification email to recipients.
    
    Phase 30: Now supports white-label branding for affiliate accounts.
    V14: Sender-aware AI insights based on account_type.
    Filters out suppressed recipients before sending.
    
    Args:
        account_id: Account UUID
        recipients: List of recipient email addresses
        payload: Report data including:
            - report_type: Type of report
            - city: City name (optional)
            - zip_codes: List of ZIP codes (optional)
            - lookback_days: Number of days covered
            - metrics: Dictionary of key metrics
            - pdf_url: Direct link to the PDF
            - total_listings: Total found in market (V14)
            - total_shown: How many displayed (V14)
            - audience_key: Preset audience type (V14)
        account_name: Account name for personalization (optional)
        db_conn: Database connection for suppression checking (optional)
        brand: Optional brand configuration for white-label output (Phase 30)
        account_type: "REGULAR" (agent) or "INDUSTRY_AFFILIATE" (title company) (V14)
    
    Returns:
        Tuple of (status_code, response_text)
    """
    if not recipients:
        logger.warning("No recipients provided for schedule email")
        return (400, "No recipients")
    
    # Check suppression list if db_conn provided
    filtered_recipients = recipients[:]
    
    if db_conn is not None:
        try:
            with db_conn.cursor() as cur:
                # Query suppressed emails for this account
                cur.execute("""
                    SELECT email
                    FROM email_suppressions
                    WHERE account_id = %s
                      AND email = ANY(%s)
                """, (account_id, recipients))
                
                suppressed = [row[0] for row in cur.fetchall()]
                
                if suppressed:
                    logger.info(f"Suppressed recipients: {suppressed}")
                    filtered_recipients = [r for r in recipients if r not in suppressed]
                
                if not filtered_recipients:
                    logger.info(f"All {len(recipients)} recipient(s) suppressed, skipping email send")
                    return (200, "All recipients suppressed")
                    
        except Exception as e:
            logger.warning(f"Error checking suppressions: {e}, proceeding with all recipients")
            # On error, don't block email - proceed with original list
            filtered_recipients = recipients
    
    # Extract data from payload
    report_type = payload.get("report_type", "market_snapshot")
    city = payload.get("city")
    zip_codes = payload.get("zip_codes") or payload.get("zips")
    lookback_days = payload.get("lookback_days", 30)
    metrics = payload.get("metrics", {})
    pdf_url = payload.get("pdf_url", "")
    listings = payload.get("listings")  # V5: Photo gallery for gallery reports
    preset_display_name = payload.get("preset_display_name")  # V6: Custom preset name (e.g., "First-Time Buyer")
    filter_description = payload.get("filter_description")  # V11: Human-readable filter summary
    
    # V14: Sender-aware AI insights
    total_found = payload.get("total_listings", 0)  # Total in market
    total_shown = payload.get("total_shown", len(listings) if listings else 0)  # How many displayed
    audience_key = payload.get("audience_key", "all")  # Preset audience type

    # EMAIL-DEPTH-PASS1: explicit truncation accounting from
    # _build_email_payload — drives the "Showing X of Y · View all in
    # the PDF" note. Falls back to the V14 fields if an older caller
    # hasn't populated them.
    total_available = payload.get("total_available", total_found)
    showing = payload.get("showing", total_shown)
    
    if not pdf_url:
        logger.error("No PDF URL provided in payload")
        return (400, "No PDF URL")
    
    # Generate email subject
    subject = schedule_email_subject(report_type, city, zip_codes)

    # Render the body ONCE with a sentinel in place of the unsubscribe URL; the
    # real per-recipient URL is substituted in the send loop below. See
    # _UNSUB_URL_SENTINEL for why this is not rendered per recipient.
    html_content = schedule_email_html(
        account_name=account_name or "there",
        report_type=report_type,
        city=city,
        zip_codes=zip_codes,
        lookback_days=lookback_days,
        metrics=metrics,
        pdf_url=pdf_url,
        unsubscribe_url=_UNSUB_URL_SENTINEL,
        brand=brand,
        listings=listings,  # V5: Photo gallery for gallery reports
        preset_display_name=preset_display_name,  # V6: Custom preset name
        filter_description=filter_description,  # V11: Human-readable filter summary
        sender_type=account_type,  # V14: Agent vs Affiliate
        total_found=total_found,  # V14: Total listings in market
        total_shown=total_shown,  # V14: How many displayed
        audience_name=preset_display_name,  # V14: Audience for AI context
        total_available=total_available,  # EMAIL-DEPTH-PASS1: truncation note
        showing=showing,                  # EMAIL-DEPTH-PASS1: truncation note
    )
    
    # Fail loudly rather than mailing a dead link to everyone. If the sentinel
    # is missing, schedule_email_html() stopped honouring unsubscribe_url and
    # every recipient would get an email with no working unsubscribe.
    if _UNSUB_URL_SENTINEL not in html_content:
        logger.critical(
            "Unsubscribe sentinel missing from rendered email body — refusing to "
            "send. schedule_email_html() no longer emits the unsubscribe_url it "
            "was given (expected at template.py:2338)."
        )
        return (500, "Unsubscribe URL missing from rendered email body")

    # Send ONE email per recipient, each carrying a token bound to that
    # recipient's own address. Previously a single message went to the whole
    # list carrying recipients[0]'s token, so every other recipient's
    # "Unsubscribe" suppressed recipient #1 and left the clicker subscribed.
    # One message per recipient also stops the To: header disclosing the whole
    # recipient list to every recipient.
    logger.info(
        f"Sending schedule email to {len(filtered_recipients)} recipient(s) "
        f"individually: {filtered_recipients}"
    )

    failures: List[Tuple[str, int, str]] = []
    for recipient in filtered_recipients:
        personalised_html = html_content.replace(
            _UNSUB_URL_SENTINEL, build_unsubscribe_url(account_id, recipient)
        )
        status_code, response_text = send_email(
            to_emails=[recipient],
            subject=subject,
            html_content=personalised_html,
        )
        if status_code != 202:
            logger.error(
                f"Schedule email to {recipient} failed: {status_code} {response_text}"
            )
            failures.append((recipient, status_code, response_text))

    if not failures:
        return (202, "Email sent successfully")

    # Partial success has no representation in email_log's status set
    # ('sent' / 'suppressed' / 'failed' — see tasks.py:626-631), so a run with
    # any failure is reported as a failure and the counts go in the response
    # text. Reporting 202 here would record a send that did not happen for
    # some recipients, which is the failure mode this branch exists to remove.
    first_email, first_status, first_text = failures[0]
    summary = (
        f"{len(failures)} of {len(filtered_recipients)} recipient(s) failed; "
        f"first: {first_email} -> {first_status} {first_text}"
    )
    logger.error(f"Schedule email partially or fully failed: {summary}")
    return (first_status, summary)

