"""What the comparable sales say, computed the way the PDF computes it.

The consumer report reaches a homeowner twice: as the PDF and as the `/r/{id}`
page. Until 2026-11-04 the page led with a figure the PDF never prints — the
home's square footage times the comps' AVERAGE price per square foot, ±8%, with
a "most likely" price in the middle — and its market tab said "6 mo" over a
sentence saying "12 months" and "2 miles" where the PDF said 0.6 mi. The owner
decided against an estimate outside the range panel; the page now shows what
the PDF shows.

These are the PDF builder's own rules (`apps/worker/src/worker/property_builder.py`),
restated because the API cannot import the worker:

  * the range is CLOSED sales only, lowest to highest (`_v2_closed_prices`) —
    an asking price is a hope, not a sale;
  * a median is the UPPER median, `a[len // 2]` (`_v2_median`), so the figure
    is a price some comparable actually sold at;
  * price per square foot is the median over closed sales with both a price
    and a size (`_build_v2_context`, the compare table's row);
  * the window is the oldest close date rounded up to 6 or 12 months
    (`_window_months`, `COMP_WINDOW_BUCKETS_MONTHS`);
  * the radius is the farthest comparable, to one decimal (`stats.max_distance`).

`tests/test_comp_summary_matches_the_pdf.py` holds the two in step: it runs the
same comps through both and compares.
"""
from datetime import date
from typing import Any, Dict, Iterable, List, Optional

#: `PropertyReportBuilder.COMP_WINDOW_BUCKETS_MONTHS`.
WINDOW_BUCKETS_MONTHS = (6, 12)

#: The line that goes beside the range, word for word as the PDF prints it
#: (`property/_v2/report.jinja2`, `.rangepanel-method`, D-134).
RANGE_METHOD = "Range of the comparable sales shown."


def _closed(c: Dict[str, Any]) -> bool:
    return str(c.get("status") or "").strip().lower() in ("closed", "sold")


def _number(value) -> Optional[float]:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def is_sale(c: Dict[str, Any]) -> bool:
    """A closed or sold comp: its price must be what it sold for."""
    return _closed(c)


def sale_price(c: Dict[str, Any]) -> Optional[float]:
    """What a closed comp SOLD for, or None when no sale price is recorded."""
    return _price(c) if _closed(c) else None


def _price(c: Dict[str, Any]) -> Optional[float]:
    # LR-018 / D-377: for a sale, `close_price` is authoritative whenever the
    # row carries the field (the worker and API shape). `price` there was
    # `closePrice or listPrice`, so on a closed comp with no close price it
    # held the ASKING price, and reading it first put that in the range, the
    # median and $/sqft. Stored rows re-read correctly with no migration.
    if _closed(c) and "close_price" in c:
        return _number(c.get("close_price"))
    # Otherwise: the PDF reads `sale_price`, then `price`; older rows used
    # `sold_price`.
    for key in ("sale_price", "price", "close_price", "sold_price"):
        n = _number(c.get(key))
        if n is not None:
            return n
    return None


def closed_prices(comps: Iterable[Dict[str, Any]]) -> List[float]:
    return sorted(p for p in (_price(c) for c in comps if _closed(c)) if p is not None)


def upper_median(values: List[float]) -> Optional[float]:
    return values[len(values) // 2] if values else None


def window_months(comps: Iterable[Dict[str, Any]], today: Optional[date] = None) -> Optional[int]:
    today = today or date.today()
    oldest = None
    for c in comps:
        raw = c.get("close_date") or c.get("sold_date") or ""
        try:
            closed = date.fromisoformat(str(raw)[:10])
        except (ValueError, TypeError):
            continue
        age = (today - closed).days
        oldest = age if oldest is None else max(oldest, age)
    if oldest is None:
        return None
    for bucket in WINDOW_BUCKETS_MONTHS:
        if oldest <= bucket * 31:
            return bucket
    return max(WINDOW_BUCKETS_MONTHS[-1], -(-oldest // 31))


def radius_miles(comps: Iterable[Dict[str, Any]]) -> Optional[float]:
    distances = [d for d in (_number(c.get("distance_miles") or c.get("distance")) for c in comps)
                 if d is not None]
    return round(max(distances), 1) if distances else None


def summarize(comps: List[Dict[str, Any]], today: Optional[date] = None) -> Dict[str, Any]:
    prices = closed_prices(comps)
    ppsf = sorted(
        p / s for p, s in ((_price(c), _number(c.get("sqft"))) for c in comps if _closed(c))
        if p and s)
    dom = [d for d in (c.get("days_on_market") for c in comps if _closed(c))
           if isinstance(d, (int, float)) and d >= 0]
    return {
        "range": ({"low": int(prices[0]), "high": int(prices[-1]), "count": len(prices),
                   "method": RANGE_METHOD} if prices else None),
        "median_price": int(upper_median(prices)) if prices else None,
        "median_price_per_sqft": int(round(upper_median(ppsf))) if ppsf else None,
        "avg_days_on_market": int(round(sum(dom) / len(dom))) if dom else None,
        "homes_sold": len(prices),
        "window_months": window_months([c for c in comps if _closed(c)], today),
        "radius_miles": radius_miles([c for c in comps if _closed(c)]),
    }
