"""
A brand colour that is not a hex triple must not stop the email.

THE DEFECT THIS EXISTS TO PREVENT (D-060)
-----------------------------------------
`schedule_email_html` calls `compute_color_roles(accent_color, dark_bg=primary_color)`
unconditionally, before any HTML is produced. That reaches `_hex_to_rgb`
(`property_builder.py`), which does `int(h[i:i+2], 16)` and raised:

    ValueError: invalid literal for int() with base 16: 'rr'

on the value "red". The exception propagated out of `schedule_email_html` into
`send_schedule_email` and the email was never sent — the same failure path as
D-055. Combined with D-033 (no failure notification when RESEND_API_KEY is
unset), one settings save silently and permanently stopped all delivery on the
account, and the owner would find out when a client asked why the reports
stopped.

This is not a malformed-input edge case. "red" is what a person types into a
field labelled colour. Two of the write paths accepted it as a bare `str`.

WHY THE GUARD COERCES RATHER THAN PASSES THROUGH
------------------------------------------------
These values are also interpolated directly into ~48 `style="…"` attributes in
the email. Letting a non-hex string through to "let CSS deal with it" would
trade the crash for a CSS-injection — `red; background: url(https://evil/…)`
is a tracking pixel, and a value containing a quote breaks out of the attribute
entirely. So anything that is not a 3- or 6-digit hex becomes the fallback, and
the tests below assert the bad value does not reach the output.
"""
import os

import pytest

os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")

from worker.email.template import schedule_email_html  # noqa: E402
from worker.property_builder import (  # noqa: E402
    compute_color_roles,
    normalize_hex_color,
)


# Values reachable today. The first four are what a person plausibly types; the
# rest are what an attacker would, given the columns accept any string.
BAD_COLORS = [
    "red",
    "blue",
    "rgb(255, 0, 0)",
    "",
    "   ",
    "#12",
    "#gggggg",
    "1B365D",                                   # hex, but missing the "#"
    '#fff" onload="alert(1)',                   # breaks out of the attribute
    "red; background: url(https://evil.test/t.gif)",  # CSS injection
    None,
]

GOOD_COLORS = ["#fff", "#FFF", "#1b365d", "#1B365D", "  #1b365d  "]


def _render(brand, report_type="market_snapshot"):
    return schedule_email_html(
        account_name="Marisol Ridge Realty",
        report_type=report_type,
        city="La Verne",
        zip_codes=None,
        lookback_days=30,
        metrics={
            "total_active": 42,
            "total_closed": 18,
            "months_of_inventory": 2.3,
            "median_list_price": 825000,
            "avg_dom": 24,
        },
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


# ── the crash ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", BAD_COLORS)
def test_bad_accent_color_does_not_stop_the_send(bad):
    """`accent_color` is the first argument to compute_color_roles."""
    html = _render({"display_name": "Marisol Ridge Realty", "accent_color": bad})
    assert html and "<html" in html.lower()


@pytest.mark.parametrize("bad", BAD_COLORS)
def test_bad_primary_color_does_not_stop_the_send(bad):
    """`primary_color` reaches it as dark_bg, and raised just as readily."""
    html = _render({"display_name": "Marisol Ridge Realty", "primary_color": bad})
    assert html and "<html" in html.lower()


def test_both_colors_bad_at_once():
    html = _render(
        {"display_name": "Marisol Ridge Realty", "accent_color": "red", "primary_color": "blue"}
    )
    assert html and "<html" in html.lower()


@pytest.mark.parametrize("bad", BAD_COLORS)
def test_compute_color_roles_never_raises(bad):
    """The guard lives deep enough to protect the two PDF callers too."""
    roles = compute_color_roles(bad, dark_bg=bad)
    assert set(roles) >= {"theme_color", "theme_color_light", "theme_color_dark"}


# ── the coercion, not just the survival ─────────────────────────────────────

@pytest.mark.parametrize(
    "bad",
    ['#fff" onload="alert(1)', "red; background: url(https://evil.test/t.gif)"],
)
def test_bad_color_does_not_reach_the_output(bad):
    """
    Surviving the render is not enough — the value must not land in a style
    attribute. This is the assertion that would fail if the guard were relaxed
    to "pass it through and let CSS decide".
    """
    html = _render({"display_name": "Marisol Ridge Realty", "accent_color": bad, "primary_color": bad})
    assert bad not in html
    assert "onload=" not in html
    assert "evil.test" not in html


@pytest.mark.parametrize("bad", BAD_COLORS)
def test_every_returned_role_is_a_real_hex(bad):
    """
    theme_color must agree with the roles derived from it. Coercing only the
    derived values would echo the bad input back through theme_color.
    """
    for name, value in compute_color_roles(bad, dark_bg=bad).items():
        assert isinstance(value, str) and value.startswith("#"), (name, value)
        assert len(value) in (4, 7), (name, value)
        int(value.lstrip("#"), 16)  # parses as hex


# ── good values are untouched ───────────────────────────────────────────────

@pytest.mark.parametrize("good", GOOD_COLORS)
def test_valid_colors_are_preserved(good):
    """The guard must not quietly replace colours that were always fine."""
    assert normalize_hex_color(good) == good.strip()


def test_a_valid_brand_color_still_reaches_the_email():
    html = _render({"display_name": "Marisol Ridge Realty", "accent_color": "#1b365d"})
    assert "#1b365d" in html
