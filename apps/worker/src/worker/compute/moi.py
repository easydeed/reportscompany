"""
Months of supply — one implementation, for every surface that shows it.

WHY THIS MODULE EXISTS
----------------------
There were three. `market_trends.py` computed MOI for the property report's
Market Trends gauge; `report_builders.py` computed it twice more, once for the
market snapshot and once for the inventory report — and the third used a
different formula from the other two:

    market_trends / snapshot   active / (closed * 30.437/window)
    inventory                  (active / closed) * (window / 30)

Those are not the same quantity. The first is inventory divided by a monthly
sales *rate*; the second is a ratio scaled by a period, which happens to
coincide only when window == 30.437 days. Two formulas for one metric is how
D-056 happened — a sentinel that meant "no data" in one place and "balanced
market" in another — so the formula lives here now and the call sites pass
their own window.

WHAT MONTHS OF SUPPLY IS
------------------------
    monthly sales rate = closings in the window * (30.437 / window_days)
    months of supply    = current active inventory / monthly sales rate

Read as: at the pace of the last `window_days`, how many months to sell every
home currently for sale. **It is a rate extrapolation, not a forecast** — §0.6
rule 6, which was written about this metric. Callers render `PACE_LABEL`
beside the number so the page says which pace it means.

THE TWO INPUTS ARE NOT SYMMETRICAL, AND GETTING THAT WRONG IS D-056
-------------------------------------------------------------------
    numerator    TOTAL current active inventory — no date window. Every
                 home for sale, not the ones listed recently. The inventory
                 report's query used to carry a `listDate` window, which made
                 the numerator "listed in the last 30 days and still active" —
                 a fraction of inventory over a full sales rate. Adding a
                 closed query without fixing that gives a wrong number more
                 convincingly than before. `market_trends.py` already had the
                 comment: "NO date filter — we want total current inventory".

    denominator  closings in a window, filtered on CLOSE date, not list date.

WHY IT RETURNS None RATHER THAN A NUMBER
----------------------------------------
Below `MIN_CLOSED_FOR_MOI` closings the rate is noise: in a small market two
sales versus three moves MOI by a third. D-056 was a sentinel (0.0, and
elsewhere 999.0) rendering as though it were a measurement. There is no
sentinel here. Not enough data returns None, and the caller says so in words.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Mean days per month across a 400-year Gregorian cycle. Matches the constant
# already used by market_trends.py and report_builders.py.
AVG_DAYS_PER_MONTH = 30.437

# The window the sales rate is measured over. Thirty days in a quiet market is
# two or three closings, and MOI then swings by whole months on a single sale.
# Ninety smooths that and is the convention the industry reports in.
SALES_RATE_WINDOW_DAYS = 90

# Below this many closings in the window, no number is published. Matches
# market_trends.MIN_CLOSED_TO_RENDER, which already dropped its page below it.
MIN_CLOSED_FOR_MOI = 3

# Rendered beside the number wherever it appears. The window is a choice, and
# a reader cannot check a number whose basis is not stated.
PACE_LABEL = f"at the last {SALES_RATE_WINDOW_DAYS} days' sales pace"

# What to say instead of a number. Not "0", not "N/A", not a blank.
INSUFFICIENT_DATA_LABEL = "Not enough recent sales to estimate"


def months_of_supply(
    active_count: int,
    closed_count: int,
    window_days: int = SALES_RATE_WINDOW_DAYS,
    active_was_truncated: bool = False,
) -> Optional[float]:
    """
    Months of supply, or None when it cannot honestly be estimated.

    `active_was_truncated` is the caller saying "my active count is a floor,
    not a count" — it hit a paging limit. A floor in the numerator produces an
    MOI that is too LOW, which reads as a hotter market than the real one, so
    it is refused rather than published. Silence beats a confident wrong
    number; that is the whole of D-056.
    """
    if active_was_truncated:
        return None
    if closed_count < MIN_CLOSED_FOR_MOI:
        return None
    if window_days <= 0 or active_count < 0:
        return None
    monthly_sales_rate = closed_count * (AVG_DAYS_PER_MONTH / window_days)
    if monthly_sales_rate <= 0:
        return None
    return round(active_count / monthly_sales_rate, 1)


def gauge_pct(moi: Optional[float], full_scale_months: int = 12) -> Optional[int]:
    """Position on a 0-to-`full_scale_months` gauge, capped short of the end."""
    if moi is None:
        return None
    return min(int(moi / full_scale_months * 100), 98)


def closed_since(window_days: int = SALES_RATE_WINDOW_DAYS, now: Optional[datetime] = None) -> str:
    """The `minclosedate` value for a sales-rate window, as YYYY-MM-DD."""
    now = now or datetime.now()
    return (now - timedelta(days=window_days)).strftime("%Y-%m-%d")


def closed_in_window(
    listings: List[Dict[str, Any]],
    window_days: int = SALES_RATE_WINDOW_DAYS,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Keep the listings that CLOSED inside the window, by their close date.

    THIS RUNS EVEN WHEN THE QUERY ALREADY ASKED FOR IT, on purpose (D-074,
    D-075). Whether SimplyRETS honours `minclosedate` is a property of the feed
    and is not yet confirmed against production — `mindate` was measured doing
    nothing at all, silently, and this repo already tracks demo/production
    divergence. Filtering here makes the result correct under either answer;
    only the number of rows fetched and discarded changes.

    A listing with no close date is dropped. It cannot be counted as a sale in
    a window whose bounds it does not have.
    """
    now = now or datetime.now()
    cutoff = now - timedelta(days=window_days)
    kept = []
    for listing in listings:
        cd = listing.get("close_date")
        if cd is None:
            continue
        if isinstance(cd, str):
            try:
                cd = datetime.fromisoformat(cd.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
        if getattr(cd, "tzinfo", None) is not None:
            cd = cd.replace(tzinfo=None)
        if cd >= cutoff:
            kept.append(listing)
    return kept


def describe(moi: Optional[float]) -> Dict[str, Any]:
    """
    The render-ready shape. One place decides how "no number" looks, so the
    surfaces cannot disagree about it the way the two formulas did.
    """
    if moi is None:
        return {
            "current": None,
            "gauge_pct": None,
            "formatted_current": INSUFFICIENT_DATA_LABEL,
            "pace_label": PACE_LABEL,
            "has_estimate": False,
        }
    return {
        "current": moi,
        "gauge_pct": gauge_pct(moi),
        "formatted_current": f"{moi} months",
        "pace_label": PACE_LABEL,
        "has_estimate": True,
    }
