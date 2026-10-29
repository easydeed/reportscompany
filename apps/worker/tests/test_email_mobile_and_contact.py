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
    """
    THE REGRESSION. `.metric-card` was defined and applied to nothing. Since
    Design's 5th package the strip's stacking class is `tr-stack`; the check is
    the same join — every four-across cell carries the class that stacks it.
    """
    html = render(report_type)
    cells = re.findall(r'<td\b[^>]*width="25%"[^>]*>', html)
    if not cells:
        pytest.skip("this layout renders no four-across metric strip")
    unstackable = [c for c in cells if "tr-stack" not in c]
    assert not unstackable, (
        f"{len(unstackable)} of {len(cells)} strip cells carry no .tr-stack, so the "
        f"rule that stacks the strip on a phone can never reach them"
    )


def test_no_responsive_rule_is_defined_and_unused():
    """
    The general form. A rule attached to nothing is invisible in review — both
    files read correctly — and it is only the join that is missing.

    Every `tr-*` rule, the dark-mode ones included: a dark rule with no element
    is a colour that never changes, which is the failure the dark gate exists
    for. No exemptions; add one by name, with a reason, if a rule is genuinely
    conditional on content no fixture here produces.
    """
    EXEMPT = set()
    # Across every document the product renders, not one: a rule is dead only
    # if NOTHING uses it anywhere.
    defined, used = set(), set()
    for rt in REPORT_TYPES:
        for listings in (None, LISTINGS):
            html = render(rt, listings=listings)
            defined |= {c for c in defined_classes(html) if c.startswith("tr-")}
            used |= used_classes(html)
    assert defined, "no tr-* rule found at all — the check is reading the wrong thing"
    dead = sorted(defined - used - EXEMPT)
    assert not dead, f"rules attached to nothing in any document: {dead}"


@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_the_stacking_rule_is_still_in_the_stylesheet(report_type):
    """
    The other half. Attaching the class to a cell achieves nothing if the media
    query is removed, and the pair is what has to hold.
    """
    html = render(report_type)
    assert "@media only screen and (max-width:620px)" in html
    assert re.search(r"\.tr-stack\s*\{[^}]*display:\s*block", html), (
        "no rule makes .tr-stack stack"
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
