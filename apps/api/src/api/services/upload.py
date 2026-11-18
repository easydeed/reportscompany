"""
Branding asset upload service.
Uploads images to Cloudflare R2 and returns public URLs.

Pass B1.1: File Upload Infrastructure
"""

import boto3
import uuid
import re
from urllib.parse import urlsplit
import io
import os
from datetime import datetime
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile, HTTPException
from PIL import Image

# Configuration from environment
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""

# Constraints
MAX_FILE_SIZE_MB = 5
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"}
MAX_DIMENSIONS = (2000, 2000)
MIN_DIMENSIONS = (100, 100)


def get_r2_client():
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


async def validate_image(file: UploadFile) -> bytes:
    """
    Validate uploaded image file.
    Returns file bytes if valid, raises HTTPException if not.
    """
    # Check content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Allowed: PNG, JPEG, WebP, GIF, SVG"
        )
    
    contents = await file.read()
    
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Maximum: {MAX_FILE_SIZE_MB}MB"
        )
    
    # SVGs are vector — skip raster dimension validation
    if file.content_type != "image/svg+xml":
        try:
            image = Image.open(io.BytesIO(contents))
            width, height = image.size
            
            if width < MIN_DIMENSIONS[0] or height < MIN_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image too small ({width}x{height}px). Minimum: {MIN_DIMENSIONS[0]}x{MIN_DIMENSIONS[1]}px"
                )
            
            if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image too large ({width}x{height}px). Maximum: {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]}px"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    
    return contents


async def upload_branding_asset(
    file: UploadFile,
    account_id: str,
    asset_type: str  # "logo" or "headshot"
) -> dict:
    """
    Upload a branding asset to R2.
    Returns dict with url, filename, and size_bytes.
    """
    # Validate
    contents = await validate_image(file)
    
    # Generate unique filename
    original_filename = file.filename or "image"
    ext = original_filename.split(".")[-1].lower() if "." in original_filename else "png"
    if ext not in ("png", "jpg", "jpeg", "webp", "gif", "svg"):
        ext = "png"
    
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    s3_key = f"branding/{account_id}/{asset_type}_{timestamp}_{unique_id}.{ext}"
    
    # Get R2 client
    client = get_r2_client()
    
    if not client:
        # Fallback for local dev: return placeholder URL
        print(f"[Upload] R2 credentials not set, using placeholder for {asset_type}")
        return {
            "url": f"https://via.placeholder.com/400x200?text={asset_type.title()}+Placeholder",
            "filename": original_filename,
            "size_bytes": len(contents),
            "s3_key": s3_key,
        }
    
    # Determine content type
    content_type_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
        "svg": "image/svg+xml",
    }
    content_type = content_type_map.get(ext, "image/png")
    
    # Upload to R2
    print(f"[Upload] Uploading to R2: {s3_key}")
    try:
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=s3_key,
            Body=contents,
            ContentType=content_type,
            CacheControl="public, max-age=31536000",  # 1 year cache
        )
    except Exception as e:
        print(f"[Upload] R2 upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # Build public URL
    if R2_PUBLIC_URL:
        public_url = f"{R2_PUBLIC_URL.rstrip('/')}/{s3_key}"
    else:
        # Fallback to presigned URL if no public URL configured
        public_url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": R2_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=604800  # 7 days
        )
    
    print(f"[Upload] Success: {public_url[:80]}...")
    
    return {
        "url": public_url,
        "filename": original_filename,
        "size_bytes": len(contents),
        "s3_key": s3_key,
    }


def _owned_branding_key(url: str, account_id: str) -> str:
    """Resolve an upload URL against an exact configured origin and key prefix."""
    bases = [R2_PUBLIC_URL] if R2_PUBLIC_URL else []
    if R2_ACCOUNT_ID:
        host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        bases.extend([f"https://{host}/{R2_BUCKET_NAME}", f"https://{R2_BUCKET_NAME}.{host}"])
    try:
        target = urlsplit(url)
    except ValueError:
        raise HTTPException(403, "Invalid branding asset URL")
    for base in bases:
        origin = urlsplit(base)
        if (target.scheme, target.netloc.lower()) != (origin.scheme, origin.netloc.lower()):
            continue
        prefix = origin.path.rstrip("/") + "/"
        if not target.path.startswith(prefix):
            continue
        key = target.path[len(prefix):]
        parts = key.split("/")
        if (len(parts) == 3 and parts[:2] == ["branding", account_id]
                and re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9]+", parts[2])):
            return key
    raise HTTPException(403, "You can only delete your own branding assets")


async def delete_branding_asset(url: str, account_id: str) -> bool:
    key = _owned_branding_key(url, account_id)
    client = get_r2_client()
    if not client:
        raise HTTPException(503, "Branding storage is unavailable")
    try:
        client.head_object(Bucket=R2_BUCKET_NAME, Key=key)
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise HTTPException(502, "Branding storage could not delete this asset") from exc
    except BotoCoreError as exc:
        raise HTTPException(502, "Branding storage could not delete this asset") from exc
    return True
