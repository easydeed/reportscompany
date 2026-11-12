"""SendGrid email provider for sending schedule notifications."""
import os
import time
import logging
import httpx
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
DEFAULT_FROM_NAME = os.getenv("DEFAULT_FROM_NAME", "Market Reports")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "reports@example.com")

# Per-request timeout, seconds. A module constant so the transport-boundary
# tests can shorten it; production keeps 30.
SENDGRID_TIMEOUT = float(os.getenv("SENDGRID_TIMEOUT", "30"))

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2.0  # Base delay in seconds (exponential backoff)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


# ── LR-023: one HTTP attempt, and an outcome that says what is known ─────────
#
# The retry loop below re-POSTs after a timeout, a request error, a 429 or a 5xx.
# A POST that SendGrid accepted, but whose response was lost, is then POSTed
# again by this function itself, and SendGrid takes no idempotency key, so the
# recipient gets the email twice. A durable claim outside this function cannot
# stop that. Scheduled sends that are recovery-tracked therefore call it with
# `single_attempt=True`: exactly one POST, and a typed outcome.
#
# The outcome is typed because the status codes here are not all SendGrid's: a
# timeout is reported as a made-up 504, a request error and a missing key as
# 500. A code cannot separate "definitely not sent" from "may have been sent".
ACCEPTED = "accepted"   # 202
REJECTED = "rejected"   # SendGrid answered 4xx (429 included): it did not accept
NOT_SENT = "not_sent"   # no request left this process: no connection, or refused before the POST
UNKNOWN = "unknown"     # the request may have reached SendGrid; the answer is missing or ambiguous


@dataclass(frozen=True)
class Attempt:
    outcome: str
    status_code: Optional[int]
    detail: str


def _one_attempt(payload: dict, http_headers: dict) -> Attempt:
    """Exactly one POST. Never sleeps, never retries."""
    try:
        with httpx.Client(timeout=SENDGRID_TIMEOUT) as client:
            response = client.post(SENDGRID_API_URL, json=payload, headers=http_headers)
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        # The connection was never made, so the request was never sent.
        return Attempt(NOT_SENT, None, f"no connection: {type(e).__name__}: {e}"[:500])
    except Exception as e:   # noqa: BLE001 - every other failure may follow the send
        # A read or write timeout, a dropped connection, a protocol error, or
        # anything unexpected: the request may have been delivered.
        return Attempt(UNKNOWN, None, f"{type(e).__name__}: {e}"[:500])
    code = response.status_code
    if code == 202:
        return Attempt(ACCEPTED, code, "accepted")
    if 400 <= code < 500:
        return Attempt(REJECTED, code, (response.text or "")[:500])
    return Attempt(UNKNOWN, code, (response.text or "")[:500])


def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    from_name: str = None,
    from_email: str = None,
    headers: Optional[Dict[str, str]] = None,
    single_attempt: bool = False,
) -> Union[Tuple[int, str], Attempt]:
    """
    Send an email using SendGrid v3 API.
    
    Includes retry logic for transient failures (rate limits, server errors).
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject line
        html_content: HTML email body
        from_name: Sender name (defaults to DEFAULT_FROM_NAME)
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        headers: Optional MESSAGE headers (not HTTP headers) to attach to this
            personalization — e.g. List-Unsubscribe. Set per personalization
            rather than at the top level so each recipient can carry their own
            token; callers that send one message per recipient depend on that.

        single_attempt: LR-023. Exactly one POST, no retries, and an `Attempt`
            is returned instead of the tuple. Legacy callers leave it False and
            keep the retries and the tuple.

    Returns:
        Tuple of (status_code, response_text), or an `Attempt` when single_attempt.
    """
    if not SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY not set, cannot send email")
        if single_attempt:
            return Attempt(NOT_SENT, None, "SENDGRID_API_KEY not configured")
        return (500, "SENDGRID_API_KEY not configured")
    
    if not to_emails:
        logger.error("No recipients provided")
        if single_attempt:
            return Attempt(NOT_SENT, None, "No recipients provided")
        return (400, "No recipients provided")
    
    # Use defaults if not provided
    from_name = from_name or DEFAULT_FROM_NAME
    from_email = from_email or DEFAULT_FROM_EMAIL
    
    # Build SendGrid payload
    personalization = {
        "to": [{"email": email} for email in to_emails],
        "subject": subject,
    }
    if headers:
        personalization["headers"] = headers

    payload = {
        "personalizations": [personalization],
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
    
    # Named http_headers, not headers: the `headers` PARAMETER carries message
    # headers into the personalization above. Reusing the name here shadowed it,
    # and was correct only because the payload happens to be built first.
    http_headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    
    if single_attempt:
        result = _one_attempt(payload, http_headers)
        log = logger.info if result.outcome == ACCEPTED else logger.error
        log("SendGrid single attempt to %d recipient(s): %s %s",
            len(to_emails), result.outcome, result.status_code)
        return result

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
            
            with httpx.Client(timeout=SENDGRID_TIMEOUT) as client:
                response = client.post(SENDGRID_API_URL, json=payload, headers=http_headers)
                
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

