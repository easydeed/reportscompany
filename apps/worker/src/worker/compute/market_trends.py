"""
Market Trends Data Fetcher & Metric Computation
================================================

Fetches SimplyRETS data and computes market trend metrics for the optional
Market Trends page on seller property reports.

Architecture rules (from cursor-market-trends-v2.md):
  - Everything is synchronous — no async/await
  - City search uses cities=city (production) or q=city (demo fallback); client-side _filter_by_city() cleans fuzzy results
  - Date filtering for closed sales is client-side by sales.closeDate (NOT minlistdate)
  - ThreadPoolExecutor for 3 parallel API calls (Closed, Active, Pending)
  - Minimum 3 closed sales required; < 5 prior closed → no trend comparisons

Field names from extract.py output:
  - "close_date"      → datetime or None
  - "close_price"     → int or None
  - "list_price"      → int or None
  - "days_on_market"  → int or None (calculated list→close for closed listings)
  - "sqft"            → int or None
  - "status"          → str
  - "city"            → str
"""

import logging
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────

AVG_DAYS_PER_MONTH = 30.437    # 365.25 / 12 — exact match with report_builders.py
MIN_CLOSED_TO_RENDER = 3       # Fewer than this → page is silently dropped
MIN_PRIOR_FOR_TRENDS = 5       # Fewer than this → no trend arrows shown


# ─── Public entry point ───────────────────────────────────────────────────────

def fetch_and_compute_market_trends(
    city: str,
    zip_code: str = "",
    state: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Orchestrates the 3 SimplyRETS API calls (parallel) and returns a
    market trends dict ready for the Jinja2 template context.

    Returns None when:
      - Any API call fails
      - Fewer than MIN_CLOSED_TO_RENDER closed sales found in the 90-day window

    The caller (PropertyReportBuilder) catches all exceptions and removes
    "market_trends" from page_set when this returns None or raises.
    """
    if not city:
        logger.warning("market_trends: no city provided — skipping")
        return None

    # Lazy imports to avoid circular dependencies at module level
    from worker.vendors.simplyrets import fetch_properties
    from worker.compute.extract import PropertyDataExtractor
    from worker.report_builders import _filter_by_city

    # ── Date windows ──────────────────────────────────────────────────────────
    now = datetime.now()
    three_months_ago = now - timedelta(days=90)
    six_months_ago = now - timedelta(days=180)

    # SimplyRETS minlistdate format: YYYY-MM-DD
    # Use 7-month window (slightly wider than 6) to capture listings that were
    # active before the 6-month mark but closed within it.
    minlistdate_str = (now - timedelta(days=210)).strftime("%Y-%m-%d")

    # ── Parallel API calls ────────────────────────────────────────────────────
    raw_closed: List[Dict] = []
    raw_active: List[Dict] = []
    raw_pending: List[Dict] = []

    # Determine city param style: prefer `cities` (deterministic) over `q` (fuzzy).
    # Demo credentials use q= because the demo feed ignores city params entirely.
    # Import at call time to avoid module-level circular imports.
    from worker.query_builders import ALLOW_CITY_SEARCH
    _city_key = "cities" if ALLOW_CITY_SEARCH else "q"

    def _fetch_closed() -> List[Dict]:
        params = {
            "status": "Closed",
            _city_key: city,
            "minlistdate": minlistdate_str,
        }
        logger.debug("market_trends: fetching closed listings for city=%s (param=%s)", city, _city_key)
        return fetch_properties(params, limit=500)

    def _fetch_active() -> List[Dict]:
        # NO date filter — we want total current inventory for MOI calculation
        params = {
            "status": "Active",
            _city_key: city,
        }
        logger.debug("market_trends: fetching active listings for city=%s (param=%s)", city, _city_key)
        return fetch_properties(params, limit=500)

    def _fetch_pending() -> List[Dict]:
        params = {
            "status": "Pending",
            _city_key: city,
        }
        logger.debug("market_trends: fetching pending listings for city=%s (param=%s)", city, _city_key)
        return fetch_properties(params, limit=200)

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            fut_closed = executor.submit(_fetch_closed)
            fut_active = executor.submit(_fetch_active)
            fut_pending = executor.submit(_fetch_pending)

            raw_closed = fut_closed.result(timeout=90)
            raw_active = fut_active.result(timeout=90)
            raw_pending = fut_pending.result(timeout=90)
    except Exception as exc:
        logger.warning("market_trends: API call failed — %s", exc)
        return None

    logger.info(
        "market_trends: fetched %d closed, %d active, %d pending for city=%s",
        len(raw_closed), len(raw_active), len(raw_pending), city,
    )

    # ── Extract & clean ───────────────────────────────────────────────────────
    try:
        cleaned_closed = PropertyDataExtractor(raw_closed).run()
        cleaned_active = PropertyDataExtractor(raw_active).run()
        # Pending: we only need the count (but extract for consistency)
        pending_count = len(raw_pending)
    except Exception as exc:
        logger.warning("market_trends: extraction failed — %s", exc)
        return None

    # ── Client-side city filter (removes q= fuzzy false positives) ────────────
    cleaned_closed = _filter_by_city(cleaned_closed, city)
    cleaned_active = _filter_by_city(cleaned_active, city)

    # ── A1: Exclude rental/lease products ────────────────────────────────────
    from worker.report_builders import _exclude_rentals
    cleaned_closed = _exclude_rentals(cleaned_closed)
    cleaned_active = _exclude_rentals(cleaned_active)

    # ── Split closed by actual close date ─────────────────────────────────────
    # This is the critical rule: minlistdate ≠ closeDate. We fetch a wide window
    # and split client-side so both periods use the same fetched dataset.
    current_closed: List[Dict] = []
    prior_closed: List[Dict] = []

    for listing in cleaned_closed:
        cd = listing.get("close_date")
        if cd is None:
            continue

        # extract.py already returns timezone-naive datetime objects via _iso()
        # but guard against string close_dates in case the extractor changes
        if isinstance(cd, str):
            try:
                cd = datetime.fromisoformat(cd.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, AttributeError):
                continue

        if cd >= three_months_ago:
            current_closed.append(listing)
        elif cd >= six_months_ago:
            prior_closed.append(listing)

    logger.info(
        "market_trends: %d current-period closed, %d prior-period closed, %d active",
        len(current_closed), len(prior_closed), len(cleaned_active),
    )

    # ── Guard: insufficient data ───────────────────────────────────────────────
    if len(current_closed) < MIN_CLOSED_TO_RENDER:
        logger.info(
            "market_trends: only %d closed sales in 90-day window (need %d) — skipping page",
            len(current_closed), MIN_CLOSED_TO_RENDER,
        )
        return None

    # ── Compute & return ──────────────────────────────────────────────────────
    try:
        return _compute_trends(
            current_closed=current_closed,
            prior_closed=prior_closed,
            active_listings=cleaned_active,
            pending_count=pending_count,
            city=city,
        )
    except Exception as exc:
        logger.warning("market_trends: computation failed — %s", exc)
        return None


# ─── Internal computation ─────────────────────────────────────────────────────

def _compute_trends(
    current_closed: List[Dict],
    prior_closed: List[Dict],
    active_listings: List[Dict],
    pending_count: int,
    city: str,
) -> Dict[str, Any]:
    """
    Compute all market trend metrics from cleaned listing data.

    Returns a dict matching the Jinja2 template's `market_trends` context variable.
    Every trend metric has both `direction` AND `sentiment`:
      - direction: "up" | "down" | "flat" | None   (factual movement)
      - sentiment: "good" | "bad" | "neutral" | None (good/bad FOR SELLERS)
    Template colors by sentiment, not direction — this prevents the
    "DOM ↓ should be green for sellers but CSS shows red" class of bugs.
    """
    has_prior_data = len(prior_closed) >= MIN_PRIOR_FOR_TRENDS

    # ── Prices ────────────────────────────────────────────────────────────────
    current_prices = [l["close_price"] for l in current_closed if l.get("close_price")]
    prior_prices   = [l["close_price"] for l in prior_closed   if l.get("close_price")]

    current_median_price = statistics.median(current_prices) if current_prices else None
    prior_median_price   = statistics.median(prior_prices)   if prior_prices   else None

    # ── DOM ───────────────────────────────────────────────────────────────────
    current_dom_vals = [l["days_on_market"] for l in current_closed if l.get("days_on_market") is not None]
    prior_dom_vals   = [l["days_on_market"] for l in prior_closed   if l.get("days_on_market") is not None]

    current_avg_dom = round(sum(current_dom_vals) / len(current_dom_vals)) if current_dom_vals else None
    prior_avg_dom   = round(sum(prior_dom_vals)   / len(prior_dom_vals))   if prior_dom_vals   else None

    # ── List-to-Sale ratio ────────────────────────────────────────────────────
    def _ratios(listings: List[Dict]) -> List[float]:
        out = []
        for l in listings:
            lp = l.get("list_price")
            cp = l.get("close_price")
            if lp and cp and lp > 0:
                out.append(cp / lp * 100)
        return out

    current_ctl = _ratios(current_closed)
    prior_ctl   = _ratios(prior_closed)

    current_avg_ctl = round(sum(current_ctl) / len(current_ctl), 1) if current_ctl else None
    prior_avg_ctl   = round(sum(prior_ctl)   / len(prior_ctl),   1) if prior_ctl   else None

    # ── Price per sq ft ───────────────────────────────────────────────────────
    def _ppsf(listings: List[Dict]) -> List[float]:
        out = []
        for l in listings:
            cp   = l.get("close_price")
            sqft = l.get("sqft")
            if cp and sqft and sqft > 0:
                out.append(cp / sqft)
        return out

    current_ppsf_vals = _ppsf(current_closed)
    prior_ppsf_vals   = _ppsf(prior_closed)

    current_avg_ppsf = round(sum(current_ppsf_vals) / len(current_ppsf_vals)) if current_ppsf_vals else None
    prior_avg_ppsf   = round(sum(prior_ppsf_vals)   / len(prior_ppsf_vals))   if prior_ppsf_vals   else None

    # ── Active listings ───────────────────────────────────────────────────────
    active_count = len(active_listings)
    active_prices = [l.get("list_price") for l in active_listings if l.get("list_price")]
    avg_active_price = round(sum(active_prices) / len(active_prices)) if active_prices else None

    # ── Months of Inventory (MOI) ─────────────────────────────────────────────
    # Formula (same as report_builders.py):
    #   monthly_sales_rate = closed_in_90_days * (30.437 / 90)
    #   MOI = active_count / monthly_sales_rate
    monthly_sales_rate = len(current_closed) * (AVG_DAYS_PER_MONTH / 90)
    moi: Optional[float] = None
    if monthly_sales_rate > 0 and active_count >= 0:
        moi = round(active_count / monthly_sales_rate, 1)

    # ── Market condition ──────────────────────────────────────────────────────
    condition_info = _classify_market_condition(
        moi=moi,
        closed_count=len(current_closed),
        active_count=active_count,
        pending_count=pending_count,
        avg_ctl=current_avg_ctl,
    )

    # ── Gauge position (capped 0-12 months for display) ───────────────────────
    # We store the raw MOI and let the template calculate position
    # A 0-12 month scale means: position % = min(MOI/12*100, 98)
    gauge_pct: Optional[int] = None
    if moi is not None:
        gauge_pct = min(int(moi / 12 * 100), 98)

    # ── B1-B3: New metrics on current_closed + active ─────────────────────────
    from worker.report_builders import (
        compute_price_cut_stats,
        compute_dom_distribution,
        compute_timeline_metrics,
    )

    price_cut_stats  = compute_price_cut_stats(active_listings)
    dom_distribution = compute_dom_distribution(current_dom_vals)
    timeline_metrics = compute_timeline_metrics(current_closed)

    # ── Build the full context dict ───────────────────────────────────────────
    now = datetime.now()
    return {
        "city": city,
        "period_label": "Last 90 Days",
        "generated_date": now.strftime("%B %Y"),
        "data_source": "MLS",
        "sample_size": len(current_closed),
        "has_prior_data": has_prior_data,

        # B1-B3: New metric groups for template use
        "price_cut_stats":  price_cut_stats,
        "dom_distribution": dom_distribution,
        "timeline_metrics": timeline_metrics,

        # Trend metrics — each has: current, prior, change_pct, direction, sentiment,
        #                           formatted_current, formatted_prior
        "median_sale_price": _build_metric(
            current=current_median_price,
            prior=prior_median_price if has_prior_data else None,
            format_fn=_fmt_currency,
            good_direction="up",    # Rising prices → good for sellers
        ),
        "avg_days_on_market": _build_metric(
            current=current_avg_dom,
            prior=prior_avg_dom if has_prior_data else None,
            format_fn=lambda x: f"{x} days",
            good_direction="down",  # Fewer DOM → selling faster → good for sellers
        ),
        "list_to_sale_ratio": _build_metric(
            current=current_avg_ctl,
            prior=prior_avg_ctl if has_prior_data else None,
            format_fn=lambda x: f"{x}%",
            good_direction="up",    # Closer to 100% → better for sellers
        ),
        "price_per_sqft": _build_metric(
            current=current_avg_ppsf,
            prior=prior_avg_ppsf if has_prior_data else None,
            format_fn=lambda x: f"${x:,}",
            good_direction="up",    # Higher PPSF → good for sellers
        ),
        "closed_sales": _build_metric(
            current=len(current_closed),
            prior=len(prior_closed) if has_prior_data else None,
            format_fn=str,
            good_direction="up",    # More sales → active market → good for sellers
        ),

        # Active listings — snapshot only, no trend comparison
        "active_listings": {
            "count": active_count,
            "avg_price": avg_active_price,
            "formatted_count": f"{active_count:,}",
            "formatted_avg_price": _fmt_currency(avg_active_price) if avg_active_price else "N/A",
        },

        # Months of inventory
        "months_of_inventory": {
            "current": moi,
            "gauge_pct": gauge_pct,
            "formatted_current": f"{moi} months" if moi is not None else "N/A",
        },

        # Market condition badge
        "market_condition": condition_info,
    }


def _classify_market_condition(
    moi: Optional[float],
    closed_count: int,
    active_count: int,
    pending_count: int,
    avg_ctl: Optional[float],
) -> Dict[str, Any]:
    """
    Determine market condition label, score, and description.

    Score: 1–10, higher = better for sellers.
    Thresholds match NAR / industry standard:
      Seller's market: MOI < 4
      Balanced market: MOI 4–6
      Buyer's market:  MOI > 6
    """
    if moi is None:
        return {
            "indicator": "unknown",
            "label": "Insufficient Data",
            "description": "Not enough recent sales data to determine market conditions.",
            "score": 0,
        }

    if moi < 4:
        indicator = "sellers"
        label = "Seller's Market"
        # 0 MOI = 10, 4 MOI = 5; linear interpolation
        score = max(5, min(10, round(10 - moi * 1.25)))
        description = (
            f"With only {moi} months of inventory and {closed_count} sales in the last "
            f"90 days, sellers have the clear advantage. Homes are moving quickly "
            f"and typically selling near or above asking price"
            + (f" ({avg_ctl:.1f}% close-to-list ratio)" if avg_ctl else "")
            + "."
        )
    elif moi <= 6:
        indicator = "balanced"
        label = "Balanced Market"
        score = 5
        description = (
            f"The market is in balance with {moi} months of inventory and "
            f"{closed_count} recent sales. Both buyers and sellers have "
            f"reasonable negotiating leverage."
        )
    else:
        indicator = "buyers"
        label = "Buyer's Market"
        # 6 MOI = 5, 12+ MOI = 1; linear decay
        score = max(1, min(4, round(11 - moi)))
        description = (
            f"With {moi} months of inventory and {active_count} active listings, "
            f"buyers have more choices and negotiating power. Competitive pricing "
            f"and strong presentation are essential for sellers."
        )

    return {
        "indicator": indicator,
        "label": label,
        "description": description,
        "score": score,
    }


def _build_metric(
    current: Optional[Any],
    prior: Optional[Any],
    format_fn,
    good_direction: str,  # "up" or "down"
) -> Dict[str, Any]:
    """
    Build a standardized trend metric dict.

    `direction` = factual movement (up/down/flat/None)
    `sentiment` = good/bad/neutral for sellers — used by template for coloring.

    These are INDEPENDENT. DOM going DOWN has direction="down" and sentiment="good".
    The template must use `sentiment` for CSS classes, never `direction` directly.
    """
    base: Dict[str, Any] = {
        "current": current,
        "prior": prior,
        "change_pct": None,
        "direction": None,
        "sentiment": None,
        "formatted_current": format_fn(current) if current is not None else "N/A",
        "formatted_prior": format_fn(prior) if prior is not None else "N/A",
    }

    if current is None or prior is None or prior == 0:
        return base

    change_pct = round((current - prior) / abs(prior) * 100, 1)
    direction: Optional[str]
    if change_pct > 0.05:
        direction = "up"
    elif change_pct < -0.05:
        direction = "down"
    else:
        direction = "flat"

    if direction == "flat":
        sentiment = "neutral"
    elif direction == good_direction:
        sentiment = "good"
    else:
        sentiment = "bad"

    base.update({
        "change_pct": change_pct,
        "direction": direction,
        "sentiment": sentiment,
    })
    return base


# ─── Formatting helpers ───────────────────────────────────────────────────────

def _fmt_currency(value: Optional[float]) -> str:
    """$725,000 or $1.2M — consistent with report_builders.py _format_currency_short"""
    if value is None:
        return "N/A"
    try:
        v = float(value)
        if v >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        return f"${int(v):,}"
    except (ValueError, TypeError):
        return str(value)


# ─── Sample data (used by test_template.py --with-market-trends) ──────────────

SAMPLE_MARKET_TRENDS: Dict[str, Any] = {
    "city": "Los Angeles",
    "period_label": "Last 90 Days",
    "generated_date": "February 2026",
    "data_source": "MLS",
    "sample_size": 89,
    "has_prior_data": True,

    "median_sale_price": {
        "current": 725000, "prior": 695000,
        "change_pct": 4.3, "direction": "up", "sentiment": "good",
        "formatted_current": "$725,000", "formatted_prior": "$695,000",
    },
    "avg_days_on_market": {
        "current": 28, "prior": 34,
        "change_pct": -17.6, "direction": "down", "sentiment": "good",
        "formatted_current": "28 days", "formatted_prior": "34 days",
    },
    "list_to_sale_ratio": {
        "current": 98.5, "prior": 97.2,
        "change_pct": 1.3, "direction": "up", "sentiment": "good",
        "formatted_current": "98.5%", "formatted_prior": "97.2%",
    },
    "price_per_sqft": {
        "current": 342, "prior": 328,
        "change_pct": 4.3, "direction": "up", "sentiment": "good",
        "formatted_current": "$342", "formatted_prior": "$328",
    },
    "closed_sales": {
        "current": 89, "prior": 78,
        "change_pct": 14.1, "direction": "up", "sentiment": "good",
        "formatted_current": "89", "formatted_prior": "78",
    },
    "active_listings": {
        "count": 156, "avg_price": 745000,
        "formatted_count": "156", "formatted_avg_price": "$745,000",
    },
    "months_of_inventory": {
        "current": 2.8,
        "gauge_pct": 23,
        "formatted_current": "2.8 months",
    },
    "market_condition": {
        "indicator": "sellers",
        "label": "Seller's Market",
        "description": (
            "With only 2.8 months of inventory and 89 sales in the last 90 days, "
            "sellers have the clear advantage. Homes are moving quickly and typically "
            "selling near or above asking price (98.5% close-to-list ratio)."
        ),
        "score": 8,
    },
}
