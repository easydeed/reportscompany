"""
Social Image Generation Engine

Generates 1080x1920 JPEG images for social media sharing (Instagram Stories, etc.)
Uses PDFShift API for reliable, scalable image generation.

Usage:
    from .social_engine import render_social_image

    jpg_path, social_url = render_social_image(
        run_id="abc123",
        account_id="uuid",
        print_base="https://example.com"
    )

Environment Variables:
    PDFSHIFT_API_KEY: Required - API key for PDFShift
    PRINT_BASE: Base URL for social pages (default: http://localhost:3000)
    SOCIAL_DIR: Directory to save generated images (default: /tmp/mr_social)
"""

import os
import httpx
from pathlib import Path
from typing import Tuple, Optional

# Configuration
PDFSHIFT_API_KEY = os.getenv("PDFSHIFT_API_KEY", "")
PRINT_BASE = os.getenv("PRINT_BASE", "http://localhost:3000")
SOCIAL_DIR = os.getenv("SOCIAL_DIR", "/tmp/mr_social")

# Ensure social directory exists
Path(SOCIAL_DIR).mkdir(parents=True, exist_ok=True)


def render_social_image(
    run_id: str,
    account_id: str,
    print_base: Optional[str] = None
) -> Tuple[str, str]:
    """
    Render social media image (1080x1920 JPEG) using PDFShift.

    Args:
        run_id: Report generation ID (UUID)
        account_id: Account UUID (for logging)
        print_base: Optional override for PRINT_BASE

    Returns:
        (jpg_path, social_url): Local path to JPEG and the source URL

    Raises:
        ValueError: If PDFSHIFT_API_KEY is not configured
        httpx.HTTPStatusError: If PDFShift API returns an error
    """
    if not PDFSHIFT_API_KEY:
        raise ValueError("PDFSHIFT_API_KEY environment variable is required")
    
    base_url = print_base or PRINT_BASE
    social_url = f"{base_url}/api/social/{run_id}"
    jpg_path = os.path.join(SOCIAL_DIR, f"{run_id}_social.jpg")
    
    print(f"📱 Generating social image: {social_url}")
    
    # PDFShift JPEG conversion
    # Docs: https://docs.pdfshift.io/
    response = httpx.post(
        "https://api.pdfshift.io/v3/convert/jpeg",  # Correct JPEG endpoint
        headers={
            "X-API-Key": PDFSHIFT_API_KEY,  # Header auth per PDFShift docs
            "Content-Type": "application/json",
        },
        json={
            "source": social_url,
            "width": 1080,
            "height": 1920,
            "quality": 90,
            "delay": 3000,
            "wait_for_network": True,
        },
        timeout=90.0
    )
    
    response.raise_for_status()
    
    with open(jpg_path, "wb") as f:
        f.write(response.content)
    
    print(f"✅ Social image saved: {jpg_path} ({len(response.content):,} bytes)")
    return jpg_path, social_url
