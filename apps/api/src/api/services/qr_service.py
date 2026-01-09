"""
QR Code Generation Service

Generate styled QR codes and upload to Cloudflare R2.

Features:
- Rounded module style for modern look
- Custom foreground colors
- High error correction for reliable scanning
- Automatic R2 upload

Usage:
    url = await generate_qr_code(
        url="https://trendyreports.io/p/abc123",
        color="#2563eb",
        report_id="uuid-here"
    )
"""

import io
import logging
import os
from typing import Optional, Tuple

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

# R2 Configuration (shared with upload.py)
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""

# QR Code defaults
DEFAULT_QR_SIZE = 10  # Box size (pixels per module)
DEFAULT_BORDER = 2    # Border modules
DEFAULT_COLOR = "#000000"
DEFAULT_BACKGROUND = "#FFFFFF"


def _get_r2_client():
    """Get configured R2 client."""
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        return None
    
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (0, 0, 0)  # Default to black
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


def _generate_qr_image(
    url: str,
    color: str = DEFAULT_COLOR,
    background: str = DEFAULT_BACKGROUND,
    box_size: int = DEFAULT_QR_SIZE,
    border: int = DEFAULT_BORDER,
) -> bytes:
    """
    Generate QR code image as PNG bytes.
    
    Uses qrcode library with StyledPilImage for rounded modules.
    """
    try:
        import qrcode
        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
        from qrcode.image.styles.colormasks import SolidFillColorMask
    except ImportError:
        logger.error("qrcode library not installed. Run: pip install qrcode[pil]")
        raise RuntimeError("QR code generation unavailable - missing qrcode library")
    
    # Convert colors
    fill_rgb = _hex_to_rgb(color)
    back_rgb = _hex_to_rgb(background)
    
    # Create QR code with high error correction
    qr = qrcode.QRCode(
        version=None,  # Auto-determine size
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction (30%)
        box_size=box_size,
        border=border,
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    # Generate styled image with rounded modules
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(
            back_color=back_rgb,
            front_color=fill_rgb,
        ),
    )
    
    # Convert to PNG bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    
    return buffer.getvalue()


def _generate_qr_image_simple(
    url: str,
    color: str = DEFAULT_COLOR,
    background: str = DEFAULT_BACKGROUND,
    box_size: int = DEFAULT_QR_SIZE,
    border: int = DEFAULT_BORDER,
) -> bytes:
    """
    Fallback: Generate simple QR code without styled modules.
    Used if styled modules aren't available.
    """
    try:
        import qrcode
    except ImportError:
        logger.error("qrcode library not installed")
        raise RuntimeError("QR code generation unavailable")
    
    fill_rgb = _hex_to_rgb(color)
    back_rgb = _hex_to_rgb(background)
    
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color=fill_rgb, back_color=back_rgb)
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    
    return buffer.getvalue()


async def generate_qr_code(
    url: str,
    color: str = DEFAULT_COLOR,
    report_id: str = "",
    background: str = DEFAULT_BACKGROUND,
    box_size: int = DEFAULT_QR_SIZE,
) -> str:
    """
    Generate QR code and upload to R2.
    
    Args:
        url: The URL to encode in the QR code
        color: Foreground color as hex (e.g., "#2563eb")
        report_id: Report ID for the filename
        background: Background color as hex (default white)
        box_size: Size of each module in pixels
    
    Returns:
        Public URL of the uploaded QR code image
    
    Example:
        qr_url = await generate_qr_code(
            url="https://trendyreports.io/p/abc123",
            color="#2563eb",
            report_id="550e8400-e29b-41d4-a716-446655440000"
        )
    """
    if not url:
        raise ValueError("URL is required for QR code generation")
    
    if not report_id:
        import uuid
        report_id = uuid.uuid4().hex[:12]
    
    # Validate color format
    if not color.startswith("#") or len(color) != 7:
        logger.warning(f"Invalid color format '{color}', using default")
        color = DEFAULT_COLOR
    
    # Generate QR code image
    try:
        png_bytes = _generate_qr_image(url, color, background, box_size)
        logger.info(f"Generated styled QR code for {url[:50]}...")
    except Exception as e:
        logger.warning(f"Styled QR generation failed, using simple: {e}")
        try:
            png_bytes = _generate_qr_image_simple(url, color, background, box_size)
        except Exception as e2:
            logger.error(f"QR code generation failed: {e2}")
            # Return fallback URL using external QR service
            return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&color={color[1:]}&data={url}"
    
    # Upload to R2
    client = _get_r2_client()
    
    if not client:
        logger.warning("R2 not configured, using external QR service fallback")
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&color={color[1:]}&data={url}"
    
    # S3 key for QR code
    s3_key = f"qr-codes/{report_id}.png"
    
    try:
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=s3_key,
            Body=png_bytes,
            ContentType="image/png",
            CacheControl="public, max-age=31536000",  # 1 year cache
        )
        logger.info(f"Uploaded QR code to R2: {s3_key}")
    except Exception as e:
        logger.error(f"R2 upload failed: {e}")
        # Fallback to external service
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&color={color[1:]}&data={url}"
    
    # Build public URL
    if R2_PUBLIC_URL:
        public_url = f"{R2_PUBLIC_URL.rstrip('/')}/{s3_key}"
    else:
        # Fallback to presigned URL
        public_url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": R2_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=604800  # 7 days
        )
    
    logger.info(f"QR code URL: {public_url[:60]}...")
    return public_url


async def delete_qr_code(report_id: str) -> bool:
    """
    Delete a QR code from R2.
    
    Args:
        report_id: The report ID used when generating the QR code
    
    Returns:
        True if deleted successfully, False otherwise
    """
    if not report_id:
        return False
    
    client = _get_r2_client()
    if not client:
        return False
    
    s3_key = f"qr-codes/{report_id}.png"
    
    try:
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=s3_key)
        logger.info(f"Deleted QR code: {s3_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete QR code: {e}")
        return False


def get_qr_code_url(report_id: str) -> Optional[str]:
    """
    Get the public URL for a QR code without generating it.
    
    Args:
        report_id: The report ID
    
    Returns:
        Public URL or None if R2 not configured
    """
    if not R2_PUBLIC_URL:
        return None
    
    return f"{R2_PUBLIC_URL.rstrip('/')}/qr-codes/{report_id}.png"

