"""
Shared Jinja2 Template Filters
===============================

Plain module-level functions used by both PropertyReportBuilder and
MarketReportBuilder.  Extracted from PropertyReportBuilder to avoid
coupling the market builder to the property class.

Usage:
    from worker.template_filters import format_currency, format_currency_short, format_number, truncate
"""

from typing import Any


def format_currency(value: Any) -> str:
    """Format number as currency: 470000 → '$470,000'."""
    if value is None:
        return "N/A"
    try:
        return f"${int(float(value)):,}"
    except (ValueError, TypeError):
        return str(value)


def format_number(value: Any) -> str:
    """Format number with commas: 1234 → '1,234'."""
    if value is None:
        return "N/A"
    try:
        return f"{int(float(value)):,}"
    except (ValueError, TypeError):
        return str(value)


def format_currency_short(value: Any) -> str:
    """Format as short currency: 470000 → '$470k', 1200000 → '$1.2M'."""
    if value is None:
        return "-"
    try:
        val = float(value)
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        elif val >= 1_000:
            return f"${val / 1_000:.0f}k"
        else:
            return f"${val:.0f}"
    except (ValueError, TypeError):
        return str(value)


def truncate(value: Any, length: int = 40, suffix: str = "...") -> str:
    """Truncate string to specified length."""
    if value is None:
        return ""
    text = str(value)
    if len(text) <= length:
        return text
    return text[: length - len(suffix)] + suffix
