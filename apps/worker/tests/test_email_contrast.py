"""
Workstream C — no text in a rendered email is unreadable against its own
background.

THE MEASUREMENT THAT MOTIVATED THIS
-----------------------------------
Before this pass, across seven brands and eight report types:

    1,167 unreadable text runs out of 3,822 measured

The worst was not subtle. `_build_quick_take` took the label colour and the
panel colour as two independent arguments with nothing relating them, so an
account that sets ONE brand colour rather than two rendered

    #dc2626 on #dc2626   1.00:1   — invisible

and the master plan's B3, recorded at 1.4:1 from a sample render, was the same
bug with two different brand values in it.

WHY A WALKER RATHER THAN THIRTY ASSERTIONS
------------------------------------------
Thirty assertions cover thirty sites and miss the thirty-first. `_contrast_audit`
resolves the actual background for every text run — inline styles, nearest
ancestor, gradients measured at each stop, rgba flattened over the backdrop —
and asserts the property. It covers the sites nobody has written yet.

Its own correctness is pinned below by a positive and a negative control, per
§0.6: *a detector's silence means nothing until you have seen it speak.* The
walker also reports how many runs it declined to judge, because "no findings"
and "nothing was looked at" are the same output otherwise.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from _contrast_audit import audit, coverage, flatten  # noqa: E402
from worker.email.template import schedule_email_html  # noqa: E402
from worker.themes import contrast  # noqa: E402

REPORT_TYPES = [
    "market_snapshot", "new_listings", "inventory", "closed",
    "price_bands", "open_houses", "new_listings_gallery", "featured_listings",
]

#: The six themes the master plan measured, plus the unbranded case — which is
#: the most common account and was the LAST thing still failing, because the
#: email's own default (#6366f1) sits inside D-098's unreachable band.
BRANDS = [
    ("demo_title", "#DC2626"),
    ("luxury_estates", "#0D9488"),
    ("coastal", "#0E7490"),
    ("amber", "#F59E0B"),
    ("lime", "#84CC16"),
    ("violet", "#7C3AED"),
    ("no_brand_set", None),
]

METRICS = {
    "total_active": 42, "total_closed": 18, "months_of_inventory": 2.3,
    "median_list_price": 825000, "median_close_price": 812000,
    "avg_dom": 24, "new_listings_7d": 11, "sale_to_list_ratio": 0.982,
}

LISTINGS = [
    {"street_address": f"{i} Oak St", "city": "La Verne",
     "list_price": 800000 + i * 1000, "close_price": 790000 + i * 1000,
     "bedrooms": 3, "bathrooms": 2, "sqft": 1800,
     "photo_url": "https://assets.example.test/p.jpg",
     "status": "Active", "days_on_market": i}
    for i in range(1, 9)
]


def render(report_type, primary):
    brand = {
        "display_name": "Marisol Ridge Realty", "rep_name": "Dana Ortiz",
        "rep_title": "Broker Associate", "rep_phone": "(626) 555-0134",
        "rep_email": "dana@example.test",
        "website_url": "https://marisolridge.example.test",
    }
    if primary:
        brand["primary_color"] = primary
        brand["accent_color"] = primary
    return schedule_email_html(
        account_name="Marisol Ridge Realty", report_type=report_type,
        city="La Verne", zip_codes=None, lookback_days=30, metrics=METRICS,
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a" * 64,
        brand=brand, listings=LISTINGS, sender_type="REGULAR",
        total_found=50, total_shown=8,
    )


# ---------------------------------------------------------------------------
# The controls. Without these, everything below is worthless.
# ---------------------------------------------------------------------------

def test_the_walker_reports_a_failure_when_there_is_one():
    """POSITIVE CONTROL — the exact defect this workstream fixed."""
    found = audit('<td style="background:#0d9488"><p style="color:#8b5cf6">Quick Take</p></td>')
    assert len(found) == 1
    assert round(found[0].ratio, 2) == 1.13


def test_the_walker_is_silent_when_there_is_not():
    """NEGATIVE CONTROL — it must be able to return nothing."""
    assert audit('<td style="background:#ffffff"><p style="color:#111827">Readable</p></td>') == []


def test_the_walker_inherits_the_nearest_ancestor_background():
    html = ('<table style="background:#ffffff"><tr>'
            '<td style="background:#0d9488"><p style="color:#ffffff">on the fill</p></td>'
            '</tr></table>')
    found = audit(html)
    assert [f.bg for f in found] == ["#0d9488"], "measured against the page, not the cell"


def test_the_walker_measures_both_ends_of_a_gradient():
    """
    The masthead is a gradient. Text on it has to survive the whole band, and a
    check against the first stop alone is how #ffffff at 1.98:1 on the lime end
    went unnoticed.
    """
    html = ('<td style="background: linear-gradient(115deg, #18235c 0%, #84cc16 100%)">'
            '<p style="color:#ffffff">Market Snapshot</p></td>')
    ratios = sorted(round(f.ratio, 2) for f in audit(html))
    assert ratios == [1.98], "only the failing stop should be reported"


def test_rgba_text_is_flattened_over_its_backdrop():
    assert flatten("rgba(255,255,255,0.7)", "#dc2626") == "#f4bebe"
    found = audit('<td style="background:#dc2626"><p style="color:rgba(255,255,255,0.7)">Last 30 Days</p></td>')
    assert round(found[0].ratio, 2) == 2.98


# ---------------------------------------------------------------------------
# The property
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("brand_name,primary", BRANDS)
@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_every_text_run_clears_aa(brand_name, primary, report_type):
    html = render(report_type, primary)
    bad = audit(html)
    assert not bad, (
        f"{brand_name} / {report_type}: {len(bad)} unreadable text run(s). "
        + "; ".join(str(f) for f in bad[:4])
    )


@pytest.mark.parametrize("report_type", REPORT_TYPES)
def test_the_audit_is_actually_looking_at_something(report_type):
    """
    THE COVERAGE GUARD. `test_every_text_run_clears_aa` passes trivially if the
    walker measures nothing — a broken parser and a clean document produce the
    same empty list. This pins that the document really is being read.
    """
    measured, declined = coverage(render(report_type, "#0D9488"))
    # Measured 2026-09-23: 54 (the two gallery layouts) to 95 (closed,
    # inventory). The floor is set well under the smallest real document and
    # well over what a broken parser returns, which is ~0.
    assert measured >= 40, f"only {measured} text runs measured — is the walker parsing?"
    assert declined == 0, (
        f"{declined} text runs could not be resolved, so the clean result above "
        f"covers less than the whole document"
    )


# ---------------------------------------------------------------------------
# The specific defects, pinned by name
# ---------------------------------------------------------------------------

def test_the_quick_take_label_is_not_invisible():
    """
    B3, and the worst of it: when an account sets one brand colour rather than
    two, `accent_color == primary_color` and the label was painted on itself.
    A property test over random brands can generate two different colours
    forever and never produce this.
    """
    from worker.email.template import _build_quick_take
    for brand in ("#dc2626", "#0d9488", "#f59e0b", "#84cc16", "#7c3aed", "#0e7490"):
        html = _build_quick_take("Market summary.", brand, brand)
        bad = audit(html)
        assert not bad, f"{brand}: {[str(f) for f in bad]}"


def test_the_unsubscribe_link_is_legible():
    """
    D-060's follow-up raised the postal address from #9ca3af (2.41:1 on the
    #f8f9fa footer) to #6b7280, and left the unsubscribe link it had used as the
    EXAMPLE of what failing looks like at 2.41:1. CAN-SPAM asks for the opt-out
    to be clear and conspicuous on the same "clearly and conspicuously" wording
    that drove the address.
    """
    html = render("market_snapshot", "#0D9488")
    assert 'color: #9ca3af' not in html, "the 2.41:1 grey is back in the footer"
    assert contrast("#6b7280", "#f8f9fa") >= 4.5


def test_white_is_not_hardcoded_onto_a_brand_fill():
    """
    The structural version: a brand colour may be a fill, but the text on it is
    derived. Asserted on the rendered document rather than the source, because
    the source has legitimate `#ffffff` fills.
    """
    for brand in ("#84CC16", "#F59E0B"):
        for rt in ("market_snapshot", "closed"):
            bad = [f for f in audit(render(rt, brand)) if f.fg == "#ffffff"]
            assert not bad, f"{brand}/{rt}: white text left on a brand fill: {[str(f) for f in bad[:3]]}"


@pytest.mark.parametrize("status,expect_hex", [
    ("Sold", "#dc2626"),
    ("Active", "#15803d"),
    ("Pending", "#b45309"),
])
def test_every_status_badge_carries_readable_text(status, expect_hex):
    """
    §3.3 — status colours are reserved, never drawn from the brand, and always
    paired with a text label. They are therefore literals, and the literals were
    chosen for brightness rather than for the white text sitting on them:

        #16a34a  white on it  3.30:1
        #f59e0b  white on it  2.15:1

    ADDED BECAUSE THE DIFFERENTIAL RUN FOUND NOTHING. Reverting the green to
    #16a34a broke no test: the render fixture gives every listing a
    `close_price`, so the badge is always "Sold" and the Active and Pending
    branches were never reached. A palette three values wide was being checked
    one value deep.
    """
    from worker.email.template import _build_photo_card_with_badge
    listing = {"street_address": "1 Oak St", "city": "La Verne",
               "list_price": 800000, "photo_url": "https://x.test/p.jpg"}
    html = _build_photo_card_with_badge(listing, "#0d9488", "#0d9488", status)
    assert expect_hex in html.lower(), f"{status} badge is not {expect_hex}"
    bad = audit(html)
    assert not bad, f"{status}: {[str(f) for f in bad]}"


def test_the_sales_table_status_badges_are_readable():
    """The same palette, reached through the other builder that draws it."""
    from worker.email.template import _build_sales_table
    for status in ("Sold", "Active", "Pending"):
        rows = [{"street_address": "1 Oak St", "list_price": 800000,
                 "bedrooms": 3, "bathrooms": 2, "sqft": 1800,
                 "status": status, "days_on_market": 4}]
        bad = audit(_build_sales_table(rows, "#0d9488", "#0d9488"))
        assert not bad, f"{status}: {[str(f) for f in bad]}"


def test_the_email_default_matches_the_rest_of_the_product():
    """
    The email defaulted to #6366f1 while templates.ts and social-templates.ts
    both default to #4F46E5 — so an unbranded account's PDF and its email were
    different colours. #6366f1 is also inside D-098's unreachable band (4.47:1),
    which made the default the one brand that could not be made readable.
    """
    html = render("market_snapshot", None)
    assert "#6366f1" not in html.lower()
    assert "4f46e5" in html.lower()
