# Cloudflare R2 Integration

## Overview

Cloudflare R2 provides S3-compatible object storage for PDFs, report JSON data, and images.

## Service Details

- **Used by:** Worker service (`tasks.py`, `property_report.py`)
- **Auth method:** S3-compatible access keys
- **Client:** boto3 (AWS SDK) with custom endpoint
- **Stored content:**
  - Generated PDF reports
  - Report JSON data
  - Property images (MLS photo proxy)
- **Presigned URLs:** Generated with 7-day expiry for secure access

## Environment Variables

| Variable | Description |
|----------|-------------|
| `R2_ACCESS_KEY_ID` | S3-compatible access key ID |
| `R2_SECRET_ACCESS_KEY` | S3-compatible secret access key |
| `R2_BUCKET` | R2 bucket name |
| `R2_ENDPOINT` | R2 endpoint URL |
| `R2_PUBLIC_URL` | Public URL base for accessing stored files |

## Key Behaviors

- Uses boto3 S3 client configured with R2-specific endpoint
- PDFs are uploaded after generation and the URL is stored in the database
- MLS photos are proxied through R2 to avoid hotlinking and ensure availability
- Presigned URLs provide time-limited access to private objects (7-day default expiry)
- Report JSON and CSV exports are also stored alongside PDFs
