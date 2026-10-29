"""The account-email shell, for the one account email the worker sends: the
schedule-failure notice. Design's 5th package.

A MIRROR, ON PURPOSE. The shell and its row helpers live in the API's
`services/email.py`, and the worker does not import the API. So the helpers are
copied here verbatim, and `apps/api/tests/test_transactional_shell.py` compares
the two copies as code — a change to one that is not made to the other fails.
Only `_app_base` differs, because the two apps read it from different places.
"""
from __future__ import annotations

import html
import re
import os
from typing import List, Optional

from worker.email.template import PLATFORM_POSTAL_ADDRESS


def _app_base() -> str:
    """Where the app lives. The one line that differs from the API's copy."""
    return os.environ.get("APP_BASE", "https://reportscompany-web.vercel.app")


_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


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
