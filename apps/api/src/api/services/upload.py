"""
Branding asset upload service.
Uploads images to Cloudflare R2 and returns public URLs.

Pass B1.1: File Upload Infrastructure
"""

import boto3
import uuid
import io
import os
from datetime import datetime
from botocore.config import Config
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

# Configuration from environment
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""

# Constraints
MAX_FILE_SIZE_MB = 5
MAX_FILE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
IMAGE_TYPES = {
    "PNG": ("image/png", {"png"}),
    "JPEG": ("image/jpeg", {"jpg", "jpeg"}),
    # Phones save photos as "multi-picture" JPEGs (MPO: a primary image plus
    # depth or preview frames). It is a JPEG to the person uploading it, so it
    # is accepted as one and only the primary image is kept (LR-007, Jerry).
    "MPO": ("image/jpeg", {"jpg", "jpeg"}),
    "WEBP": ("image/webp", {"webp"}),
    "GIF": ("image/gif", {"gif"}),
}
# What Pillow may open. MPO is not listed: Pillow opens it through its JPEG
# plugin and only then reports the format as "MPO" (naming MPO here raises).
OPEN_FORMATS = ["PNG", "JPEG", "WEBP", "GIF"]
# The stored format: an MPO is stored as an ordinary JPEG.
STORED_FORMAT = {"PNG": "PNG", "JPEG": "JPEG", "MPO": "JPEG", "WEBP": "WEBP", "GIF": "GIF"}
CANONICAL_EXT = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "GIF": "gif"}
MAX_DIMENSIONS = (2000, 2000)
MIN_DIMENSIONS = (100, 100)

NOT_AN_IMAGE = "This file isn't a PNG, JPEG, WebP or GIF image. Choose one of those formats."
UNREADABLE = "The image couldn't be read; it may be damaged or incomplete. Try exporting it again."


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


def inspect_image(contents: bytes, declared_mime=None, extension=None) -> str:
    """Check the bytes are a supported raster image; return Pillow's format.

    `declared_mime` and `extension` (an upload's) must agree with the
    detected format; an import has neither. Every refusal is a 400 that
    says what is wrong.
    """
    try:
        with Image.open(io.BytesIO(contents), formats=OPEN_FORMATS) as img:
            fmt = img.format
            if fmt not in IMAGE_TYPES:
                raise HTTPException(status_code=400, detail=NOT_AN_IMAGE)
            mime, extensions = IMAGE_TYPES[fmt]
            if declared_mime is not None and (mime != declared_mime or extension not in extensions):
                raise HTTPException(
                    status_code=400,
                    detail=(f"This file is a {CANONICAL_EXT[STORED_FORMAT[fmt]].upper()} image, but its name or "
                            "type says otherwise. Rename it with the right extension, or export it again."))
            width, height = img.size
            if not (MIN_DIMENSIONS[0] <= width <= MAX_DIMENSIONS[0] and
                    MIN_DIMENSIONS[1] <= height <= MAX_DIMENSIONS[1]):
                raise HTTPException(
                    status_code=400,
                    detail=(f"This image is {width}x{height} pixels. Use one between {MIN_DIMENSIONS[0]} and "
                            f"{MAX_DIMENSIONS[0]} pixels on each side."))
            img.verify()
        # Reopen after verify() to decode pixels. Pillow identifies some
        # truncated files from their header alone.
        with Image.open(io.BytesIO(contents), formats=OPEN_FORMATS) as img:
            img.load()
    except HTTPException:
        raise
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail=NOT_AN_IMAGE) from exc
    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail=UNREADABLE) from exc
    return fmt


def reencode(contents: bytes, fmt: str) -> bytes:
    """Decode the primary image and encode it afresh (LR-007, approved by Jerry).

    The stored file is a new encoding of the decoded pixels, so nothing from
    the upload but the picture survives: no EXIF (GPS location, camera,
    times), no XMP, no text chunks, no extra frames, no bytes appended after
    the image. The EXIF orientation is applied to the pixels first, or a
    phone photo would be stored sideways once its orientation tag is gone.
    Only transparency and the colour profile are carried over.
    """
    out = io.BytesIO()
    try:
        with Image.open(io.BytesIO(contents), formats=OPEN_FORMATS) as img:
            img.seek(0)                                    # the primary image of an MPO, GIF or WebP
            icc = img.info.get("icc_profile")
            frame = ImageOps.exif_transpose(img) or img.copy()
            frame.load()
        stored = STORED_FORMAT[fmt]
        if stored == "JPEG" and frame.mode not in ("RGB", "L"):
            frame = frame.convert("RGB")
        elif stored in ("PNG", "WEBP") and frame.mode not in ("RGB", "RGBA", "L", "LA"):
            frame = frame.convert("RGBA")
        clean = frame.copy()
        clean.info = {k: frame.info[k] for k in ("transparency",) if k in frame.info}
        options = {"icc_profile": icc} if icc else {}
        if stored == "JPEG":
            clean.save(out, "JPEG", quality=90, optimize=True, **options)
        elif stored == "PNG":
            clean.save(out, "PNG", optimize=True, **options)
        elif stored == "WEBP":
            clean.save(out, "WEBP", quality=90, **options)
        else:
            clean.save(out, "GIF")
    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail=UNREADABLE) from exc
    return out.getvalue()


def prepare_image(contents: bytes, declared_mime=None, extension=None) -> tuple[bytes, str, str]:
    """Inspect, then re-encode. Returns (stored bytes, extension, content type)."""
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail=f"The image is larger than {MAX_FILE_SIZE_MB}MB.")
    fmt = inspect_image(contents, declared_mime, extension)
    stored = STORED_FORMAT[fmt]
    mime = IMAGE_TYPES[stored][0]
    # An upload keeps its own (validated) extension; an import gets the canonical one.
    ext = extension if extension in IMAGE_TYPES[stored][1] else CANONICAL_EXT[stored]
    return reencode(contents, fmt), ext, mime


async def validate_image(file: UploadFile) -> tuple[bytes, str, str]:
    """Read a bounded raster upload, check it, and return it re-encoded."""
    if file.content_type not in {mime for mime, extensions in IMAGE_TYPES.values()}:
        raise HTTPException(status_code=400, detail=NOT_AN_IMAGE)
    contents = await file.read(MAX_FILE_BYTES + 1)
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail=f"The image is larger than {MAX_FILE_SIZE_MB}MB.")
    extension = os.path.splitext(file.filename or "")[1].lower().lstrip(".")
    return prepare_image(contents, file.content_type, extension)


async def upload_branding_asset(
    file: UploadFile,
    account_id: str,
    asset_type: str  # "logo" or "headshot"
) -> dict:
    """
    Upload a branding asset to R2.
    Returns dict with url, filename, and size_bytes.
    """
    contents, ext, content_type = await validate_image(file)
    return store_branding_image(contents, ext, content_type, account_id, asset_type, file.filename)


def store_branding_image(contents: bytes, ext: str, content_type: str, account_id: str,
                         asset_type: str, original_filename) -> dict:
    """Store already-checked, re-encoded image bytes; shared by upload and import."""
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


async def delete_branding_asset(url: str) -> bool:
    """
    Delete a branding asset from R2 by URL.
    Returns True if deleted, False if not found or failed.
    """
    if not url:
        return False
    
    client = get_r2_client()
    if not client:
        return False
    
    # Extract key from URL
    key = None
    if R2_PUBLIC_URL and url.startswith(R2_PUBLIC_URL):
        key = url.replace(f"{R2_PUBLIC_URL.rstrip('/')}/", "")
    elif "branding/" in url:
        # Try to extract key from any URL format
        idx = url.find("branding/")
        if idx >= 0:
            key = url[idx:]
    
    if not key:
        return False
    
    try:
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        print(f"[Upload] Deleted: {key}")
        return True
    except Exception as e:
        print(f"[Upload] Delete failed: {e}")
        return False

