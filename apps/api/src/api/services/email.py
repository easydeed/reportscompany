"""
Email Service using Resend

Provides email sending functionality for:
- Welcome emails
- Password reset
- Report delivery
- Scheduled report notifications
"""

import logging
from typing import Optional, Dict, Any, List
import httpx
from ..settings import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailService:
    """Email service using Resend API."""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_address = settings.EMAIL_FROM_ADDRESS
        self.reply_to = settings.EMAIL_REPLY_TO
        self.app_base = settings.APP_BASE

    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.api_key)

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email using Resend.

        Args:
            to: Recipient email(s)
            subject: Email subject
            html: HTML content
            text: Plain text content (optional)
            reply_to: Reply-to address (optional, uses default if not provided)
            tags: Optional tags for tracking

        Returns:
            Response from Resend API
        """
        if not self.is_configured:
            logger.warning("Email service not configured. Skipping email send.")
            return {"ok": False, "error": "Email service not configured"}

        # Normalize to list
        recipients = [to] if isinstance(to, str) else to

        payload = {
            "from": self.from_address,
            "to": recipients,
            "subject": subject,
            "html": html,
        }

        if text:
            payload["text"] = text

        if reply_to or self.reply_to:
            payload["reply_to"] = reply_to or self.reply_to

        if tags:
            payload["tags"] = tags

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    RESEND_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Email sent successfully: {data.get('id')}")
                    return {"ok": True, "id": data.get("id")}
                else:
                    error = response.text
                    logger.error(f"Failed to send email: {response.status_code} - {error}")
                    return {"ok": False, "error": error, "status": response.status_code}

        except Exception as e:
            logger.error(f"Exception sending email: {e}")
            return {"ok": False, "error": str(e)}

    def send_email_sync(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous version of send_email.
        """
        if not self.is_configured:
            logger.warning("Email service not configured. Skipping email send.")
            return {"ok": False, "error": "Email service not configured"}

        recipients = [to] if isinstance(to, str) else to

        payload = {
            "from": self.from_address,
            "to": recipients,
            "subject": subject,
            "html": html,
        }

        if text:
            payload["text"] = text

        if reply_to or self.reply_to:
            payload["reply_to"] = reply_to or self.reply_to

        if tags:
            payload["tags"] = tags

        try:
            with httpx.Client() as client:
                response = client.post(
                    RESEND_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Email sent successfully: {data.get('id')}")
                    return {"ok": True, "id": data.get("id")}
                else:
                    error = response.text
                    logger.error(f"Failed to send email: {response.status_code} - {error}")
                    return {"ok": False, "error": error, "status": response.status_code}

        except Exception as e:
            logger.error(f"Exception sending email: {e}")
            return {"ok": False, "error": str(e)}


# Singleton instance
email_service = EmailService()


# ============ Email Templates ============

def get_welcome_email_html(user_name: str, login_url: str) -> str:
    """Generate welcome email HTML."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Market Reports</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #7C3AED; margin: 0;">Market Reports</h1>
    </div>

    <div style="background: linear-gradient(135deg, #7C3AED 0%, #a855f7 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;">
        <h2 style="margin: 0 0 10px 0; font-size: 24px;">Welcome, {user_name}!</h2>
        <p style="margin: 0; opacity: 0.9;">Your account is ready. Let's create your first market report.</p>
    </div>

    <div style="margin-bottom: 30px;">
        <h3 style="color: #333; margin-bottom: 15px;">Getting Started</h3>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="background: #7C3AED; color: white; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 12px;">1</span>
                <span><strong>Complete your profile</strong> - Add your name and contact info</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="background: #7C3AED; color: white; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 12px;">2</span>
                <span><strong>Set up branding</strong> - Upload your logo and colors</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="background: #7C3AED; color: white; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 12px;">3</span>
                <span><strong>Create a report</strong> - Generate your first market snapshot</span>
            </div>
        </div>
    </div>

    <div style="text-align: center; margin-bottom: 30px;">
        <a href="{login_url}" style="display: inline-block; background: #7C3AED; color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600;">Get Started</a>
    </div>

    <div style="border-top: 1px solid #e5e5e5; padding-top: 20px; text-align: center; color: #666; font-size: 14px;">
        <p>Questions? Reply to this email or contact support.</p>
        <p style="margin-top: 10px;">
            <a href="{login_url}" style="color: #7C3AED; text-decoration: none;">Market Reports</a>
        </p>
    </div>
</body>
</html>
"""


def get_welcome_email_text(user_name: str, login_url: str) -> str:
    """Generate welcome email plain text."""
    return f"""
Welcome to Market Reports, {user_name}!

Your account is ready. Let's create your first market report.

Getting Started:
1. Complete your profile - Add your name and contact info
2. Set up branding - Upload your logo and colors
3. Create a report - Generate your first market snapshot

Get started: {login_url}

Questions? Reply to this email or contact support.

- The Market Reports Team
"""


def send_welcome_email(email: str, user_name: str) -> Dict[str, Any]:
    """
    Send welcome email to a new user.

    Args:
        email: User's email address
        user_name: User's display name

    Returns:
        Result from email service
    """
    login_url = f"{email_service.app_base}/app"

    html = get_welcome_email_html(user_name, login_url)
    text = get_welcome_email_text(user_name, login_url)

    return email_service.send_email_sync(
        to=email,
        subject="Welcome to Market Reports!",
        html=html,
        text=text,
        tags=[{"name": "category", "value": "welcome"}],
    )


def get_invite_email_html(
    inviter_name: str,
    company_name: str,
    invite_url: str,
) -> str:
    """Generate invite email HTML for sponsored agents."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>You're Invited to Market Reports</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #7C3AED; margin: 0;">Market Reports</h1>
    </div>

    <div style="background: linear-gradient(135deg, #7C3AED 0%, #a855f7 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;">
        <h2 style="margin: 0 0 10px 0; font-size: 24px;">You've Been Invited!</h2>
        <p style="margin: 0; opacity: 0.9;">{inviter_name} from {company_name} has invited you to Market Reports.</p>
    </div>

    <div style="margin-bottom: 30px;">
        <p>You've been invited to join Market Reports, a platform for generating beautiful real estate market reports.</p>
        <p>As a sponsored agent, you'll get:</p>
        <ul style="padding-left: 20px;">
            <li>75 free reports per month</li>
            <li>Professional branded reports</li>
            <li>Scheduled report delivery</li>
            <li>Contact management</li>
        </ul>
    </div>

    <div style="text-align: center; margin-bottom: 30px;">
        <a href="{invite_url}" style="display: inline-block; background: #7C3AED; color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600;">Accept Invitation</a>
    </div>

    <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin-bottom: 30px;">
        <p style="margin: 0; color: #856404; font-size: 14px;">
            <strong>Note:</strong> This invitation link will expire in 7 days.
        </p>
    </div>

    <div style="border-top: 1px solid #e5e5e5; padding-top: 20px; text-align: center; color: #666; font-size: 14px;">
        <p>Questions? Contact {company_name} or reply to this email.</p>
    </div>
</body>
</html>
"""


def send_invite_email(
    email: str,
    inviter_name: str,
    company_name: str,
    invite_token: str,
) -> Dict[str, Any]:
    """
    Send invitation email to a sponsored agent.

    Args:
        email: Recipient email address
        inviter_name: Name of the person sending the invite
        company_name: Company name of the inviter
        invite_token: Token for accepting the invitation

    Returns:
        Result from email service
    """
    invite_url = f"{email_service.app_base}/welcome?token={invite_token}"

    html = get_invite_email_html(inviter_name, company_name, invite_url)

    return email_service.send_email_sync(
        to=email,
        subject=f"{inviter_name} invited you to Market Reports",
        html=html,
        tags=[{"name": "category", "value": "invite"}],
    )


# ============ Password Reset Email ============

def get_password_reset_email_html(user_name: str, reset_url: str) -> str:
    """Generate password reset email HTML."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #7C3AED; margin: 0;">TrendyReports</h1>
    </div>

    <div style="background: linear-gradient(135deg, #7C3AED 0%, #a855f7 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;">
        <h2 style="margin: 0 0 10px 0; font-size: 24px;">Password Reset Request</h2>
        <p style="margin: 0; opacity: 0.9;">Hi {user_name}, we received a request to reset your password.</p>
    </div>

    <div style="margin-bottom: 30px;">
        <p>Click the button below to reset your password. This link will expire in <strong>1 hour</strong>.</p>
    </div>

    <div style="text-align: center; margin-bottom: 30px;">
        <a href="{reset_url}" style="display: inline-block; background: #7C3AED; color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600;">Reset Password</a>
    </div>

    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <p style="margin: 0 0 10px 0; font-size: 14px; color: #666;">
            <strong>Didn't request this?</strong>
        </p>
        <p style="margin: 0; font-size: 14px; color: #666;">
            If you didn't request a password reset, you can safely ignore this email. Your password won't be changed.
        </p>
    </div>

    <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin-bottom: 30px;">
        <p style="margin: 0; color: #856404; font-size: 14px;">
            <strong>Security tip:</strong> Never share this link with anyone. TrendyReports will never ask for your password via email.
        </p>
    </div>

    <div style="border-top: 1px solid #e5e5e5; padding-top: 20px; text-align: center; color: #666; font-size: 14px;">
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #7C3AED;">{reset_url}</p>
        <p style="margin-top: 20px;">
            <a href="{email_service.app_base}" style="color: #7C3AED; text-decoration: none;">TrendyReports</a>
        </p>
    </div>
</body>
</html>
"""


def get_password_reset_email_text(user_name: str, reset_url: str) -> str:
    """Generate password reset email plain text."""
    return f"""
Password Reset Request

Hi {user_name},

We received a request to reset your password. Click the link below to reset it:

{reset_url}

This link will expire in 1 hour.

Didn't request this?
If you didn't request a password reset, you can safely ignore this email. Your password won't be changed.

Security tip: Never share this link with anyone.

- The TrendyReports Team
"""


def send_password_reset_email(email: str, user_name: str, reset_token: str) -> Dict[str, Any]:
    """
    Send password reset email.

    Args:
        email: User's email address
        user_name: User's display name
        reset_token: Password reset token

    Returns:
        Result from email service
    """
    reset_url = f"{email_service.app_base}/reset-password?token={reset_token}"

    html = get_password_reset_email_html(user_name, reset_url)
    text = get_password_reset_email_text(user_name, reset_url)

    return email_service.send_email_sync(
        to=email,
        subject="Reset your TrendyReports password",
        html=html,
        text=text,
        tags=[{"name": "category", "value": "password-reset"}],
    )