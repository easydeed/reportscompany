"""SendGrid email provider for sending schedule notifications."""
import os
import logging
import httpx
from typing import List, Tuple

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DEFAULT_FROM_NAME = os.getenv("DEFAULT_FROM_NAME", "Market Reports")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "reports@example.com")


def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_name: str = None,
    from_email: str = None,
) -> Tuple[int, str]:
    """
    Send an email using SendGrid v3 API.
    
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
    
    try:
        logger.info(f"Sending email to {len(to_emails)} recipient(s): {to_emails}")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(SENDGRID_API_URL, json=payload, headers=headers)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_emails}")
                return (202, "Email sent successfully")
            else:
                error_text = response.text
                logger.error(f"SendGrid error {response.status_code}: {error_text}")
                return (response.status_code, error_text)
                
    except httpx.TimeoutException as e:
        logger.error(f"SendGrid timeout: {e}")
        return (504, f"Timeout: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"SendGrid request error: {e}")
        return (500, f"Request error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return (500, f"Unexpected error: {str(e)}")

