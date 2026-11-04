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
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# THE SUMMARY IS WRITTEN FOR THE BOX IT GOES IN (D-349).
#
# It used to be prompted for "4-5 short paragraphs, 180-250 words" — the
# retired overview page's executive summary — and printed in the cover's "In
# short" panel, which holds five lines. Nothing trimmed it, so every cover
# showed the introduction and stopped. Measured 2026-11-04 in Chromium on the
# three live themes: 336 characters fills five lines on all three; 354 runs to
# six on harbor and linen. So the prompt asks for 300 (a margin for wide
# glyphs: "$", digits, capitals), and `fit_summary` holds 330 as the ceiling.
SUMMARY_TARGET_CHARS = 300
SUMMARY_MAX_CHARS = 330

SYSTEM_PROMPT = f"""You are an expert real estate analyst writing the two- or three-sentence summary that sits on the cover of a property report, under the heading "In short".

Your audience is the reader of the report. The report was prepared by their real estate agent.

Your tone:
- Professional yet warm and approachable
- Plain and specific: one clear point, with a number that supports it
- Use "your" to address the reader directly

Length and shape:
- ONE paragraph, two or three sentences, at most {SUMMARY_TARGET_CHARS} characters including spaces. The box holds five short lines; anything longer is cut off.
- Say what the comparable sales show about this home, and the one fact that matters most (for example how many sold, how quickly, or how the home compares on size or lot).

CRITICAL RULES:
- NEVER fabricate numbers. Only reference data explicitly provided.
- Do NOT state a value, price or estimate for the reader's home. The report gives the range of the comparable sales on its own page, with how it was made.
- Do NOT state a time period or distance unless it is given in the data.
- If a data point is missing or zero, skip it gracefully.
- Plain text only: no bullet points, no markdown, no line breaks, no emojis.
- Do NOT mention "AI" or "generated." Write as if the agent prepared this summary.
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
                # ~300 characters is ~70 tokens; this is a ceiling, not a target.
                "max_tokens": 120,
                "temperature": 0.7,
            },
            timeout=20.0,
        )

        if response.status_code != 200:
            logger.error("ai_overview: OpenAI API error %s — %s", response.status_code, response.text[:200])
            return None

        result = response.json()
        text = fit_summary(result.get("choices", [{}])[0].get("message", {}).get("content", ""))

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
        f"Write the cover summary now: one paragraph, at most {SUMMARY_TARGET_CHARS} characters, plain text.",
    ]

    return "\n".join(lines)


def fit_summary(text: Optional[str]) -> str:
    """One paragraph that fits the cover's "In short" box.

    Whitespace and paragraph breaks collapse to single spaces (the box is one
    paragraph). Over `SUMMARY_MAX_CHARS`, it is cut at the last full sentence
    that fits, so the box never ends on an ellipsis mid-thought. A first
    sentence that is itself too long is left whole: the box's line clamp ends
    it on an ellipsis, which is better than an empty panel.
    """
    text = " ".join((text or "").split())
    if len(text) <= SUMMARY_MAX_CHARS:
        return text
    head = text[:SUMMARY_MAX_CHARS + 1]
    ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", head)]
    return head[:ends[-1]].strip() if ends else text
