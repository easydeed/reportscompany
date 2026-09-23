"""
D-057 — the inventory email quotes a price, and it is the right kind of price.

WHAT WAS WRONG
--------------
`build_inventory_result` emitted three metrics — `median_dom`,
`months_of_inventory`, `new_this_month` — and no price. The email's insight
paragraph reads

    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")

got None from both, and rendered, on **every** inventory email:

    "…at a median of varying prices."

A price clause with no price, in a report where every listing carries a
`list_price` the builder already reads.

THE POPULATION MATTERS
----------------------
The sentence is "{total_active} active listings at a median of {price}", and
`total_active` in the email payload is `counts["Active"]` — `len(active)`, the
DATE-FILTERED population the listings table shows, not the total inventory the
months-of-supply numerator uses. The median has to be over the same set. A
median over one population beside a count of another is D-056's mistake with
different numbers.

AND WHY THERE IS NO `median_close_price`
----------------------------------------
This report now fetches closed listings (D-056's work), so a close price is
computable. It is deliberately not emitted.

`_get_insight_paragraph` picks the price by PRECEDENCE — close, else list —
and applies that to sentences that disagree about which kind they want:

    market_snapshot:  "{n} homes SOLD at a median of {price}"      → close
    inventory:        "{n} ACTIVE LISTINGS at a median of {price}" → list
    new_listings:     "with a median ASKING price of {price}"      → list

Every report renders correctly today **only because of which metrics each
builder happens to emit**. Adding a correct `median_close_price` here would
silently turn this report's asking sentence into a sale price — a metric in one
file changing the meaning of prose in another. That coupling is D-085; the test
below pins the absence so the change fails loudly instead of reading well.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.report_builders import build_inventory_result  # noqa: E402
from worker.email.template import _get_insight_paragraph  # noqa: E402

NOW = datetime.now()


def active(price, days_ago_listed=5, dom=10):
    return {
        "status": "Active",
        "city": "Glendora",
        "list_price": price,
        "days_on_market": dom,
        "list_date": NOW - timedelta(days=days_ago_listed),
    }


def closed(price, days_ago_closed=10):
    return {
        "status": "Closed",
        "city": "Glendora",
        "close_price": price,
        "list_price": price,
        "days_on_market": 30,
        "close_date": NOW - timedelta(days=days_ago_closed),
        "list_date": NOW - timedelta(days=days_ago_closed + 30),
    }


def build(listings, **ctx):
    context = {"city": "Glendora", "lookback_days": 30}
    context.update(ctx)
    return build_inventory_result(listings, context)


# ── the price exists, and it is the median of the right set ─────────────────

def test_the_inventory_report_emits_a_median_price(build_=build):
    """THE REGRESSION. Three metrics and no price, on every inventory email."""
    result = build_([active(400_000), active(500_000), active(600_000)])
    assert result["metrics"].get("median_list_price") == 500_000, (
        "the builder emits no median price, so the email says 'varying prices'"
    )


def test_the_median_is_over_the_same_set_the_count_beside_it_describes():
    """
    `counts["Active"]` is the DATE-FILTERED population. A listing outside the
    lookback window is in the fetch but not in that count — and must not be in
    the median either, or the sentence pairs a count of one population with a
    median of another.
    """
    listings = [
        active(400_000, days_ago_listed=5),
        active(500_000, days_ago_listed=5),
        active(600_000, days_ago_listed=5),
        # outside the 30-day window: excluded from the count, so excluded here
        active(9_000_000, days_ago_listed=400),
    ]
    result = build(listings, lookback_days=30)
    assert result["counts"]["Active"] == 3
    assert result["metrics"]["median_list_price"] == 500_000, (
        "a listing outside the lookback window moved the median, so the median "
        "and the count beside it describe different populations"
    )


def test_a_listing_with_no_price_does_not_break_the_median():
    result = build([active(400_000), active(None), active(600_000)])
    assert result["metrics"]["median_list_price"] == 500_000


def test_no_priced_listings_leaves_it_none_rather_than_zero():
    """
    None, not 0. Zero is a price; "we have none to report" is not. The template
    guards on truthiness and says "varying prices", which is the honest output
    when it is actually true.
    """
    result = build([active(None), active(None)])
    assert result["metrics"]["median_list_price"] is None


# ── the sentence the metric feeds ───────────────────────────────────────────

def insight(metrics, report_type="inventory"):
    # The real signature (template.py:1670). The first version of this helper
    # passed `listings=[]`, which that function does not take — a reminder that
    # a call written from memory is a call that has not been made.
    return _get_insight_paragraph(
        report_type=report_type,
        area="Glendora",
        metrics=metrics,
        lookback_days=30,
    )


def test_the_email_stops_saying_varying_prices():
    """
    End to end through the real paragraph builder: the builder's metrics, the
    email payload's aliasing, the sentence.
    """
    result = build([active(400_000), active(500_000), active(600_000)])
    metrics = dict(result["metrics"])
    metrics["total_active"] = result["counts"]["Active"]
    metrics["total_closed"] = result["counts"]["Closed"]
    metrics.setdefault("avg_dom", metrics.get("median_dom"))

    text = insight(metrics)
    assert "varying prices" not in text, text
    assert "$500" in text or "500,000" in text or "500K" in text, (
        f"the median price does not appear in the paragraph: {text}"
    )


def test_no_price_is_invented_when_there_is_genuinely_no_price():
    """
    RESTATED 2026-09-23, DELIBERATELY. This test used to assert the literal
    string "varying prices", which was the fallback at the time. D-085's fix
    changed the mechanism: a sentence whose price is missing now DROPS the price
    clause rather than substituting a stand-in phrase, so the paragraph reads
    "There are 2 active listings in Glendora right now." instead of "…at a
    median of varying prices."

    The assertion is rewritten against the test's own stated purpose — *"naming
    something anyway would be the inventing-a-figure mistake this fix exists to
    avoid"* — rather than against the wording that happened to implement it. The
    new behaviour satisfies that purpose more completely: it names nothing at
    all, and it also cannot produce the borrowed-price failure D-085 describes.

    Recorded at this length because rewriting a test to match new behaviour is
    exactly how a guard gets quietly removed, and the distinction between that
    and this is the argument above, not the diff.
    """
    result = build([active(None), active(None)])
    metrics = dict(result["metrics"])
    metrics["total_active"] = result["counts"]["Active"]
    metrics["total_closed"] = result["counts"]["Closed"]
    text = insight(metrics)

    assert "$" not in text, f"a price appeared from a priceless report: {text}"
    assert "None" not in text
    # and the sentence still reads as a sentence
    assert "  " not in text and " ." not in text, repr(text)
    assert text.strip().endswith(".")
    assert str(result["counts"]["Active"]) in text, (
        "the count is still reported; only the price clause goes"
    )


# ── the coupling this fix must not trip ─────────────────────────────────────

def test_the_inventory_builder_does_not_emit_a_close_price():
    """
    THE GUARD, AND THE REASON IT LOOKS ODD.

    Adding `median_close_price` here would be a correct metric — this report
    fetches closed listings now — and it would silently change what the
    inventory email SAYS. `_get_insight_paragraph` picks close-price-first for
    every report type, and this report's sentence is about ASKING prices:

        "{n} active listings at a median of {price}"

    So a well-meant addition in this file would make that sentence name the
    price of homes that already sold. Nothing would fail; the email would just
    become wrong.

    Pinned here rather than argued in a comment, because a comment does not
    fail. See D-085 for the underlying coupling.
    """
    result = build(
        [active(400_000), active(500_000), closed(300_000), closed(320_000)]
    )
    assert "median_close_price" not in result["metrics"], (
        "build_inventory_result now emits median_close_price. The insight "
        "paragraph prefers it over median_list_price for EVERY report type, so "
        "this report's 'active listings at a median of…' sentence would start "
        "quoting a sale price. Fix the template's precedence first (D-085)."
    )


def test_the_sentence_names_asking_prices_not_sale_prices():
    """
    The property the guard above protects, stated as behaviour: with both
    active and closed listings present, the paragraph must quote the ASKING
    median.
    """
    result = build([active(400_000), active(500_000), closed(300_000), closed(320_000)])
    metrics = dict(result["metrics"])
    metrics["total_active"] = result["counts"]["Active"]
    metrics["total_closed"] = result["counts"]["Closed"]

    text = insight(metrics)
    assert "450" in text or "$450" in text, (
        f"expected the asking median (450,000) in the paragraph: {text}"
    )
    assert "310" not in text, (
        f"the paragraph quoted a figure derived from closed sales: {text}"
    )
