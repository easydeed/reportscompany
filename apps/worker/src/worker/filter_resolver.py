"""
Market-Adaptive Filter Resolver

Converts preset "intent" filters (with price_strategy) into concrete SimplyRETS 
query filters by resolving percentages against actual market medians.

Example:
    Input (intent):
        {
            "minbeds": 2,
            "price_strategy": {"mode": "maxprice_pct_of_median_list", "value": 0.70}
        }
    
    Output (resolved, for Irvine with median ~$2.4M):
        {
            "type": "RES",
            "minbeds": 2,
            "maxprice": 1680000
        }

This enables market-adaptive presets that work in any market without 
maintaining region-specific preset packs.
"""

from typing import Dict, List, Optional, Any
import statistics


def compute_market_stats(listings: List[Dict]) -> Dict[str, Optional[float]]:
    """
    Compute market statistics from a set of listings.
    
    Used to establish baseline medians BEFORE applying bed/bath filters,
    which keeps the median stable and consistent.
    
    Args:
        listings: List of property dicts (Active and/or Closed)
    
    Returns:
        {
            "median_list_price": float or None,
            "median_close_price": float or None,
            "count": int
        }
    """
    list_prices = [
        l.get("list_price") 
        for l in listings 
        if l.get("list_price") and l.get("status") in ("Active", "Pending")
    ]
    
    close_prices = [
        l.get("close_price") 
        for l in listings 
        if l.get("close_price") and l.get("status") == "Closed"
    ]
    
    return {
        "median_list_price": statistics.median(list_prices) if list_prices else None,
        "median_close_price": statistics.median(close_prices) if close_prices else None,
        "count": len(listings),
    }


def resolve_filters(
    filters_intent: Dict[str, Any], 
    market_stats: Dict[str, Optional[float]]
) -> Dict[str, Any]:
    """
    Convert preset intent into concrete SimplyRETS query filters.
    
    This is the core function that makes presets market-adaptive.
    
    Args:
        filters_intent: Preset filters, may include price_strategy
        market_stats: Dict with median_list_price and/or median_close_price
    
    Returns:
        Resolved filters with actual dollar amounts (ready for SimplyRETS)
    
    Example:
        filters_intent = {
            "minbeds": 2,
            "subtype": "SingleFamilyResidence",
            "price_strategy": {
                "mode": "maxprice_pct_of_median_list",
                "value": 0.70
            }
        }
        market_stats = {"median_list_price": 2400000}
        
        Returns: {
            "type": "RES",
            "minbeds": 2,
            "subtype": "SingleFamilyResidence",
            "maxprice": 1680000  # 70% of $2.4M
        }
    """
    # Always enforce type=RES to exclude rentals (prevents metric pollution)
    resolved: Dict[str, Any] = {"type": "RES"}
    
    # Pass through standard filters
    for key in ("minbeds", "minbaths", "subtype"):
        value = filters_intent.get(key)
        if value is not None and value != "":
            resolved[key] = value
    
    # Handle price strategy (market-adaptive)
    strategy = filters_intent.get("price_strategy") or {}
    mode = strategy.get("mode")
    pct = strategy.get("value")
    
    median_list = market_stats.get("median_list_price")
    median_close = market_stats.get("median_close_price")
    
    if mode and pct:
        # Resolve percentage to actual dollar amount
        if mode == "maxprice_pct_of_median_list" and median_list:
            resolved["maxprice"] = int(median_list * float(pct))
            resolved["_resolved_from"] = f"{int(pct*100)}% of median list ${median_list:,.0f}"
        
        elif mode == "maxprice_pct_of_median_close" and median_close:
            resolved["maxprice"] = int(median_close * float(pct))
            resolved["_resolved_from"] = f"{int(pct*100)}% of median close ${median_close:,.0f}"
        
        elif mode == "minprice_pct_of_median_list" and median_list:
            resolved["minprice"] = int(median_list * float(pct))
            resolved["_resolved_from"] = f"{int(pct*100)}% of median list ${median_list:,.0f}"
        
        elif mode == "minprice_pct_of_median_close" and median_close:
            resolved["minprice"] = int(median_close * float(pct))
            resolved["_resolved_from"] = f"{int(pct*100)}% of median close ${median_close:,.0f}"
        
        else:
            # Fallback: can't resolve (missing market data), try absolute values
            print(f"⚠️  Cannot resolve price_strategy {mode}: missing market data")
            if filters_intent.get("maxprice"):
                resolved["maxprice"] = int(filters_intent["maxprice"])
            if filters_intent.get("minprice"):
                resolved["minprice"] = int(filters_intent["minprice"])
    
    else:
        # No price strategy - use absolute values if provided
        if filters_intent.get("maxprice") is not None:
            resolved["maxprice"] = int(filters_intent["maxprice"])
        if filters_intent.get("minprice") is not None:
            resolved["minprice"] = int(filters_intent["minprice"])
    
    return resolved


def build_filters_label(
    filters_intent: Dict[str, Any],
    resolved_filters: Dict[str, Any],
    market_stats: Dict[str, Optional[float]]
) -> str:
    """
    Build a human-readable label describing the applied filters.
    
    Used in PDF headers and emails to explain the filter criteria.
    
    Example outputs:
        "2+ beds, 2+ baths, under $1,680,000 (70% of Irvine median)"
        "4+ beds, all prices"
        "Condos, 1+ beds"
    """
    parts = []
    
    # Beds/baths
    if resolved_filters.get("minbeds"):
        parts.append(f"{resolved_filters['minbeds']}+ beds")
    if resolved_filters.get("minbaths"):
        parts.append(f"{resolved_filters['minbaths']}+ baths")
    
    # Subtype
    subtype = resolved_filters.get("subtype")
    if subtype == "SingleFamilyResidence":
        parts.append("SFR")
    elif subtype == "Condominium":
        parts.append("Condos")
    
    # Price (with explanation if resolved from strategy)
    resolved_from = resolved_filters.get("_resolved_from")
    if resolved_filters.get("maxprice"):
        price_str = f"under ${resolved_filters['maxprice']:,}"
        if resolved_from:
            price_str += f" ({resolved_from})"
        parts.append(price_str)
    elif resolved_filters.get("minprice"):
        price_str = f"over ${resolved_filters['minprice']:,}"
        if resolved_from:
            price_str += f" ({resolved_from})"
        parts.append(price_str)
    
    return ", ".join(parts) if parts else "All listings"


def elastic_widen_filters(
    filters_intent: Dict[str, Any],
    market_stats: Dict[str, Optional[float]],
    current_results_count: int,
    min_results: int = 6
) -> Optional[Dict[str, Any]]:
    """
    If current results are too low, suggest widened filters.
    
    Elastic widening strategy:
    1. First, expand price percentage (70% → 85% → 100%)
    2. Then, expand lookback days (handled by caller)
    
    Args:
        filters_intent: Original filters with price_strategy
        market_stats: Market median data
        current_results_count: How many results current filters returned
        min_results: Minimum acceptable results (default 6 for gallery)
    
    Returns:
        Widened filters_intent, or None if can't widen further
    """
    if current_results_count >= min_results:
        return None  # No widening needed
    
    strategy = filters_intent.get("price_strategy")
    if not strategy:
        return None  # Can't widen non-strategy filters automatically
    
    current_pct = strategy.get("value", 0)
    mode = strategy.get("mode", "")
    
    # Widening steps for max price strategies (expand cap)
    if "maxprice" in mode:
        widen_steps = [0.70, 0.85, 1.00, 1.20]
        for step in widen_steps:
            if step > current_pct:
                return {
                    **filters_intent,
                    "price_strategy": {**strategy, "value": step},
                    "_widened": True,
                    "_widened_reason": f"Expanded price range from {int(current_pct*100)}% to {int(step*100)}%"
                }
    
    # Widening steps for min price strategies (lower floor)
    elif "minprice" in mode:
        widen_steps = [1.50, 1.30, 1.10, 0.90]
        for step in widen_steps:
            if step < current_pct:
                return {
                    **filters_intent,
                    "price_strategy": {**strategy, "value": step},
                    "_widened": True,
                    "_widened_reason": f"Lowered price threshold from {int(current_pct*100)}% to {int(step*100)}%"
                }
    
    return None  # Can't widen further
