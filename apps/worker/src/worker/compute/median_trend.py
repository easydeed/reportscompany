"""Twelve months of median closed price, bucketed from rows this report already has.

WHAT IT COSTS, WHICH IS NOT WHAT §7.3'S ANALYSIS SAYS
-----------------------------------------------------
Decision 01 settled the cost of a twelve-month trend at **13 requests**, by
differencing cumulative `minclosedate` counts. That is the cost of a COUNT
series — how many homes sold each month — because a count is answerable with
`count=true` and `limit=1`.

A MEDIAN is a different question. It needs the prices, not the total, so it
cannot be differenced out of counts at any price. But it does not cost 13
requests either: one `minclosedate = today - 365` query returns the closed rows
with `close_date` and `close_price` already on them (`extract.py`), and twelve
medians fall out of bucketing them here. At `page_max = 500` that is **two
requests for up to 1000 closings** — cheaper than the count series, not dearer.

The ceiling is the catch, and it is `SIMPLYRETS_MAX_RESULTS` (1000 by default).
A market with more than that in twelve months gets a truncated set, and a median
computed from a truncated, order-dependent subset is a wrong number that looks
like a right one. `fetch_properties` already logs when it hits the limit;
`series_from_closed` takes `truncated` and refuses rather than drawing it, which
is D-078's rule — a figure that cannot be trusted is not published.

WHY A MONTH CAN BE EMPTY, AND WHY THAT IS A GAP AND NOT A ZERO
---------------------------------------------------------------
A month with no closings has no median. Plotting zero would draw a crash that
did not happen. Those months are `None` and the chart breaks its line across
them.

A month with a handful of closings has a median that is arithmetically fine and
statistically meaningless — one sale's median is that sale's price. The rest of
this codebase already draws that line at three (`MIN_CLOSED_FOR_MOI`,
`market_trends.py`: "Minimum 3 closed sales required"), so this does too, and
for the same reason rather than by copying the number.
"""

import logging
import statistics
from datetime import date
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

#: Fewest closings a month needs before its median is worth plotting. Matches
#: compute.moi.MIN_CLOSED_FOR_MOI — the same judgement about the same feed.
MIN_CLOSED_FOR_MEDIAN = 3

MONTHS = 12

_MONTH_LABELS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _month_key(value) -> Optional[tuple]:
    """(year, month) from a date, datetime or ISO-ish string; None if unreadable."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return None
    year = getattr(value, "year", None)
    month = getattr(value, "month", None)
    if year is None or month is None:
        return None
    return (year, month)


def _window(today: date, months: int = MONTHS) -> List[tuple]:
    """The N (year, month) buckets ending with today's month, oldest first."""
    out = []
    year, month = today.year, today.month
    for _ in range(months):
        out.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(out))


def series_from_closed(
    closed: Sequence[Dict[str, Any]],
    today: Optional[date] = None,
    months: int = MONTHS,
    truncated: bool = False,
) -> Optional[List[Dict[str, Any]]]:
    """Bucket closed rows into monthly medians.

    Returns a list of ``{"label", "year", "month", "value", "n"}`` oldest first,
    with ``value`` None for a month that has no median worth drawing — or None
    for the whole series when it should not be drawn at all.

    ``truncated`` is the caller saying the fetch hit its row ceiling. The series
    is then refused outright: a median over an arbitrary subset of a market's
    sales is not a median of that market.
    """
    if truncated:
        logger.warning(
            "median_trend: refusing to build a series from a truncated fetch — "
            "a median over a partial, order-dependent subset is a wrong number "
            "that looks like a right one (D-078)."
        )
        return None

    today = today or date.today()
    buckets: Dict[tuple, List[float]] = {}
    for row in closed or []:
        key = _month_key(row.get("close_date"))
        price = row.get("close_price")
        if key is None or not price:
            continue
        buckets.setdefault(key, []).append(float(price))

    series = []
    for year, month in _window(today, months):
        prices = buckets.get((year, month), [])
        enough = len(prices) >= MIN_CLOSED_FOR_MEDIAN
        series.append({
            "label": _MONTH_LABELS[month - 1],
            "year": year,
            "month": month,
            "value": statistics.median(prices) if enough else None,
            "n": len(prices),
        })

    drawn = [p for p in series if p["value"] is not None]
    if len(drawn) < 2:
        # One point is not a trend, and zero is not a chart. Both cases render
        # nothing rather than a line with no slope or an empty axis.
        logger.info(
            "median_trend: %d of %d months have at least %d closings — not "
            "enough for a trend, no chart.",
            len(drawn), months, MIN_CLOSED_FOR_MEDIAN,
        )
        return None

    return series
