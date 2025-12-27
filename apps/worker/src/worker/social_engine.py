"""
Social Image Generation Engine

Generates 1080x1920 JPEG images for social media sharing (Instagram Stories, etc.)
Uses PDFShift's JPEG conversion API.

Usage:
    from .social_engine import render_social_image

    jpg_path, social_url = render_social_image(
        run_id="abc123",
        account_id="uuid",
        print_base="https://example.com"
    )

Environment Variables:
    PDFSHIFT_API_KEY: API key for PDFShift
    PRINT_BASE: Base URL for social pages
"""

import os
import httpx
from pathlib import Path
from typing import Tuple

# Configuration
PDFSHIFT_API_KEY = os.getenv("PDFSHIFT_API_KEY", "")
PDFSHIFT_JPEG_URL = "https://api.pdfshift.io/v3/convert/jpeg"
PRINT_BASE = os.getenv("PRINT_BASE", "http://localhost:3000")
SOCIAL_DIR = os.getenv("SOCIAL_DIR", "/tmp/mr_social")

# Ensure social directory exists
Path(SOCIAL_DIR).mkdir(parents=True, exist_ok=True)


def render_social_image(
    run_id: str,
    account_id: str,
    print_base: str = None
) -> Tuple[str, str]:
    """
    Render social media image (1080x1920 JPEG) using PDFShift.

    Args:
        run_id: Report generation ID
        account_id: Account UUID
        print_base: Optional override for PRINT_BASE

    Returns:
        (jpg_path, social_url): Local path to JPEG and the source URL

    Raises:
        httpx.HTTPError: If API request fails
        Exception: If API key is missing or response is invalid
    """
    if not PDFSHIFT_API_KEY:
        raise Exception("PDFSHIFT_API_KEY environment variable is required for social image generation")

    base_url = print_base or PRINT_BASE
    social_url = f"{base_url}/social/{run_id}"
    jpg_path = os.path.join(SOCIAL_DIR, f"{run_id}_social.jpg")

    print(f"📱 Rendering social image with PDFShift: {social_url}")

    # PDFShift JPEG conversion payload
    # 1080x1920 = Instagram Story / TikTok format (9:16 aspect ratio)
    payload = {
        "source": social_url,
        "format": "1080x1920",        # Custom dimensions
        "quality": 90,                 # High quality JPEG
        "full_page": True,             # Capture full page
        "delay": 3000,                 # Wait 3s for fonts/images to load
        "wait_for_network": True,      # Wait for network idle
        "timeout": 60,                 # 60s timeout
    }

    headers = {
        "X-API-Key": PDFSHIFT_API_KEY,
        "Content-Type": "application/json",
    }

    print(f"📦 PDFShift JPEG payload: {payload}")

    response = httpx.post(
        PDFSHIFT_JPEG_URL,
        json=payload,
        headers=headers,
        timeout=90.0
    )

    print(f"📊 PDFShift JPEG response: {response.status_code}")

    if response.status_code >= 400:
        try:
            error_body = response.json()
            print(f"❌ PDFShift JPEG error: {error_body}")
        except:
            print(f"❌ PDFShift JPEG error (raw): {response.text}")

    response.raise_for_status()

    # Save JPEG to disk
    jpg_bytes = response.content
    with open(jpg_path, "wb") as f:
        f.write(jpg_bytes)

    print(f"✅ Social image generated: {jpg_path} ({len(jpg_bytes)} bytes)")
    return jpg_path, social_url


def test_social_engine():
    """Test the social image engine."""
    print("Testing social image engine...")
    print(f"PDFSHIFT_API_KEY set: {'Yes' if PDFSHIFT_API_KEY else 'No'}")
    print(f"PRINT_BASE: {PRINT_BASE}")

    if not PDFSHIFT_API_KEY:
        print("❌ Cannot test: PDFSHIFT_API_KEY not set")
        return False

    # Would need a real run_id to test
    print("⚠️ To test, provide a valid run_id")
    return True


if __name__ == "__main__":
    test_social_engine()
