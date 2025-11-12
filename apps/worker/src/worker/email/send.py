"""Orchestrator for sending schedule notification emails."""
import os
import logging
import hashlib
import hmac
from typing import List, Tuple, Dict, Optional

from .providers.sendgrid import send_email
from .template import schedule_email_html, schedule_email_subject

logger = logging.getLogger(__name__)

WEB_BASE = os.getenv("WEB_BASE", "http://localhost:3000")
EMAIL_UNSUB_SECRET = os.getenv("EMAIL_UNSUB_SECRET", "change-me-in-production")


def generate_unsubscribe_token(account_id: str, email: str) -> str:
    """
    Generate HMAC-SHA256 token for unsubscribe link.
    Must match the token generation in the API unsubscribe endpoint.
    """
    message = f"{account_id}:{email}".encode()
    signature = hmac.new(
        EMAIL_UNSUB_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature


def send_schedule_email(
    account_id: str,
    recipients: List[str],
    payload: Dict,
    account_name: Optional[str] = None,
) -> Tuple[int, str]:
    """
    Send a scheduled report notification email to recipients.
    
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
        account_name: Account name for personalization (optional)
    
    Returns:
        Tuple of (status_code, response_text)
    """
    if not recipients:
        logger.warning("No recipients provided for schedule email")
        return (400, "No recipients")
    
    # Extract data from payload
    report_type = payload.get("report_type", "market_snapshot")
    city = payload.get("city")
    zip_codes = payload.get("zip_codes") or payload.get("zips")
    lookback_days = payload.get("lookback_days", 30)
    metrics = payload.get("metrics", {})
    pdf_url = payload.get("pdf_url", "")
    
    if not pdf_url:
        logger.error("No PDF URL provided in payload")
        return (400, "No PDF URL")
    
    # Generate unsubscribe URLs (one per recipient)
    # For v1, we'll use the first recipient's token for all
    # (In production, you'd send individual emails with unique tokens)
    first_recipient = recipients[0]
    unsub_token = generate_unsubscribe_token(account_id, first_recipient)
    unsubscribe_url = f"{WEB_BASE}/api/v1/email/unsubscribe?token={unsub_token}&email={first_recipient}"
    
    # Generate email subject
    subject = schedule_email_subject(report_type, city, zip_codes)
    
    # Generate HTML content
    html_content = schedule_email_html(
        account_name=account_name or "there",
        report_type=report_type,
        city=city,
        zip_codes=zip_codes,
        lookback_days=lookback_days,
        metrics=metrics,
        pdf_url=pdf_url,
        unsubscribe_url=unsubscribe_url,
    )
    
    # Send email via provider
    logger.info(f"Sending schedule email to {len(recipients)} recipient(s)")
    status_code, response_text = send_email(
        to_emails=recipients,
        subject=subject,
        html_content=html_content,
    )
    
    return (status_code, response_text)

