"""The web report pages wear the PDF's colour, by the PDF's rule (Design's digital-report handoff).

/p/{code} and /r/{id} read `theme_tokens` from the API and never compute a
colour. The API computes them with `api/themes.py`, which must be the worker's
`themes.py` exactly, from the colour the PDF of that document uses:

  * property report: accent, else brand primary, else the theme default
    (`PropertyReportBuilder._get_theme_color`, `_THEME_DEFAULT_COLORS`);
  * consumer report: secondary, else primary, else the default accent, on the
    account's default theme (`consumer_report_data`).
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
for p in ("apps/api/src", "apps/worker/src"):
    sys.path.insert(0, str(REPO / p))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")

from api.services import report_theme  # noqa: E402
from api import theme_registry as api_registry  # noqa: E402
from worker import consumer_report_data  # noqa: E402
from worker.property_builder import PropertyReportBuilder  # noqa: E402
from worker.themes import TOKENS, derive_theme  # noqa: E402

BRANDS = ["#DC2626", "#F59E0B", "#1B365D", "#84CC16", "#0D9488", "#FFFFFF", "#000000", "#7C3AED"]


def test_the_api_derivation_is_the_workers_file():
    api = (REPO / "apps/api/src/api/themes.py").read_bytes()
    worker = (REPO / "apps/worker/src/worker/themes.py").read_bytes()
    assert api == worker, (
        "apps/api/src/api/themes.py has drifted from apps/worker/src/worker/themes.py. "
        "Copy the worker's file over it: a page token must be the token the PDF printed.")


@pytest.mark.parametrize("brand", BRANDS)
def test_the_page_tokens_are_the_pdfs(brand):
    assert report_theme.tokens_for(brand) == {k: derive_theme(brand)[k] for k in TOKENS}


def test_no_colour_gives_no_tokens():
    assert report_theme.tokens_for(None) is None
    assert report_theme.tokens_for("") is None
    assert report_theme.tokens_for("not-a-colour") is None


def test_the_theme_defaults_are_the_pdfs():
    by_id = {i: PropertyReportBuilder._THEME_DEFAULT_COLORS[name]
             for i, name in api_registry.THEME_NUMBER_MAP.items()}
    assert report_theme.THEME_DEFAULT_COLORS == by_id
    assert report_theme.CONSUMER_DEFAULT_ACCENT == consumer_report_data.DEFAULT_THEME_ACCENT


def test_the_property_page_takes_the_accent_first():
    some = next(iter(api_registry.THEME_NUMBER_MAP))
    assert report_theme.property_report_color("#123456", "#abcdef", some) == "#123456"
    assert report_theme.property_report_color(None, "#abcdef", some) == "#abcdef"
    assert report_theme.property_report_color(None, None, some) == report_theme.THEME_DEFAULT_COLORS[some]
    # A retired or unknown theme falls back to the registry default, as the PDF does.
    assert report_theme.property_report_color(None, None, 999) == \
        report_theme.THEME_DEFAULT_COLORS[api_registry.DEFAULT_THEME_ID]


def test_the_consumer_page_takes_the_secondary_first():
    """The consumer PDF's own rule (consumer_report_data.py, `accent_color`):
    for a navy-primary, amber-secondary account the PDF is amber, so the page is."""
    assert report_theme.consumer_report_color("#1B365D", "#F59E0B") == "#F59E0B"
    assert report_theme.consumer_report_color("#1B365D", None) == "#1B365D"
    assert report_theme.consumer_report_color(None, None) == report_theme.CONSUMER_DEFAULT_ACCENT
    src = (REPO / "apps/worker/src/worker/consumer_report_data.py").read_text(encoding="utf-8")
    assert '"accent_color": secondary_color or primary_color or DEFAULT_THEME_ACCENT' in src
