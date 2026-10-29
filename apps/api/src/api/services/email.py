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
import re
import logging
import os
from datetime import date, datetime, timedelta, timezone
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
# THE SHELL IS DESIGN'S, AND SO ARE THE WORDS WHERE THEY ARE TRUE. Since
# 2026-10-29 the copy is ours, built from Design's twelve bodies: their
# sentence wherever the code agrees with it, a corrected one where it does not.
# "What the copy may say", above the emails, lists every correction and why.
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
    """Design's button: an ink fill holding a padded block link. In dark mode
    the fill turns light and the label ink (`tr-fill`, `tr-fill-ink`): an ink
    button on the dark card was nearly invisible (D-313), and it is the one
    thing in the email meant to be pressed."""
    return _row(f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                f'style="border-collapse:separate;"><tr><td bgcolor="#0F172A" class="tr-fill" '
                f'style="background:#0F172A;border-radius:10px;"><a href="{_e(url)}" class="tr-fill-ink" '
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
        f'valign="middle" bgcolor="#0F172A" class="tr-fill tr-fill-ink" style="width:24px;height:24px;border-radius:12px;'
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


def _email_base(content_html: str, preheader: str = "", reason: str = "") -> str:
    """Design's transactional shell around rows built by the helpers above.

    THE LOGO IS AN IMAGE OF OUTLINED SHAPES, NOT TEXT. Design's lockup sets its
    wordmark in Plus Jakarta Sans, which no mail client loads; as live text it
    would draw in a system typeface. The PNGs in apps/web/public/email/ are
    rendered from outlined paths (scripts/outline_lockup.py). The light one
    shows by default and in Outlook; dark mode swaps in the dark one. Blocked
    images show the alt text, styled for each scheme.

    `reason` is the one line above the address that says why this email was
    sent ("Sent once, when you created your account"): what an account email
    carries in place of an unsubscribe.
    """
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
    .tr-logo-l{{display:none !important;}}
    .tr-logo-d{{display:block !important;max-height:none !important;}}
    .tr-fill{{background:#F3F4F6 !important;}}
    .tr-fill-ink{{color:#0F172A !important;}}
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
<tr><td class="tr-pad" style="padding:26px 28px 0;font-family:{_FONT};"><img class="tr-logo-l" src="{_e(app)}/email/trendy-lockup-light@3x.png" width="124" height="24" alt="TrendyReports" style="display:block;width:124px;height:24px;border:0;font-family:{_FONT};font-size:16px;font-weight:800;color:#0F172A;"><!--[if !mso]><!--><img class="tr-logo-d" src="{_e(app)}/email/trendy-lockup-dark@3x.png" width="124" height="24" alt="TrendyReports" style="display:none;max-height:0;overflow:hidden;width:124px;height:24px;border:0;font-family:{_FONT};font-size:16px;font-weight:800;color:#F3F4F6;"><!--<![endif]--></td></tr>
{content_html}
<tr><td style="height:30px;line-height:30px;font-size:0;">&nbsp;</td></tr>
<tr><td class="tr-pad tr-rule" style="padding:22px 28px 28px;border-top:1px solid #ECEAE3;font-family:{_FONT};">{f'<p class="tr-muted" style="margin:0 0 8px;font-size:12px;line-height:1.6;color:#64748B;">{reason}</p>' if reason else ''}<p class="tr-muted" style="margin:0;font-size:12px;line-height:1.6;color:#64748B;">TrendyReports · {_e(PLATFORM_POSTAL_ADDRESS)} · <a href="{_e(app)}/app/help" class="tr-muted" style="color:#64748B;text-decoration:underline;">Help</a> · <a href="mailto:support@trendyreports.io" class="tr-muted" style="color:#64748B;text-decoration:underline;">Contact support</a></p></td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>'''


def _plain(content_html: str) -> str:
    """The text part of an account email, from the same rows as the HTML, so
    the two cannot say different things. A link becomes "label: url"."""
    text = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"\2: \1", content_html, flags=re.S)
    text = re.sub(r"</td>", " ", text)
    text = re.sub(r"<br\s*/?>|</(p|h1|tr|li|div)>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n\n".join(line for line in lines if line) + "\n"


# ============ What the copy may say ============
#
# OUR WORDS, DESIGN'S WHERE THEY WERE TRUE (owner, 2026-10-29). Design's 12
# transactional bodies are used line for line wherever the code agrees with
# them. Where it does not, the sentence says what the code does:
#
#   * seats are REP seats — an agent gets an account, never a seat;
#   * nothing is "paid by" the title company (a compliance call);
#   * sponsored and Free plan numbers are READ FROM `plans` when the email is
#     built, never typed (D-308); no number at all if the read fails;
#   * a failed scheduled send is not retried; a schedule pauses itself after
#     AUTO_PAUSE_AFTER failures in a row (worker), and nothing un-pauses one;
#   * at the monthly limit, a scheduled send that comes due is skipped, not
#     queued, and an upgrade does not re-send it; only reports you make count
#     toward the limit; it resets on the 1st (UTC), with a 10% grace;
#   * a rep can see their agents' reports and schedules today
#     (/v1/affiliate/all-reports returns each pdf_url) — so no "never what's in
#     them" until the rep views stop showing content;
#   * the home-value page is not held back by an unconfirmed address; reports,
#     schedules and invites are (verification.block_unverified_send);
#   * link lifetimes are the constants below, which the routes that mint the
#     tokens also read;
#   * "they" for a rep or an inviter whose pronouns are not known.

#: How long each emailed link works. The routes that create the tokens read
#: these, so the sentence in the email and the expiry in the database are one
#: value (tests/test_account_email_copy.py holds the routes to them).
VERIFY_LINK_TTL = timedelta(hours=24)
INVITE_LINK_TTL = timedelta(days=7)
RESET_LINK_TTL = timedelta(hours=1)           # the user asked for it
ADMIN_RESET_LINK_TTL = timedelta(hours=24)    # a platform admin sent it


def _ttl_words(ttl: timedelta) -> str:
    """'24 hours', '7 days', '1 hour'."""
    hours = int(ttl.total_seconds() // 3600)
    if hours % 24 == 0 and hours >= 48:
        return f"{hours // 24} days"
    return f"{hours} hour{'' if hours == 1 else 's'}"


def _plan_limits(plan_slug: str) -> Optional[Dict[str, int]]:
    """`{market_reports, schedules}` for a plan, read from `plans` when the
    email is built. None on any failure: the caller drops the number."""
    try:
        from ..db import db_conn
        with db_conn() as (conn, cur):
            cur.execute(
                "SELECT market_reports_limit, schedules_limit FROM plans WHERE plan_slug = %s",
                (plan_slug,))
            row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001 — an email must not fail on this
        logger.warning("could not read the %s plan's limits: %s", plan_slug, exc)
        return None
    if not row:
        return None
    ok = lambda v: isinstance(v, int) and 0 < v < 10000  # noqa: E731
    return {
        "market_reports": row[0] if ok(row[0]) else None,
        "schedules": row[1] if ok(row[1]) else None,
    }


def _plan_market_limit(plan_slug: str) -> Optional[int]:
    """A plan's monthly market-report limit, from `plans` (D-308)."""
    limits = _plan_limits(plan_slug)
    return limits["market_reports"] if limits else None


def _plan_sentence(plan_slug: str, whose: str = "your") -> str:
    """'{N} market reports a month and {S} schedule that sends on its own',
    from the table; '' when nothing can be read."""
    limits = _plan_limits(plan_slug) or {}
    parts = []
    if limits.get("market_reports"):
        n = limits["market_reports"]
        parts.append(f"{n} market report{'' if n == 1 else 's'} a month")
    if limits.get("schedules"):
        n = limits["schedules"]
        parts.append(f"{n} schedule{' that sends' if n == 1 else 's that send'} to {whose} contacts on {'its' if n == 1 else 'their'} own")
    return " and ".join(parts)


def _next_reset(now: Optional[datetime] = None) -> date:
    """The 1st of next month, UTC: monthly counts start at
    date_trunc('month', NOW()) on a UTC database."""
    now = now or datetime.now(timezone.utc)
    return date(now.year + (now.month == 12), now.month % 12 + 1, 1)


def _month_day(d: date) -> str:
    return f"{d.strftime('%B')} {d.day}"


def _send(to: str, subject: str, content: str, *, preheader: str, reason: str,
          category: str) -> Dict[str, Any]:
    return email_service.send_email_sync(
        to=to,
        subject=subject,
        html=_email_base(content, preheader=preheader, reason=reason),
        text=_plain(content) + f"\n{_plain(reason).strip()}\nTrendyReports · {PLATFORM_POSTAL_ADDRESS}\n",
        tags=[{"name": "category", "value": category}],
    )


# ============ Email Verification ============

def get_verification_email_html(user_name: str, verify_url: str) -> str:
    return _email_base(_verification_content(verify_url),
                       preheader=_VERIFY_LEAD, reason=_VERIFY_REASON)


def get_verification_email_text(user_name: str, verify_url: str) -> str:
    return _plain(_verification_content(verify_url))


_VERIFY_LEAD = ("Nothing is emailed in your name until this address is confirmed &mdash; "
                "no reports, schedules or invites. One click and you&rsquo;re set.")
_VERIFY_REASON = "Sent because an account was created with this address."


def _verification_content(verify_url: str) -> str:
    return (
        _h1("Confirm it&rsquo;s you.")
        + _p(_VERIFY_LEAD)
        + _cta_button(verify_url, "Confirm email")
        + _note(f"Expires in {_ttl_words(VERIFY_LINK_TTL)}. If you didn&rsquo;t sign up, ignore this.")
    )


def send_verification_email(email: str, user_name: str, verification_token: str) -> Dict[str, Any]:
    verify_url = f"{email_service.app_base}/verify-email?token={verification_token}"
    return _send(email, "Confirm your email — TrendyReports", _verification_content(verify_url),
                 preheader=_VERIFY_LEAD, reason=_VERIFY_REASON, category="verification")


# ============ Invites ============

def send_invite_email(
    email: str,
    inviter_name: str,
    company_name: str,
    invite_token: str,
    invitee_first_name: str | None = None,
) -> Dict[str, Any]:
    """Deprecated: the agent invite is `send_role_invite_email(role="sponsored_agent")`."""
    return send_role_invite_email(email, inviter_name, company_name, invite_token,
                                  invitee_first_name=invitee_first_name or "", role="sponsored_agent")


def send_role_invite_email(
    email: str,
    inviter_name: str,
    company_name: str,
    invite_token: str,
    *,
    invitee_first_name: str = "",
    role: str = "sponsored_agent",
) -> Dict[str, Any]:
    """The invite, worded for the role it creates (shared invite service)."""
    invite_url = f"{email_service.app_base}/welcome?token={invite_token}"
    inviter, company = _e(inviter_name), _e(company_name)
    expiry = f"The link works for {_ttl_words(INVITE_LINK_TTL)}."
    reason = f"Sent because {inviter} at {company} entered this address."

    if role == "company_admin":
        subject = f"You're an admin for {company_name} on TrendyReports"
        headline = f"You&rsquo;re an admin for {company}."
        lead = (f"Admins set the brand, invite the reps, and see whether the network is working. "
                f"{inviter} added you.")
        cta, note = "Set your password", expiry
        reason = f"Sent because {inviter} added you as an admin for {company}."
    elif role == "title_rep":
        subject = f"{company_name} set up a seat for you on TrendyReports"
        headline = f"{company} set up a seat for you."
        lead = (f"You&rsquo;ll invite your agents and see when their reports go out. "
                f"{company}&rsquo;s logo and colour are already on your account; you add your "
                f"photo and contact line.")
        cta, note = "Accept the invite", expiry
    elif role == "affiliate_admin":
        subject = f"{inviter_name} invited you to TrendyReports"
        headline = f"{inviter} invited you to TrendyReports."
        lead = "You&rsquo;ll invite agents and see when their reports go out."
        cta, note = "Accept the invite", expiry
    else:  # sponsored_agent, and any role without its own wording
        subject = f"{inviter_name} invited you to TrendyReports"
        headline = f"{inviter} invited you to TrendyReports."
        plan = _plan_sentence("sponsored_free")
        lead = ("Your own account: live MLS market reports for your area, with your name and photo on every page."
                + (f" Your plan includes {plan}." if plan else ""))
        cta = "Accept the invite"
        note = f"{expiry} Don&rsquo;t know {inviter}? Ignore this and nothing happens."

    content = _h1(headline) + _p(lead) + _cta_button(invite_url, cta) + _note(note)
    return _send(email, subject, content, preheader=lead, reason=reason, category="invite")


def send_rep_change_notice_email(
    email: str,
    *,
    first_name: str,
    company_name: str,
    new_rep_name: str,
    new_rep_email: str,
) -> Dict[str, Any]:
    """Tell an agent who their rep is now, after a seat reassignment.

    Without it the agent starts getting email from a stranger. Reassignment
    moves the sponsor and leaves the plan alone, which is what it says.
    """
    company = _e(company_name or "your title company")
    rep = _e(new_rep_name)
    content = (
        _h1(f"Your rep at {company} is now {rep}.")
        + _p(f"You can reach them at {_link('mailto:' + (new_rep_email or ''), _e(new_rep_email))}. "
             "Nothing about your account changes: your reports, schedules and plan stay as they are.")
    )
    return _send(email, f"Your rep at {company_name or 'your title company'} is now {new_rep_name}",
                 content, preheader=f"Your rep at {company} is now {rep}.",
                 reason=f"Sent because {company} moved your account to a new rep.",
                 category="rep-change")


# ============ Password Reset ============

def _reset_content(reset_url: str, by_admin: bool) -> str:
    if by_admin:
        lead = ("A TrendyReports administrator sent you this link to choose a new password. "
                "Your reports and schedules aren&rsquo;t affected.")
        note = (f"Expires in {_ttl_words(ADMIN_RESET_LINK_TTL)}. "
                "Your current password keeps working until you choose a new one.")
    else:
        lead = "Use the link below to choose a new one. Your reports and schedules aren&rsquo;t affected."
        note = (f"Expires in {_ttl_words(RESET_LINK_TTL)}. "
                "Didn&rsquo;t ask? Your password is unchanged &mdash; you can ignore this.")
    return (_h1("Reset your password.") + _p(lead)
            + _cta_button(reset_url, "Choose a new password") + _note(note))


def _reset_reason(by_admin: bool) -> str:
    return ("Sent because a TrendyReports administrator reset the password for this address."
            if by_admin else "Sent because someone asked to reset the password for this address.")


def get_password_reset_email_html(user_name: str, reset_url: str, *, by_admin: bool = False) -> str:
    return _email_base(_reset_content(reset_url, by_admin),
                       preheader="Choose a new password.", reason=_reset_reason(by_admin))


def get_password_reset_email_text(user_name: str, reset_url: str, *, by_admin: bool = False) -> str:
    return _plain(_reset_content(reset_url, by_admin))


def send_password_reset_email(email: str, user_name: str, reset_token: str, *,
                              by_admin: bool = False) -> Dict[str, Any]:
    """`by_admin`: a platform admin sent it, and the link lasts
    ADMIN_RESET_LINK_TTL instead of RESET_LINK_TTL."""
    reset_url = f"{email_service.app_base}/reset-password?token={reset_token}"
    return _send(email, "Reset your password — TrendyReports", _reset_content(reset_url, by_admin),
                 preheader="Choose a new password.", reason=_reset_reason(by_admin),
                 category="password-reset")


# ============ Plan Limit Notifications ============
#
# Only reports you make count toward the monthly market-report limit; reports
# your schedules make do not (services/usage.get_usage_counts). Past the limit
# there is a 10% grace (usage.grace_ceiling); beyond it new reports are refused
# AND any scheduled send that comes due is skipped by the ticker, not sent
# later. The count resets on the 1st.

def _plan_line(plan_name: Optional[str], limit: int, reset: date) -> str:
    return _note(f"{_e(plan_name) + ' · ' if plan_name else ''}{limit} market reports a month · "
                 f"resets {_month_day(reset)}")


def send_limit_warning_email(email: str, first_name: str, count: int, limit: int, *,
                             plan_name: Optional[str] = None) -> Dict[str, Any]:
    """At 80% of the month's market reports."""
    reset = _next_reset()
    left = max(limit - count, 0)
    headline = f"{count} of {limit} reports used this month."
    lead = (f"{left} left until {_month_day(reset)}. Reports your schedules make "
            "don&rsquo;t count toward this.")
    content = (
        _h1(headline) + _p(lead) + _plan_line(plan_name, limit, reset)
        + _cta_button(f"{email_service.app_base}/app/settings/billing", "See plans")
        + _note("Nothing changes unless you change it.")
    )
    return _send(email, f"{count} of {limit} reports used this month", content, preheader=lead,
                 reason="Sent once a month, when you pass 80% of your monthly reports.",
                 category="limit-warning")


def send_limit_reached_email(email: str, first_name: str, limit: int, *,
                             count: Optional[int] = None,
                             plan_name: Optional[str] = None) -> Dict[str, Any]:
    """At 100% of the month's market reports."""
    from .usage import grace_ceiling
    reset = _next_reset()
    used = limit if count is None else count
    extra = max(grace_ceiling(limit) - used, 0)
    headline = f"You&rsquo;ve used all {limit} reports this month."
    after = (f"After {'that' if extra else 'this'}, new reports pause until {_month_day(reset)}, "
             "and any scheduled send that comes due before then is skipped, not sent later. "
             "Nothing is deleted; schedules pick up again on the 1st.")
    lead = ((f"You can make {extra} more while you decide. " if extra else "") + after)
    content = (
        _h1(headline) + _p(lead) + _plan_line(plan_name, limit, reset)
        + _cta_button(f"{email_service.app_base}/app/settings/billing", "See plans")
        + _note("Upgrading lifts the limit as soon as the new plan is active. "
                "Sends skipped before then aren&rsquo;t re-sent.")
    )
    return _send(email, f"You've used all {limit} reports this month", content, preheader=lead,
                 reason="Sent once a month, when you reach your monthly limit.",
                 category="limit-reached")


# ============ Welcome / Onboarding Emails ============

def _run_city_step(last: bool = False) -> str:
    return _step_row(1, "Run your city", "Pick a city and a report type, and watch it fill in.",
                     "/app/reports/new", "Create a report", last=last)


def send_regular_agent_welcome_email(to_email: str, first_name: str) -> Dict[str, Any]:
    """Self-registered agent, after confirming their email."""
    free_limit = _plan_market_limit("free")   # D-308: from the plan, never typed
    lead = "Pick a city. We pull its latest sales from the MLS and put your name on it."
    content = (
        _h1("Let&rsquo;s make your first report.")
        + _p(lead)
        + _steps([
            _run_city_step(),
            _step_row(2, "Add your photo and logo", "Once. Your reports and emails carry them.",
                      "/app/settings/branding", "Add your brand"),
            _step_row(3, "Send it on a schedule",
                      "Pick your contacts and how often, and it goes out on its own.",
                      "/app/schedules/new", "Create a schedule", last=True),
        ])
        + _callout((f"<strong>Your Free plan</strong> includes {free_limit} market reports a month. Need more? "
                    if free_limit else "Need more reports than the Free plan includes? ")
                   + f'<a href="{_e(email_service.app_base)}/app/settings/billing" style="color:#166534;font-weight:600;text-decoration:underline;">See plans</a>.', "green")
        + _cta_button(f"{email_service.app_base}/app/reports/new", "Run my first report")
    )
    return _send(to_email, "Let's make your first report — TrendyReports", content, preheader=lead,
                 reason="Sent once, when your account was ready.", category="welcome-regular")


def send_sponsored_agent_welcome_email(to_email: str, first_name: str, affiliate_company_name: str,
                                       *, rep_name: str = "",
                                       plan_slug: str = "sponsored_free") -> Dict[str, Any]:
    """Agent invited by a rep, after accepting. `affiliate_company_name` is the
    rep's brand name (their company's, copied at invite); `rep_name` the rep's
    own name when known."""
    company = _e(affiliate_company_name or "your title company")
    rep = _e(rep_name.strip()) if (rep_name or "").strip() else ""
    plan = _plan_sentence(plan_slug)
    lead = (f"{rep + ' at ' if rep else ''}{company} invited you"
            + (f". Your plan includes {plan}." if plan else "."))
    who = (f"{rep} is your rep: they can see the reports you make and your schedules."
           if rep else f"Your rep at {company} can see the reports you make and your schedules.")
    content = (
        _h1("Your account is ready.")
        + _p(lead)
        + _p(who)
        + _steps([
            _run_city_step(),
            _step_row(2, "Add your photo", "Your name and contact go on every report.",
                      "/app/settings/profile", "Edit profile"),
            _step_row(3, "Import your contacts", "Upload a CSV, or add a few by hand.",
                      "/app/people", "Add contacts", last=True),
        ])
        + _cta_button(f"{email_service.app_base}/app/reports/new", "Run my first report")
    )
    return _send(to_email, "Your TrendyReports account is ready", content, preheader=lead,
                 reason=f"Sent once, when you accepted {rep or company}&rsquo;s invite.",
                 category="welcome-sponsored-agent")


def send_company_admin_welcome_email(to_email: str, first_name: str, company_name: str) -> Dict[str, Any]:
    """Title Company admin, after accepting."""
    company = _e(company_name or "your company")
    lead = ("Two things and the network runs itself: the brand your reps carry, and the reps "
            "who&rsquo;ll invite agents.")
    content = (
        _h1(f"Let&rsquo;s set up {company}.")
        + _p(lead)
        + _steps([
            _step_row(1, "Set the brand", "Logo, colour, name. Your reps&rsquo; accounts carry it; agents keep their own.",
                      "/app/company/branding", "Set the brand"),
            _step_row(2, "Invite your reps", "One seat each. They invite the agents.",
                      "/app/company/reps", "Invite reps"),
            _step_row(3, "Watch the dashboard", "Reps, agents sending, reports this month.",
                      "/app/company", "Open the dashboard", last=True),
        ])
        + _cta_button(f"{email_service.app_base}/app/company/branding", "Set the brand")
    )
    return _send(to_email, f"Let's set up {company_name or 'your company'} — TrendyReports", content,
                 preheader=lead, reason="Sent once, when your admin account was created.",
                 category="welcome-company-admin")


def _agent_invite_sentence() -> str:
    plan = _plan_sentence("sponsored_free", whose="their")
    return ("Each agent you invite gets their own account."
            + (f" Their plan includes {plan}." if plan else "")
            + " You&rsquo;ll see when they send and when they go quiet.")


def send_rep_welcome_email(to_email: str, first_name: str, company_name: str) -> Dict[str, Any]:
    """Title rep under a company, after accepting."""
    company = _e(company_name or "your company")
    lead = _agent_invite_sentence()
    content = (
        _h1("Start inviting your agents.")
        + _p(lead)
        + _steps([
            _step_row(1, "Add your photo and contact line",
                      f"{company}&rsquo;s logo and colour are already on your account.",
                      "/app/settings/profile", "Edit profile"),
            _step_row(2, "Invite an agent", "One at a time, or upload a CSV for a whole office.",
                      "/app/affiliate", "Invite agents"),
            _step_row(3, "Check back in a week", "My agents shows who has joined and who hasn&rsquo;t sent anything yet.",
                      "/app/affiliate", "Open My agents", last=True),
        ])
        + _cta_button(f"{email_service.app_base}/app/affiliate", "Invite my first agent")
    )
    return _send(to_email, "Start inviting your agents — TrendyReports", content, preheader=lead,
                 reason="Sent once, when you accepted the invite.", category="welcome-rep")


def send_affiliate_welcome_email(to_email: str, first_name: str) -> Dict[str, Any]:
    """Independent affiliate (no company), after accepting."""
    lead = _agent_invite_sentence()
    content = (
        _h1("Start inviting your agents.")
        + _p(lead)
        + _steps([
            _step_row(1, "Invite an agent", "One at a time, or upload a CSV for a whole office.",
                      "/app/affiliate", "Invite agents"),
            _step_row(2, "Add your photo and contact line", "They go on the reports you send.",
                      "/app/settings/branding", "Add your brand"),
            _step_row(3, "Check back in a week", "My agents shows who has joined and who hasn&rsquo;t sent anything yet.",
                      "/app/affiliate", "Open My agents", last=True),
        ])
        + _cta_button(f"{email_service.app_base}/app/affiliate", "Invite my first agent")
    )
    return _send(to_email, "Start inviting your agents — TrendyReports", content, preheader=lead,
                 reason="Sent once, when you accepted the invite.", category="welcome-affiliate")
