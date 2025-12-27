"""SendGrid email provider for sending schedule notifications."""
import os
import time
import logging
import httpx
from typing import List, Tuple

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DEFAULT_FROM_NAME = os.getenv("DEFAULT_FROM_NAME", "Market Reports")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "reports@example.com")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2.0  # Base delay in seconds (exponential backoff)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_name: str = None,
    from_email: str = None,
) -> Tuple[int, str]:
    """
    Send an email using SendGrid v3 API.
    
    Includes retry logic for transient failures (rate limits, server errors).
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject line
        html_content: HTML email body
        from_name: Sender name (defaults to DEFAULT_FROM_NAME)
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
    
    Returns:
        Tuple of (status_code, response_text)
    """
    if not SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY not set, cannot send email")
        return (500, "SENDGRID_API_KEY not configured")
    
    if not to_emails:
        logger.error("No recipients provided")
        return (400, "No recipients provided")
    
    # Use defaults if not provided
    from_name = from_name or DEFAULT_FROM_NAME
    from_email = from_email or DEFAULT_FROM_EMAIL
    
    # Build SendGrid payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": email} for email in to_emails],
                "subject": subject,
            }
        ],
        "from": {
            "email": from_email,
            "name": from_name,
        },
        "content": [
            {
                "type": "text/html",
                "value": html_content,
            }
        ],
    }
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    
    last_error = None
    last_status_code = 500
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt == 0:
                logger.info(f"Sending email to {len(to_emails)} recipient(s): {to_emails}")
            else:
                delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"Retry attempt {attempt}/{MAX_RETRIES} after {delay:.1f}s delay")
                time.sleep(delay)
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(SENDGRID_API_URL, json=payload, headers=headers)
                
                if response.status_code == 202:
                    logger.info(f"Email sent successfully to {to_emails}")
                    return (202, "Email sent successfully")
                
                last_status_code = response.status_code
                last_error = response.text
                
                # Only retry on transient errors
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    logger.error(f"SendGrid error {response.status_code}: {last_error}")
                    return (response.status_code, last_error)
                
                logger.warning(f"SendGrid returned {response.status_code}, will retry...")
                    
        except httpx.TimeoutException as e:
            last_status_code = 504
            last_error = f"Timeout: {str(e)}"
            logger.warning(f"SendGrid timeout on attempt {attempt + 1}: {e}")
        except httpx.RequestError as e:
            last_status_code = 500
            last_error = f"Request error: {str(e)}"
            logger.warning(f"SendGrid request error on attempt {attempt + 1}: {e}")
        except Exception as e:
            last_status_code = 500
            last_error = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error sending email: {e}")
            # Don't retry on unexpected errors
            return (500, last_error)
    
    # All retries exhausted
    logger.error(f"SendGrid failed after {MAX_RETRIES} retries: {last_error}")
    return (last_status_code, last_error)

