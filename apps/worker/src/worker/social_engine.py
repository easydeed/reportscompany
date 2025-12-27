"""
Social Image Generation Engine

Generates 1080x1920 JPEG images for social media sharing (Instagram Stories, etc.)
Uses Playwright for reliable browser-based screenshot generation.

Usage:
    from .social_engine import render_social_image

    jpg_path, social_url = render_social_image(
        run_id="abc123",
        account_id="uuid",
        print_base="https://example.com"
    )

Environment Variables:
    PRINT_BASE: Base URL for social pages (default: http://localhost:3000)
    SOCIAL_DIR: Directory to save generated images (default: /tmp/mr_social)
"""

import os
import asyncio
from pathlib import Path
from typing import Tuple, Optional

# Configuration
PRINT_BASE = os.getenv("PRINT_BASE", "http://localhost:3000")
SOCIAL_DIR = os.getenv("SOCIAL_DIR", "/tmp/mr_social")

# Ensure social directory exists
Path(SOCIAL_DIR).mkdir(parents=True, exist_ok=True)


async def _render_with_playwright(url: str, output_path: str) -> bool:
    """
    Render social image using Playwright (headless browser).
    
    This is the recommended approach for reliable screenshot generation.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False
    
    print(f"📱 Rendering social image with Playwright: {url}")
    
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(headless=True)
        
        # Create page with exact social media dimensions
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1  # 1:1 pixel ratio for crisp images
        )
        
        # Navigate to social page
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait for fonts and images to load
        await page.wait_for_timeout(2000)
        
        # Capture screenshot as JPEG
        await page.screenshot(
            path=output_path,
            type="jpeg",
            quality=90,
            full_page=False,  # Capture viewport only (1080x1920)
        )
        
        await browser.close()
        
        file_size = os.path.getsize(output_path)
        print(f"✅ Social image generated: {output_path} ({file_size:,} bytes)")
        return True


def render_social_image(
    run_id: str,
    account_id: str,
    print_base: Optional[str] = None
) -> Tuple[str, str]:
    """
    Render social media image (1080x1920 JPEG).
    
    Uses Playwright for browser-based screenshot generation.
    Falls back to the social page URL if screenshot fails.

    Args:
        run_id: Report generation ID (UUID)
        account_id: Account UUID (for logging/tracking)
        print_base: Optional override for PRINT_BASE

    Returns:
        (jpg_path, social_url): Local path to JPEG and the source URL

    Raises:
        Exception: If screenshot generation fails
    """
    base_url = print_base or PRINT_BASE
    
    # Use API route for clean HTML (no nested document structure)
    social_url = f"{base_url}/api/social/{run_id}"
    jpg_path = os.path.join(SOCIAL_DIR, f"{run_id}_social.jpg")
    
    print(f"📱 Generating social image for run_id={run_id}")
    print(f"   URL: {social_url}")
    print(f"   Output: {jpg_path}")
    
    # Run async playwright screenshot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(_render_with_playwright(social_url, jpg_path))
        
        if not success:
            raise Exception("Playwright screenshot failed - check logs for details")
        
        return jpg_path, social_url
        
    except Exception as e:
        print(f"❌ Social image generation failed: {e}")
        raise
    finally:
        loop.close()


def render_social_image_async(
    run_id: str,
    account_id: str,
    print_base: Optional[str] = None
) -> Tuple[str, str]:
    """
    Async version of render_social_image for use in async contexts.
    """
    base_url = print_base or PRINT_BASE
    social_url = f"{base_url}/api/social/{run_id}"
    jpg_path = os.path.join(SOCIAL_DIR, f"{run_id}_social.jpg")
    
    # This should be called from an async context
    import asyncio
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(_render_with_playwright(social_url, jpg_path))
    
    if not success:
        raise Exception("Playwright screenshot failed")
    
    return jpg_path, social_url


def check_playwright_installed() -> bool:
    """Check if Playwright is properly installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Just check if chromium is available
            browser = p.chromium.launch(headless=True)
            browser.close()
            return True
    except Exception as e:
        print(f"⚠️ Playwright check failed: {e}")
        print("   Run: pip install playwright && playwright install chromium")
        return False


def test_social_engine():
    """Test the social image engine."""
    print("=" * 60)
    print("Social Image Engine Test")
    print("=" * 60)
    print(f"PRINT_BASE: {PRINT_BASE}")
    print(f"SOCIAL_DIR: {SOCIAL_DIR}")
    print()
    
    # Check Playwright
    print("Checking Playwright installation...")
    if check_playwright_installed():
        print("✅ Playwright is installed and working")
    else:
        print("❌ Playwright is not properly installed")
        print()
        print("To install Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return False
    
    print()
    print("⚠️ To test image generation, provide a valid run_id:")
    print("   from worker.social_engine import render_social_image")
    print("   jpg_path, url = render_social_image('your-run-id', 'account-id')")
    
    return True


if __name__ == "__main__":
    test_social_engine()
