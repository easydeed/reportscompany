"""
AI-powered market insights using OpenAI.

V12: Generate contextual, professional market insights for email reports.
Uses GPT-4o-mini for fast, cost-effective insight generation.

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key
    AI_INSIGHTS_ENABLED: Set to "true" to enable (default: "false")
"""
import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_INSIGHTS_ENABLED = os.getenv("AI_INSIGHTS_ENABLED", "false").lower() == "true"

# System prompt for generating market insights
SYSTEM_PROMPT = """You are a warm, knowledgeable real estate market advisor helping agents connect with their clients. Generate concise, encouraging market insights for email reports.

Tone & Voice:
- Warm and optimistic, but grounded in data
- Speak as a trusted advisor sharing good news and opportunities
- Highlight positive trends and buyer/seller advantages
- Be encouraging without being pushy or salesy

Guidelines:
- Reference 2-3 specific numbers from the data to build credibility
- Keep insights to 2-3 sentences (40-60 words)
- Frame market conditions positively: "healthy activity", "strong demand", "excellent selection", "competitive pricing"
- Use action-oriented language: "presents opportunities", "ideal timing", "worth exploring"
- For slower markets, emphasize negotiating power and selection
- For hot markets, emphasize urgency and value retention
- Do not use emojis or exclamation marks
- Vary sentence structure - never start with "This" or "The market"
"""


def generate_insight(
    report_type: str,
    area: str,
    metrics: Dict,
    lookback_days: int = 30,
    filter_description: Optional[str] = None,
) -> Optional[str]:
    """
    Generate an AI-powered market insight blurb.
    
    Args:
        report_type: Type of report (market_snapshot, closed, new_listings_gallery, etc.)
        area: City or area name
        metrics: Dictionary of market metrics
        lookback_days: Period covered by the report
        filter_description: Optional filter criteria (e.g., "2+ beds, Condos")
    
    Returns:
        AI-generated insight string, or None if AI is disabled or fails
    """
    if not AI_INSIGHTS_ENABLED or not OPENAI_API_KEY:
        logger.debug("AI insights disabled or no API key")
        return None
    
    try:
        import httpx
        
        # Build context for the AI
        user_prompt = _build_prompt(report_type, area, metrics, lookback_days, filter_description)
        
        # Call OpenAI API
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 100,
                "temperature": 0.7,
            },
            timeout=10.0,
        )
        
        if response.status_code != 200:
            logger.warning(f"OpenAI API error: {response.status_code} - {response.text}")
            return None
        
        result = response.json()
        insight = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        if insight:
            logger.info(f"AI insight generated for {report_type} in {area}")
            return insight
        
        return None
        
    except Exception as e:
        logger.warning(f"AI insight generation failed: {e}")
        return None


def _build_prompt(
    report_type: str,
    area: str,
    metrics: Dict,
    lookback_days: int,
    filter_description: Optional[str] = None,
) -> str:
    """Build the user prompt with relevant metrics for the AI."""
    
    # Extract key metrics
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    total_closed = metrics.get("total_closed", 0)
    total_active = metrics.get("total_active", 0)
    total_listings = metrics.get("total_listings", total_active)
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    min_price = metrics.get("min_price")
    max_price = metrics.get("max_price")
    
    # Format prices
    def fmt_price(p):
        if not p:
            return "N/A"
        if p >= 1_000_000:
            return f"${p/1_000_000:.1f}M"
        return f"${p/1_000:,.0f}K"
    
    # Build prompt based on report type
    ctl_str = f"{ctl:.1f}%" if ctl else "N/A"
    dom_str = f"{avg_dom:.0f}" if avg_dom else "N/A"
    moi_str = f"{moi:.1f}" if moi else "N/A"
    
    if report_type == "market_snapshot":
        return f"""Generate an encouraging market insight for {area} based on the last {lookback_days} days:

Market Data:
- Closed Sales: {total_closed}
- Median Sale Price: {fmt_price(median_price)}
- Average Days on Market: {dom_str}
- Months of Inventory: {moi_str}
- Close-to-List Ratio: {ctl_str}

Write a 2-3 sentence warm, optimistic insight. Highlight what makes this an interesting time for buyers or sellers. Reference at least 2 specific numbers."""

    elif report_type == "closed":
        return f"""Generate an encouraging insight about recent home sales in {area} over the last {lookback_days} days:

Sales Data:
- Homes Sold: {total_closed}
- Median Sale Price: {fmt_price(median_price)}
- Average Days to Close: {dom_str}
- Close-to-List Ratio: {ctl_str}

Write a 2-3 sentence warm insight that celebrates the activity in this market. What does this tell us about buyer confidence and opportunities? Reference specific numbers."""

    elif report_type in ("new_listings_gallery", "new_listings"):
        filter_text = f" matching {filter_description}" if filter_description else ""
        return f"""Generate an encouraging insight about new listings in {area}{filter_text} over the last {lookback_days} days:

Listing Data:
- Fresh Listings: {total_listings}
- Median Asking Price: {fmt_price(median_price)}
- Price Range: {fmt_price(min_price)} to {fmt_price(max_price)}
- Average Days on Market: {dom_str}

Write a 2-3 sentence warm insight that excites buyers about these opportunities. Emphasize selection, variety, or value. Reference specific numbers."""

    else:
        # Generic prompt for other report types
        return f"""Generate an encouraging market insight for {area} based on the last {lookback_days} days:

- Total Listings: {total_listings}
- Median Price: {fmt_price(median_price)}
- Average Days on Market: {dom_str}

Write a 2-3 sentence warm, optimistic insight about opportunities in this market."""

