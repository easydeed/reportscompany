"""
The email footer's links must be real links, and the contact block must not
depend on whether the agent uploaded a headshot.

Covers P1-B tickets B2-B5. Every assertion renders through the real
`schedule_email_html`; none of them inspect source text. That is deliberate —
all four defects are properties of the *output*, and three of the four were
invisible in the sample renders that were reviewed before this pass.

THE DEFECTS THESE EXIST TO PREVENT
----------------------------------
B2  `href="tel:{rep_phone}"` interpolated `users.phone` — an unvalidated
    free-text column — straight into a URI. "(626) 555-0134" became
    `tel:(626) 555-0134`: unescaped spaces and parentheses, which is not a
    valid URI and is where strict parsers drop the link.

B3  "Update Preferences" pointed at `href="#"`. There is no preference centre
    in this product — no route in `api/routes/`, no page in `apps/web/app/` —
    so there was nothing for it to point at. It was also never in the design
    it was translated from (`app/email-templates/layouts/email-footer.tsx`);
    it was invented during translation.

B4  The phone and email pills were inlined into the `rep_photo_url` branch of
    the footer only. An agent who had not uploaded a headshot sent reports
    carrying no phone number and no email address anywhere — a recipient had
    no way to reach them. Two of the three footer branches were affected.

B5  Commercial email must carry the sender's physical postal address
    (CAN-SPAM, 15 U.S.C. §7704(a)(5)). There was no slot for one. The slot is
    what this ticket builds; the value is gated, so the tests here pin the
    behaviour on both sides of that gate — invisible while unset, rendered
    once populated — without asserting any particular address.
"""
import os
import re

import pytest

os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")

from worker.email.template import schedule_email_html, _tel_uri  # noqa: E402


REPORT_TYPES = [
    "market_snapshot",
    "new_listings",
    "inventory",
    "closed",
    "price_bands",
    "open_houses",
    "new_listings_gallery",
    "featured_listings",
]

METRICS = {
    "total_active": 42,
    "total_closed": 18,
    "months_of_inventory": 2.3,
    "median_list_price": 825000,
    "median_close_price": 812000,
    "avg_dom": 24,
}

# A complete brand, as _build_regular_brand (tasks.py:459) assembles one.
BRAND = {
    "display_name": "Marisol Ridge Realty",
    "rep_name": "Dana Ortiz",
    "rep_title": "Broker Associate",
    "rep_photo_url": "https://assets.example.test/dana.jpg",
    "rep_phone": "(626) 555-0134",
    "rep_email": "dana@example.test",
    "website_url": "https://marisolridge.example.test",
}


def _render(brand, report_type="market_snapshot"):
    return schedule_email_html(
        account_name="Marisol Ridge Realty",
        report_type=report_type,
        city="La Verne",
        zip_codes=None,
        lookback_days=30,
        metrics=METRICS,
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a" * 64,
        brand=brand,
        listings=None,
        preset_display_name=None,
        filter_description=None,
        sender_type="REGULAR",
        total_found=50,
        total_shown=8,
    )


# ── B2: tel: URI ────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "entered,expected",
    [
        # The formats the profile UI and real users actually produce.
        ("(626) 555-0134", "tel:+16265550134"),
        ("626-555-0134", "tel:+16265550134"),
        ("626.555.0134", "tel:+16265550134"),
        ("626 555 0134", "tel:+16265550134"),
        ("6265550134", "tel:+16265550134"),
        ("+1 (626) 555-0134", "tel:+16265550134"),
        ("1-626-555-0134", "tel:+16265550134"),
        ("+44 20 7946 0958", "tel:+442079460958"),
        # Extensions must become RFC 3966 ;ext=, NOT be folded into the number.
        # Folding "x12" in yields a 12-digit string that dials someone else —
        # worse than not linking, because it fails silently and plausibly.
        ("626-555-0134 x12", "tel:+16265550134;ext=12"),
        ("626-555-0134 ext 12", "tel:+16265550134;ext=12"),
        ("(626) 555-0134 ext. 7", "tel:+16265550134;ext=7"),
        ("626-555-0134 extension 400", "tel:+16265550134;ext=400"),
    ],
)
def test_tel_uri_normalises_what_agents_type(entered, expected):
    assert _tel_uri(entered) == expected


@pytest.mark.parametrize(
    "entered",
    ["555-0134", "call me", "n/a", "-", "", "   ", None],
)
def test_tel_uri_refuses_what_it_cannot_dial(entered):
    """
    Refusing beats guessing. A 7-digit local number has no resolvable area
    code, and free text has no number at all; emitting `tel:` for either
    produces a link that fails on tap.
    """
    assert _tel_uri(entered) is None


@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_rendered_tel_href_is_a_valid_uri(report_type):
    """
    The rendered href must contain no characters that are invalid in a URI.

    This is the assertion that fails against the pre-fix template: it rendered
    `tel:(626) 555-0134`, and the space alone is disqualifying.
    """
    html = _render(BRAND, report_type)
    hrefs = re.findall(r'href="(tel:[^"]*)"', html)
    assert hrefs, f"{report_type}: no tel: link rendered for a brand with a phone"
    for href in hrefs:
        assert re.fullmatch(r"tel:\+[0-9]+(;ext=[0-9]+)?", href), (
            f"{report_type}: malformed tel: URI {href!r}"
        )


def test_phone_label_is_preserved_while_href_is_normalised():
    """The agent's formatting is for humans; E.164 is for the dialer."""
    html = _render(BRAND)
    assert "(626) 555-0134" in html, "the human-readable number was lost"
    assert 'href="tel:+16265550134"' in html


def test_undialable_phone_renders_as_text_not_as_a_dead_link():
    """A pill styled like a link that goes nowhere is worse than plain text."""
    html = _render({**BRAND, "rep_phone": "call me"})
    assert "call me" in html, "the number the agent entered was dropped entirely"
    assert "tel:" not in html, "a tel: link was emitted for an undialable number"


# ── B3: no dead links ───────────────────────────────────────────────────────

@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_no_dead_anchors_anywhere_in_the_email(report_type):
    """
    `href="#"` in an email is a link that does nothing when tapped. Fails
    before the fix on the footer's "Update Preferences".
    """
    html = _render(BRAND, report_type)
    assert 'href="#"' not in html, f"{report_type}: dead anchor in rendered email"


@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_unsubscribe_link_survives(report_type):
    """B3 removes a link. It must not remove the one that is legally required."""
    html = _render(BRAND, report_type)
    assert "https://app.example.test/unsub?token=" in html
    assert ">Unsubscribe<" in html


# ── B4: the contact block does not depend on a headshot ─────────────────────

@pytest.mark.parametrize(
    "case,brand",
    [
        # Branch 1 of the footer: photo + name.
        ("photo", BRAND),
        # Branch 2: no headshot uploaded. The common case for a new account.
        ("no_photo", {k: v for k, v in BRAND.items() if k != "rep_photo_url"}),
        # Branch 3: company-branded, no rep name and no website.
        (
            "brand_only",
            {
                "display_name": "Marisol Ridge Realty",
                "rep_phone": "(626) 555-0134",
                "rep_email": "dana@example.test",
            },
        ),
    ],
)
def test_contact_details_render_in_every_footer_branch(case, brand):
    """
    Fails before the fix on `no_photo` and `brand_only`: both rendered a footer
    with no phone number and no email address at all.
    """
    html = _render(brand)
    assert 'href="tel:+16265550134"' in html, f"{case}: phone missing from footer"
    assert 'href="mailto:dana@example.test"' in html, f"{case}: email missing from footer"
    assert "(626) 555-0134" in html, f"{case}: phone not shown to the reader"


def test_contact_block_is_absent_when_there_is_nothing_to_show():
    """No contact data must not produce empty pills or a stray container."""
    html = _render({"display_name": "Marisol Ridge Realty"})
    assert "tel:" not in html
    assert "mailto:" not in html


# ── B5: postal address slot (gated) ─────────────────────────────────────────

def test_postal_address_slot_is_invisible_until_populated():
    """
    The value is gated on a business decision, so nothing may appear yet. This
    pins that the slot ships dark rather than shipping a placeholder.

    Asserted against the exact shape the address line emits — "<brand> &bull;
    <address>" — rather than against any bullet in the footer, so that this
    stays a B5 test and does not quietly re-assert B3.
    """
    html = _render(BRAND)
    footer = re.search(r"Powered by.*?</td>", html, re.S).group(0)
    assert "TODO" not in html
    assert "Marisol Ridge Realty &bull;" not in footer, (
        "something was rendered into the address slot"
    )


def test_postal_address_renders_once_supplied():
    """
    The slot must actually work the moment a value exists — otherwise 'built
    the slot' is an untested claim. No real address is asserted here; the point
    is the wiring, not the value.
    """
    html = _render({**BRAND, "postal_address": "1 Example Way, Somewhere, CA 90000"})
    assert "1 Example Way, Somewhere, CA 90000" in html
    assert "Marisol Ridge Realty &bull; 1 Example Way" in html
