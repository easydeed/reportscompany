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


def render_pdf_playwright(run_id: str, account_id: str, html_content: Optional[str] = None) -> Tuple[str, str]:
    """
    Render PDF using local Playwright/Chromium.
    
    Args:
        run_id: Report generation ID
        account_id: Account UUID
        html_content: Optional HTML string (if None, navigates to print page)
    
    Returns:
        (pdf_path, print_url): Local path to PDF and the URL that was rendered
    
    Raises:
        Exception: If Playwright fails to launch or render
    """
    from playwright.sync_api import sync_playwright
    
    print_url = f"{PRINT_BASE}/print/{run_id}"
    pdf_path = os.path.join(PDF_DIR, f"{run_id}.pdf")
    
    print(f"🎭 Rendering PDF with Playwright: {print_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        if html_content:
            # Render from HTML string
            page.set_content(html_content)
        else:
            # Navigate to print page
            page.goto(print_url, wait_until="networkidle", timeout=30000)
        
        # Generate PDF with proper formatting
        page.pdf(
            path=pdf_path,
            format="Letter",  # 8.5" x 11"
            print_background=True,
            margin={
                "top": "0.5in",
                "right": "0.5in",
                "bottom": "0.5in",
                "left": "0.5in"
            }
        )
        
        browser.close()
    
    print(f"✅ PDF generated: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
    return pdf_path, print_url


def render_pdf_pdfshift(run_id: str, account_id: str, html_content: Optional[str] = None) -> Tuple[str, str]:
    """
    Render PDF using PDFShift cloud API.
    
    Args:
        run_id: Report generation ID
        account_id: Account UUID
        html_content: Optional HTML string (if None, uses print page URL)
    
    Returns:
        (pdf_path, print_url): Local path to PDF and the URL/HTML that was rendered
    
    Raises:
        httpx.HTTPError: If API request fails
        Exception: If API key is missing or response is invalid
    """
    if not PDFSHIFT_API_KEY:
        raise Exception("PDFSHIFT_API_KEY environment variable is required when PDF_ENGINE=pdfshift")
    
    print_url = f"{PRINT_BASE}/print/{run_id}"
    pdf_path = os.path.join(PDF_DIR, f"{run_id}.pdf")
    
    # Prepare request payload
    # CRITICAL: Set margin to 0 - our HTML templates handle all margins via CSS
    # Templates use @page { margin: 0 } and .page { padding: 0.25in }
    # Adding PDFShift margins ON TOP of CSS causes content overflow to blank pages
    base_payload = {
        "sandbox": False,
        "use_print": True,  # Use @media print stylesheet
        "format": "Letter",  # US Letter: 8.5" x 11"
        "margin": {          # ZERO margins - CSS handles this
            "top": "0",
            "right": "0",
            "bottom": "0",
            "left": "0"
        },
        "remove_blank": True,  # Remove blank trailing pages
    }
    
    # PDFShift options to improve reliability with pages that load images/data after initial HTML.
    # - delay: give the page time to render
    # - wait_for_network: wait for network to go idle (default true per docs)
    # - lazy_load_images: scroll to trigger lazy-loading (helps some frameworks)
    # - timeout: let PDFShift keep loading the page longer before forcing conversion
    # Ref: https://docs.pdfshift.io/api-reference/convert-to-jpeg#convert-to-jpeg
    if html_content:
        payload = {
            **base_payload,
            "source": html_content,
        }
        print(f"☁️  Rendering PDF with PDFShift (HTML string, {len(html_content)} chars)")
    else:
        payload = {
            **base_payload,
            "source": print_url,
            "delay": 8000,            # max 10s per docs
            "wait_for_network": True, # no network requests for 500ms
            "ignore_long_polling": True,  # don't get stuck waiting on long-polling/websockets
            "lazy_load_images": True, # scroll to trigger lazy-loaded images
            # NOTE: PDFShift plan limit enforces max 100s timeout (400 if higher)
            "timeout": 100,           # seconds
        }
        print(f"☁️  Rendering PDF with PDFShift: {print_url}")
    
    # Make API request
    # PDFShift uses X-API-Key header for authentication (not Basic Auth!)
    headers = {
        "X-API-Key": PDFSHIFT_API_KEY,
        "Content-Type": "application/json"
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
    print_base: Optional[str] = None
) -> Tuple[str, str]:
    """
    Render PDF using the configured engine.
    
    Args:
        run_id: Report generation ID
        account_id: Account UUID
        html_content: Optional HTML string to render
        print_base: Optional override for PRINT_BASE
    
    Returns:
        (pdf_path, print_url): Local path to generated PDF and source URL
    
    Raises:
        ValueError: If PDF_ENGINE is invalid
        Exception: If rendering fails
    """
    # Override global PRINT_BASE if provided
    global PRINT_BASE
    if print_base:
        PRINT_BASE = print_base
    
    print(f"📄 PDF Engine: {PDF_ENGINE}")
    
    if PDF_ENGINE == "playwright":
        return render_pdf_playwright(run_id, account_id, html_content)
    elif PDF_ENGINE == "pdfshift":
        return render_pdf_pdfshift(run_id, account_id, html_content)
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

