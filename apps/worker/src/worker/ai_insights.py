"""
AI-powered market insights using OpenAI.

V14: Sender-aware, audience-aware insights with engagement focus.
- Adapts tone based on sender type (Agent vs Affiliate)
- References total found vs shown listings
- Longer, more engaging 4-5 sentence format
- Uses GPT-4o-mini for fast, cost-effective generation

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

# =============================================================================
# SYSTEM PROMPTS BY SENDER TYPE
# =============================================================================

AGENT_SYSTEM_PROMPT = """You are a warm, personable real estate agent writing to your client. You have a personal relationship with them and want to help them find their perfect home.

Your Voice:
- Warm, personal, and genuinely caring
- "I" statements - you personally selected these listings
- Like a trusted friend who happens to be a real estate expert
- Excited to share what you've found for them specifically

Structure (4-5 sentences, 80-120 words):
1. Personal hook - acknowledge their search/needs
2. What you found - reference specific numbers
3. Why these are special - your expert perspective
4. What stands out - highlight something interesting
5. Invitation - encourage them to reach out to you personally

Tone Examples:
- "I've been keeping an eye out for you, and this week delivered some exciting options."
- "I handpicked these 24 properties from over 100 new listings because they match what we discussed."
- "Let me know which ones catch your eye—I'd love to set up showings this weekend."

NEVER:
- Sound corporate or automated
- Use "we" (you're one person, their agent)
- Be generic—make it feel personal
- Use emojis
"""

AFFILIATE_SYSTEM_PROMPT = """You are a professional market analyst writing an informative real estate update on behalf of a title company or real estate services firm. You're providing valuable market intelligence to help readers stay informed.

Your Voice:
- Professional, informative, and helpful
- "We" statements - representing the company
- Like a trusted market advisor sharing insights
- Focused on market trends and opportunities

Structure (4-5 sentences, 80-120 words):
1. Market hook - what's happening in the market right now
2. The numbers - reference specific data points
3. What it means - interpret the data for readers
4. Highlights - what makes this selection noteworthy
5. Call to action - encourage engagement with an agent

Tone Examples:
- "The Irvine market saw strong activity this week with 104 new listings hitting the market."
- "We've curated 24 standout properties that represent the best opportunities across all price points."
- "Reach out to your real estate professional to explore these options before they're gone."

NEVER:
- Sound too casual or personal
- Use "I" (you represent a company)
- Make it feel like a form letter
- Use emojis
"""


def generate_insight(
    report_type: str,
    area: str,
    metrics: Dict,
    lookback_days: int = 30,
    filter_description: Optional[str] = None,
    sender_type: str = "REGULAR",
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: Optional[str] = None,
) -> Optional[str]:
    """
    Generate an AI-powered market insight blurb.
    
    Args:
        report_type: Type of report (market_snapshot, closed, new_listings_gallery, etc.)
        area: City or area name
        metrics: Dictionary of market metrics
        lookback_days: Period covered by the report
        filter_description: Optional filter criteria (e.g., "2+ beds, Condos")
        sender_type: "REGULAR" (agent) or "INDUSTRY_AFFILIATE" (title company)
        total_found: Total listings matching criteria in market
        total_shown: How many listings displayed in email
        audience_name: Preset name like "First-Time Buyers", "Luxury", etc.
    
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
        
        # Select system prompt based on sender type
        is_agent = sender_type == "REGULAR"
        system_prompt = AGENT_SYSTEM_PROMPT if is_agent else AFFILIATE_SYSTEM_PROMPT
        
        # Build context for the AI
        user_prompt = _build_prompt(
            report_type=report_type,
            area=area,
            metrics=metrics,
            lookback_days=lookback_days,
            filter_description=filter_description,
            is_agent=is_agent,
            total_found=total_found,
            total_shown=total_shown,
            audience_name=audience_name,
        )
        
        logger.info(f"Generating AI insight for {report_type} in {area} (sender: {sender_type})...")
        
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
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 250,  # V14: Longer responses (4-5 sentences)
                "temperature": 0.8,
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
            logger.info(f"AI insight generated successfully: {insight[:60]}...")
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
    is_agent: bool = True,
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: Optional[str] = None,
) -> str:
    """Build the user prompt with relevant metrics for the AI."""
    
    # Extract key metrics
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    total_closed = metrics.get("total_closed", 0)
    total_active = metrics.get("total_active", 0)
    total_listings = total_found or metrics.get("total_listings", total_active or total_closed)
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
    
    # Sender context
    sender_context = "You are their personal real estate agent." if is_agent else "You represent a title company/real estate services firm."
    
    # Curation context
    curation_context = ""
    if total_shown and total_found and total_shown < total_found:
        if is_agent:
            curation_context = f"\nYou've hand-selected {total_shown} properties from {total_found} available because these best match their needs."
        else:
            curation_context = f"\nWe've curated {total_shown} highlights from {total_found} total listings to showcase the best opportunities."
    
    # Audience context
    audience_context = ""
    if audience_name:
        audience_context = f"\nThis report is specifically for: {audience_name} buyers."
    
    # Build prompts based on report type
    if report_type == "market_snapshot":
        market_vibe = "balanced"
        if moi and moi < 3:
            market_vibe = "competitive (seller's market)"
        elif moi and moi > 6:
            market_vibe = "buyer-friendly with lots of options"
        
        return f"""{sender_context}

Write an engaging market update for {area}.{audience_context}

REAL DATA:
- {total_closed} homes sold in the last {lookback_days} days
- Median sale price: {fmt_price(median_price)}
- Average time on market: {dom_str}
- Inventory level: {moi_str} ({market_vibe})
- Sale-to-list ratio: {ctl_str}

Write 4-5 warm, engaging sentences. Make the reader feel informed and excited about the market. Reference specific numbers to build trust. End with an invitation to connect."""

    elif report_type == "closed":
        return f"""{sender_context}

Write about recent home sales in {area}.{audience_context}

REAL DATA:
- {total_closed} homes SOLD in the last {lookback_days} days
- Median sale price: {fmt_price(median_price)}
- Average days to close: {dom_str}
- Buyers paid {ctl_str} of asking price

Write 4-5 engaging sentences celebrating this activity. What does it mean for buyers and sellers? Make the numbers feel meaningful. End with encouragement to reach out."""

    elif report_type in ("new_listings_gallery", "new_listings"):
        return f"""{sender_context}{curation_context}{audience_context}

Write about new listings in {area}.

REAL DATA:
- {total_found} total new properties in the last {lookback_days} days
- Showing: {total_shown} curated selections
- Median asking price: {fmt_price(median_price)}
- Price range: {fmt_price(min_price)} to {fmt_price(max_price)}
- Average days on market: {dom_str}

Write 4-5 engaging sentences. Acknowledge you've curated these specifically for them. Build excitement about the selection. Highlight the variety or value. End by inviting them to reach out about any that catch their eye."""

    elif report_type == "featured_listings":
        return f"""{sender_context}{audience_context}

Write about featured/premium properties in {area}.

REAL DATA:
- {total_shown} hand-picked premium properties
- Highest price: {fmt_price(max_price)}

Write 4-5 engaging sentences. These are the standout properties—make them feel special. Emphasize quality over quantity. Create desire to see them. Invite them to schedule private showings."""

    else:
        return f"""{sender_context}{audience_context}

Write a market update for {area}.

Data: {total_listings} listings, {fmt_price(median_price)} median, {dom_str} average time on market.

Write 4-5 engaging sentences that make the reader want to explore the attached report and reach out."""


# =============================================================================
# AUDIENCE-BASED LISTING CAPS
# =============================================================================

# Default caps for email (PDF caps are fixed at 9 for layout)
AUDIENCE_EMAIL_CAPS = {
    "all": 24,               # All Listings - comprehensive view
    "first_time_buyers": 24, # First-Time Buyers - need lots of options
    "families": 18,          # Family Homes - moderate selection
    "condo": 18,             # Condo Watch - moderate selection
    "luxury": 8,             # Luxury - curated, exclusive
    "investors": 12,         # Investors - focused on deals
    "default": 24,           # Default fallback
}

def get_email_listing_cap(audience_key: str = "default") -> int:
    """
    Get the email listing cap for a given audience.
    
    Args:
        audience_key: The audience preset key (e.g., "first_time_buyers", "luxury")
    
    Returns:
        Maximum number of listings to show in email
    """
    return AUDIENCE_EMAIL_CAPS.get(audience_key, AUDIENCE_EMAIL_CAPS["default"])
