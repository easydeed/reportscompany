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
IMAGE_TYPES = {
    "PNG": ("image/png", {"png"}),
    "JPEG": ("image/jpeg", {"jpg", "jpeg"}),
    "WEBP": ("image/webp", {"webp"}),
    "GIF": ("image/gif", {"gif"}),
}
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


async def validate_image(file: UploadFile) -> tuple[bytes, str, str]:
    """Read a bounded raster upload and verify the three descriptions agree."""
    allowed = "Choose a PNG, JPEG, WebP or GIF image."
    if file.content_type not in {mime for mime, extensions in IMAGE_TYPES.values()}:
        raise HTTPException(status_code=400, detail=allowed)
    limit = MAX_FILE_SIZE_MB * 1024 * 1024
    contents = await file.read(limit + 1)
    if len(contents) > limit:
        raise HTTPException(status_code=400, detail=f"File exceeds the {MAX_FILE_SIZE_MB}MB limit.")
    filename = file.filename or ""
    extension = os.path.splitext(filename)[1].lower().lstrip(".")
    try:
        with Image.open(io.BytesIO(contents), formats=list(IMAGE_TYPES)) as img:
            # A JPEG container can identify itself as an unsupported
            # multi-picture format after Pillow reads the image metadata.
            detected = IMAGE_TYPES.get(img.format)
            if detected is None:
                raise HTTPException(status_code=400, detail=allowed)
            mime, extensions = detected
            if mime != file.content_type or extension not in extensions:
                raise HTTPException(status_code=400, detail="The image format, filename and content type must match.")
            width, height = img.size
            if not (MIN_DIMENSIONS[0] <= width <= MAX_DIMENSIONS[0] and
                    MIN_DIMENSIONS[1] <= height <= MAX_DIMENSIONS[1]):
                raise HTTPException(status_code=400, detail="Image dimensions must be between 100 and 2000 pixels on each side.")
            img.verify()
        # Reopen after verify() to decode pixels. Pillow identifies some
        # truncated files from their header alone.
        with Image.open(io.BytesIO(contents), formats=list(IMAGE_TYPES)) as img:
            img.load()
    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail="The uploaded image could not be decoded.") from exc
    return contents, extension, mime


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
    contents, ext, content_type = await validate_image(file)
    original_filename = file.filename

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
