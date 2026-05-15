"""
PDF Generation Engine Abstraction

Supports multiple backends:
- playwright: Local Chromium (requires system dependencies)
- pdfshift: Cloud HTML→PDF API (no local dependencies)

Usage:
    from .pdf_engine import render_pdf
    
    pdf_path, print_url = render_pdf(
        run_id="abc123",
        account_id="uuid",
        html_content="<html>...</html>",  # optional
        print_base="https://example.com"
    )

Environment Variables:
    PDF_ENGINE: "playwright" | "pdfshift" (default: playwright)
    PDFSHIFT_API_KEY: API key for PDFShift
    PRINT_BASE: Base URL for print pages
"""

import os
import httpx
from pathlib import Path
from typing import Tuple, Optional

# Configuration
PDF_ENGINE = os.getenv("PDF_ENGINE", "playwright").lower()
PDFSHIFT_API_KEY = os.getenv("PDFSHIFT_API_KEY", "")
PDFSHIFT_API_URL = os.getenv("PDFSHIFT_API_URL", "https://api.pdfshift.io/v3/convert/pdf")
PRINT_BASE = os.getenv("PRINT_BASE", "http://localhost:3000")
PDF_DIR = os.getenv("PDF_DIR", "/tmp/mr_reports")

# Ensure PDF directory exists
Path(PDF_DIR).mkdir(parents=True, exist_ok=True)


def render_pdf_playwright(
    run_id: str,
    account_id: str,
    html_content: Optional[str] = None,
    print_base: Optional[str] = None,
    header_html: Optional[str] = None,
    footer_html: Optional[str] = None,
    header_start_at: int = 1,
    footer_start_at: int = 1,
) -> Tuple[str, str]:
    """
    Render PDF using local Playwright/Chromium.

    Args:
        run_id: Report generation ID
        account_id: Account UUID
        html_content: Optional HTML string (if None, navigates to print page)
        print_base: Base URL for print pages (uses PRINT_BASE if not provided)
        header_html: Standalone HTML doc to repeat at top of pages (accepted
            for API parity with PDFShift; currently IGNORED by Playwright —
            flagged for follow-up ticket).
        footer_html: Standalone HTML doc to repeat at bottom of pages (same
            caveat as header_html).
        header_start_at: Page number to start repeating header (ignored by
            Playwright for now).
        footer_start_at: Page number to start repeating footer (ignored by
            Playwright for now).

    Returns:
        (pdf_path, print_url): Local path to PDF and the URL that was rendered

    Raises:
        Exception: If Playwright fails to launch or render
    """
    # NOTE: Playwright PDF API supports headerTemplate / footerTemplate with
    # displayHeaderFooter=True, but it has a different size model than
    # PDFShift's per-page header/footer params. Wiring that up cleanly is
    # a follow-up. For now we accept the kwargs and ignore them so the
    # caller signature is consistent across backends.
    _ = (header_html, footer_html, header_start_at, footer_start_at)
    from playwright.sync_api import sync_playwright
    
    effective_base = print_base or PRINT_BASE
    print_url = f"{effective_base}/print/{run_id}"
    pdf_path = os.path.join(PDF_DIR, f"{run_id}.pdf")
    
    print(f"🎭 Rendering PDF with Playwright: {print_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        if html_content:
            # Render from HTML string
            page.set_content(html_content, wait_until="networkidle")
        else:
            # Navigate to print page
            page.goto(print_url, wait_until="networkidle", timeout=30000)

        # Wait for fonts to load before capturing
        page.evaluate("() => document.fonts.ready")

        # Generate PDF with proper formatting
        # CRITICAL: margin: 0 — CSS handles all spacing via .page-content positioning.
        # This matches PDFShift production behavior. Templates use:
        #   @page { size: Letter; margin: 0; }
        #   .page-content { position: absolute; top: var(--page-margin); ... }
        page.pdf(
            path=pdf_path,
            format="Letter",  # 8.5" x 11"
            print_background=True,
            margin={
                "top": "0",
                "right": "0",
                "bottom": "0",
                "left": "0"
            }
        )
        
        browser.close()
    
    print(f"✅ PDF generated: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
    return pdf_path, print_url


def render_pdf_pdfshift(
    run_id: str,
    account_id: str,
    html_content: Optional[str] = None,
    print_base: Optional[str] = None,
    header_html: Optional[str] = None,
    footer_html: Optional[str] = None,
    header_start_at: int = 1,
    footer_start_at: int = 1,
) -> Tuple[str, str]:
    """
    Render PDF using PDFShift cloud API.

    Args:
        run_id: Report generation ID
        account_id: Account UUID
        html_content: Optional HTML string (if None, uses print page URL)
        print_base: Base URL for print pages (uses PRINT_BASE if not provided)
        header_html: Optional standalone HTML doc PDFShift repeats on pages.
            When provided, PDFShift's `header` parameter is set and the top
            margin is reserved for it. Use `header_start_at` to skip pages
            (e.g. start_at=2 means pages 2+ only).
        footer_html: Optional standalone HTML doc PDFShift repeats on pages.
            Same start_at semantics as header_html.
        header_start_at: First page index where the header should appear.
        footer_start_at: First page index where the footer should appear.

    Returns:
        (pdf_path, print_url): Local path to PDF and the URL/HTML that was rendered

    Raises:
        httpx.HTTPError: If API request fails
        Exception: If API key is missing or response is invalid
    """
    if not PDFSHIFT_API_KEY:
        raise Exception("PDFSHIFT_API_KEY environment variable is required when PDF_ENGINE=pdfshift")

    effective_base = print_base or PRINT_BASE
    print_url = f"{effective_base}/print/{run_id}"
    pdf_path = os.path.join(PDF_DIR, f"{run_id}.pdf")

    # PDFSHIFT-NATIVE-HEADER-FOOTER — When a `header` or `footer` is sent,
    # PDFShift reserves the declared height inside the page margin. We need
    # to widen the top/bottom margins so body content doesn't overlap.
    # When neither is sent, keep zero margins so the existing CSS @page
    # rule remains the source of truth (legacy behavior preserved).
    if header_html or footer_html:
        margin = {
            "top": "0.8in" if header_html else "0",
            "right": "0",
            "bottom": "1.0in" if footer_html else "0",
            "left": "0",
        }
    else:
        margin = {"top": "0", "right": "0", "bottom": "0", "left": "0"}

    base_payload = {
        "sandbox": False,
        "use_print": True,
        "format": "Letter",
        "margin": margin,
        "remove_blank": True,
    }

    # Attach header/footer when provided. Heights MUST match the actual
    # rendered content height of the templates — too small clips content,
    # too large leaves whitespace. Tuned for the compact gradient header
    # (~10px padding + ~30px text content) and the agent footer
    # (~48px photo + ~24px padding + 1px border).
    if header_html:
        base_payload["header"] = {
            "source": header_html,
            "height": "0.7in",
            "start_at": header_start_at,
        }
    if footer_html:
        base_payload["footer"] = {
            "source": footer_html,
            "height": "0.9in",
            "start_at": footer_start_at,
        }
    
    # PDFShift options to improve reliability with pages that load images/data after initial HTML.
    # - delay: give the page time to render
    # - wait_for_network: wait for network to go idle (default true per docs)
    # - lazy_load_images: scroll to trigger lazy-loading (helps some frameworks)
    # - timeout: let PDFShift keep loading the page longer before forcing conversion
    # Ref: https://docs.pdfshift.io/api-reference/convert-to-jpeg#convert-to-jpeg
    #
    # IMPORTANT: These options are needed for BOTH URL and HTML sources!
    # When HTML contains external image URLs (like MLS photos), PDFShift still needs
    # to fetch those images. Without these options, images may show as broken/placeholder.
    
    # Common options for image loading (applies to both URL and HTML sources)
    image_loading_options = {
        # PDFSHIFT-DELAY-REDUCTION — Reduced from 5000ms because we now
        # base64-inline all images (agent photo, logos, etc.) via
        # embed_images_as_base64 before sending HTML to PDFShift.
        # No external image fetches happen on PDFShift's side, so the
        # 5-second delay was pure dead time. 1000ms is a safe floor for
        # font / CSS settling. Recoverable savings: ~4-5 sec per report.
        "delay": 1000,
        "wait_for_network": True,  # Wait for network to go idle (no requests for 500ms)
        # PDFSHIFT-DELAY-REDUCTION — Disabled lazy_load_images because all
        # images are base64-inlined; no external resources to lazy-load.
        "lazy_load_images": False,
        "timeout": 100,            # Max 100s total (PDFShift plan limit)
    }
    
    if html_content:
        payload = {
            **base_payload,
            **image_loading_options,  # CRITICAL: Include image loading options for HTML too!
            "source": html_content,
        }
        print(f"☁️  Rendering PDF with PDFShift (HTML string, {len(html_content)} chars)")
    else:
        payload = {
            **base_payload,
            **image_loading_options,
            "source": print_url,
            "delay": 8000,            # Longer delay for URL-based (page needs to render first)
            "ignore_long_polling": True,  # Don't get stuck waiting on long-polling/websockets
        }
        print(f"☁️  Rendering PDF with PDFShift: {print_url}")
    
    # Make API request
    # PDFShift uses X-API-Key header for authentication (not Basic Auth!)
    # X-Processor-Version: 142 = new conversion engine (better CSS3, faster, better PDFs)
    headers = {
        "X-API-Key": PDFSHIFT_API_KEY,
        "Content-Type": "application/json",
        "X-Processor-Version": "142"
    }
    
    print(f"🔑 Using API key: {PDFSHIFT_API_KEY[:10]}...{PDFSHIFT_API_KEY[-4:]}")
    print(f"📦 Payload: {payload}")
    
    response = httpx.post(
        PDFSHIFT_API_URL,
        json=payload,
        headers=headers,
        timeout=120.0  # HTTP timeout for the API call itself
    )
    
    print(f"📊 PDFShift response: {response.status_code}")
    
    # If not successful, print the error details before raising
    if response.status_code >= 400:
        try:
            error_body = response.json()
            print(f"❌ PDFShift error: {error_body}")
        except:
            print(f"❌ PDFShift error (raw): {response.text}")
    
    response.raise_for_status()
    
    # Save PDF to disk
    pdf_bytes = response.content
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"✅ PDF generated: {pdf_path} ({len(pdf_bytes)} bytes)")
    return pdf_path, print_url


def render_pdf(
    run_id: str,
    account_id: str,
    html_content: Optional[str] = None,
    print_base: Optional[str] = None,
    header_html: Optional[str] = None,
    footer_html: Optional[str] = None,
    header_start_at: int = 1,
    footer_start_at: int = 1,
) -> Tuple[str, str]:
    """
    Render PDF using the configured engine.

    Args:
        run_id: Report generation ID
        account_id: Account UUID
        html_content: Optional HTML string to render
        print_base: Optional override for PRINT_BASE
        header_html: Optional standalone HTML for page header (PDFShift only).
        footer_html: Optional standalone HTML for page footer (PDFShift only).
        header_start_at: First page index where the header appears.
        footer_start_at: First page index where the footer appears.

    Returns:
        (pdf_path, print_url): Local path to generated PDF and source URL

    Raises:
        ValueError: If PDF_ENGINE is invalid
        Exception: If rendering fails
    """
    effective_print_base = print_base or PRINT_BASE

    print(f"📄 PDF Engine: {PDF_ENGINE}, print_base: {effective_print_base}")

    if PDF_ENGINE == "playwright":
        return render_pdf_playwright(
            run_id, account_id, html_content, effective_print_base,
            header_html=header_html,
            footer_html=footer_html,
            header_start_at=header_start_at,
            footer_start_at=footer_start_at,
        )
    elif PDF_ENGINE == "pdfshift":
        return render_pdf_pdfshift(
            run_id, account_id, html_content, effective_print_base,
            header_html=header_html,
            footer_html=footer_html,
            header_start_at=header_start_at,
            footer_start_at=footer_start_at,
        )
    else:
        raise ValueError(f"Invalid PDF_ENGINE: {PDF_ENGINE}. Must be 'playwright' or 'pdfshift'")


# Convenience function for testing
def test_engine():
    """Test the configured PDF engine with a simple HTML page."""
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Engine Test</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>PDF Engine Test</h1>
        <p>Engine: {engine}</p>
        <p>This is a test PDF generated by the {engine} engine.</p>
    </body>
    </html>
    """.format(engine=PDF_ENGINE)
    
    try:
        pdf_path, source = render_pdf(
            run_id="test-123",
            account_id="00000000-0000-0000-0000-000000000000",
            html_content=test_html
        )
        print(f"✅ Test passed! PDF at: {pdf_path}")
        print(f"   Source: {source}")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when executed directly
    print(f"Testing PDF engine: {PDF_ENGINE}")
    test_engine()

