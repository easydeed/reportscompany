"""render_pdf must not hand back a URL that rendered nothing (D-101).

`render_pdf` returns `(pdf_path, source_url)`. The second element used to be
`{print_base}/print/{run_id}` unconditionally — including when the PDF had just
been rendered from an `html_content` string, in which case that URL produced
none of it. `tasks.py` wrote it to `report_generations.html_url`, and the web
app surfaces that as a "view in browser" link, so a customer could open a
document visibly different from the PDF attached to their email: the legacy
`apps/web/templates/trendy-*.html` build, 15 rows a page instead of 13-then-25,
no themed header, no AI narrative.

Both directions are asserted, because only one of them is the interesting one.
A test that checked "html_content render returns None" alone would also pass
against a function that returned None always, which would take the URL path's
`html_url` with it.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker import pdf_engine  # noqa: E402

RUN_ID = "11111111-2222-3333-4444-555555555555"
ACCOUNT_ID = "00000000-0000-0000-0000-000000000000"
PRINT_BASE = "https://app.example.test"
HTML = "<html><body><h1>Rendered from a string</h1></body></html>"


@pytest.fixture
def fake_playwright(tmp_path, monkeypatch):
    """A Playwright stand-in that writes a file and records how it was driven."""
    monkeypatch.setattr(pdf_engine, "PDF_DIR", str(tmp_path))
    calls = {"goto": [], "set_content": []}

    page = MagicMock()
    page.goto.side_effect = lambda url, **kw: calls["goto"].append(url)
    page.set_content.side_effect = lambda html, **kw: calls["set_content"].append(html)
    page.pdf.side_effect = lambda **kw: Path(kw["path"]).write_bytes(b"%PDF-1.4 fake")

    browser = MagicMock()
    browser.new_page.return_value = page
    ctx = MagicMock()
    ctx.__enter__.return_value.chromium.launch.return_value = browser

    with patch.dict(sys.modules, {"playwright": MagicMock(),
                                  "playwright.sync_api": MagicMock(sync_playwright=lambda: ctx)}):
        yield calls


def test_rendering_from_html_reports_no_source_url(fake_playwright):
    pdf_path, source_url = pdf_engine.render_pdf_playwright(
        RUN_ID, ACCOUNT_ID, html_content=HTML, print_base=PRINT_BASE,
    )
    assert Path(pdf_path).exists()
    assert fake_playwright["set_content"] == [HTML], "should render the string"
    assert fake_playwright["goto"] == [], "should not navigate anywhere"
    assert source_url is None, (
        "render_pdf returned a URL for a render that came from an HTML string. "
        f"{PRINT_BASE}/print/{RUN_ID} renders the LEGACY build, not this "
        "document, and tasks.py stores this value as the customer's "
        '"view in browser" link. See D-101.'
    )


def test_rendering_from_the_print_page_does_report_its_url(fake_playwright):
    """The positive control: the URL path must still return its URL.

    Without this, returning None unconditionally would pass the test above and
    silently drop `html_url` for any caller that does render from the route.
    """
    pdf_path, source_url = pdf_engine.render_pdf_playwright(
        RUN_ID, ACCOUNT_ID, html_content=None, print_base=PRINT_BASE,
    )
    assert Path(pdf_path).exists()
    assert fake_playwright["goto"] == [f"{PRINT_BASE}/print/{RUN_ID}"]
    assert fake_playwright["set_content"] == []
    assert source_url == f"{PRINT_BASE}/print/{RUN_ID}"


@pytest.fixture
def fake_pdfshift(tmp_path, monkeypatch):
    """A PDFShift stand-in that records the payload it was sent."""
    monkeypatch.setattr(pdf_engine, "PDF_DIR", str(tmp_path))
    monkeypatch.setattr(pdf_engine, "PDFSHIFT_API_KEY", "test-key-0123456789")
    sent = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        sent.update(json)
        response = MagicMock()
        response.status_code = 200
        response.content = b"%PDF-1.4 fake"
        return response

    monkeypatch.setattr(pdf_engine.httpx, "post", fake_post)
    return sent


def test_pdfshift_rendering_from_html_reports_no_source_url(fake_pdfshift):
    _, source_url = pdf_engine.render_pdf_pdfshift(
        RUN_ID, ACCOUNT_ID, html_content=HTML, print_base=PRINT_BASE,
    )
    assert fake_pdfshift["source"] == HTML
    assert source_url is None


def test_pdfshift_rendering_from_the_print_page_does_report_its_url(fake_pdfshift):
    _, source_url = pdf_engine.render_pdf_pdfshift(
        RUN_ID, ACCOUNT_ID, html_content=None, print_base=PRINT_BASE,
    )
    assert fake_pdfshift["source"] == f"{PRINT_BASE}/print/{RUN_ID}"
    assert source_url == f"{PRINT_BASE}/print/{RUN_ID}"
