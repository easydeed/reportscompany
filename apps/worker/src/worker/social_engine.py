"""
Social Image Generation Engine

Generates 1080x1920 JPEG images for social media sharing (Instagram Stories, etc.)

Strategy:
- PRIMARY: PDFShift API (99% uptime, no server resources)
- FALLBACK: Playwright (local Chromium, if PDFShift unavailable)

Usage:
    from .social_engine import render_social_image

    jpg_path, social_url = render_social_image(
        run_id="abc123",
        account_id="uuid",
        print_base="https://example.com"
    )

Environment Variables:
    PDFSHIFT_API_KEY: API key for PDFShift (primary)
    PRINT_BASE: Base URL for social pages
    SOCIAL_DIR: Directory to save generated images
"""

import os
import httpx
import asyncio
from pathlib import Path
from typing import Tuple, Optional

# Configuration
PDFSHIFT_API_KEY = os.getenv("PDFSHIFT_API_KEY", "")
PRINT_BASE = os.getenv("PRINT_BASE", "http://localhost:3000")
SOCIAL_DIR = os.getenv("SOCIAL_DIR", "/tmp/mr_social")

# Ensure social directory exists
Path(SOCIAL_DIR).mkdir(parents=True, exist_ok=True)


def _render_with_pdfshift(url: str, output_path: str) -> bool:
    """
    PRIMARY: Render using PDFShift API.
    
    Benefits:
    - 99% uptime SaaS
    - No server resources used
    - They handle browser maintenance
    """
    if not PDFSHIFT_API_KEY:
        print("⚠️ PDFSHIFT_API_KEY not set, skipping PDFShift")
        return False
    
    print(f"📱 [PDFShift] Rendering: {url}")
    
    # PDFShift image conversion
    # Docs: https://pdfshift.io/documentation/image
    payload = {
        "source": url,
        "format": "jpeg",
        "width": 1080,
        "height": 1920,
        "quality": 90,
        "delay": 3000,  # Wait for fonts/images
        "wait_for_network": True,
    }
    
    try:
        response = httpx.post(
            "https://api.pdfshift.io/v3/convert/image",
            json=payload,
            auth=("api", PDFSHIFT_API_KEY),
            timeout=60.0
        )
        
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ [PDFShift] Generated: {output_path} ({file_size:,} bytes)")
            return True
        else:
            print(f"❌ [PDFShift] Error {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ [PDFShift] Failed: {e}")
        return False


async def _render_with_playwright(url: str, output_path: str) -> bool:
    """
    FALLBACK: Render using local Playwright/Chromium.
    
    Used when:
    - PDFShift API key not configured
    - PDFShift temporarily unavailable
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ [Playwright] Not installed. Run: pip install playwright && playwright install chromium")
        return False
    
    print(f"📱 [Playwright] Rendering: {url}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={"width": 1080, "height": 1920},
                device_scale_factor=1
            )
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for fonts
            
            await page.screenshot(
                path=output_path,
                type="jpeg",
                quality=90,
                full_page=False,
            )
            
            await browser.close()
            
            file_size = os.path.getsize(output_path)
            print(f"✅ [Playwright] Generated: {output_path} ({file_size:,} bytes)")
            return True
            
    except Exception as e:
        print(f"❌ [Playwright] Failed: {e}")
        return False


def render_social_image(
    run_id: str,
    account_id: str,
    print_base: Optional[str] = None
) -> Tuple[str, str]:
    """
    Render social media image (1080x1920 JPEG).
    
    Strategy:
    1. Try PDFShift first (99% uptime, no server load)
    2. Fall back to Playwright if PDFShift fails

    Args:
        run_id: Report generation ID (UUID)
        account_id: Account UUID (for logging)
        print_base: Optional override for PRINT_BASE

    Returns:
        (jpg_path, social_url): Local path to JPEG and the source URL

    Raises:
        Exception: If both methods fail
    """
    base_url = print_base or PRINT_BASE
    social_url = f"{base_url}/api/social/{run_id}"
    jpg_path = os.path.join(SOCIAL_DIR, f"{run_id}_social.jpg")
    
    print(f"📱 Generating social image for run_id={run_id}")
    
    # PRIMARY: PDFShift
    if _render_with_pdfshift(social_url, jpg_path):
        return jpg_path, social_url
    
    print("⚠️ PDFShift failed, trying Playwright fallback...")
    
    # FALLBACK: Playwright
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(_render_with_playwright(social_url, jpg_path))
        if success:
            return jpg_path, social_url
    finally:
        loop.close()
    
    raise Exception("Social image generation failed: both PDFShift and Playwright failed")


def test_social_engine():
    """Test the social image engine configuration."""
    print("=" * 60)
    print("Social Image Engine Status")
    print("=" * 60)
    print()
    
    # Check PDFShift
    if PDFSHIFT_API_KEY:
        print("✅ PDFShift: API key configured (PRIMARY)")
    else:
        print("⚠️ PDFShift: No API key (PDFSHIFT_API_KEY not set)")
    
    # Check Playwright
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright: Installed (FALLBACK)")
    except ImportError:
        print("⚠️ Playwright: Not installed")
        print("   Install: pip install playwright && playwright install chromium")
    
    print()
    print(f"PRINT_BASE: {PRINT_BASE}")
    print(f"SOCIAL_DIR: {SOCIAL_DIR}")
    
    return True


if __name__ == "__main__":
    test_social_engine()
