"""Defects closed on 2026-10-30 by checking the live product, pinned so they stay closed.

D-126, D-127, D-128 and D-143 were filed against the five retired property
themes (teal, bold, classic, elegant, modern), whose templates were deleted on
2026-10-27. Verified against what renders today — the `_v2` chain every live
theme uses — rather than closed on the strength of the deletion alone:

  D-126  sales charts with no values and no axis: the live chart has a y-axis
  D-127  "PIQ" as a column label: not in any live template
  D-128  the near-empty executive-summary page: `overview` is not a page
  D-143  placeholder phone and email fallbacks: none in any live template

D-227 (Jerry: delete) and D-052 (delete after proving nothing uses it) are
deletions; these keep them deleted.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "apps/worker/tests"))

from worker.property_builder import PropertyReportBuilder  # noqa: E402
from worker.theme_registry import THEME_TEMPLATES  # noqa: E402
from _template_chain import chain  # noqa: E402


def _live_property_templates() -> str:
    paths = {p for theme in THEME_TEMPLATES for p in chain(theme)}
    assert paths, "no live property templates found"
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(paths))


def test_d127_no_live_template_says_piq():
    assert not re.search(r"\bPIQ\b", _live_property_templates())


def test_d126_the_live_chart_has_an_axis():
    text = _live_property_templates()
    assert "chart-yaxis" in text and re.search(r'class="chart-yaxis"', text)


def test_d128_there_is_no_overview_page():
    assert "overview" not in PropertyReportBuilder.V2_PAGE_ORDER


def test_d143_no_placeholder_contact_fallback():
    text = _live_property_templates()
    for placeholder in ("(000) 000-0000", "agent@example.com", "info@example.com", "555-1234"):
        assert placeholder not in text, placeholder


def _tracked(path: str) -> list:
    out = subprocess.run(["git", "ls-files", path], cwd=REPO, capture_output=True, text=True, check=True)
    return [l for l in out.stdout.splitlines() if l]


def test_d227_the_unlinked_plan_page_and_its_parts_are_gone():
    web = REPO / "apps/web"
    for gone in ("app/account/plan/page.tsx", "components/v0-styling/PlanPageShell.tsx",
                 "components/stripe-billing-actions.tsx", "components/checkout-status-banner.tsx"):
        assert not (web / gone).exists(), gone


def test_d052_the_vendored_intake_app_is_not_tracked():
    assert _tracked("_intake") == []
    assert "_intake/" in (REPO / ".gitignore").read_text(encoding="utf-8")
