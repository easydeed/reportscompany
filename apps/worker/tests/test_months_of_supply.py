"""
One months-of-supply, computed one way, refusing to guess.

THE TICKET, AND WHAT IT TURNED INTO
-----------------------------------
The inventory report's query pinned `status=Active`, so its closed list was
always empty and months of supply was always the `else` branch — `0.0`, which
rendered as a balanced market. That is D-056.

Adding a Closed query is the obvious fix and on its own it produces a wrong
number more convincingly, because the numerator carried a `listDate` window:
"listed in the last 30 days and still active", divided by a full sales rate.
`market_trends.py:98` already had the comment — "NO date filter — we want total
current inventory for MOI calculation" — one report over.

FIVE COPIES, NOT TWO
--------------------
The survey found two formulas. Re-running it after fixing them found four
sites, and a fifth in `market_trends.py`:

    market_trends          active / (closed * 30.437/90)
    market snapshot        active / (closed * 30.437/lookback)
    market snapshot tiers  same again, inline, per price tier
    inventory              (active / closed) * (lookback / 30)      <-- different
                                                                        quantity

The last is not the same metric. It coincides with the others only when the
window happens to be 30.437 days. Two formulas for one number is how D-056's
sentinel came to mean "no data" in one place and "balanced market" in another,
so there is now one implementation and the window is a parameter.

WHAT THESE TESTS DO
-------------------
The arithmetic is exercised directly — it is pure and there is no excuse for
asserting anything about it indirectly. The wiring is checked structurally,
because it needs a vendor and a database to run. Where a claim is about what
reaches the page, the page is rendered.
"""
import ast
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from jinja2 import Environment, DictLoader, select_autoescape

WORKER_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(WORKER_SRC))

from worker.compute.moi import (  # noqa: E402
    AVG_DAYS_PER_MONTH,
    MIN_CLOSED_FOR_MOI,
    PACE_LABEL,
    SALES_RATE_WINDOW_DAYS,
    closed_in_window,
    describe,
    months_of_supply,
)

WORKER = WORKER_SRC / "worker"


# ── the arithmetic ──────────────────────────────────────────────────────────

def test_months_of_supply_is_inventory_over_a_monthly_sales_rate():
    """156 active, 89 sales in 90 days -> 89 * 30.437/90 = 30.1/month -> 5.2."""
    assert months_of_supply(156, 89) == 5.2


def test_the_window_changes_the_rate_and_therefore_the_answer():
    """
    Same counts over a shorter window is a faster pace and less supply. Pinned
    because `window_days` is the parameter that replaced three hard-coded
    values, and a caller passing the wrong one gets a plausible wrong number.
    """
    assert months_of_supply(156, 89, window_days=90) == 5.2
    assert months_of_supply(156, 89, window_days=30) == 1.7


@pytest.mark.parametrize("closed", range(0, MIN_CLOSED_FOR_MOI))
def test_too_few_sales_returns_none_rather_than_a_number(closed):
    """
    In a quiet market two sales versus three moves the answer by a third. The
    old code returned 0.0 here in one place and 99.9 in another, and both
    rendered as measurements.
    """
    assert months_of_supply(500, closed) is None


def test_the_floor_is_the_only_thing_between_us_and_the_old_sentinels():
    """The value at the floor must be a real number, or the floor is a wall."""
    assert months_of_supply(500, MIN_CLOSED_FOR_MOI) is not None


def test_a_truncated_active_fetch_refuses_to_publish():
    """
    A fetch that hit its paging limit returns a FLOOR, not a count. A floor in
    the numerator makes months of supply too LOW, which reads as a hotter
    market than the real one — the direction that would make a seller
    underprice. Refused, not published.
    """
    assert months_of_supply(1000, 89) is not None
    assert months_of_supply(1000, 89, active_was_truncated=True) is None


def test_there_are_no_sentinels_left():
    """
    D-056 was 0.0 meaning 'no data'. 99.9 was the same idea elsewhere. Neither
    may come back: every 'cannot estimate' path returns None.
    """
    for args in [(500, 0), (500, 1), (0, 0), (-1, 50)]:
        result = months_of_supply(*args)
        assert result is None or result >= 0
        assert result not in (99.9, 999.0)


def test_zero_inventory_is_a_real_answer_not_a_missing_one():
    """Nothing for sale and sales happening is genuinely zero months of supply,
    and must not be confused with 'no estimate'."""
    assert months_of_supply(0, 50) == 0.0
    assert describe(0.0)["has_estimate"] is True


# ── the closed window, filtered on close date ───────────────────────────────

def test_closed_in_window_filters_on_close_date_not_list_date():
    """
    D-074's mistake, in miniature: a home listed ten months ago and sold last
    month IS a sale in a 90-day window. Filtering on list date drops it, and
    long-DOM listings are exactly the ones that take that long — so the loss is
    not random and it pushes months of supply up.
    """
    now = datetime(2026, 9, 17)
    long_dom_recent_sale = {
        "list_date": now - timedelta(days=300),
        "close_date": now - timedelta(days=10),
    }
    listed_recently_sold_long_ago = {
        "list_date": now - timedelta(days=5),
        "close_date": now - timedelta(days=200),
    }
    kept = closed_in_window([long_dom_recent_sale, listed_recently_sold_long_ago], now=now)
    assert kept == [long_dom_recent_sale]


def test_a_sale_with_no_close_date_is_not_counted():
    """It cannot be placed in a window whose bounds it does not have."""
    now = datetime(2026, 9, 17)
    assert closed_in_window([{"close_date": None}, {}], now=now) == []


def test_close_dates_are_accepted_as_strings_and_as_aware_datetimes():
    """Both shapes reach this from the extractor depending on the path."""
    now = datetime(2026, 9, 17)
    recent = (now - timedelta(days=5)).isoformat()
    assert len(closed_in_window([{"close_date": recent}], now=now)) == 1
    assert len(closed_in_window([{"close_date": "not a date"}], now=now)) == 0


# ── one implementation, checked by searching for the others ─────────────────

def test_no_module_computes_the_rate_itself():
    """
    §0.6 rule 4, and the reason this test exists at all: the first survey found
    two formulas, the post-fix re-run found four, and a fifth lived in
    market_trends.py. The construct is `<count> * (AVG_DAYS_PER_MONTH / ...)`
    — a monthly sales rate — anywhere outside the module that owns it.
    """
    offenders = []
    for path in sorted(WORKER.rglob("*.py")):
        if path.name == "moi.py":
            continue
        for i, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "AVG_DAYS_PER_MONTH" in stripped:
                offenders.append(f"{path.relative_to(WORKER)}:{i}  {stripped[:70]}")
    assert not offenders, (
        f"the monthly sales rate is computed outside compute/moi.py: {offenders}"
    )


def test_no_module_keeps_its_own_copy_of_the_sentinels():
    """
    `99.9` and `999.0` were the old 'no data' values. Both rendered as
    measurements — 999 months of supply is not a market condition, it is a
    missing denominator.
    """
    offenders = []
    for path in sorted(WORKER.rglob("*.py")):
        if path.name == "moi.py":
            continue
        for i, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or "moi" not in stripped.lower():
                continue
            if "99.9" in stripped or "999.0" in stripped:
                offenders.append(f"{path.relative_to(WORKER)}:{i}  {stripped[:70]}")
    assert not offenders, f"months-of-supply sentinel(s) still present: {offenders}"


def test_both_surfaces_call_the_shared_implementation():
    """
    The requirement in the ticket, asserted rather than promised: the property
    report's gauge and the market reports must compute this the same way.
    """
    for module in ("compute/market_trends.py", "report_builders.py"):
        src = (WORKER / module).read_text()
        assert "months_of_supply" in src, f"{module} does not call the shared metric"
        assert "compute.moi" in src or "from worker.compute.moi" in src, (
            f"{module} does not import from the module that owns the formula"
        )


# ── the inventory query, which is where the numerator went wrong ────────────

def test_the_moi_numerator_query_carries_no_date_window():
    """
    THE THING THAT WOULD HAVE MADE THIS FIX WRONG. A `listDate` window on the
    Active query makes the numerator "listed recently and still active" — a
    fraction of inventory over a full sales rate.
    """
    from worker.query_builders import build_inventory_active
    q = build_inventory_active({"city": "Irvine", "lookback_days": 30})
    assert q["status"] == "Active"
    for forbidden in ("mindate", "maxdate", "minlistdate", "maxlistdate"):
        assert forbidden not in q, (
            f"build_inventory_active sends {forbidden}, so the months-of-supply "
            f"numerator is a subset of inventory rather than inventory"
        )


def test_the_closed_query_filters_on_close_date_and_not_on_list_date():
    from worker.query_builders import build_inventory_closed
    q = build_inventory_closed({"city": "Irvine", "lookback_days": 30})
    assert q["status"] == "Closed"
    assert "minclosedate" in q, "the closed query does not bound the sales window"
    for forbidden in ("minlistdate", "mindate"):
        assert forbidden not in q, (
            f"build_inventory_closed sends {forbidden} — that is D-074, which "
            f"drops long-DOM sales and inflates months of supply"
        )


def test_the_closed_window_matches_the_rate_window():
    """
    A query bounded to one window and a rate computed over another is a wrong
    number with no visible cause. These are two constants in two files and
    nothing but this connects them.
    """
    from worker.query_builders import build_inventory_closed
    q = build_inventory_closed({"city": "Irvine"})
    asked_from = datetime.strptime(q["minclosedate"], "%Y-%m-%d")
    days = (datetime.now() - asked_from).days
    assert abs(days - SALES_RATE_WINDOW_DAYS) <= 1, (
        f"the closed query asks for {days} days but the rate is computed over "
        f"{SALES_RATE_WINDOW_DAYS}"
    )


def test_the_client_side_filter_runs_even_though_the_query_asked():
    """
    The defensive half, and the reason correctness does not wait on the
    production probe: `mindate` was measured being accepted and ignored,
    silently. If `minclosedate` is ignored too, this filter is what keeps the
    denominator right — only the rows fetched and discarded change.
    """
    src = (WORKER / "report_builders.py").read_text()
    assert "closed_in_moi_window" in src or "closed_in_window" in src, (
        "the inventory builder trusts the vendor's date filter with no "
        "client-side check — see D-075"
    )


# ── what reaches the page ───────────────────────────────────────────────────

def test_the_pace_label_says_which_window_the_number_means():
    assert "90" in PACE_LABEL and "pace" in PACE_LABEL
    assert describe(5.2)["pace_label"] == PACE_LABEL
    assert describe(None)["pace_label"] == PACE_LABEL, (
        "the label disappears when there is no estimate, so a reader cannot "
        "tell what was attempted"
    )


def test_no_estimate_renders_words_rather_than_a_blank_or_a_zero():
    shown = describe(None)
    assert shown["current"] is None
    assert shown["has_estimate"] is False
    assert "Not enough" in shown["formatted_current"]
    assert shown["formatted_current"] not in ("0", "0.0", "N/A", "")


@pytest.mark.parametrize("label_block", [
    "stats-bar-label", "mini-stat-label", "stat-block-label", "stat-card-label",
])
def test_every_market_surface_that_prints_the_number_prints_the_pace(label_block):
    """
    Rendered, not grepped. Each macro is checked by putting the pace label in
    the context and looking for it in the output — a `{% if %}` in the wrong
    block would pass a text search and fail here.
    """
    macros = (WORKER / "templates" / "market" / "_base" / "macros.jinja2").read_text()
    blocks = [
        line for line in macros.splitlines()
        if label_block in line and "months_of_inventory_pace" in line
    ]
    assert len(blocks) == 1, (
        f"expected exactly one {label_block} carrying the pace label, found "
        f"{len(blocks)}"
    )
    env = Environment(loader=DictLoader({"t": blocks[0]}),
                      autoescape=select_autoescape(["html", "xml", "jinja2"]))
    with_pace = env.get_template("t").render(
        stats={"months_of_inventory": 5.2, "months_of_inventory_pace": PACE_LABEL}
    )
    assert PACE_LABEL in with_pace, f"{label_block} does not render the pace label"

    without = env.get_template("t").render(stats={"months_of_inventory": 5.2})
    assert "None" not in without, f"{label_block} leaks 'None' when the pace is absent"
