"""
Shared Cloudflare R2 upload utility.

Both market-report tasks and property-report tasks import from here to
ensure consistent behaviour: public CDN URL when R2_PUBLIC_URL is set,
presigned URL as a fallback, local dev stub when credentials are absent.
"""

import os
import logging

import boto3
from botocore.client import Config

logger = logging.getLogger(__name__)

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "market-reports")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if R2_ACCOUNT_ID else ""

# When set, all uploaded files are served via this permanent public URL
# (e.g. "https://cdn.trendyreports.io").  Without it we fall back to a
# 7-day presigned URL, which is acceptable only as a last resort.
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")


def upload_to_r2(local_path: str, s3_key: str, content_type: str = "application/pdf") -> str:
    """
    Upload *local_path* to Cloudflare R2 at *s3_key* and return the URL.

    URL priority:
      1. Permanent public CDN URL  (R2_PUBLIC_URL env var)
      2. 7-day presigned URL       (fallback when no CDN is configured)
      3. Local dev stub            (when R2 credentials are not set)

    Args:
        local_path:   Absolute path to the file to upload.
        s3_key:       Destination object key, e.g. "reports/acc-id/run.pdf".
        content_type: MIME type for the stored object.

    Returns:
        URL string that callers can persist and share with end-users.
    """
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        logger.warning("R2 credentials not configured – returning local dev stub URL")
        return f"http://localhost:10000/dev-files/{s3_key}"

    s3_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    logger.info(f"Uploading to R2: {s3_key}")
    with open(local_path, "rb") as fh:
        s3_client.upload_fileobj(
            fh,
            R2_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )

    if R2_PUBLIC_URL:
        public_url = f"{R2_PUBLIC_URL.rstrip('/')}/{s3_key}"
        logger.info(f"R2 upload complete (public): {public_url}")
        return public_url

    # Fallback: presigned URL (valid for 7 days).
    # Note: this URL will break after expiry; prefer setting R2_PUBLIC_URL.
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=604800,
    )
    logger.info(f"R2 upload complete (presigned, 7-day): {presigned_url[:100]}...")
    return presigned_url
