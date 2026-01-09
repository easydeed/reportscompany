"""
Twilio SMS Service

Send SMS notifications for lead capture events.

Environment variables:
- TWILIO_ACCOUNT_SID: Twilio account SID
- TWILIO_AUTH_TOKEN: Twilio auth token
- TWILIO_PHONE_NUMBER: Twilio phone number to send from (E.164 format)
"""

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# Twilio API base URL
TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


class TwilioSMSError(Exception):
    """Exception raised for Twilio SMS failures."""
    pass


def is_configured() -> bool:
    """Check if Twilio is properly configured."""
    return all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER])


async def send_sms(to_phone: str, message: str) -> dict:
    """
    Send an SMS message via Twilio.
    
    Args:
        to_phone: Recipient phone number (E.164 format, e.g., +15551234567)
        message: Message body (max 1600 characters)
    
    Returns:
        dict with message_sid, status, and to fields
    
    Raises:
        TwilioSMSError: If SMS sending fails
    """
    if not is_configured():
        logger.error("Twilio not configured - missing credentials")
        raise TwilioSMSError("Twilio SMS not configured")
    
    # Validate phone number format
    if not to_phone or not to_phone.startswith("+"):
        raise TwilioSMSError(f"Invalid phone number format: {to_phone}. Must be E.164 format (+1xxxxx)")
    
    # Truncate message if too long
    if len(message) > 1600:
        message = message[:1597] + "..."
        logger.warning("SMS message truncated to 1600 characters")
    
    url = f"{TWILIO_API_BASE}/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    
    data = {
        "To": to_phone,
        "From": TWILIO_PHONE_NUMBER,
        "Body": message,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                data=data,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"SMS sent successfully to {to_phone[:6]}***. SID: {result.get('sid')}")
                return {
                    "message_sid": result.get("sid"),
                    "status": result.get("status"),
                    "to": result.get("to"),
                }
            
            # Handle errors
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("message", f"HTTP {response.status_code}")
            error_code = error_data.get("code", "unknown")
            
            logger.error(f"Twilio SMS failed: {error_code} - {error_msg}")
            raise TwilioSMSError(f"Twilio error {error_code}: {error_msg}")
            
        except httpx.TimeoutException:
            logger.error("Twilio API timeout")
            raise TwilioSMSError("Twilio API timeout")
        except httpx.HTTPError as e:
            logger.error(f"Twilio HTTP error: {e}")
            raise TwilioSMSError(f"Twilio HTTP error: {e}")


async def send_lead_notification_sms(
    to_phone: str,
    lead_name: str,
    property_address: str,
    lead_phone: Optional[str] = None,
    lead_email: Optional[str] = None,
) -> dict:
    """
    Send a lead notification SMS to an agent.
    
    Args:
        to_phone: Agent's phone number (E.164 format)
        lead_name: Name of the lead who submitted
        property_address: Address of the property report
        lead_phone: Lead's phone number (optional)
        lead_email: Lead's email (optional)
    
    Returns:
        dict with message_sid, status, and to fields
    
    Raises:
        TwilioSMSError: If SMS sending fails
    """
    # Build message
    message_parts = [
        f"🏠 New Lead Alert!",
        f"",
        f"{lead_name} is interested in:",
        f"{property_address}",
    ]
    
    if lead_phone:
        message_parts.append(f"📱 {lead_phone}")
    
    if lead_email:
        message_parts.append(f"📧 {lead_email}")
    
    message_parts.extend([
        "",
        "Respond quickly for best results!",
        "",
        "- TrendyReports",
    ])
    
    message = "\n".join(message_parts)
    
    return await send_sms(to_phone, message)


def format_phone_e164(phone: str, default_country: str = "1") -> Optional[str]:
    """
    Format a phone number to E.164 format.
    
    Args:
        phone: Phone number in any format
        default_country: Default country code (default: "1" for US)
    
    Returns:
        Phone number in E.164 format (+1xxxxx) or None if invalid
    """
    if not phone:
        return None
    
    # Remove all non-digit characters except leading +
    has_plus = phone.startswith("+")
    digits = "".join(c for c in phone if c.isdigit())
    
    if not digits:
        return None
    
    # If already has + prefix, validate and return
    if has_plus:
        return f"+{digits}"
    
    # US number handling
    if len(digits) == 10:
        # 10-digit US number
        return f"+{default_country}{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        # 11-digit with leading 1
        return f"+{digits}"
    elif len(digits) > 10:
        # Assume it's already a full international number
        return f"+{digits}"
    
    # Too short
    return None

