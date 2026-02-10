# Cloudflare R2 Storage

> `apps/worker/src/worker/tasks.py` (upload_to_r2 function)
> `apps/worker/src/worker/utils/photo_proxy.py` (291 lines)
> `apps/worker/src/worker/utils/image_proxy.py` (213 lines)
> S3-compatible object storage for PDFs, report JSON, and proxied MLS photos.

## Overview

Cloudflare R2 is used as the primary storage backend for all generated content.
It is S3-compatible, accessed via `boto3` with a custom endpoint, and uses presigned
URLs for secure time-limited access.

## upload_to_r2()

Core upload function in `tasks.py`:

```python
def upload_to_r2(path: str, key: str) -> str
```

- Uploads a local file to R2 under the given key
- Uses `boto3` S3 client with `signature_version="s3v4"` and `region_name="auto"`
- Returns a presigned GET URL (7-day expiry)

Used for:
- Generated PDF files
- Report JSON data

## S3 Client Configuration

```python
boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,              # https://<account_id>.r2.cloudflarestorage.com
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config=Config(signature_version="s3v4")
)
```

## Presigned URLs

- Default expiry: 7 days (604800 seconds), configurable via `R2_PRESIGN_EXPIRES_S`
- Generated using `generate_presigned_url("get_object", ...)`
- Bucket stays private; all access is through presigned URLs

## Photo Proxy (`utils/photo_proxy.py`)

### Problem

MLS/CDN photo URLs often fail in cloud PDF renderers (PDFShift) due to:
- Hotlink protection
- IP restrictions
- Referrer checks
- Rate limiting

### Solution

Fetch photos server-side from the worker, upload to R2, and use R2 presigned URLs in PDFs.

### Key Functions

| Function | Purpose |
|----------|---------|
| `proxy_photo_url_to_r2(url, account_id, run_id, idx)` | Fetch one photo, upload to R2, return presigned URL |
| `proxy_report_photos_inplace(result_json, account_id, run_id)` | Mutate all `hero_photo_url` fields in gallery listings |
| `fetch_image_bytes(url, retry_count)` | Download image with browser-like headers and retry logic |
| `upload_photo_bytes_to_r2(content, content_type, key)` | Upload bytes to R2, return presigned URL |

### Photo Proxy Pipeline

```
MLS CDN URL
  -> fetch_image_bytes()     -- Download with browser-like headers
  -> upload_photo_bytes_to_r2()  -- Upload to R2
  -> presigned URL           -- Used in HTML/PDF templates
```

### R2 Key Structure

Photos are stored under: `report-photos/{account_id}/{run_id}/{idx}-{uuid}.{ext}`

### Feature Flag

Photo proxy is disabled by default (`PHOTO_PROXY_ENABLED=false`). Set to `true` to enable.

### Fetch Behavior

- Browser-like headers (User-Agent, Accept, Referer, Sec-Fetch-*)
- Rotates 3 different User-Agent strings across retries
- Retries on 429 (rate limited) and 403 (forbidden) with exponential backoff
- Timeout: 15 seconds per request
- Validates response is an image and > 1000 bytes
- Detects content type (JPEG, PNG, WebP, GIF)

### Fallback Behavior

On any failure, the original MLS URL is returned unchanged. Photo proxy is best-effort:
- R2 not configured -> return original URL
- Fetch failed -> return original URL
- Upload failed -> return original URL

## Image Proxy (`utils/image_proxy.py`)

Alternative approach using base64 data URIs instead of R2.

### Purpose

Converts MLS photo URLs to `data:image/jpeg;base64,...` URIs embedded directly in HTML.
This ensures images render in PDFShift without any external dependencies.

### Key Functions

| Function | Purpose |
|----------|---------|
| `fetch_image_as_base64(url, retry_count)` | Download image, return base64 data URI |
| `convert_listings_photos_to_base64(listings, photo_key)` | Convert all listing photos sequentially |

### Processing

- Sequential processing with 0.5s delay between requests to avoid rate limiting
- Max 3 concurrent fetches (configurable)
- Same browser-like headers and retry logic as photo_proxy

### Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Photo Proxy (R2)** | Small HTML, fast rendering | Extra upload step, R2 dependency |
| **Image Proxy (base64)** | No R2 dependency, self-contained HTML | Large HTML files, slower rendering |

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `R2_ACCOUNT_ID` | Cloudflare account ID | Required |
| `R2_ACCESS_KEY_ID` | R2 access key | Required |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | Required |
| `R2_BUCKET_NAME` | R2 bucket name | `market-reports` |
| `R2_PRESIGN_EXPIRES_S` | Presigned URL expiry (seconds) | `604800` (7 days) |
| `PHOTO_PROXY_ENABLED` | Enable photo proxy feature | `false` |
| `PHOTO_PROXY_FETCH_TIMEOUT_S` | Image fetch timeout | `15.0` |
| `PHOTO_PROXY_MAX_RETRIES` | Max fetch retries | `2` |
| `PHOTO_PROXY_RETRY_DELAY_S` | Delay between retries | `1.0` |
