"""
Untrusted strings must not become markup in a sent email.

THE DEFECT THIS EXISTS TO PREVENT (D-058)
-----------------------------------------
`email/template.py` had no escaping of any kind. It is ~2,500 lines of Python
f-strings with no template engine, so there was no autoescape to switch on, and
every untrusted value was interpolated raw into markup and into attribute
values. Confirmed by render, four ways, before the fix:

    rep_name  = "Dana <b>Ortiz</b>"            -> rendered as bold markup
    rep_title = "…<a href='evil'>prize</a>…"   -> rendered as a LIVE anchor
    display_name = 'Acme" onmouseover="x'      -> broke out of alt="…"
    rep_email = 'd@e.test" style="display:none'-> broke out of the mailto href

The exposure is not browser XSS — mail clients strip <script> and there is no
session to steal. It is a live attacker-authored link inside mail that carries
*someone else's* brand: `_resolve_email_brand` (tasks.py:439-447) inherits a
parent company's branding into a sub-account's sends while letting the
sub-account override contact_line1/2.

WHY THE FIX IS AT THE BOUNDARY, AND WHY THESE TESTS ARE SHAPED THIS WAY
-----------------------------------------------------------------------
Escaping at the ~460 interpolation sites would mean ~460 correct judgements
about which of two categories each site is in, because ~50 of them insert HTML
fragments the module itself built — escaping those renders markup as visible
text. So the inputs are sanitised once, on entry, and everything downstream is
clean by construction.

The tests therefore assert on the *rendered output* for each input channel
rather than on any internal helper, and they include the fragment cases
(test_rendered_markup_is_not_double_escaped) that a per-site fix would break.

THREE CHANNELS, NOT ONE
-----------------------
The ticket was filed from `rep_title`. The map found three:

  brand      user-editable, via profile and branding settings
  listings   SimplyRETS. VENDOR data — injection needs one bad MLS record and
             no malicious account at all. This is the channel nobody was
             looking at.
  arguments  account_name, city, preset/filter/audience labels

URLs ARE A SEPARATE PROBLEM
---------------------------
html.escape("javascript:alert(1)") is a no-op and the value stays live in an
href. Those fields are scheme-allowlisted instead, by safe_url().
"""
import os

import pytest

os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")

from worker.email.template import (  # noqa: E402
    schedule_email_html,
    _UNSUB_URL_SENTINEL,
)
from worker.property_builder import safe_url  # noqa: E402


# Payloads that would be live markup if interpolated raw.
MARKUP = '</p><a href="https://evil.test">Claim your prize</a><p>'
ATTR_BREAK = 'Acme" onmouseover="alert(1)'
IMG_BREAK = 'https://cdn.example.test/a.jpg" onerror="alert(1)'

BRAND = {
    "display_name": "Marisol Ridge Realty",
    "rep_name": "Dana Ortiz",
    "rep_title": "Broker Associate",
    "rep_photo_url": "https://assets.example.test/dana.jpg",
    "rep_phone": "(626) 555-0134",
    "rep_email": "dana@example.test",
    "website_url": "https://marisolridge.example.test",
}

LISTING = {
    "street_address": "123 Foothill Blvd",
    "city": "La Verne",
    "zip_code": "91750",
    "status": "Active",
    "list_price": 825000,
    "close_price": 812000,
    "bedrooms": 3,
    "bathrooms": 2,
    "sqft": 1800,
    "days_on_market": 12,
    "hero_photo_url": "https://cdn.example.test/1.jpg",
}


def _render(report_type="market_snapshot", brand=None, listings=None, **over):
    kwargs = dict(
        account_name="Marisol Ridge Realty",
        report_type=report_type,
        city="La Verne",
        zip_codes=None,
        lookback_days=30,
        metrics={
            "total_active": 42, "total_closed": 18, "months_of_inventory": 2.3,
            "median_list_price": 825000, "median_close_price": 812000,
            "avg_dom": 24, "total_listings": 1,
        },
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a" * 64,
        brand=brand if brand is not None else BRAND,
        listings=listings,
        preset_display_name=None,
        filter_description=None,
        sender_type="REGULAR",
        total_found=50,
        total_shown=8,
    )
    kwargs.update(over)
    return schedule_email_html(**kwargs)


def _assert_not_live(html, payload=MARKUP):
    """
    The payload may appear escaped — that is the point — but never as
    functioning markup.

    Asserted on the unescaped forms specifically. `onmouseover=` survives
    escaping as `onmouseover=&quot;…`, which is inert text; asserting the bare
    substring is absent would fail on correctly-escaped output and prove
    nothing. What matters is that no raw `<` opens a tag and no raw `"` closes
    an attribute.
    """
    assert '<a href="https://evil.test">' not in html
    assert '" onmouseover=' not in html
    assert '" onerror=' not in html
    assert payload not in html


# ── channel 1: brand (user-editable) ────────────────────────────────────────

@pytest.mark.parametrize(
    "field",
    ["display_name", "rep_name", "rep_title", "rep_phone", "rep_email",
     "contact_line1", "contact_line2"],
)
def test_brand_text_fields_cannot_inject_markup(field):
    """rep_title is the one the ticket was filed from; the rest are the map."""
    html = _render(brand={**BRAND, field: f"Broker{MARKUP}"})
    _assert_not_live(html)


@pytest.mark.parametrize("field", ["display_name", "rep_name", "rep_email"])
def test_brand_text_fields_cannot_break_out_of_an_attribute(field):
    """
    Most interpolation sites in this module sit inside attr="…", where a bare
    double quote is what breaks out — which is why _esc uses quote=True.
    """
    html = _render(brand={**BRAND, field: ATTR_BREAK})
    assert ATTR_BREAK not in html
    assert '" onmouseover=' not in html


# ── channel 2: listings (SimplyRETS — vendor data) ──────────────────────────

@pytest.mark.parametrize("field", ["street_address", "city", "status", "zip_code"])
def test_vendor_listing_fields_cannot_inject_markup(field):
    """
    The channel that needs no malicious account: one bad MLS record.

    `status` is carried here as a forward guard rather than a demonstration:
    the gallery card does not render it today, so this case passes against the
    unfixed module too. It is kept so the field is covered the day a card
    starts showing it.
    """
    html = _render(
        report_type="new_listings_gallery",
        listings=[{**LISTING, field: f"123 Main{MARKUP}"}],
    )
    _assert_not_live(html)


def test_vendor_photo_url_cannot_break_out_of_the_src_attribute():
    html = _render(
        report_type="new_listings_gallery",
        listings=[{**LISTING, "hero_photo_url": IMG_BREAK}],
    )
    assert '" onerror=' not in html
    assert "alert(1)" not in html


def test_listing_numerics_survive_sanitisation():
    """
    Numeric fields must NOT be escaped — they are formatted with numeric specs
    (f"{price:,.0f}"), which a str would break. This is the assertion that
    catches an over-broad sanitiser.
    """
    html = _render(report_type="new_listings_gallery", listings=[LISTING])
    assert "825,000" in html or "825K" in html or "$825" in html


# ── channel 3: top-level arguments ──────────────────────────────────────────

@pytest.mark.parametrize(
    "kwarg",
    ["account_name", "city", "preset_display_name", "filter_description"],
)
def test_top_level_arguments_cannot_inject_markup(kwarg):
    """
    `brand` is emptied deliberately. brand_name resolves as
    `brand["display_name"] or account_name`, so passing a brand with a
    display_name shadows account_name entirely and the case would pass without
    ever rendering the payload — which is exactly what the first version of
    this test did.
    """
    html = _render(brand={}, **{kwarg: f"La Verne{MARKUP}"})
    _assert_not_live(html)


# ── URLs: a scheme problem, not an escaping problem ─────────────────────────

@pytest.mark.parametrize(
    "field",
    ["website_url", "logo_url", "email_logo_url", "rep_photo_url"],
)
def test_javascript_urls_are_dropped_not_escaped(field):
    """
    html.escape() leaves `javascript:` intact and the href stays live. These
    fields are allowlisted by scheme instead.
    """
    html = _render(brand={**BRAND, field: "javascript:alert(document.domain)"})
    assert "javascript:" not in html


@pytest.mark.parametrize(
    "value,allowed",
    [
        ("https://example.test/a.png", True),
        ("http://example.test/a.png", True),
        ("//cdn.example.test/a.png", True),
        ("/local/a.png", True),
        ("javascript:alert(1)", False),
        ("JaVaScRiPt:alert(1)", False),
        ("java\tscript:alert(1)", False),
        ("data:text/html;base64,PHNjcmlwdD4=", False),
        ("vbscript:msgbox(1)", False),
        ("", False),
        (None, False),
        (12345, False),
    ],
)
def test_safe_url_allowlist(value, allowed):
    result = safe_url(value)
    assert bool(result) is allowed
    if allowed:
        assert result == value.strip()


def test_a_legitimate_url_still_reaches_the_email():
    """
    The allowlist must not break the normal case.

    rep_photo_url is dropped deliberately: website_url renders only in the
    no-headshot footer branch, so asserting it against a brand with a photo
    would have been testing the wrong branch.
    """
    brand = {k: v for k, v in BRAND.items() if k != "rep_photo_url"}
    html = _render(brand={**brand, "website_url": "https://marisolridge.example.test"})
    assert "https://marisolridge.example.test" in html


# ── the boundary must not damage what it protects ───────────────────────────

def test_rendered_markup_is_not_double_escaped():
    """
    The module builds ~50 HTML fragments and interpolates them. Sanitising at
    the boundary keeps those clean; escaping at the sites would render them as
    visible text. This asserts the document is still real markup.
    """
    html = _render(report_type="new_listings_gallery", listings=[LISTING])
    assert "<html" in html.lower()
    assert "&lt;table" not in html
    assert "&lt;a href" not in html
    assert "&lt;div" not in html


def test_the_unsubscribe_sentinel_survives_the_boundary():
    """
    THE BUG THIS CAUGHT: the sentinel is not a URL, so scheme-allowlisting it
    stripped it. send.py then found nothing to substitute per recipient and its
    guard (send.py:233) aborts the send — every email, not just a malicious
    one. The boundary must pass the sentinel through untouched.
    """
    html = _render(unsubscribe_url=_UNSUB_URL_SENTINEL)
    assert _UNSUB_URL_SENTINEL in html


def test_a_real_unsubscribe_url_survives_the_boundary():
    token = "a" * 64
    html = _render(unsubscribe_url=f"https://app.example.test/unsub?token={token}")
    assert f"https://app.example.test/unsub?token={token}" in html, (
        "the query string was mangled — a URL must be scheme-checked, not escaped"
    )


def test_apostrophes_in_ordinary_names_are_not_mangled_into_entities():
    """
    Real names contain apostrophes and ampersands. They must render as the
    character, not as a visible entity, in the delivered email.
    """
    html = _render(brand={**BRAND, "rep_name": "Erin O'Brien", "display_name": "Smith & Co"})
    assert "O&#x27;Brien" in html or "O'Brien" in html
    assert "Smith &amp; Co" in html or "Smith & Co" in html
    assert "O&amp;#x27;Brien" not in html, "double-escaped"
