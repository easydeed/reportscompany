"""
AI-Generated Property Report Overview (Executive Summary)
==========================================================

Generates a concise, personalized executive summary for property reports
using OpenAI GPT-4o-mini. The summary sits at the beginning of the report
and gives the reader (typically a homeowner) a quick, digestible overview
of what the report contains and why it matters to them.

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SYSTEM_PROMPT = """You are an expert real estate analyst writing a concise executive summary for a property report.

Your audience is the property owner. The report was prepared by their real estate agent.

Your tone:
- Professional yet warm and approachable
- Confident and knowledgeable
- Reassuring—help the owner feel informed and empowered
- Use "your" to address the owner directly

Structure (4-5 short paragraphs, 180-250 words total):
1. **Opening** (1-2 sentences): Briefly introduce the report and the property.
2. **Property Snapshot** (2-3 sentences): Highlight the key property attributes that stand out.
3. **Market Position** (2-3 sentences): How this property compares to recent comparable sales in the area. Reference specific numbers (median price, price/sqft, etc.).
4. **Market Context** (1-2 sentences): If market trends data is available, briefly note whether it's a seller's or buyer's market and what that means for the owner.
5. **Closing** (1 sentence): Encourage them to review the full report and reach out to their agent.

CRITICAL RULES:
- NEVER fabricate numbers. Only reference data explicitly provided.
- If a data point is missing or zero, skip it gracefully.
- Keep paragraphs short (2-3 sentences max each).
- Do NOT use bullet points or numbered lists—write in flowing paragraphs.
- Do NOT use markdown formatting (no **, ##, etc.)—output plain text only.
- Do NOT mention "AI" or "generated." Write as if the agent prepared this summary.
- Do NOT use emojis.
"""


def generate_overview(
    property_ctx: Dict[str, Any],
    agent_ctx: Dict[str, Any],
    stats_ctx: Dict[str, Any],
    comparables: list,
    market_trends: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Generate an AI-powered executive summary for a property report.

    Args:
        property_ctx: The 'property' dict from the report context.
        agent_ctx: The 'agent' dict from the report context.
        stats_ctx: The 'stats' dict from the report context.
        comparables: List of comparable dicts from the report context.
        market_trends: Optional market trends dict (None if page excluded).

    Returns:
        Plain-text executive summary string, or None if generation fails.
    """
    if not OPENAI_API_KEY:
        logger.info("ai_overview: skipped — OPENAI_API_KEY not set")
        return None

    try:
        import httpx

        user_prompt = _build_prompt(property_ctx, agent_ctx, stats_ctx, comparables, market_trends)

        logger.info("ai_overview: generating executive summary…")

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
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=20.0,
        )

        if response.status_code != 200:
            logger.error("ai_overview: OpenAI API error %s — %s", response.status_code, response.text[:200])
            return None

        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        # Clean up stray quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]

        if text:
            logger.info("ai_overview: generated %d chars", len(text))
            return text

        logger.warning("ai_overview: OpenAI returned empty text")
        return None

    except Exception as exc:
        logger.error("ai_overview: generation failed — %s", exc)
        return None


# ─── Prompt Builder ─────────────────────────────────────────────────────────

def _fmt_price(val) -> str:
    """Format a numeric price for the prompt."""
    if not val:
        return "N/A"
    try:
        v = float(val)
        if v >= 1_000_000:
            return f"${v / 1_000_000:.2f}M"
        if v >= 1_000:
            return f"${v / 1_000:,.0f}K"
        return f"${v:,.0f}"
    except (ValueError, TypeError):
        return str(val)


def _build_prompt(
    prop: Dict[str, Any],
    agent: Dict[str, Any],
    stats: Dict[str, Any],
    comps: list,
    market: Optional[Dict[str, Any]],
) -> str:
    """Build the user prompt with all available report data."""

    lines = [
        "Write an executive summary for the following property report.",
        "",
        "--- PROPERTY ---",
        f"Address: {prop.get('street_address', '')}, {prop.get('city', '')}, {prop.get('state', '')} {prop.get('zip_code', '')}",
    ]

    # Property attributes
    attrs = []
    if prop.get("bedrooms"):
        attrs.append(f"{prop['bedrooms']} bed")
    if prop.get("bathrooms"):
        attrs.append(f"{prop['bathrooms']} bath")
    if prop.get("sqft"):
        attrs.append(f"{int(prop['sqft']):,} sqft")
    if prop.get("lot_size"):
        attrs.append(f"{int(prop['lot_size']):,} sqft lot")
    if prop.get("year_built"):
        attrs.append(f"built {prop['year_built']}")
    if prop.get("property_type"):
        attrs.append(prop["property_type"])
    if attrs:
        lines.append(f"Key attributes: {', '.join(attrs)}")

    if prop.get("assessed_value"):
        lines.append(f"Current assessed value: {_fmt_price(prop['assessed_value'])}")

    # Agent
    lines += [
        "",
        "--- AGENT ---",
        f"Prepared by: {agent.get('name', 'Your Agent')}",
        f"Company: {agent.get('company_name', '')}",
    ]

    # Comparable sales stats
    lines += [
        "",
        "--- COMPARABLE SALES ANALYSIS ---",
        f"Number of comparable sales analyzed: {stats.get('total_comps', 0)}",
    ]
    if stats.get("avg_price_per_sqft"):
        lines.append(f"Average price per sqft: ${stats['avg_price_per_sqft']}")
    if stats.get("price_low"):
        lines.append(f"Price range: {_fmt_price(stats['price_low'])} – {_fmt_price(stats['price_high'])}")
    if stats.get("avg_sqft"):
        lines.append(f"Average comp sqft: {stats['avg_sqft']:,}" if isinstance(stats['avg_sqft'], (int, float)) else f"Average comp sqft: {stats['avg_sqft']}")
    if stats.get("avg_days_on_market"):
        lines.append(f"Average days on market: {stats['avg_days_on_market']}")

    # Market trends (optional)
    if market:
        lines += ["", "--- MARKET TRENDS ---"]
        mc = market.get("market_condition") or {}
        if mc.get("label"):
            lines.append(f"Market condition: {mc['label']}")
        if mc.get("description"):
            lines.append(f"Description: {mc['description']}")

        moi = market.get("months_of_inventory") or {}
        if moi.get("formatted_current"):
            lines.append(f"Months of inventory: {moi['formatted_current']}")

        median = market.get("median_sale_price") or {}
        if median.get("formatted_current"):
            lines.append(f"Median sale price: {median['formatted_current']}")

        dom = market.get("avg_days_on_market") or {}
        if dom.get("formatted_current"):
            lines.append(f"Average days on market (area): {dom['formatted_current']}")

        al = market.get("active_listings") or {}
        if al.get("formatted_count"):
            lines.append(f"Active listings in area: {al['formatted_count']}")

    lines += [
        "",
        "Write the executive summary now. Remember: 4-5 short paragraphs, 180-250 words, plain text only, no formatting.",
    ]

    return "\n".join(lines)
