"""
PDF Generation Adapter

Handles PDF generation with environment-aware selection:
- Local development: Playwright (Chromium)
- Production (Render): PDF API service (e.g., PDFShift, html2pdf.app)

This avoids Chromium installation issues on Render while maintaining
full local development capabilities.
"""

import os
import httpx
from typing import Optional


PDF_ENGINE = os.getenv("PDF_ENGINE", "playwright")  # "playwright" or "api"
PDF_API_URL = os.getenv("PDF_API_URL", "")  # e.g., https://api.pdfshift.io/v3/convert/pdf
PDF_API_KEY = os.getenv("PDF_API_KEY", "")


def generate_pdf(url: str, output_path: str, wait_for_network: bool = True) -> bool:
    """
    Generate PDF from HTML URL.
    
    Args:
        url: Full URL to HTML page to render
        output_path: Local path to save PDF
        wait_for_network: Wait for network idle (Playwright only)
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If PDF generation fails
    """
    if PDF_ENGINE == "api":
        return _generate_via_api(url, output_path)
    else:
        return _generate_via_playwright(url, output_path, wait_for_network)


def _generate_via_playwright(url: str, output_path: str, wait_for_network: bool) -> bool:
    """
    Generate PDF using Playwright (local development).
    Requires: playwright package + chromium installed
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright not installed. "
            "Run: pip install playwright && python -m playwright install chromium"
        )
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2)
        
        wait_option = "networkidle" if wait_for_network else "domcontentloaded"
        page.goto(url, wait_until=wait_option)
        
        page.pdf(
            path=output_path,
            format="Letter",
            print_background=True,
            margin={
                "top": "0.5in",
                "right": "0.5in",
                "bottom": "0.5in",
                "left": "0.5in"
            }
        )
        browser.close()
    
    return True


def _generate_via_api(url: str, output_path: str) -> bool:
    """
    Generate PDF using external PDF API service (production).
    
    Supported services:
    - PDFShift: https://pdfshift.io/
    - html2pdf.app: https://html2pdf.app/
    - Others with similar POST {url} → PDF response
    
    Configure via environment variables:
    - PDF_API_URL: API endpoint
    - PDF_API_KEY: API authentication key
    """
    if not PDF_API_URL or not PDF_API_KEY:
        raise ValueError(
            "PDF API not configured. Set PDF_API_URL and PDF_API_KEY environment variables."
        )
    
    # Generic PDF API request (adjust headers/payload per service)
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "source": url,
        "landscape": False,
        "margin": {
            "top": "0.5in",
            "right": "0.5in",
            "bottom": "0.5in",
            "left": "0.5in"
        }
    }
    
    # PDFShift uses Basic Auth
    auth = (PDF_API_KEY, "") if "pdfshift" in PDF_API_URL.lower() else None
    
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            PDF_API_URL,
            json=payload,
            headers=headers,
            auth=auth
        )
        response.raise_for_status()
        
        # Write PDF binary to file
        with open(output_path, "wb") as f:
            f.write(response.content)
    
    return True


def get_pdf_engine_info() -> dict:
    """Get current PDF engine configuration for debugging."""
    return {
        "engine": PDF_ENGINE,
        "api_configured": bool(PDF_API_URL and PDF_API_KEY),
        "api_url": PDF_API_URL if PDF_API_URL else None,
        "playwright_available": _is_playwright_available()
    }


def _is_playwright_available() -> bool:
    """Check if Playwright is installed and chromium is available."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


