"""
Every commercial email carries a physical postal address, attributed to
whoever it actually belongs to.

CAN-SPAM 15 U.S.C. §7704(a)(5) requires the valid physical postal address of
the sender, or of the person who initiated the message, in every commercial
email. Every email this product has ever sent shipped without one. The render
slot was built in #49 and collapsed to nothing because there was nowhere to
store a value — no postal-address column on `accounts`, none on
`affiliate_branding`, none anywhere in the schema (D-060).

THE ATTRIBUTION IS THE PART WORTH TESTING
-----------------------------------------
The footer line reads "<name> • <address>", so a naive fallback would print the
AFFILIATE'S brand beside TRENDYREPORTS' address — saying that business is
located somewhere it is not. The original TODO warned about precisely this,
about a guessed value; it arrives the same way through a fallback. A wrong
address is a worse compliance posture than a missing one, because it is an
affirmative false statement rather than an omission.

So the label travels with the value:

    account set its own     "<their brand> • <their address>"
    falling back            "Sent by TrendyReports • <platform address>"

Both satisfy the statute. Neither claims an address for a business that does
not have it.

EVERY TYPE IS RENDERED, NOT SAMPLED
-----------------------------------
The slot sits in a block shared by all eight report emails, which is an
argument, not evidence — §0.6 rule 3. Each type is rendered and searched.
"""
import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "apps" / "worker" / "src"))

from worker.email.template import (  # noqa: E402
    PLATFORM_POSTAL_ADDRESS,
    PLATFORM_SENDER_LABEL,
    schedule_email_html,
)
from worker.market_builder import ALL_REPORT_TYPES  # noqa: E402

OWN_ADDRESS = "9 Affiliate Way, Irvine, CA 92602"
ACCOUNT_BRAND = "Acme Realty"

_METRICS = {
    "median_list_price": 900000, "median_close_price": 880000, "avg_dom": 22,
    "months_of_inventory": 5.2, "total_active": 120, "new_listings_count": 8,
    "close_to_list_ratio": 99.1, "median_dom": 20,
}
_LISTINGS = [{
    "street_address": "1 Main St", "city": "Irvine", "list_price": 900000,
    "status": "Active", "beds": 3, "baths": 2, "sqft": 1800, "zip_code": "92602",
}]


def _render(report_type, brand):
    return schedule_email_html(
        account_name=ACCOUNT_BRAND,
        report_type=report_type,
        city="Irvine",
        zip_codes=None,
        lookback_days=30,
        metrics=_METRICS,
        pdf_url="https://example.test/r.pdf",
        unsubscribe_url="https://example.test/u?t=x",
        brand=brand,
        listings=_LISTINGS,
    )


def test_there_are_eight_report_types_and_this_file_covers_all_of_them():
    """
    The parametrised tests below take their list from the source of truth
    rather than a copy. If a ninth type is added they cover it automatically —
    but if that list is ever narrowed, this notices.
    """
    assert len(ALL_REPORT_TYPES) == 8, (
        f"expected eight report types, found {len(ALL_REPORT_TYPES)}: "
        f"{sorted(ALL_REPORT_TYPES)}"
    )


# ── the address is present, on every type ───────────────────────────────────

@pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
def test_an_account_without_its_own_address_still_sends_a_compliant_email(report_type):
    """
    THE URGENT HALF. No account has set an address — the column is new and
    nothing writes to it yet — so this is the path every email takes today.
    """
    html = _render(report_type, {"display_name": ACCOUNT_BRAND})
    assert PLATFORM_POSTAL_ADDRESS in html, (
        f"{report_type}: no postal address in the email at all — this is the "
        f"CAN-SPAM omission D-060 exists to close"
    )
    assert PLATFORM_SENDER_LABEL in html


@pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
def test_an_account_with_its_own_address_sends_that_one(report_type):
    html = _render(report_type, {"display_name": ACCOUNT_BRAND, "postal_address": OWN_ADDRESS})
    assert OWN_ADDRESS in html, f"{report_type}: the account's own address did not render"


# ── attribution, which is the part that can be wrong while looking right ────

@pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
def test_the_platform_address_never_wears_the_accounts_brand(report_type):
    """
    THE FAILURE THIS DESIGN EXISTS TO PREVENT. "Acme Realty • 440 Rte. 66,
    Glendora, CA 91740" asserts that Acme Realty is located at an address that
    belongs to someone else. A naive `or` in the fallback produces exactly that
    and looks entirely reasonable in review.
    """
    html = _render(report_type, {"display_name": ACCOUNT_BRAND})
    assert f"{ACCOUNT_BRAND} &bull; {PLATFORM_POSTAL_ADDRESS}" not in html, (
        f"{report_type}: the platform's address is attributed to {ACCOUNT_BRAND}"
    )
    assert f"{PLATFORM_SENDER_LABEL} &bull; {PLATFORM_POSTAL_ADDRESS}" in html, (
        f"{report_type}: the fallback does not say whose address it is"
    )


@pytest.mark.parametrize("report_type", ALL_REPORT_TYPES)
def test_an_override_does_not_also_print_the_platform_address(report_type):
    """
    Two addresses in one footer is not more compliant, it is ambiguous about
    who sent the message.
    """
    html = _render(report_type, {"display_name": ACCOUNT_BRAND, "postal_address": OWN_ADDRESS})
    assert PLATFORM_POSTAL_ADDRESS not in html, (
        f"{report_type}: both the account's address and the platform's rendered"
    )
    assert f"{ACCOUNT_BRAND} &bull; {OWN_ADDRESS}" in html


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_a_blank_stored_address_falls_back_rather_than_rendering_an_empty_line(blank):
    """
    An account that opens the settings field and saves it empty must not end up
    with a footer reading "Acme Realty • " — which is both non-compliant and
    visibly broken. Whitespace-only is the case that slipped past `or` in D-067.
    """
    html = _render("market_snapshot", {"display_name": ACCOUNT_BRAND, "postal_address": blank})
    assert PLATFORM_POSTAL_ADDRESS in html
    assert f"{ACCOUNT_BRAND} &bull; </p>" not in html


# ── the value itself ────────────────────────────────────────────────────────

def test_the_platform_address_is_not_a_placeholder():
    """
    The whole reason this sat gated: a guessed address is worse than none. If
    someone ever swaps the constant for scaffolding, that must not ship
    quietly to every recipient.
    """
    lowered = PLATFORM_POSTAL_ADDRESS.lower()
    for smell in ("todo", "tbd", "xxx", "placeholder", "your address",
                  "123 main", "123 market street", "example", "changeme"):
        assert smell not in lowered, (
            f"the platform postal address looks like a placeholder: "
            f"{PLATFORM_POSTAL_ADDRESS!r}"
        )
    # Street number, some words, a two-letter state and a ZIP. Loose on
    # purpose — an address format assertion that is too strict is a guard that
    # refuses a legitimate address (§0.6), and this one only has to catch
    # scaffolding.
    assert re.search(r"\d+.*\b[A-Z]{2}\b\s+\d{5}", PLATFORM_POSTAL_ADDRESS), (
        f"{PLATFORM_POSTAL_ADDRESS!r} does not look like a US postal address"
    )


def test_the_environment_can_override_it_but_a_blank_variable_cannot_empty_it():
    """
    The office can move without a deploy. A typo'd config value must not
    silently restore the non-compliant state this entry exists to end.
    """
    import importlib
    import worker.email.template as tpl

    os.environ["PLATFORM_POSTAL_ADDRESS"] = "1 New Office Rd, Pasadena, CA 91101"
    try:
        reloaded = importlib.reload(tpl)
        assert reloaded.PLATFORM_POSTAL_ADDRESS == "1 New Office Rd, Pasadena, CA 91101"

        os.environ["PLATFORM_POSTAL_ADDRESS"] = "   "
        reloaded = importlib.reload(tpl)
        assert reloaded.PLATFORM_POSTAL_ADDRESS, (
            "a blank environment variable emptied the postal address, which is "
            "the non-compliant state"
        )
    finally:
        os.environ.pop("PLATFORM_POSTAL_ADDRESS", None)
        importlib.reload(tpl)


# ── one address, three surfaces ─────────────────────────────────────────────

@pytest.mark.parametrize("page", ["terms", "privacy"])
def test_the_legal_pages_carry_the_same_address_as_the_email_footer(page):
    """
    G3 put this address on the legal pages on 2026-08-27 — it was in the
    repository the whole time D-060 was blocked on "the value".

    Three surfaces now assert where this business is, and they are edited by
    different people at different times. Two of them disagreeing is the kind of
    thing nobody notices until a title company doing vendor diligence does.
    """
    source = (REPO / "apps" / "web" / "app" / page / "page.tsx").read_text()
    assert PLATFORM_POSTAL_ADDRESS in source, (
        f"the {page} page and the email footer give different addresses for "
        f"the same company; the footer says {PLATFORM_POSTAL_ADDRESS!r}"
    )
