"""
Photo Proxy Utility (R2) for PDF Generation

Problem:
- MLS/CDN photo URLs often work in a user's browser, but fail in cloud HTML→PDF renderers
  (PDFShift, etc.) due to hotlink protection, IP restrictions, referrer checks, etc.

Solution:
- Fetch photos server-side from the worker (where they typically succeed),
  upload them to Cloudflare R2 (S3-compatible), and return a presigned URL.
- PDFs then load images from *our* domain (R2), not the MLS/CDN.

Notes:
- We intentionally return presigned URLs (default 7 days) so the bucket can stay private.
- If R2 is not configured, we gracefully fall back to the original URL.
"""

from __future__ import annotations

import os
import time
import uuid
from io import BytesIO
from typing import Optional, Dict, List, Tuple

import boto3
import httpx
from botocore.client import Config


# Cloudflare R2 Configuration (same env vars as worker/tasks.py)
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""

# Presign expiry: 7 days (matches existing upload_to_r2 usage)
PRESIGN_EXPIRES_S = int(os.getenv("R2_PRESIGN_EXPIRES_S", "604800"))

# Image fetch behavior
IMAGE_FETCH_TIMEOUT = float(os.getenv("PHOTO_PROXY_FETCH_TIMEOUT_S", "15.0"))
MAX_RETRIES = int(os.getenv("PHOTO_PROXY_MAX_RETRIES", "2"))
RETRY_DELAY_S = float(os.getenv("PHOTO_PROXY_RETRY_DELAY_S", "1.0"))

# User agents (look like real browsers)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _r2_configured() -> bool:
    return bool(R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME)


def _get_r2_client():
    # R2 is S3-compatible, but uses a custom endpoint and "auto" region
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def _guess_ext_and_content_type(resp: httpx.Response) -> Tuple[str, str]:
    content_type = (resp.headers.get("content-type") or "image/jpeg").split(";")[0].strip().lower()
    # Reasonable mapping for common MLS images
    if content_type == "image/png":
        return ".png", "image/png"
    if content_type == "image/webp":
        return ".webp", "image/webp"
    if content_type == "image/gif":
        return ".gif", "image/gif"
    # Default to jpeg
    return ".jpg", "image/jpeg"


def fetch_image_bytes(url: str, retry_count: int = 0) -> Optional[Tuple[bytes, str, str]]:
    """
    Fetch an image URL and return (bytes, content_type, file_ext).
    Uses browser-like headers and retries for common MLS/CDN behaviors.
    """
    if not url:
        return None

    # Skip data URIs (already embedded); don't try to re-fetch.
    if url.startswith("data:"):
        return None

    user_agent = USER_AGENTS[retry_count % len(USER_AGENTS)]
    referer = url
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            referer = f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        pass

    try:
        with httpx.Client(
            timeout=IMAGE_FETCH_TIMEOUT,
            follow_redirects=True,
            http2=False,  # Some CDNs behave oddly with HTTP/2
        ) as client:
            resp = client.get(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": referer,
                    "Sec-Fetch-Dest": "image",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "cross-site",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )

        # Rate limit / forbidden patterns
        if resp.status_code in (429, 403) and retry_count < MAX_RETRIES:
            wait_s = RETRY_DELAY_S * (retry_count + 1)
            print(f"⏳ Photo fetch {resp.status_code}; retrying in {wait_s:.1f}s: {url[:80]}...")
            time.sleep(wait_s)
            return fetch_image_bytes(url, retry_count + 1)

        if resp.status_code != 200:
            print(f"⚠️  Photo fetch failed ({resp.status_code}): {url[:80]}...")
            return None

        content_type = (resp.headers.get("content-type") or "").lower()
        if "image/" not in content_type:
            print(f"⚠️  Photo fetch returned non-image ({content_type}): {url[:80]}...")
            return None

        if len(resp.content) < 1000:
            print(f"⚠️  Photo too small ({len(resp.content)} bytes): {url[:80]}...")
            return None

        ext, normalized_ct = _guess_ext_and_content_type(resp)
        return resp.content, normalized_ct, ext

    except httpx.TimeoutException:
        if retry_count < MAX_RETRIES:
            print(f"⏱️  Photo fetch timeout; retrying: {url[:80]}...")
            time.sleep(RETRY_DELAY_S)
            return fetch_image_bytes(url, retry_count + 1)
        print(f"⏱️  Photo fetch timeout (max retries): {url[:80]}...")
        return None
    except Exception as e:
        print(f"❌ Photo fetch error: {type(e).__name__}: {e} - {url[:80]}...")
        return None


def upload_photo_bytes_to_r2(content: bytes, content_type: str, key: str) -> str:
    """
    Upload image bytes to R2 under the given key and return a presigned GET URL.
    Raises if R2 is not configured or upload fails.
    """
    if not _r2_configured():
        raise RuntimeError("R2 not configured")

    s3_client = _get_r2_client()
    s3_client.upload_fileobj(
        Fileobj=BytesIO(content),
        Bucket=R2_BUCKET_NAME,
        Key=key,
        ExtraArgs={"ContentType": content_type},
    )

    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET_NAME, "Key": key},
        ExpiresIn=PRESIGN_EXPIRES_S,
    )


def proxy_photo_url_to_r2(url: str, account_id: str, run_id: str, idx: int) -> str:
    """
    Fetch photo from MLS/CDN and return an R2 presigned URL.
    Falls back to original URL on any failure.
    """
    if not url:
        return ""

    if not _r2_configured():
        # Not configured in this environment; keep original URL.
        return url

    fetched = fetch_image_bytes(url)
    if not fetched:
        return url

    content, content_type, ext = fetched
    # Keep photo keys grouped by report run for easy debugging/cleanup.
    key = f"report-photos/{account_id}/{run_id}/{idx}-{uuid.uuid4().hex}{ext}"

    try:
        return upload_photo_bytes_to_r2(content, content_type, key)
    except Exception as e:
        print(f"⚠️  R2 upload failed, using original photo URL: {type(e).__name__}: {e}")
        return url


def proxy_report_photos_inplace(result_json: Dict, account_id: str, run_id: str) -> Dict:
    """
    Mutate a report result_json so gallery-style listing photos use R2 URLs.

    Expected shape (gallery/featured):
      result_json["listings"] = [{ "hero_photo_url": "...", ... }, ...]
    """
    listings: List[Dict] = result_json.get("listings") or []
    if not isinstance(listings, list) or not listings:
        return result_json

    for i, listing in enumerate(listings):
        if not isinstance(listing, dict):
            continue
        url = listing.get("hero_photo_url") or ""
        listing["hero_photo_url"] = proxy_photo_url_to_r2(url, account_id=account_id, run_id=run_id, idx=i)

    return result_json

