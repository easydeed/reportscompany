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

def _extract(d: Dict) -> Dict[str, Any]:
    """
    Normalize the varied data shapes builders pass in.

    Market snapshot results nest data under `counts` and `metrics`, while some
    older callers pass flat keys. This helper flattens both shapes so the
    prompt builders can always read the values they need.
    """
    counts = d.get("counts") or {}
    metrics = d.get("metrics") or {}
    listings = d.get("listings") or d.get("listings_sample") or []

    listing_count = (
        d.get("listing_count")
        or d.get("total_listings")
        or counts.get("Active")
        or len(listings)
        or 0
    )

    list_prices = [l.get("list_price") for l in listings if l.get("list_price")]
    min_price = d.get("min_price") or (min(list_prices) if list_prices else None)
    max_price = d.get("max_price") or (max(list_prices) if list_prices else None)

    return {
        "closed_count": counts.get("Closed") if counts.get("Closed") is not None else d.get("closed_count", 0),
        "active_count": counts.get("Active") if counts.get("Active") is not None else d.get("active_count", 0),
        "new_listings": (
            counts.get("NewListings")
            if counts.get("NewListings") is not None
            else metrics.get("new_listings_count")
            if metrics.get("new_listings_count") is not None
            else d.get("new_listings", 0)
        ),
        "listing_count": listing_count,
        "median_price": (
            metrics.get("median_close_price")
            or metrics.get("median_sold_price")
            or metrics.get("median_list_price")
            or d.get("median_price")
        ),
        "median_list_price": metrics.get("median_list_price") or d.get("median_list_price"),
        "median_close_price": metrics.get("median_close_price") or metrics.get("median_sold_price") or d.get("median_close_price"),
        "avg_dom": metrics.get("avg_dom") or metrics.get("median_dom") or d.get("avg_dom", "N/A"),
        "months_of_inventory": metrics.get("months_of_inventory") or d.get("months_of_inventory", "N/A"),
        "list_to_sale_ratio": metrics.get("list_to_sale_ratio") or metrics.get("sale_to_list_ratio") or d.get("list_to_sale_ratio", "N/A"),
        "close_to_list_ratio": metrics.get("close_to_list_ratio") or metrics.get("sale_to_list_ratio") or d.get("close_to_list_ratio", "N/A"),
        "min_price": min_price,
        "max_price": max_price,
        "price_bands": d.get("price_bands") or metrics.get("price_bands") or [],
        "lookback_days": d.get("lookback_days") or d.get("period_days") or 30,
    }


def _prompt_new_listings_gallery(city: str, d: Dict) -> str:
    x = _extract(d)
    return (
        f"Based on the following data for {city} over the last "
        f"{x['lookback_days']} days, write a 2-3 sentence insight "
        f"about new listings hitting the market.\n\n"
        f"Data: {x['listing_count']} new listings, "
        f"median list price {_fp(x['median_list_price'])}, "
        f"price range {_fp(x['min_price'])} – {_fp(x['max_price'])}.\n\n"
        f"Focus on what's hitting the market, price positioning, and buyer opportunity."
    )


def _prompt_featured_listings(city: str, d: Dict) -> str:
    x = _extract(d)
    return (
        f"Based on the following data for {city}, write a 2-3 sentence insight "
        f"about featured premium properties.\n\n"
        f"Data: {x['listing_count']} premium homes, "
        f"price range {_fp(x['min_price'])} – {_fp(x['max_price'])}, "
        f"city: {city}.\n\n"
        f"Focus on the premium nature and exclusivity of these properties."
    )


def _prompt_open_houses(city: str, d: Dict) -> str:
    x = _extract(d)
    return (
        f"Based on the following data for {city} this weekend, write a 2-3 "
        f"sentence insight about upcoming open houses.\n\n"
        f"Data: {x['listing_count']} open houses scheduled, "
        f"over the last {d.get('lookback_days', 7)} days, city: {city}.\n\n"
        f"Focus on the weekend opportunity, what to expect, and how buyers "
        f"should prepare."
    )


def _prompt_market_snapshot(city: str, d: Dict) -> str:
    x = _extract(d)
    return (
        f"Based on the following data for {city} over the last "
        f"{x['lookback_days']} days, write a 2-3 sentence market insight.\n\n"
        f"Data: {_fp(x['median_price'])} median sale price, "
        f"{x['closed_count']} homes sold, "
        f"{x['active_count']} active listings, "
        f"{x['new_listings']} new listings, "
        f"{x['avg_dom']} days on market, "
        f"{x['months_of_inventory']} months inventory, "
        f"{x['list_to_sale_ratio']}% list-to-sale ratio.\n\n"
        f"Provide a full market health analysis — is it a buyer's or seller's market?"
    )


def _prompt_closed(city: str, d: Dict) -> str:
    x = _extract(d)
    return (
        f"Based on the following data for {city} over the last "
        f"{x['lookback_days']} days, write a 2-3 sentence insight "
        f"about recently closed sales.\n\n"
        f"Data: {x['closed_count']} homes sold, "
        f"median sold price {_fp(x['median_close_price'] or x['median_price'])}, "
        f"average {x['avg_dom']} days on market, "
        f"{x['close_to_list_ratio']}% close-to-list ratio.\n\n"
        f"Focus on sales velocity, pricing accuracy, and market confidence."
    )


def _prompt_inventory(city: str, d: Dict) -> str:
    x = _extract(d)
    return (
        f"Based on the following data for {city}, write a 2-3 sentence insight "
        f"about current inventory.\n\n"
        f"Data: {x['active_count']} active listings, "
        f"median active price {_fp(x['median_list_price'] or x['median_price'])}, "
        f"{x['months_of_inventory']} months supply.\n\n"
        f"Focus on supply assessment, buyer options, and pricing pressure."
    )


def _prompt_price_bands(city: str, d: Dict) -> str:
    x = _extract(d)
    bands_str = ", ".join(
        f"{b.get('label', '?')}: {b.get('count', 0)}"
        for b in (x["price_bands"] or [])[:5]
    ) or "not available"
    return (
        f"Based on the following data for {city}, write a 2-3 sentence insight "
        f"about price distribution.\n\n"
        f"Data: median list price {_fp(x['median_list_price'] or x['median_price'])}, "
        f"price band breakdown — {bands_str}.\n\n"
        f"Focus on where activity is concentrated and segment opportunities."
    )


def _prompt_new_listings(city: str, d: Dict) -> str:
    x = _extract(d)
    return (
        f"Based on the following data for {city} over the last "
        f"{x['lookback_days']} days, write a 2-3 sentence insight "
        f"about new inventory flow.\n\n"
        f"Data: {x['new_listings'] or x['listing_count']} new listings, "
        f"median list price {_fp(x['median_list_price'] or x['median_price'])}, "
        f"{x['active_count']} total active.\n\n"
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


def _cache_key(report_type: str, city: str, data: Optional[Dict] = None) -> str:
    """
    Cache key includes a short hash of the report's counts + key metrics so
    different data (e.g. new snapshot the next day, different zip filter)
    does not get served a stale narrative.
    """
    today = date.today().isoformat()
    data_hash = ""
    if data is not None:
        fingerprint = {
            "counts": data.get("counts") or {},
            "listing_count": data.get("listing_count") or data.get("total_listings") or 0,
            "median_close_price": (data.get("metrics") or {}).get("median_close_price"),
            "median_list_price": (data.get("metrics") or {}).get("median_list_price"),
        }
        data_hash = hashlib.md5(
            json.dumps(fingerprint, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
    raw = f"ai_narrative:{report_type}:{city}:{today}:{data_hash}"
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
    key = _cache_key(report_type, city, data)
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
