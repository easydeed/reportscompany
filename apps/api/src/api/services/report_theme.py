"""The colour and theme a report's web pages wear: the same ones its PDF wears.

Design's digital-report handoff (2026-11-04) makes /p/{code} and /r/{id} the
PDF seen on a phone. The pages read the PDF's derived tokens — `primary`,
`primary_ink`, `on_primary`, `tint`, `primary_on_dark`, `display_ink` — and
never compute a colour themselves. This is where the API supplies them.

`api/themes.py` is the worker's `themes.py`, byte for byte
(`tests/test_api_themes_is_the_workers.py`), so a token on the page is the
token the PDF printed. The colour each page derives from is the PDF's own rule
for that document:

  * property report (/p) — `PropertyReportBuilder._get_theme_color`: the
    report's `accent_color`, else the brand's primary colour, else the theme's
    built-in default (`_THEME_DEFAULT_COLORS`). The wizard always stores an
    accent, so in practice it is the accent.
  * consumer report (/r) — `consumer_report_data.build_consumer_report_data`:
    the account's `secondary_color`, else its `primary_color`, else the
    theme default accent; on the account's `default_theme_id`.

`tests/test_report_theme_matches_the_pdf.py` holds the constants here to the
worker's.
"""
from typing import Dict, Optional

from ..theme_registry import DEFAULT_THEME_ID, THEME_NUMBER_MAP
from ..themes import TOKENS, derive_theme

#: `PropertyReportBuilder._THEME_DEFAULT_COLORS`, keyed by theme id so this file
#: names no theme (tests/test_rename_scope_numbers_are_current.py).
THEME_DEFAULT_COLORS: Dict[int, str] = {2: "#FF6B5B", 3: "#1a1a1a", 5: "#15216E"}

#: `consumer_report_data.DEFAULT_THEME_ACCENT`.
CONSUMER_DEFAULT_ACCENT = "#34d1c3"


def resolve_theme_id(theme_id) -> int:
    try:
        n = int(theme_id)
    except (TypeError, ValueError):
        return DEFAULT_THEME_ID
    return n if n in THEME_NUMBER_MAP else DEFAULT_THEME_ID


def tokens_for(color: Optional[str]) -> Optional[Dict[str, str]]:
    """The PDF's tokens for one colour, or None when there is no usable colour
    (the page then renders on its fixed neutral, visibly unbranded)."""
    if not color:
        return None
    try:
        derived = derive_theme(color)
    except (ValueError, TypeError):
        return None
    return {k: derived[k] for k in TOKENS}


def property_report_color(accent_color: Optional[str], brand_primary: Optional[str],
                          theme_id) -> str:
    return accent_color or brand_primary or THEME_DEFAULT_COLORS[resolve_theme_id(theme_id)]


def consumer_report_color(primary_color: Optional[str]) -> str:
    """The consumer PDF's rule (`build_consumer_report_data`): the account's
    primary, else the default accent. Secondary plays no part, as on /p."""
    return primary_color or CONSUMER_DEFAULT_ACCENT
