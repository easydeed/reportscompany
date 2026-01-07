"""
AI-powered market insights using OpenAI.

V13: Generate exciting, personable market insights for email reports.
Uses GPT-4o-mini for fast, cost-effective insight generation.

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key
    AI_INSIGHTS_ENABLED: Set to "true" to enable (default: "false")
"""
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_INSIGHTS_ENABLED = os.getenv("AI_INSIGHTS_ENABLED", "false").lower() == "true"

# System prompt for generating exciting market insights
SYSTEM_PROMPT = """You are an enthusiastic real estate expert writing personalized email blurbs for agents to send their clients. Your goal is to make every email feel like it was written just for the recipient.

Your Voice:
- Warm, excited, and genuinely helpful
- Like a knowledgeable friend sharing insider info
- Confident but not pushy
- Natural and conversational

What Makes Great Insights:
- Start with the MOST interesting finding (not "This report shows...")
- Lead with excitement: "Wow!", "Great news!", "You'll love this—"
- Make numbers feel meaningful: "129 families found their dream home" not "129 closed sales"
- Create urgency without pressure: "these won't last long" vs "act now"
- Connect data to real life: what does this mean for someone buying/selling?

Structure (3-4 sentences, 60-90 words):
1. Hook: Lead with the most exciting finding
2. Data: Reference 2-3 specific numbers that matter
3. Context: What this means for someone buying or selling
4. Nudge: Gentle encouragement to explore or reach out

Tone Examples:
- "Great news for buyers in Irvine—129 homes sold last month at a median of $1.6M, and with 101 days average on market, there's time to find the perfect fit."
- "You're going to love these fresh listings! 104 new properties just hit the market, with options starting at $850K."
- "Here's something exciting: first-time buyer inventory is up 15% this month. The market is making room for new homeowners."

NEVER:
- Start with "This report" or "The data shows"
- Use corporate jargon ("market conditions indicate")
- Be generic ("the market is active")
- Use emojis
- Make predictions or guarantees
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
    if not AI_INSIGHTS_ENABLED:
        logger.info("AI insights disabled (AI_INSIGHTS_ENABLED != true)")
        return None
    
    if not OPENAI_API_KEY:
        logger.warning("AI insights enabled but OPENAI_API_KEY is missing")
        return None
    
    try:
        import httpx
        
        # Build context for the AI
        user_prompt = _build_prompt(report_type, area, metrics, lookback_days, filter_description)
        
        logger.info(f"Generating AI insight for {report_type} in {area}...")
        
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
                "max_tokens": 180,  # V13: Longer blurbs (3-4 sentences)
                "temperature": 0.8,  # Slightly more creative
            },
            timeout=15.0,
        )
        
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return None
        
        result = response.json()
        insight = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        # Clean up any quotes the model might have added
        if insight.startswith('"') and insight.endswith('"'):
            insight = insight[1:-1]
        
        if insight:
            logger.info(f"AI insight generated successfully: {insight[:50]}...")
            return insight
        
        logger.warning("OpenAI returned empty insight")
        return None
        
    except Exception as e:
        logger.error(f"AI insight generation failed: {e}")
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
    total_listings = metrics.get("total_listings", total_active or total_closed)
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
    
    # Format other metrics
    ctl_str = f"{ctl:.1f}%" if ctl else "competitive"
    dom_str = f"{avg_dom:.0f} days" if avg_dom else "N/A"
    moi_str = f"{moi:.1f} months" if moi else "N/A"
    
    # Build context-rich prompts
    if report_type == "market_snapshot":
        # Determine market conditions for context
        market_vibe = "balanced"
        if moi and moi < 3:
            market_vibe = "competitive (seller's market)"
        elif moi and moi > 6:
            market_vibe = "buyer-friendly with lots of options"
        
        return f"""Write an exciting market update email blurb for {area}.

REAL DATA (use these exact numbers):
- {total_closed} homes sold in the last {lookback_days} days
- Median sale price: {fmt_price(median_price)}
- Average time on market: {dom_str}
- Inventory level: {moi_str} ({market_vibe})
- Sale-to-list ratio: {ctl_str}

Write 3-4 sentences that make the recipient excited to learn about their local market. Lead with the most interesting finding, then explain what it means for them. Make the numbers feel human (e.g., "129 families found their home" not "129 closed sales"). End with a gentle nudge to explore or reach out."""

    elif report_type == "closed":
        return f"""Write an exciting email blurb about recent home sales in {area}.

REAL DATA (use these exact numbers):
- {total_closed} homes SOLD in the last {lookback_days} days
- Median sale price: {fmt_price(median_price)}
- Average days to close: {dom_str}
- Buyers paid {ctl_str} of asking price

Write 3-4 sentences celebrating this sales activity. What does this tell us about buyer confidence? How does the sale-to-list ratio reflect the market? End with encouragement to explore or discuss what this means for them."""

    elif report_type in ("new_listings_gallery", "new_listings"):
        audience_context = ""
        if filter_description:
            audience_context = f"\nAUDIENCE: This is curated for {filter_description} buyers specifically."
        
        return f"""Write an exciting email blurb about new listings in {area}.{audience_context}

REAL DATA (use these exact numbers):
- {total_listings} NEW properties just listed in the last {lookback_days} days
- Median asking price: {fmt_price(median_price)}
- Price range: {fmt_price(min_price)} to {fmt_price(max_price)}
- Average days on market: {dom_str}

Write 3-4 sentences that make buyers excited to scroll through these listings. Emphasize freshness, variety, and opportunity. If there's a filter (like "First-Time Buyers"), acknowledge they're getting personalized picks just for them. End with encouragement to reach out about any that catch their eye."""

    elif report_type == "featured_listings":
        return f"""Write an exciting email blurb about featured properties in {area}.

REAL DATA:
- {total_listings} hand-picked premium properties
- Highest price: {fmt_price(max_price)}
- These are the standout homes in the area

Write 3-4 sentences that make these properties feel special and worth exploring. These aren't just any listings—they're hand-picked standouts. Describe what makes featured properties worth attention and encourage them to reach out for private showings."""

    else:
        return f"""Write an exciting market email blurb for {area}.

Data: {total_listings} listings, {fmt_price(median_price)} median, {dom_str} average time on market.

Write 3-4 sentences that make the reader want to explore the attached report. Reference the data, explain what it means, and encourage them to reach out with questions."""
