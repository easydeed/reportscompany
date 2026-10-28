"""
Email Service using SendGrid

Provides email sending functionality for:
- Email verification
- Agent invitations
- Password reset
- Plan limit notifications
- Welcome onboarding emails
"""

import html
import logging
import os
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


# ============ Shared Email Shell (Design, 5th package) ============
#
# docs/design-claude/5thpackage/design_handoff_email_social/emails/transactional/
#
# THE SHELL IS DESIGN'S; THE WORDS ARE NOT YET. Every email below keeps the
# wording it had, rebuilt from the row helpers so it reads in both colour
# schemes. Design's own copy for these emails contradicts decisions already
# made (the wrong address, "10 reports", "paid by", "he", a retry and an
# un-pause that do not exist, 90 vs 180 days), and it comes in when Design
# corrects it — not before.
#
# DARK MODE. The shell declares `light dark` and remaps every `tr-*` class.
# That is why the content had to be rebuilt rather than dropped in: the old
# paragraphs set `color:#374151` inline with no class, and a dark card under
# them would have been dark text on dark.
#
# ESCAPING (D-296). Every value a person typed — inviter, invitee, company and
# rep names — goes through `_e` before it reaches markup. The helpers take
# HTML, so the escaping happens at the call sites, once, where the value is
# known to be text.
#
# The same shell is inlined in `apps/worker/src/worker/tasks.py` for the
# schedule-failure notice, because the worker does not import the API.
# `test_transactional_shell.py` holds the two to the same markup.

#: TrendyReports' registered address, a business decision (see the worker's
#: `email/template.py`, where it was first recorded). Never the one in Design's
#: mocks. Environment-overridable; a blank variable cannot empty it.
PLATFORM_POSTAL_ADDRESS = (
    os.getenv("PLATFORM_POSTAL_ADDRESS", "").strip()
    or "440 Rte. 66, Glendora, CA 91740"
)

_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def _app_base() -> str:
    """Where the app lives. The one line that differs from the worker's copy."""
    return email_service.app_base


def _e(value: Optional[str]) -> str:
    """Escape a typed value for HTML. `None` is the empty string."""
    return html.escape(value or "", quote=True)


def _row(inner: str, pad: str = "14px 28px 0") -> str:
    return (f'<tr><td class="tr-pad" style="padding:{pad};font-family:{_FONT};">'
            f'{inner}</td></tr>')


def _h1(text_html: str) -> str:
    """The email's first line, as Design's headline."""
    return _row(f'<h1 class="tr-ink" style="margin:0;font-size:24px;line-height:1.25;'
                f'font-weight:800;letter-spacing:-.025em;color:#0F172A;">{text_html}</h1>',
                pad="28px 28px 0")


def _p(text_html: str) -> str:
    return _row(f'<p class="tr-body" style="margin:0;font-size:15.5px;line-height:1.6;'
                f'color:#334155;">{text_html}</p>')


def _note(text_html: str) -> str:
    """Small print inside the body: expiry, "ignore this if…"."""
    return _row(f'<p class="tr-muted" style="margin:0;font-size:13px;line-height:1.6;'
                f'color:#64748B;">{text_html}</p>')


def _link(url: str, label_html: str) -> str:
    return (f'<a href="{_e(url)}" class="tr-ink" style="color:#0F172A;'
            f'text-decoration:underline;font-weight:600;">{label_html}</a>')


def _checklist(items_html: List[str]) -> str:
    cells = "".join(
        f'<tr><td class="tr-body" style="padding:5px 0;font-family:{_FONT};font-size:15px;'
        f'line-height:1.6;color:#334155;">&#10003;&ensp;{item}</td></tr>'
        for item in items_html)
    return _row(f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                f'width="100%" style="border-collapse:collapse;">{cells}</table>')


#: Callout palettes: (background, rule, text). Pale fills with dark text, set
#: inline and given no `tr-*` class, so they stay pale in dark mode and the
#: text stays readable on them (each 7:1 or better).
_TONES = {
    "amber": ("#FFFBEB", "#F59E0B", "#92400E"),
    "red": ("#FEF2F2", "#EF4444", "#991B1B"),
    "green": ("#F0FDF4", "#22C55E", "#166534"),
    "indigo": ("#EEF2FF", "#6366F1", "#3730A3"),
}


def _callout(text_html: str, tone: str) -> str:
    bg, rule, ink = _TONES[tone]
    return _row(f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                f'width="100%" style="border-collapse:collapse;"><tr><td bgcolor="{bg}" '
                f'style="background:{bg};border-left:3px solid {rule};padding:12px 16px;'
                f'font-family:{_FONT};font-size:14px;line-height:1.55;color:{ink};">'
                f'{text_html}</td></tr></table>', pad="18px 28px 0")


def _cta_button(url: str, label: str) -> str:
    """Design's button: an ink fill holding a padded block link."""
    return _row(f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                f'style="border-collapse:separate;"><tr><td bgcolor="#0F172A" '
                f'style="background:#0F172A;border-radius:10px;"><a href="{_e(url)}" '
                f'style="display:block;padding:14px 26px;font-family:{_FONT};font-size:15px;'
                f'font-weight:700;color:#ffffff;text-decoration:none;border-radius:10px;">'
                f'{_e(label)}</a></td></tr></table>', pad="24px 28px 0")


def _step_row(number: int, heading: str, description: str, cta_url: str, cta_label: str,
              last: bool = False) -> str:
    """One numbered onboarding step: Design's disc and two lines, plus the step's
    own link, which the current wording has and Design's single button does not.
    `heading` and `description` are HTML from this module, not typed values."""
    base = _app_base()
    return (
        f'<tr><td width="34" valign="top" class="tr-rule" style="width:34px;padding:14px 0;'
        f'border-top:1px solid #ECEAE3;"><table role="presentation" cellpadding="0" '
        f'cellspacing="0" border="0"><tr><td width="24" height="24" align="center" '
        f'valign="middle" bgcolor="#0F172A" style="width:24px;height:24px;border-radius:12px;'
        f'background:#0F172A;font-family:{_FONT};font-size:12px;font-weight:700;color:#ffffff;">'
        f'{number}</td></tr></table></td>'
        f'<td valign="top" class="tr-rule" style="padding:14px 0 14px 8px;border-top:1px solid '
        f'#ECEAE3;font-family:{_FONT};"><div class="tr-ink" style="font-size:15px;font-weight:700;'
        f'color:#0F172A;">{heading}</div><div class="tr-muted" style="margin-top:3px;'
        f'font-size:13.5px;line-height:1.55;color:#64748B;">{description}</div>'
        f'<div style="margin-top:8px;font-size:13.5px;">{_link(base + cta_url, _e(cta_label) + " &rarr;")}</div>'
        f'</td></tr>'
    )


def _steps(rows: List[str]) -> str:
    return _row(f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                f'width="100%" style="border-collapse:collapse;">{"".join(rows)}</table>',
                pad="20px 28px 0")


def _questions() -> str:
    return _note('Questions? Reply to this email or reach us at '
                 + _link("mailto:support@trendyreports.io", "support@trendyreports.io") + ".")


def _email_base(content_html: str, preheader: str = "") -> str:
    """Design's transactional shell around rows built by the helpers above."""
    app = _app_base()
    return f'''<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="x-apple-disable-message-reformatting">
<title>TrendyReports</title>
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
<style>
  body{{margin:0;padding:0;-webkit-text-size-adjust:100%;}}
  table{{mso-table-lspace:0;mso-table-rspace:0;}}
  img{{border:0;line-height:100%;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;}}
  a{{color:inherit;}}
  @media (prefers-color-scheme: dark){{
    .tr-page{{background:#111827 !important;}}
    .tr-card{{background:#1F2937 !important;border-color:#374151 !important;}}
    .tr-ink{{color:#F3F4F6 !important;}}
    .tr-body{{color:#D1D5DB !important;}}
    .tr-muted{{color:#9CA3AF !important;}}
    .tr-rule{{border-color:#374151 !important;}}
  }}
  @media only screen and (max-width:620px){{
    .tr-wrap{{width:100% !important;}}
    .tr-pad{{padding-left:20px !important;padding-right:20px !important;}}
  }}
</style>
</head>
<body class="tr-page" style="margin:0;padding:0;background:#FAFAF7;">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;">{preheader}&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;</div>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" class="tr-page" style="background:#FAFAF7;border-collapse:collapse;">
<tr><td align="center" style="padding:24px 12px;">
<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" class="tr-wrap tr-card" style="width:600px;max-width:600px;background:#ffffff;border-collapse:collapse;border:1px solid #E4E2DA;">
<tr><td class="tr-pad" style="padding:26px 28px 0;font-family:{_FONT};"><table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:separate;"><tr><td valign="baseline" class="tr-ink" style="font-family:{_FONT};font-size:21px;font-weight:800;letter-spacing:-.04em;color:#0F172A;">Trendy</td><td width="6" style="width:6px;"></td><td valign="middle" bgcolor="#D1FAE5" style="background:#D1FAE5;border-radius:4px;padding:2px 7px;font-family:{_FONT};font-size:10.5px;font-weight:700;color:#065F46;">&#9650;&nbsp;Reports</td></tr></table></td></tr>
{content_html}
<tr><td style="height:30px;line-height:30px;font-size:0;">&nbsp;</td></tr>
<tr><td class="tr-pad tr-rule" style="padding:22px 28px 28px;border-top:1px solid #ECEAE3;font-family:{_FONT};"><p class="tr-muted" style="margin:0;font-size:12px;line-height:1.6;color:#64748B;">TrendyReports · {_e(PLATFORM_POSTAL_ADDRESS)} · <a href="{_e(app)}/app/help" class="tr-muted" style="color:#64748B;text-decoration:underline;">Help</a> · <a href="mailto:support@trendyreports.io" class="tr-muted" style="color:#64748B;text-decoration:underline;">Contact support</a></p></td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>'''


# ============ Email Verification ============

def get_verification_email_html(user_name: str, verify_url: str) -> str:
    """Generate email verification HTML."""
    first_name = (user_name or "").split()[0] if user_name else "there"
    content = (
        _h1(f"Hi {_e(first_name)},")
        + _p("Thanks for signing up for TrendyReports. Verify your email to start creating branded market reports for your clients.")
        + _cta_button(verify_url, "Verify My Email")
        + _note("This link expires in 24 hours.")
        + _note("If you didn't create an account, you can safely ignore this email.")
    )
    return _email_base(content, preheader="Thanks for signing up for TrendyReports.")


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
        subject="Verify your email — TrendyReports",
        html=html,
        text=text,
        tags=[{"name": "category", "value": "verification"}],
    )


# ============ Agent Invite ============

def get_invite_email_html(
    inviter_name: str,
    company_name: str,
    invite_url: str,
    invitee_first_name: str | None = None,
) -> str:
    """Generate invite email HTML for sponsored agents."""
    greeting = f"Hi {_e(invitee_first_name)}," if invitee_first_name else "Hi,"
    content = (
        _h1(greeting)
        + _p(f"<strong>{_e(inviter_name)}</strong> from <strong>{_e(company_name)}</strong> invited you to join TrendyReports &mdash; a platform for creating branded real estate market reports and property analyses.")
        + _p("Your trial account includes:")
        + _checklist([
            "Branded market reports with your contact info",
            "Automated report scheduling and delivery",
            "Property CMA reports with comparables",
        ])
        + _cta_button(invite_url, "Accept Invitation")
        + _note("This invitation expires in 7 days.")
    )
    return _email_base(content, preheader=f"{_e(inviter_name)} invited you to join TrendyReports.")


def send_invite_email(
    email: str,
    inviter_name: str,
    company_name: str,
    invite_token: str,
    invitee_first_name: str | None = None,
) -> Dict[str, Any]:
    """
    Send invitation email to a sponsored agent.

    Deprecated for new code: prefer send_role_invite_email so copy and CTA stay
    consistent per invite type (company admin, rep, agent, etc.).
    """
    invite_url = f"{email_service.app_base}/welcome?token={invite_token}"

    html = get_invite_email_html(inviter_name, company_name, invite_url, invitee_first_name)

    return email_service.send_email_sync(
        to=email,
        subject=f"{inviter_name} invited you to TrendyReports",
        html=html,
        tags=[{"name": "category", "value": "invite"}],
    )


def send_role_invite_email(
    email: str,
    inviter_name: str,
    company_name: str,
    invite_token: str,
    *,
    invitee_first_name: str = "",
    role: str = "sponsored_agent",
) -> Dict[str, Any]:
    """Send role-appropriate invitation email (shared invite service)."""
    invite_url = f"{email_service.app_base}/welcome?token={invite_token}"
    greeting = f"Hi {_e(invitee_first_name.strip())}," if (invitee_first_name or "").strip() else "Hi,"
    inviter, company = _e(inviter_name), _e(company_name)

    if role == "company_admin":
        subject = f"You're invited to manage {company_name} on TrendyReports"
        body_inner = (
            _h1(greeting)
            + _p(f"<strong>{inviter}</strong> has set up <strong>{company}</strong> on TrendyReports and invited you as the company administrator.")
            + _p("As company admin, you&rsquo;ll be able to:")
            + _checklist([
                "Set up your company&rsquo;s branding (logo and colors)",
                "Invite and manage your title reps",
                "Monitor agent activity across your team",
            ])
        )
    elif role == "affiliate_admin":
        subject = "You're invited to join TrendyReports as an affiliate"
        body_inner = (
            _h1(greeting)
            + _p(f"<strong>{inviter}</strong> has invited you to join TrendyReports to manage <strong>{company}</strong>.")
            + _p("You&rsquo;ll be able to:")
            + _checklist([
                "Set up white-label branding for your agents",
                "Invite and manage sponsored agents",
                "Track agent activity and report generation",
            ])
        )
    elif role == "title_rep":
        subject = f"You're invited to join {company_name} on TrendyReports"
        body_inner = (
            _h1(greeting)
            + _p(f"<strong>{inviter}</strong> from <strong>{company}</strong> has invited you to join as a title rep on TrendyReports.")
            + _p(f"Your company&rsquo;s branding can be applied to your book. You can invite agents &mdash; their reports can carry {company}&rsquo;s branding with your contact information.")
        )
    else:
        subject = "You're invited to join TrendyReports"
        body_inner = (
            _h1(greeting)
            + _p(f"<strong>{inviter}</strong> from <strong>{company}</strong> has invited you to join TrendyReports.")
            + _p("Your account includes access to branded market reports &mdash; generate professional reports for your clients in under 30 seconds.")
        )

    content = (
        body_inner
        + _cta_button(invite_url, "Accept Invitation")
        + _note("This invitation expires in 7 days.")
    )
    html = _email_base(content, preheader=f"{inviter} invited you to TrendyReports.")

    return email_service.send_email_sync(
        to=email,
        subject=subject,
        html=html,
        tags=[{"name": "category", "value": "invite"}],
    )


def send_rep_change_notice_email(
    email: str,
    *,
    first_name: str,
    company_name: str,
    new_rep_name: str,
    new_rep_email: str,
) -> Dict[str, Any]:
    """Tell an agent who their rep is now, after a seat reassignment.

    Without it the agent starts getting email from a stranger. Says who, from
    which company, and that nothing about the agent's own account changed —
    which is true: reassignment moves the sponsor and leaves the plan alone.

    Every interpolated value is escaped. The names are typed by company admins
    and agents, and this is HTML.
    """
    greeting = f"Hi {_e(first_name.strip())}," if (first_name or "").strip() else "Hi,"
    company = _e(company_name or "your title company")
    rep = _e(new_rep_name)
    content = (
        _h1(greeting)
        + _p(f"Your rep at <strong>{company}</strong> is now <strong>{rep}</strong> "
             f"({_link('mailto:' + (new_rep_email or ''), _e(new_rep_email))}).")
        + _p("Nothing about your account changes: your reports, schedules and plan stay as they are.")
    )
    return email_service.send_email_sync(
        to=email,
        subject=f"Your rep at {company_name or 'your title company'} is now {new_rep_name}",
        html=_email_base(content, preheader=f"Your rep at {company} is now {rep}."),
        tags=[{"name": "category", "value": "rep-change"}],
    )


# ============ Password Reset ============

def get_password_reset_email_html(user_name: str, reset_url: str) -> str:
    """Generate password reset email HTML."""
    first_name = (user_name or "").split()[0] if user_name else "there"
    content = (
        _h1(f"Hi {_e(first_name)},")
        + _p("We received a request to reset your password. Click below to choose a new one.")
        + _cta_button(reset_url, "Reset Password")
        + _note("This link expires in 1 hour. If you didn't request this, no action is needed &mdash; your password won't change.")
    )
    return _email_base(content, preheader="We received a request to reset your password.")


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
        subject="Reset your password — TrendyReports",
        html=html,
        text=text,
        tags=[{"name": "category", "value": "password-reset"}],
    )


# ============ Plan Limit Notifications ============

def send_limit_warning_email(email: str, first_name: str, count: int, limit: int) -> Dict[str, Any]:
    """Send 80% usage warning email."""
    billing_url = f"{email_service.app_base}/app/settings/billing"
    name = _e(first_name or "there")
    content = (
        _h1(f"Hi {name},")
        + _p(f"You&rsquo;ve used <strong>{count}</strong> of your <strong>{limit}</strong> monthly reports. "
             f"Upgrade your plan to continue generating reports without interruption.")
        + _callout(f"<strong>{int(count / limit * 100)}%</strong> of your monthly limit used &mdash; "
                   f"{limit - count} reports remaining.", "amber")
        + _cta_button(billing_url, "Upgrade Plan")
        + _note("Your limit resets at the start of next month.")
    )
    return email_service.send_email_sync(
        to=email,
        subject=f"You’ve used 80% of your monthly reports",
        html=_email_base(content, preheader=f"You’ve used {count} of your {limit} monthly reports."),
        tags=[{"name": "category", "value": "limit-warning"}],
    )


def send_limit_reached_email(email: str, first_name: str, limit: int) -> Dict[str, Any]:
    """Send 100% limit-reached email."""
    billing_url = f"{email_service.app_base}/app/settings/billing"
    name = _e(first_name or "there")
    content = (
        _h1(f"Hi {name},")
        + _p(f"You&rsquo;ve reached your <strong>{limit}</strong> report limit for this month. "
             f"Upgrade your plan to generate more reports.")
        + _callout("Monthly limit reached &mdash; report generation is paused until next month or until you upgrade.", "red")
        + _cta_button(billing_url, "Upgrade Plan")
        + _note("Your limit resets at the start of next month.")
    )
    return email_service.send_email_sync(
        to=email,
        subject="Monthly report limit reached",
        html=_email_base(content, preheader=f"You’ve reached your {limit} report limit for this month."),
        tags=[{"name": "category", "value": "limit-reached"}],
    )


# ============ Welcome / Onboarding Emails ============

def send_affiliate_welcome_email(to_email: str, first_name: str) -> Dict[str, Any]:
    """Welcome email for affiliate partners after invite acceptance."""
    name = _e(first_name or "there")
    content = (
        _h1(f"Welcome aboard, {name}!")
        + _p("Your affiliate account is live. Here&rsquo;s how to get your agents generating branded reports in minutes.")
        + _steps([
            _step_row(1, "Set Up Your Branding",
                      "Upload your company logo, pick brand colors, and add your contact details. Every report your agents generate will carry your branding.",
                      "/app/settings/branding", "Configure Branding"),
            _step_row(2, "Invite Your Agents",
                      "Add agents one-by-one or bulk-import a CSV. Each agent gets a trial account and an invite email with a setup link.",
                      "/app/affiliate", "Go to Agent Dashboard"),
            _step_row(3, "Monitor Performance",
                      "Track how many reports each agent generates, manage their accounts, and watch your brand reach grow from the affiliate dashboard.",
                      "/app/affiliate", "View Dashboard", last=True),
        ])
        + _questions()
    )
    return email_service.send_email_sync(
        to=to_email,
        subject="Welcome to TrendyReports — Let’s get your agents set up",
        html=_email_base(content, preheader="Your affiliate account is live."),
        tags=[{"name": "category", "value": "welcome-affiliate"}],
    )


def send_sponsored_agent_welcome_email(to_email: str, first_name: str, affiliate_company_name: str) -> Dict[str, Any]:
    """Welcome email for sponsored (trial) agents after invite acceptance."""
    name = _e(first_name or "there")
    company = _e(affiliate_company_name or "your sponsor")
    report_types = (
        "Market Snapshot &bull; New Listings Gallery &bull; Luxury Market "
        "&bull; Investor Insights &bull; Neighborhood Deep-Dive "
        "&bull; First-Time Buyer &bull; Condo &amp; Townhome &bull; Relocation Guide"
    )
    content = (
        _h1(f"Welcome, {name}!")
        + _p(f"Your trial account has been set up by <strong>{company}</strong>. You&rsquo;re ready to start creating branded real estate reports.")
        + _callout(f"<strong>Available report types:</strong> {report_types}", "indigo")
        + _steps([
            _step_row(1, "Complete Your Profile",
                      "Add your headshot, phone number, and license info so every report includes your contact details.",
                      "/app/settings/profile", "Edit Profile"),
            _step_row(2, "Generate Your First Report",
                      "Pick a city or ZIP code, choose a report type, and get a branded PDF in under 30 seconds.",
                      "/app/reports/new", "Create a Report"),
            _step_row(3, "Set Up Automated Schedules",
                      "Schedule weekly or monthly reports to be generated and emailed to your contacts automatically.",
                      "/app/schedules/new", "Create a Schedule", last=True),
        ])
        + _questions()
    )
    return email_service.send_email_sync(
        to=to_email,
        subject="Welcome to TrendyReports — Generate your first report",
        html=_email_base(content, preheader=f"Your trial account has been set up by {company}."),
        tags=[{"name": "category", "value": "welcome-sponsored-agent"}],
    )


def send_regular_agent_welcome_email(to_email: str, first_name: str) -> Dict[str, Any]:
    """Welcome email for self-registered agents after email verification."""
    name = _e(first_name or "there")
    content = (
        _h1(f"Welcome to TrendyReports, {name}!")
        + _p("Your account is verified and ready to go. Here&rsquo;s how to get your first branded report in under 30 seconds.")
        + _steps([
            _step_row(1, "Set Up Your Branding",
                      "Upload your headshot and logo, choose colors, and add your license info. This appears on every report you generate.",
                      "/app/settings/branding", "Configure Branding"),
            _step_row(2, "Generate Your First Report",
                      "Pick a city or ZIP code, choose from 8 report types, and get a beautiful branded PDF instantly.",
                      "/app/reports/new", "Create a Report"),
            _step_row(3, "Add Contacts &amp; Automate",
                      "Import your contact list and set up automated schedules to deliver fresh market reports weekly or monthly.",
                      "/app/people", "Manage Contacts", last=True),
        ])
        # TODO(D-308): "5 reports per month" is the legacy `monthly_report_limit`;
        # the enforced `market_reports_limit` for Free is 3. Kept as written
        # until the copy is corrected — the owner asked for the current wording.
        + _callout("<strong>Your Free plan</strong> includes 5 reports per month. Need more? "
                   + f'<a href="{_e(email_service.app_base)}/app/settings/billing" style="color:#166534;font-weight:600;text-decoration:underline;">Upgrade anytime</a>.', "green")
        + _questions()
    )
    return email_service.send_email_sync(
        to=to_email,
        subject="Welcome to TrendyReports — Your first report is 30 seconds away",
        html=_email_base(content, preheader="Your account is verified and ready to go."),
        tags=[{"name": "category", "value": "welcome-regular"}],
    )


def send_company_admin_welcome_email(to_email: str, first_name: str, company_name: str) -> Dict[str, Any]:
    """Welcome email for Title Company admins after invite acceptance."""
    name = _e(first_name or "there")
    company = _e(company_name or "your company")
    content = (
        _h1(f"Welcome, {name}!")
        + _p(f"Your company account for <strong>{company}</strong> is live. As the company admin you can manage title reps, control branding across your organization, and monitor report activity.")
        + _steps([
            _step_row(1, "Set Up Your Company Branding",
                      "Upload your company logo and pick brand colors. These cascade to all reps and agents, so every report generated under your organization carries your identity.",
                      "/app/company/branding", "Set Up Branding"),
            _step_row(2, "Invite Your Title Reps",
                      "Each rep manages their own book of agents. Add reps and they’ll get their own dashboard to recruit and manage agents.",
                      "/app/company/reps", "Invite Reps"),
            _step_row(3, "Monitor Your Team",
                      "See all reps, all agents, and all reports from one dashboard. Track top performers and report volume across your entire organization.",
                      "/app/company", "View Dashboard", last=True),
        ])
        + _questions()
    )
    return email_service.send_email_sync(
        to=to_email,
        subject=f"Welcome to TrendyReports — Let’s set up {company_name or 'your company'}",
        html=_email_base(content, preheader=f"Your company account for {company} is live."),
        tags=[{"name": "category", "value": "welcome-company-admin"}],
    )


def send_rep_welcome_email(to_email: str, first_name: str, company_name: str) -> Dict[str, Any]:
    """Welcome email for Title Reps after invite acceptance."""
    name = _e(first_name or "there")
    company = _e(company_name or "your company")
    content = (
        _h1(f"Welcome aboard, {name}!")
        + _p(f"You&rsquo;ve been added as a title rep for <strong>{company}</strong>. Your company branding is already set up &mdash; here&rsquo;s how to get your agents generating branded reports in minutes.")
        + _steps([
            _step_row(1, "Complete Your Profile",
                      f"Add your photo, phone number, and license info. This appears on every report your agents generate, alongside {company}’s branding.",
                      "/app/settings/profile", "Complete Profile"),
            _step_row(2, "Invite Your Agents",
                      "Add agents one at a time or bulk-import a CSV. Each agent gets a trial account and can start generating reports immediately.",
                      "/app/affiliate", "Invite Agents"),
            _step_row(3, "Watch Your Network Grow",
                      f"Your agents will generate branded reports carrying <strong>{company}</strong>’s branding and your contact info. Track their activity from your affiliate dashboard.",
                      "/app/affiliate", "View Dashboard", last=True),
        ])
        + _questions()
    )
    return email_service.send_email_sync(
        to=to_email,
        subject=f"Welcome to TrendyReports — Start inviting your agents",
        html=_email_base(content, preheader=f"You’ve been added as a title rep for {company}."),
        tags=[{"name": "category", "value": "welcome-rep"}],
    )
