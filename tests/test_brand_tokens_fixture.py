"""The web's brand-token fixture still says what `themes.derive_theme` says.

`apps/web/lib/brand-tokens.ts` ports the part of `themes.py` the social
stories use, and `apps/web/__tests__/BrandTokens.test.ts` checks the port
against `apps/web/__tests__/fixtures/brand-tokens.json`. This keeps that
fixture equal to Python, so a change to the derivation here fails until the
port follows it — rather than the story and the report it shares quietly
choosing different inks.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))

from worker.themes import derive_theme  # noqa: E402

FIXTURE = REPO / "apps/web/__tests__/fixtures/brand-tokens.json"
KEYS = {"primary": "primary", "primaryInk": "primary_ink", "onPrimary": "on_primary",
        "tint": "tint", "primaryOnDark": "primary_on_dark"}


def test_the_fixture_is_what_python_derives():
    rows = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 200
    for row in rows:
        t = derive_theme(row["input"])
        assert {k: row[k] for k in KEYS} == {k: t[v] for k, v in KEYS.items()}, row["input"]
