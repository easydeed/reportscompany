"""
The email insight paragraph must not crash on a metrics dict that is missing
optional keys.

THE DEFECT THIS EXISTS TO PREVENT
---------------------------------
`_get_insight_paragraph()` builds its fallback prose with branches shaped like:

    if moi and moi < 3:    ... f"{moi:.1f} months of inventory"
    elif moi and moi > 6:  ... f"{moi:.1f} months of inventory"
    else:                  ... f"{moi:.1f} months of inventory"   # <-- moi is falsy HERE

The `else` branch is reached *precisely when* `moi` is falsy. When
`months_of_inventory` is absent from the metrics dict, `moi` is None and the
format spec raises:

    TypeError: unsupported format string passed to NoneType.__format__

That exception propagates: `_get_insight_paragraph` -> `schedule_email_html`
(template.py:1930) -> `send_schedule_email` (email/send.py). The email is never
sent. Combined with D-033 (schedule failure notifications do not fire when
RESEND_API_KEY is unset) the visible result is a schedule that silently stops
delivering, with nobody notified.

`_get_quick_take()` in the same module has the identical branch shape and gets
it right — its `else` does not format `moi` — which is why this is a defect
rather than a design choice.

WHY THE TEST RENDERS RATHER THAN INSPECTS
-----------------------------------------
The bug is a runtime formatting error, invisible to import-time checks and to
any assertion about the source text. It only appears when the template is
actually rendered with the degraded input, so that is what these tests do —
through the real `schedule_email_html`, for every report type the generator
supports, against several shapes of incomplete metrics.

The parametrisation is deliberately wider than the two known crash sites: it
renders every report type against every degraded dict, so a `None`-format
landmine anywhere else in the fallback surfaces here rather than in a customer's
inbox.
"""
import os

import pytest

# Must be set before importing the template module: the AI path is gated on this
# at import time in ai_insights.py, and an enabled path would reach OpenAI.
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")

from worker.email.template import schedule_email_html, _get_insight_paragraph  # noqa: E402


# The eight report types the email generator supports
# (scripts/gen_email_templates.py REPORT_TYPES).
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

# A fully-populated dict, as compute/calc.py:24-35 produces it.
FULL_METRICS = {
    "total_active": 42,
    "total_pending": 6,
    "total_closed": 18,
    "new_listings_7d": 9,
    "median_list_price": 825000,
    "median_close_price": 812000,
    "avg_dom": 24,
    "avg_price_per_sqft": 487,
    "close_to_list_ratio": 99.2,
    "months_of_inventory": 2.3,
    "absorption_rate": 42.8,
    "total_listings": 50,
}

DEGRADED_METRICS = {
    # The case that actually crashed: no months_of_inventory at all.
    "no_moi": {k: v for k, v in FULL_METRICS.items() if k != "months_of_inventory"},
    # Explicit None — what market_builder.py:295 writes when the key is absent
    # upstream (`metrics.get("months_of_inventory")`).
    "moi_none": {**FULL_METRICS, "months_of_inventory": None},
    # moi present but falsy. 0.0 formats fine, so this must NOT crash either —
    # it is the case that proves the fix guards on None, not on falsiness alone.
    "moi_zero": {**FULL_METRICS, "months_of_inventory": 0},
    # Nothing at all: every optional key missing.
    "empty": {},
    # Only the counts, as a bare-bones generator might supply.
    "counts_only": {"total_active": 42, "total_closed": 18},
}


def _render(report_type, metrics):
    """Render through the real production entry point."""
    return schedule_email_html(
        account_name="Marisol Ridge Realty",
        report_type=report_type,
        city="La Verne",
        zip_codes=None,
        lookback_days=30,
        metrics=metrics,
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a" * 64,
        brand=None,
        listings=None,
        preset_display_name=None,
        filter_description=None,
        sender_type="REGULAR",
        total_found=50,
        total_shown=8,
    )


@pytest.mark.parametrize("report_type", REPORT_TYPES)
@pytest.mark.parametrize("shape", sorted(DEGRADED_METRICS))
def test_render_survives_incomplete_metrics(report_type, shape):
    """
    Every report type must render with incomplete metrics.

    Fails before the fix on market_snapshot/no_moi, market_snapshot/moi_none,
    market_snapshot/empty, market_snapshot/counts_only and the same four for
    inventory — TypeError from template.py:1556 and :1591.
    """
    html = _render(report_type, DEGRADED_METRICS[shape])
    assert html, f"{report_type}/{shape} rendered empty"
    assert "<html" in html.lower()


@pytest.mark.parametrize("report_type", ["market_snapshot", "inventory"])
def test_insight_paragraph_directly_without_moi(report_type):
    """
    The two branches that carried the defect, exercised directly.

    These are the only two report types whose fallback prose formats
    months_of_inventory, and both did it in the `else` branch reached when the
    value is falsy.
    """
    text = _get_insight_paragraph(
        report_type=report_type,
        area="La Verne",
        metrics={k: v for k, v in FULL_METRICS.items() if k != "months_of_inventory"},
        lookback_days=30,
        filter_description=None,
        sender_type="REGULAR",
        total_found=50,
        total_shown=8,
        audience_name=None,
    )
    assert text, f"{report_type} produced no insight text"
    # The prose must not claim an inventory figure it does not have.
    assert "None" not in text, f"{report_type} leaked a None into customer-facing copy: {text!r}"
    assert "months of inventory" not in text or any(
        ch.isdigit() for ch in text
    ), "an inventory claim was made with no number behind it"


@pytest.mark.parametrize("report_type", ["market_snapshot", "inventory"])
def test_moi_zero_renders_the_figure_and_does_not_crash(report_type):
    """
    Guard on None, NOT on falsiness — for the format spec only.

    moi == 0 is falsy but formattable, so it must reach the copy as "0.0" rather
    than being suppressed. This is the case that proves the guard tests
    `is not None`: a truthiness guard would silently drop a real figure.

    Deliberately NOT asserted here: which branch moi == 0 lands in. Routing it
    to the seller's-market branch reads correct in the abstract — zero months of
    inventory is as tight as a market gets — but 0 is a *sentinel* in this
    codebase, not a reading. build_inventory_result (report_builders.py:468)
    emits 0.0 when there are NO closed sales, build_market_snapshot_result:150
    emits 99.9 for the same condition, and 6 of the 8 sample report types ship
    moi = 0 meaning "not modelled". Until that disagreement is resolved, routing
    zero anywhere confident is a guess. See DEFECT_LIST.
    """
    text = _get_insight_paragraph(
        report_type=report_type,
        area="La Verne",
        metrics={**FULL_METRICS, "months_of_inventory": 0},
        lookback_days=30,
        filter_description=None,
        sender_type="REGULAR",
        total_found=50,
        total_shown=8,
        audience_name=None,
    )
    assert "0.0 months" in text, (
        "moi=0 should render as a figure, not be treated as missing: " + repr(text)
    )
    assert "None" not in text
