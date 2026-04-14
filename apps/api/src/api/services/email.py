"""
Email Service using SendGrid

Provides email sending functionality for:
- Email verification
- Agent invitations
- Password reset
- Plan limit notifications
"""

import logging
from typing import Optional, Dict, Any, List
import httpx
from ..settings import settings

logger = logging.getLogger(__name__)

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def _parse_from_address(from_addr: str) -> Dict[str, str]:
    """Parse 'Name <email>' format into SendGrid from object."""
    if "<" in from_addr:
        name = from_addr.split("<")[0].strip()
        email = from_addr.split("<")[-1].rstrip(">").strip()
        return {"email": email, "name": name} if name else {"email": email}
    return {"email": from_addr}


class EmailService:
    """Email service using SendGrid API."""

    def __init__(self):
        self.from_address = settings.EMAIL_FROM_ADDRESS
        self.reply_to = settings.EMAIL_REPLY_TO
        self.app_base = settings.APP_BASE

    @property
    def api_key(self) -> str:
        return settings.SENDGRID_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _build_payload(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        recipients = [to] if isinstance(to, str) else to

        payload: Dict[str, Any] = {
            "personalizations": [{"to": [{"email": r} for r in recipients]}],
            "from": _parse_from_address(self.from_address),
            "subject": subject,
            "content": [{"type": "text/html", "value": html}],
        }

        if text:
            payload["content"].insert(0, {"type": "text/plain", "value": text})

        effective_reply_to = reply_to or self.reply_to
        if effective_reply_to:
            payload["reply_to"] = {"email": effective_reply_to}

        if tags:
            payload["categories"] = [t.get("value", t.get("name", "")) for t in tags if t]

        return payload

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Send an email via SendGrid (async)."""
        if not self.is_configured:
            recipients_str = to if isinstance(to, str) else ", ".join(to)
            logger.error("SENDGRID_API_KEY not set — email NOT sent to: %s, subject: %s", recipients_str, subject)
            return {"ok": False, "error": "Email service not configured — SENDGRID_API_KEY missing"}

        payload = self._build_payload(to, subject, html, text, reply_to, tags)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SENDGRID_API_URL,
                    headers=self._headers(),
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code in (200, 201, 202):
                    logger.info(f"Email sent via SendGrid to {to}: {subject}")
                    return {"ok": True}
                else:
                    error = response.text
                    logger.error(f"SendGrid error {response.status_code}: {error}")
                    return {"ok": False, "error": error, "status": response.status_code}

        except Exception as e:
            logger.error(f"Exception sending email via SendGrid: {e}")
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
        """Send an email via SendGrid (synchronous)."""
        if not self.is_configured:
            recipients_str = to if isinstance(to, str) else ", ".join(to)
            logger.error("SENDGRID_API_KEY not set — email NOT sent to: %s, subject: %s", recipients_str, subject)
            return {"ok": False, "error": "Email service not configured — SENDGRID_API_KEY missing"}

        payload = self._build_payload(to, subject, html, text, reply_to, tags)

        try:
            with httpx.Client() as client:
                response = client.post(
                    SENDGRID_API_URL,
                    headers=self._headers(),
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code in (200, 201, 202):
                    logger.info(f"Email sent via SendGrid to {to}: {subject}")
                    return {"ok": True}
                else:
                    error = response.text
                    logger.error(f"SendGrid error {response.status_code}: {error}")
                    return {"ok": False, "error": error, "status": response.status_code}

        except Exception as e:
            logger.error(f"Exception sending email via SendGrid: {e}")
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
              <img src="https://trendyreports.io/white.png" width="160" alt="TrendyReports" style="display: block; max-height: 40px; width: auto; height: auto;">
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


# ============ Plan Limit Notifications ============

def send_limit_warning_email(email: str, first_name: str, count: int, limit: int) -> Dict[str, Any]:
    """Send 80% usage warning email."""
    billing_url = f"{email_service.app_base}/app/settings/billing"
    name = first_name or "there"
    content = f'''<p style="margin: 0 0 20px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; color: #111827;">
                Hi {name},
              </p>
              <p style="margin: 0 0 8px; font-size: 15px; line-height: 1.7; color: #374151;">
                You&rsquo;ve used <strong>{count}</strong> of your <strong>{limit}</strong> monthly reports.
                Upgrade your plan to continue generating reports without interruption.
              </p>
              <div style="background-color: #FFFBEB; border-left: 3px solid #F59E0B; padding: 12px 16px; border-radius: 0 6px 6px 0; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #92400E;">
                  <strong>{int(count / limit * 100)}%</strong> of your monthly limit used &mdash; {limit - count} reports remaining.
                </p>
              </div>
              {_cta_button(billing_url, "Upgrade Plan")}
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #6b7280;">
                Your limit resets at the start of next month.
              </p>'''
    return email_service.send_email_sync(
        to=email,
        subject=f"You\u2019ve used 80% of your monthly reports",
        html=_email_base(content),
        tags=[{"name": "category", "value": "limit-warning"}],
    )


def send_limit_reached_email(email: str, first_name: str, limit: int) -> Dict[str, Any]:
    """Send 100% limit-reached email."""
    billing_url = f"{email_service.app_base}/app/settings/billing"
    name = first_name or "there"
    content = f'''<p style="margin: 0 0 20px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; color: #111827;">
                Hi {name},
              </p>
              <p style="margin: 0 0 8px; font-size: 15px; line-height: 1.7; color: #374151;">
                You&rsquo;ve reached your <strong>{limit}</strong> report limit for this month.
                Upgrade your plan to generate more reports.
              </p>
              <div style="background-color: #FEF2F2; border-left: 3px solid #EF4444; padding: 12px 16px; border-radius: 0 6px 6px 0; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #991B1B;">
                  Monthly limit reached &mdash; report generation is paused until next month or until you upgrade.
                </p>
              </div>
              {_cta_button(billing_url, "Upgrade Plan")}
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #6b7280;">
                Your limit resets at the start of next month.
              </p>'''
    return email_service.send_email_sync(
        to=email,
        subject="Monthly report limit reached",
        html=_email_base(content),
        tags=[{"name": "category", "value": "limit-reached"}],
    )