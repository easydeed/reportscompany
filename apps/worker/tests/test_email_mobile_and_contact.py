"""
B4 and B23 — a CSS class applied to nothing, and a link that hides its own value.

B4: `.mobile-stack`, `.metric-card` and `.band-row` were defined inside the
document's `<style>` block and attached to **zero elements**. The media query
was correct and unreachable, so the four-across metric strip stayed four-across
at 320px and its 10px labels wrapped to three lines. The master plan calls it
the highest-impact single fix given the mobile open share; it is one attribute.

The interesting part is that nothing could have caught it by reading either
file. The CSS is right. The HTML is right. Only the pair is wrong, which is why
the check below renders the document and looks for the join.

B23: the agent's email pill was a `mailto:` link whose text was the word
"Email". The phone pill beside it showed the number, so the inconsistency was
visible in the same row. A recipient who wanted to write from another client,
or simply to see who sent this, could not find the address anywhere.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.email.template import schedule_email_html  # noqa: E402

REPORT_TYPES = ["market_snapshot", "new_listings", "inventory", "closed",
                "price_bands", "open_houses", "new_listings_gallery", "featured_listings"]

METRICS = {"total_active": 42, "total_closed": 18, "months_of_inventory": 2.3,
           "median_list_price": 825000, "median_close_price": 812000, "avg_dom": 24}
BRAND = {"display_name": "Marisol Ridge Realty", "rep_name": "Dana Ortiz",
         "rep_title": "Broker Associate", "rep_phone": "(626) 555-0134",
         "rep_email": "dana@example.test", "primary_color": "#0d9488"}


LISTINGS = [
    {"street_address": f"{i} Oak St", "city": "La Verne", "list_price": 800000 + i * 1000,
     "close_price": 790000 + i * 1000, "bedrooms": 3, "bathrooms": 2, "sqft": 1800,
     "photo_url": "https://assets.example.test/p.jpg", "status": "Active",
     "days_on_market": i}
    for i in range(1, 9)
]


def render(report_type="market_snapshot", brand=None, listings=None):
    return schedule_email_html(
        account_name="Marisol Ridge Realty", report_type=report_type, city="La Verne",
        zip_codes=None, lookback_days=30, metrics=METRICS,
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a" * 64,
        brand=BRAND if brand is None else brand, listings=listings,
        sender_type="REGULAR", total_found=50, total_shown=8)


def defined_classes(html):
    """Class names the document's <style> block writes a rule for."""
    style = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    return set(re.findall(r"\.([a-zA-Z][\w-]*)\s*\{", style))


def used_classes(html):
    body = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S)
    out = set()
    for attr in re.findall(r'class="([^"]+)"', body):
        out.update(attr.split())
    return out


# ---------------------------------------------------------------------------
# B4
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_the_metric_strip_can_actually_stack(report_type):
    """THE REGRESSION. `.metric-card` defined, applied to nothing."""
    html = render(report_type)
    # `.metric-card` is declared in the shared <style> block on every layout, so
    # its presence there says nothing. The strip itself is the four 25% cells.
    if 'width="25%"' not in html:
        pytest.skip("this layout renders no four-across metric strip")
    assert "metric-card" in used_classes(html), (
        "the .metric-card rule that stacks the four-across strip on a phone is "
        "defined and attached to no element, so it can never fire"
    )


def test_no_responsive_rule_is_defined_and_unused():
    """
    The general form. A mobile rule attached to nothing is invisible in review —
    both files read correctly — and it is only the join that is missing.

    `.mobile-hide` and `.mobile-center` are exempt: they are legitimately
    conditional on content this fixture does not produce. Named individually
    rather than pattern-matched, so a new dead rule is not quietly covered by
    the exemption.
    """
    # `.mobile-hide` and `.mobile-center` are legitimately conditional on
    # content this fixture does not produce. `.band-row` is dead: the price-band
    # rows are single-cell and have nothing to stack, so the rule describes a
    # layout that no longer exists — recorded on the register rather than given
    # an element to make the check pass.
    EXEMPT = {"mobile-hide", "mobile-center", "band-row", "dark-border"}
    # Across every document the product renders, not one — `.mobile-stack`
    # belongs to the card grids and a snapshot without listings has no cards.
    # A rule is dead only if NOTHING uses it anywhere.
    defined, used = set(), set()
    for rt in REPORT_TYPES:
        for listings in (None, LISTINGS):
            html = render(rt, listings=listings)
            defined |= {c for c in defined_classes(html)
                        if c.startswith(("mobile", "metric", "band"))}
            used |= used_classes(html)
    dead = sorted(defined - used - EXEMPT)
    assert not dead, f"responsive rules attached to nothing in any document: {dead}"


@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_the_stacking_rule_is_still_in_the_stylesheet(report_type):
    """
    The other half. Attaching the class to a cell achieves nothing if the media
    query is removed, and the pair is what has to hold.
    """
    html = render(report_type)
    assert "@media only screen and (max-width: 600px)" in html
    if "metric-card" in used_classes(html):
        assert re.search(r"\.metric-card\s*\{[^}]*display:\s*block", html), (
            "cells carry .metric-card but no rule makes it stack"
        )


# ---------------------------------------------------------------------------
# B23
# ---------------------------------------------------------------------------

def test_the_agent_email_address_is_shown_not_the_word_email():
    html = render()
    assert "dana@example.test" in html, "the address appears nowhere in the document"
    assert not re.search(r">\s*Email\s*<", html), 'the pill still renders the word "Email"'


def test_the_email_pill_is_still_a_mailto_link():
    """Showing the address must not cost the tap target."""
    html = render()
    assert 'href="mailto:dana@example.test"' in html


def test_no_email_pill_when_there_is_no_address():
    html = render(brand={k: v for k, v in BRAND.items() if k != "rep_email"})
    assert "mailto:" not in html
    assert not re.search(r">\s*Email\s*<", html)


def test_realtor_is_not_used_generically():
    """
    The other half of B23, closed earlier by D-066 — REALTOR® is a restricted
    NAR mark. Pinned here so the two halves of the register item are checked in
    one place.
    """
    html = render(brand={k: v for k, v in BRAND.items() if k != "rep_title"})
    assert not re.search(r"\bRealtor\b(?!®)", html)
