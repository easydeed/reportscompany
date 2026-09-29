"""Price bands that mean the same thing two weeks running.

WHAT WAS WRONG, MEASURED (D-111)
--------------------------------
`build_price_bands_result` did not use price bands. It used quartiles of the
current result set — the median and the 75th percentile of whatever came back
this week — so a report titled "Price Bands" showed roughly 50% / 25% / 25%
**by construction**, whatever the market did.

Bootstrapped over 400 pairs of independent weekly samples from an *unchanging*
market:

    Irvine-like, 60 sales/wk   p50 boundary moves a median of $105,500
                               between consecutive runs (p90 $269,000);
                               33 distinct first-band labels over 800 runs
    smaller, 25/wk             $55,000 median; 219 distinct labels
    thin, 10/wk                $130,000 median; 363 distinct labels

And the counts over those same runs were `[30, 15, 15]` every single time,
because they are 50/25/25 of 60 by construction.

**The report was inverted.** The part that carries information was constant by
construction, and the part that is constant in reality — the market — was what
moved on the page. An agent reading "Under $1.2M: 30" one week and "Under
$984K: 30" the next cannot tell whether inventory shifted or the divider did.

WHAT REPLACES IT
----------------
Round boundaries on a 1-2-5 ladder, laid on multiples of the step from zero,
with the **extent taken from twelve months of closings** rather than from this
week's results. Same bootstrap, same markets:

    distinct edge sets over 400 runs of an unchanging market
      Irvine-like   1   (against 33 labels for quartiles)
      smaller       2   (against 219)
      thin          1   (against 363)

and the counts start varying, because the boundaries stopped absorbing the
variation.

Rejected, with the reason measured rather than argued:

  * **fixed global bands** (a $250K step everywhere) — comparable across
    markets as well as across runs, which sounds strictly better and is not:
    one band in a $350K market and twelve in a $3M one, to buy a cross-market
    comparison this report never makes. It shows one market over time.
  * **per-market bands stored in the database** — the textbook answer, and it
    needs a schema change, a recompute policy and a migration to buy stability
    this already has. One distinct edge set in 400 runs is not meaningfully
    less stable than a stored constant, and this fails fresh rather than stale:
    a market that genuinely moves a step gets new bands rather than old ones.
  * **snapping with the extent from this week's sample** — the cheaper build,
    so it was measured too: 2 / 5 / **18** distinct edge sets. The step is
    stable (chosen identically in 382 of 400 runs) but a ten-sale week's min
    and max add or drop a band at the ends. Anchoring the extent to the
    history is what fixes it.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

#: A 1-2-5 ladder, in dollars. Every boundary the product can draw is a
#: multiple of one of these, which is what makes a label a reader recognises
#: ("$800K – $1M") rather than a percentile with a dollar sign on it.
LADDER = (25_000, 50_000, 100_000, 200_000, 250_000, 500_000, 1_000_000, 2_000_000)

#: How many bands to aim for. Six is what the stat-card row was measured to
#: hold: six cards at 56px each with labels on three lines, nothing clipped
#: (D-107). It is a target, not a promise — the ladder decides the step and
#: the market's range decides how many of them fit.
TARGET_BANDS = 6

#: And a promise, MEASURED rather than asserted. D-107 measured SIX cards
#: (56px each, row 95.2px, nothing clipped) and the first draft of this line
#: cited that measurement for a limit of eight, which it does not support.
#: Measured at eight: **53px per card, row 95px, zero labels clipped** — the
#: same row height, and the longest label the ladder can produce
#: ("$1.25M – $1.5M") wraps without truncating.
#:
#: A step that would exceed this is rejected in favour of the next rung, and
#: `band_edges` stops emitting past it regardless, so the row can never have
#: to truncate — the defect D-107 closed, arriving from the other end.
MAX_BANDS = 8

#: Below this many closings the extent is not worth deriving from history: a
#: handful of sales does not describe a market's price range any better than
#: this week's listings do, and pretending otherwise is the "a median of one
#: sale is that sale" mistake in another costume (`MIN_CLOSED_FOR_MEDIAN`).
MIN_HISTORY_FOR_EXTENT = 12


def _price(row: Dict[str, Any]) -> Optional[float]:
    for key in ("list_price", "close_price"):
        value = row.get(key)
        if value:
            return float(value)
    return None


def format_price(value: float) -> str:
    """`$800K`, `$1.25M`, `$1.5M`, `$2M`. Exact, then as short as it can be.

    TWO DECIMALS, NOT ONE, AND THIS IS NOT COSMETIC. One decimal renders a
    $1,250,000 boundary as "$1.2M" — and $250K is one of the commonest steps
    on the ladder, so above a million the label would routinely state a
    boundary the band does not have. A reader comparing "$1.2M – $1.5M"
    against a listing at $1,240,000 would put it in the wrong band.

    Trailing zeros are stripped so the common cases stay short: $1M, $1.5M,
    $2M, and $1.25M only when the quarter is real.
    """
    if value >= 1_000_000:
        text = f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".")
        return f"${text}M"
    return f"${int(round(value / 1000)):,}K"


def choose_step(low: float, high: float, target: int = TARGET_BANDS,
                maximum: int = MAX_BANDS) -> int:
    """The ladder rung that covers `low`..`high` in about `target` bands."""
    span = max(float(high) - float(low), 1.0)
    ordered = sorted(LADDER, key=lambda s: (abs(s - span / max(target, 1)), s))
    for step in ordered:
        if _count_bands(low, high, step) <= maximum:
            return step
    return LADDER[-1]


def _count_bands(low: float, high: float, step: int) -> int:
    start = (int(low) // step) * step
    return max(1, int((high - start) // step) + 1)


def band_edges(low: float, high: float, target: int = TARGET_BANDS,
               maximum: int = MAX_BANDS) -> tuple:
    """`(step, [edge, …])` — boundaries on multiples of the step, from zero.

    THE COUNT IS BOUNDED BY CONSTRUCTION, NOT BY THE LADDER HAPPENING TO
    REACH. Walking up the rungs is not enough: the ladder stops at $2M, so a
    $50K–$90M range fell through to the top rung and produced **46 bands** —
    caught by the test that asserts the row never overflows, which is the
    defect D-107 closed arriving from the other end.

    The top band is open-ended anyway, so the fix is already in the shape:
    stop emitting edges at `maximum` and let "$X+" absorb everything above.
    A luxury market gets a wide top band rather than a row nobody can read.
    """
    step = choose_step(low, high, target, maximum)
    start = (int(low) // step) * step
    edges, edge = [], start
    while edge <= high and len(edges) < maximum:
        edges.append(edge)
        edge += step
    return step, edges or [start]


def extent_from_history(history: Sequence[Dict[str, Any]]) -> Optional[tuple]:
    """`(low, high)` from twelve months of closings, or None if too few.

    None is a real answer and the caller says so on the page. Falling back to
    this week's results silently is what the measurement above rejects.
    """
    prices = [p for p in (_price(row) for row in history or []) if p]
    if len(prices) < MIN_HISTORY_FOR_EXTENT:
        return None
    return min(prices), max(prices)


def build_bands(listings: Sequence[Dict[str, Any]],
                history: Sequence[Dict[str, Any]] = ()) -> Dict[str, Any]:
    """The bands, their counts, and where the boundaries came from.

    EMPTY BANDS ARE KEPT. The old code dropped them (`if band_listings:`),
    which is why the chart's "none" row and the cards' zero handling have
    never been reachable. With fixed boundaries an empty band is routine and
    it is information: "nothing above $1.6M" is a fact about the market, and a
    band that vanishes makes the row lie about its own shape.
    """
    prices = [p for p in (_price(row) for row in listings) if p]
    if not prices:
        return {"bands": [], "step": None, "extent_source": "none", "note": None}

    extent = extent_from_history(history)
    if extent is None:
        source = "results"
        low, high = min(prices), max(prices)
        note = ("Bands sized from this period's results — fewer than "
                f"{MIN_HISTORY_FOR_EXTENT} closings in the last twelve months "
                "to size them from. They may shift between reports.")
    else:
        source = "history"
        # The history sets the extent; this period's results must still fit
        # inside it, or a listing priced outside the year's range would fall
        # off the end of the row without saying so.
        low = min(extent[0], min(prices))
        high = max(extent[1], max(prices))
        note = None

    step, edges = band_edges(low, high)
    bands = []
    for i, edge in enumerate(edges):
        upper = edge + step
        last = i == len(edges) - 1
        in_band = [l for l in listings
                   if (_price(l) or -1) >= edge and (last or (_price(l) or -1) < upper)]
        band_prices = [p for p in (_price(l) for l in in_band) if p]
        doms = [l["days_on_market"] for l in in_band
                if l.get("days_on_market") is not None]
        ppsf = [l["price_per_sqft"] for l in in_band if l.get("price_per_sqft")]
        bands.append({
            "label": (f"{format_price(edge)}+" if last and edge > 0
                      else f"{format_price(edge)} – {format_price(upper)}"),
            "low": edge,
            "high": None if last else upper,
            "count": len(in_band),
            "median_price": _median(band_prices) if band_prices else None,
            "avg_dom": round(sum(doms) / len(doms), 1) if doms else None,
            "avg_ppsf": round(sum(ppsf) / len(ppsf)) if ppsf else None,
        })
    return {"bands": bands, "step": step, "extent_source": source, "note": note}


def _median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def hottest_and_slowest(bands: Sequence[Dict[str, Any]]) -> tuple:
    """The fastest- and slowest-selling bands that actually have sales.

    `avg_dom` IS NOW None RATHER THAN 0 FOR AN EMPTY BAND, and that is the
    point. The old code ranked with

        min(bands, key=lambda b: b["avg_dom"] if b["avg_dom"] > 0 else 999)

    so a band whose sales all went under contract the day they listed scored
    999 and could never be the hottest — the zero-is-falsy family (D-108) in a
    ranking, wearing a sentinel instead of a filter, which is why that sweep
    did not catch it. Bands with no sales are excluded because they have no
    speed, not because their speed is zero.
    """
    ranked = [b for b in bands if b.get("avg_dom") is not None and b.get("count")]
    if not ranked:
        empty = {"label": "—", "count": 0, "avg_dom": None}
        return empty, empty
    return (min(ranked, key=lambda b: b["avg_dom"]),
            max(ranked, key=lambda b: b["avg_dom"]))
