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


def format_measure(value: Any) -> str:
    """A measured quantity as a person writes it: `1949`, `2`, `1.5`, `0.58`.

    D-125. `_safe_num` returns `float(val)` and the analysis table printed it
    raw, so every cell that is not currency-formatted carried a `.0`:

        Living Area   786.0    770.0    940.0    912.0
        Year Built    1949.0   1910.0   1953.0   1952.0
        Bedrooms      2.0      3.0      2.0      3.0

    `1949.0` as a year and `2.0` as a bedroom count read as machine output in
    a document a seller is meant to take seriously.

    **NOT `int()`.** `1.5` and `2.5` are real bathroom counts and `0.58` is a
    real distance, so the rule is "drop a trailing `.0`, keep a genuine
    fraction". `compute.price_bands.format_price` already does exactly this
    for currency and is the precedent.

    **NO THOUSANDS SEPARATOR.** The commonest user is Year Built, and `1,949`
    is a wrong year. Living Area and Lot Size keep `format_number`, which
    groups and is right for them.

    Anything unparseable passes through unchanged, so `ABSENT` ("-") survives
    — the same contract `format_currency` and `format_number` have, which
    D-137 relies on.
    """
    if value is None:
        return "-"
    try:
        num = float(value)
    except (ValueError, TypeError):
        return str(value)
    if num == int(num):
        return str(int(num))
    # `:g` rather than rstrip: it keeps 0.58 at two places and 1.5 at one,
    # where a fixed format has to choose and gets one of them wrong.
    return f"{num:g}"


def format_currency_short(value: Any, upper: bool = False) -> str:
    """Format as short currency: 470000 → '$470k', 1200000 → '$1.2M'.

    `upper=True` gives Design's market casing — '$470K', '$1.2M'. A PARAMETER
    rather than a second formatter: the market `_v2` page specifies an
    uppercase thousands suffix and every other surface already ships the
    lowercase one, so changing this globally would be a product-visible edit to
    emails and the live report for a casing preference on one page. Two money
    formatters is the duplication this repo keeps filing; one with a flag is
    not.
    """
    if value is None:
        return "-"
    try:
        val = float(value)
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        elif val >= 1_000:
            return f"${val / 1_000:.0f}{'K' if upper else 'k'}"
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
