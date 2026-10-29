"""
D-305 — the report link's preview printed the estimate range.

`/r/{id}`'s metadata is the preview a link shows in texts, Slack and email,
to anyone it is forwarded to. Owner decision (2026-10-29): no estimate there.
It stays in the report, beside how it was worked out.
"""
import re
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "apps/web/app/r/[id]/page.tsx"


def _metadata_source():
    src = PAGE.read_text(encoding="utf-8")
    i = src.index("export async function generateMetadata")
    j = src.index("export default", i)
    return src[i:j]


def test_the_link_preview_carries_no_estimate():
    meta = _metadata_source()
    assert "value_estimate" not in meta, "the preview reads the estimate"
    assert not re.search(r"Estimated value|\$\{?\$|toLocaleString", meta), meta


def test_the_preview_still_names_the_report():
    """The control: the fix removed the number, not the preview."""
    meta = _metadata_source()
    assert "Home Value Report" in meta and "openGraph" in meta
