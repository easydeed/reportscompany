"""
AI-powered market narratives for PDF reports using GPT-4o.

Generates 2-3 sentence market commentary tailored to each of the 8 report
types.  Results are cached in Redis (24 h TTL) so repeat renders for the
same city + date + report type skip the API call.

Environment Variables:
    OPENAI_API_KEY:  Your OpenAI API key (required)
    REDIS_URL:       Redis connection string (for caching)
"""

import hashlib
import json
import logging
import os
from datetime import date
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

_CACHE_TTL = 86_400  # 24 hours

SYSTEM_PROMPT = (
    "You are a real estate market analyst writing for an agent's client-facing "
    "PDF report.  Be specific — reference the actual numbers provided.  "
    "Tone: confident, professional, helpful.  "
    "Write exactly 2-3 sentences.  No bullet points.  No markdown.  "
    "Do not start with 'The market'.  "
    "Write in a way that an agent would be proud to put their name on."
)


# ─── Per-report-type prompt templates ────────────────────────────────────────

def _prompt_new_listings_gallery(city: str, d: Dict) -> str:
    return (
        f"Based on the following data for {city} over the last "
        f"{d.get('lookback_days', 30)} days, write a 2-3 sentence insight "
        f"about new listings hitting the market.\n\n"
        f"Data: {d.get('listing_count', 0)} new listings, "
        f"median list price {_fp(d.get('median_list_price'))}, "
        f"price range {_fp(d.get('min_price'))} – {_fp(d.get('max_price'))}.\n\n"
        f"Focus on what's hitting the market, price positioning, and buyer opportunity."
    )


def _prompt_featured_listings(city: str, d: Dict) -> str:
    return (
        f"Based on the following data for {city}, write a 2-3 sentence insight "
        f"about featured premium properties.\n\n"
        f"Data: {d.get('listing_count', 0)} premium homes, "
        f"price range {_fp(d.get('min_price'))} – {_fp(d.get('max_price'))}, "
        f"city: {city}.\n\n"
        f"Focus on the premium nature and exclusivity of these properties."
    )


def _prompt_open_houses(city: str, d: Dict) -> str:
    return (
        f"Based on the following data for {city} this weekend, write a 2-3 "
        f"sentence insight about upcoming open houses.\n\n"
        f"Data: {d.get('listing_count', 0)} open houses scheduled, "
        f"over the last {d.get('lookback_days', 7)} days, city: {city}.\n\n"
        f"Focus on the weekend opportunity, what to expect, and how buyers "
        f"should prepare."
    )


def _prompt_market_snapshot(city: str, d: Dict) -> str:
    return (
        f"Based on the following data for {city} over the last "
        f"{d.get('lookback_days', 30)} days, write a 2-3 sentence market insight.\n\n"
        f"Data: {_fp(d.get('median_price'))} median sale price, "
        f"{d.get('avg_dom', 'N/A')} days on market, "
        f"{d.get('months_of_inventory', 'N/A')} months inventory, "
        f"{d.get('list_to_sale_ratio', 'N/A')}% list-to-sale ratio, "
        f"{d.get('closed_count', 0)} homes sold.\n\n"
        f"Provide a full market health analysis — is it a buyer's or seller's market?"
    )


def _prompt_closed(city: str, d: Dict) -> str:
    return (
        f"Based on the following data for {city} over the last "
        f"{d.get('lookback_days', 30)} days, write a 2-3 sentence insight "
        f"about recently closed sales.\n\n"
        f"Data: {d.get('closed_count', 0)} homes sold, "
        f"median sold price {_fp(d.get('median_price'))}, "
        f"average {d.get('avg_dom', 'N/A')} days on market, "
        f"{d.get('close_to_list_ratio', 'N/A')}% close-to-list ratio.\n\n"
        f"Focus on sales velocity, pricing accuracy, and market confidence."
    )


def _prompt_inventory(city: str, d: Dict) -> str:
    return (
        f"Based on the following data for {city}, write a 2-3 sentence insight "
        f"about current inventory.\n\n"
        f"Data: {d.get('active_count', 0)} active listings, "
        f"median active price {_fp(d.get('median_price'))}, "
        f"{d.get('months_of_inventory', 'N/A')} months supply.\n\n"
        f"Focus on supply assessment, buyer options, and pricing pressure."
    )


def _prompt_price_bands(city: str, d: Dict) -> str:
    bands_str = ", ".join(
        f"{b.get('label', '?')}: {b.get('count', 0)}"
        for b in (d.get("price_bands") or [])[:5]
    ) or "not available"
    return (
        f"Based on the following data for {city}, write a 2-3 sentence insight "
        f"about price distribution.\n\n"
        f"Data: median list price {_fp(d.get('median_price'))}, "
        f"price band breakdown — {bands_str}.\n\n"
        f"Focus on where activity is concentrated and segment opportunities."
    )


def _prompt_new_listings(city: str, d: Dict) -> str:
    return (
        f"Based on the following data for {city} over the last "
        f"{d.get('lookback_days', 30)} days, write a 2-3 sentence insight "
        f"about new inventory flow.\n\n"
        f"Data: {d.get('listing_count', 0)} new listings, "
        f"median list price {_fp(d.get('median_price'))}, "
        f"{d.get('active_count', 0)} total active.\n\n"
        f"Focus on inventory flow, what's coming to market, and trend direction."
    )


_PROMPT_BUILDERS = {
    "new_listings_gallery": _prompt_new_listings_gallery,
    "featured_listings": _prompt_featured_listings,
    "open_houses": _prompt_open_houses,
    "market_snapshot": _prompt_market_snapshot,
    "closed": _prompt_closed,
    "inventory": _prompt_inventory,
    "price_bands": _prompt_price_bands,
    "new_listings": _prompt_new_listings,
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fp(price) -> str:
    """Format a price for prompt text."""
    if not price:
        return "N/A"
    price = float(price)
    if price >= 1_000_000:
        return f"${price / 1_000_000:.1f}M"
    return f"${price / 1_000:,.0f}K"


def _cache_key(report_type: str, city: str) -> str:
    today = date.today().isoformat()
    raw = f"ai_narrative:{report_type}:{city}:{today}"
    return f"mr:ai_narrative:{hashlib.md5(raw.encode()).hexdigest()}"


def _redis():
    """Lazy Redis connection (returns None if unavailable)."""
    try:
        from .redis_utils import create_redis_connection
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return create_redis_connection(url)
    except Exception:
        return None


# ─── Public API ──────────────────────────────────────────────────────────────

def generate_market_pdf_narrative(
    report_type: str,
    city: str,
    data: Dict[str, Any],
) -> Optional[str]:
    """
    Generate a 2-3 sentence AI market narrative for a PDF report.

    Uses GPT-4o for high quality.  Results are cached in Redis for 24 hours
    keyed by ``report_type + city + today's date``.

    Returns *None* when the API key is missing or the call fails — callers
    should treat the narrative as optional.
    """
    if not OPENAI_API_KEY:
        logger.info("AI narrative skipped — OPENAI_API_KEY not set")
        return None

    # ── Check cache ──────────────────────────────────────────────────────
    key = _cache_key(report_type, city)
    r = _redis()
    if r:
        try:
            cached = r.get(key)
            if cached:
                logger.info("AI narrative cache HIT (%s / %s)", report_type, city)
                return cached.decode("utf-8") if isinstance(cached, bytes) else cached
        except Exception as e:
            logger.warning("Redis cache read failed (non-fatal): %s", e)

    # ── Build prompt ─────────────────────────────────────────────────────
    builder = _PROMPT_BUILDERS.get(report_type)
    if not builder:
        logger.warning("No prompt template for report_type=%s", report_type)
        return None

    user_prompt = builder(city, data)

    # ── Call GPT-4o ──────────────────────────────────────────────────────
    try:
        import httpx

        logger.info("Generating AI narrative for %s / %s via GPT-4o …", report_type, city)
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 150,
                "temperature": 0.7,
            },
            timeout=20.0,
        )

        if response.status_code != 200:
            logger.error("OpenAI API error: %d – %s", response.status_code, response.text[:300])
            return None

        body = response.json()
        narrative = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if narrative.startswith('"') and narrative.endswith('"'):
            narrative = narrative[1:-1]

        if not narrative:
            logger.warning("GPT-4o returned empty narrative")
            return None

        logger.info("AI narrative OK (%d chars): %s…", len(narrative), narrative[:80])

        # ── Write cache ──────────────────────────────────────────────────
        if r:
            try:
                r.setex(key, _CACHE_TTL, narrative)
            except Exception as e:
                logger.warning("Redis cache write failed (non-fatal): %s", e)

        return narrative

    except Exception as e:
        logger.error("AI narrative generation failed: %s", e)
        return None
