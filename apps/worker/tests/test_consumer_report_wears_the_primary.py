"""The consumer PDF wears the account's PRIMARY, as /p and the agent's report do.

Decided 2026-11-04. `build_consumer_report_data` took `secondary_color or
primary_color`, so for a navy-primary, amber-secondary account the consumer PDF
(and /r, which follows it) was amber while /p for the same account was navy.

Red on main: the rendered consumer PDF's brand variables are amber's
derivation, not the navy primary's.
"""
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")

from worker import theme_registry  # noqa: E402
from worker.consumer_report_data import build_consumer_report_data  # noqa: E402
from worker.property_builder import PropertyReportBuilder  # noqa: E402
from worker.themes import TOKENS, derive_theme  # noqa: E402
from test_property_production_render import COMPS, SITEX  # noqa: E402

NAVY, AMBER = "#1B365D", "#F59E0B"


def _data(theme_id, primary=NAVY, secondary=AMBER):
    d = build_consumer_report_data(
        property_data=dict(SITEX), prop_address="1358 5th Street", prop_city="La Verne",
        prop_state="CA", prop_zip="91750", comparables=COMPS, theme_id=theme_id,
        primary_color=primary, secondary_color=secondary, agent_name="Zoe Noelle")
    d["sitex_data"] = dict(SITEX)
    return d


@pytest.fixture(autouse=True)
def _no_market_fetch(monkeypatch):
    monkeypatch.setattr(PropertyReportBuilder, "_fetch_market_trends", lambda self: None)


@pytest.mark.parametrize("theme_id", sorted(theme_registry.THEME_NUMBER_MAP))
def test_the_consumer_pdf_is_the_accounts_primary(theme_id):
    builder = PropertyReportBuilder(_data(theme_id))
    assert builder._get_theme_color().lower() == NAVY.lower()
    html = builder.render_html()
    # The page's brand inks are CSS variables (`--primary`, `--primary-ink`, …);
    # every one must be the navy primary's derivation. (A bare "amber hex
    # absent" check is wrong: a template comment quotes amber's contrast.)
    painted = {k.replace("-", "_"): v.lower() for k, v in
               re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", html)}
    want = derive_theme(NAVY)
    for token in TOKENS:
        assert painted.get(token) == want[token].lower(), (
            f"--{token.replace('_', '-')} is {painted.get(token)}, not the navy primary's "
            f"{want[token]} (amber's would be {derive_theme(AMBER)[token]})")


def test_no_primary_takes_the_default_accent_not_the_secondary():
    d = _data(next(iter(theme_registry.THEME_NUMBER_MAP)), primary="", secondary=AMBER)
    from worker.consumer_report_data import DEFAULT_THEME_ACCENT
    assert d["accent_color"] == DEFAULT_THEME_ACCENT
