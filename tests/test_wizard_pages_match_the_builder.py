"""The wizard offers exactly the pages the builder renders, and locks the ones it forces.

THE DEFECT THIS EXISTS FOR. The wizard's page picker held two copies of the
retired nine-page set (`FULL_PAGES`, `COMPACT_PAGES`) after atlas had moved to
the six-page architecture. Neither listed `notes`, and the builder rendered
only the pages it was sent, so every atlas report from the wizard — atlas is
the default theme — rendered five pages with no notes page: no agent panel,
no explainers. Nothing compared the wizard's list with the builder's.

This reads `REPORT_PAGES` out of `components/property-wizard/types.ts` and
compares it with `PropertyReportBuilder.V2_PAGE_ORDER` and `REQUIRED_PAGES`:
same ids, same order, and `required: true` exactly on the pages the builder
adds whether or not they are sent. `scripts/regressions/six_page_set.json`
drops `notes` from the wizard, reorders it, unlocks a required page, and
brings back a nine-page id; each goes red.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))

from worker.property_builder import PropertyReportBuilder  # noqa: E402

TYPES = REPO / "apps/web/components/property-wizard/types.ts"
ENTRY = re.compile(r'\{\s*id:\s*"([a-z_]+)",\s*name:\s*"[^"]*",\s*required:\s*(true|false)\s*\}')


def _wizard_pages():
    src = TYPES.read_text(encoding="utf-8")
    m = re.search(r"export const REPORT_PAGES: ReportPage\[\] = \[(.*?)\];", src, re.S)
    assert m, "REPORT_PAGES not found in components/property-wizard/types.ts"
    pages = ENTRY.findall(m.group(1))
    assert pages, "REPORT_PAGES parsed to nothing; the entry pattern no longer matches"
    return [(pid, req == "true") for pid, req in pages]


def test_the_wizard_offers_the_six_pages_in_document_order():
    assert [pid for pid, _ in _wizard_pages()] == list(PropertyReportBuilder.V2_PAGE_ORDER)


def test_the_wizard_locks_exactly_the_pages_the_builder_forces():
    locked = {pid for pid, required in _wizard_pages() if required}
    assert locked == set(PropertyReportBuilder.REQUIRED_PAGES)


def test_no_nine_page_list_survives_in_the_live_wizard():
    src = TYPES.read_text(encoding="utf-8")
    for retired in ("FULL_PAGES", "COMPACT_PAGES"):
        assert f"export const {retired}" not in src, retired
