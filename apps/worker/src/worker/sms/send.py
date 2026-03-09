"""
SMS sending via Twilio
"""
import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

# Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")


def get_twilio_client() -> Client | None:
    """Get Twilio client if credentials are configured."""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logger.warning("Twilio credentials not configured")
        return None
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms(
    to_phone: str,
    message: str,
) -> dict:
    """
    Send SMS via Twilio.
    
    Args:
        to_phone: Recipient phone number (10 digits, US format)
        message: SMS message body (max 1600 chars for concatenated SMS)
    
    Returns:
        dict with 'success', 'message_sid', and optionally 'error'
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio not configured"}
    
    # Format phone to E.164
    digits = ''.join(filter(str.isdigit, to_phone))
    if len(digits) == 10:
        to_number = f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        to_number = f"+{digits}"
    else:
        return {"success": False, "error": f"Invalid phone number: {to_phone}"}
    
    try:
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        
        logger.info(f"SMS sent successfully: {sms.sid} to {to_number}")
        return {
            "success": True,
            "message_sid": sms.sid,
            "status": sms.status
        }
        
    except TwilioRestException as e:
        logger.error(f"Twilio error sending to {to_number}: {e.msg}")
        return {
            "success": False,
            "error": str(e.msg),
            "error_code": e.code
        }
    except Exception as e:
        logger.error(f"Unexpected error sending SMS to {to_number}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def send_report_sms(
    to_phone: str,
    report_url: str,
    agent_name: str,
    property_address: str,
) -> dict:
    """
    Send the home value report SMS to consumer.
    
    Args:
        to_phone: Consumer's phone number
        report_url: URL to the mobile report viewer
        agent_name: Agent's name
        property_address: Property address for context
    """
    message = f"""Your Home Value Report is ready! 🏠

Property: {property_address}

View your personalized report:
{report_url}

Questions? Reply to this text or contact {agent_name} directly.

- TrendyReports"""
    
    result = send_sms(to_phone, message)
    result['message_body'] = message  # Include message for logging
    return result


def send_agent_notification_sms(
    to_phone: str,
    property_address: str,
    report_url: str,
    lead_name: str | None = None,
    consumer_phone: str | None = None,
    consumer_email: str | None = None,
) -> dict:
    """
    Send notification to agent about new CMA lead.
    """
    contact_lines = []
    if consumer_phone:
        digits = ''.join(filter(str.isdigit, consumer_phone))
        if len(digits) == 10:
            display_phone = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        else:
            display_phone = consumer_phone
        contact_lines.append(f"📱 {display_phone}")
    if consumer_email:
        contact_lines.append(f"📧 {consumer_email}")
    contact_block = "\n".join(contact_lines) if contact_lines else "No contact info"

    who = lead_name or "Someone"

    message = f"""🏠 New CMA Lead!

{who} is interested in:
{property_address}

{contact_block}

Respond quickly — they're actively evaluating!
- TrendyReports"""

    return send_sms(to_phone, message)

