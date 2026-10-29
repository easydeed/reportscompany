"""The home-value email: the one a person gets after asking a lead page what
their home is worth. Design's 5th package, markup in
`templates/email/home_value.jinja2` (whose header lists every departure).

Pure: values in, HTML out. `tasks.process_consumer_report` gathers the values
and sends; this decides nothing about delivery.

NO ESTIMATE IN THE EMAIL (owner decision, 2026-10-28). Nothing passed in here
can carry one: there is no parameter for it. The number stays in the report,
beside the sales it comes from.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from worker.email.template import (
    PLATFORM_POSTAL_ADDRESS, PLATFORM_SENDER_LABEL, _initials, _tel_uri, _today, _tokens,
)
from worker.property_builder import normalize_hex_color, safe_url

#: Autoescaped, unlike the market blocks' `_BLOCK_ENV`: nothing passed to this
#: template is markup, so every value — the requester's own name, the address
#: they typed, the agent's profile fields — is escaped exactly once, here.
_ENV = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parents[1] / "templates" / "email")),
    autoescape=True,
    trim_blocks=True,
)

#: The viewer's tabs (apps/web/components/mobile-report/MobileReportViewer.tsx),
#: described by what each shows. Not Design's list: that promised "what we
#: corrected" in the county record, which the report does not do.
WHATS_INSIDE = (
    ("Your home", "the details on record: beds, baths, size, lot and year built."),
    ("Nearby sales", "the comparable sales, each with its price and distance from you."),
    ("Your market", "prices, price per square foot and how fast homes are selling nearby."),
)

#: The account's colour when it has none, the same default as the market email.
DEFAULT_PRIMARY = "#4f46e5"


def home_value_email_html(
    *,
    report_url: str,
    address: str,
    city: Optional[str],
    requester_first_name: Optional[str],
    agent_name: str,
    agent_title: Optional[str] = None,
    company_name: Optional[str] = None,
    agent_phone: Optional[str] = None,
    agent_email: Optional[str] = None,
    agent_photo_url: Optional[str] = None,
    primary_color: Optional[str] = None,
    logo_url: Optional[str] = None,
    postal_address: Optional[str] = None,
) -> str:
    tk = _tokens(normalize_hex_color(primary_color, DEFAULT_PRIMARY))
    brand_name = (company_name or "").strip() or agent_name
    agent_first = (agent_name or "").split(" ")[0] or "Your agent"

    phone_href = _tel_uri(agent_phone)
    buttons = []
    if phone_href:
        buttons.append((phone_href, f"Call {agent_phone}"))
        # sms: takes the number without the extension.
        buttons.append(("sms:" + phone_href[4:].split(";")[0], "Text"))
    if agent_email:
        buttons.append((f"mailto:{agent_email}", agent_email))

    # The same attribution rule as the market email (template.py): the
    # account's own address beside its own name, or ours beside ours.
    postal = (postal_address or "").strip()
    postal_line = (f"{brand_name} · {postal}" if postal else
                   f"{PLATFORM_SENDER_LABEL} · {PLATFORM_POSTAL_ADDRESS} · on behalf of {agent_name}")

    as_of = _today().strftime("%B %-d, %Y")
    return _ENV.get_template("home_value.jinja2").render(
        primary=tk["primary"], on_primary=tk["on_primary"], dark_ink=tk["dark_ink"],
        brand_name=brand_name, logo_url=safe_url(logo_url) or None,
        date_label=as_of,
        address=address, address_line=f"{address}, {city}" if city else address,
        first_name=(requester_first_name or "").strip() or None,
        report_url=safe_url(report_url),
        inside=WHATS_INSIDE,
        agent_name=agent_name, agent_first=agent_first,
        title_line=" · ".join(x for x in (agent_title, company_name) if x),
        photo_url=safe_url(agent_photo_url) or None, initials=_initials(agent_name),
        buttons=buttons, phone=agent_phone, phone_href=phone_href,
        postal_line=postal_line,
        preheader=f"Your report on {address} is ready.",
    )
