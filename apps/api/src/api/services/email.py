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


# ============ Shared Email Shell ============

def _email_base(content_html: str) -> str:
    """Wraps content in the standard TrendyReports transactional email shell."""
    return f'''<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="color-scheme" content="light only">
  <meta name="supported-color-schemes" content="light only">
  <title>TrendyReports</title>
  <style>
    body, table, td, p, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    img {{ border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }}
    body {{ margin: 0 !important; padding: 0 !important; width: 100% !important; }}
    @media (prefers-color-scheme: dark) {{
      .email-outer {{ background-color: #232323 !important; }}
    }}
    @media screen and (max-width: 600px) {{
      .email-wrapper {{ width: 100% !important; }}
      .content-pad {{ padding: 24px 20px !important; }}
      .cta-btn {{ display: block !important; width: 100% !important; text-align: center !important; }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #F8FAFC;" class="email-outer">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" class="email-wrapper" style="max-width: 600px; width: 100%;">

          <!-- HEADER -->
          <tr>
            <td align="center" style="background: linear-gradient(135deg, #4F46E5 0%, #6366F1 50%, #818CF8 100%); background-color: #4F46E5; padding: 28px 24px 20px; border-radius: 12px 12px 0 0;">
              <img src="https://trendyreports.io/logo-white.png" width="160" alt="TrendyReports" style="display: block; max-height: 40px; width: auto; height: auto;">
            </td>
          </tr>

          <!-- CONTENT -->
          <tr>
            <td style="background-color: #ffffff; padding: 32px;" class="content-pad">
              {content_html}
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background-color: #ffffff; border-top: 1px solid #EEF2FF; padding: 20px 32px; border-radius: 0 0 12px 12px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <p style="margin: 0 0 4px; font-size: 13px; font-weight: 600; color: #6366F1;">TrendyReports</p>
                    <p style="margin: 0 0 12px; font-size: 12px; color: #9ca3af;">Branded Real Estate Reports</p>
                    <p style="margin: 0; font-size: 11px; color: #9ca3af;">
                      <a href="mailto:support@trendyreports.io" style="color: #6b7280; text-decoration: underline;">Contact Support</a>
                      &nbsp;&bull;&nbsp; &copy; 2026 TrendyReports
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''


def _cta_button(url: str, label: str) -> str:
    """Indigo CTA button with VML fallback for Outlook."""
    return f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin: 28px 0;">
                <tr>
                  <td align="center">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{url}" style="height:48px;v-text-anchor:middle;width:240px;" arcsize="17%" stroke="f" fillcolor="#4F46E5">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:16px;font-weight:bold;">{label}</center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{url}" target="_blank" class="cta-btn" style="display: inline-block; background-color: #4F46E5; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 16px; font-weight: bold; text-decoration: none; padding: 14px 32px; border-radius: 8px;">
                      {label}
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>'''


# ============ Email Verification ============

def get_verification_email_html(user_name: str, verify_url: str) -> str:
    """Generate email verification HTML."""
    first_name = (user_name or "").split()[0] if user_name else "there"
    content = f'''<p style="margin: 0 0 20px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; color: #111827;">
                Hi {first_name},
              </p>
              <p style="margin: 0 0 8px; font-size: 15px; line-height: 1.7; color: #374151;">
                Thanks for signing up for TrendyReports. Verify your email to start creating branded market reports for your clients.
              </p>
              {_cta_button(verify_url, "Verify My Email")}
              <p style="margin: 0 0 8px; font-size: 13px; line-height: 1.6; color: #6b7280;">
                This link expires in 24 hours.
              </p>
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #6b7280;">
                If you didn't create an account, you can safely ignore this email.
              </p>'''
    return _email_base(content)


def get_verification_email_text(user_name: str, verify_url: str) -> str:
    """Generate email verification plain text."""
    first_name = (user_name or "").split()[0] if user_name else "there"
    return f"""Hi {first_name},

Thanks for signing up for TrendyReports. Verify your email to start creating branded market reports for your clients.

Verify your email: {verify_url}

This link expires in 24 hours.

If you didn't create an account, you can safely ignore this email.

- The TrendyReports Team
"""


def send_verification_email(email: str, user_name: str, verification_token: str) -> Dict[str, Any]:
    """Send email verification email."""
    verify_url = f"{email_service.app_base}/verify-email?token={verification_token}"

    html = get_verification_email_html(user_name, verify_url)
    text = get_verification_email_text(user_name, verify_url)

    return email_service.send_email_sync(
        to=email,
        subject="Verify your email \u2014 TrendyReports",
        html=html,
        text=text,
        tags=[{"name": "category", "value": "verification"}],
    )


# ============ Agent Invite ============

def get_invite_email_html(
    inviter_name: str,
    company_name: str,
    invite_url: str,
) -> str:
    """Generate invite email HTML for sponsored agents."""
    content = f'''<p style="margin: 0 0 20px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; color: #111827;">
                Hi,
              </p>
              <p style="margin: 0 0 20px; font-size: 15px; line-height: 1.7; color: #374151;">
                <strong>{inviter_name}</strong> from <strong>{company_name}</strong> invited you to join TrendyReports &mdash; a platform for creating branded real estate market reports and property analyses.
              </p>
              <p style="margin: 0 0 12px; font-size: 15px; line-height: 1.7; color: #374151;">
                Your sponsored account includes:
              </p>
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin: 0 0 8px;">
                <tr><td style="padding: 6px 0; font-size: 15px; line-height: 1.7; color: #374151;">&#10003;&ensp; Branded market reports with your contact info</td></tr>
                <tr><td style="padding: 6px 0; font-size: 15px; line-height: 1.7; color: #374151;">&#10003;&ensp; Automated report scheduling and delivery</td></tr>
                <tr><td style="padding: 6px 0; font-size: 15px; line-height: 1.7; color: #374151;">&#10003;&ensp; Property CMA reports with comparables</td></tr>
              </table>
              {_cta_button(invite_url, "Accept Invitation")}
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #6b7280;">
                This invitation expires in 7 days.
              </p>'''
    return _email_base(content)


def send_invite_email(
    email: str,
    inviter_name: str,
    company_name: str,
    invite_token: str,
) -> Dict[str, Any]:
    """Send invitation email to a sponsored agent."""
    invite_url = f"{email_service.app_base}/welcome?token={invite_token}"

    html = get_invite_email_html(inviter_name, company_name, invite_url)

    return email_service.send_email_sync(
        to=email,
        subject=f"{inviter_name} invited you to TrendyReports",
        html=html,
        tags=[{"name": "category", "value": "invite"}],
    )


# ============ Password Reset ============

def get_password_reset_email_html(user_name: str, reset_url: str) -> str:
    """Generate password reset email HTML."""
    first_name = (user_name or "").split()[0] if user_name else "there"
    content = f'''<p style="margin: 0 0 20px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; color: #111827;">
                Hi {first_name},
              </p>
              <p style="margin: 0 0 8px; font-size: 15px; line-height: 1.7; color: #374151;">
                We received a request to reset your password. Click below to choose a new one.
              </p>
              {_cta_button(reset_url, "Reset Password")}
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #6b7280;">
                This link expires in 1 hour. If you didn't request this, no action is needed &mdash; your password won't change.
              </p>'''
    return _email_base(content)


def get_password_reset_email_text(user_name: str, reset_url: str) -> str:
    """Generate password reset email plain text."""
    first_name = (user_name or "").split()[0] if user_name else "there"
    return f"""Hi {first_name},

We received a request to reset your password. Click the link below to choose a new one:

{reset_url}

This link expires in 1 hour. If you didn't request this, no action is needed — your password won't change.

- The TrendyReports Team
"""


def send_password_reset_email(email: str, user_name: str, reset_token: str) -> Dict[str, Any]:
    """Send password reset email."""
    reset_url = f"{email_service.app_base}/reset-password?token={reset_token}"

    html = get_password_reset_email_html(user_name, reset_url)
    text = get_password_reset_email_text(user_name, reset_url)

    return email_service.send_email_sync(
        to=email,
        subject="Reset your password \u2014 TrendyReports",
        html=html,
        text=text,
        tags=[{"name": "category", "value": "password-reset"}],
    )